from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_VERSION = 1
PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID = (
    "urn:ai-statistician:schemas:library-aware-formalization-gap-plan:1"
)
PORTABLE_FORMALIZATION_GAP_PLAN_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:library-aware-formalization-gap-plan-row:1"
)
ROUTE_ALIGNMENT_EDGE_SCHEMA_ID = (
    "urn:ai-statistician:schemas:formalization-gap-planner-route-alignment-edge:1"
)
LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME = "library_aware_formalization_gap_planner"
LEGACY_LEAN_TARGET_PROVER_FAMILY = "lean4_adapter_with_portable_gap_schema"
TARGET_PROVER_FAMILY = "lean4"
LEGACY_TARGET_PROVER_FAMILY_ALIASES = {
    "coq": "rocq",
    "coq8": "rocq",
    "coq_rocq": "rocq",
    "rocq_coq": "rocq",
    "hol_4": "hol4",
    "lean": "lean4",
    "lean_4": "lean4",
    LEGACY_LEAN_TARGET_PROVER_FAMILY: "lean4",
    "isabelle_hol": "isabelle",
}
FORMALIZATION_DELTA_OBJECTIVE = (
    "Given a target theorem T and a current formal library snapshot L, find a "
    "small additional formalization Delta of existing reuse, wrappers, bridge "
    "lemmas, source ports, or new primitives such that L + Delta is a plausible "
    "route to a kernel-checked proof of T."
)
OPTIMIZATION_OBJECTIVES = (
    "minimize_new_declarations",
    "minimize_import_cone",
    "minimize_dependency_depth",
    "minimize_typeclass_and_statement_shape_risk",
    "maximize_existing_verified_library_reuse",
    "avoid_field_wide_formalization_not_needed_for_this_goal",
)
PROOF_EVIDENCE_STATUS = "GOAL_CONDITIONED_MINIMAL_FORMALIZATION_PLAN_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Goal-conditioned minimal formalization plans are route-selection and "
    "cost-planning artifacts, not theorem proof evidence. They identify a small "
    "additional formalization cut for a target theorem, but only target-prover "
    "kernel verification can prove the target."
)
PORTABLE_NODE_STATUSES = (
    "target",
    "existing_in_library",
    "selected_for_delta",
    "excluded_from_current_minimal_cut",
)
PORTABLE_EDGE_KINDS = ("AND_requires", "OR_not_selected")
PARETO_PROFILES = (
    "reuse_existing_library",
    "minimal_bridge_cut",
    "wrapper_only_delta",
    "source_grounded_port",
    "least_first_principles_exposure",
    "manual_review_delta",
)
INTERACTIVE_ROUTE_STAGES = (
    "target_intake",
    "literature_evidence_search",
    "informal_route_dag",
    "formal_library_coverage_mapping",
    "minimal_delta_planning",
    "leaf_prover_attempts",
    "residual_feedback_revision",
)
LEGACY_ROUTE_STAGE_ALIASES = {
    "lean_coverage_mapping": "formal_library_coverage_mapping",
}
LEGACY_EVALUATION_METRIC_ALIASES = {
    "lean_effort_new_declarations": "target_prover_effort_new_declarations",
    "lean_effort_failed_attempts": "target_prover_effort_failed_attempts",
}
LEGACY_ABLATION_ALIASES = {
    "no_lean_rag": "no_formal_grounding",
    "no_lsp_feedback": "no_proof_state_feedback",
}
LEGACY_FORMAL_REALIZATION_FIELD_ALIASES = {
    "lean_realization_dag_nodes": "formal_realization_dag_nodes",
    "lean_realization_dag_edges": "formal_realization_dag_edges",
    "revised_lean_realization_dag_nodes": "revised_formal_realization_dag_nodes",
}


def normalize_target_prover_family(value: object) -> str:
    """Return the portable canonical target-prover family key."""

    key = (
        str(value or "")
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )
    key = "_".join(part for part in key.split("_") if part)
    key = LEGACY_TARGET_PROVER_FAMILY_ALIASES.get(key, key)
    if key in {"lean", "lean4", "lean_4"} or key.startswith(
        ("lean4_", "lean_4_", "lean_")
    ):
        return "lean4"
    if key in {"coq", "coq8", "rocq"} or key.startswith(
        ("rocq_", "coq_", "coq8_")
    ):
        return "rocq"
    if key in {"isabelle", "isabelle_hol"} or key.startswith(
        ("isabelle_", "isabellehol_")
    ):
        return "isabelle"
    if key == "agda" or key.startswith("agda_"):
        return "agda"
    if key in {"hol4", "hol_4"} or key.startswith(("hol4_", "hol_4_")):
        return "hol4"
    return key


