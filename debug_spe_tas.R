#!/usr/bin/env Rscript

# Debug SPE and TAS
setwd("C:/Users/user/OneDrive - NHS/Documents/Pairwise70")
source("R/advanced_pooling_v4.R")

set.seed(123)
yi <- rnorm(10, 0.3, 0.2)
vi <- rexp(10, 10) + 0.01

cat("yi:", yi, "\n")
cat("vi:", vi, "\n")

# Debug SPE
cat("\n=== SPE Debug ===\n")
spe <- spe_meta(yi, vi, n_samples = 1000, burnin = 100)
cat("SPE tau2_samples range:", range(spe$tau2_samples), "\n")
cat("SPE theta_samples range:", range(spe$theta_samples), "\n")
cat("SPE theta_samples sd:", sd(spe$theta_samples), "\n")
cat("SPE accept_rate:", spe$accept_rate, "\n")
cat("SPE estimate:", spe$estimate, "\n")
cat("SPE se:", spe$se, "\n")

# Debug TAS
cat("\n=== TAS Debug ===\n")
tas <- tas_meta(yi, vi)
cat("TAS n_imputed:", tas$n_imputed, "\n")
cat("TAS shrinkage_factor:", tas$shrinkage_factor, "\n")
cat("TAS shrinkage_weight:", tas$shrinkage_weight, "\n")
cat("TAS tf_estimate:", tas$tf_estimate, "\n")
cat("TAS shrunk_estimate:", tas$shrunk_estimate, "\n")
cat("TAS estimate:", tas$estimate, "\n")
cat("TAS se:", tas$se, "\n")
