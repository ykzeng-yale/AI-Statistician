/* pROC: Tools Receiver operating characteristic (ROC curves) with
   (partial) area under the curve, confidence intervals and comparison.
   Copyright (C) 2016 Xavier Robin and Stefan Siegert.
   GPL-3.0-or-later.

   Source snapshot:
   https://github.com/xrobin/pROC/blob/be0475b49cb353318703f9e48aa9eb9cd125d677/src/delong.cpp
*/

// The complete pinned source sorts pooled case/control scores. For every tied
// block it records the number of controls strictly below the block plus one half
// of the controls in the block for each case, and the corresponding case count
// for each control. It then returns the normalized placements and their common
// mean theta.

for (k = 0; k < mdupl; k++) {
  XY.at(X_inds.at(k)) = n + ndupl / 2.0;
}
for (k = 0; k < ndupl; k++) {
  XY.at(Y_inds.at(k)) = m + mdupl / 2.0;
}

for (i = 0; i < L; i++) {
  if (labels.at(i)) {
    sum += XY.at(i);
    X.push_back(XY.at(i) / n);
  } else {
    Y.push_back(1.0 - XY.at(i) / m);
  }
}

ret["theta"] = sum / m / n;
ret["X"] = X;
ret["Y"] = Y;
