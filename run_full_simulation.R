#!/usr/bin/env Rscript

# Full Simulation Study - V4 Methods
# 2000 iterations x 25 scenarios = 50,000 simulations
setwd("C:/Users/user/OneDrive - NHS/Documents/Pairwise70/analysis/simulation")

source("Comprehensive_Testing_Framework.R")

cat("=== FULL SIMULATION STUDY ===\n")
cat("Iterations: 2000 x 25 scenarios = 50,000 simulations\n")
cat("Methods: REML, HKSJ, WRD, CBM, RBM, SWA, TAS, EVE, PVM, AEM, SPE, SMS\n\n")

cat("Estimated time: 8-12 hours (single core, Windows)\n")
cat("Start time:", Sys.time(), "\n\n")

# Run full simulation
full_results <- run_comprehensive_simulation(
    n_sim = 2000,
    scenarios = get_all_scenarios(),
    n_cores = 1,  # Windows compatibility
    seed = 20260116
)

cat("\n=== SIMULATION COMPLETE ===\n")
cat("Total results:", nrow(full_results), "\n\n")

# Compute performance metrics
metrics <- compute_performance_metrics(full_results)

# Method summary
method_summary <- metrics[, .(
    mean_bias = mean(bias, na.rm = TRUE),
    mean_rmse = mean(rmse, na.rm = TRUE),
    mean_coverage = mean(coverage, na.rm = TRUE),
    mean_ci_width = mean(ci_width, na.rm = TRUE),
    mean_convergence = mean(convergence_rate, na.rm = TRUE),
    n_sim = .N
), by = method]

method_summary <- method_summary[order(mean_rmse)]

cat("=== METHOD SUMMARY (sorted by RMSE) ===\n")
print(method_summary)

cat("\n=== COVERAGE BY METHOD ===\n")
for (m in method_summary$method) {
  cov_vals <- metrics[method == m, mean(coverage)]
  cat(sprintf("%-5s: %.2f%% coverage (RMSE: %.4f)\n", m, cov_vals * 100,
              metrics[method == m, mean(rmse)]))
}

# Save results
saveRDS(full_results, file = "../results/v4_full_simulation_raw.rds")
saveRDS(metrics, file = "../results/v4_full_simulation_metrics.rds")
saveRDS(method_summary, file = "../results/v4_full_simulation_summary.rds")

cat("\n=== Results saved ===\n")
cat("../results/v4_full_simulation_raw.rds\n")
cat("../results/v4_full_simulation_metrics.rds\n")
cat("../results/v4_full_simulation_summary.rds\n")

cat("\nEnd time:", Sys.time(), "\n")
