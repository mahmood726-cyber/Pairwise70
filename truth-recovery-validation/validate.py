"""
validate.py -- The first KNOWN-TRUTH validation of MAFI.

MAFI was validated on 4,424 Cochrane meta-analyses for its *internal* behaviour
(how often its robustness verdict recurs / agrees across the corpus). It has
never been confronted with INJECTED ground truth. This harness does exactly
that, using the truth-recovery DGP: we inject a known (mu, tau^2) and a known
publication-selection mechanism, then ask three honest questions.

  Q1 (coverage-by-class):  Does MAFI's robustness class track truth-recovery?
      i.e. do MAFI-"Robust" meta-analyses cover the TRUE mu more often than
      MAFI-"High" ones, when the only thing that has changed is fragility?

  Q2 (discrimination):     Does the continuous MAFI score predict "the naive DL
      95% CI misses the true mu"?  Reported as AUROC, alongside AUROC of its own
      raw inputs (I^2 and 1/k) so we can see whether MAFI adds discrimination
      *beyond* the penalties baked into it.

  Q3 (type-I capture):     At mu=0 with selection, some pooled CIs are spuriously
      significant (publication bias manufactures an effect). Does MAFI flag those
      false positives as more fragile than the correctly-null ones?

Truth-first: every number printed here is produced from seeded simulation by the
code below; nothing is hand-entered. Run with --reps to trade speed for noise.
"""

import argparse
import json
import time

import numpy as np

import dgp
import mafi as M
import mafi_pb as PB

BASE_SEED = 20260613


def _auroc(scores, labels):
    """AUROC via the Mann-Whitney U identity. labels in {0,1}; higher score
    should predict label==1. Returns NaN if a class is empty."""
    scores = np.asarray(scores, float)
    labels = np.asarray(labels, int)
    pos = scores[labels == 1]
    neg = scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), float)
    ranks[order] = np.arange(1, len(scores) + 1)
    # average ranks for ties
    _, inv, counts = np.unique(scores, return_inverse=True, return_counts=True)
    csum = np.cumsum(counts)
    start = csum - counts
    avg = (start + csum + 1) / 2.0
    ranks = avg[inv]
    r_pos = ranks[labels == 1].sum()
    n_pos, n_neg = len(pos), len(neg)
    u = r_pos - n_pos * (n_pos + 1) / 2.0
    return u / (n_pos * n_neg)


def run(reps, ks, scenarios, tau2, clinical_threshold, verbose=True):
    rng = np.random.default_rng(BASE_SEED)
    rows = []
    for scen in scenarios:
        for k in ks:
            for mu in (0.0, 0.3):
                for _ in range(reps):
                    y, v, info = dgp.generate(mu, tau2, k, scen, rng)
                    res = PB.mafi_pb(y, v, clinical_threshold)
                    ma = res["ma"]
                    covered = ma["ci_lo"] <= mu <= ma["ci_hi"]
                    rows.append({
                        "scen": scen, "k": k, "mu": mu,
                        "mafi": res["score"], "class": res["class"],
                        "I2": ma["I2"], "covered": covered,
                        "significant": ma["significant"],
                        "bias": ma["mu"] - mu,
                        "egger_t": res["egger_t"], "egger_p": res["egger_p"],
                        "pb_flag": res["pb_flag"], "risk": res["risk_score"],
                    })
            if verbose:
                print(f"  done scen={scen:13s} k={k}")
    return rows


CLASS_ORDER = ["Robust", "Low", "Moderate", "High"]


