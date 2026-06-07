# Submission Packet: Assumption Debt Analysis (Pairwise70)

## Included Materials
- Manuscript-ready Results section
- Multi-persona Research Synthesis Methods review memo
- Response-to-reviewers letter
- Intro/Discussion framing brief on the single biggest underdiagnosed flaw
- Publishability hardening checklist
- Preregistration-style analysis plan appendix
- Claims-language guardrail note
- Journal-targeted abstract (RSM)
- Journal-targeted cover letter (RSM)
- Full manuscript draft (PLOS ONE format)
- Journal-targeted cover letter (PLOS ONE)
- PLOS ONE submission checklist
- Core model summary and coefficient tables
- Collinearity, assessability, influence, outlier, functional-form, threshold, permutation, bootstrap, missingness, tau2-specification, decomposition, fixed-effects, aggregate review-level, measure-interaction, leave-one-measure, large-review exclusion, cumulative dominance removal, dataset-equal weighting, k-stratified consistency, outcome-specific fragility definitions (direction/significance/clinical/composite-count), effect-size-tail exclusion, non-sparse-events subset, I2-positive subset, and calibration diagnostics
- Figure manifest and generated figures

---

## 1) Manuscript Results Section

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

---

## 2) Multi-Persona RSM Review

# Multi-Persona Review (Research Synthesis Methods Lens)

## Persona 1: Statistical Methods Editor
**Finding:** Original inference treated 4,424 meta-analyses as independent despite clustering within 474 Cochrane datasets.  
**Risk:** Underestimated standard errors and overstated certainty.  
**Improvement implemented:** Added dataset-clustered robust SE models and exported:
- `assumption_debt_model_coefficients_cluster.csv`
- `assumption_debt_component_model_coefficients_cluster.csv`

## Persona 2: Meta-Research Methodologist
**Finding:** Primary claim needed a dependence-aware sensitivity analysis beyond robust SE.  
**Risk:** Structural dependence could still influence point estimates.  
**Improvement implemented:** Added one-analysis-per-dataset bootstrap sensitivity (400 resamples), exported:
- `assumption_debt_one_per_dataset_bootstrap.csv`

## Persona 3: Model Specification Reviewer
**Finding:** Potential confounding by effect measure family (`RR`, `OR`, `SMD`) was not explicitly handled.  
**Risk:** Estimated association could be partly attributable to scale differences.  
**Improvement implemented:** Added measure-adjusted logistic sensitivity models (with and without cluster-robust SE), exported:
- `assumption_debt_model_coefficients_measure.csv`
- `assumption_debt_model_coefficients_measure_cluster.csv`

## Persona 4: Causal/Interpretation Reviewer
**Finding:** Component model interpretation for `k < 10` was unstable because `k < 10` and `log_k` were entered together despite strong collinearity (`r = -0.80`).  
**Risk:** Sign reversal and misleading mechanistic interpretation.  
**Improvement implemented:** Added no-`log_k` component sensitivity model with clustered counterpart and explicit predictor-correlation diagnostic exports:
- `assumption_debt_component_model_coefficients_no_logk.csv`
- `assumption_debt_component_model_coefficients_no_logk_cluster.csv`
- `assumption_debt_predictor_correlation.csv`

## Persona 5: Reporting/Transparency Reviewer
**Finding:** Summary file previously omitted explicit NA handling for component fragility rates.  
**Risk:** Blank rates in downstream tables/text.  
**Improvement implemented:** Added `na.rm = TRUE` for `direction_fragile_rate` and `sig_fragile_rate` in summary output.

## Persona 6: Small-Study Effects Reviewer
**Finding:** Egger-based small-study signal prevalence can be misread without stating assessability (`k >= 10`).  
**Risk:** Understatement or overstatement of small-study concerns at the corpus level.  
**Improvement implemented:** Added assessability diagnostics export:
- `assumption_debt_small_study_assessability.csv`

## Persona 7: Influence/Robustness Reviewer
**Finding:** Need explicit evidence that no single dataset drives the primary effect.  
**Risk:** Outlier review dependence could distort corpus-level conclusions.  
**Improvement implemented:** Added leave-one-dataset-out sensitivity outputs:
- `assumption_debt_leave_one_dataset_out.csv`
- `assumption_debt_leave_one_dataset_out_summary.csv`

## Persona 8: Model Diagnostics Reviewer
**Finding:** Prior performance summary only reported apparent fit; functional form was assumed linear.  
**Risk:** Overstated model adequacy and under-specified effect shape.  
**Improvement implemented:** Added:
- row-wise and grouped-by-dataset 5-fold CV discrimination in `assumption_debt_model_performance.csv`
- linear vs categorical score LR test in `assumption_debt_score_nonlinearity_test.csv`
- categorical score coefficient exports:
  - `assumption_debt_model_coefficients_score_categorical.csv`
  - `assumption_debt_model_coefficients_score_categorical_cluster.csv`

## Persona 9: Threshold-Arbitrariness Reviewer
**Finding:** Debt score components depend on fixed cutoffs (`k < 10`, `I2 >= 50`) that could be arbitrary.  
**Risk:** Main association may be threshold-specific.  
**Improvement implemented:** Added threshold-grid sensitivity over (`k < 7/10/15`) x (`I2 >= 40/50/60`):
- `assumption_debt_threshold_sensitivity.csv`
- `assumption_debt_threshold_sensitivity_summary.csv`

## Persona 10: Null-Structure Reviewer
**Finding:** Need a conservative check against spurious score-outcome link under within-dataset structural dependence.  
**Risk:** Observed association could partly reflect structured covariate geometry rather than independent score signal.  
**Improvement implemented:** Added within-dataset permutation sensitivity:
- `assumption_debt_permutation_summary.csv`

## Persona 11: Calibration Reviewer
**Finding:** Prior calibration interpretation relied partly on in-sample metrics.  
**Risk:** Apparent calibration can be tautological for fitted logistic models.  
**Improvement implemented:** Added row-wise and grouped-by-dataset out-of-fold calibration intercept/slope in:
- `assumption_debt_model_performance.csv`

## Persona 12: Cluster-Bootstrap Reviewer
**Finding:** One-per-dataset bootstrap can overstate uncertainty by collapsing within-dataset analysis structure.  
**Risk:** Sensitivity interpretation may be pessimistic relative to realistic clustered resampling.  
**Improvement implemented:** Added dataset-level bootstrap (resampling full datasets with replacement):
- `assumption_debt_dataset_bootstrap_summary.csv`

## Persona 13: Missing-Outcome Reviewer
**Finding:** Primary outcome coding treated missing fragility flags as non-fragile by default.  
**Risk:** Potential attenuation bias in the score association.  
**Improvement implemented:** Added complete-case outcome sensitivity models:
- `assumption_debt_model_coefficients_complete_case.csv`
- `assumption_debt_model_coefficients_complete_case_cluster.csv`

## Persona 14: Synthesis/Transparency Reviewer
**Finding:** Many sensitivity outputs existed but lacked one unified summary table.  
**Risk:** Harder for editors/reviewers to audit stability across checks.  
**Improvement implemented:** Added:
- `assumption_debt_robustness_matrix.csv`

## Persona 15: Heterogeneity-Model Reviewer
**Finding:** Primary association may depend on tau2 capping choice (0.99 in base model).  
**Risk:** Effect magnitude may reflect variance-treatment specification rather than stable signal size.  
**Improvement implemented:** Added tau2-cap sensitivity outputs:
- `assumption_debt_tau2_cap_sensitivity.csv`
- `assumption_debt_tau2_cap_sensitivity_summary.csv`

## Persona 16: Influence-Outlier Reviewer
**Finding:** Extreme dominance or heterogeneity outliers might drive associations.  
**Risk:** Robustness may be overstated if a small high-leverage subset dominates.  
**Improvement implemented:** Added high-leverage exclusion sensitivity:
- `assumption_debt_high_leverage_sensitivity.csv`

