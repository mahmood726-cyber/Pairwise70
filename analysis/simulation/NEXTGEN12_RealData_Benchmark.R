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

run_with_timeout <- function(expr, timeout_sec) {
  tryCatch({
    setTimeLimit(elapsed = timeout_sec, transient = TRUE)
    on.exit(setTimeLimit(cpu = Inf, elapsed = Inf, transient = FALSE), add = TRUE)
    eval.parent(substitute(expr))
  }, error = function(e) {
    list(estimate = NA_real_, se = NA_real_, error = conditionMessage(e))
  })
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

# CRT: Causal Residual Trimming (prototype)
crt_meta <- function(yi, vi) {
  k <- length(yi)
  fit <- tryCatch(metafor::rma(yi, vi, method = "REML"), error = function(e) NULL)
  if (is.null(fit)) return(list(method = "CRT", estimate = NA_real_, se = NA_real_))

  mu <- safe_num(coef(fit))
  tau2 <- safe_num(fit$tau2)
  stud <- abs((yi - mu) / sqrt(vi + tau2 + 1e-8))
  keep <- stud <= 2.5
  if (sum(keep) < 3) keep <- order(stud)[seq_len(min(3, k))]

  yi2 <- yi[keep]
  vi2 <- vi[keep]
  fit2 <- tryCatch(metafor::rma(yi2, vi2, method = "REML", test = "knha"), error = function(e) NULL)
  if (is.null(fit2)) return(list(method = "CRT", estimate = NA_real_, se = NA_real_))

  est <- safe_num(coef(fit2))
  se <- safe_num(fit2$se)
  ci <- safe_ci(est, se, length(yi2))
  list(method = "CRT", estimate = est, se = se, ci_lb = ci$lb, ci_ub = ci$ub, n_kept = sum(keep))
}

# AWH: Adaptive Winsorized Heterogeneity (prototype)
awh_meta <- function(yi, vi) {
  k <- length(yi)
  fit <- tryCatch(metafor::rma(yi, vi, method = "REML"), error = function(e) NULL)
  if (is.null(fit)) return(list(method = "AWH", estimate = NA_real_, se = NA_real_))

  mu <- safe_num(coef(fit))
  tau2 <- safe_num(fit$tau2)
  r <- (yi - mu) / sqrt(vi + tau2 + 1e-8)
  q_low <- as.numeric(stats::quantile(r, probs = 0.10, na.rm = TRUE))
  q_high <- as.numeric(stats::quantile(r, probs = 0.90, na.rm = TRUE))
  r_w <- pmin(pmax(r, q_low), q_high)
  yi_w <- mu + r_w * sqrt(vi + tau2 + 1e-8)

  w <- 1 / (vi + tau2 + 1e-8)
  est <- sum(w * yi_w) / sum(w)
  se <- sqrt(1 / sum(w))
  ci <- safe_ci(est, se, k)
  list(method = "AWH", estimate = est, se = se, ci_lb = ci$lb, ci_ub = ci$ub)
}

# MRSTACK: Stacked Meta-Regression (intercept-only stack prototype)
mrstack_meta <- function(yi, vi) {
  k <- length(yi)
  reml <- tryCatch(metafor::rma(yi, vi, method = "REML"), error = function(e) NULL)
  hksj <- tryCatch(metafor::rma(yi, vi, method = "REML", test = "knha"), error = function(e) NULL)
  pet <- tryCatch(metafor::rma(yi, vi, mods = ~ sqrt(vi), method = "REML", test = "knha"), error = function(e) NULL)
  peese <- tryCatch(metafor::rma(yi, vi, mods = ~ vi, method = "REML", test = "knha"), error = function(e) NULL)

  tbl <- data.table(
    method = c("REML", "HKSJ", "PET", "PEESE"),
    estimate = c(
      if (!is.null(reml)) safe_num(coef(reml)) else NA_real_,
      if (!is.null(hksj)) safe_num(coef(hksj)) else NA_real_,
      if (!is.null(pet)) safe_num(coef(pet)[1]) else NA_real_,
      if (!is.null(peese)) safe_num(coef(peese)[1]) else NA_real_
    ),
    se = c(
      if (!is.null(reml)) safe_num(reml$se) else NA_real_,
      if (!is.null(hksj)) safe_num(hksj$se) else NA_real_,
      if (!is.null(pet)) safe_num(pet$se[1]) else NA_real_,
      if (!is.null(peese)) safe_num(peese$se[1]) else NA_real_
    )
  )
  tbl <- tbl[is.finite(estimate) & is.finite(se) & se > 0]
  if (nrow(tbl) < 2) return(list(method = "MRSTACK", estimate = NA_real_, se = NA_real_))

  # Softmax on negative SE favors precise components while retaining diversity.
  logits <- -scale(tbl$se)
  w <- exp(logits)
  w <- w / sum(w)
  est <- sum(w * tbl$estimate)
  se <- sqrt(sum(w * tbl$se^2) + sum(w * (tbl$estimate - est)^2))
  ci <- safe_ci(est, se, k)
  list(method = "MRSTACK", estimate = est, se = se, ci_lb = ci$lb, ci_ub = ci$ub)
}

# SAFE: Selective Adaptive Fusion Estimator
safe_meta <- function(yi, vi) {
  k <- length(yi)
  reml <- tryCatch(metafor::rma(yi, vi, method = "REML"), error = function(e) NULL)
  hksj <- tryCatch(metafor::rma(yi, vi, method = "REML", test = "knha"), error = function(e) NULL)
  lth <- lth_meta(yi, vi)
  rmr <- rmr_meta(yi, vi)
  if (is.null(reml) || is.null(hksj)) return(list(method = "SAFE", estimate = NA_real_, se = NA_real_))

  tbl <- data.table(
    method = c("REML", "HKSJ", "LTH", "RMR"),
    estimate = c(safe_num(coef(reml)), safe_num(coef(hksj)), lth$estimate, rmr$estimate),
    se = c(safe_num(reml$se), safe_num(hksj$se), lth$se, rmr$se)
  )
  tbl <- tbl[is.finite(estimate) & is.finite(se) & se > 0]
  if (nrow(tbl) < 2) return(list(method = "SAFE", estimate = NA_real_, se = NA_real_))

  center <- stats::median(tbl$estimate)
  disp <- abs(tbl$estimate - center)
  w <- (1 / tbl$se^2) * exp(-disp / (stats::mad(tbl$estimate, constant = 1) + 1e-6))
  w <- pmax(w, 1e-8)
  w <- w / sum(w)

  est <- sum(w * tbl$estimate)
  se <- sqrt(sum(w * tbl$se^2) + sum(w * (tbl$estimate - est)^2))
  ci <- safe_ci(est, se, k)
  list(method = "SAFE", estimate = est, se = se, ci_lb = ci$lb, ci_ub = ci$ub)
}

# CPC: Cross-Phenotype Consensus Pooling
cpc_meta <- function(yi, vi) {
  k <- length(yi)
  ord <- order(yi)
  g <- 3L
  groups <- split(ord, cut(seq_along(ord), breaks = g, labels = FALSE))
  ests <- numeric()
  ses <- numeric()
  for (idx in groups) {
    if (length(idx) < 3) next
    fit <- tryCatch(metafor::rma(yi[idx], vi[idx], method = "REML"), error = function(e) NULL)
    if (is.null(fit)) next
    ests <- c(ests, safe_num(coef(fit)))
    ses <- c(ses, safe_num(fit$se))
  }
  if (length(ests) < 2) return(list(method = "CPC", estimate = NA_real_, se = NA_real_))
  w <- 1 / pmax(ses, 1e-6)^2
  w <- w / sum(w)
  est <- sum(w * ests)
  se <- sqrt(sum(w * ses^2) + sum(w * (ests - est)^2))
  ci <- safe_ci(est, se, k)
  list(method = "CPC", estimate = est, se = se, ci_lb = ci$lb, ci_ub = ci$ub)
}

# DTM: Distributional Tau Mixture
dtm_meta <- function(yi, vi) {
  k <- length(yi)
  fit <- tryCatch(metafor::rma(yi, vi, method = "REML"), error = function(e) NULL)
  if (is.null(fit)) return(list(method = "DTM", estimate = NA_real_, se = NA_real_))
  tau_base <- pmax(0, safe_num(fit$tau2))
  tau_grid <- c(0.5, 1.0, 1.5) * sqrt(tau_base + 1e-8)
  tau2_grid <- tau_grid^2

  ests <- numeric()
  ses <- numeric()
  for (t2 in tau2_grid) {
    w <- 1 / (vi + t2 + 1e-8)
    ests <- c(ests, sum(w * yi) / sum(w))
    ses <- c(ses, sqrt(1 / sum(w)))
  }
  mix_w <- c(0.25, 0.5, 0.25)
  est <- sum(mix_w * ests)
  se <- sqrt(sum(mix_w * ses^2) + sum(mix_w * (ests - est)^2))
  ci <- safe_ci(est, se, k)
  list(method = "DTM", estimate = est, se = se, ci_lb = ci$lb, ci_ub = ci$ub)
}

# BSC: Bayesian Stability Calibration (empirical-Bayes style shrinkage)
bsc_meta <- function(yi, vi) {
  k <- length(yi)
  fit <- tryCatch(metafor::rma(yi, vi, method = "REML"), error = function(e) NULL)
  if (is.null(fit)) return(list(method = "BSC", estimate = NA_real_, se = NA_real_))
  mu <- safe_num(coef(fit))
  tau2 <- pmax(0, safe_num(fit$tau2))
  shrink <- tau2 / (tau2 + stats::median(vi) + 1e-8)
  adj_yi <- shrink * yi + (1 - shrink) * mu
  w <- 1 / (vi + tau2 + 1e-8)
  est <- sum(w * adj_yi) / sum(w)
  se <- sqrt(1 / sum(w))
  ci <- safe_ci(est, se, k)
  list(method = "BSC", estimate = est, se = se, ci_lb = ci$lb, ci_ub = ci$ub, shrink = shrink)
}

# HGAM: Heterogeneity GAM-style meta-regression (spline proxy)
hgam_meta <- function(yi, vi) {
  k <- length(yi)
  if (k < 6) return(list(method = "HGAM", estimate = NA_real_, se = NA_real_))
  q <- rank(vi) / (k + 1)
  df_spline <- min(4, max(3, floor(k / 8)))
  fit <- tryCatch(
    suppressWarnings(
      metafor::rma(yi, vi, mods = ~ splines::bs(q, df = df_spline), method = "REML", test = "knha")
    ),
    error = function(e) NULL
  )
  if (is.null(fit)) return(list(method = "HGAM", estimate = NA_real_, se = NA_real_))
  est <- safe_num(coef(fit)[1])
  se <- safe_num(fit$se[1])
  ci <- safe_ci(est, se, k)
  list(method = "HGAM", estimate = est, se = se, ci_lb = ci$lb, ci_ub = ci$ub)
}

# MTLE: Multi-Task Learning Effects (two-task stack over precision strata)
mtle_meta <- function(yi, vi) {
  k <- length(yi)
  ord <- order(vi)
  cut_idx <- floor(k / 2)
  idx_hi <- ord[seq_len(max(1, cut_idx))]
  idx_lo <- ord[seq(max(1, cut_idx + 1), k)]
  if (length(idx_hi) < 3 || length(idx_lo) < 3) return(list(method = "MTLE", estimate = NA_real_, se = NA_real_))

  fit_hi <- tryCatch(metafor::rma(yi[idx_hi], vi[idx_hi], method = "REML"), error = function(e) NULL)
  fit_lo <- tryCatch(metafor::rma(yi[idx_lo], vi[idx_lo], method = "REML"), error = function(e) NULL)
  if (is.null(fit_hi) || is.null(fit_lo)) return(list(method = "MTLE", estimate = NA_real_, se = NA_real_))

  ests <- c(safe_num(coef(fit_hi)), safe_num(coef(fit_lo)))
  ses <- c(safe_num(fit_hi$se), safe_num(fit_lo$se))
  w <- 1 / pmax(ses, 1e-6)^2
  w <- w / sum(w)
  est <- sum(w * ests)
  se <- sqrt(sum(w * ses^2) + sum(w * (ests - est)^2))
  ci <- safe_ci(est, se, k)
  list(method = "MTLE", estimate = est, se = se, ci_lb = ci$lb, ci_ub = ci$ub)
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
  crt <- crt_meta(yi, vi)
  awh <- awh_meta(yi, vi)
  mrstack <- mrstack_meta(yi, vi)
  safe_res <- safe_meta(yi, vi)
  cpc <- cpc_meta(yi, vi)
  dtm <- dtm_meta(yi, vi)
  bsc <- bsc_meta(yi, vi)
  hgam <- hgam_meta(yi, vi)
  mtle <- mtle_meta(yi, vi)
  pbm <- tryCatch(pbm_meta(yi, vi, n_boot_swa = n_boot_swa), error = function(e) list(estimate = NA_real_, se = NA_real_))

  tbl <- data.table(
    method = c("REML", "HKSJ", "QSE", "LTH", "RMR", "CRT", "AWH", "MRSTACK", "SAFE", "CPC", "DTM", "BSC", "HGAM", "MTLE", "PBM"),
    estimate = c(
      reml$estimate, hksj$estimate, qse$estimate, lth$estimate, rmr$estimate,
      crt$estimate, awh$estimate, mrstack$estimate, safe_res$estimate, cpc$estimate,
      dtm$estimate, bsc$estimate, hgam$estimate, mtle$estimate, safe_num(pbm$estimate)
    ),
    se = c(
      reml$se, hksj$se, qse$se, lth$se, rmr$se,
      crt$se, awh$se, mrstack$se, safe_res$se, cpc$se,
      dtm$se, bsc$se, hgam$se, mtle$se, safe_num(pbm$se)
    ),
    robust = c(0.2, 0.3, 0.6, 0.7, 0.8, 0.85, 0.75, 0.65, 0.72, 0.70, 0.74, 0.78, 0.68, 0.69, 0.9)
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
  n_rank_boot <- if (length(args) >= 5) as.integer(args[5]) else 200L
  if (!is.finite(n_rank_boot) || n_rank_boot < 50) n_rank_boot <- 200L

  data_list <- data(package = "Pairwise70")$results[, "Item"]
  if (max_datasets < length(data_list)) data_list <- data_list[seq_len(max_datasets)]

  out <- data.table()
  fail <- data.table(dataset = character(), reason = character())
  method_fail <- data.table(dataset = character(), method = character(), reason = character())

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

    reml <- run_with_timeout({
      fit <- metafor::rma(yi, vi, method = "REML")
      list(estimate = safe_num(coef(fit)), se = safe_num(fit$se))
    }, timeout_sec = timeout_sec)

    hksj <- run_with_timeout({
      fit <- metafor::rma(yi, vi, method = "REML", test = "knha")
      list(estimate = safe_num(coef(fit)), se = safe_num(fit$se))
    }, timeout_sec = timeout_sec)

    qse <- run_with_timeout(qse_meta(yi, vi), timeout_sec = timeout_sec)
    lth <- run_with_timeout(lth_meta(yi, vi), timeout_sec = timeout_sec)
    rmr <- run_with_timeout(rmr_meta(yi, vi), timeout_sec = timeout_sec)
    crt <- run_with_timeout(crt_meta(yi, vi), timeout_sec = timeout_sec)
    awh <- run_with_timeout(awh_meta(yi, vi), timeout_sec = timeout_sec)
    mrstack <- run_with_timeout(mrstack_meta(yi, vi), timeout_sec = timeout_sec)
    safe_res <- run_with_timeout(safe_meta(yi, vi), timeout_sec = timeout_sec)
    cpc <- run_with_timeout(cpc_meta(yi, vi), timeout_sec = timeout_sec)
    dtm <- run_with_timeout(dtm_meta(yi, vi), timeout_sec = timeout_sec)
    bsc <- run_with_timeout(bsc_meta(yi, vi), timeout_sec = timeout_sec)
    hgam <- run_with_timeout(hgam_meta(yi, vi), timeout_sec = timeout_sec)
    mtle <- run_with_timeout(mtle_meta(yi, vi), timeout_sec = timeout_sec)
    pbm <- run_with_timeout({
      pbm_meta(yi, vi, n_boot_swa = n_boot_swa)
    }, timeout_sec = timeout_sec)
    fatiha <- run_with_timeout({
      fatiha_meta(yi, vi, n_boot_swa = n_boot_swa)
    }, timeout_sec = timeout_sec)

    method_objects <- list(
      REML = reml, HKSJ = hksj, QSE = qse, LTH = lth, RMR = rmr, CRT = crt,
      AWH = awh, MRSTACK = mrstack, SAFE = safe_res, CPC = cpc, DTM = dtm,
      BSC = bsc, HGAM = hgam, MTLE = mtle, PBM = pbm, FATIHA = fatiha
    )
    for (mname in names(method_objects)) {
      obj <- method_objects[[mname]]
      if (!is.finite(safe_num(obj$estimate))) {
        method_fail <- rbind(method_fail, data.table(
          dataset = nm,
          method = mname,
          reason = if ("error" %in% names(obj) && nzchar(obj$error)) obj$error else "non_finite_estimate"
        ))
      }
    }

    rows <- rbindlist(list(
      eval_row(nm, es$measure, k, "REML", reml$estimate, reml$se, reml$estimate),
      eval_row(nm, es$measure, k, "HKSJ", hksj$estimate, hksj$se, reml$estimate),
      eval_row(nm, es$measure, k, "QSE", qse$estimate, qse$se, reml$estimate),
      eval_row(nm, es$measure, k, "LTH", lth$estimate, lth$se, reml$estimate),
      eval_row(nm, es$measure, k, "RMR", rmr$estimate, rmr$se, reml$estimate),
      eval_row(nm, es$measure, k, "CRT", crt$estimate, crt$se, reml$estimate),
      eval_row(nm, es$measure, k, "AWH", awh$estimate, awh$se, reml$estimate),
      eval_row(nm, es$measure, k, "MRSTACK", mrstack$estimate, mrstack$se, reml$estimate),
      eval_row(nm, es$measure, k, "SAFE", safe_res$estimate, safe_res$se, reml$estimate),
      eval_row(nm, es$measure, k, "CPC", cpc$estimate, cpc$se, reml$estimate),
      eval_row(nm, es$measure, k, "DTM", dtm$estimate, dtm$se, reml$estimate),
      eval_row(nm, es$measure, k, "BSC", bsc$estimate, bsc$se, reml$estimate),
      eval_row(nm, es$measure, k, "HGAM", hgam$estimate, hgam$se, reml$estimate),
      eval_row(nm, es$measure, k, "MTLE", mtle$estimate, mtle$se, reml$estimate),
      eval_row(nm, es$measure, k, "PBM", safe_num(pbm$estimate), safe_num(pbm$se), reml$estimate),
      eval_row(nm, es$measure, k, "FATIHA", fatiha$estimate, fatiha$se, reml$estimate)
    ), fill = TRUE)

    out <- rbind(out, rows, fill = TRUE)
  }

  n_total <- uniqueN(out$dataset)
  reml_baseline <- out[method == "REML", .(dataset, reml_est = estimate)]
  consensus_dt <- out[is.finite(estimate), .(consensus_est = median(estimate, na.rm = TRUE)), by = dataset]
  out_eval <- merge(out, reml_baseline, by = "dataset", all.x = TRUE, sort = FALSE)
  out_eval <- merge(out_eval, consensus_dt, by = "dataset", all.x = TRUE, sort = FALSE)
  out_eval[, abs_shift_vs_consensus := abs(estimate - consensus_est)]

  summary_dt <- out_eval[, .(
    n_datasets = uniqueN(dataset[is.finite(estimate)]),
    convergence = mean(is.finite(estimate)),
    median_k = median(k, na.rm = TRUE),
    mean_abs_shift_vs_reml = mean(abs_shift_vs_reml, na.rm = TRUE),
    mean_abs_shift_vs_consensus = mean(abs_shift_vs_consensus, na.rm = TRUE),
    median_se = median(se[is.finite(se)], na.rm = TRUE),
    sign_flip_rate_vs_reml = mean(sign(estimate) != sign(reml_est), na.rm = TRUE)
  ), by = method]

  # Rank uncertainty via bootstrap over datasets.
  base_metrics <- out_eval[, .(
    mean_abs_shift_vs_reml = if (any(is.finite(abs_shift_vs_reml))) {
      mean(abs_shift_vs_reml[is.finite(abs_shift_vs_reml)], na.rm = TRUE)
    } else {
      NA_real_
    },
    mean_abs_shift_vs_consensus = if (any(is.finite(abs_shift_vs_consensus))) {
      mean(abs_shift_vs_consensus[is.finite(abs_shift_vs_consensus)], na.rm = TRUE)
    } else {
      NA_real_
    },
    median_se = if (any(is.finite(se))) {
      median(se[is.finite(se)], na.rm = TRUE)
    } else {
      NA_real_
    },
    sign_flip_rate_vs_reml = {
      flip_mask <- is.finite(estimate) & is.finite(reml_est)
      if (any(flip_mask)) mean(sign(estimate[flip_mask]) != sign(reml_est[flip_mask]), na.rm = TRUE) else NA_real_
    },
    convergence = mean(is.finite(estimate))
  ), by = .(dataset, method)]
  all_methods <- unique(summary_dt$method)
  all_datasets <- unique(base_metrics$dataset)
  rank_boot <- data.table()
  set.seed(20260217)
  for (b in seq_len(n_rank_boot)) {
    ds <- sample(all_datasets, size = length(all_datasets), replace = TRUE)
    # Preserve multiplicity in bootstrap resampling (set-membership would understate uncertainty).
    sampled_dt <- data.table(dataset = ds, boot_rep = seq_along(ds))
    boot <- merge(sampled_dt, base_metrics, by = "dataset", all.x = TRUE, allow.cartesian = TRUE, sort = FALSE)
    boot_s <- boot[, .(
      mean_abs_shift_vs_reml = mean(mean_abs_shift_vs_reml, na.rm = TRUE),
      mean_abs_shift_vs_consensus = mean(mean_abs_shift_vs_consensus, na.rm = TRUE),
      median_se = median(median_se, na.rm = TRUE),
      sign_flip_rate_vs_reml = mean(sign_flip_rate_vs_reml, na.rm = TRUE),
      convergence = mean(convergence, na.rm = TRUE)
    ), by = method]
    # Ensure method completeness in bootstrap sample.
    boot_s <- merge(data.table(method = all_methods), boot_s, by = "method", all.x = TRUE, sort = FALSE)
    fill_col <- function(x, default, worst = c("high", "low")) {
      worst <- match.arg(worst)
      if (!any(is.finite(x))) return(rep(default, length(x)))
      worst_val <- if (worst == "high") {
        max(x[is.finite(x)], na.rm = TRUE)
      } else {
        min(x[is.finite(x)], na.rm = TRUE)
      }
      x[!is.finite(x)] <- worst_val
      x[is.na(x)] <- worst_val
      x
    }
    boot_s[, mean_abs_shift_vs_reml := fill_col(mean_abs_shift_vs_reml, 1e3, worst = "high")]
    boot_s[, mean_abs_shift_vs_consensus := fill_col(mean_abs_shift_vs_consensus, 1e3, worst = "high")]
    boot_s[, median_se := fill_col(median_se, 1e3, worst = "high")]
    boot_s[, sign_flip_rate_vs_reml := fill_col(sign_flip_rate_vs_reml, 1.0, worst = "high")]
    boot_s[, convergence := fill_col(convergence, 0.0, worst = "low")]
    scale01b <- function(x) {
      rx <- range(x, na.rm = TRUE)
      if (!is.finite(rx[1]) || !is.finite(rx[2]) || rx[1] == rx[2]) return(rep(0, length(x)))
      (x - rx[1]) / (rx[2] - rx[1])
    }
    boot_s[, score_shift := scale01b(mean_abs_shift_vs_reml)]
    boot_s[, score_consensus := scale01b(mean_abs_shift_vs_consensus)]
    boot_s[, score_se := scale01b(median_se)]
    boot_s[, score_flip := scale01b(sign_flip_rate_vs_reml)]
    boot_s[, score_convergence := scale01b(1 - convergence)]
    boot_s[, world_score := 0.25 * score_shift + 0.25 * score_consensus + 0.20 * score_se + 0.15 * score_flip + 0.15 * score_convergence]
    setorder(boot_s, world_score)
    boot_s[, rank := seq_len(.N)]
    rank_boot <- rbind(rank_boot, boot_s[, .(method, b, rank)], fill = TRUE)
  }
  rank_unc <- rank_boot[, .(
    rank_mean = mean(rank, na.rm = TRUE),
    rank_sd = sd(rank, na.rm = TRUE),
    rank_p10 = as.numeric(stats::quantile(rank, 0.10, na.rm = TRUE)),
    rank_p90 = as.numeric(stats::quantile(rank, 0.90, na.rm = TRUE))
  ), by = method]
  summary_dt <- merge(summary_dt, rank_unc, by = "method", all.x = TRUE, sort = FALSE)

  # Composite score: lower is better
  fill_summary_col <- function(x, default, worst = c("high", "low")) {
    worst <- match.arg(worst)
    if (!any(is.finite(x))) return(rep(default, length(x)))
    worst_val <- if (worst == "high") {
      max(x[is.finite(x)], na.rm = TRUE)
    } else {
      min(x[is.finite(x)], na.rm = TRUE)
    }
    x[!is.finite(x)] <- worst_val
    x[is.na(x)] <- worst_val
    x
  }
  summary_dt[, mean_abs_shift_vs_reml := fill_summary_col(mean_abs_shift_vs_reml, 1e3, worst = "high")]
  summary_dt[, mean_abs_shift_vs_consensus := fill_summary_col(mean_abs_shift_vs_consensus, 1e3, worst = "high")]
  summary_dt[, median_se := fill_summary_col(median_se, 1e3, worst = "high")]
  summary_dt[, sign_flip_rate_vs_reml := fill_summary_col(sign_flip_rate_vs_reml, 1.0, worst = "high")]
  summary_dt[, convergence := fill_summary_col(convergence, 0.0, worst = "low")]
  summary_dt[, rank_sd := fill_summary_col(rank_sd, 1e3, worst = "high")]
  scale01 <- function(x) {
    rx <- range(x, na.rm = TRUE)
    if (!is.finite(rx[1]) || !is.finite(rx[2]) || rx[1] == rx[2]) return(rep(0, length(x)))
    (x - rx[1]) / (rx[2] - rx[1])
  }
  summary_dt[, score_shift := scale01(mean_abs_shift_vs_reml)]
  summary_dt[, score_consensus := scale01(mean_abs_shift_vs_consensus)]
  summary_dt[, score_se := scale01(median_se)]
  summary_dt[, score_flip := scale01(sign_flip_rate_vs_reml)]
  summary_dt[, score_convergence := scale01(1 - convergence)]
  summary_dt[, score_rank_uncertainty := scale01(rank_sd)]
  summary_dt[, world_score := 0.22 * score_shift + 0.22 * score_consensus + 0.18 * score_se + 0.13 * score_flip + 0.13 * score_convergence + 0.12 * score_rank_uncertainty]
  setorder(summary_dt, world_score)
  summary_dt[, rank := seq_len(.N)]

  stamp <- format(Sys.time(), "%Y%m%d_%H%M%S")
  out_dir <- file.path(repo_root, "analysis", "results")
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

  fwrite(out, file.path(out_dir, paste0("nextgen12_realdata_raw_", stamp, ".csv")))
  fwrite(summary_dt, file.path(out_dir, paste0("nextgen12_realdata_summary_", stamp, ".csv")))
  if (nrow(fail) > 0) fwrite(fail, file.path(out_dir, paste0("nextgen12_realdata_failures_", stamp, ".csv")))
  if (nrow(method_fail) > 0) fwrite(method_fail, file.path(out_dir, paste0("nextgen12_realdata_method_failures_", stamp, ".csv")))

  cat("NextGen12 real-data benchmark complete\n")
  print(summary_dt[, .(rank, method, n_datasets, convergence, mean_abs_shift_vs_reml, mean_abs_shift_vs_consensus, median_se, sign_flip_rate_vs_reml, rank_sd, rank_p10, rank_p90, world_score)])
  cat(sprintf("Datasets attempted: %d\n", length(data_list)))
  cat(sprintf("Datasets evaluated: %d\n", uniqueN(out$dataset)))
  cat(sprintf("Datasets in result matrix: %d\n", n_total))
  cat(sprintf("Runtime controls: timeout=%ds, max_k=%d, n_boot_swa=%d, n_rank_boot=%d\n", timeout_sec, max_k, n_boot_swa, n_rank_boot))
}

main()
