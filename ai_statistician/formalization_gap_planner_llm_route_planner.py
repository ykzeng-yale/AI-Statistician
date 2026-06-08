from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .fingerprint import stable_hash
from .formalization_gap_planner_standalone import (
    FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT,
    FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_VERSION,
    standalone_input_json_schema,
    validate_standalone_input_payload,
)
from .model_backend import (
    ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY,
    AnthropicGeneratorBackend,
    GeneratorBackend,
    GeneratorRequest,
    OpenAIResponsesGeneratorBackend,
    StaticJSONGeneratorBackend,
    claude_model_tier_mismatch,
    default_generator_model,
)


FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SCHEMA_VERSION = 1
LLM_ROUTE_PLANNER_REQUEST_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-llm-route-planner-request:1"
)
LLM_ROUTE_PLANNER_RESPONSE_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-llm-route-planner-response:1"
)
LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-llm-route-planner-response-payload:1"
)
LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-llm-route-planner-response-payload-validation-manifest:1"
)
LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-llm-route-planner-response-payload-validation-row:1"
)
LLM_ROUTE_PLANNER_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-llm-route-planner-row:1"
)
ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-route-adoption-blocker-taxonomy:1"
)
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_NOT_PROOF_EVIDENCE"
)
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner LLM route-planner outputs are source-grounded "
    "mathematical planning proposals. They may propose informal proof-route "
    "DAG nodes, formal-library alignment hypotheses, residual interpretations, "
    "and minimal-delta plans, but they are not theorem proof evidence. Proof "
    "claims require target-prover kernel replay."
)
ROUTE_ADOPTION_READY_STATUS = "READY_FOR_STANDALONE_REPLAY"
ROUTE_ADOPTION_PENDING_STATUS = "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
ROUTE_ADOPTION_AWAITING_STATUS = "AWAITING_LLM_ROUTE_PLANNER_RESPONSE"
ROUTE_ADOPTION_REJECTED_STATUS = "REJECTED_LLM_ROUTE_PLAN"
ROUTE_ADOPTION_STATUSES = (
    ROUTE_ADOPTION_READY_STATUS,
    ROUTE_ADOPTION_PENDING_STATUS,
    ROUTE_ADOPTION_AWAITING_STATUS,
    ROUTE_ADOPTION_REJECTED_STATUS,
)
ROUTE_ADOPTION_BLOCKER_RESPONSE_NOT_ACCEPTED = "response_not_accepted"
ROUTE_ADOPTION_BLOCKER_RESPONSE_MISSING = "llm_route_planner_response_missing"
ROUTE_ADOPTION_BLOCKER_SEARCH_REQUESTS = "search_requests_pending_evidence"
ROUTE_ADOPTION_BLOCKER_PLANNER_NEXT_ACTIONS = (
    "planner_next_actions_pending_evidence"
)
ROUTE_ADOPTION_BLOCKER_UNCERTAINTY_FLAGS = "uncertainty_flags_require_review"
ROUTE_ADOPTION_BLOCKER_SEMANTIC_ALIGNMENT_RISKS = (
    "semantic_alignment_risks_require_review"
)
ROUTE_ADOPTION_BLOCKER_RESIDUAL_INTERPRETATIONS = (
    "residual_interpretations_require_route_replay"
)
ROUTE_ADOPTION_BLOCKER_FEEDBACK_ACTIONS = (
    "feedback_summary_actions_pending_resolution"
)
ROUTE_ADOPTION_BLOCKER_RESOURCE_PLAYBOOK_REDISPATCH = (
    "resource_response_playbook_redispatch_pending"
)
ROUTE_ADOPTION_BLOCKER_RESOURCE_REQUEST_QUEUE = (
    "resource_request_queue_pending_response"
)
ROUTE_ADOPTION_BLOCKER_FEEDBACK_REPLAN = "feedback_loop_replan_required"
ROUTE_ADOPTION_BLOCKER_REALIZATION_COVERAGE = "realization_coverage_incomplete"
ROUTE_ADOPTION_BLOCKER_VALUES = (
    ROUTE_ADOPTION_BLOCKER_RESPONSE_NOT_ACCEPTED,
    ROUTE_ADOPTION_BLOCKER_RESPONSE_MISSING,
    ROUTE_ADOPTION_BLOCKER_SEARCH_REQUESTS,
    ROUTE_ADOPTION_BLOCKER_PLANNER_NEXT_ACTIONS,
    ROUTE_ADOPTION_BLOCKER_UNCERTAINTY_FLAGS,
    ROUTE_ADOPTION_BLOCKER_SEMANTIC_ALIGNMENT_RISKS,
    ROUTE_ADOPTION_BLOCKER_RESIDUAL_INTERPRETATIONS,
    ROUTE_ADOPTION_BLOCKER_FEEDBACK_ACTIONS,
    ROUTE_ADOPTION_BLOCKER_RESOURCE_PLAYBOOK_REDISPATCH,
    ROUTE_ADOPTION_BLOCKER_RESOURCE_REQUEST_QUEUE,
    ROUTE_ADOPTION_BLOCKER_FEEDBACK_REPLAN,
    ROUTE_ADOPTION_BLOCKER_REALIZATION_COVERAGE,
)
ROUTE_ADOPTION_BLOCKER_TAXONOMY_ID = (
    "formalization_gap_planner_route_adoption_blocker_taxonomy:1"
)
ROUTE_ADOPTION_BLOCKER_TAXONOMY_COMPONENT = (
    "formalization_gap_planner_route_adoption_blocker_taxonomy"
)
ROUTE_ADOPTION_BLOCKER_DEFINITIONS = {
    ROUTE_ADOPTION_BLOCKER_RESPONSE_NOT_ACCEPTED: (
        "The LLM route-planner response was rejected or failed response "
        "contract validation."
    ),
    ROUTE_ADOPTION_BLOCKER_RESPONSE_MISSING: (
        "The route has no LLM route-planner response yet."
    ),
    ROUTE_ADOPTION_BLOCKER_SEARCH_REQUESTS: (
        "The accepted route asks for additional literature, source, library, "
        "or prover search evidence before adoption."
    ),
    ROUTE_ADOPTION_BLOCKER_PLANNER_NEXT_ACTIONS: (
        "The accepted route carries unresolved planner next-action hooks."
    ),
    ROUTE_ADOPTION_BLOCKER_UNCERTAINTY_FLAGS: (
        "The accepted route carries uncertainty flags requiring review."
    ),
    ROUTE_ADOPTION_BLOCKER_SEMANTIC_ALIGNMENT_RISKS: (
        "The accepted route carries semantic-alignment risks requiring review."
    ),
    ROUTE_ADOPTION_BLOCKER_RESIDUAL_INTERPRETATIONS: (
        "The accepted route interpreted prover residual goals and must be "
        "replayed through route repair before standalone adoption."
    ),
    ROUTE_ADOPTION_BLOCKER_FEEDBACK_ACTIONS: (
        "The feedback-loop summary recommends unresolved follow-up actions."
    ),
    ROUTE_ADOPTION_BLOCKER_RESOURCE_PLAYBOOK_REDISPATCH: (
        "A resource response must be redispatched with its request playbook "
        "before the route can use it."
    ),
    ROUTE_ADOPTION_BLOCKER_RESOURCE_REQUEST_QUEUE: (
        "The resource request queue still has pending responses."
    ),
    ROUTE_ADOPTION_BLOCKER_FEEDBACK_REPLAN: (
        "The feedback loop explicitly requires route replanning."
    ),
    ROUTE_ADOPTION_BLOCKER_REALIZATION_COVERAGE: (
        "The formal-realization coverage witness is incomplete."
    ),
}
LLM_ROUTE_PLANNER_COMPONENT = "formalization_gap_planner_llm_route_planner"
LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATOR_COMPONENT = (
    "formalization_gap_planner_llm_route_planner_response_payload_validator"
)
PROMPT_ONLY_PROVIDER = "prompt_only"
DEFAULT_LLM_ROUTE_PLANNER_PROVIDER = "anthropic"
LLM_ROUTE_PLANNER_PROVIDER_NAMES = (
    PROMPT_ONLY_PROVIDER,
    "static",
    "anthropic",
    "openai",
)
MINIMAL_DELTA_COST_POLICY_ID = (
    "formalization_gap_planner_minimal_delta_cost_policy:1"
)
LLM_ROUTE_PLANNER_MODEL_TIER_POLICY_ID = (
    "formalization_gap_planner_llm_route_planner_model_tier_policy:1"
)
LLM_ROUTE_PLANNER_MODEL_TIERS = ("auto", "haiku", "sonnet", "opus")
LLM_ROUTE_PLANNER_SEARCH_REQUEST_KIND_ALIASES = (
    "literature",
    "literature_search",
    "source",
    "source_search",
    "paper",
    "paper_search",
    "textbook",
    "textbook_search",
    "formal_library",
    "formal_library_search",
    "formal_source",
    "formal_source_search",
    "library",
    "library_search",
    "library_coverage",
    "lean_search",
    "leansearch",
    "leanfinder",
    "loogle",
    "premise_search",
    "state_search",
    "declaration",
    "declaration_search",
    "prover",
    "prover_feedback",
    "proof_state",
    "proof_state_feedback",
    "lsp",
    "lean_lsp",
    "diagnostic",
    "diagnostics",
    "interactive_feedback",
    "route_revision",
    "route_repair",
    "route_refinement",
)
LLM_ROUTE_PLANNER_PLANNER_NEXT_ACTION_HOOK_ALIASES = (
    "literature",
    "literature_search",
    "source",
    "source_search",
    "paper",
    "paper_search",
    "paperclip",
    "paperqa",
    "textbook",
    "semantic_scholar",
    "formal_library",
    "formal_library_search",
    "formal_source",
    "library",
    "library_search",
    "library_coverage",
    "lean_search",
    "leansearch",
    "leanfinder",
    "loogle",
    "premise_search",
    "state_search",
    "declaration",
    "declaration_search",
    "proof_state",
    "proof_state_feedback",
    "prover",
    "prover_feedback",
    "diagnostic",
    "diagnostics",
    "lean_lsp",
    "lsp",
    "lake",
    "interactive_feedback",
    "route_revision",
    "route_repair",
    "route_refinement",
    "replan",
    "revise_route",
)


LLM_ROUTE_PLANNER_MODEL_TIER_POLICY: dict[str, object] = {
    "policy_id": LLM_ROUTE_PLANNER_MODEL_TIER_POLICY_ID,
    "default_mode": "auto",
    "claude_model_selection": ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY,
    "objective": (
        "Use cheaper Claude Haiku calls for bounded route triage and preserve "
        "Claude Sonnet for route synthesis that involves residual goals, "
        "bridge/source-port/new-theory decisions, or larger proof DAGs."
    ),
    "auto_tier_rules": [
        "Use haiku for small routes whose primitives are already-exists, exact, near, wrapper, or different-formulation coverage and have no residual goals.",
        "Use sonnet when prover residual goals, feedback-loop replan signals, or incomplete realization-coverage witnesses are present.",
        "Use sonnet when target-intake rows expose missing proof sources, library-search requirements, proof-state probes, complex theorem shape, or large normalized theorem context.",
        "Use sonnet when any primitive needs a bridge, source port, new definition, new theory, or has unknown/missing coverage.",
        "Use sonnet for routes with more than four primitives, many source refs, or long theorem statements.",
        "Use opus only when explicitly requested by the operator; auto mode never selects opus.",
    ],
    "proof_boundary": PROOF_EVIDENCE_STATUS,
}


MINIMAL_DELTA_COST_POLICY: dict[str, object] = {
    "cost_policy_id": MINIMAL_DELTA_COST_POLICY_ID,
    "objective": (
        "Choose the route with the smallest additional target-prover effort "
        "relative to the current library snapshot, while preserving source "
        "grounding and semantic alignment."
    ),
    "coverage_bucket_base_cost": {
        "already_exists": 0,
        "exact_exists": 0,
        "different_formulation": 1,
        "near_exists": 1,
        "wrapper": 2,
        "wrapper_needed": 2,
        "bridge": 4,
        "bridge_needed": 4,
        "source_port": 7,
        "source_port_needed": 7,
        "new_definition": 9,
        "new_theory": 12,
        "new_theory_needed": 12,
        "unknown": 20,
    },
    "cost_dimensions": [
        "base coverage/action cost",
        "proof difficulty",
        "import cone or dependency footprint",
        "new definitions/typeclass burden",
        "semantic alignment risk",
        "reuse credit for existing declarations",
    ],
    "required_minimal_delta_fields": [
        "cost_model_version",
        "route_cost",
        "primitive_costs",
        "and_or_cost_graph",
        "minimality_rationale",
    ],
    "route_selection_rules": [
        "Prefer exact existing declarations over wrappers.",
        "Prefer wrappers over bridge lemmas when semantics are equivalent.",
        "Prefer bridge lemmas over source ports when the source theorem is narrow.",
        "Prefer source ports over new theory only when the cited source directly supports the needed lemma.",
        "Do not include adjacent theory unless it reduces the selected route cost or resolves a listed residual goal.",
        "If cost comparison is uncertain, emit search_requests instead of asserting minimality.",
    ],
    "proof_boundary": PROOF_EVIDENCE_STATUS,
}


LLM_ROUTE_PLANNER_OUTPUT_CONTRACT: dict[str, object] = {
    "informal_knowledge_dag_nodes": [
        {
            "node_id": "short stable id",
            "claim": "mathematical claim or side condition",
            "depends_on": ["node ids"],
            "source_refs": ["paper/book/local source ids"],
            "source_snippets": [
                {
                    "source_ref": "paper/book/local source id",
                    "excerpt": "bounded evidence excerpt supporting this node",
                    "target_primitives": ["primitive ids"],
                }
            ],
            "source_search_status": "SOURCE_BACKED|SEARCH_REQUESTED|FORMAL_GAP_BOUNDARY",
            "semantic_role": "definition|assumption|lemma|side_condition|main_step",
        }
    ],
    "source_snippets": [
        {
            "source_ref": "paper/book/local source id",
            "excerpt": "bounded evidence excerpt reused by the route plan",
            "target_primitives": ["primitive ids"],
        }
    ],
    "formal_realization_dag_nodes": [
        {
            "node_id": "short stable id",
            "primitive": "formal primitive or declaration target",
            "coverage_bucket": "already_exists|different_formulation|wrapper|bridge|source_port|new_theory",
            "candidate_declarations": ["optional target prover declarations"],
            "candidate_declaration_rows": [
                {
                    "declaration": "target prover declaration",
                    "target_prover_family": "lean4|rocq|isabelle|agda|...",
                    "source_field": "available_formal_declaration_rows|candidate_declarations|resource_request_candidate_declarations",
                }
            ],
            "formalization_action": "reuse|compose|write_wrapper|prove_bridge|source_port|define_new",
        }
    ],
    "lean_realization_dag_nodes": "legacy alias accepted for Lean-only clients; prefer formal_realization_dag_nodes",
    "route_alignment_edges": [
        {
            "informal_node_id": "informal DAG node id",
            "formal_node_id": "formal realization DAG node id",
            "alignment_status": "exact|near|bridge_needed|missing|uncertain",
            "alignment_rationale": "why this formal node realizes the informal claim",
        }
    ],
    "minimal_delta_plan": {
        "selected_primitives": ["primitive ids in the cheapest route"],
        "cost_model_version": MINIMAL_DELTA_COST_POLICY_ID,
        "route_cost": "nonnegative numeric total route cost under minimal_delta_cost_policy",
        "primitive_costs": [
            {
                "primitive": "primitive id",
                "coverage_bucket": "chosen coverage/action bucket",
                "base_cost": "number",
                "proof_difficulty_cost": "number",
                "import_cone_cost": "number",
                "definition_or_typeclass_cost": "number",
                "semantic_risk_cost": "number",
                "reuse_credit": "number",
                "total_cost": "number",
                "cost_rationale": "why this primitive cost is minimal",
            }
        ],
        "and_or_cost_graph": {
            "graph_kind": "AND_OR_ROUTE_COST_GRAPH",
            "selected_route_option_id": "chosen route option id",
            "route_options": [
                {
                    "route_option_id": "candidate route id",
                    "selected": "boolean",
                    "selected_primitives": ["primitive ids"],
                    "route_cost": "nonnegative number",
                    "cost_rationale": "why this route option costs this much",
                }
            ],
            "or_nodes": [
                {
                    "node_id": "choice point id",
                    "choices": ["route option or primitive ids"],
                    "selection_rationale": "why the selected choice is cheapest",
                }
            ],
            "and_edges": [
                {
                    "route_option_id": "candidate route id",
                    "requires": ["primitive ids jointly required by this route"],
                }
            ],
        },
        "new_definitions": ["definitions to add"],
        "wrapper_lemmas": ["wrappers to write"],
        "bridge_lemmas": ["bridge lemmas to prove"],
        "source_port_lemmas": ["source-backed lemmas to port"],
        "do_not_formalize_now": ["out-of-cut theory fragments"],
        "minimality_rationale": "why this route minimizes new Lean/prover effort",
    },
    "residual_interpretations": [
        {
            "residual_goal": "prover residual or diagnostic",
            "interpretation": "missing assumption, typeclass, lemma, or wrong formulation",
            "route_repair": "how the route should change",
            "source_refs": ["source ids supporting the repair"],
            "source_search_status": "SOURCE_BACKED|SEARCH_REQUESTED|FORMAL_GAP_BOUNDARY",
            "formal_gap_boundary": "explicit blocker if this repair is only a formal boundary",
        }
    ],
    "search_requests": [
        {
            "request_kind": "literature|formal_library|prover_feedback|route_revision",
            "query": "bounded next query",
            "reason": "why more evidence is needed before route adoption",
        }
    ],
    "uncertainty_flags": ["semantic risks and missing evidence"],
    "semantic_alignment_risks": ["risks in matching informal and formal meanings"],
    "planner_next_actions": [
        {"owner": "resource or prover adapter", "action": "bounded next action"}
    ],
    "standalone_route": {
        "display_name": "route name",
        "theorem_statement": "informal theorem statement",
        "source_refs": ["route-level sources"],
        "source_snippets": [
            {
                "source_ref": "route-level source",
                "excerpt": "bounded route-level evidence excerpt",
            }
        ],
        "primitives": [
            {
                "primitive": "primitive name",
                "coverage_status": "exact_exists|near_exists|wrapper_needed|bridge_needed|source_port_needed|definition_or_theory_missing",
                "candidate_declarations": ["optional target prover declarations"],
                "candidate_declaration_rows": [
                    {
                        "declaration": "target prover declaration",
                        "target_prover_family": "lean4|rocq|isabelle|agda|...",
                        "source_field": "available_formal_declaration_rows|candidate_declarations|resource_request_candidate_declarations",
                    }
                ],
                "source_refs": ["sources or search obligations"],
                "source_snippets": [
                    {
                        "source_ref": "primitive-level source",
                        "excerpt": "bounded primitive-level evidence excerpt",
                    }
                ],
            }
        ],
    },
    "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
}


SYSTEM_PROMPT = """\
You are the LLM route planner inside a library-aware formalization gap planner.

Your job is to synthesize a source-grounded informal proof-route DAG, align it
to the current formal library/prover context, interpret residual goals, and
propose the minimal additional formalization delta. You are not a prover. Do
not claim kernel verification. If the evidence is insufficient, emit bounded
literature, formal-library, or prover-feedback search requests instead of
inventing facts.
"""


@dataclass(frozen=True)
class FormalizationGapPlannerLLMRoutePlannerRow:
    schema_version: int
    llm_route_planner_row_id: str
    request_id: str
    route_id: str
    display_name: str
    provider_name: str
    model: str
    model_tier: str
    model_selection_rationale: str
    target_prover_family: str
    library_snapshot_ref: str
    prompt_fingerprint: str
    response_present: bool
    response_contract_ok: bool
    informal_knowledge_dag_nodes: tuple[dict[str, object], ...]
    formal_realization_dag_nodes: tuple[dict[str, object], ...]
    lean_realization_dag_nodes: tuple[dict[str, object], ...]
    route_alignment_edges: tuple[dict[str, object], ...]
    minimal_delta_plan: dict[str, object]
    residual_interpretations: tuple[dict[str, object], ...]
    search_requests: tuple[dict[str, object], ...]
    uncertainty_flags: tuple[str, ...]
    semantic_alignment_risks: tuple[str, ...]
    planner_next_actions: tuple[dict[str, object], ...]
    standalone_route: dict[str, object]
    source_refs: tuple[str, ...]
    source_snippets: tuple[dict[str, object], ...]
    realization_coverage_witness: dict[str, object]
    raw_response_text: str
    generator_metadata: dict[str, object]
    provider_failure: bool
    repair_attempts: int
    repair_error_history: tuple[dict[str, object], ...]
    generation_errors: tuple[str, ...]
    acceptance_status: str
    route_adoption_status: str
    route_adoption_blockers: tuple[str, ...]
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formalization_gap_planner_llm_route_planner(
    standalone_input_json: Path,
    out_dir: Path | None = None,
    *,
    provider_name: str = DEFAULT_LLM_ROUTE_PLANNER_PROVIDER,
    model: str = "",
    model_tier: str = "auto",
    max_tokens: int = 9000,
    temperature: float = 0.1,
    max_repair_attempts: int = 1,
    invoke_provider: bool = False,
    response_json: Path | None = None,
    static_response_json: Path | None = None,
    generator_backend: GeneratorBackend | None = None,
    formalization_gap_planner_target_intake_dir: Path | None = None,
    goal_conditioned_minimal_formalization_plan_dir: Path | None = None,
    formalization_gap_planner_library_coverage_map_dir: Path | None = None,
    formalization_gap_planner_source_grounding_audit_dir: Path | None = None,
    formalization_gap_planner_resource_request_queue_dir: Path | None = None,
    formalization_gap_planner_resource_response_ledger_dir: Path | None = None,
    formalization_gap_planner_refinement_evidence_dir: Path | None = None,
    formalization_gap_planner_route_revision_overlay_dir: Path | None = None,
    formalization_gap_planner_interactive_session_dir: Path | None = None,
    formalization_gap_planner_component_resource_registry_dir: Path | None = None,
) -> dict[str, object]:
    """Run or stage the LLM-backed route planner for standalone theorem routes."""

    errors: list[str] = []
    input_payload = _read_json(standalone_input_json, errors)
    errors.extend(validate_standalone_input_payload(input_payload))
    context_payloads = _context_payloads(
        errors,
        formalization_gap_planner_target_intake_dir=(
            formalization_gap_planner_target_intake_dir
        ),
        goal_conditioned_minimal_formalization_plan_dir=(
            goal_conditioned_minimal_formalization_plan_dir
        ),
        formalization_gap_planner_library_coverage_map_dir=(
            formalization_gap_planner_library_coverage_map_dir
        ),
        formalization_gap_planner_source_grounding_audit_dir=(
            formalization_gap_planner_source_grounding_audit_dir
        ),
        formalization_gap_planner_resource_request_queue_dir=(
            formalization_gap_planner_resource_request_queue_dir
        ),
        formalization_gap_planner_resource_response_ledger_dir=(
            formalization_gap_planner_resource_response_ledger_dir
        ),
        formalization_gap_planner_refinement_evidence_dir=(
            formalization_gap_planner_refinement_evidence_dir
        ),
        formalization_gap_planner_route_revision_overlay_dir=(
            formalization_gap_planner_route_revision_overlay_dir
        ),
        formalization_gap_planner_interactive_session_dir=(
            formalization_gap_planner_interactive_session_dir
        ),
        formalization_gap_planner_component_resource_registry_dir=(
            formalization_gap_planner_component_resource_registry_dir
        ),
    )
    routes = _routes(input_payload)
    provider = _normalize_provider_name(provider_name)
    normalized_model_tier = _normalize_model_tier(model_tier)
    request_packets = tuple(
        _request_packet(
            input_payload,
            route,
            route_index=index,
            provider_name=provider,
            model=model,
            model_tier=normalized_model_tier,
            context_payloads=context_payloads,
        )
        for index, route in enumerate(routes)
    )
    by_model_tier = Counter(
        str(packet.get("model_tier", "") or "unknown") for packet in request_packets
    )
    request_model_tier_mismatches = _request_model_tier_mismatches(request_packets)
    request_schema = llm_route_planner_request_json_schema()
    response_payload_schema = llm_route_planner_response_payload_schema()
    request_schema_errors = [
        validate_llm_route_planner_request(packet, request_schema)
        for packet in request_packets
    ]
    raw_responses: list[dict[str, Any]] = []
    if response_json is not None:
        raw_responses.extend(_read_response_json(response_json, errors))
    if static_response_json is not None and response_json is None:
        if invoke_provider:
            generator_backend = StaticJSONGeneratorBackend(
                _read_json(static_response_json, errors)
            )
        else:
            raw_responses.extend(_read_response_json(static_response_json, errors))
    if invoke_provider and generator_backend is None:
        generator_backend = _provider_backend(provider)
    if invoke_provider and generator_backend is not None:
        raw_responses.extend(
            _generate_responses(
                request_packets,
                generator_backend=generator_backend,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                max_repair_attempts=max_repair_attempts,
                errors=errors,
            )
        )

    responses_by_request = _responses_by_request(raw_responses, request_packets, errors)
    rows = tuple(
        _row_for_request(
            request,
            request_errors=request_errors,
            response=responses_by_request.get(str(request.get("request_id", ""))),
        )
        for request, request_errors in zip(request_packets, request_schema_errors)
    )
    row_dicts = [asdict(row) for row in rows]
    response_schema = llm_route_planner_response_json_schema()
    row_schema = llm_route_planner_row_json_schema()
    response_schema_errors = [
        validate_llm_route_planner_response(row, response_schema)
        for row in raw_responses
    ]
    row_schema_errors = [
        validate_llm_route_planner_row(row, row_schema) for row in row_dicts
    ]
    by_acceptance_status = Counter(row.acceptance_status for row in rows)
    by_route_adoption_status = Counter(row.route_adoption_status for row in rows)
    standalone_seed = _standalone_seed(input_payload, rows)
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": LLM_ROUTE_PLANNER_COMPONENT,
        "standalone_input_path": str(standalone_input_json),
        "standalone_input_schema_id": (
            "urn:ai-statistician:schemas:formalization-gap-planner-standalone-input:1"
        ),
        "provider_name": provider,
        "model": model,
        "model_tier_selection_mode": normalized_model_tier,
        "llm_route_planner_model_tier_policy": LLM_ROUTE_PLANNER_MODEL_TIER_POLICY,
        "max_repair_attempts": max(0, int(max_repair_attempts)),
        "invoke_provider": invoke_provider,
        "n_routes": len(routes),
        "n_request_packets": len(request_packets),
        "n_requests_with_available_source_snippets": sum(
            1
            for packet in request_packets
            if _dict_value(packet, "context_packet").get("available_source_snippets")
        ),
        "n_request_available_source_snippets": sum(
            len(_dict_value(packet, "context_packet").get("available_source_snippets", []))
            for packet in request_packets
        ),
        "n_requests_with_target_intake_rows": sum(
            1
            for packet in request_packets
            if _dict_tuple(
                _dict_value(packet, "context_packet").get("target_intake_rows", [])
            )
        ),
        "n_request_target_intake_rows": sum(
            len(
                _dict_tuple(
                    _dict_value(packet, "context_packet").get(
                        "target_intake_rows",
                        [],
                    )
                )
            )
            for packet in request_packets
        ),
        "n_request_model_tier_haiku": by_model_tier.get("haiku", 0),
        "n_request_model_tier_sonnet": by_model_tier.get("sonnet", 0),
        "n_request_model_tier_opus": by_model_tier.get("opus", 0),
        "by_request_model_tier": dict(sorted(by_model_tier.items())),
        "n_request_model_tier_mismatches": len(request_model_tier_mismatches),
        "request_model_tier_mismatches": request_model_tier_mismatches,
        "n_request_residual_goals": sum(
            len(_str_tuple(packet.get("residual_goals", [])))
            for packet in request_packets
        ),
        "n_requests_with_library_coverage_rows": sum(
            1
            for packet in request_packets
            if _dict_tuple(
                _dict_value(packet, "context_packet").get("library_coverage_rows", [])
            )
        ),
        "n_requests_with_source_grounding_rows": sum(
            1
            for packet in request_packets
            if _dict_tuple(
                _dict_value(packet, "context_packet").get("source_grounding_rows", [])
            )
        ),
        "n_requests_with_resource_response_ledger_rows": sum(
            1
            for packet in request_packets
            if _dict_tuple(
                _dict_value(packet, "context_packet").get(
                    "resource_response_ledger_rows",
                    [],
                )
            )
        ),
        "n_requests_with_resource_request_queue_rows": sum(
            1
            for packet in request_packets
            if _dict_tuple(
                _dict_value(packet, "context_packet").get(
                    "resource_request_queue_rows",
                    [],
                )
            )
        ),
        "n_request_resource_request_queue_rows": sum(
            len(
                _dict_tuple(
                    _dict_value(packet, "context_packet").get(
                        "resource_request_queue_rows",
                        [],
                    )
                )
            )
            for packet in request_packets
        ),
        "n_requests_with_resource_request_playbooks": sum(
            1
            for packet in request_packets
            if _dict_tuple(
                _dict_value(packet, "context_packet").get(
                    "resource_request_playbooks",
                    [],
                )
            )
        ),
        "n_request_resource_request_playbooks": sum(
            len(
                _dict_tuple(
                    _dict_value(packet, "context_packet").get(
                        "resource_request_playbooks",
                        [],
                    )
                )
            )
            for packet in request_packets
        ),
        "n_requests_with_refinement_evidence_rows": sum(
            1
            for packet in request_packets
            if _dict_tuple(
                _dict_value(packet, "context_packet").get("refinement_evidence_rows", [])
            )
        ),
        "n_requests_with_route_revision_overlay_rows": sum(
            1
            for packet in request_packets
            if _dict_tuple(
                _dict_value(packet, "context_packet").get("route_revision_overlay_rows", [])
            )
        ),
        "n_requests_with_interactive_session_rows": sum(
            1
            for packet in request_packets
            if _dict_tuple(
                _dict_value(packet, "context_packet").get("interactive_session_rows", [])
            )
        ),
        "n_requests_with_interactive_decision_policy_rows": sum(
            1
            for packet in request_packets
            if _dict_tuple(
                _dict_value(packet, "context_packet").get(
                    "interactive_decision_policy_rows",
                    [],
                )
            )
        ),
        "n_requests_with_feedback_loop_summary": sum(
            1
            for packet in request_packets
            if _dict_value(packet, "context_packet").get("feedback_loop_summary")
        ),
        "n_feedback_loop_summary_residual_goals": sum(
            int(
                _dict_value(
                    _dict_value(packet, "context_packet"),
                    "feedback_loop_summary",
                ).get("residual_goal_count", 0)
                or 0
            )
            for packet in request_packets
        ),
        "n_feedback_loop_summary_replan_required": sum(
            1
            for packet in request_packets
            if bool(
                _dict_value(
                    _dict_value(packet, "context_packet"),
                    "feedback_loop_summary",
                ).get("replan_required", False)
            )
        ),
        "n_feedback_loop_summary_resource_request_playbooks": sum(
            int(
                _dict_value(
                    _dict_value(packet, "context_packet"),
                    "feedback_loop_summary",
                ).get("resource_request_playbook_count", 0)
                or 0
            )
            for packet in request_packets
        ),
        "n_feedback_loop_summary_resource_response_admissible": sum(
            int(
                _dict_value(
                    _dict_value(
                        _dict_value(packet, "context_packet"),
                        "feedback_loop_summary",
                    ),
                    "resource_response_admissibility",
                ).get("admissible_count", 0)
                or 0
            )
            for packet in request_packets
        ),
        "n_feedback_loop_summary_resource_response_status_only": sum(
            int(
                _dict_value(
                    _dict_value(
                        _dict_value(packet, "context_packet"),
                        "feedback_loop_summary",
                    ),
                    "resource_response_admissibility",
                ).get("status_only_count", 0)
                or 0
            )
            for packet in request_packets
        ),
        "n_feedback_loop_summary_refinement_evidence_admissible": sum(
            int(
                _dict_value(
                    _dict_value(
                        _dict_value(packet, "context_packet"),
                        "feedback_loop_summary",
                    ),
                    "refinement_evidence_admissibility",
                ).get("admissible_count", 0)
                or 0
            )
            for packet in request_packets
        ),
        "n_feedback_loop_summary_refinement_evidence_status_only": sum(
            int(
                _dict_value(
                    _dict_value(
                        _dict_value(packet, "context_packet"),
                        "feedback_loop_summary",
                    ),
                    "refinement_evidence_admissibility",
                ).get("status_only_count", 0)
                or 0
            )
            for packet in request_packets
        ),
        "n_feedback_loop_summary_source_snippets": sum(
            len(
                _dict_tuple(
                    _dict_value(
                        _dict_value(packet, "context_packet"),
                        "feedback_loop_summary",
                    ).get("admissible_source_snippets", [])
                )
            )
            for packet in request_packets
        ),
        "n_feedback_loop_summary_realization_witnesses": sum(
            int(
                _dict_value(
                    _dict_value(
                        _dict_value(packet, "context_packet"),
                        "feedback_loop_summary",
                    ),
                    "realization_coverage",
                ).get("witness_count", 0)
                or 0
            )
            for packet in request_packets
        ),
        "n_feedback_loop_summary_incomplete_realization_coverage": sum(
            1
            for packet in request_packets
            if _dict_value(
                _dict_value(
                    _dict_value(packet, "context_packet"),
                    "feedback_loop_summary",
                ),
                "realization_coverage",
            ).get("complete") is False
        ),
        "n_feedback_loop_summary_missing_selected_formal_primitives": sum(
            len(
                _str_tuple(
                    _dict_value(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "feedback_loop_summary",
                        ),
                        "realization_coverage",
                    ).get("missing_selected_formal_primitives", [])
                )
            )
            for packet in request_packets
        ),
        "n_feedback_loop_summary_missing_delta_alignment_primitives": sum(
            len(
                _str_tuple(
                    _dict_value(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "feedback_loop_summary",
                        ),
                        "realization_coverage",
                    ).get("missing_delta_alignment_primitives", [])
                )
            )
            for packet in request_packets
        ),
        "n_requests_with_component_resource_registry_context": sum(
            1
            for packet in request_packets
            if _dict_value(packet, "context_packet").get(
                "component_resource_registry_context"
            )
        ),
        "n_component_resource_registry_components_in_prompt": sum(
            len(
                _dict_tuple(
                    _component_resource_context_from_request(packet).get(
                        "component_rows",
                        [],
                    )
                )
            )
            for packet in request_packets
        ),
        "n_component_resource_registry_resources_in_prompt": sum(
            len(
                _dict_tuple(
                    _component_resource_context_from_request(packet).get(
                        "resource_rows",
                        [],
                    )
                )
            )
            for packet in request_packets
        ),
        "n_component_resource_registry_contracts_in_prompt": sum(
            len(
                _dict_tuple(
                    _component_resource_context_from_request(packet).get(
                        "resource_contract_rows",
                        [],
                    )
                )
            )
            for packet in request_packets
        ),
        "n_request_schema_valid": sum(
            1 for request_errors in request_schema_errors if not request_errors
        ),
        "n_request_schema_invalid": sum(
            1 for request_errors in request_schema_errors if request_errors
        ),
        "n_raw_responses": len(raw_responses),
        "n_generated_response_repair_attempts": sum(
            int(row.get("repair_attempts", 0) or 0)
            for row in raw_responses
            if isinstance(row, Mapping)
        ),
        "n_generated_responses_repaired": sum(
            1
            for row in raw_responses
            if isinstance(row, Mapping)
            and int(row.get("repair_attempts", 0) or 0) > 0
            and not row.get("generation_errors")
        ),
        "n_response_schema_valid": sum(
            1 for response_errors in response_schema_errors if not response_errors
        ),
        "n_response_schema_invalid": sum(
            1 for response_errors in response_schema_errors if response_errors
        ),
        "n_rows": len(rows),
        "n_response_present": sum(1 for row in rows if row.response_present),
        "n_provider_failures": sum(1 for row in rows if row.provider_failure),
        "n_rows_with_generator_metadata": sum(
            1 for row in rows if row.generator_metadata
        ),
        "n_rows_with_generation_errors": sum(
            1 for row in rows if row.generation_errors
        ),
        "n_awaiting_llm_response": by_acceptance_status.get(
            "AWAITING_LLM_ROUTE_PLANNER_RESPONSE",
            0,
        ),
        "n_response_contract_ok": sum(1 for row in rows if row.response_contract_ok),
        "n_accepted_route_plans": sum(
            1 for row in rows if row.acceptance_status.startswith("ACCEPTED_")
        ),
        "n_route_adoption_ready": by_route_adoption_status.get(
            ROUTE_ADOPTION_READY_STATUS,
            0,
        ),
        "n_route_adoption_pending_refinement": by_route_adoption_status.get(
            ROUTE_ADOPTION_PENDING_STATUS,
            0,
        ),
        "n_route_adoption_awaiting_llm_response": by_route_adoption_status.get(
            ROUTE_ADOPTION_AWAITING_STATUS,
            0,
        ),
        "n_route_adoption_rejected": by_route_adoption_status.get(
            ROUTE_ADOPTION_REJECTED_STATUS,
            0,
        ),
        "route_adoption_blocker_taxonomy_id": ROUTE_ADOPTION_BLOCKER_TAXONOMY_ID,
        "route_adoption_blocker_values": list(ROUTE_ADOPTION_BLOCKER_VALUES),
        "by_route_adoption_status": dict(sorted(by_route_adoption_status.items())),
        "n_route_adoption_pending_search_request_blockers": sum(
            1
            for row in rows
            if ROUTE_ADOPTION_BLOCKER_SEARCH_REQUESTS in row.route_adoption_blockers
        ),
        "n_route_adoption_pending_planner_next_action_blockers": sum(
            1
            for row in rows
            if ROUTE_ADOPTION_BLOCKER_PLANNER_NEXT_ACTIONS
            in row.route_adoption_blockers
        ),
        "n_route_adoption_pending_uncertainty_blockers": sum(
            1
            for row in rows
            if ROUTE_ADOPTION_BLOCKER_UNCERTAINTY_FLAGS
            in row.route_adoption_blockers
        ),
        "n_route_adoption_pending_residual_repair_blockers": sum(
            1
            for row in rows
            if ROUTE_ADOPTION_BLOCKER_RESIDUAL_INTERPRETATIONS
            in row.route_adoption_blockers
        ),
        "n_route_adoption_pending_feedback_action_blockers": sum(
            1
            for row in rows
            if ROUTE_ADOPTION_BLOCKER_FEEDBACK_ACTIONS in row.route_adoption_blockers
        ),
        "n_route_adoption_pending_resource_playbook_redispatch_blockers": sum(
            1
            for row in rows
            if ROUTE_ADOPTION_BLOCKER_RESOURCE_PLAYBOOK_REDISPATCH
            in row.route_adoption_blockers
        ),
        "n_route_adoption_pending_resource_request_queue_blockers": sum(
            1
            for row in rows
            if ROUTE_ADOPTION_BLOCKER_RESOURCE_REQUEST_QUEUE
            in row.route_adoption_blockers
        ),
        "n_route_adoption_pending_feedback_replan_blockers": sum(
            1
            for row in rows
            if ROUTE_ADOPTION_BLOCKER_FEEDBACK_REPLAN in row.route_adoption_blockers
        ),
        "n_route_adoption_pending_realization_coverage_blockers": sum(
            1
            for row in rows
            if ROUTE_ADOPTION_BLOCKER_REALIZATION_COVERAGE
            in row.route_adoption_blockers
        ),
        "n_rejected": sum(
            count
            for status, count in by_acceptance_status.items()
            if status.startswith("REJECTED_")
        ),
        "n_informal_knowledge_dag_nodes": sum(
            len(row.informal_knowledge_dag_nodes) for row in rows
        ),
        "n_formal_realization_dag_nodes": sum(
            len(row.formal_realization_dag_nodes) for row in rows
        ),
        "n_lean_realization_dag_nodes": sum(
            len(row.lean_realization_dag_nodes) for row in rows
        ),
        "n_route_alignment_edges": sum(len(row.route_alignment_edges) for row in rows),
        "n_rows_with_realization_coverage_witness": sum(
            1 for row in rows if row.realization_coverage_witness
        ),
        "n_rows_with_complete_realization_coverage": sum(
            1
            for row in rows
            if bool(
                row.realization_coverage_witness.get(
                    "realization_coverage_complete",
                    False,
                )
            )
        ),
        "n_selected_primitives_missing_formal_realization": sum(
            len(
                _str_tuple(
                    row.realization_coverage_witness.get(
                        "selected_primitives_missing_formal_realization_node",
                        [],
                    )
                )
            )
            for row in rows
        ),
        "n_delta_primitives_missing_route_alignment": sum(
            len(
                _str_tuple(
                    row.realization_coverage_witness.get(
                        "delta_primitives_missing_route_alignment_edge",
                        [],
                    )
                )
            )
            for row in rows
        ),
        "n_search_requests": sum(len(row.search_requests) for row in rows),
        "n_planner_next_actions": sum(len(row.planner_next_actions) for row in rows),
        "n_rows_with_planner_next_actions": sum(
            1 for row in rows if row.planner_next_actions
        ),
        "n_uncertainty_flags": sum(len(row.uncertainty_flags) for row in rows),
        "n_residual_interpretations": sum(
            len(row.residual_interpretations) for row in rows
        ),
        "n_source_snippets": sum(len(row.source_snippets) for row in rows),
        "n_rows_with_source_snippets": sum(1 for row in rows if row.source_snippets),
        "n_rows_with_minimal_delta_rationale": sum(
            1
            for row in rows
            if str(row.minimal_delta_plan.get("minimality_rationale", "")).strip()
        ),
        "n_rows_with_minimal_delta_cost_witness": sum(
            1
            for row in rows
            if not _minimal_delta_cost_witness_errors(
                row.minimal_delta_plan,
                selected_primitives=_str_tuple(
                    row.minimal_delta_plan.get("selected_primitives", [])
                ),
            )
        ),
        "n_row_schema_valid": sum(
            1 for row_errors in row_schema_errors if not row_errors
        ),
        "n_row_schema_invalid": sum(
            1 for row_errors in row_schema_errors if row_errors
        ),
        "request_schema": request_schema,
        "response_payload_schema": response_payload_schema,
        "response_schema": response_schema,
        "row_schema": row_schema,
        "request_packets": request_packets,
        "rows": row_dicts,
        "standalone_seed": standalone_seed,
        "by_acceptance_status": dict(sorted(by_acceptance_status.items())),
        "all_ok": (
            not errors
            and bool(request_packets)
            and all(not request_errors for request_errors in request_schema_errors)
            and all(not response_errors for response_errors in response_schema_errors)
            and all(not row_errors for row_errors in row_schema_errors)
            and all(row.ok for row in rows)
        ),
        "errors": errors,
        "llm_route_planner_fingerprint": stable_hash([request_packets, row_dicts]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "LLM route-planner rows are planning proposals and not theorem proof evidence",
            "source-backed claims must still pass source-grounding audit before route adoption",
            "formal alignment hypotheses require library lookup and target-prover replay",
            "prompt-only runs stage the request packet but do not synthesize a new route",
            "component-resource registry context is tool-selection metadata, not evidence that any resource was called",
        ],
    }
    if out_dir is not None:
        _write_outputs(out_dir, payload)
    return payload