## Persona 17: Applied Evidence-Synthesis Reviewer
**Finding:** Results text did not separate model-based significance from sensitivity uncertainty.  
**Risk:** Overconfident interpretation in manuscript narrative.  
**Improvement implemented:** Updated manuscript section to report:
- conventional model
- cluster-robust model
- measure-adjusted and measure-adjusted cluster-robust models
- collinearity-aware no-`log_k` component model
- bootstrap median + empirical interval

File updated:
- `assumption_debt_results_section.md`

## Persona 18: Decomposition Reviewer
**Finding:** Prior models did not separate within-dataset and between-dataset score signal.  
**Risk:** Apparent association might be driven mainly by between-review differences.  
**Improvement implemented:** Added within-between decomposition models with clustered inference:
- `assumption_debt_within_between_coefficients.csv`
- `assumption_debt_within_between_coefficients_cluster.csv`

## Persona 19: Fixed-Effects Reviewer
**Finding:** Residual dataset-level confounding could still remain under pooled logistic models.  
**Risk:** Score effect could partly reflect stable review-level differences.  
**Improvement implemented:** Added dataset fixed-effects linear probability sensitivity with clustered SE:
- `assumption_debt_fixed_effects_lpm.csv`

## Persona 20: Cross-Review Consistency Reviewer
**Finding:** The main model is analysis-level; editors may request a direct review-level concordance check.  
**Risk:** Association might not replicate when collapsing to the review level.  
**Improvement implemented:** Added dataset-level aggregate binomial model:
- `assumption_debt_dataset_level_model.csv`

## Persona 21: Effect-Modification Reviewer
**Finding:** The score effect could differ across effect-measure families (`OR`, `SMD`, `GIV`).  
**Risk:** A pooled score effect might mask scale-specific behavior.  
**Improvement implemented:** Added measure-interaction testing and clustered measure-specific slope exports:
- `assumption_debt_measure_interaction_test.csv`
- `assumption_debt_measure_specific_effects_cluster.csv`

## Persona 22: Measure-Dependence Robustness Reviewer
**Finding:** Interaction tests can be low-power; a direct exclusion sensitivity by measure family is needed.  
**Risk:** One measure family could still dominate pooled results despite non-significant interaction tests.  
**Improvement implemented:** Added leave-one-measure-family-out sensitivity:
- `assumption_debt_leave_one_measure_out.csv`
- `assumption_debt_leave_one_measure_out_summary.csv`

## Persona 23: Large-Review Dominance Reviewer
**Finding:** Very large Cochrane reviews may dominate pooled analysis-level estimates.  
**Risk:** Main effect could be driven disproportionately by high-volume datasets.  
**Improvement implemented:** Added top-decile size exclusion sensitivity and explicit excluded-dataset inventory:
- `assumption_debt_large_review_sensitivity.csv`
- `assumption_debt_large_review_excluded_datasets.csv`

## Persona 24: Weighting Scheme Reviewer
**Finding:** Row-level pooled models can overweight datasets contributing many analyses.  
**Risk:** Inference may reflect contribution imbalance rather than robust cross-dataset signal.  
**Improvement implemented:** Added dataset-equal weighting sensitivity (with clustered counterpart):
- `assumption_debt_model_coefficients_dataset_equal_weight.csv`
- `assumption_debt_model_coefficients_dataset_equal_weight_cluster.csv`

## Persona 25: Information-Adequacy Stratification Reviewer
**Finding:** The score effect might exist only in sparse (`k < 10`) analyses.  
**Risk:** Practical relevance for adequately-sized meta-analyses could be overstated.  
**Improvement implemented:** Added `k`-stratified clustered models and a between-strata difference test:
- `assumption_debt_k_strata_effects.csv`
- `assumption_debt_k_strata_difference_test.csv`

## Persona 26: Outcome-Definition Reviewer
**Finding:** Composite fragility may mask different behavior for direction versus significance fragility.  
**Risk:** A single pooled outcome could obscure component-specific signal strength.  
**Improvement implemented:** Added separate outcome models for direction and significance fragility (with clustered counterparts):
- `assumption_debt_model_coefficients_direction.csv`
- `assumption_debt_model_coefficients_direction_cluster.csv`
- `assumption_debt_model_coefficients_significance.csv`
- `assumption_debt_model_coefficients_significance_cluster.csv`

## Persona 27: Effect-Size Tail Reviewer
**Finding:** Extreme effect magnitudes may unduly influence fragility-association estimates.  
**Risk:** Main association could be an artifact of the extreme right tail of `abs_estimate`.  
**Improvement implemented:** Added 99th-percentile effect-size-tail exclusion sensitivity:
- `assumption_debt_effect_tail_sensitivity.csv`

## Persona 28: Progressive Dominance Reviewer
**Finding:** Single-cutoff large-review exclusion may miss instability under progressively stronger dominance removal.  
**Risk:** Apparent robustness could depend on one arbitrary exclusion threshold.  
**Improvement implemented:** Added cumulative large-review removal curve (top 5/10/20/30/40 datasets) and summary:
- `assumption_debt_large_review_cumulative_sensitivity.csv`
- `assumption_debt_large_review_cumulative_summary.csv`

## Persona 29: Sparse-Events Context Reviewer
**Finding:** The corpus is sparse-event heavy, so association strength in non-sparse settings should be checked explicitly.  
**Risk:** Main signal might not generalize outside sparse-event contexts.  
**Improvement implemented:** Added non-sparse-events subset sensitivity:
- `assumption_debt_non_sparse_events_sensitivity.csv`

## Persona 30: Heterogeneity-Subset Reviewer
**Finding:** The association may behave differently when restricting to analyses with non-zero heterogeneity.  
**Risk:** Fragility linkage could weaken or invert in heterogeneity-present subsets.  
**Improvement implemented:** Added `I2 > 0` subset sensitivity:
- `assumption_debt_i2_positive_sensitivity.csv`

## Persona 31: Clinical-Outcome Reviewer
**Finding:** Construct validity requires checking whether the score also relates to clinical fragility, not only statistical fragility components.  
**Risk:** Main signal could be confined to statistical definitions with weaker clinical relevance.  
**Improvement implemented:** Added clinical-fragility outcome models (conventional and clustered):
- `assumption_debt_model_coefficients_clinical.csv`
- `assumption_debt_model_coefficients_clinical_cluster.csv`

## Persona 32: Count-Outcome Reviewer
**Finding:** Binary endpoints can hide incremental outcome burden when multiple fragility components co-occur.  
**Risk:** Dichotomization may underrepresent outcome-intensity information.  
**Improvement implemented:** Added composite fragility-count (0-2) quasipoisson sensitivity models (conventional and clustered):
- `assumption_debt_model_coefficients_composite_count.csv`
- `assumption_debt_model_coefficients_composite_count_cluster.csv`

## Persona 33: Conceptual-Framing Reviewer
**Finding:** The manuscript needed a singular, testable statement of the biggest underdiagnosed flaw in modern meta-analysis.  
**Risk:** Without a clear framing claim, extensive robustness work can read as fragmented rather than theory-driven.  
**Improvement implemented:** Added an introduction/discussion framing brief centered on unmeasured assumption burden ("assumption debt") with calibrated causal language:
- `assumption_debt_intro_discussion_framing.md`

## Persona 34: Effect-Scale Interpretability Reviewer
**Finding:** OR-based summaries can be misread when fragility prevalence is not rare.  
**Risk:** Practical effect magnitude may be overstated if interpreted as risk ratios.  
**Improvement implemented:** Added binary modified-Poisson RR sensitivity for the primary `fragile_any` outcome (conventional and clustered):
- `assumption_debt_model_coefficients_rr.csv`
- `assumption_debt_model_coefficients_rr_cluster.csv`

## Persona 35: Assessability-Bias Reviewer
**Finding:** Egger-based small-study component is only assessable for analyses with `k >= 10`.  
**Risk:** Composite debt score may be partly shaped by assessability structure rather than substantive fragility burden.  
**Improvement implemented:** Added no-Egger score sensitivity (3-component debt score) with clustered inference:
- `assumption_debt_model_coefficients_no_egger.csv`
- `assumption_debt_model_coefficients_no_egger_cluster.csv`

