#!/usr/bin/env Rscript

required_pkgs <- c("data.table")
missing_pkgs <- required_pkgs[!vapply(required_pkgs, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing_pkgs) > 0) {
  stop(paste("Missing required packages:", paste(missing_pkgs, collapse = ", ")))
}

suppressPackageStartupMessages({
  library(data.table)
})

parse_args <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  out <- list(
    results_dir = "analysis/results",
    stamp = NULL
  )
  for (arg in args) {
    if (grepl("^--results_dir=", arg)) out$results_dir <- sub("^--results_dir=", "", arg)
    if (grepl("^--stamp=", arg)) out$stamp <- sub("^--stamp=", "", arg)
  }
  out
}

latest_stamp <- function(results_dir) {
  files <- list.files(results_dir, pattern = "^pbm_world_rank_overall_\\d{8}_\\d{6}\\.csv$", full.names = FALSE)
  if (length(files) == 0) stop("No pbm_world_rank_overall_* files found in results_dir")
  stems <- sub("^pbm_world_rank_overall_(\\d{8}_\\d{6})\\.csv$", "\\1", files)
  stems[order(stems, decreasing = TRUE)][1]
}

write_markdown_table <- function(dt, path, title) {
  header <- paste0("# ", title, "\n\n")
  cols <- names(dt)
  md <- c(
    header,
    paste0("| ", paste(cols, collapse = " | "), " |"),
    paste0("| ", paste(rep("---", length(cols)), collapse = " | "), " |")
  )
  for (i in seq_len(nrow(dt))) {
    vals <- as.character(unlist(dt[i]))
    md <- c(md, paste0("| ", paste(vals, collapse = " | "), " |"))
  }
  writeLines(md, con = path)
}

plot_rank_bars <- function(dt, title, out_png) {
  ord <- dt[order(rank)]
  cols <- ifelse(ord$method == "PBM", "#D55E00", "#4C78A8")

  png(out_png, width = 2200, height = 1300, res = 200)
  par(mar = c(8, 7, 5, 2))
  mids <- barplot(
    height = rev(ord$world_score),
    names.arg = rev(ord$method),
    horiz = TRUE,
    las = 1,
    col = rev(cols),
    border = NA,
    xlab = "World Score (Lower Is Better)",
    cex.names = 1.2,
    cex.lab = 1.25,
    cex.main = 1.4,
    main = title
  )
  text(
    x = rev(ord$world_score) + 0.015,
    y = mids,
    labels = paste0("Rank ", rev(ord$rank), " | Score ", sprintf("%.3f", rev(ord$world_score))),
    pos = 4,
    cex = 1.0
  )
  legend("topright", legend = c("PBM", "Other"), fill = c("#D55E00", "#4C78A8"), bty = "n", cex = 1.1)
  grid(nx = NA, ny = NULL, col = "#DDDDDD")
  dev.off()
}

plot_scenario_heatmap <- function(scenario_dt, out_png) {
  # Use score-like surrogate: abs_bias + rmse + coverage gap
  x <- copy(scenario_dt)
  x[, coverage_gap := abs(coverage - 0.95)]
  x[, composite := abs_bias + rmse + coverage_gap]

  mat_dt <- dcast(x, scenario ~ method, value.var = "composite")
  scenarios <- mat_dt$scenario
  m <- as.matrix(mat_dt[, -1])
  rownames(m) <- scenarios

  # Global normalization keeps absolute gaps comparable across scenarios.
  g_rng <- range(m, na.rm = TRUE)
  if (is.finite(g_rng[1]) && is.finite(g_rng[2]) && diff(g_rng) > 0) {
    m <- (m - g_rng[1]) / diff(g_rng)
  } else {
    m[,] <- 0.5
  }

  cols <- colorRampPalette(c("#1B9E77", "#F7F7F7", "#D95F02"))(120)

  png(out_png, width = 2200, height = 1700, res = 220)
  par(mar = c(10, 10, 5, 2))
  image(
    x = seq_len(ncol(m)),
    y = seq_len(nrow(m)),
    z = t(m[nrow(m):1, , drop = FALSE]),
    col = cols,
    axes = FALSE,
    xlab = "",
    ylab = "",
    main = "Scenario-Method Heatmap (Global Scale, Lower Composite Is Better)"
  )
  axis(1, at = seq_len(ncol(m)), labels = colnames(m), las = 2, cex.axis = 1.1)
  axis(2, at = seq_len(nrow(m)), labels = rev(rownames(m)), las = 2, cex.axis = 1.0)
  box()
  mtext("Methods", side = 1, line = 8, cex = 1.2)
  mtext("Scenarios", side = 2, line = 8, cex = 1.2)
  dev.off()
}

