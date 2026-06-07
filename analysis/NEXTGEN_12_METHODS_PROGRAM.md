# NextGen-12 Meta-Analysis Method Program

## Goal
Build 12 new method families across pooling, heterogeneity, and meta-regression and evaluate them under a strict benchmark protocol against current baselines (`REML`, `HKSJ`, `PETPEESE`, `TRIMFILL`, `SWA`, `TAS`, `PBM`, `WRD`, `RBM`, `AEM`).

No single method is expected to win every scenario. Success criterion is dominance in weighted world-score plus stability under sensitivity analyses.

## Method Families (12)

### Pooling / Robust Estimation
1. `QSE` (Quantile Shrinkage Ensemble)
2. `CRT` (Causal Residual Trimming)
3. `SAFE` (Selective Adaptive Fusion Estimator)
4. `CPC` (Cross-Phenotype Consensus Pooling)

### Heterogeneity Modeling
5. `LTH` (Local-Tau Heterogeneity)
6. `DTM` (Distributional Tau Mixture)
7. `AWH` (Adaptive Winsorized Heterogeneity)
8. `BSC` (Bayesian Stability Calibration)

### Meta-Regression / Moderation
9. `RMR` (Robust Moderator Regression)
10. `MRSTACK` (Stacked Nonlinear Meta-Regression)
11. `HGAM` (Heterogeneity GAM Meta-Regression)
12. `MTLE` (Multi-Task Learning Effects)

## Benchmarking Contract
- Primary metrics: absolute bias, RMSE, 95% coverage, type-I error, power.
- Secondary metrics: CI width, convergence, applicability rate, runtime.
- Ranking: weighted world-score with sensitivity sweeps over weights.
- Stress scenarios:
  - null / non-null
  - small-k and large-k
  - high and extreme heterogeneity
  - single and multi-outlier contamination
  - step, one-sided, continuous publication bias
  - moderator misspecification for meta-regression

## Development Phases

### Phase 1 (completed)
- Build executable scaffold and method registry.
- Implement first 3 prototypes: `QSE`, `LTH`, `RMR`.
- Add smoke benchmark over synthetic scenarios.

### Phase 2 (completed)
- Implement remaining 9 methods:
  `CRT`, `SAFE`, `CPC`, `DTM`, `AWH`, `BSC`, `MRSTACK`, `HGAM`, `MTLE`.
- Add real-data benchmark harness on Pairwise70 datasets.
- Add composite ranking score (`world_score`) with convergence and sign-stability penalties.

### Phase 3
- Full world benchmark (`n_sim >= 500`) with ranking sensitivity.
- Lock top candidates and produce manuscript-grade outputs.

## Decision Rules
- Promote method if:
  - world-score improves by >= 5% vs PBM, and
  - no catastrophic failure in null/type-I scenarios.
- Reject method if:
  - type-I error inflation > 0.08 in null scenarios, or
  - applicability < 0.70 without strong compensating gains.

## Immediate Next Iteration
1. Add simulation calibration for type-I error / coverage / power for all 12 methods.
2. Run ablations of `FATIHA` component weights and trimming thresholds.
3. Promote top-performing methods into package exports (`R/advanced_pooling_v4.R`) after calibration pass.
