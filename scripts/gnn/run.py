"""Train + evaluate the demo-scale temporal attention GNN and export artifacts.

Usage: uv run python scripts/gnn/run.py

Outputs:
  data/gnn/metrics.json              honest test metrics, GNN vs GBDT
  data/gnn/attention/<login>.json    per-month top attended repos for 5 founders
  data/gnn/attention_demo.html       static SVG figure for one founder
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import polars as pl
import torch
from sklearn.metrics import average_precision_score, roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dataset import (  # noqa: E402
    DATA,
    EVENT_TYPES,
    SampleSet,
    build_edge_store,
    build_person_graphs,
    build_samples,
    gather_batch,
    load_edges,
    load_people,
    panel_months,
)
from model import TemporalEgoAttention, count_parameters  # noqa: E402

SEED = 20240719
# defaults = the config selected on validation PR-AUC (sweep 2026-07-19; see
# docs/exploration/temporal_gnn.md): K=128, d=64, lr=5e-4
K = int(os.environ.get("GNN_K", "128"))
BATCH = 512
MAX_EPOCHS = int(os.environ.get("GNN_EPOCHS", "25"))
PATIENCE = int(os.environ.get("GNN_PATIENCE", "4"))
LR = float(os.environ.get("GNN_LR", "5e-4"))
D_MODEL = int(os.environ.get("GNN_DMODEL", "64"))
WALL_CAP_SECONDS = 18 * 60
OUT = DATA / "gnn"


def to_torch(batch: dict[str, np.ndarray], device: torch.device) -> dict[str, torch.Tensor]:
    return {
        "delta_t": torch.from_numpy(batch["delta_t"]).to(device),
        "type_ids": torch.from_numpy(batch["type_ids"]).to(device),
        "scalars": torch.from_numpy(batch["scalars"]).to(device),
        "mask": torch.from_numpy(batch["mask"]).to(device),
        "actor_feats": torch.from_numpy(batch["actor_feats"]).to(device),
        "labels": torch.from_numpy(batch["labels"]).to(device),
    }


def score_split(
    model: TemporalEgoAttention,
    store,
    samples: SampleSet,
    indices: np.ndarray,
    device: torch.device,
    want_weights: bool = False,
) -> tuple[np.ndarray, list[np.ndarray] | None]:
    model.eval()
    scores = np.zeros(len(indices), dtype=np.float64)
    weights: list[np.ndarray] | None = [] if want_weights else None
    with torch.no_grad():
        for lo in range(0, len(indices), BATCH):
            chunk = indices[lo : lo + BATCH]
            batch = gather_batch(store, samples, chunk, K)
            t = to_torch(batch, device)
            logits, attn = model(
                t["delta_t"], t["type_ids"], t["scalars"], t["mask"], t["actor_feats"]
            )
            scores[lo : lo + len(chunk)] = torch.sigmoid(logits).cpu().numpy()
            if want_weights:
                weights.extend(list(attn.cpu().numpy()))
    return scores, weights


def main() -> None:
    rng = np.random.default_rng(SEED)
    torch.manual_seed(SEED)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

    t0 = time.time()
    people = load_people()
    edges = load_edges(people)
    graphs = build_person_graphs(people, edges)
    samples = build_samples(graphs)
    store = build_edge_store(graphs, samples.order)
    n_total_people = people.height
    n_people_with_edges = len(graphs)
    print(
        f"people={n_total_people} with_edges={n_people_with_edges} "
        f"edges={len(store.times)} samples={len(samples.labels)} "
        f"skipped_no_history={samples.skipped_no_history} "
        f"build_seconds={time.time() - t0:.1f}"
    )

    split_arr = samples.splits
    idx_train = np.where(split_arr == "tuning_train")[0]
    idx_val = np.where(split_arr == "validation")[0]
    idx_test = np.where(split_arr == "test")[0]
    y = samples.labels.astype(np.float32)
    print(
        f"rows train={len(idx_train)} (pos {int(y[idx_train].sum())}) "
        f"val={len(idx_val)} (pos {int(y[idx_val].sum())}) "
        f"test={len(idx_test)} (pos {int(y[idx_test].sum())})"
    )

    model = TemporalEgoAttention(d_model=D_MODEL).to(device)
    n_params = count_parameters(model)
    assert n_params < 100_000, n_params
    print(f"parameters={n_params} device={device}")

    pos = float(y[idx_train].sum())
    pos_weight = torch.tensor((len(idx_train) - pos) / pos, device=device)
    loss_fn = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)

    train_start = time.time()
    best_val, best_state, bad_epochs, epochs_run = -1.0, None, 0, 0
    for epoch in range(MAX_EPOCHS):
        model.train()
        order = rng.permutation(idx_train)
        total_loss, n_batches = 0.0, 0
        for lo in range(0, len(order), BATCH):
            chunk = order[lo : lo + BATCH]
            t = to_torch(gather_batch(store, samples, chunk, K), device)
            logits, _ = model(
                t["delta_t"], t["type_ids"], t["scalars"], t["mask"], t["actor_feats"]
            )
            loss = loss_fn(logits, t["labels"])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += float(loss)
            n_batches += 1
        val_scores, _ = score_split(model, store, samples, idx_val, device)
        val_ap = average_precision_score(y[idx_val], val_scores)
        epochs_run = epoch + 1
        elapsed = time.time() - train_start
        print(
            f"epoch {epoch + 1} loss={total_loss / n_batches:.4f} "
            f"val_pr_auc={val_ap:.4f} elapsed={elapsed:.0f}s"
        )
        if val_ap > best_val:
            best_val = val_ap
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            bad_epochs = 0
        else:
            bad_epochs += 1
            if bad_epochs >= PATIENCE:
                print("early stop")
                break
        if elapsed > WALL_CAP_SECONDS:
            print("wall-clock cap reached")
            break
    train_seconds = time.time() - train_start
    if best_state is not None:
        model.load_state_dict(best_state)

    # ---- test evaluation, GNN vs GBDT on identical rows -------------------
    gnn_scores, _ = score_split(model, store, samples, idx_test, device)
    test_logins = [samples.logins[i] for i in idx_test]
    test_months = [samples.months[i] for i in idx_test]
    test_frame = pl.DataFrame(
        {
            "gh_login": test_logins,
            "month": test_months,
            "y": y[idx_test].astype(np.int8),
            "gnn_score": gnn_scores,
        }
    )
    traj = pl.read_parquet(DATA / "scores" / "trajectories.parquet").rename(
        {"score": "gbdt_score"}
    )
    joined = test_frame.join(traj, on=["gh_login", "month"], how="left")
    both = joined.filter(pl.col("gbdt_score").is_not_null())
    print(
        f"test rows={test_frame.height} with_gbdt={both.height} "
        f"(GBDT trajectories cover all cohort test people at panel months)"
    )

    def pooled(frame: pl.DataFrame, col: str) -> dict[str, float]:
        yy = frame.get_column("y").to_numpy()
        ss = frame.get_column(col).to_numpy()
        return {
            "pr_auc": float(average_precision_score(yy, ss)),
            "roc_auc": float(roc_auc_score(yy, ss)),
        }

    def within_month(frame: pl.DataFrame, col: str) -> dict[str, float]:
        aps, ns = [], 0
        for (_m,), g in frame.group_by("month"):
            yy = g.get_column("y").to_numpy()
            if g.height >= 5 and 0 < yy.sum() < len(yy):
                aps.append(average_precision_score(yy, g.get_column(col).to_numpy()))
                ns += 1
        return {"mean_pr_auc": float(np.mean(aps)), "n_months": ns}

    # matched-group peak-score rank (A1 convention: 1 founder, >=3 members)
    person_meta = {
        str(r["actor_login"]): (str(r["match_group_id"]), str(r["person_type"]))
        for r in people.to_dicts()
    }

    def group_rank(frame: pl.DataFrame, col: str) -> dict[str, float]:
        peaks = frame.group_by("gh_login").agg(pl.col(col).max().alias("peak"))
        groups: dict[str, list[tuple[str, str, float]]] = defaultdict(list)
        for r in peaks.to_dicts():
            gid, ptype = person_meta[r["gh_login"]]
            groups[gid].append((str(r["gh_login"]), ptype, float(r["peak"])))
        rank1, tophalf, norm_ranks, chances = 0, 0, [], []
        n_groups = 0
        for members in groups.values():
            founders = [m for m in members if m[1] == "positive"]
            if len(founders) != 1 or len(members) < 3:
                continue
            n_groups += 1
            ordered = sorted(members, key=lambda m: (-m[2], m[0]))
            rank = 1 + next(i for i, m in enumerate(ordered) if m[1] == "positive")
            size = len(members)
            rank1 += int(rank == 1)
            tophalf += int(rank <= size / 2)
            norm_ranks.append((rank - 1) / (size - 1))
            chances.append(1.0 / size)
        return {
            "n_groups": n_groups,
            "p_rank1": rank1 / n_groups,
            "chance_p_rank1": float(np.mean(chances)),
            "p_top_half": tophalf / n_groups,
            "mean_normalized_rank": float(np.mean(norm_ranks)),
        }

    metrics = {
        "dataset": {
            "people": n_total_people,
            "people_with_edges": n_people_with_edges,
            "edges": int(len(store.times)),
            "samples": int(len(samples.labels)),
            "skipped_person_months_no_history": int(samples.skipped_no_history),
            "rows": {
                "tuning_train": int(len(idx_train)),
                "validation": int(len(idx_val)),
                "test": int(len(idx_test)),
            },
            "positives": {
                "tuning_train": int(y[idx_train].sum()),
                "validation": int(y[idx_val].sum()),
                "test": int(y[idx_test].sum()),
            },
        },
        "model": {
            "parameters": int(n_params),
            "k_neighborhood": K,
            "d_model": D_MODEL,
            "learning_rate": LR,
            "device": str(device),
            "epochs_run": epochs_run,
            "train_seconds": round(train_seconds, 1),
            "best_validation_pr_auc": round(best_val, 4),
        },
        "test_comparison_rows": {
            "gnn_scoreable": int(test_frame.height),
            "joint_with_gbdt": int(both.height),
        },
        "pooled_test": {
            "gnn": pooled(both, "gnn_score"),
            "gbdt": pooled(both, "gbdt_score"),
        },
        "within_month_test": {
            "gnn": within_month(both, "gnn_score"),
            "gbdt": within_month(both, "gbdt_score"),
        },
        "matched_group_peak_rank_test": {
            "gnn": group_rank(both, "gnn_score"),
            "gbdt": group_rank(both, "gbdt_score"),
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics["pooled_test"], indent=2))
    print(json.dumps(metrics["matched_group_peak_rank_test"], indent=2))

    # ---- attention exports for 5 test founders with the richest graphs ----
    test_founders = [
        login
        for login in samples.order
        if graphs[login].split == "test" and graphs[login].person_type == "positive"
    ]
    test_founders.sort(key=lambda lg: -len(graphs[lg].times))
    demo_founders = test_founders[:5]
    attention_dir = OUT / "attention"
    attention_dir.mkdir(parents=True, exist_ok=True)
    demo_payloads: dict[str, dict] = {}
    for login in demo_founders:
        g = graphs[login]
        pi = samples.order.index(login)
        sample_ids = np.where(
            (samples.person_idx == pi)
        )[0]
        if len(sample_ids) == 0:
            continue
        scores, weights = score_split(
            model, store, samples, sample_ids, device, want_weights=True
        )
        months_payload = []
        for row, si in enumerate(sample_ids):
            end = int(samples.end_idx[si])
            start = max(0, end - K)
            n = end - start
            w = weights[row][:n]
            repo_slice = g.repo_ids[start:end]
            type_slice = g.type_ids[start:end]
            repo_weight: dict[int, float] = defaultdict(float)
            repo_type_weight: dict[int, dict[int, float]] = defaultdict(
                lambda: defaultdict(float)
            )
            for j in range(n):
                repo_weight[int(repo_slice[j])] += float(w[j])
                repo_type_weight[int(repo_slice[j])][int(type_slice[j])] += float(w[j])
            top = sorted(repo_weight.items(), key=lambda kv: -kv[1])[:5]
            months_payload.append(
                {
                    "month": samples.months[si].isoformat(),
                    "score": round(float(scores[row]), 5),
                    "top_attended": [
                        {
                            "repo": g.repo_names[rid],
                            "weight": round(wt, 4),
                            "event_type": EVENT_TYPES[
                                max(repo_type_weight[rid].items(), key=lambda kv: kv[1])[0]
                            ],
                        }
                        for rid, wt in top
                    ],
                }
            )
        payload = {
            "login": login,
            "person_type": g.person_type,
            "batch_start": g.batch_start.isoformat(),
            "gestation_start": panel_months(g.batch_start)[-1].isoformat(),
            "n_edges": int(len(g.times)),
            "months": months_payload,
        }
        (attention_dir / f"{login}.json").write_text(json.dumps(payload, indent=2) + "\n")
        demo_payloads[login] = payload
    print(f"attention exports: {sorted(demo_payloads)}")

    # ---- static demo figure (self-contained HTML/SVG, no new deps) --------
    # hero = founder whose attention shifts most toward their own repos as
    # founding approaches (largest late-minus-early own-repo attention share)
    if demo_payloads:
        hero = max(demo_payloads, key=lambda lg: _own_share_delta(demo_payloads[lg]))
        write_demo_figure(demo_payloads[hero], OUT / "attention_demo.html")
        print(f"figure written for {hero}")


def _own_share(login: str, months: list[dict]) -> float:
    total = own = 0.0
    for m in months:
        for t in m["top_attended"]:
            total += t["weight"]
            if t["repo"].lower().startswith(login.lower() + "/"):
                own += t["weight"]
    return own / total if total else 0.0


def _own_share_delta(payload: dict) -> float:
    months = payload["months"]
    login = payload["login"]
    return _own_share(login, months[-6:]) - _own_share(login, months[:6])


def write_demo_figure(payload: dict, path: Path) -> None:
    months = payload["months"]
    n = len(months)
    w, h, pad_l, pad_r, pad_t, pad_b = 900, 420, 60, 20, 50, 90
    plot_w, plot_h = w - pad_l - pad_r, h - pad_t - pad_b

    def x(i: int) -> float:
        return pad_l + plot_w * (i / max(n - 1, 1))

    def yy(v: float, vmax: float) -> float:
        return pad_t + plot_h * (1 - v / vmax)

    login = payload["login"]
    top_share = [m["top_attended"][0]["weight"] if m["top_attended"] else 0.0 for m in months]
    own_share = [_own_share(login, [m]) for m in months]
    score = [m["score"] for m in months]
    smax = max(max(score), 1e-9)
    pts_share = " ".join(f"{x(i):.1f},{yy(v, 1.0):.1f}" for i, v in enumerate(top_share))
    pts_hhi = " ".join(f"{x(i):.1f},{yy(v, 1.0):.1f}" for i, v in enumerate(own_share))
    pts_score = " ".join(f"{x(i):.1f},{yy(v, smax):.1f}" for i, v in enumerate(score))
    labels = "".join(
        f'<text x="{x(i):.0f}" y="{h - pad_b + 18}" font-size="9" text-anchor="end" '
        f'transform="rotate(-45 {x(i):.0f} {h - pad_b + 18})">{months[i]["month"][:7]}</text>'
        for i in range(0, n, 3)
    )
    grid = "".join(
        f'<line x1="{pad_l}" y1="{yy(v, 1.0):.1f}" x2="{w - pad_r}" y2="{yy(v, 1.0):.1f}" '
        f'stroke="#ddd"/><text x="{pad_l - 8}" y="{yy(v, 1.0) + 3:.1f}" font-size="9" '
        f'text-anchor="end">{v:.1f}</text>'
        for v in (0.0, 0.25, 0.5, 0.75, 1.0)
    )
    final_top = months[-1]["top_attended"][:3]
    top_txt = ", ".join(f'{t["repo"]} ({t["weight"]:.2f})' for t in final_top)
    svg = f"""<!-- generated by scripts/gnn/run.py -->
