# Results: Assumption Debt Model (Cochrane Pairwise70)

## 1. Cohort and Assumption Debt Profile
We analyzed 4,424 pairwise meta-analyses from the Pairwise70 Cochrane dataset. Overall fragility (direction-fragile or significance-fragile) was 39.8%. Direction fragility was 26.7%, and significance fragility was 15.0% (both among 4,316 analyses with non-missing fragility flags). Median number of studies per meta-analysis was 9 (mean 18.2), and median I2 was 0%.

Assumption debt components were frequent: 53.8% had fewer than 10 studies, 16.4% had high heterogeneity (I2 >= 50%), 12.1% showed an Egger small-study signal (p < 0.10 with k >= 10), and 16.8% were dominated by a single study (max weight >= 50%). High assumption debt (score >= 2 of 4 components) occurred in 22.3% of meta-analyses.

## 2. Primary Association With Fragility
In the primary multivariable logistic model (`fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped`), each one-point increase in Assumption Debt Score was associated with higher odds of fragility (OR 1.15, 95% CI 1.03 to 1.28, p = 0.0117).

To address within-review dependence (multiple meta-analyses per Cochrane dataset), we computed cluster-robust standard errors by dataset. The association persisted (cluster-robust OR 1.15, 95% CI 1.02 to 1.30, p = 0.0212).

Because ORs can overstate practical contrast when outcomes are common, we added a binary modified-Poisson sensitivity for `fragile_any` to estimate relative risk directly. The association remained positive (RR 1.08, 95% CI 1.02 to 1.15, p = 0.0137), including under clustered inference (cluster-robust RR 1.08, 95% CI 1.01 to 1.16, p = 0.0243).

Because the Egger-based small-study component is only assessable when `k >= 10`, we added an assessability sensitivity score excluding the Egger component (`sparse_k + high_heterogeneity + dominance_signal`). The association remained positive (OR 1.18, 95% CI 1.05 to 1.32, p = 0.0069), including under clustered inference (cluster-robust OR 1.18, 95% CI 1.03 to 1.34, p = 0.0151).

To assess potential bias from coding missing fragility flags as non-fragile, we fit complete-case outcome models. The score association remained positive (OR 1.13, 95% CI 1.01 to 1.26; cluster-robust OR 1.13, 95% CI 1.00 to 1.27).

In outcome-specific sensitivity models, the score effect remained positive for both canonical fragility components: direction fragility (cluster-robust OR 1.17, 95% CI 1.00 to 1.37, p = 0.0509) and significance fragility (cluster-robust OR 1.30, 95% CI 1.08 to 1.56, p = 0.0059). For clinical fragility, the association was also positive and stronger (cluster-robust OR 1.40, 95% CI 1.21 to 1.61, p < 0.001). For composite fragility count (0-2), the quasipoisson sensitivity was directionally concordant (cluster-robust RR 1.16, 95% CI 1.09 to 1.23, p < 0.001).

For clinical fragility, modified-Poisson RR sensitivity also remained positive (cluster-robust RR 1.25, 95% CI 1.13 to 1.37, p < 0.001), supporting scale-robust clinical interpretation.

Under dataset-equal weighting for the clinical endpoint, the association also remained positive (cluster-robust OR 1.32, 95% CI 1.08 to 1.60, p = 0.0053), indicating that high-volume datasets are not required to recover the clinical signal.

Under a stricter joint-outcome definition requiring both direction and significance fragility simultaneously, the association was stronger and remained positive (cluster-robust OR 4.06, 95% CI 2.28 to 7.21, p < 0.001), consistent with debt concentration in the most severe fragility subset.

On the same strict joint outcome, modified-Poisson RR sensitivity remained strongly positive (cluster-robust RR 3.76, 95% CI 2.27 to 6.25, p < 0.001), indicating that the severe-endpoint finding is not specific to the OR scale.

To reduce disproportionate influence from high-volume reviews in this severe-endpoint setting, we added dataset-equal weighting sensitivity for the strict joint outcome. The association remained strongly positive (cluster-robust OR 5.45, 95% CI 2.75 to 10.80, p < 0.001).