## Persona 36: Severity-Definition Reviewer
**Finding:** Binary "any fragility" may dilute association strength for the most severe instability profile.  
**Risk:** Severe fragility mechanisms can be undercharacterized when combined with milder cases.  
**Improvement implemented:** Added strict joint-fragility outcome sensitivity (direction AND significance; conventional and clustered):
- `assumption_debt_model_coefficients_both.csv`
- `assumption_debt_model_coefficients_both_cluster.csv`

## Persona 37: Severity-Scale Reviewer
**Finding:** Severe-endpoint conclusions based only on OR scale can be questioned for interpretability.  
**Risk:** Magnitude interpretation for strict joint fragility could be seen as link-function dependent.  
**Improvement implemented:** Added modified-Poisson RR sensitivity for strict joint fragility (conventional and clustered):
- `assumption_debt_model_coefficients_both_rr.csv`
- `assumption_debt_model_coefficients_both_rr_cluster.csv`

## Persona 38: Severe-Endpoint Contribution-Balance Reviewer
**Finding:** Severe-endpoint estimates may be disproportionately influenced by datasets contributing many analyses.  
**Risk:** Strict joint-fragility signal could be over-attributed to high-volume reviews.  
**Improvement implemented:** Added dataset-equal weighting sensitivity for strict joint fragility (conventional and clustered):
- `assumption_debt_model_coefficients_both_dataset_equal_weight.csv`
- `assumption_debt_model_coefficients_both_dataset_equal_weight_cluster.csv`

## Persona 39: Clinical-Scale Interpretability Reviewer
**Finding:** Clinical-outcome interpretation benefits from RR-scale reporting in addition to ORs.  
**Risk:** Clinical-effect communication may be harder to calibrate if restricted to OR scale.  
**Improvement implemented:** Added modified-Poisson RR sensitivity for clinical fragility (conventional and clustered):
- `assumption_debt_model_coefficients_clinical_rr.csv`
- `assumption_debt_model_coefficients_clinical_rr_cluster.csv`

## Persona 40: Clinical Contribution-Balance Reviewer
**Finding:** Clinical-endpoint inference may still be influenced by high-volume datasets.  
**Risk:** Clinical signal could be overstated if contribution imbalance is not addressed directly.  
**Improvement implemented:** Added dataset-equal weighting sensitivity for clinical fragility (conventional and clustered):
- `assumption_debt_model_coefficients_clinical_dataset_equal_weight.csv`
- `assumption_debt_model_coefficients_clinical_dataset_equal_weight_cluster.csv`

## Net Effect on Main Claim
- Primary model: OR 1.15 (95% CI 1.03 to 1.28; p = 0.0117)
- Cluster-robust: OR 1.15 (95% CI 1.02 to 1.30; p = 0.0212)
- Modified-Poisson RR: RR 1.08 (95% CI 1.02 to 1.15; p = 0.0137)
- Modified-Poisson RR + cluster-robust: RR 1.08 (95% CI 1.01 to 1.16; p = 0.0243)
- No-Egger score sensitivity: OR 1.18 (95% CI 1.05 to 1.32; p = 0.0069), cluster-robust OR 1.18 (95% CI 1.03 to 1.34; p = 0.0151)
- Joint fragility outcome (direction AND significance): clustered OR 4.06 (95% CI 2.28 to 7.21; p < 0.001)
- Joint fragility outcome modified-Poisson RR: clustered RR 3.76 (95% CI 2.27 to 6.25; p < 0.001)
- Joint fragility outcome dataset-equal weighting: clustered OR 5.45 (95% CI 2.75 to 10.80; p < 0.001)
- Clinical fragility modified-Poisson RR: clustered RR 1.25 (95% CI 1.13 to 1.37; p < 0.001)
- Clinical fragility dataset-equal weighting: clustered OR 1.32 (95% CI 1.08 to 1.60; p = 0.0053)
- Measure-adjusted: OR 1.15 (95% CI 1.03 to 1.28; p = 0.0156)
- Measure-adjusted + cluster-robust: OR 1.15 (95% CI 1.02 to 1.29; p = 0.0272)
- Within-between (within component, clustered): OR 1.09 (95% CI 0.96 to 1.22; p = 0.1749)
- Within-between (between component, clustered): OR 1.35 (95% CI 1.06 to 1.73; p = 0.0164)
- Dataset fixed-effects LPM (clustered RD per +1 score): 0.023 (95% CI -0.002 to 0.048; p = 0.0746)
- Dataset-level aggregate model: OR 1.27 (95% CI 1.03 to 1.58; p = 0.0281)
- Score x measure interaction LR test: p = 0.3039 (no strong effect-modification signal)
- Leave-one-measure-family-out (clustered OR): median 1.16 (2.5% to 97.5%: 1.12 to 1.31); direction preserved in all exclusions
- Exclude largest reviews (top decile by analysis count): clustered OR 1.20 (95% CI 1.03 to 1.39; p = 0.0180), retaining 67.3% of meta-analyses
- Dataset-equal weighting: OR 1.24 (95% CI 1.11 to 1.39; p = 0.0002), clustered OR 1.24 (95% CI 1.06 to 1.46; p = 0.0074)
- k-stratified clustered ORs: 1.63 for `k < 10` and 1.25 for `k >= 10`; between-strata beta-difference p = 0.0631
- Direction fragility outcome: clustered OR 1.17 (95% CI 1.00 to 1.37; p = 0.0509)
- Significance fragility outcome: clustered OR 1.30 (95% CI 1.08 to 1.56; p = 0.0059)
- Composite fragility-count outcome (quasipoisson): clustered RR 1.16 (95% CI 1.09 to 1.23; p < 0.001)
- Framing diagnosis: the strongest underdiagnosed issue is unmeasured assumption burden; manuscript-ready intro/discussion text added
- Effect-size-tail exclusion (retain 99.0%): clustered OR 1.17 (95% CI 1.04 to 1.32; p = 0.0094)
- Cumulative large-review removal (top 5/10/20/30/40): clustered OR median 1.19 (2.5% to 97.5%: 1.14 to 1.22), retained-meta range 93.6% to 73.5%
- Non-sparse-events subset (17.4% retained): clustered OR 1.28 (95% CI 0.96 to 1.71; p = 0.0967), direction preserved with reduced precision
- Heterogeneity-present subset (`I2 > 0`, 39.0% retained): clustered OR 0.95 (95% CI 0.81 to 1.12; p = 0.5660), indicating attenuation under this restriction
- Clinical fragility outcome: clustered OR 1.40 (95% CI 1.21 to 1.61; p < 0.001)
- One-per-dataset bootstrap: median OR 1.25 (95% empirical interval 0.92 to 1.77)
- `k < 10` in no-`log_k` component model: OR 1.89 (95% CI 1.64 to 2.17)
- `k < 10` in no-`log_k` component model (cluster-robust): OR 1.89 (95% CI 1.59 to 2.25)
- Leave-one-dataset-out: OR median 1.15 (2.5% to 97.5%: 1.14 to 1.16; min-max: 1.14 to 1.17)
- Model performance: apparent AUC 0.681; row-wise 5-fold CV AUC 0.679; grouped-by-dataset 5-fold CV AUC 0.680
- Functional-form LR test (linear vs categorical score): p = 7.68e-05
- Threshold-grid sensitivity (clustered OR): median 1.25 (2.5% to 97.5%: 1.11 to 1.40; range: 1.11 to 1.42)
- Dominance-threshold sensitivity (clustered OR): median 1.15 (2.5% to 97.5%: 1.13 to 1.20; range: 1.13 to 1.20)
- Egger-threshold sensitivity (clustered OR): median 1.15 (2.5% to 97.5%: 1.14 to 1.15; range: 1.14 to 1.15)
- Assessable-only subset (`k >= 10`): clustered OR 1.31 (95% CI 1.07 to 1.61; p = 0.0084)
- Within-dataset permutation sensitivity: empirical two-sided p = 0.08
- Out-of-fold calibration: row-wise intercept ~0.00006, slope 0.983; grouped-by-dataset intercept ~-0.0011, slope 0.978
- Dataset-level bootstrap: OR median 1.15 (95% empirical interval 1.04 to 1.30)
- Complete-case outcome sensitivity: OR 1.13 (95% CI 1.01 to 1.26), cluster-robust OR 1.13 (95% CI 1.00 to 1.27)
- Tau2-cap sensitivity (clustered OR): median 1.15 (2.5% to 97.5%: 1.09 to 1.34; range: 1.09 to 1.35)
- High-leverage exclusion sensitivity (clustered): OR 1.15 (95% CI 1.01 to 1.30; p = 0.0308), retaining 93.2%

