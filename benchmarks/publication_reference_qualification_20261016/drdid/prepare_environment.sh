#!/bin/bash
# Pinned package adaptation only; no author analysis, simulation or model calls.
set -euo pipefail
umask 077
root="${1:?Supply the owned DR-DID preparation directory}"
expected_sha="${2:?Supply the frozen source-package SHA-256}"
module load R/4.4.2-gfbf-2024a
cd "$root"
printf '%s  %s\n' "$expected_sha" DRDID-pinned.tar.gz | sha256sum --check
test ! -e environment_complete.json
test ! -e library
mkdir library package_sources
export R_LIBS_USER="$root/library" PREPARATION_ROOT="$root"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MAKEFLAGS=-j2
Rscript --vanilla - <<'RSCRIPT'
root <- Sys.getenv("PREPARATION_ROOT")
needed <- c("trust", "BMisc", "Rcpp", "fastglm", "foreach", "doSNOW", "doRNG",
            "sem", "foreign", "readstata13", "matlib")
installed <- installed.packages()
missing <- setdiff(needed, rownames(installed))
if (length(missing)) {
  install.packages(missing, lib=Sys.getenv("R_LIBS_USER"), repos="https://cloud.r-project.org",
                   type="source", destdir=file.path(root, "package_sources"), Ncpus=2)
}
RSCRIPT
R CMD INSTALL --library="$root/library" DRDID-pinned.tar.gz
Rscript --vanilla - <<'RSCRIPT'
root <- Sys.getenv("PREPARATION_ROOT")
needed <- c("DRDID", "trust", "BMisc", "Rcpp", "fastglm", "foreach", "doSNOW", "doRNG",
            "sem", "foreign", "readstata13", "matlib")
for (package in needed) {
  if (!requireNamespace(package, quietly=TRUE)) stop("Missing required package: ", package)
}
stopifnot(packageVersion("DRDID") == package_version("1.3.0"),
          startsWith(normalizePath(find.package("DRDID")),
                     paste0(normalizePath(file.path(root, "library")), "/")))
installed <- installed.packages()
deps <- tools::package_dependencies(needed, db=installed,
  which=c("Depends", "Imports", "LinkingTo"), recursive=TRUE)
selected <- intersect(sort(unique(c(needed, unlist(deps, use.names=FALSE)))), rownames(installed))
write.csv(installed[selected, c("Package", "Version", "LibPath", "Built"), drop=FALSE],
          file.path(root, "resolved_packages.csv"), row.names=FALSE)
writeLines(capture.output(sessionInfo()), file.path(root, "setup_session.txt"))
writeLines('{"status":"IMPORTED","scientific_execution":false,"model_calls":0}',
           file.path(root, "environment_complete.json"))
RSCRIPT
find package_sources -type f -name '*.tar.gz' -exec sha256sum '{}' + > downloaded_packages.sha256
