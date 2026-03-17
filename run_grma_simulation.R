#!/usr/bin/env Rscript
# ============================================================================
# GRMA Simulation Runner — 2000 reps x 25 scenarios
# ============================================================================
# Uses Pairwise70 Comprehensive_Testing_Framework with GRMA + GRMA_noguard
# added to the method registry.
#
# Output:
#   grma_simulation_raw.rds       — Full results (all reps, all methods)
#   grma_simulation_metrics.rds   — Aggregated performance metrics
#   Table_bias_rmse_v8.csv        — Bias and RMSE by scenario x method
#   Table_coverage_v8.csv         — Coverage, CI width by scenario x method
#   Table_ablation_v8.csv         — Guard ablation (GRMA vs GRMA_noguard)
#
# Expected runtime: 8-12 hours (single core, bootstrap is bottleneck)
# ============================================================================

cat("=== GRMA Simulation Runner v8 ===\n")
cat("Start time:", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "\n\n")

# Source the framework (which now includes GRMA)
# Framework uses relative paths, so we must set working directory first
old_wd <- getwd()
setwd("C:/Users/user/OneDrive - NHS/Documents/Pairwise70/analysis/simulation")
source("Comprehensive_Testing_Framework.R")
setwd(old_wd)

# ============================================================================
# Configuration
# ============================================================================

N_SIM <- 2000
SEED <- 20260213
N_CORES <- 1  # Single core for Windows stability with bootstrap

# Select methods for this run: standard comparators + GRMA variants
# (Skip slow methods like PVM, SPE, CBM to keep runtime manageable)
grma_methods <- function() {
  list(
    REML = function(yi, vi) {
      fit <- rma(yi, vi, method = "REML")
      list(estimate = coef(fit), se = fit$se, ci_lb = fit$ci.lb,
           ci_ub = fit$ci.ub, pvalue = fit$pval, tau2 = fit$tau2)
    },
    HKSJ = function(yi, vi) {
      fit <- rma(yi, vi, method = "REML", test = "knha")
      list(estimate = coef(fit), se = fit$se, ci_lb = fit$ci.lb,
           ci_ub = fit$ci.ub, pvalue = fit$pval, tau2 = fit$tau2)
    },
    WRD = function(yi, vi) {
      wrd_meta(yi, vi, bootstrap = FALSE)
    },
    RBM = function(yi, vi) {
      rbm_meta(yi, vi)
    },
    GRMA = function(yi, vi) {
      grma_meta(yi, vi, effect_guard = TRUE, n_boot = 499, bca = TRUE)
    },
    GRMA_noguard = function(yi, vi) {
      grma_meta(yi, vi, effect_guard = FALSE, n_boot = 499, bca = TRUE)
    }
  )
}

# ============================================================================
# Custom simulation runner (single core, progress reporting)
# ============================================================================

cat("Loading scenarios...\n")
scenarios <- get_all_scenarios()
methods <- grma_methods()

cat(sprintf("Configuration: %d reps x %d scenarios x %d methods\n",
            N_SIM, length(scenarios), length(methods)))
cat(sprintf("Total iterations: %d\n", N_SIM * length(scenarios)))
cat(sprintf("Seed: %d, Cores: %d\n\n", SEED, N_CORES))

# Pre-generate seeds
set.seed(SEED)
all_seeds <- sample.int(1e8, N_SIM)

results_list <- list()
idx <- 0
total <- N_SIM * length(scenarios)
start_time <- Sys.time()

for (sim in seq_len(N_SIM)) {
  for (sc_idx in seq_along(scenarios)) {
    idx <- idx + 1
    scenario <- scenarios[[sc_idx]]

    # Progress reporting every 100 iterations
    if (idx %% 100 == 0 || idx == 1) {
      elapsed <- as.numeric(difftime(Sys.time(), start_time, units = "mins"))
      rate <- idx / elapsed
      eta <- (total - idx) / rate
      cat(sprintf("[%d/%d] (%.1f%%) Scenario %s, Rep %d | %.1f iter/min | ETA: %.0f min\n",
                  idx, total, 100 * idx / total, scenario$id, sim, rate, eta))
    }

    result <- tryCatch({
      run_single_simulation(scenario, methods, seed = all_seeds[sim] + sc_idx)
    }, error = function(e) {
      NULL
    })

    if (!is.null(result)) {
      results_list[[idx]] <- result
    }
  }

  # Checkpoint every 100 reps
  if (sim %% 100 == 0) {
    cat(sprintf("\n  Checkpoint at rep %d (%.1f min elapsed)\n", sim,
                as.numeric(difftime(Sys.time(), start_time, units = "mins"))))
    # Save intermediate results
    results_dt <- data.table::rbindlist(results_list, fill = TRUE)
    saveRDS(results_dt, "C:/Users/user/Downloads/GRMA_paper/grma_simulation_checkpoint.rds")
    cat("  Saved checkpoint.\n\n")
  }
}

