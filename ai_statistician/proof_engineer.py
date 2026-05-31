from __future__ import annotations

import re
from dataclasses import asdict
from typing import Any

from .proof_bank import all_obligations
from .research_schema import ResearchReport
from .schema import FormalObligation
from .verifier import MockProofVerifier, ProofVerifier


class DefaultProofEngineer:
    """Conservative proof-side repair agent for formal-gap loop actions.

    This handler does not invent new Lean theorems. It finds the best already
    registered proof-bank obligation that can serve as a bridge for a FORMAL_GAP,
    verifies that obligation with the configured verifier, and returns a
    contract-complete repair artifact. Full frontier theorem closure still
    requires adding the returned bridge to the theory plan or proving new
    primitives.
    """

    def __init__(self, verifier: ProofVerifier | None = None) -> None:
        self.verifier = verifier or MockProofVerifier()

    async def repair_formal_gap(
        self,
        item: dict[str, Any],
        report: ResearchReport,
    ) -> dict[str, Any] | None:
        primitive_tokens = _tokens(" ".join(str(row) for row in item.get("required_primitives", []) or []))
        query = " ".join(
            str(row)
            for row in (
                item.get("target_theorem_goal", ""),
                item.get("evidence", ""),
                report.problem.problem_class,
                report.problem.estimand,
                " ".join(report.problem.assumptions),
                " ".join(str(row) for row in item.get("required_primitives", []) or []),
            )
        )
        ranked = _rank_bridge_obligations(query, primitive_tokens)
        if not ranked:
            return None
        obligation, score = ranked[0]
        check = await self.verifier.verify(obligation, obligation.proof_body, [])
        if not check.ok:
            return {
                "execution_status": "PROOF_ENGINEER_BRIDGE_VERIFICATION_FAILED",
                "task_type": "proof_bank_expansion_from_formal_gap",
                "result": "Default ProofEngineer found a candidate bridge, but verifier rejected it.",
                "rerun_requested": False,
                "repair_artifact": {
                    "lean_statement": obligation.formal_statement,
                    "proof_body": obligation.proof_body,
                    "expected_lemmas": list(obligation.expected_lemmas),
                    "proof_dependencies": list(obligation.depends_on),
                    "target_theorem_goal": str(item.get("target_theorem_goal", "")),
                    "reuse_targets": [str(item.get("target_theorem_goal", "")), report.problem.problem_class],
                    "verification_errors": list(check.errors),
                },
                "proof_engineer_score": score,
            }
        return {
            "execution_status": "EXECUTED_PROOF_BANK_BRIDGE_REPAIR",
            "task_type": "proof_bank_expansion_from_formal_gap",
            "result": (
                "Default ProofEngineer verified an existing proof-bank bridge for this formal gap. "
                "This supplies a reusable bridge artifact; it does not by itself prove the full frontier theorem."
            ),
            "rerun_requested": False,
            "repair_artifact": {
                "lean_statement": obligation.formal_statement,
                "proof_body": obligation.proof_body,
                "expected_lemmas": list(obligation.expected_lemmas),
                "proof_dependencies": list(obligation.depends_on),
                "target_theorem_goal": str(item.get("target_theorem_goal", "")),
                "reuse_targets": [str(item.get("target_theorem_goal", "")), report.problem.problem_class],
                "proof_obligation_id": obligation.id,
                "bridge_for_primitives": list(item.get("required_primitives", []) or []),
                "kernel_verified": check.kernel_verified,
                "verified": check.ok,
                "verifier": check.verifier,
                "verification_strength": check.verification_strength,
                "elapsed_ms": check.elapsed_ms,
            },
            "proof_engineer_score": score,
            "kernel_verified": check.kernel_verified,
            "verified": check.ok,
        }


def _rank_bridge_obligations(
    query: str,
    primitive_tokens: set[str],
) -> list[tuple[FormalObligation, int]]:
    query_tokens = _tokens(query)
    ranked: list[tuple[FormalObligation, int]] = []
    for obligation in all_obligations():
        text = " ".join(
            (
                obligation.id,
                obligation.title,
                obligation.english,
                obligation.formal_statement,
                " ".join(obligation.tags),
                " ".join(obligation.expected_lemmas),
                " ".join(obligation.depends_on),
            )
        )
        bridge_tokens = _tokens(text)
        overlap = query_tokens & bridge_tokens
        primitive_overlap = primitive_tokens & bridge_tokens
        score = 2 * len(overlap) + 12 * len(primitive_overlap)
        if obligation.id in query:
            score += 50
        id_tokens = _tokens(obligation.id)
        score += 6 * len(primitive_tokens & id_tokens)
        if "zero" in primitive_tokens and "zero" in id_tokens:
            score += 25
        if primitive_tokens and primitive_tokens <= bridge_tokens:
            score += 30
        if obligation.tags and primitive_overlap & set().union(*(_tokens(tag) for tag in obligation.tags)):
            score += 10
        if score > 0:
            ranked.append((obligation, score))
    return sorted(ranked, key=lambda row: (-row[1], row[0].id))


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower().replace("_", " "))
    aliases: set[str] = set(words)
    if "type" in words and "i" in words:
        aliases.add("type1")
    if "e" in words and "process" in words:
        aliases.add("eprocess")
    if "zero" in words and "residual" in words:
        aliases.add("zero_residual")
    if "conditional" in words and "mean" in words and "residual" in words:
        aliases.add("conditional_mean_residual_zero")
    return aliases


def proof_engineer_fingerprint() -> str:
    return repr(
        {
            "handler": "DefaultProofEngineer",
            "n_obligations": len(all_obligations()),
            "obligations": [asdict(row) for row in all_obligations()],
        }
    )
