# Read-only reference inspection, not an agent evaluator or a source rerun.
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 2L)
root <- normalizePath(args[[1]], mustWork = TRUE)
output <- args[[2]]
stopifnot(!file.exists(output))
.libPaths(file.path(root, "library"), include.site = FALSE)
execution <- file.path(root, "execution_1")
workspace <- readRDS(file.path(execution, "author_workspace.rds"))
original <- readRDS(file.path(execution, "original_card_data.rds"))
conditions <- readRDS(file.path(execution, "execution_conditions.rds"))
fits <- workspace[c("fit_boosting", "fit_secondstage")]
numeric_counts <- function(fit) {
  lapply(fit[vapply(fit, is.numeric, logical(1))], function(x) {
    list(length = length(x), dim = dim(x), na = sum(is.na(x)),
         nan = sum(is.nan(x)), infinite = sum(is.infinite(x)))
  })
}
record <- list(
  scope = "inspection_of_same_stored_reference_not_reexecution_or_mathematical_gold",
  raw_fit_fields = lapply(fits, unclass),
  numeric_field_counts = lapply(fits, numeric_counts),
  parent_conditions = conditions,
  source_object_names = names(workspace),
  original_card = list(dim = dim(original), columns = names(original),
                       missing_by_column = colSums(is.na(original))),
  processed_card = list(dim = dim(workspace$card.data),
                        missing_by_column = colSums(is.na(workspace$card.data))),
  bspline = list(dim = dim(workspace$W), head = unname(head(workspace$W, 4))),
  hat_matrix = list(dim = dim(workspace$omega), nonfinite = sum(!is.finite(workspace$omega))))
jsonlite::write_json(record, output, auto_unbox = TRUE, pretty = TRUE,
                    digits = NA, na = "null", null = "null", dataframe = "rows")
cat("Inspected original and stored author objects without refitting.\n")