def normalize_manifest_target_prover_family(value: object) -> str:
    """Normalize a scalar or mixed target-prover manifest value."""

    text = str(value or "").strip()
    if not text:
        return ""
    if not text.lower().startswith("mixed:"):
        return normalize_target_prover_family(text)
    targets = sorted(
        {
            normalize_target_prover_family(item)
            for item in text.split(":", 1)[1].split(",")
            if normalize_target_prover_family(item)
        }
    )
    if not targets:
        return ""
    if len(targets) == 1:
        return targets[0]
    return "mixed:" + ",".join(targets)


def normalized_target_prover_family_counts(values: object) -> dict[str, int]:
    """Normalize target-prover count-map keys from rows or manifests."""

    if isinstance(values, dict):
        counts: dict[str, int] = {}
        for key, raw_count in values.items():
            target = (
                "missing"
                if str(key or "").strip() == "missing"
                else normalize_target_prover_family(key)
            )
            if not target:
                target = "missing"
            try:
                count = int(raw_count)
            except (TypeError, ValueError):
                continue
            counts[target] = counts.get(target, 0) + count
        return dict(sorted(counts.items()))
    counts: dict[str, int] = {}
    if isinstance(values, (list, tuple)):
        for value in values:
            target = normalize_target_prover_family(value) or "missing"
            counts[target] = counts.get(target, 0) + 1
    return dict(sorted(counts.items()))


