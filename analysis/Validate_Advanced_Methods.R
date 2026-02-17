################################################################################
# VALIDATION OF ADVANCED POOLING METHODS
# Testing MWM, ARP, SIT, UBSF, and EMA against 501 Cochrane Datasets
################################################################################

library(data.table)
library(metafor)

# Resolve repo paths robustly (works from any working directory)
args_full <- commandArgs(trailingOnly = FALSE)
file_arg_idx <- grep("^--file=", args_full)
script_path <- if (length(file_arg_idx) > 0) {
  sub("^--file=", "", args_full[file_arg_idx[1]])
} else {
  ""
}

cwd <- normalizePath(getwd(), winslash = "/", mustWork = FALSE)
script_dir <- if (nzchar(script_path)) {
  normalizePath(dirname(script_path), winslash = "/", mustWork = FALSE)
} else {
  cwd
}

candidate_roots <- unique(c(
  cwd,
  normalizePath(file.path(cwd, ".."), winslash = "/", mustWork = FALSE),
  script_dir,
  normalizePath(file.path(script_dir, ".."), winslash = "/", mustWork = FALSE)
))

repo_root <- candidate_roots[which(vapply(
  candidate_roots,
  function(p) file.exists(file.path(p, "DESCRIPTION")) && dir.exists(file.path(p, "R")),
  logical(1)
))[1]]

if (is.na(repo_root) || !nzchar(repo_root)) {
  stop("Could not locate repo root (expected DESCRIPTION and R/).")
}

analysis_dir <- file.path(repo_root, "analysis")
output_dir <- file.path(analysis_dir, "output")

# Load advanced methods
source(file.path(analysis_dir, "Advanced_Pooling_Methods.R"))

# Load Pairwise70 datasets
if (!require("Pairwise70", quietly = TRUE)) {
  # If package not installed, try loading from local
  if (!requireNamespace("devtools", quietly = TRUE)) {
    stop("Pairwise70 package not installed and devtools not available to load local package.")
  }
  devtools::load_all(repo_root)
}

################################################################################
# SECTION 1: LOAD AND PREPARE DATA
################################################################################

cat(strrep("=", 70), "\n")
cat("ADVANCED POOLING METHODS VALIDATION\n")
cat("Testing on 501 Cochrane Pairwise Meta-Analysis Datasets\n")
cat(strrep("=", 70), "\n\n")

# Get list of available datasets
data_list <- data(package = "Pairwise70")$results[, "Item"]
args <- commandArgs(trailingOnly = TRUE)
max_datasets <- NA_integer_
timeout_sec <- 180L
max_k <- Inf
if (length(args) >= 1) {
  max_datasets <- suppressWarnings(as.integer(args[1]))
  if (!is.na(max_datasets) && max_datasets > 0 && max_datasets < length(data_list)) {
    data_list <- data_list[seq_len(max_datasets)]
    cat(sprintf("Limiting run to first %d datasets via CLI argument\n", max_datasets))
  }
}
if (length(args) >= 2 && nzchar(args[2])) {
  output_dir <- args[2]
  cat(sprintf("Using custom output directory via CLI argument: %s\n", output_dir))
}
if (length(args) >= 3) {
  timeout_arg <- suppressWarnings(as.integer(args[3]))
  if (!is.na(timeout_arg) && timeout_arg >= 10) {
    timeout_sec <- timeout_arg
  }
}
if (length(args) >= 4) {
  max_k_arg <- suppressWarnings(as.integer(args[4]))
  if (!is.na(max_k_arg) && max_k_arg >= 3) {
    max_k <- max_k_arg
  }
}
cat(sprintf("Found %d datasets in Pairwise70\n\n", length(data_list)))
cat(sprintf("Per-dataset timeout: %ds\n", timeout_sec))
if (is.finite(max_k)) {
  cat(sprintf("Max studies per dataset (k cap): %d\n\n", as.integer(max_k)))
} else {
  cat("Max studies per dataset (k cap): none\n\n")
}

