"""Create a blind-review artifact from real semantic annotations."""

from __future__ import annotations

import hashlib
import html
import json
from datetime import date
from pathlib import Path

import polars as pl

from vc_brain.ingest.storage import atomic_write_text
from vc_brain.semantics.contracts import (
    ANNOTATIONS_PATH,
    ANNOTATION_VALIDATION_SAMPLE_PATH,
    TEXT_ITEMS_PATH,
)

SAMPLE_SIZE = 40
PER_PERSON_TYPE = SAMPLE_SIZE // 2
TIME_STRATA = 4


def _stable_key(login: str, quarter: date) -> str:
    return hashlib.sha256(f"a3-validation|{login}|{quarter}".encode()).hexdigest()


def _sample_keys(annotations: pl.DataFrame) -> list[tuple[str, date]]:
    eligible = annotations.filter(pl.col("annotation_status") == "ok")
    quarters = sorted(eligible.get_column("quarter").unique().to_list())
    quarter_stratum = {
        quarter: min(index * TIME_STRATA // len(quarters), TIME_STRATA - 1)
        for index, quarter in enumerate(quarters)
    }
    selected: list[tuple[str, date]] = []
    for person_type in ("positive", "control"):
        rows = eligible.filter(pl.col("person_type") == person_type).select(
            "actor_login", "quarter"
        ).to_dicts()
        ranked = sorted(
            rows,
            key=lambda row: _stable_key(str(row["actor_login"]), row["quarter"]),
        )
        type_selected: list[tuple[str, date]] = []
        for stratum in range(TIME_STRATA):
            candidates = [
                (str(row["actor_login"]), row["quarter"])
                for row in ranked
                if quarter_stratum[row["quarter"]] == stratum
            ]
            type_selected.extend(candidates[: PER_PERSON_TYPE // TIME_STRATA])
        if len(type_selected) < PER_PERSON_TYPE:
            already = set(type_selected)
            type_selected.extend(
                (str(row["actor_login"]), row["quarter"])
                for row in ranked
                if (str(row["actor_login"]), row["quarter"]) not in already
            )
        selected.extend(type_selected[:PER_PERSON_TYPE])
    if len(selected) != SAMPLE_SIZE:
        raise ValueError(
            f"Need {SAMPLE_SIZE} successful mixed annotations; selected {len(selected)}"
        )
    return sorted(selected, key=lambda key: _stable_key(*key))


def write_validation_sample(
    *,
    items_path: Path = TEXT_ITEMS_PATH,
    annotations_path: Path = ANNOTATIONS_PATH,
    output_path: Path = ANNOTATION_VALIDATION_SAMPLE_PATH,
) -> Path:
    """Write 40 time-stratified bundles without founder/control outcome labels."""
    items = pl.read_parquet(items_path).sort("actor_login", "quarter", "item_index")
    annotations = pl.read_parquet(annotations_path)
    keys = _sample_keys(annotations)
    annotation_lookup = {
        (str(row["actor_login"]), row["quarter"]): row
        for row in annotations.to_dicts()
    }
    item_lookup: dict[tuple[str, date], list[dict[str, object]]] = {}
    for row in items.to_dicts():
        item_lookup.setdefault((str(row["actor_login"]), row["quarter"]), []).append(
            row
        )

    sections = [
        "# A3 semantic annotation validation sample\n\n",
        "This deterministic, time-stratified blind-review sample contains 40 real "
        "person-quarter bundles. Founder/control outcome labels and matched-group "
        "identifiers are intentionally withheld.\n\n",
    ]
    for index, key in enumerate(keys, start=1):
        login, quarter = key
        annotation = annotation_lookup[key]
        sections.append(
            f"## Bundle {index:02d}: `{login}` — `{quarter.isoformat()}`\n\n"
            f"Items in bundle: {len(item_lookup[key])}\n\n"
            "### Bundle text\n\n"
        )
        for item in item_lookup[key]:
            text = (
                f"item_index: {item['item_index']}\n"
                f"created_at: {item['created_at']}\n"
                f"event_type: {item['event_type']}\n"
                f"repo_name: {item['repo_name']}\n"
                f"title: {item['title']}\n"
                f"body:\n{item['body']}"
            )
            sections.append(f"<pre>{html.escape(text)}</pre>\n\n")
        pretty_annotation = json.dumps(
            json.loads(str(annotation["annotation_json"])),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        sections.append(
            "### Model annotation\n\n"
            f"<pre>{html.escape(pretty_annotation)}</pre>\n\n"
        )
    atomic_write_text("".join(sections), output_path)
    return output_path
