# Assumption debt and fragility of conclusions in Cochrane pairwise meta-analyses: A retrospective methodological study

## Authors
[Author names and affiliations to be inserted]

## Abstract
### Background
Meta-analyses are frequently interpreted as comparably reliable despite substantial differences in assumption strain. We evaluated whether a composite assumption-burden measure ("assumption debt") is associated with fragility of meta-analytic conclusions.

### Methods and findings
We analyzed 4,424 pairwise meta-analyses from Pairwise70 (474 Cochrane review datasets). The primary outcome was any fragility (direction-fragile or significance-fragile). The primary model regressed fragility on assumption-debt score (0-4), adjusted for log(k), absolute effect size, and capped tau2. Dependence was addressed using dataset-clustered robust standard errors. Fragility increased monotonically across score strata (32.0% at score 0, 38.4% at score 1, 50.9% at score 2, 70.0% at score 3). Per +1 score point, odds of fragility were higher (OR 1.15, 95% CI 1.03 to 1.28; cluster-robust OR 1.15, 95% CI 1.02 to 1.30). Direction persisted across sensitivity families, including modified-Poisson risk-ratio modeling (cluster-robust RR 1.08, 95% CI 1.01 to 1.16), no-Egger score specification (cluster-robust OR 1.18, 95% CI 1.03 to 1.34), and assessable-only subset k >= 10 (cluster-robust OR 1.31, 95% CI 1.07 to 1.61). In multiverse synthesis, 51/52 directional checks were positive, 45/52 had confidence intervals excluding the null in the positive direction, and one-sided exact sign-test evidence against a 50% directional-null was strong (p = 1.18e-14). Conservative within-dataset permutation analysis attenuated inference (empirical p = 0.08).

### Conclusions
Higher assumption debt was consistently associated with higher fragility risk across broad modeling choices. Results support interpreting assumption debt as an instability-risk marker for evidence synthesis, while avoiding standalone causal claims.

## Introduction
Meta-analysis is central to evidence synthesis, but conventional reporting often prioritizes pooled effect magnitude and heterogeneity while under-specifying the cumulative burden of assumptions required for stable inference. In practice, analyses with materially different assumption profiles may be interpreted with similar confidence. We refer to this under-measured burden as assumption debt.

Several common stressors are well known individually: sparse study counts, substantial heterogeneity, small-study effects, and dominance of one study in the pooled estimate. However, these are rarely integrated into a single operational index and evaluated against concrete instability outcomes. We examine whether higher assumption debt is associated with fragility of conclusions in a large corpus of Cochrane pairwise meta-analyses.

The primary aim was to estimate the association between assumption-debt score and fragility after adjustment for core analytic context variables. Secondary aims were to evaluate robustness under dependence-aware inference, alternative outcome definitions, alternative link functions and weighting schemes, threshold arbitrariness, and conservative null checks.

## Methods
### Study design and data source
This is a retrospective methodological analysis of Pairwise70, comprising 4,424 pairwise meta-analyses nested within 474 Cochrane review datasets.

### Outcomes
Primary outcome was `fragile_any`, defined as either direction fragility or significance fragility. Additional outcomes were direction fragility, significance fragility, clinical fragility, strict joint fragility (direction AND significance), and composite fragility count (0-2).

### Assumption debt score
The primary score (0-4) summed four binary components:
1. `k < 10` (information sparsity)
2. `I2 >= 50%` (high heterogeneity)
3. Egger small-study signal (`p < 0.10` among analyses with `k >= 10`)
4. dominance (`max study weight >= 50%`)

A no-Egger assessability score (0-3) excluded the small-study component.

### Primary model
Primary adjusted logistic model:
`fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped`

Where `tau2_capped` was capped at the 99th percentile. Primary estimand was per +1 score-point odds ratio.

### Dependence handling
Because multiple analyses came from the same Cochrane review dataset, we used cluster-robust variance estimation at dataset level for primary and relevant sensitivity models.

### Sensitivity families
We evaluated robustness across:
- Link/scale: modified-Poisson RR for binary outcomes.
- Outcome definitions: complete-case, direction, significance, clinical, strict joint, composite count.
- Dependence structure: one-analysis-per-dataset bootstrap, leave-one-dataset-out, within-between decomposition, fixed-effects linear probability model, dataset-level aggregate model.
- Composition/weighting: dataset-equal weighting, leave-one-measure-family-out, exclusion of large reviews and cumulative large-review removal.
- Threshold arbitrariness: `k` and `I2` threshold grid; dominance threshold sweep; Egger threshold sweep; tau2 cap sweep.
- Influence and outliers: high-leverage exclusion and effect-tail exclusion.
- Conservative null: within-dataset permutation.
- Assessability restrictions: no-Egger score and `k >= 10` assessable-only subset.

