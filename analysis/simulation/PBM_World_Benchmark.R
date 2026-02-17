#!/usr/bin/env Rscript

required_pkgs <- c("metafor", "data.table")
missing_pkgs <- required_pkgs[!vapply(required_pkgs, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing_pkgs) > 0) {
  stop(
    paste0(
      "Missing required packages: ", paste(missing_pkgs, collapse = ", "), "\n",
      "Install before running benchmark, e.g.:\n",
      "Rscript -e \"install.packages(c('metafor','data.table'), repos='https://cloud.r-project.org')\""
    )
  )
}

suppressPackageStartupMessages({
  library(metafor)
  library(data.table)
  library(parallel)
})

parse_args <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  out <- list(
    n_sim = 300L,
    seed = 20260213L,
    n_boot_swa = 99L,
    out_dir = "analysis/results",
    min_obs_k = 4L,
    n_cores = max(1L, parallel::detectCores() - 1L)
  )

  for (arg in args) {
    if (grepl("^--n_sim=", arg)) out$n_sim <- as.integer(sub("^--n_sim=", "", arg))
    if (grepl("^--seed=", arg)) out$seed <- as.integer(sub("^--seed=", "", arg))
    if (grepl("^--n_boot_swa=", arg)) out$n_boot_swa <- as.integer(sub("^--n_boot_swa=", "", arg))
    if (grepl("^--out_dir=", arg)) out$out_dir <- sub("^--out_dir=", "", arg)
    if (grepl("^--min_obs_k=", arg)) out$min_obs_k <- as.integer(sub("^--min_obs_k=", "", arg))
    if (grepl("^--n_cores=", arg)) out$n_cores <- as.integer(sub("^--n_cores=", "", arg))
  }

  out
}

resolve_out_dir <- function(repo_root, out_dir_arg) {
  if (grepl("^(/|[A-Za-z]:[/\\\\])", out_dir_arg)) {
    return(normalizePath(out_dir_arg, winslash = "/", mustWork = FALSE))
  }
  normalizePath(file.path(repo_root, out_dir_arg), winslash = "/", mustWork = FALSE)
}

safe_num <- function(x) {
  if (length(x) == 0 || is.null(x) || !is.finite(x[1])) return(NA_real_)
  as.numeric(x[1])
}

safe_ci <- function(est, se, k) {
  if (!is.finite(est) || !is.finite(se) || se <= 0) {
    return(list(lb = NA_real_, ub = NA_real_))
  }
  df <- max(1, k - 2)
  t_crit <- qt(0.975, df)
  list(lb = est - t_crit * se, ub = est + t_crit * se)
}

petpeese_method <- function(yi, vi) {
  k <- length(yi)
  sei <- sqrt(vi)

  pet <- tryCatch(
    metafor::rma(yi, vi, mods = ~ sei, method = "REML", test = "knha"),
    error = function(e) NULL
  )
  peese <- tryCatch(
    metafor::rma(yi, vi, mods = ~ vi, method = "REML", test = "knha"),
    error = function(e) NULL
  )

  pet_ok <- !is.null(pet) && is.finite(pet$se[1]) && pet$se[1] > 0
  peese_ok <- !is.null(peese) && is.finite(peese$se[1]) && peese$se[1] > 0
  pet_p <- if (pet_ok) pet$pval[1] else NA_real_

  if (pet_ok && peese_ok && is.finite(pet_p) && pet_p < 0.10) {
    est <- safe_num(coef(peese)[1])
    se <- safe_num(peese$se[1])
    mode <- "PEESE"
  } else if (pet_ok) {
    est <- safe_num(coef(pet)[1])
    se <- safe_num(pet$se[1])
    mode <- "PET"
  } else if (peese_ok) {
    est <- safe_num(coef(peese)[1])
    se <- safe_num(peese$se[1])
    mode <- "PEESE"
  } else {
    est <- NA_real_
    se <- NA_real_
    mode <- "unavailable"
  }

  ci <- safe_ci(est, se, k)
  list(
    estimate = est,
    se = se,
    ci_lb = ci$lb,
    ci_ub = ci$ub,
    pvalue = ifelse(is.finite(est) && is.finite(se) && se > 0, 2 * (1 - pt(abs(est / se), max(1, k - 2))), NA_real_),
    mode = mode
  )
}