To evaluate potential confounding by effect measure type, we fit a measure-adjusted model including `factor(measure)`. The association remained similar (OR 1.15, 95% CI 1.03 to 1.28, p = 0.0156), and remained positive under simultaneous measure adjustment and cluster-robust inference (OR 1.15, 95% CI 1.02 to 1.29, p = 0.0272).

To reduce unequal contribution from large reviews, we fit a dataset-equal weighted model (each dataset contributes equal total weight across its analyses). The association remained positive and slightly larger (OR 1.24, 95% CI 1.11 to 1.39, p = 0.0002; cluster-robust OR 1.24, 95% CI 1.06 to 1.46, p = 0.0074).

To test whether the score-fragility association differed by effect-measure family, we fit a measure-interaction model (`assumption_debt_score x measure`). The global likelihood-ratio test did not support strong interaction (p = 0.3039), indicating no clear evidence that the score effect is materially measure-specific.

To separate within-review from between-review signal, we fit a within-between (Mundlak-style) decomposition model. The within-dataset score effect was positive but imprecise (OR 1.09, 95% CI 0.96 to 1.22, p = 0.1749), while the between-dataset component was stronger (OR 1.35, 95% CI 1.06 to 1.73, p = 0.0164).

As a high-stringency confounding check, we fit a dataset fixed-effects linear probability sensitivity model. The per-point score association remained positive on the risk-difference scale (RD 0.023; 95% CI -0.002 to 0.048; p = 0.0746), with attenuated precision.

At the dataset level, we fit an aggregate binomial model (fragile count / total analyses per review) using review-level mean assumption debt and mean covariates. The direction remained positive (OR 1.27, 95% CI 1.03 to 1.58, p = 0.0281), supporting cross-review consistency.

In leave-one-measure-family-out sensitivity (excluding `GIV`, `OR`, or `SMD` in turn), cluster-robust score ORs remained directionally positive (median 1.16; 2.5th to 97.5th percentile 1.12 to 1.31). Precision attenuated when excluding `OR` because the remaining sample was small (`n = 158`), but no exclusion reversed direction.

To assess large-review dominance, we excluded datasets in the top decile of analysis count (54 datasets; retain 67.3% of meta-analyses). The cluster-robust association remained positive (OR 1.20, 95% CI 1.03 to 1.39, p = 0.0180), indicating that very large reviews are not solely driving the main result.

In information-adequacy stratified models, the score-fragility association remained positive in both `k < 10` and `k >= 10` strata. Cluster-robust ORs were 1.63 (95% CI 1.33 to 2.00; p < 0.001) for `k < 10` and 1.25 (95% CI 1.04 to 1.51; p = 0.0180) for `k >= 10`. The clustered beta-difference test between strata was not strongly significant (p = 0.0631), indicating suggestive but not definitive effect-strength heterogeneity by information size.

In effect-size-tail exclusion sensitivity (excluding analyses with `abs_estimate` above the 99th percentile; retain 99.0%), the cluster-robust association remained positive (OR 1.17, 95% CI 1.04 to 1.32, p = 0.0094), indicating that extreme effect magnitudes are not necessary to recover the main signal.

In cumulative large-review removal sensitivity (excluding the top 5/10/20/30/40 largest datasets), cluster-robust ORs remained positive throughout (median 1.19; 2.5th to 97.5th percentile 1.14 to 1.22) while retained meta-analyses ranged from 93.6% to 73.5%. This supports stability under progressively stronger suppression of high-volume review influence.

In the non-sparse-events subset (17.4% of analyses; `n = 770`), the clustered association remained directionally positive but less precise (OR 1.28, 95% CI 0.96 to 1.71; p = 0.0967), consistent with reduced power and smaller retained sample.

In the heterogeneity-present subset (`I2 > 0`; 39.0% of analyses; `n = 1,724`), the clustered association was attenuated and imprecise (OR 0.95, 95% CI 0.81 to 1.12; p = 0.5660), indicating that effect direction is less stable when restricting to non-zero heterogeneity strata alone.

In a one-analysis-per-dataset bootstrap sensitivity analysis (400 resamples), the median OR was 1.25 with a 95% empirical interval of 0.92 to 1.77, indicating directional consistency with wider uncertainty under stronger independence constraints.

