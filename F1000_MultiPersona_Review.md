# Pairwise70: multi-persona peer review

This memo applies the recurring concerns in the supplied peer-review document to the current F1000 draft for this project (`Pairwise70`). It distinguishes changes already made in the draft from repository-side items that still need to hold in the released repository and manuscript bundle.

## Detected Local Evidence
- Detected documentation files: `README.md`, `truthcert/README.md`, `f1000_artifacts/tutorial_walkthrough.md`.
- Detected environment capture or packaging files: `environment.yml`.
- Detected validation/test artifacts: `f1000_artifacts/validation_summary.md`, `mini_validation_spe.R`, `run_quick_validation.R`, `analysis/Quick_Validation_V2.R`, `tests/js_function_validation.py`, `truthcert/gates/validation_gates.py`, `truthcert/tests/test_validation.py`, `truthcert/validation/run_validation.py`.
- Detected browser deliverables: `MAFI-Calculator-Complete.html`, `MAFI-Calculator.html`.
- Detected public repository root: `https://github.com/mahmood726-cyber/Pairwise70`.
- Detected public source snapshot: Fixed public commit snapshot available at `https://github.com/mahmood726-cyber/Pairwise70/tree/a3e7f22655b3f2242b459b80cbe9b5c090d3e7cb`.
- Detected public archive record: No project-specific DOI or Zenodo record URL was detected locally; archive registration pending.

## Reviewer Rerun Companion
- `F1000_Reviewer_Rerun_Manifest.md` consolidates the shortest reviewer-facing rerun path, named example files, environment capture, and validation checkpoints.

## Detected Quantitative Evidence
- `run_quick_validation_output.txt` records 1250 simulations and 16198 results; the best reported coverage is 98.3% for CBM, and the lowest is 11.2% for SPE.
- `analysis/SESSION_SUMMARY.md` reports % Robust, 36.0% Low, 25.1% Moderate, 9.7% High.
- `analysis/transportability/transportability_cv_summary.md` reports 465 reviews modeled; reported: RMSE = 6.344, MAE = 1.096 (n = 3854); or: RMSE = 0.708, MAE = 0.451 (n = 8509).

## Current Draft Strengths
- States the project rationale and niche explicitly: Many software papers claim reproducibility yet do not ship standardized benchmark data that other groups can reuse. Pairwise70 addresses that gap by packaging a large library of cleaned Cochrane pairwise meta-analysis datasets in a consistent schema, with companion HTML tools for fragility-oriented exploration.
- Names concrete worked-example paths: `README.md` for package installation and example loading; `MAFI-Calculator.html` and `MAFI-Calculator-Complete.html` for browser-based robustness walkthroughs; `analysis/` for benchmark, comparator, and method-development scripts over the corpus.
- Points reviewers to local validation materials: `EDITORIAL_REVIEW_MAFI_CALCULATOR.md` documenting companion-software review feedback; Package-level standardization and provenance described in the README and analysis scripts; Local output directories containing comparative method analyses over the corpus.
- Moderates conclusions and lists explicit limitations for Pairwise70.

## Remaining High-Priority Fixes
- Keep one minimal worked example public and ensure the manuscript paths match the released files.
- Ensure README/tutorial text, software availability metadata, and public runtime instructions stay synchronized with the manuscript.
- Confirm that the cited repository root resolves to the same fixed public source snapshot used for the submission package.
- Mint and cite a Zenodo DOI or record URL for the tagged release; none was detected locally.
- Reconfirm the quoted benchmark or validation sentence after the final rerun so the narrative text stays synchronized with the shipped artifacts.
- Keep the embedded WebR validation panel enabled in public HTML releases and rerun it after any UI or calculation changes.

## Persona Reviews

### Reproducibility Auditor
- Review question: Looks for a frozen computational environment, a fixed example input, and an end-to-end rerun path with saved outputs.
- What the revised draft now provides: The revised draft names concrete rerun assets such as `README.md` for package installation and example loading; `MAFI-Calculator.html` and `MAFI-Calculator-Complete.html` for browser-based robustness walkthroughs and ties them to validation files such as `EDITORIAL_REVIEW_MAFI_CALCULATOR.md` documenting companion-software review feedback; Package-level standardization and provenance described in the README and analysis scripts.
- What still needs confirmation before submission: Before submission, freeze the public runtime with `environment.yml` and keep at least one minimal example input accessible in the external archive.

