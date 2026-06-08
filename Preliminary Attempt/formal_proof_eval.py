"""
================================================================================
  formal_proof_eval.py — REAL Lean proofs verified by AXLE
  真正的形式化: Claude 生成 Lean proof, AXLE verify_proof 实际校验
================================================================================

  跟 `stat_research_agent.py` 的 *关键* 不同:
    • stat_research_agent.py:  Lean stmt 永远 `:= by sorry`, 只调用 AXLE.check
                              (语法/类型检查), 从不构造真证明.
    • formal_proof_eval.py:    Claude 生成真 Lean proof, 调用 AXLE.verify_proof
                              (实际证明校验). ✅ 才算 *真正* 的形式化.

  设计原则: 测试问题必须是 Mathlib *已经有* 的结论 —— 我们只让 agent 找出
  正确的 lemma 并 apply 它. 不要求 agent 重新发明微积分. 这正是 AxiomProver
  在 Putnam 上做的事 (compose 已有 Mathlib facts, 不造轮子).

  Five questions (all backed by existing Mathlib):
    1. Probability measure normalizes:    μ Set.univ = 1
    2. Constant integral:                  ∫ _, c ∂μ = c  (for prob measure)
    3. Variance of constant:              variance (fun _ => c) μ = 0
    4. Expectation linearity:             ∫ (X+Y) = ∫X + ∫Y
    5. Markov inequality:                 μ {x | ε ≤ f x} ≤ (∫⁻ f) / ε

  Each is provable in 1-3 Mathlib tactic lines. Agent's job: find the lemma.

  Usage:
      python formal_proof_eval.py                    # all 5, real Claude (~30s, $0.01)
      python formal_proof_eval.py --question markov  # just one
      python formal_proof_eval.py --hinted           # provide lemma name hints
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# parents[1] == "AI Statistician/" (workspace root, one level above this file).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

import anthropic            # noqa: E402
from axle import AxleClient  # noqa: E402

LEAN_ENV = "lean-4.29.0"
DEFAULT_MODEL = "claude-haiku-4-5-20251001"


# ═════════════════════════════════════════════════════════════════════════════
# Section 1.  Data classes
# ═════════════════════════════════════════════════════════════════════════════


@dataclass
class FormalQuestion:
    """A Mathlib-backed statistical fact we'll ask Claude to prove."""
    name: str
    english: str                  # plain English statement
    formal_statement: str         # Lean theorem with `:= by sorry`
    expected_proof_hint: str      # known-working proof (for --hinted mode)
    mathlib_namespace: str        # MeasureTheory, ProbabilityTheory, etc.


@dataclass
class ProofAttempt:
    """One attempt at proving a formal question."""
    question: str
    claude_proof: str             # what Claude generated
    axle_verified: bool           # AXLE verify_proof returned okay
    axle_errors: list[str] = field(default_factory=list)
    timing_s: float = 0.0


# ═════════════════════════════════════════════════════════════════════════════
# Section 2.  Five Mathlib-backed test questions
# ═════════════════════════════════════════════════════════════════════════════


