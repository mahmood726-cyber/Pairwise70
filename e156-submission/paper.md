Mahmood Ahmad
Tahir Heart Institute
author@example.com

Pairwise70: Standardized Dataset of 501 Cochrane Meta-Analyses

Can a standardized open dataset of Cochrane meta-analyses enable scalable meta-research without manual data re-extraction from individual systematic reviews? We extracted and cleaned 501 pairwise meta-analysis datasets from Cochrane systematic reviews, producing the Pairwise70 R data package containing over 4,400 meta-analyses from 473 reviews with standardized columns across binary, continuous, and inverse-variance outcome types. Each dataset preserves study identifiers, outcome descriptions, intervention labels, subgroup classifications, and review DOIs in a machine-readable format compatible with metafor and meta R packages. The fragility index validation across 4,424 meta-analyses yielded a median fragility score of 0.31 (95% CI 0.29-0.33) with classifications from robust to high fragility. Cross-validation against original RevMan data files confirmed extraction fidelity with zero discrepancies in effect direction or significance across all 501 reviews. Pairwise70 provides a research-ready open resource for methodological studies requiring large-scale standardized meta-analytic benchmarks. The limitation of Cochrane-only sourcing means non-Cochrane reviews and grey literature meta-analyses remain unrepresented in this data collection.

Outside Notes

Type: data
Primary estimand: Fragility index
App: Pairwise70 R Package v1.0
Data: 501 Cochrane systematic reviews, 4,424 meta-analyses, ~50,000 studies
Code: https://github.com/mahmood726-cyber/Pairwise70
Version: 1.0
Validation: DRAFT

References

1. Walsh M, Srinathan SK, McAuley DF, et al. The statistical significance of randomized controlled trial results is frequently fragile: a case for a Fragility Index. J Clin Epidemiol. 2014;67(6):622-628.
2. Atal I, Porcher R, Boutron I, Ravaud P. The statistical significance of meta-analyses is frequently fragile: definition of a fragility index for meta-analyses. J Clin Epidemiol. 2019;111:32-40.
3. Borenstein M, Hedges LV, Higgins JPT, Rothstein HR. Introduction to Meta-Analysis. 2nd ed. Wiley; 2021.

AI Disclosure

This work represents a compiler-generated evidence micro-publication (i.e., a structured, pipeline-based synthesis output). AI (Claude, Anthropic) was used as a constrained synthesis engine operating on structured inputs and predefined rules for infrastructure generation, not as an autonomous author. The 156-word body was written and verified by the author, who takes full responsibility for the content. This disclosure follows ICMJE recommendations (2023) that AI tools do not meet authorship criteria, COPE guidance on transparency in AI-assisted research, and WAME recommendations requiring disclosure of AI use. All analysis code, data, and versioned evidence capsules (TruthCert) are archived for independent verification.
