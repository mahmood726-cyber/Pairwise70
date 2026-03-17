#' TGEP Diagnostic Visualization (Base R)
source("C:/Users/user/OneDrive - NHS/Documents/Pairwise70/R/tgep_meta.R")

# Example with Cochrane data
load("C:/Users/user/OneDrive - NHS/Documents/Pairwise70/data/CD000028_pub4_data.rda")
dat <- CD000028_pub4_data[CD000028_pub4_data$Analysis.number == 1, ]
es <- metafor::escalc(measure="OR", ai=Experimental.cases, n1i=Experimental.N, ci=Control.cases, n2i=Control.N, data=dat)
es <- es[!is.na(es$yi), ]

res <- tgep_meta(es$yi, es$vi)

# Print Summary
cat("\n=== TGEP ENSEMBLE DIAGNOSTIC ===\n")
cat("Dataset: CD000028_pub4_data (k =", length(es$yi), ")\n\n")

cat("ENSEMBLE WEIGHTS:\n")
cat("----------------\n")
weights <- res$ensemble_weights
names(weights) <- names(res$guard_estimates)
print(round(weights, 3))

cat("\nGUARD ESTIMATES:\n")
cat("---------------\n")
guards <- res$guard_estimates
print(round(guards, 4))

cat("\nFINAL COMPARISON:\n")
cat("----------------\n")
reml <- as.numeric(metafor::rma(es$yi, es$vi)$beta)
cat(sprintf("Standard REML: %.4f\n", reml))
cat(sprintf("TGEP Ensemble: %.4f\n", res$estimate))
cat(sprintf("Difference:    %.4f (%.1f%%)\n", 
            res$estimate - reml, 
            abs(res$estimate - reml) / (abs(reml) + 1e-6) * 100))

# Simple Text Bar Chart
cat("\nWEIGHT DISTRIBUTION:\n")
for (i in 1:length(weights)) {
  bar <- paste0(rep("#", round(weights[i] * 20)), collapse = "")
  cat(sprintf("%-5s | %-20s (%.1f%%)\n", names(weights)[i], bar, weights[i]*100))
}
