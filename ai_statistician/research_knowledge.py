from __future__ import annotations

from pathlib import Path

from .research_schema import KnowledgeCard, OpenResearchQuestion, ResearchProblemSpec, TheoremGoal
from .retrieval import tokens


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESOURCE_ROOT = PROJECT_ROOT / "AI for Math Resources"
LEGACY_AI_STATISTICIAN_ROOT = PROJECT_ROOT / "legacy_sources" / "ai_statistician"
VENDORED_EMPIRICAL_PROCESS_ROOT = PROJECT_ROOT / "legacy_sources" / "emperical_process_lean"
LEAN_BLUEPRINT_ROOT = Path("/Users/yukang/.codex/external/leanblueprint")


KNOWLEDGE_CARDS: tuple[KnowledgeCard, ...] = (
    KnowledgeCard(
        id="aipw_double_robustness",
        title="AIPW / doubly robust causal estimation",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "For ATE under consistency, exchangeability, and positivity, the "
            "augmented inverse-probability weighted score combines outcome and "
            "propensity nuisance functions and is Neyman-orthogonal."
        ),
        tags=("causal", "ate", "semiparametric", "aipw", "efficiency", "semiparametric_causal_ate"),
    ),
    KnowledgeCard(
        id="split_conformal_prediction",
        title="Split conformal prediction",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "Under exchangeability, calibration residual quantiles yield finite "
            "sample marginal predictive coverage without distributional assumptions."
        ),
        tags=("conformal", "prediction", "coverage", "exchangeability", "distribution_free_conformal_prediction"),
    ),
    KnowledgeCard(
        id="right_censored_survival_kaplan_meier",
        title="Kaplan-Meier and Nelson-Aalen right-censored survival inference",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "Under independent right censoring, product-limit Kaplan-Meier and "
            "Nelson-Aalen counting-process estimators identify survival and "
            "cumulative hazard targets, with Greenwood-type fixed-time variance."
        ),
        tags=(
            "survival",
            "right_censored",
            "hazard",
            "kaplan_meier",
            "nelson_aalen",
            "censoring",
            "right_censored_survival_inference",
        ),
    ),
    KnowledgeCard(
        id="robust_mean_median_of_means",
        title="Median-of-means and robust mean inference",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "Median-of-means estimators split observations into blocks and take "
            "the median block mean, converting finite-variance concentration into "
            "robust deviation control under heavy tails and limited contamination."
        ),
        tags=(
            "robust",
            "mean",
            "median_of_means",
            "heavy_tails",
            "contamination",
            "minimax",
            "robust_mean_inference",
        ),
    ),
    KnowledgeCard(
        id="differential_privacy_gaussian_mechanism",
        title="Differential privacy via Gaussian mechanisms and private learning",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "For bounded-sensitivity statistical queries, Gaussian mechanisms add "
            "calibrated noise for epsilon-delta differential privacy. Private "
            "inference decomposes error into sampling variation, clipping or "
            "approximation bias, and privacy-noise variance; frontier extensions "
            "include composition accountants and local private learning for general losses."
        ),
        tags=(
            "differential_privacy",
            "privacy",
            "gaussian_mechanism",
            "private_learning",
            "privacy_composition",
            "local_privacy",
            "differential_privacy_learning",
        ),
    ),
    KnowledgeCard(
        id="nonparametric_sieve_regression_inference",
        title="Sieve, DNN, and penalized-spline nonparametric regression inference",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "Nonparametric regression inference decomposes pointwise error into "
            "sieve approximation bias, empirical estimation error, and noise. "
            "DNN and P-spline theory add approximation, tuning, and subsampling "
            "or U-statistic validity arguments on top of finite-sample estimator "
            "and concentration ingredients."
        ),
        tags=(
            "nonparametric",
            "regression",
            "sieve",
            "dnn",
            "deep_learning",
            "p_spline",
            "subsampling",
            "u_statistic",
            "nonparametric_regression_inference",
        ),
    ),
    KnowledgeCard(
        id="robust_distributed_model_privacy_inference",
        title="Robust proportional, Byzantine distributed, and model-privacy inference",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "This frontier class covers robust regression for bounded proportional "
            "responses, Byzantine-tolerant aggregation of distributed mixture-model "
            "fits, and query-response model privacy. The v0 release uses winsorized "
            "quasi-regression, label-aligned robust worker aggregation, and a noisy "
            "query-response defense simulator while full beta-regression robustness, "
            "mixture EM label-switching theory, Byzantine convergence rates, and "
            "model-stealing lower bounds remain formal gaps."
        ),
        tags=(
            "robust_regression",
            "proportional_response",
            "continuous_unit_interval",
            "byzantine",
            "distributed_learning",
            "finite_mixture",
            "label_switching",
            "model_privacy",
            "model_stealing",
            "robust_distributed_model_privacy_inference",
        ),
    ),
    KnowledgeCard(
        id="adaptive_transfer_active_preference_learning",
        title="Adaptive transfer, preference, and active-label learning inference",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "Adaptive statistical-learning problems include robust transfer across "
            "related Gaussian-mixture tasks with outlier tasks, online contextual "
            "preference learning from human feedback, and active labeling under "
            "query-scheme costs. The v0 release uses robust task-summary aggregation "
            "and finite-arm preference/query allocation while minimax transfer rates, "
            "adaptive regret theory, and active-learning risk proofs remain gaps."
        ),
        tags=(
            "transfer_learning",
            "multitask_learning",
            "gaussian_mixture",
            "preference_learning",
            "active_learning",
            "human_feedback",
            "online_learning",
            "adaptive_transfer_active_preference_learning",
        ),
    ),
    KnowledgeCard(
        id="network_graph_sbm_spectral_inference",
        title="Network graph inference via SBM edge density and spectral recovery",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "Graph-valued network inference can be release-gated through a dense "
            "stochastic-block-model surrogate: average adjacency indicators estimate "
            "edge density, while centered-adjacency spectral methods recover latent "
            "communities under separation. Mixed-membership, signed, dynamic, and "
            "graph-dependent frontier models require additional graph CLTs, matrix "
            "concentration, and network-autoregression formalization."
        ),
        tags=(
            "network",
            "graph",
            "sbm",
            "stochastic_block_model",
            "edge_density",
            "spectral",
            "community",
            "mixed_membership",
            "network_graph_inference",
        ),
    ),
    KnowledgeCard(
        id="bayesian_predictive_prior_calibration",
        title="Predictive-distribution-to-prior Bayesian calibration",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "Predictive-prior translation uses an external predictive distribution "
            "to construct an informative prior for a subsequent Bayesian model. "
            "A conjugate normal baseline exposes the key error decomposition: "
            "posterior shrinkage, sample noise, credible-interval calibration, "
            "and the formal gap between moment matching and full posterior coherence."
        ),
        tags=(
            "bayesian",
            "posterior",
            "prior",
            "predictive_distribution",
            "credible_interval",
            "calibration",
            "conjugate_normal",
            "bayesian_posterior_calibration",
        ),
    ),
    KnowledgeCard(
        id="bayesian_tree_mcmc_computation",
        title="Bayesian graph-split trees and parallel Metropolis computation",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "Bayesian computation frontier questions include graph-split BART priors "
            "for structured predictors and parallel Metropolis/Picard-map algorithms "
            "for log-concave targets. The v0 bridge uses graph-constrained boosted "
            "tree stumps and exact vectorized random-walk Metropolis chains, while "
            "BART posterior contraction, reversible tree moves, Picard-map stationarity, "
            "and parallel mixing-time theory remain explicit formal gaps."
        ),
        tags=(
            "bayesian",
            "bart",
            "graph_split",
            "tree_prior",
            "mcmc",
            "metropolis",
            "picard_map",
            "parallel_computation",
            "bayesian_tree_mcmc_computation",
        ),
    ),
    KnowledgeCard(
        id="geometric_spatial_point_process_inference",
        title="Geometric, spatial, metric-graph, and point-process inference",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "Geometric/spatial frontier papers require theory for data supported "
            "on metric graphs, manifolds, Gaussian random fields, and point "
            "processes. The v0 bridge uses metric-graph kernel smoothing and "
            "finite binned point-process intensity contrasts; full SPDE "
            "Whittle-Matern likelihood, graph Sobolev convergence, Palm kernels, "
            "and Janossy/Palm mixture identities remain explicit formal gaps."
        ),
        tags=(
            "geometric",
            "spatial",
            "metric_graph",
            "gaussian_field",
            "whittle_matern",
            "spde",
            "point_process",
            "palm_distribution",
            "geometric_spatial_point_process_inference",
        ),
    ),
    KnowledgeCard(
        id="measurement_bias_assessment_ranking",
        title="Measurement-bias-adjusted assessment ranking inference",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "Country or group rankings from large-scale assessments can be biased "
            "by cultural, linguistic, item, or platform measurement effects. A "
            "controlled additive baseline subtracts calibrated item and country/item "
            "bias terms before ranking latent abilities, while full IRT "
            "measurement-invariance and rank-functional theory remain formal gaps."
        ),
        tags=(
            "measurement_bias",
            "ranking",
            "educational_assessment",
            "item_response",
            "measurement_invariance",
            "measurement_bias_ranking_inference",
        ),
    ),
    KnowledgeCard(
        id="missing_mediation_deconvolution_inference",
        title="Missing-confounder mediation and platform-adjusted deconvolution inference",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "This class covers mediation analysis with nonignorable missing confounders "
            "using shadow variables or auxiliary data, and cell-type deconvolution when "
            "bulk/reference expression measurements come from heterogeneous platforms. "
            "The v0 executable layer uses shadow-variable confounder reconstruction and "
            "platform-scaled constrained least squares while nonparametric bridge "
            "identification, sieve inverse problems, reference uncertainty, and "
            "downstream comparison theory remain formal gaps."
        ),
        tags=(
            "missing_data",
            "mediation",
            "shadow_variable",
            "nonignorable_missingness",
            "cell_deconvolution",
            "bulk_rna_seq",
            "single_cell_reference",
            "platform_shift",
            "missing_mediation_deconvolution_inference",
        ),
    ),
    KnowledgeCard(
        id="design_based_variance_neyman",
        title="Design-based conservative variance estimation",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "For randomized experiments with fixed potential outcomes, the "
            "Neyman variance estimator is observable and conservative because "
            "the exact randomization variance subtracts unobserved unit-level "
            "treatment-effect heterogeneity."
        ),
        tags=(
            "experimental_design",
            "design_based",
            "variance",
            "randomization",
            "conservative_variance",
            "interference",
            "design_based_variance_inference",
        ),
    ),
    KnowledgeCard(
        id="experimental_design_maximin_balance",
        title="Maximin space-filling and covariate-balanced experimental design",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "Finite experimental-design optimization can be release-gated through "
            "a maximin/run-budget surrogate plus covariate-balanced rerandomization. "
            "The baseline improves geometric space filling and standardized balance, "
            "while oracle-array optimality, order-of-addition stratum orthogonality, "
            "and Gaussianized covariance optimization remain formal theorem gaps."
        ),
        tags=(
            "experimental_design",
            "space_filling",
            "maximin",
            "oracle_array",
            "order_of_addition",
            "covariate_balance",
            "gaussianized",
            "experimental_design_optimization",
        ),
    ),
    KnowledgeCard(
        id="heteroskedastic_robust_inference",
        title="Heteroskedasticity-consistent regression inference",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "Sandwich/HC standard errors target valid asymptotic inference when "
            "linear regression errors are conditionally heteroskedastic."
        ),
        tags=("regression", "heteroskedastic", "sandwich", "robust_se", "heteroskedastic_regression_inference"),
    ),
    KnowledgeCard(
        id="benjamini_hochberg_fdr",
        title="Benjamini-Hochberg false discovery rate control",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "The BH step-up procedure rejects ordered p-values below the "
            "linear q*i/m boundary and controls FDR under independent valid "
            "null p-values, with extensions for positive dependence."
        ),
        tags=("multiple_testing", "fdr", "benjamini_hochberg", "bh", "testing", "multiple_testing_fdr"),
    ),
    KnowledgeCard(
        id="anytime_valid_eprocesses",
        title="Anytime-valid inference with e-processes",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "Nonnegative e-processes/test martingales can be monitored under "
            "optional stopping; Ville-style inequalities control the chance "
            "that the process ever crosses 1/alpha under the null."
        ),
        tags=("sequential", "anytime", "optional_stopping", "eprocess", "testing", "sequential_anytime_inference"),
    ),
    KnowledgeCard(
        id="sequential_changepoint_post_detection",
        title="Sequential changepoint and post-detection inference",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "Sequential changepoint theory links CUSUM-style structural-break "
            "detectors to localization intervals and post-detection uncertainty. "
            "A production-safe baseline can simulate projected functional time "
            "series with partial measurement error, while functional CUSUM limit "
            "theory, selective/post-detection coverage, and sequential model "
            "confidence sets remain explicit formal gaps."
        ),
        tags=(
            "sequential",
            "changepoint",
            "post_detection",
            "functional_time_series",
            "model_confidence_set",
            "cusum",
            "sequential_changepoint_inference",
        ),
    ),
    KnowledgeCard(
        id="spiked_pca_dimension_reduction",
        title="High-dimensional PCA and spiked covariance inference",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "Spiked covariance models use separated eigenvalues to define a latent "
            "signal subspace; sample PCA estimates that subspace, with theory based "
            "on eigengaps, covariance concentration, and perturbation bounds."
        ),
        tags=(
            "high_dimensional",
            "pca",
            "principal_components",
            "dimension_reduction",
            "eigenvector",
            "spiked_covariance",
            "high_dimensional_pca_inference",
        ),
    ),
    KnowledgeCard(
        id="high_dimensional_latent_structure_inference",
        title="Latent membership, sufficient-dimension association, and tensor SDR",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "High-dimensional latent-structure problems include grade-of-membership "
            "simplex models, sufficient-dimension association without a sparse linear "
            "model, and tensor-valued predictors with multilinear reductions. The "
            "current executable layer uses simplex membership recovery and nonlinear "
            "association screening, while local-dependence, tensor inverse-model, and "
            "high-dimensional selection-consistency proofs remain formal gaps."
        ),
        tags=(
            "high_dimensional",
            "latent_membership",
            "grade_of_membership",
            "sufficient_dimension_reduction",
            "tensor_predictors",
            "variable_selection",
            "high_dimensional_latent_structure_inference",
        ),
    ),
    KnowledgeCard(
        id="extreme_tail_hill_weissman",
        title="Extreme-value tail index and high-quantile inference",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "Hill estimators use the top order statistics to estimate a regularly "
            "varying tail index; Weissman extrapolation converts that tail-index "
            "estimate into high-quantile or value-at-risk estimates."
        ),
        tags=(
            "extremes",
            "heavy_tails",
            "tail_index",
            "high_quantile",
            "regular_variation",
            "hill",
            "weissman",
            "extreme_tail_quantile_inference",
        ),
    ),
    KnowledgeCard(
        id="heavy_tail_time_series_extremal_dependence",
        title="Infinite-mean ACD, hyperplane extremes, and tail-robust factor time series",
        source_type="statistical_method",
        location="internal-method-card",
        summary=(
            "Heavy-tail frontier theory includes nonstandard limit behavior for "
            "integrated ACD durations with infinite means, hyperplane log-ratio "
            "representations of multivariate extremal dependence, and truncation-based "
            "factor estimation for heavy-tailed vector or tensor time series. The "
            "v0 release exposes tail-index testing, hyperplane PCA, and truncated "
            "factor subspace simulations while full QMLE limits, Husler-Reiss "
            "characterization, tensor decompositions, and dependent CLTs remain gaps."
        ),
        tags=(
            "heavy_tails",
            "infinite_mean",
            "integrated_acd",
            "extremal_dependence",
            "hyperplane",
            "factor_time_series",
            "tensor_time_series",
            "truncation",
            "heavy_tail_time_series_extremal_dependence",
        ),
    ),
    KnowledgeCard(
        id="autoformalization_llm",
        title="Autoformalization with Large Language Models",
        source_type="paper",
        location=str(RESOURCE_ROOT / "master_ai_for_math_formal_verification.md"),
        summary="Translate informal mathematical statements into formal proof-assistant statements.",
        tags=("autoformalization", "formalization", "lean"),
    ),
    KnowledgeCard(
        id="draft_sketch_prove",
        title="Draft, Sketch, and Prove",
        source_type="paper",
        location=str(RESOURCE_ROOT / "master_ai_for_math_formal_verification.md"),
        summary="Use informal proof sketches to guide formal theorem proving.",
        tags=("informal_proof", "formalization", "prover"),
    ),
    KnowledgeCard(
        id="lean_finder",
        title="Lean Finder / semantic Mathlib retrieval",
        source_type="paper",
        location=str(RESOURCE_ROOT / "master_ai_for_math_formal_verification.md"),
        summary="Natural-language intent and semantic search for Mathlib declarations.",
        tags=("retrieval", "mathlib", "lean_finder", "premise_selection"),
    ),
    KnowledgeCard(
        id="leandojo_reprover",
        title="LeanDojo / ReProver retrieval-augmented proving",
        source_type="code_paper",
        location=str(RESOURCE_ROOT / "master_ai_for_math_formal_verification.md"),
        summary="Proof-state extraction and retrieval-augmented theorem proving for Lean.",
        tags=("retrieval", "prover", "leandojo", "reprover", "lean"),
    ),
    KnowledgeCard(
        id="loogle",
        title="Loogle Mathlib search",
        source_type="tool",
        location="https://loogle.lean-lang.org/",
        summary="Identifier, type, and subexpression search over Lean/Mathlib declarations.",
        tags=("retrieval", "mathlib", "loogle"),
    ),
    KnowledgeCard(
        id="leansearch_client_local",
        title="Local LeanSearchClient / Loogle syntax integration",
        source_type="local_repo",
        location="/Users/yukang/Axiom Interview/.lake/packages/LeanSearchClient",
        summary=(
            "Local Lean package exposing #leansearch, #loogle, and state-search "
            "syntax from inside Lean. It is an integration target for using "
            "external Mathlib search providers without rebuilding search clients "
            "inside the statistician repo."
        ),
        tags=("retrieval", "mathlib", "leansearch", "loogle", "statesearch", "lean"),
    ),
    KnowledgeCard(
        id="leandojo_v2_local",
        title="Local LeanDojo-v2 prover training and tracing stack",
        source_type="local_repo",
        location="/Users/yukang/Desktop/AI for Math/Axiom Code Practice/external/LeanDojo-v2",
        summary=(
            "Local LeanDojo-v2 checkout for repository tracing, proof-state "
            "dataset generation, retrieval-augmented proving, SFT/GRPO training, "
            "and LeanProgress-style value/progress modeling."
        ),
        tags=("retrieval", "prover", "training", "leandojo", "reprover", "grpo", "lean_progress"),
    ),
    KnowledgeCard(
        id="atlas_lean_repository",
        title="Meta ATLAS Lean probability and high-dimensional statistics corpus",
        source_type="local_repo",
        location="/Users/yukang/.codex/external/ykzeng-atlas-lean",
        summary=(
            "Local shallow mirror of ykzeng-yale/atlas-lean, currently matching "
            "facebookresearch/atlas-lean. The AI Statistician indexes the "
            "probability, high-dimensional statistics, probabilistic-methods, "
            "real-analysis, Fourier, functional-analysis, differential-analysis, "
            "and projection-theory subtrees as formal-source evidence for theorem "
            "planning and proof-bank expansion. Training exporters omit external "
            "declaration payloads by default, with an explicit owner-authorized "
            "environment override for broader local export."
        ),
        tags=(
            "atlas",
            "meta",
            "lean",
            "probability",
            "high_dimensional_statistics",
            "subgaussian",
            "autoformalization",
            "retrieval_only",
        ),
    ),
    KnowledgeCard(
        id="autoform_bot_harness",
        title="Meta AutoformBot formalization harness",
        source_type="local_repo",
        location="/Users/yukang/.codex/external/ykzeng-autoform-bot",
        summary=(
            "Local shallow mirror of ykzeng-yale/autoform-bot, currently "
            "matching facebookresearch/autoform-bot, exposing "
            "statement extraction, multi-agent formalization orchestration, "
            "Lean checks, dependency-graph evaluation, proof-checker wrappers, "
            "REPL/LSP tools, Lean skill docs, evaluation, and visualization. The "
            "system records it as a reusable harness target rather than copying "
            "its code into training datasets."
        ),
        tags=("autoform", "autoformalization", "lean", "harness", "statement_extraction", "evaluation"),
    ),
    KnowledgeCard(
        id="lean_blueprint_knowledge",
        title="LeanBlueprint formalization dependency graph and visualization metadata",
        source_type="local_repo",
        location=str(LEAN_BLUEPRINT_ROOT),
        summary=(
            "Local clone of PatrickMassot/leanblueprint, a plasTeX plugin and CLI "
            "for building Lean formalization blueprints. Its key macros "
            "\\lean, \\leanok, \\uses, \\notready, \\discussion, \\proves, and "
            "\\mathlibok synchronize informal exposition, formal declaration "
            "links, dependency edges, discussion issues, and proof progress. "
            "AI-Statistician uses it as visualization/planning metadata for "
            "route DAGs, not as proof evidence."
        ),
        tags=(
            "leanblueprint",
            "blueprint",
            "visualization",
            "dependency_graph",
            "formalization",
            "lean",
            "route_dag",
        ),
    ),
    KnowledgeCard(
        id="local_mathlib_probability",
        title="Local Mathlib probability and statistics source",
        source_type="local_repo",
        location="/Users/yukang/LeanProjects/LeanPractice/.lake/packages/mathlib/Mathlib/Probability",
        summary=(
            "Local Mathlib probability tree containing variance, independence, "
            "CLT, martingale, conditional expectation, distribution, and risk files "
            "that the theory lab should mine before creating new Lean definitions."
        ),
        tags=("mathlib", "lean", "probability", "variance", "clt", "martingale", "statistics"),
    ),
    KnowledgeCard(
        id="empirical_process_lean",
        title="EmpiricalProcessLEAN / StatInference integration target",
        source_type="local_repo",
        location=str(VENDORED_EMPIRICAL_PROCESS_ROOT),
        summary=(
            "Vendored GitHub main snapshot of the full EmpericalProcessLEAN project "
            "with VdVW, Durrett probability, Vaart asymptotic statistics, "
            "probability-measure foundations, empirical-process primitives, "
            "Rademacher and martingale shared modules, matching/WDSM bridges, "
            "and optimization/shared foundation modules "
            "to mine before creating new Lean definitions."
        ),
        tags=("empirical_process", "asymptotic", "statinference", "lean"),
    ),
    KnowledgeCard(
        id="lean_stat_learning_theory",
        title="lean-stat-learning-theory local formalization repo",
        source_type="local_repo",
        location="/Users/yukang/.codex/external/lean-stat-learning-theory",
        summary=(
            "Local copy of the statistical learning theory formalization with "
            "covering numbers, sub-Gaussian lemmas, Gaussian process tools, and "
            "least-squares error-bound infrastructure to reuse before inventing "
            "new empirical-process primitives."
        ),
        tags=(
            "statistical_learning",
            "slt",
            "lean",
            "covering_number",
            "subgaussian",
            "least_squares",
            "empirical_process",
        ),
    ),
    KnowledgeCard(
        id="formal_slt",
        title="FormalSLT statistical learning theory corpus",
        source_type="local_repo",
        location="/Users/yukang/.codex/external/FormalSLT/FormalSLT",
        summary=(
            "Local clone of Robby955/FormalSLT with finite-sample statistical "
            "learning theory theorem families: Rademacher complexity, PAC/VC "
            "bridges, ERM generalization, Azuma-style bounded differences, "
            "algorithmic stability, and Dudley/chaining interfaces."
        ),
        tags=("formal_slt", "slt", "rademacher", "pac", "vc", "azuma", "stability", "lean"),
    ),
    KnowledgeCard(
        id="lean_rademacher",
        title="Lean Rademacher complexity formalization",
        source_type="local_repo",
        location="/Users/yukang/.codex/external/lean-rademacher/FoML",
        summary=(
            "Local clone of auto-res/lean-rademacher with Rademacher complexity, "
            "McDiarmid, Massart, Dudley entropy, and linear predictor "
            "generalization-bound formalizations."
        ),
        tags=("rademacher", "mcdiarmid", "massart", "dudley", "generalization", "lean"),
    ),
    KnowledgeCard(
        id="lean_machine_learning_lml",
        title="Lean Machine Learning Library",
        source_type="local_repo",
        location="/Users/yukang/.codex/external/LeanMachineLearning-LML/LeanMachineLearning",
        summary=(
            "Local clone of LeanMachineLearning/LML. It is most relevant to "
            "algorithmic-statistics routes: stochastic bandits, regret, UCB, "
            "explore-then-commit, and reusable algorithm/proof structures."
        ),
        tags=("machine_learning", "bandit", "regret", "ucb", "algorithm", "lean"),
    ),
    KnowledgeCard(
        id="brownian_motion_lean",
        title="Brownian motion and Gaussian process Lean corpus",
        source_type="local_repo",
        location="/Users/yukang/.codex/external/brownian-motion/BrownianMotion",
        summary=(
            "Local clone of RemyDegenne/brownian-motion for retrieval-only reuse "
            "of Brownian motion, Gaussian process, Kolmogorov-Chentsov, "
            "stochastic-process, and stochastic-integral theorem shapes. Some "
            "subtrees are WIP, so it is not exported as training data by default."
        ),
        tags=("brownian", "gaussian", "kolmogorov_chentsov", "stochastic_process", "retrieval_only", "lean"),
    ),
    KnowledgeCard(
        id="kolmogorov_extension_lean",
        title="Kolmogorov extension theorem Lean corpus",
        source_type="local_repo",
        location="/Users/yukang/.codex/external/kolmogorov_extension4/KolmogorovExtension4",
        summary=(
            "Local clone of RemyDegenne/kolmogorov_extension4 with projective "
            "measure families, compact systems, regular contents, and the "
            "Kolmogorov extension theorem."
        ),
        tags=("kolmogorov_extension", "projective_measure", "measure_theory", "stochastic_process", "lean"),
    ),
    KnowledgeCard(
        id="scilean_calculus",
        title="SciLean calculus and scientific computing corpus",
        source_type="local_repo",
        location="/Users/yukang/.codex/external/SciLean/SciLean",
        summary=(
            "Local clone of lecopivo/SciLean. It is useful as retrieval-only "
            "context for differentiability, gradients, Jacobians, probabilistic "
            "derivatives, Gaussian examples, and optimization algorithms; WIP "
            "regions are not exported as training data by default."
        ),
        tags=("scilean", "calculus", "autodiff", "gradient", "optimization", "probabilistic_derivative", "lean"),
    ),
    KnowledgeCard(
        id="local_statinference_repo",
        title="Local StatInference Lean codebase",
        source_type="local_repo",
        location="/Users/yukang/.codex/wdsm-lean-gate/StatInference",
        summary=(
            "Local statistics formalization workspace to mine for reusable "
            "definitions and theorem shapes before adding new proof obligations."
        ),
        tags=("statinference", "lean", "statistics", "local_code"),
    ),
    KnowledgeCard(
        id="legacy_ai_statistician_statinference",
        title="Legacy AI-Statistician StatInference source pool",
        source_type="local_repo",
        location=str(LEGACY_AI_STATISTICIAN_ROOT / "StatInference"),
        summary=(
            "Vendored legacy AI-Statistician StatInference Lean tree reused as "
            "a read-only declaration source for asymptotic-normality bridges, "
            "AIPW/IPW routes, Glivenko-Cantelli/bracketing interfaces, "
            "weak-convergence anchors, and theorem-hole planning."
        ),
        tags=(
            "legacy_ai_statistician",
            "statinference",
            "lean",
            "asymptotic",
            "causal",
            "empirical_process",
            "retrieval",
        ),
    ),
    KnowledgeCard(
        id="openprover_pipeline",
        title="OpenProver proof-search and evaluation pipeline",
        source_type="local_repo",
        location="/Users/yukang/Documents/OpenProver",
        summary=(
            "Existing prover/evaluation structure that should be reused for "
            "search orchestration and benchmark logging rather than rebuilt."
        ),
        tags=("openprover", "prover", "evaluation", "search"),
    ),
)


