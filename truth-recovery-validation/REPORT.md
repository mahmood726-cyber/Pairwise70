# MAFI under the Truth-Recovery Yardstick

**The first known-truth validation of the Meta-Analysis Fragility Index.**

MAFI was validated on 4,424 Cochrane meta-analyses for its *internal* behaviour
(corpus-level AUC 0.687 for predicting its own robustness recurrence). It had
never been confronted with **injected ground truth**. This module does that,
reusing the truth-recovery simulation harness developed for the allmeta
portfolio (a known-truth DGP that layers a parameterised publication-selection
mechanism on top of a known `mu` and `tau^2`, then measures how often each
method's interval covers the **true** effect).

> Truth-first: every number below is produced by `validate.py` from seeded
> simulation (`seed=20260613`). Reproduce with
> `python validate.py --reps 200`. Nothing is hand-entered.

**Grid:** `mu in {0.0, 0.3}`, `tau2 = 0.05`, `k in {5,10,15,25}`, 5 selection
scenarios (`none`, `step_weak/strong`, `copas_weak/strong`), 200 reps/cell
(8,000 simulated meta-analyses). Continuous effect measure; clinical
threshold 0.20.

---

## Headline finding (honest, and it is a *negative* one for MAFI)

**A "Robust" MAFI verdict does not mean the pooled effect is near the truth.
Under publication selection, MAFI's robustness class is INVERSELY related to
truth-recovery.**

### Q1 — coverage of the true `mu` by MAFI class (effect present, `mu=0.3`)

| MAFI class | n | mean MAFI | coverage of true mu | mean \|bias\| |
|---|---|---|---|---|
| Robust   | 1037 | 0.107 | **0.582** | 0.107 |
| Low      | 1740 | 0.222 | 0.673 | 0.120 |
| Moderate |  972 | 0.375 | 0.872 | 0.134 |
| High     |  251 | 0.564 | **0.992** | 0.110 |

Coverage rises **monotonically with fragility**. MAFI-"Robust" meta-analyses
cover the true effect only **58%** of the time (nominal 95%); MAFI-"High" cover
**99%**. Crucially, mean `|bias|` is roughly **flat** across classes (0.11–0.13):
the classes do not differ in accuracy, they differ in CI **width**. MAFI is
effectively a proxy for interval precision — and narrow intervals (which MAFI
calls "Robust") miss a biased truth more often.

### Q2 — does the continuous MAFI score predict "the 95% CI misses true mu"?

AUROC (higher MAFI should predict more miss, if MAFI tracked truth-risk):

| Predictor | AUROC |
|---|---|
| **MAFI score** | **0.316** |
| I² alone | 0.344 |
| 1/k alone | 0.405 |

All **below 0.5** — MAFI is *anti-predictive*: a **low** MAFI signals **more**
miss-risk, not less. (`miss_rate = 0.282` overall at `mu=0.3`.)

### Q3 — does MAFI catch publication-bias-induced false positives? (`mu=0`)

With a true null and selection, 31.8% of pooled CIs are **spuriously
significant**. MAFI does **not** flag them: mean MAFI is *lower* for the spurious
positives (0.261) than for the correctly-null MAs (0.309), and AUROC of MAFI for
flagging spurious significance is **0.40** (worse than chance).

**Why.** MAFI is computed entirely from leave-one-out stability + heterogeneity
+ k. None of those observe the funnel asymmetry that publication selection
leaves behind. A set of *selected* studies that is consistent, precise and
all-positive looks maximally "Robust" to MAFI while being badly biased.

---

## The measured improvement — MAFI-PB (`mafi_pb.py`)

The fix is the one signal MAFI omits: a small-study-effects / funnel-asymmetry
statistic (Egger's regression intercept t). On the **same** simulations:

### Q4 — recovering the discrimination MAFI lacks (effect present, `mu=0.3`)

| Predictor of CI-miss | AUROC |
|---|---|
| MAFI alone | 0.316 |
| Egger \|t\| alone | **0.594** |
| MAFI-PB risk score (fixed Egger − MAFI combo) | **0.661** |

And as a **parameter-free advisory flag** — among the meta-analyses MAFI calls
*stable* (Robust/Low):

| Subset | n | CI-miss rate |
|---|---|---|
| all MAFI-stable | 2777 | 0.361 |
| …with Egger pub-bias flag (p<0.05) | 342 | **0.506** |
| …without the flag | 2435 | 0.341 |

The flag does real work: it pulls out, from the meta-analyses MAFI declares
trustworthy, a subset whose pooled CI misses the truth **half** the time.

`mafi_pb.py` ships this as an **advisory only** — it never alters the MAFI score
(see `test_mafi_pb_advisory_and_fields`). It adds `egger_t`, `egger_p`,
`pb_flag`, `risk_score`, and a plain-language `advisory` string.

**Caveat (honest):** Egger's test is low-powered for `k<10`
(`advanced-stats.md`); MAFI-PB inherits that, so the flag is most reliable for
larger meta-analyses. It detects asymmetry; it does not correct the estimate.

---

## What transferred, and what did not

- **Transferred (as a diagnostic):** the known-truth simulation harness — "the
  honest yardstick that ranks methods" — applied cleanly and revealed a genuine
  limitation of MAFI that its 4,424-MA internal validation could not surface.
- **Transferred (as an improvement):** adding a selection signal (Egger) lifts
  CI-miss discrimination from AUROC 0.32 → 0.66, a measured gain.
- **Did NOT transfer:** the NPE / normalizing-flow estimator and conformal/SBC
  calibration are estimators of `mu`; MAFI is not an estimator, so those pieces
  do not apply here. Partial-identification bounds are also out of scope for a
  fragility *index*. Only the harness + the joint heterogeneity-plus-selection
  DGP were the relevant learnings, and those are what we used.

## Files

| File | Role |
|---|---|
| `dgp.py` | standalone known-truth DGP (joint `tau^2` + selection), vendored from the allmeta truth-recovery bench |
| `mafi.py` | faithful Python port of `MAFI-Calculator.html` (DL pooling + LOO fragility + MAFI formula) |
| `mafi_pb.py` | MAFI-PB publication-bias advisory (Egger asymmetry, flag, risk score) |
| `validate.py` | the harness: Q1–Q4 measured against injected truth |
| `tests/test_mafi_truth.py` | port-correctness, DGP reproducibility, AUROC sanity, smoke |
| `results.json` | the seeded run reproduced in this report |
