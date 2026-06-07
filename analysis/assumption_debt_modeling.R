#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(data.table)
})

if (!requireNamespace("sandwich", quietly = TRUE)) {
  stop("Package 'sandwich' is required. Install with install.packages('sandwich').")
}

repo_root <- normalizePath(".", winslash = "/", mustWork = TRUE)
input_fragility <- file.path(repo_root, "analysis", "output", "fragility_analysis_results.csv")
input_diagnostics <- file.path(repo_root, "analysis", "output", "analysis_diagnostics_results.csv")
out_dir <- file.path(repo_root, "analysis", "output")

if (!file.exists(input_fragility)) {
  stop("Missing input: analysis/output/fragility_analysis_results.csv")
}
if (!file.exists(input_diagnostics)) {
  stop("Missing input: analysis/output/analysis_diagnostics_results.csv")
}

frag <- fread(input_fragility)
diag <- fread(input_diagnostics)

frag[, aid := as.integer(analysis_id)]
if (!all(c("dataset_name", "analysis_number") %in% names(diag))) {
  stop("Diagnostics file does not contain expected keys: dataset_name, analysis_number")
}

setnames(diag, old = c("dataset_name", "analysis_number", "i2"), new = c("dataset", "aid", "i2_diag"))

diag_agg <- diag[, .(
  k_diag = suppressWarnings(max(k, na.rm = TRUE)),
  egger_min_p = suppressWarnings(min(egger_p, na.rm = TRUE)),
  max_weight_share = suppressWarnings(max(max_weight_share[is.finite(max_weight_share)], na.rm = TRUE)),
  sparse_events = suppressWarnings(max(sparse_events, na.rm = TRUE))
), by = .(dataset, aid)]

diag_agg[is.infinite(egger_min_p), egger_min_p := NA_real_]
diag_agg[!is.finite(max_weight_share), max_weight_share := NA_real_]

dat <- merge(frag, diag_agg, by = c("dataset", "aid"), all.x = TRUE)

dat[, fragile_any := as.integer(fifelse(is.na(direction_fragile), FALSE, direction_fragile) |
                              fifelse(is.na(sig_fragile), FALSE, sig_fragile))]
dat[, fragile_any_cc := fifelse(is.na(direction_fragile) | is.na(sig_fragile), NA_real_,
                                as.integer(direction_fragile | sig_fragile))]
dat[, sparse_k := as.integer(k < 10)]
dat[, high_heterogeneity := as.integer(I2 >= 50)]
dat[, small_study_signal := as.integer(!is.na(egger_min_p) & k_diag >= 10 & egger_min_p < 0.10)]
dat[, dominance_signal := as.integer(!is.na(max_weight_share) & max_weight_share >= 0.50)]
dat[, sparse_events_signal := as.integer(!is.na(sparse_events) & sparse_events > 0)]

component_cols <- c(
  "sparse_k",
  "high_heterogeneity",
  "small_study_signal",
  "dominance_signal"
)
dat[, assumption_debt_score := rowSums(.SD, na.rm = TRUE), .SDcols = component_cols]
dat[, high_debt := as.integer(assumption_debt_score >= 2)]
# Assessability sensitivity: score excluding Egger small-study component.
dat[, assumption_debt_score_no_egger := sparse_k + high_heterogeneity + dominance_signal]

model_data <- dat[
  is.finite(k) & is.finite(I2) & is.finite(tau2) & is.finite(estimate) &
    is.finite(assumption_debt_score) & is.finite(fragile_any)
]

if (nrow(model_data) < 200) {
  stop("Insufficient complete rows for modeling.")
}

model_data[, log_k := log(pmax(k, 2))]
model_data[, abs_estimate := abs(estimate)]
model_data[, tau2_capped := pmin(tau2, quantile(tau2, probs = 0.99, na.rm = TRUE))]
model_data[, dataset_n := .N, by = dataset]
model_data[, w_dataset_equal := 1 / dataset_n]
measure_counts <- sort(table(model_data$measure), decreasing = TRUE)
ref_measure_main <- names(measure_counts)[1]
model_data[, measure_factor := relevel(factor(measure), ref = ref_measure_main)]

fit_score <- glm(
  fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
  data = model_data,
  family = binomial()
)
# Assessability sensitivity: omit Egger-based component from debt score.
fit_score_no_egger <- glm(
  fragile_any ~ assumption_debt_score_no_egger + log_k + abs_estimate + tau2_capped,
  data = model_data,
  family = binomial()
)
# Binary-outcome RR sensitivity: modified Poisson approximation.
fit_score_rr <- glm(
  fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
  data = model_data,
  family = quasipoisson()
)
# Assessability sensitivity: restrict to k >= 10 where Egger-type diagnostics are assessable.
model_data_assessable <- model_data[k_diag >= 10]
fit_score_assessable <- glm(
  fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
  data = model_data_assessable,
  family = binomial()
)

# Outcome-missingness sensitivity: complete-case fragility outcome.
model_data_cc <- model_data[is.finite(fragile_any_cc)]
fit_score_cc <- glm(
  fragile_any_cc ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
  data = model_data_cc,
  family = binomial()
)

# Outcome-specific sensitivities: direction fragility and significance fragility separately.
model_data_dir <- model_data[is.finite(direction_fragile)]
model_data_sig <- model_data[is.finite(sig_fragile)]
model_data_clin <- model_data[is.finite(clinical_fragile)]
model_data_clin[, dataset_n_clin := .N, by = dataset]
model_data_clin[, w_dataset_equal_clin := 1 / dataset_n_clin]
model_data_both <- model_data[is.finite(direction_fragile) & is.finite(sig_fragile)]
model_data_both[, both_fragile := as.integer(direction_fragile == 1 & sig_fragile == 1)]
model_data_both[, dataset_n_both := .N, by = dataset]
model_data_both[, w_dataset_equal_both := 1 / dataset_n_both]
fit_score_dir <- glm(
  direction_fragile ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
  data = model_data_dir,
  family = binomial()
)
fit_score_sig <- glm(
  sig_fragile ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
  data = model_data_sig,
  family = binomial()
)
fit_score_clin <- glm(
  clinical_fragile ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
  data = model_data_clin,
  family = binomial()
)
fit_score_clin_rr <- glm(
  clinical_fragile ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
  data = model_data_clin,
  family = quasipoisson()
)
fit_score_clin_dataset_equal <- glm(
  clinical_fragile ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
  data = model_data_clin,
  family = quasibinomial(),
  weights = w_dataset_equal_clin
)
fit_score_both <- glm(
  both_fragile ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
  data = model_data_both,
  family = binomial()
)
fit_score_both_rr <- glm(
  both_fragile ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
  data = model_data_both,
  family = quasipoisson()
)
fit_score_both_dataset_equal <- glm(
  both_fragile ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
  data = model_data_both,
  family = quasibinomial(),
  weights = w_dataset_equal_both
)

# Outcome-intensity sensitivity: composite fragility count (0+), modeled with quasipoisson.
model_data_comp <- model_data[is.finite(composite_fragility)]
fit_score_comp <- glm(
  composite_fragility ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
  data = model_data_comp,
  family = quasipoisson()
)

# Functional form sensitivity: categorical assumption_debt_score.
fit_score_cat <- glm(
  fragile_any ~ factor(assumption_debt_score) + log_k + abs_estimate + tau2_capped,
  data = model_data,
  family = binomial()
)

fit_components <- glm(
  fragile_any ~ sparse_k + high_heterogeneity + small_study_signal +
    dominance_signal + sparse_events_signal + log_k + abs_estimate + tau2_capped,
  data = model_data,
  family = binomial()
)

# Collinearity-aware sensitivity: component model without log_k.
fit_components_no_logk <- glm(
  fragile_any ~ sparse_k + high_heterogeneity + small_study_signal +
    dominance_signal + sparse_events_signal + abs_estimate + tau2_capped,
  data = model_data,
  family = binomial()
)

# Sensitivity: adjust for effect measure family.
fit_score_measure <- glm(
  fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped + measure_factor,
  data = model_data,
  family = binomial()
)
fit_score_dataset_equal <- glm(
  fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
  data = model_data,
  family = quasibinomial(),
  weights = w_dataset_equal
)
fit_score_measure_interaction <- glm(
  fragile_any ~ assumption_debt_score * measure_factor + log_k + abs_estimate + tau2_capped,
  data = model_data,
  family = binomial()
)

# Within-between decomposition (Mundlak-style): separates within-dataset from between-dataset score signal.
model_data[, score_between := mean(assumption_debt_score), by = dataset]
model_data[, score_within := assumption_debt_score - score_between]
fit_score_within_between <- glm(
  fragile_any ~ score_within + score_between + log_k + abs_estimate + tau2_capped,
  data = model_data,
  family = binomial()
)

# Dataset fixed-effects linear probability sensitivity:
# tests whether within-dataset score variation predicts fragility after absorbing dataset-level confounding.
fit_score_fe_lpm <- lm(
  fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped + factor(dataset),
  data = model_data
)

or_table <- function(fit, vcov_mat = NULL) {
  if (is.null(vcov_mat)) {
    sm <- summary(fit)$coefficients
    out <- as.data.table(sm, keep.rownames = "term")
    if (ncol(out) < 5) {
      stop("Unexpected coefficient table format.")
    }
    setnames(out, old = names(out)[2:5], new = c("beta", "se", "z", "p"))
  } else {
    beta <- coef(fit)
    vc <- diag(vcov_mat)
    vc <- vc[names(beta)]
    se <- sqrt(pmax(vc, 0))
    z <- beta / se
    p <- 2 * pnorm(abs(z), lower.tail = FALSE)
    out <- data.table(
      term = names(beta),
      beta = as.numeric(beta),
      se = as.numeric(se),
      z = as.numeric(z),
      p = as.numeric(p)
    )
  }
  out[, `:=`(
    OR = exp(beta),
    OR_low = exp(beta - 1.96 * se),
    OR_high = exp(beta + 1.96 * se)
  )]
  out[]
}

score_or <- or_table(fit_score)
score_no_egger_or <- or_table(fit_score_no_egger)
score_rr <- or_table(fit_score_rr)
score_assessable_or <- or_table(fit_score_assessable)
score_cc_or <- or_table(fit_score_cc)
score_dir_or <- or_table(fit_score_dir)
score_sig_or <- or_table(fit_score_sig)
score_clin_or <- or_table(fit_score_clin)
score_clin_rr <- or_table(fit_score_clin_rr)
score_clin_dataset_equal_or <- or_table(fit_score_clin_dataset_equal)
score_both_or <- or_table(fit_score_both)
score_both_rr <- or_table(fit_score_both_rr)
score_both_dataset_equal_or <- or_table(fit_score_both_dataset_equal)
score_comp_rr <- or_table(fit_score_comp)
score_cat_or <- or_table(fit_score_cat)
comp_or <- or_table(fit_components)
comp_no_logk_or <- or_table(fit_components_no_logk)
score_measure_or <- or_table(fit_score_measure)
score_dataset_equal_or <- or_table(fit_score_dataset_equal)
score_wb_or <- or_table(fit_score_within_between)

vcov_score_cl <- sandwich::vcovCL(fit_score, cluster = model_data$dataset, type = "HC0")
vcov_score_no_egger_cl <- sandwich::vcovCL(fit_score_no_egger, cluster = model_data$dataset, type = "HC0")
vcov_score_rr_cl <- sandwich::vcovCL(fit_score_rr, cluster = model_data$dataset, type = "HC0")
vcov_score_assessable_cl <- sandwich::vcovCL(fit_score_assessable, cluster = model_data_assessable$dataset, type = "HC0")
vcov_score_cc_cl <- sandwich::vcovCL(fit_score_cc, cluster = model_data_cc$dataset, type = "HC0")
vcov_score_dir_cl <- sandwich::vcovCL(fit_score_dir, cluster = model_data_dir$dataset, type = "HC0")
vcov_score_sig_cl <- sandwich::vcovCL(fit_score_sig, cluster = model_data_sig$dataset, type = "HC0")
vcov_score_clin_cl <- sandwich::vcovCL(fit_score_clin, cluster = model_data_clin$dataset, type = "HC0")
vcov_score_clin_rr_cl <- sandwich::vcovCL(fit_score_clin_rr, cluster = model_data_clin$dataset, type = "HC0")
vcov_score_clin_dataset_equal_cl <- sandwich::vcovCL(fit_score_clin_dataset_equal, cluster = model_data_clin$dataset, type = "HC0")
vcov_score_both_cl <- sandwich::vcovCL(fit_score_both, cluster = model_data_both$dataset, type = "HC0")
vcov_score_both_rr_cl <- sandwich::vcovCL(fit_score_both_rr, cluster = model_data_both$dataset, type = "HC0")
vcov_score_both_dataset_equal_cl <- sandwich::vcovCL(fit_score_both_dataset_equal, cluster = model_data_both$dataset, type = "HC0")
vcov_score_comp_cl <- sandwich::vcovCL(fit_score_comp, cluster = model_data_comp$dataset, type = "HC0")
vcov_score_cat_cl <- sandwich::vcovCL(fit_score_cat, cluster = model_data$dataset, type = "HC0")
vcov_comp_cl <- sandwich::vcovCL(fit_components, cluster = model_data$dataset, type = "HC0")
vcov_comp_no_logk_cl <- sandwich::vcovCL(fit_components_no_logk, cluster = model_data$dataset, type = "HC0")
vcov_score_measure_cl <- sandwich::vcovCL(fit_score_measure, cluster = model_data$dataset, type = "HC0")
vcov_score_dataset_equal_cl <- sandwich::vcovCL(fit_score_dataset_equal, cluster = model_data$dataset, type = "HC0")
vcov_score_measure_int_cl <- sandwich::vcovCL(fit_score_measure_interaction, cluster = model_data$dataset, type = "HC0")
vcov_score_wb_cl <- sandwich::vcovCL(fit_score_within_between, cluster = model_data$dataset, type = "HC0")
vcov_score_fe_lpm_cl <- sandwich::vcovCL(fit_score_fe_lpm, cluster = model_data$dataset, type = "HC0")
score_or_cluster <- or_table(fit_score, vcov_score_cl)
score_no_egger_or_cluster <- or_table(fit_score_no_egger, vcov_score_no_egger_cl)
score_rr_cluster <- or_table(fit_score_rr, vcov_score_rr_cl)
score_assessable_or_cluster <- or_table(fit_score_assessable, vcov_score_assessable_cl)
score_cc_or_cluster <- or_table(fit_score_cc, vcov_score_cc_cl)
score_dir_or_cluster <- or_table(fit_score_dir, vcov_score_dir_cl)
score_sig_or_cluster <- or_table(fit_score_sig, vcov_score_sig_cl)
score_clin_or_cluster <- or_table(fit_score_clin, vcov_score_clin_cl)
score_clin_rr_cluster <- or_table(fit_score_clin_rr, vcov_score_clin_rr_cl)
score_clin_dataset_equal_or_cluster <- or_table(fit_score_clin_dataset_equal, vcov_score_clin_dataset_equal_cl)
score_both_or_cluster <- or_table(fit_score_both, vcov_score_both_cl)
score_both_rr_cluster <- or_table(fit_score_both_rr, vcov_score_both_rr_cl)
score_both_dataset_equal_or_cluster <- or_table(fit_score_both_dataset_equal, vcov_score_both_dataset_equal_cl)
score_comp_rr_cluster <- or_table(fit_score_comp, vcov_score_comp_cl)
score_cat_or_cluster <- or_table(fit_score_cat, vcov_score_cat_cl)
comp_or_cluster <- or_table(fit_components, vcov_comp_cl)
comp_no_logk_or_cluster <- or_table(fit_components_no_logk, vcov_comp_no_logk_cl)
score_measure_or_cluster <- or_table(fit_score_measure, vcov_score_measure_cl)
score_dataset_equal_or_cluster <- or_table(fit_score_dataset_equal, vcov_score_dataset_equal_cl)

