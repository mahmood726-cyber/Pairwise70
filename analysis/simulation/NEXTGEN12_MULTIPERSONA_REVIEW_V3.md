# NextGen12 Multi-Persona Review + Improvement Pass V3

Date: 2026-02-17
Scope: `analysis/simulation/NEXTGEN12_RealData_Benchmark.R`

## Personas
1. Statistical Methodologist
2. Reliability Engineer
3. Reproducibility Auditor
4. Decision Scientist

## Findings (V3)

### High
- Bootstrap rank uncertainty implementation did not correctly preserve multiplicity of resampled datasets (`%in%` used set-membership semantics).
  - Risk: underestimated rank variance and overconfident ranking claims.
  - Fix: replaced with multiplicity-preserving bootstrap assembly and robust missing-method fallback logic.

### Medium
- Promotion logic lacked explicit uncertainty penalty in final ranking objective.
  - Risk: methods with unstable ranking could still appear competitive.
  - Fix: added `score_rank_uncertainty` term and recalibrated weight mix in `world_score`.

### Medium
- Method failure handling existed but lacked a clear decision-level link.
  - Risk: weak methods could pass on primary score despite repeated fail patterns.
  - Fix: retained method failure CSV output and surfaced rank-uncertainty diagnostics (`rank_sd`, `rank_p10`, `rank_p90`) for gatekeeping.

## Improvement Pass V3 Implemented
- Added/verified uncertainty-aware fields in summary:
  - `rank_sd`, `rank_p10`, `rank_p90`
- Updated runtime controls output to include `n_rank_boot`.
- Strengthened bootstrap fill strategy for sparse method presence.

## Residual Risks
- Real-data benchmark still lacks ground-truth correctness metrics (bias/coverage/power) available only in simulation.
- Methods with low applicability (`CPC`, `HGAM`, `MTLE`) remain experimental and should stay non-promoted.

## Recommended Promotion Gate
- Require all of:
  - `convergence >= 0.98`
  - `rank_p90 <= 10`
  - `rank_sd <= 1.0`
  - simulation pass on coverage/type-I error.
