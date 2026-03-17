#!/usr/bin/env Rscript

# Mini validation to test SPE fix
setwd("C:/Users/user/OneDrive - NHS/Documents/Pairwise70")

source("R/advanced_pooling_v4.R")

cat("=== Mini Validation: SPE Fix Test ===\n")
cat("20 iterations x 5 scenarios = 100 simulations\n\n")

set.seed(2024)
n_sim <- 20
scenarios_to_test <- list(
  list(id = "B2", name = "Standard", k = 10, tau2 = 0.05, true_effect = 0.3,
       type = "baseline", outlier = NULL, pub_bias = NULL),
  list(id = "H3", name = "High het", k = 10, tau2 = 0.20, true_effect = 0.3,
       type = "heterogeneity", outlier = NULL, pub_bias = NULL),
  list(id = "O1", name = "Outlier", k = 10, tau2 = 0.05, true_effect = 0.3,
       type = "outlier", outlier = list(n = 1, shift = 3 * sqrt(0.05)), pub_bias = NULL),
  list(id = "PB2", name = "Pub bias", k = 20, tau2 = 0.05, true_effect = 0.3,
       type = "pub_bias", outlier = NULL, pub_bias = list(type = "step", cutoff = 0.05)),
  list(id = "S1", name = "Small k", k = 5, tau2 = 0.05, true_effect = 0.3,
       type = "small_study", mean_n = 20, outlier = NULL, pub_bias = NULL)
)

# Test just SPE and a few reference methods
methods_to_test <- list(
  REML = function(yi, vi) {
    fit <- metafor::rma(yi, vi, method = "REML")
    list(estimate = as.numeric(coef(fit)), se = fit$se,
         ci_lb = fit$ci.lb, ci_ub = fit$ci.ub, pvalue = fit$pval)
  },
  HKSJ = function(yi, vi) {
    fit <- metafor::rma(yi, vi, method = "REML", test = "knha")
    list(estimate = as.numeric(coef(fit)), se = fit$se,
         ci_lb = fit$ci.lb, ci_ub = fit$ci.ub, pvalue = fit$pval)
  },
  SPE = function(yi, vi) {
    spe_meta(yi, vi, n_samples = 2000, burnin = 200)
  }
)

results <- list()

for (sc in scenarios_to_test) {
  for (i in 1:n_sim) {
    set.seed(i + 1000)

    # Generate data
    yi <- rnorm(sc$k, sc$true_effect, sqrt(sc$tau2))
    vi <- rexp(sc$k, 10) + 0.01

    # Add outlier if specified
    if (!is.null(sc$outlier)) {
      yi[1] <- yi[1] + sc$outlier$shift
    }

    # Apply pub bias if specified
    if (!is.null(sc$pub_bias)) {
      z <- yi / sqrt(vi)
      p <- 2 * (1 - pnorm(abs(z)))
      if (sc$pub_bias$type == "step") {
        keep <- p <= sc$pub_bias$cutoff
        if (sum(keep) < 3) keep <- rank(p) <= floor(length(yi) / 2)
        yi <- yi[keep]
        vi <- vi[keep]
      }
    }

    if (length(yi) < 3) next

    # Run methods
    for (method_name in names(methods_to_test)) {
      result <- tryCatch({
        methods_to_test[[method_name]](yi, vi)
      }, error = function(e) NULL)

      if (!is.null(result)) {
        covered <- (sc$true_effect >= result$ci_lb) && (sc$true_effect <= result$ci_ub)
        results[[length(results) + 1]] <- data.frame(
          scenario = sc$id,
          method = method_name,
          covered = covered,
          ci_width = result$ci_ub - result$ci_lb
        )
      }
    }
  }
}

results_df <- do.call(rbind, results)

# Summary
summary <- results_df[, .(coverage = mean(covered), ci_width = mean(ci_width)), by = method]
cat("\n=== Results ===\n")
print(summary)

cat("\n=== SPE Coverage: ", round(summary[method == "SPE", coverage], 3), "===\n", sep = "")
