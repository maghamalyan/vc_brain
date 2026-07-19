"""Extract authored pre-cutoff GitHub text and freeze Cohort-D v1."""

from __future__ import annotations

import base64
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl

from vc_brain.ingest.clickhouse import ClickHouseClient
from vc_brain.ingest.storage import atomic_write_parquet, atomic_write_text
from vc_brain.ingest.sql import quote
from vc_brain.semantics.contracts import (
    COHORT_D_PATH,
    COHORT_D_SCHEMA,
    CONTROL_CANDIDATE_TEXT_PATH,
    ESTIMATED_TOKENS_PER_PERSON_QUARTER,
    EXTRACTION_SUMMARY_PATH,
    ITEMS_PER_ACTOR_QUARTER,
    MIN_TEXT_ITEMS,
    POSITIVE_CANDIDATE_TEXT_PATH,
    RAW_TEXT_SCHEMA,
    TEXT_BATCH_SIZE,
    TEXT_EVENT_TYPES,
    TEXT_ITEM_SCHEMA,
    TEXT_ITEMS_PATH,
)

LOGGER = logging.getLogger(__name__)


def _actor_values(actors: list[dict[str, Any]]) -> str:
    if not actors:
        raise ValueError("At least one actor is required")
    values = ", ".join(
        f"({quote(str(row['actor_login']))}, {quote(row['t_cutoff'].isoformat())})"
        for row in actors
    )
    return f"values('actor_login String, t_cutoff Date', {values})"


def _actor_login_list(actors: list[dict[str, Any]]) -> str:
    return ", ".join(quote(str(row["actor_login"])) for row in actors)


def text_items_sql(actors: list[dict[str, Any]]) -> str:
    """Build the bounded, actor-authored text query for one cached batch."""
    event_types = ", ".join(quote(value) for value in TEXT_EVENT_TYPES)
    return f"""
WITH cohort AS (SELECT * FROM {_actor_values(actors)})
SELECT
    actor_login,
    created_at,
    quarter,
    toUInt8(item_index) AS item_index,
    event_type,
    repo_name,
    title_b64,
    body_b64,
    t_cutoff
FROM (
    SELECT
        e.actor_login AS actor_login,
        e.created_at AS created_at,
        toStartOfQuarter(e.created_at) AS quarter,
        row_number() OVER (
            PARTITION BY e.actor_login, toStartOfQuarter(e.created_at)
            ORDER BY e.created_at DESC, e.event_type, e.repo_name, e.title, e.body
        ) AS item_index,
        toString(e.event_type) AS event_type,
        e.repo_name AS repo_name,
        base64Encode(e.title) AS title_b64,
        base64Encode(left(e.body, 1500)) AS body_b64,
        a.t_cutoff AS t_cutoff
    FROM github_events AS e
    INNER JOIN cohort AS a ON e.actor_login = a.actor_login
    PREWHERE e.actor_login IN ({_actor_login_list(actors)})
      AND e.event_type IN ({event_types})
    WHERE e.created_at < toDateTime(a.t_cutoff)
      AND (e.title != '' OR e.body != '')
)
WHERE item_index <= {ITEMS_PER_ACTOR_QUARTER}
ORDER BY actor_login, quarter, item_index
""".strip()


def _conform(frame: pl.DataFrame, schema: dict[str, pl.DataType]) -> pl.DataFrame:
    result = frame
    for column, dtype in schema.items():
        if column not in result.columns:
            result = result.with_columns(pl.lit(None, dtype=dtype).alias(column))
    return result.select(
        pl.col(column).cast(dtype, strict=False).alias(column)
        for column, dtype in schema.items()
    )


def _decode_transport_text(frame: pl.DataFrame) -> pl.DataFrame:
    if not {"title_b64", "body_b64"}.issubset(frame.columns):
        return frame

    def decode(value: str | None) -> str:
        if not value:
            return ""
        return base64.b64decode(value).decode("utf-8", "replace")

    return frame.with_columns(
        pl.col("title_b64").map_elements(decode, return_dtype=pl.String).alias("title"),
        pl.col("body_b64").map_elements(decode, return_dtype=pl.String).alias("body"),
    ).drop("title_b64", "body_b64")


def extract_text_items(
    client: ClickHouseClient,
    cohort: pl.DataFrame,
    *,
    output_path: Path,
) -> pl.DataFrame:
    """Extract and persist cached text batches for the supplied actor cutoffs."""
    required = {"actor_login", "t_cutoff"}
    missing = required - set(cohort.columns)
    if missing:
        raise ValueError(f"Text cohort is missing columns: {sorted(missing)}")
    actors = (
        cohort.select("actor_login", "t_cutoff").unique().sort("actor_login").to_dicts()
    )
    raw = client.query_actor_batches(
        actors,
        text_items_sql,
        batch_size=TEXT_BATCH_SIZE,
    )
    frame = (
        _conform(_decode_transport_text(raw), RAW_TEXT_SCHEMA)
        .sort(
            "actor_login",
            "quarter",
            "created_at",
            "event_type",
            "repo_name",
            "title",
            "body",
            descending=[False, False, True, False, False, False, False],
        )
        # github_events is distributed: window ranks can restart on shards.
        # Re-rank the merged result so this persisted cap is globally correct.
        .with_columns(
            pl.int_range(1, pl.len() + 1)
            .over("actor_login", "quarter")
            .cast(pl.UInt32)
            .alias("item_index")
        )
        .filter(pl.col("item_index") <= ITEMS_PER_ACTOR_QUARTER)
        .with_columns(pl.col("item_index").cast(pl.UInt8))
        .sort("actor_login", "quarter", "item_index")
    )
    if not frame.is_empty():
        leaked = frame.filter(pl.col("created_at").cast(pl.Date) >= pl.col("t_cutoff"))
        if not leaked.is_empty():
            raise ValueError("Semantic text extraction contained post-cutoff rows")
        over_cap = (
            frame.group_by("actor_login", "quarter")
            .len()
            .filter(pl.col("len") > ITEMS_PER_ACTOR_QUARTER)
        )
        if not over_cap.is_empty():
            raise ValueError("Semantic text extraction exceeded the quarterly cap")
    atomic_write_parquet(frame, output_path)
    LOGGER.info(
        "Semantic text extracted actors=%d observed=%d rows=%d path=%s",
        len(actors),
        frame.get_column("actor_login").n_unique() if not frame.is_empty() else 0,
        frame.height,
        output_path,
    )
    return frame