lincomb_or <- function(beta, vc, terms) {
  idx <- match(terms, names(beta))
  idx <- idx[is.finite(idx)]
  if (length(idx) == 0) {
    return(data.table(beta = NA_real_, se = NA_real_, OR = NA_real_, OR_low = NA_real_, OR_high = NA_real_, p = NA_real_))
  }
  w <- rep(1, length(idx))
  b <- sum(beta[idx] * w)
  v <- as.numeric(t(w) %*% vc[idx, idx, drop = FALSE] %*% w)
  se <- sqrt(max(v, 0))
  z <- b / se
  p <- 2 * pnorm(abs(z), lower.tail = FALSE)
  data.table(
    beta = b,
    se = se,
    OR = exp(b),
    OR_low = exp(b - 1.96 * se),
    OR_high = exp(b + 1.96 * se),
    p = p
  )
}

beta_int <- coef(fit_score_measure_interaction)
vc_int <- vcov_score_measure_int_cl
measure_levels <- levels(model_data$measure_factor)
ref_measure <- measure_levels[1]
measure_effects <- rbindlist(lapply(measure_levels, function(m) {
  int_term <- paste0("assumption_debt_score:measure_factor", m)
  terms <- "assumption_debt_score"
  if (m != ref_measure && int_term %in% names(beta_int)) {
    terms <- c(terms, int_term)
  }
  est <- lincomb_or(beta_int, vc_int, terms)
  cbind(data.table(
    measure = m,
    reference_measure = ref_measure
  ), est)
}), use.names = TRUE, fill = TRUE)

measure_interaction_lrt <- anova(fit_score_measure, fit_score_measure_interaction, test = "Chisq")
measure_interaction_test <- data.table(
  df = measure_interaction_lrt$Df[2],
  deviance = measure_interaction_lrt$Deviance[2],
  p_value = measure_interaction_lrt$`Pr(>Chi)`[2]
)
score_wb_or_cluster <- or_table(fit_score_within_between, vcov_score_wb_cl)

fe_lpm_beta <- coef(fit_score_fe_lpm)[["assumption_debt_score"]]
fe_lpm_se <- sqrt(max(vcov_score_fe_lpm_cl["assumption_debt_score", "assumption_debt_score"], 0))
fe_lpm_z <- fe_lpm_beta / fe_lpm_se
fe_lpm_p <- 2 * pnorm(abs(fe_lpm_z), lower.tail = FALSE)
fe_lpm_summary <- data.table(
  term = "assumption_debt_score",
  beta = fe_lpm_beta,
  se_cluster = fe_lpm_se,
  rd = fe_lpm_beta,
  rd_low = fe_lpm_beta - 1.96 * fe_lpm_se,
  rd_high = fe_lpm_beta + 1.96 * fe_lpm_se,
  p_cluster = fe_lpm_p,
  n_meta = nrow(model_data),
  n_datasets = uniqueN(model_data$dataset)
)

# Dataset-level aggregate sensitivity:
# model fragile counts per dataset against mean score and mean covariates.
dataset_level_data <- model_data[, .(
  n_meta = .N,
  fragile_count = sum(fragile_any),
  mean_score = mean(assumption_debt_score),
  mean_log_k = mean(log_k),
  mean_abs_estimate = mean(abs_estimate),
  mean_tau2_capped = mean(tau2_capped)
), by = dataset]
fit_dataset_level <- glm(
  cbind(fragile_count, n_meta - fragile_count) ~
    mean_score + mean_log_k + mean_abs_estimate + mean_tau2_capped,
  data = dataset_level_data,
  family = binomial()
)
dataset_level_or <- or_table(fit_dataset_level)

# Sensitivity: sample one analysis per dataset repeatedly to reduce within-dataset dependence.
set.seed(42)
n_boot <- 400
boot_beta <- numeric(n_boot)
for (b in seq_len(n_boot)) {
  idx <- model_data[, .I[sample.int(.N, 1)], by = dataset]$V1
  d_b <- model_data[idx]
  fit_b <- tryCatch(
    glm(
      fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
      data = d_b, family = binomial()
    ),
    error = function(e) NULL
  )
  boot_beta[b] <- if (is.null(fit_b)) NA_real_ else coef(fit_b)[["assumption_debt_score"]]
}
boot_beta <- boot_beta[is.finite(boot_beta)]
boot_summary <- data.table(
  n_boot = n_boot,
  n_success = length(boot_beta),
  beta_median = median(boot_beta),
  beta_q025 = quantile(boot_beta, 0.025),
  beta_q975 = quantile(boot_beta, 0.975),
  OR_median = exp(median(boot_beta)),
  OR_q025 = exp(quantile(boot_beta, 0.025)),
  OR_q975 = exp(quantile(boot_beta, 0.975))
)

# Sensitivity: leave-one-dataset-out influence on main assumption_debt_score OR.
datasets <- sort(unique(model_data$dataset))
lodo <- rbindlist(lapply(datasets, function(ds) {
  d_sub <- model_data[dataset != ds]
  fit_sub <- tryCatch(
    glm(
      fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
      data = d_sub, family = binomial()
    ),
    error = function(e) NULL
  )
  if (is.null(fit_sub)) {
    return(data.table(dataset = ds, beta = NA_real_, OR = NA_real_))
  }
  b <- coef(fit_sub)[["assumption_debt_score"]]
  data.table(dataset = ds, beta = b, OR = exp(b))
}), use.names = TRUE, fill = TRUE)

lodo_summary <- lodo[is.finite(OR), .(
  n_datasets = .N,
  OR_min = min(OR),
  OR_q025 = quantile(OR, 0.025),
  OR_median = median(OR),
  OR_q975 = quantile(OR, 0.975),
  OR_max = max(OR)
)]

# Sensitivity: dataset-level bootstrap (resample datasets with replacement).
set.seed(777)
n_dsboot <- 300
ds_ids <- unique(model_data$dataset)
dsboot_beta <- numeric(n_dsboot)
for (b in seq_len(n_dsboot)) {
  sampled_ds <- sample(ds_ids, length(ds_ids), replace = TRUE)
  map <- data.table(dataset = sampled_ds, bs_id = seq_along(sampled_ds))
  d_b <- model_data[map, on = "dataset", allow.cartesian = TRUE, nomatch = 0L]
  fit_b <- tryCatch(
    glm(fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped, data = d_b, family = binomial()),
    error = function(e) NULL
  )
  dsboot_beta[b] <- if (is.null(fit_b)) NA_real_ else coef(fit_b)[["assumption_debt_score"]]
}
dsboot_beta <- dsboot_beta[is.finite(dsboot_beta)]
dataset_bootstrap_summary <- data.table(
  n_boot = n_dsboot,
  n_success = length(dsboot_beta),
  beta_median = median(dsboot_beta),
  beta_q025 = quantile(dsboot_beta, 0.025),
  beta_q975 = quantile(dsboot_beta, 0.975),
  OR_median = exp(median(dsboot_beta)),
  OR_q025 = exp(quantile(dsboot_beta, 0.025)),
  OR_q975 = exp(quantile(dsboot_beta, 0.975))
)

# Threshold sensitivity: vary sparse-k and high-heterogeneity cutoffs.
k_thresholds <- c(7L, 10L, 15L)
i2_thresholds <- c(40, 50, 60)
threshold_grid <- CJ(k_threshold = k_thresholds, i2_threshold = i2_thresholds)

threshold_sensitivity <- rbindlist(lapply(seq_len(nrow(threshold_grid)), function(i) {
  kt <- threshold_grid$k_threshold[i]
  it <- threshold_grid$i2_threshold[i]
  d_tmp <- copy(model_data)
  d_tmp[, sparse_k_t := as.integer(k < kt)]
  d_tmp[, high_het_t := as.integer(I2 >= it)]
  d_tmp[, score_t := sparse_k_t + high_het_t + small_study_signal + dominance_signal]

  fit_t <- tryCatch(
    glm(fragile_any ~ score_t + log_k + abs_estimate + tau2_capped, data = d_tmp, family = binomial()),
    error = function(e) NULL
  )
  if (is.null(fit_t)) {
    return(data.table(k_threshold = kt, i2_threshold = it, OR = NA_real_, OR_low = NA_real_, OR_high = NA_real_, p = NA_real_,
                      OR_cluster = NA_real_, OR_cluster_low = NA_real_, OR_cluster_high = NA_real_, p_cluster = NA_real_))
  }

  sm <- summary(fit_t)$coefficients
  b <- sm["score_t", "Estimate"]
  se <- sm["score_t", "Std. Error"]
  p <- sm["score_t", "Pr(>|z|)"]

  vc <- sandwich::vcovCL(fit_t, cluster = d_tmp$dataset, type = "HC0")
  bcl <- coef(fit_t)[["score_t"]]
  secl <- sqrt(max(vc["score_t", "score_t"], 0))
  zcl <- bcl / secl
  pcl <- 2 * pnorm(abs(zcl), lower.tail = FALSE)

  data.table(
    k_threshold = kt,
    i2_threshold = it,
    OR = exp(b),
    OR_low = exp(b - 1.96 * se),
    OR_high = exp(b + 1.96 * se),
    p = p,
    OR_cluster = exp(bcl),
    OR_cluster_low = exp(bcl - 1.96 * secl),
    OR_cluster_high = exp(bcl + 1.96 * secl),
    p_cluster = pcl
  )
}), use.names = TRUE, fill = TRUE)

threshold_summary <- threshold_sensitivity[is.finite(OR_cluster), .(
  n_models = .N,
  OR_cluster_min = min(OR_cluster),
  OR_cluster_q025 = quantile(OR_cluster, 0.025),
  OR_cluster_median = median(OR_cluster),
  OR_cluster_q975 = quantile(OR_cluster, 0.975),
  OR_cluster_max = max(OR_cluster)
)]

# Threshold sensitivity: vary dominance cutoff in the score definition.
dominance_thresholds <- c(0.40, 0.50, 0.60)
dominance_threshold_sensitivity <- rbindlist(lapply(dominance_thresholds, function(dt) {
  d_tmp <- copy(model_data)
  d_tmp[, dominance_signal_t := as.integer(!is.na(max_weight_share) & max_weight_share >= dt)]
  d_tmp[, score_t := sparse_k + high_heterogeneity + small_study_signal + dominance_signal_t]

  fit_t <- tryCatch(
    glm(fragile_any ~ score_t + log_k + abs_estimate + tau2_capped, data = d_tmp, family = binomial()),
    error = function(e) NULL
  )
  if (is.null(fit_t)) {
    return(data.table(
      dominance_threshold = dt, OR = NA_real_, OR_low = NA_real_, OR_high = NA_real_, p = NA_real_,
      OR_cluster = NA_real_, OR_cluster_low = NA_real_, OR_cluster_high = NA_real_, p_cluster = NA_real_
    ))
  }

  sm <- summary(fit_t)$coefficients
  b <- sm["score_t", "Estimate"]
  se <- sm["score_t", "Std. Error"]
  p <- sm["score_t", "Pr(>|z|)"]

  vc <- sandwich::vcovCL(fit_t, cluster = d_tmp$dataset, type = "HC0")
  bcl <- coef(fit_t)[["score_t"]]
  secl <- sqrt(max(vc["score_t", "score_t"], 0))
  zcl <- bcl / secl
  pcl <- 2 * pnorm(abs(zcl), lower.tail = FALSE)

  data.table(
    dominance_threshold = dt,
    OR = exp(b),
    OR_low = exp(b - 1.96 * se),
    OR_high = exp(b + 1.96 * se),
    p = p,
    OR_cluster = exp(bcl),
    OR_cluster_low = exp(bcl - 1.96 * secl),
    OR_cluster_high = exp(bcl + 1.96 * secl),
    p_cluster = pcl
  )
}), use.names = TRUE, fill = TRUE)

