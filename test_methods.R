#!/usr/bin/env Rscript

# Simple test of new methods
set.seed(123)
yi <- c(0.25, 0.30, 0.28, 0.35, 0.22, 0.31, 0.29, 0.33, 0.27, 0.26)
vi <- c(0.02, 0.01, 0.02, 0.01, 0.03, 0.02, 0.01, 0.02, 0.02, 0.01)

cat('Toy data: k =', length(yi), '\n')

# Source the methods
source('R/advanced_pooling_v4.R')

# Test WRD
cat('\nTesting WRD...\n')
result <- wrd_meta(yi, vi)
cat('WRD: Estimate =', result$estimate, 'SE =', result$se, '\n')

# Test RBM
cat('\nTesting RBM...\n')
result <- rbm_meta(yi, vi)
cat('RBM: Estimate =', result$estimate, 'SE =', result$se, '\n')

# Test EVE
cat('\nTesting EVE...\n')
result <- eve_meta(yi, vi)
cat('EVE: Estimate =', result$estimate, 'SE =', result$se, '\n')

# Test AEM
cat('\nTesting AEM...\n')
result <- aem_meta(yi, vi)
cat('AEM: Estimate =', result$estimate, 'SE =', result$se, '\n')

# Test SMS
cat('\nTesting SMS...\n')
result <- sms_meta(yi, vi)
cat('SMS: Estimate =', result$estimate, 'SE =', result$se, '\n')

cat('\n=== Basic tests passed! ===\n')
