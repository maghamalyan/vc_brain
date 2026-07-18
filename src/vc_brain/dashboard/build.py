"""Build the offline, investor-facing VC Brain static site."""

from __future__ import annotations

import json
import shutil
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import polars as pl
from jinja2 import Environment, FileSystemLoader, select_autoescape
from plotly.offline import get_plotlyjs

from vc_brain.memo.schema import Memo


PACKAGE_DIR = Path(__file__).parent
TEMPLATE_DIR = PACKAGE_DIR / "templates"
STATIC_DIR = PACKAGE_DIR / "static"


def build_site(
    *,
    data_dir: Path = Path("data/fixtures"),
    thesis_path: Path = Path("config/thesis.json"),
    output_dir: Path = Path("site"),
) -> Path:
    """Render an entirely local static site and return its index path."""
    candidates = _load_rows(data_dir / "candidates.parquet")
    trajectories = _group_by_login(
        _load_rows(data_dir / "trajectories.parquet")
    )
    events = _group_by_login(_load_rows(data_dir / "events.parquet"))
    profiles = _load_json(data_dir / "profiles.json")
    thesis = _load_json(thesis_path)
    memos = _load_memos(data_dir / "memos")

    candidates.sort(key=lambda item: float(item["current_score"]), reverse=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_dir = output_dir / "candidate"
    asset_dir = output_dir / "assets"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    asset_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(STATIC_DIR / "styles.css", asset_dir / "styles.css")
    shutil.copy2(STATIC_DIR / "dashboard.js", asset_dir / "dashboard.js")
    (asset_dir / "plotly.min.js").write_text(get_plotlyjs(), encoding="utf-8")
    (output_dir / "thesis.json").write_text(
        json.dumps(thesis, indent=2) + "\n", encoding="utf-8"
    )

    environment = _environment()
    index_template = environment.get_template("index.html")
    detail_template = environment.get_template("candidate.html")

    decorated = []
    for rank, candidate in enumerate(candidates, start=1):
        login = str(candidate["gh_login"])
        profile = profiles.get(login, {})
        candidate_view = _candidate_view(candidate, profile, thesis, rank)
        decorated.append(candidate_view)
        memo = memos.get(login)
        candidate_events = sorted(
            events.get(login, []), key=lambda row: _iso(row.get("ts")), reverse=True
        )
        evidence_lookup = {
            str(item["evidence_id"]): item for item in candidate_events
        }
        detail_html = detail_template.render(
            page_title=f"{candidate_view['company']} — VC Brain",
            asset_prefix="../",
            candidate=candidate_view,
            trajectory_chart=_trajectory_chart(
                trajectories.get(login, []),
                candidate.get("first_detection_month"),
            ),
            events=candidate_events,
            memo=memo,
            evidence_lookup=evidence_lookup,
            synthetic=True,
        )
        (candidate_dir / f"{login}.html").write_text(
            detail_html, encoding="utf-8"
        )

    summary = {
        "candidates": len(decorated),
        "inbound": sum(item["source"] == "inbound_application" for item in decorated),
        "memo_ready": sum(item["status"] == "memo_ready" for item in decorated),
        "thesis_matches": sum(item["thesis_match"] for item in decorated),
    }
    index_html = index_template.render(
        page_title="Opportunity radar — VC Brain",
        asset_prefix="",
        candidates=decorated,
        thesis=thesis,
        summary=summary,
        synthetic=True,
    )
    index_path = output_dir / "index.html"
    index_path.write_text(index_html, encoding="utf-8")
    return index_path


def _environment() -> Environment:
    environment = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(("html", "xml")),
    )
    environment.filters["date"] = _display_date
    environment.filters["datetime"] = _display_datetime
    environment.filters["money"] = _display_money
    return environment


def _load_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".parquet" and path.exists():
        return pl.read_parquet(path).to_dicts()
    json_path = path.with_suffix(".json")
    if json_path.exists():
        value = _load_json(json_path)
        if isinstance(value, list):
            return value
    raise FileNotFoundError(f"no fixture table found for {path}")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_memos(path: Path) -> dict[str, Memo]:
    if not path.exists():
        return {}
    return {
        item.stem: Memo.model_validate_json(item.read_text(encoding="utf-8"))
        for item in sorted(path.glob("*.json"))
    }