main <- function() {
  args <- parse_args()
  results_dir <- normalizePath(args$results_dir, winslash = "/")
  stamp <- if (is.null(args$stamp)) latest_stamp(results_dir) else args$stamp

  overall_path <- file.path(results_dir, paste0("pbm_world_rank_overall_", stamp, ".csv"))
  pub_path <- file.path(results_dir, paste0("pbm_world_rank_pubbias_", stamp, ".csv"))
  scen_path <- file.path(results_dir, paste0("pbm_world_scenario_metrics_", stamp, ".csv"))

  if (!file.exists(overall_path) || !file.exists(pub_path) || !file.exists(scen_path)) {
    stop("Missing one or more benchmark source files for stamp: ", stamp)
  }

  overall <- fread(overall_path)
  pub <- fread(pub_path)
  scen <- fread(scen_path)

  tables_dir <- file.path(results_dir, "tables")
  figs_dir <- file.path(results_dir, "figures")
  dir.create(tables_dir, recursive = TRUE, showWarnings = FALSE)
  dir.create(figs_dir, recursive = TRUE, showWarnings = FALSE)

  # Manuscript tables
  t_overall <- overall[order(rank), .(
    rank, method,
    world_score = sprintf("%.4f", world_score),
    applicability = sprintf("%.3f", applicability),
    convergence = sprintf("%.3f", convergence),
    abs_bias = sprintf("%.4f", abs_bias),
    rmse = sprintf("%.4f", rmse),
    coverage = sprintf("%.3f", coverage),
    type1_error = sprintf("%.4f", type1_error),
    power = sprintf("%.4f", power)
  )]

  t_pub <- pub[order(rank), .(
    rank, method,
    world_score = sprintf("%.4f", world_score),
    applicability = sprintf("%.3f", applicability),
    convergence = sprintf("%.3f", convergence),
    abs_bias = sprintf("%.4f", abs_bias),
    rmse = sprintf("%.4f", rmse),
    coverage = sprintf("%.3f", coverage),
    type1_error = sprintf("%.4f", type1_error),
    power = sprintf("%.4f", power)
  )]

  fwrite(t_overall, file.path(tables_dir, paste0("table_pbm_overall_ranking_", stamp, ".csv")))
  fwrite(t_pub, file.path(tables_dir, paste0("table_pbm_pubbias_ranking_", stamp, ".csv")))
  write_markdown_table(t_overall, file.path(tables_dir, paste0("table_pbm_overall_ranking_", stamp, ".md")), "PBM Benchmark Overall Ranking")
  write_markdown_table(t_pub, file.path(tables_dir, paste0("table_pbm_pubbias_ranking_", stamp, ".md")), "PBM Benchmark Publication-Bias Ranking")

  # Figures
  plot_rank_bars(overall, "Overall Method Ranking (PBM Benchmark)", file.path(figs_dir, paste0("fig_pbm_overall_ranking_", stamp, ".png")))
  plot_rank_bars(pub, "Publication-Bias Scenario Ranking (PBM Benchmark)", file.path(figs_dir, paste0("fig_pbm_pubbias_ranking_", stamp, ".png")))
  plot_scenario_heatmap(scen, file.path(figs_dir, paste0("fig_pbm_scenario_heatmap_", stamp, ".png")))

  # Executive summary
  summary_lines <- c(
    "# PBM Manuscript Outputs",
    "",
    paste0("- Stamp: ", stamp),
    paste0("- Generated: ", Sys.time()),
    "",
    "## Top Methods",
    paste0("1. Overall: ", overall[order(rank)]$method[1]),
    paste0("2. Publication-bias: ", pub[order(rank)]$method[1]),
    "",
    "## Files",
    paste0("- ", file.path("analysis/results/tables", paste0("table_pbm_overall_ranking_", stamp, ".csv"))),
    paste0("- ", file.path("analysis/results/tables", paste0("table_pbm_pubbias_ranking_", stamp, ".csv"))),
    paste0("- ", file.path("analysis/results/figures", paste0("fig_pbm_overall_ranking_", stamp, ".png"))),
    paste0("- ", file.path("analysis/results/figures", paste0("fig_pbm_pubbias_ranking_", stamp, ".png"))),
    paste0("- ", file.path("analysis/results/figures", paste0("fig_pbm_scenario_heatmap_", stamp, ".png")))
  )

  summary_path <- file.path(results_dir, paste0("pbm_manuscript_outputs_", stamp, ".md"))
  writeLines(summary_lines, con = summary_path)

  cat("Manuscript outputs generated.\n")
  cat("Summary:", summary_path, "\n")
}

main()