In dataset-level bootstrap sensitivity (300 resamples of reviews with replacement), the median OR was 1.15 (95% empirical interval 1.04 to 1.30), consistent with the primary and cluster-robust estimates.

In leave-one-dataset-out sensitivity analysis across all 474 datasets, the assumption-debt OR remained tightly bounded (median 1.15; 2.5th to 97.5th percentile 1.14 to 1.16; full range 1.14 to 1.17), indicating no single Cochrane review dominated the primary association.

Functional-form comparison between a linear score term and a categorical score specification indicated nonlinearity (likelihood-ratio p = 7.68e-05). This supports reporting score-stratified risk patterns alongside the linear per-point OR.

Apparent discrimination was moderate (AUC 0.681), with similar row-wise 5-fold cross-validated discrimination (AUC 0.679) and grouped-by-dataset 5-fold discrimination (AUC 0.680), suggesting limited optimism and limited leakage from within-dataset similarity.
In-sample calibration metrics were near-ideal (intercept ~0, slope ~1). Out-of-fold calibration was also acceptable in both row-wise and grouped folds (row-wise 5-fold CV intercept ~0.00006, slope 0.983; grouped 5-fold CV intercept ~-0.0011, slope 0.978), reducing concern that calibration performance is purely in-sample tautology.

To test cutoff arbitrariness, we redefined sparse-study and heterogeneity components over a threshold grid (`k < 7/10/15` and `I2 >= 40/50/60`, 9 combinations). Cluster-robust score ORs remained positive across all grid models (median 1.25; 2.5th to 97.5th percentile 1.11 to 1.40; range 1.11 to 1.42).

Because tau2 was capped in the primary model, we assessed cap dependence (`0.95`, `0.99`, and uncapped). Cluster-robust score ORs remained positive but varied in magnitude (median 1.15; 2.5th to 97.5th percentile 1.09 to 1.34; range 1.09 to 1.35), indicating moderate specification sensitivity.

In high-leverage exclusion sensitivity (excluding analyses with max study weight >= 0.70 or tau2 above the 99th percentile), 93.2% of meta-analyses were retained and the cluster-robust score association remained positive (OR 1.15, 95% CI 1.01 to 1.30; p = 0.0308).

In a conservative within-dataset permutation sensitivity (300 repetitions), the empirical two-sided p-value for the score coefficient was 0.08. We interpret this as attenuation of evidence under strong null reshuffling, indicating that part of the observed association is likely coupled to structured covariate patterns; therefore, we present the effect as robustly directional but with non-negligible uncertainty about mechanistic attribution.

Fragility increased monotonically across score strata: 32.0% (score 0), 38.4% (score 1), 50.9% (score 2), and 70.0% (score 3).

## 3. Component-Level Sensitivity Model
In the component-expanded model (same covariate adjustment), higher fragility odds were associated with:
- high heterogeneity: OR 1.73 (95% CI 1.36 to 2.20; p < 0.001)
- dominance by one study: OR 1.34 (95% CI 1.13 to 1.59; p < 0.001)

Small-study signal and sparse-events indicators were not independently associated after adjustment in this specification. The `k < 10` component showed an inverse adjusted association when entered jointly with `log_k`; this reflects strong collinearity (correlation `r = -0.80`) between these variables.

In a collinearity-aware component sensitivity model omitting `log_k`, the `k < 10` association reversed to the expected positive direction (OR 1.89, 95% CI 1.64 to 2.17; cluster-robust OR 1.89, 95% CI 1.59 to 2.25).

Only 46.2% of meta-analyses had `k >= 10` (small-study-effect assessable by Egger); within that assessable subset, small-study signal prevalence was 26.2%.

## Table 1. Descriptive Characteristics and Assumption Debt Distribution
| Metric | Value |
|---|---|
| Meta-analyses analyzed | 4,424 |
| Fragile (any), % | 39.8 |
| Direction-fragile, % | 26.7 |
| Significance-fragile, % | 15.0 |
| Mean k (studies) | 18.2 |
| Median k (studies) | 9 |
| Median I2, % | 0.0 |
| k < 10, % | 53.8 |
| I2 >= 50%, % | 16.4 |
| Egger p < 0.10 (k >= 10), % | 12.1 |
| Max study weight >= 50%, % | 16.8 |
| Sparse-events flag > 0, % | 82.6 |
| Assumption Debt Score >= 2, % | 22.3 |

