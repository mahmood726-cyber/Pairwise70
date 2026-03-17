#' Grey Relational Meta-Analysis (GRMA)
#'
#' Robust pooling estimator using grey-relational similarity in a two-feature
#' space (effect size and log-precision) with an optional redescending Tukey
#' bisquare effect guard and bootstrap inference (percentile + full BCa).
#'
#' @param yi Numeric vector of effect sizes
#' @param vi Numeric vector of sampling variances (must be > 0)
#' @param zeta Grey resolution coefficient in (0,1]; larger values reduce contrast.
#'   Default 0.5.
#' @param norm_method Normalization method. Currently only "robust_minmax" is
#'   implemented (fitted robust scaling to [0,1]).
#' @param anchor_mode How to compute the effect anchor: "median" (default) or
#'   "trimmed_mean".
#' @param trim Trim fraction for anchor_mode="trimmed_mean". Default 0.1.
#' @param prec_cap Upper cap on precision (1/vi) before log transform. Default 1e6.
#' @param effect_guard Logical; apply Tukey bisquare guard? Default TRUE.
#' @param tukey_c Tukey bisquare tuning constant. Default 4.685.
#' @param guard_power Exponent on guard term. Default 1.
#' @param n_boot Number of bootstrap replicates. Default 999.
#' @param bca Logical; compute full BCa interval with jackknife acceleration?
#'   Default TRUE. If FALSE, reports percentile interval only.
#' @param seed Optional seed for bootstrap reproducibility.
#' @return A list with components:
#'   \describe{
#'     \item{estimate}{GRMA pooled estimate}
#'     \item{se}{Bootstrap standard error}
#'     \item{ci_lb}{Lower bound of percentile CI}
#'     \item{ci_ub}{Upper bound of percentile CI}
#'     \item{ci_lb_bca}{Lower bound of BCa CI (NA if bca=FALSE)}
#'     \item{ci_ub_bca}{Upper bound of BCa CI (NA if bca=FALSE)}
#'     \item{pvalue}{Two-sided p-value from bootstrap SE}
#'     \item{tau2}{NA_real_ (GRMA does not estimate tau-squared)}
#'     \item{method}{"GRMA" or "GRMA_noguard"}
#'     \item{k}{Number of studies}
#'     \item{w_max}{Maximum normalized weight}
#'     \item{n_eff}{Effective number of studies (1/sum(w^2))}
#'     \item{anchor_y}{Effect anchor value}
#'     \item{anchor_p}{Precision anchor value}
#'     \item{weights}{Normalized weight vector}
#'     \item{guard_values}{Guard values h_i (NULL if effect_guard=FALSE)}
#'   }
#' @export
grma_meta <- function(yi, vi,
                      zeta = 0.5,
                      norm_method = "robust_minmax",
                      anchor_mode = "median",
                      trim = 0.1,
                      prec_cap = 1e6,
                      effect_guard = TRUE,
                      tukey_c = 4.685,
                      guard_power = 1,
                      n_boot = 999,
                      bca = TRUE,
                      seed = NULL) {

  k <- length(yi)

  # --- Minimum k check: fall back to HKSJ if k < 3 ---
  if (k < 3) {
    warning("GRMA requires k >= 3. Falling back to HKSJ.")
    fit <- metafor::rma(yi, vi, method = "REML", test = "knha")
    return(list(
      estimate = as.numeric(coef(fit)),
      se = fit$se,
      ci_lb = fit$ci.lb,
      ci_ub = fit$ci.ub,
      ci_lb_bca = NA_real_,
      ci_ub_bca = NA_real_,
      pvalue = fit$pval,
      tau2 = fit$tau2,
      method = "HKSJ_fallback",
      k = k,
      w_max = NA_real_,
      n_eff = NA_real_,
      anchor_y = NA_real_,
      anchor_p = NA_real_,
      weights = NULL,
      guard_values = NULL,
      note = "k < 3, used HKSJ instead of GRMA"
    ))
  }

  # --- Core GRMA computation (extracted for bootstrap reuse) ---
  grma_core <- function(y, v) {
    n <- length(y)

    # Step 1: Precision cap + log-precision
    prec <- pmin(1.0 / v, prec_cap)
    log_prec <- log(prec + 1.0)

    # Step 2: Feature matrix (n x 2)
    feat_effect <- y
    feat_prec <- log_prec

    # Step 3: Robust min-max normalization (fitted on data)
    robust_minmax <- function(x) {
      q1 <- quantile(x, 0.05, na.rm = TRUE, names = FALSE)
      q9 <- quantile(x, 0.95, na.rm = TRUE, names = FALSE)
      rng <- q9 - q1
      if (rng < 1e-12) rng <- 1.0
      list(q_lo = q1, q_hi = q9, rng = rng)
    }

    fit_eff <- robust_minmax(feat_effect)
    fit_pre <- robust_minmax(feat_prec)

    norm_val <- function(x, fit) {
      pmin(pmax((x - fit$q_lo) / fit$rng, 0.0), 1.0)
    }

    x_eff <- norm_val(feat_effect, fit_eff)
    x_pre <- norm_val(feat_prec, fit_pre)

    # Step 4: Anchor
    if (anchor_mode == "median") {
      a_y_raw <- median(y)
    } else if (anchor_mode == "trimmed_mean") {
      a_y_raw <- mean(y, trim = trim)
    } else {
      a_y_raw <- median(y)
    }
    a_p_raw <- max(prec)

    a_eff <- norm_val(a_y_raw, fit_eff)
    a_pre <- norm_val(log(a_p_raw + 1.0), fit_pre)

    # Step 5: Grey relational coefficient and grade
    delta_eff <- abs(x_eff - a_eff)
    delta_pre <- abs(x_pre - a_pre)

    all_deltas <- c(delta_eff, delta_pre)
    delta_min <- min(all_deltas)
    delta_max <- max(all_deltas)

    grc_eff <- (delta_min + zeta * delta_max) / (delta_eff + zeta * delta_max)
    grc_pre <- (delta_min + zeta * delta_max) / (delta_pre + zeta * delta_max)

    grade <- (grc_eff + grc_pre) / 2.0

    # Step 6: Effect guard (Tukey bisquare)
    guard <- NULL
    if (effect_guard) {
      mad_y <- median(abs(y - a_y_raw))
      if (mad_y < 1e-12) mad_y <- 1e-12
      u <- abs(y - a_y_raw) / mad_y
      h <- ifelse(u < tukey_c, (1.0 - (u / tukey_c)^2)^2, 0.0)
      guard <- h
      raw_w <- grade * h^guard_power
    } else {
      raw_w <- grade
    }

    # Step 7: Normalize weights
    sw <- sum(raw_w)
    if (sw < 1e-15) {
      # All weights zero — fallback to equal weights
      w <- rep(1.0 / n, n)
    } else {
      w <- raw_w / sw
    }

    # Step 8: Pooled estimate
    est <- sum(w * y)

    list(
      estimate = est,
      weights = w,
      guard_values = guard,
      anchor_y = a_y_raw,
      anchor_p = a_p_raw
    )
  }

  # --- Fit on original data ---
  fit0 <- grma_core(yi, vi)
  est0 <- fit0$estimate
  w0 <- fit0$weights
  w_max <- max(w0)
  n_eff <- 1.0 / sum(w0^2)

  # --- Bootstrap ---
  if (!is.null(seed)) set.seed(seed)
  boot_est <- numeric(n_boot)
  for (b in seq_len(n_boot)) {
    idx <- sample.int(k, k, replace = TRUE)
    res_b <- tryCatch(
      grma_core(yi[idx], vi[idx]),
      error = function(e) list(estimate = NA_real_)
    )
    boot_est[b] <- res_b$estimate
  }

  # Remove failed replicates
  boot_ok <- boot_est[is.finite(boot_est)]
  n_ok <- length(boot_ok)

  if (n_ok < 10) {
    # Fallback: cannot do bootstrap inference
    warning("Too few successful bootstrap replicates. Reporting NA CIs.")
    return(list(
      estimate = est0,
      se = NA_real_,
      ci_lb = NA_real_,
      ci_ub = NA_real_,
      ci_lb_bca = NA_real_,
      ci_ub_bca = NA_real_,
      pvalue = NA_real_,
      tau2 = NA_real_,
      method = if (effect_guard) "GRMA" else "GRMA_noguard",
      k = k,
      w_max = w_max,
      n_eff = n_eff,
      anchor_y = fit0$anchor_y,
      anchor_p = fit0$anchor_p,
      weights = w0,
      guard_values = fit0$guard_values
    ))
  }

  boot_se <- sd(boot_ok)

  # --- Percentile CI ---
  alpha <- 0.05
  ci_lb_pct <- quantile(boot_ok, alpha / 2, names = FALSE)
  ci_ub_pct <- quantile(boot_ok, 1 - alpha / 2, names = FALSE)

  # --- BCa CI (full, with jackknife acceleration) ---
  ci_lb_bca <- NA_real_
  ci_ub_bca <- NA_real_

  if (bca && n_ok >= 50) {
    # Bias correction: z0
    prop_below <- mean(boot_ok < est0)
    # Clamp to avoid Inf from qnorm
    prop_below <- max(1 / (2 * n_ok), min(1 - 1 / (2 * n_ok), prop_below))
    z0 <- qnorm(prop_below)

    # Jackknife acceleration: a_hat
    jack_est <- numeric(k)
    for (i in seq_len(k)) {
      res_j <- tryCatch(
        grma_core(yi[-i], vi[-i]),
        error = function(e) list(estimate = NA_real_)
      )
      jack_est[i] <- res_j$estimate
    }

    jack_ok <- jack_est[is.finite(jack_est)]
    if (length(jack_ok) >= 3) {
      jack_mean <- mean(jack_ok)
      d <- jack_mean - jack_est
      d[!is.finite(d)] <- 0
      denom <- sum(d^2)
      if (denom > 1e-30) {
        a_hat <- sum(d^3) / (6.0 * denom^1.5)
      } else {
        a_hat <- 0.0
      }
    } else {
      a_hat <- 0.0
    }

    # Adjusted percentiles
    z_alpha_lo <- qnorm(alpha / 2)
    z_alpha_hi <- qnorm(1 - alpha / 2)

    adj_lo <- pnorm(z0 + (z0 + z_alpha_lo) / (1 - a_hat * (z0 + z_alpha_lo)))
    adj_hi <- pnorm(z0 + (z0 + z_alpha_hi) / (1 - a_hat * (z0 + z_alpha_hi)))

    # Clamp to valid quantile range
    adj_lo <- max(0.5 / n_ok, min(1 - 0.5 / n_ok, adj_lo))
    adj_hi <- max(0.5 / n_ok, min(1 - 0.5 / n_ok, adj_hi))

    ci_lb_bca <- quantile(boot_ok, adj_lo, names = FALSE)
    ci_ub_bca <- quantile(boot_ok, adj_hi, names = FALSE)
  }

  # --- P-value (two-sided, from bootstrap SE) ---
  if (boot_se > 1e-15) {
    z_stat <- est0 / boot_se
    pval <- 2 * (1 - pnorm(abs(z_stat)))
  } else {
    pval <- NA_real_
  }

  # --- Return ---
  list(
    estimate = est0,
    se = boot_se,
    ci_lb = ci_lb_pct,
    ci_ub = ci_ub_pct,
    ci_lb_bca = ci_lb_bca,
    ci_ub_bca = ci_ub_bca,
    pvalue = pval,
    tau2 = NA_real_,
    method = if (effect_guard) "GRMA" else "GRMA_noguard",
    k = k,
    w_max = w_max,
    n_eff = n_eff,
    anchor_y = fit0$anchor_y,
    anchor_p = fit0$anchor_p,
    weights = w0,
    guard_values = fit0$guard_values
  )
}