<h2 style="font-family:sans-serif">Temporal attention concentration — {payload["login"]}
(test founder, batch {payload["batch_start"][:7]})</h2>
<p style="font-family:sans-serif;max-width:850px">Attention over the last-{K} edge
ego-neighborhood at each panel month. Top-repo attention share and own-repo attention
share (weight on repos under the founder's own login, within top-5) vs. the model's
hazard score. Gestation window starts 9 months after the last plotted month.
Final-month top repos: {top_txt}.</p>
<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif">
<rect width="{w}" height="{h}" fill="white"/>
{grid}
<polyline points="{pts_share}" fill="none" stroke="#1f77b4" stroke-width="2"/>
<polyline points="{pts_hhi}" fill="none" stroke="#2ca02c" stroke-width="2" stroke-dasharray="5,3"/>
<polyline points="{pts_score}" fill="none" stroke="#d62728" stroke-width="2" stroke-dasharray="2,2"/>
{labels}
<g font-size="11">
<rect x="{pad_l}" y="12" width="14" height="3" fill="#1f77b4"/><text x="{pad_l + 20}" y="17">top-repo attention share</text>
<rect x="{pad_l + 190}" y="12" width="14" height="3" fill="#2ca02c"/><text x="{pad_l + 210}" y="17">own-repo attention share</text>
<rect x="{pad_l + 400}" y="12" width="14" height="3" fill="#d62728"/><text x="{pad_l + 420}" y="17">hazard score (scaled to max {smax:.3f})</text>
</g>
</svg>
"""
    path.write_text(svg)


if __name__ == "__main__":
    main()
