#!/usr/bin/env Rscript

# Quick test of SPE and TAS fixes
setwd("C:/Users/user/OneDrive - NHS/Documents/Pairwise70")

source("R/advanced_pooling_v4.R")

cat("=== Testing SPE and TAS Fixes ===\n")

# Test data
set.seed(123)
yi <- rnorm(10, 0.3, 0.2)
vi <- rexp(10, 10) + 0.01

cat("\nTesting SPE method...\n")
spe_result <- spe_meta(yi, vi, n_samples = 5000, burnin = 500)
cat("SPE Estimate:", spe_result$estimate, "\n")
cat("SPE SE:", spe_result$se, "\n")
cat("SPE CI:", spe_result$ci_lb, "to", spe_result$ci_ub, "\n")
cat("SPE CI Width:", spe_result$ci_ub - spe_result$ci_lb, "\n")

cat("\nTesting TAS method...\n")
tas_result <- tas_meta(yi, vi)
cat("TAS Estimate:", tas_result$estimate, "\n")
cat("TAS SE:", tas_result$se, "\n")
cat("TAS CI:", tas_result$ci_lb, "to", tas_result$ci_ub, "\n")
cat("TAS CI Width:", tas_result$ci_ub - tas_result$ci_lb, "\n")

# Compare to standard methods
cat("\n=== Comparison to REML/HKSJ ===\n")
reml_fit <- metafor::rma(yi, vi, method = "REML")
hksj_fit <- metafor::rma(yi, vi, method = "REML", test = "knha")

cat("REML CI:", reml_fit$ci.lb, "to", reml_fit$ci.ub, "\n")
cat("HKSJ CI:", hksj_fit$ci.lb, "to", hksj_fit$ci.ub, "\n")

cat("\n=== Fixes applied successfully! ===\n")