#' GRMA Leave-One-Out Influence Analysis
#'
#' Computes leave-one-out estimates and weight diagnostics for GRMA.
#'
#' @param yi Numeric vector of effect sizes
#' @param vi Numeric vector of sampling variances
#' @param ... Additional arguments passed to grma_meta (except n_boot)
#' @return A list with:
#'   \describe{
#'     \item{est_full}{Full-sample estimate}
#'     \item{est_loo}{Vector of leave-one-out estimates}
#'     \item{delta_est}{Absolute change in estimate for each omission}
#'     \item{w_max_loo}{w_max for each leave-one-out fit}
#'     \item{max_abs_delta_est}{Maximum absolute change in estimate}
#'     \item{idx_max_shift}{Index of study with maximum influence (0-based)}
#'     \item{max_abs_delta_maxw}{Maximum absolute change in w_max}
#'     \item{idx_maxw_shift}{Index of study with max w_max change (0-based)}
#'   }
#' @export
grma_loo <- function(yi, vi, ...) {
  k <- length(yi)
  # Full fit (minimal bootstrap, just need point estimate + w_max)
  fit_full <- grma_meta(yi, vi, n_boot = 50, bca = FALSE, ...)
  est_full <- fit_full$estimate
  w_max_full <- fit_full$w_max

  est_loo <- numeric(k)
  w_max_loo <- numeric(k)

  for (i in seq_len(k)) {
    fit_i <- grma_meta(yi[-i], vi[-i], n_boot = 50, bca = FALSE, ...)
    est_loo[i] <- fit_i$estimate
    w_max_loo[i] <- fit_i$w_max
  }

  delta_est <- abs(est_loo - est_full)
  delta_maxw <- abs(w_max_loo - w_max_full)

  idx_max <- which.max(delta_est)
  idx_maxw <- which.max(delta_maxw)

  list(
    est_full = est_full,
    est_loo = est_loo,
    delta_est = delta_est,
    w_max_full = w_max_full,
    w_max_loo = w_max_loo,
    max_abs_delta_est = max(delta_est),
    idx_max_shift = idx_max - 1L,  # 0-based for Python compatibility
    max_abs_delta_maxw = max(delta_maxw),
    idx_maxw_shift = idx_maxw - 1L,
    y_at_max = yi[idx_max],
    v_at_max = vi[idx_max]
  )
}


