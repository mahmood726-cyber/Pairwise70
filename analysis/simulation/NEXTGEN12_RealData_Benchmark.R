#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(data.table)
  library(metafor)
})

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

qse_meta <- function(yi, vi) {
  k <- length(yi)
  reml <- tryCatch(metafor::rma(yi, vi, method = "REML"), error = function(e) NULL)
  hksj <- tryCatch(metafor::rma(yi, vi, method = "REML", test = "knha"), error = function(e) NULL)
  if (is.null(reml) || is.null(hksj)) return(list(method = "QSE", estimate = NA_real_, se = NA_real_))

  ests <- c(safe_num(coef(reml)), safe_num(coef(hksj)))
  ses <- c(safe_num(reml$se), safe_num(hksj$se))
  med <- as.numeric(stats::quantile(ests, probs = 0.5, type = 8))
  dev <- pmax(abs(ests - med), 1e-6)
  w <- (1 / pmax(ses, 1e-6)^2) * (1 / dev)
  w <- w / sum(w)

  est <- sum(w * ests)
  se <- sqrt(sum(w * ses^2) + sum(w * (ests - est)^2))
  ci <- safe_ci(est, se, k)
  list(method = "QSE", estimate = est, se = se, ci_lb = ci$lb, ci_ub = ci$ub)
}

lth_meta <- function(yi, vi) {
  k <- length(yi)
  fit <- tryCatch(metafor::rma(yi, vi, method = "REML"), error = function(e) NULL)
  if (is.null(fit)) return(list(method = "LTH", estimate = NA_real_, se = NA_real_))

  mu <- safe_num(coef(fit))
  res <- yi - mu
  local_tau2 <- stats::median(pmax(0, res^2 - vi), na.rm = TRUE)
  tau2_star <- 0.6 * safe_num(fit$tau2) + 0.4 * local_tau2

  w <- 1 / (vi + tau2_star + 1e-8)
  est <- sum(w * yi) / sum(w)
  se <- sqrt(1 / sum(w))
  ci <- safe_ci(est, se, k)
  list(method = "LTH", estimate = est, se = se, ci_lb = ci$lb, ci_ub = ci$ub, tau2 = tau2_star)
}

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

# FATIHA: Faithful Adaptive Trimmed Influence Harmonized Aggregation
fatiha_meta <- function(yi, vi, n_boot_swa = 19) {
  k <- length(yi)

  reml <- tryCatch({
    fit <- metafor::rma(yi, vi, method = "REML")
    list(method = "REML", estimate = safe_num(coef(fit)), se = safe_num(fit$se))
  }, error = function(e) list(method = "REML", estimate = NA_real_, se = NA_real_))

  hksj <- tryCatch({
    fit <- metafor::rma(yi, vi, method = "REML", test = "knha")
    list(method = "HKSJ", estimate = safe_num(coef(fit)), se = safe_num(fit$se))
  }, error = function(e) list(method = "HKSJ", estimate = NA_real_, se = NA_real_))

  qse <- qse_meta(yi, vi)
  lth <- lth_meta(yi, vi)
  rmr <- rmr_meta(yi, vi)
  pbm <- tryCatch(pbm_meta(yi, vi, n_boot_swa = n_boot_swa), error = function(e) list(estimate = NA_real_, se = NA_real_))

  tbl <- data.table(
    method = c("REML", "HKSJ", "QSE", "LTH", "RMR", "PBM"),
    estimate = c(reml$estimate, hksj$estimate, qse$estimate, lth$estimate, rmr$estimate, safe_num(pbm$estimate)),
    se = c(reml$se, hksj$se, qse$se, lth$se, rmr$se, safe_num(pbm$se)),
    robust = c(0.2, 0.3, 0.6, 0.7, 0.8, 0.9)
  )
  tbl <- tbl[is.finite(estimate) & is.finite(se) & se > 0]
  if (nrow(tbl) < 2) return(list(method = "FATIHA", estimate = NA_real_, se = NA_real_))

  med <- stats::median(tbl$estimate)
  influence_penalty <- 1 / (abs(tbl$estimate - med) + 1e-5)
  precision <- 1 / (tbl$se^2)
  w <- precision * (0.5 + tbl$robust) * influence_penalty
  w <- pmax(w, 1e-8)
  w <- w / sum(w)

  est <- sum(w * tbl$estimate)
  within_var <- sum(w * tbl$se^2)
  between_var <- sum(w * (tbl$estimate - est)^2)
  se <- sqrt(within_var + (1 + 1 / nrow(tbl)) * between_var)
  ci <- safe_ci(est, se, k)

  list(method = "FATIHA", estimate = est, se = se, ci_lb = ci$lb, ci_ub = ci$ub,
       component_methods = tbl$method, ensemble_weights = stats::setNames(w, tbl$method))
}