PRIMARY_KNOWLEDGE_BY_PROBLEM_CLASS: dict[str, str] = {
    "semiparametric_causal_ate": "aipw_double_robustness",
    "distribution_free_conformal_prediction": "split_conformal_prediction",
    "right_censored_survival_inference": "right_censored_survival_kaplan_meier",
    "robust_mean_inference": "robust_mean_median_of_means",
    "differential_privacy_learning": "differential_privacy_gaussian_mechanism",
    "nonparametric_regression_inference": "nonparametric_sieve_regression_inference",
    "robust_distributed_model_privacy_inference": "robust_distributed_model_privacy_inference",
    "adaptive_transfer_active_preference_learning": "adaptive_transfer_active_preference_learning",
    "network_graph_inference": "network_graph_sbm_spectral_inference",
    "bayesian_posterior_calibration": "bayesian_predictive_prior_calibration",
    "bayesian_tree_mcmc_computation": "bayesian_tree_mcmc_computation",
    "geometric_spatial_point_process_inference": "geometric_spatial_point_process_inference",
    "measurement_bias_ranking_inference": "measurement_bias_assessment_ranking",
    "missing_mediation_deconvolution_inference": "missing_mediation_deconvolution_inference",
    "design_based_variance_inference": "design_based_variance_neyman",
    "experimental_design_optimization": "experimental_design_maximin_balance",
    "heteroskedastic_regression_inference": "heteroskedastic_robust_inference",
    "multiple_testing_fdr": "benjamini_hochberg_fdr",
    "sequential_anytime_inference": "anytime_valid_eprocesses",
    "sequential_changepoint_inference": "sequential_changepoint_post_detection",
    "high_dimensional_pca_inference": "spiked_pca_dimension_reduction",
    "high_dimensional_latent_structure_inference": "high_dimensional_latent_structure_inference",
    "extreme_tail_quantile_inference": "extreme_tail_hill_weissman",
    "heavy_tail_time_series_extremal_dependence": "heavy_tail_time_series_extremal_dependence",
}


