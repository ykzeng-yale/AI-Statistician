# pROC: Tools Receiver operating characteristic (ROC curves) with
# (partial) area under the curve, confidence intervals and comparison.
# Copyright (C) 2010-2014 Xavier Robin and contributors.
# GPL-3.0-or-later.
#
# Source snapshot:
# https://github.com/xrobin/pROC/blob/be0475b49cb353318703f9e48aa9eb9cd125d677/R/delong.R

ci_auc_delong <- function(roc, conf.level) {
  YR <- roc$controls
  XR <- roc$cases

  n <- length(YR)
  m <- length(XR)
  if (m <= 1 || n <= 1) {
    return(rep(NA, 3))
  }

  V <- delongPlacements(roc)
  SX <- sum((V$X - V$theta) * (V$X - V$theta)) / (m - 1)
  SY <- sum((V$Y - V$theta) * (V$Y - V$theta)) / (n - 1)
  S <- SX / m + SY / n
  ci <- qnorm(
    c((1 - conf.level) / 2, .5, 1 - (1 - conf.level) / 2),
    mean = V$theta,
    sd = sqrt(S)
  )
  ci[ci > 1] <- 1
  ci[ci < 0] <- 0
  return(ci)
}