def validate_formalization_gap_planner_llm_route_planner_response_payloads(
    response_json: Path,
    out_dir: Path | None = None,
    *,
    request_context_json: Path | None = None,
) -> dict[str, object]:
    """Validate raw LLM route-planner payload JSON.

    This is the public, reusable validation surface for external prover
    integrations. Without ``request_context_json`` it performs schema-only
    validation. With a staged request packet, request JSONL, manifest, or route
    planner output directory, it also performs the same request-bound grounding
    and theorem/prover consistency checks used by the full route planner.
    """

    errors: list[str] = []
    response_inputs = _read_response_payload_validation_inputs(response_json, errors)
    request_contexts = _read_response_payload_validation_request_contexts(
        request_context_json,
        errors,
    )
    request_schema = llm_route_planner_request_json_schema()
    request_schema_errors_by_id = _request_context_schema_errors_by_id(
        request_contexts,
        request_schema,
    )
    response_payload_schema = llm_route_planner_response_payload_schema()
    validation_manifest_schema = (
        llm_route_planner_response_payload_validation_manifest_json_schema()
    )
    validation_row_schema = (
        llm_route_planner_response_payload_validation_row_json_schema()
    )
    rows: list[dict[str, object]] = []
    for index, response_input in enumerate(response_inputs):
        response = response_input["response"]
        payload = _response_payload(response)
        schema_errors = validate_llm_route_planner_response_payload(
            payload,
            response_payload_schema,
        )
        request_context, request_context_errors = (
            _response_payload_validation_request_context_for_response(
                response,
                payload_index=index,
                request_contexts=request_contexts,
            )
        )
        if request_context:
            request_id = str(request_context.get("request_id", ""))
            request_context_errors = [
                *request_schema_errors_by_id.get(request_id, []),
                *request_context_errors,
                *_response_contract_errors(payload, request_context),
            ]
            request_context_validation_mode = "request_bound"
            request_context_id = request_id
            request_context_route_id = str(request_context.get("route_id", ""))
        elif request_context_json is not None:
            request_context_validation_mode = "request_context_unmatched"
            request_context_id = ""
            request_context_route_id = ""
        else:
            request_context_validation_mode = "schema_only"
            request_context_id = ""
            request_context_route_id = ""
        row_errors = sorted(set([*schema_errors, *request_context_errors]))
        rows.append(
            {
                "validation_id": (
                    "formalization_gap_planner_llm_route_planner_response_payload_validation:"
                    + stable_hash([str(response_json), index, payload])[:20]
                ),
                "schema_version": (
                    FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SCHEMA_VERSION
                ),
                "payload_index": index,
                "input_path": str(response_json),
                "input_shape": str(response_input.get("input_shape", "")),
                "response_wrapper_present": bool(
                    response_input.get("response_wrapper_present", False)
                ),
                "request_id": str(response.get("request_id", "")),
                "route_id": str(response.get("route_id", "")),
                "payload_schema_id": LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID,
                "payload_fingerprint": stable_hash(payload),
                "request_context_path": (
                    str(request_context_json) if request_context_json is not None else ""
                ),
                "request_context_validation_mode": request_context_validation_mode,
                "request_context_id": request_context_id,
                "request_context_route_id": request_context_route_id,
                "n_schema_errors": len(schema_errors),
                "n_request_context_errors": len(request_context_errors),
                "n_errors": len(row_errors),
                "ok": not row_errors,
                "errors": row_errors,
                "proof_evidence_status": PROOF_EVIDENCE_STATUS,
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            }
        )
    n_valid = sum(1 for row in rows if row["ok"])
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATOR_COMPONENT,
        "input_path": str(response_json),
        "request_context_path": (
            str(request_context_json) if request_context_json is not None else ""
        ),
        "response_payload_schema_id": LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID,
        "response_payload_validation_manifest_schema_id": (
            LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID
        ),
        "response_payload_validation_row_schema_id": (
            LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID
        ),
        "response_payload_schema": response_payload_schema,
        "response_payload_validation_manifest_schema": validation_manifest_schema,
        "response_payload_validation_row_schema": validation_row_schema,
        "n_payloads": len(rows),
        "n_valid_payloads": n_valid,
        "n_invalid_payloads": len(rows) - n_valid,
        "n_request_context_packets": len(request_contexts),
        "n_request_bound_payloads": sum(
            1
            for row in rows
            if row["request_context_validation_mode"] == "request_bound"
        ),
        "n_schema_errors": sum(int(row["n_schema_errors"]) for row in rows),
        "n_request_context_errors": sum(
            int(row["n_request_context_errors"]) for row in rows
        ),
        "rows": rows,
        "all_ok": not errors and bool(rows) and all(bool(row["ok"]) for row in rows),
        "errors": errors,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "Schema-only payload validation does not prove source grounding.",
            "Schema-only payload validation does not prove formal-library declaration provenance.",
            "Schema-only payload validation does not prove target-prover kernel verification.",
            "Request-bound payload validation is still planning preflight, not theorem proof evidence.",
            "Use the full LLM route planner or a target prover kernel for route adoption and proof evidence.",
        ],
    }
    if out_dir is not None:
        _write_response_payload_validation_outputs(out_dir, payload)
    return payload


def llm_route_planner_request_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": LLM_ROUTE_PLANNER_REQUEST_SCHEMA_ID,
        "title": "Formalization Gap Planner LLM Route Planner Request",
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "request_id",
            "route_id",
            "display_name",
            "provider_name",
            "model_tier",
            "model_selection_rationale",
            "target_prover_family",
            "library_snapshot_ref",
            "target_route",
            "context_packet",
            "minimal_delta_cost_policy",
            "required_output_contract",
            "prompt_messages",
            "proof_evidence_status",
            "proof_evidence_boundary",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SCHEMA_VERSION,
            },
            "request_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "provider_name": {"type": "string", "minLength": 1},
            "model": {"type": "string"},
            "model_tier": {"type": "string", "enum": ["haiku", "sonnet", "opus"]},
            "model_selection_rationale": {"type": "string", "minLength": 1},
            "target_prover_family": {"type": "string", "minLength": 1},
            "library_snapshot_ref": {"type": "string", "minLength": 1},
            "target_route": {"type": "object"},
            "context_packet": {"type": "object"},
            "minimal_delta_cost_policy": {"type": "object"},
            "residual_goals": string_array,
            "required_output_contract": {"type": "object"},
            "prompt_messages": {"type": "object"},
            "proof_evidence_status": {"type": "string", "const": PROOF_EVIDENCE_STATUS},
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
        },
    }


def llm_route_planner_response_json_schema() -> dict[str, object]:
    response_payload_schema = llm_route_planner_response_payload_schema()
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": LLM_ROUTE_PLANNER_RESPONSE_SCHEMA_ID,
        "title": "Formalization Gap Planner LLM Route Planner Response",
        "type": "object",
        "additionalProperties": True,
        "required": ["response_payload", "proof_evidence_boundary"],
        "properties": {
            "request_id": {"type": "string"},
            "route_id": {"type": "string"},
            "provider_name": {"type": "string"},
            "model": {"type": "string"},
            "response_payload": {"$ref": "#/$defs/response_payload"},
            "kernel_verified": {"type": "boolean", "const": False},
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
        },
        "$defs": {"response_payload": response_payload_schema},
    }


def llm_route_planner_row_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    object_array = {"type": "array", "items": {"type": "object"}}
    witness_array = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": LLM_ROUTE_PLANNER_ROW_SCHEMA_ID,
        "title": "Formalization Gap Planner LLM Route Planner Row",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "llm_route_planner_row_id",
            "request_id",
            "route_id",
            "display_name",
            "provider_name",
            "model",
            "model_tier",
            "model_selection_rationale",
            "target_prover_family",
            "library_snapshot_ref",
            "prompt_fingerprint",
            "response_present",
            "response_contract_ok",
            "informal_knowledge_dag_nodes",
            "formal_realization_dag_nodes",
            "route_alignment_edges",
            "minimal_delta_plan",
            "residual_interpretations",
            "search_requests",
            "uncertainty_flags",
            "semantic_alignment_risks",
            "planner_next_actions",
            "standalone_route",
            "source_refs",
            "source_snippets",
            "realization_coverage_witness",
            "raw_response_text",
            "generator_metadata",
            "provider_failure",
            "repair_attempts",
            "repair_error_history",
            "generation_errors",
            "acceptance_status",
            "route_adoption_status",
            "route_adoption_blockers",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "ok",
            "errors",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SCHEMA_VERSION,
            },
            "llm_route_planner_row_id": {"type": "string", "minLength": 1},
            "request_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "provider_name": {"type": "string", "minLength": 1},
            "model": {"type": "string"},
            "model_tier": {"type": "string", "enum": ["haiku", "sonnet", "opus"]},
            "model_selection_rationale": {"type": "string", "minLength": 1},
            "target_prover_family": {"type": "string", "minLength": 1},
            "library_snapshot_ref": {"type": "string", "minLength": 1},
            "prompt_fingerprint": {"type": "string", "minLength": 1},
            "response_present": {"type": "boolean"},
            "response_contract_ok": {"type": "boolean"},
            "informal_knowledge_dag_nodes": object_array,
            "formal_realization_dag_nodes": object_array,
            "lean_realization_dag_nodes": object_array,
            "route_alignment_edges": object_array,
            "minimal_delta_plan": {"type": "object"},
            "residual_interpretations": object_array,
            "search_requests": object_array,
            "uncertainty_flags": string_array,
            "semantic_alignment_risks": string_array,
            "planner_next_actions": object_array,
            "standalone_route": {"type": "object"},
            "source_refs": string_array,
            "source_snippets": object_array,
            "realization_coverage_witness": {
                "$ref": "#/$defs/realization_coverage_witness"
            },
            "raw_response_text": {"type": "string"},
            "generator_metadata": {"type": "object"},
            "provider_failure": {"type": "boolean"},
            "repair_attempts": {"type": "integer", "minimum": 0},
            "repair_error_history": object_array,
            "generation_errors": string_array,
            "acceptance_status": {"type": "string", "minLength": 1},
            "route_adoption_status": {
                "type": "string",
                "enum": list(ROUTE_ADOPTION_STATUSES),
            },
            "route_adoption_blockers": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": list(ROUTE_ADOPTION_BLOCKER_VALUES),
                },
            },
            "proof_evidence_status": {"type": "string", "const": PROOF_EVIDENCE_STATUS},
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
            "ok": {"type": "boolean"},
            "errors": string_array,
        },
        "$defs": {
            "realization_coverage_witness": {
                "type": "object",
                "additionalProperties": True,
                "required": [
                    "selected_primitives",
                    "delta_primitives",
                    "introduced_primitives",
                    "aligned_primitives",
                    "selected_primitives_with_standalone_route_node",
                    "selected_primitives_missing_standalone_route_node",
                    "selected_primitives_with_formal_realization_node",
                    "selected_primitives_missing_formal_realization_node",
                    "delta_primitives_with_route_alignment_edge",
                    "delta_primitives_missing_route_alignment_edge",
                    "introduced_primitives_with_route_alignment_edge",
                    "introduced_primitives_missing_route_alignment_edge",
                    "selected_route_coverage_complete",
                    "selected_formal_coverage_complete",
                    "delta_alignment_complete",
                    "introduced_alignment_complete",
                    "realization_coverage_complete",
                ],
                "properties": {
                    "selected_primitives": witness_array,
                    "delta_primitives": witness_array,
                    "introduced_primitives": witness_array,
                    "aligned_primitives": witness_array,
                    "selected_primitives_with_standalone_route_node": witness_array,
                    "selected_primitives_missing_standalone_route_node": witness_array,
                    "selected_primitives_with_formal_realization_node": witness_array,
                    "selected_primitives_missing_formal_realization_node": witness_array,
                    "delta_primitives_with_route_alignment_edge": witness_array,
                    "delta_primitives_missing_route_alignment_edge": witness_array,
                    "introduced_primitives_with_route_alignment_edge": witness_array,
                    "introduced_primitives_missing_route_alignment_edge": witness_array,
                    "selected_route_coverage_complete": {"type": "boolean"},
                    "selected_formal_coverage_complete": {"type": "boolean"},
                    "delta_alignment_complete": {"type": "boolean"},
                    "introduced_alignment_complete": {"type": "boolean"},
                    "realization_coverage_complete": {"type": "boolean"},
                },
            }
        },
    }


def route_adoption_blocker_taxonomy_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID,
        "title": "Formalization Gap Planner Route Adoption Blocker Taxonomy",
        "description": (
            "Portable vocabulary for explaining why an LLM route-planner row "
            "is not yet ready for standalone route replay."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "schema_id",
            "component_name",
            "taxonomy_id",
            "status_values",
            "blocker_values",
            "blocker_definitions",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "all_ok",
            "errors",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SCHEMA_VERSION,
            },
            "schema_id": {"const": ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID},
            "component_name": {"const": ROUTE_ADOPTION_BLOCKER_TAXONOMY_COMPONENT},
            "taxonomy_id": {"const": ROUTE_ADOPTION_BLOCKER_TAXONOMY_ID},
            "status_values": {
                "type": "array",
                "items": {"type": "string", "enum": list(ROUTE_ADOPTION_STATUSES)},
            },
            "blocker_values": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": list(ROUTE_ADOPTION_BLOCKER_VALUES),
                },
            },
            "blocker_definitions": {
                "type": "object",
                "additionalProperties": {"type": "string"},
            },
            "proof_evidence_status": {"const": PROOF_EVIDENCE_STATUS},
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
            "all_ok": {"type": "boolean"},
            "errors": string_array,
        },
    }


def route_adoption_blocker_taxonomy_payload() -> dict[str, object]:
    return {
        "schema_version": FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SCHEMA_VERSION,
        "schema_id": ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID,
        "component_name": ROUTE_ADOPTION_BLOCKER_TAXONOMY_COMPONENT,
        "taxonomy_id": ROUTE_ADOPTION_BLOCKER_TAXONOMY_ID,
        "status_values": list(ROUTE_ADOPTION_STATUSES),
        "blocker_values": list(ROUTE_ADOPTION_BLOCKER_VALUES),
        "blocker_definitions": dict(ROUTE_ADOPTION_BLOCKER_DEFINITIONS),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": (
            "Route-adoption blocker taxonomy artifacts define reusable planner "
            "readiness vocabulary only. They are not theorem proof evidence."
        ),
        "all_ok": True,
        "errors": [],
    }


def validate_route_adoption_blocker_taxonomy_payload(
    payload: Mapping[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    required = route_adoption_blocker_taxonomy_json_schema().get("required", [])
    if isinstance(required, list):
        for field_name in required:
            if isinstance(field_name, str) and field_name not in payload:
                errors.append(f"{field_name} required")
    if payload.get("schema_version") != (
        FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SCHEMA_VERSION
    ):
        errors.append("schema_version mismatch")
    if payload.get("schema_id") != ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID:
        errors.append("schema_id mismatch")
    if payload.get("component_name") != ROUTE_ADOPTION_BLOCKER_TAXONOMY_COMPONENT:
        errors.append("component_name mismatch")
    if payload.get("taxonomy_id") != ROUTE_ADOPTION_BLOCKER_TAXONOMY_ID:
        errors.append("taxonomy_id mismatch")
    if _str_tuple(payload.get("status_values", [])) != ROUTE_ADOPTION_STATUSES:
        errors.append("status_values must match route adoption status constants")
    if _str_tuple(payload.get("blocker_values", [])) != ROUTE_ADOPTION_BLOCKER_VALUES:
        errors.append("blocker_values must match route adoption blocker constants")
    definitions = payload.get("blocker_definitions", {})
    if not isinstance(definitions, Mapping):
        errors.append("blocker_definitions must be object")
    else:
        definition_keys = tuple(str(key) for key in definitions.keys())
        if set(definition_keys) != set(ROUTE_ADOPTION_BLOCKER_VALUES):
            errors.append("blocker_definitions keys must match blocker_values")
        empty_definitions = [
            key
            for key, value in definitions.items()
            if not isinstance(value, str) or not value.strip()
        ]
        if empty_definitions:
            errors.append(
                "blocker_definitions must be non-empty strings for: "
                + ", ".join(sorted(str(key) for key in empty_definitions))
            )
    if payload.get("proof_evidence_status") != PROOF_EVIDENCE_STATUS:
        errors.append("proof_evidence_status mismatch")
    if "not theorem proof evidence" not in str(
        payload.get("proof_evidence_boundary", "")
    ).lower():
        errors.append("proof_evidence_boundary must say not theorem proof evidence")
    payload_errors = payload.get("errors", [])
    if payload.get("all_ok") is True and payload_errors not in ([], (), None):
        errors.append("all_ok taxonomy payload must not carry errors")
    if payload.get("all_ok") is False and not payload_errors:
        errors.append("non-ok taxonomy payload must carry errors")
    return tuple(errors)


def validate_llm_route_planner_request(
    row: Mapping[str, object],
    schema: Mapping[str, object] | None = None,
) -> list[str]:
    errors = _validate_with_schema(row, schema or llm_route_planner_request_json_schema())
    provider = str(row.get("provider_name", "") or "").strip().lower()
    if provider and provider not in LLM_ROUTE_PLANNER_PROVIDER_NAMES:
        errors.append(
            "provider_name must be one of "
            + ", ".join(LLM_ROUTE_PLANNER_PROVIDER_NAMES)
        )
    prompt = row.get("prompt_messages", {})
    if not isinstance(prompt, Mapping):
        errors.append("prompt_messages must be object")
    else:
        if not str(prompt.get("system", "")).strip():
            errors.append("prompt_messages.system missing")
        if not str(prompt.get("user", "")).strip():
            errors.append("prompt_messages.user missing")
    if row.get("required_output_contract") in ({}, None):
        errors.append("required_output_contract missing")
    cost_policy = row.get("minimal_delta_cost_policy", {})
    if not isinstance(cost_policy, Mapping):
        errors.append("minimal_delta_cost_policy must be object")
    elif str(cost_policy.get("cost_policy_id", "")).strip() != MINIMAL_DELTA_COST_POLICY_ID:
        errors.append(
            "minimal_delta_cost_policy.cost_policy_id must equal "
            + MINIMAL_DELTA_COST_POLICY_ID
        )
    if str(row.get("provider_name", "") or "").strip().lower() == "anthropic":
        mismatch = _request_model_tier_mismatch(row)
        if mismatch:
            errors.append(str(mismatch["error"]))
    return sorted(set(errors))


def validate_llm_route_planner_response(
    row: Mapping[str, object],
    schema: Mapping[str, object] | None = None,
) -> list[str]:
    errors = _validate_with_schema(row, schema or llm_route_planner_response_json_schema())
    if bool(row.get("kernel_verified", False)):
        errors.append("LLM response cannot claim kernel_verified=true")
    payload = row.get("response_payload", {})
    if isinstance(payload, Mapping) and bool(payload.get("kernel_verified", False)):
        errors.append("LLM response payload cannot claim kernel_verified=true")
    if isinstance(payload, Mapping) and not bool(row.get("provider_failure", False)):
        errors.extend(validate_llm_route_planner_response_payload(payload))
    return sorted(set(errors))


def validate_llm_route_planner_response_payload(
    payload: Mapping[str, object],
    schema: Mapping[str, object] | None = None,
) -> list[str]:
    """Validate the reusable raw LLM route-planner response payload contract."""

    errors = _validate_with_schema_deep(
        payload,
        schema or llm_route_planner_response_payload_schema(),
        path="response_payload",
    )
    if bool(payload.get("kernel_verified", False)):
        errors.append("response_payload cannot claim kernel_verified=true")
    errors.extend(_response_payload_realization_field_contract_errors(payload))
    return sorted(set(errors))


def validate_llm_route_planner_response_payload_validation_manifest(
    manifest: Mapping[str, object],
    schema: Mapping[str, object] | None = None,
) -> list[str]:
    """Validate the reusable response-payload validation manifest contract."""

    return _validate_with_schema(
        manifest,
        schema or llm_route_planner_response_payload_validation_manifest_json_schema(),
    )


def validate_llm_route_planner_response_payload_validation_row(
    row: Mapping[str, object],
    schema: Mapping[str, object] | None = None,
) -> list[str]:
    """Validate a response-payload validation JSONL row."""

    return _validate_with_schema(
        row,
        schema or llm_route_planner_response_payload_validation_row_json_schema(),
    )


def validate_llm_route_planner_row(
    row: Mapping[str, object],
    schema: Mapping[str, object] | None = None,
) -> list[str]:
    errors = _validate_with_schema(row, schema or llm_route_planner_row_json_schema())
    model_tier_mismatch = _row_model_tier_mismatch_error(row)
    if model_tier_mismatch:
        errors.append(model_tier_mismatch)
    if int(row.get("repair_attempts", 0) or 0) < len(
        _dict_tuple(row.get("repair_error_history", []))
    ):
        errors.append("repair_attempts cannot be smaller than repair_error_history length")
    if row.get("response_contract_ok") and _str_tuple(row.get("generation_errors", [])):
        errors.append("accepted response cannot retain generation_errors")
    if row.get("response_present") and not row.get("response_contract_ok"):
        if not str(row.get("acceptance_status", "")).startswith("REJECTED_"):
            errors.append("present non-contract response must be rejected")
    if row.get("response_contract_ok") and not row.get("standalone_route"):
        errors.append("accepted response must include standalone_route")
    if row.get("provider_failure"):
        if not _str_tuple(row.get("generation_errors", [])):
            errors.append("provider_failure row must include generation_errors")
        if not str(row.get("acceptance_status", "")).startswith(
            "REJECTED_LLM_ROUTE_PLANNER_PROVIDER_FAILURE"
        ):
            errors.append(
                "provider_failure row must use REJECTED_LLM_ROUTE_PLANNER_PROVIDER_FAILURE"
            )
    if row.get("response_contract_ok"):
        witness = _dict_value(row, "realization_coverage_witness")
        if not bool(witness.get("realization_coverage_complete", False)):
            errors.append(
                "accepted response must include complete realization_coverage_witness"
            )
    return sorted(set(errors))


def _request_packet(
    input_payload: Mapping[str, Any],
    route: Mapping[str, Any],
    *,
    route_index: int,
    provider_name: str,
    model: str,
    model_tier: str,
    context_payloads: Mapping[str, Any],
) -> dict[str, Any]:
    route_id = str(
        route.get("route_id")
        or route.get("target_theorem_id")
        or route.get("display_name")
        or f"route_{route_index}"
    )
    display_name = str(route.get("display_name") or route_id)
    route_match_ids = _route_match_ids(route, route_id)
    target_prover_family = _route_target_prover_family(input_payload, route)
    library_snapshot_ref = str(
        route.get("library_snapshot_ref") or input_payload.get("library_snapshot_ref", "")
    )
    residual_goals = _residual_goals_for_route(route_match_ids, context_payloads)
    context_packet = {
        "standalone_input_component": str(input_payload.get("component_name", "")),
        "target_prover_family": target_prover_family,
        "library_snapshot_ref": library_snapshot_ref,
        "current_route": dict(route),
        "route_match_ids": route_match_ids,
        "replan_metadata": _dict_value(route, "replan_metadata"),
        "target_intake_rows": _rows_for_route(
            context_payloads.get("target_intake", {}),
            route_match_ids,
        ),
        "library_coverage_rows": _rows_for_route(
            context_payloads.get("library_coverage_map", {}),
            route_match_ids,
        ),
        "source_grounding_rows": _rows_for_route(
            context_payloads.get("source_grounding_audit", {}),
            route_match_ids,
        ),
        "resource_request_queue_rows": _rows_for_route(
            context_payloads.get("resource_request_queue", {}),
            route_match_ids,
        ),
        "resource_response_ledger_rows": _rows_for_route(
            context_payloads.get("resource_response_ledger", {}),
            route_match_ids,
        ),
        "refinement_evidence_rows": _rows_for_route(
            context_payloads.get("refinement_evidence", {}),
            route_match_ids,
        ),
        "route_revision_overlay_rows": _rows_for_route(
            context_payloads.get("route_revision_overlay", {}),
            route_match_ids,
        ),
        "interactive_session_rows": _rows_for_route(
            context_payloads.get("interactive_session", {}),
            route_match_ids,
        ),
        "interactive_decision_policy_rows": _rows_for_route(
            context_payloads.get("interactive_session", {}),
            route_match_ids,
            row_key="decision_policy_rows",
        ),
        "current_goal_plan_rows": _rows_for_route(
            context_payloads.get("goal_plan", {}),
            route_match_ids,
        ),
        "component_resource_registry_context": _component_resource_registry_context(
            context_payloads.get("component_resource_registry", {}),
            target_prover_family=target_prover_family,
        ),
        "residual_goals": residual_goals,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }
    context_packet["resource_request_playbooks"] = [
        dict(row) for row in _resource_request_playbooks_for_context(context_packet)
    ]
    context_packet["available_source_refs"] = list(
        _available_source_refs_for_context(route, context_packet)
    )
    context_packet["available_source_snippets"] = list(
        _available_source_snippets_for_context(route, context_packet)
    )
    formal_declaration_rows = _available_formal_declaration_rows_for_context(
        route,
        context_packet,
        target_prover_family=target_prover_family,
    )
    context_packet["available_formal_declaration_rows"] = [
        dict(row) for row in formal_declaration_rows
    ]
    context_packet["available_formal_declarations"] = [
        str(row.get("declaration", ""))
        for row in _target_compatible_formal_declaration_rows(
            formal_declaration_rows,
            target_prover_family=target_prover_family,
        )
        if str(row.get("declaration", "")).strip()
    ]
    context_packet["feedback_loop_summary"] = _feedback_loop_summary(
        context_packet,
        residual_goals=residual_goals,
    )
    selected_model_tier, model_selection_rationale = (
        _llm_route_planner_model_tier_decision(
            route,
            context_packet,
            requested_model_tier=model_tier,
        )
    )
    resolved_model = _model_for_provider_tier(
        provider_name,
        requested_model=model,
        model_tier=selected_model_tier,
    )
    request_id = "formalization_gap_planner_llm_route_request:" + stable_hash(
        [route_id, display_name, target_prover_family, library_snapshot_ref, context_packet]
    )[:20]
    prompt_messages = {
        "system": SYSTEM_PROMPT,
        "user": _user_prompt(
            target_route=route,
            context_packet=context_packet,
            required_output_contract=LLM_ROUTE_PLANNER_OUTPUT_CONTRACT,
        ),
    }
    return {
        "schema_version": FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SCHEMA_VERSION,
        "request_id": request_id,
        "route_id": route_id,
        "display_name": display_name,
        "provider_name": provider_name,
        "model": resolved_model,
        "model_tier": selected_model_tier,
        "model_selection_rationale": model_selection_rationale,
        "target_prover_family": target_prover_family,
        "library_snapshot_ref": library_snapshot_ref,
        "target_route": dict(route),
        "context_packet": context_packet,
        "residual_goals": residual_goals,
        "minimal_delta_cost_policy": MINIMAL_DELTA_COST_POLICY,
        "required_output_contract": LLM_ROUTE_PLANNER_OUTPUT_CONTRACT,
        "prompt_messages": prompt_messages,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "prompt_fingerprint": stable_hash(prompt_messages),
    }


def _user_prompt(
    *,
    target_route: Mapping[str, Any],
    context_packet: Mapping[str, Any],
    required_output_contract: Mapping[str, Any],
) -> str:
    payload = {
        "task": (
            "Synthesize or revise a library-aware formalization proof route. "
            "Use sources, current formal-library coverage, and prover residuals. "
            "Choose the minimal additional formalization delta."
        ),
        "target_route": dict(target_route),
        "context_packet": dict(context_packet),
        "minimal_delta_cost_policy": dict(MINIMAL_DELTA_COST_POLICY),
        "required_output_contract": dict(required_output_contract),
        "hard_requirements": [
            "Return only JSON.",
            "When context_packet.target_intake_rows is present, use its normalized_objects, normalized_assumptions, normalized_procedure, normalized_claim, desired_theorem_shape, literature_queries, and formal_library_grounding_queries as the target theorem context for route synthesis; lean_grounding_queries is a legacy alias only; target intake is not proof evidence.",
            "standalone_route.theorem_statement must preserve the requested target theorem identity; route repairs may add explicit side-condition notes but must not switch to a different theorem.",
            "Every informal DAG node must have source_refs, a source_search_status, or a formal_gap_boundary.",
            "SOURCE_BACKED claims may cite only source_refs listed in context_packet.available_source_refs.",
            "When context_packet.available_source_snippets contains relevant excerpts, reuse those source_snippets in informal DAG nodes or standalone_route primitives instead of paraphrasing unsupported evidence.",
            "source_snippets may cite only source_refs listed in context_packet.available_source_refs.",
            "If a needed source is not listed, emit a literature search_request instead of inventing a source_ref.",
            "Any informal node or standalone primitive with SEARCH_REQUESTED/source_search_pending status must have a matching literature/source search_request.",
            "Existing-library or reuse claims may cite only candidate_declarations or candidate_declaration_rows listed in context_packet.available_formal_declarations/available_formal_declaration_rows.",
            "Prefer candidate_declaration_rows over bare candidate_declarations so target_prover_family provenance is preserved.",
            "If a needed declaration is not listed, emit a formal_library search_request instead of inventing a candidate_declaration.",
            "Any formal-realization node or standalone primitive with unknown/formal-library-search-pending coverage must have a matching formal_library/library search_request unless it declares a formal gap boundary or concrete delta action.",
            "Every search_requests row must use a supported request_kind, include a nonempty query, and include a nonempty reason.",
            "Every planner_next_actions row must include owner and action, and the row must resolve to a supported literature/formal-library/proof-state/route-revision hook family.",
            "Use context_packet.component_resource_registry_context only to choose bounded search/prover next actions; registry rows are not evidence that a tool was called.",
            "When context_packet.feedback_loop_summary is present, treat it as the route-repair brief derived from raw residual/resource/interactive rows; it is planning context, not proof evidence.",
            "Resource-response ledger rows with awaiting, rejected, absent-response, failed-contract, or unmet-contract-minimum status are status-only; do not use them as residual-goal or route-repair evidence.",
            "Residual interpretations may cover only residual_goals listed in the request packet.",
            "If request residual_goals are present, every residual goal must have an interpretation and a route_repair or repair_action.",
            "Every residual_interpretations row that proposes route repair must have source_refs/source_snippets, a matching literature/source search_request, or a formal_gap_boundary; prover residuals alone are not source evidence for new mathematical side conditions.",
            "Every alignment edge must include an alignment_rationale.",
            "Every alignment edge informal_node_id/formal_node_id must reference nodes present in the returned informal and formal DAGs.",
            "Use formal_realization_dag_nodes for all target provers; lean_realization_dag_nodes is accepted only as a Lean legacy alias and must not be used for non-Lean target_prover_family values.",
            "Minimal delta must include selected_primitives, cost_model_version, route_cost, primitive_costs, and_or_cost_graph, and minimality_rationale.",
            "Use minimal_delta_cost_policy as the AND/OR graph cost surface; pick the route with the lowest current formalization delta cost.",
            "Every selected primitive must have exactly one primitive_costs row with base_cost, proof_difficulty_cost, import_cone_cost, definition_or_typeclass_cost, semantic_risk_cost, reuse_credit, total_cost, and cost_rationale.",
            "Every primitive_costs coverage_bucket must be listed in minimal_delta_cost_policy.coverage_bucket_base_cost, and base_cost must equal that bucket base cost.",
            "A primitive_costs coverage_bucket/base_cost must not be cheaper than the explicit coverage_bucket, coverage_status, or formalization_action markers on the corresponding formal_realization_dag_nodes or standalone_route.primitives.",
            "Every primitive_costs row must satisfy total_cost = base_cost + proof_difficulty_cost + import_cone_cost + definition_or_typeclass_cost + semantic_risk_cost - reuse_credit; route_cost must equal the sum of selected primitive total_cost values.",
            "and_or_cost_graph must enumerate route_options, non-empty or_nodes, and non-empty and_edges; it must mark exactly one selected route option and no listed alternative may have lower route_cost.",
            "Every selected primitive must appear in standalone_route.primitives and formal_realization_dag_nodes.",
            "Every wrapper, bridge, source-port, new-definition, or first-principles delta primitive must have a route_alignment_edge.",
            "New selected or delta primitives not already present in the target route or context packet must be justified by an aligned informal node with grounded source_refs, a matching literature search_request, or a formal_gap_boundary.",
            "When context_packet.resource_request_queue_rows is present, evidence-gathering search_requests and planner_next_actions should reference queued resource_request_id or resource_id entries instead of inventing new tool dispatches.",
            "When context_packet.resource_request_playbooks is present, use each playbook's operator_prompt, expected_response_fields, and acceptance_checklist as the bounded ask for search_requests and planner_next_actions.",
            "Do not claim kernel verification or theorem proof evidence.",
        ],
    }
    return json.dumps(payload, indent=2, default=str)


def _generate_responses(
    requests: tuple[dict[str, Any], ...],
    *,
    generator_backend: GeneratorBackend,
    model: str,
    max_tokens: int,
    temperature: float,
    max_repair_attempts: int,
    errors: list[str],
) -> list[dict[str, Any]]:
    responses: list[dict[str, Any]] = []
    repair_budget = max(0, int(max_repair_attempts))
    for packet in requests:
        prompt = packet.get("prompt_messages", {})
        if not isinstance(prompt, Mapping):
            errors.append(
                f"cannot generate response for malformed prompt: {packet.get('request_id', '')}"
            )
            continue
        user_prompt = str(prompt.get("user", ""))
        repair_history: list[dict[str, object]] = []
        last_response: dict[str, Any] | None = None
        last_generated: Any | None = None
        for attempt in range(repair_budget + 1):
            request_model = _generator_model_for_request(
                generator_backend,
                model or str(packet.get("model", "")),
                model_tier=str(packet.get("model_tier", "")),
            )
            try:
                generated = generator_backend.generate(
                    GeneratorRequest(
                        system_prompt=str(prompt.get("system", "")),
                        user_prompt=user_prompt,
                        model=request_model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        schema=llm_route_planner_response_payload_schema(),
                        metadata={
                            "component": LLM_ROUTE_PLANNER_COMPONENT,
                            "request_id": str(packet.get("request_id", "")),
                            "model_tier": str(packet.get("model_tier", "")),
                            "model_selection_rationale": str(
                                packet.get("model_selection_rationale", "")
                            ),
                            "repair_attempt": attempt,
                            "max_repair_attempts": repair_budget,
                        },
                    )
                )
                last_generated = generated
                generation_errors: list[str] = []
                try:
                    payload = _extract_json_object(generated.text)
                except Exception as exc:
                    payload = {}
                    generation_errors.append(
                        f"JSON extraction failed: {type(exc).__name__}: {exc}"
                    )
                candidate = {
                    "request_id": str(packet.get("request_id", "")),
                    "route_id": str(packet.get("route_id", "")),
                    "provider_name": generated.provider,
                    "model": generated.model,
                    "response_payload": payload,
                    "raw_response_text": generated.text,
                    "generator_metadata": _jsonable_mapping(generated.metadata),
                    "provider_failure": False,
                    "kernel_verified": False,
                    "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
                    "repair_attempts": attempt,
                    "repair_error_history": tuple(repair_history),
                    "generation_errors": tuple(generation_errors),
                }
                validation_errors = [
                    *generation_errors,
                    *validate_llm_route_planner_response(candidate),
                    *_response_contract_errors(payload, packet),
                ]
                if not validation_errors:
                    last_response = candidate
                    break
                last_response = {
                    **candidate,
                    "generation_errors": tuple(sorted(set(validation_errors))),
                }
                repair_history.append(
                    {
                        "attempt": attempt,
                        "errors": tuple(sorted(set(validation_errors)))[:12],
                    }
                )
                if attempt >= repair_budget:
                    break
                user_prompt = _repair_user_prompt(
                    original_user_prompt=str(prompt.get("user", "")),
                    previous_response_text=generated.text,
                    validation_errors=validation_errors,
                    attempt=attempt + 1,
                )
            except Exception as exc:
                exception_text = f"{type(exc).__name__}: {exc}"
                if attempt >= repair_budget:
                    errors.append(
                        "LLM route planner provider failed for "
                        f"{packet.get('request_id', '')}: {exception_text}"
                    )
                    last_response = {
                        "request_id": str(packet.get("request_id", "")),
                        "route_id": str(packet.get("route_id", "")),
                        "provider_name": str(
                            getattr(generator_backend, "provider_name", "")
                        ),
                        "model": request_model,
                        "response_payload": {},
                        "raw_response_text": str(getattr(last_generated, "text", "")),
                        "generator_metadata": {
                            "generator_only": True,
                            "tools_available": False,
                            "provider_failure": True,
                            "exception_type": type(exc).__name__,
                            "exception_message": str(exc)[:1000],
                            "repair_attempt": attempt,
                        },
                        "provider_failure": True,
                        "kernel_verified": False,
                        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
                        "repair_attempts": attempt,
                        "repair_error_history": tuple(repair_history),
                        "generation_errors": (
                            "provider exception: " + exception_text,
                        ),
                    }
                    break
                provider_error = "provider exception: " + exception_text
                repair_history.append(
                    {
                        "attempt": attempt,
                        "errors": (provider_error,),
                    }
                )
                user_prompt = _repair_user_prompt(
                    original_user_prompt=str(prompt.get("user", "")),
                    previous_response_text=str(
                        getattr(last_generated, "text", "")
                    ),
                    validation_errors=[provider_error],
                    attempt=attempt + 1,
                )
        if last_response is not None:
            responses.append(last_response)
    return responses


def _jsonable_mapping(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    try:
        encoded = json.dumps(dict(value), default=str)
        decoded = json.loads(encoded)
    except Exception:
        return {str(key): str(item) for key, item in value.items()}
    return dict(decoded) if isinstance(decoded, Mapping) else {}


def _repair_user_prompt(
    *,
    original_user_prompt: str,
    previous_response_text: str,
    validation_errors: list[str],
    attempt: int,
) -> str:
    payload = {
        "task": (
            "Repair your previous formalization-gap planner response. Return "
            "only one JSON object that satisfies the required output contract."
        ),
        "repair_attempt": attempt,
        "local_validation_errors": sorted(set(validation_errors))[:20],
        "previous_response_text_excerpt": previous_response_text[:5000],
        "original_request": _extract_json_object_or_text(original_user_prompt),
        "hard_requirements": [
            "Return only JSON.",
            "Do not claim kernel verification or theorem proof evidence.",
            "Use only source_refs and candidate_declarations/candidate_declaration_rows available in the original request context.",
            "Prefer candidate_declaration_rows so target_prover_family provenance is preserved.",
            "If evidence is missing, emit search_requests instead of inventing facts.",
            "When the original request has resource_request_queue_rows, align search_requests and planner_next_actions to queued resource_request_id/resource_id values.",
            "When the original request has resource_request_playbooks, keep repaired search_requests and planner_next_actions aligned to those playbook operator prompts and acceptance checklists.",
            "Include a complete minimal_delta_plan with selected_primitives, primitive_costs, and and_or_cost_graph.",
        ],
    }
    return json.dumps(payload, indent=2, default=str)


def _extract_json_object_or_text(text: str) -> object:
    try:
        return _extract_json_object(text)
    except Exception:
        return text[:12000]


def llm_route_planner_response_payload_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    source_snippet = {
        "type": "object",
        "additionalProperties": True,
        "required": ["source_ref", "excerpt"],
        "properties": {
            "source_ref": {"type": "string", "minLength": 1},
            "source_refs": string_array,
            "claim": {"type": "string"},
            "excerpt": {"type": "string", "minLength": 1},
            "target_primitives": string_array,
        },
    }
    candidate_declaration_row = {
        "type": "object",
        "additionalProperties": True,
        "required": ["declaration", "target_prover_family", "source_field"],
        "properties": {
            "declaration": {"type": "string", "minLength": 1},
            "target_prover_family": {"type": "string", "minLength": 1},
            "source_field": {"type": "string", "minLength": 1},
        },
    }
    formal_realization_node = {
        "type": "object",
        "additionalProperties": True,
        "required": ["node_id", "primitive", "coverage_bucket", "formalization_action"],
        "properties": {
            "node_id": {"type": "string", "minLength": 1},
            "primitive": {"type": "string", "minLength": 1},
            "coverage_bucket": {"type": "string", "minLength": 1},
            "candidate_declarations": string_array,
            "candidate_declaration_rows": {
                "type": "array",
                "items": {"$ref": "#/$defs/candidate_declaration_row"},
            },
            "formalization_action": {"type": "string", "minLength": 1},
            "target_prover_family": {"type": "string"},
        },
    }
    primitive_cost = {
        "type": "object",
        "additionalProperties": True,
        "required": [
            "primitive",
            "coverage_bucket",
            "base_cost",
            "proof_difficulty_cost",
            "import_cone_cost",
            "definition_or_typeclass_cost",
            "semantic_risk_cost",
            "reuse_credit",
            "total_cost",
            "cost_rationale",
        ],
        "properties": {
            "primitive": {"type": "string", "minLength": 1},
            "coverage_bucket": {"type": "string", "minLength": 1},
            "base_cost": {"type": "number"},
            "proof_difficulty_cost": {"type": "number"},
            "import_cone_cost": {"type": "number"},
            "definition_or_typeclass_cost": {"type": "number"},
            "semantic_risk_cost": {"type": "number"},
            "reuse_credit": {"type": "number"},
            "total_cost": {"type": "number"},
            "cost_rationale": {"type": "string", "minLength": 1},
        },
    }
    route_option = {
        "type": "object",
        "additionalProperties": True,
        "required": [
            "route_option_id",
            "selected",
            "selected_primitives",
            "route_cost",
            "cost_rationale",
        ],
        "properties": {
            "route_option_id": {"type": "string", "minLength": 1},
            "selected": {"type": "boolean"},
            "selected_primitives": string_array,
            "route_cost": {"type": "number"},
            "cost_rationale": {"type": "string", "minLength": 1},
        },
    }
    and_or_cost_graph = {
        "type": "object",
        "additionalProperties": True,
        "required": [
            "graph_kind",
            "selected_route_option_id",
            "route_options",
            "or_nodes",
            "and_edges",
        ],
        "properties": {
            "graph_kind": {"type": "string", "const": "AND_OR_ROUTE_COST_GRAPH"},
            "selected_route_option_id": {"type": "string", "minLength": 1},
            "route_options": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/route_option"},
            },
            "or_nodes": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "additionalProperties": True,
                    "required": ["node_id", "choices", "selection_rationale"],
                    "properties": {
                        "node_id": {"type": "string", "minLength": 1},
                        "choices": string_array,
                        "selection_rationale": {"type": "string", "minLength": 1},
                    },
                },
            },
            "and_edges": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "additionalProperties": True,
                    "required": ["route_option_id", "requires"],
                    "properties": {
                        "route_option_id": {"type": "string", "minLength": 1},
                        "requires": string_array,
                    },
                },
            },
        },
    }
    minimal_delta_plan = {
        "type": "object",
        "additionalProperties": True,
        "required": [
            "selected_primitives",
            "cost_model_version",
            "route_cost",
            "primitive_costs",
            "and_or_cost_graph",
            "minimality_rationale",
        ],
        "properties": {
            "selected_primitives": string_array,
            "cost_model_version": {
                "type": "string",
                "const": MINIMAL_DELTA_COST_POLICY_ID,
            },
            "route_cost": {"type": "number"},
            "primitive_costs": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/primitive_cost"},
            },
            "and_or_cost_graph": {"$ref": "#/$defs/and_or_cost_graph"},
            "new_definitions": string_array,
            "wrapper_lemmas": string_array,
            "bridge_lemmas": string_array,
            "source_port_lemmas": string_array,
            "do_not_formalize_now": string_array,
            "minimality_rationale": {"type": "string", "minLength": 1},
        },
    }
    standalone_primitive = {
        "type": "object",
        "additionalProperties": True,
        "required": ["primitive", "coverage_status", "source_refs"],
        "properties": {
            "primitive": {"type": "string", "minLength": 1},
            "coverage_status": {"type": "string", "minLength": 1},
            "candidate_declarations": string_array,
            "candidate_declaration_rows": {
                "type": "array",
                "items": {"$ref": "#/$defs/candidate_declaration_row"},
            },
            "source_refs": string_array,
            "source_snippets": {
                "type": "array",
                "items": {"$ref": "#/$defs/source_snippet"},
            },
            "formal_gap_boundary": {"type": "string"},
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID,
        "title": "Formalization Gap Planner LLM Route Planner Response Payload",
        "type": "object",
        "additionalProperties": True,
        "required": [
            "informal_knowledge_dag_nodes",
            "route_alignment_edges",
            "minimal_delta_plan",
            "standalone_route",
            "proof_evidence_boundary",
        ],
        "anyOf": [
            {"required": ["formal_realization_dag_nodes"]},
            {"required": ["lean_realization_dag_nodes"]},
        ],
        "properties": {
            "informal_knowledge_dag_nodes": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "additionalProperties": True,
                    "required": [
                        "node_id",
                        "claim",
                        "depends_on",
                        "source_refs",
                        "source_search_status",
                    ],
                    "properties": {
                        "node_id": {"type": "string", "minLength": 1},
                        "claim": {"type": "string", "minLength": 1},
                        "depends_on": string_array,
                        "source_refs": string_array,
                        "source_snippets": {
                            "type": "array",
                            "items": {"$ref": "#/$defs/source_snippet"},
                        },
                        "source_search_status": {"type": "string", "minLength": 1},
                        "semantic_role": {"type": "string"},
                        "formal_gap_boundary": {"type": "string"},
                    },
                },
            },
            "formal_realization_dag_nodes": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/formal_realization_node"},
            },
            "lean_realization_dag_nodes": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/formal_realization_node"},
            },
            "route_alignment_edges": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "additionalProperties": True,
                    "required": [
                        "informal_node_id",
                        "formal_node_id",
                        "alignment_status",
                        "alignment_rationale",
                    ],
                    "properties": {
                        "informal_node_id": {"type": "string", "minLength": 1},
                        "formal_node_id": {"type": "string", "minLength": 1},
                        "alignment_status": {"type": "string", "minLength": 1},
                        "alignment_rationale": {"type": "string", "minLength": 1},
                    },
                },
            },
            "minimal_delta_plan": {"$ref": "#/$defs/minimal_delta_plan"},
            "residual_interpretations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": True,
                    "required": ["residual_goal", "interpretation"],
                    "properties": {
                        "residual_goal": {"type": "string", "minLength": 1},
                        "interpretation": {"type": "string", "minLength": 1},
                        "route_repair": {"type": "string"},
                        "repair_action": {"type": "string"},
                        "source_refs": string_array,
                        "source_snippets": {
                            "type": "array",
                            "items": {"$ref": "#/$defs/source_snippet"},
                        },
                        "source_search_status": {"type": "string", "minLength": 1},
                        "formal_gap_boundary": {"type": "string"},
                    },
                },
            },
            "search_requests": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": True,
                    "required": ["request_kind", "query", "reason"],
                    "properties": {
                        "request_kind": {"type": "string", "minLength": 1},
                        "query": {"type": "string", "minLength": 1},
                        "reason": {"type": "string", "minLength": 1},
                        "resource_request_id": {"type": "string"},
                        "resource_id": {"type": "string"},
                    },
                },
            },
            "uncertainty_flags": string_array,
            "semantic_alignment_risks": string_array,
            "planner_next_actions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": True,
                    "required": ["owner", "action"],
                    "properties": {
                        "owner": {"type": "string", "minLength": 1},
                        "action": {"type": "string", "minLength": 1},
                        "resource_request_id": {"type": "string"},
                        "resource_id": {"type": "string"},
                    },
                },
            },
            "standalone_route": {
                "type": "object",
                "additionalProperties": True,
                "required": [
                    "display_name",
                    "theorem_statement",
                    "source_refs",
                    "primitives",
                ],
                "properties": {
                    "route_id": {"type": "string"},
                    "display_name": {"type": "string", "minLength": 1},
                    "theorem_statement": {"type": "string", "minLength": 1},
                    "target_prover_family": {"type": "string"},
                    "source_refs": string_array,
                    "source_snippets": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/source_snippet"},
                    },
                    "primitives": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"$ref": "#/$defs/standalone_primitive"},
                    },
                },
            },
            "source_refs": string_array,
            "source_snippets": {
                "type": "array",
                "items": {"$ref": "#/$defs/source_snippet"},
            },
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
        },
        "$defs": {
            "source_snippet": source_snippet,
            "candidate_declaration_row": candidate_declaration_row,
            "formal_realization_node": formal_realization_node,
            "primitive_cost": primitive_cost,
            "route_option": route_option,
            "and_or_cost_graph": and_or_cost_graph,
            "minimal_delta_plan": minimal_delta_plan,
            "standalone_primitive": standalone_primitive,
        },
    }


