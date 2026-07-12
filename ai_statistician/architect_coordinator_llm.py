from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .fingerprint import stable_hash
from .llm_json_repair import extract_json_object, generate_validated_json_packet
from .model_backend import GeneratorBackend, GeneratorRequest, resolve_generator_model
from .research_schema import OpenResearchQuestion


ARCHITECT_COORDINATOR_SCHEMA_VERSION = 1
ARCHITECT_COORDINATOR_PROPOSAL_NOT_EVIDENCE = "LLM_ARCHITECT_COORDINATOR_PROPOSAL_NOT_PROOF_EVIDENCE"
ARCHITECT_COORDINATOR_BOUNDARY = (
    "LLM ArchitectCoordinator packets are orchestration proposals only. They "
    "can choose subsystem order, evidence gates, retrieval priorities, and "
    "iteration policy, but they do not execute tools, validate simulations, "
    "or prove theorems. Runtime validators and AXLE/local Lean remain the "
    "authority gates."
)
ARCHITECT_CAPABILITY_GAP_ROUTING_BOUNDARY = (
    "Runtime capability-gap routing is Architect orchestration input only. "
    "It may prioritize subsystem work and capability-eval reruns, but it is "
    "not proof evidence, simulation evidence, generated-code evidence, or "
    "verifier evidence."
)

LONG_HORIZON_RESEARCH_GUIDANCE: dict[str, Any] = {
    "problem_analysis_before_retrieval": [
        "classify theorem family, statistical object, likely analogy class, and key obstacle before choosing searches",
        "separate missing mathematical insight from missing implementation, simulation, or formal-library support",
    ],
    "dynamic_stat_knowledge_bank": [
        "record similar theorem families, source refs, assumption matches, assumption mismatches, proof skeletons, and failed attempts",
        "treat the knowledge bank as prompt memory and routing evidence, not proof evidence",
    ],
    "literature_fair_comparison_gate": [
        "for every borrowed theorem family, state matched DGP/estimand/regime pieces and mismatched or unsafe-transfer pieces",
        "do not let embedding/RAG similarity substitute for semantic compatibility",
    ],
    "proposer_verifier_iteration": [
        "let proposer agents draft derivations and routes, then route verifier/critic objections back into the next theory pass",
        "only Lean/AXLE/local kernel rows can promote theorem proof claims",
    ],
}


@dataclass(frozen=True)
class ArchitectCoordinatorConfig:
    model: str = ""
    model_tier: str = "sonnet"
    max_tokens: int = 5000
    temperature: float = 0.1
    provider_name: str = "anthropic"
    max_repair_attempts: int = 1


class LLMArchitectCoordinatorAgent:
    """Generator-backed top-level Architect/Coordinator proposal worker."""

    def __init__(
        self,
        *,
        provider: GeneratorBackend,
        config: ArchitectCoordinatorConfig = ArchitectCoordinatorConfig(),
    ) -> None:
        self.provider = provider
        self.config = config

    def propose(
        self,
        *,
        question: OpenResearchQuestion,
        architect_context: Mapping[str, Any],
        runtime_config: Mapping[str, Any],
    ) -> dict[str, Any]:
        user_prompt = build_architect_coordinator_prompt(
            question=question,
            architect_context=architect_context,
            runtime_config=runtime_config,
        )
        request_model = resolve_generator_model(
            provider_name=self.config.provider_name,
            requested_model=self.config.model,
            model_tier=self.config.model_tier,
        )
        request = GeneratorRequest(
            system_prompt=ARCHITECT_COORDINATOR_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=request_model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            schema=ARCHITECT_COORDINATOR_JSON_SCHEMA,
            metadata={
                "subsystem": "ArchitectCoordinator",
                "agent": "LLMArchitectCoordinatorAgent",
                "provider_name": self.config.provider_name,
                "model_tier": self.config.model_tier,
                "resolved_model": request_model,
            },
        )

        def build_packet(payload: Mapping[str, Any], response: Any, raw_text: str) -> dict[str, Any]:
            return _normalize_architect_packet(
                payload,
                question=question,
                model=response.model or request_model,
                model_tier=self.config.model_tier,
                provider_name=self.config.provider_name or response.provider,
                raw_response=raw_text,
                runtime_config=runtime_config,
            )

        return generate_validated_json_packet(
            provider=self.provider,
            request=request,
            extract_payload=_extract_json_object,
            build_packet=build_packet,
            validate_packet=validate_architect_coordinator_packet,
            validation_label="LLM ArchitectCoordinator packet",
            max_repair_attempts=self.config.max_repair_attempts,
        )


