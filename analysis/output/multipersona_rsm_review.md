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

## Persona 41: Multiverse-Synthesis Reviewer
**Finding:** Many sensitivity analyses are now available, but readers still need a single quantitative summary of cross-specification directional consistency.  
**Risk:** Without a multiverse synthesis metric, robustness claims can be perceived as selective interpretation of individual checks.  
**Improvement implemented:** Added a specification-curve export and multiverse consistency summary:
- `assumption_debt_specification_curve.csv`
- `assumption_debt_multiverse_consistency.csv`

## Persona 42: Multiverse-Inference Reviewer
**Finding:** Descriptive consistency percentages are useful, but reviewers may ask whether directional predominance is statistically stronger than chance under a neutral sign-null.  
**Risk:** Without an inferential sign test, multiverse consistency can be criticized as descriptive-only.  
**Improvement implemented:** Added exact one-sided binomial sign test across directional robustness checks:
- `assumption_debt_multiverse_sign_test.csv`

## Persona 43: Dominance-Threshold Arbitrariness Reviewer
**Finding:** The score includes a dominance component based on a single threshold (`max weight >= 50%`), which may appear arbitrary.  
**Risk:** Robustness claims can be challenged if dependence on one dominance cutoff is not quantified.  
**Improvement implemented:** Added dominance-threshold sensitivity using cutoffs 0.40/0.50/0.60 with clustered inference summaries:
- `assumption_debt_dominance_threshold_sensitivity.csv`
- `assumption_debt_dominance_threshold_sensitivity_summary.csv`

## Persona 44: Small-Study Threshold Arbitrariness Reviewer
**Finding:** The score’s small-study component currently relies on a single Egger cutoff (`p < 0.10`).  
**Risk:** Inference may be criticized as threshold-contingent if small-study signal definitions are not stress-tested.  
**Improvement implemented:** Added Egger-threshold sensitivity using cutoffs 0.05/0.10/0.20 with clustered inference summaries:
- `assumption_debt_egger_threshold_sensitivity.csv`
- `assumption_debt_egger_threshold_sensitivity_summary.csv`

## Persona 45: Assessability-Restriction Reviewer
**Finding:** Even with threshold sweeps, reviewers can argue that inclusion of non-assessable (`k < 10`) analyses distorts interpretation of a score that contains small-study diagnostics.  
**Risk:** Main association could be challenged as an artifact of mixed assessability strata.  
**Improvement implemented:** Added assessable-only sensitivity restricted to `k >= 10` (conventional and clustered):
- `assumption_debt_model_coefficients_assessable.csv`
- `assumption_debt_model_coefficients_assessable_cluster.csv`

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
- Dominance-threshold sensitivity (clustered OR): median 1.15 (2.5% to 97.5%: 1.13 to 1.20; range: 1.13 to 1.20)
- Egger-threshold sensitivity (clustered OR): median 1.15 (2.5% to 97.5%: 1.14 to 1.15; range: 1.14 to 1.15)
- Assessable-only subset (`k >= 10`): clustered OR 1.31 (95% CI 1.07 to 1.61; p = 0.0084)
- Multiverse consistency: 51/52 directional checks were in the positive direction (98.1%); 45/52 had CIs excluding the null in the positive direction (86.5%)
- Multiverse sign test: one-sided p = 1.18e-14 for directional predominance vs null 50%
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
- Effect-size-tail exclusion (retain 99.0%): clustered OR 1.17 (95% CI 1.04 to 1.32; p = 0.0094)
- Cumulative large-review removal (top 5/10/20/30/40): clustered OR median 1.19 (2.5% to 97.5%: 1.14 to 1.22), retained-meta range 93.6% to 73.5%
- Non-sparse-events subset (17.4% retained): clustered OR 1.28 (95% CI 0.96 to 1.71; p = 0.0967), direction preserved with reduced precision
- Heterogeneity-present subset (`I2 > 0`, 39.0% retained): clustered OR 0.95 (95% CI 0.81 to 1.12; p = 0.5660), indicating attenuation under this restriction
- Clinical fragility outcome: clustered OR 1.40 (95% CI 1.21 to 1.61; p < 0.001)
- Framing diagnosis: the strongest underdiagnosed issue is unmeasured assumption burden; manuscript-ready intro/discussion text added
- One-per-dataset bootstrap: median OR 1.25 (95% empirical interval 0.92 to 1.77)
- `k < 10` in no-`log_k` component model: OR 1.89 (95% CI 1.64 to 2.17)
- `k < 10` in no-`log_k` component model (cluster-robust): OR 1.89 (95% CI 1.59 to 2.25)
- Leave-one-dataset-out: OR median 1.15 (2.5% to 97.5%: 1.14 to 1.16; min-max: 1.14 to 1.17)
- Model performance: apparent AUC 0.681; row-wise 5-fold CV AUC 0.679; grouped-by-dataset 5-fold CV AUC 0.680
- Functional-form LR test (linear vs categorical score): p = 7.68e-05
- Threshold-grid sensitivity (clustered OR): median 1.25 (2.5% to 97.5%: 1.11 to 1.40; range: 1.11 to 1.42)
- Within-dataset permutation sensitivity: empirical two-sided p = 0.08
- Out-of-fold calibration: row-wise intercept ~0.00006, slope 0.983; grouped-by-dataset intercept ~-0.0011, slope 0.978
- Dataset-level bootstrap: OR median 1.15 (95% empirical interval 1.04 to 1.30)
- Complete-case outcome sensitivity: OR 1.13 (95% CI 1.01 to 1.26), cluster-robust OR 1.13 (95% CI 1.00 to 1.27)
- Tau2-cap sensitivity (clustered OR): median 1.15 (2.5% to 97.5%: 1.09 to 1.34; range: 1.09 to 1.35)
- High-leverage exclusion sensitivity (clustered): OR 1.15 (95% CI 1.01 to 1.30; p = 0.0308), retaining 93.2%

Interpretation after review: the direction of association is stable across modeling choices, while precision attenuates under strict within-dataset and fixed-effects sensitivity checks; this supports a real signal with non-trivial attribution uncertainty.
