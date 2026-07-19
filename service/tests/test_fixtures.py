from __future__ import annotations

import importlib.util
import json
from datetime import date
from pathlib import Path
from types import ModuleType

import pytest

from conftest import DATA_DIR, WORKSPACE_ROOT


GENERATOR_PATH = WORKSPACE_ROOT / "data" / "fixtures" / "generate_fixtures.py"


def _load_generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("vcb_fixture_generator", GENERATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _file_bytes(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _month_delta(first: str, second: str) -> int:
    first_date = date.fromisoformat(f"{first[:7]}-01")
    second_date = date.fromisoformat(f"{second[:7]}-01")
    return (second_date.year - first_date.year) * 12 + (
        second_date.month - first_date.month
    )


def test_fixture_generator_is_byte_deterministic(tmp_path: Path) -> None:
    generator = _load_generator()
    first = tmp_path / "first"
    second = tmp_path / "second"

    generator.ROOT = first
    generator.main()
    generator.ROOT = second
    generator.main()

    assert _file_bytes(first) == _file_bytes(second)


def test_score_components_sum_to_current_score_for_every_candidate() -> None:
    candidates = json.loads((DATA_DIR / "candidates.json").read_text(encoding="utf-8"))

    for candidate in candidates:
        components = candidate["score_components"]
        assert 4 <= len(components) <= 6
        assert len({component["key"] for component in components}) == len(components)
        assert sum(component["contribution"] for component in components) == pytest.approx(
            candidate["current_score"], abs=0.001
        )


def test_recognition_lead_time_cohorts_match_the_synthetic_story() -> None:
    candidates = json.loads((DATA_DIR / "candidates.json").read_text(encoding="utf-8"))
    recognized_after: list[int] = []
    not_yet_recognized = []
    misses = []

    for candidate in candidates:
        recognition = candidate["recognition"]
        if recognition is None:
            assert candidate["first_detection_month"] is not None
            not_yet_recognized.append(candidate)
            continue
        lead_time = _month_delta(
            candidate["first_detection_month"], recognition["month"]
        )
        if lead_time > 0:
            recognized_after.append(lead_time)
        elif lead_time < 0:
            misses.append(candidate)

    assert len(recognized_after) == 9
    assert all(6 <= lead_time <= 18 for lead_time in recognized_after)
    assert max(recognized_after) >= 16
    assert len(set(recognized_after)) >= 5
    assert len(not_yet_recognized) == 2
    assert len(misses) == 1
    assert misses[0]["source"] == "inbound_application"
