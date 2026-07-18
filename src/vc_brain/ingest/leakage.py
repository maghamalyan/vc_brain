"""Executable leakage invariants for event extraction."""

from __future__ import annotations

import re
from collections.abc import Iterable

import polars as pl


class LeakageViolation(AssertionError):
    """An extracted dataset violates a pre-outcome or identity invariant."""


def assert_temporal_leakage_free(
    frame: pl.DataFrame,
    *,
    time_column: str = "month",
    cutoff_column: str = "t_cutoff",
) -> None:
    if frame.is_empty():
        return
    missing = {time_column, cutoff_column} - set(frame.columns)
    if missing:
        raise LeakageViolation(f"Cannot audit missing columns: {sorted(missing)}")
    leaked = frame.filter(
        pl.col(time_column).is_null()
        | pl.col(cutoff_column).is_null()
        | (pl.col(time_column).cast(pl.Date) >= pl.col(cutoff_column).cast(pl.Date))
    )
    if not leaked.is_empty():
        sample = leaked.select(time_column, cutoff_column).head(3).to_dicts()
        raise LeakageViolation(
            f"Found {leaked.height} rows at or after t_cutoff; sample={sample}"
        )


def assert_no_founders_in_negatives(
    negatives: pl.DataFrame,
    founder_logins: Iterable[str],
) -> None:
    if negatives.is_empty():
        return
    column = "actor_login" if "actor_login" in negatives.columns else "negative_login"
    if column not in negatives.columns:
        raise LeakageViolation("Negative sample has no actor login column")
    founders = {login.strip().lower() for login in founder_logins if login.strip()}
    leaked = {
        str(value).lower()
        for value in negatives.get_column(column).drop_nulls().to_list()
    } & founders
    if leaked:
        raise LeakageViolation(
            f"Negative sample contains {len(leaked)} labeled founder login(s): "
            f"{sorted(leaked)[:5]}"
        )


def _domain_tokens(domain: str) -> set[str]:
    domain = domain.lower().strip(".")
    if not domain:
        return set()
    stem = domain.split(".", 1)[0]
    return {domain, stem}


def company_repo_leakage_drops(
    repo_names: pl.DataFrame,
    cohort: pl.DataFrame,
) -> pl.DataFrame:
    """Identify actors whose feature-window repo names expose a company domain."""
    schema = {
        "actor_login": pl.String,
        "t_cutoff": pl.Date,
        "company_domain": pl.String,
        "repo_name": pl.String,
        "reason": pl.String,
    }
    if repo_names.is_empty() or cohort.is_empty():
        return pl.DataFrame(schema=schema)
    by_actor = {
        row["actor_login"]: row.get("company_domains") or []
        for row in cohort.to_dicts()
    }
    drops: list[dict[str, object]] = []
    for row in repo_names.to_dicts():
        actor = str(row["actor_login"]).lower()
        repo = str(row.get("repo_name") or "").lower()
        repo_parts = {part for part in re.split(r"[/._-]+", repo) if part}
        for domain in by_actor.get(actor, []):
            tokens = _domain_tokens(str(domain))
            if str(domain).lower() in repo or tokens & repo_parts:
                drops.append(
                    {
                        "actor_login": actor,
                        "t_cutoff": row["t_cutoff"],
                        "company_domain": domain,
                        "repo_name": row["repo_name"],
                        "reason": "company_website_domain_in_pre_cutoff_repo_name",
                    }
                )
                break
    if not drops:
        return pl.DataFrame(schema=schema)
    return pl.DataFrame(drops, schema=schema, strict=False).unique(
        subset=["actor_login"], maintain_order=True
    )
