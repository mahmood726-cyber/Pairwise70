# Preregistration-Style Analysis Plan (Retrospective Transparency Appendix)

## Objective
Evaluate whether higher assumption debt is associated with higher fragility in Cochrane pairwise meta-analyses.

## Dataset
- Source: Pairwise70
- Unit: meta-analysis-level rows nested within review datasets
- Primary outcome: `fragile_any`

## Primary Estimand
Adjusted odds ratio for `assumption_debt_score` (per +1 point) from:
`fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped`.

## Primary Inference
- Model: logistic regression
- Dependence adjustment: cluster-robust SE by `dataset`
- Primary report: effect estimate, 95% CI, p-value

## Prespecified Sensitivity Families
1. Outcome definition: complete-case, direction, significance, clinical, strict-joint, composite count.
2. Effect scale/link: modified-Poisson RR where applicable.
3. Dependence/structure: clustered SE, one-per-dataset bootstrap, leave-one-dataset-out, within-between, fixed-effects LPM, dataset-level aggregate.
4. Composition/weighting: dataset-equal weighting, leave-one-measure-family-out, large-review exclusion and cumulative removal.
5. Threshold arbitrariness: `k`, `I2`, dominance, Egger, tau2 caps.
6. Influence/outliers: high-leverage and effect-tail exclusion.
7. Conservative null: within-dataset permutation.
8. Assessability: no-Egger score and `k >= 10` assessable-only subset.

## Multiplicity and Interpretation Rule
- Primary claim is based on direction and uncertainty pattern across the full robustness matrix, not single p-values.
- Mechanistic language is allowed only if conservative-null and within-dataset checks are concordant.
- If conservative checks attenuate, report association as directional marker evidence.

## Robustness Synthesis Outputs
- `assumption_debt_robustness_matrix.csv`
- `assumption_debt_specification_curve.csv`
- `assumption_debt_multiverse_consistency.csv`
- `assumption_debt_multiverse_sign_test.csv`

## Deviations Section (to complete at submission)
- Document any deviations from this plan and rationale.