def llm_route_planner_response_payload_validation_row_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID,
        "title": (
            "Formalization Gap Planner LLM Route Planner Response Payload "
            "Validation Row"
        ),
        "type": "object",
        "additionalProperties": False,
        "required": [
            "validation_id",
            "schema_version",
            "payload_index",
            "input_path",
            "input_shape",
            "response_wrapper_present",
            "request_id",
            "route_id",
            "payload_schema_id",
            "payload_fingerprint",
            "request_context_path",
            "request_context_validation_mode",
            "request_context_id",
            "request_context_route_id",
            "n_schema_errors",
            "n_request_context_errors",
            "n_errors",
            "ok",
            "errors",
            "proof_evidence_status",
            "proof_evidence_boundary",
        ],
        "properties": {
            "validation_id": {"type": "string", "minLength": 1},
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SCHEMA_VERSION,
            },
            "payload_index": {"type": "integer"},
            "input_path": {"type": "string", "minLength": 1},
            "input_shape": {"type": "string", "minLength": 1},
            "response_wrapper_present": {"type": "boolean"},
            "request_id": {"type": "string"},
            "route_id": {"type": "string"},
            "payload_schema_id": {
                "type": "string",
                "const": LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID,
            },
            "payload_fingerprint": {"type": "string", "minLength": 1},
            "request_context_path": {"type": "string"},
            "request_context_validation_mode": {
                "type": "string",
                "minLength": 1,
            },
            "request_context_id": {"type": "string"},
            "request_context_route_id": {"type": "string"},
            "n_schema_errors": {"type": "integer"},
            "n_request_context_errors": {"type": "integer"},
            "n_errors": {"type": "integer"},
            "ok": {"type": "boolean"},
            "errors": string_array,
            "proof_evidence_status": {
                "type": "string",
                "const": PROOF_EVIDENCE_STATUS,
            },
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
        },
    }


def llm_route_planner_response_payload_validation_manifest_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID,
        "title": (
            "Formalization Gap Planner LLM Route Planner Response Payload "
            "Validation Manifest"
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "created_at",
            "component_name",
            "input_path",
            "response_payload_schema_id",
            "response_payload_validation_manifest_schema_id",
            "response_payload_validation_row_schema_id",
            "n_payloads",
            "n_valid_payloads",
            "n_invalid_payloads",
            "rows",
            "all_ok",
            "errors",
            "proof_evidence_status",
            "proof_evidence_boundary",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SCHEMA_VERSION,
            },
            "created_at": {"type": "string", "minLength": 1},
            "component_name": {
                "type": "string",
                "const": LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATOR_COMPONENT,
            },
            "input_path": {"type": "string", "minLength": 1},
            "request_context_path": {"type": "string"},
            "response_payload_schema_id": {
                "type": "string",
                "const": LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID,
            },
            "response_payload_validation_manifest_schema_id": {
                "type": "string",
                "const": LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID,
            },
            "response_payload_validation_row_schema_id": {
                "type": "string",
                "const": LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID,
            },
            "response_payload_schema": {"type": "object"},
            "response_payload_validation_manifest_schema": {"type": "object"},
            "response_payload_validation_row_schema": {"type": "object"},
            "n_payloads": {"type": "integer"},
            "n_valid_payloads": {"type": "integer"},
            "n_invalid_payloads": {"type": "integer"},
            "n_request_context_packets": {"type": "integer"},
            "n_request_bound_payloads": {"type": "integer"},
            "n_schema_errors": {"type": "integer"},
            "n_request_context_errors": {"type": "integer"},
            "rows": {
                "type": "array",
                "items": {
                    "$ref": "#/$defs/response_payload_validation_row",
                },
            },
            "all_ok": {"type": "boolean"},
            "errors": string_array,
            "proof_evidence_status": {
                "type": "string",
                "const": PROOF_EVIDENCE_STATUS,
            },
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
        },
        "$defs": {
            "response_payload_validation_row": (
                llm_route_planner_response_payload_validation_row_json_schema()
            ),
        },
    }


def _provider_backend(provider_name: str) -> GeneratorBackend:
    provider = provider_name.lower()
    if provider == "anthropic":
        return AnthropicGeneratorBackend()
    if provider == "openai":
        return OpenAIResponsesGeneratorBackend()
    raise ValueError(
        "invoke_provider requires provider_name in {anthropic, openai} "
        "or a supplied generator_backend/static_response_json"
    )


def _normalize_provider_name(provider_name: str) -> str:
    provider = str(provider_name or DEFAULT_LLM_ROUTE_PLANNER_PROVIDER).strip().lower()
    if provider not in LLM_ROUTE_PLANNER_PROVIDER_NAMES:
        raise ValueError(
            "provider_name must be one of "
            + ", ".join(LLM_ROUTE_PLANNER_PROVIDER_NAMES)
            + "; Codex/Codex exec are not accepted as pure LLM route-planner providers"
        )
    return provider


def _normalize_model_tier(model_tier: str) -> str:
    tier = (model_tier or "auto").strip().lower()
    if tier not in LLM_ROUTE_PLANNER_MODEL_TIERS:
        raise ValueError(
            "model_tier must be one of "
            + ", ".join(LLM_ROUTE_PLANNER_MODEL_TIERS)
        )
    return tier


def _model_for_provider_tier(
    provider_name: str,
    *,
    requested_model: str,
    model_tier: str,
) -> str:
    provider = str(provider_name or "").strip().lower()
    if provider == PROMPT_ONLY_PROVIDER:
        return str(requested_model or "").strip()
    return default_generator_model(
        provider,
        requested_model,
        model_tier=model_tier,
    )


def _request_model_tier_mismatches(
    requests: tuple[dict[str, Any], ...],
) -> list[dict[str, object]]:
    return [
        mismatch
        for request in requests
        for mismatch in [_request_model_tier_mismatch(request)]
        if mismatch
    ]


def _request_model_tier_mismatch(
    request: Mapping[str, Any],
) -> dict[str, object]:
    provider = str(request.get("provider_name", "") or "").strip().lower()
    if provider != "anthropic":
        return {}
    model = str(request.get("model", "") or "").strip()
    model_tier = str(request.get("model_tier", "") or "").strip().lower()
    mismatch = claude_model_tier_mismatch(
        model,
        model_tier,
        subject=f"request {request.get('request_id', '')}".strip(),
    )
    if not mismatch:
        return {}
    return {
        "request_id": str(request.get("request_id", "")),
        "route_id": str(request.get("route_id", "")),
        "provider_name": provider,
        "model": model,
        "model_tier": model_tier,
        "error": mismatch,
    }


def _row_model_tier_mismatch_error(row: Mapping[str, object]) -> str:
    provider = str(row.get("provider_name", "") or "").strip().lower()
    if provider != "anthropic":
        return ""
    model = str(row.get("model", "") or "").strip()
    model_tier = str(row.get("model_tier", "") or "").strip().lower()
    return claude_model_tier_mismatch(
        model,
        model_tier,
        subject=f"LLM route planner row {row.get('request_id', '')}".strip(),
    )


def _llm_route_planner_model_tier_decision(
    route: Mapping[str, Any],
    context_packet: Mapping[str, Any],
    *,
    requested_model_tier: str,
) -> tuple[str, str]:
    requested = _normalize_model_tier(requested_model_tier)
    if requested in {"haiku", "sonnet", "opus"}:
        return (
            requested,
            f"operator requested Claude {requested} tier for this route-planner run",
        )

    residual_goals = _str_tuple(context_packet.get("residual_goals", []))
    feedback_summary = _dict_value(context_packet, "feedback_loop_summary")
    primitives = _dict_tuple(route.get("primitives", []))
    theorem_statement = str(route.get("theorem_statement", ""))
    source_refs = _route_and_primitive_source_refs(route)
    complex_markers = {
        "bridge",
        "bridge_needed",
        "source_port",
        "source_port_needed",
        "definition_or_theory_missing",
        "new_definition",
        "new_definition_needed",
        "new_theory",
        "new_theory_needed",
        "first_principles",
        "first_principles_needed",
        "missing",
        "unknown",
    }
    route_markers = {
        _primitive_key(marker)
        for primitive in primitives
        for marker in (
            primitive.get("coverage_status", ""),
            primitive.get("coverage_bucket", ""),
            primitive.get("formalization_action", ""),
            primitive.get("alignment_status", ""),
        )
        if _primitive_key(marker)
    }
    sonnet_reasons: list[str] = []
    if residual_goals:
        sonnet_reasons.append(f"{len(residual_goals)} prover residual goal(s)")
    realization_coverage = _dict_value(feedback_summary, "realization_coverage")
    if realization_coverage.get("complete") is False:
        sonnet_reasons.append("incomplete realization-coverage witness")
    if bool(feedback_summary.get("replan_required", False)):
        sonnet_reasons.append("feedback-loop summary requires route repair")
    sonnet_reasons.extend(_target_intake_sonnet_reasons(context_packet))
    hard_markers = sorted(route_markers & complex_markers)
    if hard_markers:
        sonnet_reasons.append(
            "complex coverage/action marker(s): " + ", ".join(hard_markers[:6])
        )
    if len(primitives) > 4:
        sonnet_reasons.append(f"{len(primitives)} formalization primitive(s)")
    if len(source_refs) > 6:
        sonnet_reasons.append(f"{len(source_refs)} source reference(s)")
    if len(theorem_statement) > 600:
        sonnet_reasons.append("long theorem statement")
    if sonnet_reasons:
        return (
            "sonnet",
            "auto selected Claude Sonnet because " + "; ".join(sonnet_reasons),
        )
    return (
        "haiku",
        (
            "auto selected Claude Haiku for a small route with no residual goals "
            "and only reuse/near/wrapper-level coverage markers"
        ),
    )


def _target_intake_sonnet_reasons(
    context_packet: Mapping[str, Any],
) -> list[str]:
    rows = _dict_tuple(context_packet.get("target_intake_rows", []))
    if not rows:
        return []
    reasons: list[str] = []
    for row in rows:
        missing = _str_tuple(row.get("missing_required_fields", []))
        if missing:
            reasons.append(
                "target intake missing required field(s): "
                + ", ".join(missing[:4])
            )
        review_flags = set(_str_tuple(row.get("review_flags", [])))
        hard_flags = sorted(
            review_flags
            & {
                "proof_source_refs_missing",
                "library_coverage_search_required",
            }
        )
        if hard_flags:
            reasons.append(
                "target intake review flag(s): " + ", ".join(hard_flags[:4])
            )
        if bool(row.get("proof_state_probe_required", False)):
            reasons.append("target intake requires proof-state probe")
        assumptions = _str_tuple(row.get("normalized_assumptions", []))
        objects = _str_tuple(row.get("normalized_objects", []))
        primitives = _str_tuple(row.get("extracted_primitive_candidates", []))
        literature_queries = _str_tuple(row.get("literature_queries", []))
        formal_library_queries = _formal_library_grounding_queries_from_intake_row(row)
        theorem_statement = str(row.get("theorem_statement", "") or "")
        desired_shape = _primitive_key(row.get("desired_theorem_shape", ""))
        complex_shape_markers = {
            "asymptotic_normality",
            "central_limit_theorem",
            "empirical_process",
            "martingale",
            "conditional_expectation",
            "measurability",
            "integrability",
            "uniform_convergence",
            "minimax",
            "semiparametric",
        }
        if desired_shape in complex_shape_markers:
            reasons.append(f"complex target theorem shape: {desired_shape}")
        if len(primitives) > 4:
            reasons.append(
                f"target intake has {len(primitives)} primitive candidate(s)"
            )
        if len(assumptions) > 4:
            reasons.append(
                f"target intake has {len(assumptions)} normalized assumption(s)"
            )
        if len(objects) > 6:
            reasons.append(f"target intake has {len(objects)} normalized object(s)")
        if len(literature_queries) > 6:
            reasons.append(
                f"target intake has {len(literature_queries)} literature query(s)"
            )
        if len(formal_library_queries) > 8:
            reasons.append(
                "target intake has "
                f"{len(formal_library_queries)} formal-library grounding query(s)"
            )
        if len(theorem_statement) > 600:
            reasons.append("long target-intake theorem statement")
    return list(dict.fromkeys(reasons))


def _formal_library_grounding_queries_from_intake_row(
    row: Mapping[str, Any],
) -> tuple[str, ...]:
    generic = _str_tuple(row.get("formal_library_grounding_queries", []))
    legacy = _str_tuple(row.get("lean_grounding_queries", []))
    return tuple(dict.fromkeys([*generic, *legacy]))


def _route_and_primitive_source_refs(route: Mapping[str, Any]) -> tuple[str, ...]:
    refs: list[str] = [*_str_tuple(route.get("source_refs", []))]
    for primitive in _dict_tuple(route.get("primitives", [])):
        refs.extend(_str_tuple(primitive.get("source_refs", [])))
    return tuple(dict.fromkeys(_str_tuple(refs)))


def _generator_model_for_request(
    generator_backend: GeneratorBackend,
    requested_model: str,
    *,
    model_tier: str,
) -> str:
    provider_name = str(getattr(generator_backend, "provider_name", ""))
    if provider_name == "anthropic":
        return default_generator_model(
            "anthropic",
            requested_model,
            model_tier=model_tier or "sonnet",
        )
    return default_generator_model(provider_name, requested_model)


def _row_for_request(
    request: Mapping[str, Any],
    *,
    request_errors: list[str],
    response: Mapping[str, Any] | None,
) -> FormalizationGapPlannerLLMRoutePlannerRow:
    provider_failure = bool((response or {}).get("provider_failure", False))
    response_present = response is not None and not provider_failure
    raw_text = str((response or {}).get("raw_response_text", ""))
    payload = _response_payload(response or {})
    generation_errors = _str_tuple((response or {}).get("generation_errors", []))
    response_errors = validate_llm_route_planner_response(response or {}) if response else []
    contract_errors = (
        _response_contract_errors(payload, request) if response_present else []
    )
    response_model_tier_errors = (
        _str_tuple(
            _row_model_tier_mismatch_error(
                {
                    "request_id": request.get("request_id", ""),
                    "provider_name": (
                        (response or {}).get("provider_name")
                        or request.get("provider_name", "")
                    ),
                    "model": (response or {}).get("model") or request.get("model", ""),
                    "model_tier": request.get("model_tier", ""),
                }
            )
        )
        if response_present
        else tuple()
    )
    all_errors = [
        *request_errors,
        *response_errors,
        *contract_errors,
        *response_model_tier_errors,
        *generation_errors,
    ]
    response_contract_ok = (
        response_present
        and not response_errors
        and not contract_errors
        and not response_model_tier_errors
        and not generation_errors
    )
    if provider_failure:
        acceptance_status = "REJECTED_LLM_ROUTE_PLANNER_PROVIDER_FAILURE"
    elif not response_present:
        acceptance_status = "AWAITING_LLM_ROUTE_PLANNER_RESPONSE"
    elif response_errors or contract_errors or response_model_tier_errors:
        acceptance_status = "REJECTED_LLM_ROUTE_PLANNER_RESPONSE"
    elif _dict_tuple(payload.get("search_requests", [])):
        acceptance_status = "ACCEPTED_WITH_SEARCH_REQUESTS"
    elif _dict_tuple(payload.get("planner_next_actions", [])):
        acceptance_status = "ACCEPTED_WITH_PLANNER_NEXT_ACTIONS"
    elif _str_tuple(payload.get("uncertainty_flags", [])):
        acceptance_status = "ACCEPTED_WITH_UNCERTAINTY_FLAGS"
    else:
        acceptance_status = "ACCEPTED_LLM_ROUTE_PLAN"
    route_id = str(request.get("route_id", ""))
    target_prover_family = str(request.get("target_prover_family", ""))
    formal_nodes = _formal_realization_nodes_from_payload(
        payload,
        target_prover_family=target_prover_family,
    )
    lean_legacy_nodes = _lean_legacy_realization_nodes_for_target(
        payload,
        formal_nodes=formal_nodes,
        target_prover_family=target_prover_family,
    )
    standalone_route = _standalone_route_from_payload(
        payload,
        target_prover_family=target_prover_family,
    )
    minimal_delta_plan = _dict_value(payload, "minimal_delta_plan")
    route_alignment_edges = _dict_tuple(payload.get("route_alignment_edges", []))
    route_adoption_status, route_adoption_blockers = _route_adoption_readiness(
        response_present=response_present,
        provider_failure=provider_failure,
        response_contract_ok=response_contract_ok,
        search_requests=_dict_tuple(payload.get("search_requests", [])),
        planner_next_actions=_dict_tuple(payload.get("planner_next_actions", [])),
        uncertainty_flags=_str_tuple(payload.get("uncertainty_flags", [])),
        semantic_alignment_risks=_str_tuple(
            payload.get("semantic_alignment_risks", [])
        ),
        residual_interpretations=_dict_tuple(
            payload.get("residual_interpretations", [])
        ),
        feedback_summary=_dict_value(
            _dict_value(request, "context_packet"),
            "feedback_loop_summary",
        ),
    )
    return FormalizationGapPlannerLLMRoutePlannerRow(
        schema_version=FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SCHEMA_VERSION,
        llm_route_planner_row_id="formalization_gap_planner_llm_route_plan:"
        + stable_hash([request.get("request_id", ""), response_present, payload])[:20],
        request_id=str(request.get("request_id", "")),
        route_id=route_id,
        display_name=str(request.get("display_name", "")),
        provider_name=str((response or {}).get("provider_name") or request.get("provider_name", "")),
        model=str((response or {}).get("model") or request.get("model", "")),
        model_tier=str(request.get("model_tier", "")),
        model_selection_rationale=str(request.get("model_selection_rationale", "")),
        target_prover_family=str(request.get("target_prover_family", "")),
        library_snapshot_ref=str(request.get("library_snapshot_ref", "")),
        prompt_fingerprint=str(request.get("prompt_fingerprint", "")),
        response_present=response_present,
        response_contract_ok=response_contract_ok,
        informal_knowledge_dag_nodes=_dict_tuple(
            payload.get("informal_knowledge_dag_nodes", [])
        ),
        formal_realization_dag_nodes=formal_nodes,
        lean_realization_dag_nodes=lean_legacy_nodes,
        route_alignment_edges=route_alignment_edges,
        minimal_delta_plan=minimal_delta_plan,
        residual_interpretations=_dict_tuple(
            payload.get("residual_interpretations", [])
        ),
        search_requests=_dict_tuple(payload.get("search_requests", [])),
        uncertainty_flags=_str_tuple(payload.get("uncertainty_flags", [])),
        semantic_alignment_risks=_str_tuple(
            payload.get("semantic_alignment_risks", [])
        ),
        planner_next_actions=_dict_tuple(payload.get("planner_next_actions", [])),
        standalone_route=standalone_route,
        source_refs=_route_source_refs(payload),
        source_snippets=_route_source_snippets(payload),
        realization_coverage_witness=_realization_coverage_witness(
            request=request,
            minimal_delta=minimal_delta_plan,
            standalone_route=standalone_route,
            formal_nodes=formal_nodes,
            alignment_edges=route_alignment_edges,
        ),
        raw_response_text=raw_text,
        generator_metadata=_jsonable_mapping(
            (response or {}).get("generator_metadata", {})
        ),
        provider_failure=provider_failure,
        repair_attempts=max(0, int((response or {}).get("repair_attempts", 0) or 0)),
        repair_error_history=_dict_tuple(
            (response or {}).get("repair_error_history", [])
        ),
        generation_errors=generation_errors,
        acceptance_status=acceptance_status,
        route_adoption_status=route_adoption_status,
        route_adoption_blockers=route_adoption_blockers,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not request_errors
        and not provider_failure
        and (not response_present or response_contract_ok),
        errors=tuple(sorted(set(all_errors))),
    )


def _route_adoption_readiness(
    *,
    response_present: bool,
    provider_failure: bool,
    response_contract_ok: bool,
    search_requests: tuple[dict[str, object], ...],
    planner_next_actions: tuple[dict[str, object], ...],
    uncertainty_flags: tuple[str, ...],
    semantic_alignment_risks: tuple[str, ...],
    residual_interpretations: tuple[dict[str, object], ...],
    feedback_summary: Mapping[str, object],
) -> tuple[str, tuple[str, ...]]:
    if provider_failure or (response_present and not response_contract_ok):
        return (
            ROUTE_ADOPTION_REJECTED_STATUS,
            (ROUTE_ADOPTION_BLOCKER_RESPONSE_NOT_ACCEPTED,),
        )
    if not response_present:
        return (
            ROUTE_ADOPTION_AWAITING_STATUS,
            (ROUTE_ADOPTION_BLOCKER_RESPONSE_MISSING,),
        )

    blockers: list[str] = []
    if search_requests:
        blockers.append(ROUTE_ADOPTION_BLOCKER_SEARCH_REQUESTS)
    if planner_next_actions:
        blockers.append(ROUTE_ADOPTION_BLOCKER_PLANNER_NEXT_ACTIONS)
    if uncertainty_flags:
        blockers.append(ROUTE_ADOPTION_BLOCKER_UNCERTAINTY_FLAGS)
    if semantic_alignment_risks:
        blockers.append(ROUTE_ADOPTION_BLOCKER_SEMANTIC_ALIGNMENT_RISKS)
    if residual_interpretations:
        blockers.append(ROUTE_ADOPTION_BLOCKER_RESIDUAL_INTERPRETATIONS)
    feedback_actions = _dict_tuple(feedback_summary.get("recommended_next_actions", []))
    if feedback_actions:
        blockers.append(ROUTE_ADOPTION_BLOCKER_FEEDBACK_ACTIONS)
    if any(
        str(action.get("action", "")).strip()
        == "redispatch_resource_response_with_request_playbook"
        for action in feedback_actions
    ):
        blockers.append(ROUTE_ADOPTION_BLOCKER_RESOURCE_PLAYBOOK_REDISPATCH)
    if any(
        str(action.get("source", "")).strip() == "resource_request_queue"
        for action in feedback_actions
    ):
        blockers.append(ROUTE_ADOPTION_BLOCKER_RESOURCE_REQUEST_QUEUE)
    if _truthy(feedback_summary.get("replan_required")):
        blockers.append(ROUTE_ADOPTION_BLOCKER_FEEDBACK_REPLAN)
    realization_coverage = _dict_value(feedback_summary, "realization_coverage")
    if realization_coverage.get("complete") is False:
        blockers.append(ROUTE_ADOPTION_BLOCKER_REALIZATION_COVERAGE)
    blockers = list(dict.fromkeys(blockers))
    if blockers:
        return (ROUTE_ADOPTION_PENDING_STATUS, tuple(blockers))
    return (ROUTE_ADOPTION_READY_STATUS, tuple())