extract_effects <- function(d) {
  has_binary_cols <- all(c("Experimental.cases", "Experimental.N", "Control.cases", "Control.N") %in% names(d))
  has_cont_cols <- all(c("Experimental.mean", "Experimental.SD", "Experimental.N", "Control.mean", "Control.SD", "Control.N") %in% names(d))

  if (has_binary_cols) {
    es <- metafor::escalc(
      measure = "OR",
      ai = d$Experimental.cases,
      bi = d$Experimental.N - d$Experimental.cases,
      ci = d$Control.cases,
      di = d$Control.N - d$Control.cases
    )
    yi <- es$yi
    vi <- es$vi
    measure <- "OR"
  } else if (has_cont_cols) {
    es <- metafor::escalc(
      measure = "SMD",
      m1i = d$Experimental.mean,
      sd1i = d$Experimental.SD,
      n1i = d$Experimental.N,
      m2i = d$Control.mean,
      sd2i = d$Control.SD,
      n2i = d$Control.N
    )
    yi <- es$yi
    vi <- es$vi
    measure <- "SMD"
  } else {
    return(NULL)
  }

  keep <- is.finite(yi) & is.finite(vi) & vi > 0
  yi <- yi[keep]
  vi <- vi[keep]
  if (length(yi) < 3) return(NULL)

  list(yi = yi, vi = vi, measure = measure)
}

eval_row <- function(dataset, measure, k, method_name, est, se, baseline) {
  data.table(
    dataset = dataset,
    measure = measure,
    k = k,
    method = method_name,
    estimate = est,
    se = se,
    abs_shift_vs_reml = abs(est - baseline)
  )
}

