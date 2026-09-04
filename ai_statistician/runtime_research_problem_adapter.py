from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping

from .agent_runtime import AgentTask
from .fingerprint import stable_hash
from .research_schema import (
    OpenResearchQuestion,
    ResearchProblemSpec,
    TheoremGoal,
    frozen_formal_target_contract_errors,
    research_dimension_requirements,
    research_question_payload,
    research_task_intent_requirement,
)
from .theory_workspace import THEORY_WORKSPACE_CONTENT_AUTHORITY


LLM_RESEARCH_AUTHORITY_BOUNDARY = (
    "Architect and TheoryDeveloper packets define the research problem and open "
    "theorem targets for agentic runs. Their contents remain proposals, not "
    "simulation evidence or Lean proof evidence."
)

def is_frozen_formal_only_question(question: OpenResearchQuestion) -> bool:
    """Identify an exact-target proof task that needs no theory rewrite."""
    if not question.formal_target_contract:
        return False
    requirements = research_dimension_requirements(question.task_intent)
    return bool(
        requirements
        and requirements.get("formal") == "required"
        and all(
            requirements.get(dimension) == "not_applicable"
            for dimension in ("theory", "scientific_code", "empirical")
        )
        and research_task_intent_requirement(question.task_intent, "source_replication")
        == "not_applicable"
        and research_task_intent_requirement(question.task_intent, "novelty")
        == "not_applicable"
    )

def frozen_direct_initial_task(
    *,
    question: OpenResearchQuestion,
    architect_context: Mapping[str, Any],
) -> AgentTask | None:
    intent = question.task_intent
    requirements = research_dimension_requirements(intent)
    lanes = {key for key, value in intent.items() if value == "required"} - {"unresolved_gaps"}
    direct_lane = next(iter(lanes), "") if len(lanes) == 1 else ""
    if bool(
        requirements
        and direct_lane in {"source_replication", "theory"}
        and all(
            value == ("required" if key == direct_lane else "not_applicable")
            for key, value in requirements.items()
        )
        and research_task_intent_requirement(question.task_intent, "source_replication")
        == ("required" if direct_lane == "source_replication" else "not_applicable")
        and research_task_intent_requirement(question.task_intent, "novelty")
        == "not_applicable"
    ):
        objective = {"source_replication": "Replicate.", "theory": "Develop theory."}[direct_lane]
        return AgentTask(
            task_id=f"{direct_lane.replace('_', '-')}:{question.id}",
            owner_subsystem="TheoryDeveloper",
            objective=objective,
            inputs={
                "question": research_question_payload(question, include_task_intent=True),
                "architect_context": dict(architect_context),
            },
        )
    if not is_frozen_formal_only_question(question):
        return None
    contract = deepcopy(question.formal_target_contract)
    errors = frozen_formal_target_contract_errors(
        contract, label="question formal_target_contract", required=True
    )
    if errors:
        raise ValueError("; ".join(errors))
    target_id = str(contract["target_id"])
    contract_hash = stable_hash(contract)
    return AgentTask(
        task_id=f"retrieve-formal-target:{question.id}:{contract_hash[:8]}",
        owner_subsystem="RetrievalMemory",
        objective="Retrieve the frozen Lean target, then enter Formalizer.",
        inputs={
            "question": research_question_payload(question, include_task_intent=True),
            "architect_context": dict(architect_context),
            "retrieval_return_to_subsystem": "FormalizationEvaluator",
            "registered_problem_override": {
                "problem_class": "operator_frozen_exact_lean_target",
                "dgp": "not_applicable",
                "estimand": target_id,
                "assumptions": [],
                "asymptotic_regime": "not_applicable",
                "diagnostics": [],
                "stress_tests": [],
                "extraction_evidence": {
                    "authority": ["operator_frozen_formal_target_contract"],
                    "formal_target_contract_hash": [contract_hash],
                    "lean_source_prefix_sha256": [str(contract["lean_source_prefix_sha256"])],
                },
            },
            "theorem_goals_override": [
                {
                    "id": target_id,
                    "title": question.title,
                    "informal_statement": str(contract["lean_source_prefix"]),
                    "proof_strategy": "Use Lean feedback without changing the declaration.",
                    "status": "FORMAL_GAP",
                    "required_primitives": list(contract.get("required_primitives", [])),
                    "proof_obligations": [
                        "Complete the exact declaration "
                        f"{contract['declaration_name']} without changing its statement."
                    ],
                }
            ],
        },
        allowed_tools=("formal_source_retriever", "model_backend", "local_lean"),
        expected_artifacts=("formalization_manifest", "proof_feedback"),
        acceptance_gate="semantic review plus exact kernel evidence for the unchanged target",
        stop_condition="kernel promotion or a precise Formalizer blocker",
    )


