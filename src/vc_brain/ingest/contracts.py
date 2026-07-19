"""Stable paths and schemas for event extraction outputs."""

import os
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = Path(os.environ.get("VC_BRAIN_DATA_DIR", PROJECT_ROOT / "data"))
EVENTS_DIR = DATA_ROOT / "events"
CH_CACHE_DIR = DATA_ROOT / "cache" / "ch"
LABELS_DIR = DATA_ROOT / "labels"

BASELINES_PATH = EVENTS_DIR / "baselines" / "monthly_totals.parquet"
MONTHLY_AGG_DIR = EVENTS_DIR / "monthly_agg"
OWNED_REPO_AGG_DIR = EVENTS_DIR / "owned_repo_agg"
REPO_CREATIONS_DIR = EVENTS_DIR / "repo_creations"
NEGATIVES_DIR = EVENTS_DIR / "negatives"
NEGATIVE_CANDIDATES_PATH = NEGATIVES_DIR / "candidates.parquet"
NEGATIVE_MATCHES_PATH = NEGATIVES_DIR / "matched.parquet"
LEAKAGE_DROPS_PATH = EVENTS_DIR / "leakage" / "company_domain_drops.parquet"
DATA_CARD_PATH = EVENTS_DIR / "data_card.md"

FOUNDERS_PATH = LABELS_DIR / "founders.parquet"
FOUNDERS_RAW_PATH = LABELS_DIR / "founders_raw.parquet"
FOUNDERS_RESOLVED_PATH = LABELS_DIR / "founders_resolved.parquet"

CONFIDENT_GITHUB_THRESHOLD = 0.5
WINDOW_MONTHS = 48
# Playground quota is rows READ per hour; every actor-batch query full-scans the
# actor_login column, so fewer+bigger batches is the only real lever. Result sets
# stay small (aggregates), hence the generous guard.
ACTOR_BATCH_SIZE = 1500
RESULT_ROW_GUARD = 3_000_000
HASH_MODULUS = 400
DEFAULT_HASH_SEEDS = (0, 1, 2)
NEGATIVES_PER_POSITIVE = 5
ACTIVITY_BAND_LOW = 0.5
ACTIVITY_BAND_HIGH = 2.0
FIRST_SEEN_YEAR_TOLERANCE = 1
MATCH_OFFSET = 17

BASELINE_SCHEMA: dict[str, pl.DataType] = {
    "month": pl.Date,
    "event_type": pl.String,
    "event_count": pl.Int64,
}

MONTHLY_SCHEMA: dict[str, pl.DataType] = {
    "actor_login": pl.String,
    "month": pl.Date,
    "event_type": pl.String,
    "is_weekend": pl.Boolean,
    "event_count": pl.Int64,
    "t_cutoff": pl.Date,
    "cohort": pl.String,
    "no_gh_activity": pl.Boolean,
}

OWNED_REPO_SCHEMA: dict[str, pl.DataType] = {
    "owner_login": pl.String,
    "month": pl.Date,
    "event_type": pl.String,
    "event_count": pl.Int64,
    "t_cutoff": pl.Date,
    "cohort": pl.String,
}

REPO_CREATION_SCHEMA: dict[str, pl.DataType] = {
    "actor_login": pl.String,
    "created_at": pl.Datetime("us"),
    "repo_name": pl.String,
    "t_cutoff": pl.Date,
    "cohort": pl.String,
}
