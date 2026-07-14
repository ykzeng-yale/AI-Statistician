from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .fingerprint import stable_hash
from .generated_metric_contract import (
    GENERATED_METRIC_REQUIREMENT_AUTHORITY_PREFERRED,
    GENERATED_METRIC_REQUIREMENT_AUTHORITY_REQUIRED,
    generated_metric_requirement_set_id,
    generated_metric_requirement_prompt_schema,
    generated_sandbox_runtime_replicates,
    validate_generated_metric_requirements,
)
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
ARCHITECT_RUNTIME_SUBSYSTEMS = (
    "RetrievalMemory",
    "TheoryDeveloper",
    "SimulationEvaluator",
    "AlgorithmEngineer",
    "GeneratedCodeSemanticReviewer",
    "FormalizationEvaluator",
    "TheoremReductionClosureProofEngineer",
    "ExactSourceTheoremProofBodyExecutor",
    "SourceSemanticProofEngineer",
    "PseudoFormalBlockVerifier",
    "SourceTheoremPromotionProofEngineer",
    "ProofEngineer",
    "ExactSourceTheoremProver",
    "FormalizationGapPlanner",
    "CriticEvaluator",
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
                architect_context=architect_context,
            )

        def build_repair_context(**_kwargs: Any) -> dict[str, Any]:
            return _architect_packet_repair_context(
                architect_context=architect_context,
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
            repair_context_builder=build_repair_context,
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
    formal_verification_policy = str(
        runtime_config.get("formal_verification_policy", "optional") or "optional"
    )
    requested_evidence_contract = {
        **_architect_runtime_owned_evidence_contract(
            architect_context=architect_context,
            runtime_config=runtime_config,
        ),
        "requested_research_path": str(
            runtime_config.get("recommended_research_path", "") or ""
        ),
        "formal_required_for_final": formal_verification_policy == "required",
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
    }
    required_plan_subsystems = _required_architect_plan_subsystems(
        requested_evidence_contract
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
        "available_subsystems": list(ARCHITECT_RUNTIME_SUBSYSTEMS),
        "execution_plan_contract": {
            "required_subsystems": list(required_plan_subsystems),
            "planning_rule": (
                "author compact rows for the research path and any anticipated "
                "worker; AgentRuntime will append provenance-marked empty plan "
                "shells for mandatory evidence stages omitted by the proposal, "
                "without inventing objectives, artifacts, statistical content, "
                "code, or proof content. Order authored rows by intended execution "
                "and represent same-owner retries in iteration_policy rather than "
                "duplicate stage rows"
            ),
            "resume_rule": (
                "on plan repair or resume, return the complete amended remaining "
                "worker graph, not only the pending worker"
            ),
        },
        "authority_gates": [
            "schema validation for all LLM packets",
            "AgentRuntime owns shell/filesystem/simulation execution",
            "simulation evidence is empirical, not proof evidence",
            "algorithm sandbox evidence is not production promotion",
            "runnable generated code requires independent semantic review before downstream acceptance",
            "AXLE/local Lean/kernel evidence is required for theorem proof claims",
        ],
        "runtime_capability_gap_routing_agenda": capability_gap_routing_agenda,
        "long_horizon_research_guidance": LONG_HORIZON_RESEARCH_GUIDANCE,
        "requested_evidence_contract": requested_evidence_contract,
        "required_output_contract": ARCHITECT_COORDINATOR_OUTPUT_CONTRACT,
        "boundary": ARCHITECT_COORDINATOR_BOUNDARY,
    }
    return (
        "Act as the top-level ArchitectCoordinator for the AI Statistician runtime. "
        "Return ONLY one compact JSON object matching required_output_contract. The object "
        "must contain exactly the required top-level fields unless a field is needed for "
        "schema repair. Keep non-plan lists to at most 2 short strings or 1 short "
        "object. subsystem_execution_plan is exempt: include compact objects for the "
        "workers you select and any mandatory stages whose objective or ordering you "
        "want to specialize. AgentRuntime will append provenance-marked empty shells "
        "for omitted mandatory evidence stages and use its typed defaults; it will not "
        "invent research content. On resume or plan repair, "
        "return the complete amended remaining graph rather than only the pending worker. Do not "
        "include paragraphs, Markdown, LaTeX derivations, optional long-form analysis sections, "
        "or code. Choose the earliest feasible next subsystem from next_actions "
        "and subsystem_execution_plan; route to RetrievalMemory when source/formal "
        "context is needed, or to TheoryDeveloper when the next open obligation "
        "requires derivation, prerequisite repair, or downstream artifact preparation. "
        "Treat ExactSourceTheoremProver as a typed ProofEngineer child stage: schedule "
        "it only after ProofEngineer emits a lineage-bound exact-source work order. "
        "Its external Lean coding-agent output remains a proposal until the independent "
        "local Lean/kernel rerun accepts the preserved exact declaration. "
        "Treat GeneratedCodeSemanticReviewer as an independent typed child after "
        "AlgorithmEngineer or SimulationEvaluator executes generated code and "
        "before downstream acceptance. It must inspect exact source, actual runtime "
        "arguments, returned results, the theory packet, and the frozen empirical "
        "protocol. REVISE returns typed findings to the source coding agent for fresh "
        "generation and execution; do not replace this with execution-only checks or "
        "task-specific runtime rules. Its verdict is empirical/implementation review, "
        "never theorem proof evidence. "
        "Treat TheoremReductionClosureProofEngineer as another typed child stage: "
        "schedule it only after FormalizationEvaluator emits an immutable closure "
        "work order. Missing candidates return to the LLM ProofEngineer; existing "
        "candidates pass unchanged to local Lean, and the child must run before "
        "CriticEvaluator rather than as post-runtime processing. "
        "Treat ExactSourceTheoremProofBodyExecutor as the typed exact-source "
        "compiler child after FormalizationEvaluator has emitted a hash-bound "
        "candidate and structured target location. It must reject inferred target "
        "identity, preserve candidate lineage, route exact Lean diagnostics back "
        "to ProofEngineer, and run before CriticEvaluator. "
        "Treat SourceSemanticProofEngineer as the typed semantic-support child "
        "when FormalizationEvaluator has no exact source candidate but emits "
        "source-semantic work orders. Registered proof-bank matches are retrieval "
        "and support evidence only; unresolved definitions and proof obligations "
        "must return to the LLM ProofEngineer, and this child must not generate "
        "Lean or claim that helper support proves the source theorem. "
        "Treat PseudoFormalBlockVerifier as a typed independent calibration child "
        "only after FormalizationEvaluator emits immutable pending PF/BV request "
        "rows. It sees explicit bounded block context but no hidden dependency "
        "proof bodies; its validated verdict returns to ProofEngineer in the same "
        "runtime and never substitutes for Lean/kernel evidence. "
        "Treat SourceTheoremPromotionProofEngineer as the typed exact-candidate "
        "planning child after structured source target identity and semantic "
        "support are available but no candidate artifact exists. It must route "
        "generation to the LLM/prover and then ExactSourceTheoremProofBodyExecutor; "
        "it must not synthesize route probes, parse Lean, or claim proof. "
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
        "If architect_context.runtime_packet_validation_replan is present, treat its "
        "exact validation_errors and fingerprints as the current coding-agent blocker. "
        "Choose whether upstream theory/artifact interfaces need repair or whether a "
        "better-context coding-agent retry is feasible; do not blindly resume the failed "
        "task, weaken its validator, or invent code, statistical results, Lean, or proof "
        "evidence in the Architect packet. "
        "When requested_evidence_contract.capability_eval_requires_typed_metric_contracts "
        "is true, author empirical_metric_requirements before either coding agent "
        "runs. Include at least one required row targeting AlgorithmEngineer and "
        "one targeting SimulationEngineer. Give every row an immutable requirement "
        "id, precise metric semantics and measurement protocol, numeric comparison, "
        "aggregation/quorum, and source anchors. Copy "
        "requested_evidence_contract.generated_sandbox_runtime_replicates exactly "
        "into every row as required_runtime_replicates, and describe that same "
        "executed replicate count in the measurement protocol. If the runtime-owned "
        "contract already contains empirical_metric_requirements, they are frozen "
        "from an earlier accepted Architect plan: preserve them byte-for-value and "
        "repair the theory, DGP, measurement implementation, or generated code rather "
        "than rewriting a failed gate. If a target varies by scenario, "
        "require a returned deviation or ratio to that scenario-specific target so "
        "the comparison remains explicit. Coding agents may bind only artifact IDs "
        "and metric paths; they must copy all requirement fields unchanged and may "
        "add only optional diagnostics. AgentRuntime must reject invented or weakened "
        "required gates and must not infer a statistical gate from names or prose. "
        "These Architect requirements remain orchestration proposals, and passing "
        "their runtime contracts is empirical evidence only. "
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
        "capability_eval_requires_generated_code_semantic_review": "boolean",
        "capability_eval_requires_typed_metric_contracts": "boolean",
        "capability_eval_requires_formalizer_lean_candidate": "boolean",
        "generated_sandbox_runtime_replicates": "positive integer",
        "generated_metric_contract_policy": (
            "typed_artifact_bound_required|typed_artifact_bound_preferred"
        ),
        "generated_metric_requirement_authority_policy": (
            "architect_authored_coding_agent_bound_required|"
            "architect_authored_coding_agent_bound_preferred"
        ),
        "empirical_metric_requirements": [
            generated_metric_requirement_prompt_schema()
        ],
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
        "literature_fair_comparison_plan": {
            "type": "array",
            "minItems": 1,
            "maxItems": 2,
            "items": {
                "type": "object",
                "required": [
                    "candidate_source_family",
                    "must_match",
                    "likely_mismatches",
                    "unsafe_transfer_risks",
                ],
                "properties": {
                    "candidate_source_family": {"type": "string"},
                    "must_match": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string"},
                    },
                    "likely_mismatches": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string"},
                    },
                    "unsafe_transfer_risks": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string"},
                    },
                },
            },
        },
        "evidence_contract": {"type": "object"},
        "subsystem_execution_plan": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "subsystem",
                    "objective",
                    "inputs_needed",
                    "expected_artifacts",
                    "acceptance_gate",
                ],
                "properties": {
                    "subsystem": {"type": "string"},
                    "objective": {"type": "string"},
                    "inputs_needed": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "expected_artifacts": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "acceptance_gate": {"type": "string"},
                },
            },
        },
        "retrieval_strategy": {"type": "object"},
        "iteration_policy": {"type": "object"},
        "evidence_gates": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["artifact_kind", "required_evidence", "not_evidence"],
                "properties": {
                    "artifact_kind": {"type": "string"},
                    "required_evidence": {"type": "string"},
                    "not_evidence": {"type": "string"},
                },
            },
        },
        "risk_register": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["risk", "mitigation", "owner_subsystem"],
                "properties": {
                    "risk": {"type": "string"},
                    "mitigation": {"type": "string"},
                    "owner_subsystem": {"type": "string"},
                },
            },
        },
        "next_actions": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["owner_agent", "action", "acceptance_gate"],
                "properties": {
                    "owner_agent": {"type": "string"},
                    "action": {"type": "string"},
                    "acceptance_gate": {"type": "string"},
                },
            },
        },
    },
}


