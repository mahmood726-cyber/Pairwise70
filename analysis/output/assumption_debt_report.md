# Assumption Debt Modeling on Pairwise70 (Cochrane)

Analyzed meta-analyses: **4424**
Fragility rate (any): **39.8%**
High assumption debt (score >= 2): **22.3%**

## Primary Model
Outcome: `fragile_any`
Predictors: `assumption_debt_score + log_k + abs_estimate + tau2_capped`
Per 1-point increase in Assumption Debt Score: OR = **1.15** (95% CI 1.03 to 1.28), p = 0.01169
Assessability sensitivity (score excluding Egger component): OR = **1.18** (95% CI 1.05 to 1.32), p = 0.006878; cluster-robust OR = **1.18** (95% CI 1.03 to 1.34), p = 0.0151
Assessable-only subset (k >= 10): OR = **1.31** (95% CI 1.09 to 1.59), p = 0.004974; cluster-robust OR = **1.31** (95% CI 1.07 to 1.61), p = 0.00843
Binary modified-Poisson RR sensitivity: RR = **1.08** (95% CI 1.02 to 1.15), p = 0.01369; cluster-robust RR = **1.08** (95% CI 1.01 to 1.16), p = 0.02428
Complete-case fragility outcome estimate: OR = **1.13** (95% CI 1.01 to 1.26), p = 0.03704
Complete-case + cluster-robust estimate: OR = **1.13** (95% CI 1.00 to 1.27), p = 0.05722
Direction-fragility outcome sensitivity: OR = **1.17** (95% CI 1.02 to 1.35), p = 0.03001; cluster-robust OR = **1.17** (95% CI 1.00 to 1.37), p = 0.05091
Significance-fragility outcome sensitivity: OR = **1.30** (95% CI 1.12 to 1.50), p = 0.000503; cluster-robust OR = **1.30** (95% CI 1.08 to 1.56), p = 0.005944
Clinical-fragility outcome sensitivity: OR = **1.40** (95% CI 1.24 to 1.58), p = 6.965e-08; cluster-robust OR = **1.40** (95% CI 1.21 to 1.61), p = 3.67e-06
Clinical-fragility outcome modified-Poisson RR sensitivity: RR = **1.25** (95% CI 1.15 to 1.35), p = 1.584e-07; cluster-robust RR = **1.25** (95% CI 1.13 to 1.37), p = 3.849e-06
Clinical-fragility outcome dataset-equal weighting sensitivity: OR = **1.32** (95% CI 1.16 to 1.49), p = 2.631e-05; cluster-robust OR = **1.32** (95% CI 1.08 to 1.60), p = 0.005275
Joint-fragility outcome sensitivity (direction AND significance): OR = **4.06** (95% CI 2.22 to 7.41), p = 5.127e-06; cluster-robust OR = **4.06** (95% CI 2.28 to 7.21), p = 1.82e-06
Joint-fragility outcome modified-Poisson RR sensitivity: RR = **3.76** (95% CI 2.04 to 6.93), p = 2.191e-05; cluster-robust RR = **3.76** (95% CI 2.27 to 6.25), p = 3.047e-07
Joint-fragility outcome dataset-equal weighting sensitivity: OR = **5.45** (95% CI 2.93 to 10.15), p = 9.418e-08; cluster-robust OR = **5.45** (95% CI 2.75 to 10.80), p = 1.159e-06
Composite-fragility-count outcome sensitivity (quasipoisson RR): RR = **1.16** (95% CI 1.10 to 1.22), p = 5.33e-08; cluster-robust RR = **1.16** (95% CI 1.09 to 1.23), p = 1.057e-06
Cluster-robust (by dataset) estimate: OR = **1.15** (95% CI 1.02 to 1.30), p = 0.02117
Measure-adjusted model estimate: OR = **1.15** (95% CI 1.03 to 1.28), p = 0.0156
Measure-adjusted + cluster-robust estimate: OR = **1.15** (95% CI 1.02 to 1.29), p = 0.0272
Dataset-equal weighting estimate: OR = **1.24** (95% CI 1.11 to 1.39), p = 0.000207; cluster-robust OR = **1.24** (95% CI 1.06 to 1.46), p = 0.007387
Measure interaction test (score x measure): LR p = 0.3039; clustered measure-specific score ORs are exported for audit
Within-between decomposition: within-dataset OR = **1.09** (95% CI 0.96 to 1.22), p = 0.1749; between-dataset OR = **1.35** (95% CI 1.06 to 1.73), p = 0.01637
Dataset fixed-effects LPM sensitivity: RD per +1 score = **0.023** (95% CI -0.002 to 0.048), p = 0.07456
Dataset-level aggregate model (n=474 datasets): OR per +1 mean score = **1.27** (95% CI 1.03 to 1.58), p = 0.0281
Leave-one-measure-family-out sensitivity: clustered OR median = **1.16** (2.5% to 97.5%: 1.12 to 1.31; min-max: 1.12 to 1.31) across 3 exclusions
Large-review dominance sensitivity (exclude top decile dataset sizes; 54 datasets removed, retain 67.3% meta-analyses): clustered OR = **1.20** (95% CI 1.03 to 1.39), p = 0.01796
Cumulative large-review removal (top 5/10/20/30/40 datasets): clustered OR median = **1.19** (2.5% to 97.5%: 1.14 to 1.22; range: 1.14 to 1.22), retained-meta range 73.5% to 93.6%
Information-adequacy strata: k < 10 clustered OR = **1.63** (95% CI 1.33 to 2.00), p = 2.313e-06; k >= 10 clustered OR = **1.25** (95% CI 1.04 to 1.51), p = 0.01795; beta-difference test p = 0.06308
One-analysis-per-dataset bootstrap sensitivity: OR median = **1.25** (95% empirical interval 0.92 to 1.77), successful fits = 400/400
Dataset-level bootstrap sensitivity (300 reps): OR median = **1.15** (95% empirical interval 1.04 to 1.30), successful fits = 300/300
Leave-one-dataset-out sensitivity (n=474 datasets): OR median = **1.15** (2.5% to 97.5%: 1.14 to 1.16; min-max: 1.14 to 1.17)
Functional-form test (score linear vs categorical): LR p = 7.684e-05 (df=2)
Threshold sensitivity (k cutoffs 7/10/15; I2 cutoffs 40/50/60): clustered OR median = **1.25** (2.5% to 97.5%: 1.11 to 1.40; min-max: 1.11 to 1.42) across 9 models
Dominance-threshold sensitivity (max weight cutoffs 0.40/0.50/0.60 in score): clustered OR median = **1.15** (2.5% to 97.5%: 1.13 to 1.20; min-max: 1.13 to 1.20) across 3 models
Egger-threshold sensitivity (small-study cutoffs p<0.05/0.10/0.20 in score): clustered OR median = **1.15** (2.5% to 97.5%: 1.14 to 1.15; min-max: 1.14 to 1.15) across 3 models
Tau2-cap sensitivity (cap quantiles 0.95/0.99/1.00): clustered OR median = **1.15** (2.5% to 97.5%: 1.09 to 1.34; min-max: 1.09 to 1.35) across 3 models
High-leverage exclusion sensitivity (retain 93.2%; exclude max_weight_share >= 0.70 and tau2 > p99=2.868): clustered OR = **1.15** (95% CI 1.01 to 1.30), p = 0.03084
Effect-size-tail exclusion sensitivity (exclude abs_estimate > p99=1.881; retain 99.0%): clustered OR = **1.17** (95% CI 1.04 to 1.32), p = 0.009415
Non-sparse-events subset sensitivity (n=770; 17.4% of analyses): clustered OR = **1.28** (95% CI 0.96 to 1.71), p = 0.09668
Heterogeneity-present subset sensitivity (I2 > 0; n=1724; 39.0%): clustered OR = **0.95** (95% CI 0.81 to 1.12), p = 0.566
Within-dataset permutation sensitivity (300 reps): observed OR = 1.15; permutation beta mean = 0.0793 (95% perm interval 0.0021 to 0.1649); empirical two-sided p = 0.0800
Primary model performance: apparent AUC = 0.681, 5-fold CV AUC = 0.679, grouped 5-fold CV AUC = 0.680, Brier = 0.216, in-sample calibration (intercept=0.000, slope=1.000), 5-fold CV calibration (intercept=0.000, slope=0.983), grouped 5-fold CV calibration (intercept=-0.001, slope=0.978)
Component model (without log_k) for sparse_k: OR = **1.89** (95% CI 1.64 to 2.17), p = 1.198e-18; cluster-robust OR = **1.89** (95% CI 1.59 to 2.25), p = 8.436e-13