@dataclass(frozen=True)
class RuntimeResearchProblemBundle:
    problem: ResearchProblemSpec
    theorem_goals: tuple[TheoremGoal, ...]
    problem_formalization_source: str
    theorem_goal_source: str
    legacy_baseline_skipped_reason: str

    def provenance(self) -> dict[str, Any]:
        return {
            "problem_formalization_source": self.problem_formalization_source,
            "theorem_goal_source": self.theorem_goal_source,
            "legacy_problem_formalizer_used": False,
            "legacy_theory_planner_used": False,
            "legacy_baseline_skipped_reason": self.legacy_baseline_skipped_reason,
            "boundary": LLM_RESEARCH_AUTHORITY_BOUNDARY,
        }


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _strings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def _mapping_rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, (list, tuple)):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _architect_plan(context: Mapping[str, Any]) -> dict[str, Any]:
    plan = _mapping(context.get("architect_runtime_plan", {}))
    if plan:
        return plan
    control = _mapping(context.get("runtime_architect_control", {}))
    return _mapping(control.get("architect_runtime_plan", {})) or control


def derive_runtime_research_problem(
    *,
    question: OpenResearchQuestion,
    architect_context: Mapping[str, Any],
    theory_packet: Mapping[str, Any] | None = None,
) -> RuntimeResearchProblemBundle:
    packet = _mapping(theory_packet or {})
    if (
        packet.get("theory_content_authority")
        == THEORY_WORKSPACE_CONTENT_AUTHORITY
        or packet.get("problem_card")
        or packet.get("theorem_cards")
    ):
        return _bundle_from_theory_packet(question, packet)
    plan = _architect_plan(architect_context)
    if plan:
        return _bundle_from_architect_plan(question, plan)
    return _bundle_from_question(question)


