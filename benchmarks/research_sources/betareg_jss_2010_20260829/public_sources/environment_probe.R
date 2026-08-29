packages <- c(
  betareg = "betareg",
  Formula = "Formula",
  sandwich = "sandwich",
  lmtest = "lmtest",
  strucchange = "strucchange",
  zoo = "zoo"
)

versions <- vapply(
  packages,
  function(package) as.character(utils::packageVersion(package)),
  character(1)
)

escape_json <- function(value) {
  value <- gsub("\\\\", "\\\\\\\\", value, fixed = TRUE)
  value <- gsub('"', '\\"', value, fixed = TRUE)
  paste0('"', value, '"')
}

package_rows <- paste0(
  escape_json(names(versions)),
  ":",
  escape_json(unname(versions))
)

cat(
  paste0(
    '{"runtime_language":"r","runtime_version":',
    escape_json(R.version.string),
    ',"package_versions":{',
    paste(package_rows, collapse = ","),
    "}}\n"
  )
)
