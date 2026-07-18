from pathlib import Path

import polars as pl
import pytest

from vc_brain.labels.yc_companies import normalize_companies
from vc_brain.labels.yc_founders import (
    FounderPageError,
    extract_founders,
    parse_founders,
)

FIXTURE = Path(__file__).parent / "fixtures" / "yc_company.html"


def test_parse_founders_from_data_page_fixture() -> None:
    founders = parse_founders(FIXTURE.read_text(encoding="utf-8"))

    assert [founder["full_name"] for founder in founders] == [
        "Nicolas Dessaigne",
        "Julien Lemoine",
    ]
    assert founders[0]["twitter_url"] == "https://twitter.com/dessaigne"
    assert founders[1]["linkedin_url"] is None


def test_parse_founders_rejects_missing_identity_name() -> None:
    malformed = '<div data-page="{&quot;founders&quot;:[{&quot;user_id&quot;:1}]}"></div>'

    with pytest.raises(FounderPageError, match="non-empty full_name"):
        parse_founders(malformed)


def test_founder_stage_resumes_without_duplicates_or_refetch(tmp_path: Path) -> None:
    companies_path = tmp_path / "companies.parquet"
    output_path = tmp_path / "founders_raw.parquet"
    pages_dir = tmp_path / "pages"
    payload = [
        {
            "name": slug.title(),
            "slug": slug,
            "batch": "Summer 2024",
            "website": f"https://{slug}.example.com",
            "one_liner": "Fixture company",
            "team_size": 2,
            "status": "Active",
        }
        for slug in ("alpha", "beta", "gamma")
    ]
    normalize_companies(payload).write_parquet(companies_path)
    fixture_html = FIXTURE.read_text(encoding="utf-8")
    first_calls: list[str] = []

    def interrupted_fetch(slug: str) -> str:
        first_calls.append(slug)
        if len(first_calls) == 2:
            raise KeyboardInterrupt
        return fixture_html

    with pytest.raises(KeyboardInterrupt):
        extract_founders(
            companies_path=companies_path,
            output_path=output_path,
            pages_dir=pages_dir,
            fetch_page=interrupted_fetch,
        )

    checkpointed = pl.read_parquet(output_path)
    assert checkpointed.height == 2
    assert checkpointed.get_column("slug").unique().to_list() == ["alpha"]

    resumed_calls: list[str] = []

    def resumed_fetch(slug: str) -> str:
        resumed_calls.append(slug)
        return fixture_html

    completed = extract_founders(
        companies_path=companies_path,
        output_path=output_path,
        pages_dir=pages_dir,
        fetch_page=resumed_fetch,
    )

    assert "alpha" not in resumed_calls
    assert set(resumed_calls) == {"beta", "gamma"}
    assert completed.height == 6
    assert completed.get_column("_founder_key").n_unique() == 6