def _architect_packet_repair_context(
    *,
    architect_context: Mapping[str, Any],
    runtime_config: Mapping[str, Any],
) -> dict[str, Any]:
    runtime_contract = _architect_runtime_owned_evidence_contract(
        architect_context=architect_context,
        runtime_config=runtime_config,
    )
    return {
        "required_top_level_fields": list(
            ARCHITECT_COORDINATOR_JSON_SCHEMA["required"]
        ),
        "required_nested_fields": {
            "problem_analysis": [
                "theorem_family",
                "statistical_objects",
                "likely_analogy_classes",
                "key_obstacles",
                "missing_information",
            ],
            "stat_knowledge_bank_plan": [
                "source_families_to_collect",
                "assumption_dimensions",
                "proof_skeletons_to_track",
                "failed_attempt_memory_policy",
            ],
            "evidence_contract": list(
                ARCHITECT_COORDINATOR_OUTPUT_CONTRACT["evidence_contract"]
            ),
        },
        "required_array_item_shapes": {
            "literature_fair_comparison_plan": (
                ARCHITECT_COORDINATOR_OUTPUT_CONTRACT[
                    "literature_fair_comparison_plan"
                ][0]
            ),
            "subsystem_execution_plan": (
                ARCHITECT_COORDINATOR_OUTPUT_CONTRACT[
                    "subsystem_execution_plan"
                ][0]
            ),
            "evidence_gates": ARCHITECT_COORDINATOR_OUTPUT_CONTRACT[
                "evidence_gates"
            ][0],
            "risk_register": ARCHITECT_COORDINATOR_OUTPUT_CONTRACT[
                "risk_register"
            ][0],
            "next_actions": ARCHITECT_COORDINATOR_OUTPUT_CONTRACT[
                "next_actions"
            ][0],
        },
        "runtime_owned_evidence_contract": runtime_contract,
        "required_subsystems": list(
            _required_architect_plan_subsystems(runtime_contract)
        ),
        "empirical_metric_requirement_schema": (
            generated_metric_requirement_prompt_schema()
        ),
        "repair_prompt_priority_instructions": [
            "Return every required top-level field, even when only one row is needed.",
            "Every array named in required_array_item_shapes must contain JSON objects with exactly that shape, never strings.",
            "Author subsystem_execution_plan rows for the intended research path; runtime-owned mandatory-stage shells are appended after generation.",
            "Do not omit or rewrite runtime_owned_evidence_contract fields.",
            (
                "In capability_eval, author required empirical_metric_requirements "
                "for both coding subsystems on the first plan; on replans, preserve "
                "any runtime-owned frozen requirement set unchanged."
            ),
        ],
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
        evaluation_mode = str(
            evidence_contract.get("evaluation_mode", "") or ""
        ).strip()
        metric_policy = str(
            evidence_contract.get("generated_metric_contract_policy", "") or ""
        ).strip()
        authority_policy = str(
            evidence_contract.get(
                "generated_metric_requirement_authority_policy", ""
            )
            or ""
        ).strip()
        if metric_policy and metric_policy not in {
            "typed_artifact_bound_required",
            "typed_artifact_bound_preferred",
        }:
            errors.append(
                "evidence_contract.generated_metric_contract_policy must be "
                "typed_artifact_bound_required or typed_artifact_bound_preferred"
            )
        typed_required = evidence_contract.get(
            "capability_eval_requires_typed_metric_contracts"
        )
        if typed_required is not None and not isinstance(typed_required, bool):
            errors.append(
                "evidence_contract.capability_eval_requires_typed_metric_contracts "
                "must be a boolean"
            )
        if authority_policy and authority_policy not in {
            GENERATED_METRIC_REQUIREMENT_AUTHORITY_REQUIRED,
            GENERATED_METRIC_REQUIREMENT_AUTHORITY_PREFERRED,
        }:
            errors.append(
                "evidence_contract.generated_metric_requirement_authority_policy "
                "must be architect-authored and coding-agent-bound"
            )
        if evaluation_mode == "capability_eval" and (
            typed_required is not True
            or metric_policy != "typed_artifact_bound_required"
            or authority_policy
            != GENERATED_METRIC_REQUIREMENT_AUTHORITY_REQUIRED
            or evidence_contract.get(
                "capability_eval_requires_generated_code_semantic_review"
            )
            is not True
        ):
            errors.append(
                "capability_eval requires typed artifact-bound contracts backed "
                "by Architect-authored metric requirements and independent "
                "generated-code semantic review"
            )
        requirements = evidence_contract.get("empirical_metric_requirements", [])
        expected_runtime_replicates = evidence_contract.get(
            "generated_sandbox_runtime_replicates"
        )
        if evaluation_mode == "capability_eval" and (
            isinstance(expected_runtime_replicates, bool)
            or not isinstance(expected_runtime_replicates, int)
            or expected_runtime_replicates <= 0
        ):
            errors.append(
                "capability_eval requires a positive runtime-owned "
                "generated_sandbox_runtime_replicates value"
            )
        if requirements not in (None, [], {}):
            errors.extend(
                validate_generated_metric_requirements(
                    requirements,
                    required_target_subsystems=(
                        "AlgorithmEngineer",
                        "SimulationEngineer",
                    )
                    if evaluation_mode == "capability_eval"
                    else (),
                    expected_runtime_replicates=(
                        expected_runtime_replicates
                        if evaluation_mode == "capability_eval"
                        and isinstance(expected_runtime_replicates, int)
                        and not isinstance(expected_runtime_replicates, bool)
                        else None
                    ),
                )
            )
        elif evaluation_mode == "capability_eval":
            errors.append(
                "capability_eval requires Architect-authored "
                "empirical_metric_requirements"
            )
        for field in (
            "formal_targets",
            "simulation_targets",
            "acceptance_modes",
            "disclosure_requirements",
        ):
            if evidence_contract.get(field) in (None, "", [], {}):
                errors.append(f"evidence_contract missing or empty field: {field}")
    planned_subsystems: set[str] = set()
    for row in packet.get("subsystem_execution_plan", []) or []:
        if not isinstance(row, Mapping):
            errors.append("subsystem_execution_plan entries must be objects")
            continue
        subsystem = str(row.get("subsystem", "") or "").strip()
        if not subsystem:
            errors.append("subsystem_execution_plan entry missing subsystem")
            continue
        planned_subsystems.add(subsystem)
    for subsystem in _required_architect_plan_subsystems(evidence_contract):
        if subsystem not in planned_subsystems:
            errors.append(
                "subsystem_execution_plan missing evidence-contract-required "
                f"subsystem: {subsystem}"
            )
    forbidden = _contains_forbidden_claim(packet)
    if forbidden:
        errors.append(f"packet contains forbidden execution/proof claim: {forbidden}")
    return sorted(set(errors))


def _architect_runtime_owned_evidence_contract(
    *,
    architect_context: Mapping[str, Any] | None,
    runtime_config: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Preserve caller-owned gates without asking the LLM to transcribe them."""

    context = architect_context or {}
    config = runtime_config or {}
    requested = context.get("runtime_requested_evidence_contract", {})
    requested_contract = dict(requested) if isinstance(requested, Mapping) else {}
    contract: dict[str, Any] = {}
    for field in (
        "formal_targets",
        "simulation_targets",
        "acceptance_modes",
        "disclosure_requirements",
    ):
        value = requested_contract.get(field)
        if value not in (None, "", [], {}):
            contract[field] = value
    prior_plan = context.get("architect_runtime_plan", {})
    prior_contract = (
        prior_plan.get("evidence_contract", {})
        if isinstance(prior_plan, Mapping)
        else {}
    )
    if not isinstance(prior_contract, Mapping):
        prior_contract = {}
    prior_requirements = prior_contract.get("empirical_metric_requirements", [])
    if isinstance(prior_requirements, list) and prior_requirements:
        contract["empirical_metric_requirements"] = [
            dict(row) if isinstance(row, Mapping) else row
            for row in prior_requirements
        ]
        contract["empirical_metric_requirement_set_id"] = (
            generated_metric_requirement_set_id(
                [
                    dict(row)
                    for row in prior_requirements
                    if isinstance(row, Mapping)
                ]
            )
        )
        contract[
            "empirical_metric_requirements_frozen_from_prior_architect_plan"
        ] = True
    policy = str(
        config.get("formal_verification_policy", "")
        or requested_contract.get("formal_verification_policy", "")
        or "optional"
    ).strip().lower()
    contract["formal_verification_policy"] = policy
    contract["formal_required_for_final"] = policy == "required"
    requested_path = str(
        requested_contract.get("recommended_research_path", "")
        or config.get("recommended_research_path", "")
        or ""
    ).strip()
    if requested_path:
        contract["recommended_research_path"] = requested_path
    contract.update(_architect_runtime_capability_eval_contract(config))
    return contract


def _normalize_architect_packet(
    payload: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    model: str,
    model_tier: str,
    provider_name: str,
    raw_response: str,
    runtime_config: Mapping[str, Any] | None = None,
    architect_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    body = dict(payload)
    evidence_contract = body.get("evidence_contract", {})
    if isinstance(evidence_contract, Mapping):
        normalized_contract = dict(evidence_contract)
    else:
        normalized_contract = {}
    for key, value in _architect_runtime_owned_evidence_contract(
        architect_context=architect_context,
        runtime_config=runtime_config,
    ).items():
        normalized_contract[key] = value
    requirements = normalized_contract.get("empirical_metric_requirements", [])
    if isinstance(requirements, list) and requirements:
        normalized_contract["empirical_metric_requirement_set_id"] = (
            generated_metric_requirement_set_id(
                [dict(row) for row in requirements if isinstance(row, Mapping)]
            )
        )
        normalized_contract.setdefault(
            "empirical_metric_requirements_frozen_from_prior_architect_plan",
            False,
        )
    body["evidence_contract"] = normalized_contract
    (
        body["subsystem_execution_plan"],
        body["subsystem_execution_plan_provenance"],
    ) = _elaborate_architect_subsystem_execution_plan(
        body.get("subsystem_execution_plan", []),
        evidence_contract=normalized_contract,
    )
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


def _elaborate_architect_subsystem_execution_plan(
    value: Any,
    *,
    evidence_contract: Mapping[str, Any],
) -> tuple[list[Any], dict[str, Any]]:
    """Compile mandatory evidence topology without synthesizing research content."""

    source_rows = list(value) if isinstance(value, list) else []
    plan_rows: list[Any] = [
        dict(row) if isinstance(row, Mapping) else row for row in source_rows
    ]
    llm_authored_subsystems = [
        str(row.get("subsystem", "") or "").strip()
        for row in source_rows
        if isinstance(row, Mapping)
        and str(row.get("subsystem", "") or "").strip()
    ]
    planned_subsystems = set(llm_authored_subsystems)
    runtime_elaborated_subsystems: list[str] = []
    for subsystem in _required_architect_plan_subsystems(evidence_contract):
        if subsystem in planned_subsystems:
            continue
        plan_rows.append(
            {
                "subsystem": subsystem,
                "objective": "",
                "inputs_needed": [],
                "expected_artifacts": [],
                "acceptance_gate": "",
                "plan_row_source": "runtime_required_evidence_contract",
                "llm_authored": False,
                "runtime_defaults_required": True,
            }
        )
        planned_subsystems.add(subsystem)
        runtime_elaborated_subsystems.append(subsystem)
    provenance = {
        "artifact_kind": "ArchitectSubsystemExecutionPlanProvenance",
        "llm_authored_subsystems": llm_authored_subsystems,
        "runtime_elaborated_subsystems": runtime_elaborated_subsystems,
        "runtime_elaboration_only_adds_empty_mandatory_stage_shells": True,
        "runtime_elaboration_may_generate_research_content": False,
        "evidence_contract_fingerprint": stable_hash(dict(evidence_contract)),
        "boundary": (
            "Runtime elaboration records mandatory typed evidence topology only. "
            "It does not author statistical objectives, expected results, code, "
            "Lean declarations, proof steps, or evidence claims."
        ),
    }
    return plan_rows, provenance


def _architect_runtime_capability_eval_contract(
    runtime_config: Mapping[str, Any],
) -> dict[str, Any]:
    evaluation_mode = str(runtime_config.get("evaluation_mode", "debug") or "debug")
    capability_eval = evaluation_mode == "capability_eval"
    return {
        "evaluation_mode": evaluation_mode,
        "capability_eval_requires_generated_algorithm_code": capability_eval,
        "capability_eval_requires_generated_simulation_code": capability_eval,
        "capability_eval_requires_generated_code_semantic_review": capability_eval,
        "capability_eval_requires_typed_metric_contracts": capability_eval,
        "capability_eval_requires_formalizer_lean_candidate": capability_eval,
        "generated_sandbox_runtime_replicates": (
            generated_sandbox_runtime_replicates(
                int(runtime_config.get("n_runs", 100) or 100)
            )
        ),
        "generated_metric_contract_policy": (
            "typed_artifact_bound_required"
            if capability_eval
            else "typed_artifact_bound_preferred"
        ),
        "generated_metric_requirement_authority_policy": (
            GENERATED_METRIC_REQUIREMENT_AUTHORITY_REQUIRED
            if capability_eval
            else GENERATED_METRIC_REQUIREMENT_AUTHORITY_PREFERRED
        ),
        "capability_eval_requires_exact_source_theorem_prover": (
            capability_eval
            and bool(runtime_config.get("exact_source_theorem_prover_available", False))
        ),
        "theorem_reduction_closure_proofengineer_required": bool(
            runtime_config.get("theorem_closure_proofengineer_bridge", False)
        ),
        "exact_source_theorem_proof_body_executor_required": bool(
            runtime_config.get(
                "source_theorem_formal_environment_proofengineer_bridge",
                False,
            )
            and runtime_config.get(
                "source_theorem_formal_environment_proofengineer_execute_proof_body",
                False,
            )
        ),
        "source_semantic_proofengineer_required": bool(
            runtime_config.get("source_semantic_proofengineer_bridge", False)
        ),
        "pseudo_formal_block_verifier_required": bool(
            runtime_config.get("pseudo_formal_block_verifier_runtime", False)
        ),
        "source_theorem_promotion_proofengineer_required": bool(
            runtime_config.get(
                "source_theorem_promotion_proofengineer_bridge", False
            )
        ),
    }


def _required_architect_plan_subsystems(
    evidence_contract: Mapping[str, Any],
) -> tuple[str, ...]:
    required: set[str] = set()
    if str(evidence_contract.get("evaluation_mode", "") or "") == "capability_eval":
        required.update(("RetrievalMemory", "TheoryDeveloper", "CriticEvaluator"))
        if evidence_contract.get("capability_eval_requires_generated_simulation_code") is True:
            required.add("SimulationEvaluator")
        if evidence_contract.get("capability_eval_requires_generated_algorithm_code") is True:
            required.add("AlgorithmEngineer")
        if (
            evidence_contract.get(
                "capability_eval_requires_generated_code_semantic_review"
            )
            is True
        ):
            required.add("GeneratedCodeSemanticReviewer")
        if evidence_contract.get("capability_eval_requires_formalizer_lean_candidate") is True:
            required.add("FormalizationEvaluator")
        if (
            evidence_contract.get(
                "capability_eval_requires_exact_source_theorem_prover"
            )
            is True
        ):
            required.add("ExactSourceTheoremProver")
    if (
        evidence_contract.get("formal_required_for_final") is True
        or str(evidence_contract.get("formal_verification_policy", "") or "")
        == "required"
    ):
        required.update(
            (
                "FormalizationEvaluator",
                "ProofEngineer",
                "FormalizationGapPlanner",
            )
        )
    if (
        evidence_contract.get(
            "theorem_reduction_closure_proofengineer_required"
        )
        is True
    ):
        required.add("TheoremReductionClosureProofEngineer")
    if (
        evidence_contract.get(
            "exact_source_theorem_proof_body_executor_required"
        )
        is True
    ):
        required.add("ExactSourceTheoremProofBodyExecutor")
    if evidence_contract.get("source_semantic_proofengineer_required") is True:
        required.add("SourceSemanticProofEngineer")
    if evidence_contract.get("pseudo_formal_block_verifier_required") is True:
        required.add("PseudoFormalBlockVerifier")
    if (
        evidence_contract.get(
            "source_theorem_promotion_proofengineer_required"
        )
        is True
    ):
        required.add("SourceTheoremPromotionProofEngineer")
    return tuple(
        subsystem
        for subsystem in ARCHITECT_RUNTIME_SUBSYSTEMS
        if subsystem in required
    )


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