def _bundle_from_theory_packet(
    question: OpenResearchQuestion,
    packet: Mapping[str, Any],
) -> RuntimeResearchProblemBundle:
    document_authority = (
        packet.get("theory_content_authority") == THEORY_WORKSPACE_CONTENT_AUTHORITY
    )
    problem_card = _mapping(packet.get("problem_card", {}))
    derivation = _mapping(packet.get("theory_derivation_packet", {}))
    simulation_spec = _mapping(packet.get("simulation_ademp_spec", {}))
    proof_plan = _mapping(packet.get("proof_plan", {}))
    assumptions = _strings(problem_card.get("assumptions", [])) or tuple(
        str(row.get("assumption", "") or "").strip()
        for row in _mapping_rows(derivation.get("assumption_ledger", []))
        if str(row.get("assumption", "") or "").strip()
    )
    dgp_parts = [
        str(problem_card.get("observed_data", "") or "").strip(),
        str(problem_card.get("dgp", "") or "").strip(),
    ]
    diagnostics = list(_strings(derivation.get("self_critique", [])))
    diagnostics.extend(
        str(row.get("finding", "") or "").strip()
        for row in _mapping_rows(packet.get("critic_findings", []))
        if str(row.get("finding", "") or "").strip()
    )
    packet_id = str(packet.get("packet_id", "") or "")
    extraction_evidence = {
        "authority": (
            "TheoryDeveloperDocumentWorkspace"
            if document_authority
            else "TheoryDeveloper",
        ),
        "packet_id": (packet_id,) if packet_id else (),
        "packet_hash": (stable_hash(packet),),
    }
    if document_authority:
        document_set_hash = str(
            _mapping(packet.get("theory_workspace_manifest", {})).get(
                "document_set_hash", ""
            )
            or ""
        )
        extraction_evidence["document_set_hash"] = (
            (document_set_hash,) if document_set_hash else ()
        )
    problem = ResearchProblemSpec(
        question_id=question.id,
        problem_class=(
            "document_authoritative_frontier_problem"
            if document_authority
            else "llm_structured_frontier_problem"
        ),
        dgp="; ".join(part for part in dgp_parts if part) or question.description,
        estimand=(
            str(problem_card.get("estimand", "") or "").strip()
            or question.description
        ),
        assumptions=assumptions,
        asymptotic_regime=(
            str(problem_card.get("asymptotic_regime", "") or "").strip()
            or str(problem_card.get("desired_theorem_type", "") or "").strip()
        ),
        diagnostics=tuple(dict.fromkeys(diagnostics)),
        stress_tests=_strings(simulation_spec.get("stress_tests", [])),
        extraction_evidence=extraction_evidence,
    )
    required_primitives = _strings(proof_plan.get("required_primitives", []))
    theorem_goals = _theorem_goals_from_theory_packet(
        packet,
        required_primitives=required_primitives,
        document_authority=document_authority,
    )
    if not theorem_goals:
        theorem_goals = (
            _question_goal(
                question,
                source=(
                    "TheoryDeveloperDocuments"
                    if document_authority
                    else "TheoryDeveloper"
                ),
            ),
        )
    return RuntimeResearchProblemBundle(
        problem=problem,
        theorem_goals=theorem_goals,
        problem_formalization_source=(
            "theory_developer_document_workspace"
            if document_authority
            else "theory_developer_structured_packet"
        ),
        theorem_goal_source=(
            "theory_developer_claim_index"
            if document_authority
            else "theory_developer_theorem_cards"
        ),
        legacy_baseline_skipped_reason=(
            "Agentic research authority is supplied by hash-bound TheoryDeveloper "
            "documents and their compact claim index."
            if document_authority
            else "Agentic research authority is supplied by the validated "
            "TheoryDerivationPacket."
        ),
    )


def _theorem_goals_from_theory_packet(
    packet: Mapping[str, Any],
    *,
    required_primitives: tuple[str, ...],
    document_authority: bool = False,
) -> tuple[TheoremGoal, ...]:
    goals: list[TheoremGoal] = []
    for index, row in enumerate(
        _mapping_rows(packet.get("theorem_cards", [])), start=1
    ):
        goal_id = str(row.get("id", "") or f"theory_target_{index}").strip()
        if document_authority:
            document_path = str(row.get("document_path", "") or "").strip()
            location = f" in {document_path!r}" if document_path else ""
            statement = f"Read exact hash-bound Theory claim {goal_id!r}{location}."
            proof_strategy = (
                "Inspect the authoritative Theory document, then author and compile "
                "that unchanged claim in the active Lean project."
            )
        else:
            statement = str(
                row.get("informal_statement", "")
                or row.get("conclusion", "")
                or ""
            ).strip()
            conclusion = str(row.get("conclusion", "") or "").strip()
            if conclusion and conclusion not in statement:
                statement = f"{statement} Conclusion: {conclusion}".strip()
            proof_strategy = str(row.get("proof_strategy", "") or "")
        goals.append(
            TheoremGoal(
                id=goal_id,
                title=str(row.get("title", "") or goal_id),
                informal_statement=statement,
                proof_strategy=proof_strategy,
                status="FORMAL_GAP",
                required_primitives=required_primitives,
                proof_obligations=(),
            )
        )
    if goals:
        return tuple(goals)
    for index, row in enumerate(
        _mapping_rows(packet.get("formalization_requests", [])), start=1
    ):
        goal_id = str(
            row.get("target_theorem_card", "")
            or row.get("id", "")
            or f"formal_target_{index}"
        ).strip()
        goals.append(
            TheoremGoal(
                id=goal_id,
                title=goal_id,
                informal_statement=str(
                    row.get("lean_statement_sketch", "") or ""
                ).strip(),
                proof_strategy="Generate, compile, inspect proof state, retrieve, and revise.",
                status="FORMAL_GAP",
                required_primitives=required_primitives,
                proof_obligations=(),
            )
        )
    return tuple(goals)


