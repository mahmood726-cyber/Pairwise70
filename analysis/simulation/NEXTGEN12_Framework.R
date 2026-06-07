#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(metafor)
  library(data.table)
})

# Lightweight experimental framework for NextGen-12 methods.
# This file is intentionally isolated from package exports until methods stabilize.

resolve_repo_root <- function() {
  args_full <- commandArgs(trailingOnly = FALSE)
  file_arg_idx <- grep("^--file=", args_full)
  script_path <- if (length(file_arg_idx) > 0) sub("^--file=", "", args_full[file_arg_idx[1]]) else ""
  script_dir <- if (nzchar(script_path)) normalizePath(dirname(script_path), winslash = "/", mustWork = FALSE) else normalizePath(getwd(), winslash = "/", mustWork = FALSE)
  candidate_roots <- unique(c(
    script_dir,
    normalizePath(file.path(script_dir, "..", ".."), winslash = "/", mustWork = FALSE),
    normalizePath(getwd(), winslash = "/", mustWork = FALSE)
  ))
  repo_root <- candidate_roots[which(vapply(
    candidate_roots,
    function(p) file.exists(file.path(p, "DESCRIPTION")) && dir.exists(file.path(p, "R")),
    logical(1)
  ))[1]]
  if (is.na(repo_root) || !nzchar(repo_root)) stop("Could not locate repository root")
  repo_root
}

safe_num <- function(x) {
  if (length(x) == 0 || is.null(x) || !is.finite(x[1])) return(NA_real_)
  as.numeric(x[1])
}

safe_ci <- function(est, se, k) {
  if (!is.finite(est) || !is.finite(se) || se <= 0) return(list(lb = NA_real_, ub = NA_real_))
  df <- max(1, k - 2)
  t_crit <- qt(0.975, df)
  list(lb = est - t_crit * se, ub = est + t_crit * se)
}

# Prototype 1: QSE (Quantile Shrinkage Ensemble)
qse_meta <- function(yi, vi) {
  k <- length(yi)
  reml <- tryCatch(metafor::rma(yi, vi, method = "REML"), error = function(e) NULL)
  hksj <- tryCatch(metafor::rma(yi, vi, method = "REML", test = "knha"), error = function(e) NULL)
  if (is.null(reml) || is.null(hksj)) return(list(method = "QSE", estimate = NA_real_, se = NA_real_))

  ests <- c(safe_num(coef(reml)), safe_num(coef(hksj)))
  ses <- c(safe_num(reml$se), safe_num(hksj$se))
  if (any(!is.finite(ests)) || any(!is.finite(ses)) || any(ses <= 0)) {
    return(list(method = "QSE", estimate = NA_real_, se = NA_real_))
  }

  med <- as.numeric(stats::quantile(ests, probs = 0.5, type = 8))
  dev <- pmax(abs(ests - med), 1e-6)
  w <- (1 / ses^2) * (1 / dev)
  w <- w / sum(w)

  est <- sum(w * ests)
  se <- sqrt(sum(w * ses^2) + sum(w * (ests - est)^2))
  ci <- safe_ci(est, se, k)
  list(method = "QSE", estimate = est, se = se, ci_lb = ci$lb, ci_ub = ci$ub)
}

# Prototype 2: LTH (Local-Tau Heterogeneity)
lth_meta <- function(yi, vi) {
  k <- length(yi)
  fit <- tryCatch(metafor::rma(yi, vi, method = "REML"), error = function(e) NULL)
  if (is.null(fit)) return(list(method = "LTH", estimate = NA_real_, se = NA_real_, tau2 = NA_real_))

  mu <- safe_num(coef(fit))
  res <- yi - mu
  local_tau2 <- stats::median(pmax(0, res^2 - vi), na.rm = TRUE)
  tau2_star <- 0.5 * safe_num(fit$tau2) + 0.5 * local_tau2

  w <- 1 / (vi + tau2_star)
  est <- sum(w * yi) / sum(w)
  se <- sqrt(1 / sum(w))
  ci <- safe_ci(est, se, k)

  list(method = "LTH", estimate = est, se = se, tau2 = tau2_star, ci_lb = ci$lb, ci_ub = ci$ub)
}