cat("\nSimulation complete!\n")
cat("End time:", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "\n")
cat("Total time:", format(difftime(Sys.time(), start_time, units = "hours"), digits = 3), "\n\n")

# ============================================================================
# Combine and compute metrics
# ============================================================================

results_dt <- data.table::rbindlist(results_list, fill = TRUE)
results_df <- as.data.frame(results_dt)

cat(sprintf("Total result rows: %d\n", nrow(results_df)))

# Save raw results
saveRDS(results_df, "C:/Users/user/Downloads/GRMA_paper/grma_simulation_raw.rds")
cat("Saved grma_simulation_raw.rds\n")

# Compute metrics
metrics <- compute_performance_metrics(results_df)
saveRDS(metrics, "C:/Users/user/Downloads/GRMA_paper/grma_simulation_metrics.rds")
cat("Saved grma_simulation_metrics.rds\n")

# ============================================================================
# Export CSV tables
# ============================================================================

# For GRMA, we need to also check BCa coverage
# The simulation framework uses ci_lb/ci_ub (which for GRMA = percentile CI)
# We need a separate coverage column for BCa if available

# Table: Bias & RMSE
bias_rmse <- metrics[, c("scenario", "method", "bias", "rmse", "convergence_rate",
                          "type", "name", "k", "tau2")]
write.csv(bias_rmse, "C:/Users/user/Downloads/GRMA_paper/Table_bias_rmse_v8.csv",
          row.names = FALSE)
cat("Wrote Table_bias_rmse_v8.csv\n")

# Table: Coverage & CI width
coverage <- metrics[, c("scenario", "method", "coverage", "ci_width",
                         "type_i_error", "power", "type", "name", "k", "tau2")]
write.csv(coverage, "C:/Users/user/Downloads/GRMA_paper/Table_coverage_v8.csv",
          row.names = FALSE)
cat("Wrote Table_coverage_v8.csv\n")

# Table: Guard ablation (GRMA vs GRMA_noguard)
ablation_grma <- metrics[metrics$method == "GRMA",
                          c("scenario", "bias", "rmse", "coverage", "ci_width",
                            "convergence_rate", "type", "name")]
names(ablation_grma)[2:6] <- paste0(names(ablation_grma)[2:6], "_guard")

ablation_ng <- metrics[metrics$method == "GRMA_noguard",
                        c("scenario", "bias", "rmse", "coverage", "ci_width",
                          "convergence_rate")]
names(ablation_ng)[2:6] <- paste0(names(ablation_ng)[2:6], "_noguard")

ablation <- merge(ablation_grma, ablation_ng, by = "scenario")
ablation$bias_diff <- ablation$bias_guard - ablation$bias_noguard
ablation$rmse_diff <- ablation$rmse_guard - ablation$rmse_noguard
ablation$coverage_diff <- ablation$coverage_guard - ablation$coverage_noguard

write.csv(ablation, "C:/Users/user/Downloads/GRMA_paper/Table_ablation_v8.csv",
          row.names = FALSE)
cat("Wrote Table_ablation_v8.csv\n")

# ============================================================================
# Summary
# ============================================================================

cat("\n=== Method Summary (across all scenarios) ===\n")
method_summary <- data.table::as.data.table(metrics)[, .(
  mean_bias = mean(bias, na.rm = TRUE),
  mean_rmse = mean(rmse, na.rm = TRUE),
  mean_coverage = mean(coverage, na.rm = TRUE),
  mean_ci_width = mean(ci_width, na.rm = TRUE),
  mean_convergence = mean(convergence_rate, na.rm = TRUE)
), by = method]
print(method_summary[order(mean_rmse)])

cat("\n=== Guard Ablation Summary ===\n")
cat(sprintf("Scenarios where guard helps (lower RMSE): %d / %d\n",
            sum(ablation$rmse_diff < 0), nrow(ablation)))
cat(sprintf("Mean RMSE diff (guard - noguard): %.6f\n",
            mean(ablation$rmse_diff)))

cat("\nDone.\n")
