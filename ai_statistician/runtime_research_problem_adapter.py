from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .fingerprint import stable_hash
from .research_schema import OpenResearchQuestion, ResearchProblemSpec, TheoremGoal


LLM_RESEARCH_AUTHORITY_BOUNDARY = (
    "Architect and TheoryDeveloper packets define the research problem and open "
    "theorem targets for agentic runs. Their contents remain proposals, not "
    "simulation evidence or Lean proof evidence."
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
    if packet.get("problem_card") or packet.get("theorem_cards"):
        return _bundle_from_theory_packet(question, packet)
    plan = _architect_plan(architect_context)
    if plan:
        return _bundle_from_architect_plan(question, plan)
    return _bundle_from_question(question)


def _bundle_from_theory_packet(
    question: OpenResearchQuestion,
    packet: Mapping[str, Any],
) -> RuntimeResearchProblemBundle:
    problem_card = _mapping(packet.get("problem_card", {}))
    derivation = _mapping(packet.get("theory_derivation_packet", {}))
    simulation_spec = _mapping(packet.get("simulation_ademp_spec", {}))
    proof_plan = _mapping(packet.get("proof_plan", {}))
    assumptions = _strings(problem_card.get("assumptions", []))
    if not assumptions:
        assumptions = tuple(
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
    problem = ResearchProblemSpec(
        question_id=question.id,
        problem_class="llm_structured_frontier_problem",
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
        extraction_evidence={
            "authority": ("TheoryDeveloper",),
            "packet_id": (packet_id,) if packet_id else (),
            "packet_hash": (stable_hash(packet),),
        },
    )
    required_primitives = _strings(proof_plan.get("required_primitives", []))
    theorem_goals = _theorem_goals_from_theory_packet(
        packet,
        required_primitives=required_primitives,
    )
    if not theorem_goals:
        theorem_goals = (_question_goal(question, source="TheoryDeveloper"),)
    return RuntimeResearchProblemBundle(
        problem=problem,
        theorem_goals=theorem_goals,
        problem_formalization_source="theory_developer_structured_packet",
        theorem_goal_source="theory_developer_theorem_cards",
        legacy_baseline_skipped_reason=(
            "Agentic research authority is supplied by the validated "
            "TheoryDerivationPacket."
        ),
    )


def _theorem_goals_from_theory_packet(
    packet: Mapping[str, Any],
    *,
    required_primitives: tuple[str, ...],
) -> tuple[TheoremGoal, ...]:
    goals: list[TheoremGoal] = []
    for index, row in enumerate(
        _mapping_rows(packet.get("theorem_cards", [])), start=1
    ):
        goal_id = str(row.get("id", "") or f"theory_target_{index}").strip()
        statement = str(
            row.get("informal_statement", "")
            or row.get("conclusion", "")
            or ""
        ).strip()
        conclusion = str(row.get("conclusion", "") or "").strip()
        if conclusion and conclusion not in statement:
            statement = f"{statement} Conclusion: {conclusion}".strip()
        goals.append(
            TheoremGoal(
                id=goal_id,
                title=str(row.get("title", "") or goal_id),
                informal_statement=statement,
                proof_strategy=str(row.get("proof_strategy", "") or ""),
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
