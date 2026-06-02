from __future__ import annotations

from .fingerprint import stable_hash
from .schema import FormalObligation


def _stmt(body: str) -> str:
    return body.strip() + "\n"


FORMAL_OBLIGATIONS: dict[str, FormalObligation] = {
    "constant_estimator_unbiased": FormalObligation(
        id="constant_estimator_unbiased",
        title="Constant estimator is unbiased for its constant target",
        english="For any probability space, the expectation of the constant estimator c is c.",
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

def constantEstimator {Ω : Type*} (c : ℝ) : Ω → ℝ := fun _ => c

theorem constantEstimator_unbiased {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ] (c : ℝ) :
    ∫ ω, constantEstimator (Ω := Ω) c ω ∂μ = c := by sorry
"""
        ),
        proof_body="by\n  simp [constantEstimator]",
        tags=("estimator", "expectation", "unbiased", "constant"),
        expected_lemmas=("integral_const", "measure_univ"),
    ),
    "constant_estimator_variance_zero": FormalObligation(
        id="constant_estimator_variance_zero",
        title="Constant estimator has zero variance",
        english="The variance of a constant estimator is zero.",
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

def constantEstimator {Ω : Type*} (c : ℝ) : Ω → ℝ := fun _ => c

theorem constantEstimator_variance_zero {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ] (c : ℝ) :
    variance (constantEstimator (Ω := Ω) c) μ = 0 := by sorry
"""
        ),
        proof_body="by\n  simp [constantEstimator, variance, evariance]",
        tags=("estimator", "variance", "constant"),
        expected_lemmas=("variance", "evariance"),
    ),
    "mean2_estimator_expectation": FormalObligation(
        id="mean2_estimator_expectation",
        title="Two-variable mean estimator expectation",
        english=(
            "For integrable random variables X and Y, the expectation of "
            "(X+Y)/2 is the average of their expectations."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

noncomputable def mean2Estimator {Ω : Type*} (X Y : Ω → ℝ) : Ω → ℝ :=
  fun ω => (X ω + Y ω) / 2

theorem mean2Estimator_expectation {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) (X Y : Ω → ℝ)
    (hX : Integrable X μ) (hY : Integrable Y μ) :
    ∫ ω, mean2Estimator X Y ω ∂μ =
      ((∫ ω, X ω ∂μ) + (∫ ω, Y ω ∂μ)) / 2 := by sorry
"""
        ),
        proof_body="by\n  simp [mean2Estimator, integral_div, integral_add hX hY]",
        tags=("estimator", "expectation", "linearity", "mean"),
        expected_lemmas=("integral_add", "integral_div"),
    ),
    "mean2_estimator_unbiased": FormalObligation(
        id="mean2_estimator_unbiased",
        title="Two-variable mean estimator is unbiased",
        english=(
            "If two integrable component estimators are each unbiased for the "
            "same target theta, their average is also unbiased for theta."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

noncomputable def mean2Estimator {Ω : Type*} (X Y : Ω → ℝ) : Ω → ℝ :=
  fun ω => (X ω + Y ω) / 2

theorem mean2Estimator_unbiased {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) (X Y : Ω → ℝ) (theta : ℝ)
    (hX : Integrable X μ) (hY : Integrable Y μ)
    (hEX : ∫ ω, X ω ∂μ = theta)
    (hEY : ∫ ω, Y ω ∂μ = theta) :
    ∫ ω, mean2Estimator X Y ω ∂μ = theta := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  calc\n"
            "    ∫ ω, mean2Estimator X Y ω ∂μ =\n"
            "        ((∫ ω, X ω ∂μ) + (∫ ω, Y ω ∂μ)) / 2 := by\n"
            "          simp [mean2Estimator, integral_div, integral_add hX hY]\n"
            "    _ = theta := by\n"
            "          rw [hEX, hEY]\n"
            "          ring"
        ),
        tags=("estimator", "expectation", "linearity", "mean", "unbiased"),
        expected_lemmas=("integral_add", "integral_div", "ring"),
    ),
    "difference_estimator_unbiased": FormalObligation(
        id="difference_estimator_unbiased",
        title="Difference estimator is unbiased for a contrast",
        english=(
            "If two integrable estimators X and Y are unbiased for targets "
            "thetaX and thetaY, then their difference X-Y is unbiased for the "
            "contrast thetaX-thetaY. This is the reusable expectation bridge "
            "behind difference-in-means, treatment-effect, and contrast "
            "estimators; it does not prove randomization, identification, or "
            "asymptotic normality."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

noncomputable def differenceEstimator {Ω : Type*} (X Y : Ω → ℝ) : Ω → ℝ :=
  X - Y

theorem differenceEstimator_unbiased {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) (X Y : Ω → ℝ) (thetaX thetaY : ℝ)
    (hX : Integrable X μ) (hY : Integrable Y μ)
    (hEX : ∫ ω, X ω ∂μ = thetaX)
    (hEY : ∫ ω, Y ω ∂μ = thetaY) :
    ∫ ω, differenceEstimator X Y ω ∂μ = thetaX - thetaY := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  calc\n"
            "    ∫ ω, differenceEstimator X Y ω ∂μ = μ[X] - μ[Y] := by\n"
            "      simpa [differenceEstimator] using integral_sub hX hY\n"
            "    _ = thetaX - thetaY := by\n"
            "      rw [hEX, hEY]"
        ),
        tags=(
            "estimator",
            "expectation",
            "linearity",
            "contrast",
            "difference_in_means",
            "unbiased",
            "causal",
            "design_based",
        ),
        expected_lemmas=("integral_sub",),
    ),
    "difference_estimator_variance_decompose": FormalObligation(
        id="difference_estimator_variance_decompose",
        title="Difference estimator variance decomposition",
        english=(
            "For L2 estimators X and Y on a probability space, the variance of "
            "their contrast X-Y is Var(X)-2*Cov(X,Y)+Var(Y). This is the "
            "reusable second-moment bridge behind difference-in-means, ATE "
            "contrasts, and design-based variance calculations; it does not "
            "prove randomization, covariance estimation, or asymptotic normality."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

noncomputable def differenceEstimator {Ω : Type*} (X Y : Ω → ℝ) : Ω → ℝ :=
  X - Y

theorem differenceEstimator_variance_decompose {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (X Y : Ω → ℝ) (hX : MemLp X 2 μ) (hY : MemLp Y 2 μ) :
    variance (differenceEstimator X Y) μ =
      variance X μ - 2 * cov[X, Y; μ] + variance Y μ := by sorry
"""
        ),
        proof_body="by\n  simpa [differenceEstimator] using variance_fun_sub (μ := μ) hX hY",
        tags=(
            "estimator",
            "variance",
            "covariance",
            "contrast",
            "difference_in_means",
            "causal",
            "design_based",
            "finite_sample",
        ),
        expected_lemmas=("variance_fun_sub", "variance_sub"),
        depends_on=("difference_estimator_unbiased", "variance_nonneg"),
    ),
    "neyman_variance_conservative_algebra": FormalObligation(
        id="neyman_variance_conservative_algebra",
        title="Neyman conservative variance algebra",
        english=(
            "If an exact randomization variance decomposes as an observable "
            "Neyman bound minus a nonnegative treatment-effect variance term, "
            "then the observable bound is conservative. This is the finite "
            "algebraic bridge behind design-based variance traces; it does not "
            "prove complete randomization, finite-population potential-outcome "
            "identification, or the randomization variance formula itself."
        ),
        formal_statement=_stmt(
            """
import Mathlib

theorem neymanVariance_conservative_of_nonneg_effect_variance
    (observableBound exactVariance treatmentEffectVariance : ℝ)
    (hDecomp : exactVariance = observableBound - treatmentEffectVariance)
    (hNonneg : 0 ≤ treatmentEffectVariance) :
    exactVariance ≤ observableBound := by sorry
"""
        ),
        proof_body="by\n  nlinarith [hDecomp, hNonneg]",
        tags=(
            "estimator",
            "variance",
            "design_based",
            "neyman",
            "conservative",
            "finite_population",
            "randomization_variance",
            "treatment_effect",
        ),
        expected_lemmas=("nlinarith",),
        depends_on=("difference_estimator_variance_decompose", "variance_nonneg"),
    ),
    "finite_population_ate_mean_difference": FormalObligation(
        id="finite_population_ate_mean_difference",
        title="Finite-population ATE mean-difference algebra",
        english=(
            "For finite-population potential outcomes Y(1) and Y(0), the "
            "finite-population mean of the unit-level treatment effects "
            "Y(1)-Y(0) equals the difference between the finite-population "
            "treated and control potential-outcome means. This formalizes the "
            "ATE target algebra used by design-based traces; it does not prove "
            "complete randomization, assignment ignorability, or estimator "
            "unbiasedness under a randomization distribution."
        ),
        formal_statement=_stmt(
            """
import Mathlib

noncomputable def finitePopulationMean {n : Nat} (Y : Fin n → ℝ) : ℝ :=
  (∑ i, Y i) / (n : ℝ)

theorem finitePopulationATE_mean_difference {n : Nat}
    (Y1 Y0 : Fin n → ℝ) :
    finitePopulationMean (fun i => Y1 i - Y0 i) =
      finitePopulationMean Y1 - finitePopulationMean Y0 := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  simp [finitePopulationMean, Finset.sum_sub_distrib]\n"
            "  ring"
        ),
        tags=(
            "estimator",
            "finite_population",
            "potential_outcomes",
            "ate",
            "difference_in_means",
            "design_based",
            "finite_sample",
            "algebra",
        ),
        expected_lemmas=("Finset.sum_sub_distrib", "ring"),
        depends_on=("difference_estimator_unbiased",),
    ),
    "potential_outcome_observed_consistency": FormalObligation(
        id="potential_outcome_observed_consistency",
        title="Potential-outcome observed-outcome consistency",
        english=(
            "For binary treatment assignment, the observed outcome defined as "
            "`Y(1)` for treated units and `Y(0)` for control units satisfies "
            "the deterministic consistency identities on each unit. This is a "
            "reusable potential-outcome bridge for causal ATE traces; it does "
            "not prove conditional exchangeability, positivity, identification, "
            "or double robustness."
        ),
        formal_statement=_stmt(
            """
import Mathlib

def observedPotentialOutcome {Unit : Type*}
    (Y1 Y0 : Unit → ℝ) (W : Unit → Bool) : Unit → ℝ :=
  fun i => if W i then Y1 i else Y0 i

theorem observedPotentialOutcome_consistency {Unit : Type*}
    (Y1 Y0 : Unit → ℝ) (W : Unit → Bool) (i : Unit) :
    (W i = true → observedPotentialOutcome Y1 Y0 W i = Y1 i) ∧
      (W i = false → observedPotentialOutcome Y1 Y0 W i = Y0 i) := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  constructor\n"
            "  · intro h\n"
            "    simp [observedPotentialOutcome, h]\n"
            "  · intro h\n"
            "    simp [observedPotentialOutcome, h]"
        ),
        tags=(
            "causal",
            "ate",
            "potential_outcomes",
            "potential_outcome_consistency",
            "observed_outcome",
            "binary_treatment",
            "semiparametric",
            "identification",
        ),
        expected_lemmas=("simp",),
        depends_on=("finite_population_ate_mean_difference",),
    ),
    "propensity_score_ne_zero_of_lower_bound": FormalObligation(
        id="propensity_score_ne_zero_of_lower_bound",
        title="Propensity lower bound gives nonzero denominator",
        english=(
            "If a propensity score `p` is bounded below by a strictly positive "
            "constant `δ`, then `p` is nonzero. This is a denominator-safety "
            "bridge for inverse-propensity and AIPW traces under positivity; "
            "it does not prove overlap, conditional exchangeability, or causal "
            "identification."
        ),
        formal_statement=_stmt(
            """
import Mathlib

theorem propensityScore_ne_zero_of_lower_bound {δ p : ℝ}
    (hδ : 0 < δ) (hp : δ ≤ p) :
    p ≠ 0 := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  have hp_pos : 0 < p := lt_of_lt_of_le hδ hp\n"
            "  exact ne_of_gt hp_pos"
        ),
        tags=(
            "causal",
            "ate",
            "positivity",
            "overlap",
            "propensity",
            "propensity_score",
            "inverse_probability_weight",
            "aipw",
            "semiparametric",
            "denominator_safety",
        ),
        expected_lemmas=("lt_of_lt_of_le", "ne_of_gt"),
        depends_on=("potential_outcome_observed_consistency",),
    ),
    "propensity_weight_mul_cancel_of_lower_bound": FormalObligation(
        id="propensity_weight_mul_cancel_of_lower_bound",
        title="Propensity lower bound licenses inverse-weight cancellation",
        english=(
            "If a propensity score `p` is bounded below by a strictly positive "
            "constant `δ`, then the inverse-propensity factor cancels: "
            "`p⁻¹ * p = 1`. This is the algebraic bridge that lets AIPW and "
            "IPW proof traces use positivity to simplify inverse-weighted "
            "terms; it does not prove conditional exchangeability, "
            "identification, or double robustness."
        ),
        formal_statement=_stmt(
            """
import Mathlib

theorem propensityWeight_mul_cancel_of_lower_bound {δ p : ℝ}
    (hδ : 0 < δ) (hp : δ ≤ p) :
    p⁻¹ * p = 1 := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  have hp_pos : 0 < p := lt_of_lt_of_le hδ hp\n"
            "  exact inv_mul_cancel₀ (ne_of_gt hp_pos)"
        ),
        tags=(
            "causal",
            "ate",
            "positivity",
            "overlap",
            "propensity",
            "propensity_score",
            "propensity_weight",
            "propensity_weight_identity",
            "inverse_probability_weight",
            "aipw",
            "semiparametric",
            "denominator_safety",
            "algebra",
        ),
        expected_lemmas=("lt_of_lt_of_le", "ne_of_gt", "inv_mul_cancel₀"),
        depends_on=("propensity_score_ne_zero_of_lower_bound",),
    ),
    "propensity_weight_cancel_left_of_lower_bound": FormalObligation(
        id="propensity_weight_cancel_left_of_lower_bound",
        title="Propensity lower bound licenses left inverse-weight cancellation",
        english=(
            "If a propensity score `p` is bounded below by a strictly positive "
            "constant `δ`, then the left-oriented inverse-propensity product "
            "also cancels: `p * p⁻¹ = 1`. This complements the existing "
            "`p⁻¹ * p = 1` bridge so IPW/AIPW formal traces can normalize "
            "either algebraic orientation without relying on ad hoc rewriting; "
            "it still assumes positivity rather than proving overlap or "
            "identification."
        ),
        formal_statement=_stmt(
            """
import Mathlib

theorem propensityWeight_cancel_left_of_lower_bound {δ p : ℝ}
    (hδ : 0 < δ) (hp : δ ≤ p) :
    p * p⁻¹ = 1 := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  have hp_pos : 0 < p := lt_of_lt_of_le hδ hp\n"
            "  exact mul_inv_cancel₀ (ne_of_gt hp_pos)"
        ),
        tags=(
            "causal",
            "ate",
            "positivity",
            "overlap",
            "propensity",
            "propensity_score",
            "propensity_weight",
            "propensity_weight_identity",
            "inverse_probability_weight",
            "aipw",
            "semiparametric",
            "denominator_safety",
            "algebra",
            "left_cancellation",
        ),
        expected_lemmas=("lt_of_lt_of_le", "ne_of_gt", "mul_inv_cancel₀"),
        depends_on=("propensity_weight_mul_cancel_of_lower_bound",),
    ),
    "complete_randomization_uniform_assignment_mass": FormalObligation(
        id="complete_randomization_uniform_assignment_mass",
        title="Complete-randomization uniform assignment mass",
        english=(
            "For a finite nonempty assignment space, the uniform assignment "
            "PMF gives every assignment probability mass equal to the inverse "
            "of the number of assignments. This is the basic distributional "
            "bridge behind complete-randomization traces; it does not yet "
            "formalize fixed treated-count assignment sets, combinatorial "
            "cardinality, or design-based covariance formulas."
        ),
        formal_statement=_stmt(
            """
import Mathlib

theorem completeRandomization_uniform_assignment_mass
    (Assignment : Type*) [Fintype Assignment] [Nonempty Assignment]
    (a : Assignment) :
    PMF.uniformOfFintype Assignment a = (Fintype.card Assignment : ENNReal)⁻¹ := by sorry
"""
        ),
        proof_body="by\n  exact PMF.uniformOfFintype_apply a",
        tags=(
            "probability",
            "pmf",
            "uniform",
            "complete_randomization",
            "complete_randomization_distribution",
            "assignment",
            "design_based",
            "finite_population",
        ),
        expected_lemmas=("PMF.uniformOfFintype_apply",),
        depends_on=("finite_population_ate_mean_difference",),
    ),
    "uniform_rank_pmf_mass": FormalObligation(
        id="uniform_rank_pmf_mass",
        title="Finite uniform-rank PMF mass",
        english=(
            "For a finite nonempty rank space `Fin n`, Mathlib's uniform PMF "
            "assigns every rank mass `1 / n`. This is the finite distribution "
            "bridge used by conformal rank arguments after exchangeability has "
            "been reduced to uniform rank. It does not itself prove that "
            "exchangeable scores induce a uniform rank, nor does it prove the "
            "order-statistic conformal coverage theorem."
        ),
        formal_statement=_stmt(
            """
import Mathlib

theorem uniformRank_pmf_mass {n : Nat} [Nonempty (Fin n)] (r : Fin n) :
    PMF.uniformOfFintype (Fin n) r = (n : ENNReal)⁻¹ := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  simpa [Fintype.card_fin] using (PMF.uniformOfFintype_apply r)"
        ),
        tags=(
            "probability",
            "pmf",
            "uniform",
            "rank",
            "uniform_rank",
            "rank_uniformity",
            "exchangeable_scores",
            "finite_sample",
            "conformal",
            "distribution_free_conformal_prediction",
        ),
        expected_lemmas=("PMF.uniformOfFintype_apply", "Fintype.card_fin"),
        depends_on=("complete_randomization_uniform_assignment_mass",),
    ),
    "mean2_estimator_variance_indep": FormalObligation(
        id="mean2_estimator_variance_indep",
        title="Two-variable mean estimator variance under independence",
        english=(
            "For independent L2 component estimators X and Y, the variance of "
            "their average (X+Y)/2 is one fourth of Var(X)+Var(Y)."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

noncomputable def mean2Estimator {Ω : Type*} (X Y : Ω → ℝ) : Ω → ℝ :=
  fun ω => (X ω + Y ω) / 2

theorem mean2Estimator_variance_indep {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (X Y : Ω → ℝ) (hX : MemLp X 2 μ) (hY : MemLp Y 2 μ)
    (h_indep : IndepFun X Y μ) :
    variance (mean2Estimator X Y) μ =
      (variance X μ + variance Y μ) / 4 := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  rw [show mean2Estimator X Y = ((1 / 2 : ℝ) • (X + Y)) by\n"
            "    ext ω\n"
            "    simp [mean2Estimator]\n"
            "    ring]\n"
            "  rw [variance_smul, IndepFun.variance_add hX hY h_indep]\n"
            "  ring"
        ),
        tags=("estimator", "variance", "mean", "independence", "efficiency", "finite_sample"),
        expected_lemmas=("variance_smul", "IndepFun.variance_add", "ring"),
        depends_on=("variance_indep_add",),
    ),
    "estimator_error_chebyshev": FormalObligation(
        id="estimator_error_chebyshev",
        title="Chebyshev error bound for an unbiased estimator",
        english=(
            "If an estimator X has finite second moment and expectation theta, "
            "then the probability that its absolute error exceeds c is bounded "
            "by Var(X)/c^2."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem estimator_error_chebyshev {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (X : Ω → ℝ) (theta : ℝ) (hX : MemLp X 2 μ)
    (hMean : μ[X] = theta) {c : ℝ} (hc : 0 < c) :
    μ {ω | c ≤ |X ω - theta|} ≤ ENNReal.ofReal (variance X μ / c ^ 2) := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  simpa [hMean] using\n"
            "    (meas_ge_le_variance_div_sq (μ := μ) (X := X) hX hc)"
        ),
        tags=("estimator", "variance", "tail_bound", "chebyshev", "finite_sample", "concentration"),
        expected_lemmas=("meas_ge_le_variance_div_sq",),
    ),
    "wald_interval_contains_iff_abs_error": FormalObligation(
        id="wald_interval_contains_iff_abs_error",
        title="Symmetric Wald interval containment is absolute-error control",
        english=(
            "For real-valued point estimates, a target lies inside the symmetric "
            "interval estimate ± radius exactly when the absolute estimation "
            "error is at most the radius. This is the deterministic bridge from "
            "tail/error bounds to Wald-style confidence-interval coverage; it "
            "does not assert CLT, standard-error consistency, or nominal coverage."
        ),
        formal_statement=_stmt(
            """
import Mathlib

theorem waldInterval_contains_iff_abs_error
    (estimate theta radius : ℝ) :
    (estimate - radius ≤ theta ∧ theta ≤ estimate + radius) ↔
      |estimate - theta| ≤ radius := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  constructor\n"
            "  · intro h\n"
            "    rw [abs_le]\n"
            "    constructor\n"
            "    · linarith [h.2]\n"
            "    · linarith [h.1]\n"
            "  · intro h\n"
            "    have h_abs := abs_le.mp h\n"
            "    constructor\n"
            "    · linarith [h_abs.2]\n"
            "    · linarith [h_abs.1]"
        ),
        tags=("estimator", "confidence_interval", "coverage", "wald", "absolute_error", "real_algebra"),
        expected_lemmas=("abs_le", "linarith"),
    ),
    "wald_interval_miscoverage_iff_abs_error_gt": FormalObligation(
        id="wald_interval_miscoverage_iff_abs_error_gt",
        title="Symmetric Wald interval miss is strict absolute-error exceedance",
        english=(
            "For real-valued point estimates, a target is outside the symmetric "
            "interval estimate ± radius exactly when the interval radius is "
            "strictly smaller than the absolute estimation error. This is the "
            "deterministic bridge from interval miscoverage events to strict "
            "tail events; it does not assert CLT, standard-error consistency, "
            "or any stochastic coverage bound."
        ),
        formal_statement=_stmt(
            """
import Mathlib

theorem waldInterval_miscoverage_iff_abs_error_gt
    (estimate theta radius : ℝ) :
    (¬ (estimate - radius ≤ theta ∧ theta ≤ estimate + radius)) ↔
      radius < |estimate - theta| := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  constructor\n"
            "  · intro hnot\n"
            "    by_contra hle_not\n"
            "    have hle : |estimate - theta| ≤ radius := le_of_not_gt hle_not\n"
            "    have h_abs := abs_le.mp hle\n"
            "    apply hnot\n"
            "    constructor\n"
            "    · linarith [h_abs.2]\n"
            "    · linarith [h_abs.1]\n"
            "  · intro hgt hcontains\n"
            "    have hle : |estimate - theta| ≤ radius := by\n"
            "      rw [abs_le]\n"
            "      constructor\n"
            "      · linarith [hcontains.2]\n"
            "      · linarith [hcontains.1]\n"
            "    exact not_le_of_gt hgt hle"
        ),
        tags=(
            "estimator",
            "confidence_interval",
            "coverage",
            "miscoverage",
            "wald",
            "absolute_error",
            "tail_event",
            "real_algebra",
        ),
        expected_lemmas=("abs_le", "le_of_not_gt", "not_le_of_gt", "linarith"),
        depends_on=("wald_interval_contains_iff_abs_error",),
    ),
    "coverage_lower_bound_of_complement_error": FormalObligation(
        id="coverage_lower_bound_of_complement_error",
        title="Coverage lower bound from complement-event error control",
        english=(
            "For a probability measure, if the complement of a coverage event "
            "has probability at most alpha, then the coverage event has "
            "probability at least 1-alpha. This is the reusable measure-theoretic "
            "bridge from miscoverage/error control to coverage reporting; it "
            "does not prove the model-specific bound on the complement event."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory

theorem coverageLowerBound_of_complement_error {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (A : Set Ω) (hA : MeasurableSet A) (α : ENNReal)
    (hbad : μ Aᶜ ≤ α) :
    1 - α ≤ μ A := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  have hcoverage : μ A = 1 - μ Aᶜ := by\n"
            "    simpa using (prob_compl_eq_one_sub hA.compl : μ (Aᶜ)ᶜ = 1 - μ Aᶜ)\n"
            "  rw [hcoverage]\n"
            "  exact tsub_le_tsub_left hbad 1"
        ),
        tags=("probability", "event", "coverage", "miscoverage", "confidence_interval", "conformal", "wald"),
        expected_lemmas=("prob_compl_eq_one_sub", "tsub_le_tsub_left"),
        depends_on=("prob_compl",),
    ),
    "simultaneous_coverage_of_union_error_bound": FormalObligation(
        id="simultaneous_coverage_of_union_error_bound",
        title="Simultaneous coverage from finite bad-event union control",
        english=(
            "If the probability of the finite union of bad events is at most "
            "alpha, then the probability that no bad event occurs is at least "
            "1-alpha. This is the reusable bridge from Bonferroni/union error "
            "control to simultaneous coverage; it does not prove the individual "
            "bad-event bounds or exchangeability/rank arguments."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem simultaneousCoverage_of_union_error_bound {Ω ι : Type*}
    [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (I : Finset ι) (A : ι → Set Ω) (α : ENNReal)
    (hUnion : MeasurableSet (⋃ i ∈ I, A i))
    (hbad : μ (⋃ i ∈ I, A i) ≤ α) :
    1 - α ≤ μ (⋃ i ∈ I, A i)ᶜ := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  have hcoverage : μ (⋃ i ∈ I, A i)ᶜ = 1 - μ (⋃ i ∈ I, A i) := by\n"
            "    exact prob_compl_eq_one_sub hUnion\n"
            "  rw [hcoverage]\n"
            "  exact tsub_le_tsub_left hbad 1"
        ),
        tags=(
            "probability",
            "event",
            "coverage",
            "simultaneous",
            "simultaneous_coverage",
            "union_bound",
            "familywise_error",
            "conformal",
            "confidence_band",
        ),
        expected_lemmas=("prob_compl_eq_one_sub", "tsub_le_tsub_left"),
        depends_on=("finite_union_budget_control", "coverage_lower_bound_of_complement_error"),
    ),
    "finite_conformal_rank_coverage_counting": FormalObligation(
        id="finite_conformal_rank_coverage_counting",
        title="Finite conformal rank coverage counting bridge",
        english=(
            "For a finite set of bad ranks, if each rank event has a local "
            "probability budget and the budgets sum to a total budget, then "
            "the event that the observed rank lands in the bad-rank set has "
            "probability at most the total budget. Under measurability of this "
            "bad-rank event and a probability measure, its complement has "
            "coverage at least one minus the total budget. This is a reusable "
            "finite counting bridge for split conformal traces; it does not "
            "prove exchangeability, rank uniformity, or the order-statistic "
            "quantile theorem itself."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem finiteConformalRank_coverage_counting {Ω ρ : Type*}
    [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (BadRanks : Finset ρ) (rank : Ω → ρ)
    (α : ρ → ENNReal) (α_total : ENNReal)
    (hBadEvent : MeasurableSet {ω | rank ω ∈ BadRanks})
    (hRank : ∀ r ∈ BadRanks, μ {ω | rank ω = r} ≤ α r)
    (h_total : (∑ r ∈ BadRanks, α r) ≤ α_total) :
    1 - α_total ≤ μ ({ω | rank ω ∈ BadRanks}ᶜ) := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  have hbad : μ {ω | rank ω ∈ BadRanks} ≤ α_total := by\n"
            "    calc\n"
            "      μ {ω | rank ω ∈ BadRanks} ≤ μ (⋃ r ∈ BadRanks, {ω | rank ω = r}) := by\n"
            "        apply measure_mono\n"
            "        intro ω hω\n"
            "        exact Set.mem_iUnion.mpr ⟨rank ω, Set.mem_iUnion.mpr ⟨hω, rfl⟩⟩\n"
            "      _ ≤ ∑ r ∈ BadRanks, μ {ω | rank ω = r} := by\n"
            "        exact measure_biUnion_finset_le (μ := μ) BadRanks (fun r => {ω | rank ω = r})\n"
            "      _ ≤ ∑ r ∈ BadRanks, α r := by\n"
            "        exact Finset.sum_le_sum (fun r hr => hRank r hr)\n"
            "      _ ≤ α_total := h_total\n"
            "  have hcoverage : μ ({ω | rank ω ∈ BadRanks}ᶜ) =\n"
            "      1 - μ {ω | rank ω ∈ BadRanks} := by\n"
            "    exact prob_compl_eq_one_sub hBadEvent\n"
            "  rw [hcoverage]\n"
            "  exact tsub_le_tsub_left hbad 1"
        ),
        tags=(
            "probability",
            "event",
            "coverage",
            "finite_sample",
            "conformal",
            "rank",
            "rank_uniformity",
            "coverage_counting",
            "finite_sample_coverage_counting",
            "order_statistic_quantile_rule",
            "union_bound",
        ),
        expected_lemmas=(
            "measure_mono",
            "Set.mem_iUnion",
            "measure_biUnion_finset_le",
            "Finset.sum_le_sum",
            "prob_compl_eq_one_sub",
            "tsub_le_tsub_left",
        ),
        depends_on=(
            "simultaneous_coverage_of_union_error_bound",
            "coverage_lower_bound_of_complement_error",
            "finite_union_budget_control",
        ),
    ),
    "finite_family_absolute_error_union_control": FormalObligation(
        id="finite_family_absolute_error_union_control",
        title="Finite-family simultaneous absolute-error control",
        english=(
            "For a finite family of estimators, if each absolute-error event is "
            "bounded by a local error budget and the local budgets sum to a "
            "total budget, then the probability that any estimator exceeds its "
            "error radius is at most the total budget. This is a reusable "
            "Bonferroni bridge for simultaneous confidence bands and ranking "
            "uncertainty; it does not claim asymptotic normality or sharp rank "
            "functional theory."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem finiteFamily_absolute_error_union_control {Ω ι : Type*}
    [MeasurableSpace Ω]
    (μ : Measure Ω) (I : Finset ι)
    (X : ι → Ω → ℝ) (theta radius : ι → ℝ)
    (α : ι → ENNReal) (α_total : ENNReal)
    (hA : ∀ i ∈ I, μ {ω | radius i ≤ |X i ω - theta i|} ≤ α i)
    (h_total : (∑ i ∈ I, α i) ≤ α_total) :
    μ (⋃ i ∈ I, {ω | radius i ≤ |X i ω - theta i|}) ≤ α_total := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  calc\n"
            "    μ (⋃ i ∈ I, {ω | radius i ≤ |X i ω - theta i|}) ≤\n"
            "        ∑ i ∈ I, μ {ω | radius i ≤ |X i ω - theta i|} := by\n"
            "      exact measure_biUnion_finset_le (μ := μ) I\n"
            "        (fun i => {ω | radius i ≤ |X i ω - theta i|})\n"
            "    _ ≤ ∑ i ∈ I, α i := by\n"
            "      exact Finset.sum_le_sum (fun i hi => hA i hi)\n"
            "    _ ≤ α_total := h_total"
        ),
        tags=(
            "estimator",
            "absolute_error",
            "simultaneous",
            "confidence",
            "bands",
            "simultaneous_confidence_bands",
            "ranking",
            "familywise_error",
            "union_bound",
            "finite_sample",
            "coverage",
        ),
        expected_lemmas=("measure_biUnion_finset_le", "Finset.sum_le_sum"),
        depends_on=("finite_union_budget_control",),
    ),
    "finite_family_absolute_error_simultaneous_coverage": FormalObligation(
        id="finite_family_absolute_error_simultaneous_coverage",
        title="Finite-family absolute-error control implies simultaneous coverage",
        english=(
            "For a finite family of estimators, if every absolute-error event "
            "has a local probability budget and those budgets sum to a total "
            "budget, then the probability that no estimator exceeds its radius "
            "is at least one minus the total budget. This composes the "
            "Bonferroni absolute-error union bridge with the complement-event "
            "coverage bridge; it still does not assert model-specific CLT or "
            "standard-error consistency."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem finiteFamily_absolute_error_simultaneous_coverage {Ω ι : Type*}
    [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ] (I : Finset ι)
    (X : ι → Ω → ℝ) (theta radius : ι → ℝ)
    (α : ι → ENNReal) (α_total : ENNReal)
    (hUnion : MeasurableSet (⋃ i ∈ I, {ω | radius i ≤ |X i ω - theta i|}))
    (hA : ∀ i ∈ I, μ {ω | radius i ≤ |X i ω - theta i|} ≤ α i)
    (h_total : (∑ i ∈ I, α i) ≤ α_total) :
    1 - α_total ≤ μ (⋃ i ∈ I, {ω | radius i ≤ |X i ω - theta i|})ᶜ := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  have hbad : μ (⋃ i ∈ I, {ω | radius i ≤ |X i ω - theta i|}) ≤ α_total := by\n"
            "    calc\n"
            "      μ (⋃ i ∈ I, {ω | radius i ≤ |X i ω - theta i|}) ≤\n"
            "          ∑ i ∈ I, μ {ω | radius i ≤ |X i ω - theta i|} := by\n"
            "        exact measure_biUnion_finset_le (μ := μ) I\n"
            "          (fun i => {ω | radius i ≤ |X i ω - theta i|})\n"
            "      _ ≤ ∑ i ∈ I, α i := by\n"
            "        exact Finset.sum_le_sum (fun i hi => hA i hi)\n"
            "      _ ≤ α_total := h_total\n"
            "  have hcoverage : μ (⋃ i ∈ I, {ω | radius i ≤ |X i ω - theta i|})ᶜ =\n"
            "      1 - μ (⋃ i ∈ I, {ω | radius i ≤ |X i ω - theta i|}) := by\n"
            "    exact prob_compl_eq_one_sub hUnion\n"
            "  rw [hcoverage]\n"
            "  exact tsub_le_tsub_left hbad 1"
        ),
        tags=(
            "estimator",
            "absolute_error",
            "simultaneous",
            "confidence",
            "bands",
            "simultaneous_confidence_bands",
            "ranking",
            "familywise_error",
            "union_bound",
            "finite_sample",
            "coverage",
            "miscoverage",
        ),
        expected_lemmas=(
            "measure_biUnion_finset_le",
            "Finset.sum_le_sum",
            "prob_compl_eq_one_sub",
            "tsub_le_tsub_left",
        ),
        depends_on=(
            "finite_family_absolute_error_union_control",
            "simultaneous_coverage_of_union_error_bound",
            "coverage_lower_bound_of_complement_error",
        ),
    ),
    "pairwise_top_rank_correct_of_separation": FormalObligation(
        id="pairwise_top_rank_correct_of_separation",
        title="Pairwise top-rank correctness under separation and error control",
        english=(
            "If item i's true target exceeds item j's true target by more than "
            "twice a common error radius, and both point estimates are within "
            "that radius of their targets, then item i is ranked above item j "
            "by the estimated values. This is a deterministic bridge from "
            "simultaneous confidence bands to pairwise ranking reliability; it "
            "does not prove full rank-functional asymptotics."
        ),
        formal_statement=_stmt(
            """
import Mathlib

theorem pairwiseTopRank_correct_of_separation
    (estimate_i estimate_j theta_i theta_j radius : ℝ)
    (hsep : theta_j + 2 * radius < theta_i)
    (hi : |estimate_i - theta_i| ≤ radius)
    (hj : |estimate_j - theta_j| ≤ radius) :
    estimate_j < estimate_i := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  have hi_abs := abs_le.mp hi\n"
            "  have hj_abs := abs_le.mp hj\n"
            "  linarith"
        ),
        tags=(
            "estimator",
            "absolute_error",
            "ranking",
            "rank_functional",
            "pairwise",
            "pairwise_country_mean_separation",
            "top_rank",
            "confidence_band",
            "real_algebra",
        ),
        expected_lemmas=("abs_le", "linarith"),
        depends_on=("wald_interval_contains_iff_abs_error",),
    ),
    "top_rank_correct_of_uniform_error_separation": FormalObligation(
        id="top_rank_correct_of_uniform_error_separation",
        title="Top-rank correctness under uniform error control and separation",
        english=(
            "If a candidate i is separated from every competitor by more than "
            "twice a common estimation-error radius, and every estimate is "
            "within that radius of its target, then every competitor's "
            "estimated value is below i's estimated value. This is the "
            "finite-family deterministic bridge that turns simultaneous "
            "absolute-error control into top-item ranking reliability."
        ),
        formal_statement=_stmt(
            """
import Mathlib

theorem topRank_correct_of_uniform_error_separation {ι : Type*}
    (theta estimate : ι → ℝ) (radius : ℝ) (i : ι)
    (hsep : ∀ j, j ≠ i → theta j + 2 * radius < theta i)
    (herr_i : |estimate i - theta i| ≤ radius)
    (herr_all : ∀ j, |estimate j - theta j| ≤ radius) :
    ∀ j, j ≠ i → estimate j < estimate i := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  intro j hij\n"
            "  have hj_abs := abs_le.mp (herr_all j)\n"
            "  have hi_abs := abs_le.mp herr_i\n"
            "  have hj_upper : estimate j ≤ theta j + radius := by\n"
            "    linarith [hj_abs.1, hj_abs.2]\n"
            "  have hi_lower : theta i - radius ≤ estimate i := by\n"
            "    linarith [hi_abs.1, hi_abs.2]\n"
            "  have hsep_j : theta j + 2 * radius < theta i := hsep j hij\n"
            "  linarith"
        ),
        tags=(
            "estimator",
            "absolute_error",
            "ranking",
            "rank_functional",
            "top_rank",
            "selection",
            "best_arm",
            "simultaneous",
            "confidence_band",
            "finite_sample",
            "real_algebra",
        ),
        expected_lemmas=("abs_le", "linarith"),
        depends_on=(
            "pairwise_top_rank_correct_of_separation",
            "finite_family_absolute_error_simultaneous_coverage",
        ),
    ),
    "screening_statistic_concentration": FormalObligation(
        id="screening_statistic_concentration",
        title="Finite screening-statistic concentration by coordinate budgets",
        english=(
            "For a finite family of screening statistics, if each coordinate's "
            "absolute screening-statistic error event has a local probability "
            "budget and the local budgets sum to a total budget, then the "
            "probability that any coordinate exceeds its tolerance is bounded "
            "by the total budget. This is a reusable concentration bridge for "
            "screening/selection traces; it does not prove a model-specific "
            "sub-Gaussian, martingale, or empirical-process concentration "
            "inequality."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem screeningStatistic_concentration {Ω ι : Type*}
    [MeasurableSpace Ω]
    (μ : Measure Ω) (I : Finset ι)
    (score : ι → Ω → ℝ) (signal tolerance : ι → ℝ)
    (α : ι → ENNReal) (α_total : ENNReal)
    (hA : ∀ i ∈ I, μ {ω | tolerance i ≤ |score i ω - signal i|} ≤ α i)
    (h_total : (∑ i ∈ I, α i) ≤ α_total) :
    μ (⋃ i ∈ I, {ω | tolerance i ≤ |score i ω - signal i|}) ≤ α_total := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  calc\n"
            "    μ (⋃ i ∈ I, {ω | tolerance i ≤ |score i ω - signal i|}) ≤\n"
            "        ∑ i ∈ I, μ {ω | tolerance i ≤ |score i ω - signal i|} := by\n"
            "      exact measure_biUnion_finset_le (μ := μ) I\n"
            "        (fun i => {ω | tolerance i ≤ |score i ω - signal i|})\n"
            "    _ ≤ ∑ i ∈ I, α i := by\n"
            "      exact Finset.sum_le_sum (fun i hi => hA i hi)\n"
            "    _ ≤ α_total := h_total"
        ),
        tags=(
            "probability",
            "event",
            "screening",
            "selection",
            "screening_statistic",
            "concentration",
            "coordinate_error",
            "high_dimensional",
            "union_bound",
            "finite_sample",
        ),
        expected_lemmas=("measure_biUnion_finset_le", "Finset.sum_le_sum"),
        depends_on=("finite_family_absolute_error_union_control", "finite_union_budget_control"),
    ),
    "signal_margin_implies_active_selection": FormalObligation(
        id="signal_margin_implies_active_selection",
        title="Signal margin implies active coordinate selection",
        english=(
            "If a true signal is larger than a selection cutoff by more than "
            "an error tolerance, and the screening statistic is within that "
            "tolerance of the signal, then the screening statistic exceeds the "
            "cutoff. This deterministic bridge turns a margin/separation "
            "condition plus concentration into active-coordinate selection; it "
            "does not prove the concentration event itself."
        ),
        formal_statement=_stmt(
            """
import Mathlib

theorem signalMargin_implies_active_selection
    (score signal cutoff tolerance : ℝ)
    (hmargin : cutoff + tolerance < signal)
    (herr : |score - signal| ≤ tolerance) :
    cutoff < score := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  have herr_bounds := abs_le.mp herr\n"
            "  linarith"
        ),
        tags=(
            "screening",
            "selection",
            "active_selection",
            "signal_margin",
            "margin_condition",
            "support_recovery",
            "high_dimensional",
            "real_algebra",
        ),
        expected_lemmas=("abs_le", "linarith"),
        depends_on=("screening_statistic_concentration",),
    ),
    "inactive_coordinate_union_bound": FormalObligation(
        id="inactive_coordinate_union_bound",
        title="Inactive-coordinate false-selection finite union bound",
        english=(
            "For a finite inactive coordinate set, if each false-selection "
            "event has a local probability budget and those budgets sum to a "
            "total budget, then the probability of any inactive coordinate "
            "being selected is at most the total budget. This is a reusable "
            "false-selection bridge for high-dimensional screening traces; it "
            "does not prove the coordinate-level false-selection bound."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem inactiveCoordinate_union_bound {Ω ι : Type*}
    [MeasurableSpace Ω]
    (μ : Measure Ω) (Inactive : Finset ι) (falseSelect : ι → Set Ω)
    (α : ι → ENNReal) (α_total : ENNReal)
    (hFalse : ∀ i ∈ Inactive, μ (falseSelect i) ≤ α i)
    (h_total : (∑ i ∈ Inactive, α i) ≤ α_total) :
    μ (⋃ i ∈ Inactive, falseSelect i) ≤ α_total := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  calc\n"
            "    μ (⋃ i ∈ Inactive, falseSelect i) ≤ ∑ i ∈ Inactive, μ (falseSelect i) := by\n"
            "      exact measure_biUnion_finset_le (μ := μ) Inactive falseSelect\n"
            "    _ ≤ ∑ i ∈ Inactive, α i := by\n"
            "      exact Finset.sum_le_sum (fun i hi => hFalse i hi)\n"
            "    _ ≤ α_total := h_total"
        ),
        tags=(
            "probability",
            "event",
            "screening",
            "selection",
            "inactive_coordinate",
            "false_selection",
            "support_recovery",
            "high_dimensional",
            "union_bound",
            "finite_sample",
        ),
        expected_lemmas=("measure_biUnion_finset_le", "Finset.sum_le_sum"),
        depends_on=("finite_union_budget_control", "selected_bad_event_probability_le_finite_union_budget"),
    ),
    "selection_accuracy_lower_bound_from_support_events": FormalObligation(
        id="selection_accuracy_lower_bound_from_support_events",
        title="Selection accuracy lower bound from support-recovery events",
        english=(
            "If a correct-selection event contains the complement of a finite "
            "union of support-recovery failure events, and each failure event "
            "has a local probability budget summing to a total budget, then "
            "the correct-selection event has probability at least one minus "
            "the total budget. This is the event-algebra bridge from active/"
            "inactive screening guarantees to selection-accuracy reporting; "
            "it does not prove the model-specific screening concentration or "
            "signal-margin conditions."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem selectionAccuracy_lower_bound_from_support_events {Ω ι : Type*}
    [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (I : Finset ι) (Bad : ι → Set Ω) (Correct : Set Ω)
    (α : ι → ENNReal) (α_total : ENNReal)
    (hUnion : MeasurableSet (⋃ i ∈ I, Bad i))
    (hCorrect : (⋃ i ∈ I, Bad i)ᶜ ⊆ Correct)
    (hBad : ∀ i ∈ I, μ (Bad i) ≤ α i)
    (h_total : (∑ i ∈ I, α i) ≤ α_total) :
    1 - α_total ≤ μ Correct := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  have hbad_union : μ (⋃ i ∈ I, Bad i) ≤ α_total := by\n"
            "    calc\n"
            "      μ (⋃ i ∈ I, Bad i) ≤ ∑ i ∈ I, μ (Bad i) := by\n"
            "        exact measure_biUnion_finset_le (μ := μ) I Bad\n"
            "      _ ≤ ∑ i ∈ I, α i := by\n"
            "        exact Finset.sum_le_sum (fun i hi => hBad i hi)\n"
            "      _ ≤ α_total := h_total\n"
            "  have hcoverage : μ (⋃ i ∈ I, Bad i)ᶜ = 1 - μ (⋃ i ∈ I, Bad i) := by\n"
            "    exact prob_compl_eq_one_sub hUnion\n"
            "  calc\n"
            "    1 - α_total ≤ μ (⋃ i ∈ I, Bad i)ᶜ := by\n"
            "      rw [hcoverage]\n"
            "      exact tsub_le_tsub_left hbad_union 1\n"
            "    _ ≤ μ Correct := by\n"
            "      exact measure_mono hCorrect"
        ),
        tags=(
            "probability",
            "event",
            "screening",
            "selection",
            "selection_accuracy",
            "support_recovery",
            "active_selection",
            "inactive_coordinate",
            "false_selection",
            "coverage",
            "high_dimensional",
            "union_bound",
            "finite_sample",
        ),
        expected_lemmas=(
            "measure_biUnion_finset_le",
            "Finset.sum_le_sum",
            "prob_compl_eq_one_sub",
            "tsub_le_tsub_left",
            "measure_mono",
        ),
        depends_on=(
            "screening_statistic_concentration",
            "signal_margin_implies_active_selection",
            "inactive_coordinate_union_bound",
            "simultaneous_coverage_of_union_error_bound",
        ),
    ),
    "mean2_estimator_chebyshev_indep": FormalObligation(
        id="mean2_estimator_chebyshev_indep",
        title="Chebyshev error bound for an average of independent estimators",
        english=(
            "For independent L2 component estimators X and Y that are each "
            "unbiased for theta, the average estimator (X+Y)/2 has an absolute "
            "error tail bounded by ((Var X + Var Y)/4)/c^2."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

noncomputable def mean2Estimator {Ω : Type*} (X Y : Ω → ℝ) : Ω → ℝ :=
  fun ω => (X ω + Y ω) / 2

theorem mean2Estimator_chebyshev_indep {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (X Y : Ω → ℝ) (theta : ℝ)
    (hX : MemLp X 2 μ) (hY : MemLp Y 2 μ)
    (h_indep : IndepFun X Y μ)
    (hEX : μ[X] = theta) (hEY : μ[Y] = theta)
    {c : ℝ} (hc : 0 < c) :
    μ {ω | c ≤ |mean2Estimator X Y ω - theta|} ≤
      ENNReal.ofReal (((variance X μ + variance Y μ) / 4) / c ^ 2) := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  have hAvgMem : MemLp (mean2Estimator X Y) 2 μ := by\n"
            "    rw [show mean2Estimator X Y = ((1 / 2 : ℝ) • (X + Y)) by\n"
            "      ext ω\n"
            "      simp [mean2Estimator]\n"
            "      ring]\n"
            "    exact (hX.add hY).const_smul (1 / 2 : ℝ)\n"
            "  have hMean : μ[mean2Estimator X Y] = theta := by\n"
            "    have hXi : Integrable X μ := hX.integrable (by norm_num)\n"
            "    have hYi : Integrable Y μ := hY.integrable (by norm_num)\n"
            "    calc\n"
            "      μ[mean2Estimator X Y] = (μ[X] + μ[Y]) / 2 := by\n"
            "        simp [mean2Estimator, integral_div, integral_add hXi hYi]\n"
            "      _ = theta := by\n"
            "        rw [hEX, hEY]\n"
            "        ring\n"
            "  have hVar : variance (mean2Estimator X Y) μ =\n"
            "      (variance X μ + variance Y μ) / 4 := by\n"
            "    rw [show mean2Estimator X Y = ((1 / 2 : ℝ) • (X + Y)) by\n"
            "      ext ω\n"
            "      simp [mean2Estimator]\n"
            "      ring]\n"
            "    rw [variance_smul, IndepFun.variance_add hX hY h_indep]\n"
            "    ring\n"
            "  rw [← hVar]\n"
            "  simpa [hMean] using\n"
            "    (meas_ge_le_variance_div_sq (μ := μ) (X := mean2Estimator X Y) hAvgMem hc)"
        ),
        tags=(
            "estimator",
            "variance",
            "mean",
            "independence",
            "tail_bound",
            "chebyshev",
            "finite_sample",
            "concentration",
        ),
        expected_lemmas=(
            "MemLp.add",
            "MemLp.const_smul",
            "integral_add",
            "variance_smul",
            "IndepFun.variance_add",
            "meas_ge_le_variance_div_sq",
        ),
        depends_on=(
            "mean2_estimator_expectation",
            "mean2_estimator_variance_indep",
            "estimator_error_chebyshev",
        ),
    ),
    "finite_sample_mean_unbiased": FormalObligation(
        id="finite_sample_mean_unbiased",
        title="Finite-sample mean estimator is unbiased",
        english=(
            "For any nonzero finite sample size n, if each component estimator "
            "is integrable and unbiased for theta, the arithmetic sample mean "
            "over Fin n is also unbiased for theta."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

noncomputable def finMeanEstimator {Ω : Type*} {n : Nat}
    (X : Fin n → Ω → ℝ) : Ω → ℝ :=
  fun ω => (∑ i, X i ω) / (n : ℝ)

theorem finMeanEstimator_unbiased {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) {n : Nat} (hn : n ≠ 0)
    (X : Fin n → Ω → ℝ) (theta : ℝ)
    (hX : ∀ i, Integrable (X i) μ)
    (hEX : ∀ i, ∫ ω, X i ω ∂μ = theta) :
    ∫ ω, finMeanEstimator X ω ∂μ = theta := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  calc\n"
            "    ∫ ω, finMeanEstimator X ω ∂μ =\n"
            "        (∑ i, ∫ ω, X i ω ∂μ) / (n : ℝ) := by\n"
            "          simp [finMeanEstimator, integral_div,\n"
            "            integral_finset_sum Finset.univ (fun i _ => hX i)]\n"
            "    _ = (∑ _ : Fin n, theta) / (n : ℝ) := by\n"
            "          simp [hEX]\n"
            "    _ = theta := by\n"
            "          rw [Finset.sum_const]\n"
            "          simp [Fintype.card_fin]\n"
            "          field_simp [hn]"
        ),
        tags=("estimator", "expectation", "linearity", "mean", "unbiased", "finite_sample"),
        expected_lemmas=("integral_finset_sum", "integral_div", "Finset.sum_const", "field_simp"),
    ),
    "finite_sample_mean_variance_indep": FormalObligation(
        id="finite_sample_mean_variance_indep",
        title="Finite-sample mean estimator variance under pairwise independence",
        english=(
            "For a finite collection of pairwise independent L2 component "
            "estimators indexed by Fin n, the arithmetic sample mean has "
            "variance equal to the sum of component variances divided by n^2."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

noncomputable def finMeanEstimator {Ω : Type*} {n : Nat}
    (X : Fin n → Ω → ℝ) : Ω → ℝ :=
  fun ω => (∑ i, X i ω) / (n : ℝ)

theorem finMeanEstimator_variance_indep {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    {n : Nat} (X : Fin n → Ω → ℝ)
    (hX : ∀ i, MemLp (X i) 2 μ)
    (h_indep : Set.Pairwise (↑(Finset.univ : Finset (Fin n)))
      fun i j => IndepFun (X i) (X j) μ) :
    variance (finMeanEstimator X) μ =
      (∑ i, variance (X i) μ) / (n : ℝ) ^ 2 := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  rw [show finMeanEstimator X = ((1 / (n : ℝ)) • (∑ i, X i)) by\n"
            "    ext ω\n"
            "    simp [finMeanEstimator]\n"
            "    ring]\n"
            "  rw [variance_smul]\n"
            "  rw [IndepFun.variance_sum]\n"
            "  · ring_nf\n"
            "  · intro i hi\n"
            "    exact hX i\n"
            "  · simpa using h_indep"
        ),
        tags=("estimator", "variance", "mean", "independence", "finite_sample", "efficiency"),
        expected_lemmas=("variance_smul", "IndepFun.variance_sum", "ring_nf"),
        depends_on=("variance_indep_add",),
    ),
    "finite_sample_mean_chebyshev_indep": FormalObligation(
        id="finite_sample_mean_chebyshev_indep",
        title="Finite-sample mean Chebyshev error bound under pairwise independence",
        english=(
            "For pairwise independent L2 component estimators indexed by Fin n "
            "that are each unbiased for theta, the arithmetic sample mean has "
            "absolute-error probability bounded by its finite-sample variance "
            "identity divided by c^2."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

noncomputable def finMeanEstimator {Ω : Type*} {n : Nat}
    (X : Fin n → Ω → ℝ) : Ω → ℝ :=
  fun ω => (∑ i, X i ω) / (n : ℝ)

theorem finMeanEstimator_chebyshev_indep {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    {n : Nat} (hn : n ≠ 0)
    (X : Fin n → Ω → ℝ) (theta : ℝ)
    (hX : ∀ i, MemLp (X i) 2 μ)
    (h_indep : Set.Pairwise (↑(Finset.univ : Finset (Fin n)))
      fun i j => IndepFun (X i) (X j) μ)
    (hEX : ∀ i, μ[X i] = theta)
    {c : ℝ} (hc : 0 < c) :
    μ {ω | c ≤ |finMeanEstimator X ω - theta|} ≤
      ENNReal.ofReal (((∑ i, variance (X i) μ) / (n : ℝ) ^ 2) / c ^ 2) := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  have hAvgMem : MemLp (finMeanEstimator X) 2 μ := by\n"
            "    rw [show finMeanEstimator X = ((1 / (n : ℝ)) • (∑ i, X i)) by\n"
            "      ext ω\n"
            "      simp [finMeanEstimator]\n"
            "      ring]\n"
            "    exact (memLp_finset_sum' Finset.univ (fun i hi => hX i)).const_smul (1 / (n : ℝ))\n"
            "  have hMean : μ[finMeanEstimator X] = theta := by\n"
            "    have hXi : ∀ i, Integrable (X i) μ := fun i => (hX i).integrable (by norm_num)\n"
            "    calc\n"
            "      μ[finMeanEstimator X] = (∑ i, μ[X i]) / (n : ℝ) := by\n"
            "        simp [finMeanEstimator, integral_div,\n"
            "          integral_finset_sum Finset.univ (fun i _ => hXi i)]\n"
            "      _ = (∑ _ : Fin n, theta) / (n : ℝ) := by\n"
            "        simp [hEX]\n"
            "      _ = theta := by\n"
            "        rw [Finset.sum_const]\n"
            "        simp [Fintype.card_fin]\n"
            "        field_simp [hn]\n"
            "  have hVar : variance (finMeanEstimator X) μ =\n"
            "      (∑ i, variance (X i) μ) / (n : ℝ) ^ 2 := by\n"
            "    rw [show finMeanEstimator X = ((1 / (n : ℝ)) • (∑ i, X i)) by\n"
            "      ext ω\n"
            "      simp [finMeanEstimator]\n"
            "      ring]\n"
            "    rw [variance_smul]\n"
            "    rw [IndepFun.variance_sum]\n"
            "    · ring_nf\n"
            "    · intro i hi\n"
            "      exact hX i\n"
            "    · simpa using h_indep\n"
            "  rw [← hVar]\n"
            "  simpa [hMean] using\n"
            "    (meas_ge_le_variance_div_sq (μ := μ) (X := finMeanEstimator X) hAvgMem hc)"
        ),
        tags=(
            "estimator",
            "variance",
            "mean",
            "independence",
            "tail_bound",
            "chebyshev",
            "finite_sample",
            "concentration",
        ),
        expected_lemmas=(
            "memLp_finset_sum'",
            "integral_finset_sum",
            "IndepFun.variance_sum",
            "meas_ge_le_variance_div_sq",
        ),
        depends_on=(
            "finite_sample_mean_unbiased",
            "finite_sample_mean_variance_indep",
            "estimator_error_chebyshev",
        ),
    ),
    "block_estimator_chebyshev_bound": FormalObligation(
        id="block_estimator_chebyshev_bound",
        title="Block-estimator Chebyshev failure bound",
        english=(
            "For any L2 block estimator B with expectation theta, the probability "
            "that the block estimate is farther than c from theta is bounded by "
            "Var(B)/c^2. This is the reusable formal bridge for the block-failure "
            "ingredient in median-of-means proofs; it does not claim the full "
            "median amplification theorem."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem blockEstimator_error_chebyshev {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (B : Ω → ℝ) (theta : ℝ) (hB : MemLp B 2 μ)
    (hMean : μ[B] = theta) {c : ℝ} (hc : 0 < c) :
    μ {ω | c ≤ |B ω - theta|} ≤ ENNReal.ofReal (variance B μ / c ^ 2) := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  simpa [hMean] using\n"
            "    (meas_ge_le_variance_div_sq (μ := μ) (X := B) hB hc)"
        ),
        tags=(
            "estimator",
            "block",
            "robust",
            "median_of_means",
            "variance",
            "tail_bound",
            "chebyshev",
            "finite_sample",
            "concentration",
        ),
        expected_lemmas=("meas_ge_le_variance_div_sq",),
        depends_on=("estimator_error_chebyshev",),
    ),
    "median_of_means_failure_union_control": FormalObligation(
        id="median_of_means_failure_union_control",
        title="Median-of-means bad-block union control",
        english=(
            "If a median-of-means failure event is contained in the finite "
            "union of bad block events, and each block failure has a local "
            "probability budget, then the median failure probability is "
            "controlled by the sum of those budgets. This is a reusable finite "
            "block-control bridge for median-of-means traces; it does not prove "
            "the binomial majority tail or the sharp sub-Gaussian MoM theorem."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem medianOfMeans_failure_union_control {Ω ι : Type*}
    [MeasurableSpace Ω]
    (μ : Measure Ω) (Blocks : Finset ι) (BadBlock : ι → Set Ω)
    (MedianBad : Set Ω) (α : ι → ENNReal) (α_total : ENNReal)
    (hSubset : MedianBad ⊆ ⋃ i ∈ Blocks, BadBlock i)
    (hBlock : ∀ i ∈ Blocks, μ (BadBlock i) ≤ α i)
    (h_total : (∑ i ∈ Blocks, α i) ≤ α_total) :
    μ MedianBad ≤ α_total := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  calc\n"
            "    μ MedianBad ≤ μ (⋃ i ∈ Blocks, BadBlock i) := by\n"
            "      exact measure_mono hSubset\n"
            "    _ ≤ ∑ i ∈ Blocks, μ (BadBlock i) := by\n"
            "      exact measure_biUnion_finset_le (μ := μ) Blocks BadBlock\n"
            "    _ ≤ ∑ i ∈ Blocks, α i := by\n"
            "      exact Finset.sum_le_sum (fun i hi => hBlock i hi)\n"
            "    _ ≤ α_total := h_total"
        ),
        tags=(
            "probability",
            "event",
            "union_bound",
            "finite_sample",
            "robust",
            "median_of_means",
            "median_of_means_deviation",
            "block",
            "block_mean",
            "block_mean_definition",
            "independent_blocks",
            "chebyshev_block_failure_bound",
            "concentration",
        ),
        expected_lemmas=("measure_mono", "measure_biUnion_finset_le", "Finset.sum_le_sum"),
        depends_on=("block_estimator_chebyshev_bound", "finite_union_budget_control"),
    ),
    "affine_estimator_expectation": FormalObligation(
        id="affine_estimator_expectation",
        title="Affine estimator expectation",
        english=(
            "For an integrable estimator X on a probability space, the expectation "
            "of the affine shrinkage estimator a*X+b is a*E[X]+b."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

noncomputable def affineEstimator {Ω : Type*} (a b : ℝ) (X : Ω → ℝ) : Ω → ℝ :=
  fun ω => a * X ω + b

theorem affineEstimator_expectation {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (X : Ω → ℝ) (a b : ℝ) (hX : Integrable X μ) :
    ∫ ω, affineEstimator a b X ω ∂μ = a * (∫ ω, X ω ∂μ) + b := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  calc\n"
            "    ∫ ω, affineEstimator a b X ω ∂μ =\n"
            "        (∫ ω, a * X ω ∂μ) + ∫ ω, b ∂μ := by\n"
            "          simp [affineEstimator, integral_add (hX.const_mul a) (integrable_const b)]\n"
            "    _ = a * (∫ ω, X ω ∂μ) + b := by\n"
            "          simp [integral_const_mul]"
        ),
        tags=("estimator", "expectation", "linearity", "affine", "shrinkage", "bayesian"),
        expected_lemmas=("integral_add", "integral_const_mul", "integral_const", "measure_univ"),
    ),
    "affine_estimator_variance": FormalObligation(
        id="affine_estimator_variance",
        title="Affine estimator variance",
        english=(
            "For an L2 estimator X on a probability space, the variance of the "
            "affine shrinkage estimator a*X+b is a^2 times Var(X)."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

noncomputable def affineEstimator {Ω : Type*} (a b : ℝ) (X : Ω → ℝ) : Ω → ℝ :=
  fun ω => a * X ω + b

theorem affineEstimator_variance {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (X : Ω → ℝ) (a b : ℝ) (hX : MemLp X 2 μ) :
    variance (affineEstimator a b X) μ = a ^ 2 * variance X μ := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  unfold affineEstimator\n"
            "  rw [variance_add_const ((hX.aestronglyMeasurable).const_mul a) b]\n"
            "  exact variance_const_mul a X μ"
        ),
        tags=("estimator", "variance", "affine", "shrinkage", "bayesian", "finite_sample"),
        expected_lemmas=("variance_add_const", "variance_const_mul"),
        depends_on=("variance_nonneg",),
    ),
    "event_indicator_expectation": FormalObligation(
        id="event_indicator_expectation",
        title="Indicator estimator expectation equals event mass",
        english=(
            "For a measurable event A, the expectation of its 0/1 indicator "
            "equals the event's measure."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

noncomputable def eventIndicator {Ω : Type*} (A : Set Ω) : Ω → ℝ :=
  A.indicator (fun _ => (1 : ℝ))

theorem eventIndicator_expectation {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) (A : Set Ω) (hA : MeasurableSet A) :
    ∫ ω, eventIndicator A ω ∂μ = μ.real A := by sorry
"""
        ),
        proof_body="by\n  simp [eventIndicator, integral_indicator_const, hA]",
        tags=("estimator", "bernoulli", "indicator", "expectation", "probability"),
        expected_lemmas=("integral_indicator_const",),
    ),
    "event_indicator_product_integral_eq_inter": FormalObligation(
        id="event_indicator_product_integral_eq_inter",
        title="Product of two event indicators integrates to intersection mass",
        english=(
            "For measurable events A and B, the integral of the product of "
            "their 0/1 indicators is the measure of the intersection. This is "
            "the finite product-process bridge used before independence turns "
            "intersection probabilities into products; it does not prove "
            "conditional-expectation martingale preservation or likelihood-ratio "
            "validity by itself."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory

theorem eventIndicatorProduct_integral_eq_inter {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) (A B : Set Ω)
    (hA : MeasurableSet A) (hB : MeasurableSet B) :
    ∫ ω, (A.indicator (1 : Ω → ℝ) * B.indicator (1 : Ω → ℝ)) ω ∂μ =
      μ.real (A ∩ B) := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  rw [← Set.inter_indicator_one]\n"
            "  exact integral_indicator_one (hA.inter hB)"
        ),
        tags=(
            "probability",
            "event",
            "indicator",
            "indicator_product",
            "intersection",
            "expectation",
            "bernoulli",
            "likelihood_ratio",
            "product_process",
            "adapted_product_process",
            "conditional_expectation_product_step",
            "sequential",
        ),
        expected_lemmas=("Set.inter_indicator_one", "integral_indicator_one"),
        depends_on=("event_indicator_expectation",),
    ),
    "independent_event_indicator_product_lintegral_eq_mul": FormalObligation(
        id="independent_event_indicator_product_lintegral_eq_mul",
        title="Independent event indicators have factored product lintegral",
        english=(
            "For independent measurable events A and B, the lintegral of the "
            "product of their ENNReal 0/1 indicators factors as `μ A * μ B`. "
            "This is a reusable bridge for independent Bernoulli sequences, "
            "product-process likelihood ratios, and martingale skeletons; it "
            "does not prove conditional-expectation preservation for an entire "
            "process."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem independentEventIndicatorProduct_lintegral_eq_mul {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) (A B : Set Ω)
    (hA : MeasurableSet A) (hB : MeasurableSet B)
    (h_indep : IndepSet A B μ) :
    ∫⁻ ω, (A.indicator (1 : Ω → ENNReal) * B.indicator (1 : Ω → ENNReal)) ω ∂μ =
      μ A * μ B := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  rw [← Set.inter_indicator_one]\n"
            "  rw [lintegral_indicator_one (hA.inter hB)]\n"
            "  exact h_indep.measure_inter_eq_mul"
        ),
        tags=(
            "probability",
            "event",
            "indicator",
            "indicator_product",
            "independence",
            "bernoulli",
            "independent_bernoulli_sequence",
            "likelihood_ratio",
            "product_process",
            "adapted_product_process",
            "conditional_expectation_product_step",
            "martingale_definition",
            "sequential",
        ),
        expected_lemmas=(
            "Set.inter_indicator_one",
            "lintegral_indicator_one",
            "IndepSet.measure_inter_eq_mul",
        ),
        depends_on=("event_indicator_product_integral_eq_inter", "independent_event_inter_probability"),
    ),
    "independent_event_indicator_condExp_filtration_eq_prob": FormalObligation(
        id="independent_event_indicator_condExp_filtration_eq_prob",
        title="Future independent event indicator has constant conditional expectation over past filtration",
        english=(
            "For an independent sequence of measurable events, the conditional "
            "expectation of a future event's 0/1 indicator given the filtration "
            "generated by past events is almost everywhere the event probability. "
            "This is the first direct conditional-expectation bridge for the "
            "Bernoulli likelihood-ratio martingale skeleton; it still does not "
            "prove the full product-process martingale theorem."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem independentSet_indicator_condExp_filtrationOfSet_ae_eq {Ω : Type*} [MeasurableSpace Ω]
    {μ : Measure Ω} {s : ℕ → Set Ω}
    (hsm : ∀ n, MeasurableSet (s n)) (hs : iIndepSet s μ)
    {i j : ℕ} (hij : i < j) :
    μ[(s j).indicator (fun _ => 1 : Ω → ℝ) | filtrationOfSet hsm i] =ᵐ[μ]
      fun _ => μ.real (s j) := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  exact hs.condExp_indicator_filtrationOfSet_ae_eq hsm hij"
        ),
        tags=(
            "probability",
            "event",
            "indicator",
            "conditional_expectation",
            "filtration",
            "independence",
            "bernoulli",
            "independent_bernoulli_sequence",
            "likelihood_ratio",
            "product_process",
            "adapted_product_process",
            "conditional_expectation_product_step",
            "martingale_definition",
            "sequential",
        ),
        expected_lemmas=("iIndepSet.condExp_indicator_filtrationOfSet_ae_eq",),
        depends_on=(
            "event_indicator_expectation",
            "filtration_mono_measurable_set",
            "independent_event_indicator_product_lintegral_eq_mul",
        ),
    ),
    "independent_real_condExp_natural_eq_mean": FormalObligation(
        id="independent_real_condExp_natural_eq_mean",
        title="Future independent real variable has mean conditional expectation over natural past filtration",
        english=(
            "For an independent real-valued stochastic sequence, the "
            "conditional expectation of a future variable given the natural "
            "filtration of past variables is almost everywhere its mean. This "
            "is a reusable bridge for sample-moment LLN/CLT skeletons, "
            "martingale-difference decompositions, and regression/asymptotic "
            "normality traces; it is not a full CLT or LLN proof."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem independentReal_condExp_natural_ae_eq_of_lt {Ω : Type*} [MeasurableSpace Ω]
    {μ : Measure Ω} {X : ℕ → Ω → ℝ}
    (hX : ∀ n, StronglyMeasurable (X n)) (h_ind : iIndepFun X μ)
    {i j : ℕ} (hij : i < j) :
    μ[X j | Filtration.natural X hX i] =ᵐ[μ] fun _ => μ[X j] := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  exact h_ind.condExp_natural_ae_eq_of_lt hX hij"
        ),
        tags=(
            "probability",
            "conditional_expectation",
            "filtration",
            "independence",
            "real_valued_sequence",
            "martingale_difference",
            "iid_empirical_mean_clt",
            "sample_moment_lln",
            "exogeneity_moment_condition",
            "martingale_definition",
            "heteroskedastic_regression",
            "semiparametric_causal_ate",
            "asymptotic_normality",
        ),
        expected_lemmas=("iIndepFun.condExp_natural_ae_eq_of_lt",),
        depends_on=("filtration_mono_measurable_set",),
    ),
    "iid_real_clt_tendsto_distribution": FormalObligation(
        id="iid_real_clt_tendsto_distribution",
        title="Mathlib one-dimensional iid real central limit theorem bridge",
        english=(
            "For an independent identically distributed real-valued sequence "
            "with finite second moment, the centered sqrt(n)-scaled partial sum "
            "converges in distribution to the Gaussian law with matching "
            "variance. This is the first registered full asymptotic limit "
            "theorem in the AI Statistician proof bank; it still does not prove "
            "multivariate score CLTs, Slutsky, sandwich variance consistency, or "
            "problem-specific estimator asymptotic normality end to end."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory Filter
open scoped Real Topology

theorem iidReal_tendstoInDistribution_inv_sqrt_sum_sub {Ω Ω' : Type*}
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    {P : Measure Ω} {P' : Measure Ω'} [IsProbabilityMeasure P] [IsProbabilityMeasure P']
    {X : ℕ → Ω → ℝ} {Y : Ω' → ℝ}
    (hY : HasLaw Y (gaussianReal 0 Var[X 0; P].toNNReal) P')
    (hX : MemLp (X 0) 2 P) (hindep : iIndepFun X P)
    (hident : ∀ (i : ℕ), IdentDistrib (X i) (X 0) P P) :
    TendstoInDistribution
      (fun (n : ℕ) ω => (√n)⁻¹ * (∑ k ∈ Finset.range n, X k ω - n * P[X 0]))
      atTop Y (fun _ => P) P' := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  exact tendstoInDistribution_inv_sqrt_mul_sum_sub hY hX hindep hident"
        ),
        tags=(
            "probability",
            "central_limit_theorem",
            "asymptotic_normality",
            "convergence_in_distribution",
            "iid_empirical_mean_clt",
            "multivariate_score_clt",
            "sample_moment_lln",
            "wald_interval_slutsky",
            "semiparametric_causal_ate",
            "heteroskedastic_regression",
            "influence_function_variance",
        ),
        expected_lemmas=("tendstoInDistribution_inv_sqrt_mul_sum_sub",),
        depends_on=(
            "independent_real_condExp_natural_eq_mean",
            "finite_sample_mean_variance_indep",
            "variance_nonneg",
        ),
    ),
    "tendsto_in_distribution_continuous_mapping": FormalObligation(
        id="tendsto_in_distribution_continuous_mapping",
        title="Continuous mapping theorem for convergence in distribution",
        english=(
            "If random variables X_i converge in distribution to Z and g is "
            "continuous, then g ∘ X_i converges in distribution to g ∘ Z. "
            "This is the reusable Mathlib bridge behind delta-method, "
            "Wald-transform, matrix inverse, rank-functional, and tail-quantile "
            "continuous-mapping theorem skeletons. It does not prove Frechet "
            "differentiability, estimator consistency, or problem-specific "
            "linearization remainders."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory Filter
open scoped Topology

theorem tendstoInDistribution_continuousMapping_bridge
    {ι : Type*} {E F : Type*} {Ω : ι → Type*} {Ω' : Type*}
    {mΩ : (i : ι) → MeasurableSpace (Ω i)}
    {μ : (i : ι) → @Measure (Ω i) (mΩ i)}
    [∀ i, IsProbabilityMeasure (μ i)]
    {mΩ' : MeasurableSpace Ω'} {μ' : @Measure Ω' mΩ'}
    [IsProbabilityMeasure μ']
    [TopologicalSpace E] [MeasurableSpace E] [OpensMeasurableSpace E]
    [TopologicalSpace F] [MeasurableSpace F] [BorelSpace F]
    {X : (i : ι) → Ω i → E} {Z : Ω' → E} {l : Filter ι} {g : E → F}
    (h : TendstoInDistribution X l Z μ μ') (hg : Continuous g) :
    TendstoInDistribution (fun i => g ∘ X i) l (g ∘ Z) μ μ' := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  exact h.continuous_comp hg"
        ),
        tags=(
            "probability",
            "continuous_mapping",
            "convergence_in_distribution",
            "delta_method",
            "asymptotic_normality",
            "wald_interval_slutsky",
            "matrix_inverse_continuous_mapping",
            "tail_quantile_continuous_mapping",
            "rank_uncertainty_functional_delta_method",
            "graph_functional_delta_method",
            "product_limit_delta_method",
        ),
        expected_lemmas=("TendstoInDistribution.continuous_comp",),
        depends_on=("iid_real_clt_tendsto_distribution",),
    ),
    "slutsky_add_negligible_zero_real": FormalObligation(
        id="slutsky_add_negligible_zero_real",
        title="Real Slutsky addition bridge for a negligible remainder",
        english=(
            "If a real-valued main statistic converges in distribution and an "
            "additive real-valued remainder converges to zero in probability, "
            "then their sum has the same distributional limit. This is the "
            "reusable Mathlib Slutsky bridge behind asymptotic linearity, "
            "Wald intervals, semiparametric influence-function expansions, "
            "and regression sandwich skeletons. It still assumes the negligible "
            "remainder as a `TendstoInMeasure` input rather than proving a "
            "specific empirical-process remainder bound."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory Filter
open scoped Topology

theorem real_slutsky_add_negligible_zero
    {ι Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    {sampleLaw : Measure Sample} {limitLaw : Measure LimitSample}
    [IsProbabilityMeasure sampleLaw] [IsProbabilityMeasure limitLaw]
    {l : Filter ι} [l.IsCountablyGenerated]
    (main remainder : ι → Sample → ℝ)
    (limit : LimitSample → ℝ)
    (hmain :
      TendstoInDistribution main l limit (fun _ => sampleLaw) limitLaw)
    (hremainder :
      TendstoInMeasure sampleLaw remainder l (fun _ => (0 : ℝ)))
    (hremainder_meas :
      ∀ index, AEMeasurable (remainder index) sampleLaw) :
    TendstoInDistribution
      (fun index sample => main index sample + remainder index sample)
      l limit (fun _ => sampleLaw) limitLaw := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  simpa using\n"
            "    hmain.add_of_tendstoInMeasure_const\n"
            "      (Y := remainder)\n"
            "      (c := (0 : ℝ))\n"
            "      hremainder hremainder_meas"
        ),
        tags=(
            "probability",
            "slutsky",
            "convergence_in_distribution",
            "convergence_in_probability",
            "negligible_remainder",
            "asymptotic_linearity",
            "asymptotic_normality",
            "wald_interval_slutsky",
            "semiparametric_causal_ate",
            "heteroskedastic_regression",
            "influence_function_variance",
            "empirical_process_remainder_bound",
        ),
        expected_lemmas=("TendstoInDistribution.add_of_tendstoInMeasure_const",),
        depends_on=(
            "iid_real_clt_tendsto_distribution",
            "tendsto_in_distribution_continuous_mapping",
        ),
    ),
    "finite_event_indicator_mean_unbiased": FormalObligation(
        id="finite_event_indicator_mean_unbiased",
        title="Finite-sample event-indicator mean is unbiased",
        english=(
            "For any nonzero finite sample size n, if each measurable event "
            "A_i has the same probability p, the arithmetic mean of the event "
            "indicators 1_{A_i} is an unbiased estimator of p."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

noncomputable def eventIndicator {Ω : Type*} (A : Set Ω) : Ω → ℝ :=
  A.indicator (fun _ => (1 : ℝ))

noncomputable def finMeanEstimator {Ω : Type*} {n : Nat}
    (X : Fin n → Ω → ℝ) : Ω → ℝ :=
  fun ω => (∑ i, X i ω) / (n : ℝ)

theorem finiteEventIndicatorMean_unbiased {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ] {n : Nat} (hn : n ≠ 0)
    (A : Fin n → Set Ω) (p : ℝ)
    (hA : ∀ i, MeasurableSet (A i))
    (hP : ∀ i, μ.real (A i) = p) :
    ∫ ω, finMeanEstimator (fun i => eventIndicator (A i)) ω ∂μ = p := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  have hInt : ∀ i, Integrable (eventIndicator (A i)) μ := by\n"
            "    intro i\n"
            "    exact (integrable_const (1 : ℝ)).indicator (hA i)\n"
            "  have hEach : ∀ i, ∫ ω, eventIndicator (A i) ω ∂μ = p := by\n"
            "    intro i\n"
            "    calc\n"
            "      ∫ ω, eventIndicator (A i) ω ∂μ = μ.real (A i) := by\n"
            "        simpa [eventIndicator] using (integral_indicator_const (1 : ℝ) (hA i))\n"
            "      _ = p := hP i\n"
            "  calc\n"
            "    ∫ ω, finMeanEstimator (fun i => eventIndicator (A i)) ω ∂μ =\n"
            "        (∑ i, ∫ ω, eventIndicator (A i) ω ∂μ) / (n : ℝ) := by\n"
            "          simp [finMeanEstimator, integral_div,\n"
            "            integral_finset_sum Finset.univ (fun i _ => hInt i)]\n"
            "    _ = (∑ _ : Fin n, p) / (n : ℝ) := by\n"
            "          simp [hEach]\n"
            "    _ = p := by\n"
            "          rw [Finset.sum_const]\n"
            "          simp [Fintype.card_fin]\n"
            "          field_simp [hn]"
        ),
        tags=(
            "estimator",
            "bernoulli",
            "indicator",
            "expectation",
            "probability",
            "unbiased",
            "finite_sample",
        ),
        expected_lemmas=(
            "integral_indicator_const",
            "integral_finset_sum",
            "integrable_const",
            "Finset.sum_const",
            "field_simp",
        ),
        depends_on=("event_indicator_expectation", "finite_sample_mean_unbiased"),
    ),
    "noised_estimator_unbiased": FormalObligation(
        id="noised_estimator_unbiased",
        title="Adding mean-zero noise preserves unbiasedness",
        english=(
            "If an estimator X is unbiased for theta and an additive noise "
            "variable Z has mean zero, then X+Z is also unbiased for theta."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

noncomputable def noisedEstimator {Ω : Type*} (X Z : Ω → ℝ) : Ω → ℝ :=
  X + Z

theorem noisedEstimator_unbiased {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) (X Z : Ω → ℝ) (theta : ℝ)
    (hX : Integrable X μ) (hZ : Integrable Z μ)
    (hEX : ∫ ω, X ω ∂μ = theta)
    (hEZ : ∫ ω, Z ω ∂μ = 0) :
    ∫ ω, noisedEstimator X Z ω ∂μ = theta := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  calc\n"
            "    ∫ ω, noisedEstimator X Z ω ∂μ = μ[X] + μ[Z] := by\n"
            "      simp [noisedEstimator, integral_add hX hZ]\n"
            "    _ = theta := by\n"
            "      rw [hEX, hEZ]\n"
            "      ring"
        ),
        tags=("estimator", "expectation", "linearity", "noise", "unbiased", "finite_sample", "privacy"),
        expected_lemmas=("integral_add", "ring"),
    ),
    "noised_estimator_variance_indep": FormalObligation(
        id="noised_estimator_variance_indep",
        title="Independent additive noise variance decomposition",
        english=(
            "If an estimator X and additive noise Z are independent and both "
            "have finite second moments, then Var(X+Z)=Var(X)+Var(Z)."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

noncomputable def noisedEstimator {Ω : Type*} (X Z : Ω → ℝ) : Ω → ℝ :=
  X + Z

theorem noisedEstimator_variance_indep {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (X Z : Ω → ℝ) (hX : MemLp X 2 μ) (hZ : MemLp Z 2 μ)
    (h_indep : IndepFun X Z μ) :
    variance (noisedEstimator X Z) μ = variance X μ + variance Z μ := by sorry
"""
        ),
        proof_body="by\n  simpa [noisedEstimator] using IndepFun.variance_add hX hZ h_indep",
        tags=("estimator", "variance", "noise", "independence", "finite_sample", "privacy"),
        expected_lemmas=("IndepFun.variance_add",),
        depends_on=("variance_indep_add",),
    ),
    "noised_estimator_chebyshev_indep": FormalObligation(
        id="noised_estimator_chebyshev_indep",
        title="Chebyshev bound for an estimator with independent additive noise",
        english=(
            "If X is unbiased for theta, Z has mean zero, X and Z are "
            "independent L2 variables, then the noised estimator X+Z has "
            "absolute error tail bounded by (Var X + Var Z)/c^2."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

noncomputable def noisedEstimator {Ω : Type*} (X Z : Ω → ℝ) : Ω → ℝ :=
  X + Z

theorem noisedEstimator_chebyshev_indep {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (X Z : Ω → ℝ) (theta : ℝ)
    (hX : MemLp X 2 μ) (hZ : MemLp Z 2 μ)
    (h_indep : IndepFun X Z μ)
    (hEX : μ[X] = theta) (hEZ : μ[Z] = 0)
    {c : ℝ} (hc : 0 < c) :
    μ {ω | c ≤ |noisedEstimator X Z ω - theta|} ≤
      ENNReal.ofReal ((variance X μ + variance Z μ) / c ^ 2) := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  have hNoisedMem : MemLp (noisedEstimator X Z) 2 μ := by\n"
            "    simpa [noisedEstimator] using hX.add hZ\n"
            "  have hMean : μ[noisedEstimator X Z] = theta := by\n"
            "    have hXi : Integrable X μ := hX.integrable (by norm_num)\n"
            "    have hZi : Integrable Z μ := hZ.integrable (by norm_num)\n"
            "    calc\n"
            "      μ[noisedEstimator X Z] = μ[X] + μ[Z] := by\n"
            "        simp [noisedEstimator, integral_add hXi hZi]\n"
            "      _ = theta := by\n"
            "        rw [hEX, hEZ]\n"
            "        ring\n"
            "  have hVar : variance (noisedEstimator X Z) μ = variance X μ + variance Z μ := by\n"
            "    simpa [noisedEstimator] using IndepFun.variance_add hX hZ h_indep\n"
            "  rw [← hVar]\n"
            "  simpa [hMean] using\n"
            "    (meas_ge_le_variance_div_sq (μ := μ) (X := noisedEstimator X Z) hNoisedMem hc)"
        ),
        tags=(
            "estimator",
            "variance",
            "noise",
            "independence",
            "tail_bound",
            "chebyshev",
            "finite_sample",
            "concentration",
            "privacy",
        ),
        expected_lemmas=(
            "MemLp.add",
            "integral_add",
            "IndepFun.variance_add",
            "meas_ge_le_variance_div_sq",
        ),
        depends_on=(
            "noised_estimator_unbiased",
            "noised_estimator_variance_indep",
            "estimator_error_chebyshev",
        ),
    ),
    "aipw_score_expectation_decompose": FormalObligation(
        id="aipw_score_expectation_decompose",
        title="AIPW score expectation decomposes by linearity",
        english=(
            "For integrable contrast and augmentation terms, the expectation of "
            "an AIPW-style score contrast + treated augmentation - control "
            "augmentation decomposes into the corresponding sum and difference "
            "of expectations."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

noncomputable def aipwScore {Ω : Type*}
    (contrast treatAug controlAug : Ω → ℝ) : Ω → ℝ :=
  contrast + treatAug - controlAug

theorem aipwScore_expectation_decompose {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) (contrast treatAug controlAug : Ω → ℝ)
    (hContrast : Integrable contrast μ)
    (hTreat : Integrable treatAug μ)
    (hControl : Integrable controlAug μ) :
    ∫ ω, aipwScore contrast treatAug controlAug ω ∂μ =
      (∫ ω, contrast ω ∂μ) + (∫ ω, treatAug ω ∂μ) -
        (∫ ω, controlAug ω ∂μ) := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  calc\n"
            "    ∫ ω, aipwScore contrast treatAug controlAug ω ∂μ =\n"
            "        ∫ ω, ((contrast + treatAug - controlAug) : Ω → ℝ) ω ∂μ := by\n"
            "          rfl\n"
            "    _ = ∫ ω, ((contrast + treatAug) : Ω → ℝ) ω ∂μ - ∫ ω, controlAug ω ∂μ := by\n"
            "          exact integral_sub (hContrast.add hTreat) hControl\n"
            "    _ = (∫ ω, contrast ω ∂μ) + (∫ ω, treatAug ω ∂μ) -\n"
            "          ∫ ω, controlAug ω ∂μ := by\n"
            "          have hAdd : ∫ ω, ((contrast + treatAug) : Ω → ℝ) ω ∂μ =\n"
            "              (∫ ω, contrast ω ∂μ) + (∫ ω, treatAug ω ∂μ) := by\n"
            "            simpa using integral_add hContrast hTreat\n"
            "          rw [hAdd]"
        ),
        tags=("estimator", "expectation", "linearity", "aipw", "causal", "semiparametric"),
        expected_lemmas=("integral_add", "integral_sub"),
    ),
    "aipw_score_expectation_target_of_aug_cancel": FormalObligation(
        id="aipw_score_expectation_target_of_aug_cancel",
        title="AIPW score expectation equals target when augmentation expectations cancel",
        english=(
            "If an AIPW-style contrast has expectation psi and the treated and "
            "control augmentation terms have equal expectations, then the full "
            "contrast + treated augmentation - control augmentation score also "
            "has expectation psi. This is the finite expectation-algebra bridge "
            "used before formalizing conditional mean residual cancellation or "
            "double robustness; it does not prove nuisance correctness or "
            "conditional-expectation identities."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

noncomputable def aipwScore {Ω : Type*}
    (contrast treatAug controlAug : Ω → ℝ) : Ω → ℝ :=
  contrast + treatAug - controlAug

theorem aipwScore_expectation_eq_target_of_aug_cancel {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) (contrast treatAug controlAug : Ω → ℝ) (psi : ℝ)
    (hContrast : Integrable contrast μ)
    (hTreat : Integrable treatAug μ)
    (hControl : Integrable controlAug μ)
    (hContrastMean : (∫ ω, contrast ω ∂μ) = psi)
    (hAugCancel : (∫ ω, treatAug ω ∂μ) = (∫ ω, controlAug ω ∂μ)) :
    ∫ ω, aipwScore contrast treatAug controlAug ω ∂μ = psi := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  calc\n"
            "    ∫ ω, aipwScore contrast treatAug controlAug ω ∂μ =\n"
            "        ∫ ω, ((contrast + treatAug - controlAug) : Ω → ℝ) ω ∂μ := by\n"
            "          rfl\n"
            "    _ = ∫ ω, ((contrast + treatAug) : Ω → ℝ) ω ∂μ - ∫ ω, controlAug ω ∂μ := by\n"
            "          exact integral_sub (hContrast.add hTreat) hControl\n"
            "    _ = (∫ ω, contrast ω ∂μ) + (∫ ω, treatAug ω ∂μ) -\n"
            "          ∫ ω, controlAug ω ∂μ := by\n"
            "          have hAdd : ∫ ω, ((contrast + treatAug) : Ω → ℝ) ω ∂μ =\n"
            "              (∫ ω, contrast ω ∂μ) + (∫ ω, treatAug ω ∂μ) := by\n"
            "            simpa using integral_add hContrast hTreat\n"
            "          rw [hAdd]\n"
            "    _ = psi := by\n"
            "          rw [hContrastMean, hAugCancel]\n"
            "          ring"
        ),
        tags=(
            "estimator",
            "expectation",
            "linearity",
            "aipw",
            "causal",
            "semiparametric",
            "double_robustness",
            "conditional_mean_residual_zero",
            "nuisance_correctness_cases",
            "augmentation_cancel",
        ),
        expected_lemmas=("integral_add", "integral_sub", "ring"),
        depends_on=("aipw_score_expectation_decompose",),
    ),
    "conditional_mean_residual_zero_of_mean_eq": FormalObligation(
        id="conditional_mean_residual_zero_of_mean_eq",
        title="Residual mean is zero when centered at its expectation",
        english=(
            "If a real-valued outcome has finite mean m, then the centered "
            "residual Y - m has mean zero. This is the direct finite "
            "expectation bridge used after a conditional-expectation or "
            "nuisance-correctness argument has reduced an AIPW residual term "
            "to an ordinary mean-equality premise; it does not prove the "
            "conditional-expectation identity itself."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem conditionalMeanResidual_zero_of_mean_eq {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (Y : Ω → ℝ) (m : ℝ)
    (hY : Integrable Y μ)
    (hMean : ∫ ω, Y ω ∂μ = m) :
    ∫ ω, (Y ω - m) ∂μ = 0 := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  rw [integral_sub hY (integrable_const m)]\n"
            "  simp [hMean]"
        ),
        tags=(
            "estimator",
            "expectation",
            "linearity",
            "residual",
            "zero_residual",
            "aipw",
            "causal",
            "semiparametric",
            "double_robustness",
            "conditional_mean_residual_zero",
            "exogeneity_moment_condition",
            "nuisance_correctness_cases",
        ),
        expected_lemmas=("integral_sub", "integrable_const", "integral_const", "measure_univ"),
    ),
    "condexp_integral_eq_integral_real": FormalObligation(
        id="condexp_integral_eq_integral_real",
        title="The integral of a real conditional expectation equals the original integral",
        english=(
            "For a real-valued random variable, the integral of its conditional "
            "expectation with respect to a sub-sigma-field equals the original "
            "integral. This is the Mathlib-backed law-of-total-expectation "
            "bridge used by iterated-expectation, exogeneity, and conditional "
            "mean arguments; it does not prove model-specific conditional "
            "exchangeability or nuisance correctness."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory
open scoped MeasureTheory

theorem condExp_integral_eq_integral_real
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    (m : MeasurableSpace Ω)
    (μ : Measure[mΩ] Ω)
    (hm : m ≤ mΩ) [SigmaFinite (μ.trim hm)]
    (X : Ω → ℝ) :
    ∫ ω, μ[X | m] ω ∂μ = ∫ ω, X ω ∂μ := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  rw [integral_condExp (m := m) (m₀ := mΩ) (μ := μ) (f := X) hm]"
        ),
        tags=(
            "expectation",
            "conditional_expectation",
            "iterated_expectation",
            "law_of_total_expectation",
            "exogeneity_moment_condition",
            "conditional_mean_residual_zero",
            "aipw",
            "causal",
            "semiparametric",
        ),
        expected_lemmas=("integral_condExp",),
    ),
    "condexp_tower_of_sub_sigma_real": FormalObligation(
        id="condexp_tower_of_sub_sigma_real",
        title="Tower property for real conditional expectations over nested sigma-fields",
        english=(
            "For nested sigma-fields m1 <= m2 <= mΩ, taking the m2-conditional "
            "expectation of a real random variable and then conditioning again "
            "on m1 is almost everywhere the same as conditioning directly on "
            "m1. This is the Mathlib-backed tower-property bridge used by "
            "iterated-expectation, filtration, martingale, and causal "
            "identification theorem skeletons; it still assumes the nested "
            "sigma-field setup rather than proving model-specific exchangeability."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory
open scoped MeasureTheory

theorem condExp_tower_of_sub_sigma_real
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    (m1 m2 : MeasurableSpace Ω)
    (μ : Measure[mΩ] Ω)
    (hm12 : m1 ≤ m2)
    (hm2 : m2 ≤ mΩ) [SigmaFinite (μ.trim hm2)]
    (X : Ω → ℝ) :
    μ[μ[X | m2] | m1] =ᵐ[μ] μ[X | m1] := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  exact condExp_condExp_of_le (μ := μ) (f := X) hm12 hm2"
        ),
        tags=(
            "expectation",
            "conditional_expectation",
            "iterated_expectation",
            "tower_property",
            "filtration",
            "martingale",
            "causal",
            "semiparametric",
            "exogeneity_moment_condition",
        ),
        expected_lemmas=("condExp_condExp_of_le",),
        depends_on=("condexp_integral_eq_integral_real",),
    ),
    "conditional_mean_residual_zero_of_condExp_ae_eq": FormalObligation(
        id="conditional_mean_residual_zero_of_condExp_ae_eq",
        title="Conditional-mean residual has zero population integral",
        english=(
            "If the conditional expectation of an integrable outcome given a "
            "score sigma-field is almost everywhere equal to a supplied "
            "score-space version, then the centered residual outcome minus "
            "that version has population integral zero. This is the direct "
            "conditional-mean residual bridge needed by AIPW orthogonality, "
            "exogeneity moment conditions, and conditional-mean identification "
            "arguments. It still assumes the conditional-expectation equality "
            "premise rather than proving nuisance correctness."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory
open scoped MeasureTheory

theorem conditionalMeanResidual_integral_zero_of_condExp_ae_eq
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    (scoreSigma : MeasurableSpace Ω)
    (μ : Measure[mΩ] Ω)
    (hsub : scoreSigma ≤ mΩ) [SigmaFinite (μ.trim hsub)]
    (outcome scoreVersion : Ω → ℝ)
    (houtcome : Integrable outcome μ)
    (hscore : Integrable scoreVersion μ)
    (hcond : μ[outcome | scoreSigma] =ᵐ[μ] scoreVersion) :
    ∫ ω, (outcome ω - scoreVersion ω) ∂μ = 0 := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  have hmean : ∫ ω, outcome ω ∂μ = ∫ ω, scoreVersion ω ∂μ := by\n"
            "    rw [← integral_condExp\n"
            "      (m := scoreSigma) (m₀ := mΩ) (μ := μ) (f := outcome)\n"
            "      hsub]\n"
            "    exact integral_congr_ae hcond\n"
            "  rw [integral_sub houtcome hscore]\n"
            "  rw [hmean]\n"
            "  simp"
        ),
        tags=(
            "estimator",
            "expectation",
            "conditional_expectation",
            "linearity",
            "residual",
            "zero_residual",
            "aipw",
            "causal",
            "semiparametric",
            "double_robustness",
            "conditional_mean_residual_zero",
            "exogeneity_moment_condition",
            "nuisance_correctness_cases",
            "orthogonal_score",
        ),
        expected_lemmas=("integral_condExp", "integral_congr_ae", "integral_sub"),
        depends_on=("condexp_integral_eq_integral_real", "conditional_mean_residual_zero_of_mean_eq"),
    ),
    "aipw_score_expectation_target_of_zero_aug": FormalObligation(
        id="aipw_score_expectation_target_of_zero_aug",
        title="AIPW score expectation equals target when augmentation terms have mean zero",
        english=(
            "If an AIPW-style contrast has expectation psi and both treated "
            "and control augmentation residual terms have expectation zero, "
            "then the full contrast + treated augmentation - control "
            "augmentation score has expectation psi. This is the finite "
            "expectation bridge used after conditional mean residual zero "
            "lemmas are available; it still does not prove those conditional "
            "expectation identities."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

noncomputable def aipwScore {Ω : Type*}
    (contrast treatAug controlAug : Ω → ℝ) : Ω → ℝ :=
  contrast + treatAug - controlAug

theorem aipwScore_expectation_eq_target_of_zero_aug {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) (contrast treatAug controlAug : Ω → ℝ) (psi : ℝ)
    (hContrast : Integrable contrast μ)
    (hTreat : Integrable treatAug μ)
    (hControl : Integrable controlAug μ)
    (hContrastMean : (∫ ω, contrast ω ∂μ) = psi)
    (hTreatZero : (∫ ω, treatAug ω ∂μ) = 0)
    (hControlZero : (∫ ω, controlAug ω ∂μ) = 0) :
    ∫ ω, aipwScore contrast treatAug controlAug ω ∂μ = psi := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  calc\n"
            "    ∫ ω, aipwScore contrast treatAug controlAug ω ∂μ =\n"
            "        ∫ ω, ((contrast + treatAug - controlAug) : Ω → ℝ) ω ∂μ := by\n"
            "          rfl\n"
            "    _ = ∫ ω, ((contrast + treatAug) : Ω → ℝ) ω ∂μ - ∫ ω, controlAug ω ∂μ := by\n"
            "          exact integral_sub (hContrast.add hTreat) hControl\n"
            "    _ = (∫ ω, contrast ω ∂μ) + (∫ ω, treatAug ω ∂μ) -\n"
            "          ∫ ω, controlAug ω ∂μ := by\n"
            "          have hAdd : ∫ ω, ((contrast + treatAug) : Ω → ℝ) ω ∂μ =\n"
            "              (∫ ω, contrast ω ∂μ) + (∫ ω, treatAug ω ∂μ) := by\n"
            "            simpa using integral_add hContrast hTreat\n"
            "          rw [hAdd]\n"
            "    _ = psi := by\n"
            "          rw [hContrastMean, hTreatZero, hControlZero]\n"
            "          ring"
        ),
        tags=(
            "estimator",
            "expectation",
            "linearity",
            "aipw",
            "causal",
            "semiparametric",
            "double_robustness",
            "conditional_mean_residual_zero",
            "zero_residual",
            "augmentation_cancel",
        ),
        expected_lemmas=("integral_add", "integral_sub", "ring"),
        depends_on=(
            "aipw_score_expectation_decompose",
            "aipw_score_expectation_target_of_aug_cancel",
            "conditional_mean_residual_zero_of_condExp_ae_eq",
            "conditional_mean_residual_zero_of_mean_eq",
        ),
    ),
    "aipw_score_integrable_of_components": FormalObligation(
        id="aipw_score_integrable_of_components",
        title="AIPW score integrability from component integrability",
        english=(
            "If the contrast, treated augmentation, and control augmentation "
            "terms are integrable, then the AIPW-style contrast + treated "
            "augmentation - control augmentation score is integrable. This is "
            "the reusable bridge for the integrability side-condition in AIPW "
            "double-robustness and asymptotic-normality theorem skeletons; it "
            "does not prove conditional-expectation residual cancellation or "
            "nuisance correctness."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

noncomputable def aipwScore {Ω : Type*}
    (contrast treatAug controlAug : Ω → ℝ) : Ω → ℝ :=
  contrast + treatAug - controlAug

theorem aipwScore_integrable_of_components {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) (contrast treatAug controlAug : Ω → ℝ)
    (hContrast : Integrable contrast μ)
    (hTreat : Integrable treatAug μ)
    (hControl : Integrable controlAug μ) :
    Integrable (aipwScore contrast treatAug controlAug) μ := by sorry
"""
        ),
        proof_body="by\n  simpa [aipwScore] using (hContrast.add hTreat).sub hControl",
        tags=(
            "estimator",
            "integrability",
            "aipw",
            "causal",
            "semiparametric",
            "double_robustness",
            "asymptotic_normality",
            "integrability_of_score_terms",
            "conditional_mean_residual_zero",
            "nuisance_correctness_cases",
        ),
        expected_lemmas=("Integrable.add", "Integrable.sub"),
        depends_on=("aipw_score_expectation_decompose",),
    ),
    "prob_measure_univ": FormalObligation(
        id="prob_measure_univ",
        title="Probability measure normalizes",
        english="A probability measure assigns mass one to the universal set.",
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory

theorem prob_measure_univ {α : Type*} [MeasurableSpace α]
    (μ : Measure α) [IsProbabilityMeasure μ] :
    μ Set.univ = 1 := by sorry
"""
        ),
        proof_body="by\n  exact measure_univ",
        tags=("probability", "measure", "normalization"),
        expected_lemmas=("measure_univ",),
    ),
    "integral_of_constant": FormalObligation(
        id="integral_of_constant",
        title="Expectation of a constant",
        english="The expected value of a constant c under a probability measure is c.",
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory

theorem integral_of_constant {α : Type*} [MeasurableSpace α]
    (μ : Measure α) [IsProbabilityMeasure μ] (c : ℝ) :
    ∫ _, c ∂μ = c := by sorry
"""
        ),
        proof_body="by\n  simp [integral_const]",
        tags=("expectation", "constant", "probability"),
        expected_lemmas=("integral_const", "measure_univ"),
    ),
    "variance_nonneg": FormalObligation(
        id="variance_nonneg",
        title="Variance is nonnegative",
        english="The variance of any real-valued random variable is nonnegative.",
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem variance_nonneg_demo {Ω : Type*} {m : MeasurableSpace Ω}
    (μ : Measure Ω) (X : Ω → ℝ) :
    0 ≤ variance X μ := by sorry
"""
        ),
        proof_body="by\n  exact variance_nonneg X μ",
        tags=("variance", "nonnegative", "estimator"),
        expected_lemmas=("variance_nonneg",),
    ),
    "variance_indep_add": FormalObligation(
        id="variance_indep_add",
        title="Variance adds under independence",
        english="For independent L2 random variables, variance of the sum is the sum of variances.",
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem variance_indep_add_demo {Ω : Type*} {m : MeasurableSpace Ω}
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (X Y : Ω → ℝ) (hX : MemLp X 2 μ) (hY : MemLp Y 2 μ)
    (h_indep : IndepFun X Y μ) :
    variance (X + Y) μ = variance X μ + variance Y μ := by sorry
"""
        ),
        proof_body="by\n  exact IndepFun.variance_add hX hY h_indep",
        tags=("variance", "independence", "estimator"),
        expected_lemmas=("IndepFun.variance_add",),
    ),
    "markov_inequality": FormalObligation(
        id="markov_inequality",
        title="Markov inequality",
        english="Markov's inequality for a measurable nonnegative ENNReal function.",
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory

theorem markov_inequality {α : Type*} [MeasurableSpace α]
    (μ : Measure α) (f : α → ENNReal) (hf : Measurable f)
    (ε : ENNReal) (hε : ε ≠ 0) (hεt : ε ≠ ⊤) :
    μ {x | ε ≤ f x} ≤ (∫⁻ x, f x ∂μ) / ε := by sorry
"""
        ),
        proof_body="by\n  exact meas_ge_le_lintegral_div hf.aemeasurable hε hεt",
        tags=("probability", "inequality", "tail_bound", "markov"),
        expected_lemmas=("meas_ge_le_lintegral_div",),
    ),
    "finite_union_bound": FormalObligation(
        id="finite_union_bound",
        title="Finite union probability bound",
        english=(
            "For any finite family of events, the measure of their union is "
            "bounded by the sum of their individual measures."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem finite_union_bound {Ω ι : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) (I : Finset ι) (A : ι → Set Ω) :
    μ (⋃ i ∈ I, A i) ≤ ∑ i ∈ I, μ (A i) := by sorry
"""
        ),
        proof_body="by\n  exact measure_biUnion_finset_le (μ := μ) I A",
        tags=("probability", "event", "union_bound", "bonferroni", "finite_sample", "multiple_testing"),
        expected_lemmas=("measure_biUnion_finset_le",),
    ),
    "finite_horizon_type1_union_control": FormalObligation(
        id="finite_horizon_type1_union_control",
        title="Finite-horizon type-I error control by union allocation",
        english=(
            "For a finite monitoring horizon, if each rejection event A_i has "
            "probability at most alpha_i, then the probability of rejecting at "
            "some monitored time is bounded by the sum of the alpha_i budgets. "
            "This is a finite-horizon sequential-testing bridge; it does not "
            "claim Ville's inequality or full anytime-valid supermartingale control."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem finiteHorizon_type1_union_control {Ω ι : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) (I : Finset ι) (A : ι → Set Ω) (α : ι → ENNReal)
    (hA : ∀ i ∈ I, μ (A i) ≤ α i) :
    μ (⋃ i ∈ I, A i) ≤ ∑ i ∈ I, α i := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  calc\n"
            "    μ (⋃ i ∈ I, A i) ≤ ∑ i ∈ I, μ (A i) := by\n"
            "      exact measure_biUnion_finset_le (μ := μ) I A\n"
            "    _ ≤ ∑ i ∈ I, α i := by\n"
            "      exact Finset.sum_le_sum (fun i hi => hA i hi)"
        ),
        tags=(
            "probability",
            "event",
            "union_bound",
            "finite_horizon",
            "type1_error",
            "optional_stopping",
            "sequential",
            "eprocess",
        ),
        expected_lemmas=("measure_biUnion_finset_le", "Finset.sum_le_sum"),
        depends_on=("finite_union_bound",),
    ),
    "finite_union_budget_control": FormalObligation(
        id="finite_union_budget_control",
        title="Finite union error control by a total budget",
        english=(
            "For a finite family of events, if each event probability is bounded "
            "by a local error budget alpha_i and the sum of those budgets is at "
            "most alpha, then the probability of at least one event is at most "
            "alpha. This is a reusable Bonferroni bridge for finite-horizon "
            "monitoring, multiple testing familywise control, and conformal "
            "failure-union arguments; it does not claim BH FDR or Ville control."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem finite_union_budget_control {Ω ι : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) (I : Finset ι) (A : ι → Set Ω)
    (α : ι → ENNReal) (α_total : ENNReal)
    (hA : ∀ i ∈ I, μ (A i) ≤ α i)
    (h_total : (∑ i ∈ I, α i) ≤ α_total) :
    μ (⋃ i ∈ I, A i) ≤ α_total := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  calc\n"
            "    μ (⋃ i ∈ I, A i) ≤ ∑ i ∈ I, μ (A i) := by\n"
            "      exact measure_biUnion_finset_le (μ := μ) I A\n"
            "    _ ≤ ∑ i ∈ I, α i := by\n"
            "      exact Finset.sum_le_sum (fun i hi => hA i hi)\n"
            "    _ ≤ α_total := h_total"
        ),
        tags=(
            "probability",
            "event",
            "union_bound",
            "bonferroni",
            "finite_sample",
            "multiple_testing",
            "familywise_error",
            "sequential",
            "conformal",
        ),
        expected_lemmas=("measure_biUnion_finset_le", "Finset.sum_le_sum"),
        depends_on=("finite_union_bound", "finite_horizon_type1_union_control"),
    ),
    "selected_bad_event_probability_le_finite_union_budget": FormalObligation(
        id="selected_bad_event_probability_le_finite_union_budget",
        title="Selected bad event is controlled by a finite union budget",
        english=(
            "If a data-dependent selector always chooses an index from a finite "
            "candidate set, then the bad event for the selected candidate is "
            "contained in the finite union of all candidate bad events. If each "
            "candidate bad event has a local error budget and those budgets sum "
            "to a total budget, then the selected bad event is controlled by "
            "the same total budget. This is a reusable post-selection bridge; "
            "it does not prove selective CLTs, bootstrap validity, or model-"
            "selection consistency."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem selectedBadEvent_probability_le_finite_union_budget {Ω ι : Type*}
    [MeasurableSpace Ω]
    (μ : Measure Ω) (I : Finset ι) (select : Ω → ι) (B : ι → Set Ω)
    (α : ι → ENNReal) (α_total : ENNReal)
    (hselect : ∀ ω, select ω ∈ I)
    (hB : ∀ i ∈ I, μ (B i) ≤ α i)
    (h_total : (∑ i ∈ I, α i) ≤ α_total) :
    μ {ω | ω ∈ B (select ω)} ≤ α_total := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  calc\n"
            "    μ {ω | ω ∈ B (select ω)} ≤ μ (⋃ i ∈ I, B i) := by\n"
            "      apply measure_mono\n"
            "      intro ω hbad\n"
            "      exact Set.mem_iUnion.mpr ⟨select ω, Set.mem_iUnion.mpr ⟨hselect ω, hbad⟩⟩\n"
            "    _ ≤ ∑ i ∈ I, μ (B i) := by\n"
            "      exact measure_biUnion_finset_le (μ := μ) I B\n"
            "    _ ≤ ∑ i ∈ I, α i := by\n"
            "      exact Finset.sum_le_sum (fun i hi => hB i hi)\n"
            "    _ ≤ α_total := h_total"
        ),
        tags=(
            "probability",
            "event",
            "union_bound",
            "bonferroni",
            "finite_sample",
            "selection",
            "post_selection",
            "adaptive_selection",
            "model_selection",
            "selected_interval",
            "familywise_error",
            "conformal",
            "multiple_testing",
        ),
        expected_lemmas=(
            "measure_mono",
            "Set.mem_iUnion",
            "measure_biUnion_finset_le",
            "Finset.sum_le_sum",
        ),
        depends_on=("finite_union_bound", "finite_union_budget_control", "event_probability_mono"),
    ),
    "selected_good_event_coverage_of_finite_union_budget": FormalObligation(
        id="selected_good_event_coverage_of_finite_union_budget",
        title="Selected good-event coverage from a finite union budget",
        english=(
            "If a data-dependent selector always chooses from a finite "
            "candidate set, each candidate bad event has a local error budget, "
            "and the budgets sum to a total budget, then the complement of the "
            "selected bad event has probability at least one minus the total "
            "budget. This is the coverage-form companion to the selected bad-"
            "event bridge for post-selection and selected-interval traces."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem selectedGoodEvent_coverage_of_finite_union_budget {Ω ι : Type*}
    [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (I : Finset ι) (select : Ω → ι) (B : ι → Set Ω)
    (α : ι → ENNReal) (α_total : ENNReal)
    (hSelectedBad : MeasurableSet {ω | ω ∈ B (select ω)})
    (hselect : ∀ ω, select ω ∈ I)
    (hB : ∀ i ∈ I, μ (B i) ≤ α i)
    (h_total : (∑ i ∈ I, α i) ≤ α_total) :
    1 - α_total ≤ μ ({ω | ω ∈ B (select ω)}ᶜ) := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  have hbad : μ {ω | ω ∈ B (select ω)} ≤ α_total := by\n"
            "    calc\n"
            "      μ {ω | ω ∈ B (select ω)} ≤ μ (⋃ i ∈ I, B i) := by\n"
            "        apply measure_mono\n"
            "        intro ω hbadω\n"
            "        exact Set.mem_iUnion.mpr ⟨select ω, Set.mem_iUnion.mpr ⟨hselect ω, hbadω⟩⟩\n"
            "      _ ≤ ∑ i ∈ I, μ (B i) := by\n"
            "        exact measure_biUnion_finset_le (μ := μ) I B\n"
            "      _ ≤ ∑ i ∈ I, α i := by\n"
            "        exact Finset.sum_le_sum (fun i hi => hB i hi)\n"
            "      _ ≤ α_total := h_total\n"
            "  have hcoverage : μ ({ω | ω ∈ B (select ω)}ᶜ) =\n"
            "      1 - μ {ω | ω ∈ B (select ω)} := by\n"
            "    exact prob_compl_eq_one_sub hSelectedBad\n"
            "  rw [hcoverage]\n"
            "  exact tsub_le_tsub_left hbad 1"
        ),
        tags=(
            "probability",
            "event",
            "coverage",
            "union_bound",
            "bonferroni",
            "finite_sample",
            "selection",
            "post_selection",
            "adaptive_selection",
            "model_selection",
            "selected_interval",
            "confidence_set",
            "conformal",
            "multiple_testing",
        ),
        expected_lemmas=(
            "measure_mono",
            "Set.mem_iUnion",
            "measure_biUnion_finset_le",
            "Finset.sum_le_sum",
            "prob_compl_eq_one_sub",
            "tsub_le_tsub_left",
        ),
        depends_on=(
            "selected_bad_event_probability_le_finite_union_budget",
            "coverage_lower_bound_of_complement_error",
            "finite_union_budget_control",
        ),
    ),
    "sequential_elimination_rule_finite_union_control": FormalObligation(
        id="sequential_elimination_rule_finite_union_control",
        title="Sequential elimination rule finite-union error control",
        english=(
            "If a sequential elimination rule data-dependently selects one "
            "candidate from a finite active set, and each candidate's bad "
            "elimination event has a local error budget, then the bad event "
            "for the selected elimination is controlled by the same finite "
            "union budget. This is a finite-sample bridge for sequential "
            "model-confidence-set traces; it is not a proof of bootstrap "
            "validity, martingale elimination validity, or a full selective "
            "inference theorem."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem sequentialEliminationRule_finite_union_control {Ω ι : Type*}
    [MeasurableSpace Ω]
    (μ : Measure Ω) (I : Finset ι) (eliminate : Ω → ι) (Bad : ι → Set Ω)
    (α : ι → ENNReal) (α_total : ENNReal)
    (hEliminate : ∀ ω, eliminate ω ∈ I)
    (hBad : ∀ i ∈ I, μ (Bad i) ≤ α i)
    (h_total : (∑ i ∈ I, α i) ≤ α_total) :
    μ {ω | ω ∈ Bad (eliminate ω)} ≤ α_total := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  calc\n"
            "    μ {ω | ω ∈ Bad (eliminate ω)} ≤ μ (⋃ i ∈ I, Bad i) := by\n"
            "      apply measure_mono\n"
            "      intro ω hbadω\n"
            "      exact Set.mem_iUnion.mpr ⟨eliminate ω, Set.mem_iUnion.mpr ⟨hEliminate ω, hbadω⟩⟩\n"
            "    _ ≤ ∑ i ∈ I, μ (Bad i) := by\n"
            "      exact measure_biUnion_finset_le (μ := μ) I Bad\n"
            "    _ ≤ ∑ i ∈ I, α i := by\n"
            "      exact Finset.sum_le_sum (fun i hi => hBad i hi)\n"
            "    _ ≤ α_total := h_total"
        ),
        tags=(
            "probability",
            "event",
            "union_bound",
            "bonferroni",
            "finite_sample",
            "sequential",
            "sequential_elimination",
            "sequential_elimination_rule",
            "elimination_rule",
            "model_confidence_set",
            "model_selection",
            "post_selection",
        ),
        expected_lemmas=(
            "measure_mono",
            "Set.mem_iUnion",
            "measure_biUnion_finset_le",
            "Finset.sum_le_sum",
        ),
        depends_on=(
            "selected_bad_event_probability_le_finite_union_budget",
            "finite_union_budget_control",
            "finite_union_bound",
        ),
    ),
    "finite_null_family_no_false_rejection_probability": FormalObligation(
        id="finite_null_family_no_false_rejection_probability",
        title="Finite null-family no-false-rejection probability",
        english=(
            "For a finite family of true-null rejection events, if every null "
            "event has a local error budget and the local budgets sum to a "
            "total budget, then the probability of making no false rejection "
            "is at least one minus the total budget. This is a reusable "
            "familywise-error bridge for multiple-testing traces; it is not a "
            "proof of the BH step-up FDR theorem."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem finiteNullFamily_noFalseRejection_probability {Ω ι : Type*}
    [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (I : Finset ι) (R : ι → Set Ω)
    (α : ι → ENNReal) (α_total : ENNReal)
    (hUnion : MeasurableSet (⋃ i ∈ I, R i))
    (hR : ∀ i ∈ I, μ (R i) ≤ α i)
    (h_total : (∑ i ∈ I, α i) ≤ α_total) :
    1 - α_total ≤ μ (⋃ i ∈ I, R i)ᶜ := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  have hbad : μ (⋃ i ∈ I, R i) ≤ α_total := by\n"
            "    calc\n"
            "      μ (⋃ i ∈ I, R i) ≤ ∑ i ∈ I, μ (R i) := by\n"
            "        exact measure_biUnion_finset_le (μ := μ) I R\n"
            "      _ ≤ ∑ i ∈ I, α i := by\n"
            "        exact Finset.sum_le_sum (fun i hi => hR i hi)\n"
            "      _ ≤ α_total := h_total\n"
            "  have hnone : μ (⋃ i ∈ I, R i)ᶜ = 1 - μ (⋃ i ∈ I, R i) := by\n"
            "    exact prob_compl_eq_one_sub hUnion\n"
            "  rw [hnone]\n"
            "  exact tsub_le_tsub_left hbad 1"
        ),
        tags=(
            "probability",
            "event",
            "union_bound",
            "bonferroni",
            "finite_sample",
            "multiple_testing",
            "familywise_error",
            "false_rejection",
            "no_false_discovery",
            "fdr",
            "pvalue",
        ),
        expected_lemmas=(
            "measure_biUnion_finset_le",
            "Finset.sum_le_sum",
            "prob_compl_eq_one_sub",
            "tsub_le_tsub_left",
        ),
        depends_on=(
            "finite_union_budget_control",
            "simultaneous_coverage_of_union_error_bound",
            "prob_compl",
        ),
    ),
    "finite_null_pvalue_no_false_rejection_probability": FormalObligation(
        id="finite_null_pvalue_no_false_rejection_probability",
        title="Finite valid-null-p-value no-false-rejection probability",
        english=(
            "For a finite family of true null p-values, if each null p-value "
            "is valid at its chosen threshold in the sense that "
            "P(p_i <= tau_i) <= tau_i, and the thresholds sum to a total "
            "budget, then the probability of making no false rejection is at "
            "least one minus that budget. This is a reusable p-value-validity "
            "bridge for multiple-testing traces; it is not a proof of BH "
            "step-up self-consistency or FDR control."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem finiteNullPValue_noFalseRejection_probability {Ω ι : Type*}
    [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (I : Finset ι) (p : ι → Ω → ENNReal)
    (τ : ι → ENNReal) (α_total : ENNReal)
    (hUnion : MeasurableSet (⋃ i ∈ I, {ω | p i ω ≤ τ i}))
    (hValid : ∀ i ∈ I, μ {ω | p i ω ≤ τ i} ≤ τ i)
    (h_total : (∑ i ∈ I, τ i) ≤ α_total) :
    1 - α_total ≤ μ (⋃ i ∈ I, {ω | p i ω ≤ τ i})ᶜ := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  have hbad : μ (⋃ i ∈ I, {ω | p i ω ≤ τ i}) ≤ α_total := by\n"
            "    calc\n"
            "      μ (⋃ i ∈ I, {ω | p i ω ≤ τ i}) ≤ ∑ i ∈ I, μ {ω | p i ω ≤ τ i} := by\n"
            "        exact measure_biUnion_finset_le (μ := μ) I (fun i => {ω | p i ω ≤ τ i})\n"
            "      _ ≤ ∑ i ∈ I, τ i := by\n"
            "        exact Finset.sum_le_sum (fun i hi => hValid i hi)\n"
            "      _ ≤ α_total := h_total\n"
            "  have hnone : μ (⋃ i ∈ I, {ω | p i ω ≤ τ i})ᶜ =\n"
            "      1 - μ (⋃ i ∈ I, {ω | p i ω ≤ τ i}) := by\n"
            "    exact prob_compl_eq_one_sub hUnion\n"
            "  rw [hnone]\n"
            "  exact tsub_le_tsub_left hbad 1"
        ),
        tags=(
            "probability",
            "event",
            "union_bound",
            "bonferroni",
            "finite_sample",
            "multiple_testing",
            "familywise_error",
            "false_rejection",
            "no_false_discovery",
            "fdr",
            "pvalue",
            "p_value",
            "valid_null_pvalue",
            "valid_null_pvalue_uniformity",
            "ordered_pvalues",
            "bh_stepup_self_consistency",
            "leave_one_out_fdr_decomposition",
        ),
        expected_lemmas=(
            "measure_biUnion_finset_le",
            "Finset.sum_le_sum",
            "prob_compl_eq_one_sub",
            "tsub_le_tsub_left",
        ),
        depends_on=(
            "finite_null_family_no_false_rejection_probability",
            "finite_union_budget_control",
            "prob_compl",
        ),
    ),
    "bh_threshold_grid_mono": FormalObligation(
        id="bh_threshold_grid_mono",
        title="BH threshold grid monotonicity",
        english=(
            "For a nonnegative nominal FDR level `q`, the deterministic "
            "Benjamini-Hochberg threshold grid `q * k / m` is monotone in the "
            "rank index `k`. This is a reusable algebraic bridge for ordered "
            "p-value and BH step-up fixed-point traces; it does not prove the "
            "BH self-consistency lemma or the FDR control theorem."
        ),
        formal_statement=_stmt(
            """
import Mathlib

noncomputable def bhThreshold (q : ℝ) (m k : Nat) : ℝ :=
  q * (k : ℝ) / (m : ℝ)

theorem bhThreshold_grid_mono {q : ℝ} {m k l : Nat}
    (hq : 0 ≤ q) (hkl : k ≤ l) :
    bhThreshold q m k ≤ bhThreshold q m l := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  unfold bhThreshold\n"
            "  gcongr"
        ),
        tags=(
            "multiple_testing",
            "fdr",
            "bh",
            "benjamini_hochberg",
            "threshold",
            "threshold_grid",
            "ordered_pvalues",
            "bh_stepup_self_consistency",
            "bh_threshold_fixed_point",
            "monotonicity",
            "finite_sample",
        ),
        expected_lemmas=("gcongr",),
        depends_on=("finite_null_pvalue_no_false_rejection_probability",),
    ),
    "finite_horizon_evalue_markov_type1_control": FormalObligation(
        id="finite_horizon_evalue_markov_type1_control",
        title="Finite-horizon e-value type-I control by Markov and union allocation",
        english=(
            "For a finite monitoring horizon, if each nonnegative ENNReal "
            "e-value-like process coordinate has a Markov tail budget and the "
            "tail budgets sum to alpha_total, then the probability that any "
            "coordinate exceeds its threshold is at most alpha_total. This is "
            "a finite-horizon bridge for e-process traces; it does not prove "
            "nonnegative-supermartingale validity, Ville's inequality, or "
            "optional-stopping anytime validity."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory
open scoped ENNReal

theorem finiteHorizonEValue_markov_type1_control {Ω ι : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) (I : Finset ι) (E : ι → Ω → ENNReal)
    (u α : ι → ENNReal) (α_total : ENNReal)
    (hE : ∀ i ∈ I, Measurable (E i))
    (hu0 : ∀ i ∈ I, u i ≠ 0) (hutop : ∀ i ∈ I, u i ≠ ⊤)
    (hBudget : ∀ i ∈ I, (∫⁻ ω, E i ω ∂μ) / u i ≤ α i)
    (hTotal : (∑ i ∈ I, α i) ≤ α_total) :
    μ (⋃ i ∈ I, {ω | u i ≤ E i ω}) ≤ α_total := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  calc\n"
            "    μ (⋃ i ∈ I, {ω | u i ≤ E i ω})\n"
            "        ≤ ∑ i ∈ I, μ {ω | u i ≤ E i ω} := by\n"
            "          exact measure_biUnion_finset_le (μ := μ) I (fun i => {ω | u i ≤ E i ω})\n"
            "    _ ≤ ∑ i ∈ I, α i := by\n"
            "          exact Finset.sum_le_sum (fun i hi =>\n"
            "            le_trans\n"
            "              (meas_ge_le_lintegral_div (hE i hi).aemeasurable (hu0 i hi) (hutop i hi))\n"
            "              (hBudget i hi))\n"
            "    _ ≤ α_total := hTotal"
        ),
        tags=(
            "probability",
            "event",
            "markov",
            "tail_bound",
            "union_bound",
            "finite_horizon",
            "type1_error",
            "sequential",
            "evalue",
            "eprocess",
            "eprocess_type1_control",
            "nonnegative_supermartingale",
            "ville_inequality",
            "optional_stopping",
        ),
        expected_lemmas=("measure_biUnion_finset_le", "meas_ge_le_lintegral_div", "Finset.sum_le_sum"),
        depends_on=("markov_inequality", "finite_union_bound", "finite_union_budget_control"),
    ),
    "filtration_mono_measurable_set": FormalObligation(
        id="filtration_mono_measurable_set",
        title="Filtration monotonicity preserves measurability",
        english=(
            "If an event is measurable with respect to an earlier sigma-algebra "
            "in a filtration, then it remains measurable with respect to any "
            "later sigma-algebra. This is a reusable structural bridge for "
            "sequential inference, adapted processes, stopping times, and "
            "finite-horizon reductions of optional-stopping arguments; it does "
            "not prove Ville's inequality or optional-stopping validity."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory

theorem filtration_mono_measurableSet {Ω ι : Type*} {m : MeasurableSpace Ω}
    [Preorder ι] (ℱ : Filtration ι m) {i j : ι} (hij : i ≤ j)
    {A : Set Ω} (hA : MeasurableSet[ℱ i] A) :
    MeasurableSet[ℱ j] A := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  exact (ℱ.mono hij) A hA"
        ),
        tags=(
            "probability",
            "process",
            "filtration",
            "measurability",
            "monotonicity",
            "adapted",
            "stopping_time",
            "sequential",
            "eprocess",
            "optional_stopping",
            "ville_inequality",
        ),
        expected_lemmas=("Filtration.mono",),
    ),
    "stopping_time_le_event_measurable": FormalObligation(
        id="stopping_time_le_event_measurable",
        title="Stopping-time lower event is filtration-measurable",
        english=(
            "If tau is a stopping time with respect to a filtration, then at "
            "each deterministic time i the event {tau <= i} is measurable with "
            "respect to the sigma-algebra at time i. This is the defining "
            "measurability bridge used by optional-stopping, stopped-process, "
            "and anytime-valid inference proofs; it does not prove optional "
            "stopping or Ville's inequality."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory

theorem stoppingTime_le_event_measurable {Ω ι : Type*} {m : MeasurableSpace Ω}
    [Preorder ι] (ℱ : Filtration ι m) {τ : Ω → WithTop ι}
    (hτ : IsStoppingTime ℱ τ) (i : ι) :
    MeasurableSet[ℱ i] {ω | τ ω ≤ i} := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  exact hτ.measurableSet_le i"
        ),
        tags=(
            "probability",
            "process",
            "filtration",
            "measurability",
            "stopping_time",
            "stopped_process",
            "adapted",
            "sequential",
            "eprocess",
            "optional_stopping",
            "ville_inequality",
        ),
        expected_lemmas=("IsStoppingTime.measurableSet_le",),
        depends_on=("filtration_mono_measurable_set",),
    ),
    "submartingale_expected_stopped_value_mono": FormalObligation(
        id="submartingale_expected_stopped_value_mono",
        title="Optional stopping expectation monotonicity for bounded stopping times",
        english=(
            "For a submartingale and two bounded stopping times tau <= pi, "
            "the expected stopped value at tau is at most the expected stopped "
            "value at pi. This is a direct Mathlib optional-stopping bridge for "
            "sequential inference and stopped-process theorem skeletons; it "
            "still does not prove e-process validity or Ville's inequality."
        ),
        formal_statement=_stmt(
            """
import Mathlib

open scoped NNReal ENNReal MeasureTheory ProbabilityTheory
open MeasureTheory

theorem submartingale_expected_stoppedValue_mono_bridge {Ω E : Type*}
    {m0 : MeasurableSpace Ω} {μ : Measure Ω} {𝒢 : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E] [PartialOrder E]
    [IsOrderedAddMonoid E] [IsOrderedModule ℝ E] [ClosedIciTopology E]
    [SigmaFiniteFiltration μ 𝒢] {f : ℕ → Ω → E} {τ π : Ω → ℕ∞}
    (hf : Submartingale f 𝒢 μ) (hτ : IsStoppingTime 𝒢 τ) (hπ : IsStoppingTime 𝒢 π)
    (hle : τ ≤ π) {N : ℕ} (hbdd : ∀ ω, π ω ≤ N) :
    μ[stoppedValue f τ] ≤ μ[stoppedValue f π] := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  exact hf.expected_stoppedValue_mono hτ hπ hle hbdd"
        ),
        tags=(
            "probability",
            "martingale",
            "submartingale",
            "process",
            "filtration",
            "stopping_time",
            "stopped_process",
            "stopped_value",
            "optional_stopping",
            "sequential",
            "anytime",
            "eprocess",
            "nonnegative_supermartingale",
            "ville_inequality",
        ),
        expected_lemmas=("Submartingale.expected_stoppedValue_mono",),
        depends_on=("stopping_time_le_event_measurable",),
    ),
    "submartingale_stopped_process": FormalObligation(
        id="submartingale_stopped_process",
        title="Stopped process of a submartingale is a submartingale",
        english=(
            "Stopping a real-valued submartingale at a stopping time preserves "
            "the submartingale property. This is a reusable Mathlib bridge for "
            "stopped-process and optional-stopping theorem skeletons, and a "
            "concrete step toward nonnegative-supermartingale/e-process "
            "formalization. It does not construct an e-process or prove Ville's "
            "inequality."
        ),
        formal_statement=_stmt(
            """
import Mathlib

open scoped NNReal ENNReal MeasureTheory ProbabilityTheory
open MeasureTheory

theorem submartingale_stoppedProcess_bridge {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {𝒢 : Filtration ℕ m0} {f : ℕ → Ω → ℝ} {τ : Ω → ℕ∞}
    [SigmaFiniteFiltration μ 𝒢] (hf : Submartingale f 𝒢 μ) (hτ : IsStoppingTime 𝒢 τ) :
    Submartingale (stoppedProcess f τ) 𝒢 μ := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  exact hf.stoppedProcess hτ"
        ),
        tags=(
            "probability",
            "martingale",
            "submartingale",
            "process",
            "filtration",
            "stopping_time",
            "stopped_process",
            "optional_stopping",
            "sequential",
            "anytime",
            "eprocess",
            "nonnegative_supermartingale",
            "ville_inequality",
        ),
        expected_lemmas=("Submartingale.stoppedProcess",),
        depends_on=("submartingale_expected_stopped_value_mono",),
    ),
    "supermartingale_expected_stopped_value_antimono": FormalObligation(
        id="supermartingale_expected_stopped_value_antimono",
        title="Optional stopping expectation monotonicity for supermartingales",
        english=(
            "For bounded stopping times τ ≤ π, the stopped value of a real-valued "
            "supermartingale has decreasing expectation: E[f_π] ≤ E[f_τ]. "
            "This is the supermartingale counterpart of the existing optional-"
            "stopping submartingale bridge and is the expectation budget theorem "
            "needed for e-process/Ville type-I control skeletons."
        ),
        formal_statement=_stmt(
            """
import Mathlib

open scoped NNReal ENNReal MeasureTheory ProbabilityTheory
open MeasureTheory

theorem supermartingale_expected_stoppedValue_antimono_bridge {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {𝒢 : Filtration ℕ m0} {f : ℕ → Ω → ℝ} {τ π : Ω → ℕ∞}
    [SigmaFiniteFiltration μ 𝒢] (hf : Supermartingale f 𝒢 μ)
    (hτ : IsStoppingTime 𝒢 τ) (hπ : IsStoppingTime 𝒢 π) (hle : τ ≤ π)
    {N : ℕ} (hbdd : ∀ ω, π ω ≤ N) : μ[stoppedValue f π] ≤ μ[stoppedValue f τ] := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  rw [← sub_nonpos, ← integral_sub', stoppedValue_sub_eq_sum' hle hbdd]\n"
            "  · simp only [Finset.sum_apply]\n"
            "    have : ∀ i, MeasurableSet[𝒢 i] {ω : Ω | τ ω ≤ i ∧ i < π ω} := by\n"
            "      intro i\n"
            "      refine (hτ i).inter ?_\n"
            "      convert (hπ i).compl using 1\n"
            "      ext x\n"
            "      simp\n"
            "      rfl\n"
            "    rw [integral_finset_sum]\n"
            "    · refine Finset.sum_nonpos fun i _ => ?_\n"
            "      rw [integral_indicator (𝒢.le _ _ (this _)), integral_sub', sub_nonpos]\n"
            "      · exact hf.setIntegral_le (Nat.le_succ i) (this _)\n"
            "      · exact (hf.integrable _).integrableOn\n"
            "      · exact (hf.integrable _).integrableOn\n"
            "    intro i _\n"
            "    exact Integrable.indicator (Integrable.sub (hf.integrable _) (hf.integrable _))\n"
            "      (𝒢.le _ _ (this _))\n"
            "  · exact integrable_stoppedValue ℕ hπ hf.integrable hbdd\n"
            "  · exact integrable_stoppedValue ℕ hτ hf.integrable fun ω => le_trans (hle ω) (hbdd ω)"
        ),
        tags=(
            "probability",
            "martingale",
            "supermartingale",
            "optional_stopping",
            "stopping_time",
            "stopped_value",
            "expectation_budget",
            "filtration",
            "sequential",
            "anytime",
            "eprocess",
            "eprocess_type1_control",
            "nonnegative_supermartingale",
            "ville_inequality",
        ),
        expected_lemmas=(
            "Supermartingale.setIntegral_le",
            "stoppedValue_sub_eq_sum'",
            "integrable_stoppedValue",
            "integral_finset_sum",
        ),
        depends_on=("submartingale_expected_stopped_value_mono",),
    ),
    "submartingale_doob_maximal_ineq": FormalObligation(
        id="submartingale_doob_maximal_ineq",
        title="Doob maximal inequality for nonnegative submartingales",
        english=(
            "Doob's finite-horizon maximal inequality bounds the probability "
            "mass of the running maximum event of a nonnegative real-valued "
            "submartingale by the terminal integral over that event. This is "
            "a direct Mathlib bridge toward Ville/e-process theorem skeletons; "
            "it still does not construct an e-process or prove full anytime "
            "type-I error control."
        ),
        formal_statement=_stmt(
            """
import Mathlib

open scoped NNReal ENNReal MeasureTheory ProbabilityTheory
open MeasureTheory
open Finset

theorem submartingale_doob_maximal_ineq_bridge {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {𝒢 : Filtration ℕ m0} {f : ℕ → Ω → ℝ}
    [IsFiniteMeasure μ] (hsub : Submartingale f 𝒢 μ) (hnonneg : 0 ≤ f)
    {ε : ℝ≥0} (n : ℕ) :
    ε * μ {ω | (ε : ℝ) ≤ (range (n + 1)).sup' nonempty_range_add_one fun k => f k ω} ≤
    ENNReal.ofReal
      (∫ ω in {ω | (ε : ℝ) ≤ (range (n + 1)).sup' nonempty_range_add_one fun k => f k ω},
        f n ω ∂μ) := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  exact maximal_ineq hsub hnonneg n"
        ),
        tags=(
            "probability",
            "martingale",
            "submartingale",
            "maximal_inequality",
            "doob",
            "tail_bound",
            "process",
            "filtration",
            "stopping_time",
            "stopped_process",
            "optional_stopping",
            "sequential",
            "anytime",
            "eprocess",
            "eprocess_type1_control",
            "nonnegative_supermartingale",
            "ville_inequality",
        ),
        expected_lemmas=("maximal_ineq",),
        depends_on=("submartingale_stopped_process", "submartingale_expected_stopped_value_mono"),
    ),
    "submartingale_doob_maximal_budget": FormalObligation(
        id="submartingale_doob_maximal_budget",
        title="Budgeted Doob maximal inequality for nonnegative submartingales",
        english=(
            "If the terminal integral over the Doob running-maximum event is "
            "bounded by a threshold times an error budget, then the same budget "
            "bounds the threshold-weighted event probability. This is the "
            "finite-horizon maximal-tail budget bridge closest to Ville-style "
            "type-I control, while still leaving the e-process construction and "
            "division/cancellation step as explicit formal gaps."
        ),
        formal_statement=_stmt(
            """
import Mathlib

open scoped NNReal ENNReal MeasureTheory ProbabilityTheory
open MeasureTheory
open Finset

theorem submartingale_doob_maximal_budget_bridge {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {𝒢 : Filtration ℕ m0} {f : ℕ → Ω → ℝ}
    [IsFiniteMeasure μ] (hsub : Submartingale f 𝒢 μ) (hnonneg : 0 ≤ f)
    {ε : ℝ≥0} {α : ℝ≥0∞} (n : ℕ)
    (hbudget :
      ENNReal.ofReal
        (∫ ω in {ω | (ε : ℝ) ≤ (range (n + 1)).sup' nonempty_range_add_one fun k => f k ω},
          f n ω ∂μ) ≤ ε * α) :
    ε * μ {ω | (ε : ℝ) ≤ (range (n + 1)).sup' nonempty_range_add_one fun k => f k ω} ≤
      ε * α := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  exact le_trans (maximal_ineq hsub hnonneg n) hbudget"
        ),
        tags=(
            "probability",
            "martingale",
            "submartingale",
            "maximal_inequality",
            "doob",
            "tail_bound",
            "budget",
            "process",
            "filtration",
            "stopping_time",
            "optional_stopping",
            "sequential",
            "anytime",
            "eprocess",
            "eprocess_type1_control",
            "nonnegative_supermartingale",
            "ville_inequality",
        ),
        expected_lemmas=("maximal_ineq", "le_trans"),
        depends_on=("submartingale_doob_maximal_ineq",),
    ),
    "submartingale_doob_maximal_probability_bound": FormalObligation(
        id="submartingale_doob_maximal_probability_bound",
        title="Doob maximal probability bound from a terminal budget",
        english=(
            "If the terminal integral over the Doob running-maximum event is "
            "bounded by a nonzero threshold times an error budget, then the "
            "running-maximum event probability itself is bounded by that "
            "budget. This composes Mathlib's finite-horizon maximal inequality "
            "with ENNReal cancellation, closing the algebraic division step in "
            "the Ville/e-process theorem skeleton while still leaving the "
            "e-process construction and terminal-budget proof as explicit "
            "formal gaps."
        ),
        formal_statement=_stmt(
            """
import Mathlib

open scoped NNReal ENNReal MeasureTheory ProbabilityTheory
open MeasureTheory
open Finset

theorem submartingale_doob_maximal_probability_bound_bridge {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {𝒢 : Filtration ℕ m0} {f : ℕ → Ω → ℝ}
    [IsFiniteMeasure μ] (hsub : Submartingale f 𝒢 μ) (hnonneg : 0 ≤ f)
    {ε : ℝ≥0} {α : ℝ≥0∞} (hε : ε ≠ 0) (n : ℕ)
    (hbudget :
      ENNReal.ofReal
        (∫ ω in {ω | (ε : ℝ) ≤ (range (n + 1)).sup' nonempty_range_add_one fun k => f k ω},
          f n ω ∂μ) ≤ ε * α) :
    μ {ω | (ε : ℝ) ≤ (range (n + 1)).sup' nonempty_range_add_one fun k => f k ω} ≤ α := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  have hmul :\n"
            "      ε * μ {ω | (ε : ℝ) ≤ (range (n + 1)).sup' nonempty_range_add_one fun k => f k ω} ≤\n"
            "        ε * α := by\n"
            "    exact le_trans (maximal_ineq hsub hnonneg n) hbudget\n"
            "  have hε0 : (ε : ℝ≥0∞) ≠ 0 := by\n"
            "    exact_mod_cast hε\n"
            "  exact (ENNReal.mul_le_mul_iff_right hε0 ENNReal.coe_ne_top).mp hmul"
        ),
        tags=(
            "probability",
            "martingale",
            "submartingale",
            "maximal_inequality",
            "doob",
            "tail_bound",
            "budget",
            "probability_bound",
            "ennreal",
            "cancellation",
            "process",
            "filtration",
            "stopping_time",
            "optional_stopping",
            "sequential",
            "anytime",
            "eprocess",
            "eprocess_type1_control",
            "nonnegative_supermartingale",
            "ville_inequality",
        ),
        expected_lemmas=("maximal_ineq", "le_trans", "ENNReal.mul_le_mul_iff_right"),
        depends_on=("submartingale_doob_maximal_budget",),
    ),
    "submartingale_ae_tendsto_limit_process": FormalObligation(
        id="submartingale_ae_tendsto_limit_process",
        title="Almost-everywhere convergence of an L1-bounded submartingale",
        english=(
            "An L1-bounded real-valued submartingale converges almost "
            "everywhere to Mathlib's filtration limit process. This wraps "
            "Mathlib's martingale convergence theorem and gives survival, "
            "Nelson-Aalen/Kaplan-Meier, backward-martingale, and sequential "
            "theorem skeletons a real convergence bridge. It is still not a "
            "martingale CLT or a product-limit delta-method proof."
        ),
        formal_statement=_stmt(
            """
import Mathlib

open TopologicalSpace Filter MeasureTheory.Filtration
open scoped NNReal ENNReal MeasureTheory ProbabilityTheory Topology
open MeasureTheory

theorem submartingale_ae_tendsto_limitProcess_bridge {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {𝒢 : Filtration ℕ m0} {f : ℕ → Ω → ℝ} {R : ℝ≥0}
    [IsFiniteMeasure μ] [SigmaFiniteFiltration μ 𝒢]
    (hf : Submartingale f 𝒢 μ)
    (hbdd : ∀ n, eLpNorm (f n) 1 μ ≤ R) :
    ∀ᵐ ω ∂μ, Tendsto (fun n => f n ω) atTop (𝓝 (𝒢.limitProcess f μ ω)) := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  exact hf.ae_tendsto_limitProcess hbdd"
        ),
        tags=(
            "probability",
            "martingale",
            "submartingale",
            "convergence",
            "almost_everywhere",
            "limit_process",
            "filtration",
            "survival",
            "kaplan_meier",
            "nelson_aalen",
            "survival_martingale_clt",
            "backward_martingale",
            "sequential",
            "anytime",
        ),
        expected_lemmas=("Submartingale.ae_tendsto_limitProcess",),
        depends_on=("submartingale_expected_stopped_value_mono",),
    ),
    "submartingale_l1_tendsto_limit_process": FormalObligation(
        id="submartingale_l1_tendsto_limit_process",
        title="L1 convergence of a uniformly integrable submartingale to its limit process",
        english=(
            "A uniformly integrable real-valued submartingale converges in L1 "
            "to Mathlib's filtration limit process. This wraps the L1 "
            "martingale convergence theorem and strengthens the survival/"
            "Kaplan-Meier and Nelson-Aalen roadmap from almost-everywhere "
            "convergence to an eLpNorm convergence bridge. It is still not a "
            "martingale CLT, Greenwood variance consistency, or a product-limit "
            "delta-method proof."
        ),
        formal_statement=_stmt(
            """
import Mathlib

open TopologicalSpace Filter MeasureTheory.Filtration
open scoped NNReal ENNReal MeasureTheory ProbabilityTheory Topology
open MeasureTheory

theorem submartingale_tendsto_eLpNorm_one_limitProcess_bridge {Ω : Type*}
    {m0 : MeasurableSpace Ω} {μ : Measure Ω} {𝒢 : Filtration ℕ m0}
    {f : ℕ → Ω → ℝ} [IsFiniteMeasure μ] [SigmaFiniteFiltration μ 𝒢]
    (hf : Submartingale f 𝒢 μ)
    (hunif : UniformIntegrable f 1 μ) :
    Tendsto (fun n => eLpNorm (f n - 𝒢.limitProcess f μ) 1 μ) atTop (𝓝 0) := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  exact hf.tendsto_eLpNorm_one_limitProcess hunif"
        ),
        tags=(
            "probability",
            "martingale",
            "submartingale",
            "convergence",
            "l1_convergence",
            "uniform_integrability",
            "limit_process",
            "filtration",
            "survival",
            "kaplan_meier",
            "nelson_aalen",
            "survival_martingale_clt",
            "greenwood_variance_consistency",
            "backward_martingale",
            "sequential",
            "anytime",
        ),
        expected_lemmas=("Submartingale.tendsto_eLpNorm_one_limitProcess",),
        depends_on=("submartingale_ae_tendsto_limit_process",),
    ),
    "martingale_ae_eq_condexp_limit_process": FormalObligation(
        id="martingale_ae_eq_condexp_limit_process",
        title="Martingale values are conditional expectations of the limit process",
        english=(
            "A uniformly integrable real-valued martingale is almost everywhere "
            "equal at each time n to the conditional expectation of its "
            "filtration limit process given the nth sigma-field. This wraps "
            "the representation part of Mathlib's L1 martingale convergence "
            "theorem, giving martingale-definition and survival-theory "
            "roadmaps a direct conditional-expectation bridge. It is still not "
            "a martingale CLT, Greenwood variance consistency, or a "
            "product-limit delta-method proof."
        ),
        formal_statement=_stmt(
            """
import Mathlib

open TopologicalSpace Filter MeasureTheory.Filtration
open scoped NNReal ENNReal MeasureTheory ProbabilityTheory Topology
open MeasureTheory

theorem martingale_ae_eq_condExp_limitProcess_bridge {Ω : Type*}
    {m0 : MeasurableSpace Ω} {μ : Measure Ω} {𝒢 : Filtration ℕ m0}
    {f : ℕ → Ω → ℝ} [IsFiniteMeasure μ] [SigmaFiniteFiltration μ 𝒢]
    (hf : Martingale f 𝒢 μ) (hunif : UniformIntegrable f 1 μ) (n : ℕ) :
    f n =ᵐ[μ] μ[𝒢.limitProcess f μ | 𝒢 n] := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  exact hf.ae_eq_condExp_limitProcess hunif n"
        ),
        tags=(
            "probability",
            "martingale",
            "convergence",
            "conditional_expectation",
            "l1_convergence",
            "uniform_integrability",
            "limit_process",
            "filtration",
            "survival",
            "kaplan_meier",
            "nelson_aalen",
            "survival_martingale_clt",
            "greenwood_variance_consistency",
            "conditional_expectation_product_step",
            "martingale_definition",
        ),
        expected_lemmas=("Martingale.ae_eq_condExp_limitProcess",),
        depends_on=("submartingale_l1_tendsto_limit_process",),
    ),
    "integrable_ae_tendsto_condexp_filtration": FormalObligation(
        id="integrable_ae_tendsto_condexp_filtration",
        title="Conditional expectations along a filtration converge almost everywhere",
        english=(
            "For an integrable real function measurable with respect to the "
            "terminal sigma-field of a filtration, the conditional expectations "
            "given the finite filtration levels converge almost everywhere to "
            "the function. This wraps Mathlib's upward martingale convergence "
            "theorem for conditional expectations, giving iterated-expectation, "
            "exogeneity, and martingale-definition roadmaps a direct "
            "conditional-expectation convergence bridge."
        ),
        formal_statement=_stmt(
            """
import Mathlib

open TopologicalSpace Filter MeasureTheory.Filtration
open scoped NNReal ENNReal MeasureTheory ProbabilityTheory Topology
open MeasureTheory

theorem integrable_tendsto_ae_condExp_filtration_bridge {Ω : Type*}
    {m0 : MeasurableSpace Ω} {μ : Measure Ω} {𝒢 : Filtration ℕ m0}
    {g : Ω → ℝ} [IsFiniteMeasure μ] [SigmaFiniteFiltration μ 𝒢]
    (hg : Integrable g μ) (hgmeas : StronglyMeasurable[⨆ n, 𝒢 n] g) :
    ∀ᵐ x ∂μ, Tendsto (fun n => (μ[g | 𝒢 n]) x) atTop (𝓝 (g x)) := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  exact hg.tendsto_ae_condExp hgmeas"
        ),
        tags=(
            "probability",
            "martingale",
            "conditional_expectation",
            "almost_everywhere_convergence",
            "filtration",
            "upward_theorem",
            "integrable",
            "iterated_expectation",
            "exogeneity_moment_condition",
            "martingale_definition",
        ),
        expected_lemmas=("Integrable.tendsto_ae_condExp",),
        depends_on=("martingale_ae_eq_condexp_limit_process",),
    ),
    "integrable_l1_tendsto_condexp_filtration": FormalObligation(
        id="integrable_l1_tendsto_condexp_filtration",
        title="Conditional expectations along a filtration converge in L1",
        english=(
            "For an integrable real function measurable with respect to the "
            "terminal sigma-field of a filtration, the conditional expectations "
            "given finite filtration levels converge in L1 to the function. "
            "This wraps Mathlib's L1 upward martingale convergence theorem and "
            "is a reusable bridge for conditional-expectation, exogeneity, "
            "martingale-definition, and iterative-theory formalization targets."
        ),
        formal_statement=_stmt(
            """
import Mathlib

open TopologicalSpace Filter MeasureTheory.Filtration
open scoped NNReal ENNReal MeasureTheory ProbabilityTheory Topology
open MeasureTheory

theorem integrable_tendsto_eLpNorm_condExp_filtration_bridge {Ω : Type*}
    {m0 : MeasurableSpace Ω} {μ : Measure Ω} {𝒢 : Filtration ℕ m0}
    {g : Ω → ℝ} [IsFiniteMeasure μ] [SigmaFiniteFiltration μ 𝒢]
    (hg : Integrable g μ) (hgmeas : StronglyMeasurable[⨆ n, 𝒢 n] g) :
    Tendsto (fun n => eLpNorm (μ[g | 𝒢 n] - g) 1 μ) atTop (𝓝 0) := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  exact hg.tendsto_eLpNorm_condExp hgmeas"
        ),
        tags=(
            "probability",
            "martingale",
            "conditional_expectation",
            "l1_convergence",
            "filtration",
            "upward_theorem",
            "integrable",
            "iterated_expectation",
            "exogeneity_moment_condition",
            "martingale_definition",
        ),
        expected_lemmas=("Integrable.tendsto_eLpNorm_condExp",),
        depends_on=("integrable_ae_tendsto_condexp_filtration",),
    ),
    "event_probability_mono": FormalObligation(
        id="event_probability_mono",
        title="Event probability monotonicity",
        english="If event A is a subset of event B, then μ(A) ≤ μ(B).",
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem event_probability_mono {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) {A B : Set Ω} (hAB : A ⊆ B) :
    μ A ≤ μ B := by sorry
"""
        ),
        proof_body="by\n  exact measure_mono hAB",
        tags=("probability", "event", "monotonicity", "measure", "subset"),
        expected_lemmas=("measure_mono",),
    ),
    "independent_event_inter_probability": FormalObligation(
        id="independent_event_inter_probability",
        title="Independent event intersection probability",
        english=(
            "If two events are independent, then the probability of their "
            "intersection equals the product of their probabilities."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem independent_event_inter_probability {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) {A B : Set Ω} (h_indep : IndepSet A B μ) :
    μ (A ∩ B) = μ A * μ B := by sorry
"""
        ),
        proof_body="by\n  exact IndepSet.measure_inter_eq_mul h_indep",
        tags=("probability", "event", "independence", "intersection", "multiple_testing"),
        expected_lemmas=("IndepSet.measure_inter_eq_mul",),
    ),
    "independent_null_event_family_inter_probability": FormalObligation(
        id="independent_null_event_family_inter_probability",
        title="Finite independent null-event intersection probability",
        english=(
            "For a finite family of independent null events, the probability of "
            "their joint occurrence factors as the product of the individual "
            "probabilities. This is a reusable finite-family bridge for "
            "multiple-testing and BH/FDR proofs that need product-form null "
            "event probabilities; it does not prove p-value validity, ordering, "
            "or the BH step-up theorem."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem independentFiniteEventInter_probability {Ω ι : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) (A : ι → Set Ω) (I : Finset ι)
    (h_indep : iIndepSet A μ) :
    μ (⋂ i ∈ I, A i) = ∏ i ∈ I, μ (A i) := by sorry
"""
        ),
        proof_body="by\n  exact iIndepSet.meas_biInter h_indep I",
        tags=(
            "probability",
            "event",
            "independence",
            "intersection",
            "finite_family",
            "multiple_testing",
            "fdr",
            "bh",
            "null_pvalues",
            "pvalue",
        ),
        expected_lemmas=("iIndepSet.meas_biInter",),
        depends_on=("independent_event_inter_probability",),
    ),
    "independent_null_event_family_compl_inter_probability": FormalObligation(
        id="independent_null_event_family_compl_inter_probability",
        title="Finite independent null-event complement-intersection probability",
        english=(
            "For a finite family of independent null events, the probability "
            "that none of the events occur factors as the product of their "
            "complement probabilities. This is a reusable bridge for BH/FDR, "
            "familywise-error, and no-false-discovery decompositions; it does "
            "not prove null p-value validity, ordering, or the BH step-up theorem."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

theorem independentFiniteEventComplInter_probability {Ω ι : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) (A : ι → Set Ω) (I : Finset ι)
    (h_indep : iIndepSet A μ) :
    μ (⋂ i ∈ I, (A i)ᶜ) = ∏ i ∈ I, μ (A i)ᶜ := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  exact (iIndepSet_iff A μ).1 h_indep I (f := fun i => (A i)ᶜ) (by\n"
            "    intro i hi\n"
            "    exact (MeasurableSpace.measurableSet_generateFrom\n"
            "      (by simp : A i ∈ ({A i} : Set (Set Ω)))).compl)"
        ),
        tags=(
            "probability",
            "event",
            "independence",
            "complement",
            "intersection",
            "finite_family",
            "multiple_testing",
            "familywise_error",
            "fdr",
            "bh",
            "null_pvalues",
            "pvalue",
        ),
        expected_lemmas=("iIndepSet_iff", "MeasurableSpace.measurableSet_generateFrom"),
        depends_on=("independent_null_event_family_inter_probability", "prob_compl"),
    ),
    "first_borel_cantelli_limsup_zero": FormalObligation(
        id="first_borel_cantelli_limsup_zero",
        title="First Borel-Cantelli limsup event bound",
        english=(
            "If the sum of probabilities of a sequence of bad events is finite, "
            "then the probability that infinitely many of them occur is zero."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory Filter
open scoped ENNReal Topology

theorem first_borel_cantelli_limsup_zero {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) (A : ℕ → Set Ω) (h_sum : (∑' n, μ (A n)) ≠ ∞) :
    μ (limsup A atTop) = 0 := by sorry
"""
        ),
        proof_body="by\n  exact MeasureTheory.measure_limsup_atTop_eq_zero h_sum",
        tags=("probability", "event", "borel_cantelli", "limsup", "tail_bound", "sequential"),
        expected_lemmas=("MeasureTheory.measure_limsup_atTop_eq_zero",),
    ),
    "second_borel_cantelli_limsup_one": FormalObligation(
        id="second_borel_cantelli_limsup_one",
        title="Second Borel-Cantelli independent-event recurrence",
        english=(
            "For independent measurable events whose probabilities have "
            "divergent sum, the probability that infinitely many occur is one."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory Filter
open scoped ENNReal Topology

theorem second_borel_cantelli_limsup_one {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) (A : ℕ → Set Ω)
    (hA : ∀ n, MeasurableSet (A n)) (h_indep : iIndepSet A μ)
    (h_sum : (∑' n, μ (A n)) = ∞) :
    μ (limsup A atTop) = 1 := by sorry
"""
        ),
        proof_body="by\n  exact ProbabilityTheory.measure_limsup_eq_one hA h_indep h_sum",
        tags=("probability", "event", "borel_cantelli", "limsup", "independence", "recurrence"),
        expected_lemmas=("ProbabilityTheory.measure_limsup_eq_one",),
    ),
    "adapted_hitting_after_is_stopping_time": FormalObligation(
        id="adapted_hitting_after_is_stopping_time",
        title="Adapted hitting time is a stopping time",
        english=(
            "For a discrete adapted process, the first hitting time after a "
            "fixed start time of a measurable set is a stopping time."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory

theorem adapted_hitting_after_is_stopping_time {Ω β : Type*} {m : MeasurableSpace Ω}
    [MeasurableSpace β] (ℱ : Filtration ℕ m) (X : ℕ → Ω → β)
    (hX : Adapted ℱ X) (S : Set β) (hS : MeasurableSet S) (n : ℕ) :
    IsStoppingTime ℱ (hittingAfter X S n) := by sorry
"""
        ),
        proof_body="by\n  exact hX.isStoppingTime_hittingAfter hS",
        tags=("probability", "process", "stopping_time", "adapted", "sequential"),
        expected_lemmas=("Adapted.isStoppingTime_hittingAfter",),
    ),
    "prob_compl": FormalObligation(
        id="prob_compl",
        title="Probability of complement",
        english="For a probability measure and measurable event A, μ(Aᶜ) = 1 - μ(A).",
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory

theorem prob_compl_demo {Ω : Type*} {m : MeasurableSpace Ω}
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (A : Set Ω) (hA : MeasurableSet A) :
    μ Aᶜ = 1 - μ A := by sorry
"""
        ),
        proof_body="by\n  exact prob_compl_eq_one_sub hA",
        tags=("probability", "event", "complement"),
        expected_lemmas=("prob_compl_eq_one_sub",),
    ),
}


def all_obligations() -> list[FormalObligation]:
    return list(FORMAL_OBLIGATIONS.values())


def proof_bank_fingerprint() -> str:
    return stable_hash(
        [
            {
                "id": obligation.id,
                "title": obligation.title,
                "english": obligation.english,
                "formal_statement": obligation.formal_statement,
                "proof_body": obligation.proof_body,
                "tags": obligation.tags,
                "expected_lemmas": obligation.expected_lemmas,
                "source": obligation.source,
                "depends_on": obligation.depends_on,
            }
            for obligation in sorted(all_obligations(), key=lambda row: row.id)
        ]
    )


def get_obligation(obligation_id: str) -> FormalObligation:
    try:
        return FORMAL_OBLIGATIONS[obligation_id]
    except KeyError as exc:
        raise KeyError(f"unknown formal obligation: {obligation_id}") from exc


def obligations_by_tags(tags: set[str], *, require_all: bool = False) -> list[FormalObligation]:
    if not tags:
        return all_obligations()
    if require_all:
        return [o for o in all_obligations() if tags.issubset(set(o.tags))]
    return [o for o in all_obligations() if set(o.tags) & tags]