def _group_by_login(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["gh_login"])].append(row)
    return dict(grouped)


def _candidate_view(
    candidate: dict[str, Any],
    profile: dict[str, Any],
    thesis: dict[str, Any],
    rank: int,
) -> dict[str, Any]:
    item = dict(candidate)
    item.update(profile)
    item["rank"] = rank
    item["score_display"] = round(float(candidate["current_score"]) * 100)
    item["momentum_display"] = f"{float(candidate['momentum_3mo']) * 100:+.1f}"
    item["momentum_direction"] = (
        "up" if float(candidate["momentum_3mo"]) > 0 else "down"
        if float(candidate["momentum_3mo"]) < 0
        else "flat"
    )
    item["source_label"] = (
        "Inbound" if candidate["source"] == "inbound_application" else "Outbound"
    )
    item["company"] = candidate.get("company") or "Stealth company"
    item["founder_name"] = candidate.get("founder_name") or candidate["gh_login"]
    name_parts = str(item["founder_name"]).replace("(fixture)", "").split()
    item["initials"] = "".join(part[0] for part in name_parts[:2]).upper()
    item["thesis_match"] = _thesis_match(profile, thesis)
    return item


def _thesis_match(profile: dict[str, Any], thesis: dict[str, Any]) -> bool:
    check_min, check_max = thesis["check_size_usd"]
    return bool(
        profile.get("sector") in thesis["sectors"]
        and profile.get("stage") in thesis["stages"]
        and profile.get("geography") in thesis["geographies"]
        and check_min <= profile.get("round_size_usd", 0) <= check_max
    )


def _trajectory_chart(rows: list[dict[str, Any]], detection: Any) -> str:
    ordered = sorted(rows, key=lambda row: _iso(row.get("month")))
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=[_iso(item["month"]) for item in ordered],
            y=[round(float(item["score"]) * 100, 1) for item in ordered],
            mode="lines",
            line={"color": "#1f5b45", "width": 3, "shape": "spline"},
            fill="tozeroy",
            fillcolor="rgba(31, 91, 69, 0.08)",
            hovertemplate="%{x|%b %Y}<br><b>%{y:.1f}</b> signal score<extra></extra>",
            name="Signal score",
        )
    )
    if detection:
        detection_value = _iso(detection)
        figure.add_vline(
            x=detection_value,
            line_width=1,
            line_dash="dot",
            line_color="#b16b32",
        )
        figure.add_annotation(
            x=detection_value,
            y=1.02,
            xref="x",
            yref="paper",
            text="FIRST SIGNAL",
            showarrow=False,
            font={"size": 10, "color": "#8c5125"},
            bgcolor="#fff8ef",
            borderpad=5,
        )
    figure.update_layout(
        height=330,
        margin={"l": 44, "r": 16, "t": 28, "b": 40},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        hovermode="x unified",
        xaxis={
            "showgrid": False,
            "tickfont": {"color": "#6f746f", "size": 11},
            "fixedrange": True,
        },
        yaxis={
            "range": [0, 100],
            "ticksuffix": "%",
            "gridcolor": "#e7e9e5",
            "zeroline": False,
            "tickfont": {"color": "#6f746f", "size": 11},
            "fixedrange": True,
        },
        font={
            "family": "ui-sans-serif, -apple-system, BlinkMacSystemFont, sans-serif",
            "color": "#1c211e",
        },
    )
    return figure.to_html(
        full_html=False,
        include_plotlyjs=False,
        config={"displayModeBar": False, "responsive": True},
    )


def _iso(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value or "")


def _display_date(value: Any) -> str:
    if not value:
        return "Not detected"
    if isinstance(value, str):
        parsed = date.fromisoformat(value[:10])
    elif isinstance(value, datetime):
        parsed = value.date()
    else:
        parsed = value
    return parsed.strftime("%b %Y")


def _display_datetime(value: Any) -> str:
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
    else:
        parsed = value
    return parsed.strftime("%d %b %Y · %H:%M UTC")


def _display_money(value: int | float) -> str:
    return f"${value / 1_000_000:g}m" if value >= 1_000_000 else f"${value / 1_000:g}k"