def build_architect_coordinator_prompt(
    *,
    question: OpenResearchQuestion,
    architect_context: Mapping[str, Any],
    runtime_config: Mapping[str, Any],
) -> str:
    capability_gap_routing_agenda = architect_capability_gap_routing_agenda(
        architect_context
    )
    payload = {
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "architect_context": dict(architect_context),
        "runtime_config": dict(runtime_config),
        "available_subsystems": [
            "RetrievalMemory",
            "TheoryDeveloper",
            "SimulationEvaluator",
            "AlgorithmEngineer",
            "FormalizationEvaluator",
            "ProofEngineer",
            "ExactSourceTheoremProver",
            "CriticEvaluator",
        ],
        "authority_gates": [
            "schema validation for all LLM packets",
            "AgentRuntime owns shell/filesystem/simulation execution",
            "simulation evidence is empirical, not proof evidence",
            "algorithm sandbox evidence is not production promotion",
            "AXLE/local Lean/kernel evidence is required for theorem proof claims",
        ],
        "runtime_capability_gap_routing_agenda": capability_gap_routing_agenda,
        "long_horizon_research_guidance": LONG_HORIZON_RESEARCH_GUIDANCE,
        "requested_evidence_contract": {
            "formal_verification_policy": str(
                runtime_config.get("formal_verification_policy", "optional")
                or "optional"
            ),
            "requested_research_path": str(
                runtime_config.get("recommended_research_path", "") or ""
            ),
            **_architect_runtime_capability_eval_contract(runtime_config),
            "policy_semantics": {
                "required": (
                    "full formal proof is an acceptance gate; unresolved formal "
                    "gaps block final theorem acceptance"
                ),
                "optional": (
                    "Architect chooses simulation-first, proof-first, or "
                    "dual-track based on problem type and verification cost; "
                    "formal gaps must still be disclosed"
                ),
                "advisory": (
                    "formal tools are diagnostic only; final research-candidate "
                    "acceptance may rely on derivation, implementation, "
                    "simulation stress tests, and critic review with explicit "
                    "non-formal-proof disclosure"
                ),
            },
            "allowed_research_paths": [
                "simulation_first",
                "proof_first",
                "dual_track",
            ],
        },
        "required_output_contract": ARCHITECT_COORDINATOR_OUTPUT_CONTRACT,
        "boundary": ARCHITECT_COORDINATOR_BOUNDARY,
    }
    return (
        "Act as the top-level ArchitectCoordinator for the AI Statistician runtime. "
        "Return ONLY one compact JSON object matching required_output_contract. The object "
        "must contain exactly the required top-level fields unless a field is needed for "
        "schema repair. Keep each list to at most 2 short strings or 1 short object. Do not "
        "include paragraphs, Markdown, LaTeX derivations, optional long-form analysis sections, "
        "or code. Choose the earliest feasible next subsystem from next_actions "
        "and subsystem_execution_plan; route to RetrievalMemory when source/formal "
        "context is needed, or to TheoryDeveloper when the next open obligation "
        "requires derivation, prerequisite repair, or downstream artifact preparation. "
        "Treat ExactSourceTheoremProver as a typed ProofEngineer child stage: schedule "
        "it only after ProofEngineer emits a lineage-bound exact-source work order. "
        "Its external Lean coding-agent output remains a proposal until the independent "
        "local Lean/kernel rerun accepts the preserved exact declaration. "
        "If runtime learning memory reports concrete source-to-bridge premise targets with "
        "premise_derivation_gap_kind=concrete_premise_target_lacks_nonvacuous_derivation_candidate, "
        "route upstream to TheoryDeveloper/Formalizer for semantic-assumption or lemma repair before "
        "another exact source proof-body retry; ProofEngineer can only close the gap after a "
        "non-vacuous premise derivation candidate exists. "
        "If runtime learning memory reports learning_task=source_theorem_truth_table_feedback "
        "or trigger=RUNTIME_EVIDENCE_TRUTH_TABLE with source_theorem_kernel_verified=false, "
        "prioritize the generated next-action agenda: route proof_body_goal_reached cases to "
        "ProofEngineer/LeanProver, but route premise_derivation_gap_kind or adapter-context "
        "blockers upstream to TheoryDeveloper/Formalizer before another exact source theorem "
        "retry. If proof_body_semantic_review_blocked=true, "
        "proof_body_status=PROOF_BODY_ATTEMPT_BLOCKED, or "
        "proof_body_attempt_blocked_before_goal=true, route exact semantic-definition review/"
        "repair before any proof-body retry, even if proof_body_goal_reached=true. "
        "Do not broaden retrieval or mark the agenda accepted while this source theorem "
        "truth-table feedback is open. "
        "If runtime learning memory reports learning_task=theory_derivation_trace_feedback "
        "or trigger=RUNTIME_THEORY_DERIVATION_TRACE_INCOMPLETE, route back to "
        "TheoryDeveloper for a structured TheoryDerivationPacket with equation_chain, "
        "assumption_ledger, formalization_handoff, and stable anchor ids before "
        "asking SimulationEngineer, AlgorithmEngineer, or FormalizerProofEngineer to "
        "consume the trace. Treat this as orchestration repair memory only, not proof "
        "evidence. "
        "If runtime_capability_gap_routing_agenda contains rows, treat each row as "
        "an open capability obligation: reflect its next_owner_subsystem, "
        "target_behavior, and success_metric in subsystem_execution_plan, "
        "risk_register, or next_actions as appropriate before broad retrieval or "
        "final acceptance. Use recommended_capability_eval_command only as a rerun "
        "hint, and never mark the capability gap resolved until runtime evidence "
        "satisfies the listed success_metric. If the agenda counts show "
        "input_context_truncated=true or rows_seen>rows_loaded, treat the agenda "
        "as a compressed priority-pinned/latest view and do not infer that unseen "
        "capability gaps are resolved; row-level retention_selection explains "
        "why a visible row survived prompt-context compression. Capability-gap routing is "
        "orchestration input, not proof evidence. "
        "Do not execute tools, do not claim simulations ran, and do not claim proof evidence.\n\n"
        + json.dumps(payload, separators=(",", ":"), default=str, ensure_ascii=False)
    )


