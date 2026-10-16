#!/bin/bash
# Reference dependencies only. No author study, model call or source repair.
set -euo pipefail
umask 077
root="${1:?Supply the owned reference directory}"
module load R/4.4.2-gfbf-2024a
cd "$root"
printf '%s  %s\n' \
  87eec73481bf3ae6b2f3c9b863034dc09c94908f80f74f606386865828a08d29 reference_honestdid.tar.gz \
  c007bffb02feaa395163e9ea28dfe3fb479cb8cf26427569e2b91fe4becc6a91 lfe_3.1.1.tar.gz | sha256sum --check
test ! -e library
mkdir library
export REFERENCE_ROOT="$root" R_LIBS_USER="$root/library"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MAKEFLAGS=-j1
R CMD INSTALL --library="$root/library" lfe_3.1.1.tar.gz
R CMD INSTALL --library="$root/library" reference_honestdid.tar.gz
Rscript --vanilla - <<'RSCRIPT'
root <- Sys.getenv("REFERENCE_ROOT")
owned <- normalizePath(file.path(root, "library"))
stopifnot(packageVersion("HonestDiD") == package_version("0.2.0"),
          packageVersion("lfe") == package_version("3.1.1"))
for (p in c("HonestDiD", "lfe")) {
  stopifnot(startsWith(normalizePath(find.package(p)), paste0(owned, "/")))
}
library(HonestDiD)
library(lfe)
packages <- installed.packages()
deps <- tools::package_dependencies(c("HonestDiD", "lfe"), db=packages,
  which=c("Depends", "Imports", "LinkingTo"), recursive=TRUE)
selected <- sort(unique(c("HonestDiD", "lfe", unlist(deps, use.names=FALSE))))
selected <- intersect(selected, rownames(packages))
write.csv(packages[selected, c("Package", "Version", "LibPath", "Built"), drop=FALSE],
          file.path(root, "resolved_packages.csv"), row.names=FALSE)
writeLines(capture.output(sessionInfo()), file.path(root, "setup_session.txt"))
cat("Reference dependencies imported; no scientific source executed.\n")
RSCRIPT