def _bundle_from_architect_plan(
    question: OpenResearchQuestion,
    plan: Mapping[str, Any],
) -> RuntimeResearchProblemBundle:
    analysis = _mapping(plan.get("problem_analysis", {}))
    knowledge_plan = _mapping(plan.get("stat_knowledge_bank_plan", {}))
    evidence_contract = _mapping(plan.get("evidence_contract", {}))
    statistical_objects = _strings(analysis.get("statistical_objects", []))
    theorem_family = str(analysis.get("theorem_family", "") or "").strip()
    proof_skeletons = _strings(knowledge_plan.get("proof_skeletons_to_track", []))
    diagnostics = (
        *_strings(analysis.get("key_obstacles", [])),
        *_strings(analysis.get("missing_information", [])),
    )
    problem = ResearchProblemSpec(
        question_id=question.id,
        problem_class="architect_defined_frontier_problem",
        dgp=(
            "; ".join(statistical_objects)
            if statistical_objects
            else question.description
        ),
        estimand=theorem_family or question.description,
        assumptions=(
            _strings(analysis.get("assumption_dimensions", []))
            or _strings(knowledge_plan.get("assumption_dimensions", []))
        ),
        asymptotic_regime=theorem_family,
        diagnostics=tuple(dict.fromkeys(diagnostics)),
        stress_tests=_strings(evidence_contract.get("simulation_targets", [])),
        extraction_evidence={
            "authority": ("ArchitectCoordinator",),
            "plan_hash": (stable_hash(plan),),
        },
    )
    raw_targets = _strings(evidence_contract.get("formal_targets", []))
    goals = tuple(
        TheoremGoal(
            id=f"architect_formal_target_{index}",
            title=f"Architect formal target {index}",
            informal_statement=target,
            proof_strategy="; ".join(proof_skeletons),
            status="FORMAL_GAP",
            required_primitives=(),
            proof_obligations=(),
        )
        for index, target in enumerate(raw_targets, start=1)
    ) or (_question_goal(question, source="ArchitectCoordinator"),)
    return RuntimeResearchProblemBundle(
        problem=problem,
        theorem_goals=goals,
        problem_formalization_source="architect_coordinator_structured_plan",
        theorem_goal_source="architect_evidence_contract_formal_targets",
        legacy_baseline_skipped_reason=(
            "Agentic research authority is supplied by the validated Architect plan."
        ),
    )


def _bundle_from_question(
    question: OpenResearchQuestion,
) -> RuntimeResearchProblemBundle:
    problem = ResearchProblemSpec(
        question_id=question.id,
        problem_class="unclassified_frontier_problem",
        dgp=question.description,
        estimand=question.description,
        assumptions=(),
        asymptotic_regime="",
        diagnostics=("Architect/TheoryDeveloper structure is not available yet.",),
        stress_tests=(),
        extraction_evidence={"authority": ("OpenResearchQuestion",)},
    )
    return RuntimeResearchProblemBundle(
        problem=problem,
        theorem_goals=(_question_goal(question, source="OpenResearchQuestion"),),
        problem_formalization_source="open_research_question_fallback",
        theorem_goal_source="open_research_question_fallback",
        legacy_baseline_skipped_reason=(
            "No task-family classifier is permitted on the agentic authority path."
        ),
    )


def _question_goal(question: OpenResearchQuestion, *, source: str) -> TheoremGoal:
    return TheoremGoal(
        id="frontier_research_target_" + stable_hash([question.id, source])[:12],
        title=question.title,
        informal_statement=question.description,
        proof_strategy="Await a structured theory derivation and verifier feedback.",
        status="FORMAL_GAP",
        required_primitives=(),
        proof_obligations=(),
    )