def architect_capability_gap_routing_agenda(
    architect_context: Mapping[str, Any],
) -> dict[str, Any]:
    """Compress runtime capability-gap routing rows into Architect obligations."""
    if not isinstance(architect_context, Mapping):
        return {}
    context = architect_context.get("runtime_capability_gap_routing", {})
    if not (
        isinstance(context, Mapping)
        and context.get("artifact_kind") == "RuntimeCapabilityGapRoutingContext"
    ):
        return {}
    raw_rows = context.get("rows", [])
    if not isinstance(raw_rows, list):
        return {}
    rows: list[dict[str, Any]] = []
    owner_subsystems: set[str] = set()
    for raw_row in raw_rows:
        if not isinstance(raw_row, Mapping):
            continue
        requirement_id = _clean_architect_gap_text(
            raw_row.get("requirement_id") or raw_row.get("id")
        )
        if not requirement_id:
            continue
        next_owner = _clean_architect_gap_text(
            raw_row.get("next_owner_subsystem") or "ArchitectCoordinator"
        )
        if next_owner:
            owner_subsystems.add(next_owner)
        agenda_row = {
            "requirement_id": requirement_id,
            "scope": _clean_architect_gap_text(raw_row.get("scope")),
            "gap_status": _clean_architect_gap_text(raw_row.get("gap_status"))
            or "OPEN",
            "next_owner_subsystem": next_owner or "ArchitectCoordinator",
            "target_behavior": _clean_architect_gap_text(
                raw_row.get("target_behavior")
            ),
            "success_metric": _clean_architect_gap_text(
                raw_row.get("success_metric")
            ),
            "blocker": _clean_architect_gap_text(raw_row.get("blocker")),
            "recommended_capability_eval_command": _clean_architect_gap_text(
                raw_row.get("recommended_capability_eval_command")
            ),
            "retention_selection": _clean_architect_gap_text(
                raw_row.get("retention_selection")
            ),
            "retention_selection_boundary": _clean_architect_gap_text(
                raw_row.get("retention_selection_boundary")
            ),
            "routing_boundary": _clean_architect_gap_text(
                raw_row.get("routing_boundary")
            )
            or ARCHITECT_CAPABILITY_GAP_ROUTING_BOUNDARY,
        }
        scorecard_payload = _architect_gap_scorecard_payload(
            raw_row.get("scorecard_payload", {})
        )
        if scorecard_payload:
            agenda_row["scorecard_payload"] = scorecard_payload
        rows.append(agenda_row)
    if not rows:
        return {}
    counts = context.get("counts", {})
    if not isinstance(counts, Mapping):
        counts = {}
    rows_loaded = _architect_gap_int(counts.get("rows_loaded"), fallback=len(rows))
    rows_seen = _architect_gap_int(counts.get("rows_seen"), fallback=len(rows))
    return {
        "artifact_kind": "ArchitectCapabilityGapRoutingAgenda",
        "source_artifact_kind": "RuntimeCapabilityGapRoutingContext",
        "counts": {
            "rows_loaded": rows_loaded,
            "rows_seen": rows_seen,
            "errors": _architect_gap_int(counts.get("errors"), fallback=0),
            "max_rows": _architect_gap_int(counts.get("max_rows"), fallback=0),
            "retention_policy": _clean_architect_gap_text(
                counts.get("retention_policy")
            ),
            "input_context_truncated": rows_seen > rows_loaded,
        },
        "owner_subsystems": sorted(owner_subsystems),
        "rows": rows,
        "required_architect_behavior": [
            "allocate each open capability gap to its next_owner_subsystem",
            "keep target_behavior and success_metric visible in next_actions",
            "when input_context_truncated=true, treat rows as a compressed priority-pinned/latest view and do not mark unseen gaps resolved",
            "do not promote routing rows to proof, simulation, code, or verifier evidence",
        ],
        "source_paths": _architect_gap_source_paths(context.get("source_paths", [])),
        "boundary": ARCHITECT_CAPABILITY_GAP_ROUTING_BOUNDARY,
    }


