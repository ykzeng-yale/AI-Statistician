from __future__ import annotations

import re
from dataclasses import asdict
from typing import Any

from .proof_bank import all_obligations, get_obligation
from .proof_search import BestFirstWholeProofSearchController
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
        bridge_context = _bridge_chain_context(
            ranked,
            selected_obligation_id=obligation.id,
            item=item,
        )
        search = await BestFirstWholeProofSearchController(self.verifier).solve(
            obligation,
            max_nodes=4,
        )
        if not search.solved:
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
                    "verification_errors": [
                        error
                        for node in search.nodes
                        for error in node.errors
                    ],
                    "proof_search_nodes_expanded": search.nodes_expanded,
                    "proof_search_frontier_exhausted": search.frontier_exhausted,
                    **bridge_context,
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
                "proof_body": search.selected_proof_body,
                "expected_lemmas": list(obligation.expected_lemmas),
                "proof_dependencies": list(obligation.depends_on),
                "target_theorem_goal": str(item.get("target_theorem_goal", "")),
                "reuse_targets": [str(item.get("target_theorem_goal", "")), report.problem.problem_class],
                "proof_obligation_id": obligation.id,
                "bridge_for_primitives": list(item.get("required_primitives", []) or []),
                "kernel_verified": search.kernel_verified,
                "verified": search.solved,
                "verifier": search.verifier,
                "verification_strength": search.selected_verification_strength,
                "proof_search_strategy": "best_first_whole_proof",
                "proof_search_selected_candidate_id": search.selected_candidate_id,
                "proof_search_selected_source": search.selected_source,
                "proof_search_nodes_expanded": search.nodes_expanded,
                "proof_search_candidates_total": search.candidates_total,
                **bridge_context,
            },
            "proof_engineer_score": score,
            "kernel_verified": search.kernel_verified,
            "verified": search.solved,
        }

    async def repair_failed_obligation(
        self,
        item: dict[str, Any],
        report: ResearchReport,
    ) -> dict[str, Any] | None:
        """Repair a failed registered proof-bank obligation when possible.

        This intentionally stays narrower than arbitrary Lean proof repair. It
        only accepts obligations that already live in the proof bank, then runs
        the bounded whole-proof search controller over registered/lemma/memory
        candidates. That gives the feedback loop an executable repair path for
        stale or misranked proof bodies without pretending to invent a new
        frontier theorem.
        """

        obligation_id = _obligation_id_from_failed_item(item)
        if not obligation_id:
            return None
        try:
            obligation = get_obligation(obligation_id)
        except KeyError:
            return None
        search = await BestFirstWholeProofSearchController(self.verifier).solve(
            obligation,
            max_nodes=8,
        )
        artifact: dict[str, Any] = {
            "proof_obligation_id": obligation.id,
            "lean_statement": obligation.formal_statement,
            "expected_lemmas": list(obligation.expected_lemmas),
            "proof_dependencies": list(obligation.depends_on or obligation.expected_lemmas),
            "error_analysis": _failed_obligation_error_analysis(item, search.nodes),
            "verification_errors": [
                error
                for node in search.nodes
                for error in node.errors
            ],
            "proof_search_nodes_expanded": search.nodes_expanded,
            "proof_search_candidates_total": search.candidates_total,
            "proof_search_frontier_exhausted": search.frontier_exhausted,
        }
        if not search.solved:
            return {
                "execution_status": "PROOF_ENGINEER_FAILED_OBLIGATION_REPAIR_FAILED",
                "task_type": "lean_proof_repair_from_axle_error",
                "result": (
                    "Default ProofEngineer found the failed registered obligation, "
                    "but bounded whole-proof search did not produce a verified repair."
                ),
                "rerun_requested": False,
                "repair_artifact": artifact,
                "proof_engineer_score": 0,
            }
        artifact.update(
            {
                "repaired_proof_body": search.selected_proof_body,
                "kernel_verified": search.kernel_verified,
                "verified": search.solved,
                "verifier": search.verifier,
                "verification_strength": search.selected_verification_strength,
                "proof_search_strategy": "best_first_whole_proof",
                "proof_search_selected_candidate_id": search.selected_candidate_id,
                "proof_search_selected_source": search.selected_source,
            }
        )
        return {
            "execution_status": "EXECUTED_FAILED_PROOF_OBLIGATION_REPAIR",
            "task_type": "lean_proof_repair_from_axle_error",
            "result": (
                "Default ProofEngineer repaired a registered failed proof obligation "
                "with a verifier-accepted proof body. This repairs the subclaim; it "
                "does not prove any larger frontier theorem beyond the registered obligation."
            ),
            "rerun_requested": True,
            "repair_artifact": artifact,
            "kernel_verified": search.kernel_verified,
            "verified": search.solved,
            "proof_engineer_score": 1,
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
        if "conditional_mean_residual_zero" in primitive_tokens and "condexp" in id_tokens:
            score += 20
        if ("iterated" in primitive_tokens or "tower" in primitive_tokens) and "tower" in id_tokens:
            score += 25
        if "conditional" in primitive_tokens and "conditional_expectation" in bridge_tokens:
            score += 8
        if primitive_tokens and primitive_tokens <= bridge_tokens:
            score += 30
        if obligation.tags and primitive_overlap & set().union(*(_tokens(tag) for tag in obligation.tags)):
            score += 10
        if score > 0:
            ranked.append((obligation, score))
    return sorted(ranked, key=lambda row: (-row[1], row[0].id))


def _bridge_chain_context(
    ranked: list[tuple[FormalObligation, int]],
    *,
    selected_obligation_id: str,
    item: dict[str, Any],
    limit: int = 8,
) -> dict[str, Any]:
    ranked_rows = [
        {
            "id": obligation.id,
            "title": obligation.title,
            "score": score,
            "depends_on": list(obligation.depends_on),
            "expected_lemmas": list(obligation.expected_lemmas),
        }
        for obligation, score in ranked[:limit]
    ]
    bridge_ids = tuple(row["id"] for row in ranked_rows)
    ordered_ids = _topological_bridge_order(bridge_ids)
    return {
        "selected_bridge_obligation_id": selected_obligation_id,
        "ranked_bridge_obligations": ranked_rows,
        "bridge_chain_order": ordered_ids,
        "bridge_chain": _bridge_chain_rows(ordered_ids, selected_obligation_id, set(bridge_ids)),
        "remaining_frontier_interface": _remaining_frontier_interface(item),
        "proof_evidence_boundary": (
            "The selected bridge obligation may be verifier-accepted, but this bridge-chain "
            "context is not a proof of the full frontier theorem until the remaining interface "
            "is formalized and AXLE verify_proof accepts the composed theorem."
        ),
    }


def _topological_bridge_order(bridge_ids: tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []

    def visit(obligation_id: str) -> None:
        if obligation_id in seen:
            return
        seen.add(obligation_id)
        try:
            obligation = get_obligation(obligation_id)
        except KeyError:
            return
        for dependency_id in obligation.depends_on:
            visit(dependency_id)
        ordered.append(obligation_id)

    for bridge_id in bridge_ids:
        visit(bridge_id)
    return ordered


def _bridge_chain_rows(
    ordered_ids: list[str],
    selected_obligation_id: str,
    ranked_bridge_ids: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for obligation_id in ordered_ids:
        try:
            obligation = get_obligation(obligation_id)
        except KeyError:
            continue
        role = "selected_bridge" if obligation.id == selected_obligation_id else (
            "ranked_bridge" if obligation.id in ranked_bridge_ids else "dependency"
        )
        rows.append(
            {
                "id": obligation.id,
                "title": obligation.title,
                "role": role,
                "depends_on": list(obligation.depends_on),
                "expected_lemmas": list(obligation.expected_lemmas),
                "tags": list(obligation.tags),
            }
        )
    return rows


def _remaining_frontier_interface(item: dict[str, Any]) -> list[str]:
    target = str(item.get("target_theorem_goal", "") or "").strip()
    primitives = [str(row) for row in item.get("required_primitives", []) or [] if str(row)]
    evidence = str(item.get("evidence", "") or "").strip()
    remaining = [
        "full frontier theorem is still a FORMAL_GAP after this bridge repair",
        "compose verified bridge obligations into a non-placeholder Lean theorem statement",
    ]
    if target:
        remaining.append(f"target theorem goal: {target}")
    if primitives:
        remaining.append("required primitives: " + ", ".join(primitives))
    if evidence:
        remaining.append("gap evidence: " + evidence)
    return remaining


def _obligation_id_from_failed_item(item: dict[str, Any]) -> str:
    for key in ("proof_obligation_id", "target_theorem_goal", "target_obligation_id"):
        value = str(item.get(key, "") or "")
        if value:
            return value.split(":")[-1]
    source = str(item.get("id", "") or "")
    if source.startswith("failed_obligation:"):
        return source.split(":")[-1]
    return ""


def _failed_obligation_error_analysis(
    item: dict[str, Any],
    nodes: tuple[Any, ...],
) -> str:
    evidence = str(item.get("evidence", "") or "").strip()
    node_errors = [
        error
        for node in nodes
        for error in getattr(node, "errors", ())
        if str(error).strip()
    ]
    if evidence and node_errors:
        return "Prior verifier evidence: " + evidence + " | search errors: " + " ; ".join(node_errors[:3])
    if evidence:
        return "Prior verifier evidence: " + evidence
    if node_errors:
        return "Search errors: " + " ; ".join(node_errors[:3])
    return "No verifier error text was attached; bounded proof search repaired the registered obligation."


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower().replace("_", " "))
    aliases: set[str] = set(words)
    if "type" in words and "i" in words:
        aliases.add("type1")
    if "e" in words and "process" in words:
        aliases.add("eprocess")
    if "condexp" in words:
        aliases.update({"conditional", "expectation", "conditional_expectation"})
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
