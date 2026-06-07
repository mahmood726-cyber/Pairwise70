# Pairwise70: Comprehensive Cochrane Pairwise Meta-Analysis Dataset

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![R Version](https://img.shields.io/badge/R-%3E%3D%204.0.0-blue.svg)](https://www.r-project.org/)

## Overview

**Pairwise70** is an R data package containing **501 systematically extracted pairwise meta-analysis datasets** from Cochrane Systematic Reviews. This comprehensive collection provides ready-to-use, cleaned datasets for meta-research, methodological studies, and educational purposes.

## Key Features

- **501 Cochrane Reviews**: Largest open collection of standardized meta-analysis datasets
- **~50,000+ Individual Studies**: Tens of thousands of randomized controlled trials
- **Standardized Format**: Consistent column naming and structure across all datasets
- **Complete Metadata**: Study identifiers, outcomes, interventions, and review DOIs
- **Quality Assured**: Systematically extracted from official Cochrane data tables
- **Research Ready**: Pre-cleaned and formatted for immediate analysis

## Installation

Install directly from GitHub:

```r
# Install devtools if you haven't already
install.packages("devtools")

# Install Pairwise70
devtools::install_github("mahmood789/Pairwise70")
```

## Quick Start

```r
library(Pairwise70)

# List all available datasets
data(package = "Pairwise70")

# Load a specific dataset
data(CD002042_pub6_data)

# View dataset structure
head(CD002042_pub6_data)
str(CD002042_pub6_data)

# Example: Run a meta-analysis with metafor
library(metafor)

# Binary outcome meta-analysis
meta_result <- rma(measure = "OR",
                   ai = Experimental.cases,
                   n1i = Experimental.N,
                   ci = Control.cases,
                   n2i = Control.N,
                   data = CD002042_pub6_data,
                   method = "REML")

summary(meta_result)
forest(meta_result)
```

## Publication Bias Master Model (PBM)

`Pairwise70` includes `pbm_meta()`, an adaptive publication-bias ensemble that combines:
- PET-PEESE
- trim-and-fill
- SWA
- TAS
- HKSJ / REML baselines

```r
library(Pairwise70)
library(metafor)

data(CD002042_pub6_data)

es <- escalc(
  measure = "OR",
  ai = Experimental.cases,
  n1i = Experimental.N,
  ci = Control.cases,
  n2i = Control.N,
  data = CD002042_pub6_data
)

pbm <- pbm_meta(es$yi, es$vi)
pbm$estimate
pbm$ci_lb
pbm$ci_ub
pbm$ensemble_weights
pbm$asymmetry_detected
pbm$egger_p
```

## Dataset Structure

Each dataset contains standardized columns:

### Core Identifiers
- **Study**: Study identifier (author, year)
- **Study.year**: Publication year
- **Comparison**: Treatment comparison description
- **Outcome**: Outcome measure description
- **Subgroup**: Subgroup classification (if applicable)

### Binary Outcome Data
- **Experimental.cases**: Number of events in experimental group
- **Experimental.N**: Total participants in experimental group
- **Control.cases**: Number of events in control group
- **Control.N**: Total participants in control group

### Continuous Outcome Data
- **Experimental.mean**: Mean in experimental group
- **Experimental.SD**: Standard deviation in experimental group
- **Experimental.N**: Sample size in experimental group
- **Control.mean**: Mean in control group
- **Control.SD**: Standard deviation in control group
- **Control.N**: Sample size in control group

### Metadata
- **review_doi**: Digital Object Identifier for the Cochrane review
- **review_title**: Title of the Cochrane systematic review
- **comparison_id**: Comparison identifier within review
- **outcome_id**: Outcome identifier within comparison

## Data Collection Methodology

### Source
All data was systematically extracted from the [Cochrane Library](https://www.cochranelibrary.com/) using their official API and data export functionality.

### Extraction Process

1. **Review Identification** (2024)
   - Systematically scraped all Cochrane Systematic Reviews
   - Identified 521 reviews with extractable pairwise comparison data tables
   - Covered reviews from CD000028 (earliest) to CD016278 (latest)

2. **Data Download**
   - Used Cochrane's official data export API
   - Downloaded structured CSV files for each review
   - Captured comprehensive metadata (DOI, title, comparison/outcome IDs)

3. **Data Cleaning & Standardization**
   - Standardized column names across all 521 reviews
   - Converted data types (numeric, character, factor)
   - Removed empty rows and invalid entries
   - Validated data integrity and completeness

4. **Package Creation**
   - Converted 521 CSV files to R data format (.rda)
   - Consolidated to 501 unique datasets (some reviews had duplicate versions)
   - Generated comprehensive documentation
   - Built complete R package structure with devtools

### Quality Control

- **Validation**: All datasets validated for completeness and format consistency
- **Provenance**: Full traceability to original Cochrane reviews via DOI
- **Reproducibility**: Complete extraction pipeline documented in data-raw/
- **No Errors**: Zero errors during conversion and validation

## Dataset Coverage

### Scope
- **Cochrane Review IDs**: CD000028 to CD016278
- **Total Datasets**: 501 unique meta-analyses
- **Total Studies**: ~50,000+ individual RCTs
- **Total Participants**: Millions of trial participants across all datasets

### Medical Specialties
- Cardiology (anticoagulation, heart failure, statins, etc.)
- Oncology (chemotherapy, radiation, targeted therapy)
- Psychiatry (depression, anxiety, schizophrenia)
- Surgery (surgical interventions, anesthesia)
- Pediatrics (neonatal care, childhood diseases)
- Infectious diseases (antibiotics, vaccines)
- And many more...

### Intervention Types
- Pharmacological (medications, doses, combinations)
- Behavioral (psychotherapy, lifestyle modifications)
- Surgical (procedures, techniques)
- Preventive (screening, prophylaxis)
- Diagnostic (test accuracy, imaging)

### Outcome Types
- Binary outcomes (events/total)
- Continuous outcomes (mean/SD/N)
- Various clinical endpoints

## Use Cases

### 1. Meta-Research Studies
Analyze methodological patterns across hundreds of meta-analyses:

```r
library(Pairwise70)
library(metafor)

# Analyze heterogeneity patterns across all datasets
heterogeneity_results <- data.frame()

all_datasets <- data(package = "Pairwise70")$results[,3]

for (ds_name in all_datasets) {
  # Load dataset
  data(list = ds_name, package = "Pairwise70")
  dataset <- get(ds_name)

  # Run meta-analysis (example for binary outcomes)
  # Add your analysis...
}
```

### 2. Methodological Comparisons
Compare performance of different meta-analysis methods across real datasets

### 3. Educational Materials
Teach meta-analysis using diverse, real-world examples

### 4. Software Validation
Benchmark and validate new meta-analysis software

### 5. Meta-Meta-Analysis
See `inst/examples/meta_meta_analysis.R` for comprehensive example

## Dataset Naming Convention

Datasets follow Cochrane review identifier format:

- `CD######_pub#_data`: Standard format
  - `CD######`: Cochrane Database review number
  - `pub#`: Publication version number (when applicable)
  - `_data`: Dataset suffix

**Examples:**
- `CD002042_pub6_data`: Cochrane review CD002042, version 6
- `CD000143_pub2_data`: Cochrane review CD000143, version 2
- `CD014089_data`: Cochrane review CD014089 (no version number)

## Package Statistics

- **Total Datasets**: 501
- **Data Source Reviews**: 521 Cochrane reviews
- **Unique Reviews**: 501 (20 duplicate versions consolidated)
- **Total Studies**: ~50,000+ RCTs
- **Total Participants**: Millions
- **Package Size**: ~15MB compressed
- **Created**: January 2025
- **Last Updated**: January 2025

## Citation

If you use this package in your research, please cite:

```
Arai M. (2025). Pairwise70: Comprehensive Cochrane Pairwise Meta-Analysis Dataset.
R package version 1.0.0. https://github.com/mahmood789/Pairwise70
```

**Important**: Also cite the original Cochrane reviews used in your analysis. DOIs are provided in each dataset under the `review_doi` column.

## Methods

`Pairwise70` ships both the dataset collection and a set of pooling-method implementations exposed via `NAMESPACE`:

- **V3 robust pooling.** `adaptive_robust_pooling()`, `compare_pooling_methods()`, `mafi_weighted_ma()` (Meta-Analysis Fragility Index–weighted), `sequential_influence_trimming()`.
- **V4 robustness family.** `wrd_meta` (weighted robust DerSimonian), `cbm_meta` (clustered-bootstrap meta), `rbm_meta` (robust bootstrap meta), `swa_meta` (study-weight averaging), `tas_meta` (trimmed-and-shrunk), `eve_meta` (event-validated estimator).
- **V4 partial-pooling and shrinkage.** `pvm_meta` (partial-variance meta), `aem_meta`, `spe_meta`, `sms_meta`.
- **GRMA family.** `grma_meta()` and `grma_loo()` for grouped random-effects pooling with leave-one-out diagnostics.
- **Cross-method comparison.** `compare_methods_v4()` runs all V3/V4 methods against the same input and emits a methods-by-metric table so reviewers can see method-driven movement in the pooled estimate before locking in a primary analysis.

The bundled MAFI (Meta-Analysis Fragility Index) calculator (`MAFI-Calculator-Complete.html`) implements:

```
MAFI = 0.30 · DFI + 0.25 · SFI + 0.20 · CFI + 0.15 · Effect + 0.10 · CI
     + Heterogeneity Penalty + Sample Size Penalty
```

with classification bands Robust (< 0.15), Low (0.15–0.30), Moderate (0.30–0.50), High (> 0.50). The web calculator and the R-package `mafi_weighted_ma()` use the same weights.

R-side validation runs against `metafor` for binary and continuous outcomes; the V3/V4 methods are documented in `analysis/` with reproducible scripts.

## Known Limitations

1. **Pairwise only.** Contains only pairwise (2-arm) comparisons, not network meta-analyses. For NMA, see the network-meta repos in the portfolio.
2. **Snapshot.** Data from Cochrane reviews as of 2024–2025; living reviews may have published updated versions since extraction.
3. **Standardisation flattens complexity.** Multi-outcome / multi-comparison reviews are simplified to one outcome per dataset row; the original Cochrane review remains the source of record for nuance the standardisation drops.
4. **Binary / continuous focus.** Time-to-event, count-rate, and ordinal outcomes are not included; downstream methods needing those need a different corpus.
5. **501 unique vs 521 reviews and 595 files.** 521 reviews were ingested, 501 unique datasets resulted (some reviews had duplicate publication versions), and `data/` contains 595 `.rda` files because per-publication-version variants and a few helper objects are also stored. The "501 unique datasets" count in the DESCRIPTION is the analytical count; treat `data/` file-count as a superset.
6. **"Zero errors during conversion" is a build-time claim, not a guarantee against semantic errors.** Cell-level verification against PDF tables was not performed for the full corpus; semantic typos in the upstream Cochrane export propagate.
7. **The MAFI weight vector is fixed.** The 30 / 25 / 20 / 15 / 10 % weighting in MAFI is the published default; users wanting to re-weight (e.g. emphasise heterogeneity over CI width) need to recompute outside the bundled calculator and rerun any sensitivity analysis.
8. **Test layer is Selenium-only.** `pytest` collects no Python tests in this repo; the validation harness for the web calculator runs in Chrome. R-side `testthat` is exercised via `devtools::test()` but is not wired into a CI gate in this repo.

## Conclusions

Use `Pairwise70` when (a) the analyst needs a real-data Cochrane corpus large enough for methodology benchmarking, simulation, and teaching, (b) pairwise binary or continuous outcomes match the planned methods, and (c) the V3/V4/GRMA family of robust pooling or the MAFI fragility index is part of the comparative analysis. For network meta-analysis, time-to-event outcomes, or per-cell verification against the underlying PDFs, this corpus is not sufficient on its own — pair it with topic-specific manual extraction or hand off downstream.

## Related Packages

- **metafor**: Comprehensive meta-analysis (Viechtbauer, 2010)
- **meta**: Alternative meta-analysis package (Schwarzer et al.)
- **DTA70**: Sister package with diagnostic test accuracy datasets
- **netmeta**: Network meta-analysis tools

## Contributing

Found an issue or have suggestions?
- [Open an issue](https://github.com/mahmood789/Pairwise70/issues) on GitHub
- Submit a pull request with improvements

## License

- **Code**: MIT License
- **Data**: Derived from Cochrane Reviews. Original reviews are published under various Cochrane licenses. Please check individual review licenses via their DOI before commercial use.

## Acknowledgments

- **Cochrane Collaboration**: For maintaining the world's largest systematic review database
- **Review Authors**: Thousands of researchers who conducted the original systematic reviews
- **Trial Investigators**: Researchers who conducted the original RCTs

## Author

Mahmood Arai
mahmood726@gmail.com

## Version History

### 1.0.0 (January 2025)
- Initial release
- 501 Cochrane pairwise meta-analysis datasets
- Comprehensive documentation
- Meta-meta-analysis example included
- Automated dataset catalog
- Full devtools compatibility

---

**Generated with Claude Code**