dominance_threshold_summary <- dominance_threshold_sensitivity[is.finite(OR_cluster), .(
  n_models = .N,
  OR_cluster_min = min(OR_cluster),
  OR_cluster_q025 = quantile(OR_cluster, 0.025),
  OR_cluster_median = median(OR_cluster),
  OR_cluster_q975 = quantile(OR_cluster, 0.975),
  OR_cluster_max = max(OR_cluster)
)]

# Threshold sensitivity: vary Egger p-value cutoff for small-study signal.
egger_thresholds <- c(0.05, 0.10, 0.20)
egger_threshold_sensitivity <- rbindlist(lapply(egger_thresholds, function(et) {
  d_tmp <- copy(model_data)
  d_tmp[, small_study_signal_t := as.integer(!is.na(egger_min_p) & k_diag >= 10 & egger_min_p < et)]
  d_tmp[, score_t := sparse_k + high_heterogeneity + small_study_signal_t + dominance_signal]

  fit_t <- tryCatch(
    glm(fragile_any ~ score_t + log_k + abs_estimate + tau2_capped, data = d_tmp, family = binomial()),
    error = function(e) NULL
  )
  if (is.null(fit_t)) {
    return(data.table(
      egger_p_threshold = et, OR = NA_real_, OR_low = NA_real_, OR_high = NA_real_, p = NA_real_,
      OR_cluster = NA_real_, OR_cluster_low = NA_real_, OR_cluster_high = NA_real_, p_cluster = NA_real_
    ))
  }

  sm <- summary(fit_t)$coefficients
  b <- sm["score_t", "Estimate"]
  se <- sm["score_t", "Std. Error"]
  p <- sm["score_t", "Pr(>|z|)"]

  vc <- sandwich::vcovCL(fit_t, cluster = d_tmp$dataset, type = "HC0")
  bcl <- coef(fit_t)[["score_t"]]
  secl <- sqrt(max(vc["score_t", "score_t"], 0))
  zcl <- bcl / secl
  pcl <- 2 * pnorm(abs(zcl), lower.tail = FALSE)

  data.table(
    egger_p_threshold = et,
    OR = exp(b),
    OR_low = exp(b - 1.96 * se),
    OR_high = exp(b + 1.96 * se),
    p = p,
    OR_cluster = exp(bcl),
    OR_cluster_low = exp(bcl - 1.96 * secl),
    OR_cluster_high = exp(bcl + 1.96 * secl),
    p_cluster = pcl
  )
}), use.names = TRUE, fill = TRUE)

egger_threshold_summary <- egger_threshold_sensitivity[is.finite(OR_cluster), .(
  n_models = .N,
  OR_cluster_min = min(OR_cluster),
  OR_cluster_q025 = quantile(OR_cluster, 0.025),
  OR_cluster_median = median(OR_cluster),
  OR_cluster_q975 = quantile(OR_cluster, 0.975),
  OR_cluster_max = max(OR_cluster)
)]

# High-leverage exclusion sensitivity.
# Exclude analyses with very high single-study dominance or extreme tau2 tail.
tau2_p99 <- quantile(model_data$tau2, 0.99, na.rm = TRUE)
model_data_leverage <- model_data[
  (is.na(max_weight_share) | max_weight_share < 0.70) &
    (is.na(tau2) | tau2 <= tau2_p99)
]
fit_score_leverage <- glm(
  fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
  data = model_data_leverage,
  family = binomial()
)
vcov_score_leverage_cl <- sandwich::vcovCL(fit_score_leverage, cluster = model_data_leverage$dataset, type = "HC0")
lev_sm <- summary(fit_score_leverage)$coefficients
lev_b <- lev_sm["assumption_debt_score", "Estimate"]
lev_se <- lev_sm["assumption_debt_score", "Std. Error"]
lev_p <- lev_sm["assumption_debt_score", "Pr(>|z|)"]
lev_bcl <- coef(fit_score_leverage)[["assumption_debt_score"]]
lev_secl <- sqrt(max(vcov_score_leverage_cl["assumption_debt_score", "assumption_debt_score"], 0))
lev_zcl <- lev_bcl / lev_secl
lev_pcl <- 2 * pnorm(abs(lev_zcl), lower.tail = FALSE)
high_leverage_summary <- data.table(
  n_meta_original = nrow(model_data),
  n_meta_retained = nrow(model_data_leverage),
  pct_retained = nrow(model_data_leverage) / nrow(model_data),
  OR = exp(lev_b),
  OR_low = exp(lev_b - 1.96 * lev_se),
  OR_high = exp(lev_b + 1.96 * lev_se),
  p = lev_p,
  OR_cluster = exp(lev_bcl),
  OR_cluster_low = exp(lev_bcl - 1.96 * lev_secl),
  OR_cluster_high = exp(lev_bcl + 1.96 * lev_secl),
  p_cluster = lev_pcl,
  dominance_cutoff = 0.70,
  tau2_cutoff_p = 0.99,
  tau2_cutoff_value = tau2_p99
)

# Extreme effect-size tail exclusion sensitivity.
abs_est_p99 <- quantile(model_data$abs_estimate, 0.99, na.rm = TRUE)
model_data_effect_tail <- model_data[abs_estimate <= abs_est_p99]
fit_score_effect_tail <- glm(
  fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
  data = model_data_effect_tail,
  family = binomial()
)
vcov_score_effect_tail_cl <- sandwich::vcovCL(fit_score_effect_tail, cluster = model_data_effect_tail$dataset, type = "HC0")
et_sm <- summary(fit_score_effect_tail)$coefficients
et_b <- et_sm["assumption_debt_score", "Estimate"]
et_se <- et_sm["assumption_debt_score", "Std. Error"]
et_p <- et_sm["assumption_debt_score", "Pr(>|z|)"]
et_bcl <- coef(fit_score_effect_tail)[["assumption_debt_score"]]
et_secl <- sqrt(max(vcov_score_effect_tail_cl["assumption_debt_score", "assumption_debt_score"], 0))
et_zcl <- et_bcl / et_secl
et_pcl <- 2 * pnorm(abs(et_zcl), lower.tail = FALSE)
effect_tail_sensitivity <- data.table(
  n_meta_original = nrow(model_data),
  n_meta_retained = nrow(model_data_effect_tail),
  pct_retained = nrow(model_data_effect_tail) / nrow(model_data),
  abs_estimate_cutoff_p = 0.99,
  abs_estimate_cutoff_value = abs_est_p99,
  OR = exp(et_b),
  OR_low = exp(et_b - 1.96 * et_se),
  OR_high = exp(et_b + 1.96 * et_se),
  p = et_p,
  OR_cluster = exp(et_bcl),
  OR_cluster_low = exp(et_bcl - 1.96 * et_secl),
  OR_cluster_high = exp(et_bcl + 1.96 * et_secl),
  p_cluster = et_pcl
)

# Non-sparse-events subset sensitivity.
model_data_non_sparse <- model_data[sparse_events_signal == 0]
fit_score_non_sparse <- glm(
  fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
  data = model_data_non_sparse,
  family = binomial()
)
vcov_score_non_sparse_cl <- sandwich::vcovCL(fit_score_non_sparse, cluster = model_data_non_sparse$dataset, type = "HC0")
ns_sm <- summary(fit_score_non_sparse)$coefficients
ns_b <- ns_sm["assumption_debt_score", "Estimate"]
ns_se <- ns_sm["assumption_debt_score", "Std. Error"]
ns_p <- ns_sm["assumption_debt_score", "Pr(>|z|)"]
ns_bcl <- coef(fit_score_non_sparse)[["assumption_debt_score"]]
ns_secl <- sqrt(max(vcov_score_non_sparse_cl["assumption_debt_score", "assumption_debt_score"], 0))
ns_zcl <- ns_bcl / ns_secl
ns_pcl <- 2 * pnorm(abs(ns_zcl), lower.tail = FALSE)
non_sparse_sensitivity <- data.table(
  n_meta_original = nrow(model_data),
  n_meta_subset = nrow(model_data_non_sparse),
  pct_subset = nrow(model_data_non_sparse) / nrow(model_data),
  n_datasets_subset = uniqueN(model_data_non_sparse$dataset),
  OR = exp(ns_b),
  OR_low = exp(ns_b - 1.96 * ns_se),
  OR_high = exp(ns_b + 1.96 * ns_se),
  p = ns_p,
  OR_cluster = exp(ns_bcl),
  OR_cluster_low = exp(ns_bcl - 1.96 * ns_secl),
  OR_cluster_high = exp(ns_bcl + 1.96 * ns_secl),
  p_cluster = ns_pcl
)

# Heterogeneity-present subset sensitivity (exclude I2 == 0 analyses).
model_data_i2pos <- model_data[I2 > 0]
fit_score_i2pos <- glm(
  fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
  data = model_data_i2pos,
  family = binomial()
)
vcov_score_i2pos_cl <- sandwich::vcovCL(fit_score_i2pos, cluster = model_data_i2pos$dataset, type = "HC0")
i2_sm <- summary(fit_score_i2pos)$coefficients
i2_b <- i2_sm["assumption_debt_score", "Estimate"]
i2_se <- i2_sm["assumption_debt_score", "Std. Error"]
i2_p <- i2_sm["assumption_debt_score", "Pr(>|z|)"]
i2_bcl <- coef(fit_score_i2pos)[["assumption_debt_score"]]
i2_secl <- sqrt(max(vcov_score_i2pos_cl["assumption_debt_score", "assumption_debt_score"], 0))
i2_zcl <- i2_bcl / i2_secl
i2_pcl <- 2 * pnorm(abs(i2_zcl), lower.tail = FALSE)
i2_positive_sensitivity <- data.table(
  n_meta_original = nrow(model_data),
  n_meta_subset = nrow(model_data_i2pos),
  pct_subset = nrow(model_data_i2pos) / nrow(model_data),
  n_datasets_subset = uniqueN(model_data_i2pos$dataset),
  OR = exp(i2_b),
  OR_low = exp(i2_b - 1.96 * i2_se),
  OR_high = exp(i2_b + 1.96 * i2_se),
  p = i2_p,
  OR_cluster = exp(i2_bcl),
  OR_cluster_low = exp(i2_bcl - 1.96 * i2_secl),
  OR_cluster_high = exp(i2_bcl + 1.96 * i2_secl),
  p_cluster = i2_pcl
)

# Tau2-capping sensitivity.
tau2_caps <- c(0.95, 0.99, 1.00)
tau2_cap_sensitivity <- rbindlist(lapply(tau2_caps, function(cap_q) {
  d_t <- copy(model_data)
  if (cap_q < 1) {
    d_t[, tau2_tmp := pmin(tau2, quantile(tau2, probs = cap_q, na.rm = TRUE))]
  } else {
    d_t[, tau2_tmp := tau2]
  }
  fit_t <- tryCatch(
    glm(fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_tmp, data = d_t, family = binomial()),
    error = function(e) NULL
  )
  if (is.null(fit_t)) {
    return(data.table(
      tau2_cap_quantile = cap_q,
      OR = NA_real_, OR_low = NA_real_, OR_high = NA_real_, p = NA_real_,
      OR_cluster = NA_real_, OR_cluster_low = NA_real_, OR_cluster_high = NA_real_, p_cluster = NA_real_
    ))
  }
  sm <- summary(fit_t)$coefficients
  b <- sm["assumption_debt_score", "Estimate"]
  se <- sm["assumption_debt_score", "Std. Error"]
  p <- sm["assumption_debt_score", "Pr(>|z|)"]
  vc <- sandwich::vcovCL(fit_t, cluster = d_t$dataset, type = "HC0")
  bcl <- coef(fit_t)[["assumption_debt_score"]]
  secl <- sqrt(max(vc["assumption_debt_score", "assumption_debt_score"], 0))
  zcl <- bcl / secl
  pcl <- 2 * pnorm(abs(zcl), lower.tail = FALSE)
  data.table(
    tau2_cap_quantile = cap_q,
    OR = exp(b),
    OR_low = exp(b - 1.96 * se),
    OR_high = exp(b + 1.96 * se),
    p = p,
    OR_cluster = exp(bcl),
    OR_cluster_low = exp(bcl - 1.96 * secl),
    OR_cluster_high = exp(bcl + 1.96 * secl),
    p_cluster = pcl
  )
}), use.names = TRUE, fill = TRUE)

tau2_cap_summary <- tau2_cap_sensitivity[is.finite(OR_cluster), .(
  n_models = .N,
  OR_cluster_min = min(OR_cluster),
  OR_cluster_q025 = quantile(OR_cluster, 0.025),
  OR_cluster_median = median(OR_cluster),
  OR_cluster_q975 = quantile(OR_cluster, 0.975),
  OR_cluster_max = max(OR_cluster)
)]

