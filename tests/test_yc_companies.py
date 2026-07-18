from datetime import date

import pytest

from vc_brain.labels.yc_companies import batch_start_date


@pytest.mark.parametrize(
    ("batch", "expected"),
    [
        ("Winter 2026", date(2026, 1, 5)),
        ("Spring 2025", date(2025, 4, 1)),
        ("Summer 2024", date(2024, 6, 1)),
        ("Fall 2023", date(2023, 9, 1)),
        ("W22", date(2022, 1, 5)),
        ("SP22", date(2022, 4, 1)),
        ("S22", date(2022, 6, 1)),
        ("F22", date(2022, 9, 1)),
        (None, None),
        ("not a batch", None),
    ],
)
def test_batch_start_date(batch: str | None, expected: date | None) -> None:
    assert batch_start_date(batch) == expected