def planner_contract(library_snapshot_ref: str) -> dict[str, object]:
    return {
        "component": LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
        "schema_id": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
        "schema_version": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_VERSION,
        "library_snapshot_ref": library_snapshot_ref,
        "input_contract": {
            "target_theorem": "formal skeleton or informal theorem goal plus assumptions",
            "library_snapshot": "indexed declarations, proof-bank actions, coverage rows, and route queue",
            "optional_context": "informal proof steps, source citations, prior verifier attempts",
        },
        "output_contract": {
            "existing_reuse_nodes": "already available declarations or verified obligations",
            "minimal_additional_formalization_nodes": "wrappers, bridge lemmas, ports, or new primitives selected for this theorem",
            "source_snippets": "bounded source excerpts attached to informal route or delta nodes; these are route evidence, not proof evidence",
            "and_or_plan": "AND requirements and OR alternatives excluded from the current minimal cut",
            "work_packets": "bounded theorem-prover tasks with source and kernel-verification gates",
        },
        "portable_node_statuses": list(PORTABLE_NODE_STATUSES),
        "portable_edge_kinds": list(PORTABLE_EDGE_KINDS),
        "route_alignment_edge_schema_id": ROUTE_ALIGNMENT_EDGE_SCHEMA_ID,
        "pareto_profiles": list(PARETO_PROFILES),
        "proof_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def portable_work_packet_contract() -> dict[str, object]:
    return {
        "required_fields": [
            "primitive",
            "action_class",
            "expected_cost",
            "worker_packet_kind",
            "required_gate",
        ],
        "adapter_fields": [
            "prover_system",
            "library_snapshot_ref",
            "candidate_statement",
            "candidate_imports",
            "verifier_command",
        ],
        "acceptance_gate": (
            "kernel verification in the target prover plus no placeholder axioms/sorries"
        ),
    }


def interactive_route_synthesis_contract() -> dict[str, object]:
    return {
        "loop": list(INTERACTIVE_ROUTE_STAGES),
        "legacy_stage_aliases": dict(LEGACY_ROUTE_STAGE_ALIASES),
        "bounded_expansion_policy": [
            "start from the target theorem and expand literature only until the proof route stabilizes",
            "stop adding papers when no new required primitive or assumption is introduced",
            "search the target prover library for every informal route node before proposing new formalization",
            "let target-prover diagnostics trigger focused literature or library search only for residual gaps",
        ],
        "two_dag_contract": {
            "informal_knowledge_dag": (
                "source-backed definitions, assumptions, proof steps, and theorem variants"
            ),
            "formal_realization_dag": (
                "current formal-library declarations, near matches, wrappers, "
                "bridge lemmas, source ports, new primitives, and excluded alternatives"
            ),
            "lean_realization_dag": (
                "Lean-compatible alias for the current target-prover realization "
                "DAG when the execution backend is Lean"
            ),
            "alignment_edges": (
                "map informal nodes to exact existing formal declarations, near "
                "matches, or selected delta work packets"
            ),
        },
        "tool_roles": {
            "literature_discovery": [
                "Paperclip MCP/CLI",
                "PaperQA2",
                "OpenScholar",
                "Semantic Scholar API",
                "OpenAlex Works API",
                "arXiv",
            ],
            "pdf_math_extraction": ["GROBID", "Nougat", "olmOCR", "Marker"],
            "formal_library_grounding": [
                "local formal-source index",
                "target prover library search",
                "LeanSearch/Loogle/LeanExplore for Lean targets",
                "Rocq/coq-lsp/SerAPI for Rocq targets",
                "Isabelle find_theorems/Sledgehammer for Isabelle targets",
            ],
            "proof_state_feedback": [
                "target-prover proof-state adapter",
                "target-prover LSP/kernel diagnostics",
                "target-prover build/check command",
                "lean-lsp-mcp / Lean LSP / lake build for Lean targets",
                "Rocq/coq-lsp / SerAPI for Rocq targets",
                "Isabelle server / Sledgehammer for Isabelle targets",
                "Agda interaction-mode adapter for Agda targets",
            ],
            "premise_and_proof_search": [
                "target-prover theorem search and premise selection",
                "LeanDojo/ReProver / LeanHammer for Lean targets",
                "aesop / simp / exact? / apply? for Lean targets",
                "Rocq Search / coq-lsp / SerAPI for Rocq targets",
                "Isabelle find_theorems / Sledgehammer for Isabelle targets",
            ],
        },
        "proof_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def evaluation_protocol() -> dict[str, object]:
    return {
        "primary_metrics": [
            "route_recall",
            "delta_precision",
            "target_prover_effort_new_declarations",
            "target_prover_effort_failed_attempts",
            "coverage_classification_accuracy",
            "source_faithfulness",
            "downstream_kernel_verified_success",
        ],
        "legacy_metric_aliases": dict(LEGACY_EVALUATION_METRIC_ALIASES),
        "minimality_proxy": (
            "remove each proposed delta node and check whether the theorem route still "
            "has a kernel-verified proof or a lower-cost alternative"
        ),
        "ablations": [
            "no_literature_evidence",
            "no_formal_grounding",
            "no_proof_state_feedback",
            "no_route_planner",
            "whole_field_formalization_baseline",
        ],
        "legacy_ablation_aliases": dict(LEGACY_ABLATION_ALIASES),
        "benchmark_design": [
            "hide existing proved theorem routes and ask the planner to rediscover the minimal delta",
            "compare predicted route nodes against actual target-prover dependencies and proof obligations",
            "include SorryDB-style open sorry tasks for external validity",
            "track human interventions and build time in addition to proof success",
        ],
    }


def portable_gap_plan_json_schema() -> dict[str, object]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
        "title": "Library-Aware Formalization Gap Plan",
        "description": (
            "Portable manifest contract for theorem-conditioned formalization "
            "gap planning across proof assistant ecosystems."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "portable_schema_id",
            "portable_schema_version",
            "component_name",
            "target_prover_family",
            "library_snapshot_ref",
            "formalization_delta_objective",
            "optimization_objectives",
            "planner_contract",
            "interactive_route_synthesis_contract",
            "evaluation_protocol",
            "legacy_formal_realization_field_aliases",
            "rows",
            "proof_evidence_status",
            "proof_evidence_boundary",
        ],
        "properties": {
            "schema_version": {"type": "integer"},
            "portable_schema_id": {"const": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID},
            "portable_schema_version": {
                "const": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_VERSION
            },
            "component_name": {"const": LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME},
            "target_prover_family": {"type": "string"},
            "library_snapshot_ref": {"type": "string", "minLength": 1},
            "formalization_delta_objective": {"type": "string", "minLength": 1},
            "optimization_objectives": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
            },
            "planner_contract": {"type": "object"},
            "interactive_route_synthesis_contract": {"type": "object"},
            "evaluation_protocol": {"type": "object"},
            "legacy_formal_realization_field_aliases": {
                "type": "object",
                "required": sorted(LEGACY_FORMAL_REALIZATION_FIELD_ALIASES),
                "properties": {
                    key: {"type": "string", "const": value}
                    for key, value in LEGACY_FORMAL_REALIZATION_FIELD_ALIASES.items()
                },
            },
            "n_goal_plans": {"type": "integer", "minimum": 0},
            "n_target_prover_families": {"type": "integer", "minimum": 0},
            "by_target_prover_family": {
                "type": "object",
                "additionalProperties": {"type": "integer", "minimum": 0},
            },
            "n_and_or_plan_nodes": {"type": "integer", "minimum": 0},
            "n_and_or_plan_edges": {"type": "integer", "minimum": 0},
            "n_informal_knowledge_dag_nodes": {"type": "integer", "minimum": 0},
            "n_informal_knowledge_dag_edges": {"type": "integer", "minimum": 0},
            "n_formal_realization_dag_nodes": {"type": "integer", "minimum": 0},
            "n_formal_realization_dag_edges": {"type": "integer", "minimum": 0},
            "n_lean_realization_dag_nodes": {"type": "integer", "minimum": 0},
            "n_lean_realization_dag_edges": {"type": "integer", "minimum": 0},
            "n_route_alignment_edges": {"type": "integer", "minimum": 0},
            "n_route_revision_triggers": {"type": "integer", "minimum": 0},
            "n_portable_work_packets": {"type": "integer", "minimum": 0},
            "rows": {
                "type": "array",
                "items": {"$ref": "#/$defs/plan_row"},
            },
            "proof_evidence_status": {"const": PROOF_EVIDENCE_STATUS},
            "proof_evidence_boundary": {"type": "string", "minLength": 1},
        },
        "$defs": {
            "plan_row": {
                "type": "object",
                "additionalProperties": True,
                "required": [
                    "schema_version",
                    "planner_component",
                    "target_prover_family",
                    "library_snapshot_ref",
                    "formalization_delta_objective",
                    "goal_plan_id",
                    "route_id",
                    "display_name",
                    "route_class",
                    "pareto_profile",
                    "optimization_objectives",
                    "selected_primitives",
                    "existing_reuse_nodes",
                    "minimal_additional_formalization_nodes",
                    "do_not_formalize_now",
                    "next_work_packets",
                    "and_or_plan_nodes",
                    "and_or_plan_edges",
                    "route_option_cost_graph",
                    "route_option_cost_graph_summary",
                    "informal_knowledge_dag_nodes",
                    "informal_knowledge_dag_edges",
                    "formal_realization_dag_nodes",
                    "formal_realization_dag_edges",
                    "route_alignment_edges",
                    "route_revision_triggers",
                    "interactive_refinement_hooks",
                    "minimal_delta_summary",
                    "portable_work_packet_contract",
                    "proof_evidence_status",
                    "proof_evidence_boundary",
                    "ok",
                ],
                "properties": {
                    "planner_component": {
                        "const": LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME
                    },
                    "target_prover_family": {"type": "string"},
                    "library_snapshot_ref": {"type": "string", "minLength": 1},
                    "goal_plan_id": {"type": "string", "minLength": 1},
                    "route_id": {"type": "string", "minLength": 1},
                    "display_name": {"type": "string"},
                    "route_class": {"type": "string"},
                    "pareto_profile": {"enum": list(PARETO_PROFILES)},
                    "optimization_objectives": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "selected_primitives": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "existing_reuse_nodes": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/plan_node"},
                    },
                    "minimal_additional_formalization_nodes": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/plan_node"},
                    },
                    "next_work_packets": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/work_packet"},
                    },
                    "and_or_plan_nodes": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/and_or_node"},
                    },
                    "and_or_plan_edges": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/and_or_edge"},
                    },
                    "route_option_cost_graph": {
                        "type": "object",
                        "additionalProperties": True,
                        "description": (
                            "Route-option cost comparison graph used to justify "
                            "the selected minimal-delta cut. This is planning "
                            "evidence, not target-prover proof evidence."
                        ),
                    },
                    "route_option_cost_graph_summary": {
                        "type": "object",
                        "additionalProperties": True,
                        "properties": {
                            "selected_route_option_id": {"type": "string"},
                            "selected_route_option_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "unselected_route_option_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "n_route_options": {"type": "integer", "minimum": 0},
                            "n_unselected_route_options": {
                                "type": "integer",
                                "minimum": 0,
                            },
                            "comparison_only_primitives": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "proof_evidence_status": {
                                "const": PROOF_EVIDENCE_STATUS
                            },
                        },
                    },
                    "informal_knowledge_dag_nodes": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/route_dag_node"},
                    },
                    "informal_knowledge_dag_edges": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/route_dag_edge"},
                    },
                    "formal_realization_dag_nodes": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/route_dag_node"},
                    },
                    "formal_realization_dag_edges": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/route_dag_edge"},
                    },
                    "lean_realization_dag_nodes": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/route_dag_node"},
                    },
                    "lean_realization_dag_edges": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/route_dag_edge"},
                    },
                    "route_alignment_edges": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/route_alignment_edge"},
                    },
                    "standalone_input_trace": {
                        "type": "object",
                        "additionalProperties": True,
                        "description": (
                            "Optional trace copied from standalone/replan seed "
                            "routes so downstream audits can recover seed "
                            "provenance after planner roundtrip."
                        ),
                        "properties": {
                            "source_prover_family": {"type": "string"},
                            "source_target_prover_family": {"type": "string"},
                            "target_prover_family": {"type": "string"},
                            "target_library_snapshot_ref": {"type": "string"},
                            "trace_target_projection": {"type": "string"},
                            "target_theorem_context_packet": {"type": "object"},
                            "has_target_theorem_context_packet": {"type": "boolean"},
                            "has_llm_route_planner_target_theorem_context_packet": {
                                "type": "boolean"
                            },
                            "target_theorem_context_packet_kind": {"type": "string"},
                            "target_theorem_context_route_id": {"type": "string"},
                            "target_theorem_context_target_prover_family": {
                                "type": "string"
                            },
                            "target_theorem_context_theorem_statement": {
                                "type": "string"
                            },
                            "target_theorem_context_packet_target_mismatch": {
                                "type": "boolean"
                            },
                            "target_theorem_context_route_statement_differs": {
                                "type": "boolean"
                            },
                            "source_refs": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "source_snippets": {
                                "type": "array",
                                "items": {"$ref": "#/$defs/source_snippet"},
                            },
                            "primitive_source_snippets": {
                                "type": "array",
                                "items": {"type": "object"},
                            },
                            "has_source_snippets": {"type": "boolean"},
                            "quality_controls": {
                                "type": "object",
                                "additionalProperties": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "has_quality_controls": {"type": "boolean"},
                            "quality_control_fields": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "realization_coverage_witness": {
                                "type": "object",
                                "additionalProperties": True,
                            },
                            "has_realization_coverage_witness": {"type": "boolean"},
                            "realization_coverage_complete": {"type": "boolean"},
                            "realization_selected_primitives_missing_formal_realization": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "realization_delta_primitives_missing_route_alignment": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "llm_route_planner_fallback_route": {
                                "type": "boolean"
                            },
                            "llm_route_planner_seed_route_source": {
                                "type": "string"
                            },
                            "llm_route_planner_fallback_reason": {
                                "type": "string"
                            },
                            "llm_route_planner_fallback_boundary": {
                                "type": "string"
                            },
                            "llm_route_planner_fallback_source_acceptance_status": {
                                "type": "string"
                            },
                            "llm_route_planner_fallback_source_route_adoption_status": {
                                "type": "string"
                            },
                            "llm_route_planner_fallback_source_response_contract_ok": {
                                "type": "boolean"
                            },
                        },
                    },
                    "route_revision_triggers": {
                        "type": "array",
                        "items": {"type": "object"},
                    },
                    "interactive_refinement_hooks": {
                        "type": "array",
                        "items": {"type": "object"},
                    },
                    "minimal_delta_summary": {"type": "object"},
                    "portable_work_packet_contract": {"type": "object"},
                    "proof_evidence_status": {"const": PROOF_EVIDENCE_STATUS},
                    "proof_evidence_boundary": {"type": "string", "minLength": 1},
                    "ok": {"type": "boolean"},
                },
            },
            "plan_node": {
                "type": "object",
                "additionalProperties": True,
                "required": ["primitive", "action_class", "cost"],
                "properties": {
                    "primitive": {"type": "string"},
                    "action_class": {"type": "string"},
                    "cost": {"type": "integer", "minimum": 0},
                    "source_refs": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "source_snippets": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/source_snippet"},
                    },
                },
            },
            "work_packet": {
                "type": "object",
                "additionalProperties": True,
                "required": [
                    "primitive",
                    "action_class",
                    "expected_cost",
                    "worker_packet_kind",
                    "required_gate",
                ],
                "properties": {
                    "primitive": {"type": "string"},
                    "action_class": {"type": "string"},
                    "expected_cost": {"type": "integer", "minimum": 0},
                    "worker_packet_kind": {"type": "string"},
                    "required_gate": {"type": "string", "minLength": 1},
                },
            },
            "and_or_node": {
                "type": "object",
                "additionalProperties": True,
                "required": ["node_id", "kind", "status"],
                "properties": {
                    "node_id": {"type": "string", "minLength": 1},
                    "kind": {"type": "string"},
                    "status": {"enum": list(PORTABLE_NODE_STATUSES)},
                },
            },
            "and_or_edge": {
                "type": "object",
                "additionalProperties": True,
                "required": ["source", "target", "kind"],
                "properties": {
                    "source": {"type": "string", "minLength": 1},
                    "target": {"type": "string", "minLength": 1},
                    "kind": {"enum": list(PORTABLE_EDGE_KINDS)},
                },
            },
            "route_dag_node": {
                "type": "object",
                "additionalProperties": True,
                "required": ["node_id", "kind", "label"],
                "properties": {
                    "node_id": {"type": "string", "minLength": 1},
                    "kind": {"type": "string"},
                    "label": {"type": "string"},
                    "source_refs": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "source_ref": {"type": "string"},
                    "source_snippets": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/source_snippet"},
                    },
                    "evidence_status": {"type": "string"},
                },
            },
            "source_snippet": {
                "type": "object",
                "additionalProperties": True,
                "required": ["source_ref"],
                "properties": {
                    "snippet_id": {"type": "string"},
                    "source_ref": {"type": "string", "minLength": 1},
                    "source_refs": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "source_path": {"type": "string"},
                    "claim": {"type": "string"},
                    "excerpt": {"type": "string"},
                    "target_primitives": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "evidence_role": {"type": "string"},
                    "proof_evidence_status": {"type": "string"},
                    "proof_evidence_boundary": {"type": "string"},
                },
            },
            "route_dag_edge": {
                "type": "object",
                "additionalProperties": True,
                "required": ["source", "target", "kind"],
                "properties": {
                    "source": {"type": "string", "minLength": 1},
                    "target": {"type": "string", "minLength": 1},
                    "kind": {"type": "string"},
                },
            },
            "route_alignment_edge": {
                "type": "object",
                "additionalProperties": True,
                "required": [
                    "source",
                    "target",
                    "kind",
                    "edge_type",
                    "primitive",
                    "action_class",
                    "alignment_status",
                    "proof_evidence_status",
                    "proof_evidence_boundary",
                ],
                "properties": {
                    "source": {"type": "string", "minLength": 1},
                    "target": {"type": "string", "minLength": 1},
                    "kind": {"const": "aligned_to_formal_realization_candidate"},
                    "edge_type": {
                        "enum": [
                            "informal_to_formal_alignment",
                            "informal_to_lean_alignment",
                        ]
                    },
                    "primitive": {"type": "string", "minLength": 1},
                    "action_class": {"type": "string", "minLength": 1},
                    "alignment_status": {"type": "string", "minLength": 1},
                    "proof_evidence_status": {"const": PROOF_EVIDENCE_STATUS},
                    "proof_evidence_boundary": {"type": "string", "minLength": 1},
                },
            },
        },
    }


