#!/usr/bin/env Rscript

# Generate Final Publication Plots from Full Simulation Results
# Pairwise70 V4 Methods - 2000 iterations x 25 scenarios

setwd("C:/Users/user/OneDrive - NHS/Documents/Pairwise70/analysis")

library(ggplot2)
library(data.table)
library(scales)

cat("=== Generating Final Plots from Full Simulation ===\n")

# Load full simulation results
metrics <- readRDS("results/v4_full_simulation_metrics.rds")
summary <- readRDS("results/v4_full_simulation_summary.rds")

# Aggregate by method for plotting
plot_data <- metrics[, .(
  mean_bias = mean(bias, na.rm = TRUE),
  mean_rmse = mean(rmse, na.rm = TRUE),
  mean_coverage = mean(coverage, na.rm = TRUE),
  mean_ci_width = mean(ci_width, na.rm = TRUE),
  mean_power = mean(power, na.rm = TRUE),
  mean_type1 = mean(type1_error, na.rm = TRUE)
), by = method]

# Method colors
method_colors <- c(
  "REML" = "#1f77b4", "HKSJ" = "#ff7f0e", "MWM" = "#2ca02c",
  "WRD" = "#d62728", "CBM" = "#9467bd", "RBM" = "#8c564b",
  "SWA" = "#e377c2", "TAS" = "#7f7f7f", "EVE" = "#bcbd22",
  "PVM" = "#17becf", "AEM" = "#aec7e8", "SPE" = "#ffbb78",
  "SMS" = "#98df8a"
)

# 1. RMSE Comparison Plot
p1 <- ggplot(plot_data, aes(x = reorder(method, mean_rmse), y = mean_rmse,
                             fill = method)) +
  geom_bar(stat = "identity", color = "black", size = 0.3) +
  scale_fill_manual(values = method_colors) +
  labs(title = "RMSE Comparison (2000 iter x 25 scenarios)",
       subtitle = "50,000 total simulations",
       x = "Method", y = "Root Mean Square Error") +
  coord_cartesian(ylim = c(0.12, max(plot_data$mean_rmse) * 1.1)) +
  theme_minimal() +
  theme(legend.position = "none",
        axis.text.x = element_text(angle = 45, hjust = 1),
        plot.title = element_text(face = "bold"))

ggsave("results/plots/v4_final_rmse_comparison.png", p1,
       width = 10, height = 6, dpi = 300)

# 2. Coverage Comparison Plot
p2 <- ggplot(plot_data, aes(x = reorder(method, -mean_coverage), y = mean_coverage * 100,
                             fill = method)) +
  geom_bar(stat = "identity", color = "black", size = 0.3) +
  geom_hline(yintercept = 95, linetype = "dashed", color = "red", size = 1) +
  scale_fill_manual(values = method_colors) +
  labs(title = "Coverage Comparison (2000 iter x 25 scenarios)",
       subtitle = "Target: 95% (dashed line)",
       x = "Method", y = "Coverage (%)") +
  coord_cartesian(ylim = c(80, 100)) +
  scale_y_continuous(breaks = seq(80, 100, 2)) +
  theme_minimal() +
  theme(legend.position = "none",
        axis.text.x = element_text(angle = 45, hjust = 1),
        plot.title = element_text(face = "bold"))

ggsave("results/plots/v4_final_coverage_comparison.png", p2,
       width = 10, height = 6, dpi = 300)

# 3. Bias vs RMSE Scatter
p3 <- ggplot(plot_data, aes(x = abs(mean_bias), y = mean_rmse, color = method, size = mean_coverage)) +
  geom_point(alpha = 0.7) +
  scale_color_manual(values = method_colors) +
  labs(title = "Bias vs RMSE (2000 iter x 25 scenarios)",
       subtitle = "Size represents coverage",
       x = "Absolute Bias", y = "RMSE", color = "Method", size = "Coverage") +
  theme_minimal() +
  theme(plot.title = element_text(face = "bold"),
        legend.position = "right")

ggsave("results/plots/v4_final_bias_rmse_scatter.png", p3,
       width = 10, height = 6, dpi = 300)

# 4. Coverage vs RMSE Scatter
p4 <- ggplot(plot_data, aes(x = mean_rmse, y = mean_coverage * 100,
                             color = method, label = method)) +
  geom_point(size = 3) +
  geom_text(vjust = -0.5, hjust = 0.5, size = 3, check_overlap = TRUE) +
  geom_hline(yintercept = 95, linetype = "dashed", color = "red", alpha = 0.5) +
  scale_color_manual(values = method_colors) +
  labs(title = "Coverage vs RMSE Trade-off (2000 iter x 25 scenarios)",
       subtitle = "Ideal: Low RMSE, High Coverage (top-left)",
       x = "RMSE", y = "Coverage (%)", color = "Method") +
  theme_minimal() +
  theme(plot.title = element_text(face = "bold"),
        legend.position = "right")

ggsave("results/plots/v4_final_coverage_rmse_scatter.png", p4,
       width = 10, height = 6, dpi = 300)

cat("\n=== Final plots saved to results/plots/ ===\n")
cat("  - v4_final_rmse_comparison.png\n")
cat("  - v4_final_coverage_comparison.png\n")
cat("  - v4_final_bias_rmse_scatter.png\n")
cat("  - v4_final_coverage_rmse_scatter.png\n")
