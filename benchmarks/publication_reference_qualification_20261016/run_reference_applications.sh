#!/bin/bash
# Evaluator-side original applications; no model output or product source edits.
set -euo pipefail
umask 077
root="${1:?Supply the owned reference directory}"
module load R/4.4.2-gfbf-2024a
export R_LIBS_USER="$root/library"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
work="${2:-$root/applications_path_port_20261016}"
applications=("${@:3}")
if [[ "${#applications[@]}" -eq 0 ]]; then applications=(BenzartiCarloni LovenheimWillen); fi
mkdir "$work/execution"
cd "$work"
jq -r '.applications | to_entries[] | .key as $app |
  (.value.files[] | "\(.sha256)  \($app)/\(.path)"),
  (.value.same_byte_alias | "\(.sha256)  \($app)/\(.target)")' staged_inputs.json \
  | sha256sum --check
cd "$work/execution"
Rscript --vanilla - <<'RSCRIPT'
stopifnot(packageVersion("HonestDiD") == package_version("0.2.0"),
          packageVersion("lfe") == package_version("3.1.1"),
          packageVersion("latex2exp") == package_version("0.9.8"))
for (p in c("HonestDiD", "lfe", "latex2exp", "tidyverse", "here", "tictoc", "furrr", "glue", "haven")) {
  loadNamespace(p)
}
writeLines(capture.output(sessionInfo()), "preflight_session.txt")
write.csv(installed.packages()[, c("Package", "Version", "LibPath", "Built")],
          "packages.csv", row.names=FALSE)
RSCRIPT
overall=0
for app in "${applications[@]}"; do
  cd "$work/$app"
  printf '%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ) start $app" >> "$work/execution/events.txt"
  set +e
  REFERENCE_SESSION="$work/execution/$app.session.txt" \
  /usr/bin/time -v Rscript --vanilla -e \
    'set.seed(20261016); tryCatch(source(commandArgs(TRUE)[[1]], echo=TRUE), finally=writeLines(capture.output(sessionInfo()), Sys.getenv("REFERENCE_SESSION")))' \
    "Code/$app-Scripts/$app-Analysis.R" \
    > "$work/execution/$app.stdout.log" 2> "$work/execution/$app.stderr.log"
  code=$?
  set -e
  printf '%s\t%s\t%s\n' "$app" "$code" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$work/execution/exits.tsv"
  find Outputs Figures Temp -type f -print0 | sort -z | xargs -0 -r sha256sum \
    > "$work/execution/$app.outputs.sha256"
  if [[ "$code" -ne 0 ]]; then overall=1; fi
done
exit "$overall"
