# Frontier Statistical Theory Benchmark

Created: 2026-05-28

This benchmark turns recent papers from JASA, Annals of Statistics, JRSSB, and Biometrika into open-question / expected-theory-result pairs. It is intended for end-to-end testing of an AI statistician system: give the system the open question and assumptions, withhold the paper identity and expected results, and grade whether it reconstructs the right theoretical target or a defensibly stronger one.

## Scope and Sources

- Journal pool: Journal of the American Statistical Association, Annals of Statistics, Journal of the Royal Statistical Society: Series B, and Biometrika.
- Date window: 2024-01-01 through 2026-05-28, with selected papers sorted by publication date within each topic where feasible.
- Metadata sources: Crossref DOI/journal records plus OpenAlex DOI records where Crossref lacked abstracts, mainly for JASA and Annals of Statistics.
- Selection rule: five recent DOI-backed papers per topic with enough abstract-level metadata to define a testable question/result pair.
- Caveat: these are abstract-level benchmark targets, not a substitute for full proof-level reading of each paper. Use the DOI links for final gold-standard verification.

## Topic Index

- Causal Effects, Heterogeneity, and Sensitivity (`causal_effects`): 5 papers
- Experimental Design, Adaptive Assignment, and Randomization (`experimental_design`): 5 papers
- Sequential, Changepoint, and Anytime-Valid Inference (`sequential_change_anytime`): 5 papers
- High-Dimensional Inference, PCA, and Dimension Reduction (`high_dimensional_inference`): 5 papers
- Statistical Learning, Deep Nonparametrics, and Prediction Risk (`statistical_learning_nonparametric`): 5 papers
- Robustness, Privacy, Federated, and Distributed Statistics (`robust_privacy_distributed`): 5 papers
- Bayesian Computation, Priors, and Posterior Calibration (`bayesian_computation_posteriors`): 5 papers
- Networks, Graphs, and Relational Dependence (`networks_graphs`): 5 papers
- Geometric, Spatial, Functional, and Point-Process Inference (`geometric_spatial_point_process`): 5 papers
- Multiple Testing, Conformal Inference, and Selection (`multiple_testing_conformal_selection`): 5 papers
- Extremes, Tail Risk, Heavy Tails, and Robust Limits (`extremes_tail_heavytail`): 5 papers
- Missingness, Censoring, Measurement Error, and Data Integration (`missing_censored_measurement_error`): 5 papers

## Causal Effects, Heterogeneity, and Sensitivity

Topic test: Can a system formulate causal estimands beyond average effects and prove identification, efficiency, or sensitivity guarantees under modern complications?

### causal_effects_01: Principal stratification with U-statistics under principal ignorability