Interpretation after review: the direction of association is stable across modeling choices, while precision attenuates under strict within-dataset and fixed-effects sensitivity checks; this supports a real signal with non-trivial attribution uncertainty.

---

## 3) Response to Reviewers (RSM Style)

# Response to Reviewers (Research Synthesis Methods Style)

Manuscript: Assumption Debt in Cochrane Pairwise Meta-Analyses  
Dataset: Pairwise70 (`n = 4,424` meta-analyses across 474 datasets)

## Reviewer 1 (Methods): Non-independence across meta-analyses within reviews
**Comment:** The analysis appears to treat all meta-analyses as independent despite multiple analyses per Cochrane review.

**Response:** We agree. We added dataset-clustered robust standard errors to the primary and component models.

**Changes made:**
- `analysis/assumption_debt_modeling.R` updated to compute `vcovCL`-based inference.
- New outputs:
  - `analysis/output/assumption_debt_model_coefficients_cluster.csv`
  - `analysis/output/assumption_debt_component_model_coefficients_cluster.csv`

**Result impact:** Primary association remained positive: cluster-robust OR 1.15 (95% CI 1.02 to 1.30; p = 0.0212).

## Reviewer 2 (Robustness): Need stronger dependence sensitivity
**Comment:** Cluster-robust SEs alone may not fully capture dependence; provide a one-analysis-per-review sensitivity.

**Response:** We implemented a one-analysis-per-dataset bootstrap sensitivity (400 resamples; one random analysis per dataset each iteration).

**Changes made:**
- `analysis/assumption_debt_modeling.R` now includes the bootstrap block.
- New output:
  - `analysis/output/assumption_debt_one_per_dataset_bootstrap.csv`

**Result impact:** Median OR 1.25, empirical 95% interval 0.92 to 1.77 (direction consistent, wider uncertainty).

## Reviewer 3 (Model specification): Potential confounding by effect measure type
**Comment:** Associations could reflect differences across `RR`, `OR`, and `SMD` analyses.

**Response:** We added effect-measure-adjusted sensitivity models using `factor(measure)`, with and without clustered SEs.

**Changes made:**
- Added `fit_score_measure` to `analysis/assumption_debt_modeling.R`.
- New outputs:
  - `analysis/output/assumption_debt_model_coefficients_measure.csv`
  - `analysis/output/assumption_debt_model_coefficients_measure_cluster.csv`

**Result impact:** Association remained positive:
- Measure-adjusted OR 1.15 (95% CI 1.03 to 1.28; p = 0.0156)
- Measure-adjusted + cluster-robust OR 1.15 (95% CI 1.02 to 1.29; p = 0.0272)

## Reviewer 4 (Reporting): Missingness transparency in summary rates
**Comment:** Some fragility subrates were previously blank due to missing values.

**Response:** We corrected summary calculations using explicit `na.rm = TRUE`.

**Changes made:**
- Updated summary generation in `analysis/assumption_debt_modeling.R`.
- Refreshed output:
  - `analysis/output/assumption_debt_model_summary.csv`

## Reviewer 5 (Component interpretation): Potential collinearity-induced sign reversal for `k < 10`
**Comment:** The `k < 10` effect appears counterintuitive when `log_k` is also included.

**Response:** We agree. We quantified predictor correlation and added a no-`log_k` component sensitivity model.

**Changes made:**
- Added correlation diagnostics:
  - `analysis/output/assumption_debt_predictor_correlation.csv`
- Added no-`log_k` component model outputs:
  - `analysis/output/assumption_debt_component_model_coefficients_no_logk.csv`
  - `analysis/output/assumption_debt_component_model_coefficients_no_logk_cluster.csv`

**Result impact:** Inverse `k < 10` sign in the full component model was a collinearity artifact (`r = -0.80` between `k < 10` and `log_k`). In the no-`log_k` sensitivity model, `k < 10` was positively associated with fragility: OR 1.89 (95% CI 1.64 to 2.17), cluster-robust OR 1.89 (95% CI 1.59 to 2.25).

## Reviewer 6 (Small-study effects): Assessability not explicit
**Comment:** Egger-based small-study signal prevalence should report the assessable denominator.

**Response:** We added assessability diagnostics.

**Changes made:**
- New output:
  - `analysis/output/assumption_debt_small_study_assessability.csv`

**Result impact:** 46.2% of meta-analyses had `k >= 10`; small-study signal prevalence among assessable analyses was 26.2%.

## Reviewer 7 (Interpretation): Narrative should match sensitivity uncertainty
**Comment:** Main text should clearly separate primary and sensitivity evidence.

**Response:** We revised manuscript-ready results to present conventional, clustered, measure-adjusted, and bootstrap estimates side by side.

**Changes made:**
- Updated:
  - `analysis/output/assumption_debt_results_section.md`
- Added/updated review summary:
  - `analysis/output/multipersona_rsm_review.md`

## Reviewer 8 (Influence analysis): Confirm effect is not driven by one dataset
**Comment:** Please show that no single Cochrane review unduly influences the main assumption-debt result.

**Response:** We added a leave-one-dataset-out sensitivity analysis across all 474 datasets.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_leave_one_dataset_out.csv`
  - `analysis/output/assumption_debt_leave_one_dataset_out_summary.csv`

**Result impact:** Main OR remained stable across all leave-one-out refits (median 1.15; 2.5% to 97.5%: 1.14 to 1.16; full range 1.14 to 1.17), indicating no single dataset dominates inference.

## Reviewer 9 (Model diagnostics): Show predictive optimism and score functional form
**Comment:** Please report out-of-sample discrimination and test whether a linear score term is adequate.

**Response:** We added both row-wise and grouped-by-dataset 5-fold cross-validated AUC, plus a likelihood-ratio test comparing linear vs categorical score specification.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_model_performance.csv`
  - `analysis/output/assumption_debt_score_nonlinearity_test.csv`
  - `analysis/output/assumption_debt_model_coefficients_score_categorical.csv`
  - `analysis/output/assumption_debt_model_coefficients_score_categorical_cluster.csv`

**Result impact:** Apparent AUC was 0.681, row-wise 5-fold CV AUC was 0.679, and grouped-by-dataset 5-fold CV AUC was 0.680 (limited optimism and limited leakage signal). The linear-vs-categorical LR test indicated nonlinearity (p = 7.68e-05), so we now report score-stratified gradients alongside per-point ORs.

## Reviewer 10 (Threshold robustness): Address arbitrariness of `k` and `I2` cutoffs
**Comment:** The assumption-debt score may depend on chosen thresholds (e.g., `k < 10`, `I2 >= 50`).