def _clean_architect_gap_text(value: Any) -> str:
    return str(value or "").strip()


def _architect_gap_scorecard_payload(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    scorecard_row = (
        value.get("scorecard_row", {})
        if isinstance(value.get("scorecard_row", {}), Mapping)
        else {}
    )
    audit_metrics = (
        value.get("audit_metrics", {})
        if isinstance(value.get("audit_metrics", {}), Mapping)
        else {}
    )
    if not scorecard_row and not audit_metrics:
        return {}
    return {
        "artifact_kind": _clean_architect_gap_text(
            value.get("artifact_kind")
        )
        or "RuntimeCapabilityGapScorecardPayload",
        "requirement_id": _clean_architect_gap_text(value.get("requirement_id")),
        "scorecard_row": {
            str(key): _architect_gap_compact_value(nested)
            for key, nested in list(scorecard_row.items())[:10]
        },
        "audit_metrics": {
            key: _architect_gap_compact_value(nested)
            for key, nested in _architect_gap_metric_items(
                audit_metrics,
                limit=24,
            )
        },
        "proof_evidence_status": _clean_architect_gap_text(
            value.get("proof_evidence_status")
        ),
        "boundary": _clean_architect_gap_text(value.get("boundary")),
    }


def _architect_gap_metric_items(
    audit_metrics: Mapping[str, Any],
    *,
    limit: int,
) -> list[tuple[str, Any]]:
    indexed_items = [
        (str(key), value, index)
        for index, (key, value) in enumerate(audit_metrics.items())
    ]

    def priority(item: tuple[str, Any, int]) -> tuple[int, int]:
        key, value, index = item
        score = 0
        if _architect_gap_metric_has_signal(key, value):
            score -= 100
        for token, weight in (
            ("contract_issues", 35),
            ("missing", 30),
            ("invalid", 30),
            ("required", 25),
            ("inherited_scope", 20),
            ("scope_parent", 20),
            ("contract_complete", 15),
        ):
            if token in key:
                score -= weight
        return (score, index)

    return [
        (key, value)
        for key, value, _ in sorted(indexed_items, key=priority)[: max(limit, 0)]
    ]


def _architect_gap_metric_has_signal(key: str, value: Any) -> bool:
    if isinstance(value, bool):
        return value is False if "complete" in key or "passed" in key else value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, (list, tuple, set)):
        return bool(value)
    return value is not None