def _response_contract_errors(
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if bool(payload.get("kernel_verified", False)):
        errors.append("response_payload cannot claim kernel_verified=true")
    if "not theorem proof evidence" not in str(
        payload.get("proof_evidence_boundary", "")
    ).lower():
        errors.append("response_payload.proof_evidence_boundary must say not theorem proof evidence")
    target_prover_family = str(request.get("target_prover_family", ""))
    informal_nodes = _dict_tuple(payload.get("informal_knowledge_dag_nodes", []))
    formal_nodes = _formal_realization_nodes_from_payload(
        payload,
        target_prover_family=target_prover_family,
    )
    alignment_edges = _dict_tuple(payload.get("route_alignment_edges", []))
    if not informal_nodes:
        errors.append("informal_knowledge_dag_nodes must be non-empty")
    if not formal_nodes:
        errors.append(
            "formal_realization_dag_nodes or lean_realization_dag_nodes must be non-empty"
        )
    errors.extend(_response_realization_field_contract_errors(payload, request))
    if not alignment_edges:
        errors.append("route_alignment_edges must be non-empty")
    for index, node in enumerate(informal_nodes):
        if not str(node.get("node_id", "")).strip():
            errors.append(f"informal_knowledge_dag_nodes[{index}].node_id missing")
        if not str(node.get("claim", "")).strip():
            errors.append(f"informal_knowledge_dag_nodes[{index}].claim missing")
        has_source = bool(_str_tuple(node.get("source_refs", [])))
        has_search = bool(str(node.get("source_search_status", "")).strip())
        has_boundary = bool(str(node.get("formal_gap_boundary", "")).strip())
        if not (has_source or has_search or has_boundary):
            errors.append(
                "informal_knowledge_dag_nodes"
                f"[{index}] needs source_refs, source_search_status, or formal_gap_boundary"
            )
    errors.extend(_response_source_ref_grounding_errors(payload, request))
    errors.extend(_response_target_theorem_identity_errors(payload, request))
    errors.extend(_response_target_prover_consistency_errors(payload, request))
    errors.extend(_response_search_request_contract_errors(payload))
    errors.extend(_response_planner_next_action_contract_errors(payload))
    errors.extend(_response_source_search_obligation_errors(payload))
    errors.extend(_response_source_snippet_provenance_errors(payload, request))
    errors.extend(_response_resource_request_alignment_errors(payload, request))
    for index, node in enumerate(formal_nodes):
        if not str(node.get("node_id", "")).strip():
            errors.append(f"formal_realization_dag_nodes[{index}].node_id missing")
        if not str(node.get("primitive", "")).strip():
            errors.append(f"formal_realization_dag_nodes[{index}].primitive missing")
    errors.extend(_response_formal_declaration_grounding_errors(payload, request))
    errors.extend(_response_formal_search_obligation_errors(payload))
    for index, edge in enumerate(alignment_edges):
        for field_name in ("informal_node_id", "formal_node_id", "alignment_rationale"):
            if not str(edge.get(field_name, "")).strip():
                errors.append(f"route_alignment_edges[{index}].{field_name} missing")
    minimal_delta = _dict_value(payload, "minimal_delta_plan")
    selected_primitives = _str_tuple(minimal_delta.get("selected_primitives", []))
    if not selected_primitives:
        errors.append("minimal_delta_plan.selected_primitives must be non-empty")
    if not str(minimal_delta.get("minimality_rationale", "")).strip():
        errors.append("minimal_delta_plan.minimality_rationale missing")
    errors.extend(
        _minimal_delta_cost_witness_errors(
            minimal_delta,
            selected_primitives=selected_primitives,
        )
    )
    standalone_route = _standalone_route_from_payload(
        payload,
        target_prover_family=target_prover_family,
    )
    if not str(standalone_route.get("display_name", "")).strip():
        errors.append("standalone_route.display_name missing")
    standalone_primitives = _dict_tuple(standalone_route.get("primitives", []))
    if not standalone_primitives:
        errors.append("standalone_route.primitives must be non-empty")
    errors.extend(
        _response_primitive_coherence_errors(
            selected_primitives=selected_primitives,
            standalone_primitives=standalone_primitives,
            informal_nodes=informal_nodes,
            formal_nodes=formal_nodes,
            alignment_edges=alignment_edges,
            minimal_delta=minimal_delta,
            search_requests=_dict_tuple(payload.get("search_requests", [])),
            request=request,
        )
    )
    residual_goals = _str_tuple(request.get("residual_goals", []))
    if residual_goals and not _dict_tuple(payload.get("residual_interpretations", [])):
        errors.append("residual_interpretations required when request has residual_goals")
    errors.extend(_response_residual_interpretation_errors(payload, request))
    errors.extend(_response_residual_source_grounding_errors(payload))
    return errors


def _response_realization_field_contract_errors(
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[str]:
    target_prover_key = _target_prover_key(request.get("target_prover_family", ""))
    legacy_nodes = _dict_tuple(payload.get("lean_realization_dag_nodes", []))
    if target_prover_key and target_prover_key != "lean4" and legacy_nodes:
        return [
            "lean_realization_dag_nodes is a Lean-only legacy alias; "
            "non-Lean target prover responses must use "
            "formal_realization_dag_nodes only"
        ]
    return []


def _response_payload_realization_field_contract_errors(
    payload: Mapping[str, Any],
) -> list[str]:
    target_prover_key = _target_prover_key(
        _declared_payload_target_prover_family(payload)
    )
    legacy_nodes = _dict_tuple(payload.get("lean_realization_dag_nodes", []))
    if target_prover_key and target_prover_key != "lean4" and legacy_nodes:
        return [
            "lean_realization_dag_nodes is a Lean-only legacy alias; "
            "non-Lean target prover responses must use "
            "formal_realization_dag_nodes only"
        ]
    return []


def _declared_payload_target_prover_family(payload: Mapping[str, Any]) -> str:
    direct_values = [
        payload.get("target_prover_family", ""),
        payload.get("target_prover", ""),
    ]
    route = _dict_value(payload, "standalone_route")
    metadata = _dict_value(route, "replan_metadata")
    direct_values.extend(
        [
            route.get("target_prover_family", ""),
            route.get("target_prover", ""),
            metadata.get("target_prover_family", ""),
            metadata.get("target_prover", ""),
        ]
    )
    for value in direct_values:
        text = str(value or "").strip()
        if text:
            return text

    for node in (
        *_dict_tuple(payload.get("formal_realization_dag_nodes", [])),
        *_dict_tuple(payload.get("lean_realization_dag_nodes", [])),
        *_dict_tuple(route.get("primitives", [])),
    ):
        for field_name in ("target_prover_family", "target_prover"):
            text = str(node.get(field_name, "") or "").strip()
            if text:
                return text
        for declaration_row in _dict_tuple(node.get("candidate_declaration_rows", [])):
            text = str(
                declaration_row.get("target_prover_family", "")
                or declaration_row.get("target_prover", "")
            ).strip()
            if text:
                return text
    return ""


def _minimal_delta_cost_witness_errors(
    minimal_delta: Mapping[str, Any],
    *,
    selected_primitives: tuple[str, ...],
) -> list[str]:
    errors: list[str] = []
    if (
        str(minimal_delta.get("cost_model_version", "")).strip()
        != MINIMAL_DELTA_COST_POLICY_ID
    ):
        errors.append(
            "minimal_delta_plan.cost_model_version must equal "
            + MINIMAL_DELTA_COST_POLICY_ID
        )
    if not _is_nonnegative_number(minimal_delta.get("route_cost")):
        errors.append("minimal_delta_plan.route_cost must be a nonnegative number")
    primitive_costs = _dict_tuple(minimal_delta.get("primitive_costs", []))
    if not primitive_costs:
        errors.append("minimal_delta_plan.primitive_costs must be non-empty")
    selected = {_primitive_key(primitive) for primitive in selected_primitives}
    selected.discard("")
    if primitive_costs:
        cost_rows_by_primitive: dict[str, list[dict[str, object]]] = {}
        for index, row in enumerate(primitive_costs):
            primitive = _primitive_key(row.get("primitive", ""))
            if not primitive:
                errors.append(f"minimal_delta_plan.primitive_costs[{index}].primitive missing")
                continue
            cost_rows_by_primitive.setdefault(primitive, []).append(row)
            if not _is_nonnegative_number(row.get("total_cost")):
                errors.append(
                    f"minimal_delta_plan.primitive_costs[{index}].total_cost must be a nonnegative number"
                )
            dimension_error = _primitive_cost_dimension_accounting_error(row)
            if dimension_error:
                errors.append(
                    f"minimal_delta_plan.primitive_costs[{index}].{dimension_error}"
                )
            base_cost_policy_error = _primitive_cost_base_cost_policy_error(row)
            if base_cost_policy_error:
                errors.append(
                    f"minimal_delta_plan.primitive_costs[{index}]."
                    + base_cost_policy_error
                )
            if not str(row.get("cost_rationale", "")).strip():
                errors.append(
                    f"minimal_delta_plan.primitive_costs[{index}].cost_rationale missing"
                )
        missing_cost_rows = sorted(selected - set(cost_rows_by_primitive))
        if missing_cost_rows:
            errors.append(
                "minimal_delta_plan.primitive_costs missing selected primitives: "
                + ", ".join(missing_cost_rows)
            )
        duplicate_cost_rows = sorted(
            primitive
            for primitive, rows in cost_rows_by_primitive.items()
            if primitive in selected and len(rows) != 1
        )
        if duplicate_cost_rows:
            errors.append(
                "minimal_delta_plan.primitive_costs must contain exactly one row per selected primitive: "
                + ", ".join(duplicate_cost_rows)
            )
        route_cost_accounting_error = _route_cost_selected_primitive_accounting_error(
            minimal_delta,
            selected=selected,
            cost_rows_by_primitive=cost_rows_by_primitive,
        )
        if route_cost_accounting_error:
            errors.append(route_cost_accounting_error)
    errors.extend(
        _minimal_delta_and_or_cost_graph_errors(
            minimal_delta,
            selected=selected,
        )
    )
    return errors


def _primitive_cost_base_cost_policy_error(
    row: Mapping[str, object],
) -> str:
    bucket = _primitive_key(row.get("coverage_bucket", ""))
    if not bucket:
        return "coverage_bucket missing"
    policy = MINIMAL_DELTA_COST_POLICY.get("coverage_bucket_base_cost", {})
    if not isinstance(policy, Mapping):
        return "coverage_bucket_base_cost policy missing"
    if bucket not in policy:
        return (
            "coverage_bucket must be listed in "
            "minimal_delta_cost_policy.coverage_bucket_base_cost: "
            + bucket
        )
    expected = policy.get(bucket)
    if not _is_nonnegative_number(expected) or not _is_nonnegative_number(
        row.get("base_cost")
    ):
        return ""
    if abs(float(row.get("base_cost", 0) or 0) - float(expected)) > 1e-9:
        return (
            "base_cost must equal minimal_delta_cost_policy."
            f"coverage_bucket_base_cost[{bucket!r}]={expected}"
        )
    return ""


def _primitive_cost_dimension_accounting_error(
    row: Mapping[str, object],
) -> str:
    total_cost = row.get("total_cost")
    dimension_fields = (
        "base_cost",
        "proof_difficulty_cost",
        "import_cone_cost",
        "definition_or_typeclass_cost",
        "semantic_risk_cost",
        "reuse_credit",
    )
    missing_dimensions = [
        field_name for field_name in dimension_fields if field_name not in row
    ]
    if missing_dimensions:
        return (
            "cost dimension fields missing: "
            + ", ".join(missing_dimensions)
        )
    nonnumeric = [
        field_name
        for field_name in dimension_fields
        if not _is_nonnegative_number(row.get(field_name))
    ]
    if nonnumeric:
        return (
            "cost dimension fields must be nonnegative numbers: "
            + ", ".join(nonnumeric)
        )
    if not _is_nonnegative_number(total_cost):
        return ""
    accounted = (
        float(row.get("base_cost", 0) or 0)
        + float(row.get("proof_difficulty_cost", 0) or 0)
        + float(row.get("import_cone_cost", 0) or 0)
        + float(row.get("definition_or_typeclass_cost", 0) or 0)
        + float(row.get("semantic_risk_cost", 0) or 0)
        - float(row.get("reuse_credit", 0) or 0)
    )
    if abs(accounted - float(total_cost)) > 1e-9:
        return (
            "total_cost must equal base_cost + proof_difficulty_cost + "
            "import_cone_cost + definition_or_typeclass_cost + "
            "semantic_risk_cost - reuse_credit"
        )
    return ""


def _route_cost_selected_primitive_accounting_error(
    minimal_delta: Mapping[str, object],
    *,
    selected: set[str],
    cost_rows_by_primitive: Mapping[str, list[dict[str, object]]],
) -> str:
    route_cost = minimal_delta.get("route_cost")
    if not selected or not _is_nonnegative_number(route_cost):
        return ""
    selected_rows: list[dict[str, object]] = []
    for primitive in sorted(selected):
        rows = cost_rows_by_primitive.get(primitive, [])
        if len(rows) != 1 or not _is_nonnegative_number(rows[0].get("total_cost")):
            return ""
        selected_rows.append(rows[0])
    primitive_total = sum(float(row.get("total_cost", 0) or 0) for row in selected_rows)
    if abs(primitive_total - float(route_cost)) > 1e-9:
        return (
            "minimal_delta_plan.route_cost must equal the sum of selected "
            "primitive_costs total_cost values"
        )
    return ""


def _minimal_delta_and_or_cost_graph_errors(
    minimal_delta: Mapping[str, Any],
    *,
    selected: set[str],
) -> list[str]:
    errors: list[str] = []
    graph = _dict_value(minimal_delta, "and_or_cost_graph")
    if not graph:
        return ["minimal_delta_plan.and_or_cost_graph must be non-empty"]
    graph_kind = str(graph.get("graph_kind", "")).strip()
    if graph_kind != "AND_OR_ROUTE_COST_GRAPH":
        errors.append(
            "minimal_delta_plan.and_or_cost_graph.graph_kind must equal "
            "AND_OR_ROUTE_COST_GRAPH"
        )
    selected_route_option_id = str(
        graph.get("selected_route_option_id", "")
    ).strip()
    if not selected_route_option_id:
        errors.append(
            "minimal_delta_plan.and_or_cost_graph.selected_route_option_id missing"
        )
    route_options = _dict_tuple(graph.get("route_options", []))
    if not route_options:
        errors.append(
            "minimal_delta_plan.and_or_cost_graph.route_options must be non-empty"
        )
        return errors
    selected_options: list[dict[str, object]] = []
    selected_option_cost: float | None = None
    route_option_ids: set[str] = set()
    route_option_primitives: set[str] = set()
    for index, option in enumerate(route_options):
        option_id = str(option.get("route_option_id", "")).strip()
        if not option_id:
            errors.append(
                "minimal_delta_plan.and_or_cost_graph."
                f"route_options[{index}].route_option_id missing"
            )
        else:
            route_option_ids.add(option_id)
        route_cost = option.get("route_cost")
        if not _is_nonnegative_number(route_cost):
            errors.append(
                "minimal_delta_plan.and_or_cost_graph."
                f"route_options[{index}].route_cost must be a nonnegative number"
            )
        if not str(option.get("cost_rationale", "")).strip():
            errors.append(
                "minimal_delta_plan.and_or_cost_graph."
                f"route_options[{index}].cost_rationale missing"
            )
        option_primitives = {
            _primitive_key(primitive)
            for primitive in _str_tuple(option.get("selected_primitives", []))
        }
        option_primitives.discard("")
        route_option_primitives.update(option_primitives)
        if not option_primitives:
            errors.append(
                "minimal_delta_plan.and_or_cost_graph."
                f"route_options[{index}].selected_primitives must be non-empty"
            )
        if bool(option.get("selected", False)):
            selected_options.append(option)
            if _is_nonnegative_number(route_cost):
                selected_option_cost = float(route_cost)
            if selected_route_option_id and option_id != selected_route_option_id:
                errors.append(
                    "minimal_delta_plan.and_or_cost_graph selected option id "
                    "does not match selected_route_option_id"
                )
            if option_primitives != selected:
                errors.append(
                    "minimal_delta_plan.and_or_cost_graph selected route option "
                    "selected_primitives must match minimal_delta_plan.selected_primitives"
                )
    errors.extend(
        _and_or_cost_graph_structure_errors(
            graph,
            route_option_ids=route_option_ids,
            route_option_primitives=route_option_primitives,
            prefix="minimal_delta_plan.and_or_cost_graph",
        )
    )
    if len(selected_options) != 1:
        errors.append(
            "minimal_delta_plan.and_or_cost_graph must mark exactly one selected route option"
        )
    route_cost = minimal_delta.get("route_cost")
    if selected_option_cost is not None and _is_nonnegative_number(route_cost):
        if abs(selected_option_cost - float(route_cost)) > 1e-9:
            errors.append(
                "minimal_delta_plan.and_or_cost_graph selected route_cost must equal "
                "minimal_delta_plan.route_cost"
            )
        cheaper = [
            str(option.get("route_option_id", "")).strip() or f"route_options[{index}]"
            for index, option in enumerate(route_options)
            if _is_nonnegative_number(option.get("route_cost"))
            and float(option.get("route_cost", 0)) + 1e-9 < selected_option_cost
        ]
        if cheaper:
            errors.append(
                "minimal_delta_plan.and_or_cost_graph selected route option is not minimal; "
                "cheaper options: "
                + ", ".join(cheaper[:8])
            )
    return errors


def _and_or_cost_graph_structure_errors(
    graph: Mapping[str, Any],
    *,
    route_option_ids: set[str],
    route_option_primitives: set[str],
    prefix: str,
) -> list[str]:
    errors: list[str] = []
    or_nodes = _dict_tuple(graph.get("or_nodes", []))
    if not or_nodes:
        errors.append(f"{prefix}.or_nodes must be non-empty")
    for index, node in enumerate(or_nodes):
        if not str(node.get("node_id", "")).strip():
            errors.append(f"{prefix}.or_nodes[{index}].node_id missing")
        choices = _str_tuple(node.get("choices", []))
        if not choices:
            errors.append(f"{prefix}.or_nodes[{index}].choices must be non-empty")
        unknown_choices = [
            choice
            for choice in choices
            if choice not in route_option_ids
            and _primitive_key(choice) not in route_option_primitives
        ]
        if unknown_choices:
            errors.append(
                f"{prefix}.or_nodes[{index}].choices reference unknown route options or primitives: "
                + ", ".join(unknown_choices[:8])
            )
        if not str(node.get("selection_rationale", "")).strip():
            errors.append(f"{prefix}.or_nodes[{index}].selection_rationale missing")
    and_edges = _dict_tuple(graph.get("and_edges", []))
    if not and_edges:
        errors.append(f"{prefix}.and_edges must be non-empty")
    for index, edge in enumerate(and_edges):
        option_id = str(edge.get("route_option_id", "")).strip()
        if not option_id:
            errors.append(f"{prefix}.and_edges[{index}].route_option_id missing")
        elif option_id not in route_option_ids:
            errors.append(
                f"{prefix}.and_edges[{index}].route_option_id references unknown route option: "
                + option_id
            )
        requires = _str_tuple(edge.get("requires", []))
        if not requires:
            errors.append(f"{prefix}.and_edges[{index}].requires must be non-empty")
        unknown_requires = [
            primitive
            for primitive in requires
            if _primitive_key(primitive) not in route_option_primitives
        ]
        if unknown_requires:
            errors.append(
                f"{prefix}.and_edges[{index}].requires reference unknown primitives: "
                + ", ".join(unknown_requires[:8])
            )
    return errors


def _is_nonnegative_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0


def _response_residual_interpretation_errors(
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    request_residuals = _str_tuple(request.get("residual_goals", []))
    interpretations = _dict_tuple(payload.get("residual_interpretations", []))
    if not interpretations:
        return errors
    if not request_residuals:
        errors.append("residual_interpretations require request residual_goals")
        return errors
    request_by_key = {
        _residual_goal_key(residual): residual
        for residual in request_residuals
        if _residual_goal_key(residual)
    }
    interpreted_keys: set[str] = set()
    for index, interpretation in enumerate(interpretations):
        residual_goal = str(interpretation.get("residual_goal", "")).strip()
        if not residual_goal:
            errors.append(f"residual_interpretations[{index}].residual_goal missing")
            continue
        residual_key = _residual_goal_key(residual_goal)
        interpreted_keys.add(residual_key)
        if residual_key not in request_by_key:
            errors.append(
                "residual_interpretations"
                f"[{index}].residual_goal not present in request residual_goals: {residual_goal}"
            )
        if not str(interpretation.get("interpretation", "")).strip():
            errors.append(f"residual_interpretations[{index}].interpretation missing")
        if not (
            str(interpretation.get("route_repair", "")).strip()
            or str(interpretation.get("repair_action", "")).strip()
        ):
            errors.append(
                f"residual_interpretations[{index}] requires route_repair or repair_action"
            )
    missing = [
        request_by_key[key]
        for key in sorted(set(request_by_key) - interpreted_keys)
    ]
    if missing:
        errors.append(
            "residual_interpretations missing request residual_goals: "
            + "; ".join(missing[:8])
        )
    return errors


def _response_residual_source_grounding_errors(
    payload: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    search_requests = _dict_tuple(payload.get("search_requests", []))
    for index, interpretation in enumerate(
        _dict_tuple(payload.get("residual_interpretations", []))
    ):
        has_repair = bool(
            str(interpretation.get("route_repair", "")).strip()
            or str(interpretation.get("repair_action", "")).strip()
        )
        if not has_repair:
            continue
        if _residual_interpretation_has_source_refs(interpretation):
            continue
        if _residual_interpretation_has_formal_boundary(interpretation):
            continue
        if _has_literature_search_request_for_residual_interpretation(
            search_requests,
            interpretation=interpretation,
        ):
            continue
        errors.append(
            "residual_interpretations"
            f"[{index}] route repair requires source_refs/source_snippets, "
            "a matching literature/source search_request, or formal_gap_boundary"
        )
    return errors


def _residual_interpretation_has_source_refs(
    interpretation: Mapping[str, Any],
) -> bool:
    return bool(
        _str_tuple(
            [
                *_str_tuple(interpretation.get("source_refs", [])),
                *_source_refs_from_snippets(interpretation.get("source_snippets", [])),
            ]
        )
    )


def _residual_interpretation_has_formal_boundary(
    interpretation: Mapping[str, Any],
) -> bool:
    if str(interpretation.get("formal_gap_boundary", "")).strip():
        return True
    return _source_ref_key(interpretation.get("source_search_status", "")) in {
        "formal_gap_boundary",
        "formal_boundary_declared",
    }


def _has_literature_search_request_for_residual_interpretation(
    search_requests: tuple[dict[str, object], ...],
    *,
    interpretation: Mapping[str, Any],
) -> bool:
    primitives = _residual_interpretation_search_primitives(interpretation)
    if primitives and _has_literature_search_request_for_obligation(
        search_requests,
        primitives=primitives,
    ):
        return True
    residual_tokens = _residual_interpretation_search_tokens(interpretation)
    if not residual_tokens:
        return False
    literature_kind_keys = ("literature", "source", "paper", "textbook")
    for request in search_requests:
        kind_key = _primitive_key(request.get("request_kind", ""))
        if not any(key in kind_key for key in literature_kind_keys):
            continue
        request_tokens = _search_text_tokens(
            " ".join(
                str(request.get(field_name, ""))
                for field_name in ("query", "reason", "action", "description")
            )
        )
        if residual_tokens & request_tokens:
            return True
    return False


def _residual_interpretation_search_primitives(
    interpretation: Mapping[str, Any],
) -> tuple[str, ...]:
    primitives: list[str] = []
    primitives.extend(_str_tuple(interpretation.get("target_primitives", [])))
    primitives.extend(_str_tuple(interpretation.get("residual_primitives", [])))
    primitives.extend(_str_tuple(interpretation.get("primitive", [])))
    primitives.extend(_str_tuple(interpretation.get("primitives", [])))
    residual_goal = str(interpretation.get("residual_goal", "")).strip()
    if ":" in residual_goal:
        primitives.append(residual_goal.split(":", 1)[0])
    return tuple(
        dict.fromkeys(
            primitive
            for primitive in (_primitive_key(value) for value in primitives)
            if primitive
        )
    )


def _residual_interpretation_search_tokens(
    interpretation: Mapping[str, Any],
) -> set[str]:
    return _search_text_tokens(
        " ".join(
            str(interpretation.get(field_name, ""))
            for field_name in (
                "residual_goal",
                "interpretation",
                "route_repair",
                "repair_action",
            )
        )
    )


def _search_text_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9_]+", _source_ref_key(text))
        if len(token) >= 4
        and token
        not in {
            "with",
            "from",
            "that",
            "this",
            "into",
            "before",
            "after",
            "route",
            "repair",
            "condition",
            "residual",
            "source",
            "search",
        }
    }


def _residual_goal_key(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _response_formal_declaration_grounding_errors(
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    target_prover_family = str(request.get("target_prover_family", ""))
    available = _available_formal_declaration_keys_for_request(request)
    used_declarations = _response_candidate_declaration_locations(payload)
    ungrounded = sorted(
        (declaration, location)
        for declaration, location in used_declarations
        if _formal_declaration_key(declaration) not in available
    )
    if ungrounded:
        preview = "; ".join(
            f"{location}={declaration}"
            for declaration, location in ungrounded[:8]
        )
        errors.append(
            "response candidate_declarations must be drawn from request/context "
            f"formal-library evidence; ungrounded candidate_declarations: {preview}"
        )
    errors.extend(
        _response_candidate_declaration_row_provenance_errors(payload, request)
    )
    for index, node in enumerate(
        _formal_realization_nodes_from_payload(
            payload,
            target_prover_family=target_prover_family,
        )
    ):
        if _formal_node_claims_existing_library(node) and not _node_candidate_declarations(
            node
        ):
            errors.append(
                "formal_realization_dag_nodes"
                f"[{index}] existing-library coverage requires grounded candidate_declarations"
            )
    route = _standalone_route_from_payload(
        payload,
        target_prover_family=target_prover_family,
    )
    for index, primitive in enumerate(_dict_tuple(route.get("primitives", []))):
        if _route_primitive_claims_existing_library(
            primitive
        ) and not _node_candidate_declarations(primitive):
            errors.append(
                "standalone_route.primitives"
                f"[{index}] existing-library coverage requires grounded candidate_declarations"
            )
    return errors


def _response_candidate_declaration_row_provenance_errors(
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[str]:
    available = _available_formal_declaration_row_provenance_for_request(request)
    if not available:
        return []
    errors: list[str] = []
    unsupported: list[str] = []
    for location, row in _response_candidate_declaration_row_locations(
        payload,
        target_prover_family=str(request.get("target_prover_family", "")),
    ):
        declaration_key = _formal_declaration_key(row.get("declaration", ""))
        target_key = _target_prover_key(row.get("target_prover_family", ""))
        source_field_key = _formal_declaration_source_field_key(
            row.get("source_field", "")
        )
        if not declaration_key:
            continue
        allowed_sources = available.get((declaration_key, target_key), set())
        if not allowed_sources:
            unsupported.append(
                f"{location}={row.get('declaration', '')}"
                f"@{row.get('target_prover_family', '')}"
            )
            continue
        if source_field_key not in allowed_sources:
            unsupported.append(
                f"{location}={row.get('declaration', '')}"
                f" source_field={row.get('source_field', '')}"
            )
    if unsupported:
        errors.append(
            "response candidate_declaration_rows must preserve request/context "
            "formal-library provenance; unsupported rows: "
            + "; ".join(unsupported[:8])
        )
    return errors


TARGET_THEOREM_IDENTITY_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "existing",
    "fact",
    "facts",
    "follow",
    "following",
    "follows",
    "for",
    "from",
    "given",
    "has",
    "have",
    "imply",
    "implies",
    "in",
    "into",
    "is",
    "lemma",
    "lemmas",
    "of",
    "on",
    "or",
    "that",
    "the",
    "then",
    "there",
    "theorem",
    "theorems",
    "this",
    "to",
    "under",
    "using",
    "with",
}


def _response_target_theorem_identity_errors(
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[str]:
    route = _dict_value(payload, "standalone_route")
    response_statement = str(route.get("theorem_statement", "") or "").strip()
    if not response_statement:
        return []
    anchors = _target_theorem_identity_anchors(request)
    if not anchors:
        return []
    if any(
        _target_theorem_identity_overlap_ok(anchor, response_statement)
        for anchor in anchors
    ):
        return []
    request_route = _dict_value(request, "target_route")
    return [
        "standalone_route.theorem_statement appears to target a different theorem "
        "than the request/target-intake context; preserve target theorem identity "
        "and represent repairs as added assumptions, primitives, or route-repair "
        "metadata. "
        f"request_route_id={request.get('route_id', '')}; "
        f"request_display_name={request_route.get('display_name', '')}"
    ]


def _target_theorem_identity_anchors(
    request: Mapping[str, Any],
) -> tuple[str, ...]:
    request_route = _dict_value(request, "target_route")
    context_packet = _dict_value(request, "context_packet")
    statement_anchors = _str_tuple(
        [
            request_route.get("theorem_statement", ""),
            *[
                row.get("theorem_statement", "")
                for row in _dict_tuple(context_packet.get("target_intake_rows", []))
            ],
        ]
    )
    if statement_anchors:
        return statement_anchors
    return _str_tuple(
        row.get("normalized_claim", "")
        for row in _dict_tuple(context_packet.get("target_intake_rows", []))
    )


def _target_theorem_identity_overlap_ok(anchor: str, response: str) -> bool:
    anchor_tokens = _target_theorem_identity_tokens(anchor)
    response_tokens = _target_theorem_identity_tokens(response)
    if not anchor_tokens or not response_tokens:
        return True
    shared = anchor_tokens & response_tokens
    if len(anchor_tokens) <= 3:
        return len(shared) >= max(1, len(anchor_tokens) - 1)
    return len(shared) >= 2 and (len(shared) / len(anchor_tokens)) >= 0.35


def _target_theorem_identity_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", str(text or "").lower())
        if len(token) >= 3 and token not in TARGET_THEOREM_IDENTITY_STOPWORDS
    }


def _response_target_prover_consistency_errors(
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[str]:
    expected = _target_prover_key(request.get("target_prover_family", ""))
    if not expected:
        return []
    checks: list[tuple[str, object]] = [
        ("response_payload.target_prover_family", payload.get("target_prover_family", "")),
    ]
    route = _dict_value(payload, "standalone_route")
    checks.append(
        (
            "standalone_route.target_prover_family",
            route.get("target_prover_family", ""),
        )
    )
    metadata = _dict_value(route, "replan_metadata")
    checks.append(
        (
            "standalone_route.replan_metadata.target_prover_family",
            metadata.get("target_prover_family", ""),
        )
    )
    for index, node in enumerate(
        _formal_realization_nodes_from_payload(
            payload,
            target_prover_family=str(request.get("target_prover_family", "")),
        )
    ):
        checks.append(
            (
                f"formal_realization_dag_nodes[{index}].target_prover_family",
                node.get("target_prover_family", ""),
            )
        )
    for location, row in _response_candidate_declaration_row_locations(payload):
        checks.append(
            (
                f"{location}.target_prover_family",
                row.get("target_prover_family", ""),
            )
        )
    errors: list[str] = []
    for location, raw_value in checks:
        value = str(raw_value or "").strip()
        if not value:
            continue
        actual = _target_prover_key(value)
        if actual != expected:
            errors.append(
                f"{location} {value} does not match request target_prover_family "
                f"{request.get('target_prover_family', '')}"
            )
    return errors


def _target_prover_key(value: object) -> str:
    key = _source_ref_key(value)
    aliases = {
        "coq": "rocq",
        "rocq_coq": "rocq",
        "coq_rocq": "rocq",
        "lean": "lean4",
        "lean_4": "lean4",
        "lean4": "lean4",
        "isabelle_hol": "isabelle",
    }
    return aliases.get(key, key)


def _response_formal_search_obligation_errors(
    payload: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    search_requests = _dict_tuple(payload.get("search_requests", []))
    for index, node in enumerate(_formal_realization_nodes_from_payload(payload)):
        if not _formal_node_requires_library_search(node):
            continue
        primitives = _formal_node_search_primitives(node)
        if not _has_formal_library_search_request_for_obligation(
            search_requests,
            primitives=primitives,
        ):
            errors.append(
                "formal_realization_dag_nodes"
                f"[{index}] unknown/formal-library-search-pending coverage requires a matching formal_library/library search_request"
            )
    route = _dict_value(payload, "standalone_route")
    for index, primitive_row in enumerate(_dict_tuple(route.get("primitives", []))):
        if not _formal_node_requires_library_search(primitive_row):
            continue
        primitives = _str_tuple(
            [
                *_str_tuple(primitive_row.get("target_primitives", [])),
                *_str_tuple(primitive_row.get("primitive", "")),
            ]
        )
        if not _has_formal_library_search_request_for_obligation(
            search_requests,
            primitives=tuple(_primitive_key(primitive) for primitive in primitives),
        ):
            errors.append(
                "standalone_route.primitives"
                f"[{index}] unknown/formal-library-search-pending coverage requires a matching formal_library/library search_request"
            )
    return errors


def _formal_node_requires_library_search(node: Mapping[str, Any]) -> bool:
    if _node_candidate_declarations(node):
        return False
    if str(node.get("formal_gap_boundary", "")).strip():
        return False
    markers = (
        node.get("coverage_bucket", ""),
        node.get("coverage_status", ""),
        node.get("formalization_action", ""),
        node.get("alignment_status", ""),
        node.get("formal_search_status", ""),
        node.get("library_search_status", ""),
    )
    if any(_delta_formalization_marker(marker) for marker in markers):
        return False
    return any(_formal_library_search_marker(marker) for marker in markers)


def _formal_library_search_marker(value: object) -> bool:
    key = _primitive_key(value)
    return key in {
        "unknown",
        "coverage_unknown",
        "declaration_unknown",
        "formal_search_requested",
        "formal_search_pending",
        "formal_library_search_requested",
        "formal_library_search_pending",
        "library_search_requested",
        "library_search_pending",
        "declaration_search_requested",
        "declaration_search_pending",
    }


def _formal_node_search_primitives(node: Mapping[str, Any]) -> tuple[str, ...]:
    primitives: list[str] = []
    primitives.extend(_str_tuple(node.get("target_primitives", [])))
    primitives.extend(_str_tuple(node.get("primitive", "")))
    primitives.extend(_str_tuple(node.get("primitives", [])))
    node_id = str(node.get("node_id", "")).strip()
    if ":" in node_id:
        primitives.append(node_id.rsplit(":", 1)[-1])
    return tuple(
        dict.fromkeys(
            primitive
            for primitive in (_primitive_key(value) for value in primitives)
            if primitive
        )
    )


def _has_formal_library_search_request_for_obligation(
    search_requests: tuple[dict[str, object], ...],
    *,
    primitives: tuple[str, ...],
) -> bool:
    formal_kind_keys = (
        "formal_library",
        "formal_source",
        "library",
        "lean_search",
        "loogle",
        "declaration",
    )
    if primitives:
        return any(
            _has_search_request_for_primitive(
                search_requests,
                primitive=primitive,
                request_kind_keys=formal_kind_keys,
            )
            for primitive in primitives
        )
    return any(
        any(
            key in _primitive_key(request.get("request_kind", ""))
            for key in formal_kind_keys
        )
        and bool(
            str(
                request.get("query")
                or request.get("reason")
                or request.get("description")
                or ""
            ).strip()
        )
        for request in search_requests
    )


def _response_candidate_declaration_locations(
    payload: Mapping[str, Any],
) -> tuple[tuple[str, str], ...]:
    declarations: list[tuple[str, str]] = []
    for index, node in enumerate(_formal_realization_nodes_from_payload(payload)):
        declarations.extend(
            (declaration, f"formal_realization_dag_nodes[{index}].candidate_declarations")
            for declaration in _node_candidate_declarations(node)
        )
    route = _dict_value(payload, "standalone_route")
    for index, primitive in enumerate(_dict_tuple(route.get("primitives", []))):
        declarations.extend(
            (declaration, f"standalone_route.primitives[{index}].candidate_declarations")
            for declaration in _node_candidate_declarations(primitive)
        )
    return tuple(dict.fromkeys(declarations))


def _node_candidate_declarations(node: Mapping[str, Any]) -> tuple[str, ...]:
    declarations: list[str] = []
    declarations.extend(_formal_declaration_values(node.get("candidate_declarations", [])))
    declarations.extend(
        str(row.get("declaration", ""))
        for row in _candidate_declaration_rows(
            node.get("candidate_declaration_rows", []),
            inherited_target_prover_family=str(
                node.get("target_prover_family", "")
                or node.get("target_prover", "")
            ),
            fallback_source_field="candidate_declaration_rows",
        )
    )
    return tuple(
        dict.fromkeys(
            declaration
            for declaration in _str_tuple(declarations)
            if declaration
        )
    )


def _response_candidate_declaration_row_locations(
    payload: Mapping[str, Any],
    *,
    target_prover_family: str = "",
) -> tuple[tuple[str, dict[str, object]], ...]:
    rows: list[tuple[str, dict[str, object]]] = []
    for index, node in enumerate(
        _formal_realization_nodes_from_payload(
            payload,
            target_prover_family=target_prover_family,
        )
    ):
        rows.extend(
            (
                f"formal_realization_dag_nodes[{index}].candidate_declaration_rows[{row_index}]",
                row,
            )
            for row_index, row in enumerate(
                _candidate_declaration_rows(
                    node.get("candidate_declaration_rows", []),
                    inherited_target_prover_family=str(
                        node.get("target_prover_family", "")
                        or payload.get("target_prover_family", "")
                    ),
                    fallback_source_field="candidate_declaration_rows",
                )
            )
        )
    route = _standalone_route_from_payload(
        payload,
        target_prover_family=target_prover_family,
    )
    for index, primitive in enumerate(_dict_tuple(route.get("primitives", []))):
        rows.extend(
            (
                f"standalone_route.primitives[{index}].candidate_declaration_rows[{row_index}]",
                row,
            )
            for row_index, row in enumerate(
                _candidate_declaration_rows(
                    primitive.get("candidate_declaration_rows", []),
                    inherited_target_prover_family=str(
                        primitive.get("target_prover_family", "")
                        or route.get("target_prover_family", "")
                        or payload.get("target_prover_family", "")
                    ),
                    fallback_source_field="candidate_declaration_rows",
                )
            )
        )
    return tuple(rows)


def _formal_node_claims_existing_library(node: Mapping[str, Any]) -> bool:
    markers = (
        node.get("coverage_bucket", ""),
        node.get("coverage_status", ""),
        node.get("formalization_action", ""),
        node.get("alignment_status", ""),
    )
    return any(_existing_library_marker(marker) for marker in markers)


def _route_primitive_claims_existing_library(primitive: Mapping[str, Any]) -> bool:
    markers = (
        primitive.get("coverage_bucket", ""),
        primitive.get("coverage_status", ""),
        primitive.get("formalization_action", ""),
        primitive.get("alignment_status", ""),
    )
    return any(_existing_library_marker(marker) for marker in markers)


def _existing_library_marker(value: object) -> bool:
    key = _primitive_key(value)
    return key in {
        "already_exists",
        "exact_exists",
        "exact",
        "near_exists",
        "near",
        "different_formulation",
        "reuse",
        "compose",
        "compose_existing_declarations",
        "target_prover_replay",
    }


def _available_formal_declarations_for_context(
    route: Mapping[str, Any],
    context_packet: Mapping[str, Any],
) -> tuple[str, ...]:
    declarations: list[str] = []
    _collect_formal_declarations(route, declarations)
    _collect_formal_declarations(context_packet, declarations)
    return tuple(dict.fromkeys(_str_tuple(declarations)))


def _available_formal_declaration_rows_for_context(
    route: Mapping[str, Any],
    context_packet: Mapping[str, Any],
    *,
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    route_target = str(
        route.get("target_prover_family")
        or route.get("target_prover")
        or target_prover_family
    )
    _collect_formal_declaration_rows(
        route,
        rows,
        inherited_target_prover_family=route_target,
    )
    _collect_formal_declaration_rows(
        context_packet,
        rows,
        inherited_target_prover_family=target_prover_family,
    )
    compact: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        declaration = str(row.get("declaration", "")).strip()
        if not declaration:
            continue
        row_target = str(row.get("target_prover_family", "")).strip()
        key = (_formal_declaration_key(declaration), _target_prover_key(row_target))
        if key in seen:
            continue
        seen.add(key)
        compact.append(
            {
                "declaration": declaration,
                "target_prover_family": row_target,
                "source_field": str(row.get("source_field", "")),
            }
        )
    return tuple(compact)


def _target_compatible_formal_declaration_rows(
    rows: tuple[dict[str, object], ...],
    *,
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    target = _target_prover_key(target_prover_family)
    return tuple(
        row
        for row in rows
        if not _target_prover_key(row.get("target_prover_family", ""))
        or _target_prover_key(row.get("target_prover_family", "")) == target
    )


def _available_formal_declaration_keys_for_request(
    request: Mapping[str, Any],
) -> set[str]:
    context_packet = _dict_value(request, "context_packet")
    structured_rows = _dict_tuple(
        context_packet.get("available_formal_declaration_rows", [])
    )
    if structured_rows:
        declarations = [
            str(row.get("declaration", ""))
            for row in _target_compatible_formal_declaration_rows(
                structured_rows,
                target_prover_family=str(request.get("target_prover_family", "")),
            )
        ]
        return {
            _formal_declaration_key(declaration)
            for declaration in declarations
            if _formal_declaration_key(declaration)
        }
    declarations = list(
        _formal_declaration_values(
            context_packet.get("available_formal_declarations", [])
        )
    )
    if not declarations:
        _collect_formal_declarations(request.get("target_route", {}), declarations)
        _collect_formal_declarations(context_packet, declarations)
    return {
        _formal_declaration_key(declaration)
        for declaration in declarations
        if _formal_declaration_key(declaration)
    }


def _available_formal_declaration_row_provenance_for_request(
    request: Mapping[str, Any],
) -> dict[tuple[str, str], set[str]]:
    context_packet = _dict_value(request, "context_packet")
    structured_rows = _dict_tuple(
        context_packet.get("available_formal_declaration_rows", [])
    )
    provenance: dict[tuple[str, str], set[str]] = {}
    target_prover_family = str(request.get("target_prover_family", ""))
    for row in _target_compatible_formal_declaration_rows(
        structured_rows,
        target_prover_family=target_prover_family,
    ):
        declaration_key = _formal_declaration_key(row.get("declaration", ""))
        target_key = _target_prover_key(
            row.get("target_prover_family", "") or target_prover_family
        )
        if not declaration_key:
            continue
        source_fields = {
            _formal_declaration_source_field_key(row.get("source_field", "")),
            "available_formal_declaration_rows",
        }
        source_fields.discard("")
        provenance.setdefault((declaration_key, target_key), set()).update(
            source_fields
        )

    flat_declarations = _str_tuple(
        context_packet.get("available_formal_declarations", [])
    )
    for declaration in flat_declarations:
        declaration_key = _formal_declaration_key(declaration)
        target_key = _target_prover_key(target_prover_family)
        if declaration_key:
            provenance.setdefault((declaration_key, target_key), set()).add(
                "available_formal_declarations"
            )
    return provenance


def _collect_formal_declaration_rows(
    value: Any,
    rows: list[dict[str, object]],
    *,
    inherited_target_prover_family: str,
) -> None:
    if isinstance(value, Mapping):
        current_target = str(
            value.get("target_prover_family")
            or value.get("target_prover")
            or inherited_target_prover_family
        )
        for key, item in value.items():
            key_text = str(key)
            if key_text in {
                "available_formal_declaration_rows",
                "candidate_declaration_rows",
                "formal_declaration_hits",
                "lean_declaration_hits",
            }:
                _append_formal_declaration_rows(
                    rows,
                    item,
                    inherited_target_prover_family=current_target,
                    fallback_source_field=key_text,
                )
            if key_text in {
                "candidate_declaration",
                "candidate_declarations",
                "declaration",
                "declaration_name",
                "declaration_names",
                "lean_declaration",
                "lean_declarations",
            }:
                rows.extend(
                    {
                        "declaration": declaration,
                        "target_prover_family": current_target,
                        "source_field": key_text,
                    }
                    for declaration in _formal_declaration_values(item)
                )
            _collect_formal_declaration_rows(
                item,
                rows,
                inherited_target_prover_family=current_target,
            )
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _collect_formal_declaration_rows(
                item,
                rows,
            inherited_target_prover_family=inherited_target_prover_family,
        )


def _append_formal_declaration_rows(
    rows: list[dict[str, object]],
    values: Any,
    *,
    inherited_target_prover_family: str,
    fallback_source_field: str,
) -> None:
    for value in _dict_tuple(values):
        declaration = str(
            value.get("declaration")
            or value.get("declaration_name")
            or value.get("lean_declaration")
            or ""
        ).strip()
        if not declaration:
            continue
        rows.append(
            {
                "declaration": declaration,
                "target_prover_family": str(
                    value.get("target_prover_family", "")
                    or value.get("target_prover", "")
                    or inherited_target_prover_family
                ).strip(),
                "source_field": str(
                    value.get("source_field", "") or fallback_source_field
                ).strip(),
            }
        )


def _collect_formal_declarations(value: Any, declarations: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if key_text in {
                "candidate_declaration",
                "candidate_declarations",
                "declaration",
                "declaration_name",
                "declaration_names",
                "lean_declaration",
                "lean_declarations",
                "lean_declaration_hits",
            }:
                declarations.extend(_formal_declaration_values(item))
            _collect_formal_declarations(item, declarations)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _collect_formal_declarations(item, declarations)


def _formal_declaration_values(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value.strip() else tuple()
    if isinstance(value, Mapping):
        declarations: list[str] = []
        for key in (
            "declaration",
            "declaration_name",
            "candidate_declaration",
            "lean_declaration",
            "name",
            "full_name",
        ):
            if key in value:
                declarations.extend(_formal_declaration_values(value.get(key)))
        return _str_tuple(declarations)
    if isinstance(value, (list, tuple, set)):
        declarations: list[str] = []
        for item in value:
            declarations.extend(_formal_declaration_values(item))
        return _str_tuple(declarations)
    return tuple()


def _formal_declaration_key(value: object) -> str:
    return re.sub(r"[^a-z0-9_'.]+", "_", str(value or "").strip().lower()).strip("_")


def _formal_declaration_source_field_key(value: object) -> str:
    key = _primitive_key(value)
    aliases = {
        "available_declaration_rows": "available_formal_declaration_rows",
        "formal_declaration_rows": "available_formal_declaration_rows",
        "available_declarations": "available_formal_declarations",
        "formal_declarations": "available_formal_declarations",
    }
    return aliases.get(key, key)


def _response_source_ref_grounding_errors(
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    available = _available_source_ref_keys_for_request(request)
    used_refs = _response_source_ref_locations(payload)
    ungrounded = sorted(
        (ref, location)
        for ref, location in used_refs
        if _source_ref_key(ref) not in available
    )
    if ungrounded:
        preview = "; ".join(
            f"{location}={ref}" for ref, location in ungrounded[:8]
        )
        errors.append(
            "response source_refs must be drawn from request/context evidence; "
            f"ungrounded source_refs: {preview}"
        )
    for index, node in enumerate(_dict_tuple(payload.get("informal_knowledge_dag_nodes", []))):
        status = _source_ref_key(node.get("source_search_status", ""))
        refs = _str_tuple(
            [
                *_str_tuple(node.get("source_refs", [])),
                *_source_refs_from_snippets(node.get("source_snippets", [])),
            ]
        )
        if status == "source_backed" and not refs:
            errors.append(
                f"informal_knowledge_dag_nodes[{index}] SOURCE_BACKED requires grounded source_refs"
            )
    return errors


def _response_search_request_contract_errors(
    payload: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    for index, request in enumerate(_dict_tuple(payload.get("search_requests", []))):
        request_kind = _source_ref_key(request.get("request_kind", ""))
        if not request_kind:
            errors.append(f"search_requests[{index}].request_kind missing")
        elif request_kind not in LLM_ROUTE_PLANNER_SEARCH_REQUEST_KIND_ALIASES:
            errors.append(
                "search_requests"
                f"[{index}].request_kind unsupported: {request.get('request_kind')}"
            )
        if not str(request.get("query", "")).strip():
            errors.append(f"search_requests[{index}].query missing")
        if not str(request.get("reason", "")).strip():
            errors.append(f"search_requests[{index}].reason missing")
    return errors


def _response_planner_next_action_contract_errors(
    payload: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    for index, action in enumerate(_dict_tuple(payload.get("planner_next_actions", []))):
        if not str(action.get("owner", "")).strip():
            errors.append(f"planner_next_actions[{index}].owner missing")
        if not str(action.get("action", "")).strip():
            errors.append(f"planner_next_actions[{index}].action missing")
        if not _planner_next_action_has_supported_hook(action):
            errors.append(
                "planner_next_actions"
                f"[{index}] does not resolve to a supported hook family"
            )
    return errors


def _planner_next_action_has_supported_hook(action: Mapping[str, Any]) -> bool:
    text_key = _source_ref_key(
        " ".join(
            [
                *_planner_action_queries(action),
                *_planner_action_resource_refs(action),
            ]
        )
    )
    return any(
        _text_key_contains_alias(text_key, alias)
        for alias in LLM_ROUTE_PLANNER_PLANNER_NEXT_ACTION_HOOK_ALIASES
    )


def _text_key_contains_alias(text_key: str, alias: str) -> bool:
    return f"_{alias}_" in f"_{text_key}_"


def _response_source_search_obligation_errors(
    payload: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    search_requests = _dict_tuple(payload.get("search_requests", []))
    for index, node in enumerate(
        _dict_tuple(payload.get("informal_knowledge_dag_nodes", []))
    ):
        status = _source_ref_key(node.get("source_search_status", ""))
        if not _source_search_status_requires_request(status):
            continue
        primitives = _informal_node_search_primitives(node)
        if not _has_literature_search_request_for_obligation(
            search_requests,
            primitives=primitives,
        ):
            errors.append(
                "informal_knowledge_dag_nodes"
                f"[{index}] SEARCH_REQUESTED requires a matching literature/source search_request"
            )
    route = _dict_value(payload, "standalone_route")
    for index, primitive_row in enumerate(_dict_tuple(route.get("primitives", []))):
        status = _source_ref_key(primitive_row.get("source_search_status", ""))
        if not _source_search_status_requires_request(status):
            continue
        primitives = _str_tuple(
            [
                *_str_tuple(primitive_row.get("target_primitives", [])),
                *_str_tuple(primitive_row.get("primitive", "")),
            ]
        )
        if not _has_literature_search_request_for_obligation(
            search_requests,
            primitives=tuple(_primitive_key(primitive) for primitive in primitives),
        ):
            errors.append(
                "standalone_route.primitives"
                f"[{index}] SEARCH_REQUESTED requires a matching literature/source search_request"
            )
    return errors


def _source_search_status_requires_request(status: str) -> bool:
    return status in {
        "search_requested",
        "source_search_requested",
        "source_search_pending",
        "literature_search_requested",
        "literature_search_pending",
    }


def _informal_node_search_primitives(node: Mapping[str, Any]) -> tuple[str, ...]:
    primitives: list[str] = []
    primitives.extend(_str_tuple(node.get("target_primitives", [])))
    primitives.extend(_str_tuple(node.get("primitive", [])))
    primitives.extend(_str_tuple(node.get("primitives", [])))
    for snippet in _dict_tuple(node.get("source_snippets", [])):
        primitives.extend(_str_tuple(snippet.get("target_primitives", [])))
    node_id = str(node.get("node_id", "")).strip()
    if ":" in node_id:
        primitives.append(node_id.rsplit(":", 1)[-1])
    return tuple(
        dict.fromkeys(
            primitive
            for primitive in (_primitive_key(value) for value in primitives)
            if primitive
        )
    )


def _has_literature_search_request_for_obligation(
    search_requests: tuple[dict[str, object], ...],
    *,
    primitives: tuple[str, ...],
) -> bool:
    literature_kind_keys = ("literature", "source", "paper", "textbook")
    if primitives:
        return any(
            _has_search_request_for_primitive(
                search_requests,
                primitive=primitive,
                request_kind_keys=literature_kind_keys,
            )
            for primitive in primitives
        )
    return any(
        any(
            key in _primitive_key(request.get("request_kind", ""))
            for key in literature_kind_keys
        )
        and bool(
            str(
                request.get("query")
                or request.get("reason")
                or request.get("description")
                or ""
            ).strip()
        )
        for request in search_requests
    )


def _response_source_ref_locations(
    payload: Mapping[str, Any],
) -> tuple[tuple[str, str], ...]:
    refs: list[tuple[str, str]] = []
    refs.extend(
        (ref, "response.source_refs")
        for ref in _str_tuple(payload.get("source_refs", []))
    )
    refs.extend(
        (ref, f"response.source_snippets[{index}].source_ref")
        for index, ref in enumerate(_source_refs_from_snippets(payload.get("source_snippets", [])))
    )
    for index, node in enumerate(_dict_tuple(payload.get("informal_knowledge_dag_nodes", []))):
        refs.extend(
            (ref, f"informal_knowledge_dag_nodes[{index}].source_refs")
            for ref in _str_tuple(node.get("source_refs", []))
        )
        refs.extend(
            (ref, f"informal_knowledge_dag_nodes[{index}].source_snippets.source_ref")
            for ref in _source_refs_from_snippets(node.get("source_snippets", []))
        )
    for index, residual in enumerate(_dict_tuple(payload.get("residual_interpretations", []))):
        refs.extend(
            (ref, f"residual_interpretations[{index}].source_refs")
            for ref in _str_tuple(residual.get("source_refs", []))
        )
        refs.extend(
            (ref, f"residual_interpretations[{index}].source_snippets.source_ref")
            for ref in _source_refs_from_snippets(residual.get("source_snippets", []))
        )
    route = _dict_value(payload, "standalone_route")
    refs.extend(
        (ref, "standalone_route.source_refs")
        for ref in _str_tuple(route.get("source_refs", []))
    )
    refs.extend(
        (ref, "standalone_route.source_snippets.source_ref")
        for ref in _source_refs_from_snippets(route.get("source_snippets", []))
    )
    for index, primitive in enumerate(_dict_tuple(route.get("primitives", []))):
        refs.extend(
            (ref, f"standalone_route.primitives[{index}].source_refs")
            for ref in _str_tuple(primitive.get("source_refs", []))
        )
        refs.extend(
            (ref, f"standalone_route.primitives[{index}].source_snippets.source_ref")
            for ref in _source_refs_from_snippets(primitive.get("source_snippets", []))
        )
    return tuple(dict.fromkeys(refs))


def _response_source_snippet_provenance_errors(
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[str]:
    emitted = _response_source_snippet_locations(payload)
    if not emitted:
        return []
    available = _dict_tuple(
        _dict_value(request, "context_packet").get("available_source_snippets", [])
    )
    errors: list[str] = []
    if not available:
        return [
            "response source_snippets require request/context available_source_snippets; "
            "emit source_refs or search_requests instead"
        ]
    unsupported: list[tuple[str, str]] = []
    malformed: list[str] = []
    for snippet, location in emitted:
        source_ref = str(snippet.get("source_ref", "")).strip()
        claim = str(snippet.get("claim", "")).strip()
        excerpt = str(snippet.get("excerpt", "")).strip()
        if not source_ref or not (claim or excerpt):
            malformed.append(location)
            continue
        if not _source_snippet_supported_by_available(snippet, available):
            unsupported.append((source_ref, location))
    if malformed:
        errors.append(
            "response source_snippets require source_ref plus claim or excerpt: "
            + ", ".join(malformed[:8])
        )
    if unsupported:
        preview = "; ".join(
            f"{location}={source_ref}" for source_ref, location in unsupported[:8]
        )
        errors.append(
            "response source_snippets must be copied from or textually supported "
            "by request/context available_source_snippets; unsupported snippets: "
            + preview
        )
    return errors


def _response_source_snippet_locations(
    payload: Mapping[str, Any],
) -> tuple[tuple[dict[str, object], str], ...]:
    rows: list[tuple[dict[str, object], str]] = []
    rows.extend(
        (snippet, f"response.source_snippets[{index}]")
        for index, snippet in enumerate(_dict_tuple(payload.get("source_snippets", [])))
    )
    for index, node in enumerate(_dict_tuple(payload.get("informal_knowledge_dag_nodes", []))):
        rows.extend(
            (snippet, f"informal_knowledge_dag_nodes[{index}].source_snippets[{snippet_index}]")
            for snippet_index, snippet in enumerate(_dict_tuple(node.get("source_snippets", [])))
        )
    for index, residual in enumerate(_dict_tuple(payload.get("residual_interpretations", []))):
        rows.extend(
            (snippet, f"residual_interpretations[{index}].source_snippets[{snippet_index}]")
            for snippet_index, snippet in enumerate(_dict_tuple(residual.get("source_snippets", [])))
        )
    route = _dict_value(payload, "standalone_route")
    rows.extend(
        (snippet, f"standalone_route.source_snippets[{index}]")
        for index, snippet in enumerate(_dict_tuple(route.get("source_snippets", [])))
    )
    for index, primitive in enumerate(_dict_tuple(route.get("primitives", []))):
        rows.extend(
            (snippet, f"standalone_route.primitives[{index}].source_snippets[{snippet_index}]")
            for snippet_index, snippet in enumerate(_dict_tuple(primitive.get("source_snippets", [])))
        )
    return tuple(rows)


def _source_snippet_supported_by_available(
    snippet: Mapping[str, object],
    available: tuple[dict[str, object], ...],
) -> bool:
    source_ref_key = _source_ref_key(snippet.get("source_ref", ""))
    if not source_ref_key:
        return False
    claim = _snippet_text_key(snippet.get("claim", ""))
    excerpt = _snippet_text_key(snippet.get("excerpt", ""))
    same_source = [
        row
        for row in available
        if _source_ref_key(row.get("source_ref", "")) == source_ref_key
    ]
    if not same_source:
        return False
    if excerpt:
        return any(
            _snippet_text_contains(
                excerpt,
                _snippet_text_key(row.get("excerpt", "")),
            )
            for row in same_source
        )
    if claim:
        return any(
            _snippet_text_contains(
                claim,
                _snippet_text_key(row.get("claim", "")),
            )
            for row in same_source
        )
    return False


def _snippet_text_contains(left: str, right: str) -> bool:
    if not left or not right:
        return False
    return left in right or right in left


def _snippet_text_key(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _available_source_refs_for_context(
    route: Mapping[str, Any],
    context_packet: Mapping[str, Any],
) -> tuple[str, ...]:
    refs: list[str] = []
    _collect_source_refs(route, refs)
    _collect_source_refs(_source_ref_admissible_context(context_packet), refs)
    return tuple(dict.fromkeys(_str_tuple(refs)))


def _available_source_snippets_for_context(
    route: Mapping[str, Any],
    context_packet: Mapping[str, Any],
) -> tuple[dict[str, object], ...]:
    snippets: list[dict[str, object]] = []
    _collect_source_snippets_from_value(route, snippets)
    _collect_source_snippets_from_value(
        _source_ref_admissible_context(context_packet),
        snippets,
    )
    return tuple(_compact_source_snippets(snippets)[:12])


def _source_ref_admissible_context(
    context_packet: Mapping[str, Any],
) -> dict[str, object]:
    context = dict(context_packet)
    context.pop("available_source_refs", None)
    context.pop("available_source_snippets", None)
    context.pop("resource_request_queue_rows", None)
    context.pop("component_resource_registry_context", None)
    context["resource_response_ledger_rows"] = tuple(
        row
        for row in _dict_tuple(context_packet.get("resource_response_ledger_rows", []))
        if _resource_response_row_is_admissible_feedback(row)
    )
    context["refinement_evidence_rows"] = tuple(
        row
        for row in _dict_tuple(context_packet.get("refinement_evidence_rows", []))
        if _refinement_evidence_row_is_admissible_feedback(row)
    )
    return context


def _available_source_ref_keys_for_request(
    request: Mapping[str, Any],
) -> set[str]:
    context_packet = _dict_value(request, "context_packet")
    refs = list(_str_tuple(context_packet.get("available_source_refs", [])))
    if not refs:
        _collect_source_refs(request.get("target_route", {}), refs)
        _collect_source_refs(context_packet, refs)
    return {_source_ref_key(ref) for ref in refs if _source_ref_key(ref)}


def _collect_source_refs(value: Any, refs: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if key_text in {
                "source_ref",
                "source_refs",
                "source_id",
                "source_ids",
                "known_proof_source",
                "known_proof_sources",
                "citation_key",
                "citation_keys",
                "paper_id",
                "paper_ids",
            }:
                refs.extend(_source_ref_values(item))
            _collect_source_refs(item, refs)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _collect_source_refs(item, refs)


def _source_ref_values(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value.strip() else tuple()
    if isinstance(value, Mapping):
        refs: list[str] = []
        for key in ("source_ref", "source_id", "citation_key", "paper_id", "id"):
            if key in value:
                refs.extend(_source_ref_values(value.get(key)))
        return _str_tuple(refs)
    if isinstance(value, (list, tuple, set)):
        refs: list[str] = []
        for item in value:
            refs.extend(_source_ref_values(item))
        return _str_tuple(refs)
    return tuple()


def _source_ref_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def _response_resource_request_alignment_errors(
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[str]:
    context_packet = _dict_value(request, "context_packet")
    queue_rows = _dict_tuple(context_packet.get("resource_request_queue_rows", []))
    queued_request_ids = {
        _resource_ref_key(row.get("resource_request_id", ""))
        for row in queue_rows
        if _resource_ref_key(row.get("resource_request_id", ""))
    }
    queued_resource_ids = {
        _resource_ref_key(row.get("resource_id", ""))
        for row in queue_rows
        if _resource_ref_key(row.get("resource_id", ""))
    }
    playbooks_by_request_id, playbooks_by_resource_id = (
        _resource_request_playbook_indexes(context_packet)
    )
    registry_context = _dict_value(
        context_packet,
        "component_resource_registry_context",
    )
    allowed_resource_contract_ids = _resource_contract_ids_for_request_context(
        context_packet,
        registry_context=registry_context,
    )
    has_registry_context = any(
        _dict_tuple(registry_context.get(row_key, []))
        for row_key in (
            "resource_rows",
            "resource_contract_rows",
            "component_rows",
            "execution_plan_rows",
        )
    )
    has_resource_id_context = bool(queue_rows or has_registry_context)
    if not has_resource_id_context and not allowed_resource_contract_ids:
        return []

    allowed_resource_ids = set(queued_resource_ids)
    for row_key in (
        "resource_rows",
        "resource_contract_rows",
        "component_rows",
        "execution_plan_rows",
    ):
        for row in _dict_tuple(registry_context.get(row_key, [])):
            for field_name in (
                "resource_id",
                "local_fallback_resource_ids",
                "frontier_resource_ids",
                "local_first_resource_ids",
                "frontier_escalation_resource_ids",
            ):
                allowed_resource_ids.update(
                    _resource_ref_key(value)
                    for value in _str_tuple(row.get(field_name, []))
                    if _resource_ref_key(value)
                )
            resource_id = _resource_ref_key(row.get("resource_id", ""))
            if resource_id:
                allowed_resource_ids.add(resource_id)

    evidence_requests = [
        ("search_requests", index, row)
        for index, row in enumerate(_dict_tuple(payload.get("search_requests", [])))
    ]
    evidence_requests.extend(
        ("planner_next_actions", index, row)
        for index, row in enumerate(_dict_tuple(payload.get("planner_next_actions", [])))
    )
    if not evidence_requests:
        return []

    errors: list[str] = []
    aligned_to_queue = False
    for collection_name, index, row in evidence_requests:
        refs = _structured_resource_refs(row)
        request_ids = {
            _resource_ref_key(value)
            for value in refs["resource_request_ids"]
            if _resource_ref_key(value)
        }
        resource_ids = {
            _resource_ref_key(value)
            for value in refs["resource_ids"]
            if _resource_ref_key(value)
        }
        resource_contract_ids = {
            _resource_ref_key(value)
            for value in refs["resource_contract_ids"]
            if _resource_ref_key(value)
        }
        tool_owner_ids = {
            _resource_ref_key(value)
            for value in refs["tool_owner_ids"]
            if _resource_ref_key(value)
        }
        unknown_request_ids = sorted(request_ids - queued_request_ids)
        if unknown_request_ids:
            errors.append(
                f"{collection_name}[{index}] references unknown resource_request_id(s): "
                + ", ".join(unknown_request_ids[:8])
            )
        unknown_resource_ids = (
            sorted(resource_ids - allowed_resource_ids)
            if has_resource_id_context
            else []
        )
        if unknown_resource_ids:
            errors.append(
                f"{collection_name}[{index}] references resource_id(s) not present "
                "in request queue or registry context: "
                + ", ".join(unknown_resource_ids[:8])
            )
        unknown_resource_contract_ids = sorted(
            resource_contract_ids - allowed_resource_contract_ids
        )
        if unknown_resource_contract_ids:
            errors.append(
                f"{collection_name}[{index}] references resource_contract_id(s) "
                "not present in request queue, interactive policy, feedback "
                "summary, or registry context: "
                + ", ".join(unknown_resource_contract_ids[:8])
            )
        unknown_tool_owners = (
            sorted(
                tool_id
                for tool_id in tool_owner_ids
                if tool_id not in allowed_resource_ids
                and _resource_owner_looks_like_tool(tool_id)
            )
            if has_resource_id_context
            else []
        )
        if unknown_tool_owners:
            errors.append(
                f"{collection_name}[{index}] owner/tool is not available in "
                "queued or registry resources: "
                + ", ".join(unknown_tool_owners[:8])
            )
        if request_ids & queued_request_ids or resource_ids & queued_resource_ids:
            aligned_to_queue = True
        if tool_owner_ids & queued_resource_ids:
            aligned_to_queue = True
        errors.extend(
            _resource_request_playbook_grounding_errors(
                collection_name,
                index,
                row,
                request_ids=request_ids,
                resource_ids=resource_ids | (tool_owner_ids & queued_resource_ids),
                playbooks_by_request_id=playbooks_by_request_id,
                playbooks_by_resource_id=playbooks_by_resource_id,
            )
        )
    if queue_rows and not aligned_to_queue:
        errors.append(
            "when context_packet.resource_request_queue_rows is present, at least "
            "one search_requests or planner_next_actions row must reference a "
            "queued resource_request_id or resource_id"
        )
    return errors


def _resource_contract_ids_for_request_context(
    context_packet: Mapping[str, Any],
    *,
    registry_context: Mapping[str, Any],
) -> set[str]:
    ids: set[str] = set()
    for row_key in (
        "resource_request_queue_rows",
        "interactive_decision_policy_rows",
    ):
        ids.update(
            _resource_contract_ids_for_rows(
                _dict_tuple(context_packet.get(row_key, []))
            )
        )
    feedback_summary = _dict_value(context_packet, "feedback_loop_summary")
    ids.update(
        _resource_contract_ids_for_rows(
            _dict_tuple(feedback_summary.get("recommended_next_actions", []))
        )
    )
    for row_key in (
        "resource_rows",
        "resource_contract_rows",
        "component_rows",
        "execution_plan_rows",
    ):
        ids.update(
            _resource_contract_ids_for_rows(
                _dict_tuple(registry_context.get(row_key, []))
            )
        )
    return ids


def _resource_contract_ids_for_rows(
    rows: tuple[dict[str, object], ...] | list[dict[str, object]],
) -> set[str]:
    ids: set[str] = set()
    for row in rows:
        for field_name in (
            "resource_contract_id",
            "resource_contract_ids",
            "resource_contract",
            "resource_contracts",
        ):
            ids.update(
                _resource_ref_key(value)
                for value in _str_tuple(row.get(field_name, []))
                if _resource_ref_key(value)
            )
    return ids


def _resource_request_playbook_indexes(
    context_packet: Mapping[str, Any],
) -> tuple[dict[str, list[dict[str, object]]], dict[str, list[dict[str, object]]]]:
    playbooks = _dict_tuple(context_packet.get("resource_request_playbooks", []))
    if not playbooks:
        playbooks = tuple(
            _dict_value(row, "request_playbook")
            for row in _dict_tuple(context_packet.get("resource_request_queue_rows", []))
            if _dict_value(row, "request_playbook")
        )
    by_request_id: dict[str, list[dict[str, object]]] = {}
    by_resource_id: dict[str, list[dict[str, object]]] = {}
    for playbook in playbooks:
        request_id = _resource_ref_key(playbook.get("resource_request_id", ""))
        resource_id = _resource_ref_key(playbook.get("resource_id", ""))
        if request_id:
            by_request_id.setdefault(request_id, []).append(dict(playbook))
        if resource_id:
            by_resource_id.setdefault(resource_id, []).append(dict(playbook))
    return by_request_id, by_resource_id


def _resource_request_playbook_grounding_errors(
    collection_name: str,
    index: int,
    row: Mapping[str, Any],
    *,
    request_ids: set[str],
    resource_ids: set[str],
    playbooks_by_request_id: Mapping[str, list[dict[str, object]]],
    playbooks_by_resource_id: Mapping[str, list[dict[str, object]]],
) -> list[str]:
    matched_playbooks: list[dict[str, object]] = []
    for request_id in sorted(request_ids):
        matched_playbooks.extend(playbooks_by_request_id.get(request_id, []))
    if not matched_playbooks:
        for resource_id in sorted(resource_ids):
            matched_playbooks.extend(playbooks_by_resource_id.get(resource_id, []))
    if not matched_playbooks:
        return []

    content_tokens = _planner_action_content_tokens(row)
    if not content_tokens:
        return [
            f"{collection_name}[{index}] has no substantive query/action terms "
            "to ground against the queued request_playbook"
        ]
    for playbook in matched_playbooks:
        if content_tokens & _playbook_grounding_tokens(playbook):
            return []
    return [
        f"{collection_name}[{index}] is not grounded in the queued request_playbook "
        "operator_prompt, input_summary, expected_response_fields, or acceptance_checklist"
    ]


def _planner_action_content_tokens(row: Mapping[str, Any]) -> set[str]:
    text_parts = [
        str(row.get(field_name, ""))
        for field_name in (
            "query",
            "reason",
            "action",
            "rationale",
            "description",
            "route_repair",
            "repair_action",
        )
    ]
    return _grounding_tokens(" ".join(text_parts))


def _playbook_grounding_tokens(playbook: Mapping[str, Any]) -> set[str]:
    text_parts = [
        str(playbook.get("operator_prompt", "")),
        str(playbook.get("expected_response_artifact", "")),
        " ".join(_str_tuple(playbook.get("required_inputs", []))),
        " ".join(_str_tuple(playbook.get("expected_response_fields", []))),
        " ".join(_str_tuple(playbook.get("acceptance_checklist", []))),
        " ".join(_str_tuple(playbook.get("rejection_triggers", []))),
        " ".join(_str_tuple(playbook.get("stop_conditions", []))),
        json.dumps(_dict_value(playbook, "input_summary"), default=str),
    ]
    return _grounding_tokens(" ".join(text_parts))


def _grounding_tokens(text: str) -> set[str]:
    stopwords = {
        "action",
        "adapter",
        "artifact",
        "check",
        "contract",
        "dispatch",
        "evidence",
        "expected",
        "field",
        "fields",
        "find",
        "gate",
        "grounded",
        "literature",
        "planner",
        "prompt",
        "query",
        "queued",
        "request",
        "response",
        "resource",
        "route",
        "search",
        "source",
        "theorem",
        "tool",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9_]+", str(text or "").lower())
        if len(token) >= 4 and token not in stopwords
    }


def _structured_resource_refs(row: Mapping[str, Any]) -> dict[str, list[str]]:
    refs = {
        "resource_request_ids": [],
        "resource_ids": [],
        "resource_contract_ids": [],
        "tool_owner_ids": [],
    }

    def visit(value: Any, *, key_hint: str = "") -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                key_text = _primitive_key(key)
                if key_text in {"resource_request_id", "resource_request_ids"}:
                    refs["resource_request_ids"].extend(_str_tuple(item))
                elif key_text in {
                    "resource_id",
                    "resource_ids",
                    "resource",
                    "resources",
                    "adapter_id",
                    "adapter_ids",
                    "mcp_or_cli_hint",
                }:
                    refs["resource_ids"].extend(_str_tuple(item))
                elif key_text in {
                    "resource_contract_id",
                    "resource_contract_ids",
                    "resource_contract",
                    "resource_contracts",
                }:
                    refs["resource_contract_ids"].extend(_str_tuple(item))
                elif key_text in {
                    "owner",
                    "tool",
                    "tools",
                    "tool_name",
                    "tool_names",
                    "recommended_tool",
                    "recommended_tools",
                }:
                    refs["tool_owner_ids"].extend(_str_tuple(item))
                visit(item, key_hint=key_text)
        elif isinstance(value, (list, tuple, set)):
            for item in value:
                visit(item, key_hint=key_hint)

    visit(row)
    return refs


def _resource_ref_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def _resource_owner_looks_like_tool(value: str) -> bool:
    return any(
        token in value
        for token in (
            "adapter",
            "api",
            "cli",
            "lean_lsp",
            "leansearch",
            "loogle",
            "mcp",
            "paperclip",
            "paperqa",
            "prover",
            "tool",
        )
    )


def _response_primitive_coherence_errors(
    *,
    selected_primitives: tuple[str, ...],
    standalone_primitives: tuple[dict[str, object], ...],
    informal_nodes: tuple[dict[str, object], ...],
    formal_nodes: tuple[dict[str, object], ...],
    alignment_edges: tuple[dict[str, object], ...],
    minimal_delta: Mapping[str, Any],
    search_requests: tuple[dict[str, object], ...],
    request: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    selected = {_primitive_key(primitive) for primitive in selected_primitives}
    selected.discard("")
    standalone = {
        _primitive_key(primitive.get("primitive", ""))
        for primitive in standalone_primitives
    }
    standalone.discard("")
    formal = {_primitive_key(node.get("primitive", "")) for node in formal_nodes}
    formal.discard("")
    alignment = set()
    informal_by_node_id = {
        str(node.get("node_id", "")): node
        for node in informal_nodes
        if str(node.get("node_id", "")).strip()
    }
    formal_by_node_id = {
        str(node.get("node_id", "")): node
        for node in formal_nodes
        if str(node.get("node_id", "")).strip()
    }
    formal_primitive_by_node_id = {
        str(node.get("node_id", "")): _primitive_key(node.get("primitive", ""))
        for node in formal_nodes
        if str(node.get("node_id", "")).strip()
    }
    alignment_edges_by_primitive: dict[str, list[dict[str, object]]] = {}
    for edge in alignment_edges:
        informal_node_id = str(
            edge.get("informal_node_id") or edge.get("source") or ""
        ).strip()
        formal_node_id = str(edge.get("formal_node_id") or edge.get("target") or "").strip()
        if informal_node_id and informal_node_id not in informal_by_node_id:
            errors.append(
                "route_alignment_edges references unknown informal_node_id: "
                + informal_node_id
            )
        if formal_node_id and formal_node_id not in formal_by_node_id:
            errors.append(
                "route_alignment_edges references unknown formal_node_id: "
                + formal_node_id
            )
        primitive = _primitive_key(edge.get("primitive", ""))
        if not primitive:
            primitive = formal_primitive_by_node_id.get(formal_node_id, "")
        if not primitive:
            primitive = formal_primitive_by_node_id.get(str(edge.get("target", "")), "")
        if primitive:
            alignment.add(primitive)
            alignment_edges_by_primitive.setdefault(primitive, []).append(edge)
    selected_missing_route = sorted(selected - standalone)
    if selected_missing_route:
        errors.append(
            "minimal_delta_plan.selected_primitives missing from standalone_route.primitives: "
            + ", ".join(selected_missing_route)
        )
    selected_missing_formal = sorted(selected - formal)
    if selected_missing_formal:
        errors.append(
            "minimal_delta_plan.selected_primitives missing from formal_realization_dag_nodes: "
            + ", ".join(selected_missing_formal)
        )
    delta_primitives = _minimal_delta_primitives(minimal_delta, selected)
    delta_missing_alignment = sorted(delta_primitives - alignment)
    if delta_missing_alignment:
        errors.append(
            "minimal_delta_plan delta primitives missing route_alignment_edges: "
            + ", ".join(delta_missing_alignment)
        )
    introduced = sorted((selected | delta_primitives) - _available_primitive_keys_for_request(request))
    introduced_selected_missing_alignment = sorted(
        primitive for primitive in introduced if primitive in selected and primitive not in alignment
    )
    if introduced_selected_missing_alignment:
        errors.append(
            "introduced selected primitives require route_alignment_edges: "
            + ", ".join(introduced_selected_missing_alignment)
        )
    errors.extend(
        _introduced_primitive_evidence_errors(
            introduced_primitives=tuple(introduced),
            alignment_edges_by_primitive=alignment_edges_by_primitive,
            informal_by_node_id=informal_by_node_id,
            formal_by_node_id=formal_by_node_id,
            search_requests=search_requests,
        )
    )
    errors.extend(
        _primitive_cost_coverage_evidence_errors(
            minimal_delta=minimal_delta,
            formal_nodes=formal_nodes,
            standalone_primitives=standalone_primitives,
        )
    )
    return errors


def _primitive_cost_coverage_evidence_errors(
    *,
    minimal_delta: Mapping[str, Any],
    formal_nodes: tuple[dict[str, object], ...],
    standalone_primitives: tuple[dict[str, object], ...],
) -> list[str]:
    errors: list[str] = []
    formal_by_primitive: dict[str, list[dict[str, object]]] = {}
    for node in formal_nodes:
        primitive = _primitive_key(node.get("primitive", ""))
        if primitive:
            formal_by_primitive.setdefault(primitive, []).append(node)
    standalone_by_primitive: dict[str, list[dict[str, object]]] = {}
    for row in standalone_primitives:
        primitive = _primitive_key(row.get("primitive", ""))
        if primitive:
            standalone_by_primitive.setdefault(primitive, []).append(row)
    for index, row in enumerate(_dict_tuple(minimal_delta.get("primitive_costs", []))):
        primitive = _primitive_key(row.get("primitive", ""))
        if not primitive:
            continue
        bucket = _primitive_key(row.get("coverage_bucket", ""))
        bucket_cost = _coverage_bucket_base_cost(bucket)
        if bucket_cost is None:
            continue
        evidence_rows = [
            *formal_by_primitive.get(primitive, []),
            *standalone_by_primitive.get(primitive, []),
        ]
        evidence = _coverage_evidence_base_cost(evidence_rows)
        if evidence is None:
            continue
        evidence_cost, evidence_marker = evidence
        if bucket_cost + 1e-9 < evidence_cost:
            errors.append(
                "minimal_delta_plan.primitive_costs"
                f"[{index}].coverage_bucket/base_cost underprices "
                "formal/standalone coverage evidence for primitive "
                f"{primitive}: coverage_bucket={bucket} base_cost={bucket_cost:g} "
                f"but evidence marker {evidence_marker} requires at least "
                f"{evidence_cost:g}"
            )
    return errors


def _coverage_evidence_base_cost(
    rows: list[dict[str, object]],
) -> tuple[float, str] | None:
    best: tuple[float, str] | None = None
    for row in rows:
        for field_name in (
            "coverage_bucket",
            "coverage_status",
            "formalization_action",
            "alignment_status",
        ):
            marker = _primitive_key(row.get(field_name, ""))
            bucket = _coverage_marker_policy_bucket(marker)
            if not bucket:
                continue
            cost = _coverage_bucket_base_cost(bucket)
            if cost is None:
                continue
            label = f"{field_name}={marker}"
            if best is None or cost > best[0]:
                best = (cost, label)
    return best


def _coverage_bucket_base_cost(bucket: str) -> float | None:
    policy = MINIMAL_DELTA_COST_POLICY.get("coverage_bucket_base_cost", {})
    if not isinstance(policy, Mapping):
        return None
    value = policy.get(bucket)
    if not _is_nonnegative_number(value):
        return None
    return float(value)


def _coverage_marker_policy_bucket(marker: str) -> str:
    aliases = {
        "already_exists": "already_exists",
        "exact_exists": "exact_exists",
        "exact": "exact_exists",
        "reuse": "already_exists",
        "compose": "already_exists",
        "compose_existing_declarations": "already_exists",
        "target_prover_replay": "already_exists",
        "different_formulation": "different_formulation",
        "near_exists": "near_exists",
        "near": "near_exists",
        "wrapper": "wrapper",
        "wrapper_needed": "wrapper_needed",
        "write_wrapper": "wrapper",
        "bridge": "bridge",
        "bridge_needed": "bridge_needed",
        "prove_bridge": "bridge",
        "source_port": "source_port",
        "source_port_needed": "source_port_needed",
        "port_external_source": "source_port",
        "new_definition": "new_definition",
        "new_definition_needed": "new_definition",
        "define_new": "new_definition",
        "new_theory": "new_theory",
        "new_theory_needed": "new_theory_needed",
        "first_principles": "new_theory",
        "design_from_first_principles": "new_theory",
        "theory_missing": "new_theory",
        "unknown": "unknown",
        "coverage_unknown": "unknown",
        "declaration_unknown": "unknown",
    }
    return aliases.get(marker, "")


def _realization_coverage_witness(
    *,
    request: Mapping[str, Any],
    minimal_delta: Mapping[str, Any],
    standalone_route: Mapping[str, Any],
    formal_nodes: tuple[dict[str, object], ...],
    alignment_edges: tuple[dict[str, object], ...],
) -> dict[str, object]:
    selected_order = tuple(
        dict.fromkeys(
            primitive
            for primitive in (
                _primitive_key(item)
                for item in _str_tuple(minimal_delta.get("selected_primitives", []))
            )
            if primitive
        )
    )
    selected = set(selected_order)
    standalone = {
        primitive
        for primitive in (
            _primitive_key(row.get("primitive", ""))
            for row in _dict_tuple(standalone_route.get("primitives", []))
        )
        if primitive
    }
    formal = {
        primitive
        for primitive in (
            _primitive_key(row.get("primitive", ""))
            for row in formal_nodes
        )
        if primitive
    }
    aligned = _alignment_primitive_keys(alignment_edges, formal_nodes)
    delta_primitives = _minimal_delta_primitives(minimal_delta, selected)
    available = _available_primitive_keys_for_request(request)
    introduced = (selected | delta_primitives) - available

    selected_missing_route = tuple(
        primitive for primitive in selected_order if primitive not in standalone
    )
    selected_missing_formal = tuple(
        primitive for primitive in selected_order if primitive not in formal
    )
    delta_missing_alignment = tuple(
        primitive for primitive in sorted(delta_primitives) if primitive not in aligned
    )
    introduced_missing_alignment = tuple(
        primitive for primitive in sorted(introduced) if primitive not in aligned
    )
    return {
        "selected_primitives": list(selected_order),
        "delta_primitives": sorted(delta_primitives),
        "introduced_primitives": sorted(introduced),
        "aligned_primitives": sorted(aligned),
        "selected_primitives_with_standalone_route_node": [
            primitive for primitive in selected_order if primitive in standalone
        ],
        "selected_primitives_missing_standalone_route_node": list(
            selected_missing_route
        ),
        "selected_primitives_with_formal_realization_node": [
            primitive for primitive in selected_order if primitive in formal
        ],
        "selected_primitives_missing_formal_realization_node": list(
            selected_missing_formal
        ),
        "delta_primitives_with_route_alignment_edge": [
            primitive for primitive in sorted(delta_primitives) if primitive in aligned
        ],
        "delta_primitives_missing_route_alignment_edge": list(
            delta_missing_alignment
        ),
        "introduced_primitives_with_route_alignment_edge": [
            primitive for primitive in sorted(introduced) if primitive in aligned
        ],
        "introduced_primitives_missing_route_alignment_edge": list(
            introduced_missing_alignment
        ),
        "selected_route_coverage_complete": bool(selected_order)
        and not selected_missing_route,
        "selected_formal_coverage_complete": bool(selected_order)
        and not selected_missing_formal,
        "delta_alignment_complete": not delta_missing_alignment,
        "introduced_alignment_complete": not introduced_missing_alignment,
        "realization_coverage_complete": bool(selected_order)
        and not selected_missing_route
        and not selected_missing_formal
        and not delta_missing_alignment
        and not introduced_missing_alignment,
    }


def _alignment_primitive_keys(
    alignment_edges: tuple[dict[str, object], ...],
    formal_nodes: tuple[dict[str, object], ...],
) -> set[str]:
    formal_primitive_by_node_id = {
        str(node.get("node_id", "")): _primitive_key(node.get("primitive", ""))
        for node in formal_nodes
        if str(node.get("node_id", "")).strip()
    }
    aligned: set[str] = set()
    for edge in alignment_edges:
        primitive = _primitive_key(edge.get("primitive", ""))
        if not primitive:
            formal_node_id = str(
                edge.get("formal_node_id") or edge.get("target") or ""
            ).strip()
            primitive = formal_primitive_by_node_id.get(formal_node_id, "")
        if primitive:
            aligned.add(primitive)
    aligned.discard("")
    return aligned


def _minimal_delta_primitives(
    minimal_delta: Mapping[str, Any],
    selected: set[str],
) -> set[str]:
    explicit: set[str] = set()
    for field_name in (
        "wrapper_lemmas",
        "bridge_lemmas",
        "source_port_lemmas",
        "new_definitions",
        "new_theory_primitives",
        "first_principles_primitives",
    ):
        explicit.update(_primitive_key(item) for item in _str_tuple(minimal_delta.get(field_name, [])))
    explicit.discard("")
    return explicit or set(selected)


def _introduced_primitive_evidence_errors(
    *,
    introduced_primitives: tuple[str, ...],
    alignment_edges_by_primitive: Mapping[str, list[dict[str, object]]],
    informal_by_node_id: Mapping[str, dict[str, object]],
    formal_by_node_id: Mapping[str, dict[str, object]],
    search_requests: tuple[dict[str, object], ...],
) -> list[str]:
    errors: list[str] = []
    for primitive in introduced_primitives:
        edges = alignment_edges_by_primitive.get(primitive, [])
        if not edges:
            errors.append(
                "introduced selected/delta primitives require route_alignment_edges: "
                + primitive
            )
            continue
        informal_nodes = tuple(
            informal_by_node_id[node_id]
            for node_id in _aligned_node_ids(edges, "informal_node_id", "source")
            if node_id in informal_by_node_id
        )
        formal_nodes = tuple(
            formal_by_node_id[node_id]
            for node_id in _aligned_node_ids(edges, "formal_node_id", "target")
            if node_id in formal_by_node_id
        )
        if not any(
            _informal_node_supports_introduced_primitive(
                node,
                primitive=primitive,
                search_requests=search_requests,
            )
            for node in informal_nodes
        ):
            errors.append(
                "introduced primitive requires aligned informal evidence "
                "(grounded source_refs, matching literature search_request, "
                f"or formal_gap_boundary): {primitive}"
            )
        if not any(
            _formal_node_supports_introduced_primitive(
                node,
                primitive=primitive,
                search_requests=search_requests,
            )
            for node in formal_nodes
        ):
            errors.append(
                "introduced primitive requires aligned formal realization evidence "
                "(grounded reuse declarations, delta action, matching formal_library "
                f"search_request, or formal gap boundary): {primitive}"
            )
    return errors


def _aligned_node_ids(
    edges: tuple[dict[str, object], ...] | list[dict[str, object]],
    primary_field: str,
    fallback_field: str,
) -> tuple[str, ...]:
    return _str_tuple(
        [
            str(edge.get(primary_field) or edge.get(fallback_field) or "").strip()
            for edge in edges
        ]
    )


def _informal_node_supports_introduced_primitive(
    node: Mapping[str, Any],
    *,
    primitive: str,
    search_requests: tuple[dict[str, object], ...],
) -> bool:
    if _str_tuple(node.get("source_refs", [])):
        return True
    if str(node.get("formal_gap_boundary", "")).strip():
        return True
    status = _source_ref_key(node.get("source_search_status", ""))
    if status in {"formal_gap_boundary", "formal_boundary_declared"}:
        return True
    if status in {
        "search_requested",
        "source_search_requested",
        "source_search_pending",
        "literature_search_requested",
        "literature_search_pending",
    }:
        return _has_search_request_for_primitive(
            search_requests,
            primitive=primitive,
            request_kind_keys=("literature", "source", "paper", "textbook"),
        )
    return False


def _formal_node_supports_introduced_primitive(
    node: Mapping[str, Any],
    *,
    primitive: str,
    search_requests: tuple[dict[str, object], ...],
) -> bool:
    if _primitive_key(node.get("primitive", "")) != primitive:
        return False
    if _formal_node_claims_existing_library(node):
        return bool(_node_candidate_declarations(node))
    if str(node.get("formal_gap_boundary", "")).strip():
        return True
    markers = (
        node.get("coverage_bucket", ""),
        node.get("coverage_status", ""),
        node.get("formalization_action", ""),
        node.get("alignment_status", ""),
    )
    if any(_delta_formalization_marker(marker) for marker in markers):
        return True
    return _has_search_request_for_primitive(
        search_requests,
        primitive=primitive,
        request_kind_keys=("formal_library", "library", "prover_feedback"),
    )


def _delta_formalization_marker(value: object) -> bool:
    key = _primitive_key(value)
    return key in {
        "wrapper",
        "wrapper_needed",
        "write_wrapper",
        "bridge",
        "bridge_needed",
        "prove_bridge",
        "source_port",
        "source_port_needed",
        "port_external_source",
        "define_new",
        "new_definition",
        "new_definitions",
        "definition_missing",
        "definition_or_theory_missing",
        "new_theory",
        "new_theory_needed",
        "first_principles",
        "design_from_first_principles",
        "missing",
        "theory_missing",
    }


def _has_search_request_for_primitive(
    search_requests: tuple[dict[str, object], ...],
    *,
    primitive: str,
    request_kind_keys: tuple[str, ...],
) -> bool:
    primitive_key = _primitive_key(primitive)
    if not primitive_key:
        return False
    for request in search_requests:
        kind_key = _primitive_key(request.get("request_kind", ""))
        if request_kind_keys and not any(key in kind_key for key in request_kind_keys):
            continue
        text_key = _primitive_key(
            " ".join(
                str(request.get(field_name, ""))
                for field_name in ("query", "reason", "action", "description")
            )
        )
        if primitive_key in text_key:
            return True
    return False


def _available_primitive_keys_for_request(request: Mapping[str, Any]) -> set[str]:
    primitives: list[str] = []
    _collect_primitive_values(request.get("target_route", {}), primitives)
    _collect_primitive_values(_dict_value(request, "context_packet"), primitives)
    return {
        primitive
        for primitive in (_primitive_key(value) for value in primitives)
        if primitive
    }


def _collect_primitive_values(value: Any, primitives: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if key_text == "coverage_updates" and isinstance(item, Mapping):
                primitives.extend(str(primitive) for primitive in item.keys())
            if key_text in {
                "primitive",
                "primitives",
                "selected_primitives",
                "required_primitives",
                "delta_primitives",
                "original_selected_primitives",
                "revised_selected_primitives",
                "revised_delta_primitives",
                "added_primitives",
                "added_delta_primitives",
                "alignment_edge_primitives",
                "wrapper_lemmas",
                "bridge_lemmas",
                "source_port_lemmas",
                "new_definitions",
                "new_theory_primitives",
                "first_principles_primitives",
                "add_bridge_lemmas",
                "add_first_principles",
            }:
                primitives.extend(_primitive_values(item))
            _collect_primitive_values(item, primitives)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _collect_primitive_values(item, primitives)


def _primitive_values(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value.strip() else tuple()
    if isinstance(value, Mapping):
        values: list[str] = []
        for key in ("primitive", "name", "id"):
            if key in value:
                values.extend(_primitive_values(value.get(key)))
        return _str_tuple(values)
    if isinstance(value, (list, tuple, set)):
        values: list[str] = []
        for item in value:
            values.extend(_primitive_values(item))
        return _str_tuple(values)
    return tuple()


def _primitive_key(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def _context_payloads(
    errors: list[str],
    *,
    formalization_gap_planner_target_intake_dir: Path | None,
    goal_conditioned_minimal_formalization_plan_dir: Path | None,
    formalization_gap_planner_library_coverage_map_dir: Path | None,
    formalization_gap_planner_source_grounding_audit_dir: Path | None,
    formalization_gap_planner_resource_request_queue_dir: Path | None,
    formalization_gap_planner_resource_response_ledger_dir: Path | None,
    formalization_gap_planner_refinement_evidence_dir: Path | None,
    formalization_gap_planner_route_revision_overlay_dir: Path | None,
    formalization_gap_planner_interactive_session_dir: Path | None,
    formalization_gap_planner_component_resource_registry_dir: Path | None,
) -> dict[str, Any]:
    return {
        "target_intake": _optional_manifest(
            formalization_gap_planner_target_intake_dir,
            "formalization_gap_planner_target_intake_manifest.json",
            errors,
        ),
        "goal_plan": _optional_manifest(
            goal_conditioned_minimal_formalization_plan_dir,
            "goal_conditioned_minimal_formalization_plan_manifest.json",
            errors,
        ),
        "library_coverage_map": _optional_manifest(
            formalization_gap_planner_library_coverage_map_dir,
            "formalization_gap_planner_library_coverage_map_manifest.json",
            errors,
        ),
        "source_grounding_audit": _optional_manifest(
            formalization_gap_planner_source_grounding_audit_dir,
            "formalization_gap_planner_source_grounding_audit_manifest.json",
            errors,
        ),
        "resource_request_queue": _optional_manifest(
            formalization_gap_planner_resource_request_queue_dir,
            "formalization_gap_planner_resource_request_queue_manifest.json",
            errors,
        ),
        "resource_response_ledger": _optional_manifest(
            formalization_gap_planner_resource_response_ledger_dir,
            "formalization_gap_planner_resource_response_ledger_manifest.json",
            errors,
        ),
        "refinement_evidence": _optional_manifest(
            formalization_gap_planner_refinement_evidence_dir,
            "formalization_gap_planner_refinement_evidence_manifest.json",
            errors,
        ),
        "route_revision_overlay": _optional_manifest(
            formalization_gap_planner_route_revision_overlay_dir,
            "formalization_gap_planner_route_revision_overlay_manifest.json",
            errors,
        ),
        "interactive_session": _optional_manifest(
            formalization_gap_planner_interactive_session_dir,
            "formalization_gap_planner_interactive_session_manifest.json",
            errors,
        ),
        "component_resource_registry": _optional_manifest(
            formalization_gap_planner_component_resource_registry_dir,
            "formalization_gap_planner_component_resource_registry_manifest.json",
            errors,
        ),
    }


def _optional_manifest(
    directory: Path | None,
    filename: str,
    errors: list[str],
) -> dict[str, Any]:
    if directory is None:
        return {}
    return _read_json(directory / filename, errors)


def _rows_for_route(
    payload: Any,
    route_ids: str | tuple[str, ...],
    *,
    row_key: str = "rows",
) -> tuple[dict[str, object], ...]:
    if not isinstance(payload, Mapping):
        return tuple()
    route_id_set = {str(route_id) for route_id in _str_tuple(route_ids) if str(route_id)}
    rows = payload.get(row_key, [])
    if not isinstance(rows, list):
        return tuple()
    matched: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        candidate_ids = {
            str(row.get("route_id", "")),
            str(row.get("standalone_route_id", "")),
            str(row.get("goal_plan_id", "")),
        }
        if route_id_set.intersection(candidate_ids) or not route_id_set:
            matched.append(_compact_row(row))
    return tuple(matched[:25])


def _component_resource_registry_context(
    payload: Any,
    *,
    target_prover_family: str,
) -> dict[str, object]:
    if not isinstance(payload, Mapping):
        return {}
    target = str(target_prover_family or "").strip().lower()
    all_resource_rows = tuple(_dict_tuple(payload.get("resource_rows", [])))
    resource_row_by_id = {
        str(row.get("resource_id", "")).strip(): row
        for row in all_resource_rows
        if str(row.get("resource_id", "")).strip()
    }
    resource_rows = [
        _compact_row(row)
        for row in all_resource_rows
        if _resource_targets_match(row, target)
    ][:40]
    compatible_resource_ids = {
        str(row.get("resource_id", "")).strip()
        for row in resource_rows
        if str(row.get("resource_id", "")).strip()
    }
    component_rows = [
        _target_filtered_registry_row(
            _compact_row(row),
            compatible_resource_ids=compatible_resource_ids,
            resource_row_by_id=resource_row_by_id,
            target_prover_family=target,
        )
        for row in _dict_tuple(payload.get("component_rows", []))
    ][:20]
    execution_plan_rows = [
        _target_filtered_registry_row(
            _compact_row(row),
            compatible_resource_ids=compatible_resource_ids,
            resource_row_by_id=resource_row_by_id,
            target_prover_family=target,
        )
        for row in _dict_tuple(payload.get("execution_plan_rows", []))
    ][:20]
    referenced_resource_ids = set(compatible_resource_ids)
    referenced_resource_ids.update(_resource_ids_for_registry_context(component_rows))
    referenced_resource_ids.update(
        _resource_ids_for_registry_context(execution_plan_rows)
    )
    resource_contract_rows = [
        _compact_row(row)
        for row in _dict_tuple(payload.get("resource_contract_rows", []))
        if (
            str(row.get("resource_id", "")).strip() in referenced_resource_ids
            and _resource_targets_match(row, target)
        )
    ][:40]
    context = {
        "component_resource_registry_fingerprint": str(
            payload.get("component_resource_registry_fingerprint", "")
        ),
        "proof_evidence_boundary": str(
            payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)
        ),
        "usage_order": _str_tuple(payload.get("usage_order", [])),
        "limitations": _str_tuple(payload.get("limitations", [])),
        "component_rows": tuple(component_rows),
        "execution_plan_rows": tuple(execution_plan_rows),
        "resource_rows": tuple(resource_rows),
        "resource_contract_rows": tuple(resource_contract_rows),
    }
    return context if any(context[key] for key in ("component_rows", "resource_rows")) else {}


def _target_filtered_registry_row(
    row: dict[str, object],
    *,
    compatible_resource_ids: set[str],
    resource_row_by_id: Mapping[str, Mapping[str, object]],
    target_prover_family: str,
) -> dict[str, object]:
    filtered = dict(row)
    for field_name in (
        "local_fallback_resource_ids",
        "frontier_resource_ids",
        "local_first_resource_ids",
        "frontier_escalation_resource_ids",
        "resource_ids",
    ):
        if field_name not in filtered:
            continue
        filtered[field_name] = tuple(
            resource_id
            for resource_id in _str_tuple(filtered.get(field_name, []))
            if resource_id in compatible_resource_ids
        )
    if "adapter_ids" in filtered:
        adapter_ids = tuple(
            adapter_id
            for adapter_id in _str_tuple(filtered.get("adapter_ids", []))
            if _adapter_targets_match(
                adapter_id,
                target_prover_family=target_prover_family,
                compatible_resource_ids=compatible_resource_ids,
                resource_row_by_id=resource_row_by_id,
            )
        )
        filtered["adapter_ids"] = adapter_ids
        statuses = filtered.get("detected_adapter_statuses", {})
        if isinstance(statuses, Mapping):
            filtered["detected_adapter_statuses"] = {
                adapter_id: statuses[adapter_id]
                for adapter_id in adapter_ids
                if adapter_id in statuses
            }
    return filtered


def _adapter_targets_match(
    adapter_id: str,
    *,
    target_prover_family: str,
    compatible_resource_ids: set[str],
    resource_row_by_id: Mapping[str, Mapping[str, object]],
) -> bool:
    adapter = str(adapter_id or "").strip()
    if not adapter:
        return False
    if adapter in compatible_resource_ids:
        return True
    target = _target_prover_key(target_prover_family)
    resource_row = resource_row_by_id.get(adapter)
    if resource_row is not None:
        return _resource_targets_match(resource_row, target)
    key = _resource_ref_key(adapter)
    target_specific_tokens = {
        "lean4": ("lean", "lake", "loogle", "mathlib", "leandojo"),
        "rocq": ("rocq", "coq", "serapi"),
        "isabelle": ("isabelle", "sledgehammer", "afp"),
        "agda": ("agda",),
    }
    for prover_key, tokens in target_specific_tokens.items():
        if any(token in key for token in tokens):
            return target == prover_key
    return True


def _component_resource_context_from_request(
    request: Mapping[str, Any],
) -> dict[str, object]:
    context = _dict_value(request, "context_packet")
    registry_context = context.get("component_resource_registry_context", {})
    return dict(registry_context) if isinstance(registry_context, Mapping) else {}


def _feedback_loop_summary(
    context_packet: Mapping[str, Any],
    *,
    residual_goals: tuple[str, ...],
) -> dict[str, object]:
    row_fields = (
        "library_coverage_rows",
        "source_grounding_rows",
        "resource_request_queue_rows",
        "resource_response_ledger_rows",
        "refinement_evidence_rows",
        "route_revision_overlay_rows",
        "interactive_session_rows",
        "interactive_decision_policy_rows",
        "current_goal_plan_rows",
    )
    rows_by_field = {
        field_name: _dict_tuple(context_packet.get(field_name, []))
        for field_name in row_fields
    }
    evidence_counts = {
        field_name: len(rows)
        for field_name, rows in rows_by_field.items()
        if rows
    }
    resource_response_admissibility = _resource_response_admissibility_summary(
        rows_by_field.get("resource_response_ledger_rows", ())
    )
    refinement_evidence_admissibility = _refinement_evidence_admissibility_summary(
        rows_by_field.get("refinement_evidence_rows", ())
    )
    all_rows = tuple(row for rows in rows_by_field.values() for row in rows)
    actionable_rows_by_field = dict(rows_by_field)
    actionable_rows_by_field["resource_response_ledger_rows"] = tuple(
        row
        for row in rows_by_field.get("resource_response_ledger_rows", ())
        if _resource_response_row_is_admissible_feedback(row)
    )
    actionable_rows_by_field["refinement_evidence_rows"] = tuple(
        row
        for row in rows_by_field.get("refinement_evidence_rows", ())
        if _refinement_evidence_row_is_admissible_feedback(row)
    )
    actionable_rows = tuple(
        row for rows in actionable_rows_by_field.values() for row in rows
    )
    replan_metadata = _dict_value(context_packet, "replan_metadata")
    if not residual_goals and not evidence_counts and not replan_metadata:
        return {}

    route_revision_reasons = _unique_strings(
        _collect_row_values(actionable_rows, "route_revision_reasons")
    )
    repair_focus = _unique_strings(
        [
            *residual_goals,
            *route_revision_reasons,
            *_collect_row_values(actionable_rows, "triage_class"),
            *_collect_row_values(actionable_rows, "triage_required_gate"),
            *_collect_row_values(actionable_rows, "next_required_gate"),
        ]
    )
    recommended_next_actions = _feedback_next_actions(
        rows_by_field,
        residual_goals=residual_goals,
    )
    realization_coverage = _realization_feedback_summary(
        context_packet,
        all_rows,
    )
    realization_replan_required = (
        bool(realization_coverage)
        and realization_coverage.get("complete") is False
    )
    if realization_coverage:
        recommended_next_actions = _merge_dict_rows(
            recommended_next_actions,
            _realization_feedback_next_actions(realization_coverage),
            key_fields=("source", "action", "target_primitives"),
        )
    replan_required = any(
        _truthy(row.get(field_name))
        for row in actionable_rows
        for field_name in (
            "replan_required",
            "needs_route_replanning",
                "route_revision_recommended",
            )
    ) or realization_replan_required
    needs_more_library_grounding = any(
        _truthy(row.get("needs_more_lean_grounding"))
        or _truthy(row.get("needs_more_library_grounding"))
        for row in all_rows
    ) or bool(
        realization_coverage.get("missing_selected_formal_primitives", ())
        if realization_coverage
        else ()
    )
    summary: dict[str, object] = {
        "summary_kind": "formalization_gap_planner_feedback_loop_summary",
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "residual_goal_count": len(residual_goals),
        "residual_goals": list(residual_goals[:20]),
        "evidence_counts": evidence_counts,
        "resource_response_admissibility": resource_response_admissibility,
        "refinement_evidence_admissibility": refinement_evidence_admissibility,
        "response_acceptance_status_counts": _value_counts(
            _collect_row_values(all_rows, "acceptance_status")
        ),
        "source_grounding_status_counts": _value_counts(
            _collect_row_values(all_rows, "source_grounding_status")
        ),
        "coverage_status_counts": _value_counts(
            [
                *_collect_row_values(all_rows, "coverage_status"),
                *_collect_row_values(all_rows, "coverage_bucket"),
            ]
        ),
        "route_revision_statuses": list(
            _unique_strings(
                [
                    *_collect_row_values(all_rows, "revision_status"),
                    *_collect_row_values(all_rows, "stability_decision"),
                    *_collect_row_values(all_rows, "session_state"),
                ]
            )[:20]
        ),
        "replan_required": replan_required,
        "needs_more_literature": any(
            _truthy(row.get("needs_more_literature")) for row in all_rows
        ),
        "needs_more_library_grounding": needs_more_library_grounding,
        "needs_more_proof_state_feedback": any(
            _truthy(row.get("needs_more_proof_state_feedback")) for row in all_rows
        ),
        "repair_focus": list(repair_focus[:20]),
        "route_revision_reasons": list(route_revision_reasons[:20]),
        "admissible_source_refs": list(
            _unique_strings(
                list(_str_tuple(context_packet.get("available_source_refs", [])))
            )[:25]
        ),
        "admissible_source_snippets": _collect_source_snippets(actionable_rows)[:12],
        "admissible_formal_declarations": list(
            _unique_strings(
                list(
                    _str_tuple(context_packet.get("available_formal_declarations", []))
                )
            )[:25]
        ),
        "recommended_next_actions": recommended_next_actions,
    }
    resource_request_playbooks = _dict_tuple(
        context_packet.get("resource_request_playbooks", [])
    )
    if resource_request_playbooks:
        summary["resource_request_playbook_count"] = len(resource_request_playbooks)
        summary["resource_request_playbooks"] = resource_request_playbooks[:12]
    if realization_coverage:
        summary["realization_coverage"] = realization_coverage
    if replan_metadata:
        summary["prior_replan_metadata"] = {
            key: replan_metadata[key]
            for key in (
                "source_route_id",
                "llm_route_planner_row_id",
                "llm_route_planner_acceptance_status",
                "revised_selected_primitives",
                "residual_goals",
                "alignment_edge_primitives",
                "llm_route_planner_realization_coverage_witness",
                "realization_coverage_witness",
            )
            if key in replan_metadata
        }
    return summary


def _realization_feedback_summary(
    context_packet: Mapping[str, Any],
    rows: tuple[dict[str, object], ...],
) -> dict[str, object]:
    witnesses: list[dict[str, object]] = []
    current_route = _dict_value(context_packet, "current_route")
    route_witness = _compact_realization_witness(
        current_route.get("realization_coverage_witness", {})
    )
    if route_witness:
        witnesses.append({"source": "current_route", **route_witness})
    replan_metadata = _dict_value(context_packet, "replan_metadata")
    for metadata_key in (
        "llm_route_planner_realization_coverage_witness",
        "realization_coverage_witness",
    ):
        metadata_witness = _compact_realization_witness(replan_metadata.get(metadata_key, {}))
        if metadata_witness:
            witnesses.append({"source": f"replan_metadata.{metadata_key}", **metadata_witness})
    for row in rows:
        trace = _dict_value(row, "standalone_input_trace")
        trace_witness = _compact_realization_witness(
            trace.get("realization_coverage_witness", {})
        )
        if trace_witness:
            witnesses.append(
                {
                    "source": "standalone_input_trace",
                    "goal_plan_id": str(row.get("goal_plan_id", "")),
                    "route_id": str(row.get("route_id", "")),
                    **trace_witness,
                }
            )
    deduped: list[dict[str, object]] = []
    seen: set[str] = set()
    for witness in witnesses:
        fingerprint = stable_hash(
            [
                witness.get("selected_primitives", []),
                witness.get("delta_primitives", []),
                witness.get("selected_primitives_missing_formal_realization_node", []),
                witness.get("delta_primitives_missing_route_alignment_edge", []),
                witness.get("realization_coverage_complete", False),
            ]
        )
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        deduped.append(witness)
    if not deduped:
        return {}
    missing_selected = _unique_strings(
        primitive
        for witness in deduped
        for primitive in _str_tuple(
            witness.get("selected_primitives_missing_formal_realization_node", [])
        )
    )
    missing_delta = _unique_strings(
        primitive
        for witness in deduped
        for primitive in _str_tuple(
            witness.get("delta_primitives_missing_route_alignment_edge", [])
        )
    )
    return {
        "witness_count": len(deduped),
        "complete": all(
            bool(witness.get("realization_coverage_complete", False))
            for witness in deduped
        ),
        "missing_selected_formal_primitives": list(missing_selected[:20]),
        "missing_delta_alignment_primitives": list(missing_delta[:20]),
        "witnesses": deduped[:8],
    }


def _compact_realization_witness(value: object) -> dict[str, object]:
    witness = value if isinstance(value, Mapping) else {}
    if not witness:
        return {}
    list_fields = (
        "selected_primitives",
        "delta_primitives",
        "introduced_primitives",
        "aligned_primitives",
        "selected_primitives_missing_standalone_route_node",
        "selected_primitives_missing_formal_realization_node",
        "delta_primitives_missing_route_alignment_edge",
        "introduced_primitives_missing_route_alignment_edge",
    )
    compact: dict[str, object] = {
        field_name: list(_str_tuple(witness.get(field_name, [])))
        for field_name in list_fields
        if _str_tuple(witness.get(field_name, []))
    }
    compact["realization_coverage_complete"] = bool(
        witness.get("realization_coverage_complete", False)
    )
    return compact


def _realization_feedback_next_actions(
    realization_coverage: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    actions: list[dict[str, object]] = []
    missing_selected = _str_tuple(
        realization_coverage.get("missing_selected_formal_primitives", [])
    )
    if missing_selected:
        actions.append(
            {
                "source": "realization_coverage_witness",
                "owner": "formalizer",
                "action": "add_or_reformulate_formal_realization_nodes",
                "target_primitives": list(missing_selected[:12]),
                "reason": "selected primitives lack formal-realization DAG coverage",
            }
        )
    missing_delta = _str_tuple(
        realization_coverage.get("missing_delta_alignment_primitives", [])
    )
    if missing_delta:
        actions.append(
            {
                "source": "realization_coverage_witness",
                "owner": "formalization_gap_planner",
                "action": "add_route_alignment_edges_for_delta_primitives",
                "target_primitives": list(missing_delta[:12]),
                "reason": "delta primitives lack informal-to-formal route alignment edges",
            }
        )
    return tuple(actions)


def _resource_response_admissibility_summary(
    rows: tuple[dict[str, object], ...],
) -> dict[str, object]:
    admissible_ids: list[str] = []
    status_only_ids: list[str] = []
    rejected_ids: list[str] = []
    awaiting_ids: list[str] = []
    absent_response_ids: list[str] = []
    failed_contract_ids: list[str] = []
    playbook_present_ids: list[str] = []
    playbook_grounded_ids: list[str] = []
    playbook_grounding_failed_ids: list[str] = []
    for row in rows:
        request_id = str(row.get("resource_request_id", "")).strip()
        if not request_id:
            request_id = str(row.get("resource_response_ledger_id", "")).strip()
        status = str(row.get("acceptance_status", "")).strip()
        request_playbook_present = _truthy(row.get("request_playbook_present"))
        response_playbook_grounded = _truthy(row.get("response_playbook_grounded"))
        if request_playbook_present:
            playbook_present_ids.append(request_id)
        if request_playbook_present and response_playbook_grounded:
            playbook_grounded_ids.append(request_id)
        if (
            request_playbook_present
            and _truthy(row.get("response_present"))
            and not response_playbook_grounded
        ):
            playbook_grounding_failed_ids.append(request_id)
        if _resource_response_row_is_admissible_feedback(row):
            admissible_ids.append(request_id)
            continue
        status_only_ids.append(request_id)
        if status == "AWAITING_RESOURCE_RESPONSE":
            awaiting_ids.append(request_id)
        if status.startswith("REJECTED_"):
            rejected_ids.append(request_id)
        if not _truthy(row.get("response_present")):
            absent_response_ids.append(request_id)
        if (
            not _truthy(row.get("response_contract_ok"))
            or (
                "response_contract_minimum_met" in row
                and not _truthy(row.get("response_contract_minimum_met"))
            )
        ):
            failed_contract_ids.append(request_id)
    return {
        "total_count": len(rows),
        "admissible_count": len(admissible_ids),
        "status_only_count": len(status_only_ids),
        "admissible_request_ids": list(_unique_strings(admissible_ids)[:20]),
        "status_only_request_ids": list(_unique_strings(status_only_ids)[:20]),
        "rejected_request_ids": list(_unique_strings(rejected_ids)[:20]),
        "awaiting_request_ids": list(_unique_strings(awaiting_ids)[:20]),
        "absent_response_request_ids": list(_unique_strings(absent_response_ids)[:20]),
        "failed_contract_request_ids": list(_unique_strings(failed_contract_ids)[:20]),
        "request_playbook_present_count": len(playbook_present_ids),
        "playbook_grounded_count": len(playbook_grounded_ids),
        "playbook_grounding_failed_count": len(playbook_grounding_failed_ids),
        "playbook_grounded_request_ids": list(
            _unique_strings(playbook_grounded_ids)[:20]
        ),
        "playbook_grounding_failed_request_ids": list(
            _unique_strings(playbook_grounding_failed_ids)[:20]
        ),
    }


def _refinement_evidence_admissibility_summary(
    rows: tuple[dict[str, object], ...],
) -> dict[str, object]:
    admissible_ids: list[str] = []
    status_only_ids: list[str] = []
    rejected_ids: list[str] = []
    awaiting_ids: list[str] = []
    failed_contract_ids: list[str] = []
    for row in rows:
        evidence_id = str(row.get("refinement_evidence_id", "")).strip()
        if not evidence_id:
            evidence_id = str(row.get("refinement_item_id", "")).strip()
        status = str(row.get("acceptance_status", "")).strip()
        if _refinement_evidence_row_is_admissible_feedback(row):
            admissible_ids.append(evidence_id)
            continue
        status_only_ids.append(evidence_id)
        if status.startswith("AWAITING_"):
            awaiting_ids.append(evidence_id)
        if status.startswith("REJECTED_"):
            rejected_ids.append(evidence_id)
        if (
            "response_contract_ok" in row
            and not _truthy(row.get("response_contract_ok"))
        ) or ("ok" in row and not _truthy(row.get("ok"))):
            failed_contract_ids.append(evidence_id)
    return {
        "total_count": len(rows),
        "admissible_count": len(admissible_ids),
        "status_only_count": len(status_only_ids),
        "admissible_evidence_ids": list(_unique_strings(admissible_ids)[:20]),
        "status_only_evidence_ids": list(_unique_strings(status_only_ids)[:20]),
        "rejected_evidence_ids": list(_unique_strings(rejected_ids)[:20]),
        "awaiting_evidence_ids": list(_unique_strings(awaiting_ids)[:20]),
        "failed_contract_evidence_ids": list(_unique_strings(failed_contract_ids)[:20]),
    }


def _feedback_next_actions(
    rows_by_field: Mapping[str, tuple[dict[str, object], ...]],
    *,
    residual_goals: tuple[str, ...],
) -> list[dict[str, object]]:
    actions: list[dict[str, object]] = []
    for row in rows_by_field.get("interactive_session_rows", ()):
        if not (
            str(row.get("next_interaction_kind", "")).strip()
            or str(row.get("next_owner_agent", "")).strip()
            or _str_tuple(row.get("next_tools", []))
            or _str_tuple(row.get("next_queries", []))
        ):
            continue
        actions.append(
            {
                "source": "interactive_session",
                "owner": str(row.get("next_owner_agent", "")).strip(),
                "action": str(row.get("next_interaction_kind", "")).strip(),
                "tools": list(_str_tuple(row.get("next_tools", []))[:8]),
                "queries": list(_str_tuple(row.get("next_queries", []))[:8]),
                "commands": list(_str_tuple(row.get("next_commands", []))[:8]),
                "gate": str(row.get("triage_required_gate", "")).strip(),
            }
        )
    for row in rows_by_field.get("interactive_decision_policy_rows", ()):
        action_text = (
            str(row.get("next_interaction_kind", "")).strip()
            or "; ".join(_str_tuple(row.get("feedback_actions", []))[:3])
            or "; ".join(_str_tuple(row.get("fallback_actions", []))[:3])
        )
        if not action_text and not _str_tuple(row.get("resource_contract_ids", [])):
            continue
        actions.append(
            {
                "source": "interactive_decision_policy",
                "owner": "planner",
                "action": action_text,
                "resource_contracts": list(
                    _str_tuple(row.get("resource_contract_ids", []))[:8]
                ),
                "quality_gates": list(_str_tuple(row.get("quality_gates", []))[:8]),
                "stop_conditions": list(
                    _str_tuple(row.get("stop_conditions", []))[:8]
                ),
            }
        )
    for row in rows_by_field.get("resource_request_queue_rows", ()):
        if not (
            str(row.get("resource_request_id", "")).strip()
            or str(row.get("execution_command", "")).strip()
            or str(row.get("mcp_or_cli_hint", "")).strip()
        ):
            continue
        request_playbook = _dict_value(row, "request_playbook")
        actions.append(
            {
                "source": "resource_request_queue",
                "owner": str(row.get("resource_id", "")).strip(),
                "action": str(row.get("queue_action_kind", "")).strip()
                or str(row.get("request_phase", "")).strip()
                or "dispatch_resource_request",
                "resource_request_id": str(row.get("resource_request_id", "")).strip(),
                "request_phase": str(row.get("request_phase", "")).strip(),
                "acceptance_gate": str(row.get("acceptance_gate", "")).strip(),
                "expected_response_artifact": str(
                    row.get("expected_response_artifact", "")
                ).strip(),
                "resource_contracts": list(
                    _str_tuple(row.get("resource_contract_ids", []))[:8]
                ),
                "request_contract_fields": list(
                    _str_tuple(row.get("request_contract_fields", []))[:8]
                ),
                "response_contract_fields": list(
                    _str_tuple(row.get("response_contract_fields", []))[:8]
                ),
                "execution_command": str(row.get("execution_command", "")).strip(),
                "mcp_or_cli_hint": str(row.get("mcp_or_cli_hint", "")).strip(),
                "stop_conditions": list(
                    _str_tuple(row.get("stop_conditions", []))[:8]
                ),
                "request_playbook_present": bool(request_playbook),
                "operator_prompt": str(
                    request_playbook.get("operator_prompt", "")
                ).strip(),
                "acceptance_checklist": list(
                    _str_tuple(request_playbook.get("acceptance_checklist", []))[:8]
                ),
                "rejection_triggers": list(
                    _str_tuple(request_playbook.get("rejection_triggers", []))[:8]
                ),
            }
        )
    for row in rows_by_field.get("resource_response_ledger_rows", ()):
        if (
            _truthy(row.get("request_playbook_present"))
            and _truthy(row.get("response_present"))
            and not _truthy(row.get("response_playbook_grounded"))
        ):
            actions.append(
                {
                    "source": "resource_response_ledger",
                    "owner": str(row.get("resource_id", "")).strip(),
                    "action": "redispatch_resource_response_with_request_playbook",
                    "resource_request_id": str(
                        row.get("resource_request_id", "")
                    ).strip(),
                    "acceptance_status": str(
                        row.get("acceptance_status", "")
                    ).strip(),
                    "reason": (
                        "response_present but not grounded in queued "
                        "request_playbook"
                    ),
                    "response_contract_fields": list(
                        _str_tuple(row.get("response_contract_fields", []))[:8]
                    ),
                    "matched_response_contract_fields": list(
                        _str_tuple(row.get("matched_response_contract_fields", []))[
                            :8
                        ]
                    ),
                    "missing_response_contract_fields": list(
                        _str_tuple(row.get("missing_response_contract_fields", []))[
                            :8
                        ]
                    ),
                }
            )
            continue
        if not _resource_response_row_is_admissible_feedback(row):
            continue
        if not (
            _truthy(row.get("route_revision_recommended"))
            or _str_tuple(row.get("route_revision_reasons", []))
        ):
            continue
        actions.append(
            {
                "source": "resource_response_ledger",
                "owner": str(row.get("resource_id", "")).strip(),
                "action": "route_revision_recommended",
                "resource_request_id": str(row.get("resource_request_id", "")).strip(),
                "acceptance_status": str(row.get("acceptance_status", "")).strip(),
                "reasons": list(_str_tuple(row.get("route_revision_reasons", []))[:8]),
                "response_summary": str(row.get("response_summary", "")).strip(),
            }
        )
    for row in rows_by_field.get("route_revision_overlay_rows", ()):
        if not (
            str(row.get("route_revision_summary", "")).strip()
            or _str_tuple(row.get("revised_delta_primitives", []))
            or _str_tuple(row.get("revised_selected_primitives", []))
        ):
            continue
        actions.append(
            {
                "source": "route_revision_overlay",
                "owner": "route_planner",
                "action": str(row.get("route_revision_summary", "")).strip()
                or "apply_route_revision_overlay",
                "revised_selected_primitives": list(
                    _str_tuple(row.get("revised_selected_primitives", []))[:12]
                ),
                "revised_delta_primitives": list(
                    _str_tuple(row.get("revised_delta_primitives", []))[:12]
                ),
            }
        )
    if not actions and residual_goals:
        actions.append(
            {
                "source": "residual_goals",
                "owner": "route_planner",
                "action": "interpret_residual_goals_and_emit_route_repair",
                "residual_goals": list(residual_goals[:8]),
            }
        )
    return actions[:12]


def _collect_source_snippets(
    rows: tuple[dict[str, object], ...] | list[dict[str, object]],
) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for row in rows:
        candidates.extend(_row_source_snippet_candidates(row))
    return _compact_source_snippets(candidates)


def _resource_request_playbooks_for_context(
    context_packet: Mapping[str, Any],
) -> tuple[dict[str, object], ...]:
    playbooks: list[dict[str, object]] = []
    for row in _dict_tuple(context_packet.get("resource_request_queue_rows", [])):
        request_playbook = _dict_value(row, "request_playbook")
        if not request_playbook:
            continue
        playbook = {
            "resource_request_id": str(
                request_playbook.get("resource_request_id")
                or row.get("resource_request_id", "")
            ).strip(),
            "resource_id": str(
                request_playbook.get("resource_id") or row.get("resource_id", "")
            ).strip(),
            "request_phase": str(
                request_playbook.get("request_phase") or row.get("request_phase", "")
            ).strip(),
            "target_prover_family": str(
                request_playbook.get("target_prover_family")
                or row.get("target_prover_family", "")
            ).strip(),
            "operator_prompt": str(
                request_playbook.get("operator_prompt", "")
            ).strip(),
            "input_summary": _dict_value(request_playbook, "input_summary"),
            "required_inputs": list(
                _str_tuple(
                    request_playbook.get(
                        "required_inputs",
                        row.get("request_contract_fields", []),
                    )
                )
            ),
            "expected_response_fields": list(
                _str_tuple(
                    request_playbook.get(
                        "expected_response_fields",
                        row.get("response_contract_fields", []),
                    )
                )
            ),
            "expected_response_artifact": str(
                request_playbook.get("expected_response_artifact")
                or row.get("expected_response_artifact", "")
            ).strip(),
            "acceptance_checklist": list(
                _str_tuple(request_playbook.get("acceptance_checklist", []))
            ),
            "rejection_triggers": list(
                _str_tuple(request_playbook.get("rejection_triggers", []))
            ),
            "stop_conditions": list(
                _str_tuple(
                    request_playbook.get(
                        "stop_conditions",
                        row.get("stop_conditions", []),
                    )
                )
            ),
            "execution_command": str(
                request_playbook.get("execution_command")
                or row.get("execution_command", "")
            ).strip(),
            "mcp_or_cli_hint": str(
                request_playbook.get("mcp_or_cli_hint")
                or row.get("mcp_or_cli_hint", "")
            ).strip(),
            "proof_evidence_boundary": str(
                request_playbook.get(
                    "proof_evidence_boundary",
                    PROOF_EVIDENCE_BOUNDARY,
                )
            ),
        }
        if playbook["resource_request_id"] or playbook["operator_prompt"]:
            playbooks.append(playbook)
    return tuple(playbooks[:25])


def _collect_source_snippets_from_value(
    value: Any,
    snippets: list[dict[str, object]],
) -> None:
    if isinstance(value, Mapping):
        snippets.extend(_row_source_snippet_candidates(value))
        for item in value.values():
            _collect_source_snippets_from_value(item, snippets)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _collect_source_snippets_from_value(item, snippets)


def _compact_source_snippets(
    candidates: list[dict[str, object]] | tuple[dict[str, object], ...],
) -> list[dict[str, object]]:
    snippets: list[dict[str, object]] = []
    seen: set[str] = set()
    for snippet in candidates:
        source_ref = str(snippet.get("source_ref", "")).strip()
        claim = str(snippet.get("claim", "")).strip()
        excerpt = str(snippet.get("excerpt", "")).strip()
        if not source_ref or not (claim or excerpt):
            continue
        compact = {
            key: snippet[key]
            for key in (
                "source_ref",
                "claim",
                "excerpt",
                "rank",
                "evidence_role",
                "target_primitives",
                "matched_terms",
            )
            if key in snippet
        }
        key = stable_hash(
            [
                compact.get("source_ref", ""),
                compact.get("claim", ""),
                str(compact.get("excerpt", ""))[:500],
            ]
        )
        if key in seen:
            continue
        seen.add(key)
        snippets.append(compact)
    return snippets


def _row_source_snippet_candidates(
    row: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    candidates: list[dict[str, object]] = []
    containers = [row]
    response_payload = _dict_value(row, "response_payload")
    if response_payload:
        containers.append(response_payload)
    for container in containers:
        candidates.extend(_dict_tuple(container.get("source_snippets", [])))
        for node in _dict_tuple(container.get("route_evidence_nodes", [])):
            source_ref = str(node.get("source_ref", "")).strip()
            excerpt = str(node.get("excerpt", "")).strip()
            if not source_ref or not excerpt:
                continue
            candidates.append(
                {
                    "source_ref": source_ref,
                    "claim": str(node.get("label", "")).strip(),
                    "excerpt": excerpt,
                    "rank": node.get("rank", 0),
                    "evidence_role": str(
                        node.get(
                            "evidence_role",
                            "source-backed informal route evidence",
                        )
                    ).strip(),
                    "target_primitives": _str_tuple(
                        node.get("target_primitives", [])
                    ),
                    "matched_terms": _str_tuple(node.get("matched_terms", [])),
                }
            )
    return tuple(candidates)


def _collect_row_values(
    rows: tuple[dict[str, object], ...] | list[dict[str, object]],
    field_name: str,
) -> tuple[str, ...]:
    values: list[str] = []
    for row in rows:
        values.extend(_str_tuple(row.get(field_name, [])))
    return _str_tuple(values)


def _unique_strings(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    return _str_tuple(
        list(dict.fromkeys(str(value) for value in values if str(value).strip()))
    )


def _value_counts(values: tuple[str, ...] | list[str]) -> dict[str, int]:
    counter = Counter(_unique_value for _unique_value in values if _unique_value)
    return dict(sorted(counter.items()))


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value != 0
    return str(value or "").strip().lower() in {
        "true",
        "yes",
        "y",
        "1",
        "required",
        "needed",
        "recommended",
    }


def _resource_targets_match(row: Mapping[str, Any], target_prover_family: str) -> bool:
    targets = {value.lower() for value in _str_tuple(row.get("target_prover_families", []))}
    if not targets:
        return True
    target = target_prover_family.lower()
    return target in targets or "all" in targets or "any" in targets


def _resource_ids_for_registry_context(rows: list[dict[str, object]]) -> set[str]:
    resource_ids: set[str] = set()
    for row in rows:
        for field_name in (
            "resource_id",
            "local_fallback_resource_ids",
            "frontier_resource_ids",
            "local_first_resource_ids",
            "frontier_escalation_resource_ids",
        ):
            resource_ids.update(_str_tuple(row.get(field_name, [])))
    return {resource_id for resource_id in resource_ids if resource_id}


def _compact_row(row: Mapping[str, Any]) -> dict[str, object]:
    keep = (
        "goal_plan_id",
        "route_id",
        "target_intake_id",
        "target_id",
        "standalone_route_id",
        "refinement_evidence_id",
        "refinement_item_id",
        "display_name",
        "domain",
        "target_prover_family",
        "library_snapshot_ref",
        "theorem_statement",
        "theorem_skeleton",
        "normalized_objects",
        "normalized_assumptions",
        "normalized_procedure",
        "normalized_claim",
        "desired_theorem_shape",
        "proof_source_refs",
        "primitive_seed_rows",
        "extracted_primitive_candidates",
        "background_primitives",
        "literature_queries",
        "formal_library_grounding_queries",
        "lean_grounding_queries",
        "proof_state_probe_required",
        "missing_required_fields",
        "review_flags",
        "proof_evidence_status",
        "proof_evidence_boundary",
        "ok",
        "errors",
        "primitive",
        "component_id",
        "component_name",
        "planner_stage",
        "role",
        "required_capabilities",
        "resource_id",
        "resource_request_id",
        "resource_name",
        "resource_kind",
        "surface",
        "target_prover_families",
        "evidence_contract",
        "capability_tags",
        "validation_signals",
        "request_contract_fields",
        "response_contract_fields",
        "acceptance_gate",
        "escalation_policy",
        "output_artifact_kind",
        "expected_response_artifact",
        "response_present",
        "response_contract_minimum_met",
        "response_contract_ok",
        "request_playbook_present",
        "response_playbook_grounded",
        "response_playbook_grounding_terms",
        "response_summary",
        "response_payload",
        "response_artifacts",
        "coverage_bucket",
        "coverage_status",
        "candidate_declarations",
        "candidate_declaration_rows",
        "source_refs",
        "source_snippets",
        "source_grounding_status",
        "residual_goals",
        "prover_diagnostics",
        "prover_attempt_status",
        "prover_diagnostic_signature",
        "route_revision_recommended",
        "route_revision_reasons",
        "acceptance_status",
        "matched_response_contract_fields",
        "missing_response_contract_fields",
        "hook_kind",
        "evidence_kind",
        "tool_name",
        "route_evidence_nodes",
        "lean_declaration_hits",
        "coverage_updates",
        "route_revision_summary",
        "revised_selected_primitives",
        "revised_delta_primitives",
        "revised_informal_knowledge_dag_nodes",
        "revised_formal_realization_dag_nodes",
        "revised_lean_realization_dag_nodes",
        "revised_route_alignment_edges",
        "revision_status",
        "applied_hook_kinds",
        "applied_refinement_evidence_ids",
        "applied_resource_response_traces",
        "resource_response_summary",
        "resource_response_summary_by_acceptance_status",
        "resource_response_awaiting_request_ids",
        "resource_response_rejected_request_ids",
        "next_required_gate",
        "interactive_session_row_id",
        "decision_policy_row_id",
        "session_state",
        "next_interaction_kind",
        "next_owner_agent",
        "next_tools",
        "next_queries",
        "next_commands",
        "user_checkpoint",
        "stability_decision",
        "stable_under_current_evidence_bound",
        "needs_more_literature",
        "needs_more_lean_grounding",
        "needs_more_proof_state_feedback",
        "needs_route_replanning",
        "triage_class",
        "triage_required_gate",
        "replan_required",
        "decision_rationale",
        "trigger_signals",
        "evidence_inputs",
        "expected_outputs",
        "feedback_actions",
        "evaluation_hooks",
        "required_tool_contracts",
        "standalone_input_trace",
        "component_ids",
        "local_fallback_resource_ids",
        "frontier_resource_ids",
        "adapter_ids",
        "local_first_resource_ids",
        "frontier_escalation_resource_ids",
        "resource_contract_ids",
        "required_quality_signals",
        "quality_gates",
        "response_validation_signals",
        "stop_conditions",
        "fallback_actions",
        "bounded_evidence_claim",
        "resource_selection_rationale",
        "request_phase",
        "request_rank",
        "queue_action_kind",
        "escalation_triggers",
        "execution_command",
        "mcp_or_cli_hint",
        "dispatch_spec",
        "request_playbook",
        "request_payload",
    )
    compact: dict[str, object] = {}
    for key in keep:
        if key not in row:
            continue
        if key == "standalone_input_trace":
            trace = _compact_standalone_input_trace(row[key])
            if trace:
                compact[key] = trace
            continue
        compact[key] = row[key]
    return compact


def _compact_standalone_input_trace(value: object) -> dict[str, object]:
    trace = value if isinstance(value, Mapping) else {}
    if not trace:
        return {}
    compact: dict[str, object] = {
        "trace_kind": str(trace.get("trace_kind", "")),
        "source_route_id": str(trace.get("source_route_id", "")),
        "has_replan_metadata": bool(trace.get("has_replan_metadata", False)),
        "applied_hook_kinds": list(_str_tuple(trace.get("applied_hook_kinds", []))),
        "residual_goals": list(_str_tuple(trace.get("residual_goals", []))),
        "llm_route_planner_route_adoption_status": str(
            trace.get("llm_route_planner_route_adoption_status", "")
        ),
        "llm_route_planner_route_adoption_blockers": list(
            _str_tuple(trace.get("llm_route_planner_route_adoption_blockers", []))
        ),
        "has_minimal_delta_and_or_cost_graph": bool(
            trace.get("has_minimal_delta_and_or_cost_graph", False)
        ),
        "minimal_delta_route_option_count": int(
            trace.get("minimal_delta_route_option_count", 0) or 0
        ),
        "minimal_delta_selected_route_option_id": str(
            trace.get("minimal_delta_selected_route_option_id", "")
        ),
        "minimal_delta_selected_route_cost": trace.get(
            "minimal_delta_selected_route_cost",
            None,
        ),
        "has_realization_coverage_witness": bool(
            trace.get("has_realization_coverage_witness", False)
        ),
        "realization_coverage_complete": bool(
            trace.get("realization_coverage_complete", False)
        ),
        "realization_selected_primitives_missing_formal_realization": list(
            _str_tuple(
                trace.get(
                    "realization_selected_primitives_missing_formal_realization",
                    [],
                )
            )
        ),
        "realization_delta_primitives_missing_route_alignment": list(
            _str_tuple(
                trace.get(
                    "realization_delta_primitives_missing_route_alignment",
                    [],
                )
            )
        ),
    }
    witness = _compact_realization_witness(trace.get("realization_coverage_witness", {}))
    if witness:
        compact["realization_coverage_witness"] = witness
    return compact


def _residual_goals_for_route(
    route_ids: tuple[str, ...],
    context_payloads: Mapping[str, Any],
) -> tuple[str, ...]:
    residuals: list[str] = []
    for source_name in (
        "resource_response_ledger",
        "source_grounding_audit",
        "refinement_evidence",
        "route_revision_overlay",
        "interactive_session",
    ):
        for row in _rows_for_route(context_payloads.get(source_name, {}), route_ids):
            if (
                source_name == "resource_response_ledger"
                and not _resource_response_row_is_admissible_feedback(row)
            ):
                continue
            if (
                source_name == "refinement_evidence"
                and not _refinement_evidence_row_is_admissible_feedback(row)
            ):
                continue
            residuals.extend(_str_tuple(row.get("residual_goals", [])))
    return _str_tuple(residuals)


def _resource_response_row_is_admissible_feedback(row: Mapping[str, object]) -> bool:
    status = str(row.get("acceptance_status", "")).strip()
    if status == "AWAITING_RESOURCE_RESPONSE" or status.startswith("REJECTED_"):
        return False
    if not _truthy(row.get("response_present")):
        return False
    if not _truthy(row.get("response_contract_ok")):
        return False
    if "response_contract_minimum_met" in row and not _truthy(
        row.get("response_contract_minimum_met")
    ):
        return False
    return True


def _refinement_evidence_row_is_admissible_feedback(row: Mapping[str, object]) -> bool:
    status = str(row.get("acceptance_status", "")).strip()
    if not status or status.startswith("AWAITING_") or status.startswith("REJECTED_"):
        return False
    if "response_present" in row and not _truthy(row.get("response_present")):
        return False
    if "response_contract_ok" in row and not _truthy(row.get("response_contract_ok")):
        return False
    if "ok" in row and not _truthy(row.get("ok")):
        return False
    return True


def _route_match_ids(route: Mapping[str, Any], route_id: str) -> tuple[str, ...]:
    replan_metadata = _dict_value(route, "replan_metadata")
    ids = [
        route_id,
        str(route.get("source_route_id", "")),
        str(route.get("goal_plan_id", "")),
        str(replan_metadata.get("source_route_id", "")),
        str(replan_metadata.get("source_goal_plan_id", "")),
    ]
    return _str_tuple(ids)


def _responses_by_request(
    responses: list[dict[str, Any]],
    requests: tuple[dict[str, Any], ...],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    by_request: dict[str, dict[str, Any]] = {}
    request_ids = {str(packet.get("request_id", "")) for packet in requests}
    route_to_request = {
        str(packet.get("route_id", "")): str(packet.get("request_id", ""))
        for packet in requests
    }
    for response in responses:
        request_id = str(response.get("request_id", ""))
        if not request_id:
            route_id = str(response.get("route_id", ""))
            if route_id in route_to_request:
                request_id = route_to_request[route_id]
                response["request_id"] = request_id
            elif len(requests) == 1:
                request_id = str(requests[0].get("request_id", ""))
                response["request_id"] = request_id
        if request_id not in request_ids:
            errors.append(f"LLM response references unknown request_id: {request_id}")
            continue
        if request_id in by_request:
            errors.append(f"duplicate LLM response for request_id: {request_id}")
            continue
        by_request[request_id] = response
    return by_request


def _standalone_seed(
    input_payload: Mapping[str, Any],
    rows: tuple[FormalizationGapPlannerLLMRoutePlannerRow, ...],
) -> dict[str, object]:
    accepted_routes = [
        _accepted_route_for_seed(row)
        for row in rows
        if row.response_contract_ok and row.standalone_route
    ]
    routes = accepted_routes or [dict(route) for route in _routes(input_payload)]
    seed: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_VERSION,
        "component_name": FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT,
        "library_snapshot_ref": str(input_payload.get("library_snapshot_ref", "")),
        "routes": routes,
        "llm_route_planner_source": LLM_ROUTE_PLANNER_COMPONENT,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }
    seed_target = _single_seed_target_prover_family(input_payload, routes)
    if seed_target:
        seed["target_prover_family"] = seed_target
    return seed


def _accepted_route_for_seed(
    row: FormalizationGapPlannerLLMRoutePlannerRow,
) -> dict[str, object]:
    route = dict(row.standalone_route)
    route["target_prover_family"] = row.target_prover_family
    source_refs = tuple(
        dict.fromkeys(
            [
                *_str_tuple(route.get("source_refs", [])),
                *row.source_refs,
            ]
        )
    )
    route["source_refs"] = list(source_refs)
    source_snippets = _merge_dict_rows(
        _dict_tuple(route.get("source_snippets", [])),
        row.source_snippets,
        key_fields=("source_ref", "excerpt", "claim"),
    )
    if source_snippets:
        route["source_snippets"] = [dict(snippet) for snippet in source_snippets]
    revised_informal_nodes = tuple(
        _llm_informal_node_for_seed(node) for node in row.informal_knowledge_dag_nodes
    )
    revised_formal_nodes = tuple(
        _llm_formal_node_for_seed(node) for node in row.formal_realization_dag_nodes
    )
    revised_lean_nodes = tuple(
        _llm_formal_node_for_seed(node) for node in row.lean_realization_dag_nodes
    )
    revised_alignment_edges = tuple(_llm_alignment_edges_for_seed(row))
    metadata = _dict_value(route, "replan_metadata")
    applied_hook_kinds = tuple(
        dict.fromkeys([*_str_tuple(metadata.get("applied_hook_kinds", [])), "llm_route_planner"])
    )
    applied_proposal_ids = tuple(
        dict.fromkeys(
            [
                *_str_tuple(metadata.get("applied_proposal_ids", [])),
                row.llm_route_planner_row_id,
            ]
        )
    )
    selected_primitives = _str_tuple(row.minimal_delta_plan.get("selected_primitives", []))
    and_or_cost_graph = _dict_value(row.minimal_delta_plan, "and_or_cost_graph")
    realization_coverage_witness = dict(row.realization_coverage_witness)
    residual_goals = tuple(
        dict.fromkeys(
            [
                *_str_tuple(metadata.get("residual_goals", [])),
                *[
                    str(item.get("residual_goal", "")).strip()
                    for item in row.residual_interpretations
                    if str(item.get("residual_goal", "")).strip()
                ],
            ]
        )
    )
    llm_refinement_hooks = _llm_refinement_hooks_for_search_requests(
        row.search_requests,
        planner_next_actions=row.planner_next_actions,
        selected_primitives=selected_primitives,
        theorem_statement=str(route.get("theorem_statement", "")),
        target_prover_family=row.target_prover_family,
    )
    if not row.search_requests:
        llm_refinement_hooks = _merge_dict_rows(
            llm_refinement_hooks,
            _llm_refinement_hooks_for_planner_next_actions(
                row.planner_next_actions,
                selected_primitives=selected_primitives,
                theorem_statement=str(route.get("theorem_statement", "")),
                target_prover_family=row.target_prover_family,
            ),
            key_fields=("hook_kind", "queries", "acceptance_record"),
        )
    llm_route_revision_triggers = _llm_route_revision_triggers_for_search_requests(
        row.search_requests,
    )
    if not row.search_requests:
        llm_route_revision_triggers = _merge_dict_rows(
            llm_route_revision_triggers,
            _llm_route_revision_triggers_for_planner_next_actions(
                row.planner_next_actions,
            ),
            key_fields=("trigger_kind", "condition", "next_action"),
        )
    route_refinement_hooks = _merge_dict_rows(
        _dict_tuple(route.get("interactive_refinement_hooks", [])),
        llm_refinement_hooks,
        key_fields=("hook_kind", "queries", "acceptance_record"),
    )
    route_revision_triggers = _merge_dict_rows(
        _dict_tuple(route.get("route_revision_triggers", [])),
        llm_route_revision_triggers,
        key_fields=("trigger_kind", "condition", "next_action"),
    )
    metadata = {
        **metadata,
        "source_route_id": str(metadata.get("source_route_id", row.route_id)),
        "llm_route_planner_row_id": row.llm_route_planner_row_id,
        "llm_route_planner_request_id": row.request_id,
        "llm_route_planner_provider": row.provider_name,
        "llm_route_planner_model": row.model,
        "llm_route_planner_model_tier": row.model_tier,
        "llm_route_planner_model_selection_rationale": (
            row.model_selection_rationale
        ),
        "llm_route_planner_generator_metadata": dict(row.generator_metadata),
        "llm_route_planner_generator_metadata_keys": sorted(
            str(key) for key in row.generator_metadata
        ),
        "target_prover_family": row.target_prover_family,
        "llm_route_planner_acceptance_status": row.acceptance_status,
        "llm_route_planner_route_adoption_status": row.route_adoption_status,
        "llm_route_planner_route_adoption_blockers": list(
            row.route_adoption_blockers
        ),
        "llm_route_planner_search_requests": [dict(item) for item in row.search_requests],
        "llm_route_planner_interactive_refinement_hooks": [
            dict(item) for item in llm_refinement_hooks
        ],
        "llm_route_planner_route_revision_triggers": [
            dict(item) for item in llm_route_revision_triggers
        ],
        "llm_route_planner_uncertainty_flags": list(row.uncertainty_flags),
        "llm_route_planner_semantic_alignment_risks": list(row.semantic_alignment_risks),
        "llm_route_planner_residual_interpretations": [
            dict(item) for item in row.residual_interpretations
        ],
        "llm_route_planner_minimal_delta_plan": dict(row.minimal_delta_plan),
        "llm_route_planner_realization_coverage_witness": realization_coverage_witness,
        "minimal_delta_and_or_cost_graph": dict(and_or_cost_graph),
        "applied_hook_kinds": list(applied_hook_kinds),
        "applied_proposal_ids": list(applied_proposal_ids),
        "source_refs": list(source_refs),
        "source_snippets": [dict(snippet) for snippet in source_snippets],
        "revised_informal_knowledge_dag_nodes": [dict(node) for node in revised_informal_nodes],
        "revised_formal_realization_dag_nodes": [dict(node) for node in revised_formal_nodes],
        "revised_route_alignment_edges": [dict(edge) for edge in revised_alignment_edges],
        "alignment_edge_primitives": list(
            dict.fromkeys(
                [
                    *_str_tuple(metadata.get("alignment_edge_primitives", [])),
                    *[
                        str(edge.get("primitive", "")).strip()
                        for edge in revised_alignment_edges
                        if str(edge.get("primitive", "")).strip()
                    ],
                    *selected_primitives,
                ]
            )
        ),
        "revised_selected_primitives": list(selected_primitives),
        "residual_goals": list(residual_goals),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }
    if revised_lean_nodes:
        metadata["revised_lean_realization_dag_nodes"] = [
            dict(node) for node in revised_lean_nodes
        ]
    else:
        metadata.pop("revised_lean_realization_dag_nodes", None)
    route["replan_metadata"] = metadata
    route["interactive_refinement_hooks"] = [
        dict(item) for item in route_refinement_hooks
    ]
    route["route_revision_triggers"] = [
        dict(item) for item in route_revision_triggers
    ]
    route["revised_informal_knowledge_dag_nodes"] = [
        dict(node) for node in revised_informal_nodes
    ]
    route["revised_formal_realization_dag_nodes"] = [
        dict(node) for node in revised_formal_nodes
    ]
    if revised_lean_nodes:
        route["revised_lean_realization_dag_nodes"] = [
            dict(node) for node in revised_lean_nodes
        ]
    else:
        route.pop("revised_lean_realization_dag_nodes", None)
    route["revised_route_alignment_edges"] = [
        dict(edge) for edge in revised_alignment_edges
    ]
    route["minimal_delta_and_or_cost_graph"] = dict(and_or_cost_graph)
    route["realization_coverage_witness"] = realization_coverage_witness
    route["llm_route_planner_row_id"] = row.llm_route_planner_row_id
    route["llm_route_planner_acceptance_status"] = row.acceptance_status
    route["llm_route_planner_route_adoption_status"] = row.route_adoption_status
    route["llm_route_planner_route_adoption_blockers"] = list(
        row.route_adoption_blockers
    )
    return route


def _llm_informal_node_for_seed(node: Mapping[str, Any]) -> dict[str, object]:
    node_id = str(node.get("node_id", "")).strip()
    return {
        **dict(node),
        "node_id": node_id,
        "label": str(node.get("label") or node.get("claim") or node_id),
        "kind": str(node.get("kind") or node.get("semantic_role") or "llm_informal_dag_node"),
        "node_type": str(
            node.get("node_type") or node.get("semantic_role") or "llm_informal_dag_node"
        ),
        "node_source": "llm_route_planner_revised_informal_dag",
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
    }


def _llm_formal_node_for_seed(node: Mapping[str, Any]) -> dict[str, object]:
    node_id = str(node.get("node_id", "")).strip()
    primitive = str(node.get("primitive") or node.get("label") or node_id)
    return {
        **dict(node),
        "node_id": node_id,
        "label": str(node.get("label") or primitive),
        "primitive": primitive,
        "kind": str(node.get("kind") or "llm_formal_realization_node"),
        "node_type": str(node.get("node_type") or "llm_formal_realization_node"),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
    }


def _llm_refinement_hooks_for_search_requests(
    search_requests: tuple[dict[str, object], ...],
    *,
    planner_next_actions: tuple[dict[str, object], ...],
    selected_primitives: tuple[str, ...],
    theorem_statement: str,
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    hooks: list[dict[str, object]] = []
    for index, request in enumerate(search_requests):
        hook_kind = _hook_kind_for_llm_search_request(request)
        query = str(request.get("query", "")).strip()
        reason = str(request.get("reason", "")).strip()
        queries = _str_tuple(
            [
                query,
                reason if not query else "",
                theorem_statement if hook_kind == "proof_state_feedback" else "",
            ]
        )
        resource_binding_summary = _llm_resource_binding_summary(
            request,
            planner_next_actions=planner_next_actions,
        )
        hooks.append(
            {
                "hook_kind": hook_kind,
                "recommended_tools": list(
                    _recommended_tools_for_llm_hook(
                        hook_kind,
                        target_prover_family=target_prover_family,
                    )
                ),
                "queries": list(queries),
                "target_primitives": list(
                    _target_primitives_for_llm_search_request(
                        request,
                        selected_primitives=selected_primitives,
                    )
                ),
                "acceptance_record": _acceptance_record_for_llm_hook(hook_kind),
                "llm_route_planner_search_request_index": index,
                "llm_route_planner_search_request": dict(request),
                "planner_next_actions": [dict(action) for action in planner_next_actions],
                "resource_request_ids": list(
                    resource_binding_summary["resource_request_ids"]
                ),
                "resource_ids": list(resource_binding_summary["resource_ids"]),
                "resource_request_bindings": [
                    dict(item)
                    for item in resource_binding_summary["resource_request_bindings"]
                ],
                "proof_evidence_status": PROOF_EVIDENCE_STATUS,
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            }
        )
    return _merge_dict_rows(
        tuple(hooks),
        tuple(),
        key_fields=("hook_kind", "queries", "acceptance_record"),
    )


def _llm_route_revision_triggers_for_search_requests(
    search_requests: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    triggers: list[dict[str, object]] = []
    for index, request in enumerate(search_requests):
        hook_kind = _hook_kind_for_llm_search_request(request)
        query = str(request.get("query", "")).strip()
        reason = str(request.get("reason", "")).strip()
        resource_binding_summary = _llm_resource_binding_summary(request)
        triggers.append(
            {
                "trigger_kind": _trigger_kind_for_llm_hook(hook_kind),
                "condition": reason or query or str(request.get("request_kind", "")).strip(),
                "next_action": _next_action_for_llm_hook(hook_kind, query=query),
                "llm_route_planner_search_request_index": index,
                "llm_route_planner_search_request": dict(request),
                "resource_request_ids": list(
                    resource_binding_summary["resource_request_ids"]
                ),
                "resource_ids": list(resource_binding_summary["resource_ids"]),
                "resource_request_bindings": [
                    dict(item)
                    for item in resource_binding_summary["resource_request_bindings"]
                ],
                "proof_evidence_status": PROOF_EVIDENCE_STATUS,
            }
        )
    return _merge_dict_rows(
        tuple(triggers),
        tuple(),
        key_fields=("trigger_kind", "condition", "next_action"),
    )


def _llm_refinement_hooks_for_planner_next_actions(
    planner_next_actions: tuple[dict[str, object], ...],
    *,
    selected_primitives: tuple[str, ...],
    theorem_statement: str,
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    hooks: list[dict[str, object]] = []
    for index, action in enumerate(planner_next_actions):
        hook_kind = _hook_kind_for_llm_planner_action(action)
        queries = _str_tuple(
            [
                *_planner_action_queries(action),
                theorem_statement if hook_kind == "proof_state_feedback" else "",
            ]
        )
        if not queries and not _planner_action_resource_refs(action):
            continue
        resource_binding_summary = _llm_resource_binding_summary(action)
        hooks.append(
            {
                "hook_kind": hook_kind,
                "recommended_tools": list(
                    _recommended_tools_for_llm_hook(
                        hook_kind,
                        target_prover_family=target_prover_family,
                    )
                ),
                "queries": list(queries),
                "target_primitives": list(
                    _target_primitives_for_llm_search_request(
                        action,
                        selected_primitives=selected_primitives,
                    )
                ),
                "acceptance_record": _acceptance_record_for_llm_hook(hook_kind),
                "llm_route_planner_planner_next_action_index": index,
                "llm_route_planner_planner_next_action": dict(action),
                "resource_request_ids": list(
                    resource_binding_summary["resource_request_ids"]
                ),
                "resource_ids": list(resource_binding_summary["resource_ids"]),
                "resource_request_bindings": [
                    dict(item)
                    for item in resource_binding_summary["resource_request_bindings"]
                ],
                "proof_evidence_status": PROOF_EVIDENCE_STATUS,
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            }
        )
    return _merge_dict_rows(
        tuple(hooks),
        tuple(),
        key_fields=("hook_kind", "queries", "acceptance_record"),
    )


def _llm_route_revision_triggers_for_planner_next_actions(
    planner_next_actions: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    triggers: list[dict[str, object]] = []
    for index, action in enumerate(planner_next_actions):
        hook_kind = _hook_kind_for_llm_planner_action(action)
        query = "; ".join(_planner_action_queries(action))
        if not query and not _planner_action_resource_refs(action):
            continue
        resource_binding_summary = _llm_resource_binding_summary(action)
        triggers.append(
            {
                "trigger_kind": _trigger_kind_for_llm_hook(hook_kind),
                "condition": query
                or str(action.get("action", "")).strip()
                or str(action.get("owner", "")).strip(),
                "next_action": _next_action_for_llm_hook(hook_kind, query=query),
                "llm_route_planner_planner_next_action_index": index,
                "llm_route_planner_planner_next_action": dict(action),
                "resource_request_ids": list(
                    resource_binding_summary["resource_request_ids"]
                ),
                "resource_ids": list(resource_binding_summary["resource_ids"]),
                "resource_request_bindings": [
                    dict(item)
                    for item in resource_binding_summary["resource_request_bindings"]
                ],
                "proof_evidence_status": PROOF_EVIDENCE_STATUS,
            }
        )
    return _merge_dict_rows(
        tuple(triggers),
        tuple(),
        key_fields=("trigger_kind", "condition", "next_action"),
    )


def _llm_resource_binding_summary(
    search_request: Mapping[str, object],
    *,
    planner_next_actions: tuple[dict[str, object], ...] = (),
) -> dict[str, tuple[object, ...]]:
    rows = [("search_request", search_request)]
    rows.extend((f"planner_next_actions[{index}]", row) for index, row in enumerate(planner_next_actions))
    resource_request_ids: list[str] = []
    resource_ids: list[str] = []
    bindings: list[dict[str, object]] = []
    for source, row in rows:
        refs = _structured_resource_refs(row)
        request_ids = _str_tuple(refs.get("resource_request_ids", []))
        row_resource_ids = _str_tuple(
            [
                *refs.get("resource_ids", []),
                *refs.get("tool_owner_ids", []),
            ]
        )
        resource_request_ids.extend(request_ids)
        resource_ids.extend(row_resource_ids)
        for request_id in request_ids or ("",):
            for resource_id in row_resource_ids or ("",):
                if request_id or resource_id:
                    bindings.append(
                        {
                            "source": source,
                            "resource_request_id": request_id,
                            "resource_id": resource_id,
                        }
                    )
    return {
        "resource_request_ids": tuple(dict.fromkeys(_str_tuple(resource_request_ids))),
        "resource_ids": tuple(dict.fromkeys(_str_tuple(resource_ids))),
        "resource_request_bindings": tuple(
            dict(item)
            for item in _merge_dict_rows(
                tuple(bindings),
                tuple(),
                key_fields=("source", "resource_request_id", "resource_id"),
            )
        ),
    }


def _hook_kind_for_llm_planner_action(action: Mapping[str, object]) -> str:
    refs = _structured_resource_refs(action)
    text = _primitive_key(
        " ".join(
            [
                *(_planner_action_queries(action)),
                *refs.get("resource_ids", []),
                *refs.get("tool_owner_ids", []),
                *refs.get("resource_request_ids", []),
            ]
        )
    )
    if any(
        token in text
        for token in (
            "proof_state",
            "prover",
            "diagnostic",
            "lean_lsp",
            "lsp",
            "lake",
        )
    ):
        return "proof_state_feedback"
    if any(token in text for token in ("lean_search", "leansearch", "leanfinder", "loogle")):
        return "lean_library_grounding"
    if any(
        token in text
        for token in (
            "formal_library",
            "formal_source",
            "library",
            "declaration",
            "formal_source_index",
        )
    ):
        return "formal_library_grounding"
    if any(
        token in text
        for token in (
            "literature",
            "source",
            "paper",
            "paperclip",
            "paperqa",
            "textbook",
            "semantic_scholar",
        )
    ):
        return "literature_discovery"
    if "route" in text and "revision" in text:
        return "route_revision"
    return "route_revision"


def _planner_action_queries(action: Mapping[str, object]) -> tuple[str, ...]:
    queries: list[str] = []
    for field_name in (
        "query",
        "queries",
        "reason",
        "rationale",
        "action",
        "next_action",
        "description",
    ):
        queries.extend(_str_tuple(action.get(field_name, [])))
    return _str_tuple(queries)


def _planner_action_resource_refs(action: Mapping[str, object]) -> tuple[str, ...]:
    refs = _structured_resource_refs(action)
    return _str_tuple(
        [
            *refs.get("resource_request_ids", []),
            *refs.get("resource_ids", []),
            *refs.get("tool_owner_ids", []),
        ]
    )


def _hook_kind_for_llm_search_request(request: Mapping[str, object]) -> str:
    kind = _primitive_key(request.get("request_kind", ""))
    if any(token in kind for token in ("lean_search", "leansearch", "leanfinder", "loogle")):
        return "lean_library_grounding"
    if any(
        token in kind
        for token in ("formal_library", "formal_source", "library", "declaration")
    ):
        return "formal_library_grounding"
    if any(token in kind for token in ("literature", "source", "paper", "textbook")):
        return "literature_discovery"
    if any(token in kind for token in ("prover", "proof_state", "lsp", "diagnostic")):
        return "proof_state_feedback"
    if "route" in kind and "revision" in kind:
        return "route_revision"
    return "route_revision"


def _recommended_tools_for_llm_hook(
    hook_kind: str,
    *,
    target_prover_family: str = "",
) -> tuple[str, ...]:
    if hook_kind == "proof_state_feedback":
        return _proof_state_tools_for_target_prover(target_prover_family)
    return {
        "literature_discovery": (
            "Paperclip MCP/CLI",
            "PaperQA2",
            "OpenScholar",
            "Semantic Scholar API",
        ),
        "lean_library_grounding": (
            "local Lean RAG DB",
            "LeanSearch",
            "LeanExplore",
            "Loogle",
        ),
        "formal_library_grounding": (
            "target-prover formal-source index",
            "target-prover library search/RAG",
            "Rocq/Isabelle/Agda adapter search",
            "local formal-source index",
        ),
        "route_revision": (
            "literature_discovery",
            "formal_library_grounding",
            "proof_state_feedback",
        ),
    }.get(hook_kind, ("planner",))


def _proof_state_tools_for_target_prover(target_prover_family: str) -> tuple[str, ...]:
    target = _source_ref_key(target_prover_family)
    if target in {"lean", "lean4"}:
        return (
            "lean-lsp-mcp",
            "Lean LSP",
            "lake build",
        )
    if target in {"rocq", "coq"}:
        return (
            "Rocq/coq-lsp proof-state adapter",
            "SerAPI/sertop",
            "rocq/coq build command",
        )
    if target in {"isabelle", "isabelle_hol", "hol"}:
        return (
            "Isabelle server proof-state adapter",
            "find_theorems/Sledgehammer",
            "isabelle build",
        )
    if target == "agda":
        return (
            "Agda interaction-mode proof-state adapter",
            "agda --interaction-json",
            "agda type-check command",
        )
    return (
        "target-prover proof-state adapter",
        "target-prover LSP/kernel diagnostics",
        "target-prover build/check command",
    )


def _acceptance_record_for_llm_hook(hook_kind: str) -> str:
    return {
        "literature_discovery": (
            "attach source-backed theorem variants, assumptions, and proof-route "
            "passages before treating the route repair as source grounded"
        ),
        "lean_library_grounding": (
            "return candidate declarations and coverage labels before claiming "
            "reuse or minimal bridge work"
        ),
        "formal_library_grounding": (
            "return target-prover candidate declarations and coverage labels "
            "before claiming reuse or minimal bridge work"
        ),
        "proof_state_feedback": (
            "record residual goals and diagnostics as route-planning feedback "
            "unless the target prover kernel verifies the theorem"
        ),
        "route_revision": (
            "revise the informal DAG, formal realization DAG, selected delta, "
            "and minimal-delta cost witness before replay"
        ),
    }.get(hook_kind, "record bounded planner feedback only")


def _trigger_kind_for_llm_hook(hook_kind: str) -> str:
    return {
        "literature_discovery": "literature_route_evidence_needed",
        "formal_library_grounding": "formal_leaf_attempt_required",
        "lean_library_grounding": "lean_leaf_attempt_required",
        "proof_state_feedback": "blocked_by_formal_side_condition",
        "route_revision": "llm_route_revision_requested",
    }.get(hook_kind, "llm_route_revision_requested")


def _next_action_for_llm_hook(hook_kind: str, *, query: str) -> str:
    action = {
        "literature_discovery": "run bounded literature/source search",
        "formal_library_grounding": "search target-prover formal library declarations and update coverage",
        "lean_library_grounding": "search formal library declarations and update coverage",
        "proof_state_feedback": "attempt focused prover/LSP feedback and record residual goals",
        "route_revision": "revise route from bounded LLM search request",
    }.get(hook_kind, "revise route from bounded LLM search request")
    return f"{action}: {query}" if query else action


def _target_primitives_for_llm_search_request(
    request: Mapping[str, object],
    *,
    selected_primitives: tuple[str, ...],
) -> tuple[str, ...]:
    text = _primitive_key(
        " ".join(
            str(request.get(field_name, ""))
            for field_name in ("query", "reason")
        )
    )
    matched = [
        primitive
        for primitive in selected_primitives
        if _primitive_key(primitive) and _primitive_key(primitive) in text
    ]
    return _str_tuple(matched or selected_primitives[:6])


def _llm_alignment_edges_for_seed(
    row: FormalizationGapPlannerLLMRoutePlannerRow,
) -> tuple[dict[str, object], ...]:
    primitive_by_node_id = {
        str(node.get("node_id", "")): str(node.get("primitive") or node.get("label") or "")
        for node in row.formal_realization_dag_nodes
        if str(node.get("node_id", ""))
    }
    fallback_primitives = _str_tuple(row.minimal_delta_plan.get("selected_primitives", []))
    edges: list[dict[str, object]] = []
    for index, edge in enumerate(row.route_alignment_edges):
        source = str(edge.get("source") or edge.get("informal_node_id") or "").strip()
        target = str(edge.get("target") or edge.get("formal_node_id") or "").strip()
        primitive = str(edge.get("primitive") or primitive_by_node_id.get(target, "")).strip()
        if not primitive and len(fallback_primitives) == 1:
            primitive = fallback_primitives[0]
        if not primitive:
            primitive = f"llm_alignment_edge_{index + 1}"
        edges.append(
            {
                **dict(edge),
                "source": source,
                "target": target,
                "primitive": primitive,
                "kind": str(edge.get("kind") or "aligned_to_formal_realization_candidate"),
                "edge_type": str(edge.get("edge_type") or "llm_informal_to_formal_alignment"),
                "alignment_status": str(edge.get("alignment_status", "")),
                "proof_evidence_status": PROOF_EVIDENCE_STATUS,
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            }
        )
    return tuple(edges)


def _routes(payload: Mapping[str, Any]) -> tuple[dict[str, object], ...]:
    routes = payload.get("routes", [])
    if isinstance(routes, list):
        return tuple(route for route in routes if isinstance(route, dict))
    return tuple()


def _target_prover_family(payload: Mapping[str, Any]) -> str:
    return str(payload.get("target_prover_family") or payload.get("target_prover") or "lean4")


def _route_target_prover_family(
    payload: Mapping[str, Any],
    route: Mapping[str, Any],
) -> str:
    metadata = _dict_value(route, "replan_metadata")
    return str(
        route.get("target_prover_family")
        or route.get("target_prover")
        or metadata.get("target_prover_family")
        or metadata.get("target_prover")
        or _target_prover_family(payload)
    )


def _single_seed_target_prover_family(
    input_payload: Mapping[str, Any],
    routes: list[dict[str, object]],
) -> str:
    targets: list[str] = []
    seen: set[str] = set()
    for route in routes:
        target = _route_target_prover_family(input_payload, route).strip()
        key = _target_prover_key(target)
        if not target or not key or key in seen:
            continue
        seen.add(key)
        targets.append(target)
    if len(targets) == 1:
        return targets[0]
    return ""


def _formal_realization_nodes_from_payload(
    payload: Mapping[str, Any],
    *,
    target_prover_family: str = "",
) -> tuple[dict[str, object], ...]:
    formal_nodes = _dict_tuple(payload.get("formal_realization_dag_nodes", []))
    if not formal_nodes:
        formal_nodes = _dict_tuple(payload.get("lean_realization_dag_nodes", []))
    inherited_target = str(
        target_prover_family
        or payload.get("target_prover_family")
        or payload.get("target_prover")
        or ""
    )
    return tuple(
        _normalize_candidate_declaration_fields(
            node,
            inherited_target_prover_family=inherited_target,
        )
        for node in formal_nodes
    )


def _lean_legacy_realization_nodes_for_target(
    payload: Mapping[str, Any],
    *,
    formal_nodes: tuple[dict[str, object], ...],
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    target_key = _target_prover_key(target_prover_family)
    if target_key != "lean4":
        return tuple()
    legacy_nodes = _dict_tuple(payload.get("lean_realization_dag_nodes", []))
    if not legacy_nodes:
        return formal_nodes
    return tuple(
        _normalize_candidate_declaration_fields(
            node,
            inherited_target_prover_family=target_prover_family,
        )
        for node in legacy_nodes
    )


def _standalone_route_from_payload(
    payload: Mapping[str, Any],
    *,
    target_prover_family: str = "",
) -> dict[str, object]:
    route = _dict_value(payload, "standalone_route")
    if not route:
        return {}
    inherited_target = str(
        target_prover_family
        or route.get("target_prover_family")
        or route.get("target_prover")
        or payload.get("target_prover_family")
        or payload.get("target_prover")
        or ""
    )
    primitives = tuple(
        _normalize_candidate_declaration_fields(
            primitive,
            inherited_target_prover_family=inherited_target,
        )
        for primitive in _dict_tuple(route.get("primitives", []))
    )
    return {
        **route,
        "primitives": [dict(primitive) for primitive in primitives],
    }


def _normalize_candidate_declaration_fields(
    row: Mapping[str, Any],
    *,
    inherited_target_prover_family: str,
) -> dict[str, object]:
    normalized = dict(row)
    row_target = str(
        normalized.get("target_prover_family")
        or normalized.get("target_prover")
        or inherited_target_prover_family
    ).strip()
    declaration_rows = _candidate_declaration_rows(
        normalized.get("candidate_declaration_rows", []),
        inherited_target_prover_family=row_target,
        fallback_source_field="candidate_declaration_rows",
    )
    flat_declarations = _formal_declaration_values(
        normalized.get("candidate_declarations", [])
    )
    if not declaration_rows and flat_declarations:
        declaration_rows = tuple(
            {
                "declaration": declaration,
                "target_prover_family": row_target,
                "source_field": "candidate_declarations",
            }
            for declaration in flat_declarations
        )
    if declaration_rows:
        normalized["candidate_declaration_rows"] = [
            dict(declaration_row) for declaration_row in declaration_rows
        ]
    if declaration_rows and not flat_declarations:
        normalized["candidate_declarations"] = [
            str(declaration_row.get("declaration", ""))
            for declaration_row in declaration_rows
            if str(declaration_row.get("declaration", "")).strip()
        ]
    return normalized


def _candidate_declaration_rows(
    values: Any,
    *,
    inherited_target_prover_family: str,
    fallback_source_field: str,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for value in _dict_tuple(values):
        declaration = str(
            value.get("declaration")
            or value.get("declaration_name")
            or value.get("candidate_declaration")
            or value.get("lean_declaration")
            or value.get("name")
            or value.get("full_name")
            or ""
        ).strip()
        if not declaration:
            continue
        rows.append(
            {
                "declaration": declaration,
                "target_prover_family": str(
                    value.get("target_prover_family", "")
                    or value.get("target_prover", "")
                    or inherited_target_prover_family
                ).strip(),
                "source_field": str(
                    value.get("source_field", "") or fallback_source_field
                ).strip(),
            }
        )
    compact: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        key = (
            _formal_declaration_key(row.get("declaration", "")),
            _target_prover_key(row.get("target_prover_family", "")),
            str(row.get("source_field", "")),
        )
        if not key[0] or key in seen:
            continue
        seen.add(key)
        compact.append(row)
    return tuple(compact)


def _route_source_refs(payload: Mapping[str, Any]) -> tuple[str, ...]:
    refs: list[str] = []
    refs.extend(_str_tuple(payload.get("source_refs", [])))
    refs.extend(_source_refs_from_snippets(payload.get("source_snippets", [])))
    for node in _dict_tuple(payload.get("informal_knowledge_dag_nodes", [])):
        refs.extend(_str_tuple(node.get("source_refs", [])))
        refs.extend(_source_refs_from_snippets(node.get("source_snippets", [])))
    for residual in _dict_tuple(payload.get("residual_interpretations", [])):
        refs.extend(_str_tuple(residual.get("source_refs", [])))
        refs.extend(_source_refs_from_snippets(residual.get("source_snippets", [])))
    route = _dict_value(payload, "standalone_route")
    refs.extend(_str_tuple(route.get("source_refs", [])))
    refs.extend(_source_refs_from_snippets(route.get("source_snippets", [])))
    for primitive in _dict_tuple(route.get("primitives", [])):
        refs.extend(_str_tuple(primitive.get("source_refs", [])))
        refs.extend(_source_refs_from_snippets(primitive.get("source_snippets", [])))
    return _str_tuple(refs)


def _route_source_snippets(payload: Mapping[str, Any]) -> tuple[dict[str, object], ...]:
    snippets: list[dict[str, object]] = []
    snippets.extend(_dict_tuple(payload.get("source_snippets", [])))
    for node in _dict_tuple(payload.get("informal_knowledge_dag_nodes", [])):
        snippets.extend(_dict_tuple(node.get("source_snippets", [])))
    for residual in _dict_tuple(payload.get("residual_interpretations", [])):
        snippets.extend(_dict_tuple(residual.get("source_snippets", [])))
    route = _dict_value(payload, "standalone_route")
    snippets.extend(_dict_tuple(route.get("source_snippets", [])))
    for primitive in _dict_tuple(route.get("primitives", [])):
        snippets.extend(_dict_tuple(primitive.get("source_snippets", [])))
    return _merge_dict_rows(tuple(snippets), tuple(), key_fields=("source_ref", "excerpt", "claim"))


def _source_refs_from_snippets(values: Any) -> tuple[str, ...]:
    refs: list[str] = []
    for snippet in _dict_tuple(values):
        refs.extend(_str_tuple(snippet.get("source_ref", "")))
        refs.extend(_str_tuple(snippet.get("source_refs", [])))
    return _str_tuple(refs)


def _response_payload(response: Mapping[str, Any]) -> dict[str, Any]:
    payload = response.get("response_payload", response)
    return dict(payload) if isinstance(payload, Mapping) else {}


def _read_response_json(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    payload = _read_json(path, errors)
    if not payload:
        return []
    if isinstance(payload, dict) and isinstance(payload.get("responses"), list):
        return [
            dict(row)
            for row in payload["responses"]
            if isinstance(row, dict)
        ]
    if isinstance(payload, dict) and any(
        key in payload for key in ("response_payload", "informal_knowledge_dag_nodes")
    ):
        return [_normalize_response_object(payload)]
    if isinstance(payload, list):
        return [_normalize_response_object(row) for row in payload if isinstance(row, dict)]
    errors.append(f"unsupported LLM response JSON shape: {path}")
    return []


def _read_response_payload_validation_inputs(
    path: Path,
    errors: list[str],
) -> list[dict[str, Any]]:
    payload = _read_json(path, errors)
    if not payload:
        return []
    if isinstance(payload, dict) and isinstance(payload.get("responses"), list):
        rows: list[dict[str, Any]] = []
        for index, row in enumerate(payload["responses"]):
            if not isinstance(row, dict):
                continue
            rows.append(
                _response_payload_validation_input(
                    row,
                    input_shape=f"responses[{index}]",
                )
            )
        return rows
    if isinstance(payload, list):
        return [
            _response_payload_validation_input(row, input_shape=f"list[{index}]")
            for index, row in enumerate(payload)
            if isinstance(row, dict)
        ]
    if isinstance(payload, dict) and any(
        key in payload for key in ("response_payload", "informal_knowledge_dag_nodes")
    ):
        return [_response_payload_validation_input(payload, input_shape="object")]
    errors.append(f"unsupported LLM response payload validation JSON shape: {path}")
    return []


def _read_response_payload_validation_request_contexts(
    path: Path | None,
    errors: list[str],
) -> tuple[dict[str, Any], ...]:
    if path is None:
        return tuple()
    if not path.exists():
        errors.append(f"LLM route-planner request context path does not exist: {path}")
        return tuple()
    if path.is_dir():
        request_jsonl = (
            path / "formalization_gap_planner_llm_route_planner_requests.jsonl"
        )
        if request_jsonl.exists():
            return _read_request_context_jsonl(request_jsonl, errors)
        manifest_json = (
            path / "formalization_gap_planner_llm_route_planner_manifest.json"
        )
        if manifest_json.exists():
            return _read_response_payload_validation_request_contexts(
                manifest_json,
                errors,
            )
        errors.append(
            "LLM route-planner request context directory is missing "
            "formalization_gap_planner_llm_route_planner_requests.jsonl or "
            "formalization_gap_planner_llm_route_planner_manifest.json: "
            + str(path)
        )
        return tuple()
    if path.suffix.lower() == ".jsonl":
        return _read_request_context_jsonl(path, errors)
    payload = _read_json(path, errors)
    if isinstance(payload, Mapping) and isinstance(payload.get("request_packets"), list):
        return tuple(
            dict(row)
            for row in payload["request_packets"]
            if isinstance(row, Mapping)
        )
    if isinstance(payload, Mapping) and str(payload.get("request_id", "")).strip():
        return (dict(payload),)
    if isinstance(payload, list):
        return tuple(dict(row) for row in payload if isinstance(row, Mapping))
    errors.append(f"unsupported LLM route-planner request context JSON shape: {path}")
    return tuple()


def _read_request_context_jsonl(
    path: Path,
    errors: list[str],
) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        errors.append(f"failed to read LLM route-planner request context JSONL {path}: {exc}")
        return tuple()
    for line_index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError as exc:
            errors.append(
                "failed to parse LLM route-planner request context JSONL "
                f"{path}:{line_index}: {exc}"
            )
            continue
        if isinstance(value, Mapping):
            rows.append(dict(value))
        else:
            errors.append(
                "LLM route-planner request context JSONL row must be object: "
                f"{path}:{line_index}"
            )
    if not rows:
        errors.append(f"LLM route-planner request context JSONL had no rows: {path}")
    return tuple(rows)


def _request_context_schema_errors_by_id(
    request_contexts: tuple[dict[str, Any], ...],
    schema: Mapping[str, object],
) -> dict[str, list[str]]:
    errors_by_id: dict[str, list[str]] = {}
    for index, request in enumerate(request_contexts):
        request_id = str(request.get("request_id", "")).strip()
        request_key = request_id or f"request_context[{index}]"
        row_errors = validate_llm_route_planner_request(request, schema)
        if not request_id:
            row_errors.append(f"request_context[{index}].request_id missing")
        if row_errors:
            errors_by_id[request_key] = [
                f"request_context[{index}].{error}" for error in sorted(set(row_errors))
            ]
    return errors_by_id


def _response_payload_validation_request_context_for_response(
    response: Mapping[str, Any],
    *,
    payload_index: int,
    request_contexts: tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], list[str]]:
    if not request_contexts:
        return {}, []
    response_request_id = str(response.get("request_id", "")).strip()
    if response_request_id:
        matches = [
            request
            for request in request_contexts
            if str(request.get("request_id", "")).strip() == response_request_id
        ]
        if len(matches) == 1:
            return matches[0], []
        if not matches:
            return {}, [
                "request_context could not be matched by request_id for "
                f"payload_index={payload_index}: {response_request_id}"
            ]
        return {}, [
            "request_context request_id is not unique for "
            f"payload_index={payload_index}: {response_request_id}"
        ]
    response_route_id = str(response.get("route_id", "")).strip()
    if response_route_id:
        matches = [
            request
            for request in request_contexts
            if str(request.get("route_id", "")).strip() == response_route_id
        ]
        if len(matches) == 1:
            return matches[0], []
        if len(matches) > 1:
            return {}, [
                "request_context route_id is not unique for "
                f"payload_index={payload_index}: {response_route_id}"
            ]
    if len(request_contexts) == 1:
        return request_contexts[0], []
    return {}, [
        "request_context could not be matched for payload_index="
        f"{payload_index}; include response request_id or route_id"
    ]


def _response_payload_validation_input(
    row: Mapping[str, Any],
    *,
    input_shape: str,
) -> dict[str, Any]:
    wrapper_present = "response_payload" in row
    response = dict(row) if wrapper_present else _normalize_response_object(row)
    return {
        "response": response,
        "input_shape": input_shape,
        "response_wrapper_present": wrapper_present,
    }


def _normalize_response_object(row: Mapping[str, Any]) -> dict[str, Any]:
    if "response_payload" in row:
        normalized = dict(row)
    else:
        normalized = {
            "request_id": str(row.get("request_id", "")),
            "route_id": str(row.get("route_id", "")),
            "provider_name": str(row.get("provider_name", "")),
            "model": str(row.get("model", "")),
            "response_payload": dict(row),
        }
    normalized.setdefault("kernel_verified", False)
    normalized.setdefault("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)
    return normalized


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    try:
        value = json.loads(stripped)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
    if not match:
        raise ValueError("LLM response did not contain a JSON object")
    value = json.loads(match.group(0))
    return value if isinstance(value, dict) else {}


def _read_json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON file: {path}")
        return {}
    except Exception as exc:
        errors.append(f"failed to parse {path}: {type(exc).__name__}: {exc}")
        return {}


def _validate_with_schema(
    row: Mapping[str, object],
    schema: Mapping[str, object],
) -> list[str]:
    if not isinstance(row, Mapping):
        return ["row must be an object"]
    errors: list[str] = []
    required = tuple(schema.get("required", ()))
    for field_name in required:
        if field_name not in row:
            errors.append(f"{field_name} required")
    properties = schema.get("properties", {})
    if isinstance(properties, Mapping):
        for field_name, field_schema in properties.items():
            if field_name in row and isinstance(field_schema, Mapping):
                errors.extend(_schema_property_errors(field_name, row[field_name], field_schema))
    if schema.get("additionalProperties") is False:
        allowed = set(properties) if isinstance(properties, Mapping) else set(required)
        for field_name in row:
            if field_name not in allowed:
                errors.append(f"{field_name} unexpected")
    if "proof_evidence_boundary" in row and "not theorem proof evidence" not in str(
        row.get("proof_evidence_boundary", "")
    ).lower():
        errors.append("proof_evidence_boundary must say not theorem proof evidence")
    return errors


def _validate_with_schema_deep(
    row: Mapping[str, object],
    schema: Mapping[str, object],
    *,
    path: str,
) -> list[str]:
    if not isinstance(row, Mapping):
        return [f"{path or 'row'} must be object"]
    return _deep_schema_value_errors(
        path,
        row,
        schema,
        root_schema=schema,
    )


def _deep_schema_value_errors(
    path: str,
    value: object,
    schema: Mapping[str, object],
    *,
    root_schema: Mapping[str, object],
) -> list[str]:
    ref = schema.get("$ref")
    if isinstance(ref, str):
        resolved = _resolve_local_schema_ref(ref, root_schema)
        if resolved is None:
            return [f"{path or 'row'} has unresolved schema ref {ref}"]
        return _deep_schema_value_errors(
            path,
            value,
            resolved,
            root_schema=root_schema,
        )

    any_of = schema.get("anyOf")
    errors: list[str] = []
    if isinstance(any_of, list) and any_of:
        branch_errors = [
            _deep_schema_value_errors(
                path,
                value,
                dict(branch),
                root_schema=root_schema,
            )
            for branch in any_of
            if isinstance(branch, Mapping)
        ]
        if not any(not errors for errors in branch_errors):
            first_errors = next((errors for errors in branch_errors if errors), [])
            detail = "; ".join(first_errors[:3])
            suffix = f": {detail}" if detail else ""
            errors.append(
                f"{path or 'row'} must match at least one anyOf branch{suffix}"
            )

    expected_type = schema.get("type")
    if expected_type == "object":
        if not isinstance(value, Mapping):
            return [f"{path or 'row'} must be object"]
        properties = schema.get("properties", {})
        required = tuple(schema.get("required", ()))
        for field_name in required:
            if field_name not in value:
                errors.append(f"{_schema_path(path, str(field_name))} required")
        if isinstance(properties, Mapping):
            for field_name, field_schema in properties.items():
                if field_name not in value or not isinstance(field_schema, Mapping):
                    continue
                errors.extend(
                    _deep_schema_value_errors(
                        _schema_path(path, str(field_name)),
                        value[field_name],
                        field_schema,
                        root_schema=root_schema,
                    )
                )
        if schema.get("additionalProperties") is False:
            allowed = set(properties) if isinstance(properties, Mapping) else set()
            for field_name in value:
                if field_name not in allowed:
                    errors.append(f"{_schema_path(path, str(field_name))} unexpected")
    elif expected_type == "array":
        if not isinstance(value, (list, tuple)):
            return [f"{path or 'row'} must be array"]
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            errors.append(f"{path or 'row'} must contain at least {min_items} item(s)")
        item_schema = schema.get("items", {})
        if isinstance(item_schema, Mapping):
            for index, item in enumerate(value):
                errors.extend(
                    _deep_schema_value_errors(
                        f"{path}[{index}]" if path else f"[{index}]",
                        item,
                        item_schema,
                        root_schema=root_schema,
                    )
                )
    elif expected_type == "string":
        if not isinstance(value, str):
            return [f"{path or 'row'} must be string"]
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            errors.append(f"{path or 'row'} must be non-empty")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and not re.search(pattern, value):
            errors.append(f"{path or 'row'} must match {pattern}")
    elif expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            return [f"{path or 'row'} must be integer"]
    elif expected_type == "number":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return [f"{path or 'row'} must be number"]
    elif expected_type == "boolean":
        if not isinstance(value, bool):
            return [f"{path or 'row'} must be boolean"]

    enum_values = schema.get("enum")
    if isinstance(enum_values, list) and value not in enum_values:
        errors.append(f"{path or 'row'} must be one of {', '.join(map(str, enum_values))}")
    if "const" in schema and value != schema.get("const"):
        errors.append(f"{path or 'row'} must equal {schema.get('const')}")
    return errors


def _resolve_local_schema_ref(
    ref: str,
    root_schema: Mapping[str, object],
) -> Mapping[str, object] | None:
    if not ref.startswith("#/$defs/"):
        return None
    name = ref.removeprefix("#/$defs/")
    defs = root_schema.get("$defs", {})
    if not isinstance(defs, Mapping):
        return None
    resolved = defs.get(name)
    return dict(resolved) if isinstance(resolved, Mapping) else None


def _schema_path(prefix: str, field_name: str) -> str:
    return f"{prefix}.{field_name}" if prefix else field_name


def _schema_property_errors(
    field_name: str,
    value: object,
    schema: Mapping[str, object],
) -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type == "string":
        if not isinstance(value, str):
            errors.append(f"{field_name} must be string")
            return errors
        if isinstance(schema.get("minLength"), int) and len(value) < int(schema["minLength"]):
            errors.append(f"{field_name} must be non-empty")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and not re.search(pattern, value):
            errors.append(f"{field_name} must match {pattern}")
        const = schema.get("const")
        if const is not None and value != const:
            errors.append(f"{field_name} must equal {const}")
    elif expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{field_name} must be integer")
            return errors
        const = schema.get("const")
        if const is not None and value != const:
            errors.append(f"{field_name} must equal {const}")
    elif expected_type == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{field_name} must be boolean")
        const = schema.get("const")
        if const is not None and value != const:
            errors.append(f"{field_name} must equal {const}")
    elif expected_type == "array":
        if not isinstance(value, (list, tuple)):
            errors.append(f"{field_name} must be array")
            return errors
        item_schema = schema.get("items", {})
        if isinstance(item_schema, Mapping) and item_schema.get("type") == "string":
            for index, item in enumerate(value):
                if not isinstance(item, str):
                    errors.append(f"{field_name}[{index}] must be string")
        if isinstance(item_schema, Mapping) and item_schema.get("type") == "object":
            for index, item in enumerate(value):
                if not isinstance(item, Mapping):
                    errors.append(f"{field_name}[{index}] must be object")
    elif expected_type == "object" and not isinstance(value, Mapping):
        errors.append(f"{field_name} must be object")
    return errors


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(str(value) for value in values if str(value))


def _dict_tuple(values: Any) -> tuple[dict[str, object], ...]:
    if not isinstance(values, (list, tuple)):
        return tuple()
    return tuple(dict(value) for value in values if isinstance(value, Mapping))


def _merge_dict_rows(
    primary: tuple[dict[str, object], ...],
    secondary: tuple[dict[str, object], ...],
    *,
    key_fields: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for row in (*primary, *secondary):
        key = stable_hash(
            [
                str(row.get(field_name, ""))
                for field_name in key_fields
            ]
            or [row]
        )
        if key in seen:
            continue
        seen.add(key)
        rows.append(dict(row))
    return tuple(rows)


def _dict_value(row: Mapping[str, Any], key: str) -> dict[str, Any]:
    value = row.get(key, {})
    return dict(value) if isinstance(value, Mapping) else {}


def _write_outputs(out_dir: Path, payload: Mapping[str, object]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "formalization_gap_planner_llm_route_planner_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / "formalization_gap_planner_llm_route_planner_requests.jsonl").write_text(
        "\n".join(
            json.dumps(row, sort_keys=True)
            for row in payload.get("request_packets", [])
            if isinstance(row, dict)
        )
        + ("\n" if payload.get("request_packets") else ""),
        encoding="utf-8",
    )
    (out_dir / "formalization_gap_planner_llm_route_planner.jsonl").write_text(
        "\n".join(
            json.dumps(row, sort_keys=True)
            for row in payload.get("rows", [])
            if isinstance(row, dict)
        )
        + ("\n" if payload.get("rows") else ""),
        encoding="utf-8",
    )
    (out_dir / "formalization_gap_planner_llm_route_planner_request.schema.json").write_text(
        json.dumps(llm_route_planner_request_json_schema(), indent=2),
        encoding="utf-8",
    )
    (out_dir / "formalization_gap_planner_llm_route_planner_response.schema.json").write_text(
        json.dumps(llm_route_planner_response_json_schema(), indent=2),
        encoding="utf-8",
    )
    (
        out_dir
        / "formalization_gap_planner_llm_route_planner_response_payload.schema.json"
    ).write_text(
        json.dumps(llm_route_planner_response_payload_schema(), indent=2),
        encoding="utf-8",
    )
    (
        out_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.schema.json"
    ).write_text(
        json.dumps(
            llm_route_planner_response_payload_validation_manifest_json_schema(),
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        out_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_row.schema.json"
    ).write_text(
        json.dumps(
            llm_route_planner_response_payload_validation_row_json_schema(),
            indent=2,
        ),
        encoding="utf-8",
    )
    (out_dir / "formalization_gap_planner_llm_route_planner_row.schema.json").write_text(
        json.dumps(llm_route_planner_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.json").write_text(
        json.dumps(payload.get("standalone_seed", {}), indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / "formalization_gap_planner_llm_route_planner_standalone_seed.schema.json").write_text(
        json.dumps(standalone_input_json_schema(), indent=2),
        encoding="utf-8",
    )
    (out_dir / "formalization_gap_planner_llm_route_planner.md").write_text(
        _markdown_report(payload),
        encoding="utf-8",
    )


def _write_response_payload_validation_outputs(
    out_dir: Path,
    payload: Mapping[str, object],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (
        out_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.json"
    ).write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    (
        out_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation.jsonl"
    ).write_text(
        "\n".join(
            json.dumps(row, sort_keys=True)
            for row in payload.get("rows", [])
            if isinstance(row, dict)
        )
        + ("\n" if payload.get("rows") else ""),
        encoding="utf-8",
    )
    (
        out_dir
        / "formalization_gap_planner_llm_route_planner_response_payload.schema.json"
    ).write_text(
        json.dumps(llm_route_planner_response_payload_schema(), indent=2),
        encoding="utf-8",
    )
    (
        out_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.schema.json"
    ).write_text(
        json.dumps(
            llm_route_planner_response_payload_validation_manifest_json_schema(),
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        out_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_row.schema.json"
    ).write_text(
        json.dumps(
            llm_route_planner_response_payload_validation_row_json_schema(),
            indent=2,
        ),
        encoding="utf-8",
    )


def _markdown_report(payload: Mapping[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner LLM Route Planner",
        "",
        f"- Requests: {payload.get('n_request_schema_valid')}/{payload.get('n_request_packets')}",
        f"- Model tier mode: {payload.get('model_tier_selection_mode')}",
        f"- Request tiers: {payload.get('by_request_model_tier')}",
        f"- Request model-tier mismatches: {payload.get('n_request_model_tier_mismatches')}",
        f"- Repair attempts: {payload.get('n_generated_response_repair_attempts')}",
        f"- Repaired responses: {payload.get('n_generated_responses_repaired')}",
        f"- Responses present: {payload.get('n_response_present')}",
        f"- Provider failures: {payload.get('n_provider_failures')}",
        f"- Rows with generator metadata: {payload.get('n_rows_with_generator_metadata')}",
        f"- Accepted route plans: {payload.get('n_accepted_route_plans')}",
        f"- Route adoption ready: {payload.get('n_route_adoption_ready')}",
        f"- Route adoption pending refinement: {payload.get('n_route_adoption_pending_refinement')}",
        f"- Awaiting LLM response: {payload.get('n_awaiting_llm_response')}",
        f"- Rejected: {payload.get('n_rejected')}",
        f"- Informal DAG nodes: {payload.get('n_informal_knowledge_dag_nodes')}",
        f"- Formal realization nodes: {payload.get('n_formal_realization_dag_nodes')}",
        f"- Alignment edges: {payload.get('n_route_alignment_edges')}",
        f"- Search requests: {payload.get('n_search_requests')}",
        f"- Planner next actions: {payload.get('n_planner_next_actions')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Acceptance Status",
        "",
    ]
    for status, count in sorted((payload.get("by_acceptance_status", {}) or {}).items()):
        lines.append(f"- `{status}`: {count}")
    return "\n".join(lines) + "\n"