def analyse(rows):
    arr = rows
    out = {}

    # ---- Q1: coverage of true mu by MAFI class (effect-present, mu=0.3) ----
    eff = [r for r in arr if r["mu"] == 0.3]
    q1 = {}
    for c in CLASS_ORDER:
        sub = [r for r in eff if r["class"] == c]
        if sub:
            cov = np.mean([r["covered"] for r in sub])
            q1[c] = {"n": len(sub), "coverage": round(float(cov), 4),
                     "mean_mafi": round(float(np.mean([r["mafi"] for r in sub])), 3),
                     "mean_abs_bias": round(float(np.mean([abs(r["bias"]) for r in sub])), 4)}
    out["Q1_coverage_by_class_mu0.3"] = q1

    # ---- Q2: discrimination -- predict CI-miss (effect-present) ----
    miss = [0 if r["covered"] else 1 for r in eff]
    auc_mafi = _auroc([r["mafi"] for r in eff], miss)
    auc_i2 = _auroc([r["I2"] for r in eff], miss)
    auc_invk = _auroc([1.0 / r["k"] for r in eff], miss)
    out["Q2_auroc_predict_CImiss_mu0.3"] = {
        "MAFI": round(float(auc_mafi), 4),
        "I2_alone": round(float(auc_i2), 4),
        "inv_k_alone": round(float(auc_invk), 4),
        "n": len(eff), "miss_rate": round(float(np.mean(miss)), 4),
    }

    # ---- Q3: type-I capture (mu=0, selection scenarios only) ----
    null_rows = [r for r in arr if r["mu"] == 0.0 and r["scen"] != "none"]
    spurious = [r for r in null_rows if r["significant"]]
    correct = [r for r in null_rows if not r["significant"]]
    def cls_dist(rs):
        n = len(rs)
        return {c: round(sum(1 for r in rs if r["class"] == c) / n, 3)
                for c in CLASS_ORDER} if n else {}
    out["Q3_typeI_capture_mu0_selection"] = {
        "n_null": len(null_rows),
        "spurious_sig_rate": round(len(spurious) / max(1, len(null_rows)), 4),
        "mean_mafi_spurious": round(float(np.mean([r["mafi"] for r in spurious])), 3) if spurious else None,
        "mean_mafi_correct_null": round(float(np.mean([r["mafi"] for r in correct])), 3) if correct else None,
        "class_dist_spurious": cls_dist(spurious),
        "class_dist_correct_null": cls_dist(correct),
        "auroc_mafi_flags_spurious": round(float(_auroc(
            [r["mafi"] for r in null_rows],
            [1 if r["significant"] else 0 for r in null_rows])), 4),
    }

    # ---- Q4: does the publication-bias augmentation (MAFI-PB) recover the
    #      discrimination MAFI alone lacks? (effect-present, mu=0.3) ----
    abs_t = [abs(r["egger_t"]) for r in eff]
    risk = [r["risk"] for r in eff]
    auc_egger = _auroc(abs_t, miss)
    auc_risk = _auroc(risk, miss)
    # Parameter-free flag value: miss-rate among MAFI-stable MAs, split by the
    # Egger pub-bias flag. If the flag works, flagged-stable MAs miss far more.
    stable = [r for r in eff if r["class"] in ("Robust", "Low")]
    st_flag = [r for r in stable if r["pb_flag"]]
    st_noflag = [r for r in stable if not r["pb_flag"]]
    out["Q4_pubbias_augmentation_mu0.3"] = {
        "auroc_MAFI_alone": round(float(auc_mafi), 4),
        "auroc_Egger_abs_t": round(float(auc_egger), 4),
        "auroc_MAFI_PB_risk": round(float(auc_risk), 4),
        "among_MAFI_stable": {
            "n": len(stable),
            "miss_rate_overall": round(float(np.mean([0 if r["covered"] else 1 for r in stable])), 4),
            "n_pb_flagged": len(st_flag),
            "miss_rate_pb_flagged": round(float(np.mean([0 if r["covered"] else 1 for r in st_flag])), 4) if st_flag else None,
            "miss_rate_pb_not_flagged": round(float(np.mean([0 if r["covered"] else 1 for r in st_noflag])), 4) if st_noflag else None,
        },
    }

    # ---- overall coverage by class across everything (context) ----
    allq = {}
    for c in CLASS_ORDER:
        sub = [r for r in arr if r["class"] == c]
        if sub:
            allq[c] = {"n": len(sub),
                       "coverage": round(float(np.mean([r["covered"] for r in sub])), 4)}
    out["coverage_by_class_overall"] = allq
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=150,
                    help="replications per (scenario,k,mu) cell")
    ap.add_argument("--ks", type=int, nargs="+", default=[5, 10, 15, 25])
    ap.add_argument("--tau2", type=float, default=0.05)
    ap.add_argument("--clinical", type=float, default=0.20,
                    help="clinical-significance threshold for CFI")
    ap.add_argument("--out", default="results.json")
    args = ap.parse_args()

    t0 = time.time()
    print(f"[validate] reps={args.reps} ks={args.ks} tau2={args.tau2} "
          f"clinical={args.clinical}")
    rows = run(args.reps, args.ks, dgp.SCENARIOS, args.tau2, args.clinical)
    out = analyse(rows)
    out["_meta"] = {"reps": args.reps, "ks": args.ks, "tau2": args.tau2,
                    "clinical_threshold": args.clinical,
                    "n_total": len(rows), "seconds": round(time.time() - t0, 1),
                    "seed": BASE_SEED}
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    print(f"[validate] {len(rows)} sims in {out['_meta']['seconds']}s "
          f"-> {args.out}")


if __name__ == "__main__":
    main()