### Robustness synthesis
We summarized robustness using:
- a robustness matrix of all specifications,
- a specification-curve export,
- multiverse consistency counts (directional and CI support), and
- one-sided exact binomial sign test versus a 50% directional-null.

### Software and reproducibility
All analyses were run in R using scripted, file-based outputs in `analysis/output`.

## Results
### Cohort profile
Among 4,424 meta-analyses, fragile-any prevalence was 39.8%. Direction fragility was 26.7% and significance fragility 15.0% (among analyses with non-missing fragility flags). Median k was 9 (mean 18.2). Median I2 was 0%.

Assumption components were frequent: `k < 10` in 53.8%, `I2 >= 50%` in 16.4%, Egger signal in 12.1%, and dominance in 16.8%. High debt (`score >= 2`) occurred in 22.3%.

### Primary association
Per +1 score point, fragility odds increased:
- OR 1.15 (95% CI 1.03 to 1.28; p = 0.0117)
- Cluster-robust OR 1.15 (95% CI 1.02 to 1.30; p = 0.0212)

### Key sensitivity findings
- Modified-Poisson RR: cluster-robust RR 1.08 (95% CI 1.01 to 1.16; p = 0.0243).
- No-Egger score: cluster-robust OR 1.18 (95% CI 1.03 to 1.34; p = 0.0151).
- Assessable-only subset (`k >= 10`): cluster-robust OR 1.31 (95% CI 1.07 to 1.61; p = 0.0084).
- Clinical fragility outcome: cluster-robust OR 1.40 (95% CI 1.21 to 1.61; p < 0.001).
- Strict joint fragility: cluster-robust OR 4.06 (95% CI 2.28 to 7.21; p < 0.001).
- Dataset-equal weighting (primary): cluster-robust OR 1.24 (95% CI 1.06 to 1.46; p = 0.0074).
- Within-between model: within OR 1.09 (95% CI 0.96 to 1.22), between OR 1.35 (95% CI 1.06 to 1.73).
- Fixed-effects LPM sensitivity: RD 0.023 (95% CI -0.002 to 0.048).

### Robustness multiverse
Across robustness specifications:
- 51/52 directional checks were positive (98.1%).
- 45/52 had CIs excluding the null in positive direction (86.5%).
- One-sided exact sign test vs 50% directional-null: p = 1.18e-14.

Conservative permutation check showed attenuation (empirical p = 0.08).

### Model diagnostics
Discrimination was moderate and stable:
- apparent AUC 0.681,
- 5-fold CV AUC 0.679,
- grouped 5-fold CV AUC 0.680.

Functional-form test supported nonlinearity (LR p = 7.68e-05).

## Discussion
In this large Cochrane corpus, higher assumption debt was consistently associated with higher fragility risk. The signal persisted across dependence-aware models, outcome definitions, weighting schemes, threshold sweeps, and assessability-focused restrictions.

The most conservative analyses qualify interpretation. Within-between and fixed-effects sensitivity analyses attenuated precision for within-dataset contrasts, and permutation results suggested residual attribution uncertainty. Accordingly, these findings support a marker interpretation: assumption debt is a robust indicator of instability risk, not a standalone proof of causal mechanism.

Methodologically, this work supports routine reporting of assumption burden alongside pooled effects. We recommend three practical reporting norms: (1) explicit debt profiling, (2) fragility reporting on both binary and intensity scales, and (3) claim calibration proportional to assumption burden.

## Limitations
1. Observational methodological design limits causal attribution.
2. Sensitivity specifications are not statistically independent, so multiverse counts may overstate effective diversity.
3. External transportability beyond Pairwise70/Cochrane remains to be established.

## Conclusions
Assumption debt is strongly and consistently associated with fragility of meta-analytic conclusions across a wide range of models. Integrating assumption-burden profiling into routine synthesis reporting may improve inference discipline and reduce overconfident interpretation.

## Data Availability
All analysis outputs used in this manuscript are available in `analysis/output` within the project workspace. Source dataset: Pairwise70.

## Code Availability
Reproducible analysis code is provided in `analysis/assumption_debt_modeling.R`.

## Funding
[To be completed]

## Competing interests
The authors declare no competing interests. [Edit if needed]

## Ethics statement
No human participants were newly recruited; analysis used existing methodological datasets.

## Supporting information
- S1 File: `assumption_debt_results_section.md`
- S2 File: `response_to_reviewers_rsm_assumption_debt.md`
- S3 File: `assumption_debt_robustness_matrix.csv`
- S4 File: `assumption_debt_specification_curve.csv`
- S5 File: `assumption_debt_multiverse_consistency.csv`
- S6 File: `assumption_debt_multiverse_sign_test.csv`

## References (placeholders; replace with formatted bibliography)
1. Cochrane Handbook for Systematic Reviews of Interventions.
2. Literature on fragility indices and fragility in meta-analysis.
3. Literature on robust variance estimation and clustered inference.
4. Literature on multiverse/specification-curve analyses.
