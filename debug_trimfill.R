#!/usr/bin/env Rscript

# Debug trimfill
library(metafor)

set.seed(123)
yi <- rnorm(10, 0.3, 0.2)
vi <- rexp(10, 10) + 0.01

tf <- tryCatch(
  trimfill(yi, vi, estimator = "R0", method = "REML"),
  error = function(e) rma(yi, vi, method = "REML")
)

cat("class(tf):", class(tf), "\n")
cat("names(tf):", names(tf), "\n")
cat("tf$k:", tf$k, "\n")

if ("fill" %in% names(tf)) {
  cat("tf$fill exists\n")
  cat("class(tf$fill):", class(tf$fill), "\n")
  if (is.data.frame(tf$fill)) {
    cat("nrow(tf$fill):", nrow(tf$fill), "\n")
    print(tf$fill)
  }
} else {
  cat("tf$fill does NOT exist\n")
}

cat("coef(tf):", coef(tf), "\n")
cat("tf$se:", tf$se, "\n")
cat("tf$ci.lb:", tf$ci.lb, "\n")
cat("tf$ci.ub:", tf$ci.ub, "\n")
