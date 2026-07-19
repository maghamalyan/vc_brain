"""Claude's verification gate: sample confident linkages, print YC vs GitHub side by side.

Usage: uv run python scripts/spotcheck_labels.py [n_samples] [seed]
Fetches each sampled GitHub profile LIVE so the check is independent of the
resolver's cached view.
"""

import json
import subprocess
import sys

import httpx
import polars as pl

N = int(sys.argv[1]) if len(sys.argv) > 1 else 25
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 7

resolved = pl.read_parquet("data/labels/founders_resolved.parquet")
raw = pl.read_parquet("data/labels/founders_raw.parquet")
raw = raw.with_columns(
    (pl.col("slug") + ":" + pl.col("user_id").cast(pl.Utf8)).alias("_founder_key")
)
joined = resolved.join(raw, on="_founder_key", how="inner")
conf = joined.filter(pl.col("gh_confidence") >= 0.5)
sample = conf.sample(n=min(N, len(conf)), seed=SEED)

token = subprocess.run(
    ["gh", "auth", "token"], capture_output=True, text=True, timeout=10
).stdout.strip()
client = httpx.Client(
    headers={"Authorization": f"Bearer {token}"}, timeout=20.0
)

for i, row in enumerate(sample.to_dicts(), 1):
    profile = client.get(f"https://api.github.com/users/{row['gh_login']}").json()
    print(f"--- {i}/{len(sample)} conf={row['gh_confidence']:.2f} "
          f"method={row['resolution_method']}")
    print(f"  YC : {row['founder_name']} | {row['company']} ({row['batch']}) | "
          f"tw={row.get('twitter_url','')} | bio={str(row.get('founder_bio',''))[:90]}")
    print(f"  GH : {row['gh_login']} | name={profile.get('name')} | "
          f"co={profile.get('company')} | tw={profile.get('twitter_username')} | "
          f"blog={profile.get('blog')} | bio={str(profile.get('bio',''))[:90]}")
    print(f"  sig: {json.dumps(json.loads(row['evidence']))[:160]}")
