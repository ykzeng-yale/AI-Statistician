# Exact-object diagnostics only; no acceptance threshold or theorem assessment.
args <- commandArgs(TRUE)
stopifnot(length(args) == 4)
generated <- normalizePath(args[1], mustWork = TRUE)
reference <- normalizePath(args[2], mustWork = TRUE)
application <- args[3]
output <- args[4]
stopifnot(!dir.exists(output), !file.exists(output))
dir.create(output, recursive = TRUE)
paths <- function(root) {
  unlist(lapply(c("Outputs", "Temp"), function(channel) {
    folder <- file.path(channel, application)
    entries <- list.files(file.path(root, folder), pattern = "[.]rds$", recursive = TRUE)
    file.path(folder, entries)
  }), use.names = FALSE)
}
rows <- lapply(sort(union(paths(generated), paths(reference))), function(path) {
  a <- file.path(generated, path)
  b <- file.path(reference, path)
  both <- file.exists(a) && file.exists(b)
  result <- if (both) tryCatch({
    actual <- readRDS(a)
    original <- readRDS(b)
    list(identical = identical(actual, original),
         comparison = paste(all.equal(actual, original, tolerance = 0,
                                      check.attributes = TRUE), collapse = " | "))
  }, error = function(error) list(identical = NA, comparison = conditionMessage(error))) else {
    list(identical = NA, comparison = "Missing generated or original object")
  }
  data.frame(path = path, generated_present = file.exists(a),
             original_present = file.exists(b), identical = result$identical,
             zero_tolerance_diagnostic = result$comparison)
})
write.csv(do.call(rbind, rows), file.path(output, "object_comparison.csv"), row.names = FALSE)
writeLines(capture.output(sessionInfo()), file.path(output, "session.txt"))
