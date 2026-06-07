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

## Reviewer 41 (Synthesis transparency): Quantify cross-specification consistency
**Comment:** The manuscript reports many sensitivity analyses; please provide a formal multiverse-style summary showing how often direction and inference remain concordant across specifications.

**Response:** We added a specification-curve export across directional robustness checks and a multiverse consistency summary table that quantifies sign consistency and CI support for positive direction.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_specification_curve.csv`
  - `analysis/output/assumption_debt_multiverse_consistency.csv`

**Result impact:** Directional concordance was high across the robustness multiverse: 51/52 directional checks (98.1%) were positive, and 45/52 (86.5%) had confidence intervals excluding the null in the positive direction.

## Reviewer 42 (Multiverse inference): Add formal sign-predominance test
**Comment:** Please complement multiverse consistency percentages with an inferential test against a neutral 50% sign-null.

**Response:** We added an exact one-sided binomial sign test across directional robustness checks.

**Changes made:**
- New output:
  - `analysis/output/assumption_debt_multiverse_sign_test.csv`

**Result impact:** Positive-direction predominance was far beyond a 50% sign-null (51/52 positive; one-sided exact p = 1.18e-14; exact CI for positive share 0.912 to 1.000).

## Reviewer 43 (Component-threshold arbitrariness): Stress-test dominance cutoff
**Comment:** Please show that results are not an artifact of using one specific dominance cutoff (`max_weight_share >= 0.50`) in the score.

**Response:** We added a dominance-threshold sensitivity varying the dominance component cutoff over 0.40, 0.50, and 0.60, while keeping the same model structure and clustered inference.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_dominance_threshold_sensitivity.csv`
  - `analysis/output/assumption_debt_dominance_threshold_sensitivity_summary.csv`

**Result impact:** Clustered score ORs remained positive at all dominance cutoffs (0.40: 1.20, 95% CI 1.07 to 1.35; 0.50: 1.15, 95% CI 1.02 to 1.30; 0.60: 1.13, 95% CI 1.00 to 1.27). Across these models, clustered OR median was 1.15 (2.5% to 97.5%: 1.13 to 1.20).

## Reviewer 44 (Small-study threshold arbitrariness): Stress-test Egger cutoff
**Comment:** Please verify that results are not dependent on the specific Egger cutoff (`p < 0.10`) used to define small-study signal in the score.

**Response:** We added Egger-threshold sensitivity varying the small-study component cutoff over 0.05, 0.10, and 0.20, with the same model structure and clustered inference.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_egger_threshold_sensitivity.csv`
  - `analysis/output/assumption_debt_egger_threshold_sensitivity_summary.csv`

**Result impact:** Clustered score ORs remained positive at all Egger cutoffs (0.05: 1.14, 95% CI 1.01 to 1.29; 0.10: 1.15, 95% CI 1.02 to 1.30; 0.20: 1.15, 95% CI 1.02 to 1.31). Across these models, clustered OR median was 1.15 (2.5% to 97.5%: 1.14 to 1.15).

## Reviewer 45 (Assessability restriction): k >= 10 subset verification
**Comment:** Please verify that the primary association remains when restricting analyses to the Egger-assessable stratum (`k >= 10`).

**Response:** We added an assessable-only sensitivity model restricted to `k_diag >= 10`, using the same covariate structure with and without clustered inference.

**Changes made:**
- New outputs:
  - `analysis/output/assumption_debt_model_coefficients_assessable.csv`
  - `analysis/output/assumption_debt_model_coefficients_assessable_cluster.csv`

**Result impact:** The association remained positive in the assessable subset: OR 1.31 (95% CI 1.09 to 1.59; p = 0.0050), cluster-robust OR 1.31 (95% CI 1.07 to 1.61; p = 0.0084).

## Consolidated post-revision conclusion
Across all prespecified and added sensitivity analyses, the estimated association between assumption debt and fragility is generally positive but not uniform across every restricted subset. Precision attenuates under stricter dependence controls (including within-between decomposition and dataset fixed-effects sensitivity), while review-level aggregate modeling confirms cross-review directional concordance. We found no strong measure-family effect modification signal, leave-one-measure-family-out analyses did not show directional reversal, exclusion of the largest reviews did not remove the association, cumulative large-review removal preserved positive direction across progressively stronger exclusions, dataset-equal weighting preserved the effect under balanced contribution assumptions, `k`-stratified analyses retained positive direction in both sparse and better-powered subsets, and outcome-specific models supported positive associations for direction, significance, clinical fragility, strict joint fragility, and composite fragility-count definitions. Binary modified-Poisson modeling confirmed direction on the RR scale for primary, strict-joint, and clinical outcomes; no-Egger score sensitivity confirmed direction under Egger-assessability stress testing; strict-joint dataset-equal weighting confirmed severe-endpoint stability; and clinical dataset-equal weighting confirmed clinical-endpoint stability under balanced contribution assumptions. Exclusion of extreme effect-size tails did not remove the association. Non-sparse-events subset analysis retained positive direction with expected precision loss, whereas the `I2 > 0` subset attenuated toward null. Component-level interpretation requires collinearity-aware specification, influence analysis indicates the main effect is not driven by any single dataset, functional-form checks indicate nonlinearity that is now explicitly reported, threshold-grid testing shows results are not an artifact of one specific cutoff choice, and conservative permutation analysis indicates residual attribution uncertainty. We therefore frame the central underdiagnosed issue as unmeasured assumption burden, interpreted as a stability-risk marker rather than a definitive standalone causal mechanism.
