"""Pod E — close the screening gap: mid-gestation (15 < g < 50) controls.

The wave-2 screen (`screen.py`) measured label noise for high-gestation
(g >= 50: 25.8%) and low-gestation (g <= 15: 5.1%) pilot controls but left
the mid band unscreened; the extrapolation in label_noise_scale.md
interpolated ~10-15%. This measures it: every annotated pilot control with
15 < gestation_likelihood < 50 (n=41, all top-region since the pilot
annotations cover only the top region) goes through the identical pipeline —
same evidence collection, same adjudicator prompt/model/caches, same
deterministic GONE/NO_EVIDENCE rules — imported from `screen.py`, not
reimplemented.

All collected evidence is current-day, LABEL/IDENTITY USE ONLY
(data_basis=current_day_label_only); it must never feed model features.
Output: data/pilot/control_screen_mid.parquet (screen_group=mid_gestation).
"""

from __future__ import annotations

import logging
import os

import httpx
import polars as pl
from dotenv import load_dotenv

from vc_brain.ingest.contracts import DATA_ROOT
from vc_brain.labels.probe_net import USER_AGENT
from vc_brain.labels.control_screen import (
    HIGH_GESTATION,
    LOW_GESTATION,
    binomial_ci,
    screen_one,
)
from vc_brain.semantics.person_annotate import ANNOTATIONS_PATH
from vc_brain.semantics.person_extract import PILOT_COHORT_PATH

LOGGER = logging.getLogger(__name__)
MID_SCREEN_PATH = DATA_ROOT / "pilot" / "control_screen_mid.parquet"


def select_mid_cohort() -> pl.DataFrame:
    """All annotated pilot controls with 15 < gestation < 50 (the unscreened band)."""
    cohort = pl.read_parquet(PILOT_COHORT_PATH)
    ann = pl.read_parquet(ANNOTATIONS_PATH).with_columns(
        pl.col("gestation_likelihood").cast(pl.Float64, strict=False)
    )
    return (
        cohort.join(ann, on="gh_login", how="inner")
        .filter(
            (pl.col("person_type") == "control")
            & (pl.col("gestation_likelihood") > LOW_GESTATION)
            & (pl.col("gestation_likelihood") < HIGH_GESTATION)
        )
        .sort("gh_login")
        .with_columns(pl.lit("mid_gestation").alias("screen_group"))
        .select(
            "gh_login", "screen_group", "gestation_likelihood", "peak",
            "builder_type", "building_what",
        )
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    load_dotenv("/Users/mishaaghamalyan/Development/personal/competitions/vc_brain/.env")
    api_key = os.getenv("OPENROUTER_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_KEY missing")

    cohort = select_mid_cohort()
    LOGGER.info("screening %d mid-gestation controls", cohort.height)
    records = []
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=20) as web:
        with httpx.Client() as llm:
            for i, login in enumerate(cohort["gh_login"], 1):
                records.append(screen_one(web, llm, api_key, login))
                if i % 10 == 0:
                    LOGGER.info("progress %d/%d", i, cohort.height)

    out = cohort.join(pl.DataFrame(records), on="gh_login", how="left")
    MID_SCREEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.write_parquet(MID_SCREEN_PATH)
    print(f"wrote {out.height} rows -> {MID_SCREEN_PATH}")

    print("\n=== classification, mid band ===")
    print(out.group_by("classification").len().sort("len", descending=True))
    sub = out.filter(pl.col("classification") != "GONE")
    k = sub.filter(pl.col("classification") == "FOUNDER_EVIDENCE").height
    km = sub.filter(
        pl.col("classification").is_in(["FOUNDER_EVIDENCE", "MEET_WORTHY"])
    ).height
    n = sub.height
    lo, hi = binomial_ci(k, n)
    lom, him = binomial_ci(km, n)
    print(
        f"\nmid_gestation   founder: {k}/{n} = {k/n:.1%} (95% CI {lo:.1%}-{hi:.1%})"
        f" | founder+meet: {km}/{n} = {km/n:.1%} (CI {lom:.1%}-{him:.1%})"
    )
    print("\n=== FOUNDER_EVIDENCE hits ===")
    with pl.Config(fmt_str_lengths=70, tbl_width_chars=140):
        print(
            out.filter(pl.col("classification") == "FOUNDER_EVIDENCE").select(
                "gh_login", "gestation_likelihood", "company_or_product", "evidence_url"
            )
        )


if __name__ == "__main__":
    main()
