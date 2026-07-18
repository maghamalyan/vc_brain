"""Stable paths and parquet schemas shared by label pipeline stages."""

import os
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = Path(os.environ.get("VC_BRAIN_DATA_DIR", PROJECT_ROOT / "data"))
YC_CACHE_DIR = DATA_ROOT / "cache" / "yc"
LABELS_DIR = DATA_ROOT / "labels"

COMPANIES_PATH = LABELS_DIR / "companies.parquet"
FOUNDERS_RAW_PATH = LABELS_DIR / "founders_raw.parquet"
FOUNDERS_RESOLVED_PATH = LABELS_DIR / "founders_resolved.parquet"
FOUNDERS_PATH = LABELS_DIR / "founders.parquet"
DATA_CARD_PATH = LABELS_DIR / "data_card.md"

COMPANY_SCHEMA: dict[str, pl.DataType] = {
    "name": pl.String,
    "slug": pl.String,
    "batch": pl.String,
    "batch_year": pl.Int32,
    "batch_start_date": pl.Date,
    "website": pl.String,
    "one_liner": pl.String,
    "long_description": pl.String,
    "team_size": pl.Int64,
    "status": pl.String,
    "industries": pl.List(pl.String),
    "regions": pl.List(pl.String),
    "launched_at": pl.String,
    "url": pl.String,
}

FOUNDER_RAW_SCHEMA: dict[str, pl.DataType] = {
    "_founder_key": pl.String,
    "founder_name": pl.String,
    "company": pl.String,
    "slug": pl.String,
    "batch": pl.String,
    "batch_year": pl.Int32,
    "batch_start_date": pl.Date,
    "company_website": pl.String,
    "one_liner": pl.String,
    "team_size": pl.Int64,
    "status": pl.String,
    "linkedin_url": pl.String,
    "twitter_url": pl.String,
    "founder_bio": pl.String,
    "title": pl.String,
    "user_id": pl.String,
}

RESOLUTION_SCHEMA: dict[str, pl.DataType] = {
    "_founder_key": pl.String,
    "gh_login": pl.String,
    "gh_confidence": pl.Float64,
    "resolution_method": pl.String,
    "evidence": pl.String,
}
