"""
dgp.py -- Known-truth data-generating process for meta-analyses, with a
parameterised PUBLICATION-SELECTION mechanism layered on top of a known
(mu, tau^2).

This is a standalone adaptation of the truth-recovery yardstick built for the
allmeta portfolio (F:\\allmeta, branch truth-recovery-unified-estimator,
truth-recovery-bench/dgp.py). It is vendored here verbatim-in-spirit so the
MAFI validation has NO external runtime dependency.

A "meta-analysis" is the set of PUBLISHED studies an analyst observes. Studies
are drawn from the true random-effects model and a selection rule decides which
get published; we oversample until the target observed count k is reached. So k
is the number of *published* studies (what a reviewer sees) while the true mu is
the unconditional population mean any honest method must recover.

Mechanisms
----------
none         : no selection (pure heterogeneity baseline)
step_weak    : Vevea-Hedges one-sided p-value step weights, mild
step_strong  : same, severe
copas_weak   : Copas latent-variable selection, mild effect/selection corr
copas_strong : same, strong corr

Everything is driven by an explicit numpy Generator -> fully reproducible.
"""

import numpy as np
from scipy import stats

# One-sided p-value cutpoints (favouring large POSITIVE effects) and the
# publication weight applied to each interval [0,c1), [c1,c2), [c2,1].
_STEP_CUTS = np.array([0.025, 0.05])
_STEP_WEIGHTS = {
    "weak":   np.array([1.0, 0.75, 0.55]),
    "strong": np.array([1.0, 0.35, 0.10]),
}
# Copas latent selection z = g0 + g1/se + d ; publish if z>0.
_COPAS = {
    "weak":   {"g0": -0.10, "g1": 0.12, "rho": 0.50},
    "strong": {"g0": -0.20, "g1": 0.12, "rho": 0.90},
}

SCENARIOS = ["none", "step_weak", "step_strong", "copas_weak", "copas_strong"]


def _draw_se(rng, k, se_lo, se_hi):
    """Log-uniform standard errors -> realistic spread of study precisions."""
    return np.exp(rng.uniform(np.log(se_lo), np.log(se_hi), size=k))


def _step_weight(p_one, cuts, weights):
    idx = np.searchsorted(cuts, p_one, side="right")
    return weights[idx]


def generate(mu, tau2, k, scenario, rng, se_lo=0.10, se_hi=0.70,
             max_factor=400):
    """Return (y, v, info) for one published meta-analysis of observed size k.

    y    : observed effect sizes (length k)
    v    : their sampling variances (se**2)
    info : dict(n_generated, k, sel_frac, degenerate)
    """
    if scenario == "none":
        se = _draw_se(rng, k, se_lo, se_hi)
        theta = rng.normal(mu, np.sqrt(tau2), size=k)
        y = rng.normal(theta, se)
        return y, se ** 2, {"n_generated": k, "k": k, "sel_frac": 1.0,
                            "degenerate": False}

    kind = "weak" if scenario.endswith("weak") else "strong"
    is_step = scenario.startswith("step")
    if is_step:
        weights = _STEP_WEIGHTS[kind]
    else:
        cp = _COPAS[kind]

    keep_y, keep_se = [], []
    n_examined = 0
    cap = max_factor * k
    while len(keep_y) < k and n_examined < cap:
        b = max(k, 64)
        se = _draw_se(rng, b, se_lo, se_hi)
        theta = rng.normal(mu, np.sqrt(tau2), size=b)
        eps = rng.normal(0.0, 1.0, size=b)
        y = theta + se * eps
        if is_step:
            p_one = stats.norm.sf(y / se)
            w = _step_weight(p_one, _STEP_CUTS, weights)
            published = rng.random(b) < w
        else:
            d = cp["rho"] * eps + np.sqrt(1 - cp["rho"] ** 2) * rng.normal(0, 1, size=b)
            z = cp["g0"] + cp["g1"] / se + d
            published = z > 0
        n_examined += b
        for yi, sei, pub in zip(y, se, published):
            if pub:
                keep_y.append(yi)
                keep_se.append(sei)
                if len(keep_y) >= k:
                    break

    degenerate = len(keep_y) < k
    if degenerate:
        # Top up with unselected draws so downstream code always sees k studies.
        need = k - len(keep_y)
        se = _draw_se(rng, need, se_lo, se_hi)
        theta = rng.normal(mu, np.sqrt(tau2), size=need)
        y = rng.normal(theta, se)
        keep_y.extend(list(y))
        keep_se.extend(list(se))

    yy = np.array(keep_y[:k])
    ss = np.array(keep_se[:k])
    sel_frac = k / max(1, n_examined)
    return yy, ss ** 2, {"n_generated": n_examined, "k": k,
                         "sel_frac": sel_frac, "degenerate": degenerate}
