# PBM Multi-Persona Review

Date: 2026-02-13

## Personas

1. Statistical Methodologist
2. Software Reliability Engineer
3. Reproducibility Auditor
4. Clinical Meta-Research End User

## Findings And Fixes

### 1) Metrics logic (high severity)

- Finding: type-I error and power were previously averaged with non-applicable rows, which diluted both metrics.
- Fix: updated `analysis/simulation/PBM_World_Benchmark.R` to compute:
  - `type1_error` only in null-effect scenarios.
  - `power` only in non-null scenarios.

### 2) Applicability vs convergence conflation (high severity)

- Finding: methods with design constraints (e.g., SWA/TAS requiring `k >= 10`) were treated as non-converged instead of non-applicable.
- Fix: added explicit `applicable` tracking and included applicability in ranking (`score_app`).

### 3) Scenario breadth (medium severity)

- Finding: initial benchmark focused heavily on publication-bias mechanisms and lacked explicit outlier and extreme heterogeneity stress tests.
- Fix: expanded grid to 17 scenarios including:
  - `HET_ZERO`, `HET_EXTREME`
  - `OUTLIER_SINGLE`, `OUTLIER_MULTI`
  - `PB_CONT_NULL`, plus prior PB scenarios

### 4) PBM weighting stability (medium severity)

- Finding: inverse-SE weighting in `pbm_meta()` could become dominated by one component if SE was extremely small.
- Fix: added:
  - SE floor (`1e-6`)
  - weight cap relative to median weight
  - small positive floor before normalization

### 5) Traceability (low severity)

- Finding: PBM output lacked an explicit list of active component methods used in the final ensemble.
- Fix: added `component_methods` to `pbm_meta()` return object.

## Residual Risks

- SWA runtime remains high for large simulation runs because of bootstrap.
- Method rankings are sensitive to composite score weights; sensitivity analysis of ranking weights is recommended for manuscript claims.
- External baselines (e.g., full weight-function MLE/Bayesian selection models) are not yet included in this benchmark harness.

## Recommended Next Patches

1. Add optional parallel execution in benchmark loop.
2. Add ranking-weight sensitivity output (`world_score` under multiple weighting schemes).
3. Add external comparator adapters when package availability is confirmed.