### Validation and Benchmarking Statistician
- Review question: Checks whether the paper shows evidence that outputs are accurate, reproducible, and compared against known references or stress tests.
- What the revised draft now provides: The manuscript now cites concrete validation evidence including `EDITORIAL_REVIEW_MAFI_CALCULATOR.md` documenting companion-software review feedback; Package-level standardization and provenance described in the README and analysis scripts; Local output directories containing comparative method analyses over the corpus and frames conclusions as being supported by those materials rather than by interface availability alone.
- What still needs confirmation before submission: Concrete numeric evidence detected locally is now available for quotation: `run_quick_validation_output.txt` records 1250 simulations and 16198 results; the best reported coverage is 98.3% for CBM, and the lowest is 11.2% for SPE; `analysis/SESSION_SUMMARY.md` reports % Robust, 36.0% Low, 25.1% Moderate, 9.7% High.

### Methods-Rigor Reviewer
- Review question: Examines modeling assumptions, scope conditions, and whether method-specific caveats are stated instead of implied.
- What the revised draft now provides: The architecture and discussion sections now state the method scope explicitly and keep caveats visible through limitations such as The corpus is pairwise only and does not natively encode network structures; It is a snapshot of extracted Cochrane data rather than a continuously updated registry.
- What still needs confirmation before submission: Retain method-specific caveats in the final Results and Discussion and avoid collapsing exploratory thresholds or heuristics into universal recommendations.

### Comparator and Positioning Reviewer
- Review question: Asks what gap the tool fills relative to existing software and whether the manuscript avoids unsupported superiority claims.
- What the revised draft now provides: The introduction now positions the software against an explicit comparator class: Comparable resources exist as individual packages or bespoke collections, but Pairwise70 emphasizes breadth, uniform schema, and packaged examples across hundreds of Cochrane reviews. The included HTML calculators serve as user-facing companions rather than replacements for standard statistical software.
- What still needs confirmation before submission: Keep the comparator discussion citation-backed in the final submission and avoid phrasing that implies blanket superiority over better-established tools.

### Documentation and Usability Reviewer
- Review question: Looks for a README, tutorial, worked example, input-schema clarity, and short interpretation guidance for outputs.
- What the revised draft now provides: The revised draft points readers to concrete walkthrough materials such as `README.md` for package installation and example loading; `MAFI-Calculator.html` and `MAFI-Calculator-Complete.html` for browser-based robustness walkthroughs; `analysis/` for benchmark, comparator, and method-development scripts over the corpus and spells out expected outputs in the Methods section.
- What still needs confirmation before submission: Make sure the public archive exposes a readable README/tutorial bundle: currently detected files include `README.md`, `truthcert/README.md`, `f1000_artifacts/tutorial_walkthrough.md`.

### Software Engineering Hygiene Reviewer
- Review question: Checks for evidence of testing, deployment hygiene, browser/runtime verification, secret handling, and removal of obvious development leftovers.
- What the revised draft now provides: The draft now foregrounds regression and validation evidence via `f1000_artifacts/validation_summary.md`, `mini_validation_spe.R`, `run_quick_validation.R`, `analysis/Quick_Validation_V2.R`, `tests/js_function_validation.py`, `truthcert/gates/validation_gates.py`, `truthcert/tests/test_validation.py`, `truthcert/validation/run_validation.py`, and browser-facing projects are described as self-validating where applicable.
- What still needs confirmation before submission: Before submission, remove any dead links, exposed secrets, or development-stage text from the public repo and ensure the runtime path described in the manuscript matches the shipped code.

### Claims-and-Limitations Editor
- Review question: Verifies that conclusions are bounded to what the repository actually demonstrates and that limitations are explicit.
- What the revised draft now provides: The abstract and discussion now moderate claims and pair them with explicit limitations, including The corpus is pairwise only and does not natively encode network structures; It is a snapshot of extracted Cochrane data rather than a continuously updated registry; Companion calculators are educational and sensitivity-oriented, not complete meta-analysis suites.
- What still needs confirmation before submission: Keep the conclusion tied to documented functions and artifacts only; avoid adding impact claims that are not directly backed by validation, benchmarking, or user-study evidence.

### F1000 and Editorial Compliance Reviewer
- Review question: Checks for manuscript completeness, software/data availability clarity, references, and reviewer-facing support files.
- What the revised draft now provides: The revised draft is more complete structurally and now points reviewers to software availability, data availability, and reviewer-facing support files.
- What still needs confirmation before submission: Confirm repository/archive metadata, figure/export requirements, and supporting-file synchronization before release.
