"""
mafi.py -- Faithful Python port of the published MAFI (Meta-Analysis Fragility
Index) computation, ported line-for-line from MAFI-Calculator.html so the
known-truth validation scores the *same* index the manuscript ships.

Pipeline (continuous effect-measure path, nullValue = 0):
  1. DerSimonian-Laird random-effects pooling (inverse-variance), Wald 95% CI
     (+/- 1.96 SE), z-test p-value, I^2 from Q.
  2. Leave-one-out refits -> Direction / Significance / Clinical fragility
     counts, max |effect change|, max relative CI-width change.
  3. MAFI = 0.30*DFI_rate + 0.25*SFI_rate + 0.20*CFI_rate
            + 0.15*min(1,maxEffectChange) + 0.10*min(1,maxRelCIchange)   (core)
          + (I^2/100)*0.20            (heterogeneity penalty)
          + max(0,(1-k/20))*0.30      (small-sample penalty),  capped at 1.

Classification:  <=0.15 Robust | <=0.30 Low | <=0.50 Moderate | else High.

Weights are normalised exactly as the calculator does (here they already sum to
1, so normalisation is the identity, but we keep the step for parity).
"""

import numpy as np
from scipy import stats

_Z = 1.96  # the calculator uses the literal 1.96, not norm.ppf(0.975)


def random_effects_ma(y, v):
    """DerSimonian-Laird RE meta-analysis. Mirrors runRandomEffectsMA()."""
    y = np.asarray(y, float)
    v = np.asarray(v, float)
    k = len(y)
    w = 1.0 / v
    sumW = w.sum()
    fixed = (w * y).sum() / sumW
    Q = (w * (y - fixed) ** 2).sum()
    df = k - 1
    C = sumW - (w * w).sum() / sumW
    tau2 = max(0.0, (Q - df) / C) if C > 0 else 0.0
    I2 = max(0.0, (Q - df) / Q * 100.0) if Q > 0 else 0.0
    rw = 1.0 / (v + tau2)
    sumRE = rw.sum()
    mu = (rw * y).sum() / sumRE
    se = np.sqrt(1.0 / sumRE)
    z = mu / se
    p = 2.0 * (1.0 - stats.norm.cdf(abs(z)))
    return {
        "k": k, "mu": mu, "se": se,
        "ci_lo": mu - _Z * se, "ci_hi": mu + _Z * se,
        "z": z, "p": p, "Q": Q, "I2": I2, "tau2": tau2,
        "significant": p < 0.05,
    }


def _loo(y, v, full, clinical_threshold):
    """Leave-one-out fragility components. Mirrors leaveOneOutAnalysis()."""
    k = len(y)
    orig_effect = full["mu"]
    orig_sig = full["significant"]
    orig_clin = (abs(orig_effect) >= clinical_threshold
                 if clinical_threshold else False)
    orig_ci_w = full["ci_hi"] - full["ci_lo"]

    dir_changes = sig_changes = clin_changes = 0
    max_eff = 0.0
    max_ci = 0.0
    for i in range(k):
        mask = np.arange(k) != i
        r = random_effects_ma(y[mask], v[mask])
        # direction flip (sign relative to null = 0)
        if (r["mu"] >= 0) != (orig_effect >= 0):
            dir_changes += 1
        if r["significant"] != orig_sig:
            sig_changes += 1
        if clinical_threshold:
            looc = abs(r["mu"]) >= clinical_threshold
            if looc != orig_clin:
                clin_changes += 1
        max_eff = max(max_eff, abs(r["mu"] - orig_effect))
        loo_ci_w = r["ci_hi"] - r["ci_lo"]
        if orig_ci_w > 0:
            max_ci = max(max_ci, abs(loo_ci_w - orig_ci_w) / orig_ci_w)
    return {"DFI": dir_changes, "SFI": sig_changes, "CFI": clin_changes,
            "maxEffectChange": max_eff, "maxCIChange": max_ci}


_WEIGHTS = {"direction": 0.30, "significance": 0.25,
            "clinical": 0.20, "effect": 0.15, "ci": 0.10}


def mafi_score(y, v, clinical_threshold=None):
    """Full MAFI for one meta-analysis. Returns dict with score, class, parts."""
    full = random_effects_ma(y, v)
    frag = _loo(y, v, full, clinical_threshold)
    k = full["k"]

    dfi = frag["DFI"] / k
    sfi = frag["SFI"] / k
    cfi = frag["CFI"] / k
    eff = min(1.0, frag["maxEffectChange"])
    ci = min(1.0, frag["maxCIChange"])

    tw = sum(_WEIGHTS.values())
    w = {kk: vv / tw for kk, vv in _WEIGHTS.items()}
    core = (w["direction"] * dfi + w["significance"] * sfi
            + w["clinical"] * cfi + w["effect"] * eff + w["ci"] * ci)

    het_pen = (full["I2"] / 100.0) * 0.20
    k_pen = max(0.0, (1 - k / 20.0) * 0.30)
    score = min(1.0, core + het_pen + k_pen)

    return {
        "score": score, "class": classify(score),
        "core": core, "het_pen": het_pen, "k_pen": k_pen,
        "components": {"DFI": dfi, "SFI": sfi, "CFI": cfi,
                       "effect": eff, "ci": ci},
        "ma": full,
    }


def classify(score):
    if score <= 0.15:
        return "Robust"
    if score <= 0.30:
        return "Low"
    if score <= 0.50:
        return "Moderate"
    return "High"