trimfill_method <- function(yi, vi) {
  k <- length(yi)
  fit_reml <- tryCatch(metafor::rma(yi, vi, method = "REML"), error = function(e) NULL)
  if (is.null(fit_reml)) {
    return(list(estimate = NA_real_, se = NA_real_, ci_lb = NA_real_, ci_ub = NA_real_, pvalue = NA_real_, n_imputed = NA_integer_))
  }

  tf <- tryCatch(metafor::trimfill(fit_reml), error = function(e) NULL)
  if (is.null(tf)) {
    return(list(
      estimate = safe_num(coef(fit_reml)),
      se = safe_num(fit_reml$se),
      ci_lb = safe_num(fit_reml$ci.lb),
      ci_ub = safe_num(fit_reml$ci.ub),
      pvalue = safe_num(fit_reml$pval),
      n_imputed = 0L
    ))
  }

  n_imp <- if ("fill" %in% names(tf) && !is.null(tf$fill)) tf$k - k else 0L
  list(
    estimate = safe_num(coef(tf)),
    se = safe_num(tf$se),
    ci_lb = safe_num(tf$ci.lb),
    ci_ub = safe_num(tf$ci.ub),
    pvalue = safe_num(tf$pval),
    n_imputed = as.integer(n_imp)
  )
}

scenario_grid <- function() {
  list(
    # Baseline / heterogeneity
    list(id = "BASE_NULL", kind = "none", k = 10, tau2 = 0.05, theta = 0.00),
    list(id = "BASE_SMALLK", kind = "none", k = 6, tau2 = 0.05, theta = 0.30),
    list(id = "BASE_STD", kind = "none", k = 20, tau2 = 0.05, theta = 0.30),
    list(id = "HET_ZERO", kind = "none", k = 20, tau2 = 0.00, theta = 0.30),
    list(id = "HET_HIGH", kind = "none", k = 20, tau2 = 0.30, theta = 0.30),
    list(id = "HET_EXTREME", kind = "none", k = 25, tau2 = 0.60, theta = 0.30),

    # Outlier stress tests
    list(id = "OUTLIER_SINGLE", kind = "outlier", k = 20, tau2 = 0.08, theta = 0.30, out_n = 1, out_shift = 4.0),
    list(id = "OUTLIER_MULTI", kind = "outlier", k = 25, tau2 = 0.08, theta = 0.30, out_n = 3, out_shift = 3.0),

    # Publication bias
    list(id = "PB_STEP_MILD", kind = "step", k = 25, tau2 = 0.08, theta = 0.30, cutoff = 0.10, drop_prob = 0.50),
    list(id = "PB_STEP_MOD", kind = "step", k = 25, tau2 = 0.08, theta = 0.30, cutoff = 0.05, drop_prob = 0.70),
    list(id = "PB_STEP_SEV", kind = "step", k = 25, tau2 = 0.08, theta = 0.30, cutoff = 0.05, drop_prob = 0.90),
    list(id = "PB_ONE_SIDED", kind = "one_sided", k = 25, tau2 = 0.08, theta = 0.15, cutoff = 0.05, drop_prob = 0.85),
    list(id = "PB_CONT", kind = "continuous", k = 25, tau2 = 0.08, theta = 0.30, slope = 12),
    list(id = "PB_NULL_TYPE1", kind = "step", k = 25, tau2 = 0.08, theta = 0.00, cutoff = 0.05, drop_prob = 0.85),
    list(id = "PB_SMALL_K", kind = "step", k = 8, tau2 = 0.08, theta = 0.30, cutoff = 0.05, drop_prob = 0.80),
    list(id = "PB_HIGH_HET", kind = "step", k = 25, tau2 = 0.40, theta = 0.30, cutoff = 0.05, drop_prob = 0.80),
    list(id = "PB_CONT_NULL", kind = "continuous", k = 25, tau2 = 0.08, theta = 0.00, slope = 14)
  )
}

