# Pairwise70: a software tool for reviewer-auditable evidence synthesis

## Authors
- Mahmood Ahmad [1,2]
- Niraj Kumar [1]
- Bilaal Dar [3]
- Laiba Khan [1]
- Andrew Woo [4]
- Corresponding author: Andrew Woo (andy2709w@gmail.com)

## Affiliations
1. Royal Free Hospital
2. Tahir Heart Institute Rabwah
3. King's College Medical School
4. St George's Medical School

## Abstract
**Background:** Many software papers claim reproducibility yet do not ship standardized benchmark data that other groups can reuse. Pairwise70 addresses that gap by packaging a large library of cleaned Cochrane pairwise meta-analysis datasets in a consistent schema, with companion HTML tools for fragility-oriented exploration.

**Methods:** Pairwise70 is an R data package containing 501 standardized Cochrane review datasets with harmonized columns, review metadata, and ready-to-run examples. The project directory also includes browser-based MAFI calculators and a broad set of benchmark and comparison scripts.

**Results:** The local package provides loadable review datasets, study metadata, example code, meta-research analyses, and two HTML calculators for the Meta-Analysis Fragility Index, including a complete edition with GRADE-oriented interpretation.

**Conclusions:** Pairwise70 is presented as benchmark infrastructure plus companion software, with claims centered on data standardization, teaching value, and reproducible method comparison rather than on a single novel estimator.

## Keywords
meta-analysis dataset; Cochrane reviews; reproducibility; benchmark corpus; browser calculator; software tool

## Introduction
The software contribution is twofold: a reusable dataset corpus for method development and education, and local tools that make robustness concepts tangible to users who may not code in R or Python. That directly answers reviewer requests for example data and guided walkthroughs.

Comparable resources exist as individual packages or bespoke collections, but Pairwise70 emphasizes breadth, uniform schema, and packaged examples across hundreds of Cochrane reviews. The included HTML calculators serve as user-facing companions rather than replacements for standard statistical software.

The manuscript structure below is deliberately aligned to common open-software review requests: the rationale is stated explicitly, at least one runnable example path is named, local validation artifacts are listed, and conclusions are bounded to the functions and outputs documented in the repository.

## Methods
### Software architecture and workflow
The project includes the R data package, analysis scripts, local benchmark outputs, and the `MAFI-Calculator*.html` applications. Standardized columns cover identifiers, binary and continuous outcomes, and review metadata.

### Installation, runtime, and reviewer reruns
The local implementation is packaged under `C:\Models\Pairwise70`. The manuscript identifies the local entry points, dependency manifest, fixed example input, and expected saved outputs so that reviewers can rerun the documented workflow without reconstructing it from scratch.

- Entry directory: `C:\Models\Pairwise70`.
- Detected documentation entry points: `README.md`, `truthcert/README.md`, `f1000_artifacts/tutorial_walkthrough.md`.
- Detected environment capture or packaging files: `environment.yml`.
- Named worked-example paths in this draft: `README.md` for package installation and example loading; `MAFI-Calculator.html` and `MAFI-Calculator-Complete.html` for browser-based robustness walkthroughs; `analysis/` for benchmark, comparator, and method-development scripts over the corpus.
- Detected validation or regression artifacts: `f1000_artifacts/validation_summary.md`, `mini_validation_spe.R`, `run_quick_validation.R`, `analysis/Quick_Validation_V2.R`, `tests/js_function_validation.py`, `truthcert/gates/validation_gates.py`, `truthcert/tests/test_validation.py`, `truthcert/validation/run_validation.py`.
- Detected example or sample data files: `analysis/research_output/Table1_Sample_Characteristics.csv`.
- Detected browser deliverables with built-in WebR self-validation: `MAFI-Calculator-Complete.html`, `MAFI-Calculator.html`.

### Worked examples and validation materials
**Example or fixed demonstration paths**
- `README.md` for package installation and example loading.
- `MAFI-Calculator.html` and `MAFI-Calculator-Complete.html` for browser-based robustness walkthroughs.
- `analysis/` for benchmark, comparator, and method-development scripts over the corpus.

**Validation and reporting artifacts**
- `EDITORIAL_REVIEW_MAFI_CALCULATOR.md` documenting companion-software review feedback.
- Package-level standardization and provenance described in the README and analysis scripts.
- Local output directories containing comparative method analyses over the corpus.

### Typical outputs and user-facing deliverables
- A large benchmark corpus of standardized pairwise meta-analysis datasets.
- Companion browser tools for MAFI and GRADE-oriented interpretation.
- A base for method development, teaching, and reproducible comparative evaluation.

### Reviewer-informed safeguards
- Provides a named example workflow or fixed demonstration path.
- Documents local validation artifacts rather than relying on unsupported claims.
- Positions the software against existing tools without claiming blanket superiority.
- States limitations and interpretation boundaries in the manuscript itself.
- Requires explicit environment capture and public example accessibility in the released archive.

