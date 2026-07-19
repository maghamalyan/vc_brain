"""Unit tests for the pure strategy/metric helpers in scripts/gnn/rerank.py."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "gnn"))

from rerank import (  # noqa: E402
    blend_scores,
    matched_group_metrics,
    person_peaks,
    precision_at_k,
    tie_break_scores,
    tie_diagnostics,
    topk_rerank_scores,
    within_month_mean_pr_auc,
)


def test_tie_break_never_reorders_distinct_gbdt_scores() -> None:
    gbdt = np.array([0.9, 0.5, 0.5, 0.5, 0.1])
    gnn = np.array([0.0, 0.2, 0.99, 0.5, 1.0])
    out = tie_break_scores(gbdt, gnn)
    order = np.argsort(-out, kind="stable")
    # distinct GBDT levels keep their order; the 0.5 tie resolves by GNN desc
    assert list(order) == [0, 2, 3, 1, 4]


def test_tie_break_rejects_out_of_range_gnn() -> None:
    with pytest.raises(ValueError):
        tie_break_scores(np.array([0.5, 0.4]), np.array([1.5, 0.0]))


def test_blend_alpha_one_recovers_gbdt() -> None:
    gbdt = np.array([0.1, 0.42, 0.9])
    gnn = np.array([0.99, 0.01, 0.5])
    np.testing.assert_allclose(blend_scores(gbdt, gnn, 1.0), gbdt, atol=1e-12)
    np.testing.assert_allclose(blend_scores(gbdt, gnn, 0.0), gnn, atol=1e-12)


def test_topk_rerank_preserves_multiset_and_outside_rows() -> None:
    months = np.array(["2024-01"] * 5 + ["2024-02"] * 3, dtype=object)
    logins = np.array(list("abcdefgh"), dtype=object)
    gbdt = np.array([0.9, 0.8, 0.7, 0.2, 0.1, 0.6, 0.5, 0.4])
    gnn = np.array([0.1, 0.2, 0.9, 0.5, 0.5, 0.1, 0.9, 0.5])
    out = topk_rerank_scores(months, logins, gbdt, gnn, alpha=0.0, k=3)
    # outside the per-month top-3, untouched
    np.testing.assert_array_equal(out[3:5], gbdt[3:5])
    # per-month score multisets preserved
    assert sorted(out[:5]) == sorted(gbdt[:5])
    assert sorted(out[5:]) == sorted(gbdt[5:])
    # alpha=0 means pure GNN order inside the top-3 of month 1: c > b > a
    assert out[2] > out[1] > out[0]


def test_topk_rerank_alpha_one_is_identity() -> None:
    months = np.array(["m"] * 4, dtype=object)
    logins = np.array(list("abcd"), dtype=object)
    gbdt = np.array([0.9, 0.8, 0.7, 0.6])
    gnn = np.array([0.1, 0.9, 0.2, 0.8])
    out = topk_rerank_scores(months, logins, gbdt, gnn, alpha=1.0, k=2)
    np.testing.assert_allclose(out, gbdt, atol=1e-12)


def test_person_peaks_and_precision() -> None:
    logins = np.array(["b", "a", "b", "c"], dtype=object)
    scores = np.array([0.2, 0.9, 0.7, 0.5])
    uniq, peaks = person_peaks(logins, scores)
    assert list(uniq) == ["a", "b", "c"]
    np.testing.assert_allclose(peaks, [0.9, 0.7, 0.5])
    is_pos = np.array([1, 0, 1], dtype=np.int8)
    assert precision_at_k(uniq, is_pos, peaks, 2) == 0.5
    assert precision_at_k(uniq, is_pos, peaks, 3) == pytest.approx(2 / 3)


def test_matched_group_metrics_expected_rank_under_ties() -> None:
    # one group of 4: founder tied with one control at the top
    gids = np.array(["g"] * 4, dtype=object)
    is_pos = np.array([1, 0, 0, 0], dtype=np.int8)
    peaks = np.array([0.8, 0.8, 0.5, 0.2])
    m = matched_group_metrics(gids, is_pos, peaks)
    assert m["n_groups"] == 1
    assert m["p_rank1"] == pytest.approx(0.5)
    assert m["p_top_half"] == pytest.approx(1.0)
    assert m["chance_p_rank1"] == pytest.approx(0.25)
    # groups without exactly one founder or with <3 members are skipped
    skip = matched_group_metrics(
        np.array(["a", "a"], dtype=object),
        np.array([1, 0], dtype=np.int8),
        np.array([0.9, 0.1]),
    )
    assert skip["n_groups"] == 0


def test_within_month_mean_pr_auc_skips_degenerate_months() -> None:
    months = np.array(["m1"] * 6 + ["m2"] * 6 + ["m3"] * 2, dtype=object)
    y = np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0], dtype=np.int8)
    s = np.array([0.9, 0.1, 0.2, 0.3, 0.1, 0.2, 0.5] + [0.1] * 7)
    result = within_month_mean_pr_auc(months, y, s)
    # m2 has no positives, m3 has <5 rows -> only m1 counts, perfectly ranked
    assert result["n_months"] == 1
    assert result["mean_pr_auc"] == pytest.approx(1.0)


def test_tie_diagnostics_counts_mixed_groups() -> None:
    logins = np.array(list("abcdef"), dtype=object)
    is_pos = np.array([1, 0, 0, 1, 0, 0], dtype=np.int8)
    peaks = np.array([0.5, 0.5, 0.5, 0.4, 0.3, 0.3])
    d = tie_diagnostics(logins, is_pos, peaks)
    assert d["people"] == 6
    assert d["distinct_peak_scores"] == 3
    assert d["people_in_tied_peak_groups"] == 5
    assert d["tie_groups"] == 2
    # only the 0.5 group mixes founder and control; 0.3 is control-only
    assert d["tie_groups_spanning_founder_control"] == 1
    assert d["people_in_founder_control_tie_groups"] == 3
