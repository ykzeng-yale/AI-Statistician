# Read-only comparison after the reference process terminates; no agent grading.
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 1L)
root <- normalizePath(args[[1]], mustWork = TRUE)
.libPaths(file.path(root, "library"), include.site = FALSE)
fresh_path <- file.path(root, "reference_default", "output", "simstudy.rds")
archive <- file.path(root, "sources", "replication.zip")
inspection <- file.path(root, "inspection")
stopifnot(!dir.exists(inspection))
dir.create(inspection)
fresh <- readRDS(fresh_path)
author <- readRDS(gzcon(unz(archive, "output/simstudy.rds", open = "rb")))
keys <- c("SimFn", "Function", "SimNumber")
metrics <- c("LogLikelihood", "RMSE", "ConfIntCov")
stopifnot(all(c(keys, metrics) %in% names(fresh)),
          all(c(keys, metrics) %in% names(author)),
          !anyDuplicated(fresh[keys]), !anyDuplicated(author[keys]))
both <- merge(fresh, author, by = keys, all = TRUE,
              suffixes = c("_fresh", "_author"))
write.csv(fresh, file.path(inspection, "fresh_simulation.csv"), row.names = FALSE)
write.csv(author, file.path(inspection, "cached_author_simulation.csv"), row.names = FALSE)
write.csv(both, file.path(inspection, "cellwise_comparison.csv"), row.names = FALSE)
cat("Fresh rows:", nrow(fresh), "Author rows:", nrow(author),
    "Outer join rows:", nrow(both), "\n")
print(table(fresh$SimFn, fresh$Function))
for (metric in metrics) {
  a <- both[[paste0(metric, "_fresh")]]
  b <- both[[paste0(metric, "_author")]]
  finite_pairs <- is.finite(a) & is.finite(b)
  cat("\nMetric:", metric, "\n")
  cat("Fresh NA:", sum(is.na(a)), "Fresh infinite:", sum(is.infinite(a)),
      "Author NA:", sum(is.na(b)), "Author infinite:", sum(is.infinite(b)), "\n")
  cat("Finite pairs:", sum(finite_pairs), "Max absolute difference:",
      if (any(finite_pairs)) max(abs(a[finite_pairs] - b[finite_pairs])) else NA_real_,
      "\n")
  print(aggregate(fresh[[metric]], fresh[c("SimFn", "Function")], mean))
}

state_path <- file.path(root, "reference_default", "output", "fresh_workspace.RData")
if (file.exists(state_path)) {
  state <- new.env(parent = emptyenv())
  load(state_path, envir = state)
  cat("\nIntroductory RMSE (observations, normal, point-normal):\n")
  print(c(sqrt(mean((state$pdat$mle - state$pdat$u)^2)),
          sqrt(mean((state$pdat$est.n - state$pdat$u)^2)),
          sqrt(mean((state$pdat$est.pn - state$pdat$u)^2))))
  cat("\nBaseball posterior example:\n")
  print(head(state$dat), digits = 10)
}
