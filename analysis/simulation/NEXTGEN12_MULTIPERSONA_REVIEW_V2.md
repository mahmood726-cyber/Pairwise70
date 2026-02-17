# NextGen12 Multi-Persona Review + Improvement Pass V2

Date: 2026-02-17
Scope: `analysis/simulation/NEXTGEN12_RealData_Benchmark.R`

## Personas
1. Statistical Methodologist
2. Reliability Engineer
3. Reproducibility Auditor
4. Decision Scientist

## New Findings

### High
- Rank ordering lacked uncertainty quantification.
  - Risk: unstable rankings being interpreted as true performance differences.
  - Fix: added bootstrap rank uncertainty (`rank_sd`, `rank_p10`, `rank_p90`).

### Medium
- Composite score still vulnerable to noisy point estimates if rank uncertainty is ignored.
  - Risk: brittle promotion decisions.
  - Fix: added `score_rank_uncertainty` to world score.

- Bootstrap completeness handling could propagate NA/Inf values.
  - Risk: distorted uncertainty estimates.
  - Fix: robust column fill strategy for sparse bootstrap method presence.

## Improvement Pass V2 Implemented
- New CLI arg: `n_rank_boot` (default 200, min 50).
- New outputs in summary:
  - `rank_sd`
  - `rank_p10`
  - `rank_p90`
- Updated world score to include uncertainty penalty:
  - `0.22*shift_reml + 0.22*shift_consensus + 0.18*se + 0.13*flip + 0.13*convergence + 0.12*rank_uncertainty`

## Residual Risks
- Real-data benchmark still lacks causal ground truth; simulation calibration remains mandatory.
- Some methods with lower applicability (`CPC`, `HGAM`, `MTLE`) need targeted calibration or gating.

## Promotion Gate (recommended)
- Promote only methods with:
  - `convergence >= 0.98`
  - `rank_p90 <= 8`
  - acceptable type-I/coverage in simulation pass.