main <- function() {
  repo_root <- resolve_repo_root()
  source(file.path(repo_root, "R", "advanced_pooling_v4.R"))

  if (!require("Pairwise70", quietly = TRUE)) {
    if (!requireNamespace("devtools", quietly = TRUE)) stop("Pairwise70 not installed and devtools unavailable")
    devtools::load_all(repo_root)
  }

  args <- commandArgs(trailingOnly = TRUE)
  max_datasets <- if (length(args) >= 1) as.integer(args[1]) else 70L
  if (!is.finite(max_datasets) || max_datasets < 10) max_datasets <- 70L
  timeout_sec <- if (length(args) >= 2) as.integer(args[2]) else 30L
  if (!is.finite(timeout_sec) || timeout_sec < 10) timeout_sec <- 30L
  max_k <- if (length(args) >= 3) as.integer(args[3]) else 120L
  if (!is.finite(max_k) || max_k < 3) max_k <- 120L
  n_boot_swa <- if (length(args) >= 4) as.integer(args[4]) else 19L
  if (!is.finite(n_boot_swa) || n_boot_swa < 9) n_boot_swa <- 19L

  data_list <- data(package = "Pairwise70")$results[, "Item"]
  if (max_datasets < length(data_list)) data_list <- data_list[seq_len(max_datasets)]

  out <- data.table()
  fail <- data.table(dataset = character(), reason = character())

  for (nm in data_list) {
    d <- tryCatch({
      data(list = nm, package = "Pairwise70", envir = environment())
      get(nm)
    }, error = function(e) NULL)

    if (is.null(d) || !is.data.frame(d)) {
      fail <- rbind(fail, data.table(dataset = nm, reason = "load_failed"))
      next
    }

    es <- tryCatch(extract_effects(d), error = function(e) NULL)
    if (is.null(es)) {
      fail <- rbind(fail, data.table(dataset = nm, reason = "effects_failed"))
      next
    }

    yi <- es$yi
    vi <- es$vi
    if (length(yi) > max_k) {
      keep <- order(vi)[seq_len(max_k)]
      yi <- yi[keep]
      vi <- vi[keep]
    }
    k <- length(yi)

    reml <- tryCatch({
      setTimeLimit(elapsed = timeout_sec, transient = TRUE)
      on.exit(setTimeLimit(cpu = Inf, elapsed = Inf, transient = FALSE), add = TRUE)
      fit <- metafor::rma(yi, vi, method = "REML")
      list(estimate = safe_num(coef(fit)), se = safe_num(fit$se))
    }, error = function(e) list(estimate = NA_real_, se = NA_real_))

    hksj <- tryCatch({
      fit <- metafor::rma(yi, vi, method = "REML", test = "knha")
      list(estimate = safe_num(coef(fit)), se = safe_num(fit$se))
    }, error = function(e) list(estimate = NA_real_, se = NA_real_))

    qse <- tryCatch(qse_meta(yi, vi), error = function(e) list(estimate = NA_real_, se = NA_real_))
    lth <- tryCatch(lth_meta(yi, vi), error = function(e) list(estimate = NA_real_, se = NA_real_))
    rmr <- tryCatch(rmr_meta(yi, vi), error = function(e) list(estimate = NA_real_, se = NA_real_))
    pbm <- tryCatch({
      setTimeLimit(elapsed = timeout_sec, transient = TRUE)
      on.exit(setTimeLimit(cpu = Inf, elapsed = Inf, transient = FALSE), add = TRUE)
      pbm_meta(yi, vi, n_boot_swa = n_boot_swa)
    }, error = function(e) list(estimate = NA_real_, se = NA_real_))
    fatiha <- tryCatch({
      setTimeLimit(elapsed = timeout_sec, transient = TRUE)
      on.exit(setTimeLimit(cpu = Inf, elapsed = Inf, transient = FALSE), add = TRUE)
      fatiha_meta(yi, vi, n_boot_swa = n_boot_swa)
    }, error = function(e) list(estimate = NA_real_, se = NA_real_))

    rows <- rbindlist(list(
      eval_row(nm, es$measure, k, "REML", reml$estimate, reml$se, reml$estimate),
      eval_row(nm, es$measure, k, "HKSJ", hksj$estimate, hksj$se, reml$estimate),
      eval_row(nm, es$measure, k, "QSE", qse$estimate, qse$se, reml$estimate),
      eval_row(nm, es$measure, k, "LTH", lth$estimate, lth$se, reml$estimate),
      eval_row(nm, es$measure, k, "RMR", rmr$estimate, rmr$se, reml$estimate),
      eval_row(nm, es$measure, k, "PBM", safe_num(pbm$estimate), safe_num(pbm$se), reml$estimate),
      eval_row(nm, es$measure, k, "FATIHA", fatiha$estimate, fatiha$se, reml$estimate)
    ), fill = TRUE)

    out <- rbind(out, rows, fill = TRUE)
  }

  summary_dt <- out[is.finite(estimate), .(
    n_datasets = uniqueN(dataset),
    median_k = median(k, na.rm = TRUE),
    mean_abs_shift_vs_reml = mean(abs_shift_vs_reml, na.rm = TRUE),
    median_se = median(se, na.rm = TRUE)
  ), by = method][order(mean_abs_shift_vs_reml)]

  stamp <- format(Sys.time(), "%Y%m%d_%H%M%S")
  out_dir <- file.path(repo_root, "analysis", "results")
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

  fwrite(out, file.path(out_dir, paste0("nextgen12_realdata_raw_", stamp, ".csv")))
  fwrite(summary_dt, file.path(out_dir, paste0("nextgen12_realdata_summary_", stamp, ".csv")))
  if (nrow(fail) > 0) fwrite(fail, file.path(out_dir, paste0("nextgen12_realdata_failures_", stamp, ".csv")))

  cat("NextGen12 real-data benchmark complete\n")
  print(summary_dt)
  cat(sprintf("Datasets attempted: %d\n", length(data_list)))
  cat(sprintf("Datasets evaluated: %d\n", uniqueN(out$dataset)))
  cat(sprintf("Runtime controls: timeout=%ds, max_k=%d, n_boot_swa=%d\n", timeout_sec, max_k, n_boot_swa))
}

main()
