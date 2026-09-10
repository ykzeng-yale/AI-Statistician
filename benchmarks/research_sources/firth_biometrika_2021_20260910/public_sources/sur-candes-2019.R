## Distributed as part of the supplementary material for the manuscript
## "Jeffreys-prior penalty, finiteness and shrinkage in binomial-response generalized linear models"
##
## Authors: Ioannis Kosmidis, David Firth
## Date: 19 March 2020
## Licence: GPL 2 or greater
## NOT A POLISHED PIECE OF PUBLIC-USE SOFTWARE!  Provided "as is".
## NO WARRANTY OF FITNESS FOR ANY PURPOSE!

source("jeffreys-MPL.R")
library("rbenchmark")

## Setting for Figure 2b on p 11 of the supplementary information appendix of
##
## Sur P, and Candès EJ (2019). A Modern Maximum-Likelihood Theory for
## High-Dimensional Logistic Regression.  Proceedings of the National
## Academy of Sciences 116 (29):
## 14516–25. https://doi.org/10.1073/pnas.1810420116.
##
## The supplementary information appendix has been downloaded from
## https://www.pnas.org/content/pnas/suppl/2019/06/29/1810420116.DCSupplemental/pnas.1810420116.sapp.pdf
set.seed(111)
n <- 1000
p <- 200
beta <- c(rep(10, p/8), rep(-10, p/8), rep(0, 3*p/4))
x <- matrix(rnorm(n * p, 0, sqrt(1/n)), n, p)
probs <- plogis(x %*% beta) 
y <- rbinom(n, 1, probs)

## Test times of glm, brglm, brglm2 and JeffreysMPL
reps <- 50
times <- benchmark(
    "glm" = {
        mod_ml <- glm(y ~ -1 + x, family = binomial(logit), model = FALSE, epsilon = 1e-04)
    },
    "JeffreysMPL" = {
        mod_br_alt <- JeffreysMPL(y = y, m = NULL, X = x, a = 1/2, link = "logit", epsilon = 1e-04)
    },
    replications = reps,
    columns = c("test", "replications", "elapsed", "relative"),
    order = NULL)

## The computing times reported in Section S3.5 of the supplementary material
(elapsed <- times$elapsed[times$test == "JeffreysMPL"]/reps)
## [1] 2.72972

## Reproducing Figure S1 in the supplementary material, which is also
## given as Figure 2b on p 11 of the supplementary information
## appendix of Sur P, and Candès EJ (2019)
plot_coefs <- function(model) {
    coefs <- coef(model)
    plot(coefs, ylim = c(-30, 30), xlab = "parameter", ylab = "estimate")
    ## True values
    segments(x0 = 1, x1 = p/8, y0 = 10, y1 = 10, lwd = 2)
    segments(x0 = p/8 + 1, x1 = p/4, y0 = -10, y1 = -10, lwd = 2)
    segments(x0 = p/4 + 1, x1 = p, y0 = 0, y1 = 0, lwd = 2)
}

par(mfrow = c(1, 2))
plot_coefs(mod_ml)
title("Maximum likelihood")
plot_coefs(mod_br_alt)
title("JeffreysMPL (a = 1/2; logistic link)")

