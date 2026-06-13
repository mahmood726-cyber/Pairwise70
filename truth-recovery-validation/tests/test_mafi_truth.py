"""
Tests for the MAFI known-truth validation harness.

Two jobs:
  1. Port correctness -- the Python MAFI reproduces the canonical DerSimonian-
     Laird pooling and the documented MAFI formula on hand-checkable inputs.
  2. Harness sanity / determinism -- the DGP is reproducible and the validation
     produces well-formed, monotone-in-the-right-direction results.
"""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dgp
import mafi as M
import mafi_pb as PB
import validate as V


# ---------------------------------------------------------------------------
# Port correctness
# ---------------------------------------------------------------------------
def test_dl_pooling_matches_hand_computation():
    # 3 studies, known yi / vi -> closed-form DL.
    y = np.array([0.45, 0.32, 0.50])
    se = np.array([0.12, 0.15, 0.10])
    v = se ** 2
    r = M.random_effects_ma(y, v)
    # independent recomputation
    w = 1 / v
    fixed = (w * y).sum() / w.sum()
    Q = (w * (y - fixed) ** 2).sum()
    df = 2
    C = w.sum() - (w * w).sum() / w.sum()
    tau2 = max(0.0, (Q - df) / C)
    rw = 1 / (v + tau2)
    mu = (rw * y).sum() / rw.sum()
    se_mu = np.sqrt(1 / rw.sum())
    assert r["mu"] == pytest.approx(mu, rel=1e-12)
    assert r["se"] == pytest.approx(se_mu, rel=1e-12)
    assert r["ci_lo"] == pytest.approx(mu - 1.96 * se_mu, rel=1e-12)
    assert r["tau2"] == pytest.approx(tau2, rel=1e-12)


def test_mafi_homogeneous_low_fragility():
    # Tight, consistent, strongly-significant studies -> not High fragility.
    y = np.array([0.50, 0.48, 0.52, 0.49, 0.51, 0.50])
    v = np.full(6, 0.02 ** 2)
    res = M.mafi_score(y, v, clinical_threshold=0.20)
    assert res["components"]["DFI"] == 0.0      # no sign flips
    assert res["components"]["SFI"] == 0.0      # stays significant
    assert res["class"] in ("Robust", "Low")


def test_mafi_formula_decomposition():
    # The reported score equals core + het_pen + k_pen (capped at 1).
    y = np.array([0.4, -0.1, 0.6, 0.2, 0.9])
    v = np.array([0.05, 0.08, 0.03, 0.06, 0.04])
    res = M.mafi_score(y, v, clinical_threshold=0.20)
    recon = min(1.0, res["core"] + res["het_pen"] + res["k_pen"])
    assert res["score"] == pytest.approx(recon, rel=1e-12)
    assert 0.0 <= res["score"] <= 1.0


def test_classify_boundaries():
    assert M.classify(0.15) == "Robust"
    assert M.classify(0.1500001) == "Low"
    assert M.classify(0.30) == "Low"
    assert M.classify(0.50) == "Moderate"
    assert M.classify(0.5001) == "High"


# ---------------------------------------------------------------------------
# DGP / harness
# ---------------------------------------------------------------------------
def test_dgp_reproducible():
    r1 = np.random.default_rng(7)
    r2 = np.random.default_rng(7)
    y1, v1, _ = dgp.generate(0.3, 0.05, 12, "step_strong", r1)
    y2, v2, _ = dgp.generate(0.3, 0.05, 12, "step_strong", r2)
    assert np.allclose(y1, y2) and np.allclose(v1, v2)


def test_dgp_returns_k_studies():
    rng = np.random.default_rng(1)
    for scen in dgp.SCENARIOS:
        y, v, info = dgp.generate(0.3, 0.05, 10, scen, rng)
        assert len(y) == 10 and len(v) == 10
        assert np.all(v > 0)


def test_selection_inflates_naive_estimate():
    # Strong positive selection should bias the naive DL mean UP relative to no
    # selection, at the same true mu. (sanity that the DGP actually selects.)
    rng = np.random.default_rng(123)
    mu = 0.3
    none_mu, sel_mu = [], []
    for _ in range(400):
        y, v, _ = dgp.generate(mu, 0.05, 10, "none", rng)
        none_mu.append(M.random_effects_ma(y, v)["mu"])
        y, v, _ = dgp.generate(mu, 0.05, 10, "step_strong", rng)
        sel_mu.append(M.random_effects_ma(y, v)["mu"])
    assert np.mean(sel_mu) > np.mean(none_mu)


def test_auroc_sane():
    # perfect separation -> 1.0 ; reversed -> 0.0
    assert V._auroc([1, 2, 3, 4], [0, 0, 1, 1]) == pytest.approx(1.0)
    assert V._auroc([4, 3, 2, 1], [0, 0, 1, 1]) == pytest.approx(0.0)
    assert 0.4 <= V._auroc(np.random.default_rng(0).random(2000),
                           np.random.default_rng(1).integers(0, 2, 2000)) <= 0.6


def test_egger_detects_asymmetry():
    # Build an asymmetric funnel: small studies (large se) skewed positive.
    se = np.array([0.6, 0.5, 0.55, 0.5, 0.2, 0.15, 0.1])
    y = np.array([1.2, 1.0, 1.1, 0.9, 0.32, 0.30, 0.31])  # small studies inflated
    v = se ** 2
    b0, t, p = PB.egger_asymmetry(y, v)
    assert p < 0.05  # asymmetry flagged
    # symmetric / precise set -> no flag
    se2 = np.full(7, 0.1)
    y2 = np.array([0.30, 0.31, 0.29, 0.30, 0.32, 0.28, 0.30])
    b02, t2, p2 = PB.egger_asymmetry(y2, se2 ** 2)
    assert p2 > 0.05


def test_mafi_pb_advisory_and_fields():
    y = np.array([0.4, 0.42, 0.39, 0.41, 0.40, 0.43])
    v = np.full(6, 0.05 ** 2)
    res = PB.mafi_pb(y, v, clinical_threshold=0.20)
    for key in ("egger_t", "egger_p", "pb_flag", "advisory", "risk_score", "score", "class"):
        assert key in res
    assert isinstance(res["pb_flag"], bool)
    # MAFI-PB never alters the underlying MAFI score (advisory only)
    base = M.mafi_score(y, v, 0.20)
    assert res["score"] == pytest.approx(base["score"], rel=1e-12)


def test_harness_smoke_runs():
    rows = V.run(reps=8, ks=[5, 10], scenarios=dgp.SCENARIOS,
                 tau2=0.05, clinical_threshold=0.20, verbose=False)
    out = V.analyse(rows)
    assert "Q1_coverage_by_class_mu0.3" in out
    assert "Q2_auroc_predict_CImiss_mu0.3" in out
    assert out["Q2_auroc_predict_CImiss_mu0.3"]["n"] > 0