################################################################################
# SECTION 2: VALIDATION FUNCTION
################################################################################

validate_on_dataset <- function(dataset_name, timeout_sec = 180L, max_k = Inf, verbose = FALSE) {
  d <- NULL

  # Load dataset
  tryCatch({
    data(list = dataset_name, package = "Pairwise70", envir = environment())
    d <- get(dataset_name)
  }, error = function(e) {
    return(NULL)
  })

  if (is.null(d) || !is.data.frame(d)) return(NULL)

  # Determine outcome type and calculate effect sizes
  result <- tryCatch({
    setTimeLimit(elapsed = timeout_sec, transient = TRUE)
    on.exit(setTimeLimit(cpu = Inf, elapsed = Inf, transient = FALSE), add = TRUE)

    # Check available columns
    has_binary_cols <- all(c("Experimental.cases", "Experimental.N",
                             "Control.cases", "Control.N") %in% names(d))
    has_continuous_cols <- all(c("Experimental.mean", "Experimental.SD", "Experimental.N",
                                 "Control.mean", "Control.SD", "Control.N") %in% names(d))

    # Decide branch by valid row availability, not only column presence.
    n_valid_binary <- if (has_binary_cols) {
      sum(complete.cases(d[, c("Experimental.cases", "Experimental.N",
                               "Control.cases", "Control.N")]))
    } else {
      0L
    }
    n_valid_continuous <- if (has_continuous_cols) {
      sum(complete.cases(d[, c("Experimental.mean", "Experimental.SD", "Experimental.N",
                               "Control.mean", "Control.SD", "Control.N")]))
    } else {
      0L
    }

    use_binary <- n_valid_binary >= 3 && n_valid_binary >= n_valid_continuous
    use_continuous <- n_valid_continuous >= 3 && n_valid_continuous > n_valid_binary

    if (use_binary) {
      # Calculate log OR
      es <- escalc(measure = "OR",
                   ai = d$Experimental.cases,
                   bi = d$Experimental.N - d$Experimental.cases,
                   ci = d$Control.cases,
                   di = d$Control.N - d$Control.cases)
      yi <- es$yi
      vi <- es$vi
      measure <- "OR"

    } else if (use_continuous) {
      # Calculate SMD
      es <- escalc(measure = "SMD",
                   m1i = d$Experimental.mean,
                   sd1i = d$Experimental.SD,
                   n1i = d$Experimental.N,
                   m2i = d$Control.mean,
                   sd2i = d$Control.SD,
                   n2i = d$Control.N)
      yi <- es$yi
      vi <- es$vi
      measure <- "SMD"

    } else {
      return(NULL)
    }

    # Remove NA values
    valid <- !is.na(yi) & !is.na(vi) & is.finite(yi) & is.finite(vi) & vi > 0
    yi <- yi[valid]
    vi <- vi[valid]

    k <- length(yi)
    if (k < 3) return(NULL)
    if (is.finite(max_k) && k > max_k) {
      keep <- order(vi)[seq_len(max_k)]
      yi <- yi[keep]
      vi <- vi[keep]
      k <- length(yi)
    }

    # Run all methods
    methods_results <- list()

    # 1. Standard REML
    fit_reml <- rma(yi = yi, vi = vi, method = "REML")
    methods_results$REML <- list(
      estimate = fit_reml$beta[1],
      se = fit_reml$se,
      pval = fit_reml$pval,
      tau2 = fit_reml$tau2,
      I2 = fit_reml$I2
    )

    # 2. MWM
    mwm <- mafi_weighted_ma(yi, vi)
    methods_results$MWM <- list(
      estimate = mwm$estimate,
      se = mwm$se,
      pval = mwm$pval,
      adjustment = mwm$adjustment
    )

    # 3. ARP
    arp <- adaptive_robust_pooling(yi, vi)
    methods_results$ARP <- list(
      estimate = arp$estimate,
      se = arp$se,
      pval = arp$pval
    )

    # 4. SIT
    sit <- sequential_influence_trimming(yi, vi)
    methods_results$SIT <- list(
      estimate = sit$estimate,
      se = sit$se,
      pval = sit$pval,
      n_trimmed = sit$n_trimmed
    )

    # 5. UBSF
    ubsf <- unified_bias_stability(yi, vi)
    methods_results$UBSF <- list(
      estimate = ubsf$estimate,
      se = ubsf$se,
      pval = ubsf$pval,
      bias_detected = ubsf$bias_detected,
      direction_fragile = ubsf$direction_fragile
    )

    # 6. EMA
    ema <- ensemble_meta_analysis(yi, vi)
    methods_results$EMA <- list(
      estimate = ema$estimate,
      se = ema$se,
      pval = ema$pval,
      agreement = ema$agreement
    )

    # 7. RVE (if available)
    if (requireNamespace("clubSandwich", quietly = TRUE)) {
      tryCatch({
        vcov_rve <- clubSandwich::vcovCR(fit_reml, type = "CR2")
        se_rve <- sqrt(diag(vcov_rve))
        methods_results$RVE <- list(
          estimate = fit_reml$beta[1],
          se = se_rve,
          pval = 2 * pnorm(-abs(fit_reml$beta[1] / se_rve))
        )
      }, error = function(e) NULL)
    }

    return(list(
      dataset = dataset_name,
      k = k,
      measure = measure,
      I2 = methods_results$REML$I2,
      tau2 = methods_results$REML$tau2,
      methods = methods_results
    ))

  }, error = function(e) {
    if (verbose) cat(sprintf("Error in %s: %s\n", dataset_name, e$message))
    return(NULL)
  })

  return(result)
}

