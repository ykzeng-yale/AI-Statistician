# Operator launcher, not an author-source modification. Reproduce the single
# coefficient experiment in sur-candes-2019.R, excluding its timing benchmark.
source("jeffreys-MPL.R")
set.seed(111)
n <- 1000
p <- 200
beta <- c(rep(10, p/8), rep(-10, p/8), rep(0, 3*p/4))
x <- matrix(rnorm(n * p, 0, sqrt(1/n)), n, p)
probs <- plogis(x %*% beta)
y <- rbinom(n, 1, probs)
mod_ml <- glm(y ~ -1 + x, family = binomial(logit), model = FALSE, epsilon = 1e-04)
mod_br_alt <- JeffreysMPL(y = y, m = NULL, X = x, a = 1/2, link = "logit", epsilon = 1e-04)
write.csv(data.frame(parameter = seq_len(p), truth = beta,
                     maximum_likelihood = coef(mod_ml),
                     jeffreys_penalized = mod_br_alt$coefficients),
          "coefficients.csv", row.names = FALSE)
cat("rows", n, "columns", p, "\n")
cat("author_converged", mod_br_alt$converged, "author_iterations", mod_br_alt$iter, "\n")
cat("R_version", R.version.string, "\n")
cat("enrichwith_version", as.character(packageVersion("enrichwith")), "\n")