## Table 2. Multivariable Logistic Models for Fragility
| Model / Term | OR | 95% CI | p-value |
|---|---:|---|---:|
| **Primary model** |  |  |  |
| Assumption Debt Score (per +1) | 1.15 | 1.03 to 1.28 | 0.0117 |
| Assumption Debt Score (no-Egger score sensitivity) | 1.18 | 1.05 to 1.32 | 0.0069 |
| Assumption Debt Score (no-Egger score sensitivity + cluster-robust) | 1.18 | 1.03 to 1.34 | 0.0151 |
| Assumption Debt Score (modified-Poisson RR) | 1.08 (RR) | 1.02 to 1.15 | 0.0137 |
| Assumption Debt Score (modified-Poisson RR + cluster-robust) | 1.08 (RR) | 1.01 to 1.16 | 0.0243 |
| Assumption Debt Score (assessable subset `k >= 10`) | 1.31 | 1.09 to 1.59 | 0.0050 |
| Assumption Debt Score (assessable subset `k >= 10` + cluster-robust) | 1.31 | 1.07 to 1.61 | 0.0084 |
| Assumption Debt Score (complete-case outcome) | 1.13 | 1.01 to 1.26 | 0.0370 |
| Assumption Debt Score (complete-case + cluster-robust) | 1.13 | 1.00 to 1.27 | 0.0572 |
| Assumption Debt Score (direction fragility outcome) | 1.17 | 1.02 to 1.35 | 0.0300 |
| Assumption Debt Score (direction fragility + cluster-robust) | 1.17 | 1.00 to 1.37 | 0.0509 |
| Assumption Debt Score (significance fragility outcome) | 1.30 | 1.12 to 1.50 | 0.0005 |
| Assumption Debt Score (significance fragility + cluster-robust) | 1.30 | 1.08 to 1.56 | 0.0059 |
| Assumption Debt Score (clinical fragility outcome) | 1.40 | 1.24 to 1.58 | <0.001 |
| Assumption Debt Score (clinical fragility + cluster-robust) | 1.40 | 1.21 to 1.61 | <0.001 |
| Assumption Debt Score (clinical fragility modified-Poisson RR) | 1.25 (RR) | 1.15 to 1.35 | <0.001 |
| Assumption Debt Score (clinical fragility modified-Poisson RR + cluster-robust) | 1.25 (RR) | 1.13 to 1.37 | <0.001 |
| Assumption Debt Score (clinical fragility dataset-equal weighting) | 1.32 | 1.16 to 1.49 | <0.001 |
| Assumption Debt Score (clinical fragility dataset-equal weighting + cluster-robust) | 1.32 | 1.08 to 1.60 | 0.0053 |
| Assumption Debt Score (joint fragility outcome: direction AND significance) | 4.06 | 2.22 to 7.41 | <0.001 |
| Assumption Debt Score (joint fragility outcome + cluster-robust) | 4.06 | 2.28 to 7.21 | <0.001 |
| Assumption Debt Score (joint fragility modified-Poisson RR) | 3.76 (RR) | 2.04 to 6.93 | <0.001 |
| Assumption Debt Score (joint fragility modified-Poisson RR + cluster-robust) | 3.76 (RR) | 2.27 to 6.25 | <0.001 |
| Assumption Debt Score (joint fragility dataset-equal weighting) | 5.45 | 2.93 to 10.15 | <0.001 |
| Assumption Debt Score (joint fragility dataset-equal weighting + cluster-robust) | 5.45 | 2.75 to 10.80 | <0.001 |
| Assumption Debt Score (composite fragility-count outcome; quasipoisson RR) | 1.16 (RR) | 1.10 to 1.22 | <0.001 |
| Assumption Debt Score (composite fragility-count + cluster-robust; quasipoisson RR) | 1.16 (RR) | 1.09 to 1.23 | <0.001 |
| Assumption Debt Score (cluster-robust by dataset) | 1.15 | 1.02 to 1.30 | 0.0212 |
| Assumption Debt Score (measure-adjusted) | 1.15 | 1.03 to 1.28 | 0.0156 |
| Assumption Debt Score (measure-adjusted + cluster-robust) | 1.15 | 1.02 to 1.29 | 0.0272 |
| Assumption Debt Score (dataset-equal weighting) | 1.24 | 1.11 to 1.39 | 0.0002 |
| Assumption Debt Score (dataset-equal weighting + cluster-robust) | 1.24 | 1.06 to 1.46 | 0.0074 |
| Score x measure interaction LR test | N/A | N/A | 0.3039 |
| Assumption Debt Score (within-between: within component, cluster-robust) | 1.09 | 0.96 to 1.22 | 0.1749 |
| Assumption Debt Score (within-between: between component, cluster-robust) | 1.35 | 1.06 to 1.73 | 0.0164 |
| Assumption Debt Score (dataset fixed-effects LPM, clustered RD) | 0.023 (RD) | -0.002 to 0.048 | 0.0746 |
| Assumption Debt Score (dataset-level aggregate model) | 1.27 | 1.03 to 1.58 | 0.0281 |
| Leave-one-measure-family-out (clustered OR median) | 1.16 | 1.12 to 1.31 (2.5% to 97.5%) | N/A |
| Exclude largest reviews (top decile by size; cluster-robust) | 1.20 | 1.03 to 1.39 | 0.0180 |
| k-stratified (`k < 10`; cluster-robust) | 1.63 | 1.33 to 2.00 | <0.001 |
| k-stratified (`k >= 10`; cluster-robust) | 1.25 | 1.04 to 1.51 | 0.0180 |
| k-strata clustered beta-difference test | N/A | N/A | 0.0631 |
| Effect-size-tail exclusion (cluster-robust) | 1.17 | 1.04 to 1.32 | 0.0094 |
| Cumulative largest-review removal (clustered OR median) | 1.19 | 1.14 to 1.22 (2.5% to 97.5%) | N/A |
| Non-sparse-events subset (cluster-robust) | 1.28 | 0.96 to 1.71 | 0.0967 |
| Heterogeneity-present subset (`I2 > 0`; cluster-robust) | 0.95 | 0.81 to 1.12 | 0.5660 |
| Assumption Debt Score (one-per-dataset bootstrap median) | 1.25 | 0.92 to 1.77 | N/A |
| Assumption Debt Score (dataset-level bootstrap median) | 1.15 | 1.04 to 1.30 | N/A |
| Assumption Debt Score (leave-one-dataset-out median) | 1.15 | 1.14 to 1.16 (2.5% to 97.5%) | N/A |
| Score linear vs categorical LR test | N/A | N/A | 7.68e-05 |
| Threshold-grid sensitivity (clustered OR median) | 1.25 | 1.11 to 1.40 (2.5% to 97.5%) | N/A |
| Dominance-threshold sensitivity (clustered OR median) | 1.15 | 1.13 to 1.20 (2.5% to 97.5%) | N/A |
| Egger-threshold sensitivity (clustered OR median) | 1.15 | 1.14 to 1.15 (2.5% to 97.5%) | N/A |
| Tau2-cap sensitivity (clustered OR median) | 1.15 | 1.09 to 1.34 (2.5% to 97.5%) | N/A |
| High-leverage exclusion sensitivity (cluster-robust) | 1.15 | 1.01 to 1.30 | 0.0308 |
| Within-dataset permutation sensitivity | N/A | N/A | empirical p = 0.08 |
| Multiverse consistency (directionally positive checks) | 51/52 (98.1%) | N/A | N/A |
| Multiverse consistency (CI supports positive direction) | 45/52 (86.5%) | N/A | N/A |
| Multiverse directional sign test vs 50% null | 51/52 positive | exact CI 0.912 to 1.000 | one-sided p = 1.18e-14 |
| log(k) | 0.59 | 0.54 to 0.64 | <0.001 |
| abs_estimate | 0.26 | 0.21 to 0.32 | <0.001 |
| tau2_capped | 2.86 | 2.35 to 3.46 | <0.001 |
| **Component-expanded model** |  |  |  |
| k < 10 | 0.69 | 0.55 to 0.87 | 0.0013 |
| I2 >= 50% | 1.73 | 1.36 to 2.20 | <0.001 |
| Small-study signal (Egger p < 0.10) | 0.99 | 0.78 to 1.24 | 0.905 |
| Dominance (max weight >= 50%) | 1.34 | 1.13 to 1.59 | <0.001 |
| Sparse-events flag > 0 | 0.98 | 0.81 to 1.17 | 0.787 |
| log(k) | 0.47 | 0.41 to 0.54 | <0.001 |
| abs_estimate | 0.26 | 0.21 to 0.32 | <0.001 |
| tau2_capped | 2.33 | 1.85 to 2.92 | <0.001 |
| `k < 10` in no-`log_k` component model | 1.89 | 1.64 to 2.17 | <0.001 |
| `k < 10` in no-`log_k` component model (cluster-robust) | 1.89 | 1.59 to 2.25 | <0.001 |

