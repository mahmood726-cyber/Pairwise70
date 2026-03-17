#!/usr/bin/env Rscript

# Monitor and Process Full Simulation Results
# Run this to check simulation status or process results when complete

setwd("C:/Users/user/OneDrive - NHS/Documents/Pairwise70/analysis")

cat("=== Pairwise70 V4 - Simulation Status Check ===\n\n")

# Check for results files
results_dir <- "results"
full_sim_files <- c(
  "v4_full_simulation_raw.rds",
  "v4_full_simulation_metrics.rds",
  "v4_full_simulation_summary.rds"
)

existing_files <- file.exists(file.path(results_dir, full_sim_files))

cat("Results Files Status:\n")
for (i in seq_along(full_sim_files)) {
  status <- ifelse(existing_files[i], "✓ FOUND", "✗ MISSING")
  cat(sprintf("  %s %s\n", status, full_sim_files[i]))
}

cat("\n")

n_found <- sum(existing_files)

if (n_found == 0) {
  cat("STATUS: Simulation NOT complete\n")
  cat("The full simulation is still running.\n")
  cat("Expected completion: 8-12 hours after start time.\n")
  cat("\nTo check if R is still running:\n")
  cat("  - Windows: tasklist | findstr R\n")
  cat("  - Git Bash: ps aux | grep R\n")

} else if (n_found < 3) {
  cat("STATUS: Simulation PARTIALLY complete\n")
  cat(sprintf("Found %d of 3 expected files.\n", n_found))
  cat("The simulation may still be running or was interrupted.\n")

} else {
  cat("STATUS: ✓ SIMULATION COMPLETE!\n\n")

  # Load and process results
  cat("Loading results...\n")
  metrics <- readRDS(file.path(results_dir, "v4_full_simulation_metrics.rds"))
  summary <- readRDS(file.path(results_dir, "v4_full_simulation_summary.rds"))

  cat("\n=== FINAL RESULTS (2000 iterations x 25 scenarios) ===\n\n")

  # Print summary table
  print(summary, row.names = FALSE)

  cat("\n=== Coverage by Method ===\n")
  for (m in summary$method) {
    cov_vals <- metrics[method == m, mean(coverage)]
    rmse_vals <- metrics[method == m, mean(rmse)]
    cat(sprintf("%-5s: %6.2f%% coverage (RMSE: %.4f)\n",
                m, cov_vals * 100, rmse_vals))
  }

  cat("\n=== Best Methods by Metric ===\n")
  best_rmse <- summary[which.min(mean_rmse), ]
  best_cov <- summary[which.max(mean_coverage), ]
  cat(sprintf("  Lowest RMSE:  %s (%.4f)\n", best_rmse$method, best_rmse$mean_rmse))
  cat(sprintf("  Best Coverage: %s (%.2f%%)\n", best_cov$method, best_cov$mean_coverage * 100))

  # Generate final plots
  cat("\n=== Generating Final Plots ===\n")
  source("simulation/generate_plots.R")

  # Copy final results to v2 directory
  v2_results_dir <- "../../Pairwise70_Results_v2/simulation_results"
  if (dir.exists(v2_results_dir)) {
    file.copy(file.path(results_dir, "v4_full_simulation_raw.rds"),
              file.path(v2_results_dir, "v4_full_simulation_raw.rds"))
    file.copy(file.path(results_dir, "v4_full_simulation_metrics.rds"),
              file.path(v2_results_dir, "v4_full_simulation_metrics.rds"))
    file.copy(file.path(results_dir, "v4_full_simulation_summary.rds"),
              file.path(v2_results_dir, "v4_full_simulation_summary.rds"))
    cat("\nResults copied to Pairwise70_Results_v2/\n")
  }

  cat("\n=== All Processing Complete ===\n")
}

cat("\nEnd time:", Sys.time(), "\n")
