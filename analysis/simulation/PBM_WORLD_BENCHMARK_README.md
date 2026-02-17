# PBM World Benchmark

This benchmark evaluates `pbm_meta()` against major publication-bias comparators:

- `REML`
- `HKSJ`
- `PETPEESE`
- `TRIMFILL`
- `SWA`
- `TAS`
- `PBM`

## Script

- `analysis/simulation/PBM_World_Benchmark.R`

## Run

```bash
cd /mnt/c/Users/mahmo/Pairwise70
Rscript analysis/simulation/PBM_World_Benchmark.R --n_sim=300 --n_boot_swa=99
```

Publication-grade run:

```bash
Rscript analysis/simulation/PBM_World_Benchmark.R --n_sim=500 --n_boot_swa=49 --min_obs_k=4
```

Fast smoke test:

```bash
Rscript analysis/simulation/PBM_World_Benchmark.R --n_sim=50 --n_boot_swa=39
```

## Outputs

Files are written to `analysis/results/` with timestamp suffix:

- `pbm_world_raw_*.csv`: iteration-level outputs
- `pbm_world_scenario_metrics_*.csv`: per-scenario method metrics
- `pbm_world_rank_overall_*.csv`: global ranking
- `pbm_world_rank_pubbias_*.csv`: ranking in publication-bias scenarios only
- `pbm_world_report_*.md`: concise benchmark report

## Metrics

- Bias
- Absolute bias
- RMSE
- Coverage
- CI width
- Convergence rate
- Type I error
- Power

Composite ranking uses a weighted score over normalized metrics (`world_score`).
The benchmark also reports method applicability (e.g., SWA/TAS require `k >= 10`).
