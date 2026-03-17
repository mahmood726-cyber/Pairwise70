#!/usr/bin/env Rscript

# Quick Validation of V4 Methods
# Run 50 iterations x 25 scenarios = 1250 simulations

setwd("C:/Users/user/OneDrive - NHS/Documents/Pairwise70/analysis/simulation")

source("Comprehensive_Testing_Framework.R")

cat("=== QUICK VALIDATION ===\n")
cat("Iterations: 50 x 25 scenarios = 1250 simulations\n")
cat("Methods: REML, HKSJ, WRD, CBM, RBM, SWA, TAS, EVE, PVM, AEM, SPE, SMS\n\n")

# Run quick validation (single core for Windows compatibility)
quick_results <- run_quick_validation(n_sim = 50, n_cores = 1)

cat("\n=== METHOD SUMMARY (sorted by RMSE) ===\n")
print(quick_results$method_summary)

cat("\n=== COVERAGE BY METHOD ===\n")
coverage_summary <- quick_results$metrics[, .(method, scenario, coverage)]
for (m in unique(coverage_summary$method)) {
  cov_vals <- coverage_summary[method == m, mean(coverage)]
  cat(sprintf("%-5s: %.1f%% coverage\n", m, cov_vals * 100))
}

# Save results
saveRDS(quick_results$results, file = "../results/v4_quick_validation.rds")
saveRDS(quick_results$metrics, file = "../results/v4_quick_validation_metrics.rds")

cat("\n=== Results saved ===\n")
cat("../results/v4_quick_validation.rds\n")
cat("../results/v4_quick_validation_metrics.rds\n")