## Figure Captions
**Figure 1. Distribution of Assumption Debt Components Across Cochrane Pairwise Meta-Analyses.**  
Bar chart showing prevalence (%) of each component: `k < 10`, `I2 >= 50%`, small-study signal (Egger p < 0.10 among k >= 10), dominance (max study weight >= 50%), and sparse-events flag.

**Figure 2. Fragility Gradient by Assumption Debt Score.**  
Line or bar plot of fragility proportion by score (0-3), with 95% binomial confidence intervals and sample size labels for each score stratum.

**Figure 3. Adjusted Odds Ratios for Fragility.**  
Forest plot of adjusted ORs (95% CI) from the component-expanded logistic model, highlighting heterogeneity and dominance as the strongest positive predictors of fragility.

## Data Sources for This Section
- `analysis/output/assumption_debt_model_summary.csv`
- `analysis/output/assumption_debt_components.csv`
- `analysis/output/assumption_debt_by_score.csv`
- `analysis/output/assumption_debt_model_coefficients.csv`
- `analysis/output/assumption_debt_model_coefficients_no_egger.csv`
- `analysis/output/assumption_debt_model_coefficients_no_egger_cluster.csv`
- `analysis/output/assumption_debt_model_coefficients_rr.csv`
- `analysis/output/assumption_debt_model_coefficients_rr_cluster.csv`
- `analysis/output/assumption_debt_model_coefficients_assessable.csv`
- `analysis/output/assumption_debt_model_coefficients_assessable_cluster.csv`
- `analysis/output/assumption_debt_model_coefficients_complete_case.csv`
- `analysis/output/assumption_debt_model_coefficients_complete_case_cluster.csv`
- `analysis/output/assumption_debt_model_coefficients_direction.csv`
- `analysis/output/assumption_debt_model_coefficients_direction_cluster.csv`
- `analysis/output/assumption_debt_model_coefficients_significance.csv`
- `analysis/output/assumption_debt_model_coefficients_significance_cluster.csv`
- `analysis/output/assumption_debt_model_coefficients_clinical.csv`
- `analysis/output/assumption_debt_model_coefficients_clinical_cluster.csv`
- `analysis/output/assumption_debt_model_coefficients_clinical_rr.csv`
- `analysis/output/assumption_debt_model_coefficients_clinical_rr_cluster.csv`
- `analysis/output/assumption_debt_model_coefficients_clinical_dataset_equal_weight.csv`
- `analysis/output/assumption_debt_model_coefficients_clinical_dataset_equal_weight_cluster.csv`
- `analysis/output/assumption_debt_model_coefficients_both.csv`
- `analysis/output/assumption_debt_model_coefficients_both_cluster.csv`
- `analysis/output/assumption_debt_model_coefficients_both_rr.csv`
- `analysis/output/assumption_debt_model_coefficients_both_rr_cluster.csv`
- `analysis/output/assumption_debt_model_coefficients_both_dataset_equal_weight.csv`
- `analysis/output/assumption_debt_model_coefficients_both_dataset_equal_weight_cluster.csv`
- `analysis/output/assumption_debt_model_coefficients_composite_count.csv`
- `analysis/output/assumption_debt_model_coefficients_composite_count_cluster.csv`
- `analysis/output/assumption_debt_component_model_coefficients.csv`
- `analysis/output/assumption_debt_model_coefficients_cluster.csv`
- `analysis/output/assumption_debt_component_model_coefficients_cluster.csv`
- `analysis/output/assumption_debt_component_model_coefficients_no_logk.csv`
- `analysis/output/assumption_debt_component_model_coefficients_no_logk_cluster.csv`
- `analysis/output/assumption_debt_model_coefficients_measure.csv`
- `analysis/output/assumption_debt_model_coefficients_measure_cluster.csv`
- `analysis/output/assumption_debt_model_coefficients_dataset_equal_weight.csv`
- `analysis/output/assumption_debt_model_coefficients_dataset_equal_weight_cluster.csv`
- `analysis/output/assumption_debt_measure_interaction_test.csv`
- `analysis/output/assumption_debt_measure_specific_effects_cluster.csv`
- `analysis/output/assumption_debt_within_between_coefficients.csv`
- `analysis/output/assumption_debt_within_between_coefficients_cluster.csv`
- `analysis/output/assumption_debt_fixed_effects_lpm.csv`
- `analysis/output/assumption_debt_dataset_level_model.csv`
- `analysis/output/assumption_debt_leave_one_measure_out.csv`
- `analysis/output/assumption_debt_leave_one_measure_out_summary.csv`
- `analysis/output/assumption_debt_large_review_sensitivity.csv`
- `analysis/output/assumption_debt_large_review_excluded_datasets.csv`
- `analysis/output/assumption_debt_k_strata_effects.csv`
- `analysis/output/assumption_debt_k_strata_difference_test.csv`
- `analysis/output/assumption_debt_effect_tail_sensitivity.csv`
- `analysis/output/assumption_debt_large_review_cumulative_sensitivity.csv`
- `analysis/output/assumption_debt_large_review_cumulative_summary.csv`
- `analysis/output/assumption_debt_non_sparse_events_sensitivity.csv`
- `analysis/output/assumption_debt_i2_positive_sensitivity.csv`
- `analysis/output/assumption_debt_predictor_correlation.csv`
- `analysis/output/assumption_debt_small_study_assessability.csv`
- `analysis/output/assumption_debt_one_per_dataset_bootstrap.csv`
- `analysis/output/assumption_debt_leave_one_dataset_out.csv`
- `analysis/output/assumption_debt_leave_one_dataset_out_summary.csv`
- `analysis/output/assumption_debt_model_performance.csv`
- `analysis/output/assumption_debt_score_nonlinearity_test.csv`
- `analysis/output/assumption_debt_model_coefficients_score_categorical.csv`
- `analysis/output/assumption_debt_model_coefficients_score_categorical_cluster.csv`
- `analysis/output/assumption_debt_threshold_sensitivity.csv`
- `analysis/output/assumption_debt_threshold_sensitivity_summary.csv`
- `analysis/output/assumption_debt_dominance_threshold_sensitivity.csv`
- `analysis/output/assumption_debt_dominance_threshold_sensitivity_summary.csv`
- `analysis/output/assumption_debt_egger_threshold_sensitivity.csv`
- `analysis/output/assumption_debt_egger_threshold_sensitivity_summary.csv`
- `analysis/output/assumption_debt_tau2_cap_sensitivity.csv`
- `analysis/output/assumption_debt_tau2_cap_sensitivity_summary.csv`
- `analysis/output/assumption_debt_high_leverage_sensitivity.csv`
- `analysis/output/assumption_debt_permutation_summary.csv`
- `analysis/output/assumption_debt_dataset_bootstrap_summary.csv`
- `analysis/output/assumption_debt_robustness_matrix.csv`
- `analysis/output/assumption_debt_specification_curve.csv`
- `analysis/output/assumption_debt_multiverse_consistency.csv`
- `analysis/output/assumption_debt_multiverse_sign_test.csv`
