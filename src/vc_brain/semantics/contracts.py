"""Stable paths and schemas for semantic trajectory artifacts."""

import polars as pl

from vc_brain.ingest.contracts import DATA_ROOT

SEMANTICS_DIR = DATA_ROOT / "semantics"
TEXT_DIR = SEMANTICS_DIR / "text"
ANNOTATION_CACHE_DIR = DATA_ROOT / "cache" / "semantic_annotations"

POSITIVE_CANDIDATE_TEXT_PATH = TEXT_DIR / "positive_candidates.parquet"
CONTROL_CANDIDATE_TEXT_PATH = TEXT_DIR / "control_candidates.parquet"
COHORT_D_PATH = SEMANTICS_DIR / "cohort_d.parquet"
TEXT_ITEMS_PATH = TEXT_DIR / "items.parquet"
EXTRACTION_SUMMARY_PATH = SEMANTICS_DIR / "extraction_summary.json"
ANNOTATIONS_PATH = SEMANTICS_DIR / "annotations.parquet"

TEXT_EVENT_TYPES = (
    "IssuesEvent",
    "PullRequestEvent",
    "IssueCommentEvent",
    "PullRequestReviewCommentEvent",
    "DiscussionEvent",
)
TEXT_BATCH_SIZE = 1_500
MIN_TEXT_ITEMS = 20
ITEMS_PER_ACTOR_QUARTER = 40
ESTIMATED_TOKENS_PER_PERSON_QUARTER = 1_500

RAW_TEXT_SCHEMA: dict[str, pl.DataType] = {
    "actor_login": pl.String,
    "created_at": pl.Datetime("us"),
    "quarter": pl.Date,
    "item_index": pl.UInt8,
    "event_type": pl.String,
    "repo_name": pl.String,
    "title": pl.String,
    "body": pl.String,
    "t_cutoff": pl.Date,
}

COHORT_D_SCHEMA: dict[str, pl.DataType] = {
    "actor_login": pl.String,
    "t_cutoff": pl.Date,
    "person_type": pl.String,
    "matched_positive_login": pl.String,
    "text_item_count": pl.UInt32,
    "person_quarter_count": pl.UInt32,
}

TEXT_ITEM_SCHEMA: dict[str, pl.DataType] = {
    **RAW_TEXT_SCHEMA,
    "person_type": pl.String,
    "matched_positive_login": pl.String,
}