FORMAL_INFRASTRUCTURE_KNOWLEDGE: tuple[str, ...] = (
    "local_mathlib_probability",
    "local_statinference_repo",
    "empirical_process_lean",
    "lean_stat_learning_theory",
    "legacy_ai_statistician_statinference",
    "lean_finder",
    "leandojo_reprover",
    "loogle",
    "leansearch_client_local",
    "leandojo_v2_local",
    "atlas_lean_repository",
    "autoform_bot_harness",
    "openprover_pipeline",
    "lean_blueprint_knowledge",
)


def knowledge_by_id(card_id: str) -> KnowledgeCard:
    for card in KNOWLEDGE_CARDS:
        if card.id == card_id:
            return card
    raise KeyError(f"unknown research knowledge card: {card_id}")


def retrieve_research_knowledge(query: str, tags: tuple[str, ...] = (), *, k: int = 6) -> list[KnowledgeCard]:
    q_tokens = tokens(" ".join([query, *tags]))
    rows: list[tuple[float, KnowledgeCard]] = []
    for card in KNOWLEDGE_CARDS:
        haystack = " ".join([card.id, card.title, card.summary, " ".join(card.tags)])
        overlap = q_tokens & tokens(haystack)
        tag_bonus = len(set(tags) & set(card.tags))
        score = len(overlap) + 2.0 * tag_bonus
        if score > 0:
            rows.append((score, card))
    return [card for _, card in sorted(rows, key=lambda row: (-row[0], row[1].id))[:k]]