generate_dataset <- function(sc) {
  k <- sc$k
  vi <- rexp(k, rate = 14) + 0.01
  theta_i <- rnorm(k, mean = sc$theta, sd = sqrt(sc$tau2))
  yi <- rnorm(k, mean = theta_i, sd = sqrt(vi))

  z <- yi / sqrt(vi)
  p <- 2 * (1 - pnorm(abs(z)))

  keep <- rep(TRUE, k)
  if (sc$kind == "step") {
    low_sig <- p > sc$cutoff
    keep[low_sig] <- runif(sum(low_sig)) > sc$drop_prob
  } else if (sc$kind == "one_sided") {
    low_sig_neg <- (p > sc$cutoff) & (yi < 0)
    keep[low_sig_neg] <- runif(sum(low_sig_neg)) > sc$drop_prob
  } else if (sc$kind == "continuous") {
    pub_prob <- plogis(-sc$slope * (p - 0.05))
    keep <- runif(k) < pub_prob
  } else if (sc$kind == "outlier") {
    out_n <- min(sc$out_n, k)
    out_idx <- sample.int(k, size = out_n, replace = FALSE)
    yi[out_idx] <- yi[out_idx] + sc$out_shift * sqrt(vi[out_idx] + sc$tau2)
  }

  if (sum(keep) < 4) {
    keep <- rank(p, ties.method = "first") <= min(k, 4)
  }

  list(
    yi = yi[keep],
    vi = vi[keep],
    k_obs = sum(keep)
  )
}

is_method_applicable <- function(method, k_obs) {
  if (k_obs < 3) return(FALSE)
  if (method %in% c("SWA", "TAS") && k_obs < 10) return(FALSE)
  TRUE
}

run_method <- function(method, yi, vi, n_boot_swa, cache = NULL) {
  tryCatch({
    if (method == "REML") {
      fit <- metafor::rma(yi, vi, method = "REML")
      return(list(estimate = safe_num(coef(fit)), se = safe_num(fit$se), ci_lb = safe_num(fit$ci.lb), ci_ub = safe_num(fit$ci.ub), pvalue = safe_num(fit$pval)))
    }
    if (method == "HKSJ") {
      fit <- metafor::rma(yi, vi, method = "REML", test = "knha")
      return(list(estimate = safe_num(coef(fit)), se = safe_num(fit$se), ci_lb = safe_num(fit$ci.lb), ci_ub = safe_num(fit$ci.ub), pvalue = safe_num(fit$pval)))
    }
    if (method == "PETPEESE") return(petpeese_method(yi, vi))
    if (method == "TRIMFILL") return(trimfill_method(yi, vi))
    if (method == "SWA") return(swa_meta(yi, vi, n_boot = n_boot_swa))
    if (method == "TAS") return(tas_meta(yi, vi))
    if (method == "PBM") {
      swa_cached <- if (!is.null(cache) && !is.null(cache$SWA)) cache$SWA else NULL
      tas_cached <- if (!is.null(cache) && !is.null(cache$TAS)) cache$TAS else NULL
      return(pbm_meta(yi, vi, n_boot_swa = n_boot_swa, swa_result = swa_cached, tas_result = tas_cached))
    }
    stop(paste("Unknown method:", method))
  }, error = function(e) {
    list(estimate = NA_real_, se = NA_real_, ci_lb = NA_real_, ci_ub = NA_real_, pvalue = NA_real_, error = conditionMessage(e))
  })
}

rank_table <- function(summary_dt) {
  dt <- copy(summary_dt)
  dt[, coverage_gap := abs(coverage - 0.95)]
  dt[, type1_gap := abs(type1_error - 0.05)]

  scale01 <- function(x) {
    rng <- range(x, na.rm = TRUE)
    if (!all(is.finite(rng)) || diff(rng) <= 0) return(rep(0.5, length(x)))
    (x - rng[1]) / diff(rng)
  }

  dt[, score_abs_bias := scale01(abs_bias)]
  dt[, score_rmse := scale01(rmse)]
  dt[, score_coverage := scale01(coverage_gap)]
  dt[, score_width := scale01(ci_width)]
  # Convergence is assessed among applicable analyses only.
  # If a method is never applicable in a slice, don't double-penalize it here
  # (applicability is already penalized via score_app).
  dt[, score_conv := ifelse(is.na(convergence), 0, 1 - convergence)]
  dt[, score_app := 1 - applicability]
  dt[, score_type1 := scale01(type1_gap)]

  dt[, world_score :=
       0.30 * score_abs_bias +
       0.25 * score_rmse +
       0.20 * score_coverage +
       0.10 * score_width +
       0.08 * score_type1 +
       0.04 * score_conv +
       0.03 * score_app]

  dt[, rank := frank(world_score, ties.method = "min")]
  setorder(dt, rank, world_score)
  dt
}