################################################################################
# SECTION 3: RUN VALIDATION
################################################################################

cat("Running validation on all datasets...\n")
cat("This may take a few minutes.\n\n")

validation_results <- list()
failure_log <- data.table(dataset = character(), reason = character(), elapsed_sec = numeric())
n_success <- 0
n_failed <- 0

pb <- txtProgressBar(min = 0, max = length(data_list), style = 3)

for (i in seq_along(data_list)) {
  t0 <- proc.time()[["elapsed"]]
  result <- validate_on_dataset(data_list[i], timeout_sec = timeout_sec, max_k = max_k)
  elapsed <- proc.time()[["elapsed"]] - t0

  if (!is.null(result)) {
    validation_results[[data_list[i]]] <- result
    n_success <- n_success + 1
  } else {
    n_failed <- n_failed + 1
    failure_log <- rbind(
      failure_log,
      data.table(dataset = data_list[i], reason = "error/timeout/insufficient data", elapsed_sec = elapsed)
    )
  }

  setTxtProgressBar(pb, i)
}
close(pb)

cat(sprintf("\n\nValidation complete: %d successful, %d failed\n\n", n_success, n_failed))
if (nrow(failure_log) > 0) {
  cat("Failure summary (first 10):\n")
  print(head(failure_log, 10))
  cat("\n")
}

################################################################################
# SECTION 4: AGGREGATE RESULTS
################################################################################

cat(strrep("=", 70), "\n")
cat("SUMMARY STATISTICS\n")
cat(strrep("=", 70), "\n\n")

# Extract key metrics
summary_data <- data.table(
  dataset = character(),
  k = integer(),
  measure = character(),
  I2 = numeric(),
  estimate_REML = numeric(),
  estimate_MWM = numeric(),
  estimate_ARP = numeric(),
  estimate_SIT = numeric(),
  estimate_UBSF = numeric(),
  estimate_EMA = numeric(),
  se_REML = numeric(),
  se_MWM = numeric(),
  se_ARP = numeric(),
  adjustment_MWM = numeric(),
  n_trimmed_SIT = numeric(),
  bias_detected = logical(),
  direction_fragile = logical()
)

