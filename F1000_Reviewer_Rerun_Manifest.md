# Pairwise70: reviewer rerun manifest

This manifest is the shortest reviewer-facing rerun path for the local software package. It lists the files that should be sufficient to recreate one worked example, inspect saved outputs, and verify that the manuscript claims remain bounded to what the repository actually demonstrates.

## Reviewer Entry Points
- Project directory: `C:\Models\Pairwise70`.
- Preferred documentation start points: `README.md`, `truthcert/README.md`, `f1000_artifacts/tutorial_walkthrough.md`.
- Detected public repository root: `https://github.com/mahmood726-cyber/Pairwise70`.
- Detected public source snapshot: Fixed public commit snapshot available at `https://github.com/mahmood726-cyber/Pairwise70/tree/a3e7f22655b3f2242b459b80cbe9b5c090d3e7cb`.
- Detected public archive record: No project-specific DOI or Zenodo record URL was detected locally; archive registration pending.
- Environment capture files: `environment.yml`.
- Validation/test artifacts: `f1000_artifacts/validation_summary.md`, `mini_validation_spe.R`, `run_quick_validation.R`, `analysis/Quick_Validation_V2.R`, `tests/js_function_validation.py`, `truthcert/gates/validation_gates.py`, `truthcert/tests/test_validation.py`, `truthcert/validation/run_validation.py`.

## Worked Example Inputs
- Manuscript-named example paths: `README.md` for package installation and example loading; `MAFI-Calculator.html` and `MAFI-Calculator-Complete.html` for browser-based robustness walkthroughs; `analysis/` for benchmark, comparator, and method-development scripts over the corpus; analysis/research_output/Table1_Sample_Characteristics.csv.
- Auto-detected sample/example files: `analysis/research_output/Table1_Sample_Characteristics.csv`.

## Expected Outputs To Inspect
- A large benchmark corpus of standardized pairwise meta-analysis datasets.
- Companion browser tools for MAFI and GRADE-oriented interpretation.
- A base for method development, teaching, and reproducible comparative evaluation.

## Minimal Reviewer Rerun Sequence
- Start with the README/tutorial files listed below and keep the manuscript paths synchronized with the public archive.
- Create the local runtime from the detected environment capture files if available: `environment.yml`.
- Run at least one named example path from the manuscript and confirm that the generated outputs match the saved validation materials.
- Quote one concrete numeric result from the local validation snippets below when preparing the final software paper.
- Open the browser deliverable and confirm that the embedded WebR validation panel completes successfully after the page finishes initializing.

## Local Numeric Evidence Available
- `run_quick_validation_output.txt` records 1250 simulations and 16198 results; the best reported coverage is 98.3% for CBM, and the lowest is 11.2% for SPE.
- `analysis/SESSION_SUMMARY.md` reports % Robust, 36.0% Low, 25.1% Moderate, 9.7% High.
- `analysis/transportability/transportability_cv_summary.md` reports 465 reviews modeled; reported: RMSE = 6.344, MAE = 1.096 (n = 3854); or: RMSE = 0.708, MAE = 0.451 (n = 8509).

## Browser Deliverables
- HTML entry points: `MAFI-Calculator-Complete.html`, `MAFI-Calculator.html`.
- The shipped HTML applications include embedded WebR self-validation and should be checked after any UI or calculation change.