def portable_gap_plan_row_json_schema() -> dict[str, object]:
    """JSON Schema for one JSONL row from a portable gap-plan manifest."""

    manifest_schema = portable_gap_plan_json_schema()
    defs = json.loads(json.dumps(manifest_schema.get("$defs", {})))
    plan_row = defs.pop("plan_row", {})
    if not isinstance(plan_row, dict):
        plan_row = {}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": PORTABLE_FORMALIZATION_GAP_PLAN_ROW_SCHEMA_ID,
        "title": "Library-Aware Formalization Gap Plan Row",
        "description": (
            "One portable goal-conditioned formalization-gap plan row. Rows "
            "carry the informal route DAG, formal realization DAG, minimal "
            "delta cut, alignment edges, and work packets for a target theorem; "
            "they are not theorem proof evidence."
        ),
        **plan_row,
        "$defs": defs,
    }


def route_alignment_edge_json_schema() -> dict[str, object]:
    """JSON Schema for an informal-DAG to formal-realization alignment edge."""

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": ROUTE_ALIGNMENT_EDGE_SCHEMA_ID,
        "title": "Formalization Gap Planner Route Alignment Edge",
        "description": (
            "Portable edge contract connecting a source-backed informal route "
            "node to an existing declaration, near match, wrapper, bridge "
            "lemma, source port, or new primitive candidate in a target prover."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "source",
            "target",
            "kind",
            "edge_type",
            "primitive",
            "action_class",
            "alignment_status",
            "proof_evidence_status",
            "proof_evidence_boundary",
        ],
        "properties": {
            "source": {
                "type": "string",
                "minLength": 1,
                "description": "Node id in the informal knowledge DAG.",
            },
            "target": {
                "type": "string",
                "minLength": 1,
                "description": "Node id in the formal realization DAG.",
            },
            "kind": {"const": "aligned_to_formal_realization_candidate"},
            "edge_type": {
                "enum": [
                    "informal_to_formal_alignment",
                    "informal_to_lean_alignment",
                ]
            },
            "primitive": {"type": "string", "minLength": 1},
            "action_class": {"type": "string", "minLength": 1},
            "alignment_status": {"type": "string", "minLength": 1},
            "proof_evidence_status": {"const": PROOF_EVIDENCE_STATUS},
            "proof_evidence_boundary": {"type": "string", "minLength": 1},
        },
    }


