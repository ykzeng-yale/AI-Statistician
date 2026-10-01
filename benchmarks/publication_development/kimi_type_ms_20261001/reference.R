args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 3)
source(args[[1]])
scenarios <- read.csv(args[[2]], stringsAsFactors = FALSE)
rows <- lapply(seq_len(nrow(scenarios)), function(i) {
  scenario <- scenarios[i, ]
  result <- retro_r(rho = scenario$rho, n = scenario$n,
                    alternative = scenario$alternative,
                    sig_level = scenario$sig_level, B = scenario$B,
                    seed = scenario$seed)
  data.frame(scenario_id = scenario$scenario_id, power = result$power,
             typeM = result$typeM, typeS = result$typeS,
             crit_lower = result$crit_r[[1]],
             crit_upper = result$crit_r[[2]])
})
options(digits = 17)
write.csv(do.call(rbind, rows), args[[3]], row.names = FALSE)
