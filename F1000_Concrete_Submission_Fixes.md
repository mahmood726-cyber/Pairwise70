# Pairwise70: concrete submission fixes

This file converts the multi-persona review into repository-side actions that should be checked before external submission of the F1000 software paper for `Pairwise70`.

## Detectable Local State
- Documentation files detected: `README.md`, `truthcert/README.md`, `f1000_artifacts/tutorial_walkthrough.md`.
- Environment lock or container files detected: `environment.yml`.
- Package manifests detected: `DESCRIPTION`, `truthcert/setup.py`.
- Example data files detected: `analysis/research_output/Table1_Sample_Characteristics.csv`.
- Validation artifacts detected: `f1000_artifacts/validation_summary.md`, `mini_validation_spe.R`, `run_quick_validation.R`, `analysis/Quick_Validation_V2.R`, `tests/js_function_validation.py`, `truthcert/gates/validation_gates.py`, `truthcert/tests/test_validation.py`, `truthcert/validation/run_validation.py`.
- Detected public repository root: `https://github.com/mahmood726-cyber/Pairwise70`.
- Detected public source snapshot: Fixed public commit snapshot available at `https://github.com/mahmood726-cyber/Pairwise70/tree/a3e7f22655b3f2242b459b80cbe9b5c090d3e7cb`.
- Detected public archive record: No project-specific DOI or Zenodo record URL was detected locally; archive registration pending.

## High-Priority Fixes
- Check that the manuscript's named example paths exist in the public archive and can be run without repository archaeology.
- Confirm that the cited repository root (`https://github.com/mahmood726-cyber/Pairwise70`) resolves to the same fixed public source snapshot used for submission.
- Archive the tagged release and insert the Zenodo DOI or record URL once it has been minted; no project-specific archive DOI was detected locally.
- Reconfirm the quoted benchmark or validation sentence after the final rerun so the narrative text matches the shipped artifacts.
- Keep the embedded WebR validation panel enabled in shipped HTML files and rerun it after any UI or calculation changes.

## Numeric Evidence Available To Quote
- `run_quick_validation_output.txt` records 1250 simulations and 16198 results; the best reported coverage is 98.3% for CBM, and the lowest is 11.2% for SPE.
- `analysis/SESSION_SUMMARY.md` reports % Robust, 36.0% Low, 25.1% Moderate, 9.7% High.
- `analysis/transportability/transportability_cv_summary.md` reports 465 reviews modeled; reported: RMSE = 6.344, MAE = 1.096 (n = 3854); or: RMSE = 0.708, MAE = 0.451 (n = 8509).

## Manuscript Files To Keep In Sync
- `F1000_Software_Tool_Article.md`
- `F1000_Reviewer_Rerun_Manifest.md`
- `F1000_MultiPersona_Review.md`
- `F1000_Submission_Checklist_RealReview.md` where present
- README/tutorial files and the public repository release metadata
