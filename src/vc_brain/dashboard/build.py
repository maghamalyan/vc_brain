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

from vc_brain.dashboard.wire import (
    BacktestFounder,
    BacktestSummary,
    DashboardInputs,
)
from vc_brain.memo.schema import Memo


PACKAGE_DIR = Path(__file__).parent
TEMPLATE_DIR = PACKAGE_DIR / "templates"
STATIC_DIR = PACKAGE_DIR / "static"


def build_site(
    *,
    data_dir: Path = Path("data/fixtures"),
    thesis_path: Path = Path("config/thesis.json"),
    output_dir: Path = Path("site"),
    inputs: DashboardInputs | None = None,
) -> Path:
    """Render an entirely local static site and return its index path."""
    if inputs is None:
        inputs = _fixture_inputs(data_dir)
    candidates = list(inputs.candidates)
    trajectories = _group_by_login(inputs.trajectories)
    events = _group_by_login(inputs.events)
    profiles = inputs.profiles
    thesis = _load_json(thesis_path)
    memos = inputs.memos

    candidates.sort(key=lambda item: float(item["current_score"]), reverse=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_dir = output_dir / "candidate"
    asset_dir = output_dir / "assets"
    memo_dir = output_dir / "memos"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    asset_dir.mkdir(parents=True, exist_ok=True)
    memo_dir.mkdir(parents=True, exist_ok=True)
    _remove_generated(candidate_dir, "*.html")
    _remove_generated(memo_dir, "*.json")
    shutil.copy2(STATIC_DIR / "styles.css", asset_dir / "styles.css")
    shutil.copy2(STATIC_DIR / "dashboard.js", asset_dir / "dashboard.js")
    (asset_dir / "plotly.min.js").write_text(get_plotlyjs(), encoding="utf-8")
    (output_dir / "thesis.json").write_text(
        json.dumps(thesis, indent=2) + "\n", encoding="utf-8"
    )

    environment = _environment()
    index_template = environment.get_template("index.html")
    detail_template = environment.get_template("candidate.html")
    backtest_template = environment.get_template("backtest.html")

    decorated = []
    for rank, candidate in enumerate(candidates, start=1):
        login = str(candidate["gh_login"])
        profile = profiles.get(login, {})
        candidate_view = _candidate_view(candidate, profile, thesis, rank)
        decorated.append(candidate_view)
        memo = memos.get(login)
        memo_link = None
        if memo_path := inputs.memo_paths.get(login):
            target = memo_dir / f"{login}.json"
            shutil.copy2(memo_path, target)
            memo_link = f"../memos/{login}.json"
        candidate_events = sorted(
            events.get(login, []), key=lambda row: _iso(row.get("ts")), reverse=True
        )
        evidence_lookup = {str(item["evidence_id"]): item for item in candidate_events}
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
            memo_link=memo_link,
            evidence_lookup=evidence_lookup,
            synthetic=inputs.synthetic,
            current_page="radar",
        )
        (candidate_dir / f"{login}.html").write_text(detail_html, encoding="utf-8")

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
        synthetic=inputs.synthetic,
        current_page="radar",
    )
    index_path = output_dir / "index.html"
    index_path.write_text(index_html, encoding="utf-8")
    backtest_html = backtest_template.render(
        page_title="We found them first — VC Brain",
        asset_prefix="",
        backtest=_backtest_view(inputs.backtest),
        synthetic=inputs.synthetic,
        current_page="backtest",
    )
    (output_dir / "backtest.html").write_text(backtest_html, encoding="utf-8")
    return index_path


def _fixture_inputs(data_dir: Path) -> DashboardInputs:
    candidates = _load_rows(data_dir / "candidates.parquet")
    trajectories = _load_rows(data_dir / "trajectories.parquet")
    events = _load_rows(data_dir / "events.parquet")
    profiles = _load_json(data_dir / "profiles.json")
    memos = _load_memos(data_dir / "memos")
    top_outbound = sorted(
        (
            candidate
            for candidate in candidates
            if candidate["source"] == "outbound_detector"
        ),
        key=lambda candidate: float(candidate["current_score"]),
        reverse=True,
    )[:3]
    memo_paths: dict[str, Path] = {}
    for candidate in top_outbound:
        login = str(candidate["gh_login"])
        path = data_dir / "memos" / f"{login}.json"
        if path.exists():
            memo_paths[login] = path
    return DashboardInputs(
        candidates=candidates,
        trajectories=trajectories,
        events=events,
        profiles=profiles,
        memos=memos,
        memo_paths=memo_paths,
        backtest=_fixture_backtest(candidates, trajectories),
        synthetic=True,
    )


