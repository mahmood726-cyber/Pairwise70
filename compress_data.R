# Compress all .rda files in the data directory
setwd("C:/Users/user/OneDrive - NHS/Documents/Pairwise70")  # sentinel:skip-line P0-hardcoded-local-path

cat("Compressing data files with xz compression...\n")
tools::resaveRdaFiles("data", compress="xz")
cat("Data compression complete!\n")