**Response:** We added a threshold-grid sensitivity analysis across plausible alternatives.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_threshold_sensitivity.csv`
  - `analysis/output/assumption_debt_threshold_sensitivity_summary.csv`

**Result impact:** Cluster-robust ORs for the score remained positive across all 9 combinations of `k` and `I2` cutoffs (median 1.25; 2.5% to 97.5%: 1.11 to 1.40; full range 1.11 to 1.42).

## Reviewer 11 (Conservative null check): Assess residual structure under permutation
**Comment:** Provide a strict null-structure sensitivity analysis to assess whether associations persist beyond within-dataset structure.

**Response:** We added within-dataset permutation sensitivity for the score effect.

**Changes made:**
- New output:
  - `analysis/output/assumption_debt_permutation_summary.csv`

**Result impact:** The permutation empirical two-sided p-value was 0.08. We now frame the primary finding as directionally robust but with conservative-null attenuation, and avoid mechanistic over-interpretation.

## Reviewer 12 (Calibration realism): Add out-of-fold calibration
**Comment:** In-sample calibration can be optimistic; please report out-of-fold calibration.

**Response:** We added row-wise and grouped-by-dataset 5-fold out-of-fold calibration intercept and slope.

**Changes made:**
- Updated output:
  - `analysis/output/assumption_debt_model_performance.csv`

**Result impact:** Out-of-fold calibration remained acceptable in both schemes (row-wise intercept ~0.00006, slope 0.983; grouped-by-dataset intercept ~-0.0011, slope 0.978), supporting model transport realism within the dataset.

## Reviewer 13 (Transparency): Provide one table summarizing all robustness checks
**Comment:** The number of sensitivity analyses makes cross-checking difficult.

**Response:** We added a single robustness matrix consolidating estimates and intervals from all key checks.

**Changes made:**
- New output:
  - `analysis/output/assumption_debt_robustness_matrix.csv`

## Reviewer 14 (Cluster-resampling realism): Add dataset-level bootstrap
**Comment:** One-per-dataset bootstrap may be too conservative because it discards within-dataset analysis multiplicity.

**Response:** We added a dataset-level bootstrap that resamples entire datasets with replacement while preserving within-dataset structure.

**Changes made:**
- New output:
  - `analysis/output/assumption_debt_dataset_bootstrap_summary.csv`

**Result impact:** Dataset-level bootstrap OR median was 1.15 (95% empirical interval 1.04 to 1.30), aligning closely with primary and cluster-robust estimates.

## Reviewer 15 (Outcome missingness): Avoid implicit non-fragile coding bias
**Comment:** Coding missing fragility outcomes as non-fragile may bias effect estimates.

**Response:** We added complete-case outcome sensitivity models for the primary score effect.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_model_coefficients_complete_case.csv`
  - `analysis/output/assumption_debt_model_coefficients_complete_case_cluster.csv`

**Result impact:** Complete-case association remained positive (OR 1.13, 95% CI 1.01 to 1.26), with cluster-robust complete-case estimate OR 1.13 (95% CI 1.00 to 1.27).

## Reviewer 16 (Variance-specification sensitivity): Dependence on tau2 capping
**Comment:** The primary model caps tau2; please show whether conclusions depend on the cap choice.

**Response:** We added a tau2-cap sensitivity grid comparing cap quantiles 0.95, 0.99, and uncapped.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_tau2_cap_sensitivity.csv`
  - `analysis/output/assumption_debt_tau2_cap_sensitivity_summary.csv`

**Result impact:** Cluster-robust ORs remained positive across cap choices (median 1.15; 2.5% to 97.5%: 1.09 to 1.34; range 1.09 to 1.35), indicating directional stability with moderate magnitude sensitivity.

## Reviewer 17 (Influence/outlier robustness): Exclude high-leverage analyses
**Comment:** Please evaluate whether dominant or extreme-heterogeneity analyses drive the main effect.

**Response:** We added a high-leverage exclusion sensitivity, removing analyses with max study weight >= 0.70 or tau2 above the 99th percentile.

**Changes made:**
- New output:
  - `analysis/output/assumption_debt_high_leverage_sensitivity.csv`

**Result impact:** After excluding high-leverage analyses (retaining 93.2% of meta-analyses), the cluster-robust score effect remained positive: OR 1.15 (95% CI 1.01 to 1.30; p = 0.0308).

## Reviewer 18 (Within-vs-between decomposition): Separate cluster-level and within-cluster score signal
**Comment:** The pooled model may mix between-review and within-review information; please decompose these components.

**Response:** We added a within-between (Mundlak-style) decomposition model with clustered inference.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_within_between_coefficients.csv`
  - `analysis/output/assumption_debt_within_between_coefficients_cluster.csv`

**Result impact:** The within-dataset component was positive but imprecise (OR 1.09, 95% CI 0.96 to 1.22; p = 0.1749), while the between-dataset component was stronger and positive (OR 1.35, 95% CI 1.06 to 1.73; p = 0.0164). We now state explicitly that part of the signal is contextual across reviews.

## Reviewer 19 (Dataset-level confounding): Add a fixed-effects sensitivity
**Comment:** Please test whether the association remains under dataset fixed effects.

**Response:** We added a dataset fixed-effects linear probability sensitivity model with clustered standard errors.

**Changes made:**
- New output:
  - `analysis/output/assumption_debt_fixed_effects_lpm.csv`

**Result impact:** The per-point score effect remained directionally positive on the risk-difference scale (RD 0.023; 95% CI -0.002 to 0.048; p = 0.0746), with expected precision attenuation under stricter confounding control.

## Reviewer 20 (Cross-review consistency): Add a review-level aggregate check
**Comment:** Please verify whether the association remains when analyses are collapsed to the dataset level.

**Response:** We added a dataset-level aggregate binomial model using review-level fragile counts and mean predictors.

**Changes made:**
- New output:
  - `analysis/output/assumption_debt_dataset_level_model.csv`

**Result impact:** The review-level association remained positive (OR per +1 mean score 1.27; 95% CI 1.03 to 1.58; p = 0.0281), supporting cross-review concordance.

## Reviewer 21 (Effect modification): Test score-by-measure interaction
**Comment:** Please evaluate whether the assumption-debt association differs by effect-measure family.

**Response:** We added a score-by-measure interaction model and exported clustered measure-specific slope estimates.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_measure_interaction_test.csv`
  - `analysis/output/assumption_debt_measure_specific_effects_cluster.csv`

**Result impact:** The global interaction likelihood-ratio test was not statistically compelling (p = 0.3039), so we found no strong evidence that the score effect materially differs by measure family in this dataset.

## Reviewer 22 (Measure-family dominance): Add leave-one-measure-family-out sensitivity
**Comment:** A non-significant interaction test may not exclude practical dominance by one measure family; please perform exclusion sensitivity.

**Response:** We added leave-one-measure-family-out sensitivity by excluding `GIV`, `OR`, and `SMD` in turn and refitting the primary model.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_leave_one_measure_out.csv`
  - `analysis/output/assumption_debt_leave_one_measure_out_summary.csv`

**Result impact:** Cluster-robust ORs remained directionally positive across all exclusions (median 1.16; 2.5% to 97.5%: 1.12 to 1.31). Precision attenuated when excluding `OR` due to a much smaller retained sample, but no exclusion reversed direction.

## Reviewer 23 (Large-review dominance): Exclude high-volume datasets
**Comment:** Please verify that very large reviews are not disproportionately driving the association.

**Response:** We added a top-decile dataset-size exclusion sensitivity.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_large_review_sensitivity.csv`
  - `analysis/output/assumption_debt_large_review_excluded_datasets.csv`

**Result impact:** After excluding the largest 10% of datasets by analysis count (54 datasets removed; 67.3% of meta-analyses retained), the cluster-robust association remained positive (OR 1.20; 95% CI 1.03 to 1.39; p = 0.0180).

## Reviewer 24 (Contribution imbalance): Use dataset-equal weighting
**Comment:** Please show that the result does not depend on datasets with many analyses receiving disproportionate row-level influence.

**Response:** We added a dataset-equal weighted sensitivity model (each dataset contributes equal total weight), with clustered inference.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_model_coefficients_dataset_equal_weight.csv`
  - `analysis/output/assumption_debt_model_coefficients_dataset_equal_weight_cluster.csv`

