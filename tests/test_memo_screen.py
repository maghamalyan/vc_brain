import json
from pathlib import Path

from vc_brain.memo.schema import Memo
from vc_brain.memo.screen import screen_candidate


FIXTURES = Path("data/fixtures")


def test_screen_is_deterministic_and_keeps_axes_independent() -> None:
    login = "grace-hopper-fixture"
    candidates = json.loads((FIXTURES / "candidates.json").read_text())
    candidate = next(item for item in candidates if item["gh_login"] == login)
    evidence = [
        item
        for item in json.loads((FIXTURES / "events.json").read_text())
        if item["gh_login"] == login
    ]
    trajectory = [
        item
        for item in json.loads((FIXTURES / "trajectories.json").read_text())
        if item["gh_login"] == login
    ]
    memo = Memo.model_validate_json(
        (FIXTURES / "memos" / f"{login}.json").read_text()
    )

    first = screen_candidate(candidate, evidence, memo, trajectory)
    second = screen_candidate(candidate, evidence, memo, trajectory)

    assert first == second
    assert first.founder.trend == "improving"
    assert first.founder.score != first.market.score
    assert first.market.claim_ids == ["grace-product"]
    assert first.idea_vs_market.claim_ids == ["grace-product", "grace-build"]


def test_declining_trajectory_sets_founder_trend() -> None:
    login = "grace-hopper-fixture"
    memo = Memo.model_validate_json(
        (FIXTURES / "memos" / f"{login}.json").read_text()
    )
    trajectory = [
        {"month": "2026-01-01", "score": 0.8},
        {"month": "2026-02-01", "score": 0.6},
        {"month": "2026-03-01", "score": 0.4},
    ]

    screen = screen_candidate(
        {"current_score": 0.4}, [], memo, trajectory
    )

    assert screen.founder.trend == "declining"

