"""Stage 4: assemble final founder labels and a compact data card."""

from datetime import UTC, date, datetime
from pathlib import Path

import polars as pl

from vc_brain.labels.contracts import (
    DATA_CARD_PATH,
    FOUNDERS_PATH,
    FOUNDERS_RAW_PATH,
    FOUNDERS_RESOLVED_PATH,
    RESOLUTION_SCHEMA,
)
from vc_brain.labels.storage import (
    atomic_write_parquet,
    atomic_write_text,
)

FINAL_COLUMNS = [
    "founder_name",
    "company",
    "slug",
    "batch",
    "batch_start_date",
    "founding_date_est",
    "t_cutoff",
    "gh_login",
    "gh_confidence",
    "resolution_method",
    "evidence",
    "linkedin_url",
    "twitter_url",
    "founder_bio",
    "title",
    "company_website",
    "one_liner",
    "team_size",
    "status",
]


def estimated_date(value: date | None, months: int) -> date | None:
    if value is None:
        return None
    total = value.year * 12 + value.month - 1 - months
    year, zero_based_month = divmod(total, 12)
    month = zero_based_month + 1
    is_leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    month_lengths = (
        31,
        29 if is_leap else 28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    )
    return date(year, month, min(value.day, month_lengths[month - 1]))


def markdown_table(frame: pl.DataFrame) -> str:
    if frame.is_empty():
        return "_No rows._\n"
    headers = frame.columns
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in frame.iter_rows():
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines) + "\n"


def render_data_card(frame: pl.DataFrame) -> str:
    generated_at = datetime.now(UTC).isoformat()
    by_batch = (
        frame.group_by("batch")
        .len(name="rows")
        .sort("batch", descending=True)
    )
    by_method_year = (
        frame.with_columns(pl.col("batch").str.extract(r"(\d{4})", 1).alias("batch_year"))
        .group_by("batch_year", "resolution_method")
        .agg(
            pl.len().alias("rows"),
            pl.col("gh_login").is_not_null().mean().round(4).alias("resolution_rate"),
        )
        .sort("batch_year", "resolution_method", descending=[True, False])
    )
    histogram = (
        frame.with_columns(
            pl.when(pl.col("gh_confidence").is_null())
            .then(pl.lit("missing"))
            .when(pl.col("gh_confidence") < 0.25)
            .then(pl.lit("[0.00, 0.25)"))
            .when(pl.col("gh_confidence") < 0.5)
            .then(pl.lit("[0.25, 0.50)"))
            .when(pl.col("gh_confidence") < 0.75)
            .then(pl.lit("[0.50, 0.75)"))
            .when(pl.col("gh_confidence") < 1.0)
            .then(pl.lit("[0.75, 1.00)"))
            .otherwise(pl.lit("1.00"))
            .alias("confidence_bin")
        )
        .group_by("confidence_bin")
        .len(name="rows")
        .sort("confidence_bin")
    )
    resolved = frame.get_column("gh_login").is_not_null().sum()
    resolution_rate = resolved / frame.height if frame.height else 0.0
    return "".join(
        [
            "# YC Founder Label Data Card\n\n",
            f"Generated: `{generated_at}`\n\n",
            f"Rows: **{frame.height:,}**  \n",
            f"Resolved GitHub handles: **{resolved:,}** ",
            f"(**{resolution_rate:.1%}**)\n\n",
            "## Rows per batch\n\n",
            markdown_table(by_batch),
            "\n## Resolution rate by method and batch year\n\n",
            markdown_table(by_method_year),
            "\n## Confidence histogram\n\n",
            markdown_table(histogram),
            "\n## Known limitations\n\n",
            "- YC pages can omit or lag founder-team changes.\n",
            "- Batch dates are canonical season dates; founding dates are estimated ",
            "as nine months before them.\n",
            "- GitHub resolution favors precision over recall and leaves candidates ",
            "below 0.5 unresolved.\n",
            "- Search results and public profile fields can change over time.\n",
            "- SerpAPI fallback is limited by the persisted global call cap.\n",
        ]
    )


def build_labels(
    *,
    founders_raw_path: Path = FOUNDERS_RAW_PATH,
    resolved_path: Path = FOUNDERS_RESOLVED_PATH,
    output_path: Path = FOUNDERS_PATH,
    data_card_path: Path = DATA_CARD_PATH,
) -> pl.DataFrame:
    if not founders_raw_path.exists():
        raise FileNotFoundError(
            f"Missing {founders_raw_path}; run the founders stage first"
        )
    raw = pl.read_parquet(founders_raw_path)
    if resolved_path.exists():
        resolved = pl.read_parquet(resolved_path).select(list(RESOLUTION_SCHEMA))
    else:
        resolved = pl.DataFrame(schema=RESOLUTION_SCHEMA)
    frame = (
        raw.join(resolved, on="_founder_key", how="left")
        .with_columns(
            pl.col("batch_start_date")
            .map_elements(
                lambda value: estimated_date(value, 9), return_dtype=pl.Date
            )
            .alias("founding_date_est"),
            pl.col("batch_start_date")
            .map_elements(
                lambda value: estimated_date(value, 12), return_dtype=pl.Date
            )
            .alias("t_cutoff"),
            pl.col("resolution_method").fill_null("none"),
        )
        .select(FINAL_COLUMNS)
    )
    atomic_write_parquet(frame, output_path)
    atomic_write_text(render_data_card(frame), data_card_path)
    return frame
