"""Can the temporal-attention GNN improve the GBDT ranking as a reranker/blend?

Three strategies, each tuned ONLY on validation (matched-group expected
P(rank=1)), then evaluated once on test against the GBDT-alone baseline:

  a. tie-break   — within exact GBDT score ties, order by GNN score
  b. logit blend — sigmoid(alpha*logit(gbdt) + (1-alpha)*logit(gnn))
  c. top-K rerank — GBDT keeps its per-calendar-month top-200 set; the blend
     only permutes the GBDT score values *inside* that set (outside rows and
     the score multiset are untouched)

Score sources:
  * GBDT test  — data/scores/trajectories.parquet (verified bit-identical to
    the saved selected model in exploration).
  * GBDT validation — the saved bundle was refit on tuning+validation, so its
    validation scores are in-sample. We replicate the *tuning-stage* LightGBM
    (fit on tuning_train only, early-stopped on validation) exactly as
    train.py does, and assert its validation PR-AUC matches the recorded
    training_metrics.json value.
  * GNN — no checkpoint was saved by scripts/gnn/run.py, so the model is
    retrained identically (same seed/config); MPS kernels wobble ~±0.01
    validation PR-AUC across runs. The checkpoint and aligned scores are
    saved this time.

Usage: uv run python scripts/gnn/rerank.py
Outputs: data/eval/gnn_rerank.json, data/gnn/rerank_scores.parquet,
         data/gnn/model_rerank.pt
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import polars as pl

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

ALPHA_GRID = [round(a * 0.05, 2) for a in range(21)]
TOP_K_PER_MONTH = 200
N_BOOTSTRAP = 200
BOOTSTRAP_SEED = 20240719
PRECISION_KS = (50, 100)


# --------------------------------------------------------------------------
# pure strategy / metric helpers (unit-tested; no torch, no I/O)
# --------------------------------------------------------------------------


def logit(p: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    clipped = np.clip(np.asarray(p, dtype=np.float64), eps, 1.0 - eps)
    return np.log(clipped / (1.0 - clipped))


def tie_break_scores(gbdt: np.ndarray, gnn: np.ndarray) -> np.ndarray:
    """GBDT order preserved exactly; GNN reorders only inside exact ties.

    Adds eps*gnn with eps = half the smallest gap between distinct GBDT
    values, so no pair of distinct GBDT scores can ever be reordered
    (gnn scores live in (0, 1)).
    """
    gbdt = np.asarray(gbdt, dtype=np.float64)
    gnn = np.asarray(gnn, dtype=np.float64)
    if np.any((gnn < 0.0) | (gnn > 1.0)):
        raise ValueError("gnn scores must lie in [0, 1]")
    distinct = np.unique(gbdt)
    if len(distinct) < 2:
        return gbdt + 0.5 * gnn
    min_gap = float(np.min(np.diff(distinct)))
    return gbdt + 0.5 * min_gap * gnn


def blend_scores(gbdt: np.ndarray, gnn: np.ndarray, alpha: float) -> np.ndarray:
    z = alpha * logit(gbdt) + (1.0 - alpha) * logit(gnn)
    return 1.0 / (1.0 + np.exp(-z))


def topk_rerank_scores(
    month_keys: np.ndarray,
    logins: np.ndarray,
    gbdt: np.ndarray,
    gnn: np.ndarray,
    alpha: float,
    k: int = TOP_K_PER_MONTH,
) -> np.ndarray:
    """Within each calendar month, permute the GBDT top-k's score values.

    The top-k set is chosen by (gbdt desc, login asc); its members are
    re-ordered by the blend (desc, login asc) and re-assigned the same
    score values sorted descending. Rows outside the top-k are unchanged,
    and each month's score multiset is preserved exactly.
    """
    gbdt = np.asarray(gbdt, dtype=np.float64)
    out = gbdt.copy()
    blended = blend_scores(gbdt, gnn, alpha)
    for month in np.unique(month_keys):
        idx = np.where(month_keys == month)[0]
        if len(idx) <= 1:
            continue
        sel_order = sorted(idx, key=lambda i: (-gbdt[i], logins[i]))
        top = np.array(sel_order[: min(k, len(sel_order))])
        values = np.sort(gbdt[top])[::-1]
        reranked = sorted(top, key=lambda i: (-blended[i], logins[i]))
        out[np.array(reranked)] = values
    return out


def person_peaks(
    logins: np.ndarray, scores: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Unique logins (sorted) with each person's max score."""
    order = np.argsort(logins, kind="stable")
    uniq, starts = np.unique(logins[order], return_index=True)
    peaks = np.array(
        [scores[order[s:e]].max() for s, e in zip(starts, [*starts[1:], len(order)])]
    )
    return uniq, peaks