**Result impact:** The association remained positive and slightly stronger under equal-dataset weighting (OR 1.24; 95% CI 1.11 to 1.39; p = 0.0002), with clustered estimate OR 1.24 (95% CI 1.06 to 1.46; p = 0.0074).

## Reviewer 25 (Information adequacy): Stratify by number of studies
**Comment:** Please confirm whether the score effect persists among meta-analyses with at least 10 studies.

**Response:** We added `k`-stratified clustered models (`k < 10` and `k >= 10`) and a clustered between-strata beta-difference test.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_k_strata_effects.csv`
  - `analysis/output/assumption_debt_k_strata_difference_test.csv`

**Result impact:** The score effect remained positive in both strata: OR 1.63 (95% CI 1.33 to 2.00; p < 0.001) for `k < 10` and OR 1.25 (95% CI 1.04 to 1.51; p = 0.0180) for `k >= 10`. The between-strata beta-difference test was suggestive but not definitive (p = 0.0631).

## Reviewer 26 (Outcome definition): Separate direction and significance fragility outcomes
**Comment:** Please show whether the score association holds for both fragility components individually.

**Response:** We added separate outcome models for `direction_fragile` and `sig_fragile` with the same covariate adjustment and clustered inference.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_model_coefficients_direction.csv`
  - `analysis/output/assumption_debt_model_coefficients_direction_cluster.csv`
  - `analysis/output/assumption_debt_model_coefficients_significance.csv`
  - `analysis/output/assumption_debt_model_coefficients_significance_cluster.csv`

**Result impact:** The score association remained positive for both outcomes: direction fragility clustered OR 1.17 (95% CI 1.00 to 1.37; p = 0.0509) and significance fragility clustered OR 1.30 (95% CI 1.08 to 1.56; p = 0.0059).

## Reviewer 27 (Effect-size influence): Exclude extreme effect-magnitude tail
**Comment:** Please verify the main result is not driven by extreme absolute effect estimates.

**Response:** We added an effect-size-tail exclusion sensitivity, removing analyses above the 99th percentile of `abs_estimate`.

**Changes made:**
- New output:
  - `analysis/output/assumption_debt_effect_tail_sensitivity.csv`

**Result impact:** After excluding the top 1% of effect magnitudes (retaining 99.0% of analyses), the clustered score effect remained positive: OR 1.17 (95% CI 1.04 to 1.32; p = 0.0094).

## Reviewer 28 (Progressive dominance): Apply cumulative large-review removal
**Comment:** A single top-decile exclusion may be threshold-dependent; please evaluate progressive removal of the largest reviews.

**Response:** We added a cumulative large-review removal sensitivity across top 5/10/20/30/40 datasets by analysis count.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_large_review_cumulative_sensitivity.csv`
  - `analysis/output/assumption_debt_large_review_cumulative_summary.csv`

**Result impact:** Clustered ORs remained positive across all removal levels (median 1.19; 2.5% to 97.5%: 1.14 to 1.22), with retained meta-analyses ranging from 93.6% to 73.5%.

## Reviewer 29 (Context generalizability): Evaluate non-sparse-events subset
**Comment:** Since sparse-event analyses are common, please show the score association in non-sparse-event settings.

**Response:** We added a non-sparse-events subset sensitivity model (`sparse_events_signal == 0`).

**Changes made:**
- New output:
  - `analysis/output/assumption_debt_non_sparse_events_sensitivity.csv`

**Result impact:** In the non-sparse subset (17.4% of analyses; n = 770), the clustered OR remained directionally positive (1.28) but with wider uncertainty (95% CI 0.96 to 1.71; p = 0.0967), consistent with reduced precision in the smaller subset.

## Reviewer 30 (Heterogeneity context): Restrict to non-zero heterogeneity analyses
**Comment:** Please evaluate the score association in analyses with `I2 > 0`.

**Response:** We added an `I2 > 0` subset sensitivity model with clustered inference.

**Changes made:**
- New output:
  - `analysis/output/assumption_debt_i2_positive_sensitivity.csv`

**Result impact:** In the heterogeneity-present subset (39.0% of analyses; n = 1,724), the clustered OR was 0.95 (95% CI 0.81 to 1.12; p = 0.5660), indicating attenuation and reduced directional clarity under this restriction.

## Reviewer 31 (Clinical construct validity): Evaluate clinical fragility outcome
**Comment:** Please show whether the assumption-debt association is also present for clinical fragility.

**Response:** We added clinical-fragility outcome models using the same covariate structure and clustered inference.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_model_coefficients_clinical.csv`
  - `analysis/output/assumption_debt_model_coefficients_clinical_cluster.csv`

**Result impact:** The clinical-fragility association was positive and robust: clustered OR 1.40 (95% CI 1.21 to 1.61; p < 0.001).

## Reviewer 32 (Outcome intensity): Evaluate composite fragility-count outcome
**Comment:** Binary fragility outcomes may hide severity gradients when both direction and significance fragility co-occur.

**Response:** We added quasipoisson models for composite fragility count (0-2) using the same covariate structure, with clustered inference by dataset.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_model_coefficients_composite_count.csv`
  - `analysis/output/assumption_debt_model_coefficients_composite_count_cluster.csv`

**Result impact:** The composite-count association was positive and concordant: clustered RR 1.16 (95% CI 1.09 to 1.23; p < 0.001).

## Reviewer 33 (Conceptual framing): State the single biggest underdiagnosed flaw
**Comment:** The paper should explicitly name the primary underdiagnosed methodological flaw and align the Discussion around that claim.

**Response:** We added a manuscript-ready framing brief for Introduction and Discussion that identifies the core flaw as unmeasured assumption burden ("assumption debt"), and explicitly calibrates causal language using conservative sensitivity findings.

**Changes made:**
- New output:
  - `analysis/output/assumption_debt_intro_discussion_framing.md`

**Result impact:** The argument is now explicit and testable: higher assumption burden consistently tracks higher fragility, while conservative null/decomposition checks motivate cautious mechanistic claims.

## Reviewer 34 (Effect-scale interpretability): Report RR sensitivity for binary fragility
**Comment:** ORs can be difficult to interpret with non-rare outcomes; please provide a risk-ratio scale sensitivity.

**Response:** We added a binary modified-Poisson sensitivity model for `fragile_any` with clustered inference by dataset.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_model_coefficients_rr.csv`
  - `analysis/output/assumption_debt_model_coefficients_rr_cluster.csv`

**Result impact:** The score association remained positive on the RR scale: RR 1.08 (95% CI 1.02 to 1.15; p = 0.0137), cluster-robust RR 1.08 (95% CI 1.01 to 1.16; p = 0.0243).

## Reviewer 35 (Assessability structure): Test dependence on Egger-assessable component
**Comment:** The Egger-based small-study component is only assessable when `k >= 10`; please verify the main result is not an artifact of this assessability pattern.

**Response:** We added a no-Egger score sensitivity that excludes the Egger component and refits the primary model with the same covariate structure, including clustered inference.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_model_coefficients_no_egger.csv`
  - `analysis/output/assumption_debt_model_coefficients_no_egger_cluster.csv`

**Result impact:** The no-Egger score association remained positive: OR 1.18 (95% CI 1.05 to 1.32; p = 0.0069), cluster-robust OR 1.18 (95% CI 1.03 to 1.34; p = 0.0151).

## Reviewer 36 (Outcome severity definition): Evaluate strict joint-fragility endpoint
**Comment:** Please test whether results persist under a stricter fragility definition requiring both direction and significance fragility.

**Response:** We added a strict joint-fragility sensitivity model (`direction_fragile AND sig_fragile`) with the same covariate structure and clustered inference.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_model_coefficients_both.csv`
  - `analysis/output/assumption_debt_model_coefficients_both_cluster.csv`

**Result impact:** The strict-joint outcome association remained positive and larger: OR 4.06 (95% CI 2.22 to 7.41; p < 0.001), cluster-robust OR 4.06 (95% CI 2.28 to 7.21; p < 0.001).

