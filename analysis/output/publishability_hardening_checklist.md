# Publishability Hardening Checklist

## Positioning
- Primary claim: higher assumption debt is associated with higher fragility risk.
- Causal boundary: treat assumption debt as a risk marker, not a standalone causal mechanism.
- Main estimand: per +1 score effect on `fragile_any` in the primary adjusted model.

## Manuscript Architecture
- Main text should present one primary model, one dependence-aware sensitivity, and one multiverse summary.
- Move exhaustive checks to appendix tables linked by stable file names.
- Keep abstract conclusions aligned with conservative results (`I2 > 0` attenuation, permutation p = 0.08).

## Minimum Figures/Tables for Submission
- Figure 1: score distribution and fragility gradient.
- Figure 2: primary + clustered + assessable-only + RR sensitivity forest panel.
- Table 1: prespecified primary/secondary estimands.
- Table 2: multiverse consistency summary (direction, CI support, sign test).

## Methods Transparency
- State handling of missing fragility flags and complete-case sensitivity.
- State cluster unit (`dataset`) and rationale.
- State all threshold families tested (`k`, `I2`, dominance, Egger, tau2 cap).
- State robustness-matrix construction rule and directional-null definitions.

## Residual Risks to Declare
- Correlated specification family may inflate apparent multiverse stability.
- Within-dataset permutation attenuation implies non-trivial attribution uncertainty.
- External transportability remains untested unless validated on a separate corpus.

## Before Submission
- Freeze analysis script hash and output manifest.
- Add one-command reproducibility instructions.
- Add data provenance + licensing notes for Pairwise70 inputs.
- Ensure all claims in abstract/discussion are marker-language consistent.
