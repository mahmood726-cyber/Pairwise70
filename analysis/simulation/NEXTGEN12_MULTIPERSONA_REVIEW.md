# NextGen12 Multi-Persona Review + Improvement Pass

Date: 2026-02-17
Scope: `analysis/simulation/NEXTGEN12_RealData_Benchmark.R`

## Personas
1. Statistical Methodologist
2. Reliability Engineer
3. Reproducibility Auditor
4. Research Operations Lead

## Findings (ordered by severity)

### High
- Over-anchoring to REML in score definition could bias rankings toward REML-like methods.
  - Risk: suppresses genuinely better alternatives that differ from REML.
  - Fix applied: added `mean_abs_shift_vs_consensus` and integrated into `world_score`.

- Missing per-method failure diagnostics.
  - Risk: methods silently fail and appear weak without attribution.
  - Fix applied: added `method_fail` capture and `nextgen12_realdata_method_failures_*.csv` output.

### Medium
- Inconsistent timeout guards across methods.
  - Risk: sporadic hangs and run-to-run instability.
  - Fix applied: unified method execution via `run_with_timeout()` helper.

- HGAM spline warnings due low `df` settings.
  - Risk: warning noise and brittle behavior in small-k settings.
  - Fix applied: enforce spline `df >= 3` and wrap fit in `suppressWarnings()`.

### Low
- Composite score lacked a consensus-stability dimension.
  - Risk: ranking overweights single baseline proximity.
  - Fix applied: new `score_consensus` term in weighted score.

## Improvement Pass Implemented
- Added helper: `run_with_timeout(expr, timeout_sec)`.
- Added outputs:
  - method-level failures CSV
  - consensus shift metric
- Updated scoring:
  - `world_score = 0.25*shift_reml + 0.25*shift_consensus + 0.20*se + 0.15*flip + 0.15*convergence`

## Residual Risks
- Real-data benchmark still lacks ground-truth bias/coverage metrics.
- Some methods (e.g., `CPC`, `HGAM`) show lower robustness on current runtime settings; they need calibration before promotion.
- Current method implementations are prototype-level and should not yet be exported as stable package APIs.

## Next Priority Actions
1. Add simulation calibration pass for type-I error, coverage, and power for all 12 methods.
2. Add ablation analysis for `FATIHA` component weights and thresholds.
3. Promote only methods passing calibration gates to package-level exports.
