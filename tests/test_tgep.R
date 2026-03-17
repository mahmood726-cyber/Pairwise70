# Test Suite for TGEP Methodology
library(testthat)
library(metafor)

# Source methods
source("C:/Users/user/OneDrive - NHS/Documents/Pairwise70/R/tgep_meta.R")

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

cat("
All TGEP tests passed!
")