# Permutation sensitivity: shuffle score within dataset to break score-outcome link.
set.seed(321)
n_perm <- 300
perm_beta <- numeric(n_perm)
for (i in seq_len(n_perm)) {
  d_perm <- copy(model_data)
  d_perm[, score_perm := assumption_debt_score[sample.int(.N)], by = dataset]
  fit_perm <- tryCatch(
    glm(fragile_any ~ score_perm + log_k + abs_estimate + tau2_capped, data = d_perm, family = binomial()),
    error = function(e) NULL
  )
  perm_beta[i] <- if (is.null(fit_perm)) NA_real_ else coef(fit_perm)[["score_perm"]]
}
perm_beta <- perm_beta[is.finite(perm_beta)]
obs_beta <- coef(fit_score)[["assumption_debt_score"]]
perm_empirical_p <- mean(abs(perm_beta) >= abs(obs_beta))
permutation_summary <- data.table(
  n_perm = n_perm,
  n_success = length(perm_beta),
  observed_beta = obs_beta,
  observed_OR = exp(obs_beta),
  perm_beta_mean = mean(perm_beta),
  perm_beta_sd = sd(perm_beta),
  perm_beta_q025 = quantile(perm_beta, 0.025),
  perm_beta_q975 = quantile(perm_beta, 0.975),
  empirical_p_two_sided = perm_empirical_p
)

# Leave-one-measure-family-out sensitivity.
measure_levels_full <- sort(unique(model_data$measure))
lomo <- rbindlist(lapply(measure_levels_full, function(mdrop) {
  d_sub <- model_data[measure != mdrop]
  fit_sub <- tryCatch(
    glm(fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped, data = d_sub, family = binomial()),
    error = function(e) NULL
  )
  if (is.null(fit_sub)) {
    return(data.table(
      excluded_measure = mdrop, n_meta = nrow(d_sub), OR = NA_real_, OR_low = NA_real_, OR_high = NA_real_, p = NA_real_,
      OR_cluster = NA_real_, OR_cluster_low = NA_real_, OR_cluster_high = NA_real_, p_cluster = NA_real_
    ))
  }
  sm <- summary(fit_sub)$coefficients
  b <- sm["assumption_debt_score", "Estimate"]
  se <- sm["assumption_debt_score", "Std. Error"]
  p <- sm["assumption_debt_score", "Pr(>|z|)"]
  vc <- sandwich::vcovCL(fit_sub, cluster = d_sub$dataset, type = "HC0")
  bcl <- coef(fit_sub)[["assumption_debt_score"]]
  secl <- sqrt(max(vc["assumption_debt_score", "assumption_debt_score"], 0))
  zcl <- bcl / secl
  pcl <- 2 * pnorm(abs(zcl), lower.tail = FALSE)
  data.table(
    excluded_measure = mdrop,
    n_meta = nrow(d_sub),
    OR = exp(b),
    OR_low = exp(b - 1.96 * se),
    OR_high = exp(b + 1.96 * se),
    p = p,
    OR_cluster = exp(bcl),
    OR_cluster_low = exp(bcl - 1.96 * secl),
    OR_cluster_high = exp(bcl + 1.96 * secl),
    p_cluster = pcl
  )
}), use.names = TRUE, fill = TRUE)

lomo_summary <- lomo[is.finite(OR_cluster), .(
  n_models = .N,
  OR_cluster_min = min(OR_cluster),
  OR_cluster_q025 = quantile(OR_cluster, 0.025),
  OR_cluster_median = median(OR_cluster),
  OR_cluster_q975 = quantile(OR_cluster, 0.975),
  OR_cluster_max = max(OR_cluster)
)]

# Information-adequacy stratified sensitivity (k < 10 vs k >= 10).
fit_stratified_score <- function(d) {
  fit <- tryCatch(
    glm(fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped, data = d, family = binomial()),
    error = function(e) NULL
  )
  if (is.null(fit)) {
    return(data.table(
      beta = NA_real_, se = NA_real_, OR = NA_real_, OR_low = NA_real_, OR_high = NA_real_, p = NA_real_,
      beta_cluster = NA_real_, se_cluster = NA_real_, OR_cluster = NA_real_, OR_cluster_low = NA_real_,
      OR_cluster_high = NA_real_, p_cluster = NA_real_
    ))
  }
  sm <- summary(fit)$coefficients
  b <- sm["assumption_debt_score", "Estimate"]
  se <- sm["assumption_debt_score", "Std. Error"]
  p <- sm["assumption_debt_score", "Pr(>|z|)"]
  vc <- sandwich::vcovCL(fit, cluster = d$dataset, type = "HC0")
  bcl <- coef(fit)[["assumption_debt_score"]]
  secl <- sqrt(max(vc["assumption_debt_score", "assumption_debt_score"], 0))
  zcl <- bcl / secl
  pcl <- 2 * pnorm(abs(zcl), lower.tail = FALSE)
  data.table(
    beta = b, se = se, OR = exp(b), OR_low = exp(b - 1.96 * se), OR_high = exp(b + 1.96 * se), p = p,
    beta_cluster = bcl, se_cluster = secl, OR_cluster = exp(bcl),
    OR_cluster_low = exp(bcl - 1.96 * secl), OR_cluster_high = exp(bcl + 1.96 * secl), p_cluster = pcl
  )
}

d_k_lt10 <- model_data[k < 10]
d_k_ge10 <- model_data[k >= 10]
strata_effects <- rbindlist(list(
  cbind(data.table(stratum = "k_lt_10", n_meta = nrow(d_k_lt10), n_datasets = uniqueN(d_k_lt10$dataset)),
        fit_stratified_score(d_k_lt10)),
  cbind(data.table(stratum = "k_ge_10", n_meta = nrow(d_k_ge10), n_datasets = uniqueN(d_k_ge10$dataset)),
        fit_stratified_score(d_k_ge10))
), use.names = TRUE, fill = TRUE)

beta_lt <- strata_effects[stratum == "k_lt_10", beta_cluster]
se_lt <- strata_effects[stratum == "k_lt_10", se_cluster]
beta_ge <- strata_effects[stratum == "k_ge_10", beta_cluster]
se_ge <- strata_effects[stratum == "k_ge_10", se_cluster]
z_diff <- (beta_lt - beta_ge) / sqrt(se_lt^2 + se_ge^2)
p_diff <- 2 * pnorm(abs(z_diff), lower.tail = FALSE)
strata_difference <- data.table(
  contrast = "k_lt_10_vs_k_ge_10",
  beta_diff_cluster = beta_lt - beta_ge,
  z = z_diff,
  p_value = p_diff
)

# Large-review dominance sensitivity:
# Exclude datasets in the top decile by number of meta-analyses.
ds_size <- model_data[, .(n_meta = .N), by = dataset]
size_cutoff <- quantile(ds_size$n_meta, 0.90, na.rm = TRUE)
large_ds <- ds_size[n_meta >= size_cutoff, dataset]
model_data_no_large <- model_data[!dataset %in% large_ds]
fit_no_large <- glm(
  fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
  data = model_data_no_large,
  family = binomial()
)
sm_no_large <- summary(fit_no_large)$coefficients
b_no_large <- sm_no_large["assumption_debt_score", "Estimate"]
se_no_large <- sm_no_large["assumption_debt_score", "Std. Error"]
p_no_large <- sm_no_large["assumption_debt_score", "Pr(>|z|)"]
vc_no_large <- sandwich::vcovCL(fit_no_large, cluster = model_data_no_large$dataset, type = "HC0")
bcl_no_large <- coef(fit_no_large)[["assumption_debt_score"]]
secl_no_large <- sqrt(max(vc_no_large["assumption_debt_score", "assumption_debt_score"], 0))
zcl_no_large <- bcl_no_large / secl_no_large
pcl_no_large <- 2 * pnorm(abs(zcl_no_large), lower.tail = FALSE)
large_review_sensitivity <- data.table(
  cutoff_quantile = 0.90,
  size_cutoff = size_cutoff,
  n_datasets_excluded = length(large_ds),
  n_meta_original = nrow(model_data),
  n_meta_retained = nrow(model_data_no_large),
  pct_meta_retained = nrow(model_data_no_large) / nrow(model_data),
  OR = exp(b_no_large),
  OR_low = exp(b_no_large - 1.96 * se_no_large),
  OR_high = exp(b_no_large + 1.96 * se_no_large),
  p = p_no_large,
  OR_cluster = exp(bcl_no_large),
  OR_cluster_low = exp(bcl_no_large - 1.96 * secl_no_large),
  OR_cluster_high = exp(bcl_no_large + 1.96 * secl_no_large),
  p_cluster = pcl_no_large
)
large_review_excluded <- ds_size[dataset %in% large_ds][order(-n_meta)]

# Cumulative large-review removal curve.
ds_size_sorted <- ds_size[order(-n_meta)]
cum_drop_steps <- c(5L, 10L, 20L, 30L, 40L)
cum_drop_steps <- cum_drop_steps[cum_drop_steps < nrow(ds_size_sorted)]
large_review_cumulative <- rbindlist(lapply(cum_drop_steps, function(kdrop) {
  drop_ds <- ds_size_sorted[seq_len(kdrop), dataset]
  d_sub <- model_data[!dataset %in% drop_ds]
  fit_sub <- tryCatch(
    glm(fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped, data = d_sub, family = binomial()),
    error = function(e) NULL
  )
  if (is.null(fit_sub)) {
    return(data.table(
      n_datasets_excluded = kdrop,
      n_meta_retained = nrow(d_sub),
      pct_meta_retained = nrow(d_sub) / nrow(model_data),
      OR = NA_real_, OR_low = NA_real_, OR_high = NA_real_, p = NA_real_,
      OR_cluster = NA_real_, OR_cluster_low = NA_real_, OR_cluster_high = NA_real_, p_cluster = NA_real_
    ))
  }
  sm <- summary(fit_sub)$coefficients
  b <- sm["assumption_debt_score", "Estimate"]
  se <- sm["assumption_debt_score", "Std. Error"]
  p <- sm["assumption_debt_score", "Pr(>|z|)"]
  vc <- sandwich::vcovCL(fit_sub, cluster = d_sub$dataset, type = "HC0")
  bcl <- coef(fit_sub)[["assumption_debt_score"]]
  secl <- sqrt(max(vc["assumption_debt_score", "assumption_debt_score"], 0))
  zcl <- bcl / secl
  pcl <- 2 * pnorm(abs(zcl), lower.tail = FALSE)
  data.table(
    n_datasets_excluded = kdrop,
    n_meta_retained = nrow(d_sub),
    pct_meta_retained = nrow(d_sub) / nrow(model_data),
    OR = exp(b),
    OR_low = exp(b - 1.96 * se),
    OR_high = exp(b + 1.96 * se),
    p = p,
    OR_cluster = exp(bcl),
    OR_cluster_low = exp(bcl - 1.96 * secl),
    OR_cluster_high = exp(bcl + 1.96 * secl),
    p_cluster = pcl
  )
}), use.names = TRUE, fill = TRUE)

large_review_cumulative_summary <- large_review_cumulative[is.finite(OR_cluster), .(
  n_steps = .N,
  OR_cluster_min = min(OR_cluster),
  OR_cluster_q025 = quantile(OR_cluster, 0.025),
  OR_cluster_median = median(OR_cluster),
  OR_cluster_q975 = quantile(OR_cluster, 0.975),
  OR_cluster_max = max(OR_cluster),
  min_pct_retained = min(pct_meta_retained),
  max_pct_retained = max(pct_meta_retained)
)]

# Performance metrics for the primary model.
calc_auc <- function(actual, predicted) {
  valid <- is.finite(actual) & is.finite(predicted)
  if (sum(valid) < 10) return(NA_real_)
  a <- actual[valid]
  p <- predicted[valid]
  n_pos <- sum(a == 1)
  n_neg <- sum(a == 0)
  if (n_pos == 0 || n_neg == 0) return(NA_real_)
  ranks <- rank(p)
  (sum(ranks[a == 1]) - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)
}

pred_primary <- predict(fit_score, type = "response")
pred_primary <- pmin(pmax(pred_primary, 1e-8), 1 - 1e-8)
logit_pred <- qlogis(pred_primary)

cal_intercept_fit <- glm(model_data$fragile_any ~ 1 + offset(logit_pred), family = binomial())
cal_slope_fit <- glm(model_data$fragile_any ~ logit_pred, family = binomial())

# 5-fold cross-validated AUC (apparent-optimism check).
set.seed(123)
fold_id <- sample(rep(1:5, length.out = nrow(model_data)))
cv_pred <- rep(NA_real_, nrow(model_data))
for (fold in 1:5) {
  train <- model_data[fold_id != fold]
  test <- model_data[fold_id == fold]
  fit_cv <- glm(
    fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
    data = train,
    family = binomial()
  )
  cv_pred[fold_id == fold] <- predict(fit_cv, newdata = test, type = "response")
}
cv_pred <- pmin(pmax(cv_pred, 1e-8), 1 - 1e-8)
logit_cv_pred <- qlogis(cv_pred)
cal_intercept_cv_fit <- glm(model_data$fragile_any ~ 1 + offset(logit_cv_pred), family = binomial())
cal_slope_cv_fit <- glm(model_data$fragile_any ~ logit_cv_pred, family = binomial())

# Grouped 5-fold CV by dataset (prevents leakage across analyses from same review).
set.seed(124)
unique_ds <- unique(model_data$dataset)
ds_fold_map <- data.table(
  dataset = unique_ds,
  fold = sample(rep(1:5, length.out = length(unique_ds)))
)
model_data_cv_ds <- merge(model_data, ds_fold_map, by = "dataset", all.x = TRUE)
cv_pred_group <- rep(NA_real_, nrow(model_data_cv_ds))
for (fold_idx in 1:5) {
  train <- model_data_cv_ds[fold != fold_idx]
  test <- model_data_cv_ds[fold == fold_idx]
  fit_cv <- glm(
    fragile_any ~ assumption_debt_score + log_k + abs_estimate + tau2_capped,
    data = train,
    family = binomial()
  )
  cv_pred_group[model_data_cv_ds$fold == fold_idx] <- predict(fit_cv, newdata = test, type = "response")
}
cv_pred_group <- pmin(pmax(cv_pred_group, 1e-8), 1 - 1e-8)
logit_cv_pred_group <- qlogis(cv_pred_group)
cal_intercept_cv_group_fit <- glm(model_data_cv_ds$fragile_any ~ 1 + offset(logit_cv_pred_group), family = binomial())
cal_slope_cv_group_fit <- glm(model_data_cv_ds$fragile_any ~ logit_cv_pred_group, family = binomial())

