"""Resumable label-building pipeline for YC founders and GitHub identities."""

from vc_brain.labels.build_labels import build_labels
from vc_brain.labels.gh_resolve import resolve_founders, score_candidate
from vc_brain.labels.yc_companies import build_companies
from vc_brain.labels.yc_founders import extract_founders, parse_founders

__all__ = [
    "build_companies",
    "build_labels",
    "extract_founders",
    "parse_founders",
    "resolve_founders",
    "score_candidate",
]