## Reviewer 37 (Severity scale interpretability): Confirm strict-joint result on RR scale
**Comment:** Please verify that strict joint-fragility findings are not dependent on OR link interpretation.

**Response:** We added modified-Poisson RR sensitivity models for the strict joint-fragility endpoint with clustered inference.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_model_coefficients_both_rr.csv`
  - `analysis/output/assumption_debt_model_coefficients_both_rr_cluster.csv`

**Result impact:** The strict-joint signal remained strongly positive on RR scale: RR 3.76 (95% CI 2.04 to 6.93; p < 0.001), cluster-robust RR 3.76 (95% CI 2.27 to 6.25; p < 0.001).

## Reviewer 38 (Severe-endpoint contribution balance): Equal-weight strict-joint sensitivity
**Comment:** Please verify that the strict joint-fragility finding is not driven by high-volume datasets.

**Response:** We added dataset-equal weighting sensitivity for strict joint fragility, assigning equal total weight to each dataset in the strict-endpoint subset, with clustered inference.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_model_coefficients_both_dataset_equal_weight.csv`
  - `analysis/output/assumption_debt_model_coefficients_both_dataset_equal_weight_cluster.csv`

**Result impact:** The strict-joint association remained strongly positive under balanced-contribution weighting: OR 5.45 (95% CI 2.93 to 10.15; p < 0.001), cluster-robust OR 5.45 (95% CI 2.75 to 10.80; p < 0.001).

## Reviewer 39 (Clinical scale interpretability): Report clinical fragility on RR scale
**Comment:** Please provide clinical-fragility sensitivity on a risk-ratio scale to complement OR estimates.

**Response:** We added modified-Poisson RR sensitivity models for clinical fragility with clustered inference.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_model_coefficients_clinical_rr.csv`
  - `analysis/output/assumption_debt_model_coefficients_clinical_rr_cluster.csv`

**Result impact:** Clinical-fragility association remained positive on RR scale: RR 1.25 (95% CI 1.15 to 1.35; p < 0.001), cluster-robust RR 1.25 (95% CI 1.13 to 1.37; p < 0.001).

## Reviewer 40 (Clinical contribution balance): Equal-weight clinical sensitivity
**Comment:** Please verify that clinical-endpoint findings are not driven by datasets contributing many analyses.

**Response:** We added dataset-equal weighting sensitivity for clinical fragility, assigning equal total weight to each dataset in the clinical subset, with clustered inference.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_model_coefficients_clinical_dataset_equal_weight.csv`
  - `analysis/output/assumption_debt_model_coefficients_clinical_dataset_equal_weight_cluster.csv`

**Result impact:** Clinical association remained positive under balanced-contribution weighting: OR 1.32 (95% CI 1.16 to 1.49; p < 0.001), cluster-robust OR 1.32 (95% CI 1.08 to 1.60; p = 0.0053).

## Consolidated post-revision conclusion
Across all prespecified and added sensitivity analyses, the estimated association between assumption debt and fragility is generally positive but not uniform across every restricted subset. Precision attenuates under stricter dependence controls (including within-between decomposition and dataset fixed-effects sensitivity), while review-level aggregate modeling confirms cross-review directional concordance. We found no strong measure-family effect modification signal, leave-one-measure-family-out analyses did not show directional reversal, exclusion of the largest reviews did not remove the association, cumulative large-review removal preserved positive direction across progressively stronger exclusions, dataset-equal weighting preserved the effect under balanced contribution assumptions, `k`-stratified analyses retained positive direction in both sparse and better-powered subsets, and outcome-specific models supported positive associations for direction, significance, clinical fragility, strict joint fragility, and composite fragility-count definitions. Binary modified-Poisson modeling confirmed direction on the RR scale for primary, strict-joint, and clinical outcomes; no-Egger score sensitivity confirmed direction under Egger-assessability stress testing; strict-joint dataset-equal weighting confirmed severe-endpoint stability; and clinical dataset-equal weighting confirmed clinical-endpoint stability under balanced contribution assumptions. Exclusion of extreme effect-size tails did not remove the association. Non-sparse-events subset analysis retained positive direction with expected precision loss, whereas the `I2 > 0` subset attenuated toward null. Component-level interpretation requires collinearity-aware specification, influence analysis indicates the main effect is not driven by any single dataset, functional-form checks indicate nonlinearity that is now explicitly reported, threshold-grid testing shows results are not an artifact of one specific cutoff choice, and conservative permutation analysis indicates residual attribution uncertainty. We therefore frame the central underdiagnosed issue as unmeasured assumption burden, interpreted as a stability-risk marker rather than a definitive standalone causal mechanism.

---

## 4) Primary Numeric Outputs (CSV files)

- `assumption_debt_model_summary.csv`
- `assumption_debt_model_coefficients.csv`
- `assumption_debt_model_coefficients_no_egger.csv`
- `assumption_debt_model_coefficients_no_egger_cluster.csv`
- `assumption_debt_model_coefficients_rr.csv`
- `assumption_debt_model_coefficients_rr_cluster.csv`
- `assumption_debt_model_coefficients_assessable.csv`
- `assumption_debt_model_coefficients_assessable_cluster.csv`
- `assumption_debt_model_coefficients_cluster.csv`
- `assumption_debt_model_coefficients_complete_case.csv`
- `assumption_debt_model_coefficients_complete_case_cluster.csv`
- `assumption_debt_model_coefficients_direction.csv`
- `assumption_debt_model_coefficients_direction_cluster.csv`
- `assumption_debt_model_coefficients_significance.csv`
- `assumption_debt_model_coefficients_significance_cluster.csv`
- `assumption_debt_model_coefficients_clinical.csv`
- `assumption_debt_model_coefficients_clinical_cluster.csv`
- `assumption_debt_model_coefficients_clinical_rr.csv`
- `assumption_debt_model_coefficients_clinical_rr_cluster.csv`
- `assumption_debt_model_coefficients_clinical_dataset_equal_weight.csv`
- `assumption_debt_model_coefficients_clinical_dataset_equal_weight_cluster.csv`
- `assumption_debt_model_coefficients_both.csv`
- `assumption_debt_model_coefficients_both_cluster.csv`
- `assumption_debt_model_coefficients_both_rr.csv`
- `assumption_debt_model_coefficients_both_rr_cluster.csv`
- `assumption_debt_model_coefficients_both_dataset_equal_weight.csv`
- `assumption_debt_model_coefficients_both_dataset_equal_weight_cluster.csv`
- `assumption_debt_model_coefficients_composite_count.csv`
- `assumption_debt_model_coefficients_composite_count_cluster.csv`
- `assumption_debt_model_coefficients_measure.csv`
- `assumption_debt_model_coefficients_measure_cluster.csv`
- `assumption_debt_model_coefficients_dataset_equal_weight.csv`
- `assumption_debt_model_coefficients_dataset_equal_weight_cluster.csv`
- `assumption_debt_measure_interaction_test.csv`
- `assumption_debt_measure_specific_effects_cluster.csv`
- `assumption_debt_leave_one_measure_out.csv`
- `assumption_debt_leave_one_measure_out_summary.csv`
- `assumption_debt_large_review_sensitivity.csv`
- `assumption_debt_large_review_excluded_datasets.csv`
- `assumption_debt_large_review_cumulative_sensitivity.csv`
- `assumption_debt_large_review_cumulative_summary.csv`
- `assumption_debt_k_strata_effects.csv`
- `assumption_debt_k_strata_difference_test.csv`
- `assumption_debt_effect_tail_sensitivity.csv`
- `assumption_debt_non_sparse_events_sensitivity.csv`
- `assumption_debt_i2_positive_sensitivity.csv`
- `assumption_debt_within_between_coefficients.csv`
- `assumption_debt_within_between_coefficients_cluster.csv`
- `assumption_debt_fixed_effects_lpm.csv`
- `assumption_debt_dataset_level_model.csv`
- `assumption_debt_component_model_coefficients.csv`
- `assumption_debt_component_model_coefficients_cluster.csv`
- `assumption_debt_component_model_coefficients_no_logk.csv`
- `assumption_debt_component_model_coefficients_no_logk_cluster.csv`
- `assumption_debt_model_coefficients_score_categorical.csv`
- `assumption_debt_model_coefficients_score_categorical_cluster.csv`
- `assumption_debt_one_per_dataset_bootstrap.csv`
- `assumption_debt_dataset_bootstrap_summary.csv`
- `assumption_debt_leave_one_dataset_out.csv`
- `assumption_debt_leave_one_dataset_out_summary.csv`
- `assumption_debt_threshold_sensitivity.csv`
- `assumption_debt_threshold_sensitivity_summary.csv`
- `assumption_debt_dominance_threshold_sensitivity.csv`
- `assumption_debt_dominance_threshold_sensitivity_summary.csv`
- `assumption_debt_egger_threshold_sensitivity.csv`
- `assumption_debt_egger_threshold_sensitivity_summary.csv`
- `assumption_debt_tau2_cap_sensitivity.csv`
- `assumption_debt_tau2_cap_sensitivity_summary.csv`
- `assumption_debt_high_leverage_sensitivity.csv`
- `assumption_debt_permutation_summary.csv`
- `assumption_debt_robustness_matrix.csv`
- `assumption_debt_specification_curve.csv`
- `assumption_debt_multiverse_consistency.csv`
- `assumption_debt_multiverse_sign_test.csv`
- `assumption_debt_model_performance.csv`
- `assumption_debt_score_nonlinearity_test.csv`
- `assumption_debt_components.csv`
- `assumption_debt_by_score.csv`
- `assumption_debt_predictor_correlation.csv`
- `assumption_debt_small_study_assessability.csv`