# Prototype 3: RMR (Robust Moderator Regression) with no moderators yet (intercept-only robust fallback)
rmr_meta <- function(yi, vi) {
  k <- length(yi)
  fit <- tryCatch(metafor::rma(yi, vi, method = "REML"), error = function(e) NULL)
  if (is.null(fit)) return(list(method = "RMR", estimate = NA_real_, se = NA_real_))

  mu <- safe_num(coef(fit))
  tau2 <- safe_num(fit$tau2)
  stud <- (yi - mu) / sqrt(vi + tau2 + 1e-8)
  huber <- ifelse(abs(stud) <= 1.5, 1, 1.5 / abs(stud))

  w <- (1 / (vi + tau2 + 1e-8)) * huber
  est <- sum(w * yi) / sum(w)
  se <- sqrt(1 / sum(w))
  ci <- safe_ci(est, se, k)

  list(method = "RMR", estimate = est, se = se, ci_lb = ci$lb, ci_ub = ci$ub)
}

simulate_dataset <- function(k = 20, theta = 0.3, tau2 = 0.08, outlier = FALSE) {
  vi <- rexp(k, rate = 14) + 0.01
  theta_i <- rnorm(k, theta, sqrt(tau2))
  yi <- rnorm(k, theta_i, sqrt(vi))
  if (outlier && k >= 1) {
    idx <- sample.int(k, 1)
    yi[idx] <- yi[idx] + 4 * sqrt(vi[idx] + tau2)
  }
  list(yi = yi, vi = vi)
}

evaluate_method <- function(res, theta_true) {
  data.table(
    method = res$method,
    estimate = safe_num(res$estimate),
    se = safe_num(res$se),
    bias = safe_num(res$estimate) - theta_true,
    abs_bias = abs(safe_num(res$estimate) - theta_true)
  )
}

main <- function() {
  set.seed(20260217)

  repo_root <- resolve_repo_root()
  source(file.path(repo_root, "R", "advanced_pooling_v4.R"))

  args <- commandArgs(trailingOnly = TRUE)
  n_sim <- if (length(args) >= 1) as.integer(args[1]) else 100L
  if (!is.finite(n_sim) || n_sim < 10) n_sim <- 100L

  scenarios <- list(
    list(id = "BASE", theta = 0.3, tau2 = 0.08, k = 20, outlier = FALSE),
    list(id = "OUTLIER", theta = 0.3, tau2 = 0.08, k = 20, outlier = TRUE),
    list(id = "HET_HIGH", theta = 0.3, tau2 = 0.35, k = 25, outlier = FALSE)
  )

  all <- data.table()
  for (sc in scenarios) {
    for (i in seq_len(n_sim)) {
      dat <- simulate_dataset(k = sc$k, theta = sc$theta, tau2 = sc$tau2, outlier = sc$outlier)

      reml <- tryCatch({
        fit <- metafor::rma(dat$yi, dat$vi, method = "REML")
        list(method = "REML", estimate = safe_num(coef(fit)), se = safe_num(fit$se))
      }, error = function(e) list(method = "REML", estimate = NA_real_, se = NA_real_))

      qse <- qse_meta(dat$yi, dat$vi)
      lth <- lth_meta(dat$yi, dat$vi)
      rmr <- rmr_meta(dat$yi, dat$vi)
      pbm <- tryCatch(pbm_meta(dat$yi, dat$vi, n_boot_swa = 39), error = function(e) list(method = "PBM", estimate = NA_real_, se = NA_real_))

      chunk <- rbindlist(list(
        evaluate_method(reml, sc$theta),
        evaluate_method(qse, sc$theta),
        evaluate_method(lth, sc$theta),
        evaluate_method(rmr, sc$theta),
        evaluate_method(list(method = "PBM", estimate = pbm$estimate, se = pbm$se), sc$theta)
      ), fill = TRUE)
      chunk[, `:=`(scenario = sc$id, iter = i)]
      all <- rbind(all, chunk, fill = TRUE)
    }
  }

  summary_dt <- all[, .(
    mean_est = mean(estimate, na.rm = TRUE),
    abs_bias = mean(abs_bias, na.rm = TRUE),
    rmse = sqrt(mean(bias^2, na.rm = TRUE))
  ), by = .(scenario, method)][order(scenario, abs_bias)]

  out_dir <- file.path(repo_root, "analysis", "results")
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  stamp <- format(Sys.time(), "%Y%m%d_%H%M%S")

  fwrite(all, file.path(out_dir, paste0("nextgen12_proto_raw_", stamp, ".csv")))
  fwrite(summary_dt, file.path(out_dir, paste0("nextgen12_proto_summary_", stamp, ".csv")))

  cat("NextGen12 prototype benchmark complete\n")
  print(summary_dt)
}

main()