def _architect_gap_compact_value(value: Any) -> Any:
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, str):
        return value[:500]
    if isinstance(value, Mapping):
        return {
            str(key): _architect_gap_compact_value(nested)
            for key, nested in list(value.items())[:10]
        }
    if isinstance(value, list):
        return [_architect_gap_compact_value(item) for item in value[:10]]
    return str(value)[:500]


def _architect_gap_int(value: Any, *, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(fallback)


def _architect_gap_source_paths(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(path) for path in value]
    if value in (None, ""):
        return []
    return [str(value)]


ARCHITECT_COORDINATOR_SYSTEM_PROMPT = """\
You are the top-level ArchitectCoordinator inside an AI Statistician AgentRuntime.

Your job is to coordinate specialized LLM workers and runtime validators for an
open statistical research task. You plan, route, and set evidence gates; you are
not the executor or verifier. Keep proof, simulation, retrieval, and sandbox
evidence boundaries explicit.
"""


ARCHITECT_COORDINATOR_OUTPUT_CONTRACT: dict[str, Any] = {
    "intake_assessment": {
        "problem_type": "string",
        "frontier_difficulty": "low|medium|high",
        "primary_success_criteria": ["one short string"],
        "known_risks": ["one short string"],
    },
    "problem_analysis": {
        "theorem_family": "one short string",
        "statistical_objects": ["one short string"],
        "likely_analogy_classes": ["one short string"],
        "key_obstacles": ["one short string"],
        "missing_information": ["one short string"],
    },
    "stat_knowledge_bank_plan": {
        "source_families_to_collect": ["one short string"],
        "assumption_dimensions": ["one short string"],
        "proof_skeletons_to_track": ["one short string"],
        "failed_attempt_memory_policy": "one short string",
    },
    "literature_fair_comparison_plan": [
        {
            "candidate_source_family": "one short string",
            "must_match": ["one short string"],
            "likely_mismatches": ["one short string"],
            "unsafe_transfer_risks": ["one short string"],
        }
    ],
    "evidence_contract": {
        "formal_verification_policy": "required|optional|advisory",
        "recommended_research_path": "simulation_first|proof_first|dual_track",
        "formal_required_for_final": "boolean",
        "evaluation_mode": "debug|capability_eval",
        "capability_eval_requires_generated_algorithm_code": "boolean",
        "capability_eval_requires_generated_simulation_code": "boolean",
        "capability_eval_requires_formalizer_lean_candidate": "boolean",
        "formal_targets": ["one short string"],
        "simulation_targets": ["one short string"],
        "acceptance_modes": ["one short string"],
        "disclosure_requirements": ["one short string"],
    },
    "subsystem_execution_plan": [
        {
            "subsystem": "RetrievalMemory",
            "objective": "one short string",
            "inputs_needed": ["one short string"],
            "expected_artifacts": ["one short string"],
            "acceptance_gate": "one short string",
        }
    ],
    "retrieval_strategy": {
        "paper_queries": ["one short string"],
        "formal_source_queries": ["one short string"],
        "lean_rag_priorities": ["one short string"],
    },
    "iteration_policy": {
        "reroute_triggers": ["one short string"],
        "max_repair_rounds": "integer",
        "stop_conditions": ["one short string"],
    },
    "evidence_gates": [
        {
            "artifact_kind": "string",
            "required_evidence": "one short string",
            "not_evidence": "one short string",
        }
    ],
    "risk_register": [
        {"risk": "one short string", "mitigation": "one short string", "owner_subsystem": "string"}
    ],
    "next_actions": [
        {"owner_agent": "RetrievalMemory", "action": "one short string", "acceptance_gate": "one short string"}
    ],
}


ARCHITECT_COORDINATOR_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": True,
    "required": [
        "intake_assessment",
        "problem_analysis",
        "stat_knowledge_bank_plan",
        "literature_fair_comparison_plan",
        "evidence_contract",
        "subsystem_execution_plan",
        "retrieval_strategy",
        "iteration_policy",
        "evidence_gates",
        "risk_register",
        "next_actions",
    ],
    "properties": {
        "intake_assessment": {"type": "object"},
        "problem_analysis": {"type": "object"},
        "stat_knowledge_bank_plan": {"type": "object"},
        "literature_fair_comparison_plan": {"type": "array", "minItems": 1},
        "evidence_contract": {"type": "object"},
        "subsystem_execution_plan": {"type": "array", "minItems": 1},
        "retrieval_strategy": {"type": "object"},
        "iteration_policy": {"type": "object"},
        "evidence_gates": {"type": "array", "minItems": 1},
        "risk_register": {"type": "array", "minItems": 1},
        "next_actions": {"type": "array", "minItems": 1},
    },
}


