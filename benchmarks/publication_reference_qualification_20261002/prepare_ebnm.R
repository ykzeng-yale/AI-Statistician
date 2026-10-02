# Evaluator environment preparation only; never imported by the product.
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 1L)
root <- normalizePath(args[[1]], mustWork = TRUE)
lib <- file.path(root, "library")
downloads <- file.path(root, "dependencies")
stopifnot(dir.exists(lib), dir.exists(downloads))
.libPaths(lib, include.site = FALSE)
options(repos = c(CRAN = "https://cloud.r-project.org"), timeout = 180)

ap <- available.packages(type = "binary")
saveRDS(ap, file.path(root, "binary_package_index.rds"))
roots <- c("tidyverse", "flashier", "ashr", "mixsqp", "truncnorm",
           "trust", "deconvolveR", "magrittr", "rlang", "dplyr", "ggplot2",
           "microbenchmark", "gt", "scales", "Rtsne", "ggrepel", "cowplot")
deps <- tools::package_dependencies(roots, db = ap,
                                   which = c("Depends", "Imports", "LinkingTo"),
                                   recursive = TRUE)
packages <- sort(unique(c(roots, unlist(deps, use.names = FALSE))))
packages <- setdiff(packages[packages %in% rownames(ap)], c("ebnm", "horseshoe"))
downloaded <- download.packages(packages, destdir = downloads,
                                available = ap, type = "binary")
stopifnot(setequal(downloaded[, 1], packages))
write.csv(ap[packages, c("Package", "Version", "Repository", "MD5sum")],
          file.path(root, "binary_resolution.csv"), row.names = FALSE)
install.packages(downloaded[, 2], repos = NULL, type = "binary", lib = lib)
install.packages(file.path(root, "sources", "horseshoe_0.2.0.tar.gz"),
                 repos = NULL, type = "source", lib = lib)
install.packages(file.path(root, "sources", "package.tar.gz"),
                 repos = NULL, type = "source", lib = lib)

required <- c(packages, "horseshoe", "ebnm")
locations <- vapply(required, find.package, character(1), lib.loc = lib)
stopifnot(all(startsWith(normalizePath(locations), paste0(lib, "/"))))
stopifnot(as.character(packageVersion("ebnm", lib.loc = lib)) == "1.1-38")
write.csv(installed.packages(lib.loc = lib)[, c("Package", "Version", "Built")],
          file.path(root, "installed_packages.csv"), row.names = FALSE)
writeLines(capture.output(sessionInfo()), file.path(root, "preparation_session.txt"))
cat("Prepared", length(required), "reference packages in the owned library.\n")