def retrieve_problem_knowledge(
    question: OpenResearchQuestion,
    problem: ResearchProblemSpec,
    theorem_goals: tuple[TheoremGoal, ...] | list[TheoremGoal],
    *,
    k: int = 8,
) -> list[KnowledgeCard]:
    """Retrieve method and formalization resources for a normalized problem.

    The trace should show both parts of the theory-lab workflow: a statistical
    method card tied to the problem class, and reusable Lean/search resources
    that are relevant when theorem goals become formal proof obligations.  This
    is still intentionally small and deterministic; stronger RAG systems such as
    Lean Finder/ReProver plug in as providers later.
    """

    seeded_ids: list[str] = []
    primary = PRIMARY_KNOWLEDGE_BY_PROBLEM_CLASS.get(problem.problem_class)
    if primary:
        seeded_ids.append(primary)

    goal_text = " ".join(
        " ".join([goal.title, goal.informal_statement, goal.proof_strategy, goal.status])
        for goal in theorem_goals
    )
    scored = retrieve_research_knowledge(
        " ".join(
            [
                question.title,
                question.description,
                problem.problem_class,
                problem.dgp,
                problem.estimand,
                " ".join(problem.assumptions),
                problem.asymptotic_regime,
                goal_text,
                "Lean Mathlib StatInference formal proof retrieval premise selection",
            ]
        ),
        tags=question.tags + (problem.problem_class, "lean", "mathlib", "statinference", "retrieval"),
        k=len(KNOWLEDGE_CARDS),
    )
    # Guarantee the audit-critical formalization substrate appears even when
    # domain-specific method cards score highly and the trace keeps only k cards.
    seeded_ids.extend(FORMAL_INFRASTRUCTURE_KNOWLEDGE)
    seeded_ids.extend(card.id for card in scored)

    out: list[KnowledgeCard] = []
    seen: set[str] = set()
    for card_id in seeded_ids:
        if card_id in seen:
            continue
        try:
            card = knowledge_by_id(card_id)
        except KeyError:
            continue
        out.append(card)
        seen.add(card.id)
        if len(out) >= k:
            break
    return out
