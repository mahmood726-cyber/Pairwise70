#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(data.table)
  library(ggplot2)
})

repo_root <- normalizePath(".", winslash = "/", mustWork = TRUE)
out_dir <- file.path(repo_root, "analysis", "output")
fig_dir <- file.path(out_dir, "figures_assumption_debt")
dir.create(fig_dir, showWarnings = FALSE, recursive = TRUE)

summary_file <- file.path(out_dir, "assumption_debt_model_summary.csv")
components_file <- file.path(out_dir, "assumption_debt_components.csv")
by_score_file <- file.path(out_dir, "assumption_debt_by_score.csv")
component_model_file <- file.path(out_dir, "assumption_debt_component_model_coefficients.csv")

required_files <- c(summary_file, components_file, by_score_file, component_model_file)
missing_files <- required_files[!file.exists(required_files)]
if (length(missing_files) > 0) {
  stop("Missing required files:\n", paste(missing_files, collapse = "\n"))
}

components <- fread(components_file)
by_score <- fread(by_score_file)
coef_dt <- fread(component_model_file)

label_map <- c(
  sparse_k = "k < 10",
  high_heterogeneity = "I2 >= 50%",
  small_study_signal = "Small-study signal\n(Egger p < 0.10)",
  dominance_signal = "Dominance\n(max weight >= 50%)",
  sparse_events_signal = "Sparse-events flag > 0"
)

components[, component_label := factor(label_map[component], levels = unname(label_map))]
components[, prevalence_pct := 100 * prevalence]

p1 <- ggplot(components, aes(x = component_label, y = prevalence_pct)) +
  geom_col(fill = "#1f78b4", width = 0.72) +
  geom_text(aes(label = sprintf("%.1f%%", prevalence_pct)), vjust = -0.35, size = 3.6) +
  scale_y_continuous(limits = c(0, max(components$prevalence_pct) * 1.12)) +
  labs(
    title = "Figure 1. Assumption Debt Components in Cochrane Pairwise Meta-Analyses",
    x = NULL,
    y = "Prevalence (%)"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold"),
    axis.text.x = element_text(angle = 20, hjust = 1),
    panel.grid.minor = element_blank()
  )

by_score[, score := as.integer(assumption_debt_score)]
by_score[, fragile_n := round(n_meta * fragile_rate)]
by_score[, ci_lb := 100 * pmax(0, fragile_rate - 1.96 * sqrt((fragile_rate * (1 - fragile_rate)) / pmax(n_meta, 1)))]
by_score[, ci_ub := 100 * pmin(1, fragile_rate + 1.96 * sqrt((fragile_rate * (1 - fragile_rate)) / pmax(n_meta, 1)))]
by_score[, fragile_pct := 100 * fragile_rate]

p2 <- ggplot(by_score, aes(x = score, y = fragile_pct)) +
  geom_col(fill = "#33a02c", width = 0.72) +
  geom_errorbar(aes(ymin = ci_lb, ymax = ci_ub), width = 0.15, linewidth = 0.7) +
  geom_text(aes(label = sprintf("n=%d", n_meta)), vjust = -1.0, size = 3.4) +
  geom_text(aes(label = sprintf("%.1f%%", fragile_pct)), vjust = 1.7, color = "white", size = 3.6) +
  scale_x_continuous(breaks = by_score$score) +
  scale_y_continuous(limits = c(0, max(by_score$ci_ub) * 1.15)) +
  labs(
    title = "Figure 2. Fragility Gradient by Assumption Debt Score",
    x = "Assumption Debt Score",
    y = "Fragility rate (%)"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold"),
    panel.grid.minor = element_blank()
  )

exclude_terms <- c("(Intercept)", "log_k", "abs_estimate", "tau2_capped")
plot_coef <- coef_dt[!(term %in% exclude_terms)]
plot_coef[, term_label := factor(
  term,
  levels = c("high_heterogeneity", "dominance_signal", "small_study_signal", "sparse_events_signal", "sparse_k"),
  labels = c(
    "I2 >= 50%",
    "Dominance (max weight >= 50%)",
    "Small-study signal (Egger p < 0.10)",
    "Sparse-events flag > 0",
    "k < 10"
  )
)]

p3 <- ggplot(plot_coef, aes(x = OR, y = term_label)) +
  geom_vline(xintercept = 1, linetype = "dashed", color = "gray45") +
  geom_errorbar(
    aes(xmin = OR_low, xmax = OR_high),
    orientation = "y",
    width = 0.22,
    color = "#e31a1c",
    linewidth = 0.9
  ) +
  geom_point(size = 2.7, color = "#e31a1c") +
  scale_x_log10() +
  labs(
    title = "Figure 3. Adjusted Odds Ratios for Fragility (Component Model)",
    x = "Odds ratio (log scale)",
    y = NULL
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold"),
    panel.grid.minor = element_blank()
  )

ggsave(file.path(fig_dir, "figure1_assumption_debt_components.png"), p1, width = 10, height = 6, dpi = 320)
ggsave(file.path(fig_dir, "figure2_fragility_gradient.png"), p2, width = 9, height = 6, dpi = 320)
ggsave(file.path(fig_dir, "figure3_adjusted_or_forest.png"), p3, width = 10, height = 6.2, dpi = 320)

manifest <- c(
  "# Assumption Debt Figure Manifest",
  "",
  "Generated files:",
  "- figures_assumption_debt/figure1_assumption_debt_components.png",
  "- figures_assumption_debt/figure2_fragility_gradient.png",
  "- figures_assumption_debt/figure3_adjusted_or_forest.png",
  "",
  "Source script:",
  "- analysis/assumption_debt_figures.R"
)
writeLines(manifest, file.path(out_dir, "assumption_debt_figure_manifest.md"))

cat("Assumption debt figures generated in analysis/output/figures_assumption_debt/\n")
