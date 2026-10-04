packages <- strsplit(Sys.getenv("AI_STATISTICIAN_SOURCE_PACKAGES"), ",", fixed = TRUE)[[1]]
if (length(packages) == 0L || any(!nzchar(packages))) stop("Source package list is required")
versions <- setNames(lapply(packages, function(package) {
  as.character(utils::packageVersion(package))
}), packages)
cat(jsonlite::toJSON(list(runtime_language = "r", runtime_version = R.version.string,
                        package_versions = versions), auto_unbox = TRUE), "\n", sep = "")