def validate_route_alignment_edge(
    edge: dict[str, Any],
    schema: dict[str, object] | None = None,
) -> list[str]:
    """Validate a portable route-alignment edge against the public schema."""

    edge_schema = schema or route_alignment_edge_json_schema()
    if not isinstance(edge, dict):
        return ["route alignment edge must be an object"]
    errors: list[str] = []
    for field_name in edge_schema.get("required", []):
        if field_name not in edge:
            errors.append(f"{field_name} missing")
    properties = edge_schema.get("properties", {})
    if isinstance(properties, dict):
        for field_name, field_schema in properties.items():
            if field_name in edge and isinstance(field_schema, dict):
                errors.extend(
                    _schema_property_errors(field_name, edge[field_name], field_schema)
                )
    boundary = str(edge.get("proof_evidence_boundary", ""))
    if "not theorem proof evidence" not in boundary:
        errors.append("proof_evidence_boundary must say not theorem proof evidence")
    return errors


def validate_portable_gap_plan_row(
    row: dict[str, Any],
    schema: dict[str, object] | None = None,
    *,
    library_snapshot_ref: str = "",
) -> list[str]:
    """Validate one portable gap-plan JSONL row against the public row schema."""

    row_schema = schema or portable_gap_plan_row_json_schema()
    if not isinstance(row, dict):
        return ["portable gap-plan row must be an object"]
    errors: list[str] = []
    required = row_schema.get("required", [])
    if isinstance(required, list):
        for field_name in required:
            if isinstance(field_name, str) and field_name not in row:
                errors.append(f"{field_name} required")
    properties = row_schema.get("properties", {})
    if isinstance(properties, dict):
        for field_name, field_schema in properties.items():
            if not isinstance(field_name, str) or field_name not in row:
                continue
            if isinstance(field_schema, dict):
                errors.extend(
                    _schema_property_errors(field_name, row[field_name], field_schema)
                )
    semantic_errors: list[str] = []
    _validate_row(
        row,
        0,
        library_snapshot_ref or str(row.get("library_snapshot_ref", "")),
        semantic_errors,
    )
    errors.extend(_strip_row_prefix(error) for error in semantic_errors)
    return errors