def _fixture_backtest(
    candidates: list[dict[str, Any]], trajectories: list[dict[str, Any]]
) -> BacktestSummary:
    by_login = _group_by_login(trajectories)
    detected = [
        candidate
        for candidate in candidates
        if candidate["source"] == "outbound_detector"
        and candidate.get("first_detection_month")
    ]
    founders: list[BacktestFounder] = []
    for candidate in detected[:8]:
        detection = date.fromisoformat(str(candidate["first_detection_month"])[:10])
        batch_start = _add_months(detection, 12)
        founders.append(
            BacktestFounder(
                gh_login=str(candidate["gh_login"]),
                founder_name=str(candidate["founder_name"]),
                company=str(candidate["company"]),
                batch="fixture cohort",
                batch_start=batch_start,
                detection_month=detection,
                lead_months=12,
                current_score=float(candidate["current_score"]),
                trajectory=by_login.get(str(candidate["gh_login"]), []),
            )
        )
    total = sum(candidate["source"] == "outbound_detector" for candidate in candidates)
    return BacktestSummary(
        detected=len(detected),
        total_test_founders=total,
        detection_rate=len(detected) / total if total else 0.0,
        median_lead_months=12.0 if detected else None,
        lead_months_iqr=(12.0, 12.0) if detected else None,
        threshold=(
            "99th percentile of synthetic control scores in the same calendar month"
        ),
        founders=founders,
    )


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
        "up"
        if float(candidate["momentum_3mo"]) > 0
        else "down"
        if float(candidate["momentum_3mo"]) < 0
        else "flat"
    )
    item["source_label"] = (
        "Inbound" if candidate["source"] == "inbound_application" else "Outbound"
    )
    percentile = float(candidate["score_percentile"])
    item["score_percentile_display"] = (
        percentile * 100 if percentile <= 1 else percentile
    )
    item["company"] = candidate.get("company") or "Stealth company"
    item["founder_name"] = candidate.get("founder_name") or candidate["gh_login"]
    name_parts = str(item["founder_name"]).replace("(fixture)", "").split()
    item["initials"] = "".join(part[0] for part in name_parts[:2]).upper()
    item["thesis_match"] = _thesis_match(profile, thesis)
    return item


def _backtest_view(backtest: BacktestSummary) -> dict[str, Any]:
    founders = []
    for rank, founder in enumerate(backtest.founders, start=1):
        founders.append(
            {
                "rank": rank,
                "gh_login": founder.gh_login,
                "founder_name": founder.founder_name,
                "company": founder.company,
                "batch": founder.batch,
                "batch_start": founder.batch_start,
                "detection_month": founder.detection_month,
                "lead_months": founder.lead_months,
                "current_score": round(founder.current_score * 100),
                "chart": _backtest_trajectory_chart(founder),
            }
        )
    return {
        "detected": backtest.detected,
        "total_test_founders": backtest.total_test_founders,
        "detection_rate": round(backtest.detection_rate * 100),
        "median_lead_months": (
            _number(backtest.median_lead_months)
            if backtest.median_lead_months is not None
            else None
        ),
        "lead_months_iqr": backtest.lead_months_iqr,
        "threshold": backtest.threshold,
        "founders": founders,
    }


def _thesis_match(profile: dict[str, Any], thesis: dict[str, Any]) -> bool:
    check_min, check_max = thesis["check_size_usd"]
    round_size = profile.get("round_size_usd")
    return bool(
        profile.get("sector") in thesis["sectors"]
        and profile.get("stage") in thesis["stages"]
        and profile.get("geography") in thesis["geographies"]
        and isinstance(round_size, (int, float))
        and check_min <= round_size <= check_max
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


def _backtest_trajectory_chart(founder: BacktestFounder) -> str:
    ordered = sorted(founder.trajectory, key=lambda row: _iso(row.get("month")))
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=[_iso(item["month"]) for item in ordered],
            y=[round(float(item["score"]) * 100, 1) for item in ordered],
            mode="lines",
            line={"color": "#1f5b45", "width": 2.5, "shape": "spline"},
            fill="tozeroy",
            fillcolor="rgba(31, 91, 69, 0.07)",
            hovertemplate=("%{x|%b %Y}<br><b>%{y:.1f}</b> signal score<extra></extra>"),
            name="Signal score",
        )
    )
    for marker, label, color, position in (
        (founder.detection_month, "DETECTED", "#b16b32", 1.05),
        (founder.batch_start, "YC BATCH", "#385f86", 0.91),
    ):
        marker_value = marker.isoformat()
        figure.add_vline(
            x=marker_value,
            line_width=1.2,
            line_dash="dot",
            line_color=color,
        )
        figure.add_annotation(
            x=marker_value,
            y=position,
            xref="x",
            yref="paper",
            text=label,
            showarrow=False,
            font={"size": 9, "color": color},
            bgcolor="rgba(247,248,245,0.92)",
            borderpad=3,
        )
    figure.update_layout(
        height=245,
        margin={"l": 42, "r": 12, "t": 38, "b": 36},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        hovermode="x unified",
        xaxis={
            "showgrid": False,
            "tickfont": {"color": "#747b76", "size": 10},
            "fixedrange": True,
        },
        yaxis={
            "range": [0, 100],
            "ticksuffix": "%",
            "gridcolor": "#e7e9e5",
            "zeroline": False,
            "tickfont": {"color": "#747b76", "size": 10},
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


def _remove_generated(path: Path, pattern: str) -> None:
    for generated in path.glob(pattern):
        if generated.is_file():
            generated.unlink()


def _add_months(value: date, months: int) -> date:
    index = value.year * 12 + value.month - 1 + months
    return date(index // 12, index % 12 + 1, 1)


def _number(value: float) -> int | float:
    return int(value) if value.is_integer() else round(value, 1)


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


def _display_money(value: int | float | None) -> str:
    if value is None:
        return "Not disclosed"
    return f"${value / 1_000_000:g}m" if value >= 1_000_000 else f"${value / 1_000:g}k"