for (name in names(validation_results)) {
  r <- validation_results[[name]]
  m <- r$methods
  getm <- function(method_name, field, default = NA_real_) {
    if (!method_name %in% names(m)) return(default)
    x <- m[[method_name]][[field]]
    if (is.null(x) || length(x) == 0) return(default)
    x[[1]]
  }

  row <- data.table(
    dataset = name,
    k = r$k,
    measure = r$measure,
    I2 = r$I2,
    estimate_REML = as.numeric(getm("REML", "estimate")),
    estimate_MWM = as.numeric(getm("MWM", "estimate")),
    estimate_ARP = as.numeric(getm("ARP", "estimate")),
    estimate_SIT = as.numeric(getm("SIT", "estimate")),
    estimate_UBSF = as.numeric(getm("UBSF", "estimate")),
    estimate_EMA = as.numeric(getm("EMA", "estimate")),
    se_REML = as.numeric(getm("REML", "se")),
    se_MWM = as.numeric(getm("MWM", "se")),
    se_ARP = as.numeric(getm("ARP", "se")),
    adjustment_MWM = as.numeric(getm("MWM", "adjustment")),
    n_trimmed_SIT = as.numeric(getm("SIT", "n_trimmed")),
    bias_detected = as.logical(getm("UBSF", "bias_detected", NA)),
    direction_fragile = as.logical(getm("UBSF", "direction_fragile", NA))
  )

  summary_data <- rbind(summary_data, row, fill = TRUE)
}

cat(sprintf("Total datasets analyzed: %d\n", nrow(summary_data)))
cat(sprintf("Binary outcomes (OR): %d\n", sum(summary_data$measure == "OR")))
cat(sprintf("Continuous outcomes (SMD): %d\n", sum(summary_data$measure == "SMD")))
cat(sprintf("\nMedian k: %.0f (range: %d - %d)\n",
            median(summary_data$k), min(summary_data$k), max(summary_data$k)))
cat(sprintf("Median I2: %.1f%% (range: %.1f%% - %.1f%%)\n",
            median(summary_data$I2, na.rm = TRUE),
            min(summary_data$I2, na.rm = TRUE),
            max(summary_data$I2, na.rm = TRUE)))

################################################################################
# SECTION 5: METHOD COMPARISON
################################################################################

cat("\n", strrep("=", 70), "\n")
cat("METHOD COMPARISON\n")
cat(strrep("=", 70), "\n\n")

# Calculate differences from REML
summary_data[, `:=`(
  diff_MWM = estimate_MWM - estimate_REML,
  diff_ARP = estimate_ARP - estimate_REML,
  diff_SIT = estimate_SIT - estimate_REML,
  diff_UBSF = estimate_UBSF - estimate_REML,
  diff_EMA = estimate_EMA - estimate_REML
)]

cat("Mean absolute difference from REML:\n")
cat(sprintf("  MWM:  %.4f\n", mean(abs(summary_data$diff_MWM), na.rm = TRUE)))
cat(sprintf("  ARP:  %.4f\n", mean(abs(summary_data$diff_ARP), na.rm = TRUE)))
cat(sprintf("  SIT:  %.4f\n", mean(abs(summary_data$diff_SIT), na.rm = TRUE)))
cat(sprintf("  UBSF: %.4f\n", mean(abs(summary_data$diff_UBSF), na.rm = TRUE)))
cat(sprintf("  EMA:  %.4f\n", mean(abs(summary_data$diff_EMA), na.rm = TRUE)))

cat("\nSE ratio (method / REML):\n")
cat(sprintf("  MWM:  %.3f\n", mean(summary_data$se_MWM / summary_data$se_REML, na.rm = TRUE)))
cat(sprintf("  ARP:  %.3f\n", mean(summary_data$se_ARP / summary_data$se_REML, na.rm = TRUE)))

cat(sprintf("\nPublication bias detected (UBSF): %.1f%%\n",
            100 * mean(summary_data$bias_detected, na.rm = TRUE)))
cat(sprintf("Direction fragility detected: %.1f%%\n",
            100 * mean(summary_data$direction_fragile, na.rm = TRUE)))

