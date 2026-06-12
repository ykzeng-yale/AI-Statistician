from __future__ import annotations

import json
import re
from collections import Counter
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .fingerprint import stable_hash
from .formalization_gap_planner_contract import (
    LEGACY_FORMAL_REALIZATION_FIELD_ALIASES,
)
from .formalization_gap_planner_local_formal_source_adapter import (
    LEGACY_FORMAL_SOURCE_ADAPTER_FIELD_ALIASES,
)
from .formalization_gap_planner_standalone import (
    FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT,
    FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_VERSION,
    llm_route_planner_seed_route_selection_json_schema,
    standalone_input_json_schema,
    validate_standalone_input_payload,
)
from .formalization_gap_planner_target_intake import (
    LEGACY_TARGET_INTAKE_FIELD_ALIASES,
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
LLM_ROUTE_PLANNER_LIBRARY_ALIGNMENT_SUMMARY_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-llm-route-planner-library-alignment-summary:1"
)
LLM_ROUTE_PLANNER_MANIFEST_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-llm-route-planner-manifest:1"
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
REPAIR_ATTEMPT_LEDGER_KIND = (
    "formalization_gap_planner_llm_route_planner_repair_attempt_ledger"
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
ROUTE_ADOPTION_BLOCKER_OMITTED_COST_HINT_PRIMITIVES = (
    "omitted_cost_hint_primitives_require_review"
)
ROUTE_ADOPTION_BLOCKER_FORMAL_GAP_BOUNDARIES = (
    "formal_gap_boundaries_require_resolution"
)
ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING = "source_grounding_obligations_pending"
ROUTE_ADOPTION_BLOCKER_QUALITY_CONTROLS = "quality_control_obligations_pending"
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
    ROUTE_ADOPTION_BLOCKER_OMITTED_COST_HINT_PRIMITIVES,
    ROUTE_ADOPTION_BLOCKER_FORMAL_GAP_BOUNDARIES,
    ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING,
    ROUTE_ADOPTION_BLOCKER_QUALITY_CONTROLS,
)
QUALITY_CONTROL_FIELDS = (
    "resource_contract_ids",
    "required_quality_signals",
    "quality_gates",
    "response_validation_signals",
    "stop_conditions",
)
CONTEXT_PACKET_INVENTORY_KIND = (
    "formalization_gap_planner_llm_route_planner_context_packet_inventory"
)
ROUTE_PLANNING_BRIEF_KIND = (
    "formalization_gap_planner_llm_route_planner_route_planning_brief"
)
LIBRARY_ALIGNMENT_SUMMARY_KIND = (
    "formalization_gap_planner_llm_route_planner_library_alignment_summary"
)
CONTEXT_PACKET_ROW_FIELDS = (
    "target_intake_rows",
    "library_coverage_rows",
    "source_grounding_rows",
    "resource_request_queue_rows",
    "resource_response_ledger_rows",
    "refinement_evidence_rows",
    "route_revision_overlay_rows",
    "route_replan_handoff_rows",
    "interactive_session_rows",
    "interactive_decision_policy_rows",
    "current_goal_plan_rows",
)
ROUTE_MATCH_SCALAR_FIELDS = (
    "route_id",
    "source_route_id",
    "target_route_id",
    "current_route_id",
    "request_route_id",
    "selected_route_id",
    "standalone_route_id",
    "target_id",
    "target_theorem_id",
    "display_name",
    "goal_plan_id",
    "source_goal_plan_id",
    "target_goal_plan_id",
)
ROUTE_MATCH_COLLECTION_FIELDS = (
    "route_match_ids",
    "route_ids",
    "source_route_ids",
    "standalone_route_ids",
    "goal_plan_ids",
)
ROUTE_MATCH_NESTED_FIELDS = (
    "replan_metadata",
    "standalone_input_trace",
)
ROUTE_ADOPTION_BLOCKER_TAXONOMY_ID = (
    "formalization_gap_planner_route_adoption_blocker_taxonomy:1"
)
ROUTE_ADOPTION_BLOCKER_TAXONOMY_COMPONENT = (
    "formalization_gap_planner_route_adoption_blocker_taxonomy"
)
STANDALONE_REPLAY_GATE_KIND = (
    "formalization_gap_planner_llm_route_planner_standalone_replay_gate"
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
    ROUTE_ADOPTION_BLOCKER_OMITTED_COST_HINT_PRIMITIVES: (
        "The selected route omits one or more primitives from the request-bound "
        "minimal-delta cost-hint baseline and needs review before standalone "
        "route adoption."
    ),
    ROUTE_ADOPTION_BLOCKER_FORMAL_GAP_BOUNDARIES: (
        "The accepted route carries explicit formal-gap boundaries that must be "
        "resolved, searched, or replayed before standalone adoption."
    ),
    ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING: (
        "The request context contains source-grounding audit rows whose claims "
        "or prover residual repairs remain unaccounted, source-search pending, "
        "or explicitly failed."
    ),
    ROUTE_ADOPTION_BLOCKER_QUALITY_CONTROLS: (
        "The route carries quality-control obligations whose required gates, "
        "signals, or stop conditions have not been discharged by admissible "
        "resource-response or refinement evidence."
    ),
}
ROUTE_ADOPTION_BLOCKER_TRIGGER_FIELDS = {
    ROUTE_ADOPTION_BLOCKER_RESPONSE_NOT_ACCEPTED: (
        "request_errors",
        "provider_failure",
        "response_contract_ok",
    ),
    ROUTE_ADOPTION_BLOCKER_RESPONSE_MISSING: ("response_present",),
    ROUTE_ADOPTION_BLOCKER_SEARCH_REQUESTS: ("response_payload.search_requests",),
    ROUTE_ADOPTION_BLOCKER_PLANNER_NEXT_ACTIONS: (
        "response_payload.planner_next_actions",
    ),
    ROUTE_ADOPTION_BLOCKER_UNCERTAINTY_FLAGS: (
        "response_payload.uncertainty_flags",
    ),
    ROUTE_ADOPTION_BLOCKER_SEMANTIC_ALIGNMENT_RISKS: (
        "response_payload.semantic_alignment_risks",
    ),
    ROUTE_ADOPTION_BLOCKER_RESIDUAL_INTERPRETATIONS: (
        "response_payload.residual_interpretations",
    ),
    ROUTE_ADOPTION_BLOCKER_FEEDBACK_ACTIONS: (
        "context_packet.feedback_loop_summary.recommended_next_actions",
    ),
    ROUTE_ADOPTION_BLOCKER_RESOURCE_PLAYBOOK_REDISPATCH: (
        "context_packet.feedback_loop_summary.recommended_next_actions[].action",
    ),
    ROUTE_ADOPTION_BLOCKER_RESOURCE_REQUEST_QUEUE: (
        "context_packet.feedback_loop_summary.recommended_next_actions[].source",
    ),
    ROUTE_ADOPTION_BLOCKER_FEEDBACK_REPLAN: (
        "context_packet.feedback_loop_summary.replan_required",
    ),
    ROUTE_ADOPTION_BLOCKER_REALIZATION_COVERAGE: (
        "rows[].realization_coverage_witness.realization_coverage_complete",
        "context_packet.feedback_loop_summary.realization_coverage.complete",
    ),
    ROUTE_ADOPTION_BLOCKER_OMITTED_COST_HINT_PRIMITIVES: (
        "rows[].realization_coverage_witness.omitted_cost_hint_primitives",
        "context_packet.minimal_delta_cost_hints.route_option_hints",
    ),
    ROUTE_ADOPTION_BLOCKER_FORMAL_GAP_BOUNDARIES: (
        "response_payload.informal_knowledge_dag_nodes[].formal_gap_boundary",
        "response_payload.formal_realization_dag_nodes[].formal_gap_boundary",
        "response_payload.residual_interpretations[].formal_gap_boundary",
        "response_payload.standalone_route.primitives[].formal_gap_boundary",
    ),
    ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING: (
        "context_packet.source_grounding_obligations.pending",
        "context_packet.source_grounding_rows[].grounding_status",
        "context_packet.source_grounding_rows[].ok",
    ),
    ROUTE_ADOPTION_BLOCKER_QUALITY_CONTROLS: (
        "context_packet.quality_control_obligations.pending",
        "context_packet.context_packet_inventory.n_pending_quality_control_values",
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
LLM_ROUTE_PLANNER_LEGACY_RESPONSE_FIELD_ALIASES = {
    "lean_realization_dag_nodes": LEGACY_FORMAL_REALIZATION_FIELD_ALIASES[
        "lean_realization_dag_nodes"
    ],
}
LLM_ROUTE_PLANNER_LEGACY_CONTEXT_FIELD_ALIASES = {
    **LEGACY_TARGET_INTAKE_FIELD_ALIASES,
    **LEGACY_FORMAL_SOURCE_ADAPTER_FIELD_ALIASES,
}
SOURCE_SNIPPET_MIN_SUPPORT_TOKENS = 3
SOURCE_SNIPPET_MIN_TWO_TOKEN_SUPPORT_CHARS = 18
FORMAL_GAP_BOUNDARY_MIN_SUPPORT_TOKENS = 3
FORMAL_GAP_BOUNDARY_MIN_TWO_TOKEN_SUPPORT_CHARS = 20
SOURCE_SNIPPET_TEXT_SUPPORT_STOPWORDS = {
    "after",
    "also",
    "among",
    "before",
    "from",
    "into",
    "that",
    "this",
    "under",
    "with",
}
FORMAL_GAP_BOUNDARY_TEXT_STOPWORDS = {
    "after",
    "also",
    "from",
    "into",
    "that",
    "this",
    "under",
    "with",
}
LLM_ROUTE_PLANNER_SOURCE_SEARCH_STATUS_KEYS = (
    "source_backed",
    "search_requested",
    "search_pending",
    "source_search_requested",
    "source_search_pending",
    "literature_search_requested",
    "literature_search_pending",
    "formal_gap_boundary",
    "formal_boundary",
    "formal_boundary_declared",
)
SOURCE_GROUNDING_UNRESOLVED_STATUSES = (
    "source_search_pending",
    "unaccounted",
)
SOURCE_GROUNDING_RESIDUAL_NODE_SOURCE = "refinement_evidence_prover_feedback"
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
        "Use sonnet when the seed route itself carries uncertainty flags, semantic alignment risks, source-search-pending markers, or substantive formal-gap boundaries.",
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
        "new_theory_primitives": ["new theory fragments to design"],
        "first_principles_primitives": ["first-principles fragments to design"],
        "wrapper_lemmas": ["wrappers to write"],
        "bridge_lemmas": ["bridge lemmas to prove"],
        "source_port_lemmas": ["source-backed lemmas to port"],
        "do_not_formalize_now": ["out-of-cut theory fragments"],
        "minimality_rationale": "why this route minimizes new target-prover effort",
    },
    "residual_interpretations": [
        {
            "residual_goal": "prover residual or diagnostic",
            "interpretation": "missing assumption, typeclass, lemma, or wrong formulation",
            "route_repair": "how the route should change",
            "target_primitives": ["primitive ids affected by this residual"],
            "source_refs": ["source ids supporting the repair"],
            "source_snippets": [
                {
                    "source_ref": "paper/book/local source id",
                    "excerpt": "bounded evidence excerpt supporting the repair",
                    "target_primitives": ["primitive ids"],
                }
            ],
            "source_search_status": "SOURCE_BACKED|SEARCH_REQUESTED|FORMAL_GAP_BOUNDARY",
            "formal_gap_boundary": "explicit blocker if this repair is only a formal boundary",
        }
    ],
    "search_requests": [
        {
            "request_kind": "literature|formal_library|prover_feedback|route_revision",
            "query": "bounded next query",
            "reason": "why more evidence is needed before route adoption",
            "target_primitives": ["primitive ids bounded by this request"],
            "resource_request_id": "optional queued request id",
            "resource_id": "optional registry or queued resource id",
            "resource_contract_ids": ["optional grounded resource contract ids"],
            "required_quality_signals": ["optional grounded quality signals"],
            "quality_gates": ["optional grounded quality gates"],
            "response_validation_signals": ["optional grounded response checks"],
            "stop_conditions": ["optional grounded stop conditions"],
        }
    ],
    "uncertainty_flags": ["semantic risks and missing evidence"],
    "semantic_alignment_risks": ["risks in matching informal and formal meanings"],
    "planner_next_actions": [
        {
            "owner": "resource or prover adapter",
            "action": "bounded next action",
            "target_primitives": ["primitive ids bounded by this action"],
            "resource_request_id": "optional queued request id",
            "resource_id": "optional registry or queued resource id",
            "resource_contract_ids": ["optional grounded resource contract ids"],
            "required_quality_signals": ["optional grounded quality signals"],
            "quality_gates": ["optional grounded quality gates"],
            "response_validation_signals": ["optional grounded response checks"],
            "stop_conditions": ["optional grounded stop conditions"],
        }
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
    model_tier_decision_evidence: dict[str, object]
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
    quality_control_obligations: dict[str, object]
    feedback_loop_summary: dict[str, object]
    context_packet_inventory: dict[str, object]
    raw_response_text: str
    generator_metadata: dict[str, object]
    provider_failure: bool
    repair_attempts: int
    repair_error_history: tuple[dict[str, object], ...]
    repair_attempt_ledger: tuple[dict[str, object], ...]
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
    formalization_gap_planner_route_replan_handoff_dir: Path | None = None,
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
        formalization_gap_planner_route_replan_handoff_dir=(
            formalization_gap_planner_route_replan_handoff_dir
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
    by_model_tier_decision_basis = Counter(
        str(
            _dict_value(packet, "model_tier_decision_evidence").get(
                "decision_basis",
                "",
            )
            or "missing"
        )
        for packet in request_packets
    )
    invalid_model_tier_decision_evidence = tuple(
        packet
        for packet in request_packets
        if _model_tier_decision_evidence_errors(
            _dict_value(packet, "model_tier_decision_evidence"),
            selected_model_tier=str(packet.get("model_tier", "")),
            effective_model_tier=str(packet.get("model_tier", "")),
            allow_repair_escalation=False,
        )
    )
    request_generation_policy_tier_matches = [
        packet
        for packet in request_packets
        if _dict_value(packet, "llm_generation_policy").get("selected_model_tier")
        == packet.get("model_tier")
        and _dict_value(packet, "llm_generation_policy").get("resolved_model")
        == packet.get("model")
    ]
    request_generation_policy_current_claude_tier_sources = [
        packet
        for packet in request_packets
        if not _llm_generation_policy_claude_model_source_errors(
            _dict_value(packet, "llm_generation_policy")
        )
    ]
    library_alignment_summaries = tuple(
        _request_library_alignment_summary(packet) for packet in request_packets
    )
    library_alignment_route_option_rows = tuple(
        row
        for summary in library_alignment_summaries
        for row in _dict_tuple(summary.get("route_option_alignment", []))
    )
    by_library_delta_class = Counter(
        str(row.get("library_delta_class", "") or "unknown")
        for summary in library_alignment_summaries
        for row in _dict_tuple(summary.get("primitive_alignment", []))
    )
    by_library_minimum_coverage_bucket = Counter(
        str(row.get("minimum_coverage_bucket", "") or "unknown")
        for summary in library_alignment_summaries
        for row in _dict_tuple(summary.get("primitive_alignment", []))
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
    generation_preflight_errors = _generation_preflight_errors(
        request_packets,
        request_schema_errors,
    )
    generation_request_packets = tuple(
        packet
        for packet, packet_errors in zip(request_packets, request_schema_errors)
        if not packet_errors
    )
    if invoke_provider and generator_backend is not None:
        raw_responses.extend(
            _generate_responses(
                generation_request_packets,
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
    by_route_adoption_blocker = _route_adoption_blocker_summary(rows)
    route_adoption_blocker_counts = _route_adoption_blocker_counts(rows)
    repair_attempt_ledger = tuple(
        ledger_row
        for row in rows
        for ledger_row in row.repair_attempt_ledger
    )
    standalone_seed = _standalone_seed(input_payload, rows)
    standalone_replay_gate = _standalone_replay_gate(row_dicts, standalone_seed)
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
        "legacy_response_field_aliases": dict(
            LLM_ROUTE_PLANNER_LEGACY_RESPONSE_FIELD_ALIASES
        ),
        "legacy_context_field_aliases": dict(
            LLM_ROUTE_PLANNER_LEGACY_CONTEXT_FIELD_ALIASES
        ),
        "max_repair_attempts": max(0, int(max_repair_attempts)),
        "invoke_provider": invoke_provider,
        "n_routes": len(routes),
        "n_request_packets": len(request_packets),
        "n_requests_with_context_packet_inventory": sum(
            1
            for packet in request_packets
            if _dict_value(
                _dict_value(packet, "context_packet"),
                "context_packet_inventory",
            )
        ),
        "n_request_context_inventory_total_rows": sum(
            int(
                _dict_value(
                    _dict_value(packet, "context_packet"),
                    "context_packet_inventory",
                ).get("total_context_rows", 0)
                or 0
            )
            for packet in request_packets
        ),
        "n_requests_with_route_planning_brief": sum(
            1
            for packet in request_packets
            if _dict_value(
                _dict_value(packet, "context_packet"),
                "route_planning_brief",
            )
        ),
        "n_request_route_planning_focus_rows": sum(
            len(
                _dict_tuple(
                    _dict_value(
                        _dict_value(packet, "context_packet"),
                        "route_planning_brief",
                    ).get("planner_focus", [])
                )
            )
            for packet in request_packets
        ),
        "n_request_route_planning_evidence_gaps": sum(
            len(
                _dict_tuple(
                    _dict_value(
                        _dict_value(packet, "context_packet"),
                        "route_planning_brief",
                    ).get("evidence_gaps", [])
                )
            )
            for packet in request_packets
        ),
        "n_requests_with_library_alignment_summary": sum(
            1 for summary in library_alignment_summaries if summary
        ),
        "n_request_library_alignment_primitives": sum(
            int(summary.get("n_primitives", 0) or 0)
            for summary in library_alignment_summaries
        ),
        "n_request_library_alignment_reuse_ready_primitives": (
            by_library_delta_class.get("reuse_ready", 0)
        ),
        "n_request_library_alignment_wrapper_primitives": (
            by_library_delta_class.get("wrapper", 0)
        ),
        "n_request_library_alignment_bridge_primitives": (
            by_library_delta_class.get("bridge", 0)
        ),
        "n_request_library_alignment_source_port_primitives": (
            by_library_delta_class.get("source_port", 0)
        ),
        "n_request_library_alignment_new_definition_primitives": (
            by_library_delta_class.get("new_definition", 0)
        ),
        "n_request_library_alignment_new_theory_primitives": (
            by_library_delta_class.get("new_theory", 0)
        ),
        "n_request_library_alignment_unknown_primitives": (
            by_library_delta_class.get("unknown", 0)
        ),
        "n_request_library_alignment_bridge_or_harder_primitives": sum(
            int(summary.get("n_bridge_or_harder_primitives", 0) or 0)
            for summary in library_alignment_summaries
        ),
        "n_request_library_alignment_target_compatible_reuse_declarations": sum(
            int(summary.get("n_target_compatible_reuse_declarations", 0) or 0)
            for summary in library_alignment_summaries
        ),
        "n_request_library_alignment_route_options": len(
            library_alignment_route_option_rows
        ),
        "n_request_library_alignment_route_option_primitives": sum(
            int(row.get("n_selected_primitives", 0) or 0)
            for row in library_alignment_route_option_rows
        ),
        "n_request_library_alignment_route_option_bridge_or_harder_primitives": sum(
            int(row.get("n_bridge_or_harder_primitives", 0) or 0)
            for row in library_alignment_route_option_rows
        ),
        "n_request_library_alignment_route_option_target_compatible_reuse_declarations": sum(
            int(row.get("n_target_compatible_reuse_declarations", 0) or 0)
            for row in library_alignment_route_option_rows
        ),
        "total_request_library_alignment_route_option_minimum_base_cost": sum(
            float(row.get("minimum_route_base_cost", 0) or 0)
            for row in library_alignment_route_option_rows
            if _is_nonnegative_number(row.get("minimum_route_base_cost"))
        ),
        "by_request_library_alignment_delta_class": dict(
            sorted(by_library_delta_class.items())
        ),
        "by_request_library_alignment_minimum_coverage_bucket": dict(
            sorted(by_library_minimum_coverage_bucket.items())
        ),
        "n_requests_with_legacy_context_field_aliases": sum(
            1
            for packet in request_packets
            if _dict_value(
                _dict_value(packet, "context_packet"),
                "legacy_context_field_aliases",
            )
            and _dict_value(
                _dict_value(packet, "context_packet"),
                "legacy_context_field_aliases",
            )
            == _legacy_context_field_aliases_for_target(
                packet.get("target_prover_family", "")
            )
        ),
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
        "n_requests_with_model_tier_decision_evidence": sum(
            1
            for packet in request_packets
            if _dict_value(packet, "model_tier_decision_evidence")
        ),
        "n_request_model_tier_decision_auto_haiku_bounded": (
            by_model_tier_decision_basis.get("auto_haiku_bounded_route", 0)
        ),
        "n_request_model_tier_decision_auto_sonnet_triggered": (
            by_model_tier_decision_basis.get("auto_sonnet_triggers", 0)
        ),
        "n_request_model_tier_decision_operator_override": (
            by_model_tier_decision_basis.get("operator_override", 0)
        ),
        "n_request_model_tier_decision_sonnet_triggers": sum(
            len(
                _str_tuple(
                    _dict_value(packet, "model_tier_decision_evidence").get(
                        "sonnet_triggers",
                        [],
                    )
                )
            )
            for packet in request_packets
        ),
        "n_request_model_tier_decision_evidence_invalid": len(
            invalid_model_tier_decision_evidence
        ),
        "by_request_model_tier_decision_basis": dict(
            sorted(by_model_tier_decision_basis.items())
        ),
        "n_requests_with_llm_generation_policy": sum(
            1 for packet in request_packets if packet.get("llm_generation_policy")
        ),
        "n_request_llm_generation_policy_tier_model_matches": len(
            request_generation_policy_tier_matches
        ),
        "n_request_llm_generation_policy_codex_exclusions": sum(
            1
            for packet in request_packets
            if {"codex", "codex_exec"}.issubset(
                set(
                    _str_tuple(
                        _dict_value(packet, "llm_generation_policy").get(
                            "prohibited_generator_providers",
                            [],
                        )
                    )
                )
            )
        ),
        "n_request_llm_generation_policy_current_claude_tier_source": len(
            request_generation_policy_current_claude_tier_sources
        ),
        "n_request_model_tier_mismatches": len(request_model_tier_mismatches),
        "request_model_tier_mismatches": request_model_tier_mismatches,
        "n_generation_preflight_blocked": len(generation_preflight_errors),
        "generation_preflight_errors": generation_preflight_errors,
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
        "n_request_source_grounding_rows": sum(
            len(
                _dict_tuple(
                    _dict_value(packet, "context_packet").get(
                        "source_grounding_rows",
                        [],
                    )
                )
            )
            for packet in request_packets
        ),
        "n_requests_with_source_grounding_obligation_inventory": sum(
            1
            for packet in request_packets
            if _request_context_packet_inventory(packet).get(
                "source_grounding_obligation_present",
            )
        ),
        "n_requests_with_pending_source_grounding_obligation_inventory": sum(
            1
            for packet in request_packets
            if _request_context_packet_inventory(packet).get(
                "source_grounding_obligation_pending",
            )
        ),
        "n_request_source_grounding_unresolved_rows": sum(
            int(
                _request_context_packet_inventory(packet).get(
                    "source_grounding_unresolved_count",
                    0,
                )
                or 0
            )
            for packet in request_packets
        ),
        "n_request_residual_source_grounding_unresolved_rows": sum(
            int(
                _request_context_packet_inventory(packet).get(
                    "residual_source_grounding_unresolved_count",
                    0,
                )
                or 0
            )
            for packet in request_packets
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
        "n_requests_with_minimal_delta_cost_hints": sum(
            1
            for packet in request_packets
            if _dict_value(packet, "context_packet").get(
                "minimal_delta_cost_hints"
            )
        ),
        "n_request_primitive_cost_hints": sum(
            len(
                _dict_tuple(
                    _dict_value(
                        _dict_value(packet, "context_packet"),
                        "minimal_delta_cost_hints",
                    ).get("primitive_cost_hints", [])
                )
            )
            for packet in request_packets
        ),
        "n_request_route_option_cost_hints": sum(
            len(
                _dict_tuple(
                    _dict_value(
                        _dict_value(packet, "context_packet"),
                        "minimal_delta_cost_hints",
                    ).get("route_option_hints", [])
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
        "n_requests_with_route_replan_handoff_rows": sum(
            1
            for packet in request_packets
            if _dict_tuple(
                _dict_value(packet, "context_packet").get(
                    "route_replan_handoff_rows",
                    [],
                )
            )
        ),
        "n_request_route_replan_handoff_rows": sum(
            len(
                _dict_tuple(
                    _dict_value(packet, "context_packet").get(
                        "route_replan_handoff_rows",
                        [],
                    )
                )
            )
            for packet in request_packets
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
        "n_feedback_loop_summary_incomplete_cost_hint_baseline_coverage": sum(
            1
            for packet in request_packets
            if _dict_value(
                _dict_value(
                    _dict_value(packet, "context_packet"),
                    "feedback_loop_summary",
                ),
                "realization_coverage",
            ).get("cost_hint_baseline_coverage_complete") is False
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
        "n_feedback_loop_summary_omitted_cost_hint_primitives": sum(
            len(
                _str_tuple(
                    _dict_value(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "feedback_loop_summary",
                        ),
                        "realization_coverage",
                    ).get("omitted_cost_hint_primitives", [])
                )
            )
            for packet in request_packets
        ),
        "n_feedback_loop_summary_prior_llm_route_planner_hook_traces": sum(
            len(
                _dict_tuple(
                    _dict_value(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "feedback_loop_summary",
                        ),
                        "prior_replan_metadata",
                    ).get("applied_llm_route_planner_hook_traces", [])
                )
            )
            for packet in request_packets
        ),
        "n_requests_with_feedback_loop_summary_prior_llm_route_planner_hook_traces": sum(
            1
            for packet in request_packets
            if _dict_tuple(
                _dict_value(
                    _dict_value(
                        _dict_value(packet, "context_packet"),
                        "feedback_loop_summary",
                    ),
                    "prior_replan_metadata",
                ).get("applied_llm_route_planner_hook_traces", [])
            )
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
        "n_requests_with_quality_control_obligation_inventory": sum(
            1
            for packet in request_packets
            if _request_context_packet_inventory(packet).get(
                "quality_control_obligation_present",
            )
        ),
        "n_requests_with_pending_quality_control_obligation_inventory": sum(
            1
            for packet in request_packets
            if _request_context_packet_inventory(packet).get(
                "quality_control_obligation_pending",
            )
        ),
        "n_request_quality_control_obligation_fields": sum(
            int(
                _request_context_packet_inventory(packet).get(
                    "quality_control_obligation_field_count",
                    0,
                )
                or 0
            )
            for packet in request_packets
        ),
        "n_request_quality_control_obligation_values": sum(
            int(
                _request_context_packet_inventory(packet).get(
                    "quality_control_obligation_value_count",
                    0,
                )
                or 0
            )
            for packet in request_packets
        ),
        "n_request_pending_quality_control_fields": sum(
            int(
                _request_context_packet_inventory(packet).get(
                    "pending_quality_control_field_count",
                    0,
                )
                or 0
            )
            for packet in request_packets
        ),
        "n_request_pending_quality_control_values": sum(
            int(
                _request_context_packet_inventory(packet).get(
                    "pending_quality_control_value_count",
                    0,
                )
                or 0
            )
            for packet in request_packets
        ),
        "n_request_discharged_quality_control_fields": sum(
            int(
                _request_context_packet_inventory(packet).get(
                    "discharged_quality_control_field_count",
                    0,
                )
                or 0
            )
            for packet in request_packets
        ),
        "n_request_discharged_quality_control_values": sum(
            int(
                _request_context_packet_inventory(packet).get(
                    "discharged_quality_control_value_count",
                    0,
                )
                or 0
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
        "n_generated_responses_model_tier_escalated": sum(
            1
            for row in raw_responses
            if isinstance(row, Mapping)
            and (
                row.get("model_tier_escalated")
                or _dict_value(row, "generator_metadata").get(
                    "model_tier_escalated"
                )
            )
        ),
        "n_generated_responses_haiku_to_sonnet_escalated": sum(
            1
            for row in raw_responses
            if isinstance(row, Mapping)
            and str(row.get("requested_model_tier", "")).strip().lower()
            == "haiku"
            and str(row.get("model_tier", "")).strip().lower() == "sonnet"
            and (
                row.get("model_tier_escalated")
                or _dict_value(row, "generator_metadata").get(
                    "model_tier_escalated"
                )
            )
        ),
        "n_repair_attempt_ledger_rows": len(repair_attempt_ledger),
        "n_requests_with_repair_attempt_ledger": len(
            {
                str(row.get("request_id", ""))
                for row in repair_attempt_ledger
                if str(row.get("request_id", "")).strip()
            }
        ),
        "n_repair_attempt_ledger_error_items": sum(
            int(row.get("error_count", 0) or 0)
            for row in repair_attempt_ledger
        ),
        "n_repair_attempt_ledger_model_tier_escalations": sum(
            1
            for row in repair_attempt_ledger
            if row.get("model_tier_escalated")
        ),
        "repair_attempt_ledger": repair_attempt_ledger,
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
        "n_rows_with_model_tier_escalation": sum(
            1
            for row in rows
            if row.generator_metadata.get("model_tier_escalated")
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
        "route_adoption_blocker_counts": route_adoption_blocker_counts,
        "by_route_adoption_status": dict(sorted(by_route_adoption_status.items())),
        "by_route_adoption_blocker": by_route_adoption_blocker,
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
        "n_route_adoption_pending_omitted_cost_hint_primitive_blockers": sum(
            1
            for row in rows
            if ROUTE_ADOPTION_BLOCKER_OMITTED_COST_HINT_PRIMITIVES
            in row.route_adoption_blockers
        ),
        "n_route_adoption_pending_formal_gap_boundary_blockers": sum(
            1
            for row in rows
            if ROUTE_ADOPTION_BLOCKER_FORMAL_GAP_BOUNDARIES
            in row.route_adoption_blockers
        ),
        "n_route_adoption_pending_source_grounding_blockers": sum(
            1
            for row in rows
            if ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING
            in row.route_adoption_blockers
        ),
        "n_route_adoption_pending_quality_control_blockers": sum(
            1
            for row in rows
            if ROUTE_ADOPTION_BLOCKER_QUALITY_CONTROLS
            in row.route_adoption_blockers
        ),
        "n_route_adoption_omitted_cost_hint_primitives": sum(
            len(_omitted_cost_hint_primitives(row.minimal_delta_plan, request))
            for row, request in zip(rows, request_packets)
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
        "n_delta_action_witness_required_primitives": sum(
            len(
                _str_tuple(
                    row.realization_coverage_witness.get(
                        "delta_action_witness_required_primitives",
                        [],
                    )
                )
            )
            for row in rows
        ),
        "n_delta_action_witness_missing_primitives": sum(
            len(
                _str_tuple(
                    row.realization_coverage_witness.get(
                        "delta_action_witness_missing_primitives",
                        [],
                    )
                )
            )
            for row in rows
        ),
        "n_rows_with_delta_action_witness_obligations": sum(
            1
            for row in rows
            if _str_tuple(
                row.realization_coverage_witness.get(
                    "delta_action_witness_required_primitives",
                    [],
                )
            )
        ),
        "n_rows_with_complete_delta_action_witness": sum(
            1
            for row in rows
            if _str_tuple(
                row.realization_coverage_witness.get(
                    "delta_action_witness_required_primitives",
                    [],
                )
            )
            and bool(
                row.realization_coverage_witness.get(
                    "delta_action_witness_complete",
                    False,
                )
            )
        ),
        "n_search_requests": sum(len(row.search_requests) for row in rows),
        "n_planner_next_actions": sum(len(row.planner_next_actions) for row in rows),
        "n_rows_with_planner_next_actions": sum(
            1 for row in rows if row.planner_next_actions
        ),
        "n_rows_with_context_packet_inventory": sum(
            1 for row in rows if row.context_packet_inventory
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
        "standalone_replay_gate": standalone_replay_gate,
        "standalone_replay_gate_ok": bool(standalone_replay_gate.get("gate_ok", False)),
        "n_standalone_replay_route_candidates": int(
            standalone_replay_gate.get("n_route_candidates", 0) or 0
        ),
        "n_standalone_replay_adoptable_route_candidates": int(
            standalone_replay_gate.get("n_adoptable_route_candidates", 0) or 0
        ),
        "n_standalone_replay_blocked_route_candidates": int(
            standalone_replay_gate.get("n_blocked_route_candidates", 0) or 0
        ),
        "standalone_replay_gate_blockers": list(
            _str_tuple(standalone_replay_gate.get("gate_blockers", []))
        ),
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
        payload_target_prover_family = _declared_payload_target_prover_family(
            payload
        )
        payload_target_prover_key = _target_prover_key(
            payload_target_prover_family
        )
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
            request_context_target_prover_family = str(
                request_context.get("target_prover_family", "") or ""
            ).strip()
            request_context_target_prover_key = _target_prover_key(
                request_context_target_prover_family
            )
            request_context_inventory = _dict_value(
                _dict_value(request_context, "context_packet"),
                "context_packet_inventory",
            )
        elif request_context_json is not None:
            request_context_validation_mode = "request_context_unmatched"
            request_context_id = ""
            request_context_route_id = ""
            request_context_target_prover_family = ""
            request_context_target_prover_key = ""
            request_context_inventory = {}
        else:
            request_context_validation_mode = "schema_only"
            request_context_id = ""
            request_context_route_id = ""
            request_context_target_prover_family = ""
            request_context_target_prover_key = ""
            request_context_inventory = {}
        target_prover_family_consistent = not (
            payload_target_prover_key
            and request_context_target_prover_key
            and payload_target_prover_key != request_context_target_prover_key
        )
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
                "payload_target_prover_family": payload_target_prover_family,
                "payload_target_prover_key": payload_target_prover_key,
                "request_context_target_prover_family": (
                    request_context_target_prover_family
                ),
                "request_context_target_prover_key": request_context_target_prover_key,
                "target_prover_family_consistent": (
                    target_prover_family_consistent
                ),
                "request_context_inventory_present": bool(request_context_inventory),
                "request_context_inventory_total_rows": int(
                    request_context_inventory.get("total_context_rows", 0) or 0
                ),
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
    request_context_inventories = tuple(
        _dict_value(
            _dict_value(request_context, "context_packet"),
            "context_packet_inventory",
        )
        for request_context in request_contexts
    )
    request_context_inventory_total_rows = sum(
        int(inventory.get("total_context_rows", 0) or 0)
        for inventory in request_context_inventories
        if inventory
    )
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
        "n_request_contexts_with_context_packet_inventory": sum(
            1 for inventory in request_context_inventories if inventory
        ),
        "n_request_context_inventory_total_rows": (
            request_context_inventory_total_rows
        ),
        "n_request_bound_payloads": sum(
            1
            for row in rows
            if row["request_context_validation_mode"] == "request_bound"
        ),
        "n_request_bound_payloads_with_context_packet_inventory": sum(
            1
            for row in rows
            if row["request_context_validation_mode"] == "request_bound"
            and row["request_context_inventory_present"]
        ),
        "n_request_bound_payload_context_inventory_total_rows": sum(
            int(row["request_context_inventory_total_rows"] or 0)
            for row in rows
            if row["request_context_validation_mode"] == "request_bound"
        ),
        "n_payloads_with_declared_target_prover_family": sum(
            1 for row in rows if str(row["payload_target_prover_family"]).strip()
        ),
        "n_request_bound_payloads_with_target_prover_family_mismatch": sum(
            1
            for row in rows
            if row["request_context_validation_mode"] == "request_bound"
            and not bool(row["target_prover_family_consistent"])
        ),
        "by_payload_target_prover_family": _value_counts(
            [
                str(row["payload_target_prover_key"]).strip()
                for row in rows
                if str(row["payload_target_prover_key"]).strip()
            ]
        ),
        "by_request_context_target_prover_family": _value_counts(
            [
                str(row["request_context_target_prover_key"]).strip()
                for row in rows
                if str(row["request_context_target_prover_key"]).strip()
            ]
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
    library_alignment_summary_schema = (
        llm_route_planner_library_alignment_summary_json_schema()
    )
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
            "model_tier_decision_evidence",
            "llm_generation_policy",
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
            "model_tier_decision_evidence": {"type": "object"},
            "llm_generation_policy": {"type": "object"},
            "target_prover_family": {"type": "string", "minLength": 1},
            "library_snapshot_ref": {"type": "string", "minLength": 1},
            "target_route": {"type": "object"},
            "context_packet": {
                "type": "object",
                "required": ["library_alignment_summary"],
                "properties": {
                    "library_alignment_summary": {
                        "$ref": "#/$defs/library_alignment_summary"
                    }
                },
            },
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
        "$defs": {
            "library_alignment_summary": library_alignment_summary_schema,
        },
    }


def llm_route_planner_library_alignment_summary_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    nonnegative_integer = {"type": "integer", "minimum": 0}
    nonnegative_number = {"type": "number", "minimum": 0}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": LLM_ROUTE_PLANNER_LIBRARY_ALIGNMENT_SUMMARY_SCHEMA_ID,
        "title": (
            "Formalization Gap Planner LLM Route Planner Library Alignment Summary"
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "schema_id",
            "summary_kind",
            "route_id",
            "display_name",
            "target_prover_family",
            "library_snapshot_ref",
            "cost_policy_id",
            "n_primitives",
            "n_reuse_ready_primitives",
            "n_wrapper_primitives",
            "n_bridge_primitives",
            "n_source_port_primitives",
            "n_new_definition_primitives",
            "n_new_theory_primitives",
            "n_unknown_primitives",
            "n_bridge_or_harder_primitives",
            "n_target_compatible_reuse_declarations",
            "n_route_options",
            "by_library_delta_class",
            "by_minimum_coverage_bucket",
            "primitive_alignment",
            "route_option_alignment",
            "proof_evidence_status",
            "proof_evidence_boundary",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SCHEMA_VERSION,
            },
            "schema_id": {
                "type": "string",
                "const": LLM_ROUTE_PLANNER_LIBRARY_ALIGNMENT_SUMMARY_SCHEMA_ID,
            },
            "summary_kind": {
                "type": "string",
                "const": LIBRARY_ALIGNMENT_SUMMARY_KIND,
            },
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "target_prover_family": {"type": "string", "minLength": 1},
            "library_snapshot_ref": {"type": "string"},
            "cost_policy_id": {
                "type": "string",
                "const": MINIMAL_DELTA_COST_POLICY_ID,
            },
            "n_primitives": nonnegative_integer,
            "n_reuse_ready_primitives": nonnegative_integer,
            "n_wrapper_primitives": nonnegative_integer,
            "n_bridge_primitives": nonnegative_integer,
            "n_source_port_primitives": nonnegative_integer,
            "n_new_definition_primitives": nonnegative_integer,
            "n_new_theory_primitives": nonnegative_integer,
            "n_unknown_primitives": nonnegative_integer,
            "n_bridge_or_harder_primitives": nonnegative_integer,
            "n_target_compatible_reuse_declarations": nonnegative_integer,
            "n_route_options": nonnegative_integer,
            "by_library_delta_class": {
                "type": "object",
                "additionalProperties": nonnegative_integer,
            },
            "by_minimum_coverage_bucket": {
                "type": "object",
                "additionalProperties": nonnegative_integer,
            },
            "primitive_alignment": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": True,
                    "required": [
                        "primitive",
                        "minimum_coverage_bucket",
                        "library_delta_class",
                        "minimum_base_cost",
                        "minimum_cost_source",
                        "minimum_cost_marker",
                        "evidence_sources",
                        "has_target_compatible_declaration",
                        "target_compatible_declarations",
                        "target_compatible_declaration_count",
                        "candidate_declaration_row_count",
                    ],
                    "properties": {
                        "primitive": {"type": "string", "minLength": 1},
                        "minimum_coverage_bucket": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "library_delta_class": {
                            "type": "string",
                            "enum": [
                                "reuse_ready",
                                "wrapper",
                                "bridge",
                                "source_port",
                                "new_definition",
                                "new_theory",
                                "unknown",
                            ],
                        },
                        "minimum_base_cost": nonnegative_number,
                        "minimum_cost_source": {"type": "string"},
                        "minimum_cost_marker": {"type": "string"},
                        "evidence_sources": string_array,
                        "has_target_compatible_declaration": {"type": "boolean"},
                        "target_compatible_declarations": string_array,
                        "target_compatible_declaration_count": nonnegative_integer,
                        "candidate_declaration_row_count": nonnegative_integer,
                    },
                },
            },
            "route_option_alignment": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": True,
                    "required": [
                        "route_option_id",
                        "option_kind",
                        "selected_primitives",
                        "n_selected_primitives",
                        "minimum_route_base_cost",
                        "cost_policy_id",
                        "cost_rationale",
                        "n_bridge_or_harder_primitives",
                        "n_target_compatible_reuse_declarations",
                        "by_library_delta_class",
                        "by_minimum_coverage_bucket",
                    ],
                    "properties": {
                        "route_option_id": {"type": "string", "minLength": 1},
                        "option_kind": {"type": "string"},
                        "selected_primitives": string_array,
                        "n_selected_primitives": nonnegative_integer,
                        "minimum_route_base_cost": nonnegative_number,
                        "cost_policy_id": {
                            "type": "string",
                            "const": MINIMAL_DELTA_COST_POLICY_ID,
                        },
                        "cost_rationale": {"type": "string"},
                        "n_bridge_or_harder_primitives": nonnegative_integer,
                        "n_target_compatible_reuse_declarations": nonnegative_integer,
                        "by_library_delta_class": {
                            "type": "object",
                            "additionalProperties": nonnegative_integer,
                        },
                        "by_minimum_coverage_bucket": {
                            "type": "object",
                            "additionalProperties": nonnegative_integer,
                        },
                    },
                },
            },
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


def llm_route_planner_manifest_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    object_array = {"type": "array", "items": {"type": "object"}}
    nonnegative_integer = {"type": "integer", "minimum": 0}
    nonnegative_number = {"type": "number", "minimum": 0}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": LLM_ROUTE_PLANNER_MANIFEST_SCHEMA_ID,
        "title": "Formalization Gap Planner LLM Route Planner Manifest",
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "created_at",
            "component_name",
            "standalone_input_path",
            "provider_name",
            "model_tier_selection_mode",
            "llm_route_planner_model_tier_policy",
            "legacy_response_field_aliases",
            "legacy_context_field_aliases",
            "invoke_provider",
            "n_routes",
            "n_request_packets",
            "n_requests_with_context_packet_inventory",
            "n_request_context_inventory_total_rows",
            "n_requests_with_route_planning_brief",
            "n_request_route_planning_focus_rows",
            "n_request_route_planning_evidence_gaps",
            "n_requests_with_library_alignment_summary",
            "n_request_library_alignment_primitives",
            "n_request_library_alignment_reuse_ready_primitives",
            "n_request_library_alignment_wrapper_primitives",
            "n_request_library_alignment_bridge_primitives",
            "n_request_library_alignment_source_port_primitives",
            "n_request_library_alignment_new_definition_primitives",
            "n_request_library_alignment_new_theory_primitives",
            "n_request_library_alignment_unknown_primitives",
            "n_request_library_alignment_bridge_or_harder_primitives",
            "n_request_library_alignment_target_compatible_reuse_declarations",
            "n_request_library_alignment_route_options",
            "n_request_library_alignment_route_option_primitives",
            "n_request_library_alignment_route_option_bridge_or_harder_primitives",
            "n_request_library_alignment_route_option_target_compatible_reuse_declarations",
            "total_request_library_alignment_route_option_minimum_base_cost",
            "by_request_library_alignment_delta_class",
            "by_request_library_alignment_minimum_coverage_bucket",
            "n_requests_with_legacy_context_field_aliases",
            "n_request_model_tier_haiku",
            "n_request_model_tier_sonnet",
            "n_request_model_tier_opus",
            "by_request_model_tier",
            "n_requests_with_model_tier_decision_evidence",
            "n_request_model_tier_decision_auto_haiku_bounded",
            "n_request_model_tier_decision_auto_sonnet_triggered",
            "n_request_model_tier_decision_operator_override",
            "n_request_model_tier_decision_sonnet_triggers",
            "n_request_model_tier_decision_evidence_invalid",
            "by_request_model_tier_decision_basis",
            "n_requests_with_llm_generation_policy",
            "n_request_llm_generation_policy_tier_model_matches",
            "n_request_llm_generation_policy_codex_exclusions",
            "n_request_llm_generation_policy_current_claude_tier_source",
            "n_request_model_tier_mismatches",
            "request_model_tier_mismatches",
            "n_generation_preflight_blocked",
            "n_request_source_grounding_rows",
            "n_requests_with_source_grounding_obligation_inventory",
            "n_requests_with_pending_source_grounding_obligation_inventory",
            "n_request_source_grounding_unresolved_rows",
            "n_request_residual_source_grounding_unresolved_rows",
            "n_requests_with_quality_control_obligation_inventory",
            "n_requests_with_pending_quality_control_obligation_inventory",
            "n_request_quality_control_obligation_fields",
            "n_request_quality_control_obligation_values",
            "n_request_pending_quality_control_fields",
            "n_request_pending_quality_control_values",
            "n_request_discharged_quality_control_fields",
            "n_request_discharged_quality_control_values",
            "n_request_schema_valid",
            "n_request_schema_invalid",
            "n_raw_responses",
            "n_repair_attempt_ledger_rows",
            "n_requests_with_repair_attempt_ledger",
            "n_repair_attempt_ledger_error_items",
            "repair_attempt_ledger",
            "n_response_schema_valid",
            "n_response_schema_invalid",
            "n_rows",
            "n_response_present",
            "n_response_contract_ok",
            "n_accepted_route_plans",
            "n_route_adoption_ready",
            "n_route_adoption_pending_refinement",
            "n_route_adoption_awaiting_llm_response",
            "n_route_adoption_rejected",
            "route_adoption_blocker_taxonomy_id",
            "route_adoption_blocker_values",
            "route_adoption_blocker_counts",
            "by_route_adoption_status",
            "by_route_adoption_blocker",
            "n_route_adoption_pending_formal_gap_boundary_blockers",
            "n_route_adoption_pending_source_grounding_blockers",
            "n_route_adoption_pending_quality_control_blockers",
            "n_informal_knowledge_dag_nodes",
            "n_formal_realization_dag_nodes",
            "n_lean_realization_dag_nodes",
            "n_route_alignment_edges",
            "n_delta_action_witness_required_primitives",
            "n_delta_action_witness_missing_primitives",
            "n_rows_with_delta_action_witness_obligations",
            "n_rows_with_complete_delta_action_witness",
            "n_rows_with_context_packet_inventory",
            "n_row_schema_valid",
            "n_row_schema_invalid",
            "request_schema",
            "response_payload_schema",
            "response_schema",
            "row_schema",
            "request_packets",
            "rows",
            "standalone_seed",
            "standalone_replay_gate",
            "standalone_replay_gate_ok",
            "n_standalone_replay_route_candidates",
            "n_standalone_replay_adoptable_route_candidates",
            "n_standalone_replay_blocked_route_candidates",
            "standalone_replay_gate_blockers",
            "by_acceptance_status",
            "all_ok",
            "errors",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "limitations",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SCHEMA_VERSION,
            },
            "created_at": {"type": "string", "minLength": 1},
            "component_name": {"type": "string", "const": LLM_ROUTE_PLANNER_COMPONENT},
            "standalone_input_path": {"type": "string", "minLength": 1},
            "provider_name": {"type": "string", "minLength": 1},
            "model": {"type": "string"},
            "model_tier_selection_mode": {"type": "string", "minLength": 1},
            "llm_route_planner_model_tier_policy": {"type": "object"},
            "legacy_response_field_aliases": {
                "type": "object",
                "required": ["lean_realization_dag_nodes"],
                "properties": {
                    "lean_realization_dag_nodes": {
                        "type": "string",
                        "const": "formal_realization_dag_nodes",
                    }
                },
            },
            "legacy_context_field_aliases": {
                "type": "object",
                "required": sorted(LLM_ROUTE_PLANNER_LEGACY_CONTEXT_FIELD_ALIASES),
                "properties": {
                    key: {"type": "string", "const": value}
                    for key, value in LLM_ROUTE_PLANNER_LEGACY_CONTEXT_FIELD_ALIASES.items()
                },
            },
            "max_repair_attempts": nonnegative_integer,
            "invoke_provider": {"type": "boolean"},
            "n_routes": nonnegative_integer,
            "n_request_packets": nonnegative_integer,
            "n_requests_with_context_packet_inventory": nonnegative_integer,
            "n_request_context_inventory_total_rows": nonnegative_integer,
            "n_requests_with_route_planning_brief": nonnegative_integer,
            "n_request_route_planning_focus_rows": nonnegative_integer,
            "n_request_route_planning_evidence_gaps": nonnegative_integer,
            "n_requests_with_library_alignment_summary": nonnegative_integer,
            "n_request_library_alignment_primitives": nonnegative_integer,
            "n_request_library_alignment_reuse_ready_primitives": nonnegative_integer,
            "n_request_library_alignment_wrapper_primitives": nonnegative_integer,
            "n_request_library_alignment_bridge_primitives": nonnegative_integer,
            "n_request_library_alignment_source_port_primitives": nonnegative_integer,
            "n_request_library_alignment_new_definition_primitives": (
                nonnegative_integer
            ),
            "n_request_library_alignment_new_theory_primitives": (
                nonnegative_integer
            ),
            "n_request_library_alignment_unknown_primitives": nonnegative_integer,
            "n_request_library_alignment_bridge_or_harder_primitives": (
                nonnegative_integer
            ),
            "n_request_library_alignment_target_compatible_reuse_declarations": (
                nonnegative_integer
            ),
            "n_request_library_alignment_route_options": nonnegative_integer,
            "n_request_library_alignment_route_option_primitives": (
                nonnegative_integer
            ),
            "n_request_library_alignment_route_option_bridge_or_harder_primitives": (
                nonnegative_integer
            ),
            "n_request_library_alignment_route_option_target_compatible_reuse_declarations": (
                nonnegative_integer
            ),
            "total_request_library_alignment_route_option_minimum_base_cost": (
                nonnegative_number
            ),
            "by_request_library_alignment_delta_class": {"type": "object"},
            "by_request_library_alignment_minimum_coverage_bucket": {
                "type": "object"
            },
            "n_requests_with_legacy_context_field_aliases": nonnegative_integer,
            "n_request_model_tier_haiku": nonnegative_integer,
            "n_request_model_tier_sonnet": nonnegative_integer,
            "n_request_model_tier_opus": nonnegative_integer,
            "by_request_model_tier": {"type": "object"},
            "n_requests_with_model_tier_decision_evidence": nonnegative_integer,
            "n_request_model_tier_decision_auto_haiku_bounded": nonnegative_integer,
            "n_request_model_tier_decision_auto_sonnet_triggered": nonnegative_integer,
            "n_request_model_tier_decision_operator_override": nonnegative_integer,
            "n_request_model_tier_decision_sonnet_triggers": nonnegative_integer,
            "n_request_model_tier_decision_evidence_invalid": nonnegative_integer,
            "by_request_model_tier_decision_basis": {"type": "object"},
            "n_requests_with_llm_generation_policy": nonnegative_integer,
            "n_request_llm_generation_policy_tier_model_matches": (
                nonnegative_integer
            ),
            "n_request_llm_generation_policy_codex_exclusions": (
                nonnegative_integer
            ),
            "n_request_llm_generation_policy_current_claude_tier_source": (
                nonnegative_integer
            ),
            "n_request_model_tier_mismatches": nonnegative_integer,
            "request_model_tier_mismatches": object_array,
            "n_generation_preflight_blocked": nonnegative_integer,
            "generation_preflight_errors": object_array,
            "n_request_source_grounding_rows": nonnegative_integer,
            "n_requests_with_source_grounding_obligation_inventory": (
                nonnegative_integer
            ),
            "n_requests_with_pending_source_grounding_obligation_inventory": (
                nonnegative_integer
            ),
            "n_request_source_grounding_unresolved_rows": nonnegative_integer,
            "n_request_residual_source_grounding_unresolved_rows": (
                nonnegative_integer
            ),
            "n_requests_with_quality_control_obligation_inventory": nonnegative_integer,
            "n_requests_with_pending_quality_control_obligation_inventory": (
                nonnegative_integer
            ),
            "n_request_quality_control_obligation_fields": nonnegative_integer,
            "n_request_quality_control_obligation_values": nonnegative_integer,
            "n_request_pending_quality_control_fields": nonnegative_integer,
            "n_request_pending_quality_control_values": nonnegative_integer,
            "n_request_discharged_quality_control_fields": nonnegative_integer,
            "n_request_discharged_quality_control_values": nonnegative_integer,
            "n_request_schema_valid": nonnegative_integer,
            "n_request_schema_invalid": nonnegative_integer,
            "n_raw_responses": nonnegative_integer,
            "n_generated_response_repair_attempts": nonnegative_integer,
            "n_generated_responses_repaired": nonnegative_integer,
            "n_generated_responses_model_tier_escalated": nonnegative_integer,
            "n_generated_responses_haiku_to_sonnet_escalated": (
                nonnegative_integer
            ),
            "n_repair_attempt_ledger_rows": nonnegative_integer,
            "n_requests_with_repair_attempt_ledger": nonnegative_integer,
            "n_repair_attempt_ledger_error_items": nonnegative_integer,
            "n_repair_attempt_ledger_model_tier_escalations": (
                nonnegative_integer
            ),
            "repair_attempt_ledger": object_array,
            "n_response_schema_valid": nonnegative_integer,
            "n_response_schema_invalid": nonnegative_integer,
            "n_rows": nonnegative_integer,
            "n_response_present": nonnegative_integer,
            "n_provider_failures": nonnegative_integer,
            "n_rows_with_generator_metadata": nonnegative_integer,
            "n_rows_with_model_tier_escalation": nonnegative_integer,
            "n_rows_with_generation_errors": nonnegative_integer,
            "n_response_contract_ok": nonnegative_integer,
            "n_accepted_route_plans": nonnegative_integer,
            "n_route_adoption_ready": nonnegative_integer,
            "n_route_adoption_pending_refinement": nonnegative_integer,
            "n_route_adoption_awaiting_llm_response": nonnegative_integer,
            "n_route_adoption_rejected": nonnegative_integer,
            "route_adoption_blocker_taxonomy_id": {
                "type": "string",
                "const": ROUTE_ADOPTION_BLOCKER_TAXONOMY_ID,
            },
            "route_adoption_blocker_values": string_array,
            "route_adoption_blocker_counts": {"type": "object"},
            "by_route_adoption_status": {"type": "object"},
            "by_route_adoption_blocker": {"type": "object"},
            "n_route_adoption_pending_formal_gap_boundary_blockers": (
                nonnegative_integer
            ),
            "n_route_adoption_pending_source_grounding_blockers": (
                nonnegative_integer
            ),
            "n_route_adoption_pending_quality_control_blockers": (
                nonnegative_integer
            ),
            "n_route_adoption_omitted_cost_hint_primitives": nonnegative_integer,
            "n_informal_knowledge_dag_nodes": nonnegative_integer,
            "n_formal_realization_dag_nodes": nonnegative_integer,
            "n_lean_realization_dag_nodes": nonnegative_integer,
            "n_route_alignment_edges": nonnegative_integer,
            "n_delta_action_witness_required_primitives": nonnegative_integer,
            "n_delta_action_witness_missing_primitives": nonnegative_integer,
            "n_rows_with_delta_action_witness_obligations": nonnegative_integer,
            "n_rows_with_complete_delta_action_witness": nonnegative_integer,
            "n_rows_with_context_packet_inventory": nonnegative_integer,
            "n_row_schema_valid": nonnegative_integer,
            "n_row_schema_invalid": nonnegative_integer,
            "request_schema": {
                "type": "object",
                "required": ["$id"],
                "properties": {"$id": {"const": LLM_ROUTE_PLANNER_REQUEST_SCHEMA_ID}},
            },
            "response_payload_schema": {
                "type": "object",
                "required": ["$id"],
                "properties": {
                    "$id": {"const": LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID}
                },
            },
            "response_schema": {
                "type": "object",
                "required": ["$id"],
                "properties": {"$id": {"const": LLM_ROUTE_PLANNER_RESPONSE_SCHEMA_ID}},
            },
            "row_schema": {
                "type": "object",
                "required": ["$id"],
                "properties": {"$id": {"const": LLM_ROUTE_PLANNER_ROW_SCHEMA_ID}},
            },
            "request_packets": object_array,
            "rows": object_array,
            "standalone_seed": {"type": "object"},
            "standalone_replay_gate": {
                "type": "object",
                "required": [
                    "gate_kind",
                    "gate_ok",
                    "gate_status",
                    "selected_route_adoptable_for_standalone_replay",
                    "n_route_candidates",
                    "n_adoptable_route_candidates",
                    "n_blocked_route_candidates",
                    "gate_blockers",
                    "proof_evidence_boundary",
                ],
                "properties": {
                    "gate_kind": {"const": STANDALONE_REPLAY_GATE_KIND},
                    "gate_ok": {"type": "boolean"},
                    "gate_status": {"type": "string", "minLength": 1},
                    "selected_route_adoptable_for_standalone_replay": {
                        "type": "boolean"
                    },
                    "selected_route_adoption_status": {"type": "string"},
                    "selected_route_adoption_blockers": string_array,
                    "n_route_candidates": nonnegative_integer,
                    "n_contract_valid_route_candidates": nonnegative_integer,
                    "n_ready_route_candidates": nonnegative_integer,
                    "n_adoptable_route_candidates": nonnegative_integer,
                    "n_blocked_route_candidates": nonnegative_integer,
                    "n_manifest_rows": nonnegative_integer,
                    "n_manifest_rows_response_contract_ok": nonnegative_integer,
                    "gate_blockers": string_array,
                    "proof_evidence_status": {"const": PROOF_EVIDENCE_STATUS},
                    "proof_evidence_boundary": {
                        "type": "string",
                        "pattern": "not theorem proof evidence",
                    },
                },
            },
            "standalone_replay_gate_ok": {"type": "boolean"},
            "n_standalone_replay_route_candidates": nonnegative_integer,
            "n_standalone_replay_adoptable_route_candidates": nonnegative_integer,
            "n_standalone_replay_blocked_route_candidates": nonnegative_integer,
            "standalone_replay_gate_blockers": string_array,
            "by_acceptance_status": {"type": "object"},
            "all_ok": {"type": "boolean"},
            "errors": string_array,
            "llm_route_planner_fingerprint": {"type": "string"},
            "proof_evidence_status": {
                "type": "string",
                "const": PROOF_EVIDENCE_STATUS,
            },
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
            "limitations": string_array,
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
            "model_tier_decision_evidence",
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
            "quality_control_obligations",
            "feedback_loop_summary",
            "context_packet_inventory",
            "raw_response_text",
            "generator_metadata",
            "provider_failure",
            "repair_attempts",
            "repair_error_history",
            "repair_attempt_ledger",
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
            "model_tier_decision_evidence": {"type": "object"},
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
            "quality_control_obligations": {"type": "object"},
            "feedback_loop_summary": {"type": "object"},
            "context_packet_inventory": {"type": "object"},
            "raw_response_text": {"type": "string"},
            "generator_metadata": {"type": "object"},
            "provider_failure": {"type": "boolean"},
            "repair_attempts": {"type": "integer", "minimum": 0},
            "repair_error_history": object_array,
            "repair_attempt_ledger": object_array,
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
                    "cost_hint_baseline_primitives",
                    "omitted_cost_hint_primitives",
                    "delta_primitives_with_route_alignment_edge",
                    "delta_primitives_missing_route_alignment_edge",
                    "introduced_primitives_with_route_alignment_edge",
                    "introduced_primitives_missing_route_alignment_edge",
                    "delta_action_witness_required_primitives",
                    "delta_action_witnessed_primitives",
                    "delta_action_witness_missing_primitives",
                    "delta_action_witness_complete",
                    "cost_hint_baseline_coverage_complete",
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
                    "cost_hint_baseline_primitives": witness_array,
                    "omitted_cost_hint_primitives": witness_array,
                    "delta_primitives_with_route_alignment_edge": witness_array,
                    "delta_primitives_missing_route_alignment_edge": witness_array,
                    "introduced_primitives_with_route_alignment_edge": witness_array,
                    "introduced_primitives_missing_route_alignment_edge": witness_array,
                    "delta_action_witness_required_primitives": witness_array,
                    "delta_action_witnessed_primitives": witness_array,
                    "delta_action_witness_missing_primitives": witness_array,
                    "delta_action_witness_complete": {"type": "boolean"},
                    "delta_action_witness_rows": object_array,
                    "missing_delta_action_witnesses": object_array,
                    "cost_hint_baseline_coverage_complete": {"type": "boolean"},
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
    trigger_field_properties = {
        blocker: {
            "type": "array",
            "items": {"type": "string"},
            "const": list(fields),
        }
        for blocker, fields in ROUTE_ADOPTION_BLOCKER_TRIGGER_FIELDS.items()
    }
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
            "blocker_trigger_fields",
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
            "blocker_trigger_fields": {
                "type": "object",
                "additionalProperties": False,
                "required": list(ROUTE_ADOPTION_BLOCKER_VALUES),
                "properties": trigger_field_properties,
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
        "blocker_trigger_fields": {
            blocker: list(fields)
            for blocker, fields in ROUTE_ADOPTION_BLOCKER_TRIGGER_FIELDS.items()
        },
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
    trigger_fields = payload.get("blocker_trigger_fields", {})
    if not isinstance(trigger_fields, Mapping):
        errors.append("blocker_trigger_fields must be object")
    else:
        trigger_keys = tuple(str(key) for key in trigger_fields.keys())
        if set(trigger_keys) != set(ROUTE_ADOPTION_BLOCKER_VALUES):
            errors.append("blocker_trigger_fields keys must match blocker_values")
        empty_trigger_fields = [
            key
            for key, values in trigger_fields.items()
            if not _str_tuple(values)
        ]
        if empty_trigger_fields:
            errors.append(
                "blocker_trigger_fields must list at least one trigger field for: "
                + ", ".join(sorted(str(key) for key in empty_trigger_fields))
            )
        mismatched_trigger_fields = [
            blocker
            for blocker, expected in ROUTE_ADOPTION_BLOCKER_TRIGGER_FIELDS.items()
            if _str_tuple(trigger_fields.get(blocker, [])) != tuple(expected)
        ]
        if mismatched_trigger_fields:
            errors.append(
                "blocker_trigger_fields values must match route adoption "
                "blocker trigger constants for: "
                + ", ".join(sorted(mismatched_trigger_fields))
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
    errors.extend(
        _model_tier_decision_evidence_errors(
            _dict_value(row, "model_tier_decision_evidence"),
            selected_model_tier=str(row.get("model_tier", "")),
            effective_model_tier=str(row.get("model_tier", "")),
            allow_repair_escalation=False,
        )
    )
    errors.extend(_llm_generation_policy_errors(row))
    errors.extend(_context_packet_inventory_errors(row))
    return sorted(set(errors))


def validate_llm_route_planner_manifest(
    manifest: Mapping[str, object],
    schema: Mapping[str, object] | None = None,
) -> list[str]:
    """Validate an LLM route-planner manifest artifact."""

    errors = _validate_with_schema(
        manifest,
        schema or llm_route_planner_manifest_json_schema(),
    )
    manifest_rows = _dict_tuple(manifest.get("rows", []))
    if int(manifest.get("n_request_packets", 0) or 0) != len(
        _dict_tuple(manifest.get("request_packets", []))
    ):
        errors.append("n_request_packets must match request_packets length")
    if int(manifest.get("n_rows", 0) or 0) != len(manifest_rows):
        errors.append("n_rows must match rows length")
    if int(manifest.get("n_row_schema_valid", 0) or 0) + int(
        manifest.get("n_row_schema_invalid", 0) or 0
    ) != int(manifest.get("n_rows", 0) or 0):
        errors.append("row schema valid/invalid counts must sum to n_rows")
    if int(manifest.get("n_request_schema_valid", 0) or 0) + int(
        manifest.get("n_request_schema_invalid", 0) or 0
    ) != int(manifest.get("n_request_packets", 0) or 0):
        errors.append(
            "request schema valid/invalid counts must sum to n_request_packets"
        )
    if (
        manifest.get("legacy_context_field_aliases")
        != LLM_ROUTE_PLANNER_LEGACY_CONTEXT_FIELD_ALIASES
    ):
        errors.append(
            "legacy_context_field_aliases must match planner legacy context aliases"
        )
    request_packets = _dict_tuple(manifest.get("request_packets", []))
    n_requests_with_context_aliases = sum(
        1
        for packet in request_packets
        if _dict_value(
            _dict_value(packet, "context_packet"),
            "legacy_context_field_aliases",
        )
        and _dict_value(
            _dict_value(packet, "context_packet"),
            "legacy_context_field_aliases",
        )
        == _legacy_context_field_aliases_for_target(
            packet.get("target_prover_family", "")
        )
    )
    if int(
        manifest.get("n_requests_with_legacy_context_field_aliases", 0) or 0
    ) != n_requests_with_context_aliases:
        errors.append(
            "n_requests_with_legacy_context_field_aliases must match request_packets"
        )
    n_requests_with_route_planning_brief = sum(
        1
        for packet in request_packets
        if _dict_value(
            _dict_value(packet, "context_packet"),
            "route_planning_brief",
        )
    )
    if int(
        manifest.get("n_requests_with_route_planning_brief", 0) or 0
    ) != n_requests_with_route_planning_brief:
        errors.append(
            "n_requests_with_route_planning_brief must match request_packets"
        )
    n_route_planning_focus_rows = sum(
        len(
            _dict_tuple(
                _dict_value(
                    _dict_value(packet, "context_packet"),
                    "route_planning_brief",
                ).get("planner_focus", [])
            )
        )
        for packet in request_packets
    )
    if int(
        manifest.get("n_request_route_planning_focus_rows", 0) or 0
    ) != n_route_planning_focus_rows:
        errors.append(
            "n_request_route_planning_focus_rows must match request_packets"
        )
    n_route_planning_evidence_gaps = sum(
        len(
            _dict_tuple(
                _dict_value(
                    _dict_value(packet, "context_packet"),
                    "route_planning_brief",
                ).get("evidence_gaps", [])
            )
        )
        for packet in request_packets
    )
    if int(
        manifest.get("n_request_route_planning_evidence_gaps", 0) or 0
    ) != n_route_planning_evidence_gaps:
        errors.append(
            "n_request_route_planning_evidence_gaps must match request_packets"
        )
    library_alignment_summaries = tuple(
        _request_library_alignment_summary(packet) for packet in request_packets
    )
    library_alignment_rows = tuple(
        row
        for summary in library_alignment_summaries
        for row in _dict_tuple(summary.get("primitive_alignment", []))
    )
    library_alignment_route_option_rows = tuple(
        row
        for summary in library_alignment_summaries
        for row in _dict_tuple(summary.get("route_option_alignment", []))
    )
    library_delta_class_counts = Counter(
        str(row.get("library_delta_class", "") or "unknown")
        for row in library_alignment_rows
    )
    library_minimum_bucket_counts = Counter(
        str(row.get("minimum_coverage_bucket", "") or "unknown")
        for row in library_alignment_rows
    )
    library_alignment_count_checks = (
        (
            "n_requests_with_library_alignment_summary",
            sum(1 for summary in library_alignment_summaries if summary),
        ),
        (
            "n_request_library_alignment_primitives",
            sum(
                int(summary.get("n_primitives", 0) or 0)
                for summary in library_alignment_summaries
            ),
        ),
        (
            "n_request_library_alignment_reuse_ready_primitives",
            library_delta_class_counts.get("reuse_ready", 0),
        ),
        (
            "n_request_library_alignment_wrapper_primitives",
            library_delta_class_counts.get("wrapper", 0),
        ),
        (
            "n_request_library_alignment_bridge_primitives",
            library_delta_class_counts.get("bridge", 0),
        ),
        (
            "n_request_library_alignment_source_port_primitives",
            library_delta_class_counts.get("source_port", 0),
        ),
        (
            "n_request_library_alignment_new_definition_primitives",
            library_delta_class_counts.get("new_definition", 0),
        ),
        (
            "n_request_library_alignment_new_theory_primitives",
            library_delta_class_counts.get("new_theory", 0),
        ),
        (
            "n_request_library_alignment_unknown_primitives",
            library_delta_class_counts.get("unknown", 0),
        ),
        (
            "n_request_library_alignment_bridge_or_harder_primitives",
            sum(
                int(summary.get("n_bridge_or_harder_primitives", 0) or 0)
                for summary in library_alignment_summaries
            ),
        ),
        (
            "n_request_library_alignment_target_compatible_reuse_declarations",
            sum(
                int(
                    summary.get(
                        "n_target_compatible_reuse_declarations",
                        0,
                    )
                    or 0
                )
                for summary in library_alignment_summaries
            ),
        ),
        (
            "n_request_library_alignment_route_options",
            len(library_alignment_route_option_rows),
        ),
        (
            "n_request_library_alignment_route_option_primitives",
            sum(
                int(row.get("n_selected_primitives", 0) or 0)
                for row in library_alignment_route_option_rows
            ),
        ),
        (
            "n_request_library_alignment_route_option_bridge_or_harder_primitives",
            sum(
                int(row.get("n_bridge_or_harder_primitives", 0) or 0)
                for row in library_alignment_route_option_rows
            ),
        ),
        (
            "n_request_library_alignment_route_option_target_compatible_reuse_declarations",
            sum(
                int(row.get("n_target_compatible_reuse_declarations", 0) or 0)
                for row in library_alignment_route_option_rows
            ),
        ),
    )
    for field_name, expected_value in library_alignment_count_checks:
        if int(manifest.get(field_name, 0) or 0) != int(expected_value):
            errors.append(f"{field_name} must match request_packets")
    expected_route_option_cost = sum(
        float(row.get("minimum_route_base_cost", 0) or 0)
        for row in library_alignment_route_option_rows
        if _is_nonnegative_number(row.get("minimum_route_base_cost"))
    )
    if abs(
        float(
            manifest.get(
                "total_request_library_alignment_route_option_minimum_base_cost",
                0,
            )
            or 0
        )
        - expected_route_option_cost
    ) > 1e-9:
        errors.append(
            "total_request_library_alignment_route_option_minimum_base_cost "
            "must match request_packets"
        )
    if dict(
        manifest.get("by_request_library_alignment_delta_class", {}) or {}
    ) != dict(sorted(library_delta_class_counts.items())):
        errors.append(
            "by_request_library_alignment_delta_class must match request_packets"
        )
    if dict(
        manifest.get("by_request_library_alignment_minimum_coverage_bucket", {})
        or {}
    ) != dict(sorted(library_minimum_bucket_counts.items())):
        errors.append(
            "by_request_library_alignment_minimum_coverage_bucket must match "
            "request_packets"
        )
    decision_evidence_rows = tuple(
        _dict_value(packet, "model_tier_decision_evidence")
        for packet in request_packets
    )
    decision_basis_counts = Counter(
        str(row.get("decision_basis", "") or "missing")
        for row in decision_evidence_rows
    )
    if int(
        manifest.get("n_requests_with_model_tier_decision_evidence", 0) or 0
    ) != sum(1 for row in decision_evidence_rows if row):
        errors.append(
            "n_requests_with_model_tier_decision_evidence must match request_packets"
        )
    if int(
        manifest.get("n_request_model_tier_decision_auto_haiku_bounded", 0) or 0
    ) != decision_basis_counts.get("auto_haiku_bounded_route", 0):
        errors.append(
            "n_request_model_tier_decision_auto_haiku_bounded must match request_packets"
        )
    if int(
        manifest.get("n_request_model_tier_decision_auto_sonnet_triggered", 0) or 0
    ) != decision_basis_counts.get("auto_sonnet_triggers", 0):
        errors.append(
            "n_request_model_tier_decision_auto_sonnet_triggered must match request_packets"
        )
    if int(
        manifest.get("n_request_model_tier_decision_operator_override", 0) or 0
    ) != decision_basis_counts.get("operator_override", 0):
        errors.append(
            "n_request_model_tier_decision_operator_override must match request_packets"
        )
    if int(
        manifest.get("n_request_model_tier_decision_sonnet_triggers", 0) or 0
    ) != sum(
        len(_str_tuple(row.get("sonnet_triggers", [])))
        for row in decision_evidence_rows
    ):
        errors.append(
            "n_request_model_tier_decision_sonnet_triggers must match request_packets"
        )
    invalid_decision_evidence = [
        row
        for packet, row in zip(request_packets, decision_evidence_rows)
        if _model_tier_decision_evidence_errors(
            row,
            selected_model_tier=str(packet.get("model_tier", "")),
            effective_model_tier=str(packet.get("model_tier", "")),
            allow_repair_escalation=False,
        )
    ]
    if int(
        manifest.get("n_request_model_tier_decision_evidence_invalid", 0) or 0
    ) != len(invalid_decision_evidence):
        errors.append(
            "n_request_model_tier_decision_evidence_invalid must match request_packets"
        )
    if dict(manifest.get("by_request_model_tier_decision_basis", {}) or {}) != dict(
        sorted(decision_basis_counts.items())
    ):
        errors.append(
            "by_request_model_tier_decision_basis must match request_packets"
        )
    if int(manifest.get("n_requests_with_llm_generation_policy", 0) or 0) != sum(
        1 for packet in request_packets if packet.get("llm_generation_policy")
    ):
        errors.append(
            "n_requests_with_llm_generation_policy must match request_packets"
        )
    generation_policy_tier_matches = sum(
        1
        for packet in request_packets
        if _dict_value(packet, "llm_generation_policy").get("selected_model_tier")
        == packet.get("model_tier")
        and _dict_value(packet, "llm_generation_policy").get("resolved_model")
        == packet.get("model")
    )
    if int(
        manifest.get("n_request_llm_generation_policy_tier_model_matches", 0) or 0
    ) != generation_policy_tier_matches:
        errors.append(
            "n_request_llm_generation_policy_tier_model_matches must match request_packets"
        )
    generation_policy_codex_exclusions = sum(
        1
        for packet in request_packets
        if {"codex", "codex_exec"}.issubset(
            set(
                _str_tuple(
                    _dict_value(packet, "llm_generation_policy").get(
                        "prohibited_generator_providers",
                        [],
                    )
                )
            )
        )
    )
    if int(
        manifest.get("n_request_llm_generation_policy_codex_exclusions", 0) or 0
    ) != generation_policy_codex_exclusions:
        errors.append(
            "n_request_llm_generation_policy_codex_exclusions must match request_packets"
        )
    generation_policy_current_claude_tier_source = sum(
        1
        for packet in request_packets
        if not _llm_generation_policy_claude_model_source_errors(
            _dict_value(packet, "llm_generation_policy")
        )
    )
    if int(
        manifest.get(
            "n_request_llm_generation_policy_current_claude_tier_source",
            0,
        )
        or 0
    ) != generation_policy_current_claude_tier_source:
        errors.append(
            "n_request_llm_generation_policy_current_claude_tier_source must match request_packets"
        )
    repair_attempt_ledger = _dict_tuple(manifest.get("repair_attempt_ledger", []))
    row_repair_attempt_ledger = tuple(
        ledger_row
        for row in manifest_rows
        for ledger_row in _dict_tuple(row.get("repair_attempt_ledger", []))
    )
    if int(manifest.get("n_repair_attempt_ledger_rows", 0) or 0) != len(
        repair_attempt_ledger
    ):
        errors.append("n_repair_attempt_ledger_rows must match repair_attempt_ledger")
    if tuple(repair_attempt_ledger) != row_repair_attempt_ledger:
        errors.append("repair_attempt_ledger must match row repair_attempt_ledger")
    if int(
        manifest.get("n_requests_with_repair_attempt_ledger", 0) or 0
    ) != len(
        {
            str(row.get("request_id", ""))
            for row in repair_attempt_ledger
            if str(row.get("request_id", "")).strip()
        }
    ):
        errors.append(
            "n_requests_with_repair_attempt_ledger must match repair_attempt_ledger"
        )
    if int(
        manifest.get("n_repair_attempt_ledger_error_items", 0) or 0
    ) != sum(int(row.get("error_count", 0) or 0) for row in repair_attempt_ledger):
        errors.append(
            "n_repair_attempt_ledger_error_items must match repair_attempt_ledger"
        )
    expected_standalone_replay_gate = _standalone_replay_gate(
        manifest_rows,
        _dict_value(manifest, "standalone_seed"),
    )
    observed_standalone_replay_gate = _dict_value(
        manifest,
        "standalone_replay_gate",
    )
    if observed_standalone_replay_gate != expected_standalone_replay_gate:
        errors.append("standalone_replay_gate must match rows and standalone_seed")
    if bool(manifest.get("standalone_replay_gate_ok", False)) != bool(
        expected_standalone_replay_gate.get("gate_ok", False)
    ):
        errors.append("standalone_replay_gate_ok must match standalone_replay_gate")
    if int(
        manifest.get("n_standalone_replay_route_candidates", 0) or 0
    ) != int(expected_standalone_replay_gate.get("n_route_candidates", 0) or 0):
        errors.append(
            "n_standalone_replay_route_candidates must match standalone_replay_gate"
        )
    if int(
        manifest.get("n_standalone_replay_adoptable_route_candidates", 0) or 0
    ) != int(
        expected_standalone_replay_gate.get("n_adoptable_route_candidates", 0)
        or 0
    ):
        errors.append(
            "n_standalone_replay_adoptable_route_candidates must match standalone_replay_gate"
        )
    if int(
        manifest.get("n_standalone_replay_blocked_route_candidates", 0) or 0
    ) != int(
        expected_standalone_replay_gate.get("n_blocked_route_candidates", 0) or 0
    ):
        errors.append(
            "n_standalone_replay_blocked_route_candidates must match standalone_replay_gate"
        )
    if list(_str_tuple(manifest.get("standalone_replay_gate_blockers", []))) != (
        list(_str_tuple(expected_standalone_replay_gate.get("gate_blockers", [])))
    ):
        errors.append(
            "standalone_replay_gate_blockers must match standalone_replay_gate"
        )
    embedded_schema_ids = {
        "request_schema": LLM_ROUTE_PLANNER_REQUEST_SCHEMA_ID,
        "response_payload_schema": LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID,
        "response_schema": LLM_ROUTE_PLANNER_RESPONSE_SCHEMA_ID,
        "row_schema": LLM_ROUTE_PLANNER_ROW_SCHEMA_ID,
    }
    for field_name, expected_schema_id in embedded_schema_ids.items():
        embedded_schema = manifest.get(field_name, {})
        if not isinstance(embedded_schema, Mapping):
            errors.append(f"{field_name} must be object")
            continue
        observed_schema_id = str(embedded_schema.get("$id", "") or "")
        if observed_schema_id != expected_schema_id:
            errors.append(f"{field_name}.$id must equal {expected_schema_id}")
    if (
        str(manifest.get("route_adoption_blocker_taxonomy_id", "") or "")
        != ROUTE_ADOPTION_BLOCKER_TAXONOMY_ID
    ):
        errors.append(
            "route_adoption_blocker_taxonomy_id must equal "
            + ROUTE_ADOPTION_BLOCKER_TAXONOMY_ID
        )
    if _str_tuple(manifest.get("route_adoption_blocker_values", [])) != (
        ROUTE_ADOPTION_BLOCKER_VALUES
    ):
        errors.append(
            "route_adoption_blocker_values must match route adoption blocker constants"
        )
    return sorted(set(errors))


def _route_adoption_blocker_counts(
    rows: tuple[FormalizationGapPlannerLLMRoutePlannerRow, ...],
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.route_adoption_blockers)
    return dict(sorted(counts.items()))


def _route_adoption_blocker_summary(
    rows: tuple[FormalizationGapPlannerLLMRoutePlannerRow, ...],
) -> dict[str, dict[str, object]]:
    counts = _route_adoption_blocker_counts(rows)
    summaries: dict[str, dict[str, object]] = {}
    for blocker in sorted(counts):
        blocker_rows = [
            row for row in rows if blocker in row.route_adoption_blockers
        ]
        summaries[blocker] = {
            "n_rows": len(blocker_rows),
            "n_blocker_occurrences": counts[blocker],
            "by_route_adoption_status": dict(
                sorted(
                    Counter(
                        row.route_adoption_status for row in blocker_rows
                    ).items()
                )
            ),
            "by_acceptance_status": dict(
                sorted(Counter(row.acceptance_status for row in blocker_rows).items())
            ),
            "n_response_present": sum(
                1 for row in blocker_rows if row.response_present
            ),
            "n_response_contract_ok": sum(
                1 for row in blocker_rows if row.response_contract_ok
            ),
            "n_provider_failures": sum(
                1 for row in blocker_rows if row.provider_failure
            ),
        }
    return summaries


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
    errors.extend(_kernel_proof_claim_errors(row, location="llm_route_planner_response"))
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
    errors.extend(_kernel_proof_claim_errors(payload, location="response_payload"))
    errors.extend(_response_payload_realization_field_contract_errors(payload))
    errors.extend(_response_payload_lean_legacy_declaration_field_errors(payload))
    errors.extend(_response_payload_target_prover_internal_consistency_errors(payload))
    return sorted(set(errors))


def validate_llm_route_planner_response_payload_validation_manifest(
    manifest: Mapping[str, object],
    schema: Mapping[str, object] | None = None,
) -> list[str]:
    """Validate the reusable response-payload validation manifest contract."""

    errors = _validate_with_schema(
        manifest,
        schema or llm_route_planner_response_payload_validation_manifest_json_schema(),
    )
    rows = _dict_tuple(manifest.get("rows", []))
    valid_rows = sum(1 for row in rows if bool(row.get("ok", False)))
    invalid_rows = len(rows) - valid_rows
    schema_errors = sum(int(row.get("n_schema_errors", 0) or 0) for row in rows)
    request_context_errors = sum(
        int(row.get("n_request_context_errors", 0) or 0) for row in rows
    )
    request_bound_rows = tuple(
        row
        for row in rows
        if str(row.get("request_context_validation_mode", ""))
        == "request_bound"
    )
    request_bound_rows_with_inventory = tuple(
        row
        for row in request_bound_rows
        if bool(row.get("request_context_inventory_present", False))
    )
    request_bound_inventory_total_rows = sum(
        int(row.get("request_context_inventory_total_rows", 0) or 0)
        for row in request_bound_rows
    )
    payload_target_counts = _value_counts(
        [
            _target_prover_key(row.get("payload_target_prover_key", ""))
            for row in rows
            if str(row.get("payload_target_prover_key", "") or "").strip()
        ]
    )
    request_context_target_counts = _value_counts(
        [
            _target_prover_key(row.get("request_context_target_prover_key", ""))
            for row in rows
            if str(row.get("request_context_target_prover_key", "") or "").strip()
        ]
    )
    payloads_with_declared_target = sum(
        1
        for row in rows
        if str(row.get("payload_target_prover_family", "") or "").strip()
    )
    target_mismatch_rows = tuple(
        row
        for row in request_bound_rows
        if not bool(row.get("target_prover_family_consistent", False))
    )
    if int(manifest.get("n_payloads", 0) or 0) != len(rows):
        errors.append("n_payloads must match rows length")
    if int(manifest.get("n_valid_payloads", 0) or 0) != valid_rows:
        errors.append("n_valid_payloads must match rows with ok=true")
    if int(manifest.get("n_invalid_payloads", 0) or 0) != invalid_rows:
        errors.append("n_invalid_payloads must match rows with ok=false")
    if int(manifest.get("n_schema_errors", 0) or 0) != schema_errors:
        errors.append("n_schema_errors must match row n_schema_errors sum")
    if int(manifest.get("n_request_context_errors", 0) or 0) != (
        request_context_errors
    ):
        errors.append(
            "n_request_context_errors must match row n_request_context_errors sum"
        )
    if int(manifest.get("n_request_bound_payloads", 0) or 0) != len(
        request_bound_rows
    ):
        errors.append(
            "n_request_bound_payloads must match request_bound validation rows"
        )
    if int(
        manifest.get("n_request_bound_payloads_with_context_packet_inventory", 0)
        or 0
    ) != len(request_bound_rows_with_inventory):
        errors.append(
            "n_request_bound_payloads_with_context_packet_inventory must match "
            "request_bound rows with context_packet_inventory"
        )
    if int(
        manifest.get("n_request_bound_payload_context_inventory_total_rows", 0)
        or 0
    ) != request_bound_inventory_total_rows:
        errors.append(
            "n_request_bound_payload_context_inventory_total_rows must match "
            "request_bound row inventory total"
        )
    if int(
        manifest.get("n_payloads_with_declared_target_prover_family", 0) or 0
    ) != payloads_with_declared_target:
        errors.append(
            "n_payloads_with_declared_target_prover_family must match rows "
            "with payload_target_prover_family"
        )
    if int(
        manifest.get(
            "n_request_bound_payloads_with_target_prover_family_mismatch",
            0,
        )
        or 0
    ) != len(target_mismatch_rows):
        errors.append(
            "n_request_bound_payloads_with_target_prover_family_mismatch must "
            "match request-bound rows with inconsistent target prover family"
        )
    if dict(manifest.get("by_payload_target_prover_family", {}) or {}) != (
        payload_target_counts
    ):
        errors.append(
            "by_payload_target_prover_family must match validation row target counts"
        )
    if dict(
        manifest.get("by_request_context_target_prover_family", {}) or {}
    ) != request_context_target_counts:
        errors.append(
            "by_request_context_target_prover_family must match validation row request-context target counts"
        )
    embedded_row_schema = manifest.get("response_payload_validation_row_schema", {})
    for index, row in enumerate(rows):
        row_errors = validate_llm_route_planner_response_payload_validation_row(
            row,
            embedded_row_schema if isinstance(embedded_row_schema, Mapping) else None,
        )
        errors.extend(f"rows[{index}].{error}" for error in row_errors)
    embedded_schema_ids = {
        "response_payload_schema": LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID,
        "response_payload_validation_manifest_schema": (
            LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID
        ),
        "response_payload_validation_row_schema": (
            LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID
        ),
    }
    for field_name, expected_schema_id in embedded_schema_ids.items():
        embedded_schema = manifest.get(field_name, {})
        if not isinstance(embedded_schema, Mapping):
            errors.append(f"{field_name} must be object")
            continue
        observed_schema_id = str(embedded_schema.get("$id", "") or "")
        if observed_schema_id != expected_schema_id:
            errors.append(f"{field_name}.$id must equal {expected_schema_id}")
    if bool(manifest.get("all_ok", False)):
        if not rows:
            errors.append("all_ok validation manifest must include at least one row")
        if not all(bool(row.get("ok", False)) for row in rows):
            errors.append("all_ok validation manifest cannot contain failed rows")
        if _str_tuple(manifest.get("errors", [])):
            errors.append("all_ok validation manifest must not carry errors")
    return sorted(set(errors))


def validate_llm_route_planner_response_payload_validation_row(
    row: Mapping[str, object],
    schema: Mapping[str, object] | None = None,
) -> list[str]:
    """Validate a response-payload validation JSONL row."""

    errors = _validate_with_schema(
        row,
        schema or llm_route_planner_response_payload_validation_row_json_schema(),
    )
    count_fields = (
        "payload_index",
        "request_context_inventory_total_rows",
        "n_schema_errors",
        "n_request_context_errors",
        "n_errors",
    )
    count_values: dict[str, int] = {}
    for field_name in count_fields:
        value = row.get(field_name, 0)
        if not isinstance(value, int) or isinstance(value, bool):
            count_values[field_name] = 0
            continue
        count_values[field_name] = value
        if value < 0:
            errors.append(f"{field_name} must be nonnegative")

    reported_errors = _str_tuple(row.get("errors", []))
    n_errors = count_values["n_errors"]
    n_schema_errors = count_values["n_schema_errors"]
    n_request_context_errors = count_values["n_request_context_errors"]
    if n_errors != len(reported_errors):
        errors.append("n_errors must match errors length")
    if n_errors > n_schema_errors + n_request_context_errors:
        errors.append(
            "n_errors cannot exceed n_schema_errors + n_request_context_errors"
        )
    if bool(row.get("ok", False)):
        if n_errors != 0 or reported_errors:
            errors.append("ok validation row must have zero errors")
    elif n_errors <= 0:
        errors.append("failed validation row must carry n_errors")
    payload_target_key = _target_prover_key(
        row.get("payload_target_prover_key", "")
        or row.get("payload_target_prover_family", "")
    )
    request_target_key = _target_prover_key(
        row.get("request_context_target_prover_key", "")
        or row.get("request_context_target_prover_family", "")
    )
    expected_target_consistent = not (
        payload_target_key
        and request_target_key
        and payload_target_key != request_target_key
    )
    if bool(row.get("target_prover_family_consistent", False)) != (
        expected_target_consistent
    ):
        errors.append(
            "target_prover_family_consistent must match normalized payload and request target prover keys"
        )

    return sorted(set(errors))


def validate_llm_route_planner_row(
    row: Mapping[str, object],
    schema: Mapping[str, object] | None = None,
) -> list[str]:
    errors = _validate_with_schema(row, schema or llm_route_planner_row_json_schema())
    model_tier_mismatch = _row_model_tier_mismatch_error(row)
    if model_tier_mismatch:
        errors.append(model_tier_mismatch)
    repair_attempts = _nonnegative_int(row.get("repair_attempts", 0))
    repair_error_history = _dict_tuple(row.get("repair_error_history", []))
    history_attempts = tuple(
        _nonnegative_int(item.get("attempt", index), default=index)
        for index, item in enumerate(repair_error_history)
    )
    if history_attempts and max(history_attempts) > repair_attempts:
        errors.append(
            "repair_error_history attempt cannot exceed repair_attempts"
        )
    repair_attempt_ledger = _dict_tuple(row.get("repair_attempt_ledger", []))
    if len(repair_attempt_ledger) != len(repair_error_history):
        errors.append(
            "repair_attempt_ledger length must match repair_error_history length"
        )
    for index, (history_item, ledger_item) in enumerate(
        zip(repair_error_history, repair_attempt_ledger)
    ):
        history_attempt = _nonnegative_int(
            history_item.get("attempt", index),
            default=index,
        )
        ledger_attempt = _nonnegative_int(
            ledger_item.get("failed_attempt_index", -1),
            default=-1,
        )
        if ledger_attempt != history_attempt:
            errors.append(
                f"repair_attempt_ledger[{index}].failed_attempt_index must match repair_error_history"
            )
        history_errors = _str_tuple(history_item.get("errors", []))
        ledger_errors = _str_tuple(ledger_item.get("errors", []))
        if ledger_errors != history_errors:
            errors.append(
                f"repair_attempt_ledger[{index}].errors must match repair_error_history"
            )
        if int(ledger_item.get("error_count", 0) or 0) != len(ledger_errors):
            errors.append(
                f"repair_attempt_ledger[{index}].error_count must match errors"
            )
        history_categories = _str_tuple(
            history_item.get("repair_guidance_categories", [])
        )
        ledger_categories = _str_tuple(
            ledger_item.get("repair_guidance_categories", [])
        )
        if ledger_categories != history_categories:
            errors.append(
                f"repair_attempt_ledger[{index}].repair_guidance_categories must match repair_error_history"
            )
        if str(ledger_item.get("repair_guidance_fingerprint", "")) != str(
            history_item.get("repair_guidance_fingerprint", "")
        ):
            errors.append(
                f"repair_attempt_ledger[{index}].repair_guidance_fingerprint must match repair_error_history"
            )
        if str(ledger_item.get("ledger_kind", "")) != REPAIR_ATTEMPT_LEDGER_KIND:
            errors.append(
                f"repair_attempt_ledger[{index}].ledger_kind must equal {REPAIR_ATTEMPT_LEDGER_KIND}"
            )
    if row.get("response_contract_ok") and _str_tuple(row.get("generation_errors", [])):
        errors.append("accepted response cannot retain generation_errors")
    if row.get("response_present") and not row.get("response_contract_ok"):
        if not str(row.get("acceptance_status", "")).startswith("REJECTED_"):
            errors.append("present non-contract response must be rejected")
    if row.get("response_contract_ok") and not row.get("standalone_route"):
        errors.append("accepted response must include standalone_route")
    generator_metadata = _dict_value(row, "generator_metadata")
    errors.extend(
        _model_tier_decision_evidence_errors(
            _dict_value(row, "model_tier_decision_evidence"),
            selected_model_tier=str(row.get("model_tier", "")),
            effective_model_tier=str(row.get("model_tier", "")),
            allow_repair_escalation=True,
        )
    )
    if generator_metadata.get("model_tier_escalated"):
        requested_tier = str(
            generator_metadata.get("requested_model_tier", "")
        ).strip().lower()
        effective_tier = str(
            generator_metadata.get("effective_model_tier", "")
        ).strip().lower()
        if str(row.get("provider_name", "")).strip().lower() != "anthropic":
            errors.append("model_tier_escalated is allowed only for anthropic rows")
        if requested_tier != "haiku" or effective_tier != "sonnet":
            errors.append("model_tier_escalated must be haiku-to-sonnet")
        if str(row.get("model_tier", "")).strip().lower() != effective_tier:
            errors.append("model_tier must match generator_metadata.effective_model_tier")
    inventory = _dict_value(row, "context_packet_inventory")
    if inventory.get("inventory_kind") != CONTEXT_PACKET_INVENTORY_KIND:
        errors.append(
            "context_packet_inventory.inventory_kind must equal "
            + CONTEXT_PACKET_INVENTORY_KIND
        )
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
    residual_goals = _residual_goals_for_route(
        route_match_ids,
        context_payloads,
        route=route,
    )
    context_packet = {
        "standalone_input_component": str(input_payload.get("component_name", "")),
        "route_id": route_id,
        "display_name": display_name,
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
        "route_replan_handoff_rows": _rows_for_route(
            context_payloads.get("route_replan_handoff", {}),
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
        "legacy_context_field_aliases": dict(
            _legacy_context_field_aliases_for_target(target_prover_family)
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
    context_packet["minimal_delta_cost_hints"] = _minimal_delta_cost_hints(
        route,
        context_packet,
        target_prover_family=target_prover_family,
    )
    context_packet["library_alignment_summary"] = _library_alignment_summary(
        context_packet,
        route_id=route_id,
        display_name=display_name,
        target_prover_family=target_prover_family,
        library_snapshot_ref=library_snapshot_ref,
    )
    context_packet["source_grounding_obligations"] = (
        _source_grounding_obligation_summary(context_packet)
    )
    context_packet["feedback_loop_summary"] = _feedback_loop_summary(
        context_packet,
        residual_goals=residual_goals,
    )
    context_packet["route_planning_brief"] = _route_planning_brief(
        route_id=route_id,
        display_name=display_name,
        route=route,
        context_packet=context_packet,
        residual_goals=residual_goals,
        target_prover_family=target_prover_family,
        library_snapshot_ref=library_snapshot_ref,
    )
    context_packet["context_packet_inventory"] = _context_packet_inventory(
        context_packet,
        residual_goals=residual_goals,
    )
    (
        selected_model_tier,
        model_selection_rationale,
        model_tier_decision_evidence,
    ) = (
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
    required_output_contract = _output_contract_for_target_prover(
        target_prover_family
    )
    request_id = "formalization_gap_planner_llm_route_request:" + stable_hash(
        [route_id, display_name, target_prover_family, library_snapshot_ref, context_packet]
    )[:20]
    prompt_messages = {
        "system": SYSTEM_PROMPT,
        "user": _user_prompt(
            target_route=route,
            context_packet=context_packet,
            required_output_contract=required_output_contract,
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
        "model_tier_decision_evidence": model_tier_decision_evidence,
        "llm_generation_policy": _llm_generation_policy_snapshot(
            provider_name=provider_name,
            resolved_model=resolved_model,
            selected_model_tier=selected_model_tier,
            requested_model_tier=model_tier,
            model_selection_rationale=model_selection_rationale,
        ),
        "target_prover_family": target_prover_family,
        "library_snapshot_ref": library_snapshot_ref,
        "target_route": dict(route),
        "context_packet": context_packet,
        "residual_goals": residual_goals,
        "minimal_delta_cost_policy": MINIMAL_DELTA_COST_POLICY,
        "required_output_contract": required_output_contract,
        "prompt_messages": prompt_messages,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "prompt_fingerprint": stable_hash(prompt_messages),
    }


def _library_alignment_summary(
    context_packet: Mapping[str, Any],
    *,
    route_id: str,
    display_name: str,
    target_prover_family: str,
    library_snapshot_ref: str,
) -> dict[str, object]:
    cost_hints = _dict_value(context_packet, "minimal_delta_cost_hints")
    primitive_rows: list[dict[str, object]] = []
    for hint in _dict_tuple(cost_hints.get("primitive_cost_hints", [])):
        primitive = _primitive_key(hint.get("primitive", ""))
        if not primitive:
            continue
        bucket = _primitive_key(hint.get("minimum_coverage_bucket", ""))
        if not bucket:
            bucket = "unknown"
        delta_class = _library_delta_class_for_bucket(bucket)
        declaration_rows = _target_compatible_formal_declaration_rows(
            _dict_tuple(hint.get("candidate_declaration_rows", [])),
            target_prover_family=target_prover_family,
        )
        declarations = [
            str(row.get("declaration", ""))
            for row in declaration_rows
            if str(row.get("declaration", "")).strip()
        ]
        primitive_rows.append(
            {
                "primitive": primitive,
                "minimum_coverage_bucket": bucket,
                "library_delta_class": delta_class,
                "minimum_base_cost": hint.get("minimum_base_cost", 20),
                "minimum_cost_source": str(hint.get("minimum_cost_source", "")),
                "minimum_cost_marker": str(hint.get("minimum_cost_marker", "")),
                "evidence_sources": list(_str_tuple(hint.get("evidence_sources", []))),
                "has_target_compatible_declaration": bool(declarations),
                "target_compatible_declarations": declarations,
                "target_compatible_declaration_count": len(declarations),
                "candidate_declaration_row_count": len(
                    _dict_tuple(hint.get("candidate_declaration_rows", []))
                ),
            }
        )
    by_class = _value_counts(
        [
            str(row.get("library_delta_class", "unknown"))
            for row in primitive_rows
        ]
    )
    by_bucket = _value_counts(
        [
            str(row.get("minimum_coverage_bucket", "unknown"))
            for row in primitive_rows
        ]
    )
    primitive_rows_by_name = {
        str(row.get("primitive", "")): row for row in primitive_rows
    }
    route_option_rows: list[dict[str, object]] = []
    for hint in _dict_tuple(cost_hints.get("route_option_hints", [])):
        route_option_id = str(hint.get("route_option_id", "")).strip()
        if not route_option_id:
            continue
        selected_primitives = [
            _primitive_key(primitive)
            for primitive in _str_tuple(hint.get("selected_primitives", []))
            if _primitive_key(primitive)
        ]
        selected_rows = [
            primitive_rows_by_name[primitive]
            for primitive in selected_primitives
            if primitive in primitive_rows_by_name
        ]
        selected_class_counts = _value_counts(
            [
                str(row.get("library_delta_class", "unknown"))
                for row in selected_rows
            ]
        )
        selected_bucket_counts = _value_counts(
            [
                str(row.get("minimum_coverage_bucket", "unknown"))
                for row in selected_rows
            ]
        )
        route_option_rows.append(
            {
                "route_option_id": route_option_id,
                "option_kind": str(hint.get("option_kind", "")),
                "selected_primitives": selected_primitives,
                "n_selected_primitives": len(selected_primitives),
                "minimum_route_base_cost": hint.get("minimum_route_base_cost", 0),
                "cost_policy_id": str(
                    hint.get("cost_policy_id", MINIMAL_DELTA_COST_POLICY_ID)
                ),
                "cost_rationale": str(hint.get("cost_rationale", "")),
                "n_bridge_or_harder_primitives": sum(
                    selected_class_counts.get(delta_class, 0)
                    for delta_class in (
                        "bridge",
                        "source_port",
                        "new_definition",
                        "new_theory",
                        "unknown",
                    )
                ),
                "n_target_compatible_reuse_declarations": sum(
                    int(row.get("target_compatible_declaration_count", 0) or 0)
                    for row in selected_rows
                ),
                "by_library_delta_class": dict(sorted(selected_class_counts.items())),
                "by_minimum_coverage_bucket": dict(
                    sorted(selected_bucket_counts.items())
                ),
            }
        )
    return {
        "schema_version": FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SCHEMA_VERSION,
        "schema_id": LLM_ROUTE_PLANNER_LIBRARY_ALIGNMENT_SUMMARY_SCHEMA_ID,
        "summary_kind": LIBRARY_ALIGNMENT_SUMMARY_KIND,
        "route_id": route_id,
        "display_name": display_name,
        "target_prover_family": target_prover_family,
        "library_snapshot_ref": library_snapshot_ref,
        "cost_policy_id": MINIMAL_DELTA_COST_POLICY_ID,
        "n_primitives": len(primitive_rows),
        "n_reuse_ready_primitives": by_class.get("reuse_ready", 0),
        "n_wrapper_primitives": by_class.get("wrapper", 0),
        "n_bridge_primitives": by_class.get("bridge", 0),
        "n_source_port_primitives": by_class.get("source_port", 0),
        "n_new_definition_primitives": by_class.get("new_definition", 0),
        "n_new_theory_primitives": by_class.get("new_theory", 0),
        "n_unknown_primitives": by_class.get("unknown", 0),
        "n_bridge_or_harder_primitives": sum(
            by_class.get(delta_class, 0)
            for delta_class in (
                "bridge",
                "source_port",
                "new_definition",
                "new_theory",
                "unknown",
            )
        ),
        "n_target_compatible_reuse_declarations": sum(
            int(row.get("target_compatible_declaration_count", 0) or 0)
            for row in primitive_rows
        ),
        "n_route_options": len(route_option_rows),
        "by_library_delta_class": dict(sorted(by_class.items())),
        "by_minimum_coverage_bucket": dict(sorted(by_bucket.items())),
        "primitive_alignment": primitive_rows,
        "route_option_alignment": route_option_rows,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _library_delta_class_for_bucket(bucket: str) -> str:
    normalized = _coverage_marker_policy_bucket(_primitive_key(bucket)) or _primitive_key(
        bucket
    )
    if normalized in {
        "already_exists",
        "exact_exists",
        "different_formulation",
        "near_exists",
    }:
        return "reuse_ready"
    if normalized in {"wrapper", "wrapper_needed"}:
        return "wrapper"
    if normalized in {"bridge", "bridge_needed"}:
        return "bridge"
    if normalized in {"source_port", "source_port_needed"}:
        return "source_port"
    if normalized in {"new_definition", "new_definition_needed"}:
        return "new_definition"
    if normalized in {"new_theory", "new_theory_needed", "first_principles"}:
        return "new_theory"
    return "unknown"


def _route_planning_brief(
    *,
    route_id: str,
    display_name: str,
    route: Mapping[str, Any],
    context_packet: Mapping[str, Any],
    residual_goals: tuple[str, ...],
    target_prover_family: str,
    library_snapshot_ref: str,
) -> dict[str, object]:
    source_refs = _str_tuple(context_packet.get("available_source_refs", []))
    source_snippets = _dict_tuple(context_packet.get("available_source_snippets", []))
    formal_declaration_rows = _dict_tuple(
        context_packet.get("available_formal_declaration_rows", [])
    )
    cost_hints = _dict_value(context_packet, "minimal_delta_cost_hints")
    alignment_summary = _dict_value(context_packet, "library_alignment_summary")
    primitive_cost_hints = _dict_tuple(cost_hints.get("primitive_cost_hints", []))
    route_option_hints = _dict_tuple(cost_hints.get("route_option_hints", []))
    feedback_summary = _dict_value(context_packet, "feedback_loop_summary")
    playbooks = _dict_tuple(context_packet.get("resource_request_playbooks", []))
    quality_control_obligations = _quality_control_obligation_summary(context_packet)
    source_grounding_obligations = _source_grounding_obligation_summary(
        context_packet
    )
    target_intake_rows = _dict_tuple(context_packet.get("target_intake_rows", []))
    planner_focus: list[dict[str, object]] = []
    evidence_gaps: list[dict[str, object]] = []

    def add_focus(
        focus_id: str,
        *,
        priority: int,
        action: str,
        reason: str,
        evidence_fields: tuple[str, ...],
        required_output_fields: tuple[str, ...],
        target_primitives: tuple[str, ...] = (),
    ) -> None:
        planner_focus.append(
            {
                "focus_id": focus_id,
                "priority": priority,
                "action": action,
                "reason": reason,
                "target_primitives": list(target_primitives),
                "evidence_fields": list(evidence_fields),
                "required_output_fields": list(required_output_fields),
                "proof_evidence_status": PROOF_EVIDENCE_STATUS,
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            }
        )

    def add_gap(
        gap_id: str,
        *,
        gap_kind: str,
        reason: str,
        recommended_action: str,
        evidence_fields: tuple[str, ...],
        target_primitives: tuple[str, ...] = (),
    ) -> None:
        evidence_gaps.append(
            {
                "gap_id": gap_id,
                "gap_kind": gap_kind,
                "reason": reason,
                "recommended_action": recommended_action,
                "target_primitives": list(target_primitives),
                "evidence_fields": list(evidence_fields),
            }
        )

    add_focus(
        "preserve_target_theorem_identity",
        priority=1,
        action="preserve requested theorem identity and target prover family",
        reason="route repair may add explicit side-condition notes but must not switch theorem",
        evidence_fields=("target_route", "context_packet.current_route"),
        required_output_fields=("standalone_route.theorem_statement",),
    )
    if residual_goals:
        add_focus(
            "interpret_residual_goals",
            priority=1,
            action="interpret prover residual goals and emit grounded route repair",
            reason="request residual_goals are present and must be covered by residual_interpretations",
            evidence_fields=(
                "residual_goals",
                "context_packet.feedback_loop_summary",
                "context_packet.available_source_snippets",
            ),
            required_output_fields=("residual_interpretations", "search_requests"),
            target_primitives=_residual_goal_target_primitives(residual_goals),
        )
    if source_refs or source_snippets:
        add_focus(
            "synthesize_source_grounded_informal_route",
            priority=2,
            action="build informal knowledge DAG from admissible source refs and snippets",
            reason="source evidence is available in the request context",
            evidence_fields=(
                "context_packet.available_source_refs",
                "context_packet.available_source_snippets",
            ),
            required_output_fields=(
                "informal_knowledge_dag_nodes",
                "standalone_route.primitives.source_refs",
            ),
        )
    else:
        add_focus(
            "request_literature_source_evidence",
            priority=2,
            action="emit bounded literature/source search requests before source-backed claims",
            reason="no admissible source refs or source snippets are available",
            evidence_fields=("context_packet.available_source_refs",),
            required_output_fields=("search_requests",),
        )
        add_gap(
            "missing_source_evidence",
            gap_kind="source_grounding",
            reason="no available source refs/snippets can ground informal claims",
            recommended_action="emit literature search_request rows",
            evidence_fields=("context_packet.available_source_refs",),
        )
    if formal_declaration_rows:
        add_focus(
            "map_formal_library_coverage",
            priority=3,
            action="align route primitives to target-compatible formal declaration rows",
            reason="formal declaration rows are available for reuse or bridge planning",
            evidence_fields=(
                "context_packet.available_formal_declaration_rows",
                "context_packet.available_formal_declarations",
            ),
            required_output_fields=(
                "formal_realization_dag_nodes",
                "minimal_delta_plan.primitive_costs",
            ),
        )
    else:
        add_focus(
            "request_formal_library_grounding",
            priority=3,
            action="emit formal-library search requests before exact-reuse claims",
            reason="no target-compatible formal declaration rows are available",
            evidence_fields=("context_packet.available_formal_declaration_rows",),
            required_output_fields=("search_requests",),
        )
        add_gap(
            "missing_formal_library_grounding",
            gap_kind="formal_library_grounding",
            reason="no available declaration row can justify existing-library coverage",
            recommended_action="emit formal_library search_request rows",
            evidence_fields=("context_packet.available_formal_declaration_rows",),
        )
    if primitive_cost_hints or route_option_hints:
        add_focus(
            "minimize_formalization_delta",
            priority=4,
            action="choose the lowest-cost AND/OR route consistent with coverage hints",
            reason="minimal_delta_cost_hints provide lower bounds for current library reuse",
            evidence_fields=("context_packet.minimal_delta_cost_hints",),
            required_output_fields=(
                "minimal_delta_plan",
                "minimal_delta_plan.and_or_cost_graph",
            ),
        )
    if alignment_summary:
        add_focus(
            "honor_library_alignment_summary",
            priority=3,
            action=(
                "use per-primitive library alignment classes as lower-bound "
                "reuse versus delta decisions"
            ),
            reason=(
                "library_alignment_summary classifies each primitive against "
                "current target-prover coverage and target-compatible declarations"
            ),
            evidence_fields=(
                "context_packet.library_alignment_summary",
                "context_packet.minimal_delta_cost_hints",
            ),
            required_output_fields=(
                "formal_realization_dag_nodes",
                "minimal_delta_plan.primitive_costs",
            ),
        )
    if bool(feedback_summary.get("replan_required", False)):
        add_focus(
            "revise_route_from_feedback",
            priority=1,
            action="repair the route using feedback-loop evidence and next actions",
            reason="feedback_loop_summary marks replan_required",
            evidence_fields=("context_packet.feedback_loop_summary",),
            required_output_fields=(
                "standalone_route",
                "planner_next_actions",
                "residual_interpretations",
            ),
        )
    if playbooks:
        add_focus(
            "align_followup_to_resource_playbooks",
            priority=2,
            action="align search_requests and planner_next_actions to queued resource playbooks",
            reason="resource_request_playbooks define bounded operator prompts and acceptance checks",
            evidence_fields=("context_packet.resource_request_playbooks",),
            required_output_fields=("search_requests", "planner_next_actions"),
        )
    if bool(quality_control_obligations.get("pending", False)):
        add_focus(
            "discharge_pending_quality_controls",
            priority=2,
            action="preserve or request evidence for pending quality controls",
            reason="context has pending quality-control obligations",
            evidence_fields=(
                "context_packet.feedback_loop_summary",
                "context_packet.resource_request_queue_rows",
            ),
            required_output_fields=("planner_next_actions", "search_requests"),
        )
        add_gap(
            "pending_quality_controls",
            gap_kind="quality_control",
            reason="quality controls remain pending in the context packet",
            recommended_action="emit bounded next actions that discharge pending controls",
            evidence_fields=("context_packet.context_packet_inventory",),
        )
    if bool(source_grounding_obligations.get("pending", False)):
        add_focus(
            "resolve_source_grounding_obligations",
            priority=2,
            action=(
                "resolve unaccounted or source-search-pending grounding rows "
                "before adoption"
            ),
            reason=(
                "source-grounding audit rows in the request context remain "
                "unresolved"
            ),
            evidence_fields=(
                "context_packet.source_grounding_obligations",
                "context_packet.source_grounding_rows",
            ),
            required_output_fields=("search_requests", "planner_next_actions"),
        )
        add_gap(
            "pending_source_grounding",
            gap_kind="source_grounding",
            reason=(
                "source-grounding audit rows remain unaccounted, source-search "
                "pending, or failed"
            ),
            recommended_action=(
                "emit bounded source-search or route-repair next actions"
            ),
            evidence_fields=("context_packet.source_grounding_obligations",),
        )

    target_context = {
        "theorem_statement": str(
            route.get("theorem_statement")
            or route.get("formal_statement")
            or route.get("statement")
            or ""
        ),
        "target_intake_claims": [
            str(row.get("normalized_claim", "")).strip()
            for row in target_intake_rows[:6]
            if str(row.get("normalized_claim", "")).strip()
        ],
        "desired_theorem_shapes": [
            str(row.get("desired_theorem_shape", "")).strip()
            for row in target_intake_rows[:6]
            if str(row.get("desired_theorem_shape", "")).strip()
        ],
        "normalized_objects": list(
            dict.fromkeys(
                object_name
                for row in target_intake_rows
                for object_name in _str_tuple(row.get("normalized_objects", []))
            )
        )[:12],
        "normalized_assumptions": list(
            dict.fromkeys(
                assumption
                for row in target_intake_rows
                for assumption in _str_tuple(row.get("normalized_assumptions", []))
            )
        )[:12],
    }
    evidence_summary = {
        "source_ref_count": len(source_refs),
        "source_snippet_count": len(source_snippets),
        "formal_declaration_row_count": len(formal_declaration_rows),
        "residual_goal_count": len(residual_goals),
        "primitive_cost_hint_count": len(primitive_cost_hints),
        "route_option_cost_hint_count": len(route_option_hints),
        "library_alignment_primitive_count": int(
            alignment_summary.get("n_primitives", 0) or 0
        ),
        "library_alignment_bridge_or_harder_count": int(
            alignment_summary.get("n_bridge_or_harder_primitives", 0) or 0
        ),
        "library_alignment_unknown_count": int(
            alignment_summary.get("n_unknown_primitives", 0) or 0
        ),
        "target_compatible_reuse_declaration_count": int(
            alignment_summary.get("n_target_compatible_reuse_declarations", 0)
            or 0
        ),
        "resource_request_playbook_count": len(playbooks),
        "feedback_replan_required": bool(feedback_summary.get("replan_required", False)),
        "pending_quality_control_value_count": int(
            quality_control_obligations.get("n_pending_values", 0) or 0
        ),
        "source_grounding_unresolved_count": int(
            source_grounding_obligations.get("n_unresolved_rows", 0) or 0
        ),
        "residual_source_grounding_unresolved_count": int(
            source_grounding_obligations.get(
                "n_residual_unresolved_rows",
                0,
            )
            or 0
        ),
    }
    return {
        "brief_kind": ROUTE_PLANNING_BRIEF_KIND,
        "route_id": route_id,
        "display_name": display_name,
        "target_prover_family": target_prover_family,
        "library_snapshot_ref": library_snapshot_ref,
        "target_context": target_context,
        "evidence_summary": evidence_summary,
        "planner_focus": sorted(
            planner_focus,
            key=lambda item: (
                int(item.get("priority", 999) or 999),
                str(item.get("focus_id", "")),
            ),
        ),
        "evidence_gaps": evidence_gaps,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _residual_goal_target_primitives(
    residual_goals: tuple[str, ...],
) -> tuple[str, ...]:
    primitives: list[str] = []
    for residual in residual_goals:
        prefix = str(residual).split(":", 1)[0].strip()
        if prefix and re.match(r"^[A-Za-z_][A-Za-z0-9_.'-]*$", prefix):
            primitives.append(prefix)
    return tuple(dict.fromkeys(primitives))


def _source_grounding_obligation_summary(
    context_packet: Mapping[str, Any],
) -> dict[str, object]:
    rows = _dict_tuple(context_packet.get("source_grounding_rows", []))
    statuses = tuple(_source_grounding_status(row) for row in rows)
    unresolved_rows = tuple(
        row for row in rows if _source_grounding_row_unresolved(row)
    )
    residual_rows = tuple(
        row for row in rows if _source_grounding_row_from_residual(row)
    )
    residual_unresolved_rows = tuple(
        row
        for row in unresolved_rows
        if _source_grounding_row_from_residual(row)
    )
    return {
        "present": bool(rows),
        "pending": bool(unresolved_rows),
        "discharged": bool(rows) and not unresolved_rows,
        "n_rows": len(rows),
        "n_residual_rows": len(residual_rows),
        "n_unresolved_rows": len(unresolved_rows),
        "n_residual_unresolved_rows": len(residual_unresolved_rows),
        "by_grounding_status": _value_counts(statuses),
        "unresolved_grounding_statuses": sorted(
            {
                _source_grounding_status(row)
                for row in unresolved_rows
                if _source_grounding_status(row)
            }
        ),
        "unresolved_row_ids": [
            _source_grounding_row_id(row) for row in unresolved_rows[:25]
        ],
        "residual_unresolved_row_ids": [
            _source_grounding_row_id(row)
            for row in residual_unresolved_rows[:25]
        ],
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _source_grounding_status(row: Mapping[str, object]) -> str:
    return str(
        row.get("grounding_status")
        or row.get("source_grounding_status")
        or ""
    ).strip()


def _source_grounding_row_unresolved(row: Mapping[str, object]) -> bool:
    status = _source_grounding_status(row)
    ok_value = row.get("ok")
    ok_explicitly_false = ok_value is False or (
        "ok" in row and str(ok_value).strip().lower() in {"false", "no", "0"}
    )
    return ok_explicitly_false or status in SOURCE_GROUNDING_UNRESOLVED_STATUSES


def _source_grounding_row_from_residual(row: Mapping[str, object]) -> bool:
    node_source = str(row.get("node_source", "")).strip()
    if node_source == SOURCE_GROUNDING_RESIDUAL_NODE_SOURCE:
        return True
    searchable_fields = (
        row.get("source_grounding_id", ""),
        row.get("node_id", ""),
        row.get("node_kind", ""),
        row.get("required_next_action", ""),
    )
    return any("residual" in str(value).lower() for value in searchable_fields)


def _source_grounding_row_id(row: Mapping[str, object]) -> str:
    return str(
        row.get("source_grounding_id")
        or row.get("node_id")
        or row.get("route_id")
        or row.get("source_route_id")
        or ""
    ).strip()


def _context_packet_inventory(
    context_packet: Mapping[str, Any],
    *,
    residual_goals: tuple[str, ...],
) -> dict[str, object]:
    row_counts = {
        field_name: len(_dict_tuple(context_packet.get(field_name, [])))
        for field_name in CONTEXT_PACKET_ROW_FIELDS
    }
    feedback_summary = _dict_value(context_packet, "feedback_loop_summary")
    cost_hints = _dict_value(context_packet, "minimal_delta_cost_hints")
    alignment_summary = _dict_value(context_packet, "library_alignment_summary")
    registry_context = _dict_value(
        context_packet,
        "component_resource_registry_context",
    )
    route_planning_brief = _dict_value(context_packet, "route_planning_brief")
    quality_control_obligations = _quality_control_obligation_summary(context_packet)
    source_grounding_obligations = _source_grounding_obligation_summary(
        context_packet
    )
    quality_controls = _dict_value(quality_control_obligations, "quality_controls")
    pending_quality_controls = _dict_value(
        quality_control_obligations,
        "pending_quality_controls",
    )
    discharged_quality_controls = _dict_value(
        quality_control_obligations,
        "discharged_quality_controls",
    )
    return {
        "inventory_kind": CONTEXT_PACKET_INVENTORY_KIND,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "row_counts": row_counts,
        "total_context_rows": sum(row_counts.values()),
        "residual_goal_count": len(residual_goals),
        "available_source_ref_count": len(
            _str_tuple(context_packet.get("available_source_refs", []))
        ),
        "available_source_snippet_count": len(
            _dict_tuple(context_packet.get("available_source_snippets", []))
        ),
        "available_formal_declaration_count": len(
            _str_tuple(context_packet.get("available_formal_declarations", []))
        ),
        "available_formal_declaration_row_count": len(
            _dict_tuple(context_packet.get("available_formal_declaration_rows", []))
        ),
        "resource_request_playbook_count": len(
            _dict_tuple(context_packet.get("resource_request_playbooks", []))
        ),
        "legacy_context_field_alias_count": len(
            _dict_value(context_packet, "legacy_context_field_aliases")
        ),
        "primitive_cost_hint_count": len(
            _dict_tuple(cost_hints.get("primitive_cost_hints", []))
        ),
        "route_option_cost_hint_count": len(
            _dict_tuple(cost_hints.get("route_option_hints", []))
        ),
        "library_alignment_summary_present": bool(alignment_summary),
        "library_alignment_primitive_count": int(
            alignment_summary.get("n_primitives", 0) or 0
        ),
        "library_alignment_reuse_ready_count": int(
            alignment_summary.get("n_reuse_ready_primitives", 0) or 0
        ),
        "library_alignment_wrapper_count": int(
            alignment_summary.get("n_wrapper_primitives", 0) or 0
        ),
        "library_alignment_bridge_count": int(
            alignment_summary.get("n_bridge_primitives", 0) or 0
        ),
        "library_alignment_source_port_count": int(
            alignment_summary.get("n_source_port_primitives", 0) or 0
        ),
        "library_alignment_new_definition_count": int(
            alignment_summary.get("n_new_definition_primitives", 0) or 0
        ),
        "library_alignment_new_theory_count": int(
            alignment_summary.get("n_new_theory_primitives", 0) or 0
        ),
        "library_alignment_unknown_count": int(
            alignment_summary.get("n_unknown_primitives", 0) or 0
        ),
        "library_alignment_bridge_or_harder_count": int(
            alignment_summary.get("n_bridge_or_harder_primitives", 0) or 0
        ),
        "library_alignment_target_compatible_reuse_declaration_count": int(
            alignment_summary.get("n_target_compatible_reuse_declarations", 0)
            or 0
        ),
        "component_resource_count": len(
            _dict_tuple(registry_context.get("resource_rows", []))
        ),
        "component_resource_contract_count": len(
            _dict_tuple(registry_context.get("resource_contract_rows", []))
        ),
        "route_planning_brief_present": bool(route_planning_brief),
        "route_planning_brief_focus_count": len(
            _dict_tuple(route_planning_brief.get("planner_focus", []))
        ),
        "route_planning_brief_evidence_gap_count": len(
            _dict_tuple(route_planning_brief.get("evidence_gaps", []))
        ),
        "feedback_loop_summary_present": bool(feedback_summary),
        "feedback_loop_summary_replan_required": bool(
            feedback_summary.get("replan_required", False)
        ),
        "feedback_loop_summary_recommended_next_action_count": len(
            _dict_tuple(feedback_summary.get("recommended_next_actions", []))
        ),
        "feedback_loop_summary_prior_llm_route_planner_hook_trace_count": len(
            _dict_tuple(
                _dict_value(
                    feedback_summary,
                    "prior_replan_metadata",
                ).get("applied_llm_route_planner_hook_traces", [])
            )
        ),
        "quality_control_obligation_present": bool(
            quality_control_obligations.get("present", False)
        ),
        "quality_control_obligation_pending": bool(
            quality_control_obligations.get("pending", False)
        ),
        "quality_control_obligation_discharged": bool(
            quality_control_obligations.get("discharged", False)
        ),
        "quality_control_obligation_field_count": len(quality_controls),
        "quality_control_obligation_value_count": _quality_control_value_count(
            quality_controls
        ),
        "pending_quality_control_field_count": len(pending_quality_controls),
        "pending_quality_control_value_count": _quality_control_value_count(
            pending_quality_controls
        ),
        "discharged_quality_control_field_count": len(discharged_quality_controls),
        "discharged_quality_control_value_count": _quality_control_value_count(
            discharged_quality_controls
        ),
        "source_grounding_obligation_present": bool(
            source_grounding_obligations.get("present", False)
        ),
        "source_grounding_obligation_pending": bool(
            source_grounding_obligations.get("pending", False)
        ),
        "source_grounding_obligation_discharged": bool(
            source_grounding_obligations.get("discharged", False)
        ),
        "source_grounding_row_count": int(
            source_grounding_obligations.get("n_rows", 0) or 0
        ),
        "source_grounding_residual_row_count": int(
            source_grounding_obligations.get("n_residual_rows", 0) or 0
        ),
        "source_grounding_unresolved_count": int(
            source_grounding_obligations.get("n_unresolved_rows", 0) or 0
        ),
        "residual_source_grounding_unresolved_count": int(
            source_grounding_obligations.get("n_residual_unresolved_rows", 0)
            or 0
        ),
    }


def _library_alignment_summary_errors(
    context_packet: Mapping[str, Any],
) -> list[str]:
    summary = _dict_value(context_packet, "library_alignment_summary")
    if not summary:
        return []
    expected = _library_alignment_summary(
        context_packet,
        route_id=str(context_packet.get("route_id", "")),
        display_name=str(
            context_packet.get("display_name", "")
            or context_packet.get("route_id", "")
        ),
        target_prover_family=str(context_packet.get("target_prover_family", "")),
        library_snapshot_ref=str(context_packet.get("library_snapshot_ref", "")),
    )
    errors: list[str] = []
    scalar_fields = (
        "schema_version",
        "schema_id",
        "summary_kind",
        "route_id",
        "display_name",
        "target_prover_family",
        "library_snapshot_ref",
        "cost_policy_id",
        "n_primitives",
        "n_reuse_ready_primitives",
        "n_wrapper_primitives",
        "n_bridge_primitives",
        "n_source_port_primitives",
        "n_new_definition_primitives",
        "n_new_theory_primitives",
        "n_unknown_primitives",
        "n_bridge_or_harder_primitives",
        "n_target_compatible_reuse_declarations",
        "n_route_options",
        "proof_evidence_status",
        "proof_evidence_boundary",
    )
    for field_name in scalar_fields:
        if summary.get(field_name) != expected.get(field_name):
            errors.append(
                "context_packet.library_alignment_summary."
                f"{field_name} must match minimal_delta_cost_hints"
            )
    for field_name in (
        "by_library_delta_class",
        "by_minimum_coverage_bucket",
        "primitive_alignment",
        "route_option_alignment",
    ):
        if summary.get(field_name) != expected.get(field_name):
            errors.append(
                "context_packet.library_alignment_summary."
                f"{field_name} must match minimal_delta_cost_hints"
            )
    return errors


def _context_packet_inventory_errors(row: Mapping[str, object]) -> list[str]:
    context_packet = _dict_value(row, "context_packet")
    inventory = _dict_value(context_packet, "context_packet_inventory")
    if not inventory:
        return []
    errors: list[str] = []
    if inventory.get("inventory_kind") != CONTEXT_PACKET_INVENTORY_KIND:
        errors.append(
            "context_packet.context_packet_inventory.inventory_kind must equal "
            + CONTEXT_PACKET_INVENTORY_KIND
        )
    row_counts = _dict_value(inventory, "row_counts")
    total_context_rows = 0
    for field_name in CONTEXT_PACKET_ROW_FIELDS:
        expected_count = len(_dict_tuple(context_packet.get(field_name, [])))
        actual_count = int(row_counts.get(field_name, 0) or 0)
        total_context_rows += expected_count
        if actual_count != expected_count:
            errors.append(
                "context_packet.context_packet_inventory.row_counts."
                f"{field_name} must match context_packet.{field_name}"
            )
    if int(inventory.get("total_context_rows", 0) or 0) != total_context_rows:
        errors.append(
            "context_packet.context_packet_inventory.total_context_rows must "
            "match summed context row counts"
        )
    scalar_count_checks = (
        (
            "residual_goal_count",
            len(_str_tuple(context_packet.get("residual_goals", []))),
        ),
        (
            "available_source_ref_count",
            len(_str_tuple(context_packet.get("available_source_refs", []))),
        ),
        (
            "available_source_snippet_count",
            len(_dict_tuple(context_packet.get("available_source_snippets", []))),
        ),
        (
            "available_formal_declaration_count",
            len(_str_tuple(context_packet.get("available_formal_declarations", []))),
        ),
        (
            "available_formal_declaration_row_count",
            len(
                _dict_tuple(
                    context_packet.get("available_formal_declaration_rows", [])
                )
            ),
        ),
        (
            "resource_request_playbook_count",
            len(_dict_tuple(context_packet.get("resource_request_playbooks", []))),
        ),
        (
            "legacy_context_field_alias_count",
            len(_dict_value(context_packet, "legacy_context_field_aliases")),
        ),
    )
    aliases = _dict_value(context_packet, "legacy_context_field_aliases")
    if aliases != _legacy_context_field_aliases_for_target(
        context_packet.get("target_prover_family", "")
    ):
        errors.append(
            "context_packet.legacy_context_field_aliases must match planner "
            "legacy context alias contract for target_prover_family"
        )
    for field_name, expected_count in scalar_count_checks:
        if int(inventory.get(field_name, 0) or 0) != expected_count:
            errors.append(
                "context_packet.context_packet_inventory."
                f"{field_name} must match context_packet"
            )
    cost_hints = _dict_value(context_packet, "minimal_delta_cost_hints")
    if int(inventory.get("primitive_cost_hint_count", 0) or 0) != len(
        _dict_tuple(cost_hints.get("primitive_cost_hints", []))
    ):
        errors.append(
            "context_packet.context_packet_inventory.primitive_cost_hint_count "
            "must match context_packet.minimal_delta_cost_hints"
        )
    if int(inventory.get("route_option_cost_hint_count", 0) or 0) != len(
        _dict_tuple(cost_hints.get("route_option_hints", []))
    ):
        errors.append(
            "context_packet.context_packet_inventory.route_option_cost_hint_count "
            "must match context_packet.minimal_delta_cost_hints"
        )
    alignment_summary = _dict_value(context_packet, "library_alignment_summary")
    if bool(inventory.get("library_alignment_summary_present", False)) != bool(
        alignment_summary
    ):
        errors.append(
            "context_packet.context_packet_inventory."
            "library_alignment_summary_present must match "
            "context_packet.library_alignment_summary"
        )
    if alignment_summary:
        errors.extend(_library_alignment_summary_errors(context_packet))
        alignment_count_checks = (
            ("library_alignment_primitive_count", "n_primitives"),
            ("library_alignment_reuse_ready_count", "n_reuse_ready_primitives"),
            ("library_alignment_wrapper_count", "n_wrapper_primitives"),
            ("library_alignment_bridge_count", "n_bridge_primitives"),
            ("library_alignment_source_port_count", "n_source_port_primitives"),
            (
                "library_alignment_new_definition_count",
                "n_new_definition_primitives",
            ),
            ("library_alignment_new_theory_count", "n_new_theory_primitives"),
            ("library_alignment_unknown_count", "n_unknown_primitives"),
            (
                "library_alignment_bridge_or_harder_count",
                "n_bridge_or_harder_primitives",
            ),
            (
                "library_alignment_target_compatible_reuse_declaration_count",
                "n_target_compatible_reuse_declarations",
            ),
        )
        for inventory_field, summary_field in alignment_count_checks:
            if int(inventory.get(inventory_field, 0) or 0) != int(
                alignment_summary.get(summary_field, 0) or 0
            ):
                errors.append(
                    "context_packet.context_packet_inventory."
                    f"{inventory_field} must match "
                    "context_packet.library_alignment_summary"
                )
    feedback_summary = _dict_value(context_packet, "feedback_loop_summary")
    if bool(inventory.get("feedback_loop_summary_present", False)) != bool(
        feedback_summary
    ):
        errors.append(
            "context_packet.context_packet_inventory.feedback_loop_summary_present "
            "must match context_packet.feedback_loop_summary"
        )
    if bool(inventory.get("feedback_loop_summary_replan_required", False)) != bool(
        feedback_summary.get("replan_required", False)
    ):
        errors.append(
            "context_packet.context_packet_inventory."
            "feedback_loop_summary_replan_required must match "
            "context_packet.feedback_loop_summary"
        )
    if int(
        inventory.get("feedback_loop_summary_recommended_next_action_count", 0) or 0
    ) != len(_dict_tuple(feedback_summary.get("recommended_next_actions", []))):
        errors.append(
            "context_packet.context_packet_inventory."
            "feedback_loop_summary_recommended_next_action_count must match "
            "context_packet.feedback_loop_summary"
        )
    prior_metadata = _dict_value(feedback_summary, "prior_replan_metadata")
    if int(
        inventory.get(
            "feedback_loop_summary_prior_llm_route_planner_hook_trace_count",
            0,
        )
        or 0
    ) != len(
        _dict_tuple(prior_metadata.get("applied_llm_route_planner_hook_traces", []))
    ):
        errors.append(
            "context_packet.context_packet_inventory."
            "feedback_loop_summary_prior_llm_route_planner_hook_trace_count "
            "must match context_packet.feedback_loop_summary.prior_replan_metadata"
        )
    route_planning_brief = _dict_value(context_packet, "route_planning_brief")
    if bool(inventory.get("route_planning_brief_present", False)) != bool(
        route_planning_brief
    ):
        errors.append(
            "context_packet.context_packet_inventory.route_planning_brief_present "
            "must match context_packet.route_planning_brief"
        )
    if route_planning_brief:
        if route_planning_brief.get("brief_kind") != ROUTE_PLANNING_BRIEF_KIND:
            errors.append(
                "context_packet.route_planning_brief.brief_kind must equal "
                + ROUTE_PLANNING_BRIEF_KIND
            )
        if str(route_planning_brief.get("route_id", "")) != str(
            row.get("route_id", "")
        ):
            errors.append(
                "context_packet.route_planning_brief.route_id must match request route_id"
            )
        if str(route_planning_brief.get("target_prover_family", "")) != str(
            context_packet.get("target_prover_family", "")
        ):
            errors.append(
                "context_packet.route_planning_brief.target_prover_family must match context_packet"
            )
        if int(inventory.get("route_planning_brief_focus_count", 0) or 0) != len(
            _dict_tuple(route_planning_brief.get("planner_focus", []))
        ):
            errors.append(
                "context_packet.context_packet_inventory.route_planning_brief_focus_count "
                "must match context_packet.route_planning_brief"
            )
        if int(
            inventory.get("route_planning_brief_evidence_gap_count", 0) or 0
        ) != len(_dict_tuple(route_planning_brief.get("evidence_gaps", []))):
            errors.append(
                "context_packet.context_packet_inventory.route_planning_brief_evidence_gap_count "
                "must match context_packet.route_planning_brief"
            )
        brief_summary = _dict_value(route_planning_brief, "evidence_summary")
        brief_count_checks = (
            (
                "source_ref_count",
                len(_str_tuple(context_packet.get("available_source_refs", []))),
            ),
            (
                "source_snippet_count",
                len(_dict_tuple(context_packet.get("available_source_snippets", []))),
            ),
            (
                "formal_declaration_row_count",
                len(
                    _dict_tuple(
                        context_packet.get("available_formal_declaration_rows", [])
                    )
                ),
            ),
            (
                "residual_goal_count",
                len(_str_tuple(context_packet.get("residual_goals", []))),
            ),
            (
                "primitive_cost_hint_count",
                len(_dict_tuple(cost_hints.get("primitive_cost_hints", []))),
            ),
            (
                "route_option_cost_hint_count",
                len(_dict_tuple(cost_hints.get("route_option_hints", []))),
            ),
            (
                "library_alignment_primitive_count",
                int(alignment_summary.get("n_primitives", 0) or 0),
            ),
            (
                "library_alignment_bridge_or_harder_count",
                int(
                    alignment_summary.get("n_bridge_or_harder_primitives", 0)
                    or 0
                ),
            ),
            (
                "library_alignment_unknown_count",
                int(alignment_summary.get("n_unknown_primitives", 0) or 0),
            ),
            (
                "target_compatible_reuse_declaration_count",
                int(
                    alignment_summary.get(
                        "n_target_compatible_reuse_declarations",
                        0,
                    )
                    or 0
                ),
            ),
            (
                "resource_request_playbook_count",
                len(_dict_tuple(context_packet.get("resource_request_playbooks", []))),
            ),
            (
                "source_grounding_unresolved_count",
                int(
                    _source_grounding_obligation_summary(context_packet).get(
                        "n_unresolved_rows",
                        0,
                    )
                    or 0
                ),
            ),
            (
                "residual_source_grounding_unresolved_count",
                int(
                    _source_grounding_obligation_summary(context_packet).get(
                        "n_residual_unresolved_rows",
                        0,
                    )
                    or 0
                ),
            ),
        )
        for field_name, expected_count in brief_count_checks:
            if int(brief_summary.get(field_name, 0) or 0) != expected_count:
                errors.append(
                    "context_packet.route_planning_brief.evidence_summary."
                    f"{field_name} must match context_packet"
                )
    quality_control_obligations = _quality_control_obligation_summary(context_packet)
    quality_controls = _dict_value(quality_control_obligations, "quality_controls")
    pending_quality_controls = _dict_value(
        quality_control_obligations,
        "pending_quality_controls",
    )
    discharged_quality_controls = _dict_value(
        quality_control_obligations,
        "discharged_quality_controls",
    )
    quality_control_count_checks = (
        (
            "quality_control_obligation_present",
            bool(quality_control_obligations.get("present", False)),
        ),
        (
            "quality_control_obligation_pending",
            bool(quality_control_obligations.get("pending", False)),
        ),
        (
            "quality_control_obligation_discharged",
            bool(quality_control_obligations.get("discharged", False)),
        ),
        ("quality_control_obligation_field_count", len(quality_controls)),
        (
            "quality_control_obligation_value_count",
            _quality_control_value_count(quality_controls),
        ),
        ("pending_quality_control_field_count", len(pending_quality_controls)),
        (
            "pending_quality_control_value_count",
            _quality_control_value_count(pending_quality_controls),
        ),
        ("discharged_quality_control_field_count", len(discharged_quality_controls)),
        (
            "discharged_quality_control_value_count",
            _quality_control_value_count(discharged_quality_controls),
        ),
    )
    for field_name, expected_value in quality_control_count_checks:
        actual_value = inventory.get(
            field_name,
            False if isinstance(expected_value, bool) else 0,
        )
        if isinstance(expected_value, bool):
            matches = bool(actual_value) == expected_value
        else:
            matches = int(actual_value or 0) == expected_value
        if not matches:
            errors.append(
                "context_packet.context_packet_inventory."
                f"{field_name} must match quality_control_obligations"
            )
    source_grounding_obligations = _source_grounding_obligation_summary(
        context_packet
    )
    reported_source_grounding_obligations = _dict_value(
        context_packet,
        "source_grounding_obligations",
    )
    if reported_source_grounding_obligations:
        source_grounding_summary_checks = (
            "present",
            "pending",
            "discharged",
            "n_rows",
            "n_residual_rows",
            "n_unresolved_rows",
            "n_residual_unresolved_rows",
        )
        for field_name in source_grounding_summary_checks:
            if reported_source_grounding_obligations.get(
                field_name
            ) != source_grounding_obligations.get(field_name):
                errors.append(
                    "context_packet.source_grounding_obligations."
                    f"{field_name} must match context_packet.source_grounding_rows"
                )
    source_grounding_count_checks = (
        (
            "source_grounding_obligation_present",
            bool(source_grounding_obligations.get("present", False)),
        ),
        (
            "source_grounding_obligation_pending",
            bool(source_grounding_obligations.get("pending", False)),
        ),
        (
            "source_grounding_obligation_discharged",
            bool(source_grounding_obligations.get("discharged", False)),
        ),
        (
            "source_grounding_row_count",
            int(source_grounding_obligations.get("n_rows", 0) or 0),
        ),
        (
            "source_grounding_residual_row_count",
            int(source_grounding_obligations.get("n_residual_rows", 0) or 0),
        ),
        (
            "source_grounding_unresolved_count",
            int(source_grounding_obligations.get("n_unresolved_rows", 0) or 0),
        ),
        (
            "residual_source_grounding_unresolved_count",
            int(
                source_grounding_obligations.get(
                    "n_residual_unresolved_rows",
                    0,
                )
                or 0
            ),
        ),
    )
    for field_name, expected_value in source_grounding_count_checks:
        actual_value = inventory.get(
            field_name,
            False if isinstance(expected_value, bool) else 0,
        )
        if isinstance(expected_value, bool):
            matches = bool(actual_value) == expected_value
        else:
            matches = int(actual_value or 0) == expected_value
        if not matches:
            errors.append(
                "context_packet.context_packet_inventory."
                f"{field_name} must match source_grounding_obligations"
            )
    return errors


def _output_contract_for_target_prover(target_prover_family: str) -> dict[str, object]:
    contract = deepcopy(LLM_ROUTE_PLANNER_OUTPUT_CONTRACT)
    if _target_prover_key(target_prover_family) != "lean4":
        contract.pop("lean_realization_dag_nodes", None)
    return contract


def _user_prompt(
    *,
    target_route: Mapping[str, Any],
    context_packet: Mapping[str, Any],
    required_output_contract: Mapping[str, Any],
) -> str:
    target_prover_key = _target_prover_key(
        context_packet.get("target_prover_family", "")
    )
    target_intake_requirement = (
        "When context_packet.target_intake_rows is present, use its "
        "normalized_objects, normalized_assumptions, normalized_procedure, "
        "normalized_claim, desired_theorem_shape, literature_queries, and "
        "formal_library_grounding_queries as the target theorem context for "
        "route synthesis; target intake is not proof evidence."
    )
    formal_realization_requirement = (
        "Use formal_realization_dag_nodes for the target-prover realization DAG."
    )
    declaration_seed_requirement = (
        "Resource-request candidate declarations are search seeds only; they "
        "cannot justify existing-library or reuse coverage until accepted "
        "formal_declaration_hits or route-level formal context is available."
    )
    declaration_scope_requirement = (
        "Primitive-scoped formal_declaration_hits may justify existing-library "
        "or reuse coverage only for the matching primitive; use bridge/prover "
        "feedback/search when a declaration is merely a premise for a different "
        "primitive."
    )
    if target_prover_key == "lean4":
        target_intake_requirement = (
            target_intake_requirement
            + " lean_grounding_queries is a legacy alias only."
        )
        formal_realization_requirement = (
            "Use formal_realization_dag_nodes for all target provers; "
            "lean_realization_dag_nodes is accepted only as a Lean legacy "
            "alias and must not be used for non-Lean target_prover_family "
            "values."
        )
        declaration_seed_requirement = (
            "Resource-request candidate declarations are search seeds only; "
            "they cannot justify existing-library or reuse coverage until "
            "accepted formal_declaration_hits, a Lean-only legacy "
            "lean_declaration_hits alias listed in "
            "context_packet.legacy_context_field_aliases, or route-level "
            "formal context is available."
        )
        declaration_scope_requirement = (
            "Primitive-scoped formal_declaration_hits, or Lean-only legacy "
            "lean_declaration_hits aliases listed in "
            "context_packet.legacy_context_field_aliases, may justify "
            "existing-library or reuse coverage only for the matching "
            "primitive; use bridge/prover feedback/search when a declaration "
            "is merely a premise for a different primitive."
        )
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
            target_intake_requirement,
            "standalone_route.theorem_statement must preserve the requested target theorem identity; route repairs may add explicit side-condition notes but must not switch to a different theorem.",
            "Every informal DAG node must have source_refs, a source_search_status, or a formal_gap_boundary.",
            "source_search_status values are limited to SOURCE_BACKED, SEARCH_REQUESTED/search_pending/source_search_pending/literature_search_pending, or FORMAL_GAP_BOUNDARY/formal_boundary_declared; unsupported status strings are rejected.",
            "Any FORMAL_GAP_BOUNDARY/formal_boundary_declared status or formal_gap_boundary field must include a substantive boundary explanation, not a placeholder such as todo/later.",
            "SOURCE_BACKED claims may cite only source_refs listed in context_packet.available_source_refs.",
            "Any standalone_route primitive marked SOURCE_BACKED must carry primitive-level source_refs or source_snippets; route-level source_refs do not silently justify that primitive.",
            "When context_packet.available_source_snippets contains relevant excerpts, reuse those source_snippets in informal DAG nodes or standalone_route primitives instead of paraphrasing unsupported evidence.",
            "source_snippets may cite only source_refs listed in context_packet.available_source_refs.",
            "Partial source_snippets are checked against both their own target_primitives and their enclosing informal/route primitive scope; omitting target_primitives inside a primitive-specific node does not make the source evidence support that primitive.",
            "If a needed source is not listed, emit a literature search_request instead of inventing a source_ref.",
            "Any informal node or standalone primitive with SEARCH_REQUESTED/source_search_pending status must have a matching literature/source search_request.",
            "Existing-library or reuse claims may cite only candidate_declarations or candidate_declaration_rows listed in context_packet.available_formal_declarations/available_formal_declaration_rows.",
            declaration_seed_requirement,
            declaration_scope_requirement,
            "Prefer candidate_declaration_rows over bare candidate_declarations so target_prover_family provenance is preserved.",
            "If a needed declaration is not listed, emit a formal_library search_request instead of inventing a candidate_declaration.",
            "Any formal-realization node or standalone primitive with unknown/formal-library-search-pending coverage must have a matching formal_library/library search_request unless it declares a formal gap boundary or concrete delta action.",
            "Every search_requests row must use a supported request_kind, include a nonempty query, and include a nonempty reason.",
            "search_requests.target_primitives may mention only primitives already present in the request context, selected/delta/cost-hint plan, formal realization DAG, standalone route, alignment edges, or residual interpretations.",
            "Every planner_next_actions row must include owner and action, and the row must resolve to a supported literature/formal-library/proof-state/route-revision hook family.",
            "planner_next_actions.target_primitives may mention only primitives already present in the request context, selected/delta/cost-hint plan, formal realization DAG, standalone route, alignment edges, or residual interpretations.",
            "Use context_packet.context_packet_inventory as the compact inventory of available evidence and feedback rows; raw context_packet rows remain the source of truth if a count is surprising.",
            "Use context_packet.legacy_context_field_aliases only as a compatibility map; prefer portable fields such as formal_library_grounding_queries and formal_declaration_hits in new route output.",
            "Use context_packet.component_resource_registry_context only to choose bounded search/prover next actions; registry rows are not evidence that a tool was called.",
            "When context_packet.feedback_loop_summary is present, treat it as the route-repair brief derived from raw residual/resource/interactive rows; it is planning context, not proof evidence.",
            "When context_packet.route_replan_handoff_rows is present, preserve its applied evidence ids, quality controls, and next_commands as prior handoff context; route-replan handoff rows are planning input, not proof evidence.",
            "Resource-response ledger rows with awaiting, rejected, absent-response, failed-contract, or unmet-contract-minimum status are status-only; do not use them as residual-goal or route-repair evidence.",
            "Residual interpretations may cover only residual_goals listed in the request packet.",
            "If request residual_goals are present, every residual goal must have an interpretation and a route_repair or repair_action.",
            "Every residual_interpretations row that proposes route repair must have source_refs/source_snippets, a matching literature/source search_request, or a formal_gap_boundary; prover residuals alone are not source evidence for new mathematical side conditions.",
            "Every alignment edge must include an alignment_rationale.",
            "Every alignment edge informal_node_id/formal_node_id must reference nodes present in the returned informal and formal DAGs.",
            formal_realization_requirement,
            "Minimal delta must include selected_primitives, cost_model_version, route_cost, primitive_costs, and_or_cost_graph, and minimality_rationale.",
            "Use minimal_delta_cost_policy as the AND/OR graph cost surface; pick the route with the lowest current formalization delta cost.",
            "When context_packet.minimal_delta_cost_hints is present, use primitive_cost_hints as lower-bound coverage evidence and do not choose route options cheaper than their minimum_route_base_cost.",
            "If the selected route omits any primitive from context_packet.minimal_delta_cost_hints.route_option_hints, and_or_cost_graph.route_options must still enumerate that baseline primitive set with route_cost at least minimum_route_base_cost.",
            "Every selected primitive must have exactly one primitive_costs row with base_cost, proof_difficulty_cost, import_cone_cost, definition_or_typeclass_cost, semantic_risk_cost, reuse_credit, total_cost, and cost_rationale.",
            "Every primitive_costs coverage_bucket must be listed in minimal_delta_cost_policy.coverage_bucket_base_cost, and base_cost must equal that bucket base cost.",
            "A primitive_costs coverage_bucket/base_cost must not be cheaper than the explicit coverage_bucket, coverage_status, or formalization_action markers on the corresponding formal_realization_dag_nodes or standalone_route.primitives.",
            "Every primitive_costs row must satisfy total_cost = base_cost + proof_difficulty_cost + import_cone_cost + definition_or_typeclass_cost + semantic_risk_cost - reuse_credit; route_cost must equal the sum of selected primitive total_cost values.",
            "and_or_cost_graph must enumerate route_options, non-empty or_nodes, and non-empty and_edges; it must mark exactly one selected route option and no listed alternative may have lower route_cost.",
            "Every selected primitive must appear in standalone_route.primitives and formal_realization_dag_nodes.",
            "Every wrapper, bridge, source-port, new-definition, or first-principles delta primitive must have a route_alignment_edge.",
            "Every wrapper_lemmas, bridge_lemmas, source_port_lemmas, new_definitions, new_theory_primitives, or first_principles_primitives item used as a selected-delta action witness must be an actionable work item, not only the primitive name; include the primitive plus a theorem statement, definition goal, porting target, proof obligation, or construction description.",
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
        requested_model_tier = str(packet.get("model_tier", "") or "").strip()
        current_model_tier = requested_model_tier
        model_tier_escalated = False
        model_tier_escalation_reason = ""
        for attempt in range(repair_budget + 1):
            request_model = _generator_model_for_generation_attempt(
                generator_backend,
                packet,
                explicit_model=model,
                model_tier=str(packet.get("model_tier", "")),
                attempt_model_tier=current_model_tier,
            )
            try:
                generated = generator_backend.generate(
                    GeneratorRequest(
                        system_prompt=str(prompt.get("system", "")),
                        user_prompt=user_prompt,
                        model=request_model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        schema=llm_route_planner_response_payload_schema(
                            target_prover_family=str(
                                packet.get("target_prover_family", "")
                            )
                        ),
                        metadata={
                            "component": LLM_ROUTE_PLANNER_COMPONENT,
                            "request_id": str(packet.get("request_id", "")),
                            "requested_model_tier": requested_model_tier,
                            "model_tier": current_model_tier,
                            "model_tier_escalated": model_tier_escalated,
                            "model_tier_escalation_reason": (
                                model_tier_escalation_reason
                            ),
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
                    "requested_model_tier": requested_model_tier,
                    "model_tier": current_model_tier,
                    "model_tier_escalated": model_tier_escalated,
                    "model_tier_escalation_reason": model_tier_escalation_reason,
                    "response_payload": payload,
                    "raw_response_text": generated.text,
                    "generator_metadata": _generator_metadata_with_model_tier(
                        generated.metadata,
                        requested_model_tier=requested_model_tier,
                        effective_model_tier=current_model_tier,
                        model_tier_escalated=model_tier_escalated,
                        model_tier_escalation_reason=model_tier_escalation_reason,
                    ),
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
                unique_validation_errors = tuple(sorted(set(validation_errors)))
                repair_guidance_rows = _repair_guidance_rows(
                    unique_validation_errors
                )
                repair_entry: dict[str, object] = {
                    "attempt": attempt,
                    "model": request_model,
                    "model_tier": current_model_tier,
                    "requested_model_tier": requested_model_tier,
                    "errors": unique_validation_errors[:12],
                    "repair_guidance_categories": _repair_guidance_categories(
                        repair_guidance_rows
                    ),
                    "repair_guidance_fingerprint": stable_hash(
                        repair_guidance_rows
                    ),
                }
                if attempt >= repair_budget:
                    repair_history.append(repair_entry)
                    last_response = {
                        **candidate,
                        "repair_error_history": tuple(repair_history),
                        "generation_errors": unique_validation_errors,
                    }
                    break
                user_prompt = _repair_user_prompt(
                    original_user_prompt=str(prompt.get("user", "")),
                    previous_response_text=generated.text,
                    validation_errors=validation_errors,
                    attempt=attempt + 1,
                    repair_guidance_rows=repair_guidance_rows,
                )
                next_model_tier, next_tier_reason = _next_repair_model_tier(
                    generator_backend,
                    packet,
                    explicit_model=model,
                    current_model_tier=current_model_tier,
                )
                repair_entry["next_repair_attempt"] = attempt + 1
                repair_entry["next_repair_model_tier"] = next_model_tier
                repair_entry["repair_prompt_fingerprint"] = stable_hash(user_prompt)
                if next_model_tier != current_model_tier:
                    repair_entry["model_tier_escalation"] = (
                        f"{current_model_tier}_to_{next_model_tier}"
                    )
                    repair_entry["model_tier_escalation_reason"] = next_tier_reason
                    model_tier_escalated = True
                    model_tier_escalation_reason = next_tier_reason
                current_model_tier = next_model_tier
                repair_history.append(repair_entry)
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
                        "requested_model_tier": requested_model_tier,
                        "model_tier": current_model_tier,
                        "model_tier_escalated": model_tier_escalated,
                        "model_tier_escalation_reason": (
                            model_tier_escalation_reason
                        ),
                        "response_payload": {},
                        "raw_response_text": str(getattr(last_generated, "text", "")),
                        "generator_metadata": _generator_metadata_with_model_tier(
                            {
                                "generator_only": True,
                                "tools_available": False,
                                "provider_failure": True,
                                "exception_type": type(exc).__name__,
                                "exception_message": str(exc)[:1000],
                                "repair_attempt": attempt,
                            },
                            requested_model_tier=requested_model_tier,
                            effective_model_tier=current_model_tier,
                            model_tier_escalated=model_tier_escalated,
                            model_tier_escalation_reason=(
                                model_tier_escalation_reason
                            ),
                        ),
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
                repair_guidance_rows = _repair_guidance_rows([provider_error])
                user_prompt = _repair_user_prompt(
                    original_user_prompt=str(prompt.get("user", "")),
                    previous_response_text=str(
                        getattr(last_generated, "text", "")
                    ),
                    validation_errors=[provider_error],
                    attempt=attempt + 1,
                    repair_guidance_rows=repair_guidance_rows,
                )
                next_model_tier, next_tier_reason = _next_repair_model_tier(
                    generator_backend,
                    packet,
                    explicit_model=model,
                    current_model_tier=current_model_tier,
                )
                repair_entry: dict[str, object] = {
                    "attempt": attempt,
                    "model": request_model,
                    "model_tier": current_model_tier,
                    "requested_model_tier": requested_model_tier,
                    "errors": (provider_error,),
                    "repair_guidance_categories": _repair_guidance_categories(
                        repair_guidance_rows
                    ),
                    "repair_guidance_fingerprint": stable_hash(
                        repair_guidance_rows
                    ),
                    "next_repair_attempt": attempt + 1,
                    "next_repair_model_tier": next_model_tier,
                    "repair_prompt_fingerprint": stable_hash(user_prompt),
                }
                if next_model_tier != current_model_tier:
                    repair_entry["model_tier_escalation"] = (
                        f"{current_model_tier}_to_{next_model_tier}"
                    )
                    repair_entry["model_tier_escalation_reason"] = next_tier_reason
                    model_tier_escalated = True
                    model_tier_escalation_reason = next_tier_reason
                current_model_tier = next_model_tier
                repair_history.append(
                    repair_entry
                )
        if last_response is not None:
            responses.append(last_response)
    return responses


def _generator_model_for_generation_attempt(
    generator_backend: GeneratorBackend,
    packet: Mapping[str, Any],
    *,
    explicit_model: str,
    model_tier: str,
    attempt_model_tier: str,
) -> str:
    if explicit_model:
        requested_model = explicit_model
    elif str(attempt_model_tier or "").strip() != str(model_tier or "").strip():
        requested_model = ""
    else:
        requested_model = str(packet.get("model", ""))
    return _generator_model_for_request(
        generator_backend,
        requested_model,
        model_tier=attempt_model_tier or model_tier,
    )


def _next_repair_model_tier(
    generator_backend: GeneratorBackend,
    packet: Mapping[str, Any],
    *,
    explicit_model: str,
    current_model_tier: str,
) -> tuple[str, str]:
    provider_name = str(getattr(generator_backend, "provider_name", ""))
    requested_tier = str(packet.get("model_tier", "") or "").strip().lower()
    current_tier = str(current_model_tier or "").strip().lower()
    if (
        provider_name == "anthropic"
        and not explicit_model
        and requested_tier == "haiku"
        and current_tier == "haiku"
    ):
        return (
            "sonnet",
            (
                "auto escalated Claude Haiku repair attempt to Sonnet after "
                "local response validation failed"
            ),
        )
    return current_tier, ""


def _generator_metadata_with_model_tier(
    metadata: object,
    *,
    requested_model_tier: str,
    effective_model_tier: str,
    model_tier_escalated: bool,
    model_tier_escalation_reason: str,
) -> dict[str, object]:
    generator_metadata = _jsonable_mapping(metadata)
    generator_metadata.update(
        {
            "requested_model_tier": requested_model_tier,
            "effective_model_tier": effective_model_tier,
            "model_tier_escalated": bool(model_tier_escalated),
            "model_tier_escalation_reason": model_tier_escalation_reason,
        }
    )
    return generator_metadata


def _jsonable_mapping(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    try:
        encoded = json.dumps(dict(value), default=str)
        decoded = json.loads(encoded)
    except Exception:
        return {str(key): str(item) for key, item in value.items()}
    return dict(decoded) if isinstance(decoded, Mapping) else {}


def _repair_guidance_rows(
    validation_errors: Iterable[object],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for error in sorted(set(str(item) for item in validation_errors if str(item)))[
        :20
    ]:
        category, focus, required_action, contract_fields = (
            _repair_guidance_for_error(error)
        )
        rows.append(
            {
                "repair_guidance_row_id": (
                    "formalization_gap_planner_llm_route_planner_repair_guidance:"
                    + stable_hash([error, category, contract_fields])[:20]
                ),
                "error": error,
                "error_category": category,
                "repair_focus": focus,
                "required_action": required_action,
                "contract_fields": list(contract_fields),
                "proof_evidence_status": PROOF_EVIDENCE_STATUS,
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            }
        )
    return tuple(rows)


def _repair_guidance_categories(
    repair_guidance_rows: Iterable[Mapping[str, object]],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                str(row.get("error_category", "")).strip()
                for row in repair_guidance_rows
                if str(row.get("error_category", "")).strip()
            }
        )
    )


def _repair_guidance_for_error(
    error: str,
) -> tuple[str, str, str, tuple[str, ...]]:
    normalized = error.lower()
    if "provider exception" in normalized:
        return (
            "provider_exception",
            "provider call failed before a valid planner response was available",
            "retry only if the provider failure is transient; otherwise record a provider-failure row",
            ("provider_name", "generator_metadata", "generation_errors"),
        )
    if "kernel_verified" in normalized or "proof_evidence_boundary" in normalized:
        return (
            "proof_boundary_violation",
            "response asserted proof evidence beyond planner authority",
            "remove kernel proof claims and state that the route is not theorem proof evidence",
            ("kernel_verified", "proof_evidence_boundary"),
        )
    if "residual" in normalized:
        return (
            "residual_repair_grounding",
            "prover residual interpretation is incomplete or ungrounded",
            "interpret every residual goal with a source-backed repair, search request, or formal gap boundary",
            ("residual_interpretations", "search_requests", "formal_gap_boundary"),
        )
    if (
        "minimal_delta" in normalized
        or "primitive_cost" in normalized
        or "route_cost" in normalized
        or "and_or_cost_graph" in normalized
        or "coverage_bucket" in normalized
        or "cost_policy" in normalized
    ):
        return (
            "minimal_delta_accounting",
            "minimal-delta cost witness or AND/OR route graph is invalid",
            "recompute primitive costs, route options, selected route cost, and minimality rationale from the request cost policy",
            ("minimal_delta_plan", "primitive_costs", "and_or_cost_graph"),
        )
    if (
        "formal_declaration" in normalized
        or "candidate_declaration" in normalized
        or "formal_library" in normalized
        or "formal_realization" in normalized
        or "lean_realization" in normalized
        or "lean-only legacy" in normalized
    ):
        return (
            "formal_library_grounding",
            "formal realization or declaration reuse is not grounded in available library context",
            "use only available formal declaration rows or emit a formal-library search request",
            (
                "formal_realization_dag_nodes",
                "formal_declaration_hits",
                "search_requests",
            ),
        )
    if (
        "source_ref" in normalized
        or "source_refs" in normalized
        or "source_snippet" in normalized
        or "source_search" in normalized
        or "source_search_status" in normalized
        or "source-backed" in normalized
        or "source backed" in normalized
    ):
        return (
            "source_grounding",
            "informal mathematical claim lacks admissible source evidence",
            "cite only available source refs/snippets or emit a literature search request",
            (
                "informal_knowledge_dag_nodes",
                "standalone_route.primitives",
                "source_refs",
                "source_snippets",
                "search_requests",
            ),
        )
    if "search_requests" in normalized or "planner_next_actions" in normalized:
        return (
            "bounded_followup_contract",
            "follow-up work item is missing required bounded-action fields",
            "emit supported literature/formal-library/proof-state/route-revision actions with query, reason, owner, and target primitives",
            ("search_requests", "planner_next_actions"),
        )
    if "alignment" in normalized:
        return (
            "route_alignment",
            "informal and formal DAG nodes are not connected by valid alignment edges",
            "add route_alignment_edges that reference existing informal/formal node ids and explain the alignment",
            (
                "informal_knowledge_dag_nodes",
                "formal_realization_dag_nodes",
                "route_alignment_edges",
            ),
        )
    if "target_prover" in normalized or "theorem identity" in normalized:
        return (
            "target_contract",
            "response drifted from the requested theorem or target prover family",
            "preserve theorem identity and target_prover_family while adding only explicit side-condition notes",
            ("target_prover_family", "standalone_route.theorem_statement"),
        )
    return (
        "schema_contract",
        "response violates the published planner response schema",
        "repair the JSON shape and required fields without inventing evidence",
        ("response_payload",),
    )


def _repair_user_prompt(
    *,
    original_user_prompt: str,
    previous_response_text: str,
    validation_errors: list[str],
    attempt: int,
    repair_guidance_rows: tuple[dict[str, object], ...] | None = None,
) -> str:
    guidance_rows = (
        repair_guidance_rows
        if repair_guidance_rows is not None
        else _repair_guidance_rows(validation_errors)
    )
    payload = {
        "task": (
            "Repair your previous formalization-gap planner response. Return "
            "only one JSON object that satisfies the required output contract."
        ),
        "repair_attempt": attempt,
        "local_validation_errors": sorted(set(validation_errors))[:20],
        "repair_guidance_rows": list(guidance_rows),
        "previous_response_text_excerpt": previous_response_text[:5000],
        "original_request": _extract_json_object_or_text(original_user_prompt),
        "hard_requirements": [
            "Return only JSON.",
            "Use repair_guidance_rows as prioritized local validator feedback; fix the named contract fields instead of deleting evidence or changing the theorem.",
            "Do not claim kernel verification or theorem proof evidence.",
            "Use only source_refs and candidate_declarations/candidate_declaration_rows available in the original request context.",
            "Prefer candidate_declaration_rows so target_prover_family provenance is preserved.",
            "If evidence is missing, emit search_requests instead of inventing facts.",
            "When the original request has resource_request_queue_rows, align search_requests and planner_next_actions to queued resource_request_id/resource_id values.",
            "When the original request has resource_request_playbooks, keep repaired search_requests and planner_next_actions aligned to those playbook operator prompts and acceptance checklists.",
            "Include a complete minimal_delta_plan with selected_primitives, primitive_costs, and and_or_cost_graph.",
            "If a selected primitive needs wrapper, bridge, source-port, definition, or new-theory work, list an actionable work item in the matching minimal_delta_plan bucket; a bare primitive name is not enough.",
        ],
    }
    return json.dumps(payload, indent=2, default=str)


def _extract_json_object_or_text(text: str) -> object:
    try:
        return _extract_json_object(text)
    except Exception:
        return text[:12000]


def llm_route_planner_response_payload_schema(
    *, target_prover_family: str = ""
) -> dict[str, object]:
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
            "new_theory_primitives": string_array,
            "first_principles_primitives": string_array,
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
    schema: dict[str, object] = {
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
                        "target_primitives": string_array,
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
                        "target_primitives": string_array,
                        "resource_request_id": {"type": "string"},
                        "resource_id": {"type": "string"},
                        "resource_contract_ids": string_array,
                        "required_quality_signals": string_array,
                        "quality_gates": string_array,
                        "response_validation_signals": string_array,
                        "stop_conditions": string_array,
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
                        "target_primitives": string_array,
                        "resource_request_id": {"type": "string"},
                        "resource_id": {"type": "string"},
                        "resource_contract_ids": string_array,
                        "required_quality_signals": string_array,
                        "quality_gates": string_array,
                        "response_validation_signals": string_array,
                        "stop_conditions": string_array,
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
    if target_prover_family and _target_prover_key(target_prover_family) != "lean4":
        schema["anyOf"] = [{"required": ["formal_realization_dag_nodes"]}]
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            properties.pop("lean_realization_dag_nodes", None)
    return schema


def llm_route_planner_response_payload_validation_row_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    nonnegative_integer = {"type": "integer", "minimum": 0}
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
            "payload_target_prover_family",
            "payload_target_prover_key",
            "request_context_target_prover_family",
            "request_context_target_prover_key",
            "target_prover_family_consistent",
            "request_context_inventory_present",
            "request_context_inventory_total_rows",
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
            "payload_index": nonnegative_integer,
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
            "payload_target_prover_family": {"type": "string"},
            "payload_target_prover_key": {"type": "string"},
            "request_context_target_prover_family": {"type": "string"},
            "request_context_target_prover_key": {"type": "string"},
            "target_prover_family_consistent": {"type": "boolean"},
            "request_context_inventory_present": {"type": "boolean"},
            "request_context_inventory_total_rows": nonnegative_integer,
            "n_schema_errors": nonnegative_integer,
            "n_request_context_errors": nonnegative_integer,
            "n_errors": nonnegative_integer,
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
            "n_request_context_packets",
            "n_request_contexts_with_context_packet_inventory",
            "n_request_context_inventory_total_rows",
            "n_request_bound_payloads",
            "n_request_bound_payloads_with_context_packet_inventory",
            "n_request_bound_payload_context_inventory_total_rows",
            "n_payloads_with_declared_target_prover_family",
            "n_request_bound_payloads_with_target_prover_family_mismatch",
            "by_payload_target_prover_family",
            "by_request_context_target_prover_family",
            "n_schema_errors",
            "n_request_context_errors",
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
            "response_payload_schema": {
                "type": "object",
                "required": ["$id"],
                "properties": {
                    "$id": {"const": LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID}
                },
            },
            "response_payload_validation_manifest_schema": {
                "type": "object",
                "required": ["$id"],
                "properties": {
                    "$id": {
                        "const": (
                            LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID
                        )
                    }
                },
            },
            "response_payload_validation_row_schema": {
                "type": "object",
                "required": ["$id"],
                "properties": {
                    "$id": {
                        "const": (
                            LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID
                        )
                    }
                },
            },
            "n_payloads": {"type": "integer"},
            "n_valid_payloads": {"type": "integer"},
            "n_invalid_payloads": {"type": "integer"},
            "n_request_context_packets": {"type": "integer"},
            "n_request_contexts_with_context_packet_inventory": {"type": "integer"},
            "n_request_context_inventory_total_rows": {"type": "integer"},
            "n_request_bound_payloads": {"type": "integer"},
            "n_request_bound_payloads_with_context_packet_inventory": {"type": "integer"},
            "n_request_bound_payload_context_inventory_total_rows": {
                "type": "integer"
            },
            "n_payloads_with_declared_target_prover_family": {"type": "integer"},
            "n_request_bound_payloads_with_target_prover_family_mismatch": {
                "type": "integer"
            },
            "by_payload_target_prover_family": {
                "type": "object",
                "additionalProperties": {"type": "integer"},
            },
            "by_request_context_target_prover_family": {
                "type": "object",
                "additionalProperties": {"type": "integer"},
            },
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


def _llm_generation_policy_snapshot(
    *,
    provider_name: str,
    resolved_model: str,
    selected_model_tier: str,
    requested_model_tier: str,
    model_selection_rationale: str,
) -> dict[str, object]:
    claude_selection = dict(ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY)
    return {
        "policy_id": LLM_ROUTE_PLANNER_MODEL_TIER_POLICY_ID,
        "policy_kind": "request_scoped_generator_only_llm_policy",
        "provider_name": provider_name,
        "resolved_model": resolved_model,
        "selected_model_tier": selected_model_tier,
        "requested_model_tier": requested_model_tier,
        "model_selection_rationale": model_selection_rationale,
        "default_mode": LLM_ROUTE_PLANNER_MODEL_TIER_POLICY["default_mode"],
        "auto_tier_rules": list(LLM_ROUTE_PLANNER_MODEL_TIER_POLICY["auto_tier_rules"]),
        "route_planner_provider_names": list(LLM_ROUTE_PLANNER_PROVIDER_NAMES),
        "supported_live_generator_providers": ["anthropic", "openai", "static"],
        "prohibited_generator_providers": ["codex", "codex_exec"],
        "codex_policy": (
            "Codex/Codex exec are not accepted as pure LLM route-planner "
            "providers because this system requires a stable generator-only "
            "API boundary."
        ),
        "claude_model_selection": claude_selection,
        "claude_models_by_tier": dict(claude_selection.get("models_by_tier", {})),
        "claude_cost_split": dict(claude_selection.get("cost_split", {})),
        "claude_model_source_checked_date": str(
            claude_selection.get("source_checked_date", "")
        ),
        "claude_model_id_versioning": str(
            claude_selection.get("model_id_versioning", "")
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _llm_generation_policy_errors(row: Mapping[str, object]) -> list[str]:
    policy = row.get("llm_generation_policy", {})
    if not isinstance(policy, Mapping):
        return ["llm_generation_policy must be object"]
    errors: list[str] = []
    if str(policy.get("policy_id", "")).strip() != LLM_ROUTE_PLANNER_MODEL_TIER_POLICY_ID:
        errors.append(
            "llm_generation_policy.policy_id must equal "
            + LLM_ROUTE_PLANNER_MODEL_TIER_POLICY_ID
        )
    if str(policy.get("provider_name", "")).strip() != str(
        row.get("provider_name", "")
    ).strip():
        errors.append("llm_generation_policy.provider_name must match provider_name")
    if str(policy.get("resolved_model", "")).strip() != str(row.get("model", "")).strip():
        errors.append("llm_generation_policy.resolved_model must match model")
    if str(policy.get("selected_model_tier", "")).strip() != str(
        row.get("model_tier", "")
    ).strip():
        errors.append("llm_generation_policy.selected_model_tier must match model_tier")
    prohibited = set(_str_tuple(policy.get("prohibited_generator_providers", [])))
    if not {"codex", "codex_exec"}.issubset(prohibited):
        errors.append(
            "llm_generation_policy.prohibited_generator_providers must include "
            "codex and codex_exec"
        )
    supported = set(_str_tuple(policy.get("supported_live_generator_providers", [])))
    if supported and {"codex", "codex_exec"}.intersection(supported):
        errors.append(
            "llm_generation_policy.supported_live_generator_providers must not "
            "include codex or codex_exec"
        )
    if policy.get("proof_evidence_status") != PROOF_EVIDENCE_STATUS:
        errors.append("llm_generation_policy.proof_evidence_status mismatch")
    if "not theorem proof evidence" not in str(
        policy.get("proof_evidence_boundary", "")
    ).lower():
        errors.append(
            "llm_generation_policy.proof_evidence_boundary must say not theorem proof evidence"
        )
    errors.extend(_llm_generation_policy_claude_model_source_errors(policy))
    return errors


def _llm_generation_policy_claude_model_source_errors(
    policy: Mapping[str, object],
) -> list[str]:
    expected_models = {
        str(tier): str(model)
        for tier, model in _dict_value(
            ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY,
            "models_by_tier",
        ).items()
    }
    expected_source_date = str(
        ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY.get("source_checked_date", "")
        or ""
    )
    errors: list[str] = []
    policy_models = {
        str(tier): str(model)
        for tier, model in _dict_value(policy, "claude_models_by_tier").items()
    }
    if policy_models != expected_models:
        errors.append(
            "llm_generation_policy.claude_models_by_tier must match current "
            "Claude tier policy"
        )
    selection = _dict_value(policy, "claude_model_selection")
    selection_models = {
        str(tier): str(model)
        for tier, model in _dict_value(selection, "models_by_tier").items()
    }
    if selection_models != expected_models:
        errors.append(
            "llm_generation_policy.claude_model_selection.models_by_tier must "
            "match current Claude tier policy"
        )
    if (
        str(policy.get("claude_model_source_checked_date", "") or "")
        != expected_source_date
    ):
        errors.append(
            "llm_generation_policy.claude_model_source_checked_date must match "
            "current Claude tier policy source_checked_date"
        )
    if (
        str(selection.get("source_checked_date", "") or "")
        != expected_source_date
    ):
        errors.append(
            "llm_generation_policy.claude_model_selection.source_checked_date "
            "must match current Claude tier policy source_checked_date"
        )
    source_evidence = _dict_value(selection, "source_evidence")
    evidence_models = {
        str(tier): str(model)
        for tier, model in _dict_value(
            source_evidence,
            "verified_latest_cost_tier_api_ids",
        ).items()
    }
    if evidence_models != expected_models:
        errors.append(
            "llm_generation_policy.claude_model_selection.source_evidence."
            "verified_latest_cost_tier_api_ids must match current Claude tier policy"
        )
    versioning = str(policy.get("claude_model_id_versioning", "") or "").lower()
    if "pinned snapshot" not in versioning or "not evergreen" not in versioning:
        errors.append(
            "llm_generation_policy.claude_model_id_versioning must record pinned "
            "snapshot and not-evergreen policy"
        )
    return errors


def _request_model_tier_mismatches(
    requests: tuple[dict[str, Any], ...],
) -> list[dict[str, object]]:
    return [
        mismatch
        for request in requests
        for mismatch in [_request_model_tier_mismatch(request)]
        if mismatch
    ]


def _generation_preflight_errors(
    requests: tuple[dict[str, Any], ...],
    request_schema_errors: list[list[str]],
) -> list[dict[str, object]]:
    errors: list[dict[str, object]] = []
    for request, request_errors in zip(requests, request_schema_errors):
        if not request_errors:
            continue
        errors.append(
            {
                "request_id": str(request.get("request_id", "")),
                "route_id": str(request.get("route_id", "")),
                "provider_name": str(request.get("provider_name", "")),
                "model": str(request.get("model", "")),
                "model_tier": str(request.get("model_tier", "")),
                "errors": tuple(sorted(set(request_errors))),
            }
        )
    return errors


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
) -> tuple[str, str, dict[str, object]]:
    requested = _normalize_model_tier(requested_model_tier)
    primitives = _dict_tuple(route.get("primitives", []))
    residual_goals = _str_tuple(context_packet.get("residual_goals", []))
    source_refs = _route_and_primitive_source_refs(route)
    theorem_statement = str(route.get("theorem_statement", ""))
    route_markers = _route_coverage_action_markers(primitives)
    hard_markers = sorted(route_markers & _complex_route_markers())
    base_evidence = _model_tier_decision_evidence_base(
        route=route,
        requested_model_tier=requested,
        primitives=primitives,
        residual_goals=residual_goals,
        source_refs=source_refs,
        theorem_statement=theorem_statement,
        route_markers=route_markers,
        hard_markers=hard_markers,
    )
    if requested in {"haiku", "sonnet", "opus"}:
        evidence = dict(base_evidence)
        evidence.update(
            {
                "selected_model_tier": requested,
                "effective_model_tier": requested,
                "selection_mode": "operator_requested",
                "decision_basis": "operator_override",
                "sonnet_triggers": [],
                "haiku_safety_checks": {},
            }
        )
        return (
            requested,
            f"operator requested Claude {requested} tier for this route-planner run",
            evidence,
        )

    feedback_summary = _dict_value(context_packet, "feedback_loop_summary")
    sonnet_reasons: list[str] = []
    if residual_goals:
        sonnet_reasons.append(f"{len(residual_goals)} prover residual goal(s)")
    realization_coverage = _dict_value(feedback_summary, "realization_coverage")
    if realization_coverage.get("complete") is False:
        sonnet_reasons.append("incomplete realization-coverage witness")
    if realization_coverage.get("cost_hint_baseline_coverage_complete") is False:
        sonnet_reasons.append("omitted cost-hint primitive(s) require route review")
    if bool(feedback_summary.get("replan_required", False)):
        sonnet_reasons.append("feedback-loop summary requires route repair")
    sonnet_reasons.extend(_target_intake_sonnet_reasons(context_packet))
    sonnet_reasons.extend(_seed_route_risk_sonnet_reasons(route, primitives))
    cost_hint_reasons = _minimal_delta_cost_hint_sonnet_reasons(context_packet)
    sonnet_reasons.extend(cost_hint_reasons)
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
        evidence = dict(base_evidence)
        evidence.update(
            {
                "selected_model_tier": "sonnet",
                "effective_model_tier": "sonnet",
                "selection_mode": "auto",
                "decision_basis": "auto_sonnet_triggers",
                "sonnet_triggers": list(sonnet_reasons),
                "haiku_safety_checks": {},
            }
        )
        return (
            "sonnet",
            "auto selected Claude Sonnet because " + "; ".join(sonnet_reasons),
            evidence,
        )
    haiku_checks = {
        "no_residual_goals": not residual_goals,
        "primitive_count_at_most_four": len(primitives) <= 4,
        "source_ref_count_at_most_six": len(source_refs) <= 6,
        "theorem_statement_at_most_600_chars": len(theorem_statement) <= 600,
        "no_complex_coverage_or_action_markers": not hard_markers,
    }
    evidence = dict(base_evidence)
    evidence.update(
        {
            "selected_model_tier": "haiku",
            "effective_model_tier": "haiku",
            "selection_mode": "auto",
            "decision_basis": "auto_haiku_bounded_route",
            "sonnet_triggers": [],
            "haiku_safety_checks": haiku_checks,
        }
    )
    return (
        "haiku",
        (
            "auto selected Claude Haiku for a small route with no residual goals "
            "and only reuse/near/wrapper-level coverage markers"
        ),
        evidence,
    )


def _complex_route_markers() -> set[str]:
    return {
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


def _route_coverage_action_markers(
    primitives: tuple[Mapping[str, Any], ...],
) -> set[str]:
    return {
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


def _model_tier_decision_evidence_base(
    *,
    route: Mapping[str, Any],
    requested_model_tier: str,
    primitives: tuple[Mapping[str, Any], ...],
    residual_goals: tuple[str, ...],
    source_refs: tuple[str, ...],
    theorem_statement: str,
    route_markers: set[str],
    hard_markers: list[str],
) -> dict[str, object]:
    return {
        "evidence_kind": "formalization_gap_planner_llm_route_planner_model_tier_decision",
        "policy_id": LLM_ROUTE_PLANNER_MODEL_TIER_POLICY_ID,
        "requested_model_tier": requested_model_tier,
        "route_id": str(route.get("route_id", "")),
        "display_name": str(route.get("display_name", "")),
        "model_tier_escalated": False,
        "route_signal_counts": {
            "primitive_count": len(primitives),
            "residual_goal_count": len(residual_goals),
            "source_ref_count": len(source_refs),
            "theorem_statement_chars": len(theorem_statement),
            "coverage_action_marker_count": len(route_markers),
            "complex_coverage_action_marker_count": len(hard_markers),
        },
        "coverage_action_markers": sorted(route_markers),
        "complex_coverage_action_markers": list(hard_markers),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _seed_route_risk_sonnet_reasons(
    route: Mapping[str, Any],
    primitives: tuple[Mapping[str, Any], ...],
) -> list[str]:
    reasons: list[str] = []
    uncertainty_flags = _str_tuple(route.get("uncertainty_flags", []))
    if uncertainty_flags:
        reasons.append(
            "seed route uncertainty flag(s): " + ", ".join(uncertainty_flags[:4])
        )
    semantic_alignment_risks = _str_tuple(route.get("semantic_alignment_risks", []))
    if semantic_alignment_risks:
        reasons.append(
            "seed route semantic alignment risk(s): "
            + ", ".join(semantic_alignment_risks[:4])
        )

    boundary_targets: list[str] = []
    if _formal_gap_boundary_is_substantive(
        str(route.get("formal_gap_boundary", "") or "")
    ):
        boundary_targets.append("route")
    for primitive in primitives:
        if not _formal_gap_boundary_is_substantive(
            str(primitive.get("formal_gap_boundary", "") or "")
        ):
            continue
        boundary_targets.append(str(primitive.get("primitive", "") or "primitive"))
    if boundary_targets:
        reasons.append(
            "seed route formal-gap boundary marker(s): "
            + ", ".join(boundary_targets[:6])
        )

    pending_source_search_targets: list[str] = []
    route_source_status = _primitive_key(route.get("source_search_status", ""))
    if _source_search_status_requires_sonnet(route_source_status):
        pending_source_search_targets.append("route")
    for primitive in primitives:
        source_status = _primitive_key(primitive.get("source_search_status", ""))
        if not _source_search_status_requires_sonnet(source_status):
            continue
        pending_source_search_targets.append(
            str(primitive.get("primitive", "") or "primitive")
        )
    if pending_source_search_targets:
        reasons.append(
            "seed route source-search status requires route synthesis: "
            + ", ".join(pending_source_search_targets[:6])
        )

    return reasons


def _source_search_status_requires_sonnet(status: str) -> bool:
    return status in {
        "search_requested",
        "search_pending",
        "source_search_pending",
        "literature_search_pending",
        "formal_boundary_declared",
        "formal_gap_boundary",
    }


def _minimal_delta_cost_hint_sonnet_reasons(
    context_packet: Mapping[str, Any],
) -> list[str]:
    hints = _dict_value(context_packet, "minimal_delta_cost_hints")
    primitive_hints = _dict_tuple(hints.get("primitive_cost_hints", []))
    if not primitive_hints:
        return []
    bridge_cost = _coverage_bucket_base_cost("bridge_needed")
    bridge_cost = 4.0 if bridge_cost is None else bridge_cost
    expensive = [
        str(row.get("primitive", "")).strip()
        for row in primitive_hints
        if _is_nonnegative_number(row.get("minimum_base_cost"))
        and float(row.get("minimum_base_cost", 0) or 0) >= bridge_cost
    ]
    if expensive:
        return [
            "minimal-delta cost hint requires bridge-or-harder work for "
            + ", ".join(expensive[:6])
        ]
    return []


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


def _legacy_context_field_aliases_for_target(
    target_prover_family: object,
) -> dict[str, str]:
    if _target_prover_key(target_prover_family) == "lean4":
        return dict(LLM_ROUTE_PLANNER_LEGACY_CONTEXT_FIELD_ALIASES)
    return {}


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


def _nonnegative_int(value: object, *, default: int = 0) -> int:
    try:
        parsed = int(value or 0)
    except (TypeError, ValueError):
        return default
    return max(0, parsed)


def _repair_attempt_ledger_rows(
    *,
    request: Mapping[str, Any],
    response: Mapping[str, Any],
    response_contract_ok: bool,
    acceptance_status: str,
) -> tuple[dict[str, object], ...]:
    history = _dict_tuple(response.get("repair_error_history", []))
    if not history:
        return tuple()
    request_id = str(response.get("request_id") or request.get("request_id") or "")
    route_id = str(response.get("route_id") or request.get("route_id") or "")
    provider_name = str(
        response.get("provider_name") or request.get("provider_name") or ""
    )
    model = str(response.get("model") or request.get("model") or "")
    requested_model_tier = str(request.get("model_tier", ""))
    model_tier = _effective_response_model_tier(request, response)
    generator_metadata = _dict_value(response, "generator_metadata")
    model_tier_escalated = bool(
        response.get("model_tier_escalated")
        or generator_metadata.get("model_tier_escalated")
    )
    model_tier_escalation_reason = str(
        response.get("model_tier_escalation_reason")
        or generator_metadata.get("model_tier_escalation_reason")
        or ""
    )
    target_prover_family = str(request.get("target_prover_family", ""))
    final_repair_attempts = _nonnegative_int(response.get("repair_attempts", 0))
    provider_failure = bool(response.get("provider_failure", False))
    rows: list[dict[str, object]] = []
    for ordinal, item in enumerate(history):
        failed_attempt_index = _nonnegative_int(
            item.get("attempt", ordinal),
            default=ordinal,
        )
        errors = _str_tuple(item.get("errors", []))
        next_attempt = item.get("next_repair_attempt", "")
        if next_attempt == "":
            next_attempt_index: int | str = ""
        else:
            next_attempt_index = _nonnegative_int(next_attempt)
        row = {
            "ledger_kind": REPAIR_ATTEMPT_LEDGER_KIND,
            "repair_attempt_row_id": (
                "formalization_gap_planner_llm_route_planner_repair_attempt:"
                + stable_hash(
                    [
                        request_id,
                        route_id,
                        provider_name,
                        model,
                        failed_attempt_index,
                        errors,
                    ]
                )[:20]
            ),
            "request_id": request_id,
            "route_id": route_id,
            "provider_name": provider_name,
            "model": model,
            "model_tier": model_tier,
            "requested_model_tier": requested_model_tier,
            "model_tier_escalated": model_tier_escalated,
            "model_tier_escalation_reason": model_tier_escalation_reason,
            "target_prover_family": target_prover_family,
            "failed_attempt_index": failed_attempt_index,
            "next_repair_attempt": next_attempt_index,
            "failed_attempt_model": str(item.get("model", "")),
            "failed_attempt_model_tier": str(item.get("model_tier", "")),
            "next_repair_model_tier": str(
                item.get("next_repair_model_tier", "")
            ),
            "repair_prompt_fingerprint": str(
                item.get("repair_prompt_fingerprint", "")
            ),
            "repair_guidance_categories": list(
                _str_tuple(item.get("repair_guidance_categories", []))
            ),
            "repair_guidance_fingerprint": str(
                item.get("repair_guidance_fingerprint", "")
            ),
            "error_count": len(errors),
            "errors": list(errors),
            "error_fingerprint": stable_hash(errors),
            "final_repair_attempts": final_repair_attempts,
            "final_response_contract_ok": response_contract_ok,
            "final_acceptance_status": acceptance_status,
            "provider_failure": provider_failure,
            "proof_evidence_status": PROOF_EVIDENCE_STATUS,
            "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        }
        rows.append(row)
    return tuple(rows)


def _effective_response_model_tier(
    request: Mapping[str, Any],
    response: Mapping[str, Any],
) -> str:
    generator_metadata = _dict_value(response, "generator_metadata")
    for value in (
        response.get("model_tier", ""),
        response.get("effective_model_tier", ""),
        generator_metadata.get("effective_model_tier", ""),
        request.get("model_tier", ""),
    ):
        tier = str(value or "").strip().lower()
        if tier:
            return tier
    return ""


def _effective_model_selection_rationale(
    request: Mapping[str, Any],
    response: Mapping[str, Any],
) -> str:
    rationale = str(request.get("model_selection_rationale", ""))
    generator_metadata = _dict_value(response, "generator_metadata")
    escalated = bool(
        response.get("model_tier_escalated")
        or generator_metadata.get("model_tier_escalated")
    )
    reason = str(
        response.get("model_tier_escalation_reason")
        or generator_metadata.get("model_tier_escalation_reason")
        or ""
    ).strip()
    if escalated and reason:
        return (rationale + "; " if rationale else "") + reason
    return rationale


def _effective_model_tier_decision_evidence(
    request: Mapping[str, Any],
    response: Mapping[str, Any],
    *,
    effective_model_tier: str,
) -> dict[str, object]:
    evidence = dict(_dict_value(request, "model_tier_decision_evidence"))
    if not evidence:
        return {}
    generator_metadata = _dict_value(response, "generator_metadata")
    escalated = bool(
        response.get("model_tier_escalated")
        or generator_metadata.get("model_tier_escalated")
    )
    reason = str(
        response.get("model_tier_escalation_reason")
        or generator_metadata.get("model_tier_escalation_reason")
        or ""
    ).strip()
    evidence["effective_model_tier"] = str(effective_model_tier or "").strip().lower()
    evidence["model_tier_escalated"] = escalated
    if escalated and reason:
        evidence["model_tier_escalation_reason"] = reason
    return evidence


def _model_tier_decision_evidence_errors(
    evidence: Mapping[str, object],
    *,
    selected_model_tier: str,
    effective_model_tier: str,
    allow_repair_escalation: bool,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(evidence, Mapping) or not evidence:
        return ["model_tier_decision_evidence missing"]
    prefix = "model_tier_decision_evidence"
    if str(evidence.get("evidence_kind", "")).strip() != (
        "formalization_gap_planner_llm_route_planner_model_tier_decision"
    ):
        errors.append(f"{prefix}.evidence_kind mismatch")
    if str(evidence.get("policy_id", "")).strip() != LLM_ROUTE_PLANNER_MODEL_TIER_POLICY_ID:
        errors.append(f"{prefix}.policy_id mismatch")
    if evidence.get("proof_evidence_status") != PROOF_EVIDENCE_STATUS:
        errors.append(f"{prefix}.proof_evidence_status mismatch")
    if "not theorem proof evidence" not in str(
        evidence.get("proof_evidence_boundary", "")
    ).lower():
        errors.append(f"{prefix}.proof_evidence_boundary must say not theorem proof evidence")

    requested = str(evidence.get("requested_model_tier", "")).strip().lower()
    selected = str(evidence.get("selected_model_tier", "")).strip().lower()
    effective = str(evidence.get("effective_model_tier", "")).strip().lower()
    expected_selected = str(selected_model_tier or "").strip().lower()
    expected_effective = str(effective_model_tier or "").strip().lower()
    if requested not in LLM_ROUTE_PLANNER_MODEL_TIERS:
        errors.append(f"{prefix}.requested_model_tier must be a planner tier")
    if selected not in {"haiku", "sonnet", "opus"}:
        errors.append(f"{prefix}.selected_model_tier must be haiku, sonnet, or opus")
    if selected and expected_selected and selected != expected_selected:
        if not (
            allow_repair_escalation
            and selected == "haiku"
            and expected_selected == "sonnet"
            and bool(evidence.get("model_tier_escalated", False))
        ):
            errors.append(f"{prefix}.selected_model_tier must match selected tier")
    if effective and expected_effective and effective != expected_effective:
        errors.append(f"{prefix}.effective_model_tier must match effective tier")
    if effective and effective not in {"haiku", "sonnet", "opus"}:
        errors.append(f"{prefix}.effective_model_tier must be haiku, sonnet, or opus")

    decision_basis = str(evidence.get("decision_basis", "")).strip()
    if decision_basis not in {
        "operator_override",
        "auto_sonnet_triggers",
        "auto_haiku_bounded_route",
    }:
        errors.append(f"{prefix}.decision_basis unsupported")
    selection_mode = str(evidence.get("selection_mode", "")).strip()
    if decision_basis == "operator_override" and selection_mode != "operator_requested":
        errors.append(f"{prefix}.selection_mode must be operator_requested")
    if decision_basis.startswith("auto_") and selection_mode != "auto":
        errors.append(f"{prefix}.selection_mode must be auto")

    sonnet_triggers = _str_tuple(evidence.get("sonnet_triggers", []))
    if decision_basis == "auto_sonnet_triggers":
        if selected != "sonnet":
            errors.append(f"{prefix}.auto_sonnet_triggers must select sonnet")
        if not sonnet_triggers:
            errors.append(f"{prefix}.sonnet_triggers required for auto Sonnet")
    if decision_basis == "auto_haiku_bounded_route":
        if selected != "haiku":
            errors.append(f"{prefix}.auto_haiku_bounded_route must select haiku")
        checks = _dict_value(evidence, "haiku_safety_checks")
        if not checks:
            errors.append(f"{prefix}.haiku_safety_checks required for auto Haiku")
        failed_checks = sorted(
            str(key)
            for key, value in checks.items()
            if value is not True
        )
        if failed_checks:
            errors.append(
                f"{prefix}.haiku_safety_checks failed: "
                + ", ".join(failed_checks)
            )
        if sonnet_triggers:
            errors.append(f"{prefix}.auto Haiku must not carry sonnet_triggers")
    if bool(evidence.get("model_tier_escalated", False)):
        if not allow_repair_escalation:
            errors.append(f"{prefix}.model_tier_escalated not allowed in request")
        if selected != "haiku" or effective != "sonnet":
            errors.append(f"{prefix}.model_tier_escalated must be haiku-to-sonnet")
    return errors


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
    effective_model_tier = _effective_response_model_tier(request, response or {})
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
                    "model_tier": effective_model_tier,
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
    elif request_errors:
        acceptance_status = "REJECTED_LLM_ROUTE_PLANNER_REQUEST_CONTRACT"
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
    elif _str_tuple(payload.get("semantic_alignment_risks", [])):
        acceptance_status = "ACCEPTED_WITH_SEMANTIC_ALIGNMENT_RISKS"
    elif _dict_tuple(payload.get("residual_interpretations", [])):
        acceptance_status = "ACCEPTED_WITH_RESIDUAL_REPAIR"
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
    context_packet = _dict_value(request, "context_packet")
    feedback_summary = _dict_value(context_packet, "feedback_loop_summary")
    context_packet_inventory = _dict_value(
        context_packet,
        "context_packet_inventory",
    )
    quality_control_obligations = _quality_control_obligation_summary(context_packet)
    source_grounding_obligations = _source_grounding_obligation_summary(
        context_packet
    )
    realization_coverage_witness = _realization_coverage_witness(
        request=request,
        minimal_delta=minimal_delta_plan,
        standalone_route=standalone_route,
        formal_nodes=formal_nodes,
        alignment_edges=route_alignment_edges,
    )
    route_adoption_status, route_adoption_blockers = _route_adoption_readiness(
        request_errors=tuple(request_errors),
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
        feedback_summary=feedback_summary,
        realization_coverage_witness=realization_coverage_witness,
        omitted_cost_hint_primitives=_omitted_cost_hint_primitives(
            minimal_delta_plan,
            request,
        ),
        formal_gap_boundary_obligations=_formal_gap_boundary_obligations(
            payload,
            request,
        ),
        quality_control_obligations_pending=bool(
            quality_control_obligations.get("pending", False)
        ),
        source_grounding_obligations_pending=bool(
            source_grounding_obligations.get("pending", False)
        ),
    )
    repair_attempt_ledger = _repair_attempt_ledger_rows(
        request=request,
        response=response or {},
        response_contract_ok=response_contract_ok,
        acceptance_status=acceptance_status,
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
        model_tier=effective_model_tier,
        model_selection_rationale=_effective_model_selection_rationale(
            request,
            response or {},
        ),
        model_tier_decision_evidence=_effective_model_tier_decision_evidence(
            request,
            response or {},
            effective_model_tier=effective_model_tier,
        ),
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
        realization_coverage_witness=realization_coverage_witness,
        quality_control_obligations=dict(quality_control_obligations),
        feedback_loop_summary=dict(feedback_summary),
        context_packet_inventory=dict(context_packet_inventory),
        raw_response_text=raw_text,
        generator_metadata=_jsonable_mapping(
            (response or {}).get("generator_metadata", {})
        ),
        provider_failure=provider_failure,
        repair_attempts=max(0, int((response or {}).get("repair_attempts", 0) or 0)),
        repair_error_history=_dict_tuple(
            (response or {}).get("repair_error_history", [])
        ),
        repair_attempt_ledger=repair_attempt_ledger,
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
    request_errors: tuple[str, ...] = (),
    response_present: bool,
    provider_failure: bool,
    response_contract_ok: bool,
    search_requests: tuple[dict[str, object], ...],
    planner_next_actions: tuple[dict[str, object], ...],
    uncertainty_flags: tuple[str, ...],
    semantic_alignment_risks: tuple[str, ...],
    residual_interpretations: tuple[dict[str, object], ...],
    feedback_summary: Mapping[str, object],
    realization_coverage_witness: Mapping[str, object],
    omitted_cost_hint_primitives: tuple[str, ...],
    formal_gap_boundary_obligations: tuple[str, ...],
    quality_control_obligations_pending: bool,
    source_grounding_obligations_pending: bool = False,
) -> tuple[str, tuple[str, ...]]:
    if (
        request_errors
        or provider_failure
        or (response_present and not response_contract_ok)
    ):
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
    if (
        realization_coverage.get("complete") is False
        or realization_coverage_witness.get("realization_coverage_complete") is False
    ):
        blockers.append(ROUTE_ADOPTION_BLOCKER_REALIZATION_COVERAGE)
    if omitted_cost_hint_primitives:
        blockers.append(ROUTE_ADOPTION_BLOCKER_OMITTED_COST_HINT_PRIMITIVES)
    if formal_gap_boundary_obligations:
        blockers.append(ROUTE_ADOPTION_BLOCKER_FORMAL_GAP_BOUNDARIES)
    if source_grounding_obligations_pending:
        blockers.append(ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING)
    if quality_control_obligations_pending:
        blockers.append(ROUTE_ADOPTION_BLOCKER_QUALITY_CONTROLS)
    blockers = list(dict.fromkeys(blockers))
    if blockers:
        return (ROUTE_ADOPTION_PENDING_STATUS, tuple(blockers))
    return (ROUTE_ADOPTION_READY_STATUS, tuple())


def _quality_control_obligations_pending(
    context_packet: Mapping[str, Any],
) -> bool:
    summary = _quality_control_obligation_summary(context_packet)
    return bool(summary.get("pending", False))


def _quality_control_obligation_summary(
    context_packet: Mapping[str, Any],
    *,
    recommended_next_actions: tuple[dict[str, object], ...] = (),
    include_feedback_summary: bool = True,
) -> dict[str, object]:
    obligations = _quality_control_obligations_for_context(
        context_packet,
        recommended_next_actions=recommended_next_actions,
        include_feedback_summary=include_feedback_summary,
    )
    discharged = _quality_control_discharges_for_context(context_packet)
    pending = _quality_control_difference(obligations, discharged)
    present = any(obligations.values())
    return {
        "present": present,
        "pending": any(pending.values()),
        "discharged": present and not any(pending.values()),
        "quality_controls": _quality_controls_to_lists(obligations),
        "discharged_quality_controls": _quality_controls_to_lists(discharged),
        "pending_quality_controls": _quality_controls_to_lists(pending),
        "pending_fields": sorted(
            field_name for field_name, values in pending.items() if values
        ),
        "n_pending_values": sum(len(values) for values in pending.values()),
    }


def _quality_control_obligations_for_context(
    context_packet: Mapping[str, Any],
    *,
    recommended_next_actions: tuple[dict[str, object], ...],
    include_feedback_summary: bool,
) -> dict[str, tuple[str, ...]]:
    current_route = _dict_value(context_packet, "current_route")
    replan_metadata = _dict_value(context_packet, "replan_metadata")
    rows: list[Mapping[str, Any]] = [
        current_route,
        _dict_value(current_route, "quality_controls"),
        replan_metadata,
        _dict_value(replan_metadata, "quality_controls"),
    ]
    rows.extend(_dict_tuple(context_packet.get("resource_request_queue_rows", [])))
    rows.extend(_dict_tuple(context_packet.get("interactive_decision_policy_rows", [])))
    rows.extend(recommended_next_actions)
    if include_feedback_summary:
        feedback_summary = _dict_value(context_packet, "feedback_loop_summary")
        rows.extend(_dict_tuple(feedback_summary.get("recommended_next_actions", [])))
        prior_replan_metadata = _dict_value(
            feedback_summary,
            "prior_replan_metadata",
        )
        rows.extend(
            (
                prior_replan_metadata,
                _dict_value(prior_replan_metadata, "quality_controls"),
            )
        )
    return _merge_quality_control_values(
        *(_quality_control_values_for_row(row) for row in rows)
    )


def _quality_control_discharges_for_context(
    context_packet: Mapping[str, Any],
) -> dict[str, tuple[str, ...]]:
    rows: list[Mapping[str, Any]] = []
    rows.extend(
        row
        for row in _dict_tuple(context_packet.get("resource_response_ledger_rows", []))
        if _resource_response_row_is_admissible_feedback(row)
    )
    rows.extend(
        row
        for row in _dict_tuple(context_packet.get("refinement_evidence_rows", []))
        if _refinement_evidence_row_is_admissible_feedback(row)
    )
    return _merge_quality_control_values(
        *(_quality_control_values_for_row(row) for row in rows)
    )


def _quality_control_values_for_row(
    row: Mapping[str, Any],
) -> dict[str, tuple[str, ...]]:
    nested = row.get("quality_controls", {})
    return _merge_quality_control_values(
        _direct_quality_control_values(row),
        _direct_quality_control_values(nested if isinstance(nested, Mapping) else {}),
    )


def _direct_quality_control_values(
    row: Mapping[str, Any],
) -> dict[str, tuple[str, ...]]:
    controls: dict[str, tuple[str, ...]] = {}
    for field_name in QUALITY_CONTROL_FIELDS:
        values = _str_tuple(row.get(field_name, []))
        if values:
            controls[field_name] = tuple(dict.fromkeys(values))
    return controls


def _merge_quality_control_values(
    *controls: Mapping[str, tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    merged: dict[str, tuple[str, ...]] = {}
    for field_name in QUALITY_CONTROL_FIELDS:
        values: list[str] = []
        for payload in controls:
            values.extend(_str_tuple(payload.get(field_name, [])))
        unique_values = tuple(dict.fromkeys(value for value in values if value))
        if unique_values:
            merged[field_name] = unique_values
    return merged


def _quality_control_difference(
    obligations: Mapping[str, tuple[str, ...]],
    discharged: Mapping[str, tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    pending: dict[str, tuple[str, ...]] = {}
    for field_name in QUALITY_CONTROL_FIELDS:
        discharged_values = set(_str_tuple(discharged.get(field_name, [])))
        missing = tuple(
            value
            for value in _str_tuple(obligations.get(field_name, []))
            if value not in discharged_values
        )
        if missing:
            pending[field_name] = missing
    return pending


def _quality_controls_to_lists(
    controls: Mapping[str, tuple[str, ...]],
) -> dict[str, list[str]]:
    return {
        field_name: list(_str_tuple(controls.get(field_name, [])))
        for field_name in QUALITY_CONTROL_FIELDS
        if _str_tuple(controls.get(field_name, []))
    }


def _quality_control_value_count(controls: Mapping[str, Any]) -> int:
    return sum(len(_str_tuple(values)) for values in controls.values())


def _response_contract_errors(
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if bool(payload.get("kernel_verified", False)):
        errors.append("response_payload cannot claim kernel_verified=true")
    errors.extend(_kernel_proof_claim_errors(payload, location="response_payload"))
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
    errors.extend(_response_source_search_status_errors(payload))
    errors.extend(_response_formal_gap_boundary_errors(payload, request))
    errors.extend(_response_source_ref_grounding_errors(payload, request))
    errors.extend(_response_target_theorem_identity_errors(payload, request))
    errors.extend(_response_target_prover_consistency_errors(payload, request))
    errors.extend(_response_search_request_contract_errors(payload))
    errors.extend(_response_search_request_primitive_grounding_errors(payload, request))
    errors.extend(_response_planner_next_action_contract_errors(payload))
    errors.extend(_response_planner_next_action_primitive_grounding_errors(payload, request))
    errors.extend(_response_source_search_obligation_errors(payload))
    errors.extend(_response_source_snippet_provenance_errors(payload, request))
    errors.extend(_response_source_snippet_primitive_support_errors(payload, request))
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
    errors.extend(_minimal_delta_request_hint_errors(payload, request))
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


def _kernel_proof_claim_errors(value: Any, *, location: str) -> list[str]:
    errors: list[str] = []
    for path, key, item in _kernel_proof_claim_paths(value, location=location):
        errors.append(
            f"{path}.{key} cannot claim kernel/proved theorem evidence: {item}"
        )
    return errors


def _kernel_proof_claim_paths(
    value: Any,
    *,
    location: str,
) -> tuple[tuple[str, str, object], ...]:
    claims: list[tuple[str, str, object]] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            key_normalized = key_text.lower()
            child_location = f"{location}.{key_text}"
            if (
                key_normalized
                in {
                    "kernel_verified",
                    "full_frontier_theorem_proved",
                    "theorem_proved",
                }
                and item is True
            ):
                claims.append((location, key_text, item))
            if key_normalized in {"proof_evidence_status", "claim_status"}:
                item_text = str(item)
                item_upper = item_text.upper()
                if (
                    ("KERNEL_VERIFIED" in item_upper or "PROVED" in item_upper)
                    and "NOT_PROOF_EVIDENCE" not in item_upper
                ):
                    claims.append((location, key_text, item))
            claims.extend(_kernel_proof_claim_paths(item, location=child_location))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            claims.extend(
                _kernel_proof_claim_paths(item, location=f"{location}[{index}]")
            )
    return tuple(claims)


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


def _nonempty_legacy_declaration_hit_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, (list, tuple, set)):
        return any(_nonempty_legacy_declaration_hit_value(item) for item in value)
    return bool(value)


def _response_payload_lean_legacy_declaration_field_errors(
    payload: Mapping[str, Any],
) -> list[str]:
    target_prover_key = _target_prover_key(
        _declared_payload_target_prover_family(payload)
    )
    if not target_prover_key or target_prover_key == "lean4":
        return []

    errors: list[str] = []

    def check_container(location: str, container: Mapping[str, Any]) -> None:
        if _nonempty_legacy_declaration_hit_value(
            container.get("lean_declaration_hits")
        ):
            errors.append(
                f"{location}.lean_declaration_hits is a Lean-only legacy "
                "declaration field; non-Lean target prover responses must use "
                "formal_declaration_hits or candidate_declaration_rows"
            )

    check_container("response_payload", payload)
    route = _dict_value(payload, "standalone_route")
    check_container("standalone_route", route)
    for index, node in enumerate(
        _dict_tuple(payload.get("formal_realization_dag_nodes", []))
    ):
        check_container(f"formal_realization_dag_nodes[{index}]", node)
    for index, primitive in enumerate(_dict_tuple(route.get("primitives", []))):
        check_container(f"standalone_route.primitives[{index}]", primitive)
    return errors


def _response_payload_target_prover_internal_consistency_errors(
    payload: Mapping[str, Any],
) -> list[str]:
    declared_target = _declared_payload_target_prover_family(payload)
    expected = _target_prover_key(declared_target)
    if not expected:
        return []
    checks: list[tuple[str, object]] = [
        ("response_payload.target_prover_family", payload.get("target_prover_family", "")),
        ("response_payload.target_prover", payload.get("target_prover", "")),
    ]
    route = _dict_value(payload, "standalone_route")
    checks.extend(
        [
            ("standalone_route.target_prover_family", route.get("target_prover_family", "")),
            ("standalone_route.target_prover", route.get("target_prover", "")),
        ]
    )
    metadata = _dict_value(route, "replan_metadata")
    checks.extend(
        [
            (
                "standalone_route.replan_metadata.target_prover_family",
                metadata.get("target_prover_family", ""),
            ),
            (
                "standalone_route.replan_metadata.target_prover",
                metadata.get("target_prover", ""),
            ),
        ]
    )
    for index, node in enumerate(
        _formal_realization_nodes_from_payload(
            payload,
            target_prover_family=declared_target,
        )
    ):
        checks.extend(
            [
                (
                    f"formal_realization_dag_nodes[{index}].target_prover_family",
                    node.get("target_prover_family", ""),
                ),
                (
                    f"formal_realization_dag_nodes[{index}].target_prover",
                    node.get("target_prover", ""),
                ),
            ]
        )
    for location, row in _response_candidate_declaration_row_locations(
        payload,
        target_prover_family=declared_target,
    ):
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
                f"{location} {value} does not match declared payload "
                f"target_prover_family {declared_target}"
            )
    return errors


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
    route_option_primitives_by_id: dict[str, set[str]] = {}
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
        if option_id:
            route_option_primitives_by_id[option_id] = option_primitives
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
            route_option_primitives_by_id=route_option_primitives_by_id,
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
    route_option_primitives_by_id: Mapping[str, set[str]],
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
        require_primitives = {
            _primitive_key(primitive)
            for primitive in requires
            if _primitive_key(primitive)
        }
        if option_id in route_option_primitives_by_id:
            expected_primitives = route_option_primitives_by_id[option_id]
            if require_primitives != expected_primitives:
                errors.append(
                    f"{prefix}.and_edges[{index}].requires must match "
                    "route_options selected_primitives for route_option_id "
                    f"{option_id}"
                )
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
    if _formal_gap_boundary_is_substantive(
        str(interpretation.get("formal_gap_boundary", "") or "")
    ):
        return True
    return False


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
    errors.extend(
        _response_existing_coverage_declaration_support_errors(payload, request)
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


def _response_existing_coverage_declaration_support_errors(
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[str]:
    support_sources = _available_formal_declaration_existing_support_for_request(
        request
    )
    if not support_sources:
        return []
    primitive_support = _available_formal_declaration_primitive_support_for_request(
        request
    )
    primitive_non_support = (
        _available_formal_declaration_primitive_non_support_for_request(request)
    )

    errors: list[str] = []
    target_prover_family = str(request.get("target_prover_family", ""))
    for index, node in enumerate(
        _formal_realization_nodes_from_payload(
            payload,
            target_prover_family=target_prover_family,
        )
    ):
        if not _formal_node_claims_existing_library(node):
            continue
        inherited_target = str(
            node.get("target_prover_family", "")
            or node.get("target_prover", "")
            or payload.get("target_prover_family", "")
            or target_prover_family
        )
        unsupported = _candidate_declarations_without_existing_support(
            node,
            support_sources=support_sources,
            primitive_support=primitive_support,
            primitive_non_support=primitive_non_support,
            primitive=str(node.get("primitive", "")),
            inherited_target_prover_family=inherited_target,
        )
        if unsupported:
            errors.append(
                "formal_realization_dag_nodes"
                f"[{index}] existing-library coverage uses provisional or "
                "unsupported formal declaration evidence: "
                + "; ".join(unsupported[:8])
            )

    route = _standalone_route_from_payload(
        payload,
        target_prover_family=target_prover_family,
    )
    for index, primitive in enumerate(_dict_tuple(route.get("primitives", []))):
        if not _route_primitive_claims_existing_library(primitive):
            continue
        inherited_target = str(
            primitive.get("target_prover_family", "")
            or primitive.get("target_prover", "")
            or route.get("target_prover_family", "")
            or route.get("target_prover", "")
            or payload.get("target_prover_family", "")
            or target_prover_family
        )
        unsupported = _candidate_declarations_without_existing_support(
            primitive,
            support_sources=support_sources,
            primitive_support=primitive_support,
            primitive_non_support=primitive_non_support,
            primitive=str(primitive.get("primitive", "")),
            inherited_target_prover_family=inherited_target,
        )
        if unsupported:
            errors.append(
                "standalone_route.primitives"
                f"[{index}] existing-library coverage uses provisional or "
                "unsupported formal declaration evidence: "
                + "; ".join(unsupported[:8])
            )
    return errors


def _candidate_declarations_without_existing_support(
    node: Mapping[str, Any],
    *,
    support_sources: Mapping[tuple[str, str], set[str]],
    primitive_support: Mapping[tuple[str, str], set[str]],
    primitive_non_support: Mapping[tuple[str, str], set[str]],
    primitive: str,
    inherited_target_prover_family: str,
) -> list[str]:
    unsupported: list[str] = []
    primitive_key = _primitive_key(primitive)
    for row in _node_candidate_declaration_rows(
        node,
        inherited_target_prover_family=inherited_target_prover_family,
    ):
        declaration = str(row.get("declaration", "")).strip()
        declaration_key = _formal_declaration_key(declaration)
        target_key = _target_prover_key(
            row.get("target_prover_family", "") or inherited_target_prover_family
        )
        if not declaration_key:
            continue
        source_fields = support_sources.get((declaration_key, target_key), set())
        if not source_fields and target_key:
            source_fields = support_sources.get((declaration_key, ""), set())
        if not any(
            _formal_declaration_source_field_supports_existing_coverage(source_field)
            for source_field in source_fields
        ):
            source_preview = str(row.get("source_field", "")).strip()
            unsupported.append(
                f"{declaration}@{row.get('target_prover_family', '')}"
                + (f" source_field={source_preview}" if source_preview else "")
            )
            continue
        supported_primitives = primitive_support.get((declaration_key, target_key), set())
        if not supported_primitives and target_key:
            supported_primitives = primitive_support.get((declaration_key, ""), set())
        if (
            primitive_key
            and supported_primitives
            and primitive_key not in supported_primitives
        ):
            unsupported.append(
                f"{declaration}@{row.get('target_prover_family', '')} "
                "has primitive-scoped formal declaration evidence for "
                + ", ".join(sorted(supported_primitives)[:8])
                + f", not {primitive_key}"
            )
            continue
        unsupported_primitives = primitive_non_support.get(
            (declaration_key, target_key), set()
        )
        if not unsupported_primitives and target_key:
            unsupported_primitives = primitive_non_support.get((declaration_key, ""), set())
        if primitive_key and primitive_key in unsupported_primitives:
            unsupported.append(
                f"{declaration}@{row.get('target_prover_family', '')} "
                "has formal declaration evidence marked unsupported for "
                f"{primitive_key}"
            )
    return unsupported


def _node_candidate_declaration_rows(
    node: Mapping[str, Any],
    *,
    inherited_target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    rows = list(
        _candidate_declaration_rows(
            node.get("candidate_declaration_rows", []),
            inherited_target_prover_family=inherited_target_prover_family,
            fallback_source_field="candidate_declaration_rows",
        )
    )
    rows.extend(
        {
            "declaration": declaration,
            "target_prover_family": inherited_target_prover_family,
            "source_field": "candidate_declarations",
        }
        for declaration in _formal_declaration_values(
            node.get("candidate_declarations", [])
        )
    )
    compact: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        key = (
            _formal_declaration_key(row.get("declaration", "")),
            _target_prover_key(row.get("target_prover_family", "")),
            _formal_declaration_source_field_key(row.get("source_field", "")),
        )
        if not key[0] or key in seen:
            continue
        seen.add(key)
        compact.append(row)
    return tuple(compact)


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
    if _formal_gap_boundary_is_substantive(
        str(node.get("formal_gap_boundary", "") or "")
    ):
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
    primitive_support: dict[tuple[str, str], set[str]] = {}
    primitive_non_support: dict[tuple[str, str], set[str]] = {}
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
    _collect_formal_declaration_primitive_support(
        route,
        primitive_support,
        inherited_target_prover_family=route_target,
        inherited_primitives=tuple(),
    )
    _collect_formal_declaration_primitive_support(
        context_packet,
        primitive_support,
        inherited_target_prover_family=target_prover_family,
        inherited_primitives=tuple(),
    )
    _collect_formal_declaration_primitive_non_support(
        route,
        primitive_non_support,
        inherited_target_prover_family=route_target,
    )
    _collect_formal_declaration_primitive_non_support(
        context_packet,
        primitive_non_support,
        inherited_target_prover_family=target_prover_family,
    )
    compact: list[dict[str, object]] = []
    by_key: dict[tuple[str, str], dict[str, object]] = {}
    source_fields_by_key: dict[tuple[str, str], list[str]] = {}
    for row in rows:
        declaration = str(row.get("declaration", "")).strip()
        if not declaration:
            continue
        row_target = str(row.get("target_prover_family", "")).strip()
        key = (_formal_declaration_key(declaration), _target_prover_key(row_target))
        source_field = str(row.get("source_field", "")).strip()
        source_fields = source_fields_by_key.setdefault(key, [])
        if (
            source_field
            and _formal_declaration_source_field_rank(source_field) > 0
            and source_field not in source_fields
        ):
            source_fields.append(source_field)
        current = by_key.get(key)
        if current is not None:
            if _formal_declaration_source_field_rank(
                source_field
            ) > _formal_declaration_source_field_rank(
                current.get("source_field", "")
            ):
                current["source_field"] = source_field
            continue
        current = {
            "declaration": declaration,
            "target_prover_family": row_target,
            "source_field": source_field,
        }
        by_key[key] = current
        compact.append(current)
    for row in compact:
        key = (
            _formal_declaration_key(row.get("declaration", "")),
            _target_prover_key(row.get("target_prover_family", "")),
        )
        source_fields = source_fields_by_key.get(key, [])
        if len(source_fields) > 1:
            row["source_fields"] = list(source_fields)
        scoped_primitives = sorted(primitive_support.get(key, set()))
        unsupported_primitives = sorted(primitive_non_support.get(key, set()))
        if scoped_primitives:
            row["target_primitives"] = sorted(
                set(scoped_primitives).union(unsupported_primitives)
            )
            row["supported_target_primitives"] = scoped_primitives
        elif unsupported_primitives:
            row["target_primitives"] = unsupported_primitives
        if unsupported_primitives:
            row["unsupported_target_primitives"] = unsupported_primitives
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
        source_fields = set(_formal_declaration_row_source_fields(row))
        source_fields.add("available_formal_declaration_rows")
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


def _available_formal_declaration_existing_support_for_request(
    request: Mapping[str, Any],
) -> dict[tuple[str, str], set[str]]:
    context_packet = _dict_value(request, "context_packet")
    structured_rows = _dict_tuple(
        context_packet.get("available_formal_declaration_rows", [])
    )
    support: dict[tuple[str, str], set[str]] = {}
    target_prover_family = str(request.get("target_prover_family", ""))
    for row in _target_compatible_formal_declaration_rows(
        structured_rows,
        target_prover_family=target_prover_family,
    ):
        declaration_key = _formal_declaration_key(row.get("declaration", ""))
        target_key = _target_prover_key(
            row.get("target_prover_family", "") or target_prover_family
        )
        source_fields = _formal_declaration_row_source_fields(row)
        if declaration_key and source_fields:
            support.setdefault((declaration_key, target_key), set()).update(
                source_fields
            )

    if structured_rows:
        return support

    for declaration in _str_tuple(
        context_packet.get("available_formal_declarations", [])
    ):
        declaration_key = _formal_declaration_key(declaration)
        target_key = _target_prover_key(target_prover_family)
        if declaration_key:
            support.setdefault((declaration_key, target_key), set()).add(
                "available_formal_declarations"
            )
    return support


def _formal_declaration_row_source_fields(row: Mapping[str, Any]) -> tuple[str, ...]:
    fields: list[str] = []
    fields.append(str(row.get("source_field", "")).strip())
    fields.extend(_str_tuple(row.get("source_fields", [])))
    return tuple(
        dict.fromkeys(
            field
            for field in (
                _formal_declaration_source_field_key(value) for value in fields
            )
            if field
        )
    )


def _formal_declaration_source_field_rank(value: object) -> int:
    key = _formal_declaration_source_field_key(value)
    if not key:
        return 0
    if key in {"declaration", "declaration_name", "declaration_names"}:
        return 0
    if _formal_declaration_source_field_supports_existing_coverage(key):
        return 3
    if "resource_request" in key or key.startswith("pending_"):
        return 1
    return 2


def _available_formal_declaration_primitive_support_for_request(
    request: Mapping[str, Any],
) -> dict[tuple[str, str], set[str]]:
    support: dict[tuple[str, str], set[str]] = {}
    _collect_formal_declaration_primitive_support(
        _dict_value(request, "context_packet"),
        support,
        inherited_target_prover_family=str(request.get("target_prover_family", "")),
        inherited_primitives=tuple(),
    )
    return support


def _available_formal_declaration_primitive_non_support_for_request(
    request: Mapping[str, Any],
) -> dict[tuple[str, str], set[str]]:
    non_support: dict[tuple[str, str], set[str]] = {}
    _collect_formal_declaration_primitive_non_support(
        _dict_value(request, "context_packet"),
        non_support,
        inherited_target_prover_family=str(request.get("target_prover_family", "")),
    )
    return non_support


def _collect_formal_declaration_primitive_support(
    value: Any,
    support: dict[tuple[str, str], set[str]],
    *,
    inherited_target_prover_family: str,
    inherited_primitives: tuple[str, ...],
) -> None:
    if isinstance(value, Mapping):
        explicit_target = str(
            value.get("target_prover_family") or value.get("target_prover") or ""
        ).strip()
        current_target = str(
            explicit_target or inherited_target_prover_family
        )
        scoped_primitives = tuple(
            dict.fromkeys(
                [
                    *inherited_primitives,
                    *_primitive_positive_scope_values(value),
                ]
            )
        )
        for field_name in ("formal_declaration_hits", "lean_declaration_hits"):
            for row in _dict_tuple(value.get(field_name, [])):
                row_scope = _primitive_positive_scope_values(row)
                row_primitives = tuple(
                    dict.fromkeys(row_scope if row_scope else scoped_primitives)
                )
                if not row_primitives:
                    continue
                declaration = str(
                    row.get("declaration")
                    or row.get("declaration_name")
                    or row.get("candidate_declaration")
                    or row.get("lean_declaration")
                    or row.get("name")
                    or row.get("full_name")
                    or ""
                ).strip()
                declaration_key = _formal_declaration_key(declaration)
                target_key = _target_prover_key(
                    _formal_declaration_target_for_source_field(
                        explicit_target_prover_family=str(
                            row.get("target_prover_family", "")
                            or row.get("target_prover", "")
                        ),
                        inherited_target_prover_family=current_target,
                        source_field=field_name,
                    )
                )
                if declaration_key:
                    support.setdefault((declaration_key, target_key), set()).update(
                        row_primitives
                    )
        for item in value.values():
            _collect_formal_declaration_primitive_support(
                item,
                support,
                inherited_target_prover_family=current_target,
                inherited_primitives=scoped_primitives,
            )
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _collect_formal_declaration_primitive_support(
                item,
                support,
                inherited_target_prover_family=inherited_target_prover_family,
                inherited_primitives=inherited_primitives,
            )


def _collect_formal_declaration_primitive_non_support(
    value: Any,
    non_support: dict[tuple[str, str], set[str]],
    *,
    inherited_target_prover_family: str,
) -> None:
    if isinstance(value, Mapping):
        explicit_target = str(
            value.get("target_prover_family") or value.get("target_prover") or ""
        ).strip()
        current_target = str(
            explicit_target or inherited_target_prover_family
        )
        for field_name in ("formal_declaration_hits", "lean_declaration_hits"):
            for row in _dict_tuple(value.get(field_name, [])):
                row_primitives = _primitive_negative_scope_values(row)
                if not row_primitives:
                    continue
                declaration = str(
                    row.get("declaration")
                    or row.get("declaration_name")
                    or row.get("candidate_declaration")
                    or row.get("lean_declaration")
                    or row.get("name")
                    or row.get("full_name")
                    or ""
                ).strip()
                declaration_key = _formal_declaration_key(declaration)
                target_key = _target_prover_key(
                    _formal_declaration_target_for_source_field(
                        explicit_target_prover_family=str(
                            row.get("target_prover_family", "")
                            or row.get("target_prover", "")
                        ),
                        inherited_target_prover_family=current_target,
                        source_field=field_name,
                    )
                )
                if declaration_key:
                    non_support.setdefault((declaration_key, target_key), set()).update(
                        row_primitives
                    )
        for item in value.values():
            _collect_formal_declaration_primitive_non_support(
                item,
                non_support,
                inherited_target_prover_family=current_target,
            )
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _collect_formal_declaration_primitive_non_support(
                item,
                non_support,
                inherited_target_prover_family=inherited_target_prover_family,
            )


def _primitive_positive_scope_values(value: Mapping[str, Any]) -> tuple[str, ...]:
    primitives: list[str] = []
    supported = _primitive_values(value.get("supported_target_primitives", []))
    unsupported = {
        _primitive_key(primitive)
        for primitive in _primitive_values(value.get("unsupported_target_primitives", []))
        if _primitive_key(primitive)
    }
    if supported:
        primitives.extend(supported)
    elif unsupported:
        candidates = [
            *_primitive_values(value.get("primitive", "")),
            *_primitive_values(value.get("target_primitives", [])),
        ]
        primitives.extend(
            primitive
            for primitive in candidates
            if _primitive_key(primitive) not in unsupported
        )
    else:
        primitives.extend(_primitive_values(value.get("primitive", "")))
        primitives.extend(_primitive_values(value.get("target_primitives", [])))
    coverage_updates = _dict_value(value, "coverage_updates")
    primitives.extend(str(primitive) for primitive in coverage_updates.keys())
    return tuple(
        dict.fromkeys(
            primitive
            for primitive in (_primitive_key(item) for item in primitives)
            if primitive
        )
    )


def _primitive_negative_scope_values(value: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            primitive
            for primitive in (
                _primitive_key(item)
                for item in _primitive_values(
                    value.get("unsupported_target_primitives", [])
                )
            )
            if primitive
        )
    )


def _formal_declaration_source_field_supports_existing_coverage(
    value: object,
) -> bool:
    key = _formal_declaration_source_field_key(value)
    if not key:
        return False
    if key in {
        "available_formal_declaration_rows",
        "available_formal_declarations",
    }:
        return False
    if (
        "resource_request" in key
        or key.startswith("request_payload_")
        or key.startswith("pending_")
    ):
        return False
    return (
        key
        in {
            "candidate_declaration",
            "candidate_declarations",
            "candidate_declaration_rows",
            "formal_declaration_hits",
            "lean_declaration",
            "lean_declarations",
            "lean_declaration_hits",
            "route_level_formal_context",
        }
        or key.endswith("_formal_context")
        or key.endswith("_declaration_hits")
    )


def _collect_formal_declaration_rows(
    value: Any,
    rows: list[dict[str, object]],
    *,
    inherited_target_prover_family: str,
    suppress_generic_declaration_fields: bool = False,
) -> None:
    if isinstance(value, Mapping):
        explicit_target = str(
            value.get("target_prover_family") or value.get("target_prover") or ""
        ).strip()
        current_target = str(
            explicit_target or inherited_target_prover_family
        )
        suppress_here = suppress_generic_declaration_fields or any(
            str(value.get(field_name, "")).strip()
            for field_name in (
                "resource_request_id",
                "action_resource_plan_id",
                "primitive_action_id",
            )
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
            } and not suppress_here:
                declaration_target = _formal_declaration_target_for_source_field(
                    explicit_target_prover_family=explicit_target,
                    inherited_target_prover_family=current_target,
                    source_field=key_text,
                )
                rows.extend(
                    {
                        "declaration": declaration,
                        "target_prover_family": declaration_target,
                        "source_field": key_text,
                    }
                    for declaration in _formal_declaration_values(item)
                )
            _collect_formal_declaration_rows(
                item,
                rows,
                inherited_target_prover_family=current_target,
                suppress_generic_declaration_fields=(
                    suppress_here
                    or key_text
                    in {
                        "candidate_declaration_rows",
                        "formal_declaration_hits",
                        "lean_declaration_hits",
                        "request_payload",
                        "request_playbook",
                        "resource_request_playbooks",
                        "resource_request_queue_rows",
                        "input_summary",
                    }
                ),
            )
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _collect_formal_declaration_rows(
                item,
                rows,
                inherited_target_prover_family=inherited_target_prover_family,
                suppress_generic_declaration_fields=(
                    suppress_generic_declaration_fields
                ),
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
        explicit_target = str(
            value.get("target_prover_family", "") or value.get("target_prover", "")
        ).strip()
        rows.append(
            {
                "declaration": declaration,
                "target_prover_family": _formal_declaration_target_for_source_field(
                    explicit_target_prover_family=explicit_target,
                    inherited_target_prover_family=inherited_target_prover_family,
                    source_field=str(
                        value.get("source_field", "") or fallback_source_field
                    ),
                ).strip(),
                "source_field": str(
                    value.get("source_field", "") or fallback_source_field
                ).strip(),
            }
        )


def _formal_declaration_target_for_source_field(
    *,
    explicit_target_prover_family: str,
    inherited_target_prover_family: str,
    source_field: object,
) -> str:
    explicit = str(explicit_target_prover_family or "").strip()
    if explicit:
        return explicit
    key = _formal_declaration_source_field_key(source_field)
    if key in {
        "lean_declaration",
        "lean_declarations",
        "lean_declaration_hits",
    }:
        return "lean4"
    return str(inherited_target_prover_family or "").strip()


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
                "formal_declaration_hits",
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
    route = _dict_value(payload, "standalone_route")
    for index, primitive in enumerate(_dict_tuple(route.get("primitives", []))):
        status = _source_ref_key(primitive.get("source_search_status", ""))
        refs = _str_tuple(
            [
                *_str_tuple(primitive.get("source_refs", [])),
                *_source_refs_from_snippets(primitive.get("source_snippets", [])),
            ]
        )
        if status == "source_backed" and not refs:
            errors.append(
                "standalone_route.primitives"
                f"[{index}] SOURCE_BACKED requires primitive-level source_refs or source_snippets"
            )
    return errors


def _response_source_search_status_errors(
    payload: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    for location, value in _response_source_search_status_locations(payload):
        raw_status = str(value or "").strip()
        if not raw_status:
            continue
        status_key = _source_ref_key(raw_status)
        if status_key not in LLM_ROUTE_PLANNER_SOURCE_SEARCH_STATUS_KEYS:
            errors.append(
                f"{location}.source_search_status unsupported: {raw_status}; "
                "expected one of "
                + ", ".join(LLM_ROUTE_PLANNER_SOURCE_SEARCH_STATUS_KEYS)
            )
    return errors


def _response_source_search_status_locations(
    payload: Mapping[str, Any],
) -> tuple[tuple[str, object], ...]:
    rows: list[tuple[str, object]] = []
    for index, node in enumerate(
        _dict_tuple(payload.get("informal_knowledge_dag_nodes", []))
    ):
        rows.append(
            (
                f"informal_knowledge_dag_nodes[{index}]",
                node.get("source_search_status", ""),
            )
        )
    for index, residual in enumerate(
        _dict_tuple(payload.get("residual_interpretations", []))
    ):
        rows.append(
            (
                f"residual_interpretations[{index}]",
                residual.get("source_search_status", ""),
            )
        )
    route = _dict_value(payload, "standalone_route")
    if "source_search_status" in route:
        rows.append(("standalone_route", route.get("source_search_status", "")))
    for index, primitive in enumerate(_dict_tuple(route.get("primitives", []))):
        rows.append(
            (
                f"standalone_route.primitives[{index}]",
                primitive.get("source_search_status", ""),
            )
        )
    return tuple(rows)


def _response_formal_gap_boundary_errors(
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    for location, row in _response_formal_gap_boundary_locations(payload, request):
        boundary = str(row.get("formal_gap_boundary", "") or "").strip()
        status_key = _source_ref_key(row.get("source_search_status", ""))
        requires_boundary = bool(boundary) or _source_search_status_is_formal_boundary(
            status_key
        )
        if not requires_boundary:
            continue
        if not boundary:
            errors.append(
                f"{location}.formal_gap_boundary required when "
                "source_search_status declares a formal boundary"
            )
            continue
        if not _formal_gap_boundary_is_substantive(boundary):
            errors.append(
                f"{location}.formal_gap_boundary must be a substantive formal "
                "boundary explanation, not a placeholder"
            )
    return errors


def _formal_gap_boundary_obligations(
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
) -> tuple[str, ...]:
    obligations: list[str] = []
    for location, row in _response_formal_gap_boundary_locations(payload, request):
        boundary = str(row.get("formal_gap_boundary", "") or "").strip()
        if _formal_gap_boundary_is_substantive(boundary):
            obligations.append(location)
    return tuple(dict.fromkeys(obligations))


def _response_formal_gap_boundary_locations(
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
) -> tuple[tuple[str, dict[str, object]], ...]:
    rows: list[tuple[str, dict[str, object]]] = []
    for index, node in enumerate(
        _dict_tuple(payload.get("informal_knowledge_dag_nodes", []))
    ):
        rows.append((f"informal_knowledge_dag_nodes[{index}]", node))
    for index, residual in enumerate(
        _dict_tuple(payload.get("residual_interpretations", []))
    ):
        rows.append((f"residual_interpretations[{index}]", residual))
    target_prover_family = str(request.get("target_prover_family", ""))
    for index, node in enumerate(
        _formal_realization_nodes_from_payload(
            payload,
            target_prover_family=target_prover_family,
        )
    ):
        rows.append((f"formal_realization_dag_nodes[{index}]", node))
    route = _standalone_route_from_payload(
        payload,
        target_prover_family=target_prover_family,
    )
    rows.append(("standalone_route", route))
    for index, primitive in enumerate(_dict_tuple(route.get("primitives", []))):
        rows.append((f"standalone_route.primitives[{index}]", primitive))
    return tuple(rows)


def _formal_gap_boundary_is_substantive(text: str) -> bool:
    stripped = str(text or "").strip()
    if not stripped:
        return False
    tokens = [
        token
        for token in re.findall(r"[a-z0-9]+", stripped.lower())
        if len(token) >= 4 and token not in FORMAL_GAP_BOUNDARY_TEXT_STOPWORDS
    ]
    if len(tokens) >= FORMAL_GAP_BOUNDARY_MIN_SUPPORT_TOKENS:
        return True
    return (
        len(tokens) >= 2
        and len(stripped) >= FORMAL_GAP_BOUNDARY_MIN_TWO_TOKEN_SUPPORT_CHARS
    )


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


def _response_search_request_primitive_grounding_errors(
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[str]:
    return _response_target_primitive_grounding_errors(
        payload,
        request,
        collection_name="search_requests",
    )


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


def _response_planner_next_action_primitive_grounding_errors(
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[str]:
    return _response_target_primitive_grounding_errors(
        payload,
        request,
        collection_name="planner_next_actions",
    )


def _response_target_primitive_grounding_errors(
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
    *,
    collection_name: str,
) -> list[str]:
    allowed_primitives = _bounded_action_allowed_primitive_keys(payload, request)
    errors: list[str] = []
    for index, action in enumerate(_dict_tuple(payload.get(collection_name, []))):
        target_primitives = _planner_action_target_primitive_keys(action)
        if not target_primitives:
            continue
        ungrounded = sorted(target_primitives - allowed_primitives)
        if ungrounded:
            errors.append(
                f"{collection_name}[{index}].target_primitives must be drawn from request, route, "
                "formal-realization, residual, or cost-hint primitive evidence; "
                "ungrounded target_primitives: "
                + ", ".join(ungrounded[:8])
            )
    return errors


def _bounded_action_allowed_primitive_keys(
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
) -> set[str]:
    target_prover_family = str(request.get("target_prover_family", ""))
    minimal_delta = _dict_value(payload, "minimal_delta_plan")
    selected_primitives = {
        _primitive_key(primitive)
        for primitive in _str_tuple(minimal_delta.get("selected_primitives", []))
    }
    selected_primitives.discard("")
    allowed = set(_available_primitive_keys_for_request(request))
    allowed.update(selected_primitives)
    allowed.update(_minimal_delta_primitives(minimal_delta, selected_primitives))
    allowed.update(_cost_hint_baseline_primitives(request))
    for row in _dict_tuple(minimal_delta.get("primitive_costs", [])):
        primitive = _primitive_key(row.get("primitive", ""))
        if primitive:
            allowed.add(primitive)
    for node in _formal_realization_nodes_from_payload(
        payload,
        target_prover_family=target_prover_family,
    ):
        primitive = _primitive_key(node.get("primitive", ""))
        if primitive:
            allowed.add(primitive)
    route = _standalone_route_from_payload(
        payload,
        target_prover_family=target_prover_family,
    )
    for primitive_row in _dict_tuple(route.get("primitives", [])):
        primitive = _primitive_key(primitive_row.get("primitive", ""))
        if primitive:
            allowed.add(primitive)
    for edge in _dict_tuple(payload.get("route_alignment_edges", [])):
        primitive = _primitive_key(edge.get("primitive", ""))
        if primitive:
            allowed.add(primitive)
    for interpretation in _dict_tuple(payload.get("residual_interpretations", [])):
        allowed.update(_residual_interpretation_search_primitives(interpretation))
    allowed.discard("")
    return allowed


def _planner_action_target_primitive_keys(action: Mapping[str, Any]) -> set[str]:
    primitives: set[str] = set()
    for field_name in (
        "target_primitive",
        "target_primitives",
        "primitive",
        "primitives",
    ):
        primitives.update(
            _primitive_key(primitive)
            for primitive in _primitive_values(action.get(field_name))
            if _primitive_key(primitive)
        )
    primitives.discard("")
    return primitives


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
        "search_pending",
        "source_search_requested",
        "source_search_pending",
        "literature_search_requested",
        "literature_search_pending",
    }


def _source_search_status_is_formal_boundary(status: str) -> bool:
    return status in {
        "formal_gap_boundary",
        "formal_boundary",
        "formal_boundary_declared",
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


def _response_source_snippet_primitive_support_errors(
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[str]:
    """Reject using partial source snippets as evidence for unsupported primitives."""

    emitted = _response_source_snippet_locations_with_context(payload)
    if not emitted:
        return []
    available = _dict_tuple(
        _dict_value(request, "context_packet").get("available_source_snippets", [])
    )
    if not available:
        return []
    search_requests = _dict_tuple(payload.get("search_requests", []))
    errors: list[str] = []
    for snippet, location, context_primitives in emitted:
        emitted_primitives = _str_tuple(
            [
                *_str_tuple(snippet.get("target_primitives", [])),
                *context_primitives,
            ]
        )
        emitted_supported = _str_tuple(
            snippet.get("supported_target_primitives", [])
        )
        if not emitted_primitives and not emitted_supported:
            continue
        matches = _matching_available_source_snippets(snippet, available)
        if not matches:
            continue
        unsupported_keys: set[str] = set()
        supported_keys: set[str] = set()
        unsupported_labels: dict[str, str] = {}
        for match in matches:
            for primitive in _str_tuple(
                match.get("unsupported_target_primitives", [])
            ):
                key = _primitive_key(primitive)
                if key:
                    unsupported_keys.add(key)
                    unsupported_labels.setdefault(key, primitive)
            for primitive in _str_tuple(
                match.get("supported_target_primitives", [])
            ):
                key = _primitive_key(primitive)
                if key:
                    supported_keys.add(key)
        if not unsupported_keys:
            continue
        claimed_primitives = tuple(
            dict.fromkeys([*emitted_primitives, *emitted_supported])
        )
        overclaimed = tuple(
            primitive
            for primitive in claimed_primitives
            if _primitive_key(primitive) in unsupported_keys
            and _primitive_key(primitive) not in supported_keys
        )
        if not overclaimed:
            continue
        uncovered = tuple(
            primitive
            for primitive in overclaimed
            if not _has_literature_search_request_for_obligation(
                search_requests,
                primitives=(primitive,),
            )
        )
        if uncovered:
            errors.append(
                f"{location} uses partial source evidence for unsupported "
                "target primitive(s) without a matching literature/source "
                "search_request: "
                + ", ".join(
                    unsupported_labels.get(_primitive_key(primitive), primitive)
                    for primitive in uncovered[:8]
                )
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


def _response_source_snippet_locations_with_context(
    payload: Mapping[str, Any],
) -> tuple[tuple[dict[str, object], str, tuple[str, ...]], ...]:
    rows: list[tuple[dict[str, object], str, tuple[str, ...]]] = []
    rows.extend(
        (snippet, f"response.source_snippets[{index}]", tuple())
        for index, snippet in enumerate(_dict_tuple(payload.get("source_snippets", [])))
    )
    for index, node in enumerate(_dict_tuple(payload.get("informal_knowledge_dag_nodes", []))):
        context_primitives = _source_snippet_informal_node_context_primitives(node)
        rows.extend(
            (
                snippet,
                f"informal_knowledge_dag_nodes[{index}].source_snippets[{snippet_index}]",
                context_primitives,
            )
            for snippet_index, snippet in enumerate(_dict_tuple(node.get("source_snippets", [])))
        )
    for index, residual in enumerate(_dict_tuple(payload.get("residual_interpretations", []))):
        context_primitives = _source_snippet_declared_context_primitives(residual)
        rows.extend(
            (
                snippet,
                f"residual_interpretations[{index}].source_snippets[{snippet_index}]",
                context_primitives,
            )
            for snippet_index, snippet in enumerate(_dict_tuple(residual.get("source_snippets", [])))
        )
    route = _dict_value(payload, "standalone_route")
    rows.extend(
        (snippet, f"standalone_route.source_snippets[{index}]", tuple())
        for index, snippet in enumerate(_dict_tuple(route.get("source_snippets", [])))
    )
    for index, primitive in enumerate(_dict_tuple(route.get("primitives", []))):
        context_primitives = _source_snippet_declared_context_primitives(primitive)
        rows.extend(
            (
                snippet,
                f"standalone_route.primitives[{index}].source_snippets[{snippet_index}]",
                context_primitives,
            )
            for snippet_index, snippet in enumerate(_dict_tuple(primitive.get("source_snippets", [])))
        )
    return tuple(rows)


def _source_snippet_informal_node_context_primitives(
    node: Mapping[str, Any],
) -> tuple[str, ...]:
    primitives = list(_source_snippet_declared_context_primitives(node))
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


def _source_snippet_declared_context_primitives(
    value: Mapping[str, Any],
) -> tuple[str, ...]:
    primitives: list[str] = []
    for field_name in (
        "target_primitive",
        "target_primitives",
        "primitive",
        "primitives",
    ):
        primitives.extend(_primitive_values(value.get(field_name)))
    return tuple(
        dict.fromkeys(
            primitive
            for primitive in (_primitive_key(value) for value in primitives)
            if primitive
        )
    )


def _matching_available_source_snippets(
    snippet: Mapping[str, object],
    available: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    source_ref_key = _source_ref_key(snippet.get("source_ref", ""))
    if not source_ref_key:
        return tuple()
    claim = _snippet_text_key(snippet.get("claim", ""))
    excerpt = _snippet_text_key(snippet.get("excerpt", ""))
    matches: list[dict[str, object]] = []
    for row in available:
        if _source_ref_key(row.get("source_ref", "")) != source_ref_key:
            continue
        row_claim = _snippet_text_key(row.get("claim", ""))
        row_excerpt = _snippet_text_key(row.get("excerpt", ""))
        if excerpt:
            if _snippet_text_contains(excerpt, row_excerpt):
                matches.append(row)
            continue
        if claim and _snippet_text_contains(claim, row_claim):
            matches.append(row)
    return tuple(matches)


def _source_snippet_supported_by_available(
    snippet: Mapping[str, object],
    available: tuple[dict[str, object], ...],
) -> bool:
    return bool(_matching_available_source_snippets(snippet, available))


def _snippet_text_contains(left: str, right: str) -> bool:
    if not left or not right:
        return False
    if left in right:
        return _snippet_text_has_substantive_anchor(left)
    if right in left:
        return _snippet_text_has_substantive_anchor(right)
    return False


def _snippet_text_has_substantive_anchor(text: str) -> bool:
    stripped = str(text or "").strip()
    if not stripped:
        return False
    substantive_tokens = [
        token
        for token in re.findall(r"[a-z0-9]+", stripped.lower())
        if len(token) >= 4 and token not in SOURCE_SNIPPET_TEXT_SUPPORT_STOPWORDS
    ]
    if len(substantive_tokens) >= SOURCE_SNIPPET_MIN_SUPPORT_TOKENS:
        return True
    return (
        len(substantive_tokens) >= 2
        and len(stripped) >= SOURCE_SNIPPET_MIN_TWO_TOKEN_SUPPORT_CHARS
    )


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
    quality_context = _quality_control_context_for_request(
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
                "adapter_ids",
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
        errors.extend(
            _quality_control_grounding_errors(
                collection_name,
                index,
                row,
                resource_contract_ids=resource_contract_ids,
                quality_context=quality_context,
            )
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


def _quality_control_context_for_request(
    context_packet: Mapping[str, Any],
    *,
    registry_context: Mapping[str, Any],
) -> dict[str, object]:
    required_quality_signals: set[str] = set()
    quality_gates: set[str] = set()
    response_validation_signals: set[str] = set()
    stop_conditions: set[str] = set()
    response_validation_signals_by_contract_id: dict[str, set[str]] = {}

    def absorb(row: Mapping[str, Any], *, contract_scoped: bool = False) -> None:
        required_quality_signals.update(
            _quality_control_keys(row, ("required_quality_signal", "required_quality_signals"))
        )
        quality_gates.update(_quality_control_keys(row, ("quality_gate", "quality_gates", "gate")))
        row_response_validation_signals = _quality_control_keys(
            row,
            (
                "response_validation_signal",
                "response_validation_signals",
                "validation_signal",
                "validation_signals",
            ),
        )
        response_validation_signals.update(row_response_validation_signals)
        stop_conditions.update(_quality_control_keys(row, ("stop_condition", "stop_conditions")))
        if contract_scoped:
            for contract_id in _resource_contract_ids_for_rows((dict(row),)):
                response_validation_signals_by_contract_id.setdefault(
                    contract_id,
                    set(),
                ).update(row_response_validation_signals)

    for row_key in (
        "interactive_decision_policy_rows",
        "resource_request_queue_rows",
    ):
        for row in _dict_tuple(context_packet.get(row_key, [])):
            absorb(row, contract_scoped=True)
    for row in _dict_tuple(context_packet.get("interactive_session_rows", [])):
        absorb(row)
    current_route = _dict_value(context_packet, "current_route")
    absorb(_dict_value(current_route, "quality_controls"), contract_scoped=True)
    replan_metadata = _dict_value(context_packet, "replan_metadata")
    absorb(_dict_value(replan_metadata, "quality_controls"), contract_scoped=True)
    feedback_summary = _dict_value(context_packet, "feedback_loop_summary")
    for row in _dict_tuple(feedback_summary.get("recommended_next_actions", [])):
        absorb(row, contract_scoped=True)
    prior_replan_metadata = _dict_value(feedback_summary, "prior_replan_metadata")
    absorb(
        _dict_value(prior_replan_metadata, "quality_controls"),
        contract_scoped=True,
    )

    for row in _dict_tuple(registry_context.get("resource_rows", [])):
        absorb(row)
    for row in _dict_tuple(registry_context.get("component_rows", [])):
        absorb(row)
    for row in _dict_tuple(registry_context.get("execution_plan_rows", [])):
        absorb(row)
    for row in _dict_tuple(registry_context.get("resource_contract_rows", [])):
        absorb(row, contract_scoped=True)

    return {
        "required_quality_signals": required_quality_signals,
        "quality_gates": quality_gates,
        "response_validation_signals": response_validation_signals,
        "stop_conditions": stop_conditions,
        "response_validation_signals_by_contract_id": response_validation_signals_by_contract_id,
    }


def _quality_control_grounding_errors(
    collection_name: str,
    index: int,
    row: Mapping[str, Any],
    *,
    resource_contract_ids: set[str],
    quality_context: Mapping[str, object],
) -> list[str]:
    errors: list[str] = []
    for field_name, aliases in (
        ("required_quality_signals", ("required_quality_signal", "required_quality_signals")),
        ("quality_gates", ("quality_gate", "quality_gates", "gate")),
        (
            "response_validation_signals",
            (
                "response_validation_signal",
                "response_validation_signals",
                "validation_signal",
                "validation_signals",
            ),
        ),
        ("stop_conditions", ("stop_condition", "stop_conditions")),
    ):
        declared = _quality_control_keys(row, aliases)
        allowed = set(quality_context.get(field_name, set()) or set())
        unknown = sorted(declared - allowed) if allowed else []
        if unknown:
            errors.append(
                f"{collection_name}[{index}] references {field_name} not present "
                "in request interactive policy, resource queue, feedback summary, "
                "or component-resource registry context: "
                + ", ".join(unknown[:8])
            )

    declared_response_signals = _quality_control_keys(
        row,
        (
            "response_validation_signal",
            "response_validation_signals",
            "validation_signal",
            "validation_signals",
        ),
    )
    by_contract = quality_context.get("response_validation_signals_by_contract_id", {})
    if (
        declared_response_signals
        and resource_contract_ids
        and isinstance(by_contract, Mapping)
    ):
        allowed_for_contracts: set[str] = set()
        for contract_id in resource_contract_ids:
            allowed_for_contracts.update(set(by_contract.get(contract_id, set()) or set()))
        if allowed_for_contracts:
            unknown_for_contracts = sorted(
                declared_response_signals - allowed_for_contracts
            )
            if unknown_for_contracts:
                errors.append(
                    f"{collection_name}[{index}] response_validation_signals are "
                    "not supported by the referenced resource_contract_id(s): "
                    + ", ".join(unknown_for_contracts[:8])
                )
    return errors


def _quality_control_keys(
    row: Mapping[str, Any],
    field_names: tuple[str, ...],
) -> set[str]:
    keys: set[str] = set()
    for field_name in field_names:
        keys.update(
            _resource_ref_key(value)
            for value in _str_tuple(row.get(field_name, []))
            if _resource_ref_key(value)
        )
    return keys


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
    current_route = _dict_value(context_packet, "current_route")
    replan_metadata = _dict_value(context_packet, "replan_metadata")
    prior_replan_metadata = _dict_value(feedback_summary, "prior_replan_metadata")
    ids.update(
        _resource_contract_ids_for_rows(
            (
                _dict_value(current_route, "quality_controls"),
                _dict_value(replan_metadata, "quality_controls"),
                _dict_value(prior_replan_metadata, "quality_controls"),
            )
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
    errors.extend(
        _minimal_delta_actionability_witness_errors(
            minimal_delta=minimal_delta,
            formal_nodes=formal_nodes,
            standalone_primitives=standalone_primitives,
            selected=selected,
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


def _minimal_delta_actionability_witness_errors(
    *,
    minimal_delta: Mapping[str, Any],
    formal_nodes: tuple[dict[str, object], ...],
    standalone_primitives: tuple[dict[str, object], ...],
    selected: set[str],
) -> list[str]:
    errors: list[str] = []
    witness = _minimal_delta_action_witness_status(
        minimal_delta=minimal_delta,
        formal_nodes=formal_nodes,
        standalone_primitives=standalone_primitives,
        selected=selected,
    )
    for item in _dict_tuple(witness.get("missing_delta_action_witnesses", [])):
        primitive = str(item.get("primitive", "")).strip()
        action_field = str(item.get("required_action_field", "")).strip()
        acceptable_fields = _str_tuple(item.get("acceptable_action_fields", []))
        sources = _str_tuple(item.get("requirement_sources", []))
        if primitive and action_field:
            errors.append(
                "minimal_delta_plan selected primitive "
                f"{primitive} requires actionable action witness in "
                f"{', '.join(acceptable_fields)} because "
                + "; ".join(sources)
            )
    return errors


def _minimal_delta_action_witness_status(
    *,
    minimal_delta: Mapping[str, Any],
    formal_nodes: tuple[dict[str, object], ...],
    standalone_primitives: tuple[dict[str, object], ...],
    selected: set[str],
) -> dict[str, object]:
    required_by_primitive = _minimal_delta_action_requirements(
        minimal_delta=minimal_delta,
        formal_nodes=formal_nodes,
        standalone_primitives=standalone_primitives,
        selected=selected,
    )
    witnessed: list[str] = []
    missing: list[str] = []
    missing_rows: list[dict[str, object]] = []
    witness_rows: list[dict[str, object]] = []
    for primitive, action_fields in sorted(required_by_primitive.items()):
        primitive_missing = False
        for action_field, sources in sorted(action_fields.items()):
            acceptable_fields = _minimal_delta_action_witness_fields(action_field)
            matched_fields: list[str] = []
            placeholder_fields: list[str] = []
            matched_items_by_field: dict[str, list[str]] = {}
            placeholder_items_by_field: dict[str, list[str]] = {}
            for field_name in acceptable_fields:
                match = _minimal_delta_action_list_match_status(
                    minimal_delta.get(field_name, []),
                    primitive,
                )
                if match["matched_items"]:
                    matched_items_by_field[field_name] = list(match["matched_items"])
                if match["placeholder_items"]:
                    placeholder_fields.append(field_name)
                    placeholder_items_by_field[field_name] = list(
                        match["placeholder_items"]
                    )
                if match["actionable_items"]:
                    matched_fields.append(field_name)
            row = {
                "primitive": primitive,
                "required_action_field": action_field,
                "acceptable_action_fields": list(acceptable_fields),
                "requirement_sources": sorted(sources),
                "matched_action_fields": matched_fields,
                "placeholder_action_fields": placeholder_fields,
                "matched_action_items_by_field": matched_items_by_field,
                "placeholder_action_items_by_field": placeholder_items_by_field,
            }
            if matched_fields:
                witness_rows.append(row)
            else:
                primitive_missing = True
                missing_rows.append(row)
        if primitive_missing:
            missing.append(primitive)
        else:
            witnessed.append(primitive)
    required_primitives = tuple(sorted(required_by_primitive))
    return {
        "delta_action_witness_required_primitives": list(required_primitives),
        "delta_action_witnessed_primitives": sorted(set(witnessed)),
        "delta_action_witness_missing_primitives": sorted(set(missing)),
        "delta_action_witness_complete": not missing_rows,
        "delta_action_witness_rows": witness_rows,
        "missing_delta_action_witnesses": missing_rows,
    }


def _minimal_delta_action_requirements(
    *,
    minimal_delta: Mapping[str, Any],
    formal_nodes: tuple[dict[str, object], ...],
    standalone_primitives: tuple[dict[str, object], ...],
    selected: set[str],
) -> dict[str, dict[str, set[str]]]:
    required_by_primitive: dict[str, dict[str, set[str]]] = {}
    if not selected:
        return required_by_primitive

    def add_requirement(
        primitive: str,
        action_field: str,
        *,
        marker: str,
        source_field: str,
    ) -> None:
        primitive_key = _primitive_key(primitive)
        if not primitive_key or primitive_key not in selected:
            return
        required_by_primitive.setdefault(primitive_key, {}).setdefault(
            action_field,
            set(),
        ).add(f"{source_field}={marker}")

    for row in formal_nodes:
        primitive = _primitive_key(row.get("primitive", ""))
        for field_name in (
            "coverage_bucket",
            "coverage_status",
            "formalization_action",
            "alignment_status",
        ):
            marker = _primitive_key(row.get(field_name, ""))
            for action_field in _minimal_delta_action_fields_for_marker(marker):
                add_requirement(
                    primitive,
                    action_field,
                    marker=marker,
                    source_field=f"formal_realization_dag_nodes.{field_name}",
                )
    for row in standalone_primitives:
        primitive = _primitive_key(row.get("primitive", ""))
        for field_name in (
            "coverage_bucket",
            "coverage_status",
            "formalization_action",
            "alignment_status",
        ):
            marker = _primitive_key(row.get(field_name, ""))
            for action_field in _minimal_delta_action_fields_for_marker(marker):
                add_requirement(
                    primitive,
                    action_field,
                    marker=marker,
                    source_field=f"standalone_route.primitives.{field_name}",
                )
    for index, row in enumerate(_dict_tuple(minimal_delta.get("primitive_costs", []))):
        primitive = _primitive_key(row.get("primitive", ""))
        marker = _primitive_key(row.get("coverage_bucket", ""))
        for action_field in _minimal_delta_action_fields_for_marker(marker):
            add_requirement(
                primitive,
                action_field,
                marker=marker,
                source_field=(
                    "minimal_delta_plan.primitive_costs"
                    f"[{index}].coverage_bucket"
                ),
            )
    return required_by_primitive


def _minimal_delta_action_fields_for_marker(marker: str) -> tuple[str, ...]:
    bucket = _coverage_marker_policy_bucket(marker)
    if bucket in {"wrapper", "wrapper_needed"}:
        return ("wrapper_lemmas",)
    if bucket in {"bridge", "bridge_needed"}:
        return ("bridge_lemmas",)
    if bucket in {"source_port", "source_port_needed"}:
        return ("source_port_lemmas",)
    if bucket == "new_definition":
        return ("new_definitions",)
    if bucket in {"new_theory", "new_theory_needed"}:
        return ("new_theory_primitives",)
    return tuple()


def _minimal_delta_action_witness_fields(action_field: str) -> tuple[str, ...]:
    if action_field == "new_theory_primitives":
        return (
            "new_theory_primitives",
            "first_principles_primitives",
            "new_definitions",
        )
    return (action_field,)


def _minimal_delta_action_list_match_status(
    values: object,
    primitive: str,
) -> dict[str, tuple[str, ...]]:
    primitive_key = _primitive_key(primitive)
    if not primitive_key:
        return {
            "matched_items": tuple(),
            "actionable_items": tuple(),
            "placeholder_items": tuple(),
        }
    matched_items: list[str] = []
    actionable_items: list[str] = []
    placeholder_items: list[str] = []
    for value in _minimal_delta_action_item_texts(values):
        value_key = _primitive_key(value)
        if value_key == primitive_key:
            matched_items.append(value)
            placeholder_items.append(value)
            continue
        if primitive_key in value_key or value_key in primitive_key:
            matched_items.append(value)
            if _minimal_delta_action_item_is_actionable(value, primitive_key):
                actionable_items.append(value)
            else:
                placeholder_items.append(value)
    return {
        "matched_items": tuple(matched_items),
        "actionable_items": tuple(actionable_items),
        "placeholder_items": tuple(placeholder_items),
    }


def _minimal_delta_action_item_texts(values: object) -> tuple[str, ...]:
    if isinstance(values, Mapping):
        return (_minimal_delta_action_item_text(values),)
    if isinstance(values, str):
        return (values,) if values.strip() else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(
        text
        for text in (_minimal_delta_action_item_text(value) for value in values)
        if text
    )


def _minimal_delta_action_item_text(value: object) -> str:
    if isinstance(value, Mapping):
        parts = []
        for field_name in (
            "primitive",
            "lemma",
            "lemma_name",
            "definition",
            "statement",
            "theorem_statement",
            "goal",
            "proof_obligation",
            "construction",
            "description",
            "rationale",
        ):
            text = str(value.get(field_name, "") or "").strip()
            if text:
                parts.append(text)
        return " ".join(parts)
    return str(value or "").strip()


def _minimal_delta_action_item_is_actionable(text: str, primitive_key: str) -> bool:
    value_key = _primitive_key(text)
    if not value_key or value_key == primitive_key:
        return False
    remainder = value_key.replace(primitive_key, " ")
    content_tokens = [
        token
        for token in re.findall(r"[a-z0-9]+", remainder)
        if len(token) >= 4
        and token
        not in {
            "action",
            "delta",
            "lemma",
            "primitive",
            "selected",
            "theorem",
            "work",
        }
    ]
    action_markers = {
        "bridge",
        "construct",
        "define",
        "definition",
        "derive",
        "formalize",
        "goal",
        "obligation",
        "port",
        "prove",
        "show",
        "source",
        "statement",
        "target",
        "wrapper",
    }
    return bool(content_tokens) and (
        ":" in text
        or any(marker in value_key for marker in action_markers)
    )


def _minimal_delta_request_hint_errors(
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
) -> list[str]:
    """Reject LLM responses that underprice deterministic request cost hints."""

    hints = _dict_value(
        _dict_value(request, "context_packet"),
        "minimal_delta_cost_hints",
    )
    if not hints:
        return []
    errors: list[str] = []
    minimal_delta = _dict_value(payload, "minimal_delta_plan")
    primitive_hints = _request_primitive_cost_hints_by_primitive(hints)
    for index, row in enumerate(_dict_tuple(minimal_delta.get("primitive_costs", []))):
        primitive = _primitive_key(row.get("primitive", ""))
        hint = primitive_hints.get(primitive)
        if not hint or not _is_nonnegative_number(row.get("base_cost")):
            continue
        minimum_base_cost = float(hint.get("minimum_base_cost", 0) or 0)
        base_cost = float(row.get("base_cost", 0) or 0)
        if base_cost + 1e-9 < minimum_base_cost:
            errors.append(
                "minimal_delta_plan.primitive_costs"
                f"[{index}].base_cost underprices request minimal_delta_cost_hints "
                f"for primitive {primitive}: base_cost={base_cost:g} but "
                f"minimum_base_cost={minimum_base_cost:g} "
                f"source={hint.get('minimum_cost_source', '')} "
                f"marker={hint.get('minimum_cost_marker', '')}"
            )
    errors.extend(
        _minimal_delta_route_option_primitive_hint_errors(
            minimal_delta,
            primitive_hints,
        )
    )

    selected = {
        _primitive_key(primitive)
        for primitive in _str_tuple(minimal_delta.get("selected_primitives", []))
    }
    selected.discard("")
    route_cost = minimal_delta.get("route_cost")
    for hint_index, hint in enumerate(_dict_tuple(hints.get("route_option_hints", []))):
        minimum_route_base_cost = hint.get("minimum_route_base_cost")
        hint_primitives = {
            _primitive_key(primitive)
            for primitive in _str_tuple(hint.get("selected_primitives", []))
        }
        hint_primitives.discard("")
        if not hint_primitives or not _is_nonnegative_number(minimum_route_base_cost):
            continue
        minimum_cost = float(minimum_route_base_cost or 0)
        if (
            selected == hint_primitives
            and _is_nonnegative_number(route_cost)
            and float(route_cost or 0) + 1e-9 < minimum_cost
        ):
            errors.append(
                "minimal_delta_plan.route_cost underprices request "
                "minimal_delta_cost_hints route option "
                f"{hint.get('route_option_id', f'route_option_hints[{hint_index}]')}: "
                f"route_cost={float(route_cost or 0):g} but "
                f"minimum_route_base_cost={minimum_cost:g}"
            )
        errors.extend(
            _minimal_delta_baseline_route_option_hint_errors(
                minimal_delta,
                hint,
                hint_index=hint_index,
                selected=selected,
                hint_primitives=hint_primitives,
                minimum_route_base_cost=minimum_cost,
            )
        )
        errors.extend(
            _minimal_delta_selected_route_option_hint_errors(
                minimal_delta,
                hint,
                hint_index=hint_index,
                hint_primitives=hint_primitives,
                minimum_route_base_cost=minimum_cost,
            )
        )
    return errors


def _cost_hint_baseline_primitives(
    request: Mapping[str, Any],
) -> tuple[str, ...]:
    hints = _dict_value(
        _dict_value(request, "context_packet"),
        "minimal_delta_cost_hints",
    )
    if not hints:
        return tuple()
    primitives: list[str] = []
    for hint in _dict_tuple(hints.get("route_option_hints", [])):
        primitives.extend(
            _primitive_key(primitive)
            for primitive in _str_tuple(hint.get("selected_primitives", []))
        )
    return tuple(dict.fromkeys(primitive for primitive in primitives if primitive))


def _omitted_cost_hint_primitives(
    minimal_delta: Mapping[str, Any],
    request: Mapping[str, Any],
) -> tuple[str, ...]:
    baseline = _cost_hint_baseline_primitives(request)
    if not baseline:
        return tuple()
    selected = {
        _primitive_key(primitive)
        for primitive in _str_tuple(minimal_delta.get("selected_primitives", []))
    }
    selected.discard("")
    return tuple(primitive for primitive in baseline if primitive not in selected)


def _minimal_delta_baseline_route_option_hint_errors(
    minimal_delta: Mapping[str, Any],
    hint: Mapping[str, Any],
    *,
    hint_index: int,
    selected: set[str],
    hint_primitives: set[str],
    minimum_route_base_cost: float,
) -> list[str]:
    omitted = sorted(hint_primitives - selected)
    if not omitted:
        return []
    graph = _dict_value(minimal_delta, "and_or_cost_graph")
    hint_route_option_id = str(hint.get("route_option_id", "")).strip()
    matching_options: list[tuple[int, dict[str, object]]] = []
    for index, option in enumerate(_dict_tuple(graph.get("route_options", []))):
        option_id = str(option.get("route_option_id", "")).strip()
        option_primitives = {
            _primitive_key(primitive)
            for primitive in _str_tuple(option.get("selected_primitives", []))
        }
        option_primitives.discard("")
        if option_primitives == hint_primitives or (
            hint_route_option_id and option_id == hint_route_option_id
        ):
            matching_options.append((index, option))
    if not matching_options:
        return [
            "minimal_delta_plan.and_or_cost_graph.route_options must include "
            "request minimal_delta_cost_hints baseline route option "
            f"{hint_route_option_id or f'route_option_hints[{hint_index}]'} "
            "when selected route omits hinted primitive(s): "
            + ", ".join(omitted)
        ]
    errors: list[str] = []
    for index, option in matching_options:
        option_cost = option.get("route_cost")
        if not _is_nonnegative_number(option_cost):
            continue
        if float(option_cost or 0) + 1e-9 < minimum_route_base_cost:
            errors.append(
                "minimal_delta_plan.and_or_cost_graph.route_options"
                f"[{index}].route_cost underprices request "
                "minimal_delta_cost_hints baseline route option "
                f"{hint_route_option_id or f'route_option_hints[{hint_index}]'}: "
                f"route_cost={float(option_cost or 0):g} but "
                f"minimum_route_base_cost={minimum_route_base_cost:g}"
            )
    return errors


def _request_primitive_cost_hints_by_primitive(
    hints: Mapping[str, Any],
) -> dict[str, dict[str, object]]:
    by_primitive: dict[str, dict[str, object]] = {}
    for hint in _dict_tuple(hints.get("primitive_cost_hints", [])):
        primitive = _primitive_key(hint.get("primitive", ""))
        if not primitive or not _is_nonnegative_number(hint.get("minimum_base_cost")):
            continue
        current = by_primitive.get(primitive)
        if current is None or float(
            hint.get("minimum_base_cost", 0) or 0
        ) > float(current.get("minimum_base_cost", 0) or 0):
            by_primitive[primitive] = dict(hint)
    return by_primitive


def _minimal_delta_route_option_primitive_hint_errors(
    minimal_delta: Mapping[str, Any],
    primitive_hints: Mapping[str, Mapping[str, object]],
) -> list[str]:
    """Reject route options cheaper than request-provided primitive lower bounds."""

    graph = _dict_value(minimal_delta, "and_or_cost_graph")
    errors: list[str] = []
    if not primitive_hints:
        return errors
    for index, option in enumerate(_dict_tuple(graph.get("route_options", []))):
        option_cost = option.get("route_cost")
        if not _is_nonnegative_number(option_cost):
            continue
        option_primitives = tuple(
            dict.fromkeys(
                primitive
                for primitive in (
                    _primitive_key(value)
                    for value in _str_tuple(option.get("selected_primitives", []))
                )
                if primitive
            )
        )
        hinted_primitives: list[str] = []
        minimum_known_base_cost = 0.0
        sources: list[str] = []
        markers: list[str] = []
        for primitive in option_primitives:
            hint = primitive_hints.get(primitive)
            if not hint:
                continue
            hinted_primitives.append(primitive)
            minimum_known_base_cost += float(hint.get("minimum_base_cost", 0) or 0)
            source = str(hint.get("minimum_cost_source", "")).strip()
            marker = str(hint.get("minimum_cost_marker", "")).strip()
            if source:
                sources.append(source)
            if marker:
                markers.append(marker)
        if not hinted_primitives:
            continue
        if float(option_cost or 0) + 1e-9 < minimum_known_base_cost:
            errors.append(
                "minimal_delta_plan.and_or_cost_graph.route_options"
                f"[{index}].route_cost underprices request primitive cost hints: "
                f"route_cost={float(option_cost or 0):g} but "
                f"minimum_known_base_cost={minimum_known_base_cost:g} "
                f"primitives={','.join(hinted_primitives)} "
                f"sources={','.join(dict.fromkeys(sources))} "
                f"markers={','.join(dict.fromkeys(markers))}"
            )
    return errors


def _minimal_delta_selected_route_option_hint_errors(
    minimal_delta: Mapping[str, Any],
    hint: Mapping[str, Any],
    *,
    hint_index: int,
    hint_primitives: set[str],
    minimum_route_base_cost: float,
) -> list[str]:
    errors: list[str] = []
    graph = _dict_value(minimal_delta, "and_or_cost_graph")
    hint_route_option_id = str(hint.get("route_option_id", "")).strip()
    for index, option in enumerate(_dict_tuple(graph.get("route_options", []))):
        if not bool(option.get("selected", False)):
            continue
        option_id = str(option.get("route_option_id", "")).strip()
        option_primitives = {
            _primitive_key(primitive)
            for primitive in _str_tuple(option.get("selected_primitives", []))
        }
        option_primitives.discard("")
        if not (
            option_id == hint_route_option_id
            or (option_primitives and option_primitives == hint_primitives)
        ):
            continue
        option_cost = option.get("route_cost")
        if not _is_nonnegative_number(option_cost):
            continue
        if float(option_cost or 0) + 1e-9 < minimum_route_base_cost:
            errors.append(
                "minimal_delta_plan.and_or_cost_graph.route_options"
                f"[{index}].route_cost underprices request "
                "minimal_delta_cost_hints route option "
                f"{hint_route_option_id or f'route_option_hints[{hint_index}]'}: "
                f"route_cost={float(option_cost or 0):g} but "
                f"minimum_route_base_cost={minimum_route_base_cost:g}"
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
        "add_minimal_wrapper": "wrapper",
        "bridge": "bridge",
        "bridge_needed": "bridge_needed",
        "prove_bridge": "bridge",
        "bridge_lemma": "bridge_needed",
        "design_bridge_lemma": "bridge_needed",
        "source_port": "source_port",
        "source_port_needed": "source_port_needed",
        "port_external_source": "source_port",
        "new_definition": "new_definition",
        "new_definition_needed": "new_definition",
        "define_new": "new_definition",
        "formalize_assumption_interface": "new_definition",
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
    cost_hint_baseline = _cost_hint_baseline_primitives(request)
    omitted_cost_hint = _omitted_cost_hint_primitives(minimal_delta, request)

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
    action_witness = _minimal_delta_action_witness_status(
        minimal_delta=minimal_delta,
        formal_nodes=formal_nodes,
        standalone_primitives=_dict_tuple(standalone_route.get("primitives", [])),
        selected=selected,
    )
    action_witness_complete = bool(
        action_witness.get("delta_action_witness_complete", False)
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
        "cost_hint_baseline_primitives": list(cost_hint_baseline),
        "omitted_cost_hint_primitives": list(omitted_cost_hint),
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
        **action_witness,
        "cost_hint_baseline_coverage_complete": not omitted_cost_hint,
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
        and not introduced_missing_alignment
        and action_witness_complete,
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
        candidate_primitives = _minimal_delta_action_primitives_for_field(
            minimal_delta,
            field_name,
            selected,
        )
        for item in _minimal_delta_action_item_texts(minimal_delta.get(field_name, [])):
            item_key = _primitive_key(item)
            if not item_key:
                continue
            prefix_matches = {
                primitive
                for primitive in candidate_primitives
                if item_key == primitive
                or item_key.startswith(f"{primitive}_")
                or item_key.startswith(f"{primitive}:")
            }
            matched_selected = prefix_matches or {
                primitive
                for primitive in candidate_primitives
                if primitive in item_key or item_key in primitive
            }
            if matched_selected:
                explicit.update(matched_selected)
            else:
                explicit.add(item_key)
    explicit.discard("")
    return explicit or set(selected)


def _minimal_delta_action_primitives_for_field(
    minimal_delta: Mapping[str, Any],
    field_name: str,
    selected: set[str],
) -> set[str]:
    candidates: set[str] = set()
    for row in _dict_tuple(minimal_delta.get("primitive_costs", [])):
        primitive = _primitive_key(row.get("primitive", ""))
        if not primitive or primitive not in selected:
            continue
        for action_field in _minimal_delta_action_fields_for_marker(
            _primitive_key(row.get("coverage_bucket", ""))
        ):
            if field_name in _minimal_delta_action_witness_fields(action_field):
                candidates.add(primitive)
    return candidates or set(selected)


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
    if _formal_gap_boundary_is_substantive(
        str(node.get("formal_gap_boundary", "") or "")
    ):
        return True
    status = _source_ref_key(node.get("source_search_status", ""))
    if _source_search_status_requires_request(status):
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
    if _formal_gap_boundary_is_substantive(
        str(node.get("formal_gap_boundary", "") or "")
    ):
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


def _minimal_delta_cost_hints(
    route: Mapping[str, Any],
    context_packet: Mapping[str, Any],
    *,
    target_prover_family: str,
) -> dict[str, object]:
    rows_by_primitive: dict[str, list[tuple[str, dict[str, object]]]] = {}
    primitive_order: list[str] = []

    def add_row(source: str, row: Mapping[str, object]) -> None:
        primitive = _primitive_key(row.get("primitive", ""))
        if not primitive:
            return
        if primitive not in rows_by_primitive:
            primitive_order.append(primitive)
        rows_by_primitive.setdefault(primitive, []).append((source, dict(row)))

    for row in _dict_tuple(route.get("primitives", [])):
        add_row("current_route.primitives", row)
    for row in _dict_tuple(context_packet.get("library_coverage_rows", [])):
        add_row("library_coverage_rows", row)
    for row in _dict_tuple(context_packet.get("current_goal_plan_rows", [])):
        for packet in (
            *_dict_tuple(row.get("portable_work_packets", [])),
            *_dict_tuple(row.get("next_work_packets", [])),
        ):
            add_row("current_goal_plan_rows.work_packets", packet)
    for row in _dict_tuple(context_packet.get("resource_response_ledger_rows", [])):
        if not _resource_response_row_is_admissible_feedback(row):
            continue
        for update in _coverage_update_hint_rows(
            row,
            target_prover_family=target_prover_family,
        ):
            add_row("resource_response_ledger_rows.coverage_updates", update)
    for row in _dict_tuple(context_packet.get("refinement_evidence_rows", [])):
        if not _refinement_evidence_row_is_admissible_feedback(row):
            continue
        for update in _coverage_update_hint_rows(
            row,
            target_prover_family=target_prover_family,
        ):
            add_row("refinement_evidence_rows.coverage_updates", update)

    primitive_hints = [
        _primitive_cost_hint(
            primitive,
            rows_by_primitive.get(primitive, []),
            target_prover_family=target_prover_family,
        )
        for primitive in primitive_order
    ]
    route_option_hints: list[dict[str, object]] = []
    if primitive_hints:
        selected_primitives = [
            str(hint.get("primitive", ""))
            for hint in primitive_hints
            if str(hint.get("primitive", "")).strip()
        ]
        route_option_hints.append(
            {
                "route_option_id": "route_option:current_route_min_delta_baseline",
                "option_kind": "current_route_primitive_set",
                "selected_primitives": selected_primitives,
                "minimum_route_base_cost": sum(
                    float(hint.get("minimum_base_cost", 0) or 0)
                    for hint in primitive_hints
                    if _is_nonnegative_number(hint.get("minimum_base_cost"))
                ),
                "cost_policy_id": MINIMAL_DELTA_COST_POLICY_ID,
                "cost_rationale": (
                    "Sum of per-primitive minimum_base_cost values derived from "
                    "current route and coverage-map evidence."
                ),
            }
        )
    return {
        "hint_kind": "minimal_delta_cost_hints",
        "cost_policy_id": MINIMAL_DELTA_COST_POLICY_ID,
        "primitive_cost_hints": primitive_hints,
        "route_option_hints": route_option_hints,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _coverage_update_hint_rows(
    row: Mapping[str, Any],
    *,
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    updates = _dict_value(row, "coverage_updates")
    if not updates:
        return tuple()
    target = str(
        row.get("target_prover_family")
        or row.get("target_prover")
        or target_prover_family
    )
    rows: list[dict[str, object]] = []
    for primitive, coverage_status in updates.items():
        primitive_key = _primitive_key(primitive)
        coverage_key = _primitive_key(coverage_status)
        if not primitive_key or not coverage_key:
            continue
        candidate_rows = _candidate_declaration_rows_for_coverage_update(
            row,
            primitive=str(primitive),
            inherited_target_prover_family=target,
        )
        rows.append(
            {
                "primitive": str(primitive).strip(),
                "coverage_status": str(coverage_status).strip(),
                "target_prover_family": target,
                "source_field": "coverage_updates",
                "candidate_declaration_rows": [dict(item) for item in candidate_rows],
            }
        )
    return tuple(rows)


def _candidate_declaration_rows_for_coverage_update(
    row: Mapping[str, Any],
    *,
    primitive: str,
    inherited_target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    primitive_key = _primitive_key(primitive)
    if not primitive_key:
        return tuple()
    candidates: list[dict[str, object]] = []
    for source_field, values in (
        ("candidate_declaration_rows", row.get("candidate_declaration_rows", [])),
        ("formal_declaration_hits", row.get("formal_declaration_hits", [])),
    ):
        for candidate in _candidate_declaration_rows(
            values,
            inherited_target_prover_family=inherited_target_prover_family,
            fallback_source_field=source_field,
        ):
            if not _candidate_declaration_row_supports_primitive(
                candidate,
                primitive_key=primitive_key,
            ):
                continue
            candidates.append(dict(candidate))
    if _target_prover_key(inherited_target_prover_family) == "lean4":
        for candidate in _candidate_declaration_rows(
            row.get("lean_declaration_hits", []),
            inherited_target_prover_family=inherited_target_prover_family,
            fallback_source_field="lean_declaration_hits",
        ):
            if not _candidate_declaration_row_supports_primitive(
                candidate,
                primitive_key=primitive_key,
            ):
                continue
            candidates.append(dict(candidate))
    return tuple(_compact_candidate_declaration_rows(candidates))


def _candidate_declaration_row_supports_primitive(
    row: Mapping[str, object],
    *,
    primitive_key: str,
) -> bool:
    unsupported = {
        _primitive_key(item)
        for item in _str_tuple(row.get("unsupported_target_primitives", []))
        if _primitive_key(item)
    }
    if primitive_key in unsupported:
        return False
    supported_scope = {
        _primitive_key(item)
        for item in _str_tuple(row.get("supported_target_primitives", []))
        if _primitive_key(item)
    }
    if supported_scope:
        return primitive_key in supported_scope
    target_scope = {
        _primitive_key(item)
        for item in _str_tuple(row.get("target_primitives", []))
        if _primitive_key(item)
    }
    if target_scope:
        return primitive_key in target_scope
    return True


def _primitive_cost_hint(
    primitive: str,
    source_rows: list[tuple[str, dict[str, object]]],
    *,
    target_prover_family: str,
) -> dict[str, object]:
    coverage_markers = [
        marker
        for source, row in source_rows
        for marker in _coverage_cost_marker_rows(row, source=source)
    ]
    if coverage_markers:
        lower_bound = max(
            coverage_markers,
            key=lambda marker: float(marker.get("base_cost", 0) or 0),
        )
    else:
        unknown_cost = _coverage_bucket_base_cost("unknown")
        lower_bound = {
            "source": "minimal_delta_cost_hints.default",
            "source_field": "coverage_status",
            "marker": "unknown",
            "normalized_coverage_bucket": "unknown",
            "base_cost": 20 if unknown_cost is None else unknown_cost,
        }
    candidate_rows = [
        normalized
        for _, row in source_rows
        for normalized in _candidate_declaration_rows(
            row.get("candidate_declaration_rows", []),
            inherited_target_prover_family=str(
                row.get("target_prover_family", "")
                or target_prover_family
            ),
            fallback_source_field="candidate_declaration_rows",
        )
    ]
    for source, row in source_rows:
        row_target = str(row.get("target_prover_family", "") or target_prover_family)
        candidate_rows.extend(
            {
                "declaration": declaration,
                "target_prover_family": row_target,
                "source_field": source + ".candidate_declarations",
            }
            for declaration in _formal_declaration_values(
                row.get("candidate_declarations", [])
            )
        )
    compact_candidate_rows = _compact_candidate_declaration_rows(candidate_rows)
    return {
        "primitive": primitive,
        "evidence_sources": list(
            dict.fromkeys(source for source, _ in source_rows if source)
        ),
        "coverage_markers": coverage_markers,
        "minimum_coverage_bucket": str(
            lower_bound.get("normalized_coverage_bucket", "unknown")
        ),
        "minimum_base_cost": lower_bound.get("base_cost", 20),
        "minimum_cost_source": str(lower_bound.get("source", "")),
        "minimum_cost_marker": str(lower_bound.get("marker", "")),
        "candidate_declarations": [
            str(row.get("declaration", ""))
            for row in _target_compatible_formal_declaration_rows(
                tuple(compact_candidate_rows),
                target_prover_family=target_prover_family,
            )
            if str(row.get("declaration", "")).strip()
        ],
        "candidate_declaration_rows": compact_candidate_rows,
        "has_target_compatible_declaration": bool(
            _target_compatible_formal_declaration_rows(
                tuple(compact_candidate_rows),
                target_prover_family=target_prover_family,
            )
        ),
    }


def _coverage_cost_marker_rows(
    row: Mapping[str, object],
    *,
    source: str,
) -> list[dict[str, object]]:
    markers: list[dict[str, object]] = []
    for field_name in (
        "coverage_bucket",
        "coverage_status",
        "formalization_action",
        "alignment_status",
        "action_class",
    ):
        marker = _primitive_key(row.get(field_name, ""))
        bucket = _coverage_marker_policy_bucket(marker)
        if not bucket:
            continue
        cost = _coverage_bucket_base_cost(bucket)
        if cost is None:
            continue
        markers.append(
            {
                "source": source,
                "source_field": field_name,
                "marker": marker,
                "normalized_coverage_bucket": bucket,
                "base_cost": cost,
            }
        )
    return markers


def _compact_candidate_declaration_rows(
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    compact: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        declaration = str(row.get("declaration", "")).strip()
        if not declaration:
            continue
        target = str(row.get("target_prover_family", "")).strip()
        source_field = str(row.get("source_field", "")).strip()
        key = (
            _formal_declaration_key(declaration),
            _target_prover_key(target),
            source_field,
        )
        if key in seen:
            continue
        seen.add(key)
        compact.append(
            {
                "declaration": declaration,
                "target_prover_family": target,
                "source_field": source_field,
            }
        )
    return compact


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
    formalization_gap_planner_route_replan_handoff_dir: Path | None,
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
        "route_replan_handoff": _optional_manifest(
            formalization_gap_planner_route_replan_handoff_dir,
            "formalization_gap_planner_route_replan_handoff_manifest.json",
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
        candidate_ids = _row_route_match_ids(row)
        if route_id_set.intersection(candidate_ids) or not route_id_set:
            matched.append(_compact_row(row))
    return tuple(matched[:25])


def _row_route_match_ids(row: Mapping[str, Any]) -> set[str]:
    ids = set(_route_match_id_values(row))
    for nested_field in ROUTE_MATCH_NESTED_FIELDS:
        ids.update(_route_match_id_values(_dict_value(row, nested_field)))
    return {route_id for route_id in ids if route_id}


def _route_match_id_values(row: Mapping[str, Any]) -> tuple[str, ...]:
    values: list[str] = []
    for field_name in ROUTE_MATCH_SCALAR_FIELDS:
        values.extend(_str_tuple(row.get(field_name, "")))
    for field_name in ROUTE_MATCH_COLLECTION_FIELDS:
        values.extend(_str_tuple(row.get(field_name, [])))
    return _str_tuple(values)


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


def _request_context_packet_inventory(
    request: Mapping[str, Any],
) -> dict[str, object]:
    context = _dict_value(request, "context_packet")
    inventory = context.get("context_packet_inventory", {})
    return dict(inventory) if isinstance(inventory, Mapping) else {}


def _request_library_alignment_summary(
    request: Mapping[str, Any],
) -> dict[str, object]:
    context = _dict_value(request, "context_packet")
    summary = context.get("library_alignment_summary", {})
    return dict(summary) if isinstance(summary, Mapping) else {}


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
        "route_replan_handoff_rows",
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
    initial_quality_control_obligations = _quality_control_obligation_summary(
        context_packet,
        include_feedback_summary=False,
    )
    if (
        not residual_goals
        and not evidence_counts
        and not replan_metadata
        and not initial_quality_control_obligations.get("present")
    ):
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
        and (
            realization_coverage.get("complete") is False
            or realization_coverage.get("cost_hint_baseline_coverage_complete")
            is False
        )
    )
    if realization_coverage:
        recommended_next_actions = _merge_dict_rows(
            recommended_next_actions,
            _realization_feedback_next_actions(realization_coverage),
            key_fields=("source", "action", "target_primitives"),
        )
    quality_control_obligations = _quality_control_obligation_summary(
        context_packet,
        recommended_next_actions=recommended_next_actions,
        include_feedback_summary=False,
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
    if quality_control_obligations.get("present"):
        summary["quality_control_obligations"] = quality_control_obligations
    if replan_metadata:
        summary["prior_replan_metadata"] = {
            key: replan_metadata[key]
            for key in (
                "source_route_id",
                "llm_route_planner_row_id",
                "llm_route_planner_acceptance_status",
                "revised_selected_primitives",
                "residual_goals",
                "quality_controls",
                "applied_llm_route_planner_hook_traces",
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
                witness.get("cost_hint_baseline_primitives", []),
                witness.get("omitted_cost_hint_primitives", []),
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
    cost_hint_baseline = _unique_strings(
        primitive
        for witness in deduped
        for primitive in _str_tuple(witness.get("cost_hint_baseline_primitives", []))
    )
    omitted_cost_hint = _unique_strings(
        primitive
        for witness in deduped
        for primitive in _str_tuple(witness.get("omitted_cost_hint_primitives", []))
    )
    cost_hint_complete = all(
        bool(witness.get("cost_hint_baseline_coverage_complete", True))
        for witness in deduped
    )
    return {
        "witness_count": len(deduped),
        "complete": all(
            bool(witness.get("realization_coverage_complete", False))
            for witness in deduped
        ),
        "missing_selected_formal_primitives": list(missing_selected[:20]),
        "missing_delta_alignment_primitives": list(missing_delta[:20]),
        "cost_hint_baseline_primitives": list(cost_hint_baseline[:20]),
        "omitted_cost_hint_primitives": list(omitted_cost_hint[:20]),
        "cost_hint_baseline_coverage_complete": cost_hint_complete,
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
        "cost_hint_baseline_primitives",
        "omitted_cost_hint_primitives",
        "selected_primitives_missing_standalone_route_node",
        "selected_primitives_missing_formal_realization_node",
        "delta_primitives_missing_route_alignment_edge",
        "introduced_primitives_missing_route_alignment_edge",
        "delta_action_witness_required_primitives",
        "delta_action_witnessed_primitives",
        "delta_action_witness_missing_primitives",
    )
    compact: dict[str, object] = {
        field_name: list(_str_tuple(witness.get(field_name, [])))
        for field_name in list_fields
        if _str_tuple(witness.get(field_name, []))
    }
    compact["realization_coverage_complete"] = bool(
        witness.get("realization_coverage_complete", False)
    )
    if (
        "delta_action_witness_complete" in witness
        or _str_tuple(witness.get("delta_action_witness_required_primitives", []))
        or _str_tuple(witness.get("delta_action_witness_missing_primitives", []))
    ):
        compact["delta_action_witness_complete"] = bool(
            witness.get("delta_action_witness_complete", False)
        )
        compact["missing_delta_action_witnesses"] = [
            dict(row)
            for row in _dict_tuple(witness.get("missing_delta_action_witnesses", []))[:8]
        ]
    if (
        "cost_hint_baseline_coverage_complete" in witness
        or _str_tuple(witness.get("cost_hint_baseline_primitives", []))
        or _str_tuple(witness.get("omitted_cost_hint_primitives", []))
    ):
        compact["cost_hint_baseline_coverage_complete"] = bool(
            witness.get("cost_hint_baseline_coverage_complete", False)
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
    missing_action_witness = _str_tuple(
        realization_coverage.get("missing_delta_action_witness_primitives", [])
    )
    if missing_action_witness:
        actions.append(
            {
                "source": "realization_coverage_witness",
                "owner": "formalization_planner",
                "action": "add_minimal_delta_action_witnesses",
                "target_primitives": list(missing_action_witness[:12]),
                "reason": (
                    "selected positive-delta primitives must be listed in "
                    "wrapper_lemmas, bridge_lemmas, source_port_lemmas, "
                    "new_definitions, or new_theory_primitives"
                ),
            }
        )
    omitted_cost_hint = _str_tuple(
        realization_coverage.get("omitted_cost_hint_primitives", [])
    )
    if omitted_cost_hint:
        actions.append(
            {
                "source": "realization_coverage_witness",
                "owner": "formalization_gap_planner",
                "action": "review_or_restore_omitted_cost_hint_primitives",
                "target_primitives": list(omitted_cost_hint[:12]),
                "reason": (
                    "request-bound minimal-delta cost hints include primitives "
                    "omitted by the selected route"
                ),
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
    for row in rows_by_field.get("route_replan_handoff_rows", ()):
        if not (
            _str_tuple(row.get("next_commands", []))
            or _str_tuple(row.get("residual_goals", []))
            or _str_tuple(row.get("applied_refinement_evidence_ids", []))
        ):
            continue
        actions.append(
            {
                "source": "route_replan_handoff",
                "owner": "route_planner",
                "action": "continue_from_route_replan_handoff",
                "route_replan_handoff_id": str(
                    row.get("route_replan_handoff_id", "")
                ).strip(),
                "route_revision_overlay_id": str(
                    row.get("route_revision_overlay_id", "")
                ).strip(),
                "applied_refinement_evidence_ids": list(
                    _str_tuple(row.get("applied_refinement_evidence_ids", []))[:12]
                ),
                "residual_goals": list(
                    _str_tuple(row.get("residual_goals", []))[:12]
                ),
                "quality_controls": _dict_value(row, "quality_controls"),
                "commands": list(_str_tuple(row.get("next_commands", []))[:8]),
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
                "supported_target_primitives",
                "unsupported_target_primitives",
                "source_support_status",
                "matched_terms",
            )
            if key in snippet
        }
        for primitive_key in (
            "target_primitives",
            "supported_target_primitives",
            "unsupported_target_primitives",
            "matched_terms",
        ):
            if primitive_key in compact:
                compact[primitive_key] = _str_tuple(compact[primitive_key])
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
                    "supported_target_primitives": _str_tuple(
                        node.get("supported_target_primitives", [])
                    ),
                    "unsupported_target_primitives": _str_tuple(
                        node.get("unsupported_target_primitives", [])
                    ),
                    "source_support_status": str(
                        node.get("source_support_status", "")
                    ).strip(),
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
        "source_goal_plan_id",
        "target_goal_plan_id",
        "route_id",
        "source_route_id",
        "target_route_id",
        "current_route_id",
        "request_route_id",
        "selected_route_id",
        "route_match_ids",
        "target_intake_id",
        "target_id",
        "target_theorem_id",
        "standalone_route_id",
        "route_replan_handoff_id",
        "route_revision_overlay_id",
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
        "formal_declaration_hits",
        "lean_declaration_hits",
        "coverage_updates",
        "route_revision_summary",
        "source_grounding_id",
        "node_source",
        "node_id",
        "node_kind",
        "node_label",
        "grounding_status",
        "required_next_action",
        "residual_primitives",
        "residual_evidence_ids",
        "residual_attempt_status",
        "residual_diagnostic_signature",
        "revised_selected_primitives",
        "revised_delta_primitives",
        "revised_informal_knowledge_dag_nodes",
        "revised_formal_realization_dag_nodes",
        "revised_lean_realization_dag_nodes",
        "revised_route_alignment_edges",
        "revision_status",
        "applied_hook_kinds",
        "applied_proposal_ids",
        "applied_refinement_evidence_ids",
        "applied_llm_route_planner_hook_traces",
        "applied_resource_response_traces",
        "applied_prover_attempt_statuses",
        "applied_prover_diagnostic_signatures",
        "quality_controls",
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
    compact_target = _target_prover_key(compact.get("target_prover_family", ""))
    if compact_target and compact_target != "lean4":
        for lean_legacy_key in (
            "lean_grounding_queries",
            "lean_declaration_hits",
            "revised_lean_realization_dag_nodes",
            "needs_more_lean_grounding",
        ):
            compact.pop(lean_legacy_key, None)
    return compact


def _compact_standalone_input_trace(value: object) -> dict[str, object]:
    trace = value if isinstance(value, Mapping) else {}
    if not trace:
        return {}
    compact: dict[str, object] = {
        "trace_kind": str(trace.get("trace_kind", "")),
        "source_route_id": str(trace.get("source_route_id", "")),
        "source_goal_plan_id": str(trace.get("source_goal_plan_id", "")),
        "has_replan_metadata": bool(trace.get("has_replan_metadata", False)),
        "applied_hook_kinds": list(_str_tuple(trace.get("applied_hook_kinds", []))),
        "residual_goals": list(_str_tuple(trace.get("residual_goals", []))),
        "llm_route_planner_route_adoption_status": str(
            trace.get("llm_route_planner_route_adoption_status", "")
        ),
        "llm_route_planner_route_adoption_blockers": list(
            _str_tuple(trace.get("llm_route_planner_route_adoption_blockers", []))
        ),
        "llm_route_planner_seed_adoptable_for_standalone_replay": bool(
            trace.get("llm_route_planner_seed_adoptable_for_standalone_replay", False)
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
    *,
    route: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    residuals: list[str] = []
    route = route or {}
    residuals.extend(_str_tuple(route.get("residual_goals", [])))
    residuals.extend(
        _str_tuple(_dict_value(route, "replan_metadata").get("residual_goals", []))
    )
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
    ids = [route_id, *_route_match_id_values(route)]
    for nested_field in ROUTE_MATCH_NESTED_FIELDS:
        ids.extend(_route_match_id_values(_dict_value(route, nested_field)))
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
    accepted_rows = tuple(
        row for row in rows if row.response_contract_ok and row.standalone_route
    )
    if accepted_rows:
        selection_rows = _standalone_seed_route_selection_rows(accepted_rows)
        rows_by_id = {row.llm_route_planner_row_id: row for row in accepted_rows}
        routes = []
        for selection_row in selection_rows:
            row = rows_by_id[str(selection_row["llm_route_planner_row_id"])]
            route = _accepted_route_for_seed(row)
            _apply_seed_route_selection(route, selection_row)
            routes.append(route)
        selection_status = "accepted_llm_routes_ranked"
    else:
        routes = _fallback_routes_for_seed(input_payload, rows)
        selection_rows = _fallback_seed_route_selection_rows(routes)
        for route, selection_row in zip(routes, selection_rows):
            _apply_seed_route_selection(route, selection_row)
        selection_status = "fallback_routes_ranked"
    seed: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_VERSION,
        "component_name": FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT,
        "library_snapshot_ref": str(input_payload.get("library_snapshot_ref", "")),
        "routes": routes,
        "llm_route_planner_seed_route_selection": (
            _standalone_seed_route_selection_summary(
                selection_rows,
                selection_status=selection_status,
            )
        ),
        "llm_route_planner_source": LLM_ROUTE_PLANNER_COMPONENT,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }
    seed_target = _single_seed_target_prover_family(input_payload, routes)
    if seed_target:
        seed["target_prover_family"] = seed_target
    return seed


def _standalone_seed_route_selection_rows(
    rows: tuple[FormalizationGapPlannerLLMRoutePlannerRow, ...],
) -> tuple[dict[str, object], ...]:
    indexed_rows = tuple(enumerate(rows))
    ranked = sorted(
        indexed_rows,
        key=lambda item: _seed_route_selection_sort_key(item[1], item[0]),
    )
    selection_rows: list[dict[str, object]] = []
    for rank, (original_index, row) in enumerate(ranked, start=1):
        route_cost = _minimal_delta_route_cost(row.minimal_delta_plan)
        selected_route_option_id = str(
            _dict_value(row.minimal_delta_plan, "and_or_cost_graph").get(
                "selected_route_option_id",
                "",
            )
        )
        selection_rows.append(
            {
                "selection_rank": rank,
                "selected": rank == 1,
                "adoptable_for_standalone_replay": (
                    _seed_selection_row_adoptable_for_standalone_replay(
                        response_contract_ok=row.response_contract_ok,
                        route_adoption_status=row.route_adoption_status,
                        route_adoption_blockers=row.route_adoption_blockers,
                    )
                ),
                "selection_reason": (
                    "ranked by route_adoption_status, minimal_delta_plan.route_cost, "
                    "route_adoption_blocker_count, then original request order"
                ),
                "source_order": original_index,
                "route_id": row.route_id,
                "seed_route_id": str(row.standalone_route.get("route_id", "")),
                "llm_route_planner_row_id": row.llm_route_planner_row_id,
                "request_id": row.request_id,
                "route_adoption_status": row.route_adoption_status,
                "route_adoption_status_rank": _route_adoption_status_rank(
                    row.route_adoption_status
                ),
                "route_adoption_blocker_count": len(row.route_adoption_blockers),
                "route_adoption_blockers": list(row.route_adoption_blockers),
                "acceptance_status": row.acceptance_status,
                "minimal_delta_route_cost": route_cost,
                "minimal_delta_selected_route_option_id": selected_route_option_id,
                "response_contract_ok": row.response_contract_ok,
                "proof_evidence_status": PROOF_EVIDENCE_STATUS,
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            }
        )
    return tuple(selection_rows)


def _fallback_seed_route_selection_rows(
    routes: list[dict[str, object]],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for index, route in enumerate(routes):
        metadata = _dict_value(route, "replan_metadata")
        route_adoption_blockers = _str_tuple(
            route.get(
                "llm_route_planner_route_adoption_blockers",
                metadata.get("llm_route_planner_route_adoption_blockers", []),
            )
        )
        response_contract_ok = bool(
            route.get(
                "llm_route_planner_response_contract_ok",
                metadata.get("llm_route_planner_response_contract_ok", False),
            )
        )
        route_adoption_status = str(
            route.get(
                "llm_route_planner_route_adoption_status",
                metadata.get("llm_route_planner_route_adoption_status", ""),
            )
        )
        rows.append(
            {
                "selection_rank": index + 1,
                "selected": index == 0,
                "adoptable_for_standalone_replay": (
                    _seed_selection_row_adoptable_for_standalone_replay(
                        response_contract_ok=response_contract_ok,
                        route_adoption_status=route_adoption_status,
                        route_adoption_blockers=route_adoption_blockers,
                    )
                ),
                "selection_reason": (
                    "no accepted LLM route was available; fallback routes keep "
                    "standalone input order"
                ),
                "source_order": index,
                "route_id": str(
                    route.get("route_id")
                    or metadata.get("source_route_id")
                    or f"fallback_route_{index}"
                ),
                "seed_route_id": str(route.get("route_id", "")),
                "llm_route_planner_row_id": str(
                    route.get("llm_route_planner_row_id", "")
                ),
                "request_id": str(metadata.get("llm_route_planner_request_id", "")),
                "route_adoption_status": route_adoption_status,
                "route_adoption_status_rank": _route_adoption_status_rank(
                    route_adoption_status
                ),
                "route_adoption_blocker_count": len(route_adoption_blockers),
                "route_adoption_blockers": list(route_adoption_blockers),
                "acceptance_status": str(
                    route.get("llm_route_planner_acceptance_status", "")
                ),
                "minimal_delta_route_cost": None,
                "minimal_delta_selected_route_option_id": "",
                "response_contract_ok": response_contract_ok,
                "proof_evidence_status": PROOF_EVIDENCE_STATUS,
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            }
        )
    return tuple(rows)


def _standalone_seed_route_selection_summary(
    selection_rows: tuple[dict[str, object], ...],
    *,
    selection_status: str,
) -> dict[str, object]:
    selected = next(
        (row for row in selection_rows if bool(row.get("selected", False))),
        {},
    )
    return {
        "selection_kind": (
            "formalization_gap_planner_llm_route_planner_seed_route_selection"
        ),
        "selection_status": selection_status,
        "selection_policy": (
            "prefer READY_FOR_STANDALONE_REPLAY routes, then lower "
            "minimal_delta_plan.route_cost, fewer route-adoption blockers, and "
            "finally original request order"
        ),
        "selected_route_id": str(selected.get("route_id", "")),
        "selected_seed_route_id": str(selected.get("seed_route_id", "")),
        "selected_llm_route_planner_row_id": str(
            selected.get("llm_route_planner_row_id", "")
        ),
        "selected_request_id": str(selected.get("request_id", "")),
        "selected_route_adoption_status": str(
            selected.get("route_adoption_status", "")
        ),
        "selected_route_adoptable_for_standalone_replay": bool(
            selected.get("adoptable_for_standalone_replay", False)
        ),
        "selected_minimal_delta_route_cost": selected.get(
            "minimal_delta_route_cost",
            None,
        ),
        "n_route_candidates": len(selection_rows),
        "n_ready_route_candidates": sum(
            1
            for row in selection_rows
            if str(row.get("route_adoption_status", "")) == ROUTE_ADOPTION_READY_STATUS
        ),
        "n_adoptable_route_candidates": sum(
            1
            for row in selection_rows
            if bool(row.get("adoptable_for_standalone_replay", False))
        ),
        "n_selected_route_candidates_not_adoptable": sum(
            1
            for row in selection_rows
            if bool(row.get("selected", False))
            and not bool(row.get("adoptable_for_standalone_replay", False))
        ),
        "n_contract_valid_route_candidates": sum(
            1 for row in selection_rows if bool(row.get("response_contract_ok", False))
        ),
        "selection_rows": [dict(row) for row in selection_rows],
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _standalone_replay_gate(
    rows: Iterable[Mapping[str, object]],
    standalone_seed: Mapping[str, object],
) -> dict[str, object]:
    selection = _dict_value(
        standalone_seed,
        "llm_route_planner_seed_route_selection",
    )
    selection_rows = _dict_tuple(selection.get("selection_rows", []))
    selected = next(
        (row for row in selection_rows if bool(row.get("selected", False))),
        {},
    )
    selected_blockers = list(_str_tuple(selected.get("route_adoption_blockers", [])))
    gate_blockers = sorted(
        {
            blocker
            for row in selection_rows
            for blocker in _str_tuple(row.get("route_adoption_blockers", []))
        }
    )
    n_adoptable = sum(
        1
        for row in selection_rows
        if bool(row.get("adoptable_for_standalone_replay", False))
    )
    n_candidates = len(selection_rows)
    selected_adoptable = bool(
        selection.get("selected_route_adoptable_for_standalone_replay", False)
    )
    selected_status = str(selected.get("route_adoption_status", "") or "")
    if selected_adoptable:
        gate_status = ROUTE_ADOPTION_READY_STATUS
    elif not selection_rows:
        gate_status = "NO_ROUTE_CANDIDATES"
    elif selected_status == ROUTE_ADOPTION_AWAITING_STATUS:
        gate_status = ROUTE_ADOPTION_AWAITING_STATUS
    elif selected_status == ROUTE_ADOPTION_REJECTED_STATUS:
        gate_status = ROUTE_ADOPTION_REJECTED_STATUS
    else:
        gate_status = ROUTE_ADOPTION_PENDING_STATUS
    row_maps = tuple(rows)
    return {
        "gate_kind": STANDALONE_REPLAY_GATE_KIND,
        "gate_ok": selected_adoptable,
        "gate_status": gate_status,
        "selected_route_adoptable_for_standalone_replay": selected_adoptable,
        "selected_route_id": str(selection.get("selected_route_id", "")),
        "selected_seed_route_id": str(selection.get("selected_seed_route_id", "")),
        "selected_llm_route_planner_row_id": str(
            selection.get("selected_llm_route_planner_row_id", "")
        ),
        "selected_request_id": str(selection.get("selected_request_id", "")),
        "selected_route_adoption_status": selected_status,
        "selected_route_adoption_blockers": selected_blockers,
        "n_route_candidates": n_candidates,
        "n_contract_valid_route_candidates": sum(
            1
            for row in selection_rows
            if bool(row.get("response_contract_ok", False))
        ),
        "n_ready_route_candidates": sum(
            1
            for row in selection_rows
            if str(row.get("route_adoption_status", "")) == ROUTE_ADOPTION_READY_STATUS
        ),
        "n_adoptable_route_candidates": n_adoptable,
        "n_blocked_route_candidates": max(0, n_candidates - n_adoptable),
        "n_manifest_rows": len(row_maps),
        "n_manifest_rows_response_contract_ok": sum(
            1 for row in row_maps if bool(row.get("response_contract_ok", False))
        ),
        "gate_blockers": gate_blockers,
        "selection_status": str(selection.get("selection_status", "")),
        "selection_policy": str(selection.get("selection_policy", "")),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _apply_seed_route_selection(
    route: dict[str, object],
    selection_row: Mapping[str, object],
) -> None:
    selected = bool(selection_row.get("selected", False))
    route["llm_route_planner_seed_selected"] = selected
    route["llm_route_planner_seed_selection_rank"] = int(
        selection_row.get("selection_rank", 0) or 0
    )
    route["llm_route_planner_seed_selection_reason"] = str(
        selection_row.get("selection_reason", "")
    )
    route["llm_route_planner_seed_adoptable_for_standalone_replay"] = bool(
        selection_row.get("adoptable_for_standalone_replay", False)
    )
    route["llm_route_planner_seed_minimal_delta_route_cost"] = selection_row.get(
        "minimal_delta_route_cost",
        None,
    )
    metadata = _dict_value(route, "replan_metadata")
    metadata = {
        **metadata,
        "llm_route_planner_seed_selected": selected,
        "llm_route_planner_seed_selection_rank": int(
            selection_row.get("selection_rank", 0) or 0
        ),
        "llm_route_planner_seed_selection_reason": str(
            selection_row.get("selection_reason", "")
        ),
        "llm_route_planner_seed_adoptable_for_standalone_replay": bool(
            selection_row.get("adoptable_for_standalone_replay", False)
        ),
        "llm_route_planner_seed_minimal_delta_route_cost": selection_row.get(
            "minimal_delta_route_cost",
            None,
        ),
    }
    route["replan_metadata"] = metadata


def _seed_selection_row_adoptable_for_standalone_replay(
    *,
    response_contract_ok: bool,
    route_adoption_status: object,
    route_adoption_blockers: Iterable[object],
) -> bool:
    return (
        bool(response_contract_ok)
        and str(route_adoption_status or "") == ROUTE_ADOPTION_READY_STATUS
        and not tuple(route_adoption_blockers)
    )


def _seed_route_selection_sort_key(
    row: FormalizationGapPlannerLLMRoutePlannerRow,
    source_order: int,
) -> tuple[float, float, float, int, str]:
    route_cost = _minimal_delta_route_cost(row.minimal_delta_plan)
    return (
        float(_route_adoption_status_rank(row.route_adoption_status)),
        float("inf") if route_cost is None else float(route_cost),
        float(len(row.route_adoption_blockers)),
        source_order,
        row.route_id,
    )


def _route_adoption_status_rank(status: object) -> int:
    status_text = str(status or "")
    if status_text == ROUTE_ADOPTION_READY_STATUS:
        return 0
    if status_text == ROUTE_ADOPTION_PENDING_STATUS:
        return 1
    if status_text == ROUTE_ADOPTION_AWAITING_STATUS:
        return 2
    if status_text == ROUTE_ADOPTION_REJECTED_STATUS:
        return 3
    return 4


def _minimal_delta_route_cost(minimal_delta_plan: Mapping[str, object]) -> float | None:
    cost = minimal_delta_plan.get("route_cost")
    if not _is_nonnegative_number(cost):
        return None
    return float(cost)


def _fallback_routes_for_seed(
    input_payload: Mapping[str, Any],
    rows: tuple[FormalizationGapPlannerLLMRoutePlannerRow, ...],
) -> list[dict[str, object]]:
    rows_by_route_id = {row.route_id: row for row in rows if row.route_id}
    routes: list[dict[str, object]] = []
    for route in _routes(input_payload):
        row = rows_by_route_id.get(str(route.get("route_id", "")))
        if row is None:
            routes.append(dict(route))
            continue
        routes.append(_fallback_route_for_seed(route, row))
    return routes


def _fallback_route_for_seed(
    route: Mapping[str, Any],
    row: FormalizationGapPlannerLLMRoutePlannerRow,
) -> dict[str, object]:
    fallback = dict(route)
    metadata = _dict_value(fallback, "replan_metadata")
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
        "llm_route_planner_errors": list(row.errors),
        "llm_route_planner_generation_errors": list(row.generation_errors),
        "llm_route_planner_request_contract_blocked": (
            row.acceptance_status
            == "REJECTED_LLM_ROUTE_PLANNER_REQUEST_CONTRACT"
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }
    fallback["target_prover_family"] = row.target_prover_family
    fallback["replan_metadata"] = metadata
    fallback["llm_route_planner_row_id"] = row.llm_route_planner_row_id
    fallback["llm_route_planner_acceptance_status"] = row.acceptance_status
    fallback["llm_route_planner_route_adoption_status"] = row.route_adoption_status
    fallback["llm_route_planner_route_adoption_blockers"] = list(
        row.route_adoption_blockers
    )
    return fallback


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
    llm_refinement_hooks = _merge_dict_rows(
        llm_refinement_hooks,
        _llm_refinement_hooks_for_residual_interpretations(
            row.residual_interpretations,
            selected_primitives=selected_primitives,
            target_prover_family=row.target_prover_family,
        ),
        key_fields=("hook_kind", "queries", "acceptance_record"),
    )
    llm_refinement_hooks = _merge_dict_rows(
        llm_refinement_hooks,
        _llm_refinement_hooks_for_route_review_flags(
            uncertainty_flags=row.uncertainty_flags,
            semantic_alignment_risks=row.semantic_alignment_risks,
            selected_primitives=selected_primitives,
            target_prover_family=row.target_prover_family,
        ),
        key_fields=("hook_kind", "queries", "acceptance_record"),
    )
    llm_refinement_hooks = _merge_dict_rows(
        llm_refinement_hooks,
        _llm_refinement_hooks_for_quality_control_obligations(
            row.quality_control_obligations,
            selected_primitives=selected_primitives,
            theorem_statement=str(route.get("theorem_statement", "")),
            target_prover_family=row.target_prover_family,
        ),
        key_fields=("hook_kind", "queries", "acceptance_record"),
    )
    llm_refinement_hooks = _merge_dict_rows(
        llm_refinement_hooks,
        _llm_refinement_hooks_for_feedback_summary(
            row.feedback_loop_summary,
            selected_primitives=selected_primitives,
            theorem_statement=str(route.get("theorem_statement", "")),
            target_prover_family=row.target_prover_family,
        ),
        key_fields=("hook_kind", "queries", "acceptance_record"),
    )
    llm_refinement_hooks = _merge_dict_rows(
        llm_refinement_hooks,
        _llm_refinement_hooks_for_feedback_replan_required(
            row.feedback_loop_summary,
            selected_primitives=selected_primitives,
            target_prover_family=row.target_prover_family,
        ),
        key_fields=("hook_kind", "queries", "acceptance_record"),
    )
    llm_refinement_hooks = _merge_dict_rows(
        llm_refinement_hooks,
        _llm_refinement_hooks_for_realization_coverage_witness(
            row.realization_coverage_witness,
        ),
        key_fields=("hook_kind", "queries", "acceptance_record"),
    )
    llm_route_revision_triggers = _llm_route_revision_triggers_for_search_requests(
        row.search_requests,
        target_prover_family=row.target_prover_family,
    )
    llm_route_revision_triggers = _merge_dict_rows(
        llm_route_revision_triggers,
        _llm_route_revision_triggers_for_planner_next_actions(
            row.planner_next_actions,
            target_prover_family=row.target_prover_family,
        ),
        key_fields=("trigger_kind", "condition", "next_action"),
    )
    llm_route_revision_triggers = _merge_dict_rows(
        llm_route_revision_triggers,
        _llm_route_revision_triggers_for_residual_interpretations(
            row.residual_interpretations,
            selected_primitives=selected_primitives,
        ),
        key_fields=("trigger_kind", "condition", "next_action"),
    )
    llm_route_revision_triggers = _merge_dict_rows(
        llm_route_revision_triggers,
        _llm_route_revision_triggers_for_route_review_flags(
            uncertainty_flags=row.uncertainty_flags,
            semantic_alignment_risks=row.semantic_alignment_risks,
            selected_primitives=selected_primitives,
        ),
        key_fields=("trigger_kind", "condition", "next_action"),
    )
    llm_route_revision_triggers = _merge_dict_rows(
        llm_route_revision_triggers,
        _llm_route_revision_triggers_for_quality_control_obligations(
            row.quality_control_obligations,
            selected_primitives=selected_primitives,
            target_prover_family=row.target_prover_family,
        ),
        key_fields=("trigger_kind", "condition", "next_action"),
    )
    llm_route_revision_triggers = _merge_dict_rows(
        llm_route_revision_triggers,
        _llm_route_revision_triggers_for_feedback_summary(
            row.feedback_loop_summary,
            selected_primitives=selected_primitives,
            target_prover_family=row.target_prover_family,
        ),
        key_fields=("trigger_kind", "condition", "next_action"),
    )
    llm_route_revision_triggers = _merge_dict_rows(
        llm_route_revision_triggers,
        _llm_route_revision_triggers_for_feedback_replan_required(
            row.feedback_loop_summary,
            selected_primitives=selected_primitives,
        ),
        key_fields=("trigger_kind", "condition", "next_action"),
    )
    llm_route_revision_triggers = _merge_dict_rows(
        llm_route_revision_triggers,
        _llm_route_revision_triggers_for_realization_coverage_witness(
            row.realization_coverage_witness,
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
        "llm_route_planner_planner_next_actions": [
            dict(item) for item in row.planner_next_actions
        ],
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
        "llm_route_planner_quality_control_obligations": dict(
            row.quality_control_obligations
        ),
        "llm_route_planner_feedback_loop_summary": dict(row.feedback_loop_summary),
        "llm_route_planner_errors": list(row.errors),
        "llm_route_planner_generation_errors": list(row.generation_errors),
        "llm_route_planner_request_contract_blocked": (
            row.acceptance_status
            == "REJECTED_LLM_ROUTE_PLANNER_REQUEST_CONTRACT"
        ),
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
    quality_controls_for_metadata = _dict_value(
        row.quality_control_obligations,
        "quality_controls",
    )
    if quality_controls_for_metadata:
        metadata["quality_controls"] = quality_controls_for_metadata
        route["quality_controls"] = quality_controls_for_metadata
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
        hook_kind = _target_scoped_llm_hook_kind(
            _hook_kind_for_llm_search_request(request),
            target_prover_family=target_prover_family,
        )
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
                "quality_controls": _quality_control_payload_for_row(request),
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
    *,
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    triggers: list[dict[str, object]] = []
    for index, request in enumerate(search_requests):
        hook_kind = _target_scoped_llm_hook_kind(
            _hook_kind_for_llm_search_request(request),
            target_prover_family=target_prover_family,
        )
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
                "quality_controls": _quality_control_payload_for_row(request),
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
        hook_kind = _target_scoped_llm_hook_kind(
            _hook_kind_for_llm_planner_action(action),
            target_prover_family=target_prover_family,
        )
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
                "quality_controls": _quality_control_payload_for_row(action),
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
    *,
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    triggers: list[dict[str, object]] = []
    for index, action in enumerate(planner_next_actions):
        hook_kind = _target_scoped_llm_hook_kind(
            _hook_kind_for_llm_planner_action(action),
            target_prover_family=target_prover_family,
        )
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
                "quality_controls": _quality_control_payload_for_row(action),
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


def _llm_refinement_hooks_for_residual_interpretations(
    residual_interpretations: tuple[dict[str, object], ...],
    *,
    selected_primitives: tuple[str, ...],
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    hooks: list[dict[str, object]] = []
    for index, residual in enumerate(residual_interpretations):
        queries = _residual_interpretation_queries(residual)
        if not queries:
            continue
        resource_binding_summary = _llm_resource_binding_summary(residual)
        hooks.append(
            {
                "hook_kind": "route_revision",
                "recommended_tools": list(
                    _recommended_tools_for_llm_hook(
                        "route_revision",
                        target_prover_family=target_prover_family,
                    )
                ),
                "queries": list(queries),
                "target_primitives": list(
                    _target_primitives_for_llm_residual_interpretation(
                        residual,
                        selected_primitives=selected_primitives,
                    )
                ),
                "acceptance_record": _acceptance_record_for_llm_hook("route_revision"),
                "llm_route_planner_residual_interpretation_index": index,
                "llm_route_planner_residual_interpretation": dict(residual),
                "quality_controls": _quality_control_payload_for_row(residual),
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


def _llm_route_revision_triggers_for_residual_interpretations(
    residual_interpretations: tuple[dict[str, object], ...],
    *,
    selected_primitives: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    triggers: list[dict[str, object]] = []
    for index, residual in enumerate(residual_interpretations):
        queries = _residual_interpretation_queries(residual)
        if not queries:
            continue
        resource_binding_summary = _llm_resource_binding_summary(residual)
        residual_goal = str(residual.get("residual_goal", "")).strip()
        repair_action = str(
            residual.get("route_repair") or residual.get("repair_action") or ""
        ).strip()
        triggers.append(
            {
                "trigger_kind": "llm_route_revision_requested",
                "condition": residual_goal or queries[0],
                "next_action": _next_action_for_llm_hook(
                    "route_revision",
                    query=repair_action or "; ".join(queries),
                ),
                "target_primitives": list(
                    _target_primitives_for_llm_residual_interpretation(
                        residual,
                        selected_primitives=selected_primitives,
                    )
                ),
                "llm_route_planner_residual_interpretation_index": index,
                "llm_route_planner_residual_interpretation": dict(residual),
                "quality_controls": _quality_control_payload_for_row(residual),
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


def _residual_interpretation_queries(
    residual: Mapping[str, object],
) -> tuple[str, ...]:
    return _str_tuple(
        [
            residual.get("residual_goal", ""),
            residual.get("route_repair", ""),
            residual.get("repair_action", ""),
            residual.get("interpretation", ""),
        ]
    )


def _target_primitives_for_llm_residual_interpretation(
    residual: Mapping[str, object],
    *,
    selected_primitives: tuple[str, ...],
) -> tuple[str, ...]:
    explicit = _explicit_target_primitives_for_llm_row(
        residual,
        selected_primitives=selected_primitives,
    )
    if explicit:
        return explicit
    text = _primitive_key(" ".join(_residual_interpretation_queries(residual)))
    matched = [
        primitive
        for primitive in selected_primitives
        if _primitive_key(primitive) and _primitive_key(primitive) in text
    ]
    return _str_tuple(matched or selected_primitives[:6])


def _llm_refinement_hooks_for_route_review_flags(
    *,
    uncertainty_flags: tuple[str, ...],
    semantic_alignment_risks: tuple[str, ...],
    selected_primitives: tuple[str, ...],
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    hooks: list[dict[str, object]] = []
    for source_field, flags in (
        ("uncertainty_flags", uncertainty_flags),
        ("semantic_alignment_risks", semantic_alignment_risks),
    ):
        queries = _str_tuple(flags)
        if not queries:
            continue
        target_primitives = _target_primitives_for_llm_route_review_flags(
            queries,
            selected_primitives=selected_primitives,
        )
        hooks.append(
            {
                "hook_kind": "route_revision",
                "recommended_tools": list(
                    _recommended_tools_for_llm_hook(
                        "route_revision",
                        target_prover_family=target_prover_family,
                    )
                ),
                "queries": list(queries),
                "target_primitives": list(target_primitives),
                "acceptance_record": _acceptance_record_for_llm_route_review_flags(
                    source_field
                ),
                f"llm_route_planner_{source_field}": list(queries),
                "llm_route_planner_review_source": source_field,
                "proof_evidence_status": PROOF_EVIDENCE_STATUS,
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            }
        )
    return _merge_dict_rows(
        tuple(hooks),
        tuple(),
        key_fields=("hook_kind", "queries", "acceptance_record"),
    )


def _llm_route_revision_triggers_for_route_review_flags(
    *,
    uncertainty_flags: tuple[str, ...],
    semantic_alignment_risks: tuple[str, ...],
    selected_primitives: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    triggers: list[dict[str, object]] = []
    for source_field, flags in (
        ("uncertainty_flags", uncertainty_flags),
        ("semantic_alignment_risks", semantic_alignment_risks),
    ):
        queries = _str_tuple(flags)
        if not queries:
            continue
        trigger_kind = (
            "llm_uncertainty_review_required"
            if source_field == "uncertainty_flags"
            else "llm_semantic_alignment_review_required"
        )
        target_primitives = _target_primitives_for_llm_route_review_flags(
            queries,
            selected_primitives=selected_primitives,
        )
        triggers.append(
            {
                "trigger_kind": trigger_kind,
                "condition": "; ".join(queries),
                "next_action": _next_action_for_llm_hook(
                    "route_revision",
                    query="; ".join(queries),
                ),
                "target_primitives": list(target_primitives),
                f"llm_route_planner_{source_field}": list(queries),
                "llm_route_planner_review_source": source_field,
                "proof_evidence_status": PROOF_EVIDENCE_STATUS,
            }
        )
    return _merge_dict_rows(
        tuple(triggers),
        tuple(),
        key_fields=("trigger_kind", "condition", "next_action"),
    )


def _acceptance_record_for_llm_route_review_flags(source_field: str) -> str:
    if source_field == "semantic_alignment_risks":
        return (
            "revise the informal/formal alignment or add bounded evidence before "
            "treating semantic-risk flags as resolved"
        )
    return (
        "revise the route, search bounded evidence, or record a formal boundary "
        "before treating uncertainty flags as resolved"
    )


def _target_primitives_for_llm_route_review_flags(
    flags: tuple[str, ...],
    *,
    selected_primitives: tuple[str, ...],
) -> tuple[str, ...]:
    text = _primitive_key(" ".join(flags))
    matched = [
        primitive
        for primitive in selected_primitives
        if _primitive_key(primitive) and _primitive_key(primitive) in text
    ]
    return _str_tuple(matched or selected_primitives[:6])


def _llm_refinement_hooks_for_quality_control_obligations(
    quality_control_obligations: Mapping[str, object],
    *,
    selected_primitives: tuple[str, ...],
    theorem_statement: str,
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    pending_quality_controls = _dict_value(
        quality_control_obligations,
        "pending_quality_controls",
    )
    if not pending_quality_controls:
        return tuple()
    hook_kind = _target_scoped_llm_hook_kind(
        _hook_kind_for_llm_quality_control_obligations(
            pending_quality_controls
        ),
        target_prover_family=target_prover_family,
    )
    queries = _quality_control_obligation_queries(
        pending_quality_controls,
        theorem_statement=theorem_statement,
        hook_kind=hook_kind,
    )
    if not queries:
        return tuple()
    return (
        {
            "hook_kind": hook_kind,
            "recommended_tools": list(
                _recommended_tools_for_llm_hook(
                    hook_kind,
                    target_prover_family=target_prover_family,
                )
            ),
            "queries": list(queries),
            "target_primitives": list(selected_primitives[:6]),
            "acceptance_record": (
                "discharge pending quality controls with an admissible resource "
                "response or refinement-evidence row before route adoption"
            ),
            "quality_controls": dict(pending_quality_controls),
            "llm_route_planner_quality_control_obligations": dict(
                quality_control_obligations
            ),
            "llm_route_planner_review_source": "quality_control_obligations",
            "proof_evidence_status": PROOF_EVIDENCE_STATUS,
            "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        },
    )


def _llm_route_revision_triggers_for_quality_control_obligations(
    quality_control_obligations: Mapping[str, object],
    *,
    selected_primitives: tuple[str, ...],
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    pending_quality_controls = _dict_value(
        quality_control_obligations,
        "pending_quality_controls",
    )
    if not pending_quality_controls:
        return tuple()
    hook_kind = _target_scoped_llm_hook_kind(
        _hook_kind_for_llm_quality_control_obligations(
            pending_quality_controls
        ),
        target_prover_family=target_prover_family,
    )
    queries = _quality_control_obligation_queries(
        pending_quality_controls,
        theorem_statement="",
        hook_kind=hook_kind,
    )
    if not queries:
        return tuple()
    return (
        {
            "trigger_kind": "quality_control_evidence_required",
            "condition": "; ".join(queries),
            "next_action": _next_action_for_llm_hook(
                hook_kind,
                query="; ".join(queries),
            ),
            "target_primitives": list(selected_primitives[:6]),
            "quality_controls": dict(pending_quality_controls),
            "llm_route_planner_quality_control_obligations": dict(
                quality_control_obligations
            ),
            "llm_route_planner_review_source": "quality_control_obligations",
            "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        },
    )


def _hook_kind_for_llm_quality_control_obligations(
    pending_quality_controls: Mapping[str, object],
) -> str:
    text = _primitive_key(
        " ".join(
            [
                *pending_quality_controls.keys(),
                *[
                    item
                    for values in pending_quality_controls.values()
                    for item in _str_tuple(values)
                ],
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
            "kernel",
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
        )
    ):
        return "literature_discovery"
    return "route_revision"


def _quality_control_obligation_queries(
    pending_quality_controls: Mapping[str, object],
    *,
    theorem_statement: str,
    hook_kind: str,
) -> tuple[str, ...]:
    summary_parts = [
        f"{field_name}={', '.join(_str_tuple(values))}"
        for field_name, values in pending_quality_controls.items()
        if _str_tuple(values)
    ]
    return _str_tuple(
        [
            "discharge pending quality controls: " + "; ".join(summary_parts)
            if summary_parts
            else "",
            theorem_statement if hook_kind == "proof_state_feedback" else "",
        ]
    )


def _llm_refinement_hooks_for_feedback_summary(
    feedback_summary: Mapping[str, object],
    *,
    selected_primitives: tuple[str, ...],
    theorem_statement: str,
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    hooks: list[dict[str, object]] = []
    for index, action in enumerate(
        _dict_tuple(feedback_summary.get("recommended_next_actions", []))
    ):
        hook_kind = _target_scoped_llm_hook_kind(
            _hook_kind_for_llm_feedback_action(action),
            target_prover_family=target_prover_family,
        )
        queries = _feedback_action_queries(
            action,
            theorem_statement=theorem_statement,
            hook_kind=hook_kind,
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
                    _target_primitives_for_llm_feedback_action(
                        action,
                        selected_primitives=selected_primitives,
                    )
                ),
                "acceptance_record": _acceptance_record_for_llm_feedback_action(
                    action,
                    hook_kind,
                ),
                "llm_route_planner_feedback_next_action_index": index,
                "llm_route_planner_feedback_next_action": dict(action),
                "quality_controls": _quality_control_payload_for_feedback_action(
                    action
                ),
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


def _llm_route_revision_triggers_for_feedback_summary(
    feedback_summary: Mapping[str, object],
    *,
    selected_primitives: tuple[str, ...],
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    triggers: list[dict[str, object]] = []
    for index, action in enumerate(
        _dict_tuple(feedback_summary.get("recommended_next_actions", []))
    ):
        hook_kind = _target_scoped_llm_hook_kind(
            _hook_kind_for_llm_feedback_action(action),
            target_prover_family=target_prover_family,
        )
        queries = _feedback_action_queries(
            action,
            theorem_statement="",
            hook_kind=hook_kind,
        )
        if not queries and not _planner_action_resource_refs(action):
            continue
        resource_binding_summary = _llm_resource_binding_summary(action)
        triggers.append(
            {
                "trigger_kind": _trigger_kind_for_llm_feedback_action(action, hook_kind),
                "condition": "; ".join(queries)
                or str(action.get("action", "")).strip()
                or str(action.get("source", "")).strip(),
                "next_action": _next_action_for_llm_hook(
                    hook_kind,
                    query="; ".join(queries),
                ),
                "target_primitives": list(
                    _target_primitives_for_llm_feedback_action(
                        action,
                        selected_primitives=selected_primitives,
                    )
                ),
                "llm_route_planner_feedback_next_action_index": index,
                "llm_route_planner_feedback_next_action": dict(action),
                "quality_controls": _quality_control_payload_for_feedback_action(
                    action
                ),
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


def _llm_refinement_hooks_for_feedback_replan_required(
    feedback_summary: Mapping[str, object],
    *,
    selected_primitives: tuple[str, ...],
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    if not _feedback_replan_requires_standalone_hook(feedback_summary):
        return tuple()
    queries = _feedback_replan_queries(feedback_summary)
    return (
        {
            "hook_kind": "route_revision",
            "recommended_tools": list(
                _recommended_tools_for_llm_hook(
                    "route_revision",
                    target_prover_family=target_prover_family,
                )
            ),
            "queries": list(queries),
            "target_primitives": list(
                _target_primitives_for_feedback_replan_required(
                    feedback_summary,
                    selected_primitives=selected_primitives,
                )
            ),
            "acceptance_record": _acceptance_record_for_llm_hook("route_revision"),
            "llm_route_planner_feedback_replan_required": True,
            "llm_route_planner_feedback_loop_summary": dict(feedback_summary),
            "proof_evidence_status": PROOF_EVIDENCE_STATUS,
            "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        },
    )


def _llm_route_revision_triggers_for_feedback_replan_required(
    feedback_summary: Mapping[str, object],
    *,
    selected_primitives: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    if not _feedback_replan_requires_standalone_hook(feedback_summary):
        return tuple()
    queries = _feedback_replan_queries(feedback_summary)
    condition = "; ".join(queries)
    return (
        {
            "trigger_kind": ROUTE_ADOPTION_BLOCKER_FEEDBACK_REPLAN,
            "condition": condition,
            "next_action": _next_action_for_llm_hook(
                "route_revision",
                query=condition,
            ),
            "target_primitives": list(
                _target_primitives_for_feedback_replan_required(
                    feedback_summary,
                    selected_primitives=selected_primitives,
                )
            ),
            "llm_route_planner_feedback_replan_required": True,
            "llm_route_planner_feedback_loop_summary": dict(feedback_summary),
            "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        },
    )


def _feedback_replan_requires_standalone_hook(
    feedback_summary: Mapping[str, object],
) -> bool:
    if not _truthy(feedback_summary.get("replan_required")):
        return False
    return not any(
        _feedback_action_is_route_revision_work(action)
        for action in _dict_tuple(feedback_summary.get("recommended_next_actions", []))
    )


def _feedback_action_is_route_revision_work(action: Mapping[str, object]) -> bool:
    source = _primitive_key(str(action.get("source", "")))
    action_name = _primitive_key(str(action.get("action", "")))
    if source in {"route_revision_overlay", "route_replan_handoff"}:
        return True
    if action_name in {
        "route_revision_recommended",
        "apply_route_revision_overlay",
        "continue_from_route_replan_handoff",
    }:
        return True
    return _hook_kind_for_llm_feedback_action(action) == "route_revision"


def _feedback_replan_queries(
    feedback_summary: Mapping[str, object],
) -> tuple[str, ...]:
    queries = _unique_strings(
        [
            *_str_tuple(feedback_summary.get("route_revision_reasons", [])),
            *_str_tuple(feedback_summary.get("repair_focus", [])),
            *_str_tuple(feedback_summary.get("residual_goals", [])),
        ]
    )
    return queries or ("feedback loop requested route replan before adoption",)


def _target_primitives_for_feedback_replan_required(
    feedback_summary: Mapping[str, object],
    *,
    selected_primitives: tuple[str, ...],
) -> tuple[str, ...]:
    realization_coverage = _dict_value(feedback_summary, "realization_coverage")
    explicit = _unique_strings(
        [
            *_str_tuple(
                realization_coverage.get("missing_selected_formal_primitives", [])
            ),
            *_str_tuple(
                realization_coverage.get("missing_delta_alignment_primitives", [])
            ),
            *_str_tuple(realization_coverage.get("omitted_cost_hint_primitives", [])),
        ]
    )
    if explicit:
        return explicit
    text = _primitive_key(
        " ".join(
            [
                *_str_tuple(feedback_summary.get("route_revision_reasons", [])),
                *_str_tuple(feedback_summary.get("repair_focus", [])),
                *_str_tuple(feedback_summary.get("residual_goals", [])),
            ]
        )
    )
    matched = [
        primitive
        for primitive in selected_primitives
        if _primitive_key(primitive) and _primitive_key(primitive) in text
    ]
    return _str_tuple(matched or selected_primitives[:6])


def _hook_kind_for_llm_feedback_action(action: Mapping[str, object]) -> str:
    source = _primitive_key(str(action.get("source", "")))
    action_name = _primitive_key(str(action.get("action", "")))
    if source in {"route_revision_overlay", "route_replan_handoff"}:
        return "route_revision"
    if action_name in {
        "route_revision_recommended",
        "apply_route_revision_overlay",
        "continue_from_route_replan_handoff",
    }:
        return "route_revision"
    refs = _structured_resource_refs(action)
    text = _primitive_key(
        " ".join(
            [
                *_feedback_action_text_values(action),
                *refs.get("resource_ids", []),
                *refs.get("tool_owner_ids", []),
                *refs.get("resource_contract_ids", []),
                str(action.get("source", "")),
            ]
        )
    )
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
    if any(
        token in text
        for token in (
            "proof_state",
            "prover",
            "diagnostic",
            "lean_lsp",
            "lsp",
            "lake",
            "kernel",
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
        )
    ):
        return "formal_library_grounding"
    return "route_revision"


def _trigger_kind_for_llm_feedback_action(
    action: Mapping[str, object],
    hook_kind: str,
) -> str:
    source = str(action.get("source", "")).strip()
    action_name = str(action.get("action", "")).strip()
    if source == "resource_request_queue":
        return "queued_resource_response_required"
    if action_name == "redispatch_resource_response_with_request_playbook":
        return "resource_response_playbook_redispatch_required"
    return _trigger_kind_for_llm_hook(hook_kind)


def _acceptance_record_for_llm_feedback_action(
    action: Mapping[str, object],
    hook_kind: str,
) -> str:
    source = str(action.get("source", "")).strip()
    action_name = str(action.get("action", "")).strip()
    if source == "resource_request_queue":
        return (
            "dispatch the queued resource request and ledger an admissible "
            "response before route adoption"
        )
    if action_name == "redispatch_resource_response_with_request_playbook":
        return (
            "redispatch the resource response with its request playbook and "
            "validate grounding before route adoption"
        )
    return _acceptance_record_for_llm_hook(hook_kind)


def _feedback_action_queries(
    action: Mapping[str, object],
    *,
    theorem_statement: str,
    hook_kind: str,
) -> tuple[str, ...]:
    return _str_tuple(
        [
            *_feedback_action_text_values(action),
            theorem_statement if hook_kind == "proof_state_feedback" else "",
        ]
    )


def _feedback_action_text_values(action: Mapping[str, object]) -> tuple[str, ...]:
    values: list[str] = []
    for field_name in (
        "operator_prompt",
        "execution_command",
        "mcp_or_cli_hint",
        "reason",
        "action",
        "request_phase",
        "acceptance_gate",
        "expected_response_artifact",
        "response_summary",
        "route_replan_handoff_id",
        "route_revision_overlay_id",
        "resource_request_id",
    ):
        values.extend(_str_tuple(action.get(field_name, [])))
    for field_name in (
        "acceptance_checklist",
        "rejection_triggers",
        "response_contract_fields",
        "matched_response_contract_fields",
        "missing_response_contract_fields",
        "resource_contracts",
        "commands",
        "residual_goals",
        "reasons",
    ):
        values.extend(_str_tuple(action.get(field_name, [])))
    return _str_tuple(values)


def _target_primitives_for_llm_feedback_action(
    action: Mapping[str, object],
    *,
    selected_primitives: tuple[str, ...],
) -> tuple[str, ...]:
    explicit = _explicit_target_primitives_for_llm_row(
        action,
        selected_primitives=selected_primitives,
    )
    if explicit:
        return explicit
    text = _primitive_key(" ".join(_feedback_action_text_values(action)))
    matched = [
        primitive
        for primitive in selected_primitives
        if _primitive_key(primitive) and _primitive_key(primitive) in text
    ]
    return _str_tuple(matched or selected_primitives[:6])


def _quality_control_payload_for_feedback_action(
    action: Mapping[str, object],
) -> dict[str, object]:
    payload = _quality_control_payload_for_row(action)
    resource_contracts = _str_tuple(action.get("resource_contracts", []))
    if resource_contracts:
        payload["resource_contract_ids"] = list(
            dict.fromkeys(
                [
                    *_str_tuple(payload.get("resource_contract_ids", [])),
                    *resource_contracts,
                ]
            )
        )
    return payload


def _llm_refinement_hooks_for_realization_coverage_witness(
    realization_coverage_witness: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    realization_coverage = _realization_coverage_summary_for_witness(
        realization_coverage_witness
    )
    hooks: list[dict[str, object]] = []
    for index, action in enumerate(
        _realization_feedback_next_actions(realization_coverage)
    ):
        queries = _realization_coverage_action_queries(action)
        if not queries:
            continue
        hooks.append(
            {
                "hook_kind": "route_revision",
                "recommended_tools": list(
                    _recommended_tools_for_llm_hook("route_revision")
                ),
                "queries": list(queries),
                "target_primitives": list(_str_tuple(action.get("target_primitives", []))),
                "acceptance_record": (
                    "revise or explicitly justify realization-coverage witness "
                    "gaps before standalone route adoption"
                ),
                "llm_route_planner_realization_coverage_action_index": index,
                "llm_route_planner_realization_coverage_action": dict(action),
                "llm_route_planner_realization_coverage_witness": dict(
                    realization_coverage_witness
                ),
                "proof_evidence_status": PROOF_EVIDENCE_STATUS,
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
            }
        )
    return _merge_dict_rows(
        tuple(hooks),
        tuple(),
        key_fields=("hook_kind", "queries", "acceptance_record"),
    )


def _llm_route_revision_triggers_for_realization_coverage_witness(
    realization_coverage_witness: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    realization_coverage = _realization_coverage_summary_for_witness(
        realization_coverage_witness
    )
    triggers: list[dict[str, object]] = []
    for index, action in enumerate(
        _realization_feedback_next_actions(realization_coverage)
    ):
        queries = _realization_coverage_action_queries(action)
        if not queries:
            continue
        triggers.append(
            {
                "trigger_kind": _trigger_kind_for_realization_coverage_action(action),
                "condition": "; ".join(queries),
                "next_action": _next_action_for_llm_hook(
                    "route_revision",
                    query="; ".join(queries),
                ),
                "target_primitives": list(_str_tuple(action.get("target_primitives", []))),
                "llm_route_planner_realization_coverage_action_index": index,
                "llm_route_planner_realization_coverage_action": dict(action),
                "llm_route_planner_realization_coverage_witness": dict(
                    realization_coverage_witness
                ),
                "proof_evidence_status": PROOF_EVIDENCE_STATUS,
            }
        )
    return _merge_dict_rows(
        tuple(triggers),
        tuple(),
        key_fields=("trigger_kind", "condition", "next_action"),
    )


def _realization_coverage_summary_for_witness(
    realization_coverage_witness: Mapping[str, object],
) -> dict[str, object]:
    witness = _compact_realization_witness(realization_coverage_witness)
    if not witness:
        return {}
    return {
        "complete": bool(witness.get("realization_coverage_complete", False)),
        "missing_selected_formal_primitives": list(
            _str_tuple(
                witness.get("selected_primitives_missing_formal_realization_node", [])
            )
        ),
        "missing_delta_alignment_primitives": list(
            _str_tuple(witness.get("delta_primitives_missing_route_alignment_edge", []))
        ),
        "missing_delta_action_witness_primitives": list(
            _str_tuple(witness.get("delta_action_witness_missing_primitives", []))
        ),
        "delta_action_witness_required_primitives": list(
            _str_tuple(witness.get("delta_action_witness_required_primitives", []))
        ),
        "delta_action_witness_complete": bool(
            witness.get("delta_action_witness_complete", True)
        ),
        "cost_hint_baseline_primitives": list(
            _str_tuple(witness.get("cost_hint_baseline_primitives", []))
        ),
        "omitted_cost_hint_primitives": list(
            _str_tuple(witness.get("omitted_cost_hint_primitives", []))
        ),
        "cost_hint_baseline_coverage_complete": bool(
            witness.get("cost_hint_baseline_coverage_complete", True)
        ),
        "witnesses": [dict(witness)],
    }


def _realization_coverage_action_queries(
    action: Mapping[str, object],
) -> tuple[str, ...]:
    return _str_tuple(
        [
            action.get("action", ""),
            action.get("reason", ""),
            *(_str_tuple(action.get("target_primitives", []))),
        ]
    )


def _trigger_kind_for_realization_coverage_action(
    action: Mapping[str, object],
) -> str:
    action_name = str(action.get("action", "")).strip()
    if action_name == "review_or_restore_omitted_cost_hint_primitives":
        return "omitted_cost_hint_primitives_review_required"
    if action_name == "add_minimal_delta_action_witnesses":
        return "minimal_delta_action_witness_repair_required"
    return "realization_coverage_repair_required"


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
                    quality_controls = _quality_control_payload_for_row(row)
                    bindings.append(
                        {
                            "source": source,
                            "resource_request_id": request_id,
                            "resource_id": resource_id,
                            **(
                                {"quality_controls": quality_controls}
                                if quality_controls
                                else {}
                            ),
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


def _quality_control_payload_for_row(row: Mapping[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for field_name in (
        "resource_contract_ids",
        "required_quality_signals",
        "quality_gates",
        "response_validation_signals",
        "stop_conditions",
    ):
        values = _str_tuple(row.get(field_name, []))
        if values:
            payload[field_name] = list(values)
    return payload


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


def _target_scoped_llm_hook_kind(
    hook_kind: str,
    *,
    target_prover_family: str,
) -> str:
    if (
        hook_kind == "lean_library_grounding"
        and _target_prover_key(target_prover_family) != "lean4"
    ):
        return "formal_library_grounding"
    return hook_kind


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
    explicit = _explicit_target_primitives_for_llm_row(
        request,
        selected_primitives=selected_primitives,
    )
    if explicit:
        return explicit
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


def _explicit_target_primitives_for_llm_row(
    row: Mapping[str, object],
    *,
    selected_primitives: tuple[str, ...],
) -> tuple[str, ...]:
    selected_by_key = {
        _primitive_key(primitive): primitive
        for primitive in selected_primitives
        if _primitive_key(primitive)
    }
    values: list[str] = []
    seen: set[str] = set()
    for field_name in (
        "target_primitive",
        "target_primitives",
        "primitive",
        "primitives",
    ):
        for primitive in _primitive_values(row.get(field_name)):
            primitive_text = str(primitive).strip()
            primitive_key = _primitive_key(primitive_text)
            if not primitive_key or primitive_key in seen:
                continue
            seen.add(primitive_key)
            values.append(str(selected_by_key.get(primitive_key, primitive_text)))
    return _str_tuple(values[:12])


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
        row: dict[str, object] = {
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
        for field_name in (
            "source_fields",
            "target_primitives",
            "supported_target_primitives",
            "unsupported_target_primitives",
            "source_refs",
            "matched_terms",
        ):
            values = _candidate_declaration_row_list_field_values(
                field_name,
                value.get(field_name, []),
            )
            if values:
                row[field_name] = list(values)
        rows.append(row)
    compact_by_key: dict[tuple[str, str, str], dict[str, object]] = {}
    for row in rows:
        key = (
            _formal_declaration_key(row.get("declaration", "")),
            _target_prover_key(row.get("target_prover_family", "")),
            str(row.get("source_field", "")),
        )
        if not key[0]:
            continue
        if key not in compact_by_key:
            compact_by_key[key] = dict(row)
            continue
        existing = compact_by_key[key]
        for field_name in (
            "source_fields",
            "target_primitives",
            "supported_target_primitives",
            "unsupported_target_primitives",
            "source_refs",
            "matched_terms",
        ):
            merged = tuple(
                dict.fromkeys(
                    [
                        *_str_tuple(existing.get(field_name, [])),
                        *_str_tuple(row.get(field_name, [])),
                    ]
                )
            )
            if merged:
                existing[field_name] = list(merged)
    return tuple(compact_by_key.values())


def _candidate_declaration_row_list_field_values(
    field_name: str,
    value: Any,
) -> tuple[str, ...]:
    if field_name in {
        "target_primitives",
        "supported_target_primitives",
        "unsupported_target_primitives",
    }:
        return _primitive_values(value)
    return _str_tuple(value)


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
    (
        out_dir / "formalization_gap_planner_llm_route_planner_manifest.schema.json"
    ).write_text(
        json.dumps(llm_route_planner_manifest_json_schema(), indent=2),
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
    library_alignment_summaries = []
    for row in payload.get("request_packets", []):
        if not isinstance(row, Mapping):
            continue
        summary = _request_library_alignment_summary(row)
        if summary:
            library_alignment_summaries.append(summary)
    (
        out_dir
        / "formalization_gap_planner_llm_route_planner_library_alignment_summaries.jsonl"
    ).write_text(
        "\n".join(
            json.dumps(row, sort_keys=True)
            for row in library_alignment_summaries
            if isinstance(row, dict)
        )
        + ("\n" if library_alignment_summaries else ""),
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
    (
        out_dir
        / "formalization_gap_planner_llm_route_planner_library_alignment_summary.schema.json"
    ).write_text(
        json.dumps(llm_route_planner_library_alignment_summary_json_schema(), indent=2),
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
    (out_dir / "formalization_gap_planner_llm_route_planner_seed_route_selection.schema.json").write_text(
        json.dumps(llm_route_planner_seed_route_selection_json_schema(), indent=2),
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
        f"- Request tier-decision basis: {payload.get('by_request_model_tier_decision_basis')}",
        f"- Invalid tier-decision evidence: {payload.get('n_request_model_tier_decision_evidence_invalid')}",
        f"- Request model-tier mismatches: {payload.get('n_request_model_tier_mismatches')}",
        f"- Generation preflight blocks: {payload.get('n_generation_preflight_blocked')}",
        f"- Repair attempts: {payload.get('n_generated_response_repair_attempts')}",
        f"- Repaired responses: {payload.get('n_generated_responses_repaired')}",
        f"- Repair ledger rows: {payload.get('n_repair_attempt_ledger_rows')}",
        f"- Responses present: {payload.get('n_response_present')}",
        f"- Provider failures: {payload.get('n_provider_failures')}",
        f"- Rows with generator metadata: {payload.get('n_rows_with_generator_metadata')}",
        f"- Accepted route plans: {payload.get('n_accepted_route_plans')}",
        f"- Route adoption ready: {payload.get('n_route_adoption_ready')}",
        f"- Route adoption pending refinement: {payload.get('n_route_adoption_pending_refinement')}",
        f"- Standalone replay gate OK: {payload.get('standalone_replay_gate_ok')}",
        f"- Standalone replay adoptable candidates: {payload.get('n_standalone_replay_adoptable_route_candidates')}/{payload.get('n_standalone_replay_route_candidates')}",
        f"- Standalone replay blockers: {payload.get('standalone_replay_gate_blockers')}",
        f"- Route adoption blocker counts: {payload.get('route_adoption_blocker_counts')}",
        f"- Awaiting LLM response: {payload.get('n_awaiting_llm_response')}",
        f"- Rejected: {payload.get('n_rejected')}",
        f"- Informal DAG nodes: {payload.get('n_informal_knowledge_dag_nodes')}",
        f"- Formal realization nodes: {payload.get('n_formal_realization_dag_nodes')}",
        f"- Alignment edges: {payload.get('n_route_alignment_edges')}",
        f"- Delta action witness required/missing: {payload.get('n_delta_action_witness_required_primitives')}/{payload.get('n_delta_action_witness_missing_primitives')}",
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