def precision_at_k(
    logins: np.ndarray, is_positive: np.ndarray, peaks: np.ndarray, k: int
) -> float:
    """Person-level precision@k; sort by (peak desc, login asc) as in eval."""
    order = sorted(range(len(logins)), key=lambda i: (-peaks[i], logins[i]))
    top = order[: min(k, len(order))]
    return float(np.mean(is_positive[top])) if top else 0.0


def matched_group_metrics(
    group_ids: np.ndarray, is_positive: np.ndarray, peaks: np.ndarray
) -> dict[str, float]:
    """Expected-rank convention of eval/report.py (uniform over tied ranks)."""
    rank1, tophalf, norm_rank, chance = [], [], [], []
    for gid in np.unique(group_ids):
        members = np.where(group_ids == gid)[0]
        founders = members[is_positive[members] == 1]
        if len(founders) != 1 or len(members) < 3:
            continue
        founder_peak = peaks[founders[0]]
        higher = int(np.sum(peaks[members] > founder_peak))
        tied = int(np.sum(peaks[members] == founder_peak))
        possible = range(higher + 1, higher + tied + 1)
        size = len(members)
        rank1.append(1.0 / tied if higher == 0 else 0.0)
        half = -(-size // 2)  # ceil
        tophalf.append(sum(r <= half for r in possible) / tied)
        norm_rank.append(sum((r - 1) / (size - 1) for r in possible) / tied)
        chance.append(1.0 / size)
    if not rank1:
        return {"n_groups": 0}
    return {
        "n_groups": len(rank1),
        "p_rank1": float(np.mean(rank1)),
        "chance_p_rank1": float(np.mean(chance)),
        "p_top_half": float(np.mean(tophalf)),
        "mean_normalized_rank": float(np.mean(norm_rank)),
    }


def within_month_mean_pr_auc(
    month_keys: np.ndarray, y: np.ndarray, scores: np.ndarray, min_rows: int = 5
) -> dict[str, float]:
    """Unweighted mean PR-AUC over calendar months (run.py convention)."""
    from sklearn.metrics import average_precision_score

    aps = []
    for month in np.unique(month_keys):
        mask = month_keys == month
        yy = y[mask]
        if mask.sum() >= min_rows and 0 < yy.sum() < len(yy):
            aps.append(float(average_precision_score(yy, scores[mask])))
    return {
        "mean_pr_auc": float(np.mean(aps)) if aps else float("nan"),
        "n_months": len(aps),
    }


def tie_diagnostics(
    logins: np.ndarray, is_positive: np.ndarray, peaks: np.ndarray
) -> dict[str, float | int]:
    """How bad is GBDT leaf quantization at the person level?"""
    uniq, inverse, counts = np.unique(peaks, return_inverse=True, return_counts=True)
    in_tie = counts[inverse] > 1
    mixed_values = {
        v
        for v in range(len(uniq))
        if counts[v] > 1
        and 0 < is_positive[inverse == v].sum() < counts[v]
    }
    in_mixed = np.array([inverse[i] in mixed_values for i in range(len(logins))])
    order = sorted(range(len(logins)), key=lambda i: (-peaks[i], logins[i]))
    boundary_spans = {}
    for k in PRECISION_KS:
        if len(order) > k:
            cut = peaks[order[k - 1]]
            boundary_spans[str(k)] = int(np.sum(peaks == cut))
    return {
        "people": int(len(logins)),
        "distinct_peak_scores": int(len(uniq)),
        "people_in_tied_peak_groups": int(in_tie.sum()),
        "frac_people_in_tied_peak_groups": float(in_tie.mean()),
        "tie_groups": int(np.sum(counts > 1)),
        "tie_groups_spanning_founder_control": len(mixed_values),
        "people_in_founder_control_tie_groups": int(in_mixed.sum()),
        "frac_people_in_founder_control_tie_groups": float(in_mixed.mean()),
        "people_sharing_score_at_rank_cut": boundary_spans,
    }


def matched_group_tie_count(
    group_ids: np.ndarray, is_positive: np.ndarray, peaks: np.ndarray
) -> dict[str, int]:
    """Among eligible matched groups, how often is the founder's peak tied?"""
    eligible = tied = 0
    for gid in np.unique(group_ids):
        members = np.where(group_ids == gid)[0]
        founders = members[is_positive[members] == 1]
        if len(founders) != 1 or len(members) < 3:
            continue
        eligible += 1
        founder_peak = peaks[founders[0]]
        if int(np.sum(peaks[members] == founder_peak)) > 1:
            tied += 1
    return {"eligible_groups": eligible, "groups_with_founder_peak_tied": tied}


# --------------------------------------------------------------------------
# evaluation harness
# --------------------------------------------------------------------------


def evaluate_strategy(
    frame: dict[str, np.ndarray], scores: np.ndarray
) -> dict[str, object]:
    logins, peaks = person_peaks(frame["login"], scores)
    meta = frame["person_meta"]
    is_pos = np.array([meta[lg][1] for lg in logins], dtype=np.int8)
    gids = np.array([meta[lg][0] for lg in logins])
    result: dict[str, object] = {
        f"precision_at_{k}": precision_at_k(logins, is_pos, peaks, k)
        for k in PRECISION_KS
    }
    result["matched_group"] = matched_group_metrics(gids, is_pos, peaks)
    result["within_month"] = within_month_mean_pr_auc(
        frame["cal_month"], frame["y"], scores
    )
    return result


def bootstrap_deltas(
    frame: dict[str, np.ndarray],
    baseline: np.ndarray,
    strategy: np.ndarray,
    rng: np.random.Generator,
    n_boot: int = N_BOOTSTRAP,
) -> dict[str, object]:
    """Paired bootstrap CIs (people for precision/within-month, groups for
    matched-group metrics) for strategy-minus-baseline deltas."""
    from sklearn.metrics import average_precision_score

    logins_b, peaks_b = person_peaks(frame["login"], baseline)
    _, peaks_s = person_peaks(frame["login"], strategy)
    meta = frame["person_meta"]
    is_pos = np.array([meta[lg][1] for lg in logins_b], dtype=np.int8)
    gids = np.array([meta[lg][0] for lg in logins_b])
    n_people = len(logins_b)

    login_rows: dict[str, np.ndarray] = {}
    row_order = np.argsort(frame["login"], kind="stable")
    uniq, starts = np.unique(frame["login"][row_order], return_index=True)
    for lg, s, e in zip(uniq, starts, [*starts[1:], len(row_order)]):
        login_rows[lg] = row_order[s:e]
    assert list(uniq) == list(logins_b)

    uniq_gids = np.unique(gids)
    deltas: dict[str, list[float]] = {
        **{f"precision_at_{k}": [] for k in PRECISION_KS},
        "p_rank1": [],
        "p_top_half": [],
        "within_month_mean_pr_auc": [],
    }
    for _ in range(n_boot):
        take = rng.integers(0, n_people, n_people)
        for k in PRECISION_KS:
            resampled_logins = np.array(
                [f"{logins_b[i]}#{j}" for j, i in enumerate(take)]
            )
            pb = precision_at_k(resampled_logins, is_pos[take], peaks_b[take], k)
            ps = precision_at_k(resampled_logins, is_pos[take], peaks_s[take], k)
            deltas[f"precision_at_{k}"].append(ps - pb)
        rows = np.concatenate([login_rows[logins_b[i]] for i in take])
        wm_b = wm_s = wm_n = 0.0
        for month in np.unique(frame["cal_month"][rows]):
            mask = rows[frame["cal_month"][rows] == month]
            yy = frame["y"][mask]
            if len(mask) >= 5 and 0 < yy.sum() < len(yy):
                wm_b += average_precision_score(yy, baseline[mask])
                wm_s += average_precision_score(yy, strategy[mask])
                wm_n += 1
        if wm_n:
            deltas["within_month_mean_pr_auc"].append((wm_s - wm_b) / wm_n)
        g_take = rng.integers(0, len(uniq_gids), len(uniq_gids))
        g_members = np.concatenate(
            [
                np.where(gids == uniq_gids[g])[0]
                for g in g_take
            ]
        )
        g_ids_resampled = np.concatenate(
            [
                np.full(int(np.sum(gids == uniq_gids[g])), j)
                for j, g in enumerate(g_take)
            ]
        )
        mg_b = matched_group_metrics(
            g_ids_resampled, is_pos[g_members], peaks_b[g_members]
        )
        mg_s = matched_group_metrics(
            g_ids_resampled, is_pos[g_members], peaks_s[g_members]
        )
        if mg_b.get("n_groups"):
            deltas["p_rank1"].append(mg_s["p_rank1"] - mg_b["p_rank1"])
            deltas["p_top_half"].append(mg_s["p_top_half"] - mg_b["p_top_half"])
    out: dict[str, object] = {}
    for name, values in deltas.items():
        arr = np.array(values)
        out[name] = {
            "delta_mean": float(arr.mean()),
            "ci_low": float(np.percentile(arr, 2.5)),
            "ci_high": float(np.percentile(arr, 97.5)),
            "n_resamples": int(len(arr)),
        }
    return out


def tune_alpha(
    frame: dict[str, np.ndarray],
    score_fn,
) -> tuple[float, list[dict[str, float]]]:
    """Grid-search alpha on validation matched-group expected P(rank=1);
    ties broken by top-half probability, then by larger alpha (GBDT-heavy)."""
    curve = []
    best = None
    for alpha in ALPHA_GRID:
        scores = score_fn(alpha)
        logins, peaks = person_peaks(frame["login"], scores)
        meta = frame["person_meta"]
        is_pos = np.array([meta[lg][1] for lg in logins], dtype=np.int8)
        gids = np.array([meta[lg][0] for lg in logins])
        mg = matched_group_metrics(gids, is_pos, peaks)
        curve.append({"alpha": alpha, **{k: v for k, v in mg.items()}})
        key = (mg["p_rank1"], mg["p_top_half"], alpha)
        if best is None or key > best[0]:
            best = (key, alpha)
    return best[1], curve


# --------------------------------------------------------------------------
# score production
# --------------------------------------------------------------------------


def train_and_score_gnn() -> "pl.DataFrame":
    """Retrain the temporal GNN exactly as scripts/gnn/run.py (no checkpoint
    was saved by the original experiment) and score validation + test rows."""
    import polars as pl
    import torch
    from sklearn.metrics import average_precision_score

    from dataset import (
        build_edge_store,
        build_person_graphs,
        build_samples,
        gather_batch,
        load_edges,
        load_people,
    )
    from model import TemporalEgoAttention
    from run import BATCH, K, LR, MAX_EPOCHS, OUT, PATIENCE, SEED, to_torch

    rng = np.random.default_rng(SEED)
    torch.manual_seed(SEED)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    people = load_people()
    edges = load_edges(people)
    graphs = build_person_graphs(people, edges)
    samples = build_samples(graphs)
    store = build_edge_store(graphs, samples.order)
    y = samples.labels.astype(np.float32)
    idx_train = np.where(samples.splits == "tuning_train")[0]
    idx_val = np.where(samples.splits == "validation")[0]
    idx_test = np.where(samples.splits == "test")[0]

    model = TemporalEgoAttention(d_model=64).to(device)
    pos = float(y[idx_train].sum())
    loss_fn = torch.nn.BCEWithLogitsLoss(
        pos_weight=torch.tensor((len(idx_train) - pos) / pos, device=device)
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)

    def score(indices: np.ndarray) -> np.ndarray:
        model.eval()
        out = np.zeros(len(indices))
        with torch.no_grad():
            for lo in range(0, len(indices), BATCH):
                chunk = indices[lo : lo + BATCH]
                t = to_torch(gather_batch(store, samples, chunk, K), device)
                logits, _ = model(
                    t["delta_t"], t["type_ids"], t["scalars"], t["mask"],
                    t["actor_feats"],
                )
                out[lo : lo + len(chunk)] = torch.sigmoid(logits).cpu().numpy()
        return out

    best_val, best_state, bad, epochs_run = -1.0, None, 0, 0
    t0 = time.time()
    for epoch in range(MAX_EPOCHS):
        model.train()
        order = rng.permutation(idx_train)
        for lo in range(0, len(order), BATCH):
            chunk = order[lo : lo + BATCH]
            t = to_torch(gather_batch(store, samples, chunk, K), device)
            logits, _ = model(
                t["delta_t"], t["type_ids"], t["scalars"], t["mask"],
                t["actor_feats"],
            )
            loss = loss_fn(logits, t["labels"])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        val_ap = float(average_precision_score(y[idx_val], score(idx_val)))
        epochs_run = epoch + 1
        print(f"gnn epoch {epochs_run} val_pr_auc={val_ap:.4f}")
        if val_ap > best_val:
            best_val = val_ap
            best_state = {
                k: v.detach().cpu().clone() for k, v in model.state_dict().items()
            }
            bad = 0
        else:
            bad += 1
            if bad >= PATIENCE:
                break
    model.load_state_dict(best_state)
    print(
        f"gnn retrained: epochs={epochs_run} best_val_pr_auc={best_val:.4f} "
        f"({time.time() - t0:.0f}s; original artifact run was 0.1786, "
        f"MPS wobble ~±0.01)"
    )
    OUT.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), OUT / "model_rerank.pt")

    idx_scored = np.concatenate([idx_val, idx_test])
    scores = score(idx_scored)
    frame = pl.DataFrame(
        {
            "gh_login": [samples.logins[i] for i in idx_scored],
            "month": [samples.months[i] for i in idx_scored],
            "split": [str(samples.splits[i]) for i in idx_scored],
            "y_gnn": y[idx_scored].astype(np.int8),
            "gnn_score": scores,
        }
    )
    meta = people.select(
        pl.col("actor_login").alias("gh_login"),
        "person_type",
        "match_group_id",
    )
    frame = frame.join(meta, on="gh_login", how="left")
    return frame.with_columns(
        gnn_val_pr_auc=pl.lit(best_val), gnn_epochs=pl.lit(epochs_run)
    )


