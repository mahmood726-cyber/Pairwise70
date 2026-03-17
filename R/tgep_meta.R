#' Triple-Guard Ensemble Pooling (TGEP)
#'
#' An adaptive, frequentist ensemble method that stacks three specialized guards
#' (Spatial, Winsorized, and Bias-Adaptive) using LOO-CV weighting.
#'
#' @param yi Numeric vector of effect sizes.
#' @param vi Numeric vector of sampling variances.
#' @param n_boot Number of bootstrap iterations for SE calculation. Default 100.
#' @param temperature Softmax temperature for weighting (1.0 = default adaptive).
#' @return A list containing the pooled estimate, standard error, and ensemble diagnostics.
#' @export
tgep_meta <- function(yi, vi, n_boot = 100, temperature = 1.0) {
  k <- length(yi)
  
  # Minimum k check: fall back to HKSJ if k < 4
  if (k < 4) {
    fit <- metafor::rma(yi, vi, method = "REML", test = "knha")
    return(list(
      estimate = as.numeric(coef(fit)),
      se = fit$se,
      ci_lb = fit$ci.lb,
      ci_ub = fit$ci.ub,
      pvalue = fit$pval,
      method = "HKSJ_fallback",
      k = k,
      note = "k < 4, TGEP requires at least 4 studies for CV stacking"
    ))
  }

  # 1. Define Guard Components (referencing internal logic)
  guards <- list(
    GRMA = function(y, v) {
      # Robust Spatial Guard
      # (Internal simplified GRMA logic)
      prec <- 1/v; lp <- log(prec + 1)
      s <- function(x) { r <- diff(range(x)); if(r < 1e-12) 1 else (x-min(x))/r }
      x_e <- s(y); x_p <- s(lp)
      a_e <- s(median(y)); a_p <- s(max(lp))
      d_e <- abs(x_e - a_e); d_p <- abs(x_p - a_p)
      g_e <- (0.5) / (d_e + 0.5); g_p <- (0.5) / (d_p + 0.5)
      w <- (g_e + g_p)/2; w <- w/sum(w)
      sum(w * y)
    },
    WRD = function(y, v) {
      # Winsorized Magnitude Guard
      fit <- tryCatch(metafor::rma(y, v, method="REML"), error=function(e) list(beta=median(y), tau2=0))
      est <- as.numeric(fit$beta); tau2 <- if(is.null(fit$tau2)) 0 else fit$tau2
      z <- (y - est) / sqrt(v + tau2)
      z_w <- pmin(pmax(z, -2.5), 2.5)
      y_w <- est + z_w * sqrt(v + tau2)
      w <- 1/(v + tau2); sum(w * y_w)/sum(w)
    },
    SWA = function(y, v) {
      # Bias-Adaptive Guard
      fit <- tryCatch(metafor::rma(y, v, method="REML"), error=function(e) list(beta=median(y), tau2=0))
      tau2 <- if(is.null(fit$tau2)) 0 else fit$tau2
      p <- 2 * (1 - pnorm(abs(y / sqrt(v + tau2))))
      w_s <- ifelse(p < 0.05, 1.0, 0.4)
      w <- (1/(v + tau2)) / w_s; sum(w * y)/sum(w)
    }
  )

  # 2. Point Estimates and Stacking Weights
  est_guards <- sapply(guards, function(f) f(yi, vi))
  
  loo_errors <- matrix(0, nrow = k, ncol = length(guards))
  for (i in 1:k) {
    y_m <- yi[-i]; v_m <- vi[-i]
    for (g in 1:length(guards)) {
      est_i <- tryCatch(guards[[g]](y_m, v_m), error = function(e) median(y_m))
      loo_errors[i, g] <- (yi[i] - est_i)^2 / vi[i]
    }
  }
  
  cv_scores <- colMeans(loo_errors)
  # Standardized softmax weighting
  cv_scaled <- (cv_scores - min(cv_scores)) / (max(cv_scores) - min(cv_scores) + 1e-6)
  w_ens <- exp(-cv_scaled / temperature) / sum(exp(-cv_scaled / temperature))
  
  estimate <- sum(w_ens * est_guards)

  # 3. Bootstrap SE
  if (n_boot > 0) {
    boot_est <- numeric(n_boot)
    for (b in 1:n_boot) {
      idx <- sample(1:k, k, replace = TRUE)
      try({
        y_b <- yi[idx]; v_b <- vi[idx]
        e_b <- sapply(guards, function(f) f(y_b, v_b))
        boot_est[b] <- sum(w_ens * e_b)
      }, silent = TRUE)
    }
    boot_est <- boot_est[is.finite(boot_est) & boot_est != 0]
    se <- if(length(boot_est) > 5) sd(boot_est) else sqrt(sum(w_ens^2 * (vi + var(yi))))/sqrt(k)
  } else {
    se <- sqrt(sum(w_ens^2 * (vi + var(yi))))/sqrt(k)
  }

  list(
    estimate = estimate,
    se = se,
    ci_lb = estimate - 1.96 * se,
    ci_ub = estimate + 1.96 * se,
    pvalue = 2 * (1 - pnorm(abs(estimate / se))),
    method = "TGEP",
    k = k,
    ensemble_weights = w_ens,
    guard_estimates = est_guards,
    cv_scores = cv_scores
  )
}