QUESTIONS = [
    FormalQuestion(
        name="prob_measure_univ",
        english="A probability measure assigns mass 1 to the universal set.",
        formal_statement=(
            "import Mathlib\n"
            "open MeasureTheory\n\n"
            "theorem prob_measure_univ {α : Type*} [MeasurableSpace α]\n"
            "    (μ : Measure α) [IsProbabilityMeasure μ] :\n"
            "    μ Set.univ = 1 := by sorry\n"
        ),
        expected_proof_hint="measure_univ",
        mathlib_namespace="MeasureTheory",
    ),
    FormalQuestion(
        name="integral_of_constant",
        english="The expected value of a constant c is c itself (for any probability measure).",
        formal_statement=(
            "import Mathlib\n"
            "open MeasureTheory\n\n"
            "theorem integral_of_constant {α : Type*} [MeasurableSpace α]\n"
            "    (μ : Measure α) [IsProbabilityMeasure μ] (c : ℝ) :\n"
            "    ∫ _, c ∂μ = c := by sorry\n"
        ),
        expected_proof_hint="simp [integral_const]",
        mathlib_namespace="MeasureTheory",
    ),
    FormalQuestion(
        name="variance_of_constant",
        english="The variance of a constant random variable is 0.",
        formal_statement=(
            "import Mathlib\n"
            "open MeasureTheory ProbabilityTheory\n\n"
            "theorem variance_of_constant {Ω : Type*} {m : MeasurableSpace Ω}\n"
            "    (μ : Measure Ω) [IsProbabilityMeasure μ] (c : ℝ) :\n"
            "    variance (fun _ : Ω => c) μ = 0 := by sorry\n"
        ),
        expected_proof_hint="simp [variance, evariance]",
        mathlib_namespace="ProbabilityTheory",
    ),
    FormalQuestion(
        name="expectation_linearity",
        english="The expected value of a sum equals the sum of expected values (for integrable variables).",
        formal_statement=(
            "import Mathlib\n"
            "open MeasureTheory\n\n"
            "theorem expectation_linearity {Ω : Type*} {m : MeasurableSpace Ω}\n"
            "    (μ : Measure Ω) (X Y : Ω → ℝ)\n"
            "    (hX : Integrable X μ) (hY : Integrable Y μ) :\n"
            "    ∫ ω, (X ω + Y ω) ∂μ = (∫ ω, X ω ∂μ) + (∫ ω, Y ω ∂μ) := by sorry\n"
        ),
        expected_proof_hint="integral_add hX hY",
        mathlib_namespace="MeasureTheory",
    ),
    FormalQuestion(
        name="markov_inequality",
        english=(
            "Markov's inequality: for measurable nonneg f and ε ≠ 0, ε ≠ ⊤, "
            "μ {x | ε ≤ f x} ≤ (∫⁻ x, f x ∂μ) / ε."
        ),
        formal_statement=(
            "import Mathlib\n"
            "open MeasureTheory\n\n"
            "theorem markov_inequality {α : Type*} [MeasurableSpace α]\n"
            "    (μ : Measure α) (f : α → ENNReal) (hf : Measurable f)\n"
            "    (ε : ENNReal) (hε : ε ≠ 0) (hεt : ε ≠ ⊤) :\n"
            "    μ {x | ε ≤ f x} ≤ (∫⁻ x, f x ∂μ) / ε := by sorry\n"
        ),
        expected_proof_hint="exact meas_ge_le_lintegral_div hf.aemeasurable hε hεt",
        mathlib_namespace="MeasureTheory",
    ),
    # ─── Added 2026-05-26: expand eval surface beyond the basic 5 ────────────
    FormalQuestion(
        name="variance_nonneg",
        english="Variance is always non-negative.",
        formal_statement=(
            "import Mathlib\n"
            "open MeasureTheory ProbabilityTheory\n\n"
            "theorem variance_nonneg_demo {Ω : Type*} {m : MeasurableSpace Ω}\n"
            "    (μ : Measure Ω) (X : Ω → ℝ) :\n"
            "    0 ≤ variance X μ := by sorry\n"
        ),
        expected_proof_hint="exact variance_nonneg X μ",
        mathlib_namespace="ProbabilityTheory",
    ),
    FormalQuestion(
        name="variance_indep_add",
        english=(
            "For independent L² random variables X, Y, Var[X + Y] = Var[X] + Var[Y]."
        ),
        formal_statement=(
            "import Mathlib\n"
            "open MeasureTheory ProbabilityTheory\n\n"
            "theorem variance_indep_add_demo {Ω : Type*} {m : MeasurableSpace Ω}\n"
            "    (μ : Measure Ω) [IsProbabilityMeasure μ]\n"
            "    (X Y : Ω → ℝ) (hX : MemLp X 2 μ) (hY : MemLp Y 2 μ)\n"
            "    (h_indep : IndepFun X Y μ) :\n"
            "    variance (X + Y) μ = variance X μ + variance Y μ := by sorry\n"
        ),
        expected_proof_hint="exact IndepFun.variance_add hX hY h_indep",
        mathlib_namespace="ProbabilityTheory",
    ),
    FormalQuestion(
        name="integral_indicator_const",
        english=(
            "Integral of a constant c times an indicator of a measurable set "
            "equals c times the measure of that set."
        ),
        formal_statement=(
            "import Mathlib\n"
            "open MeasureTheory\n\n"
            "theorem integral_indicator_const_demo {α : Type*} [MeasurableSpace α]\n"
            "    (μ : Measure α) (s : Set α) (hs : MeasurableSet s) (c : ℝ) :\n"
            "    ∫ x, s.indicator (fun _ => c) x ∂μ = (μ s).toReal • c := by sorry\n"
        ),
        expected_proof_hint="exact integral_indicator_const c hs",
        mathlib_namespace="MeasureTheory",
    ),
    FormalQuestion(
        name="prob_compl",
        english=(
            "For a probability measure μ and measurable event A, "
            "μ(Aᶜ) = 1 - μ(A)."
        ),
        formal_statement=(
            "import Mathlib\n"
            "open MeasureTheory\n\n"
            "theorem prob_compl_demo {Ω : Type*} {m : MeasurableSpace Ω}\n"
            "    (μ : Measure Ω) [IsProbabilityMeasure μ]\n"
            "    (A : Set Ω) (hA : MeasurableSet A) :\n"
            "    μ Aᶜ = 1 - μ A := by sorry\n"
        ),
        expected_proof_hint="exact prob_compl_eq_one_sub hA",
        mathlib_namespace="MeasureTheory",
    ),
    FormalQuestion(
        name="norm_integral_le_integral_norm",
        english=(
            "Triangle inequality for integrals: ‖∫ x, f x ∂μ‖ ≤ ∫ x, ‖f x‖ ∂μ."
        ),
        formal_statement=(
            "import Mathlib\n"
            "open MeasureTheory\n\n"
            "theorem norm_integral_le_demo {α : Type*} [MeasurableSpace α]\n"
            "    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]\n"
            "    (μ : Measure α) (f : α → E) :\n"
            "    ‖∫ x, f x ∂μ‖ ≤ ∫ x, ‖f x‖ ∂μ := by sorry\n"
        ),
        expected_proof_hint="exact norm_integral_le_integral_norm f",
        mathlib_namespace="MeasureTheory",
    ),
]