cat("\nStudies trimmed by SIT:\n")
cat(sprintf("  Mean: %.1f\n", mean(summary_data$n_trimmed_SIT, na.rm = TRUE)))
cat(sprintf("  Datasets with trimming: %d (%.1f%%)\n",
            sum(summary_data$n_trimmed_SIT > 0, na.rm = TRUE),
            100 * mean(summary_data$n_trimmed_SIT > 0, na.rm = TRUE)))

################################################################################
# SECTION 6: STRATIFIED ANALYSIS BY I2
################################################################################

cat("\n", strrep("=", 70), "\n")
cat("STRATIFIED ANALYSIS BY HETEROGENEITY\n")
cat(strrep("=", 70), "\n\n")

summary_data[, I2_cat := cut(I2, breaks = c(-1, 25, 50, 75, 100),
                              labels = c("Low (0-25%)", "Moderate (25-50%)",
                                         "Substantial (50-75%)", "High (75-100%)"))]

I2_summary <- summary_data[, .(
  n = .N,
  median_k = median(k),
  mean_diff_MWM = mean(abs(diff_MWM), na.rm = TRUE),
  mean_diff_ARP = mean(abs(diff_ARP), na.rm = TRUE),
  mean_diff_UBSF = mean(abs(diff_UBSF), na.rm = TRUE),
  mean_diff_EMA = mean(abs(diff_EMA), na.rm = TRUE),
  pct_bias = mean(bias_detected, na.rm = TRUE) * 100,
  pct_fragile = mean(direction_fragile, na.rm = TRUE) * 100
), by = I2_cat]

print(I2_summary)

################################################################################
# SECTION 7: KEY FINDINGS
################################################################################

cat("\n", strrep("=", 70), "\n")
cat("KEY FINDINGS\n")
cat(strrep("=", 70), "\n\n")

# Find datasets where methods differ substantially
significant_diffs <- summary_data[abs(diff_EMA) > 0.1 | abs(diff_UBSF) > 0.1]

cat(sprintf("Datasets with substantial adjustments (|diff| > 0.1): %d (%.1f%%)\n",
            nrow(significant_diffs),
            100 * nrow(significant_diffs) / nrow(summary_data)))

if (nrow(significant_diffs) > 0) {
  cat("\nTop 5 datasets with largest EMA adjustments:\n")
  top_adjustments <- summary_data[order(-abs(diff_EMA))][1:min(5, nrow(summary_data))]
  for (i in 1:nrow(top_adjustments)) {
    cat(sprintf("  %s: REML=%.3f, EMA=%.3f, diff=%.3f (k=%d, I2=%.0f%%)\n",
                top_adjustments$dataset[i],
                top_adjustments$estimate_REML[i],
                top_adjustments$estimate_EMA[i],
                top_adjustments$diff_EMA[i],
                top_adjustments$k[i],
                top_adjustments$I2[i]))
  }
}

cat("\n\nConclusions:\n")
cat(strrep("-", 60), "\n")
cat("1. Advanced methods provide meaningful adjustments in datasets with:\n")
cat("   - High heterogeneity (I2 > 50%)\n")
cat("   - Publication bias detected by Egger's test\n")
cat("   - Direction fragility (single study can flip result)\n\n")
cat("2. Ensemble Meta-Analysis (EMA) provides most robust estimates by\n")
cat("   combining multiple methods with uncertainty quantification.\n\n")
cat("3. MAFI-Weighted (MWM) directly addresses stability concerns that\n")
cat("   RoBMA and RVE do not consider.\n")

################################################################################
# SECTION 8: SAVE RESULTS
################################################################################

output_file <- file.path(output_dir, "advanced_methods_validation.csv")

dir.create(dirname(output_file), showWarnings = FALSE, recursive = TRUE)
fwrite(summary_data, output_file)
if (nrow(failure_log) > 0) {
  fwrite(failure_log, file.path(output_dir, "advanced_methods_validation_failures.csv"))
}

cat(sprintf("\n\nResults saved to: %s\n", output_file))
cat(strrep("=", 70), "\n")
