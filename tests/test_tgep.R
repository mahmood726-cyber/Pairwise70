# Test Suite for TGEP Methodology
library(testthat)
library(metafor)

# Source methods
source(if (file.exists("R/tgep_meta.R")) "R/tgep_meta.R" else "../R/tgep_meta.R")

context("TGEP Pooling Method")

test_that("TGEP point estimate is stable and reasonable", {
  set.seed(123)
  yi <- rnorm(10, 0.5, 0.1)
  vi <- runif(10, 0.01, 0.05)
  
  res <- tgep_meta(yi, vi, n_boot = 0)
  
  expect_equal(res$k, 10)
  expect_true(res$estimate > 0)
  expect_true(is.numeric(res$se))
  expect_equal(res$method, "TGEP")
})

test_that("TGEP handles small k correctly", {
  yi <- c(0.1, 0.2, 0.3)
  vi <- c(0.01, 0.01, 0.01)
  
  # Should trigger fallback to HKSJ
  res <- tgep_meta(yi, vi, n_boot = 0)
  
  expect_equal(res$method, "HKSJ_fallback")
})

test_that("TGEP ensemble weights sum to 1", {
  set.seed(123)
  yi <- rnorm(10)
  vi <- runif(10, 0.01, 0.1)
  
  res <- tgep_meta(yi, vi, n_boot = 0)
  
  expect_equal(sum(res$ensemble_weights), 1.0, tolerance = 1e-7)
})


test_that("GRMA median anchor is evaluated on the complete effect vector", {
  x <- tgep_meta(c(-3, -1, 1, 3), rep(0.03, 4), n_boot = 0)
  expect_equal(unname(x$guard_estimates[["GRMA"]]), 0, tolerance = 1e-10)
})

test_that("GRMA returns the common value for identical effects", {
  x <- tgep_meta(rep(2, 4), rep(0.03, 4), n_boot = 0)
  expect_equal(unname(x$guard_estimates[["GRMA"]]), 2, tolerance = 1e-10)
})


test_that("bootstrap retention excludes failed draws without deleting valid zero estimates", {
  draws <- c(NA_real_, 0, 1, NaN, -2, Inf, -Inf)
  expect_equal(.tgep_valid_bootstrap(draws), c(0, 1, -2))
})


test_that("TGEP reports uncertainty unavailable rather than recycling unrelated dimensions", {
  x <- tgep_meta(c(-3, -1, 1, 3), rep(0.03, 4), n_boot = 0)
  expect_true(is.na(x$se))
  expect_true(is.na(x$ci_lb))
  expect_true(is.na(x$ci_ub))
  expect_true(is.na(x$pvalue))
  expect_equal(x$uncertainty_status, "not_estimable_from_requested_bootstrap")
})


test_that("TGEP rejects malformed vectors and invalid tuning controls", {
  yi <- c(-0.2, 0.1, 0.3, 0.4)
  vi <- rep(0.02, 4)
  invalid <- list(
    list(yi=yi, vi=rep(0.02, 8)),
    list(yi=yi, vi=rep(0.02, 2)),
    list(yi=yi, vi=c(0.02, 0, 0.02, 0.02)),
    list(yi=yi, vi=c(0.02, -0.1, 0.02, 0.02)),
    list(yi=yi, vi=c(0.02, NA_real_, 0.02, 0.02)),
    list(yi=c(yi[1:3], Inf), vi=vi),
    list(yi=yi[1], vi=vi[1]),
    list(yi=matrix(yi, nrow=2), vi=vi),
    list(yi=yi, vi=vi, temperature=0),
    list(yi=yi, vi=vi, temperature=-1),
    list(yi=yi, vi=vi, temperature=Inf),
    list(yi=yi, vi=vi, n_boot=-1),
    list(yi=yi, vi=vi, n_boot=2.5),
    list(yi=yi, vi=vi, n_boot=NA_real_),
    list(yi=yi, vi=vi, n_boot=Inf)
  )
  for (i in seq_along(invalid)) {
    expect_error(do.call(tgep_meta, invalid[[i]]),
                 regexp="^TGEP input:", info=paste("input case", i))
  }
})

test_that("valid TGEP inputs retain finite point estimate and honest missing SE", {
  yi <- c(-0.2, 0.1, 0.3, 0.4)
  vi <- rep(0.02, 4)
  x <- tgep_meta(yi, vi, n_boot=0, temperature=1)
  expect_true(is.finite(x$estimate))
  expect_equal(x$k, length(yi))
  expect_true(is.na(x$se))
  expect_identical(x$uncertainty_status, "not_estimable_from_requested_bootstrap")
})

cat("
All TGEP tests passed!
")