perf_summary <- data.table(
  n_meta = nrow(model_data),
  auc_apparent = calc_auc(model_data$fragile_any, pred_primary),
  auc_cv_5fold = calc_auc(model_data$fragile_any, cv_pred),
  auc_cv_5fold_grouped = calc_auc(model_data_cv_ds$fragile_any, cv_pred_group),
  brier = mean((model_data$fragile_any - pred_primary)^2),
  calibration_intercept = coef(cal_intercept_fit)[1],
  calibration_slope = coef(cal_slope_fit)[2],
  calibration_intercept_cv_5fold = coef(cal_intercept_cv_fit)[1],
  calibration_slope_cv_5fold = coef(cal_slope_cv_fit)[2],
  calibration_intercept_cv_5fold_grouped = coef(cal_intercept_cv_group_fit)[1],
  calibration_slope_cv_5fold_grouped = coef(cal_slope_cv_group_fit)[2]
)

# Likelihood ratio test for nonlinearity of assumption_debt_score.
nonlinearity_test <- anova(fit_score, fit_score_cat, test = "Chisq")
nonlinearity_summary <- data.table(
  df = nonlinearity_test$Df[2],
  deviance = nonlinearity_test$Deviance[2],
  p_value = nonlinearity_test$`Pr(>Chi)`[2]
)

summary_table <- model_data[, .(
  n_meta = .N,
  fragile_rate = mean(fragile_any),
  direction_fragile_rate = mean(direction_fragile, na.rm = TRUE),
  sig_fragile_rate = mean(sig_fragile, na.rm = TRUE),
  mean_k = mean(k),
  median_k = median(k),
  median_I2 = median(I2, na.rm = TRUE),
  high_heterogeneity_rate = mean(high_heterogeneity),
  small_study_signal_rate = mean(small_study_signal, na.rm = TRUE),
  dominance_signal_rate = mean(dominance_signal, na.rm = TRUE),
  sparse_events_signal_rate = mean(sparse_events_signal, na.rm = TRUE),
  high_debt_rate = mean(high_debt),
  mean_assumption_debt = mean(assumption_debt_score)
)]

debt_gradient <- model_data[, .(
  n_meta = .N,
  fragile_rate = mean(fragile_any),
  median_k = median(k),
  median_I2 = median(I2, na.rm = TRUE)
), by = assumption_debt_score][order(assumption_debt_score)]

component_prevalence <- model_data[, lapply(.SD, mean), .SDcols = component_cols]
component_prevalence <- melt(component_prevalence, measure.vars = component_cols,
                             variable.name = "component", value.name = "prevalence")
component_prevalence <- rbind(
  component_prevalence,
  data.table(component = "sparse_events_signal", prevalence = mean(model_data$sparse_events_signal, na.rm = TRUE))
)

predictor_correlation <- as.data.table(cor(model_data[, .(
  sparse_k,
  high_heterogeneity,
  small_study_signal,
  dominance_signal,
  log_k,
  tau2_capped,
  abs_estimate
)]), keep.rownames = "term")

small_study_assessability <- data.table(
  n_meta = nrow(model_data),
  pct_k_ge_10 = mean(model_data$k >= 10),
  pct_small_study_signal_overall = mean(model_data$small_study_signal, na.rm = TRUE),
  pct_small_study_signal_among_k_ge_10 = mean(model_data[k >= 10]$small_study_signal, na.rm = TRUE)
)

fwrite(summary_table, file.path(out_dir, "assumption_debt_model_summary.csv"))
fwrite(debt_gradient, file.path(out_dir, "assumption_debt_by_score.csv"))
fwrite(component_prevalence, file.path(out_dir, "assumption_debt_components.csv"))
fwrite(predictor_correlation, file.path(out_dir, "assumption_debt_predictor_correlation.csv"))
fwrite(small_study_assessability, file.path(out_dir, "assumption_debt_small_study_assessability.csv"))
fwrite(perf_summary, file.path(out_dir, "assumption_debt_model_performance.csv"))
fwrite(nonlinearity_summary, file.path(out_dir, "assumption_debt_score_nonlinearity_test.csv"))
fwrite(score_or, file.path(out_dir, "assumption_debt_model_coefficients.csv"))
fwrite(score_no_egger_or, file.path(out_dir, "assumption_debt_model_coefficients_no_egger.csv"))
fwrite(score_rr, file.path(out_dir, "assumption_debt_model_coefficients_rr.csv"))
fwrite(score_assessable_or, file.path(out_dir, "assumption_debt_model_coefficients_assessable.csv"))
fwrite(score_cc_or, file.path(out_dir, "assumption_debt_model_coefficients_complete_case.csv"))
fwrite(score_dir_or, file.path(out_dir, "assumption_debt_model_coefficients_direction.csv"))
fwrite(score_sig_or, file.path(out_dir, "assumption_debt_model_coefficients_significance.csv"))
fwrite(score_clin_or, file.path(out_dir, "assumption_debt_model_coefficients_clinical.csv"))
fwrite(score_clin_rr, file.path(out_dir, "assumption_debt_model_coefficients_clinical_rr.csv"))
fwrite(score_clin_dataset_equal_or, file.path(out_dir, "assumption_debt_model_coefficients_clinical_dataset_equal_weight.csv"))
fwrite(score_both_or, file.path(out_dir, "assumption_debt_model_coefficients_both.csv"))
fwrite(score_both_rr, file.path(out_dir, "assumption_debt_model_coefficients_both_rr.csv"))
fwrite(score_both_dataset_equal_or, file.path(out_dir, "assumption_debt_model_coefficients_both_dataset_equal_weight.csv"))
fwrite(score_comp_rr, file.path(out_dir, "assumption_debt_model_coefficients_composite_count.csv"))
fwrite(score_cat_or, file.path(out_dir, "assumption_debt_model_coefficients_score_categorical.csv"))
fwrite(comp_or, file.path(out_dir, "assumption_debt_component_model_coefficients.csv"))
fwrite(comp_no_logk_or, file.path(out_dir, "assumption_debt_component_model_coefficients_no_logk.csv"))
fwrite(score_or_cluster, file.path(out_dir, "assumption_debt_model_coefficients_cluster.csv"))
fwrite(score_no_egger_or_cluster, file.path(out_dir, "assumption_debt_model_coefficients_no_egger_cluster.csv"))
fwrite(score_rr_cluster, file.path(out_dir, "assumption_debt_model_coefficients_rr_cluster.csv"))
fwrite(score_assessable_or_cluster, file.path(out_dir, "assumption_debt_model_coefficients_assessable_cluster.csv"))
fwrite(score_cc_or_cluster, file.path(out_dir, "assumption_debt_model_coefficients_complete_case_cluster.csv"))
fwrite(score_dir_or_cluster, file.path(out_dir, "assumption_debt_model_coefficients_direction_cluster.csv"))
fwrite(score_sig_or_cluster, file.path(out_dir, "assumption_debt_model_coefficients_significance_cluster.csv"))
fwrite(score_clin_or_cluster, file.path(out_dir, "assumption_debt_model_coefficients_clinical_cluster.csv"))
fwrite(score_clin_rr_cluster, file.path(out_dir, "assumption_debt_model_coefficients_clinical_rr_cluster.csv"))
fwrite(score_clin_dataset_equal_or_cluster, file.path(out_dir, "assumption_debt_model_coefficients_clinical_dataset_equal_weight_cluster.csv"))
fwrite(score_both_or_cluster, file.path(out_dir, "assumption_debt_model_coefficients_both_cluster.csv"))
fwrite(score_both_rr_cluster, file.path(out_dir, "assumption_debt_model_coefficients_both_rr_cluster.csv"))
fwrite(score_both_dataset_equal_or_cluster, file.path(out_dir, "assumption_debt_model_coefficients_both_dataset_equal_weight_cluster.csv"))
fwrite(score_comp_rr_cluster, file.path(out_dir, "assumption_debt_model_coefficients_composite_count_cluster.csv"))
fwrite(score_cat_or_cluster, file.path(out_dir, "assumption_debt_model_coefficients_score_categorical_cluster.csv"))
fwrite(comp_or_cluster, file.path(out_dir, "assumption_debt_component_model_coefficients_cluster.csv"))
fwrite(comp_no_logk_or_cluster, file.path(out_dir, "assumption_debt_component_model_coefficients_no_logk_cluster.csv"))
fwrite(score_measure_or, file.path(out_dir, "assumption_debt_model_coefficients_measure.csv"))
fwrite(score_measure_or_cluster, file.path(out_dir, "assumption_debt_model_coefficients_measure_cluster.csv"))
fwrite(score_dataset_equal_or, file.path(out_dir, "assumption_debt_model_coefficients_dataset_equal_weight.csv"))
fwrite(score_dataset_equal_or_cluster, file.path(out_dir, "assumption_debt_model_coefficients_dataset_equal_weight_cluster.csv"))
fwrite(measure_effects, file.path(out_dir, "assumption_debt_measure_specific_effects_cluster.csv"))
fwrite(measure_interaction_test, file.path(out_dir, "assumption_debt_measure_interaction_test.csv"))
fwrite(score_wb_or, file.path(out_dir, "assumption_debt_within_between_coefficients.csv"))
fwrite(score_wb_or_cluster, file.path(out_dir, "assumption_debt_within_between_coefficients_cluster.csv"))
fwrite(fe_lpm_summary, file.path(out_dir, "assumption_debt_fixed_effects_lpm.csv"))
fwrite(dataset_level_or, file.path(out_dir, "assumption_debt_dataset_level_model.csv"))
fwrite(boot_summary, file.path(out_dir, "assumption_debt_one_per_dataset_bootstrap.csv"))
fwrite(dataset_bootstrap_summary, file.path(out_dir, "assumption_debt_dataset_bootstrap_summary.csv"))
fwrite(lodo, file.path(out_dir, "assumption_debt_leave_one_dataset_out.csv"))
fwrite(lodo_summary, file.path(out_dir, "assumption_debt_leave_one_dataset_out_summary.csv"))
fwrite(threshold_sensitivity, file.path(out_dir, "assumption_debt_threshold_sensitivity.csv"))
fwrite(threshold_summary, file.path(out_dir, "assumption_debt_threshold_sensitivity_summary.csv"))
fwrite(dominance_threshold_sensitivity, file.path(out_dir, "assumption_debt_dominance_threshold_sensitivity.csv"))
fwrite(dominance_threshold_summary, file.path(out_dir, "assumption_debt_dominance_threshold_sensitivity_summary.csv"))
fwrite(egger_threshold_sensitivity, file.path(out_dir, "assumption_debt_egger_threshold_sensitivity.csv"))
fwrite(egger_threshold_summary, file.path(out_dir, "assumption_debt_egger_threshold_sensitivity_summary.csv"))
fwrite(tau2_cap_sensitivity, file.path(out_dir, "assumption_debt_tau2_cap_sensitivity.csv"))
fwrite(tau2_cap_summary, file.path(out_dir, "assumption_debt_tau2_cap_sensitivity_summary.csv"))
fwrite(high_leverage_summary, file.path(out_dir, "assumption_debt_high_leverage_sensitivity.csv"))
fwrite(effect_tail_sensitivity, file.path(out_dir, "assumption_debt_effect_tail_sensitivity.csv"))
fwrite(non_sparse_sensitivity, file.path(out_dir, "assumption_debt_non_sparse_events_sensitivity.csv"))
fwrite(i2_positive_sensitivity, file.path(out_dir, "assumption_debt_i2_positive_sensitivity.csv"))
fwrite(permutation_summary, file.path(out_dir, "assumption_debt_permutation_summary.csv"))
fwrite(lomo, file.path(out_dir, "assumption_debt_leave_one_measure_out.csv"))
fwrite(lomo_summary, file.path(out_dir, "assumption_debt_leave_one_measure_out_summary.csv"))
fwrite(strata_effects, file.path(out_dir, "assumption_debt_k_strata_effects.csv"))
fwrite(strata_difference, file.path(out_dir, "assumption_debt_k_strata_difference_test.csv"))
fwrite(large_review_sensitivity, file.path(out_dir, "assumption_debt_large_review_sensitivity.csv"))
fwrite(large_review_excluded, file.path(out_dir, "assumption_debt_large_review_excluded_datasets.csv"))
fwrite(large_review_cumulative, file.path(out_dir, "assumption_debt_large_review_cumulative_sensitivity.csv"))
fwrite(large_review_cumulative_summary, file.path(out_dir, "assumption_debt_large_review_cumulative_summary.csv"))

