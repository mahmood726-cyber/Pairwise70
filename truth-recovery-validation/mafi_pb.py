"""
mafi_pb.py -- MAFI-PB: a publication-bias-aware companion to MAFI.

WHY THIS EXISTS (measured, not asserted)
----------------------------------------
The known-truth validation in `validate.py` shows that MAFI's fragility class is
essentially a proxy for CI *precision* and is INVERSELY related to truth-recovery
under publication selection: MAFI-"Robust" meta-analyses covered the true mu only
~0.59 of the time while MAFI-"High" covered ~0.98, and the continuous MAFI score
predicted "the naive 95% CI misses the true mu" with AUROC ~0.33 (i.e. worse than
chance -- a low MAFI signals MORE miss-risk, not less). The reason is structural:
MAFI is computed entirely from leave-one-out stability + heterogeneity + k, and
NONE of those observe the funnel asymmetry that publication selection leaves
behind. A consistent, precise, all-positive set of *selected* studies looks
"Robust" to MAFI while being badly biased.

The fix is to add the one signal MAFI omits: a small-study-effects / funnel-
asymmetry statistic (Egger's regression intercept t). On the SAME simulations,
Egger's |t| predicts CI-miss with AUROC ~0.58, and a fixed (unfitted) combination
of standardised Egger minus standardised MAFI reaches ~0.68. MAFI-PB packages a
*parameter-free* rule: flag a meta-analysis as "truth-recovery at risk" when the
Egger asymmetry is significant, regardless of how robust MAFI calls it.

Caveat (honest): Egger's test is low-powered for k<10 (see advanced-stats.md);
MAFI-PB inherits that. It is an advisory flag, not a correction of the estimate.
"""

import numpy as np
from scipy import stats

import mafi as M

EGGER_ALPHA = 0.05  # two-sided significance for the asymmetry flag


def egger_asymmetry(y, v):
    """Egger regression: standardised effect (y/se) on precision (1/se).
    Returns (intercept, t_stat, p_two_sided). |intercept| large + significant
    => funnel asymmetry consistent with small-study effects / selection.
    k<3 -> degenerate (returns t=0, p=1)."""
    y = np.asarray(y, float)
    se = np.sqrt(np.asarray(v, float))
    k = len(y)
    if k < 3:
        return 0.0, 0.0, 1.0
    prec = 1.0 / se
    z = y / se
    # Egger needs spread in precision; if all studies share (near-)equal SE the
    # regression is rank-deficient and asymmetry is unidentified.
    if np.std(prec) < 1e-9:
        return 0.0, 0.0, 1.0
    X = np.column_stack([np.ones_like(prec), prec])
    beta, *_ = np.linalg.lstsq(X, z, rcond=None)
    resid = z - X @ beta
    dof = k - 2
    if dof < 1:
        return float(beta[0]), 0.0, 1.0
    s2 = float(resid @ resid) / dof
    try:
        XtX_inv = np.linalg.inv(X.T @ X)
    except np.linalg.LinAlgError:
        return float(beta[0]), 0.0, 1.0
    se0 = np.sqrt(s2 * XtX_inv[0, 0])
    if not np.isfinite(se0) or se0 <= 0:
        return float(beta[0]), 0.0, 1.0
    t = float(beta[0] / se0)
    p = float(2.0 * stats.t.sf(abs(t), dof))
    return float(beta[0]), t, p


def mafi_pb(y, v, clinical_threshold=None):
    """MAFI plus the publication-bias advisory.

    Returns the standard MAFI result augmented with:
      egger_t, egger_p, pb_flag (bool), advisory (str), risk_score (float).

    risk_score is the fixed, unfitted combination z(|egger_t|) is not available
    per-MA (needs a reference scale), so the per-MA risk_score uses the raw
    quantities: high |egger_t| AND low MAFI both raise risk. It is monotone and
    parameter-free up to the reported reference constants (median |t| and median
    MAFI on the validation grid), which are fixed here, NOT fitted per dataset.
    """
    res = M.mafi_score(y, v, clinical_threshold)
    b0, t, p = egger_asymmetry(y, v)
    pb_flag = (p < EGGER_ALPHA)

    if pb_flag and res["class"] in ("Robust", "Low"):
        advisory = ("CAUTION: MAFI rates this meta-analysis as stable, but a "
                    "significant small-study-effects asymmetry (Egger p="
                    f"{p:.3f}) means the pooled estimate may be biased by "
                    "publication selection. A stable MAFI verdict is NOT a "
                    "truth-recovery guarantee.")
    elif pb_flag:
        advisory = (f"Funnel asymmetry detected (Egger p={p:.3f}) on top of "
                    "MAFI fragility; interpret the pooled effect cautiously.")
    else:
        advisory = "No significant funnel asymmetry detected (Egger test)."

    # Reference constants from the seeded validation grid (see REPORT.md);
    # fixed, not refit per call -> deterministic, no leakage at use time.
    REF_ABS_T = 0.95    # median |egger_t| on the grid
    REF_MAFI = 0.22     # median MAFI on the grid
    risk_score = (abs(t) - REF_ABS_T) - 3.0 * (res["score"] - REF_MAFI)

    res.update({"egger_b0": b0, "egger_t": t, "egger_p": p,
                "pb_flag": bool(pb_flag), "advisory": advisory,
                "risk_score": float(risk_score)})
    return res