def gbdt_scores() -> tuple["pl.DataFrame", dict[str, float]]:
    """Validation scores from a replicated tuning-stage LightGBM (honest,
    out-of-sample); test scores from data/scores/trajectories.parquet."""
    import lightgbm as lgb
    import polars as pl
    from sklearn.metrics import average_precision_score

    from vc_brain.models.train import (
        _labels,
        _matrix,
        _scale_pos_weight,
        lightgbm_params,
        temporal_split,
    )

    root = SCRIPT_DIR.parents[1]
    panel = pl.read_parquet(root / "data" / "features" / "panel.parquet")
    features = json.loads(
        (root / "data" / "models" / "feature_list.json").read_text()
    )
    recorded = json.loads(
        (root / "data" / "models" / "training_metrics.json").read_text()
    )["validation"]["lightgbm_pr_auc"]
    split = temporal_split(panel)
    tuning = split.filter(pl.col("split") == "tuning_train")
    validation = split.filter(pl.col("split") == "validation")
    x_tuning, y_tuning = _matrix(tuning, features), _labels(tuning)
    x_val, y_val = _matrix(validation, features), _labels(validation)
    model = lgb.LGBMClassifier(
        **lightgbm_params(scale_pos_weight=_scale_pos_weight(y_tuning))
    )
    model.fit(
        x_tuning,
        y_tuning,
        eval_X=x_val,
        eval_y=y_val,
        eval_metric="average_precision",
        callbacks=[lgb.early_stopping(30, first_metric_only=True, verbose=False)],
    )
    val_scores = model.predict_proba(x_val)[:, 1]
    val_pr = float(average_precision_score(y_val, val_scores))
    if abs(val_pr - recorded) > 1e-9:
        raise AssertionError(
            f"tuning-stage replication drifted: {val_pr} != recorded {recorded}"
        )
    val_frame = validation.select(
        "gh_login", "month", pl.col("y").cast(pl.Int8)
    ).with_columns(
        pl.Series("gbdt_score", val_scores),
        pl.lit("validation").alias("split"),
    )
    traj = pl.read_parquet(root / "data" / "scores" / "trajectories.parquet")
    test_frame = (
        split.filter(pl.col("split") == "test")
        .select("gh_login", "month", pl.col("y").cast(pl.Int8))
        .join(traj, on=["gh_login", "month"], how="inner")
        .rename({"score": "gbdt_score"})
        .with_columns(pl.lit("test").alias("split"))
    )
    full_test = split.filter(pl.col("split") == "test")
    if test_frame.height != full_test.height:
        raise AssertionError("trajectories.parquet does not cover the test panel")
    return (
        pl.concat([val_frame, test_frame.select(val_frame.columns)]),
        {"replicated_tuning_val_pr_auc": val_pr, "recorded_val_pr_auc": recorded},
    )