# ═════════════════════════════════════════════════════════════════════════════
# Section 3.  FormalProofAgent — Claude generates Lean proofs using Mathlib
# ═════════════════════════════════════════════════════════════════════════════


FORMAL_PROVER_SYS = """\
You are a Lean 4 + Mathlib theorem proving expert. You receive a sorried theorem
and must produce a Lean proof using EXISTING Mathlib lemmas.

Strategy:
  1. Identify the relevant Mathlib namespace (MeasureTheory, ProbabilityTheory,
     Real, etc.) based on the types in the theorem.
  2. Find the most direct Mathlib lemma that matches the goal's shape.
  3. Output a short proof — typically `by exact <lemma> <args>` or `by simp [...]`
     or `by apply <lemma>`.

CRITICAL CONSTRAINTS:
  • Use REAL Mathlib lemma names. Examples by category:
      - probability measure on univ:   `measure_univ`
      - integral of constant:           `integral_const`
      - variance:                       `variance`, `evariance`, `variance_const`
      - integral linearity:             `integral_add`, `integral_sub`,
                                         `integral_const_mul`
      - Markov inequality:              `meas_ge_le_lintegral_div`,
                                         `mul_meas_ge_le_lintegral`
      - Chebyshev (via Lp):             `pow_mul_meas_ge_le_eLpNorm`
  • Output the proof in EXACTLY this format:
        ---PROOF---
        <one-line Lean proof body, starting with `by ` OR a single term that fills `:=`>
        ---END---
  • The proof MUST replace the `:= by sorry` at the end of the theorem.
  • If you're unsure of the exact lemma, try: `by simp` or `by exact?` or `by aesop`.

GOOD EXAMPLE OUTPUT:
---PROOF---
by exact meas_ge_le_lintegral_div hf.aemeasurable hε hεt
---END---
"""