score_term <- score_or[term == "assumption_debt_score"]
score_term_no_egger <- score_no_egger_or[term == "assumption_debt_score_no_egger"]
score_term_rr <- score_rr[term == "assumption_debt_score"]
score_term_assessable <- score_assessable_or[term == "assumption_debt_score"]
score_term_cc <- score_cc_or[term == "assumption_debt_score"]
score_term_cluster <- score_or_cluster[term == "assumption_debt_score"]
score_term_no_egger_cluster <- score_no_egger_or_cluster[term == "assumption_debt_score_no_egger"]
score_term_rr_cluster <- score_rr_cluster[term == "assumption_debt_score"]
score_term_assessable_cluster <- score_assessable_or_cluster[term == "assumption_debt_score"]
score_term_cc_cluster <- score_cc_or_cluster[term == "assumption_debt_score"]
score_term_dir <- score_dir_or[term == "assumption_debt_score"]
score_term_sig <- score_sig_or[term == "assumption_debt_score"]
score_term_clin <- score_clin_or[term == "assumption_debt_score"]
score_term_clin_rr <- score_clin_rr[term == "assumption_debt_score"]
score_term_clin_dataset_equal <- score_clin_dataset_equal_or[term == "assumption_debt_score"]
score_term_both <- score_both_or[term == "assumption_debt_score"]
score_term_both_rr <- score_both_rr[term == "assumption_debt_score"]
score_term_both_dataset_equal <- score_both_dataset_equal_or[term == "assumption_debt_score"]
score_term_comp <- score_comp_rr[term == "assumption_debt_score"]
score_term_dir_cluster <- score_dir_or_cluster[term == "assumption_debt_score"]
score_term_sig_cluster <- score_sig_or_cluster[term == "assumption_debt_score"]
score_term_clin_cluster <- score_clin_or_cluster[term == "assumption_debt_score"]
score_term_clin_rr_cluster <- score_clin_rr_cluster[term == "assumption_debt_score"]
score_term_clin_dataset_equal_cluster <- score_clin_dataset_equal_or_cluster[term == "assumption_debt_score"]
score_term_both_cluster <- score_both_or_cluster[term == "assumption_debt_score"]
score_term_both_rr_cluster <- score_both_rr_cluster[term == "assumption_debt_score"]
score_term_both_dataset_equal_cluster <- score_both_dataset_equal_or_cluster[term == "assumption_debt_score"]
score_term_comp_cluster <- score_comp_rr_cluster[term == "assumption_debt_score"]
score_term_measure <- score_measure_or[term == "assumption_debt_score"]
score_term_measure_cluster <- score_measure_or_cluster[term == "assumption_debt_score"]
score_term_dataset_equal <- score_dataset_equal_or[term == "assumption_debt_score"]
score_term_dataset_equal_cluster <- score_dataset_equal_or_cluster[term == "assumption_debt_score"]
score_within_term <- score_wb_or[term == "score_within"]
score_between_term <- score_wb_or[term == "score_between"]
score_within_term_cluster <- score_wb_or_cluster[term == "score_within"]
score_between_term_cluster <- score_wb_or_cluster[term == "score_between"]
score_term_dataset_level <- dataset_level_or[term == "mean_score"]
sparse_k_term_no_logk <- comp_no_logk_or[term == "sparse_k"]
sparse_k_term_no_logk_cluster <- comp_no_logk_or_cluster[term == "sparse_k"]
if (nrow(score_term) != 1) {
  stop("Model term assumption_debt_score not found.")
}
if (nrow(score_term_cluster) != 1) {
  stop("Clustered model term assumption_debt_score not found.")
}
if (nrow(score_term_no_egger) != 1 || nrow(score_term_no_egger_cluster) != 1) {
  stop("No-Egger score model term assumption_debt_score_no_egger not found.")
}
if (nrow(score_term_assessable) != 1 || nrow(score_term_assessable_cluster) != 1) {
  stop("Assessable-subset model term assumption_debt_score not found.")
}
if (nrow(score_term_rr) != 1 || nrow(score_term_rr_cluster) != 1) {
  stop("RR sensitivity model term assumption_debt_score not found.")
}
if (nrow(score_term_cc) != 1 || nrow(score_term_cc_cluster) != 1) {
  stop("Complete-case model term assumption_debt_score not found.")
}
if (nrow(score_term_dir) != 1 || nrow(score_term_sig) != 1 || nrow(score_term_clin) != 1 || nrow(score_term_clin_rr) != 1 ||
    nrow(score_term_clin_dataset_equal) != 1 || nrow(score_term_both) != 1 ||
    nrow(score_term_both_rr) != 1 || nrow(score_term_both_dataset_equal) != 1 || nrow(score_term_comp) != 1 ||
    nrow(score_term_dir_cluster) != 1 || nrow(score_term_sig_cluster) != 1 || nrow(score_term_clin_cluster) != 1 ||
    nrow(score_term_clin_rr_cluster) != 1 || nrow(score_term_clin_dataset_equal_cluster) != 1 ||
    nrow(score_term_both_cluster) != 1 || nrow(score_term_both_rr_cluster) != 1 ||
    nrow(score_term_both_dataset_equal_cluster) != 1 || nrow(score_term_comp_cluster) != 1) {
  stop("Outcome-specific model term assumption_debt_score not found.")
}
if (nrow(score_term_measure) != 1 || nrow(score_term_measure_cluster) != 1) {
  stop("Measure-adjusted model term assumption_debt_score not found.")
}
if (nrow(score_term_dataset_equal) != 1 || nrow(score_term_dataset_equal_cluster) != 1) {
  stop("Dataset-equal weighted model term assumption_debt_score not found.")
}
if (nrow(score_within_term) != 1 || nrow(score_within_term_cluster) != 1 ||
    nrow(score_between_term) != 1 || nrow(score_between_term_cluster) != 1) {
  stop("Within-between model terms not found.")
}
if (nrow(score_term_dataset_level) != 1) {
  stop("Dataset-level model term mean_score not found.")
}
if (nrow(sparse_k_term_no_logk) != 1 || nrow(sparse_k_term_no_logk_cluster) != 1) {
  stop("No-log_k component model term sparse_k not found.")
}
score_cat_terms <- score_cat_or[grepl("^factor\\(assumption_debt_score\\)", term)]
score_cat_terms_cluster <- score_cat_or_cluster[grepl("^factor\\(assumption_debt_score\\)", term)]

robustness_matrix <- data.table(
  check = c(
    "Primary model",
    "Primary model (no-Egger score)",
    "Primary model (no-Egger score) + cluster-robust",
    "Assessable subset (k >= 10)",
    "Assessable subset (k >= 10) + cluster-robust",
    "Primary model (modified Poisson RR)",
    "Primary model (modified Poisson RR) + cluster-robust",
    "Complete-case outcome",
    "Complete-case outcome + cluster-robust",
    "Direction fragility outcome",
    "Direction fragility outcome + cluster-robust",
    "Significance fragility outcome",
    "Significance fragility outcome + cluster-robust",
    "Clinical fragility outcome",
    "Clinical fragility outcome + cluster-robust",
    "Clinical fragility outcome (modified Poisson RR)",
    "Clinical fragility outcome (modified Poisson RR) + cluster-robust",
    "Clinical fragility outcome (dataset-equal weighting)",
    "Clinical fragility outcome (dataset-equal weighting) + cluster-robust",
    "Joint fragility outcome (direction AND significance)",
    "Joint fragility outcome + cluster-robust",
    "Joint fragility outcome (direction AND significance, modified Poisson RR)",
    "Joint fragility outcome (direction AND significance, modified Poisson RR) + cluster-robust",
    "Joint fragility outcome (direction AND significance, dataset-equal weighting)",
    "Joint fragility outcome (direction AND significance, dataset-equal weighting) + cluster-robust",
    "Composite fragility count outcome",
    "Composite fragility count outcome + cluster-robust",
    "Cluster-robust",
    "Measure-adjusted",
    "Measure-adjusted + cluster-robust",
    "Dataset-equal weighting",
    "Dataset-equal weighting + cluster-robust",
    "Within-between (within component)",
    "Within-between (between component)",
    "Dataset fixed-effects LPM (clustered RD)",
    "Dataset-level aggregate model",
    "Leave-one-measure-family-out",
    "Exclude largest reviews (top decile)",
    "Cumulative largest-review removal",
    "k-stratified (k < 10)",
    "k-stratified (k >= 10)",
    "One-per-dataset bootstrap",
    "Dataset-level bootstrap",
    "Leave-one-dataset-out",
    "Threshold-grid sensitivity",
    "Dominance-threshold sensitivity",
    "Egger-threshold sensitivity",
    "Tau2-cap sensitivity",
    "High-leverage exclusion",
    "Effect-size-tail exclusion",
    "Non-sparse-events subset",
    "Heterogeneity-present subset (I2 > 0)",
    "Permutation sensitivity"
  ),
  effect_metric = c(
    "OR",
    "OR",
    "OR_cluster",
    "OR",
    "OR_cluster",
    "RR",
    "RR_cluster",
    "OR",
    "OR_cluster",
    "OR",
    "OR_cluster",
    "OR",
    "OR_cluster",
    "OR",
    "OR_cluster",
    "RR",
    "RR_cluster",
    "OR",
    "OR_cluster",
    "OR",
    "OR_cluster",
    "RR",
    "RR_cluster",
    "OR",
    "OR_cluster",
    "RR",
    "RR_cluster",
    "OR",
    "OR",
    "OR",
    "OR",
    "OR_cluster",
    "OR_cluster",
    "OR_cluster",
    "RD_cluster",
    "OR_dataset",
    "OR_cluster_median",
    "OR_cluster",
    "OR_cluster_median",
    "OR_cluster",
    "OR_cluster",
    "OR_median",
    "OR_median",
    "OR_median",
    "OR_cluster_median",
    "OR_cluster_median",
    "OR_cluster_median",
    "OR_cluster_median",
    "OR_cluster",
    "OR_cluster",
    "OR_cluster",
    "OR_cluster",
    "empirical_p"
  ),
  estimate = c(
    score_term$OR,
    score_term_no_egger$OR,
    score_term_no_egger_cluster$OR,
    score_term_assessable$OR,
    score_term_assessable_cluster$OR,
    score_term_rr$OR,
    score_term_rr_cluster$OR,
    score_term_cc$OR,
    score_term_cc_cluster$OR,
    score_term_dir$OR,
    score_term_dir_cluster$OR,
    score_term_sig$OR,
    score_term_sig_cluster$OR,
    score_term_clin$OR,
    score_term_clin_cluster$OR,
    score_term_clin_rr$OR,
    score_term_clin_rr_cluster$OR,
    score_term_clin_dataset_equal$OR,
    score_term_clin_dataset_equal_cluster$OR,
    score_term_both$OR,
    score_term_both_cluster$OR,
    score_term_both_rr$OR,
    score_term_both_rr_cluster$OR,
    score_term_both_dataset_equal$OR,
    score_term_both_dataset_equal_cluster$OR,
    score_term_comp$OR,
    score_term_comp_cluster$OR,
    score_term_cluster$OR,
    score_term_measure$OR,
    score_term_measure_cluster$OR,
    score_term_dataset_equal$OR,
    score_term_dataset_equal_cluster$OR,
    score_within_term_cluster$OR,
    score_between_term_cluster$OR,
    fe_lpm_summary$rd,
    score_term_dataset_level$OR,
    lomo_summary$OR_cluster_median,
    large_review_sensitivity$OR_cluster,
    large_review_cumulative_summary$OR_cluster_median,
    strata_effects[stratum == "k_lt_10", OR_cluster],
    strata_effects[stratum == "k_ge_10", OR_cluster],
    boot_summary$OR_median,
    dataset_bootstrap_summary$OR_median,
    lodo_summary$OR_median,
    threshold_summary$OR_cluster_median,
    dominance_threshold_summary$OR_cluster_median,
    egger_threshold_summary$OR_cluster_median,
    tau2_cap_summary$OR_cluster_median,
    high_leverage_summary$OR_cluster,
    effect_tail_sensitivity$OR_cluster,
    non_sparse_sensitivity$OR_cluster,
    i2_positive_sensitivity$OR_cluster,
    permutation_summary$empirical_p_two_sided
  ),
  interval_low = c(
    score_term$OR_low,
    score_term_no_egger$OR_low,
    score_term_no_egger_cluster$OR_low,
    score_term_assessable$OR_low,
    score_term_assessable_cluster$OR_low,
    score_term_rr$OR_low,
    score_term_rr_cluster$OR_low,
    score_term_cc$OR_low,
    score_term_cc_cluster$OR_low,
    score_term_dir$OR_low,
    score_term_dir_cluster$OR_low,
    score_term_sig$OR_low,
    score_term_sig_cluster$OR_low,
    score_term_clin$OR_low,
    score_term_clin_cluster$OR_low,
    score_term_clin_rr$OR_low,
    score_term_clin_rr_cluster$OR_low,
    score_term_clin_dataset_equal$OR_low,
    score_term_clin_dataset_equal_cluster$OR_low,
    score_term_both$OR_low,
    score_term_both_cluster$OR_low,
    score_term_both_rr$OR_low,
    score_term_both_rr_cluster$OR_low,
    score_term_both_dataset_equal$OR_low,
    score_term_both_dataset_equal_cluster$OR_low,
    score_term_comp$OR_low,
    score_term_comp_cluster$OR_low,
    score_term_cluster$OR_low,
    score_term_measure$OR_low,
    score_term_measure_cluster$OR_low,
    score_term_dataset_equal$OR_low,
    score_term_dataset_equal_cluster$OR_low,
    score_within_term_cluster$OR_low,
    score_between_term_cluster$OR_low,
    fe_lpm_summary$rd_low,
    score_term_dataset_level$OR_low,
    lomo_summary$OR_cluster_q025,
    large_review_sensitivity$OR_cluster_low,
    large_review_cumulative_summary$OR_cluster_q025,
    strata_effects[stratum == "k_lt_10", OR_cluster_low],
    strata_effects[stratum == "k_ge_10", OR_cluster_low],
    boot_summary$OR_q025,
    dataset_bootstrap_summary$OR_q025,
    lodo_summary$OR_q025,
    threshold_summary$OR_cluster_q025,
    dominance_threshold_summary$OR_cluster_q025,
    egger_threshold_summary$OR_cluster_q025,
    tau2_cap_summary$OR_cluster_q025,
    high_leverage_summary$OR_cluster_low,
    effect_tail_sensitivity$OR_cluster_low,
    non_sparse_sensitivity$OR_cluster_low,
    i2_positive_sensitivity$OR_cluster_low,
    NA_real_
  ),
  interval_high = c(
    score_term$OR_high,
    score_term_no_egger$OR_high,
    score_term_no_egger_cluster$OR_high,
    score_term_assessable$OR_high,
    score_term_assessable_cluster$OR_high,
    score_term_rr$OR_high,
    score_term_rr_cluster$OR_high,
    score_term_cc$OR_high,
    score_term_cc_cluster$OR_high,
    score_term_dir$OR_high,
    score_term_dir_cluster$OR_high,
    score_term_sig$OR_high,
    score_term_sig_cluster$OR_high,
    score_term_clin$OR_high,
    score_term_clin_cluster$OR_high,
    score_term_clin_rr$OR_high,
    score_term_clin_rr_cluster$OR_high,
    score_term_clin_dataset_equal$OR_high,
    score_term_clin_dataset_equal_cluster$OR_high,
    score_term_both$OR_high,
    score_term_both_cluster$OR_high,
    score_term_both_rr$OR_high,
    score_term_both_rr_cluster$OR_high,
    score_term_both_dataset_equal$OR_high,
    score_term_both_dataset_equal_cluster$OR_high,
    score_term_comp$OR_high,
    score_term_comp_cluster$OR_high,
    score_term_cluster$OR_high,
    score_term_measure$OR_high,
    score_term_measure_cluster$OR_high,
    score_term_dataset_equal$OR_high,
    score_term_dataset_equal_cluster$OR_high,
    score_within_term_cluster$OR_high,
    score_between_term_cluster$OR_high,
    fe_lpm_summary$rd_high,
    score_term_dataset_level$OR_high,
    lomo_summary$OR_cluster_q975,
    large_review_sensitivity$OR_cluster_high,
    large_review_cumulative_summary$OR_cluster_q975,
    strata_effects[stratum == "k_lt_10", OR_cluster_high],
    strata_effects[stratum == "k_ge_10", OR_cluster_high],
    boot_summary$OR_q975,
    dataset_bootstrap_summary$OR_q975,
    lodo_summary$OR_q975,
    threshold_summary$OR_cluster_q975,
    dominance_threshold_summary$OR_cluster_q975,
    egger_threshold_summary$OR_cluster_q975,
    tau2_cap_summary$OR_cluster_q975,
    high_leverage_summary$OR_cluster_high,
    effect_tail_sensitivity$OR_cluster_high,
    non_sparse_sensitivity$OR_cluster_high,
    i2_positive_sensitivity$OR_cluster_high,
    NA_real_
  ),
  p_value = c(
    score_term$p,
    score_term_no_egger$p,
    score_term_no_egger_cluster$p,
    score_term_assessable$p,
    score_term_assessable_cluster$p,
    score_term_rr$p,
    score_term_rr_cluster$p,
    score_term_cc$p,
    score_term_cc_cluster$p,
    score_term_dir$p,
    score_term_dir_cluster$p,
    score_term_sig$p,
    score_term_sig_cluster$p,
    score_term_clin$p,
    score_term_clin_cluster$p,
    score_term_clin_rr$p,
    score_term_clin_rr_cluster$p,
    score_term_clin_dataset_equal$p,
    score_term_clin_dataset_equal_cluster$p,
    score_term_both$p,
    score_term_both_cluster$p,
    score_term_both_rr$p,
    score_term_both_rr_cluster$p,
    score_term_both_dataset_equal$p,
    score_term_both_dataset_equal_cluster$p,
    score_term_comp$p,
    score_term_comp_cluster$p,
    score_term_cluster$p,
    score_term_measure$p,
    score_term_measure_cluster$p,
    score_term_dataset_equal$p,
    score_term_dataset_equal_cluster$p,
    score_within_term_cluster$p,
    score_between_term_cluster$p,
    fe_lpm_summary$p_cluster,
    score_term_dataset_level$p,
    NA_real_,
    large_review_sensitivity$p_cluster,
    NA_real_,
    strata_effects[stratum == "k_lt_10", p_cluster],
    strata_effects[stratum == "k_ge_10", p_cluster],
    NA_real_,
    NA_real_,
    NA_real_,
    NA_real_,
    NA_real_,
    NA_real_,
    NA_real_,
    high_leverage_summary$p_cluster,
    effect_tail_sensitivity$p_cluster,
    non_sparse_sensitivity$p_cluster,
    i2_positive_sensitivity$p_cluster,
    permutation_summary$empirical_p_two_sided
  )
)
fwrite(robustness_matrix, file.path(out_dir, "assumption_debt_robustness_matrix.csv"))