---

## 5) Figures and Manifests

- `assumption_debt_figure_manifest.md`
- `figures_assumption_debt/figure1_assumption_debt_components.png`
- `figures_assumption_debt/figure2_fragility_gradient.png`
- `figures_assumption_debt/figure3_adjusted_or_forest.png`

---

## 6) Full File Inventory in ZIP (98 files)

- `submission_packet_assumption_debt.md`
- `assumption_debt_results_section.md`
- `multipersona_rsm_review.md`
- `response_to_reviewers_rsm_assumption_debt.md`
- `assumption_debt_report.md`
- `assumption_debt_intro_discussion_framing.md`
- `publishability_hardening_checklist.md`
- `preregistration_style_analysis_plan.md`
- `claims_language_guide.md`
- `abstract_rsm_250w.md`
- `cover_letter_rsm.md`
- `manuscript_plos_one_draft.md`
- `cover_letter_plos_one.md`
- `plos_one_submission_checklist.md`
- `assumption_debt_model_summary.csv`
- `assumption_debt_model_coefficients.csv`
- `assumption_debt_model_coefficients_no_egger.csv`
- `assumption_debt_model_coefficients_no_egger_cluster.csv`
- `assumption_debt_model_coefficients_rr.csv`
- `assumption_debt_model_coefficients_rr_cluster.csv`
- `assumption_debt_model_coefficients_assessable.csv`
- `assumption_debt_model_coefficients_assessable_cluster.csv`
- `assumption_debt_model_coefficients_cluster.csv`
- `assumption_debt_model_coefficients_complete_case.csv`
- `assumption_debt_model_coefficients_complete_case_cluster.csv`
- `assumption_debt_model_coefficients_direction.csv`
- `assumption_debt_model_coefficients_direction_cluster.csv`
- `assumption_debt_model_coefficients_significance.csv`
- `assumption_debt_model_coefficients_significance_cluster.csv`
- `assumption_debt_model_coefficients_clinical.csv`
- `assumption_debt_model_coefficients_clinical_cluster.csv`
- `assumption_debt_model_coefficients_clinical_rr.csv`
- `assumption_debt_model_coefficients_clinical_rr_cluster.csv`
- `assumption_debt_model_coefficients_clinical_dataset_equal_weight.csv`
- `assumption_debt_model_coefficients_clinical_dataset_equal_weight_cluster.csv`
- `assumption_debt_model_coefficients_both.csv`
- `assumption_debt_model_coefficients_both_cluster.csv`
- `assumption_debt_model_coefficients_both_rr.csv`
- `assumption_debt_model_coefficients_both_rr_cluster.csv`
- `assumption_debt_model_coefficients_both_dataset_equal_weight.csv`
- `assumption_debt_model_coefficients_both_dataset_equal_weight_cluster.csv`
- `assumption_debt_model_coefficients_composite_count.csv`
- `assumption_debt_model_coefficients_composite_count_cluster.csv`
- `assumption_debt_model_coefficients_measure.csv`
- `assumption_debt_model_coefficients_measure_cluster.csv`
- `assumption_debt_model_coefficients_dataset_equal_weight.csv`
- `assumption_debt_model_coefficients_dataset_equal_weight_cluster.csv`
- `assumption_debt_measure_interaction_test.csv`
- `assumption_debt_measure_specific_effects_cluster.csv`
- `assumption_debt_leave_one_measure_out.csv`
- `assumption_debt_leave_one_measure_out_summary.csv`
- `assumption_debt_large_review_sensitivity.csv`
- `assumption_debt_large_review_excluded_datasets.csv`
- `assumption_debt_large_review_cumulative_sensitivity.csv`
- `assumption_debt_large_review_cumulative_summary.csv`
- `assumption_debt_k_strata_effects.csv`
- `assumption_debt_k_strata_difference_test.csv`
- `assumption_debt_effect_tail_sensitivity.csv`
- `assumption_debt_non_sparse_events_sensitivity.csv`
- `assumption_debt_i2_positive_sensitivity.csv`
- `assumption_debt_within_between_coefficients.csv`
- `assumption_debt_within_between_coefficients_cluster.csv`
- `assumption_debt_fixed_effects_lpm.csv`
- `assumption_debt_dataset_level_model.csv`
- `assumption_debt_component_model_coefficients.csv`
- `assumption_debt_component_model_coefficients_cluster.csv`
- `assumption_debt_component_model_coefficients_no_logk.csv`
- `assumption_debt_component_model_coefficients_no_logk_cluster.csv`
- `assumption_debt_model_coefficients_score_categorical.csv`
- `assumption_debt_model_coefficients_score_categorical_cluster.csv`
- `assumption_debt_one_per_dataset_bootstrap.csv`
- `assumption_debt_dataset_bootstrap_summary.csv`
- `assumption_debt_leave_one_dataset_out.csv`
- `assumption_debt_leave_one_dataset_out_summary.csv`
- `assumption_debt_threshold_sensitivity.csv`
- `assumption_debt_threshold_sensitivity_summary.csv`
- `assumption_debt_dominance_threshold_sensitivity.csv`
- `assumption_debt_dominance_threshold_sensitivity_summary.csv`
- `assumption_debt_egger_threshold_sensitivity.csv`
- `assumption_debt_egger_threshold_sensitivity_summary.csv`
- `assumption_debt_tau2_cap_sensitivity.csv`
- `assumption_debt_tau2_cap_sensitivity_summary.csv`
- `assumption_debt_high_leverage_sensitivity.csv`
- `assumption_debt_permutation_summary.csv`
- `assumption_debt_robustness_matrix.csv`
- `assumption_debt_specification_curve.csv`
- `assumption_debt_multiverse_consistency.csv`
- `assumption_debt_multiverse_sign_test.csv`
- `assumption_debt_model_performance.csv`
- `assumption_debt_score_nonlinearity_test.csv`
- `assumption_debt_components.csv`
- `assumption_debt_by_score.csv`
- `assumption_debt_predictor_correlation.csv`
- `assumption_debt_small_study_assessability.csv`
- `assumption_debt_figure_manifest.md`
- `figures_assumption_debt/figure1_assumption_debt_components.png`
- `figures_assumption_debt/figure2_fragility_gradient.png`
- `figures_assumption_debt/figure3_adjusted_or_forest.png`
