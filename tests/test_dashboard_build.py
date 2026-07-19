from html.parser import HTMLParser
import json
from datetime import date, datetime
from pathlib import Path

import polars as pl
import pytest

from vc_brain.dashboard.build import build_site
from vc_brain.dashboard.run import main
from vc_brain.dashboard.wire import DashboardWiringError, wire_real_data


class StructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.tables = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if element_id := attributes.get("id"):
            self.ids.add(element_id)
        if tag == "a" and (href := attributes.get("href")):
            self.links.append(href)
        if tag == "table":
            self.tables += 1


def parse(path: Path) -> tuple[StructureParser, str]:
    html = path.read_text(encoding="utf-8")
    parser = StructureParser()
    parser.feed(html)
    return parser, html


def test_dashboard_build_exposes_ranked_and_trust_boundaries(tmp_path: Path) -> None:
    output = tmp_path / "site"

    index_path = build_site(output_dir=output)

    index, index_html = parse(index_path)
    assert index.tables == 1
    assert "ranked-candidates" in index.ids
    assert "thesis-filter" in index.ids
    assert index_html.count("data-candidate-row") == 12
    assert "Synthetic demo data" in index_html
    assert (output / "assets" / "plotly.min.js").stat().st_size > 1_000_000
    assert (output / "thesis.json").exists()
    assert (output / "backtest.html").exists()
    _, backtest_html = parse(output / "backtest.html")
    assert "We found them first" in backtest_html
    assert "Retrospective backtest, out-of-time split" in backtest_html
    assert "Synthetic demo data" in backtest_html

    detail, detail_html = parse(output / "candidate" / "ada-lovelace-fixture.html")
    assert {
        "trajectory-chart",
        "investment-memo",
        "three-axis-screen",
        "evidence-timeline",
        "evidence-gaps",
    }.issubset(detail.ids)
    assert "plotly.min.js" in detail_html
    assert "trust-badge verified" in detail_html
    assert "Contradiction detected" in detail_html
    assert "LICENSE is AGPL-3.0" in detail_html
    assert any(link.startswith("https://github.com/") for link in detail.links)

    _, honest_gap_html = parse(output / "candidate" / "grace-hopper-fixture.html")
    assert "Traction &amp; KPIs: not disclosed — pre-launch." in honest_gap_html


