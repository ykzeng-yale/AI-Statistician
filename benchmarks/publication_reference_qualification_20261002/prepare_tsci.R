# Evaluator environment preparation only; never imported by the product.
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 1L)
root <- normalizePath(args[[1]], mustWork = TRUE)
lib <- file.path(root, "library")
downloads <- file.path(root, "dependencies")
stopifnot(dir.exists(lib), dir.exists(downloads))
.libPaths(lib, include.site = FALSE)
Sys.setenv(R_LIBS = lib, R_LIBS_USER = lib)
options(repos = c(CRAN = "https://cloud.r-project.org"), timeout = 180)

sources <- c(xgboost = "xgboost_1.7.7.1.tar.gz", fda = "fda_6.1.8.tar.gz",
             TSCI = "TSCI_3.0.5.tar.gz")
ap <- available.packages(type = "binary")
saveRDS(ap, file.path(root, "binary_package_index.rds"))
db <- ap
metadata <- file.path(root, "source_metadata")
dir.create(metadata)
for (name in names(sources)) {
  untar(file.path(root, "sources", sources[[name]]),
        files = paste0(name, "/DESCRIPTION"), exdir = metadata)
  description <- read.dcf(file.path(metadata, name, "DESCRIPTION"))[1L, ]
  row <- setNames(rep(NA_character_, ncol(db)), colnames(db))
  fields <- intersect(names(description), names(row))
  row[fields] <- description[fields]
  if (!name %in% rownames(db)) {
    db <- rbind(db, row)
    rownames(db)[nrow(db)] <- name
  } else db[name, ] <- row
}
roots <- c(names(sources), "ivmodel", "jsonlite")
deps <- tools::package_dependencies(roots, db = db,
                                   which = c("Depends", "Imports", "LinkingTo"), recursive = TRUE)
required <- sort(unique(c(roots, unlist(deps, use.names = FALSE))))
packages <- setdiff(required[required %in% rownames(ap)], names(sources))
downloaded <- download.packages(packages, destdir = downloads, available = ap, type = "binary")
stopifnot(setequal(downloaded[, 1], packages))
write.csv(ap[packages, c("Package", "Version", "Repository", "MD5sum")],
          file.path(root, "binary_resolution.csv"), row.names = FALSE)
install.packages(downloaded[, 2], repos = NULL, type = "binary", lib = lib)
for (name in names(sources)) {
  install.packages(file.path(root, "sources", sources[[name]]),
                   repos = NULL, type = "source", lib = lib)
  expected <- read.dcf(file.path(metadata, name, "DESCRIPTION"))[1L, "Version"]
  stopifnot(packageVersion(name, lib.loc = lib) == package_version(expected))
}
owned <- c(packages, names(sources))
locations <- vapply(owned, find.package, character(1), lib.loc = lib)
stopifnot(all(startsWith(normalizePath(locations), paste0(lib, "/"))))
stopifnot(all(vapply(required, requireNamespace, logical(1), quietly = TRUE)))
write.csv(installed.packages(lib.loc = lib)[, c("Package", "Version", "Built")],
          file.path(root, "installed_packages.csv"), row.names = FALSE)
writeLines(capture.output(sessionInfo()), file.path(root, "preparation_session.txt"))
cat("Prepared", length(owned), "reference packages in the owned library.\n")
