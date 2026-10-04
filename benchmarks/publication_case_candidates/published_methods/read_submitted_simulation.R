# Assessment-only reader. It neither executes author code nor assigns scientific credit.
numeric_cells <- function(x) {
  stopifnot(is.numeric(x), is.null(dim(x)))
  lapply(seq_along(x), function(i) {
    value <- x[[i]]
    state <- if (is.nan(value)) "NaN" else if (is.na(value)) "NA" else
      if (is.infinite(value)) if (value > 0) "Inf" else "-Inf" else "finite"
    list(name=if (is.null(names(x))) NULL else names(x)[[i]],
         storage_type=typeof(x), state=state,
         value=if (state == "finite") unname(value) else NULL)
  })
}

read_ebnm_simstudy <- function(path) {
  x <- readRDS(path)
  keys <- c("SimFn", "Function", "SimNumber")
  metrics <- c("LogLikelihood", "RMSE", "ConfIntCov")
  stopifnot(is.data.frame(x), !anyDuplicated(names(x)),
            all(c(keys, metrics) %in% names(x)))
  stopifnot(!anyNA(x[keys]), !anyDuplicated(x[keys]),
            is.character(x$SimFn), is.character(x$Function),
            is.numeric(x$SimNumber), all(is.finite(x$SimNumber)),
            all(x$SimNumber == trunc(x$SimNumber)),
            all(vapply(x[metrics], is.numeric, logical(1))))
  list(channel="ebnm_simstudy", rows=lapply(seq_len(nrow(x)), function(i) {
    list(source_row=i, SimFn=x$SimFn[[i]], Function=x$Function[[i]],
         SimNumber=unname(x$SimNumber[[i]]),
         metrics=lapply(setNames(metrics, metrics), function(name) numeric_cells(x[[name]][i])[[1]]))
  }))
}

read_ebnm_timecomps <- function(path) {
  x <- readRDS(path)
  stopifnot(is.data.frame(x), !anyDuplicated(names(x)),
            all(c("n", "expr", "time") %in% names(x)),
            is.numeric(x$n), !anyNA(x$n), all(is.finite(x$n)),
            is.character(x$expr) || is.factor(x$expr), !anyNA(x$expr),
            is.numeric(x$time))
  list(channel="ebnm_timecomps", time_units="nanoseconds_in_author_microbenchmark_object",
       rows=lapply(seq_len(nrow(x)), function(i) {
    list(source_row=i, n=unname(x$n[[i]]), expr=as.character(x$expr)[[i]],
         time=numeric_cells(x$time[i])[[1]])
  }))
}

read_bizicount_montes <- function(path) {
  env <- new.env(parent=emptyenv())
  loaded <- load(path, envir=env)
  stopifnot(all(c("res", "session") %in% loaded), is.list(env$res))
  res <- env$res
  list(channel="bizicount_montes", stored_slots=length(res),
       loaded_objects=loaded, stored_session_class=class(env$session),
       rows=lapply(seq_along(res), function(i) {
    row <- res[[i]]
    if (is.null(row)) return(list(slot=i, disposition="NULL"))
    if (inherits(row, "condition")) {
      body <- unclass(row)
      message <- if (is.list(body)) body[["message"]] else NULL
      return(list(slot=i, disposition="stored_condition", classes=class(row),
                  message=if (is.character(message)) message else NULL))
    }
    stopifnot(is.numeric(row), is.null(dim(row)), !is.object(row),
              !is.null(names(row)), !anyNA(names(row)),
              all(nzchar(names(row))), !anyDuplicated(names(row)))
    list(slot=i, disposition="numeric_return_not_convergence_verdict",
         fields=numeric_cells(row))
  }))
}

if (sys.nframe() == 0L) {
  args <- commandArgs(trailingOnly=TRUE)
  stopifnot(length(args) == 2L)
  result <- switch(args[[1]],
    ebnm_simstudy=read_ebnm_simstudy(args[[2]]),
    ebnm_timecomps=read_ebnm_timecomps(args[[2]]),
    bizicount_montes=read_bizicount_montes(args[[2]]),
    stop("unknown declared reference channel"))
  cat(jsonlite::toJSON(result, auto_unbox=TRUE, null="null", digits=NA), "\n")
}