def _strip_row_prefix(error: str) -> str:
    prefix = "rows[0]."
    return error[len(prefix) :] if error.startswith(prefix) else error


def write_route_alignment_edge_schema(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "formalization_gap_planner_route_alignment_edge.schema.json"
    path.write_text(
        json.dumps(route_alignment_edge_json_schema(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return path


def write_portable_gap_plan_row_schema(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "library_aware_formalization_gap_plan_row.schema.json"
    path.write_text(
        json.dumps(portable_gap_plan_row_json_schema(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return path


def validate_portable_gap_plan_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("portable_schema_id") != PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID:
        errors.append("portable_schema_id does not match contract schema id")
    if (
        payload.get("portable_schema_version")
        != PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_VERSION
    ):
        errors.append("portable_schema_version does not match contract schema version")
    if payload.get("component_name") != LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME:
        errors.append("component_name is not library_aware_formalization_gap_planner")
    for field_name in ("interactive_route_synthesis_contract", "evaluation_protocol"):
        if not isinstance(payload.get(field_name), dict):
            errors.append(f"{field_name} missing")
    aliases = payload.get("legacy_formal_realization_field_aliases")
    if aliases != LEGACY_FORMAL_REALIZATION_FIELD_ALIASES:
        errors.append(
            "legacy_formal_realization_field_aliases does not match contract aliases"
        )
    if not str(payload.get("library_snapshot_ref", "")):
        errors.append("library_snapshot_ref missing")
    if payload.get("proof_evidence_status") != PROOF_EVIDENCE_STATUS:
        errors.append("proof_evidence_status does not preserve planning boundary")
    if "not theorem proof evidence" not in str(payload.get("proof_evidence_boundary", "")):
        errors.append("proof_evidence_boundary must explicitly say not theorem proof evidence")

    rows = payload.get("rows", [])
    if not isinstance(rows, (list, tuple)):
        errors.append("rows must be a list")
        return errors
    target_counts: dict[str, int] = {}
    for row in rows:
        if isinstance(row, dict):
            target = (
                normalize_target_prover_family(row.get("target_prover_family", ""))
                or "missing"
            )
            target_counts[target] = target_counts.get(target, 0) + 1
    expected_target_summary = dict(sorted(target_counts.items()))
    declared_target_summary = (
        normalized_target_prover_family_counts(payload.get("by_target_prover_family"))
        if payload.get("by_target_prover_family") is not None
        else None
    )
    if declared_target_summary is not None and declared_target_summary != expected_target_summary:
        errors.append("by_target_prover_family does not match row target_prover_family counts")
    declared_manifest_target = normalize_manifest_target_prover_family(
        payload.get("target_prover_family", "")
    )
    if declared_manifest_target:
        non_missing_targets = tuple(
            target for target in expected_target_summary if target != "missing"
        )
        expected_manifest_target = (
            non_missing_targets[0]
            if len(non_missing_targets) == 1
            else "mixed:" + ",".join(non_missing_targets)
            if len(non_missing_targets) > 1
            else ""
        )
        if expected_manifest_target and declared_manifest_target != expected_manifest_target:
            errors.append("target_prover_family does not match normalized row target families")
    declared_target_family_count = payload.get("n_target_prover_families")
    if declared_target_family_count is not None:
        expected_target_family_count = sum(
            1 for target in expected_target_summary if target != "missing"
        )
        if declared_target_family_count != expected_target_family_count:
            errors.append("n_target_prover_families does not match row target_prover_family counts")
    snapshot_ref = str(payload.get("library_snapshot_ref", ""))
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"rows[{idx}] must be an object")
            continue
        _validate_row(row, idx, snapshot_ref, errors)
    return errors


def write_portable_gap_plan_schema(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "library_aware_formalization_gap_plan.schema.json"
    path.write_text(
        json.dumps(portable_gap_plan_json_schema(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return path


def _validate_row(
    row: dict[str, Any],
    idx: int,
    snapshot_ref: str,
    errors: list[str],
) -> None:
    required_fields = (
        "goal_plan_id",
        "route_id",
        "display_name",
        "pareto_profile",
        "selected_primitives",
        "next_work_packets",
        "and_or_plan_nodes",
        "and_or_plan_edges",
        "route_option_cost_graph",
        "route_option_cost_graph_summary",
        "informal_knowledge_dag_nodes",
        "informal_knowledge_dag_edges",
        "formal_realization_dag_nodes",
        "formal_realization_dag_edges",
        "route_alignment_edges",
        "route_revision_triggers",
        "interactive_refinement_hooks",
        "minimal_delta_summary",
        "portable_work_packet_contract",
        "proof_evidence_boundary",
    )
    for field_name in required_fields:
        if field_name not in row:
            errors.append(f"rows[{idx}].{field_name} missing")
    if row.get("planner_component") != LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME:
        errors.append(f"rows[{idx}].planner_component mismatch")
    if snapshot_ref and row.get("library_snapshot_ref") != snapshot_ref:
        errors.append(f"rows[{idx}].library_snapshot_ref mismatch")
    if row.get("pareto_profile") not in PARETO_PROFILES:
        errors.append(f"rows[{idx}].pareto_profile is not portable")
    if not isinstance(row.get("and_or_plan_nodes", []), (list, tuple)):
        errors.append(f"rows[{idx}].and_or_plan_nodes must be a list")
    if not isinstance(row.get("and_or_plan_edges", []), (list, tuple)):
        errors.append(f"rows[{idx}].and_or_plan_edges must be a list")
    if not isinstance(row.get("route_option_cost_graph", {}), dict):
        errors.append(f"rows[{idx}].route_option_cost_graph must be an object")
    if not isinstance(row.get("route_option_cost_graph_summary", {}), dict):
        errors.append(
            f"rows[{idx}].route_option_cost_graph_summary must be an object"
        )
    if not isinstance(row.get("next_work_packets", []), (list, tuple)):
        errors.append(f"rows[{idx}].next_work_packets must be a list")
    for dag_field in (
        "informal_knowledge_dag_nodes",
        "informal_knowledge_dag_edges",
        "formal_realization_dag_nodes",
        "formal_realization_dag_edges",
        "route_revision_triggers",
        "interactive_refinement_hooks",
        "route_alignment_edges",
    ):
        if not isinstance(row.get(dag_field, []), (list, tuple)):
            errors.append(f"rows[{idx}].{dag_field} must be a list")
    alignment_edges = row.get("route_alignment_edges", [])
    selected = set(_str_tuple(row.get("selected_primitives", [])))
    aligned = set()
    if isinstance(alignment_edges, (list, tuple)):
        for edge_idx, edge in enumerate(alignment_edges):
            if not isinstance(edge, dict):
                errors.append(f"rows[{idx}].route_alignment_edges[{edge_idx}] must be an object")
                continue
            edge_errors = validate_route_alignment_edge(edge)
            errors.extend(
                f"rows[{idx}].route_alignment_edges[{edge_idx}].{error}"
                for error in edge_errors
            )
            for field_name in ("source", "target", "kind", "primitive"):
                if not str(edge.get(field_name, "")):
                    errors.append(
                        f"rows[{idx}].route_alignment_edges[{edge_idx}].{field_name} missing"
                    )
            if edge.get("kind") != "aligned_to_formal_realization_candidate":
                errors.append(
                    f"rows[{idx}].route_alignment_edges[{edge_idx}].kind mismatch"
                )
            primitive = str(edge.get("primitive", ""))
            if primitive:
                aligned.add(primitive)
    missing_alignment = tuple(sorted(item for item in selected - aligned if item))
    if missing_alignment:
        errors.append(
            f"rows[{idx}].route_alignment_edges missing selected primitives: "
            + ",".join(missing_alignment)
        )
    summary = row.get("minimal_delta_summary", {})
    if isinstance(summary, dict) and summary.get("pareto_profile") != row.get("pareto_profile"):
        errors.append(f"rows[{idx}].minimal_delta_summary.pareto_profile mismatch")
    contract = row.get("portable_work_packet_contract", {})
    if isinstance(contract, dict):
        required_packet_fields = contract.get("required_fields", [])
        if "primitive" not in required_packet_fields:
            errors.append(f"rows[{idx}].portable_work_packet_contract missing primitive")
    else:
        errors.append(f"rows[{idx}].portable_work_packet_contract must be an object")


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(str(value) for value in values if str(value))


def _schema_property_errors(
    field_name: str,
    value: Any,
    field_schema: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    expected_type = field_schema.get("type")
    if expected_type == "string":
        if not isinstance(value, str):
            errors.append(f"{field_name} must be a string")
        elif field_schema.get("minLength") and len(value) < int(
            field_schema["minLength"]
        ):
            errors.append(f"{field_name} must be nonempty")
    elif expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{field_name} must be an integer")
        elif "minimum" in field_schema and value < int(field_schema["minimum"]):
            errors.append(f"{field_name} must be >= {field_schema['minimum']}")
    elif expected_type == "boolean" and not isinstance(value, bool):
        errors.append(f"{field_name} must be a boolean")
    elif expected_type == "array" and not isinstance(value, (list, tuple)):
        errors.append(f"{field_name} must be an array")
    elif expected_type == "object" and not isinstance(value, dict):
        errors.append(f"{field_name} must be an object")
    if "const" in field_schema and value != field_schema["const"]:
        errors.append(f"{field_name} must equal {field_schema['const']!r}")
    enum_values = field_schema.get("enum")
    if isinstance(enum_values, list) and value not in enum_values:
        errors.append(f"{field_name} must be one of {enum_values!r}")
    return errors
