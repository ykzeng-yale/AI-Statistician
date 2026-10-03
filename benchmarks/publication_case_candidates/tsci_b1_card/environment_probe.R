packages <- c("ivmodel", "ranger", "MASS", "jsonlite")
versions <- setNames(lapply(packages, function(package) {
  as.character(utils::packageVersion(package))
}), packages)
cat(jsonlite::toJSON(list(
  runtime_language = "r",
  runtime_version = R.version.string,
  package_versions = versions
), auto_unbox = TRUE), "\n", sep = "")
