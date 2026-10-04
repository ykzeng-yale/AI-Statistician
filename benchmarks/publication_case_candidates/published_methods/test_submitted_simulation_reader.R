# Fresh serialization fixtures only: no author results, reference comparisons or model calls.
args <- commandArgs(trailingOnly=TRUE)
stopifnot(length(args) == 1L)
source(args[[1]])
root <- tempfile("submitted-simulation-reader-")
dir.create(root)

must_fail <- function(expr) stopifnot(inherits(tryCatch({force(expr); NULL}, error=identity), "error"))

sim <- expand.grid(SimFn=c("normal", "point_t", "asymm_tophat"),
                   Function=paste0("ebnm_", c("flat", "normal", "point_normal", "point_laplace",
                     "normal_scale_mixture", "unimodal_symmetric", "unimodal", "npmle", "deconvolver", "horseshoe")),
                   SimNumber=seq_len(10), stringsAsFactors=FALSE)
sim$LogLikelihood <- rep(c(NA_real_, NaN, Inf, -Inf, 0), length.out=nrow(sim))
sim$RMSE <- seq_len(nrow(sim)) / 1000
sim$ConfIntCov <- rep(0.4, nrow(sim))
sim <- sim[rev(seq_len(nrow(sim))), ]
class(sim) <- c("tbl_df", "tbl", "data.frame")
simpath <- file.path(root, "fresh.rds")
saveRDS(sim, simpath)
parsed <- read_ebnm_simstudy(simpath)
stopifnot(length(parsed$rows) == 300L,
          identical(parsed$rows[[1]]$SimFn, sim$SimFn[[1]]),
          parsed$rows[[1]]$SimNumber == sim$SimNumber[[1]],
          parsed$rows[[1]]$metrics$RMSE$value == sim$RMSE[[1]],
          setequal(vapply(parsed$rows, function(x) x$metrics$LogLikelihood$state, ""),
                   c("NA", "NaN", "Inf", "-Inf", "finite")))
cli <- system2(file.path(R.home("bin"), "Rscript"),
               c("--vanilla", shQuote(normalizePath(args[[1]])), "ebnm_simstudy", shQuote(simpath)),
               stdout=TRUE, stderr=TRUE)
stopifnot(is.null(attr(cli, "status")))
cli_result <- jsonlite::fromJSON(paste(cli, collapse="\n"), simplifyVector=FALSE)
stopifnot(length(cli_result$rows) == 300L,
          cli_result$rows[[1]]$metrics$LogLikelihood$state == "finite")
duplicate <- rbind(sim, sim[1, ])
saveRDS(duplicate, simpath)
must_fail(read_ebnm_simstudy(simpath))
sim$SimFn[[1]] <- NA_character_
saveRDS(sim, simpath)
must_fail(read_ebnm_simstudy(simpath))

timing <- data.frame(n=c(100, 100, sqrt(100000)),
                     expr=factor(c("ebnm_normal", "ebnm_normal", "ebnm_flat")),
                     time=c(NA_real_, 0, 1e8))
saveRDS(timing, simpath)
parsed <- read_ebnm_timecomps(simpath)
stopifnot(length(parsed$rows) == 3L, parsed$rows[[1]]$source_row == 1L,
          parsed$rows[[2]]$source_row == 2L, parsed$rows[[1]]$time$state == "NA",
          parsed$rows[[2]]$time$value == 0, parsed$rows[[3]]$n == timing$n[[3]])

res <- vector("list", 4000)
res[[1]] <- c(n=500, psi1_tru=0.1, psi2_tru=0.6, dep_true=0.85,
             "est.biv1.ct1_(Intercept)"=2, "se.biv1.ct1_(Intercept)"=NA_real_,
             conv1=3, conv2=1, "ll.biv1"=-Inf, "ll.biv2"=NaN)
res[[3]] <- simpleError("fresh fixture error, not an author failure")
res[[4000]] <- c(n=500, psi1_tru=0.6, psi2_tru=0.6, dep_true=0.85, "est.uni1.ct_(Intercept)"=7)
session <- list(opaque="fixture, not a historical or active runtime attestation")
datapath <- file.path(root, "fresh.RData")
save(res, session, file=datapath)
parsed <- read_bizicount_montes(datapath)
stopifnot(parsed$stored_slots == 4000L, length(parsed$rows) == 4000L,
          parsed$rows[[2]]$slot == 2L, parsed$rows[[2]]$disposition == "NULL",
          parsed$rows[[3]]$disposition == "stored_condition",
          parsed$rows[[3]]$message == "fresh fixture error, not an author failure",
          parsed$rows[[4000]]$slot == 4000L,
          parsed$rows[[1]]$fields[[7]]$name == "conv1", parsed$rows[[1]]$fields[[7]]$value == 3,
          parsed$rows[[1]]$fields[[6]]$state == "NA", parsed$rows[[1]]$fields[[9]]$state == "-Inf",
          parsed$rows[[1]]$fields[[10]]$state == "NaN")
encoded <- jsonlite::toJSON(parsed, auto_unbox=TRUE, null="null", digits=NA)
roundtrip <- jsonlite::fromJSON(encoded, simplifyVector=FALSE)
stopifnot(roundtrip$rows[[2]]$slot == 2, roundtrip$rows[[2]]$disposition == "NULL",
          is.null(roundtrip$rows[[1]]$fields[[6]]$value),
          roundtrip$rows[[1]]$fields[[6]]$state == "NA")
res[[1]] <- c(ambiguous=1, ambiguous=2)
save(res, session, file=datapath)
must_fail(read_bizicount_montes(datapath))
save(session, file=datapath)
must_fail(read_bizicount_montes(datapath))
writeBin(charToRaw("not an R serialization"), simpath)
must_fail(read_ebnm_simstudy(simpath))
must_fail(read_ebnm_simstudy(file.path(root, "absent.rds")))
unlink(root, recursive=TRUE)
cat("Fresh reader fixtures passed; no numerical or mathematical assessment performed.\n")