def _write_real_contract(root: Path, *, founder_count: int = 7) -> None:
    score_dir = root / "scores"
    event_dir = root / "events" / "repo_creations"
    label_dir = root / "labels"
    eval_dir = root / "eval"
    memo_dir = root / "memos"
    for path in (score_dir, event_dir, label_dir, eval_dir, memo_dir):
        path.mkdir(parents=True, exist_ok=True)

    candidates = []
    trajectories = []
    attributions = []
    labels = []
    creations = []
    first_panel_month = date(2021, 1, 1)
    dynamic_leads = [12, 14, 16, 18]
    lead_months = []
    for index in range(founder_count):
        login = f"real-founder-{index}"
        batch_start = date(2025, 1, 1)
        if index < 3:
            detection = first_panel_month
            lead = 48
        else:
            lead = dynamic_leads[(index - 3) % len(dynamic_leads)]
            detection_index = batch_start.year * 12 + batch_start.month - 1 - lead
            detection = date(detection_index // 12, detection_index % 12 + 1, 1)
        lead_months.append(lead)
        candidates.append(
            {
                "gh_login": login,
                "founder_name": "Stale model name",
                "company": "Stale model company",
                "source": "outbound_detector",
                "current_score": 0.99 - index * 0.02,
                "score_percentile": 0.999 - index * 0.001,
                "momentum_3mo": 0.08 - index * 0.005,
                "first_detection_month": detection,
                "status": "candidate",
            }
        )
        for feature_index, feature in enumerate(
            ("tenure_months", "activity_push_3m", "own_repo_share_3m")
        ):
            attributions.append(
                {
                    "login": login,
                    "crossing_month": detection,
                    "feature": feature,
                    "delta_contrib": 0.3 - feature_index * 0.1,
                }
            )
        trajectories.append(
            {"gh_login": login, "month": first_panel_month, "score": 0.2}
        )
        if detection != first_panel_month:
            trajectories.append(
                {
                    "gh_login": login,
                    "month": detection,
                    "score": 0.9 - index * 0.01,
                }
            )
        labels.append(
            {
                "founder_name": f"Real Founder {index}",
                "company": f"Real Company {index}",
                "slug": f"real-company-{index}",
                "batch": f"W{25 + index}",
                "batch_start_date": batch_start,
                "gh_login": login,
                "one_liner": "A real test-cohort company.",
            }
        )
        creations.append(
            {
                "actor_login": login,
                "created_at": datetime(2023, index + 1, 10, 12, 0),
                "repo_name": f"{login}/signal-repo",
            }
        )

    pl.DataFrame(candidates).write_parquet(score_dir / "candidates.parquet")
    pl.DataFrame(trajectories).write_parquet(score_dir / "trajectories.parquet")
    pl.DataFrame(attributions).write_parquet(score_dir / "attributions.parquet")
    pl.DataFrame(labels).write_parquet(label_dir / "founders.parquet")
    pl.DataFrame(creations).write_parquet(event_dir / "positives.parquet")
    (eval_dir / "report.json").write_text(
        json.dumps(
            {
                "split_contract": {"test": "B >= 2024-01-01"},
                "matched_group_rank": {
                    "groups": 415,
                    "rank_1_probability": 0.345,
                    "chance_rank_1_probability": 1 / 6,
                },
                "feature_display_names": {
                    "tenure_months": "GitHub tenure",
                    "activity_push_3m": "3-month push activity",
                    "own_repo_share_3m": "recent own-repository focus",
                },
                "lead_time": {
                    "detected": founder_count,
                    "total_test_founders": 10,
                    "detection_rate": founder_count / 10,
                    "lead_months_median": 18.0,
                    "lead_months_iqr": [15.0, 48.0],
                    "lead_months": lead_months,
                    "threshold": (
                        "99th percentile of control scores in the same calendar month"
                    ),
                },
            }
        ),
        encoding="utf-8",
    )

    memo = json.loads(
        (Path("data/fixtures/memos/ada-lovelace-fixture.json")).read_text(
            encoding="utf-8"
        )
    )
    memo["company"] = "Real Company 0"
    memo["founder_logins"] = ["real-founder-0"]
    (memo_dir / "real-founder-0.json").write_text(json.dumps(memo), encoding="utf-8")


def test_real_wiring_builds_honest_backtest_and_real_evidence(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    _write_real_contract(data_root)

    inputs = wire_real_data(data_root)
    assert inputs.backtest.window_start_detected == 3
    assert inputs.backtest.window_start_share == pytest.approx(3 / 7)
    assert inputs.backtest.rising_signal_detected == 4
    assert inputs.backtest.rising_median_lead_months == 15.0
    assert inputs.backtest.rising_lead_months_iqr == (13.5, 16.5)
    assert [
        founder.high_propensity_from_start for founder in inputs.backtest.founders
    ] == [
        True,
        True,
        True,
        False,
        False,
        False,
        False,
    ]
    output = tmp_path / "site"
    build_site(inputs=inputs, output_dir=output)

    _, index_html = parse(output / "index.html")
    assert "Real Founder 0" in index_html
    assert "Stale model name" not in index_html
    assert "Synthetic demo data" not in index_html

    detail, detail_html = parse(output / "candidate" / "real-founder-0.html")
    assert "https://github.com/real-founder-0/signal-repo" in detail.links
    assert "https://www.ycombinator.com/companies/real-company-0" in detail.links
    assert "../memos/real-founder-0.json" in detail.links
    assert "Open source memo JSON" in detail_html
    assert (output / "memos" / "real-founder-0.json").exists()

    _, backtest_html = parse(output / "backtest.html")
    assert "70%" in backtest_html
    assert "High-propensity from window start" in backtest_html
    assert "43%" in backtest_html
    assert "3 of 7 detected founders" in backtest_html
    assert "true lead is at least 48 months" in backtest_html
    assert "Rising signal during window" in backtest_html
    assert "15 months" in backtest_html
    assert "IQR 13.5–16.5 months" in backtest_html
    assert "Median lead time" not in backtest_html
    assert (
        "Panel prevalence is case-control (~25%), not population base rate"
        in backtest_html
    )
    assert "calibrated probabilities live in the eval report" in backtest_html
    assert "Real Founder 0" in backtest_html
    assert backtest_html.count("data-backtest-founder") == 7
    assert "YC BATCH" in backtest_html
    assert "99th percentile" in backtest_html
    assert "Against age- and activity-matched controls" in backtest_html
    assert "34.5%" in backtest_html
    assert "Flagged on:" in backtest_html
    assert "recent own-repository focus" in backtest_html


def test_real_wiring_lists_all_missing_model_outputs(tmp_path: Path) -> None:
    with pytest.raises(DashboardWiringError) as error:
        wire_real_data(tmp_path / "data")

    message = str(error.value)
    assert "scores/candidates.parquet" in message
    assert "scores/trajectories.parquet" in message
    assert "scores/attributions.parquet" in message
    assert "eval/report.json" in message
    assert "labels/founders.parquet" in message
    assert "events/repo_creations" in message


def test_cli_modes_are_explicit_and_fixture_mode_remains_offline(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "fixture-site"
    main(["--fixtures", "--output", str(output)])
    assert (output / "index.html").exists()
    assert (output / "backtest.html").exists()

    with pytest.raises(SystemExit) as error:
        main(
            [
                "--real",
                "--data-dir",
                str(tmp_path / "missing-data"),
                "--output",
                str(tmp_path / "real-site"),
            ]
        )
    assert error.value.code == 2
    stderr = capsys.readouterr().err
    assert "Missing required real-data inputs" in stderr
    assert "scores/candidates.parquet" in stderr
