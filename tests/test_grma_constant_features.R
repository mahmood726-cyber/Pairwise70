# Regression tests for constant-feature grey relational coefficients.
# Only synthetic inputs are used; these do not validate clinical estimates.
library(testthat)
library(metafor)
source(if (file.exists("R/grma_meta.R")) "R/grma_meta.R" else "../R/grma_meta.R")

test_that("flat effect and precision features do not cause 0/0 GRC", {
  yi <- rep(0.4, 4)
  vi <- rep(0.04, 4)
  for (guard in c(TRUE, FALSE)) {
    fit <- grma_meta(yi, vi, n_boot = 20L, bca = FALSE,
                     seed = 101L, effect_guard = guard)
    expect_equal(fit$estimate, 0.4, tolerance = 1e-12)
    expect_equal(unname(fit$weights), rep(0.25, 4), tolerance = 1e-12)
    expect_equal(fit$w_max, 0.25, tolerance = 1e-12)
    expect_equal(fit$n_eff, 4, tolerance = 1e-12)
    expect_equal(fit$ci_lb, 0.4, tolerance = 1e-12)
    expect_equal(fit$ci_ub, 0.4, tolerance = 1e-12)
    # Zero resampling variation is not a calibrated hypothesis test.
    expect_true(is.na(fit$pvalue))
  }
})

test_that("flat negative, zero and capped-precision examples remain finite", {
  for (mu in c(-0.5, 0.0, 1.2)) {
    fit <- suppressWarnings(
      grma_meta(rep(mu, 5), rep(1e-12, 5), n_boot = 0L,
                bca = FALSE, effect_guard = TRUE)
    )
    expect_equal(fit$estimate, mu, tolerance = 1e-12)
    expect_equal(unname(fit$weights), rep(0.2, 5), tolerance = 1e-12)
    expect_true(is.na(fit$se))
    expect_true(is.na(fit$pvalue))
  }
})

test_that("varying features preserve finite normalized GRMA weights", {
  scenarios <- list(
    list(y = c(-0.2, 0.05, 0.3, 0.9), v = rep(0.04, 4)),
    list(y = rep(0.4, 4), v = c(0.01, 0.02, 0.04, 0.08)),
    list(y = c(-0.2, 0.05, 0.3, 0.9), v = c(0.01, 0.02, 0.04, 0.08))
  )
  for (example in scenarios) {
    fit <- suppressWarnings(
      grma_meta(example$y, example$v, n_boot = 0L,
                bca = FALSE, effect_guard = FALSE)
    )
    expect_true(is.finite(fit$estimate))
    expect_true(all(is.finite(fit$weights)))
    expect_true(all(fit$weights >= 0))
    expect_equal(sum(fit$weights), 1.0, tolerance = 1e-12)
  }
})
