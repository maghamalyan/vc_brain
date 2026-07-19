"""Temporal bipartite ego-graph dataset for the demo-scale TGAT experiment.

Builds (actor, repo, t, event_type) edges from local parquet files only:
  - data/semantics/text/items.parquet   (issue/PR/comment items, Cohort-D)
  - data/events/repo_creations/*.parquet (CreateEvent-level rows)

Sampling and labels mirror src/vc_brain/features/build.py exactly:
  - panel months: batch_start - 48 .. batch_start - 12 (37 months)
  - hazard label: 1 iff batch_start-15 <= month <= batch_start-12 (positives only)
  - split (train.py temporal_split): batch_start <= 2022-12-31 tuning,
    <= 2023-12-31 validation, else test; controls inherit the matched positive's
    batch_start via matched_positive_login.

Leakage rule: a sample at month m uses only edges with timestamp < m.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import numpy as np
import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA = PROJECT_ROOT / "data"
EPOCH = date(2015, 1, 1)
CONFIDENCE_THRESHOLD = 0.5  # same as features/build.py

EVENT_TYPES = [
    "PullRequestEvent",
    "IssueCommentEvent",
    "IssuesEvent",
    "PullRequestReviewCommentEvent",
    "CreateEvent",
]
EVENT_TYPE_ID = {name: i for i, name in enumerate(EVENT_TYPES)}
N_EVENT_TYPES = len(EVENT_TYPES)
# actor context feature dims: type mix (5) + log1p total + log1p distinct repos
# + tenure years + own-repo share + log1p days since last event
N_ACTOR_FEATS = N_EVENT_TYPES + 5


def add_months(value: date, months: int) -> date:
    total = value.year * 12 + (value.month - 1) + months
    return date(total // 12, total % 12 + 1, 1)


def panel_months(batch_start: date) -> list[date]:
    return [add_months(batch_start, offset) for offset in range(-48, -11)]


def hazard_label(batch_start: date, month: date) -> int:
    return int(add_months(batch_start, -15) <= month <= add_months(batch_start, -12))


def _days(value: date) -> float:
    return float((value - EPOCH).days)


@dataclass
class PersonGraph:
    login: str
    person_type: str
    match_group_id: str
    batch_start: date
    split: str
    # per-edge arrays sorted by time
    times: np.ndarray  # float64 days since EPOCH
    type_ids: np.ndarray  # int64
    repo_ids: np.ndarray  # int64, person-local
    is_own: np.ndarray  # float32
    is_first: np.ndarray  # float32 first event on this repo
    repo_names: list[str] = field(default_factory=list)
    # cumulative helpers
    cum_types: np.ndarray | None = None  # (n+1, T)
    cum_distinct: np.ndarray | None = None  # (n+1,)
    cum_own: np.ndarray | None = None  # (n+1,)

    def finalize(self) -> None:
        n = len(self.times)
        one_hot = np.zeros((n, N_EVENT_TYPES), dtype=np.float64)
        one_hot[np.arange(n), self.type_ids] = 1.0
        ct = np.zeros((n + 1, N_EVENT_TYPES), dtype=np.float64)
        np.cumsum(one_hot, axis=0, out=ct[1:])
        self.cum_types = ct
        self.cum_distinct = np.concatenate(
            [[0.0], np.cumsum(self.is_first.astype(np.float64))]
        )
        self.cum_own = np.concatenate([[0.0], np.cumsum(self.is_own.astype(np.float64))])


def load_people() -> pl.DataFrame:
    """Cohort-D people joined to labels; split assignment as in temporal_split."""
    cohort = pl.read_parquet(DATA / "semantics" / "cohort_d.parquet")
    labels = (
        pl.read_parquet(DATA / "labels" / "founders.parquet")
        .filter(
            pl.col("gh_login").is_not_null()
            & (pl.col("gh_login").str.strip_chars() != "")
            & (pl.col("gh_confidence") >= CONFIDENCE_THRESHOLD)
            & pl.col("batch_start_date").is_not_null()
        )
        .with_columns(pl.col("gh_login").str.to_lowercase())
        .sort("batch_start_date", "gh_login")
        .unique(subset=["gh_login"], keep="first")
        .select("gh_login", "batch_start_date")
    )
    people = cohort.join(
        labels, left_on="matched_positive_login", right_on="gh_login", how="inner"
    ).with_columns(
        pl.col("batch_start_date").dt.truncate("1mo"),
    )
    if people.height != cohort.height:
        missing = cohort.height - people.height
        raise ValueError(f"{missing} cohort people lack a confident label join")
    people = people.with_columns(
        pl.when(pl.col("batch_start_date") <= date(2022, 12, 31))
        .then(pl.lit("tuning_train"))
        .when(pl.col("batch_start_date") <= date(2023, 12, 31))
        .then(pl.lit("validation"))
        .otherwise(pl.lit("test"))
        .alias("split"),
        (
            pl.col("matched_positive_login")
            + pl.lit("|")
            + pl.col("batch_start_date").dt.to_string("%Y-%m-%d")
        ).alias("match_group_id"),
    )
    return people


def load_edges(people: pl.DataFrame) -> pl.DataFrame:
    logins = people.get_column("actor_login")
    items = (
        pl.read_parquet(DATA / "semantics" / "text" / "items.parquet")
        .select("actor_login", "created_at", "event_type", "repo_name")
        .filter(pl.col("actor_login").is_in(logins.implode()))
    )
    creations = pl.concat(
        [
            pl.read_parquet(DATA / "events" / "repo_creations" / name).select(
                "actor_login", "created_at", "repo_name"
            )
            for name in ("positives.parquet", "negatives.parquet")
        ]
    ).filter(pl.col("actor_login").is_in(logins.implode()))
    creations = creations.with_columns(pl.lit("CreateEvent").alias("event_type"))
    edges = pl.concat([items, creations.select(items.columns)]).sort(
        "actor_login", "created_at"
    )
    # enforce the leakage boundary against each person's t_cutoff
    cutoffs = people.select("actor_login", "t_cutoff")
    joined = edges.join(cutoffs, on="actor_login", how="inner")
    bad = joined.filter(
        pl.col("created_at").cast(pl.Date) >= pl.col("t_cutoff")
    )
    if not bad.is_empty():
        raise ValueError(f"{bad.height} edges at/after t_cutoff — leakage")
    return joined.drop("t_cutoff")


def build_person_graphs(
    people: pl.DataFrame, edges: pl.DataFrame
) -> dict[str, PersonGraph]:
    meta = {
        str(r["actor_login"]): r
        for r in people.select(
            "actor_login", "person_type", "match_group_id", "batch_start_date", "split"
        ).to_dicts()
    }
    graphs: dict[str, PersonGraph] = {}
    for (login,), group in edges.group_by("actor_login", maintain_order=True):
        login = str(login)
        row = meta[login]
        times = np.array(
            [
                (ts - datetime(2015, 1, 1)).total_seconds() / 86400.0
                for ts in group.get_column("created_at")
            ],
            dtype=np.float64,
        )
        order = np.argsort(times, kind="stable")
        times = times[order]
        types = group.get_column("event_type").to_numpy()[order]
        repos = group.get_column("repo_name").to_numpy()[order]
        type_ids = np.array([EVENT_TYPE_ID[t] for t in types], dtype=np.int64)
        repo_index: dict[str, int] = {}
        repo_ids = np.empty(len(repos), dtype=np.int64)
        is_first = np.zeros(len(repos), dtype=np.float32)
        for i, repo in enumerate(repos):
            if repo not in repo_index:
                repo_index[repo] = len(repo_index)
                is_first[i] = 1.0
            repo_ids[i] = repo_index[repo]
        is_own = np.array(
            [1.0 if str(r).split("/", 1)[0].lower() == login else 0.0 for r in repos],
            dtype=np.float32,
        )
        graph = PersonGraph(
            login=login,
            person_type=str(row["person_type"]),
            match_group_id=str(row["match_group_id"]),
            batch_start=row["batch_start_date"],
            split=str(row["split"]),
            times=times,
            type_ids=type_ids,
            repo_ids=repo_ids,
            is_own=is_own,
            is_first=is_first,
            repo_names=list(repo_index.keys()),
        )
        graph.finalize()
        graphs[login] = graph
    return graphs


@dataclass
class SampleSet:
    """Flat arrays describing every (person, month) sample."""

    logins: list[str]
    person_idx: np.ndarray  # int32 index into `order`
    end_idx: np.ndarray  # int32: edges [0, end) are visible
    month_days: np.ndarray  # float64
    months: list[date]
    labels: np.ndarray  # int8
    splits: np.ndarray  # object array of split names
    actor_feats: np.ndarray  # float32 (N, N_ACTOR_FEATS)
    order: list[str]  # person order for person_idx
    skipped_no_history: int = 0


def build_samples(graphs: dict[str, PersonGraph]) -> SampleSet:
    order = sorted(graphs)
    logins: list[str] = []
    person_idx: list[int] = []
    end_idx: list[int] = []
    month_days: list[float] = []
    months: list[date] = []
    labels: list[int] = []
    splits: list[str] = []
    feats: list[np.ndarray] = []
    skipped = 0
    for pi, login in enumerate(order):
        g = graphs[login]
        for month in panel_months(g.batch_start):
            md = _days(month)
            end = int(np.searchsorted(g.times, md, side="left"))
            if end == 0:
                skipped += 1
                continue
            label = (
                hazard_label(g.batch_start, month)
                if g.person_type == "positive"
                else 0
            )
            total = float(end)
            mix = g.cum_types[end] / total
            distinct = g.cum_distinct[end]
            own_share = g.cum_own[end] / total
            tenure_years = (md - g.times[0]) / 365.25
            since_last = md - g.times[end - 1]
            feats.append(
                np.concatenate(
                    [
                        mix,
                        [
                            np.log1p(total),
                            np.log1p(distinct),
                            tenure_years,
                            own_share,
                            np.log1p(since_last),
                        ],
                    ]
                ).astype(np.float32)
            )
            logins.append(login)
            person_idx.append(pi)
            end_idx.append(end)
            month_days.append(md)
            months.append(month)
            labels.append(label)
            splits.append(g.split)
    return SampleSet(
        logins=logins,
        person_idx=np.array(person_idx, dtype=np.int32),
        end_idx=np.array(end_idx, dtype=np.int32),
        month_days=np.array(month_days, dtype=np.float64),
        months=months,
        labels=np.array(labels, dtype=np.int8),
        splits=np.array(splits, dtype=object),
        actor_feats=np.stack(feats),
        order=order,
        skipped_no_history=skipped,
    )


@dataclass
class EdgeStore:
    """All persons' edges concatenated, for O(1) batch gathering."""

    offsets: np.ndarray  # (P+1,) int64 into flat arrays
    times: np.ndarray
    type_ids: np.ndarray
    repo_ids: np.ndarray
    is_own: np.ndarray
    is_first: np.ndarray


