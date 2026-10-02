# Evaluator-only invocation of the complete, unedited journal attachment.
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 2L)
root <- normalizePath(args[[1]], mustWork = TRUE)
output <- args[[2]]
stopifnot(!file.exists(output), dir.create(output))
output <- normalizePath(output)
lib <- file.path(root, "library")
.libPaths(lib, include.site = FALSE)
Sys.setenv(R_LIBS = lib, R_LIBS_USER = lib)
stopifnot(packageVersion("TSCI", lib.loc = lib) == package_version("3.0.5"),
          packageVersion("xgboost", lib.loc = lib) == package_version("1.7.7.1"),
          packageVersion("fda", lib.loc = lib) == package_version("6.1.8"))
script <- file.path(root, "replication.R")
script_md5 <- tools::md5sum(script)
original_data <- new.env()
data("card.data", package = "ivmodel", envir = original_data)
saveRDS(original_data$card.data, file.path(output, "original_card_data.rds"))
writeLines(capture.output(sessionInfo()), file.path(output, "session_before.txt"))
setwd(output)
author <- new.env(parent = globalenv())
conditions <- list()
failure <- NULL
started <- proc.time()
tryCatch(withCallingHandlers(
  source(script, local = author, echo = TRUE, max.deparse.length = Inf),
  warning = function(w) {
    conditions[[length(conditions) + 1L]] <<- list(
      message = conditionMessage(w), call = deparse(conditionCall(w)), class = class(w))
  }), error = function(e) {
    failure <<- list(message = conditionMessage(e), call = deparse(conditionCall(e)), class = class(e))
  })
elapsed <- unname((proc.time() - started)[["elapsed"]])
unchanged <- identical(script_md5, tools::md5sum(script))
saveRDS(as.list(author), "author_workspace.rds")
saveRDS(list(warnings = conditions, error = failure, elapsed_seconds = elapsed,
             source_unchanged = unchanged), "execution_conditions.rds")
writeLines(capture.output(sessionInfo()), "session_after.txt")
cat("Source elapsed seconds:", elapsed, "\nWarnings observed in parent:", length(conditions), "\n")
if (!is.null(failure)) {
  cat("Author source failed:", failure$message, "\n", file = stderr())
  quit(status = 1L)
}
stopifnot(unchanged)