def to_arrays(frame: "pl.DataFrame") -> dict[str, np.ndarray]:
    person_meta = {
        str(r["gh_login"]): (
            str(r["match_group_id"]),
            1 if r["person_type"] == "positive" else 0,
        )
        for r in frame.select(
            "gh_login", "match_group_id", "person_type"
        ).unique().to_dicts()
    }
    return {
        "login": frame.get_column("gh_login").to_numpy().astype(object),
        "cal_month": np.array(
            [m.isoformat() for m in frame.get_column("month")], dtype=object
        ),
        "y": frame.get_column("y").to_numpy().astype(np.int8),
        "gbdt": frame.get_column("gbdt_score").to_numpy().astype(np.float64),
        "gnn": frame.get_column("gnn_score").to_numpy().astype(np.float64),
        "person_meta": person_meta,
    }


def main() -> None:
    import polars as pl

    root = SCRIPT_DIR.parents[1]
    gnn = train_and_score_gnn()
    gnn_val_pr = float(gnn.get_column("gnn_val_pr_auc")[0])
    gnn_epochs = int(gnn.get_column("gnn_epochs")[0])
    gnn = gnn.drop("gnn_val_pr_auc", "gnn_epochs")
    gbdt, gbdt_info = gbdt_scores()

    aligned = gnn.join(gbdt.drop("split"), on=["gh_login", "month"], how="inner")
    if aligned.height != gnn.height:
        raise AssertionError(
            f"GBDT scores missing for {gnn.height - aligned.height} GNN rows"
        )
    mismatched = aligned.filter(pl.col("y_gnn") != pl.col("y"))
    if not mismatched.is_empty():
        raise AssertionError(f"{mismatched.height} label mismatches GNN vs panel")
    aligned = aligned.drop("y_gnn")
    aligned.write_parquet(root / "data" / "gnn" / "rerank_scores.parquet")

    val = to_arrays(aligned.filter(pl.col("split") == "validation"))
    test = to_arrays(aligned.filter(pl.col("split") == "test"))
    print(
        f"aligned rows: val={len(val['y'])} test={len(test['y'])} "
        f"(people val={len(val['person_meta'])} test={len(test['person_meta'])})"
    )

    # ---- tie problem quantification --------------------------------------
    from vc_brain.models.train import temporal_split

    panel = pl.read_parquet(root / "data" / "features" / "panel.parquet")
    split_full = temporal_split(panel).filter(pl.col("split") == "test")
    traj = pl.read_parquet(root / "data" / "scores" / "trajectories.parquet")
    full = split_full.select(
        "gh_login", "month", "person_type", "match_group_id"
    ).join(traj, on=["gh_login", "month"], how="inner")
    f_logins = full.get_column("gh_login").to_numpy().astype(object)
    f_scores = full.get_column("score").to_numpy().astype(np.float64)
    f_meta = {
        str(r["gh_login"]): (
            str(r["match_group_id"]),
            1 if r["person_type"] == "positive" else 0,
        )
        for r in full.select(
            "gh_login", "match_group_id", "person_type"
        ).unique().to_dicts()
    }
    fl, fp = person_peaks(f_logins, f_scores)
    f_pos = np.array([f_meta[lg][1] for lg in fl], dtype=np.int8)
    f_gids = np.array([f_meta[lg][0] for lg in fl])
    tl, tp = person_peaks(test["login"], test["gbdt"])
    t_pos = np.array([test["person_meta"][lg][1] for lg in tl], dtype=np.int8)
    t_gids = np.array([test["person_meta"][lg][0] for lg in tl])
    ties = {
        "full_test_pool": {
            **tie_diagnostics(fl, f_pos, fp),
            "distinct_row_scores": int(np.unique(f_scores).size),
            "rows": int(len(f_scores)),
            **matched_group_tie_count(f_gids, f_pos, fp),
        },
        "gnn_scoreable_test_pool": {
            **tie_diagnostics(tl, t_pos, tp),
            "distinct_row_scores": int(np.unique(test["gbdt"]).size),
            "rows": int(len(test["gbdt"])),
            **matched_group_tie_count(t_gids, t_pos, tp),
        },
    }

    # ---- validation-only tuning ------------------------------------------
    alpha_blend, blend_curve = tune_alpha(
        val, lambda a: blend_scores(val["gbdt"], val["gnn"], a)
    )
    alpha_topk, topk_curve = tune_alpha(
        val,
        lambda a: topk_rerank_scores(
            val["cal_month"], val["login"], val["gbdt"], val["gnn"], a
        ),
    )
    print(f"tuned alphas: blend={alpha_blend} topk={alpha_topk}")

    # ---- test evaluation --------------------------------------------------
    strategies = {
        "baseline_gbdt": test["gbdt"],
        "tie_break": tie_break_scores(test["gbdt"], test["gnn"]),
        "logit_blend": blend_scores(test["gbdt"], test["gnn"], alpha_blend),
        "topk_rerank": topk_rerank_scores(
            test["cal_month"], test["login"], test["gbdt"], test["gnn"],
            alpha_topk,
        ),
        "gnn_alone": test["gnn"],
    }
    results = {name: evaluate_strategy(test, s) for name, s in strategies.items()}
    # a fresh identically-seeded rng per strategy => identical resamples, so
    # deltas are paired both within and across strategies
    cis = {
        name: bootstrap_deltas(
            test,
            strategies["baseline_gbdt"],
            s,
            np.random.default_rng(BOOTSTRAP_SEED),
        )
        for name, s in strategies.items()
        if name != "baseline_gbdt"
    }

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "protocol": {
            "tuning": "all strategy parameters tuned on validation only "
            "(matched-group expected P(rank=1); ties -> top-half, then "
            "larger alpha); test scored once",
            "gbdt_validation_scores": "replicated tuning-stage LightGBM "
            "(saved bundle is refit on tuning+validation, i.e. in-sample "
            "on validation)",
            "gbdt_test_scores": "data/scores/trajectories.parquet",
            "gnn": "retrained identically (no checkpoint was saved by "
            "run.py); checkpoint now saved to data/gnn/model_rerank.pt",
            "alpha_grid": ALPHA_GRID,
            "top_k_per_month": TOP_K_PER_MONTH,
            "bootstrap": {
                "n_resamples": N_BOOTSTRAP,
                "seed": BOOTSTRAP_SEED,
                "units": "people (precision@k, within-month); matched "
                "groups (rank metrics); paired deltas vs baseline",
            },
            "pool_note": "precision@k is computed on the GNN-scoreable "
            "test pool, not the full eval pool; the baseline column uses "
            "the same pool so the comparison is apples-to-apples",
        },
        "score_sources": {
            **gbdt_info,
            "gnn_retrain_val_pr_auc": gnn_val_pr,
            "gnn_retrain_epochs": gnn_epochs,
            "original_gnn_val_pr_auc": 0.1786,
        },
        "aligned_rows": {
            "validation": int(len(val["y"])),
            "test": int(len(test["y"])),
            "validation_people": len(val["person_meta"]),
            "test_people": len(test["person_meta"]),
        },
        "tie_problem": ties,
        "validation_tuning": {
            "alpha_blend": alpha_blend,
            "alpha_topk": alpha_topk,
            "blend_curve": blend_curve,
            "topk_curve": topk_curve,
        },
        "test_results": results,
        "test_bootstrap_deltas_vs_baseline": cis,
    }
    out = root / "data" / "eval" / "gnn_rerank.json"
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {out}")
    for name in ("tie_break", "logit_blend", "topk_rerank"):
        r = results[name]
        b = results["baseline_gbdt"]
        print(
            f"{name}: P@50 {r['precision_at_50']:.3f} "
            f"(base {b['precision_at_50']:.3f}) "
            f"P(rank=1) {r['matched_group']['p_rank1']:.3f} "
            f"(base {b['matched_group']['p_rank1']:.3f}) "
            f"within-month {r['within_month']['mean_pr_auc']:.3f} "
            f"(base {b['within_month']['mean_pr_auc']:.3f})"
        )


if __name__ == "__main__":
    main()
