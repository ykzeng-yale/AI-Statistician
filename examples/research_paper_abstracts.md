# Paper-Style Research Question Benchmark

Each section uses `id: title` followed by optional tags and an abstract-style
description. This file exercises the same research workflow as JSON input while
matching the shape of paper abstracts or journal problem statements.

## causal_ate_paper: Semiparametric ATE estimation with doubly robust scores

Tags: causal, ate, semiparametric, aipw

We study iid observational data with baseline covariates, a binary treatment,
and a continuous outcome. Under consistency, conditional exchangeability, and
positivity, the target is the average treatment effect. Develop an estimator
based on an augmented inverse-probability weighted score, state identification,
double robustness, and asymptotic normality goals, and evaluate finite-sample
bias, RMSE, standard error calibration, and 95% confidence interval coverage.

## conformal_paper: Distribution-free split conformal prediction under exchangeability

Tags: conformal, prediction, coverage, exchangeability

For exchangeable regression data with a nonlinear response surface, construct a
prediction interval procedure with marginal coverage close to 95%. Formalize the
finite-sample coverage target, record the exchangeability/rank argument as a
formal gap when not available in Lean, and evaluate empirical coverage,
miscoverage, average interval width, and prediction-center RMSE.

## survival_paper: Right-censored survival inference with Kaplan-Meier estimation

Tags: survival, right_censored, hazard, kaplan_meier, censoring

We observe iid time-to-event data subject to independent right censoring. The
target is the survival probability at a clinically meaningful fixed time.
Develop a Kaplan-Meier or Nelson-Aalen estimator, state independent-censoring
identification, consistency, and Greenwood fixed-time asymptotic normality
goals, retrieve available probability and indicator facts, and evaluate bias,
RMSE, standard error calibration, censoring fraction, and 95% coverage in
simulation.

## robust_mean_paper: Robust sub-Gaussian mean inference under contamination

Tags: robust_mean, subgaussian, heavy_tails, contamination, median_of_means, minimax

We observe iid data from a heavy-tailed location model with a small fraction of
gross-error contamination. The target is the uncontaminated mean or location
parameter. Develop a median-of-means robust estimator, state sub-Gaussian
deviation and minimax corruption-rate goals, retrieve available mean, variance,
and probability-inequality facts, and evaluate bias, RMSE, standard error
calibration, contamination fraction, and 95% coverage in simulation.

## design_variance_paper: Conservative variance estimation in randomized experiments

Tags: experimental_design, design_based_variance, randomization, conservative_variance

We study a randomized experiment with fixed potential outcomes and heterogeneous
unit-level treatment effects. The target is the randomization variance of the
difference-in-means treatment-effect estimator, but exact unbiased variance
estimation is impossible from one assignment. Develop a conservative design-based
variance estimator, state Neyman validity and optimized variance-bound
minimality goals, retrieve available mean and variance facts, and evaluate bias,
RMSE, coverage, standard error calibration, and conservativeness ratio in
simulation.

## robust_regression_paper: Heteroskedastic robust inference for a regression slope

Tags: regression, heteroskedastic, robust_se, sandwich

Consider a low-dimensional linear regression with conditionally heteroskedastic
errors. The target is the slope coefficient. Develop the OLS estimator with HC1
sandwich standard errors, state the consistency and asymptotic Wald validity
goals, retrieve available variance and linearity facts, and evaluate bias, RMSE,
standard error calibration, and 95% coverage in simulation.

## fdr_paper: False discovery rate control for large-scale multiple testing

Tags: multiple_testing, fdr, benjamini_hochberg, bh

We consider many independent z-tests with a sparse mixture of non-null effects.
The target is a rejection rule that controls false discovery rate at a nominal
level while maintaining nontrivial discovery power. Develop the
Benjamini-Hochberg step-up procedure, state the finite-sample FDR control goal
under independent valid null p-values and the sparse-mixture power goal, retrieve
available probability inequalities and complement facts, and evaluate empirical
FDR, false discovery proportion variability, rejection rate, and power.

## anytime_paper: Anytime-valid sequential testing with e-processes

Tags: sequential, anytime, optional_stopping, eprocess

We observe Bernoulli outcomes sequentially and want to monitor evidence against
a simple null hypothesis while preserving type-I error under optional stopping.
Develop a likelihood-ratio e-process test, state the Ville-inequality
anytime-valid control goal and the martingale property of the likelihood-ratio
process, retrieve available probability inequality facts, and evaluate
optional-stopping type-I error, power, and stopping-time behavior in simulation.

## high_dimensional_pca_paper: Spiked-covariance PCA under high-dimensional asymptotics

Tags: high_dimensional, pca, eigenvector, dimension_reduction, spiked_covariance

We observe high-dimensional vectors whose covariance has a separated rank-one
signal spike. The target is the leading population eigenvector or signal
subspace. Develop a sample-PCA estimator, state the population eigenspace target
and the high-dimensional recovery goals, retrieve available variance and
formalization infrastructure facts, and evaluate alignment, subspace error,
angle error, and leading-eigenvalue behavior in simulation.

## extreme_tail_quantile_paper: Hill and Weissman inference for extreme quantiles

Tags: extremes, heavy_tails, tail_index, high_quantile, regular_variation, hill, weissman

We observe iid heavy-tailed losses and want inference for the upper tail index
and a rare high quantile. Develop a Hill estimator based on top order
statistics, use Weissman extrapolation for the target quantile, state the
regular-variation consistency and asymptotic normality goals, retrieve available
probability-inequality facts, and evaluate bias, RMSE, standard error
calibration, and high-quantile coverage in simulation.