def validate_architect_coordinator_packet(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in (
        "intake_assessment",
        "problem_analysis",
        "stat_knowledge_bank_plan",
        "literature_fair_comparison_plan",
        "evidence_contract",
        "subsystem_execution_plan",
        "retrieval_strategy",
        "iteration_policy",
        "evidence_gates",
        "risk_register",
        "next_actions",
    ):
        if packet.get(field) in (None, "", [], {}):
            errors.append(f"missing or empty field: {field}")
    if packet.get("proof_evidence_status") != ARCHITECT_COORDINATOR_PROPOSAL_NOT_EVIDENCE:
        errors.append("proof_evidence_status must preserve architect proposal boundary")
    if packet.get("runtime_executed") is not False:
        errors.append("LLM ArchitectCoordinator packet cannot set runtime_executed=true")
    if packet.get("kernel_verified") is not False:
        errors.append("LLM ArchitectCoordinator packet cannot set kernel_verified=true")
    problem_analysis = packet.get("problem_analysis", {})
    if isinstance(problem_analysis, Mapping):
        for field in (
            "theorem_family",
            "statistical_objects",
            "likely_analogy_classes",
            "key_obstacles",
            "missing_information",
        ):
            if problem_analysis.get(field) in (None, "", [], {}):
                errors.append(f"problem_analysis missing or empty field: {field}")
    knowledge_plan = packet.get("stat_knowledge_bank_plan", {})
    if isinstance(knowledge_plan, Mapping):
        for field in (
            "source_families_to_collect",
            "assumption_dimensions",
            "proof_skeletons_to_track",
            "failed_attempt_memory_policy",
        ):
            if knowledge_plan.get(field) in (None, "", [], {}):
                errors.append(f"stat_knowledge_bank_plan missing or empty field: {field}")
    for row in packet.get("literature_fair_comparison_plan", []) or []:
        if not isinstance(row, Mapping):
            errors.append("literature_fair_comparison_plan entries must be objects")
            continue
        for field in (
            "candidate_source_family",
            "must_match",
            "likely_mismatches",
            "unsafe_transfer_risks",
        ):
            if row.get(field) in (None, "", [], {}):
                errors.append(
                    f"literature_fair_comparison_plan entry missing or empty field: {field}"
                )
    evidence_contract = packet.get("evidence_contract", {})
    if isinstance(evidence_contract, Mapping):
        policy = str(
            evidence_contract.get("formal_verification_policy", "") or ""
        ).strip().lower()
        if policy not in {"required", "optional", "advisory"}:
            errors.append(
                "evidence_contract.formal_verification_policy must be required, "
                "optional, or advisory"
            )
        path = str(
            evidence_contract.get("recommended_research_path", "") or ""
        ).strip().lower()
        if path not in {"simulation_first", "proof_first", "dual_track"}:
            errors.append(
                "evidence_contract.recommended_research_path must be "
                "simulation_first, proof_first, or dual_track"
            )
        if not isinstance(evidence_contract.get("formal_required_for_final"), bool):
            errors.append(
                "evidence_contract.formal_required_for_final must be a boolean"
            )
        for field in (
            "formal_targets",
            "simulation_targets",
            "acceptance_modes",
            "disclosure_requirements",
        ):
            if evidence_contract.get(field) in (None, "", [], {}):
                errors.append(f"evidence_contract missing or empty field: {field}")
    for row in packet.get("subsystem_execution_plan", []) or []:
        if not isinstance(row, Mapping):
            errors.append("subsystem_execution_plan entries must be objects")
            continue
        if not str(row.get("subsystem", "")).strip():
            errors.append("subsystem_execution_plan entry missing subsystem")
    forbidden = _contains_forbidden_claim(packet)
    if forbidden:
        errors.append(f"packet contains forbidden execution/proof claim: {forbidden}")
    return sorted(set(errors))


def _normalize_architect_packet(
    payload: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    model: str,
    model_tier: str,
    provider_name: str,
    raw_response: str,
    runtime_config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    body = dict(payload)
    evidence_contract = body.get("evidence_contract", {})
    if isinstance(evidence_contract, Mapping):
        normalized_contract = dict(evidence_contract)
    else:
        normalized_contract = {}
    for key, value in _architect_runtime_capability_eval_contract(
        runtime_config or {}
    ).items():
        normalized_contract.setdefault(key, value)
    body["evidence_contract"] = normalized_contract
    body["proof_evidence_status"] = ARCHITECT_COORDINATOR_PROPOSAL_NOT_EVIDENCE
    body["evidence_boundary"] = ARCHITECT_COORDINATOR_BOUNDARY
    body["runtime_executed"] = False
    body["kernel_verified"] = False
    packet_id = stable_hash(
        {
            "question_id": question.id,
            "provider": provider_name,
            "model": model,
            "model_tier": model_tier,
            "body": body,
        }
    )[:24]
    return {
        "schema_version": ARCHITECT_COORDINATOR_SCHEMA_VERSION,
        "artifact_kind": "ArchitectCoordinatorProposalPacket",
        "packet_id": f"architect_coordinator_proposal:{packet_id}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_agent": "LLMArchitectCoordinatorAgent",
        "provider": provider_name,
        "model": model,
        "model_tier": model_tier,
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "raw_response_fingerprint": stable_hash(raw_response),
        **body,
    }


def _architect_runtime_capability_eval_contract(
    runtime_config: Mapping[str, Any],
) -> dict[str, Any]:
    evaluation_mode = str(runtime_config.get("evaluation_mode", "debug") or "debug")
    capability_eval = evaluation_mode == "capability_eval"
    return {
        "evaluation_mode": evaluation_mode,
        "capability_eval_requires_generated_algorithm_code": capability_eval,
        "capability_eval_requires_generated_simulation_code": capability_eval,
        "capability_eval_requires_formalizer_lean_candidate": capability_eval,
    }


def _extract_json_object(text: str) -> dict[str, Any]:
    return extract_json_object(text, label="LLM ArchitectCoordinator")


def _contains_forbidden_claim(value: Any) -> str:
    text = json.dumps(value, default=str).lower()
    forbidden = (
        "runtime_executed\": true",
        "kernel_verified\": true",
        "simulation passed",
        "theorem proved",
        "kernel verified theorem",
    )
    for token in forbidden:
        if token in text:
            return token
    return ""
