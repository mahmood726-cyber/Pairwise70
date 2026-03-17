# Real-world Impact Analysis: TGEP on Cochrane Data
library(metafor)
library(data.table)

# Source all required methods
source("C:/Users/user/OneDrive - NHS/Documents/Pairwise70/R/tgep_meta.R")
source("C:/Users/user/OneDrive - NHS/Documents/Pairwise70/R/grma_meta.R")
source("C:/Users/user/OneDrive - NHS/Documents/Pairwise70/R/advanced_pooling_v4.R")

cat("=== REAL-WORLD IMPACT ANALYSIS (TGEP) ===\n")

# 1. Select a random subset of datasets (e.g., 20)
data_files <- list.files("C:/Users/user/OneDrive - NHS/Documents/Pairwise70/data", pattern="\\.rda$", full.names=TRUE)
set.seed(20260214)
subset_files <- sample(data_files, 20)

impact_results <- list()

for (f in subset_files) {
  try({
    load(f)
    # Use basename and sub with escaped dots
    ds_name <- sub("\\.rda$", "", basename(f))
    df <- get(ds_name)
    
    # Process Analysis 1 only for speed
    ma_data <- df[df$Analysis.number == 1, ]
    if(nrow(ma_data) < 5) next
    
    # Calculate Log OR
    dat <- escalc(measure="OR", ai=Experimental.cases, n1i=Experimental.N,
                  ci=Control.cases, n2i=Control.N, data=ma_data)
    dat <- dat[!is.na(dat$yi) & !is.na(dat$vi), ]
    if(nrow(dat) < 5) next
    
    # REML
    fit_reml <- rma(dat$yi, dat$vi, method="REML")
    # TGEP
    fit_tgep <- tgep_meta(dat$yi, dat$vi, n_boot = 0)
    
    impact_results[[ds_name]] <- data.table(
      dataset = ds_name,
      k = nrow(dat),
      reml_est = as.numeric(fit_reml$beta),
      tgep_est = fit_tgep$estimate,
      reml_se = fit_reml$se,
      tgep_se = fit_tgep$se,
      abs_diff = abs(as.numeric(fit_reml$beta) - fit_tgep$estimate),
      rel_diff = abs(as.numeric(fit_reml$beta) - fit_tgep$estimate) / (abs(as.numeric(fit_reml$beta)) + 1e-6)
    )
    cat(".")
  }, silent = TRUE)
}

impact_dt <- rbindlist(impact_results)
cat("\n\nAnalysis Complete.\n")

if (nrow(impact_dt) > 0) {
    # Summary Stats
    summary_impact <- impact_dt[, .(
      N_Datasets = .N,
      Mean_Abs_Diff = mean(abs_diff),
      Median_Abs_Diff = median(abs_diff),
      Mean_Rel_Diff = mean(rel_diff),
      SE_Ratio = mean(tgep_se / (reml_se + 1e-12))
    )]

    print(summary_impact)

    # Significant Discrepancies
    cat("\nTop 5 Most Impacted Meta-Analyses (Largest relative change):\n")
    print(impact_dt[order(-rel_diff)][1:5])

    sink("C:/Users/user/Downloads/PoolingMethodology/Real_World_Impact_Summary.txt")
    cat("REAL-WORLD IMPACT ANALYSIS: TGEP VS REML\n")
    cat("========================================\n\n")
    print(summary_impact)
    cat("\nIndividual Dataset results:\n")
    print(impact_dt)
    sink()

    cat("\nSummary report saved to Downloads/PoolingMethodology/Real_World_Impact_Summary.txt\n")
} else {
    cat("No valid datasets analyzed.\n")
}