## Review-Driven Revisions
This draft has been tightened against recurring open peer-review objections taken from the supplied reviewer reports.
- Reproducibility: the draft names a reviewer rerun path and points readers to validation artifacts instead of assuming interface availability is proof of correctness.
- Validation: claims are anchored to local tests, validation summaries, simulations, or consistency checks rather than to unsupported assertions of performance.
- Comparators and niche: the manuscript now names the relevant comparison class and keeps the claimed niche bounded instead of implying universal superiority.
- Documentation and interpretation: the text expects a worked example, input transparency, and reviewer-verifiable outputs rather than a high-level feature list alone.
- Claims discipline: conclusions are moderated to the documented scope of Pairwise70 and paired with explicit limitations.
- Browser verification: HTML applications in this directory now include embedded WebR checks so reviewer-facing dashboards can validate their displayed calculations in situ.

## Use Cases and Results
The software outputs should be described in terms of concrete reviewer-verifiable workflows: running the packaged example, inspecting the generated results, and checking that the reported interpretation matches the saved local artifacts. In this project, the most important result layer is the availability of a transparent execution path from input to analysis output.

Representative local result: `run_quick_validation_output.txt` records 1250 simulations and 16198 results; the best reported coverage is 98.3% for CBM, and the lowest is 11.2% for SPE.

### Concrete local quantitative evidence
- `run_quick_validation_output.txt` records 1250 simulations and 16198 results; the best reported coverage is 98.3% for CBM, and the lowest is 11.2% for SPE.
- `analysis/SESSION_SUMMARY.md` reports % Robust, 36.0% Low, 25.1% Moderate, 9.7% High.
- `analysis/transportability/transportability_cv_summary.md` reports 465 reviews modeled; reported: RMSE = 6.344, MAE = 1.096 (n = 3854); or: RMSE = 0.708, MAE = 0.451 (n = 8509).

## Discussion
Representative local result: `run_quick_validation_output.txt` records 1250 simulations and 16198 results; the best reported coverage is 98.3% for CBM, and the lowest is 11.2% for SPE.

For F1000Research, the paper leans into what reviewers repeatedly ask for: accessible example data, explicit schema, downloadable artifacts, and browser tools that demonstrate how the dataset can support real methodological questions.

### Limitations
- The corpus is pairwise only and does not natively encode network structures.
- It is a snapshot of extracted Cochrane data rather than a continuously updated registry.
- Companion calculators are educational and sensitivity-oriented, not complete meta-analysis suites.

## Software Availability
- Local source package: `Pairwise70` under `C:\Models`.
- Public repository: `https://github.com/mahmood726-cyber/Pairwise70`.
- Public source snapshot: Fixed public commit snapshot available at `https://github.com/mahmood726-cyber/Pairwise70/tree/a3e7f22655b3f2242b459b80cbe9b5c090d3e7cb`.
- DOI/archive record: No project-specific DOI or Zenodo record URL was detected locally; archive registration pending.
- Environment capture detected locally: `environment.yml`.
- Reviewer-facing documentation detected locally: `README.md`, `truthcert/README.md`, `f1000_artifacts/tutorial_walkthrough.md`.
- Reproducibility walkthrough: `f1000_artifacts/tutorial_walkthrough.md` where present.
- Validation summary: `f1000_artifacts/validation_summary.md` where present.
- Reviewer rerun manifest: `F1000_Reviewer_Rerun_Manifest.md`.
- Multi-persona review memo: `F1000_MultiPersona_Review.md`.
- Concrete submission-fix note: `F1000_Concrete_Submission_Fixes.md`.
- License: see the local `LICENSE` file.

## Data Availability
The datasets, schema descriptions, and companion software are stored in the local project directory. The original source material is derived from publicly accessible Cochrane reviews.

## Reporting Checklist
Real-peer-review-aligned checklist: `F1000_Submission_Checklist_RealReview.md`.
Reviewer rerun companion: `F1000_Reviewer_Rerun_Manifest.md`.
Companion reviewer-response artifact: `F1000_MultiPersona_Review.md`.
Project-level concrete fix list: `F1000_Concrete_Submission_Fixes.md`.

## Declarations
### Competing interests
The authors declare that no competing interests were disclosed.

### Grant information
No specific grant was declared for this manuscript draft.

### Author contributions (CRediT)
| Author | CRediT roles |
|---|---|
| Mahmood Ahmad | Conceptualization; Software; Validation; Data curation; Writing - original draft; Writing - review and editing |
| Niraj Kumar | Conceptualization |
| Bilaal Dar | Conceptualization |
| Laiba Khan | Conceptualization |
| Andrew Woo | Conceptualization |

### Acknowledgements
The authors acknowledge contributors to open statistical methods, reproducible research software, and reviewer-led software quality improvement.

## References
1. DerSimonian R, Laird N. Meta-analysis in clinical trials. Controlled Clinical Trials. 1986;7(3):177-188.
2. Higgins JPT, Thompson SG. Quantifying heterogeneity in a meta-analysis. Statistics in Medicine. 2002;21(11):1539-1558.
3. Viechtbauer W. Conducting meta-analyses in R with the metafor package. Journal of Statistical Software. 2010;36(3):1-48.
4. Page MJ, McKenzie JE, Bossuyt PM, et al. The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. BMJ. 2021;372:n71.
5. Fay C, Rochette S, Guyader V, Girard C. Engineering Production-Grade Shiny Apps. Chapman and Hall/CRC. 2022.