#' GRMA Valley Diagnostic (Exploratory)
#'
#' Tests for bimodality-like patterns by comparing within-cluster dispersion
#' around the pooled estimate with global dispersion.
#'
#' @param yi Numeric vector of effect sizes
#' @param estimate GRMA pooled estimate
#' @param n_perm Number of permutations for p-value calibration. Default 999.
#' @param seed Optional seed.
#' @return A list with valley_flag (logical) and valley_p (p-value).
#' @keywords internal
grma_valley <- function(yi, estimate, n_perm = 999, seed = NULL) {
  k <- length(yi)
  if (k < 4) return(list(valley_flag = FALSE, valley_p = 1.0))

  # Split studies into above/below estimate
  below <- yi[yi <= estimate]
  above <- yi[yi > estimate]

  if (length(below) < 2 || length(above) < 2) {
    return(list(valley_flag = FALSE, valley_p = 1.0))
  }

  # Test statistic: ratio of within-group variance to total variance
  within_var <- (var(below) * (length(below) - 1) +
                   var(above) * (length(above) - 1)) / (k - 2)
  total_var <- var(yi)
  if (total_var < 1e-15) return(list(valley_flag = FALSE, valley_p = 1.0))

  obs_ratio <- within_var / total_var

  # Permutation calibration
  if (!is.null(seed)) set.seed(seed)
  perm_ratios <- numeric(n_perm)
  for (p in seq_len(n_perm)) {
    y_perm <- sample(yi)
    b <- y_perm[y_perm <= estimate]
    a <- y_perm[y_perm > estimate]
    if (length(b) >= 2 && length(a) >= 2) {
      wv <- (var(b) * (length(b) - 1) + var(a) * (length(a) - 1)) / (k - 2)
      perm_ratios[p] <- wv / total_var
    } else {
      perm_ratios[p] <- 1.0
    }
  }

  valley_p <- mean(perm_ratios <= obs_ratio)
  valley_flag <- valley_p < 0.05

  list(valley_flag = valley_flag, valley_p = valley_p)
}
