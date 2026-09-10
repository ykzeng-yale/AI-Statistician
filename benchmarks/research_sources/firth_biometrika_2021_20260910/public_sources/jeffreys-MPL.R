## Distributed as part of the supplementary material for the manuscript
## "Jeffreys-prior penalty, finiteness and shrinkage in binomial-response generalized linear models"
##
## Authors: Ioannis Kosmidis, David Firth
## Date: 19 March 2020
## Licence: GPL 2 or greater
## NOT A POLISHED PIECE OF PUBLIC-USE SOFTWARE!  Provided "as is".
## NO WARRANTY OF FITNESS FOR ANY PURPOSE!

#' @param y a vector of binomial counts
#' @param m a vector of binomial totals. If \code{NULL} then the totals are taken to be 1, assuming that \code{y} is a vector of Bernoulli observations
#' @param X the model matrix
#' @param a a positive constant determining the amount of penalization of the likelihood by Jeffreys prior; \code{a = 1/2} corresponds to penalization by Jeffreys prior (default) and \code{a = 0} results in no penalization
#' @param link: the name of the link function; some options are \code{"logit"} (default), \code{"probit"}, \code{"cloglog"}, \code{"cauchit"}. A \code{link-glm} object is constructed internally using \code{make.link{link}}
#' @param adj a positive constant which defaults to \code{0.001}. \code{adj} is added to \code{y} and \code{2 * adj} is added to \code{m}, before maximum likelihood estimation is used to obtain the starting values fot the iterations of Algorithm S1 in the supplementary material document
#' @param epsilon a small positive constant; default value is \code{1e-08}. If the difference of the consecutive values for each parameter is less than \code{tol}, then \code{JeffreysMPL} reports convergence
#' @param maxit the maximum number of repeated ML fits; default is \code{100}
#' @param verbose should iteration information be printed? Default is \code{FALSE}
JeffreysMPL <- function(y, m = NULL, X, a = 1/2, link = "logit",
                        adj = 0.001, epsilon = 1e-08, maxit = 100, verbose = FALSE) {
    require("enrichwith")
    link <- make.link(link)
    link <- enrich(link)
    family <- binomial(link)
    G <- link$linkinv
    g <- link$mu.eta
    gdash <- link$d2mu.deta
    if (is.null(m)) {
        m <- rep(1, length(y))
    }
    b <- coef(glm.fit(X, (y + adj)/(m + 2 * adj), weights = (m + 2 * adj), family = family))
    adjusted_responses <- matrix(y + adj, nrow = length(y))
    adjusted_totals <- matrix(m + 2 * adj, nrow = length(y))
    for (i in seq.int(maxit)) {
        eta <- drop(X %*% b)
        dlist <- gdash(eta)
        pi <- G(eta)
        attributes(pi) <- NULL
        d <- g(eta)
        dd <- gdash(eta)
        w <- d^2 / pi / (1 - pi)
        q <- dd / w + pi
        j  <- q <= 0.5
        V <- sqrt(m * w) * X
        QR <- qr(V)
        Q <- qr.Q(QR)
        h <- rowSums(Q * Q)
        y_adj <- y + 2 * a * h * pi * (1 + (q - 0.5) * (1 - j) / pi / (1 - pi))
        m_adj <- m + 2 * a * h * (1 + (q - 0.5) * (pi - j) / pi / (1 - pi))
        adjusted_responses <- cbind(adjusted_responses, y_adj)
        adjusted_totals <- cbind(adjusted_totals, m_adj)
        bp <- b
        b <- coef(glm.fit(X, y_adj/m_adj, weights = m_adj, family = family))
        crit <- abs(bp - b)
        if (verbose) cat("iteration", i, "max abs coef diff", max(crit), "\n")
        if (all(crit < epsilon, na.rm = TRUE))
            break
    }
    conv <- 1
    if (i == maxit) {
        warning("iteration limit reached")
        conv <- 0
    }
    list(iter = i,
         coefficients = b,
         converged = conv,
         fitted.values = pi,
         adjusted_responses = adjusted_responses,
         adjusted_totals = adjusted_totals)
}