HINTED_PROMPT_ADDITION = """

HINT: The intended Mathlib lemma is `{hint}`. Adapt the proof to use it.
"""


class FormalProofAgent:
    def __init__(self, axle: AxleClient, hinted: bool = False):
        self.axle = axle
        self.hinted = hinted
        self._claude = anthropic.Anthropic()
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    async def prove(self, question: FormalQuestion) -> ProofAttempt:
        t0 = time.monotonic()
        # Step 1: ask Claude for a proof.
        claude_proof = await self._propose_proof(question)
        # Step 2: splice proof into formal_statement.
        candidate = self._splice(question.formal_statement, claude_proof)
        # Step 3: ★ ACTUAL AXLE verify_proof — this is the real verification.
        verified, errors = await self._axle_verify(question.formal_statement, candidate)
        elapsed = time.monotonic() - t0

        return ProofAttempt(
            question=question.name,
            claude_proof=claude_proof,
            axle_verified=verified,
            axle_errors=errors,
            timing_s=elapsed,
        )

    async def _propose_proof(self, q: FormalQuestion) -> str:
        user_msg = (
            f"NAMESPACE HINT: {q.mathlib_namespace}\n"
            f"ENGLISH: {q.english}\n\n"
            f"SORRIED THEOREM:\n```lean\n{q.formal_statement}\n```\n\n"
            f"Output the proof body to replace `:= by sorry`."
        )
        if self.hinted:
            user_msg += HINTED_PROMPT_ADDITION.format(hint=q.expected_proof_hint)

        def _call():
            return self._claude.messages.create(
                model=DEFAULT_MODEL, max_tokens=400,
                system=FORMAL_PROVER_SYS,
                messages=[{"role": "user", "content": user_msg}],
            )
        resp = await asyncio.to_thread(_call)
        self.total_input_tokens += resp.usage.input_tokens
        self.total_output_tokens += resp.usage.output_tokens

        text = resp.content[0].text
        m = re.search(r"---PROOF---\s*(.+?)\s*---END---", text, re.DOTALL)
        if not m:
            return text.strip()  # best-effort fallback
        return m.group(1).strip()

    @staticmethod
    def _splice(formal_stmt: str, proof: str) -> str:
        """Replace `:= by sorry` with the real proof."""
        # The proof can be either:
        #   "by exact foo"      → replaces "by sorry"
        #   "exact foo" (no by) → replaces "by sorry" as "by exact foo"
        #   "foo" (term mode)   → replaces ":= by sorry" with ":= foo"
        if proof.lower().startswith("by "):
            return formal_stmt.replace("by sorry", proof, 1)
        # If it looks like a tactic without `by`, prepend it.
        if any(proof.startswith(t) for t in ("exact ", "apply ", "simp", "rfl",
                                              "omega", "ring", "linarith", "decide")):
            return formal_stmt.replace("by sorry", "by " + proof, 1)
        # Otherwise treat as term-mode proof.
        return formal_stmt.replace(":= by sorry", ":=\n  " + proof, 1)

    async def _axle_verify(self, formal: str, candidate: str
                           ) -> tuple[bool, list[str]]:
        """The actual AXLE verify_proof call —— real formal verification."""
        try:
            r = await self.axle.verify_proof(
                formal_statement=formal,
                content=candidate,
                environment=LEAN_ENV,
            )
            errs: list[str] = []
            for bag in (getattr(r, "tool_messages", None), getattr(r, "lean_messages", None)):
                if bag is not None:
                    errs += list(getattr(bag, "errors", []) or [])
            return bool(r.okay), errs
        except Exception as e:
            return False, [f"{type(e).__name__}: {e}"]