# Multiverse consistency summary across robustness specifications.
is_ratio_metric <- grepl("^(OR|RR)", robustness_matrix$effect_metric)
is_rd_metric <- robustness_matrix$effect_metric == "RD_cluster"
is_directional_metric <- is_ratio_metric | is_rd_metric

robustness_direction <- copy(robustness_matrix[is_directional_metric])
robustness_direction[, null_value := ifelse(effect_metric == "RD_cluster", 0, 1)]
robustness_direction[, direction_positive := estimate > null_value]
robustness_direction[, ci_supports_positive := !is.na(interval_low) & interval_low > null_value]

robustness_direction <- robustness_direction[order(estimate)]
robustness_direction[, specification_rank := .I]
fwrite(
  robustness_direction[, .(
    specification_rank, check, effect_metric, estimate, interval_low, interval_high,
    p_value, null_value, direction_positive, ci_supports_positive
  )],
  file.path(out_dir, "assumption_debt_specification_curve.csv")
)

multiverse_consistency <- data.table(
  total_robustness_checks = nrow(robustness_matrix),
  directional_checks = nrow(robustness_direction),
  directionally_positive_n = sum(robustness_direction$direction_positive, na.rm = TRUE),
  directionally_positive_pct = 100 * mean(robustness_direction$direction_positive, na.rm = TRUE),
  ci_supports_positive_n = sum(robustness_direction$ci_supports_positive, na.rm = TRUE),
  ci_supports_positive_pct = 100 * mean(robustness_direction$ci_supports_positive, na.rm = TRUE),
  pvalue_available_n = sum(!is.na(robustness_direction$p_value)),
  pvalue_lt_0_05_n = sum(robustness_direction$p_value < 0.05, na.rm = TRUE),
  pvalue_lt_0_05_pct_among_available =
    100 * mean(robustness_direction$p_value < 0.05, na.rm = TRUE)
)
fwrite(multiverse_consistency, file.path(out_dir, "assumption_debt_multiverse_consistency.csv"))

# Inferential summary: exact sign test for directional predominance across specifications.
sign_test <- binom.test(
  x = sum(robustness_direction$direction_positive, na.rm = TRUE),
  n = nrow(robustness_direction),
  p = 0.5,
  alternative = "greater"
)
multiverse_sign_test <- data.table(
  directional_checks = nrow(robustness_direction),
  directionally_positive_n = sum(robustness_direction$direction_positive, na.rm = TRUE),
  positive_share = mean(robustness_direction$direction_positive, na.rm = TRUE),
  null_positive_share = 0.5,
  sign_test_p_one_sided = sign_test$p.value,
  exact_ci_low = sign_test$conf.int[1],
  exact_ci_high = sign_test$conf.int[2]
)
fwrite(multiverse_sign_test, file.path(out_dir, "assumption_debt_multiverse_sign_test.csv"))