main <- function() {
  args <- parse_args()
  set.seed(args$seed)

  file_arg <- grep("^--file=", commandArgs(), value = TRUE)
  script_path <- if (length(file_arg) > 0) sub("^--file=", "", file_arg[1]) else "analysis/simulation/PBM_World_Benchmark.R"
  script_dir <- normalizePath(dirname(script_path), winslash = "/")
  repo_root <- normalizePath(file.path(script_dir, "..", ".."), winslash = "/")

  source(file.path(repo_root, "R", "advanced_pooling.R"))
  source(file.path(repo_root, "R", "advanced_pooling_v4.R"))

  out_dir <- resolve_out_dir(repo_root, args$out_dir)
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

  scenarios <- scenario_grid()
  methods <- c("REML", "HKSJ", "PETPEESE", "TRIMFILL", "SWA", "TAS", "PBM")

  cat("PBM World Benchmark\n")
  cat("n_sim:", args$n_sim, "\n")
  cat("n_scenarios:", length(scenarios), "\n")
  cat("n_cores:", args$n_cores, "\n")
  cat("methods:", paste(methods, collapse = ", "), "\n\n")

  all <- vector("list", length(scenarios) * args$n_sim * length(methods))
  idx <- 1L

  for (s in seq_along(scenarios)) {
    sc <- scenarios[[s]]
    cat(sprintf("[%d/%d] %s\n", s, length(scenarios), sc$id))

    iter_runner <- function(i) {
      dat <- generate_dataset(sc)
      yi <- dat$yi
      vi <- dat$vi

      # Per-iteration cache: avoid recomputing SWA/TAS inside PBM.
      cache <- list()
      if (length(yi) >= args$min_obs_k && is_method_applicable("SWA", length(yi))) {
        cache$SWA <- run_method("SWA", yi, vi, args$n_boot_swa, cache = NULL)
      }
      if (length(yi) >= args$min_obs_k && is_method_applicable("TAS", length(yi))) {
        cache$TAS <- run_method("TAS", yi, vi, args$n_boot_swa, cache = NULL)
      }

      iter_rows <- vector("list", length(methods))
      ridx <- 1L
      for (m in methods) {
        applicable <- is_method_applicable(m, length(yi))
        if (length(yi) < args$min_obs_k || !applicable) {
          res <- list(estimate = NA_real_, se = NA_real_, ci_lb = NA_real_, ci_ub = NA_real_, pvalue = NA_real_)
        } else if (m %in% c("SWA", "TAS") && !is.null(cache[[m]])) {
          res <- cache[[m]]
        } else {
          res <- run_method(m, yi, vi, args$n_boot_swa, cache = cache)
        }

        iter_rows[[ridx]] <- data.table(
          scenario = sc$id,
          scenario_kind = sc$kind,
          method = m,
          iter = i,
          k_target = sc$k,
          k_obs = length(yi),
          true_theta = sc$theta,
          estimate = safe_num(res$estimate),
          se = safe_num(res$se),
          ci_lb = safe_num(res$ci_lb),
          ci_ub = safe_num(res$ci_ub),
          pvalue = safe_num(res$pvalue),
          applicable = as.integer(applicable && length(yi) >= args$min_obs_k),
          converged = as.integer(is.finite(safe_num(res$estimate)) && is.finite(safe_num(res$se)) && safe_num(res$se) > 0)
        )
        ridx <- ridx + 1L
      }
      rbindlist(iter_rows)
    }

    iter_results <- if (args$n_cores > 1L) {
      parallel::mclapply(seq_len(args$n_sim), iter_runner, mc.cores = args$n_cores, mc.set.seed = TRUE)
    } else {
      lapply(seq_len(args$n_sim), iter_runner)
    }

    for (ir in iter_results) {
      all[[idx]] <- ir
      idx <- idx + 1L
    }
  }

  raw <- rbindlist(all, use.names = TRUE, fill = TRUE)

  perf <- raw[, .(
    n = .N,
    applicable_n = sum(applicable, na.rm = TRUE),
    applicability = mean(applicable, na.rm = TRUE),
    convergence = ifelse(sum(applicable == 1, na.rm = TRUE) > 0,
                         mean(converged[applicable == 1], na.rm = TRUE),
                         NA_real_),
    bias = mean(estimate[converged == 1] - true_theta[converged == 1], na.rm = TRUE),
    abs_bias = mean(abs(estimate[converged == 1] - true_theta[converged == 1]), na.rm = TRUE),
    rmse = sqrt(mean((estimate[converged == 1] - true_theta[converged == 1])^2, na.rm = TRUE)),
    coverage = mean(ci_lb[converged == 1] <= true_theta[converged == 1] & ci_ub[converged == 1] >= true_theta[converged == 1], na.rm = TRUE),
    ci_width = mean(ci_ub[converged == 1] - ci_lb[converged == 1], na.rm = TRUE),
    type1_error = ifelse(unique(true_theta) == 0, mean(pvalue[converged == 1] < 0.05, na.rm = TRUE), NA_real_),
    power = ifelse(unique(true_theta) != 0, mean(pvalue[converged == 1] < 0.05, na.rm = TRUE), NA_real_)
  ), by = .(scenario, scenario_kind, method)]

  overall <- perf[, .(
    scenarios = .N,
    applicability = mean(applicability, na.rm = TRUE),
    convergence = mean(convergence, na.rm = TRUE),
    bias = mean(bias, na.rm = TRUE),
    abs_bias = mean(abs_bias, na.rm = TRUE),
    rmse = mean(rmse, na.rm = TRUE),
    coverage = mean(coverage, na.rm = TRUE),
    ci_width = mean(ci_width, na.rm = TRUE),
    type1_error = mean(type1_error, na.rm = TRUE),
    power = mean(power, na.rm = TRUE),
    type1_scenarios = sum(!is.na(type1_error)),
    power_scenarios = sum(!is.na(power))
  ), by = method]

  overall_pub <- perf[grepl("^PB_", scenario), .(
    scenarios = .N,
    applicability = mean(applicability, na.rm = TRUE),
    convergence = mean(convergence, na.rm = TRUE),
    bias = mean(bias, na.rm = TRUE),
    abs_bias = mean(abs_bias, na.rm = TRUE),
    rmse = mean(rmse, na.rm = TRUE),
    coverage = mean(coverage, na.rm = TRUE),
    ci_width = mean(ci_width, na.rm = TRUE),
    type1_error = mean(type1_error, na.rm = TRUE),
    power = mean(power, na.rm = TRUE),
    type1_scenarios = sum(!is.na(type1_error)),
    power_scenarios = sum(!is.na(power))
  ), by = method]

  rank_all <- rank_table(overall)
  rank_pub <- rank_table(overall_pub)

  stamp <- format(Sys.time(), "%Y%m%d_%H%M%S")
  fwrite(raw, file.path(out_dir, paste0("pbm_world_raw_", stamp, ".csv")))
  fwrite(perf, file.path(out_dir, paste0("pbm_world_scenario_metrics_", stamp, ".csv")))
  fwrite(rank_all, file.path(out_dir, paste0("pbm_world_rank_overall_", stamp, ".csv")))
  fwrite(rank_pub, file.path(out_dir, paste0("pbm_world_rank_pubbias_", stamp, ".csv")))

  report <- c(
    "# PBM World Benchmark",
    "",
    paste0("- Date: ", Sys.time()),
    paste0("- n_sim: ", args$n_sim),
    paste0("- seed: ", args$seed),
    paste0("- n_boot_swa: ", args$n_boot_swa),
    paste0("- scenarios: ", length(scenarios)),
    paste0("- n_cores: ", args$n_cores),
    paste0("- methods: ", paste(methods, collapse = ", ")),
    paste0("- min_obs_k: ", args$min_obs_k),
    "",
    "## Top 3 Overall"
  )

  top_all <- rank_all[1:min(3, .N)]
  for (i in seq_len(nrow(top_all))) {
    report <- c(report, sprintf(
      "%d. %s (score=%.4f, abs_bias=%.4f, rmse=%.4f, coverage=%.3f)",
      i, top_all$method[i], top_all$world_score[i], top_all$abs_bias[i], top_all$rmse[i], top_all$coverage[i]
    ))
  }

  report <- c(report, "", "## Top 3 Publication-Bias Scenarios")
  top_pub <- rank_pub[1:min(3, .N)]
  for (i in seq_len(nrow(top_pub))) {
    report <- c(report, sprintf(
      "%d. %s (score=%.4f, abs_bias=%.4f, rmse=%.4f, coverage=%.3f)",
      i, top_pub$method[i], top_pub$world_score[i], top_pub$abs_bias[i], top_pub$rmse[i], top_pub$coverage[i]
    ))
  }

  report_path <- file.path(out_dir, paste0("pbm_world_report_", stamp, ".md"))
  writeLines(report, con = report_path)

  cat("\nDone.\n")
  cat("Top overall method:", rank_all$method[1], "\n")
  cat("Top pub-bias method:", rank_pub$method[1], "\n")
  cat("Report:", report_path, "\n")
}

`%||%` <- function(a, b) if (!is.null(a)) a else b

main()