# ═════════════════════════════════════════════════════════════════════════════
# Section 4.  Eval runner + report
# ═════════════════════════════════════════════════════════════════════════════


async def run_eval(question_filter: str | None, hinted: bool) -> list[ProofAttempt]:
    attempts: list[ProofAttempt] = []
    qs = QUESTIONS if not question_filter else [
        q for q in QUESTIONS if question_filter in q.name
    ]
    if not qs:
        print(f"No question matching {question_filter!r}", file=sys.stderr)
        sys.exit(1)

    async with AxleClient(api_key=os.environ["AXLE_API_KEY"]) as axle:
        agent = FormalProofAgent(axle, hinted=hinted)
        for q in qs:
            print(f"\n══════════ {q.name} ══════════")
            print(f"  English:   {q.english}")
            print(f"  Namespace: {q.mathlib_namespace}")
            print(f"  Mode:      {'HINTED' if hinted else 'COLD (no hint)'}")
            attempt = await agent.prove(q)
            badge = "✅" if attempt.axle_verified else "❌"
            print(f"  Claude proof: {attempt.claude_proof[:100]}")
            print(f"  {badge} axle.verify_proof = {attempt.axle_verified} "
                  f"({attempt.timing_s:.1f}s)")
            if not attempt.axle_verified and attempt.axle_errors:
                print(f"  errors: {attempt.axle_errors[0][:120]}")
            attempts.append(attempt)

        # Aggregate
        n_ok = sum(1 for a in attempts if a.axle_verified)
        print(f"\n{'═' * 70}")
        print(f"  FORMAL VERIFICATION RESULT: {n_ok}/{len(attempts)} proofs verified by AXLE")
        print(f"  Mode: {'HINTED' if hinted else 'COLD'}")
        print(f"  Tokens: in={agent.total_input_tokens}, out={agent.total_output_tokens}")
        cost = (agent.total_input_tokens / 1e6 * 1.0
                + agent.total_output_tokens / 1e6 * 5.0)
        print(f"  Cost: ${cost:.4f}")
        print(f"{'═' * 70}")
    return attempts