def _eligible_people(
    text: pl.DataFrame,
    cohort: pl.DataFrame,
    *,
    person_type: str,
) -> pl.DataFrame:
    counts = text.group_by("actor_login", "t_cutoff").agg(
        pl.len().cast(pl.UInt32).alias("text_item_count"),
        pl.col("quarter").n_unique().cast(pl.UInt32).alias("person_quarter_count"),
    )
    result = cohort.join(
        counts,
        on=["actor_login", "t_cutoff"],
        how="inner",
        validate="1:1",
    ).filter(pl.col("text_item_count") >= MIN_TEXT_ITEMS)
    return result.with_columns(pl.lit(person_type).alias("person_type"))


def freeze_cohort_d(
    client: ClickHouseClient,
    *,
    positive_cohort: pl.DataFrame,
    matches: pl.DataFrame,
    positive_text_path: Path = POSITIVE_CANDIDATE_TEXT_PATH,
    control_text_path: Path = CONTROL_CANDIDATE_TEXT_PATH,
    cohort_path: Path = COHORT_D_PATH,
    items_path: Path = TEXT_ITEMS_PATH,
    summary_path: Path = EXTRACTION_SUMMARY_PATH,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    """Apply the ≥20-item filter to founders and each of their matched controls."""
    required_matches = {"actor_login", "t_cutoff", "matched_positive_login"}
    missing = required_matches - set(matches.columns)
    if missing:
        raise ValueError(f"Matched controls are missing columns: {sorted(missing)}")
    matched_positive_logins = set(
        matches.get_column("matched_positive_login")
        .cast(pl.String)
        .str.to_lowercase()
        .to_list()
    )
    founders = (
        positive_cohort.with_columns(pl.col("actor_login").str.to_lowercase())
        .filter(pl.col("actor_login").is_in(matched_positive_logins))
        .select("actor_login", "t_cutoff")
        .unique()
    )
    positive_text = extract_text_items(client, founders, output_path=positive_text_path)
    eligible_founders = _eligible_people(
        positive_text,
        founders,
        person_type="positive",
    ).with_columns(pl.col("actor_login").alias("matched_positive_login"))

    controls = (
        matches.with_columns(
            pl.col("actor_login").str.to_lowercase(),
            pl.col("matched_positive_login").str.to_lowercase(),
        )
        .filter(
            pl.col("matched_positive_login").is_in(
                eligible_founders.get_column("actor_login").to_list()
            )
        )
        .select("actor_login", "t_cutoff", "matched_positive_login")
        .unique()
    )
    control_text = extract_text_items(client, controls, output_path=control_text_path)
    eligible_controls = _eligible_people(
        control_text,
        controls,
        person_type="control",
    )

    cohort_d = _conform(
        pl.concat([eligible_founders, eligible_controls], how="diagonal_relaxed"),
        COHORT_D_SCHEMA,
    ).sort("matched_positive_login", "person_type", "actor_login")
    selected_text = pl.concat(
        [
            positive_text.join(
                eligible_founders.select(
                    "actor_login", "person_type", "matched_positive_login"
                ),
                on="actor_login",
                how="inner",
                validate="m:1",
            ),
            control_text.join(
                eligible_controls.select(
                    "actor_login", "person_type", "matched_positive_login"
                ),
                on="actor_login",
                how="inner",
                validate="m:1",
            ),
        ],
        how="diagonal_relaxed",
    )
    items = _conform(selected_text, TEXT_ITEM_SCHEMA).sort(
        "matched_positive_login", "person_type", "actor_login", "quarter", "item_index"
    )
    person_quarters = items.select("actor_login", "quarter").unique().height
    summary: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "contract": {
            "event_types": list(TEXT_EVENT_TYPES),
            "strictly_pre_cutoff": True,
            "body_character_cap": 1_500,
            "items_per_actor_quarter_cap": ITEMS_PER_ACTOR_QUARTER,
            "minimum_items_per_person": MIN_TEXT_ITEMS,
        },
        "extraction_rows": {
            "positive_candidates": positive_text.height,
            "control_candidates": control_text.height,
            "cohort_d_final": items.height,
        },
        "cohort": {
            "founders": eligible_founders.height,
            "controls": eligible_controls.height,
            "people": cohort_d.height,
            "person_quarters": person_quarters,
            "text_items": items.height,
        },
        "annotation_cost_estimate": {
            "estimated_tokens_per_person_quarter": ESTIMATED_TOKENS_PER_PERSON_QUARTER,
            "estimated_total_tokens": person_quarters
            * ESTIMATED_TOKENS_PER_PERSON_QUARTER,
        },
        "annotation_status": "not_started",
    }
    atomic_write_parquet(cohort_d, cohort_path)
    atomic_write_parquet(items, items_path)
    atomic_write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", summary_path
    )
    return cohort_d, items, summary