def build_edge_store(graphs: dict[str, PersonGraph], order: list[str]) -> EdgeStore:
    offsets = np.zeros(len(order) + 1, dtype=np.int64)
    for i, login in enumerate(order):
        offsets[i + 1] = offsets[i] + len(graphs[login].times)
    return EdgeStore(
        offsets=offsets,
        times=np.concatenate([graphs[k].times for k in order]),
        type_ids=np.concatenate([graphs[k].type_ids for k in order]),
        repo_ids=np.concatenate([graphs[k].repo_ids for k in order]),
        is_own=np.concatenate([graphs[k].is_own for k in order]),
        is_first=np.concatenate([graphs[k].is_first for k in order]),
    )


def gather_batch(
    store: EdgeStore,
    samples: SampleSet,
    indices: np.ndarray,
    k: int,
) -> dict[str, np.ndarray]:
    """Return padded last-k edge windows for the given sample indices."""
    b = len(indices)
    delta_t = np.zeros((b, k), dtype=np.float32)
    type_ids = np.zeros((b, k), dtype=np.int64)
    scalars = np.zeros((b, k, 2), dtype=np.float32)
    repo_ids = np.full((b, k), -1, dtype=np.int64)
    mask = np.zeros((b, k), dtype=bool)  # True = padding
    for row, si in enumerate(indices):
        pi = samples.person_idx[si]
        base = store.offsets[pi]
        end = base + samples.end_idx[si]
        start = max(base, end - k)
        n = end - start
        sl = slice(start, end)
        delta_t[row, :n] = samples.month_days[si] - store.times[sl]
        type_ids[row, :n] = store.type_ids[sl]
        scalars[row, :n, 0] = store.is_own[sl]
        scalars[row, :n, 1] = store.is_first[sl]
        repo_ids[row, :n] = store.repo_ids[sl]
        mask[row, n:] = True
    return {
        "delta_t": delta_t,
        "type_ids": type_ids,
        "scalars": scalars,
        "repo_ids": repo_ids,
        "mask": mask,
        "actor_feats": samples.actor_feats[indices],
        "labels": samples.labels[indices].astype(np.float32),
    }