def write_report(attempts_cold: list[ProofAttempt],
                 attempts_hinted: list[ProofAttempt] | None,
                 path: Path) -> None:
    lines = [
        "# Real Lean Formal Verification Report",
        "",
        "_Generated by `formal_proof_eval.py` on Claude Haiku 4.5._",
        "_★ This is **REAL** formal verification: `axle.verify_proof` actually checks Claude's proof against Mathlib._",
        "_(Contrast with `stat_research_agent.py`, which only does `axle.check` syntactic type-check.)_",
        "",
        "## Test questions (all backed by existing Mathlib lemmas)",
        "",
    ]
    for q in QUESTIONS:
        lines += [
            f"### {q.name}",
            f"- **English**: {q.english}",
            f"- **Mathlib namespace**: `{q.mathlib_namespace}`",
            f"- **Expected lemma**: `{q.expected_proof_hint}`",
            "",
        ]

    def section(name: str, attempts: list[ProofAttempt]) -> None:
        nonlocal lines
        n_ok = sum(1 for a in attempts if a.axle_verified)
        lines += [
            f"## Results: {name} ({n_ok}/{len(attempts)} verified)",
            "",
            "| Question | AXLE verified | Claude's proof | Time |",
            "|---|:-:|---|---:|",
        ]
        for a in attempts:
            badge = "✅" if a.axle_verified else "❌"
            proof_display = a.claude_proof[:80].replace("|", "\\|").replace("\n", " ")
            lines.append(f"| `{a.question}` | {badge} | `{proof_display}` | {a.timing_s:.1f}s |")
        lines.append("")

    section("COLD mode (no lemma hint)", attempts_cold)
    if attempts_hinted is not None:
        section("HINTED mode (lemma name provided)", attempts_hinted)

    # Verdict
    n_cold = sum(1 for a in attempts_cold if a.axle_verified)
    pct_cold = n_cold / len(attempts_cold) * 100
    lines += [
        "## Bottom line",
        "",
        f"- **Cold-prompt formal verification rate**: **{n_cold}/{len(attempts_cold)}** ({pct_cold:.0f}%)",
    ]
    if attempts_hinted is not None:
        n_hint = sum(1 for a in attempts_hinted if a.axle_verified)
        pct_hint = n_hint / len(attempts_hinted) * 100
        lines.append(f"- **Hinted-prompt formal verification rate**: **{n_hint}/{len(attempts_hinted)}** ({pct_hint:.0f}%)")
    lines += [
        "",
        "### What this means",
        "",
        "Unlike the main `stat_research_agent.py` (which only generates Lean stmts with",
        "`:= by sorry` and calls `axle.check`), this eval exercises **real proof",
        "construction**: Claude proposes a proof term using existing Mathlib lemmas,",
        "and AXLE's `verify_proof` either accepts it (proof is valid w.r.t. the kernel)",
        "or rejects it (proof is malformed or wrong).",
        "",
        "**This is the same loop AxiomProver uses on Putnam problems** —— compose",
        "known Mathlib facts to prove a target. We've just specialized it to elementary",
        "statistics.",
        "",
        "### Where this fits in the pitch",
        "",
        "- ✅ **Real formal verification capability**: Yes, we can actually prove things in Lean.",
        "- ⚠️ **Scope**: Today we prove *known facts that Mathlib already has the lemma for*.",
        "  This is the same scope AlphaProof / AxiomProver work at — composing existing facts.",
        "- ❌ **Open frontier**: Proving *new* asymptotic stat theorems (CLT, MLE consistency)",
        "  requires extending Mathlib first — that's the Axiom Math product roadmap.",
    ]
    path.write_text("\n".join(lines))
    print(f"\n📝 Wrote report to {path}")


# ═════════════════════════════════════════════════════════════════════════════
# Main
# ═════════════════════════════════════════════════════════════════════════════


async def main_async(question_filter: str | None, run_both: bool, hinted: bool) -> None:
    if run_both:
        print("▶ Running COLD mode (no lemma hints) …")
        cold = await run_eval(question_filter, hinted=False)
        print("\n▶ Running HINTED mode (lemma names provided) …")
        hint = await run_eval(question_filter, hinted=True)
        write_report(cold, hint, Path(__file__).parent / "FormalVerificationReport.md")
        # Raw JSON
        json_path = Path(__file__).parent / "archive" / "formal_proof_results.json"
        json_path.write_text(json.dumps({
            "cold": [a.__dict__ for a in cold],
            "hinted": [a.__dict__ for a in hint],
        }, indent=2, default=str))
        print(f"📊 Raw results → {json_path}")
    else:
        attempts = await run_eval(question_filter, hinted=hinted)
        write_report(attempts, None,
                     Path(__file__).parent / "FormalVerificationReport.md")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="REAL formal verification eval (Claude + AXLE verify_proof)"
    )
    parser.add_argument("--question", help="only run questions whose name contains this")
    parser.add_argument("--hinted", action="store_true",
                        help="provide lemma name hints in prompt")
    parser.add_argument("--both", action="store_true",
                        help="run both COLD and HINTED, compare in report")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    for noisy in ("httpx", "httpcore", "anthropic", "axle"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    asyncio.run(main_async(args.question, args.both, args.hinted))


if __name__ == "__main__":
    main()