report_lines <- c(
  "# Assumption Debt Modeling on Pairwise70 (Cochrane)",
  "",
  sprintf("Analyzed meta-analyses: **%d**", nrow(model_data)),
  sprintf("Fragility rate (any): **%.1f%%**", 100 * summary_table$fragile_rate),
  sprintf("High assumption debt (score >= 2): **%.1f%%**", 100 * summary_table$high_debt_rate),
  "",
  "## Primary Model",
  "Outcome: `fragile_any`",
  "Predictors: `assumption_debt_score + log_k + abs_estimate + tau2_capped`",
  sprintf(
    "Per 1-point increase in Assumption Debt Score: OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    score_term$OR, score_term$OR_low, score_term$OR_high, score_term$p
  ),
  sprintf(
    "Assessability sensitivity (score excluding Egger component): OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g; cluster-robust OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    score_term_no_egger$OR, score_term_no_egger$OR_low, score_term_no_egger$OR_high, score_term_no_egger$p,
    score_term_no_egger_cluster$OR, score_term_no_egger_cluster$OR_low, score_term_no_egger_cluster$OR_high, score_term_no_egger_cluster$p
  ),
  sprintf(
    "Assessable-only subset (k >= 10): OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g; cluster-robust OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    score_term_assessable$OR, score_term_assessable$OR_low, score_term_assessable$OR_high, score_term_assessable$p,
    score_term_assessable_cluster$OR, score_term_assessable_cluster$OR_low, score_term_assessable_cluster$OR_high, score_term_assessable_cluster$p
  ),
  sprintf(
    "Binary modified-Poisson RR sensitivity: RR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g; cluster-robust RR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    score_term_rr$OR, score_term_rr$OR_low, score_term_rr$OR_high, score_term_rr$p,
    score_term_rr_cluster$OR, score_term_rr_cluster$OR_low, score_term_rr_cluster$OR_high, score_term_rr_cluster$p
  ),
  sprintf(
    "Complete-case fragility outcome estimate: OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    score_term_cc$OR, score_term_cc$OR_low, score_term_cc$OR_high, score_term_cc$p
  ),
  sprintf(
    "Complete-case + cluster-robust estimate: OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    score_term_cc_cluster$OR, score_term_cc_cluster$OR_low, score_term_cc_cluster$OR_high, score_term_cc_cluster$p
  ),
  sprintf(
    "Direction-fragility outcome sensitivity: OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g; cluster-robust OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    score_term_dir$OR, score_term_dir$OR_low, score_term_dir$OR_high, score_term_dir$p,
    score_term_dir_cluster$OR, score_term_dir_cluster$OR_low, score_term_dir_cluster$OR_high, score_term_dir_cluster$p
  ),
  sprintf(
    "Significance-fragility outcome sensitivity: OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g; cluster-robust OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    score_term_sig$OR, score_term_sig$OR_low, score_term_sig$OR_high, score_term_sig$p,
    score_term_sig_cluster$OR, score_term_sig_cluster$OR_low, score_term_sig_cluster$OR_high, score_term_sig_cluster$p
  ),
  sprintf(
    "Clinical-fragility outcome sensitivity: OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g; cluster-robust OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    score_term_clin$OR, score_term_clin$OR_low, score_term_clin$OR_high, score_term_clin$p,
    score_term_clin_cluster$OR, score_term_clin_cluster$OR_low, score_term_clin_cluster$OR_high, score_term_clin_cluster$p
  ),
  sprintf(
    "Clinical-fragility outcome modified-Poisson RR sensitivity: RR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g; cluster-robust RR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    score_term_clin_rr$OR, score_term_clin_rr$OR_low, score_term_clin_rr$OR_high, score_term_clin_rr$p,
    score_term_clin_rr_cluster$OR, score_term_clin_rr_cluster$OR_low, score_term_clin_rr_cluster$OR_high, score_term_clin_rr_cluster$p
  ),
  sprintf(
    "Clinical-fragility outcome dataset-equal weighting sensitivity: OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g; cluster-robust OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    score_term_clin_dataset_equal$OR, score_term_clin_dataset_equal$OR_low, score_term_clin_dataset_equal$OR_high, score_term_clin_dataset_equal$p,
    score_term_clin_dataset_equal_cluster$OR, score_term_clin_dataset_equal_cluster$OR_low, score_term_clin_dataset_equal_cluster$OR_high, score_term_clin_dataset_equal_cluster$p
  ),
  sprintf(
    "Joint-fragility outcome sensitivity (direction AND significance): OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g; cluster-robust OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    score_term_both$OR, score_term_both$OR_low, score_term_both$OR_high, score_term_both$p,
    score_term_both_cluster$OR, score_term_both_cluster$OR_low, score_term_both_cluster$OR_high, score_term_both_cluster$p
  ),
  sprintf(
    "Joint-fragility outcome modified-Poisson RR sensitivity: RR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g; cluster-robust RR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    score_term_both_rr$OR, score_term_both_rr$OR_low, score_term_both_rr$OR_high, score_term_both_rr$p,
    score_term_both_rr_cluster$OR, score_term_both_rr_cluster$OR_low, score_term_both_rr_cluster$OR_high, score_term_both_rr_cluster$p
  ),
  sprintf(
    "Joint-fragility outcome dataset-equal weighting sensitivity: OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g; cluster-robust OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    score_term_both_dataset_equal$OR, score_term_both_dataset_equal$OR_low, score_term_both_dataset_equal$OR_high, score_term_both_dataset_equal$p,
    score_term_both_dataset_equal_cluster$OR, score_term_both_dataset_equal_cluster$OR_low, score_term_both_dataset_equal_cluster$OR_high, score_term_both_dataset_equal_cluster$p
  ),
  sprintf(
    "Composite-fragility-count outcome sensitivity (quasipoisson RR): RR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g; cluster-robust RR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    score_term_comp$OR, score_term_comp$OR_low, score_term_comp$OR_high, score_term_comp$p,
    score_term_comp_cluster$OR, score_term_comp_cluster$OR_low, score_term_comp_cluster$OR_high, score_term_comp_cluster$p
  ),
  sprintf(
    "Cluster-robust (by dataset) estimate: OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    score_term_cluster$OR, score_term_cluster$OR_low, score_term_cluster$OR_high, score_term_cluster$p
  ),
  sprintf(
    "Measure-adjusted model estimate: OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    score_term_measure$OR, score_term_measure$OR_low, score_term_measure$OR_high, score_term_measure$p
  ),
  sprintf(
    "Measure-adjusted + cluster-robust estimate: OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    score_term_measure_cluster$OR, score_term_measure_cluster$OR_low, score_term_measure_cluster$OR_high, score_term_measure_cluster$p
  ),
  sprintf(
    "Dataset-equal weighting estimate: OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g; cluster-robust OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    score_term_dataset_equal$OR, score_term_dataset_equal$OR_low, score_term_dataset_equal$OR_high, score_term_dataset_equal$p,
    score_term_dataset_equal_cluster$OR, score_term_dataset_equal_cluster$OR_low, score_term_dataset_equal_cluster$OR_high, score_term_dataset_equal_cluster$p
  ),
  sprintf(
    "Measure interaction test (score x measure): LR p = %.4g; clustered measure-specific score ORs are exported for audit",
    measure_interaction_test$p_value
  ),
  sprintf(
    "Within-between decomposition: within-dataset OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g; between-dataset OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    score_within_term_cluster$OR, score_within_term_cluster$OR_low, score_within_term_cluster$OR_high, score_within_term_cluster$p,
    score_between_term_cluster$OR, score_between_term_cluster$OR_low, score_between_term_cluster$OR_high, score_between_term_cluster$p
  ),
  sprintf(
    "Dataset fixed-effects LPM sensitivity: RD per +1 score = **%.3f** (95%% CI %.3f to %.3f), p = %.4g",
    fe_lpm_summary$rd, fe_lpm_summary$rd_low, fe_lpm_summary$rd_high, fe_lpm_summary$p_cluster
  ),
  sprintf(
    "Dataset-level aggregate model (n=%d datasets): OR per +1 mean score = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    nrow(dataset_level_data), score_term_dataset_level$OR, score_term_dataset_level$OR_low,
    score_term_dataset_level$OR_high, score_term_dataset_level$p
  ),
  sprintf(
    "Leave-one-measure-family-out sensitivity: clustered OR median = **%.2f** (2.5%% to 97.5%%: %.2f to %.2f; min-max: %.2f to %.2f) across %d exclusions",
    lomo_summary$OR_cluster_median, lomo_summary$OR_cluster_q025, lomo_summary$OR_cluster_q975,
    lomo_summary$OR_cluster_min, lomo_summary$OR_cluster_max, as.integer(lomo_summary$n_models)
  ),
  sprintf(
    "Large-review dominance sensitivity (exclude top decile dataset sizes; %d datasets removed, retain %.1f%% meta-analyses): clustered OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    large_review_sensitivity$n_datasets_excluded, 100 * large_review_sensitivity$pct_meta_retained,
    large_review_sensitivity$OR_cluster, large_review_sensitivity$OR_cluster_low,
    large_review_sensitivity$OR_cluster_high, large_review_sensitivity$p_cluster
  ),
  sprintf(
    "Cumulative large-review removal (top 5/10/20/30/40 datasets): clustered OR median = **%.2f** (2.5%% to 97.5%%: %.2f to %.2f; range: %.2f to %.2f), retained-meta range %.1f%% to %.1f%%",
    large_review_cumulative_summary$OR_cluster_median, large_review_cumulative_summary$OR_cluster_q025,
    large_review_cumulative_summary$OR_cluster_q975, large_review_cumulative_summary$OR_cluster_min,
    large_review_cumulative_summary$OR_cluster_max,
    100 * large_review_cumulative_summary$min_pct_retained, 100 * large_review_cumulative_summary$max_pct_retained
  ),
  sprintf(
    "Information-adequacy strata: k < 10 clustered OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g; k >= 10 clustered OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g; beta-difference test p = %.4g",
    strata_effects[stratum == "k_lt_10", OR_cluster], strata_effects[stratum == "k_lt_10", OR_cluster_low],
    strata_effects[stratum == "k_lt_10", OR_cluster_high], strata_effects[stratum == "k_lt_10", p_cluster],
    strata_effects[stratum == "k_ge_10", OR_cluster], strata_effects[stratum == "k_ge_10", OR_cluster_low],
    strata_effects[stratum == "k_ge_10", OR_cluster_high], strata_effects[stratum == "k_ge_10", p_cluster],
    strata_difference$p_value
  ),
  sprintf(
    "One-analysis-per-dataset bootstrap sensitivity: OR median = **%.2f** (95%% empirical interval %.2f to %.2f), successful fits = %d/%d",
    boot_summary$OR_median, boot_summary$OR_q025, boot_summary$OR_q975,
    boot_summary$n_success, boot_summary$n_boot
  ),
  sprintf(
    "Dataset-level bootstrap sensitivity (%d reps): OR median = **%.2f** (95%% empirical interval %.2f to %.2f), successful fits = %d/%d",
    dataset_bootstrap_summary$n_boot, dataset_bootstrap_summary$OR_median,
    dataset_bootstrap_summary$OR_q025, dataset_bootstrap_summary$OR_q975,
    dataset_bootstrap_summary$n_success, dataset_bootstrap_summary$n_boot
  ),
  sprintf(
    "Leave-one-dataset-out sensitivity (n=%d datasets): OR median = **%.2f** (2.5%% to 97.5%%: %.2f to %.2f; min-max: %.2f to %.2f)",
    lodo_summary$n_datasets, lodo_summary$OR_median, lodo_summary$OR_q025, lodo_summary$OR_q975,
    lodo_summary$OR_min, lodo_summary$OR_max
  ),
  sprintf(
    "Functional-form test (score linear vs categorical): LR p = %.4g (df=%d)",
    nonlinearity_summary$p_value, as.integer(nonlinearity_summary$df)
  ),
  sprintf(
    "Threshold sensitivity (k cutoffs 7/10/15; I2 cutoffs 40/50/60): clustered OR median = **%.2f** (2.5%% to 97.5%%: %.2f to %.2f; min-max: %.2f to %.2f) across %d models",
    threshold_summary$OR_cluster_median, threshold_summary$OR_cluster_q025, threshold_summary$OR_cluster_q975,
    threshold_summary$OR_cluster_min, threshold_summary$OR_cluster_max, as.integer(threshold_summary$n_models)
  ),
  sprintf(
    "Dominance-threshold sensitivity (max weight cutoffs 0.40/0.50/0.60 in score): clustered OR median = **%.2f** (2.5%% to 97.5%%: %.2f to %.2f; min-max: %.2f to %.2f) across %d models",
    dominance_threshold_summary$OR_cluster_median, dominance_threshold_summary$OR_cluster_q025,
    dominance_threshold_summary$OR_cluster_q975, dominance_threshold_summary$OR_cluster_min,
    dominance_threshold_summary$OR_cluster_max, as.integer(dominance_threshold_summary$n_models)
  ),
  sprintf(
    "Egger-threshold sensitivity (small-study cutoffs p<0.05/0.10/0.20 in score): clustered OR median = **%.2f** (2.5%% to 97.5%%: %.2f to %.2f; min-max: %.2f to %.2f) across %d models",
    egger_threshold_summary$OR_cluster_median, egger_threshold_summary$OR_cluster_q025,
    egger_threshold_summary$OR_cluster_q975, egger_threshold_summary$OR_cluster_min,
    egger_threshold_summary$OR_cluster_max, as.integer(egger_threshold_summary$n_models)
  ),
  sprintf(
    "Tau2-cap sensitivity (cap quantiles 0.95/0.99/1.00): clustered OR median = **%.2f** (2.5%% to 97.5%%: %.2f to %.2f; min-max: %.2f to %.2f) across %d models",
    tau2_cap_summary$OR_cluster_median, tau2_cap_summary$OR_cluster_q025, tau2_cap_summary$OR_cluster_q975,
    tau2_cap_summary$OR_cluster_min, tau2_cap_summary$OR_cluster_max, as.integer(tau2_cap_summary$n_models)
  ),
  sprintf(
    "High-leverage exclusion sensitivity (retain %.1f%%; exclude max_weight_share >= 0.70 and tau2 > p99=%.3f): clustered OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    100 * high_leverage_summary$pct_retained, high_leverage_summary$tau2_cutoff_value,
    high_leverage_summary$OR_cluster, high_leverage_summary$OR_cluster_low, high_leverage_summary$OR_cluster_high,
    high_leverage_summary$p_cluster
  ),
  sprintf(
    "Effect-size-tail exclusion sensitivity (exclude abs_estimate > p99=%.3f; retain %.1f%%): clustered OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    effect_tail_sensitivity$abs_estimate_cutoff_value, 100 * effect_tail_sensitivity$pct_retained,
    effect_tail_sensitivity$OR_cluster, effect_tail_sensitivity$OR_cluster_low, effect_tail_sensitivity$OR_cluster_high,
    effect_tail_sensitivity$p_cluster
  ),
  sprintf(
    "Non-sparse-events subset sensitivity (n=%d; %.1f%% of analyses): clustered OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    non_sparse_sensitivity$n_meta_subset, 100 * non_sparse_sensitivity$pct_subset,
    non_sparse_sensitivity$OR_cluster, non_sparse_sensitivity$OR_cluster_low, non_sparse_sensitivity$OR_cluster_high,
    non_sparse_sensitivity$p_cluster
  ),
  sprintf(
    "Heterogeneity-present subset sensitivity (I2 > 0; n=%d; %.1f%%): clustered OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    i2_positive_sensitivity$n_meta_subset, 100 * i2_positive_sensitivity$pct_subset,
    i2_positive_sensitivity$OR_cluster, i2_positive_sensitivity$OR_cluster_low, i2_positive_sensitivity$OR_cluster_high,
    i2_positive_sensitivity$p_cluster
  ),
  sprintf(
    "Within-dataset permutation sensitivity (%d reps): observed OR = %.2f; permutation beta mean = %.4f (95%% perm interval %.4f to %.4f); empirical two-sided p = %.4f",
    permutation_summary$n_success, permutation_summary$observed_OR, permutation_summary$perm_beta_mean,
    permutation_summary$perm_beta_q025, permutation_summary$perm_beta_q975, permutation_summary$empirical_p_two_sided
  ),
  sprintf(
    "Primary model performance: apparent AUC = %.3f, 5-fold CV AUC = %.3f, grouped 5-fold CV AUC = %.3f, Brier = %.3f, in-sample calibration (intercept=%.3f, slope=%.3f), 5-fold CV calibration (intercept=%.3f, slope=%.3f), grouped 5-fold CV calibration (intercept=%.3f, slope=%.3f)",
    perf_summary$auc_apparent, perf_summary$auc_cv_5fold, perf_summary$auc_cv_5fold_grouped, perf_summary$brier,
    perf_summary$calibration_intercept, perf_summary$calibration_slope,
    perf_summary$calibration_intercept_cv_5fold, perf_summary$calibration_slope_cv_5fold,
    perf_summary$calibration_intercept_cv_5fold_grouped, perf_summary$calibration_slope_cv_5fold_grouped
  ),
  sprintf(
    "Component model (without log_k) for sparse_k: OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g; cluster-robust OR = **%.2f** (95%% CI %.2f to %.2f), p = %.4g",
    sparse_k_term_no_logk$OR, sparse_k_term_no_logk$OR_low, sparse_k_term_no_logk$OR_high, sparse_k_term_no_logk$p,
    sparse_k_term_no_logk_cluster$OR, sparse_k_term_no_logk_cluster$OR_low, sparse_k_term_no_logk_cluster$OR_high, sparse_k_term_no_logk_cluster$p
  ),
  "",
  "## Assumption Debt Components (prevalence)",
  sprintf("- sparse_k (k < 10): %.1f%%", 100 * component_prevalence[component == "sparse_k", prevalence]),
  sprintf("- high_heterogeneity (I2 >= 50): %.1f%%", 100 * component_prevalence[component == "high_heterogeneity", prevalence]),
  sprintf("- small_study_signal (Egger p < 0.10 with k >= 10): %.1f%%", 100 * component_prevalence[component == "small_study_signal", prevalence]),
  sprintf("- dominance_signal (max weight >= 50%%): %.1f%%", 100 * component_prevalence[component == "dominance_signal", prevalence]),
  sprintf("- sparse_events_signal (>0 sparse-event flags): %.1f%%", 100 * component_prevalence[component == "sparse_events_signal", prevalence]),
  sprintf("- predictor correlation sparse_k vs log_k: %.2f", predictor_correlation[term == "sparse_k"]$log_k),
  sprintf("- analyses with k >= 10 (small-study assessable): %.1f%%", 100 * small_study_assessability$pct_k_ge_10),
  sprintf("- small-study signal prevalence among k >= 10: %.1f%%", 100 * small_study_assessability$pct_small_study_signal_among_k_ge_10),
  "",
  "## Interpretation",
  "Higher assumption debt is associated with higher fragility risk in real Cochrane pairwise meta-analyses.",
  "This quantifies the proposed underdiagnosed issue: assumptions are often strained in ways that predict unstable conclusions.",
  "The association remains directionally consistent under cluster-robust and one-analysis-per-dataset sensitivity analyses.",
  "Within-between decomposition shows a positive but attenuated within-dataset association (imprecise) and a stronger between-dataset association, indicating potential contextual clustering while preserving directional coherence.",
  "Dataset fixed-effects sensitivity reaches the same directional conclusion on the risk-difference scale.",
  "Dataset-level aggregate modeling is also directionally concordant, supporting cross-review consistency while not replacing individual-analysis inference.",
  "The inverse sparse_k sign in the full component model is attributable to collinearity with log_k and reverses in the no-log_k sensitivity model.",
  "Model diagnostics indicate moderate discrimination with limited apparent optimism and acceptable out-of-fold calibration.",
  "Functional-form testing indicates departures from strict linearity of the score effect."
)

writeLines(report_lines, file.path(out_dir, "assumption_debt_report.md"))

cat("Assumption debt modeling complete.\n")
cat("Outputs written to analysis/output/.\n")