## Assumption Debt Components (prevalence)
- sparse_k (k < 10): 53.8%
- high_heterogeneity (I2 >= 50): 16.4%
- small_study_signal (Egger p < 0.10 with k >= 10): 12.1%
- dominance_signal (max weight >= 50%): 16.8%
- sparse_events_signal (>0 sparse-event flags): 82.6%
- predictor correlation sparse_k vs log_k: -0.80
- analyses with k >= 10 (small-study assessable): 46.2%
- small-study signal prevalence among k >= 10: 26.2%

## Interpretation
Higher assumption debt is associated with higher fragility risk in real Cochrane pairwise meta-analyses.
This quantifies the proposed underdiagnosed issue: assumptions are often strained in ways that predict unstable conclusions.
The association remains directionally consistent under cluster-robust and one-analysis-per-dataset sensitivity analyses.
Within-between decomposition shows a positive but attenuated within-dataset association (imprecise) and a stronger between-dataset association, indicating potential contextual clustering while preserving directional coherence.
Dataset fixed-effects sensitivity reaches the same directional conclusion on the risk-difference scale.
Dataset-level aggregate modeling is also directionally concordant, supporting cross-review consistency while not replacing individual-analysis inference.
The inverse sparse_k sign in the full component model is attributable to collinearity with log_k and reverses in the no-log_k sensitivity model.
Model diagnostics indicate moderate discrimination with limited apparent optimism and acceptable out-of-fold calibration.
Functional-form testing indicates departures from strict linearity of the score effect.
