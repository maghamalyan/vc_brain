from datetime import date
from pathlib import Path

import polars as pl

from vc_brain.labels.build_labels import FINAL_COLUMNS, build_labels
from vc_brain.labels.contracts import FOUNDER_RAW_SCHEMA, RESOLUTION_SCHEMA


def test_build_labels_assembles_dates_and_exact_columns(tmp_path: Path) -> None:
    raw_path = tmp_path / "founders_raw.parquet"
    resolved_path = tmp_path / "founders_resolved.parquet"
    output_path = tmp_path / "founders.parquet"
    card_path = tmp_path / "data_card.md"
    pl.DataFrame(
        [
            {
                "_founder_key": "acme:1",
                "founder_name": "Alice Smith",
                "company": "Acme",
                "slug": "acme",
                "batch": "Winter 2024",
                "batch_year": 2024,
                "batch_start_date": date(2024, 1, 5),
                "company_website": "https://acme.example",
                "one_liner": "Makes things",
                "team_size": 2,
                "status": "Active",
                "linkedin_url": None,
                "twitter_url": "@alice",
                "founder_bio": "Founder",
                "title": "CEO",
                "user_id": "1",
            }
        ],
        schema=FOUNDER_RAW_SCHEMA,
    ).write_parquet(raw_path)
    pl.DataFrame(
        [
            {
                "_founder_key": "acme:1",
                "gh_login": "alice",
                "gh_confidence": 0.9,
                "resolution_method": "search",
                "evidence": "{}",
            }
        ],
        schema=RESOLUTION_SCHEMA,
    ).write_parquet(resolved_path)

    result = build_labels(
        founders_raw_path=raw_path,
        resolved_path=resolved_path,
        output_path=output_path,
        data_card_path=card_path,
    )

    assert result.columns == FINAL_COLUMNS
    assert result.item(0, "founding_date_est") == date(2023, 4, 5)
    assert result.item(0, "t_cutoff") == date(2023, 1, 5)
    assert "Known limitations" in card_path.read_text(encoding="utf-8")