- Source: JRSSB, 2026-05-27; Xinyuan Chen, Fan Li; DOI: [10.1093/jrsssb/qkag044](https://doi.org/10.1093/jrsssb/qkag044)
- Open question: How can principal stratification handle nonlinear win-loss or ordinal causal contrasts rather than only principal average treatment effects?
- Assumptions to recover: binary intermediate variable, principal ignorability, nonparametric observed-data model, U-statistic form for nonlinear contrasts.
- Expected theoretical results:
  - Define principal generalized causal effect estimands on a probability scale.
  - Prove nonparametric identification under principal ignorability.
  - Derive efficient influence functions and asymptotic theory for U-statistic estimators.

### causal_effects_02: Enhanced Inference for Distributions and Quantiles of Individual Treatment Effects in Various Experiments

- Source: JASA, 2026-05-21; Zhe Chen, Xinran Li; DOI: [10.1080/01621459.2026.2615997](https://doi.org/10.1080/01621459.2026.2615997)
- Open question: How can randomized experiments support sharper inference for the distribution and quantiles of individual treatment effects when individual effects are not observed?
- Assumptions to recover: completely or stratified randomized experiment, potential-outcome schedule fixed before assignment, partial identification of ITE distribution.
- Expected theoretical results:
  - Construct less conservative randomization-based bounds for treatment-effect distributions and quantiles.
  - Give finite-sample valid inference procedures under the randomization design.
  - Show improvement over worst-case rearrangement bounds in structured experimental settings.

### causal_effects_03: Quantifying individual risk for binary outcomes

- Source: JRSSB, 2026-05-19; Peng Wu, Peng Ding, Zhi Geng et al.; DOI: [10.1093/jrsssb/qkag071](https://doi.org/10.1093/jrsssb/qkag071)
- Open question: For binary outcomes, how can one quantify the fraction of individuals harmed by treatment rather than relying on subgroup-average treatment effects?
- Assumptions to recover: potential outcomes for binary response, observed covariates, treatment evaluation and individualized policy setting, partial identification of individual harm.
- Expected theoretical results:
  - Define the fraction negatively affected as an individual-risk estimand.
  - Establish identification or sharp partial-identification bounds under stated causal assumptions.
  - Develop estimation and inference that distinguish individual risk from CATE.

### causal_effects_04: Nonparametric tests of treatment effect homogeneity for policy-makers

- Source: JASA, 2026-05-18; Oliver Dukes, Mats J. Stensrud, Riccardo Brioschi et al.; DOI: [10.1080/01621459.2026.2670746](https://doi.org/10.1080/01621459.2026.2670746)
- Open question: Can treatment-effect homogeneity be tested nonparametrically in a way that is aligned with policy decisions?
- Assumptions to recover: conditional average treatment effect, continuous or discrete covariates, structured alternatives for heterogeneity, no sample splitting requirement.
- Expected theoretical results:
  - Construct tests for quantitative and qualitative treatment-effect heterogeneity.
  - Derive tractable asymptotic null distributions without sample splitting.
  - Characterize power against alternatives where personalized rules improve policy value.

### causal_effects_05: An average-case sensitivity analysis for unmeasured confounding

- Source: Biometrika, 2026-04-29; Yao Zhang, Qingyuan Zhao; DOI: [10.1093/biomet/asag030](https://doi.org/10.1093/biomet/asag030)
- Open question: How can sensitivity analysis for unmeasured confounding use average-case rather than worst-case confounding strength?
- Assumptions to recover: observational causal inference, marginal sensitivity model baseline, bounded second moment of propensity-score ratio, unconfoundedness violation represented by hidden variables.
- Expected theoretical results:
  - Define an average-case sensitivity model indexed by a propensity-ratio moment.
  - Characterize the resulting sensitivity region or bounds.
  - Develop inferential procedures that remain interpretable when worst-case bounds are too pessimistic.

## Experimental Design, Adaptive Assignment, and Randomization

Topic test: Can a system design experiments and derive finite-sample or asymptotic inference under nonstandard assignment mechanisms?

### experimental_design_01: Oracle arrays and their use for constructing space-filling designs

- Source: JRSSB, 2026-05-19; Boxin Tang; DOI: [10.1093/jrsssb/qkag075](https://doi.org/10.1093/jrsssb/qkag075)
- Open question: How can maximin space-filling designs be constructed when direct optimization of Lp distances is theoretically difficult?
- Assumptions to recover: quantitative factors in computer experiments, maximin distance criterion, Hamming-distance array construction as proxy, mapping from discrete arrays to Lp space.
- Expected theoretical results:
  - Introduce oracle arrays as maximin Hamming-distance building blocks.
  - Prove constructions that generate maximin Hamming arrays and translate them into maximin Lp-distance designs.
  - Give design-quality guarantees relative to direct space-filling criteria.

### experimental_design_02: Optimized Variance Estimation under Interference and Complex Experimental Designs

- Source: JASA, 2026-05-13; Christopher Harshaw, Joel Middleton, Fredrik Sävje; DOI: [10.1080/01621459.2026.2627027](https://doi.org/10.1080/01621459.2026.2627027)
- Open question: When unbiased variance estimation is impossible under interference and complex designs, what is the least conservative estimable variance bound?
- Assumptions to recover: design-based potential outcomes, interference or complex assignment, partial knowledge of potential-outcome structure, risk preference over conservativeness.
- Expected theoretical results:
  - Formulate conservative variance estimation as an optimization problem.
  - Identify the lowest estimable upper bound for the true variance under given constraints.
  - Prove design-based validity of the optimized conservative estimator.

### experimental_design_03: Design Stability in Adaptive Experiments: Implications for Treatment Effect Estimation

- Source: Biometrika, 2026-05-05; Saikat Sengupta, Koulik Khamaru, Suvrojit Ghosh et al.; DOI: [10.1093/biomet/asag032](https://doi.org/10.1093/biomet/asag032)
- Open question: Under sequentially adaptive treatment assignment, when are standard treatment-effect estimators asymptotically valid?
- Assumptions to recover: potential outcomes, assignment probabilities depend on past assignments and outcomes, inverse-propensity and augmented inverse-propensity estimators, design stability condition.
- Expected theoretical results:
  - Define design stability for adaptive experiments.
  - Prove consistency and asymptotic normality for IPW and AIPW estimators under stability.
  - Clarify when adaptive assignment invalidates or preserves treatment-effect inference.

### experimental_design_04: Stratum order-of-addition designs

- Source: JRSSB, 2026-04-27; Liushan Zhou, Ze Liu, Min-Qian Liu et al.; DOI: [10.1093/jrsssb/qkag064](https://doi.org/10.1093/jrsssb/qkag064)
- Open question: Can order-of-addition experiments be made model-free, economical, and robust to model uncertainty?
- Assumptions to recover: responses depend on component order, limited run budget, model uncertainty, stratum orthogonality criterion.
- Expected theoretical results:
  - Define stratum order-of-addition designs.
  - Prove orthogonality properties of different strengths.
  - Show that the designs reduce run size while retaining robustness across plausible response models.

### experimental_design_05: Gaussianized design optimization for covariate balance in randomized experiments

- Source: JRSSB, 2026-04-22; Wenxuan Guo, Tengyuan Liang, Panos Toulis; DOI: [10.1093/jrsssb/qkag067](https://doi.org/10.1093/jrsssb/qkag067)
- Open question: How can randomized experiments optimize covariate balance for binary and nonbinary treatments without heuristic tuning?
- Assumptions to recover: randomized experiment, covariate balance objective, treatments represented through Gaussianized assignments, continuous optimization over covariance matrices.
- Expected theoretical results:
  - Translate covariate-balance design into a Gaussian covariance optimization problem.
  - Establish balance and precision properties of the resulting assignments.
  - Show extension beyond binary-treatment rerandomization.

## Sequential, Changepoint, and Anytime-Valid Inference

Topic test: Can a system preserve inferential validity after optional stopping, online detection, and data-dependent changepoint localization?

### sequential_change_anytime_01: Inference for structural changes in nonstationary functional time series with partial measurement error

- Source: JRSSB, 2026-05-19; Lujia Bai, Qirui Hu, Weichi Wu; DOI: [10.1093/jrsssb/qkag072](https://doi.org/10.1093/jrsssb/qkag072)
- Open question: How can structural breaks be detected and localized in locally stationary functional time series observed with partial measurement error?
- Assumptions to recover: locally stationary functional time series, possibly discontinuous trajectories, heterogeneous partial measurement error, no presmoothing or dimension reduction.
- Expected theoretical results:
  - Construct bootstrap-assisted tests for structural breaks.
  - Prove asymptotic size control and local-alternative detection.
  - Derive localization guarantees for estimated changepoints.

### sequential_change_anytime_02: Sequential model confidence sets

- Source: JRSSB, 2026-05-13; Sebastian Arnold, Georgios Gavrilopoulos, Benedikt Schulz et al.; DOI: [10.1093/jrsssb/qkag066](https://doi.org/10.1093/jrsssb/qkag066)
- Open question: How can model confidence sets be updated sequentially when model evaluation happens over time rather than at a fixed sample size?
- Assumptions to recover: candidate model set, loss or performance process, sequential evaluation, selection uncertainty.
- Expected theoretical results:
  - Extend model confidence sets to a sequential setting.
  - Prove coverage of the best model set under optional monitoring.
  - Give elimination or updating rules with controlled error over time.

### sequential_change_anytime_03: Post-detection inference for sequential changepoint localization

- Source: JRSSB, 2026-04-27; Aytijhya Saha, Aaditya Ramdas; DOI: [10.1093/jrsssb/qkag069](https://doi.org/10.1093/jrsssb/qkag069)
- Open question: After a sequential detector stops and declares a change, how can one form valid confidence sets for the changepoint?
- Assumptions to recover: data-dependent stopping time, arbitrary sequential detection algorithm, unknown changepoint, minimal distributional assumptions.
- Expected theoretical results:
  - Build post-detection confidence sets using only data observed up to the stopping time.
  - Prove nonasymptotic validity for broad pre/postchange classes.
  - Extend the construction to composite prechange settings.

### sequential_change_anytime_04: Combining evidence across filtrations

- Source: JRSSB, 2026-04-08; Yo Joong Choe, Aaditya Ramdas; DOI: [10.1093/jrsssb/qkag058](https://doi.org/10.1093/jrsssb/qkag058)
- Open question: How can evidence from anytime-valid e-processes built on different filtrations be combined without losing validity?
- Assumptions to recover: composite null hypothesis, e-processes or test martingales, multiple filtrations, optional stopping.
- Expected theoretical results:
  - Identify why simple averaging fails across filtrations.
  - Construct a valid cross-filtration evidence-combination method.
  - Prove anytime validity for randomness, independence, or forecast-evaluation examples.

### sequential_change_anytime_05: Anytime validity is free: inducing sequential tests

- Source: JRSSB, 2026-02-21; Nick W Koning, Sam van Meer; DOI: [10.1093/jrsssb/qkag050](https://doi.org/10.1093/jrsssb/qkag050)
- Open question: Is anytime validity necessarily less powerful than a fixed-sample valid test?
- Assumptions to recover: finite maximum sample size, valid fixed-sample test, sequential stopping rule, conditional significance reuse.
- Expected theoretical results:
  - Show how to induce an anytime-valid test from any valid fixed-N test.
  - Prove the induced test matches the fixed-sample test at N.
  - Establish validity for procedures that use a test outcome as a conditional significance level.

## High-Dimensional Inference, PCA, and Dimension Reduction

Topic test: Can a system derive inference and estimation guarantees when dimension, dependence, and weak identifiability break classical fixed-p theory?

### high_dimensional_inference_01: Generalized Grade-of-Membership Estimation for High-dimensional Locally Dependent Data

- Source: JASA, 2026-05-18; Ling Chen, Chengzhu Huang, Yuqi Gu; DOI: [10.1080/01621459.2026.2670011](https://doi.org/10.1080/01621459.2026.2670011)
- Open question: How can mixed-membership grade-of-membership models be estimated scalably for high-dimensional locally dependent categorical data?
- Assumptions to recover: multivariate categorical responses, high-dimensional polytomous items, mixed-membership simplex structure, local dependence.
- Expected theoretical results:
  - Reformulate the model as a three-way quasi-tensor problem.
  - Develop a scalable flattening and estimation procedure.
  - Prove high-dimensional estimation guarantees for membership and model parameters.

### high_dimensional_inference_02: High-Dimensional Statistical Inference and Variable Selection Using Sufficient Dimension Association

- Source: JASA, 2026-04-28; Shangyuan Ye, Shauna Rakshe, Ye Liang; DOI: [10.1080/01621459.2026.2632869](https://doi.org/10.1080/01621459.2026.2632869)
- Open question: Can variable selection and inference work in high dimensions without specifying a sparse linear regression model?
- Assumptions to recover: high-dimensional predictors, conditional association target, possible nonlinear or misspecified regression, sufficient dimension association.
- Expected theoretical results:
  - Define sufficient dimension association for conditional predictor-response relevance.
  - Develop variable-selection and inference procedures without a parametric regression form.
  - Prove validity under high-dimensional asymptotics beyond sparse linear models.

### high_dimensional_inference_03: Rank tests for PCA under weak identifiability

- Source: Annals of Statistics, 2026-04-01; Davy Paindaveine, Laura Peralvo Maroto, Thomas Verdebout; DOI: [10.1214/25-aos2552](https://doi.org/10.1214/25-aos2552)
- Open question: How should leading-eigenvector hypotheses in PCA be tested when the leading eigengap vanishes and identifiability becomes weak?
- Assumptions to recover: elliptical triangular array, p-dimensional shape matrices, leading eigenvalue ratio approaches one, rank-based testing.
- Expected theoretical results:
  - Analyze limiting experiments under weak identifiability.
  - Derive rank-test limiting distributions for PCA directions.
  - Show robustness of rank procedures in near-unidentified eigenvector regimes.

### high_dimensional_inference_04: Spectrum-aware debiasing: A modern inference framework with applications to principal components regression

- Source: Annals of Statistics, 2026-04-01; Yufan Li, Pragya Sur; DOI: [10.1214/25-aos2586](https://doi.org/10.1214/25-aos2586)
- Open question: How can high-dimensional regression estimators be debiased under structured dependence, heavy tails, or latent low-rank structure?
- Assumptions to recover: high-dimensional regression, structured row-column dependence, non-sub-Gaussian or asymmetric covariates, spectral information in design/noise.
- Expected theoretical results:
  - Introduce spectrum-aware debiasing via a rescaled gradient step.
  - Prove inference validity beyond iid sub-Gaussian designs.
  - Apply the framework to principal-components regression and related estimators.

### high_dimensional_inference_05: Generalized multilinear models for sufficient dimension reduction on tensor-valued predictors

- Source: Annals of Statistics, 2026-04-01; Daniel Kapla, Efstathia Bura; DOI: [10.1214/25-aos2598](https://doi.org/10.1214/25-aos2598)
- Open question: How can sufficient dimension reduction be generalized to tensor-valued predictors in regression or classification?
- Assumptions to recover: tensor-valued predictors, quadratic exponential family inverse model, multilinear low-dimensional reductions, continuous or binary predictors.
- Expected theoretical results:
  - Derive multilinear sufficient reductions for supervised learning.
  - Construct estimators for continuous and binary tensor predictors.
  - Prove consistency and asymptotic normality using manifold theory.

## Statistical Learning, Deep Nonparametrics, and Prediction Risk

Topic test: Can a system move from prediction algorithms to inferential procedures with rates, regret bounds, and uncertainty quantification?

### statistical_learning_nonparametric_01: Inference for Deep Neural Network Estimators in Generalized Nonparametric Models

- Source: JASA, 2026-05-21; Xuran Meng, Yi Li; DOI: [10.1080/01621459.2026.2637894](https://doi.org/10.1080/01621459.2026.2637894)
- Open question: How can one build valid inference for subject-specific means estimated by deep neural networks in generalized nonparametric models?
- Assumptions to recover: generalized nonparametric regression model, categorical or exponential-family outcomes, DNN estimator, dependence between estimation error and inputs.
- Expected theoretical results:
  - Establish error bounds for DNN estimators without independence of errors and inputs.
  - Construct ensemble subsampling inference using U-statistic ideas.
  - Prove asymptotic validity for subject-specific mean inference.

### statistical_learning_nonparametric_02: Robust Unsupervised Multi-task and Transfer Learning on Gaussian Mixture Models

- Source: JASA, 2026-05-18; Ye Tian, Haolei Weng, Lucy Xia et al.; DOI: [10.1080/01621459.2026.2670031](https://doi.org/10.1080/01621459.2026.2670031)
- Open question: How can unsupervised transfer across Gaussian mixture tasks remain minimax-optimal when some tasks are unrelated outliers?
- Assumptions to recover: multiple Gaussian mixture-model tasks, unknown similarity across tasks, fraction of arbitrary outlier tasks, EM-type estimation.
- Expected theoretical results:
  - Develop a robust multitask GMM learning procedure.
  - Prove minimax-optimal convergence rates under task relatedness and contamination.
  - Show transfer gains over single-task learning when similarity is present.

### statistical_learning_nonparametric_03: Deep P-Spline: Theory, Fast Tuning, and Application

- Source: JASA, 2026-05-18; Noah Yi-Ting Hung, Li-Hsiang Lin, Vince D. Calhoun; DOI: [10.1080/01621459.2026.2671447](https://doi.org/10.1080/01621459.2026.2671447)
- Open question: Can neural-network architecture selection be treated as penalized spline knot selection with theory and fast tuning?
- Assumptions to recover: regression with DNNs, basis-expansion analogy, difference penalty for neuron or knot selection, latent-variable ECM tuning.
- Expected theoretical results:
  - Define the Deep P-Spline model class and penalty.
  - Derive theoretical guarantees for approximation or estimation under the penalized formulation.
  - Provide efficient tuning algorithms with statistical justification.

### statistical_learning_nonparametric_04: Contextual Online Uncertainty-Aware Preference Learning for Human Feedback

- Source: JASA, 2026-05-18; Nan Lu, Ethan Lee, Ethan X. Fang et al.; DOI: [10.1080/01621459.2026.2668736](https://doi.org/10.1080/01621459.2026.2668736)
- Open question: How can online preference learning from human feedback optimize decisions while supporting inference on the optimal model?
- Assumptions to recover: dynamic contextual information, dependent online preference outcomes, human-feedback comparisons, regret and asymptotic inference targets.
- Expected theoretical results:
  - Construct an online decision strategy for contextual preference data.
  - Prove an optimal regret bound.
  - Derive asymptotic distributions for estimators despite adaptive dependence.

### statistical_learning_nonparametric_05: Efficient Human-in-the-Loop Active Learning: A Novel Framework for Data Labeling in AI Systems

- Source: JASA, 2026-05-11; Yiran Huang, Jian-Feng Yang, Haoda Fu; DOI: [10.1080/01621459.2026.2656455](https://doi.org/10.1080/01621459.2026.2656455)
- Open question: How should active learning allocate expert labeling effort when query schemes themselves may differ in cost or information?
- Assumptions to recover: unlabeled data pool, expert human labels, multiple query schemes, classification or prediction target.
- Expected theoretical results:
  - Formulate human-in-the-loop active learning with query-scheme choice.
  - Develop efficient labeling rules for modern AI systems.
  - Prove statistical efficiency or risk reduction relative to standard active learning baselines.

## Robustness, Privacy, Federated, and Distributed Statistics

Topic test: Can a system derive guarantees under contamination, privacy noise, adversarial workers, and distribution shift?

### robust_privacy_distributed_01: Scalable and Robust Regression Models for Continuous Proportional Data

- Source: JASA, 2026-05-18; Changwoo J. Lee, Benjamin K. Dahl, Otso Ovaskainen et al.; DOI: [10.1080/01621459.2026.2626081](https://doi.org/10.1080/01621459.2026.2626081)
- Open question: How can regression for continuous proportional responses remain scalable and robust to beta-model misspecification and outliers?
- Assumptions to recover: continuous response on unit interval, generalized linear modeling, misspecification or outliers, scalability constraints.
- Expected theoretical results:
  - Define a robust regression model class for proportional data.
  - Derive estimation and inference theory under misspecification.
  - Show robustness and scalability relative to beta regression.

### robust_privacy_distributed_02: Edgeworth Accountant: An Analytical Approach to Differential Privacy Composition

- Source: JASA, 2026-05-18; Hua Wang, Sheng Gao, Huanyu Zhang et al.; DOI: [10.1080/01621459.2026.2668139](https://doi.org/10.1080/01621459.2026.2668139)
- Open question: How can the privacy loss of many composed private algorithms be computed analytically and accurately?
- Assumptions to recover: composition of private mechanisms, privacy-loss random variables, Edgeworth expansion, target overall privacy accounting.
- Expected theoretical results:
  - Introduce an Edgeworth-accountant approximation to composed privacy loss.
  - Derive analytical privacy-composition formulas with error control.
  - Compare accuracy and efficiency to existing numerical privacy accountants.

### robust_privacy_distributed_03: Byzantine-tolerant distributed learning of finite mixture models

- Source: JRSSB, 2026-04-16; Qiong Zhang, Yan Shuo Tan, Jiahua Chen; DOI: [10.1093/jrsssb/qkag065](https://doi.org/10.1093/jrsssb/qkag065)
- Open question: How can finite mixture models be learned over distributed machines when labels may switch and some machines are Byzantine?
- Assumptions to recover: split-and-conquer distributed data, finite mixture model, label switching across local estimators, Byzantine or corrupted workers.
- Expected theoretical results:
  - Construct a label-aligned distributed estimator robust to Byzantine machines.
  - Prove consistency and convergence rates for mixture parameters.
  - Quantify tolerance to worker corruption.

### robust_privacy_distributed_04: Model privacy: a unified framework for understanding model stealing attacks and defences

- Source: JRSSB, 2026-04-02; Ganghua Wang, Yuhong Yang, Jie Ding; DOI: [10.1093/jrsssb/qkag059](https://doi.org/10.1093/jrsssb/qkag059)
- Open question: Can model stealing and defenses be represented in a unified statistical privacy framework?
- Assumptions to recover: query-response access to a learned model, adversarial model recovery, defense mechanisms, model privacy metric.
- Expected theoretical results:
  - Formalize model privacy for stealing attacks and defenses.
  - Derive risk or identifiability limits for model recovery under query constraints.
  - Unify common attacks and defenses under one theoretical framework.

### robust_privacy_distributed_05: Versatile differentially private learning for general loss functions

- Source: Annals of Statistics, 2026-04-01; Qilong Lu, Song Xi Chen, Yumou Qiu; DOI: [10.1214/25-aos2583](https://doi.org/10.1214/25-aos2583)
- Open question: Can local differential privacy be made analysis-agnostic for general loss functions and repeated downstream analyses?
- Assumptions to recover: local privacy setting, general empirical loss functions, zero-inflated symmetric multivariate Laplace noise, online or increasing data volume.
- Expected theoretical results:
  - Define the ZIL privacy mechanism and its trade-off function.
  - Prove local differential privacy guarantees without specifying downstream analysis tasks.
  - Develop unified estimation and inference theory under the privatized release.

## Bayesian Computation, Priors, and Posterior Calibration

Topic test: Can a system reason about posterior computation and calibration when likelihoods, geometries, or tuning parameters are nonstandard?

### bayesian_computation_posteriors_01: GS-BART: Bayesian Additive Regression Trees with Graph-split Decision Rules

- Source: JASA, 2026-04-28; Shuren He, Huiyan Sang, Quan Zhou; DOI: [10.1080/01621459.2026.2655550](https://doi.org/10.1080/01621459.2026.2655550)
- Open question: How can Bayesian additive regression trees split on graph-structured predictors while retaining statistical interpretability?
- Assumptions to recover: BART prior, graph-structured covariates, graph-split decision rules, nonparametric regression.
- Expected theoretical results:
  - Define graph-split BART priors and tree moves.
  - Derive posterior or predictive consistency/inference properties for graph-structured splits.
  - Show how graph constraints improve interpretability without losing flexibility.

### bayesian_computation_posteriors_02: Translating Predictive Distributions into Informative Priors

- Source: JASA, 2026-04-22; Andrew A. Manderson, Robert J. B. Goudie; DOI: [10.1080/01621459.2026.2614034](https://doi.org/10.1080/01621459.2026.2614034)
- Open question: How can predictive distributions from one analysis be translated into informative priors for a subsequent model?
- Assumptions to recover: available predictive distribution, target Bayesian model, prior elicitation through prediction, uncertainty propagation.
- Expected theoretical results:
  - Define a mapping from predictive distributions to prior distributions.
  - Prove calibration or coherence properties of the translated prior.
  - Characterize when the induced prior preserves predictive uncertainty.

### bayesian_computation_posteriors_03: Parallel computations for Metropolis Markov chains with Picard maps

- Source: Biometrika, 2026-03-31; S Grazzi, G Zanella; DOI: [10.1093/biomet/asag022](https://doi.org/10.1093/biomet/asag022)
- Open question: Can zeroth-order Metropolis chains be simulated faster using parallel Picard-map computations?
- Assumptions to recover: random-walk Metropolis, log-concave target on R^d, gradient-free computation, parallel processors.
- Expected theoretical results:
  - Construct Picard-map parallel algorithms for Metropolis chains.
  - Prove mixing or approximation guarantees in O(d) or O(1) parallel iterations under stated targets.
  - Quantify the speedup over sequential simulation.

### bayesian_computation_posteriors_04: Sequential Gibbs Posteriors with Applications to Principal Component Analysis

- Source: Biometrika, 2026-03-24; Steven Winter, Omar Melikechi, David B Dunson; DOI: [10.1093/biomet/asag020](https://doi.org/10.1093/biomet/asag020)
- Open question: How can Gibbs posteriors be sequentially calibrated so credible regions attain frequentist coverage?
- Assumptions to recover: Gibbs posterior based on exponentiated loss, single tuning parameter causes poor uncertainty calibration, sequential updating, PCA application.
- Expected theoretical results:
  - Define sequential Gibbs posteriors with adaptive information weighting.
  - Prove coverage calibration or asymptotic uncertainty validity.
  - Demonstrate the theory for principal-component analysis.

### bayesian_computation_posteriors_05: Geodesic slice sampling on Riemannian manifolds

- Source: Biometrika, 2026-02-06; Alain Durmus, Samuel Gruffaz, Mareike Hasenpflug et al.; DOI: [10.1093/biomet/asag006](https://doi.org/10.1093/biomet/asag006)
- Open question: How can slice sampling be generalized to posterior distributions on Riemannian manifolds such as Stiefel or Grassmann spaces?
- Assumptions to recover: target probability measure on a Riemannian manifold, geodesic paths, slice-sampling construction, manifold-valued Bayesian parameters.
- Expected theoretical results:
  - Define geodesic slice sampling as a manifold MCMC method.
  - Prove invariance and convergence properties for the target measure.
  - Show practical applicability to matrix-valued Bayesian inference.

## Networks, Graphs, and Relational Dependence

Topic test: Can a system model network dependence, latent communities, and graph-valued observations with identifiable and computationally tractable inference?

### networks_graphs_01: Inferences on mixing probabilities and ranking in mixed-membership models

- Source: JASA, 2026-05-18; Sohom Bhattacharya, Jianqing Fan, Jikai Hou; DOI: [10.1080/01621459.2026.2671448](https://doi.org/10.1080/01621459.2026.2671448)
- Open question: How can mixed-membership network models support inference on node mixing probabilities and ranking?
- Assumptions to recover: degree-corrected mixed-membership model, network latent structure, node-level mixed membership, ranking target.
- Expected theoretical results:
  - Develop estimators for mixing probabilities in mixed-membership networks.
  - Derive asymptotic inference for membership and ranking functionals.
  - Quantify uncertainty in latent network rankings.

### networks_graphs_02: Nonparametric Inference for Balance in Signed Networks

- Source: Biometrika, 2026-04-28; Xuyang Chen, Yinjie Wang, Weijing Tang; DOI: [10.1093/biomet/asag031](https://doi.org/10.1093/biomet/asag031)
- Open question: How can one test social-balance theory nonparametrically in signed networks?
- Assumptions to recover: signed network with positive and negative ties, balance-theory generating process, nonparametric null/alternative, network dependence.
- Expected theoretical results:
  - Characterize a signed-network data-generating process tied to balance theory.
  - Construct nonparametric tests or estimators for balance.
  - Prove validity and consistency under network dependence.

### networks_graphs_03: Autoregressive networks with dependent edges

- Source: JRSSB, 2026-04-16; Jinyuan Chang, Qin Fang, Eric D Kolaczyk et al.; DOI: [10.1093/jrsssb/qkag063](https://doi.org/10.1093/jrsssb/qkag063)
- Open question: How can dynamic networks be modeled autoregressively while allowing dependent edges such as transitivity and degree heterogeneity?
- Assumptions to recover: time-indexed network sequence, conditional edge independence given lagged network, dependent-edge features, increasing parameter dimension.
- Expected theoretical results:
  - Define autoregressive network models connected to temporal ERGMs.
  - Derive MLE or improved estimator theory in high-dimensional parameter settings.
  - Prove convergence rates and support simulation/inference.

### networks_graphs_04: Estimation of grouped time-varying network vector autoregressive models

- Source: Annals of Statistics, 2026-04-01; Degui Li, Bin Peng, Songqiao Tang et al.; DOI: [10.1214/25-aos2580](https://doi.org/10.1214/25-aos2580)
- Open question: How can large-scale network vector autoregressions estimate time-varying momentum and spillover effects when nodes form latent groups?
- Assumptions to recover: network vector autoregression, time-varying coefficients, latent group structure, local smoothing.
- Expected theoretical results:
  - Estimate the number and membership of latent groups consistently.
  - Derive group-specific local-linear estimators for time-varying effects.
  - Prove improved convergence relative to nodewise estimation.

### networks_graphs_05: Inferring the dependence graph density of binary graphical models in high dimension

- Source: Annals of Statistics, 2026-04-01; Julien Chevallier, Eva Löcherbach, Guilherme Ost; DOI: [10.1214/25-aos2592](https://doi.org/10.1214/25-aos2592)
- Open question: Can the density of an unknown dependence graph be inferred from high-dimensional binary interacting chains?
- Assumptions to recover: binary interacting chains, directed Erdos-Renyi dependence graph, excitatory and inhibitory populations, observation over T time units.
- Expected theoretical results:
  - Construct estimators for the graph connectivity parameter.
  - Establish identifiability and consistency from chain observations.
  - Derive high-dimensional rates depending on number of chains and time horizon.

## Geometric, Spatial, Functional, and Point-Process Inference

Topic test: Can a system extend classical asymptotic theory to data living on graphs, manifolds, spatial fields, functions, or point processes?

### geometric_spatial_point_process_01: A parameterization of anisotropic Gaussian fields with penalized complexity priors

- Source: JASA, 2026-05-18; L. Llamazares-Elias, J. Latz, F. Lindgren; DOI: [10.1080/01621459.2026.2670016](https://doi.org/10.1080/01621459.2026.2670016)
- Open question: How can anisotropic Gaussian random fields be parametrized so Bayesian SPDE priors encode meaningful covariance structure under limited likelihood information?
- Assumptions to recover: Gaussian random fields via SPDEs, anisotropic correlation length and diffusion matrix, in-fill asymptotics, penalized complexity priors.
- Expected theoretical results:
  - Construct a smooth invertible anisotropy parametrization.
  - Define penalized complexity priors for correlation and diffusion structure.
  - Analyze posterior or inferential behavior when likelihood information is weak.

### geometric_spatial_point_process_02: Statistical inference for Gaussian Whittle–Matérn fields on metric graphs

- Source: JRSSB, 2026-05-11; David Bolin, Alexandre B Simas, Jonas Wallin; DOI: [10.1093/jrsssb/qkag074](https://doi.org/10.1093/jrsssb/qkag074)
- Open question: How can Gaussian Whittle-Matern fields on compact metric graphs support likelihood inference and optimal prediction?
- Assumptions to recover: compact metric graph, fractional-order stochastic differential equation, Gaussian Whittle-Matern field, possibly misspecified parameters.
- Expected theoretical results:
  - Prove consistency and asymptotic normality of maximum likelihood estimators.
  - Give necessary and sufficient conditions for optimal prediction under misspecification.
  - Handle unavailable closed-form covariance through operator-based inference.

### geometric_spatial_point_process_03: Nonparametric estimators over metric graphs

- Source: Biometrika, 2026-04-15; Aldo Clemente, Eleonora Arnone, Jorge Mateu et al.; DOI: [10.1093/biomet/asag029](https://doi.org/10.1093/biomet/asag029)
- Open question: How can penalized likelihood methods be defined for regression and density estimation when data live over metric graphs?
- Assumptions to recover: functional spaces on metric graphs, graph-supported observations, penalized likelihood, nonparametric regression and density estimation.
- Expected theoretical results:
  - Develop Sobolev-type functional analysis on metric graphs including Poincare inequalities.
  - Prove well-posedness of graph-based penalized likelihood estimators.
  - Establish consistency or convergence rates for regression and density estimation on graphs.

### geometric_spatial_point_process_04: Generalized point process additive models

- Source: JRSSB, 2026-04-13; Kuang-Yao Lee, Jiehuan Sun, Bing Li et al.; DOI: [10.1093/jrsssb/qkag061](https://doi.org/10.1093/jrsssb/qkag061)
- Open question: How can scalar responses be regressed on high-dimensional point-process predictors with sparsity and low-dimensional structure?
- Assumptions to recover: point-process predictors as random counting measures, kernel embedding for random measures, additive or reduced-basis structure, penalized likelihood.
- Expected theoretical results:
  - Define generalized point-process additive models.
  - Develop penalized-likelihood estimation for point-process covariates.
  - Prove estimation consistency and selection consistency as predictor complexity grows.

### geometric_spatial_point_process_05: Palm distributions of superposed point processes for statistical inference

- Source: Biometrika, 2026-03-28; M Beraha, F Camerlenghi, L Ghilotti; DOI: [10.1093/biomet/asag021](https://doi.org/10.1093/biomet/asag021)
- Open question: What is the Palm distribution of a superposition of independent point processes, and how can it support inference for corrupted point processes?
- Assumptions to recover: independent point-process superposition, Palm distributions and moment measures, minimum contrast estimation, shot-noise Cox processes.
- Expected theoretical results:
  - Derive a mixture representation for Palm distributions of superposed point processes.
  - Apply the result to minimum contrast estimation for corrupted processes.
  - Obtain explicit higher-order Palm and Janossy expressions in relevant finite cases.

## Multiple Testing, Conformal Inference, and Selection

Topic test: Can a system control error rates after model selection, multiple comparisons, conformal calibration, or reinforcement-learning variable screening?

### multiple_testing_conformal_selection_01: Sequential Knockoffs for Variable Selection in Reinforcement Learning

- Source: JASA, 2026-05-01; Tao Ma, Jin Zhu, Hengrui Cai et al.; DOI: [10.1080/01621459.2026.2658863](https://doi.org/10.1080/01621459.2026.2658863)
- Open question: How can one identify a minimal sufficient state in reinforcement learning while controlling false discoveries among state variables?
- Assumptions to recover: Markov decision process, oversized state representation, minimal sufficient state, sequential knockoff variable selection.
- Expected theoretical results:
  - Define minimal sufficient state for MDPs.
  - Construct sequential knockoffs for state-variable selection.
  - Prove false-discovery control and Markov sufficiency guarantees.

### multiple_testing_conformal_selection_02: Structured Conformal Inference for Matrix Completion with Applications to Group Recommender Systems

- Source: JASA, 2026-04-28; Ziyi Liang, Tianmin Xie, Xin Tong et al.; DOI: [10.1080/01621459.2026.2658287](https://doi.org/10.1080/01621459.2026.2658287)
- Open question: Can conformal inference give joint uncertainty regions for groups of missing entries in matrix completion?
- Assumptions to recover: sparsely observed matrix, black-box matrix-completion algorithm, group of missing entries, exchangeability or conformal calibration structure.
- Expected theoretical results:
  - Construct structured conformal confidence regions for grouped matrix entries.
  - Prove model-agnostic coverage guarantees.
  - Show how joint regions improve group recommendation uncertainty over entrywise intervals.

### multiple_testing_conformal_selection_03: Finding Distributions that Differ, with False Discovery Rate Control

- Source: Biometrika, 2026-04-04; Yonghoon Lee, Edgar Dobriban, Eric Tchetgen Tchetgen; DOI: [10.1093/biomet/asag025](https://doi.org/10.1093/biomet/asag025)
- Open question: How can one identify which comparison distributions differ from a reference distribution while controlling FDR exactly and distribution-free?
- Assumptions to recover: one reference sample, multiple comparison-group samples, two-sample distributional differences, batch conformal p-values.
- Expected theoretical results:
  - Define batch conformal p-values for distribution comparison.
  - Prove positive regression dependence across groups.
  - Combine with Benjamini-Hochberg to obtain exact distribution-free FDR control.

### multiple_testing_conformal_selection_04: Large-scale multiple testing: Fundamental limits of false discovery rate control and compound oracle

- Source: Annals of Statistics, 2026-04-01; Yutong Nie, Yihong Wu; DOI: [10.1214/25-aos2581](https://doi.org/10.1214/25-aos2581)
- Open question: What is the optimal asymptotic trade-off between false discovery rate and false nondiscovery rate in large-scale testing?
- Assumptions to recover: two-group random mixture model, many hypotheses, FDR and FNR criteria, compound-oracle benchmark.
- Expected theoretical results:
  - Characterize the asymptotically optimal FDR-FNR trade-off.
  - Define and analyze the compound oracle beyond separable decision rules.
  - Establish fundamental limits for large-scale multiple testing procedures.

### multiple_testing_conformal_selection_05: Assumption-lean post-integrated inference with surrogate-control outcomes

- Source: Biometrika, 2026-02-03; Jin-Hong Du, Kathryn Roeder, Larry Wasserman; DOI: [10.1093/biomet/asag004](https://doi.org/10.1093/biomet/asag004)
- Open question: How can multiple testing after data integration remain valid when embeddings are data-dependent and latent heterogeneity is present?
- Assumptions to recover: high-dimensional outcomes, data integration embeddings, surrogate-control or negative-control outcomes, hidden mediators, confounders, and moderators.
- Expected theoretical results:
  - Use control outcomes to identify projected direct-effect estimands after integration.
  - Develop semiparametric and doubly robust inference under misspecification and error-prone embeddings.
  - Prove bias quantifications, finite-sample linear expansions, and uniform concentration bounds for data-adaptive estimation.

## Extremes, Tail Risk, Heavy Tails, and Robust Limits

Topic test: Can a system derive asymptotics when classical finite-moment, light-tail, or central-limit assumptions fail?

### extremes_tail_heavytail_01: Tail Risk in the Tail: Estimating High Quantiles When a Related Variable is Extreme

- Source: JASA, 2026-05-21; Natalia Nolde, Chen Zhou, Menglin Zhou; DOI: [10.1080/01621459.2026.2640643](https://doi.org/10.1080/01621459.2026.2640643)
- Open question: How can high quantiles of one variable be estimated conditional on another related variable being extreme?
- Assumptions to recover: bivariate tail dependence, conditional high quantile target, univariate high-quantile estimator as component, weak tail conditions.
- Expected theoretical results:
  - Construct a tail-dependence adjustment factor for conditional high quantiles.
  - Establish asymptotic behavior of the estimator under weak conditions.
  - Apply the theory to conditional value-at-risk style systemic-risk measures.

### extremes_tail_heavytail_02: Beyond the mean: limit theory and tests for infinite-mean autoregressive conditional durations

- Source: JRSSB, 2026-03-30; Giuseppe Cavaliere, Thomas Mikosch, Anders Rahbek et al.; DOI: [10.1093/jrsssb/qkag053](https://doi.org/10.1093/jrsssb/qkag053)
- Open question: How can integrated autoregressive conditional duration models be analyzed when durations have infinite means?
- Assumptions to recover: integrated ACD model, infinite expected duration, random number of durations over fixed time, quasi-maximum likelihood.
- Expected theoretical results:
  - Develop a unified limit theory for QMLE in integrated ACD models.
  - Handle breakdown of conventional asymptotics under infinite means.
  - Build tests based on the new limiting results.

### extremes_tail_heavytail_03: Characterizing extremal dependence on a hyperplane

- Source: Biometrika, 2026-03-03; P Wan; DOI: [10.1093/biomet/asag015](https://doi.org/10.1093/biomet/asag015)
- Open question: How can extremal dependence among asymptotically dependent variables be represented on a linear hyperplane?
- Assumptions to recover: d asymptotically dependent variables, hyperplane perpendicular to all-ones vector, multivariate extremes, tail-dependence approximation.
- Expected theoretical results:
  - Represent extremal dependence by random vectors on a (d-1)-dimensional hyperplane.
  - Use the representation to enable PCA-like low-dimensional tail approximations.
  - Characterize the Husler-Reiss family through a Gaussian law on the hyperplane.

### extremes_tail_heavytail_04: Information theoretic limits of robust sub-Gaussian mean estimation under star-shaped constraints

- Source: Annals of Statistics, 2026-02-01; Akshay Prasadan, Matey Neykov; DOI: [10.1214/25-aos2576](https://doi.org/10.1214/25-aos2576)
- Open question: What are the minimax limits for robust sub-Gaussian mean estimation under star-shaped constraints and adversarial corruption?
- Assumptions to recover: Gaussian or sub-Gaussian mean model, bounded star-shaped constraint set, epsilon-fraction adversarial corruption, squared l2 loss.
- Expected theoretical results:
  - Derive minimax risk rates in terms of local entropy, corruption fraction, variance, and set diameter.
  - Construct algorithms attaining the rates under known or symmetric noise settings.
  - Show matching lower bounds for robust constrained mean estimation.

### extremes_tail_heavytail_05: Tail-robust factor modelling of vector and tensor time series in high dimensions

- Source: Biometrika, 2025-12-26; Matteo Barigozzi, Haeran Cho, Hyeyoung Maeng; DOI: [10.1093/biomet/asaf093](https://doi.org/10.1093/biomet/asaf093)
- Open question: How can vector and tensor time-series factor models be estimated consistently under heavy tails?
- Assumptions to recover: high-dimensional vector or tensor time series, heavy-tailed observations, factor model, data truncation plus tensor decomposition.
- Expected theoretical results:
  - Develop a two-step truncated tensor factor estimator.
  - Prove consistency and asymptotic normality under only low-order moment assumptions.
  - Derive rates that explicitly depend on tail heaviness and tensor dimensions.

## Missingness, Censoring, Measurement Error, and Data Integration

Topic test: Can a system repair inference when observed data are censored, biased, platform-shifted, or missing not at random?

### missing_censored_measurement_error_01: Accounting for Measurement Bias: A New Framework for Reliable Country Ranking in Large-Scale Educational Assessments

- Source: JASA, 2026-05-18; Jing Ouyang, Yunxiao Chen, Chengcheng Li et al.; DOI: [10.1080/01621459.2026.2670732](https://doi.org/10.1080/01621459.2026.2670732)
- Open question: How can country rankings from educational assessments remain reliable when item-response measurements contain cultural or linguistic bias?
- Assumptions to recover: large-scale educational assessment, item response theory ranking, measurement bias across countries/items, ranking uncertainty.
- Expected theoretical results:
  - Define a bias-adjusted ranking framework for IRT-based country comparisons.
  - Derive inference procedures that account for measurement bias.
  - Quantify ranking reliability under cross-country measurement noninvariance.

### missing_censored_measurement_error_02: Efficient Nonparametric Inference for Mediation Analysis with Nonignorable Missing Confounders

- Source: JASA, 2026-04-20; Jiawei Shan, Wei Li, Chunrong Ai; DOI: [10.1080/01621459.2026.2654218](https://doi.org/10.1080/01621459.2026.2654218)
- Open question: How can mediation effects be identified and estimated efficiently when confounders are nonignorably missing?
- Assumptions to recover: mediation analysis, nonignorable missing confounders, shadow variables from covariates or auxiliary data, ill-posed inverse problem.
- Expected theoretical results:
  - Define a shadow-variable identification framework for mediation effects.
  - Develop sieve iterative outward estimation.
  - Prove large-sample theory including asymptotic distribution and efficiency loss from missingness.

### missing_censored_measurement_error_03: Functional Principal Component Analysis for Sparse Censored Data

- Source: Biometrika, 2026-04-16; Caitrin Murphy, Eric Laber, Rhonda Merwin et al.; DOI: [10.1093/biomet/asag023](https://doi.org/10.1093/biomet/asag023)
- Open question: How can functional PCA be performed when functional observations are sparsely sampled and censored by instrument limits?
- Assumptions to recover: functional data, sparse observations, censoring/truncation at measurement boundaries, mean/covariance/eigenfunction estimation.
- Expected theoretical results:
  - Extend FPCA estimators to correct instrument-induced censoring.
  - Derive consistency and asymptotic behavior for mean, covariance, and scores.
  - Show naive FPCA is biased under censoring.

### missing_censored_measurement_error_04: Nonparametric inference for censored data using deep neural networks

- Source: JRSSB, 2026-04-02; Wen Su, Qiang Wu, Kin-Yat Liu et al.; DOI: [10.1093/jrsssb/qkag060](https://doi.org/10.1093/jrsssb/qkag060)
- Open question: Can deep neural networks support nonparametric hazard inference for right-censored survival data?
- Assumptions to recover: right-censored survival time, conditional hazard function, DNN approximation to log hazard, likelihood-based estimator.
- Expected theoretical results:
  - Construct a DNN likelihood estimator for conditional hazards.
  - Prove nonasymptotic error bounds and functional asymptotic normality.
  - Develop one-sample goodness-of-fit and two-sample comparison tests.

### missing_censored_measurement_error_05: Statistical inference for cell type deconvolution

- Source: JRSSB, 2026-03-17; Dongyue Xie, Lin Gui, Jingshu Wang; DOI: [10.1093/jrsssb/qkag054](https://doi.org/10.1093/jrsssb/qkag054)
- Open question: How can cell type deconvolution remain inferentially valid when reference and bulk data come from heterogeneous measurement platforms?
- Assumptions to recover: bulk RNA-seq and reference single-cell data, platform-specific scaling effects, measurement noise, external approximation of cell-type proportions.
- Expected theoretical results:
  - Introduce measurement-error-adjusted deconvolution.
  - Derive estimators and inference procedures accounting for reference uncertainty and platform shifts.
  - Show validity for downstream comparisons across individuals.

