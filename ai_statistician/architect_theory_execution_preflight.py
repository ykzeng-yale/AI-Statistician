from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .client_tool_loop import (
    ClientToolExecutionContext,
    ClientToolExecutionResult,
    ClientToolInputError,
    ClientToolLoopError,
    run_bounded_client_tool_loop,
)
from .fingerprint import stable_hash
from .llm_json_repair import (
    PacketValidationError,
    extract_json_object,
    generate_validated_json_packet,
)
from .model_backend import (
    ClientToolCall,
    ClientToolDefinition,
    ClientToolTurnRequest,
    GeneratorBackend,
    GeneratorRequest,
    resolve_generator_model,
)
from .metric_protocol_finding_ledger import (
    METRIC_PROTOCOL_FINDING_RESOLVED_BY_CURRENT_THEORY,
    METRIC_PROTOCOL_FINDING_UNRESOLVED,
    active_metric_protocol_finding_ledger,
    metric_protocol_finding_ledger_fingerprint,
    normalize_metric_protocol_findings,
    update_metric_protocol_finding_ledger,
)
from .research_schema import OpenResearchQuestion


ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SCHEMA_VERSION = 7
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL_VERSION = 10
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS = (
    "question_estimand_dgp_and_regime_alignment",
    "primitive_mathematical_consistency",
    "ideal_to_executable_observation_mapping",
    "termination_censoring_and_resource_feasibility",
    "guarantee_transport_and_measurement_identifiability",
)
_ESTIMATOR_DECLARATION_REQUIREMENTS = (
    (
        "procedure_identity_declared_valid",
        "established procedure identity",
    ),
    (
        "theorem_applications_declared_valid",
        "valid theorem applications",
    ),
    (
        "ideal_to_executable_mapping_declared",
        "source-declared executable mapping",
    ),
    (
        "total_or_typed_bounded_outcome_declared",
        "bounded or typed outcome",
    ),
    (
        "guarantee_transport_argument_declared",
        "guarantee transport",
    ),
)
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_NOT_PROOF_EVIDENCE = (
    "ARCHITECT_THEORY_EXECUTION_PREFLIGHT_NOT_PROOF_EVIDENCE"
)
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SOURCE_TRANSPORT = (
    "client_tool_source_query_v3"
)
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_SOURCE_SEARCHES = 3
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_TOOL_TURNS = 5
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_TERMINAL_RECOVERY_TURNS = 1
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_NO_PROGRESS_TURNS = 2
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_BOUNDARY = (
    "This independent pre-execution review can reject a TheoryDeveloper handoff "
    "that is mathematically inconsistent or cannot be represented by a finite "
    "executable experiment. It does not require theorem-proof closure before an "
    "exact finite estimator can be tested. It is not generated execution, empirical "
    "acceptance, or theorem proof evidence."
)
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL = (
    (
        "Review only the supplied pre-execution theory and research-contract "
        "artifacts. Treat every derivation, theorem card, sanity check, and expected "
        "behavior as an unverified claim. Do not invent task-family formulas, code, "
        "thresholds, observed results, or proof claims."
    ),
    (
        "Reconstruct the estimand, DGP, parameter regime, and central identities "
        "from primitive definitions. Expand probabilities and expectations over "
        "their full declared support and test at least one boundary, counterexample, "
        "or incompatible regime when a universal or finite claim is made."
    ),
    (
        "For every estimator, recompute the procedure-defining identity that carries "
        "its claimed invariant or guarantee, including normalization and sample-size "
        "scale for every executable output. Do not validate an identity by restating "
        "a theorem card, sanity check, named theorem, or the estimator's own formula."
    ),
    (
        "Audit data dependence and operator closure explicitly. If a parameter, "
        "function, model, stopping rule, tuning value, extremum, or candidate is "
        "selected from the same observations, condition on the information available "
        "before the next observation and recompute the claimed identity after that "
        "selection. A fixed-candidate result does not automatically survive plug-in, "
        "optimization, maximization, minimization, stopping, or nonlinear composition; "
        "verify the exact closure direction and hypotheses or mark it non-PASS."
    ),
    (
        "For every estimator, distinguish the ideal mathematical procedure from the "
        "finite executable observation returned to AlgorithmEngineer or "
        "SimulationEngineer. A finite input interface cannot silently implement a "
        "procedure that may require unbounded data. Describe only behavior explicitly "
        "declared by the source; a proposed repair is not current semantics."
    ),
    (
        "Use each estimator's source_interface_inventory before judging interface "
        "presence. Distinguish a present-but-incomplete contract from an absent one: "
        "never call outputs or request/response fields MISSING when the inventory "
        "lists them, and identify the exact unresolved mapping instead. Reconstruct "
        "every execution branch from the listed field meanings before proposing a "
        "counterexample; do not substitute a hypothetical branch for a declared one."
    ),
    (
        "Every executable procedure must return for every admitted sandbox input, "
        "or expose timeout, truncation, nontermination, or censoring as a separate "
        "typed outcome with a defined estimand. Distinguish not observed within a "
        "resource bound from never occurs. If the source supplies neither totality nor "
        "a typed bounded outcome, mark the mapping non-PASS instead of inventing one."
    ),
    (
        "A finite truncation, approximation, or censoring rule neither automatically "
        "destroys nor automatically preserves an ideal guarantee. Derive the needed "
        "event inclusion, error decomposition, or changed estimand before deciding."
    ),
    (
        "When executable code returns the exact finite-sample estimator named by an "
        "asymptotic theorem, transport to that output is an identity once the same "
        "DGP, estimator, regime, hypotheses, and typed boundary outcomes are explicit. "
        "Do not demand a new nonasymptotic error bound merely to authorize empirical "
        "evaluation of an asymptotic approximation."
    ),
    (
        "This stage gates metric authoring and finite execution, not mathematical or "
        "formal proof closure. A missing full proof, proof-assistant derivation, or "
        "robustness result is a downstream TheoryDeveloper, Critic, or Formalizer "
        "obligation rather than a pre-execution blocker when the declared finite "
        "estimator, DGP, estimand, measurement, and boundary outcomes are already "
        "coherent. Do not emit such downstream obligations as findings here."
    ),
    (
        "Treat an explicit assumption as the admitted scope. A documented failure "
        "outside that scope is not a robustness blocker unless the requested DGP or "
        "metric enters the excluded regime, or the claimed output silently extends "
        "the guarantee beyond the assumption."
    ),
    (
        "Check that every requested empirical performance measure is identifiable "
        "from the executable outputs under every requested DGP and regime. Reject "
        "undefined expectations, impossible return contracts, and measurements that "
        "silently replace the stated theoretical object."
    ),
    (
        "When the source invokes a named theorem, audit its exact hypotheses and "
        "conclusion. Do not replace a missing hypothesis with a nearby moment or "
        "regularity condition, and do not treat naming the theorem as verification."
    ),
    (
        "Bind every theorem hypothesis to the same DGP, probability law, filtration, "
        "or measure under which its conclusion is used. A condition established under "
        "one regime cannot discharge an assumption needed under another regime."
    ),
    (
        "Inspect source critic findings, semantic risks, self-critique, and rejected "
        "alternatives. A risk remains a blocker only when it invalidates the central "
        "procedure inside the admitted DGP or leaves an executable branch or requested "
        "measurement undefined. A proposed future repair is not a current resolution."
    ),
    (
        "Use only exact evidence anchor IDs from the supplied catalog. Evidence refs "
        "identify the claims you inspected; they do not turn TheoryDeveloper prose "
        "into evidence or proof."
    ),
    (
        "Mark uncertainty FAIL or UNCERTAIN and emit a concrete upstream-theory "
        "finding. AgentRuntime derives ACCEPT only when every required dimension and "
        "estimator check is PASS and no finding remains."
    ),
    (
        "Report only blockers to metric authoring or finite execution. Use one compact "
        "finding per distinct blocker and the minimum repair needed to make the "
        "declared contract coherent; omit optional feature requests and unrelated "
        "method improvements."
    ),
    (
        "Review dimensions, estimators, and active prior findings in the exact ordered "
        "slots supplied by ordered_review_slots. AgentRuntime owns and binds their "
        "identities; do not copy identity strings into output rows. Mark a prior "
        "finding RESOLVED_BY_CURRENT_THEORY only when current source anchors show the "
        "required change and set current_finding=null; otherwise mark it UNRESOLVED "
        "and place exactly one semantic continuation in current_finding. Do not "
        "disguise a persistent defect as a newly worded finding."
    ),
)


def _compact_value(
    value: Any,
    *,
    depth: int = 0,
    max_depth: int = 4,
    list_limit: int = 10,
    text_limit: int = 520,
) -> Any:
    if isinstance(value, Mapping):
        if depth >= max_depth:
            return {
                "compacted_mapping_keys": [
                    str(key) for key in list(value.keys())[:20]
                ]
            }
        return {
            str(key): _compact_value(
                child,
                depth=depth + 1,
                max_depth=max_depth,
                list_limit=list_limit,
                text_limit=text_limit,
            )
            for key, child in list(value.items())[:24]
        }
    if isinstance(value, (list, tuple)):
        return [
            _compact_value(
                child,
                depth=depth + 1,
                max_depth=max_depth,
                list_limit=list_limit,
                text_limit=text_limit,
            )
            for child in list(value)[:list_limit]
        ]
    if isinstance(value, str):
        return value if len(value) <= text_limit else value[: text_limit - 3] + "..."
    return value


def _project_estimator_specs(value: Any) -> tuple[list[dict[str, Any]], list[str]]:
    raw_rows = value if isinstance(value, list) else []
    projected: list[dict[str, Any]] = []
    estimator_ids: list[str] = []
    used_ids: set[str] = set()
    for index, raw_row in enumerate(raw_rows[:8]):
        if not isinstance(raw_row, Mapping):
            continue
        source_id = str(raw_row.get("id", "") or "").strip()
        estimator_id = source_id or f"estimator_{index}"
        if estimator_id in used_ids:
            estimator_id = f"{estimator_id}#{index}"
        used_ids.add(estimator_id)
        estimator_ids.append(estimator_id)
        selected = {
            key: raw_row.get(key)
            for key in (
                "id",
                "name",
                "formula",
                "algorithm",
                "algorithm_sketch",
                "inputs",
                "outputs",
                "normalization",
                "sample_size_order",
                "required_assumptions",
            )
            if key in raw_row
        }
        interface = raw_row.get("estimator_interface_contract", {})
        interface = interface if isinstance(interface, Mapping) else {}

        def field_inventory(rows: Any) -> list[dict[str, Any]]:
            fields: list[dict[str, Any]] = []
            for raw_field in rows if isinstance(rows, list | tuple) else []:
                if isinstance(raw_field, Mapping):
                    name = str(
                        raw_field.get("name", "")
                        or raw_field.get("id", "")
                        or ""
                    ).strip()
                else:
                    name = str(raw_field or "").strip()
                if name:
                    field = {"name": name[:160]}
                    if isinstance(raw_field, Mapping):
                        for key in (
                            "meaning",
                            "binding",
                            "normalization",
                            "sample_size_order",
                            "derivation_ref",
                        ):
                            value = str(raw_field.get(key, "") or "").strip()
                            if value:
                                field[key] = value[:320]
                    fields.append(field)
            return fields[:12]

        source_interface_inventory = {
            "declared_outputs": field_inventory(raw_row.get("outputs", [])),
            "request_fields": field_inventory(interface.get("request_fields", [])),
            "response_fields": field_inventory(interface.get("response_fields", [])),
        }
        projected.append(
            {
                "preflight_estimator_id": estimator_id,
                "source_interface_inventory": source_interface_inventory,
                "source_estimator": _compact_value(
                    selected,
                    max_depth=6,
                    list_limit=8,
                    text_limit=420,
                ),
            }
        )
    return projected, estimator_ids


def _active_prior_finding_rows(
    prior_finding_ledger: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        deepcopy(dict(row))
        for row in active_metric_protocol_finding_ledger(
            prior_finding_ledger
        )
    ]


def build_architect_theory_execution_preflight_material(
    *,
    question: OpenResearchQuestion,
    theory_protocol_material: Mapping[str, Any],
    upstream_research_contract: Mapping[str, Any],
    prior_finding_ledger: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    semantic_material = theory_protocol_material.get("theory_semantic_material", {})
    semantic = dict(semantic_material) if isinstance(semantic_material, Mapping) else {}
    derivation = semantic.get("theory_derivation_packet", {})
    derivation = dict(derivation) if isinstance(derivation, Mapping) else {}
    estimator_specs, estimator_ids = _project_estimator_specs(
        semantic.get("estimator_specs", [])
    )

    sections: Sequence[tuple[str, str, Any]] = (
        (
            "question",
            "research_question",
            {
                "id": question.id,
                "title": question.title,
                "description": question.description,
                "tags": list(question.tags),
            },
        ),
        ("theory.problem_card", "problem_card", semantic.get("problem_card", {})),
        ("theory.estimator_specs", "estimator_specs", estimator_specs),
        (
            "theory.simulation_ademp_spec",
            "simulation_design",
            semantic.get("simulation_ademp_spec", {}),
        ),
        (
            "theory.derivation_steps",
            "derivation_steps",
            derivation.get("derivation_steps", []),
        ),
        (
            "theory.equation_chain",
            "equation_chain",
            derivation.get("equation_chain", []),
        ),
        (
            "theory.assumption_ledger",
            "assumption_ledger",
            derivation.get("assumption_ledger", []),
        ),
        (
            "theory.sanity_checks",
            "sanity_checks",
            derivation.get("sanity_checks", []),
        ),
        (
            "theory.self_critique",
            "source_self_critique",
            derivation.get("self_critique", []),
        ),
        (
            "theory.rejected_alternatives",
            "rejected_alternatives",
            derivation.get("rejected_alternatives", []),
        ),
        (
            "theory.theorem_cards",
            "theorem_cards",
            semantic.get("theorem_cards", []),
        ),
        ("theory.lemma_cards", "lemma_cards", semantic.get("lemma_cards", [])),
        (
            "theory.critic_findings",
            "source_critic_findings",
            semantic.get("critic_findings", []),
        ),
        (
            "architect.upstream_research_contract",
            "upstream_research_contract",
            upstream_research_contract,
        ),
    )
    anchor_catalog = [
        {
            "anchor_id": anchor_id,
            "artifact_role": artifact_role,
            "content": (
                content
                if anchor_id == "theory.estimator_specs"
                else _compact_value(content)
            ),
        }
        for anchor_id, artifact_role, content in sections
    ]
    anchor_catalog_id = "architect_theory_execution_preflight_catalog:" + stable_hash(
        anchor_catalog
    )[:20]
    active_prior_findings = _active_prior_finding_rows(prior_finding_ledger)
    retrieval_context = theory_protocol_material.get("retrieval_context", {})
    retrieval_context = (
        deepcopy(dict(retrieval_context))
        if isinstance(retrieval_context, Mapping)
        else {}
    )
    prior_revision_indices = [
        int(row.get("latest_seen_revision_index", 0) or 0)
        for row in prior_finding_ledger
        if isinstance(row, Mapping)
    ]
    return {
        "schema_version": ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SCHEMA_VERSION,
        "artifact_kind": "ArchitectTheoryExecutionPreflightMaterial",
        "question_id": question.id,
        "source_theory_packet_id": str(
            theory_protocol_material.get("source_theory_packet_id", "") or ""
        ),
        "source_theory_packet_hash": str(
            theory_protocol_material.get("source_theory_packet_hash", "") or ""
        ),
        "execution_results_available": False,
        "required_estimator_ids": estimator_ids,
        "active_prior_finding_ledger": active_prior_findings,
        "active_prior_finding_ids": [
            str(row.get("finding_id", "") or "")
            for row in active_prior_findings
            if str(row.get("finding_id", "") or "").strip()
        ],
        "prior_finding_ledger": [
            deepcopy(dict(row))
            for row in prior_finding_ledger
            if isinstance(row, Mapping)
        ],
        "preflight_revision_index": (
            max(prior_revision_indices, default=-1) + 1
        ),
        "anchor_catalog_id": anchor_catalog_id,
        "anchor_catalog": anchor_catalog,
        "anchor_catalog_fingerprint": stable_hash(anchor_catalog),
        "retrieval_context": retrieval_context,
        "proof_evidence_status": ARCHITECT_THEORY_EXECUTION_PREFLIGHT_NOT_PROOF_EVIDENCE,
        "boundary": ARCHITECT_THEORY_EXECUTION_PREFLIGHT_BOUNDARY,
    }


def architect_theory_execution_preflight_json_schema(
    material: Mapping[str, Any],
) -> dict[str, Any]:
    anchor_ids = [
        str(row.get("anchor_id", "") or "")
        for row in material.get("anchor_catalog", []) or []
        if isinstance(row, Mapping) and str(row.get("anchor_id", "") or "").strip()
    ]
    estimator_ids = [
        str(value)
        for value in material.get("required_estimator_ids", []) or []
        if str(value).strip()
    ]
    active_prior_finding_ids = [
        str(value)
        for value in material.get("active_prior_finding_ids", []) or []
        if str(value).strip()
    ]
    evidence_refs = {
        "type": "array",
        "minItems": 1,
        "maxItems": min(6, max(1, len(anchor_ids))),
        "items": {"type": "string", "enum": anchor_ids},
    }
    required_fields = [
        "dimension_reviews",
        "estimator_execution_checks",
        "findings",
    ]
    if active_prior_finding_ids:
        required_fields.append("prior_finding_reviews")
    finding_properties: dict[str, Any] = {
        "severity": {
            "type": "string",
            "enum": ["medium", "high", "critical"],
        },
        "category": {
            "type": "string",
            "minLength": 1,
            "maxLength": 100,
        },
        "summary": {
            "type": "string",
            "minLength": 1,
            "maxLength": 280,
        },
        "required_change": {
            "type": "string",
            "minLength": 1,
            "maxLength": 360,
        },
        "evidence_refs": evidence_refs,
    }
    finding_required_fields = [
        "severity",
        "category",
        "summary",
        "required_change",
        "evidence_refs",
    ]
    finding_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": list(finding_required_fields),
        "properties": deepcopy(finding_properties),
    }
    dimension_review_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["status", "rationale", "evidence_refs"],
        "properties": {
            "status": {
                "type": "string",
                "enum": ["PASS", "FAIL", "UNCERTAIN"],
            },
            "rationale": {
                "type": "string",
                "minLength": 1,
                "maxLength": 300,
            },
            "evidence_refs": evidence_refs,
        },
    }
    prior_finding_review_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "status",
            "rationale",
            "evidence_refs",
            "current_finding",
        ],
        "properties": {
            "status": {
                "type": "string",
                "enum": [
                    METRIC_PROTOCOL_FINDING_UNRESOLVED,
                    METRIC_PROTOCOL_FINDING_RESOLVED_BY_CURRENT_THEORY,
                ],
            },
            "rationale": {
                "type": "string",
                "minLength": 1,
                "maxLength": 280,
            },
            "evidence_refs": evidence_refs,
            "current_finding": {
                "description": (
                    "Supply one semantic continuation for UNRESOLVED and null for "
                    "RESOLVED_BY_CURRENT_THEORY. AgentRuntime binds the ordered slot "
                    "to the prior and canonical finding identity."
                ),
                "anyOf": [
                    {"$ref": "#/$defs/finding"},
                    {"type": "null"},
                ],
            },
        },
    }

    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": required_fields,
        "properties": {
            "prior_finding_reviews": {
                "type": "array",
                "minItems": len(active_prior_finding_ids),
                "maxItems": len(active_prior_finding_ids),
                "description": (
                    "One review per active prior finding in ordered_review_slots "
                    "order. AgentRuntime binds each array position to its canonical "
                    "finding identity."
                ),
                "items": {"$ref": "#/$defs/prior_finding_review"},
            },
            "dimension_reviews": {
                "type": "array",
                "minItems": len(ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS),
                "maxItems": len(ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS),
                "description": (
                    "One review per dimension in ordered_review_slots order. Do not "
                    "copy dimension names into rows."
                ),
                "items": {"$ref": "#/$defs/dimension_review"},
            },
            "estimator_execution_checks": {
                "type": "array",
                "minItems": len(estimator_ids),
                "maxItems": len(estimator_ids),
                "description": (
                    "One check per estimator in ordered_review_slots order. Do not "
                    "copy estimator IDs into rows."
                ),
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "audit_rationale",
                        "procedure_identity_declared_valid",
                        "theorem_applications_declared_valid",
                        "ideal_to_executable_mapping_declared",
                        "total_or_typed_bounded_outcome_declared",
                        "guarantee_transport_argument_declared",
                        "boundary_or_counterexample",
                        "status",
                        "evidence_refs",
                    ],
                    "properties": {
                        "audit_rationale": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 720,
                            "description": (
                                "Compactly audit the source-declared procedure identity; "
                                "adaptive choices or operators; invoked theorem hypotheses "
                                "under the conclusion law; executable mapping and total or "
                                "typed bounded outcomes; and guarantee transport. Recompute "
                                "rather than restating source prose. Put each blocking defect "
                                "in findings instead of duplicating it here."
                            ),
                        },
                        "procedure_identity_declared_valid": {
                            "type": "boolean",
                            "description": (
                                "True only when the supplied derivation establishes the "
                                "recomputed identity after every declared adaptive choice "
                                "or operator; reviewer prose cannot fill a missing argument."
                            ),
                        },
                        "theorem_applications_declared_valid": {
                            "type": "boolean",
                            "description": (
                                "True only when the source establishes every invoked "
                                "theorem hypothesis under the law governing its conclusion."
                            ),
                        },
                        "ideal_to_executable_mapping_declared": {
                            "type": "boolean",
                            "description": (
                                "True only when the source explicitly maps every ideal "
                                "outcome to an executable observation."
                            ),
                        },
                        "total_or_typed_bounded_outcome_declared": {
                            "type": "boolean",
                            "description": (
                                "True only when the source establishes total return or "
                                "declares timeout, truncation, or censoring as a typed outcome."
                            ),
                        },
                        "guarantee_transport_argument_declared": {
                            "type": "boolean",
                            "description": (
                                "True only when the source derives how the ideal guarantee "
                                "applies to the executable observation or changed estimand."
                            ),
                        },
                        "boundary_or_counterexample": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 360,
                            "description": (
                                "Give one source-scoped boundary check or counterexample. "
                                "Do not add an out-of-scope robustness requirement."
                            ),
                        },
                        "status": {
                            "type": "string",
                            "enum": ["PASS", "FAIL", "UNCERTAIN"],
                        },
                        "evidence_refs": evidence_refs,
                    },
                },
            },
            "findings": {
                "type": "array",
                "maxItems": max(3, len(active_prior_finding_ids)),
                "description": (
                    "Only genuinely new defects that block metric authoring or finite "
                    "execution. Continue active prior defects only inside the ordered "
                    "prior_finding_reviews current_finding field. Exclude downstream "
                    "proof obligations and robustness outside the admitted DGP."
                ),
                "items": {"$ref": "#/$defs/finding"},
            },
        },
    }
    schema["$defs"] = {
        "dimension_review": dimension_review_schema,
        "estimator_execution_check": deepcopy(
            schema["properties"]["estimator_execution_checks"]["items"]
        ),
        "prior_finding_review": prior_finding_review_schema,
        "finding": finding_schema,
    }
    schema["properties"]["estimator_execution_checks"]["items"] = {
        "$ref": "#/$defs/estimator_execution_check"
    }
    if not active_prior_finding_ids:
        schema["properties"].pop("prior_finding_reviews", None)
        schema["$defs"].pop("prior_finding_review", None)
    return schema


def build_architect_theory_execution_preflight_prompt(
    material: Mapping[str, Any],
) -> str:
    source_material = {
        key: value
        for key, value in material.items()
        if key not in {"prior_finding_ledger", "retrieval_context"}
    }
    retrieval_context = material.get("retrieval_context", {})
    retrieval_context = (
        retrieval_context if isinstance(retrieval_context, Mapping) else {}
    )
    formal_source_groups = [
        row
        for row in retrieval_context.get("formal_source_hits", []) or []
        if isinstance(row, Mapping)
    ]
    payload = {
        "task": (
            "Decide whether this theory handoff is mathematically coherent and "
            "representable by a finite generated-code and simulation workflow before "
            "metric authoring or execution."
        ),
        "review_protocol_version": ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL_VERSION,
        "review_protocol": list(ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL),
        "ordered_review_slots": {
            "dimension_reviews": [
                {
                    "output_index": index,
                    "dimension": dimension,
                }
                for index, dimension in enumerate(
                    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS
                )
            ],
            "estimator_execution_checks": [
                {
                    "output_index": index,
                    "estimator_id": str(estimator_id),
                }
                for index, estimator_id in enumerate(
                    material.get("required_estimator_ids", []) or []
                )
            ],
            "prior_finding_reviews": [
                {
                    "output_index": index,
                    "finding_id": str(finding_id),
                }
                for index, finding_id in enumerate(
                    material.get("active_prior_finding_ids", []) or []
                )
            ],
        },
        "source_material": source_material,
        "retrieval_source_inventory": {
            "knowledge_cards": len(
                retrieval_context.get("knowledge_cards", []) or []
            ),
            "paper_sources": len(
                retrieval_context.get("paper_sources", []) or []
            ),
            "formal_source_hit_groups": len(formal_source_groups),
            "formal_source_hits": sum(
                len(row.get("hits", []) or []) for row in formal_source_groups
            ),
            "access_policy": (
                "Use search_preflight_sources in client-tool mode. Retrieval rows "
                "are context, not proof or automatic semantic authority."
            ),
        },
        "verdict_policy": (
            "Do not return an overall verdict. AgentRuntime derives it from the "
            "complete dimension, estimator, and finding rows."
        ),
    }
    return "Review the following typed packet. Return JSON only.\n\n" + json.dumps(
        payload,
        separators=(",", ":"),
        default=str,
    )


def _architect_theory_execution_preflight_submit_schema(
    material: Mapping[str, Any],
) -> dict[str, Any]:
    schema = architect_theory_execution_preflight_json_schema(material)
    finding_schema = schema["$defs"]["finding"]
    finding_schema["properties"]["source_evidence_refs"] = {
        "type": "array",
        "minItems": 1,
        "maxItems": 6,
        "items": {
            "type": "string",
            "minLength": 1,
            "maxLength": 120,
            "pattern": r"^S[1-9][0-9]*H[1-9][0-9]*$",
        },
        "description": (
            "Short source_ref handles returned by search_preflight_sources that "
            "support this blocking finding. Use S...H... handles here only. Runtime "
            "resolves them to immutable source_hit_id values. The separate "
            "evidence_refs field accepts only theory anchor IDs from its enum."
        ),
    }
    finding_schema["required"].append("source_evidence_refs")
    return schema


def _preflight_source_tokens(value: Any) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_']{1,}", str(value))
    }


def _preflight_source_row(
    *,
    source_kind: str,
    source_identity: str,
    title: str,
    location: str,
    content: Any,
    provenance: Any = None,
) -> dict[str, Any]:
    row = {
        "source_kind": str(source_kind),
        "source_identity": str(source_identity),
        "title": str(title)[:240],
        "location": str(location)[:500],
        "content": _compact_value(
            content,
            max_depth=4,
            list_limit=6,
            text_limit=420,
        ),
        "provenance": _compact_value(
            provenance or {},
            max_depth=3,
            list_limit=6,
            text_limit=300,
        ),
    }
    row["source_hit_id"] = "preflight_source_hit:" + stable_hash(row)[:20]
    return row


def _object_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    raw = getattr(value, "__dict__", None)
    return dict(raw) if isinstance(raw, Mapping) else {}


def _formal_source_hit_row(value: Any) -> dict[str, Any] | None:
    hit = _object_mapping(value)
    declaration = _object_mapping(hit.get("declaration", {}))
    if not declaration:
        declaration = hit
    name = str(
        declaration.get("name", "")
        or hit.get("name", "")
        or hit.get("declaration_name", "")
    ).strip()
    signature = str(
        declaration.get("signature", "")
        or hit.get("signature", "")
        or hit.get("statement", "")
    ).strip()
    path = str(declaration.get("path", "") or hit.get("path", "")).strip()
    line = declaration.get("line", hit.get("line", ""))
    source_id = str(
        declaration.get("source_id", "")
        or hit.get("source_id", "")
        or hit.get("provider", "")
        or "formal_library"
    ).strip()
    if not (name or signature or path):
        return None
    identity = ":".join(
        value
        for value in (source_id, path, str(line or ""), name)
        if value
    )
    return _preflight_source_row(
        source_kind="formal_library_declaration",
        source_identity=identity or stable_hash(hit),
        title=name or path or source_id,
        location=(f"{path}:{line}" if path and line else path),
        content={
            "kind": declaration.get("kind", hit.get("kind", "")),
            "namespace": declaration.get(
                "namespace", hit.get("namespace", "")
            ),
            "signature": signature,
            "reference": declaration.get(
                "reference", hit.get("reference", "")
            ),
            "matched_terms": list(hit.get("matched_terms", []) or []),
            "score": hit.get("score", 0.0),
        },
        provenance=hit.get("provenance", {}),
    )


def _preflight_source_catalog(material: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for anchor in material.get("anchor_catalog", []) or []:
        if not isinstance(anchor, Mapping):
            continue
        anchor_id = str(anchor.get("anchor_id", "") or "").strip()
        if not anchor_id:
            continue
        rows.append(
            _preflight_source_row(
                source_kind="theory_anchor",
                source_identity=anchor_id,
                title=str(anchor.get("artifact_role", "") or anchor_id),
                location=anchor_id,
                content=anchor.get("content"),
                provenance={
                    "source_theory_packet_id": material.get(
                        "source_theory_packet_id", ""
                    ),
                    "source_theory_packet_hash": material.get(
                        "source_theory_packet_hash", ""
                    ),
                },
            )
        )

    retrieval = material.get("retrieval_context", {})
    retrieval = retrieval if isinstance(retrieval, Mapping) else {}
    for source_kind, key in (
        ("retrieval_knowledge_card", "knowledge_cards"),
        ("retrieval_paper_source", "paper_sources"),
    ):
        for index, value in enumerate(retrieval.get(key, []) or []):
            if not isinstance(value, Mapping):
                continue
            identity = str(
                value.get("id", "")
                or value.get("source_id", "")
                or value.get("paper_id", "")
                or stable_hash(value)
            )
            rows.append(
                _preflight_source_row(
                    source_kind=source_kind,
                    source_identity=identity,
                    title=str(
                        value.get("title", "")
                        or value.get("name", "")
                        or f"{key}[{index}]"
                    ),
                    location=str(
                        value.get("source", "")
                        or value.get("url", "")
                        or value.get("path", "")
                    ),
                    content=value,
                    provenance=value.get("provenance", {}),
                )
            )
    for group in retrieval.get("formal_source_hits", []) or []:
        if not isinstance(group, Mapping):
            continue
        for value in group.get("hits", []) or []:
            row = _formal_source_hit_row(value)
            if row is not None:
                rows.append(row)
    return rows


def _search_preflight_sources(
    *,
    material: Mapping[str, Any],
    source_retriever: Any,
    query: str,
    source_scope: str,
    k: int,
    search_index: int,
    exclude_hit_ids: set[str] | None = None,
    prior_source_refs: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    query_tokens = _preflight_source_tokens(query)
    if not query_tokens:
        raise ClientToolInputError(
            "query must contain at least one searchable word"
        )
    allowed_kinds = {
        "theory": {"theory_anchor"},
        "retrieval_memory": {
            "retrieval_knowledge_card",
            "retrieval_paper_source",
            "formal_library_declaration",
        },
        "formal_library": {"formal_library_declaration"},
        "all": {
            "theory_anchor",
            "retrieval_knowledge_card",
            "retrieval_paper_source",
            "formal_library_declaration",
        },
    }[source_scope]
    contextual_ranked: list[tuple[float, dict[str, Any]]] = []
    formal_ranked: list[tuple[float, dict[str, Any]]] = []
    for row in _preflight_source_catalog(material):
        if row["source_kind"] not in allowed_kinds:
            continue
        row_text = json.dumps(row, default=str, ensure_ascii=False)
        row_tokens = _preflight_source_tokens(row_text)
        overlap = query_tokens.intersection(row_tokens)
        if not overlap:
            continue
        phrase_bonus = 2.0 if query.lower() in row_text.lower() else 0.0
        ranked = (
            formal_ranked
            if row["source_kind"] == "formal_library_declaration"
            else contextual_ranked
        )
        ranked.append((float(len(overlap)) + phrase_bonus, row))

    provider_errors: list[dict[str, str]] = []
    if source_scope in {"formal_library", "all"} and source_retriever is not None:
        search = getattr(source_retriever, "search", None)
        if callable(search):
            try:
                for hit in search(query, k=k) or []:
                    row = _formal_source_hit_row(hit)
                    if row is not None:
                        try:
                            score = float(_object_mapping(hit).get("score", 0.0))
                        except (TypeError, ValueError):
                            score = 0.0
                        formal_ranked.append((score, row))
            except Exception as exc:  # provider isolation belongs at the tool edge
                provider_errors.append(
                    {
                        "provider": str(
                            getattr(source_retriever, "source", "formal_source")
                        ),
                        "error_type": type(exc).__name__,
                        "detail_withheld": "true",
                    }
                )

    def deduplicate_ranked(
        rows: list[tuple[float, dict[str, Any]]],
        *,
        channel: str,
    ) -> list[dict[str, Any]]:
        deduplicated: list[dict[str, Any]] = []
        seen: set[str] = set()
        for score, row in sorted(
            rows,
            key=lambda item: (-item[0], item[1]["source_hit_id"]),
        ):
            hit_id = str(row["source_hit_id"])
            if hit_id in seen:
                continue
            seen.add(hit_id)
            deduplicated.append(
                {
                    **row,
                    "retrieval_channel": channel,
                    "retrieval_rank_within_channel": len(deduplicated) + 1,
                    "retrieval_score": score,
                }
            )
        return deduplicated

    contextual = deduplicate_ranked(
        contextual_ranked,
        channel="theory_and_retrieval_context",
    )
    formal = deduplicate_ranked(
        formal_ranked,
        channel="formal_library",
    )
    if source_scope == "formal_library":
        fused = formal
    elif source_scope == "theory":
        fused = contextual
    else:
        fused = []
        for rank in range(max(len(contextual), len(formal))):
            if rank < len(contextual):
                fused.append(contextual[rank])
            if rank < len(formal):
                fused.append(formal[rank])
    excluded = set(exclude_hit_ids or set())
    source_refs = dict(prior_source_refs or {})
    duplicate_source_refs_reused = list(
        dict.fromkeys(
            source_refs.get(str(row.get("source_hit_id", "") or ""), "")
            for row in fused
            if str(row.get("source_hit_id", "") or "") in excluded
            and source_refs.get(str(row.get("source_hit_id", "") or ""), "")
        )
    )[:12]
    unseen_fused = [
        row
        for row in fused
        if str(row.get("source_hit_id", "") or "") not in excluded
    ]
    hits = [
        {
            **row,
            "source_ref": f"S{search_index}H{index + 1}",
        }
        for index, row in enumerate(unseen_fused[:k])
    ]
    observation_core = {
        "query": query,
        "source_scope": source_scope,
        "hits": hits,
        "duplicate_source_refs_reused": duplicate_source_refs_reused,
        "provider_errors": provider_errors,
        "retrieval_fusion": (
            "round_robin_context_then_formal_v2_cross_turn_deduplicated"
            if source_scope in {"retrieval_memory", "all"}
            else "single_channel_rank_v1"
        ),
    }
    return {
        "observation_id": (
            "preflight_source_observation:"
            + stable_hash(observation_core)[:20]
        ),
        **observation_core,
        "boundary": (
            "These are runtime-returned source candidates. The reviewing model owns "
            "the semantic judgment; retrieval is not proof or automatic support."
        ),
    }


def _preflight_source_grounding_errors(packet: Mapping[str, Any]) -> list[str]:
    if packet.get("source_grounding_required") is not True:
        return []
    errors: list[str] = []
    if packet.get("source_grounding_transport") != (
        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SOURCE_TRANSPORT
    ):
        errors.append("preflight source-grounding transport mismatch")
    observations = [
        dict(row)
        for row in packet.get("preflight_source_observations", []) or []
        if isinstance(row, Mapping)
    ]
    if not observations:
        errors.append("preflight source grounding requires a source observation")
    hit_ids: set[str] = set()
    source_refs: dict[str, str] = {}
    for observation in observations:
        core = {
            key: observation.get(key)
            for key in (
                "query",
                "source_scope",
                "hits",
                "duplicate_source_refs_reused",
                "provider_errors",
                "retrieval_fusion",
            )
        }
        expected_id = "preflight_source_observation:" + stable_hash(core)[:20]
        if observation.get("observation_id") != expected_id:
            errors.append("preflight source observation identity mismatch")
        for hit in observation.get("hits", []) or []:
            if isinstance(hit, Mapping):
                hit_id = str(hit.get("source_hit_id", "") or "").strip()
                hit_identity_material = {
                    key: value
                    for key, value in hit.items()
                    if key
                    not in {
                        "source_hit_id",
                        "source_ref",
                        "retrieval_score",
                        "retrieval_channel",
                        "retrieval_rank_within_channel",
                    }
                }
                expected_hit_id = (
                    "preflight_source_hit:"
                    + stable_hash(hit_identity_material)[:20]
                )
                if hit_id != expected_hit_id:
                    errors.append("preflight source hit identity mismatch")
                if hit_id:
                    hit_ids.add(hit_id)
                source_ref = str(hit.get("source_ref", "") or "").strip()
                if not re.fullmatch(r"S[1-9][0-9]*H[1-9][0-9]*", source_ref):
                    errors.append("preflight source hit has invalid source_ref")
                elif source_ref in source_refs:
                    errors.append("preflight source_ref must be unique")
                else:
                    source_refs[source_ref] = hit_id
    findings = [
        row
        for row in packet.get("findings", []) or []
        if isinstance(row, Mapping)
    ]
    expected_bindings: list[dict[str, Any]] = []
    for finding in findings:
        refs = [
            str(value).strip()
            for value in finding.get("source_evidence_refs", []) or []
            if str(value).strip()
        ]
        invalid_refs = [ref for ref in refs if ref not in hit_ids]
        if not refs or invalid_refs:
            errors.append(
                "every preflight finding must cite runtime-returned source refs"
                + (
                    "; invalid refs: " + ", ".join(invalid_refs[:6])
                    if invalid_refs
                    else ""
                )
                + (
                    "; available handles: "
                    + ", ".join(sorted(source_refs)[:12])
                    if source_refs
                    else ""
                )
            )
        expected_bindings.append(
            {
                "finding_id": str(finding.get("finding_id", "") or ""),
                "source_evidence_refs": refs,
                "runtime_verified_source_refs": bool(
                    refs and all(ref in hit_ids for ref in refs)
                ),
                "runtime_selected_semantics": False,
            }
        )
    if packet.get("source_grounding_bindings", []) != expected_bindings:
        errors.append("preflight source-grounding bindings mismatch")
    expected_fingerprint = stable_hash(observations) if observations else ""
    if str(packet.get("preflight_source_observations_fingerprint", "") or "") != (
        expected_fingerprint
    ):
        errors.append("preflight source observation fingerprint mismatch")
    return errors


def _canonical_preflight_source_refs(
    values: Any,
    *,
    source_grounding: Mapping[str, Any],
) -> list[str]:
    ref_to_hit: dict[str, str] = {}
    for observation in source_grounding.get(
        "preflight_source_observations", []
    ) or []:
        if not isinstance(observation, Mapping):
            continue
        for hit in observation.get("hits", []) or []:
            if not isinstance(hit, Mapping):
                continue
            hit_id = str(hit.get("source_hit_id", "") or "").strip()
            source_ref = str(hit.get("source_ref", "") or "").strip()
            if hit_id:
                ref_to_hit[hit_id] = hit_id
            if source_ref and hit_id:
                ref_to_hit[source_ref] = hit_id
    canonical: list[str] = []
    for value in values or []:
        ref = str(value).strip()
        if not ref:
            continue
        resolved = ref_to_hit.get(ref, ref)
        if resolved not in canonical:
            canonical.append(resolved)
    return canonical


def _derived_verdict(packet: Mapping[str, Any]) -> str:
    dimension_rows = packet.get("dimension_reviews", [])
    estimator_rows = packet.get("estimator_execution_checks", [])
    prior_finding_reviews = packet.get("prior_finding_reviews", [])
    all_pass = bool(dimension_rows) and all(
        isinstance(row, Mapping)
        and str(row.get("status", "") or "").strip().upper() == "PASS"
        for row in dimension_rows
    )
    all_estimators_pass = all(
        isinstance(row, Mapping)
        and str(row.get("status", "") or "").strip().upper() == "PASS"
        and all(
            row.get(field) is True
            for field, _description in _ESTIMATOR_DECLARATION_REQUIREMENTS
        )
        for row in estimator_rows or []
    )
    all_prior_findings_resolved = all(
        isinstance(row, Mapping)
        and str(row.get("status", "") or "").strip().upper()
        == METRIC_PROTOCOL_FINDING_RESOLVED_BY_CURRENT_THEORY
        for row in prior_finding_reviews or []
    )
    return (
        "ACCEPT"
        if all_pass
        and all_estimators_pass
        and all_prior_findings_resolved
        and not packet.get("findings", [])
        else "REVISE"
    )


def _derived_repair_instructions(packet: Mapping[str, Any]) -> list[str]:
    return list(
        dict.fromkeys(
            str(row.get("required_change", "") or "").strip()
            for row in packet.get("findings", []) or []
            if isinstance(row, Mapping)
            and str(row.get("required_change", "") or "").strip()
        )
    )


def _derived_consistency_warnings(packet: Mapping[str, Any]) -> list[dict[str, str]]:
    dimension_rows = [
        row
        for row in packet.get("dimension_reviews", []) or []
        if isinstance(row, Mapping)
    ]
    estimator_rows = [
        row
        for row in packet.get("estimator_execution_checks", []) or []
        if isinstance(row, Mapping)
    ]
    primitive_dimension = next(
        (
            row
            for row in dimension_rows
            if str(row.get("dimension", "") or "")
            == "primitive_mathematical_consistency"
        ),
        {},
    )
    invalid_identity_ids = [
        str(row.get("estimator_id", "") or "")
        for row in estimator_rows
        if row.get("procedure_identity_declared_valid") is not True
        or row.get("theorem_applications_declared_valid") is not True
    ]
    if invalid_identity_ids and str(
        primitive_dimension.get("status", "") or ""
    ).strip().upper() == "PASS":
        return [
            {
                "warning_code": "primitive_summary_conflicts_with_estimator_checks",
                "summary": (
                    "The reviewer marked primitive mathematical consistency PASS "
                    "while at least one estimator identity or theorem application "
                    "remains unestablished. Fine-grained checks control the verdict."
                ),
                "estimator_ids": ",".join(invalid_identity_ids),
            }
        ]
    return []


def _source_interface_inventories(
    material: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    estimator_anchor = next(
        (
            row
            for row in material.get("anchor_catalog", []) or []
            if isinstance(row, Mapping)
            and row.get("anchor_id") == "theory.estimator_specs"
        ),
        {},
    )
    inventories: dict[str, dict[str, Any]] = {}
    for projected in estimator_anchor.get("content", []) or []:
        if not isinstance(projected, Mapping):
            continue
        estimator_id = str(projected.get("preflight_estimator_id", "") or "")
        inventory = projected.get("source_interface_inventory", {})
        if estimator_id and isinstance(inventory, Mapping):
            inventories[estimator_id] = dict(inventory)
    return inventories


def _invalid_estimator_declarations(
    row: Mapping[str, Any],
) -> list[tuple[str, str]]:
    return [
        (field, description)
        for field, description in _ESTIMATOR_DECLARATION_REQUIREMENTS
        if row.get(field) is not True
    ]


def _normalize_estimator_status_summaries(
    rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    normalized_rows: list[dict[str, Any]] = []
    normalizations: list[dict[str, Any]] = []
    for source_row in rows:
        row = dict(source_row)
        reported_status = str(row.get("status", "") or "").strip().upper()
        invalid_declarations = _invalid_estimator_declarations(row)
        if reported_status == "PASS" and invalid_declarations:
            row["status"] = "UNCERTAIN"
            normalizations.append(
                {
                    "estimator_id": str(row.get("estimator_id", "") or "").strip(),
                    "model_reported_status": "PASS",
                    "runtime_normalized_status": "UNCERTAIN",
                    "false_or_missing_declaration_fields": [
                        field for field, _description in invalid_declarations
                    ],
                    "rule": (
                        "A PASS estimator summary requires every granular declaration "
                        "flag to be true; the runtime only downgraded the redundant "
                        "summary and preserved all model-authored semantic fields."
                    ),
                    "runtime_selected_semantics": False,
                }
            )
        normalized_rows.append(row)
    return normalized_rows, normalizations


def _ordered_review_slot_rows(
    value: Any,
    *,
    expected_count: int,
) -> dict[int, dict[str, Any]]:
    if isinstance(value, Mapping):
        return {
            index: dict(value[f"slot_{index}"])
            for index in range(expected_count)
            if isinstance(value.get(f"slot_{index}"), Mapping)
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return {
            index: dict(row)
            for index, row in enumerate(value[:expected_count])
            if isinstance(row, Mapping)
        }
    return {}


def _normalize_packet(
    payload: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    material: Mapping[str, Any],
    model: str,
    model_tier: str,
    provider_name: str,
    raw_response: str,
    source_grounding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    body = dict(payload)
    grounding = deepcopy(dict(source_grounding or {}))
    if grounding:
        body.update(grounding)
    else:
        body.update(
            {
                "source_grounding_required": False,
                "source_grounding_transport": (
                    "legacy_structured_output_without_client_tools"
                ),
                "preflight_source_observations": [],
                "preflight_source_observations_fingerprint": "",
                "runtime_selected_review_semantics": False,
            }
        )
    raw_dimension_reviews = _ordered_review_slot_rows(
        body.get("dimension_reviews", {}),
        expected_count=len(ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS),
    )
    body["dimension_reviews"] = [
        {
            "dimension": dimension,
            **{
                key: (
                    str(value or "").strip().upper()
                    if key == "status"
                    else value
                )
                for key, value in raw_dimension_reviews[index].items()
                if key != "dimension"
            },
        }
        for index, dimension in enumerate(
            ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS
        )
        if index in raw_dimension_reviews
    ]
    active_prior_finding_ids = list(
        material.get("active_prior_finding_ids", []) or []
    )
    raw_prior_finding_reviews = _ordered_review_slot_rows(
        body.get("prior_finding_reviews", {}),
        expected_count=len(active_prior_finding_ids),
    )
    prior_finding_continuations: list[dict[str, Any]] = []
    normalized_prior_reviews: list[dict[str, Any]] = []
    for transport_index, raw_finding_id in enumerate(
        active_prior_finding_ids
    ):
        if transport_index not in raw_prior_finding_reviews:
            continue
        finding_id = str(raw_finding_id)
        review = {
            key: (
                str(value or "").strip().upper()
                if key == "status"
                else value
            )
            for key, value in raw_prior_finding_reviews[transport_index].items()
            if key not in {"finding_id", "prior_finding_id"}
        }
        raw_continuation = review.pop("current_finding", None)
        normalized_prior_reviews.append({"finding_id": finding_id, **review})
        if isinstance(raw_continuation, Mapping):
            continuation = {
                key: value
                for key, value in dict(raw_continuation).items()
                if key not in {"finding_id", "prior_finding_id", "repair_scope"}
            }
            prior_finding_continuations.append(
                {
                    **continuation,
                    "prior_finding_id": finding_id,
                    "finding_id": finding_id,
                    "repair_scope": "upstream_theory",
                }
            )
    body["prior_finding_reviews"] = normalized_prior_reviews
    required_estimator_ids = list(
        material.get("required_estimator_ids", []) or []
    )
    raw_estimator_rows = {
        index: {
            key: value
            for key, value in row.items()
            if key != "estimator_id"
        }
        for index, row in _ordered_review_slot_rows(
            body.get("estimator_execution_checks", {}),
            expected_count=len(required_estimator_ids),
        ).items()
    }
    estimator_rows: list[dict[str, Any]] = []
    estimator_identity_bindings: list[dict[str, Any]] = []
    for transport_index, raw_estimator_id in enumerate(
        required_estimator_ids
    ):
        if transport_index not in raw_estimator_rows:
            continue
        estimator_id = str(raw_estimator_id)
        model_row = raw_estimator_rows[transport_index]
        if "status" in model_row:
            model_row["status"] = str(
                model_row.get("status", "") or ""
            ).strip().upper()
        estimator_rows.append({"estimator_id": estimator_id, **model_row})
        estimator_identity_bindings.append(
            {
                "transport_index": transport_index,
                "estimator_id": estimator_id,
                "model_reported_status": model_row.get("status"),
                "model_row_fingerprint": stable_hash(model_row),
                "identity_source": "estimator_execution_checks_ordered_index",
                "runtime_selected_semantics": False,
            }
        )
    (
        body["estimator_execution_checks"],
        body["runtime_estimator_status_normalizations"],
    ) = _normalize_estimator_status_summaries(estimator_rows)
    body["runtime_estimator_identity_bindings"] = estimator_identity_bindings
    normalized_findings: list[dict[str, Any]] = list(
        prior_finding_continuations
    )
    for raw_finding in body.get("findings", []) or []:
        if not isinstance(raw_finding, Mapping):
            continue
        finding = {**dict(raw_finding), "repair_scope": "upstream_theory"}
        prior_finding_id = str(
            finding.get("prior_finding_id", "") or ""
        ).strip()
        if prior_finding_id:
            finding["finding_id"] = prior_finding_id
        else:
            finding = normalize_metric_protocol_findings(
                question_id=question.id,
                findings=[finding],
                preserve_existing_ids=False,
            )[0]
        normalized_findings.append(finding)
    body["findings"] = normalized_findings
    if body.get("source_grounding_required") is True:
        for finding in normalized_findings:
            finding["source_evidence_refs"] = (
                _canonical_preflight_source_refs(
                    finding.get("source_evidence_refs", []),
                    source_grounding=grounding,
                )
            )
    body["source_grounding_bindings"] = [
        {
            "finding_id": str(finding.get("finding_id", "") or ""),
            "source_evidence_refs": [
                str(value).strip()
                for value in finding.get("source_evidence_refs", []) or []
                if str(value).strip()
            ],
            "runtime_verified_source_refs": True,
            "runtime_selected_semantics": False,
        }
        for finding in normalized_findings
    ] if body.get("source_grounding_required") is True else []
    body["runtime_prior_finding_identity_bindings"] = [
        {
            "transport_index": transport_index,
            "prior_finding_id": finding_id,
            "canonical_finding_id": finding_id,
            "model_continuation_fingerprint": stable_hash(
                {
                    key: value
                    for key, value in row.items()
                    if key
                    not in {
                        "finding_id",
                        "prior_finding_id",
                        "repair_scope",
                    }
                }
            ),
            "identity_source": "prior_finding_reviews_ordered_index",
            "runtime_selected_semantics": False,
        }
        for transport_index, finding_id in enumerate(active_prior_finding_ids)
        for row in normalized_findings
        if str(row.get("prior_finding_id", "") or "").strip() == finding_id
    ]
    body["repair_instructions"] = _derived_repair_instructions(body)
    body["derived_consistency_warnings"] = _derived_consistency_warnings(body)
    body["overall_verdict"] = _derived_verdict(body)
    packet_id = "architect_theory_execution_preflight:" + stable_hash(
        [
            question.id,
            material.get("source_theory_packet_id", ""),
            material.get("source_theory_packet_hash", ""),
            body,
        ]
    )[:20]
    prior_finding_ledger = [
        dict(row)
        for row in material.get("prior_finding_ledger", []) or []
        if isinstance(row, Mapping)
    ]
    cumulative_finding_ledger = update_metric_protocol_finding_ledger(
        question_id=question.id,
        prior_ledger=prior_finding_ledger,
        prior_finding_reviews=body["prior_finding_reviews"],
        current_findings=body["findings"],
        current_verdict=body["overall_verdict"],
        review_packet_id=packet_id,
        revision_index=int(material.get("preflight_revision_index", 0) or 0),
    )
    active_finding_ledger = active_metric_protocol_finding_ledger(
        cumulative_finding_ledger
    )
    prior_active_ids = [
        str(value)
        for value in material.get("active_prior_finding_ids", []) or []
        if str(value).strip()
    ]
    resolved_prior_ids = [
        str(row.get("finding_id", "") or "")
        for row in body["prior_finding_reviews"]
        if str(row.get("status", "") or "").strip().upper()
        == METRIC_PROTOCOL_FINDING_RESOLVED_BY_CURRENT_THEORY
    ]
    active_finding_ids = [
        str(row.get("finding_id", "") or "")
        for row in active_finding_ledger
        if str(row.get("finding_id", "") or "").strip()
    ]
    new_finding_ids = [
        str(row.get("finding_id", "") or "")
        for row in body["findings"]
        if str(row.get("finding_id", "") or "").strip()
        and str(row.get("finding_id", "") or "") not in prior_active_ids
    ]
    progress_made = bool(
        resolved_prior_ids
        or (not prior_active_ids and new_finding_ids)
    )
    body["cumulative_finding_ledger"] = cumulative_finding_ledger
    body["cumulative_finding_ledger_fingerprint"] = (
        metric_protocol_finding_ledger_fingerprint(cumulative_finding_ledger)
        if cumulative_finding_ledger
        else ""
    )
    body["active_unresolved_finding_ids"] = active_finding_ids
    body["prior_finding_resolution_summary"] = {
        "prior_active_finding_ids": prior_active_ids,
        "resolved_prior_finding_ids": resolved_prior_ids,
        "still_unresolved_prior_finding_ids": [
            finding_id
            for finding_id in prior_active_ids
            if finding_id in active_finding_ids
        ],
        "new_finding_ids": new_finding_ids,
        "progress_made": progress_made,
        "stalled": bool(prior_active_ids and not progress_made),
    }
    return {
        "schema_version": ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SCHEMA_VERSION,
        "artifact_kind": "ArchitectTheoryExecutionPreflightReviewPacket",
        "packet_id": packet_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_id": question.id,
        "source_theory_packet_id": str(
            material.get("source_theory_packet_id", "") or ""
        ),
        "source_theory_packet_hash": str(
            material.get("source_theory_packet_hash", "") or ""
        ),
        "anchor_catalog_id": str(material.get("anchor_catalog_id", "") or ""),
        "anchor_catalog_fingerprint": str(
            material.get("anchor_catalog_fingerprint", "") or ""
        ),
        "review_input_fingerprint": stable_hash(dict(material)),
        "source_agent": "LLMArchitectMetricSemanticReviewerAgent",
        "provider_name": provider_name,
        "model": model,
        "model_tier": model_tier,
        "independent_agent": True,
        "independent_invocation": True,
        "pre_execution_review": True,
        "execution_results_observed": False,
        "generated_code_observed": False,
        "simulation_results_observed": False,
        "execution_authorized": False,
        "kernel_verified": False,
        "review_protocol_version": ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL_VERSION,
        **body,
        "raw_response_fingerprint": stable_hash(raw_response),
        "proof_evidence_status": ARCHITECT_THEORY_EXECUTION_PREFLIGHT_NOT_PROOF_EVIDENCE,
        "boundary": ARCHITECT_THEORY_EXECUTION_PREFLIGHT_BOUNDARY,
    }


def validate_architect_theory_execution_preflight_packet(
    packet: Mapping[str, Any],
    *,
    material: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if packet.get("artifact_kind") != "ArchitectTheoryExecutionPreflightReviewPacket":
        errors.append("theory execution preflight artifact_kind mismatch")
    if packet.get("schema_version") != ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SCHEMA_VERSION:
        errors.append("theory execution preflight schema_version mismatch")
    if packet.get("review_protocol_version") != ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL_VERSION:
        errors.append("theory execution preflight protocol version mismatch")
    for field in (
        "packet_id",
        "question_id",
        "source_theory_packet_id",
        "source_theory_packet_hash",
        "anchor_catalog_id",
        "anchor_catalog_fingerprint",
        "review_input_fingerprint",
        "source_agent",
        "provider_name",
        "model",
        "model_tier",
    ):
        if not str(packet.get(field, "") or "").strip():
            errors.append(f"theory execution preflight missing lineage field: {field}")
    for field in (
        "source_theory_packet_id",
        "source_theory_packet_hash",
        "anchor_catalog_id",
        "anchor_catalog_fingerprint",
    ):
        if str(packet.get(field, "") or "") != str(material.get(field, "") or ""):
            errors.append(f"theory execution preflight {field} mismatch")
    if str(packet.get("question_id", "") or "") != str(
        material.get("question_id", "") or ""
    ):
        errors.append("theory execution preflight question_id mismatch")
    if str(packet.get("review_input_fingerprint", "") or "") != stable_hash(
        dict(material)
    ):
        errors.append(
            "theory execution preflight review_input_fingerprint mismatch"
        )

    dimension_rows = [
        row
        for row in packet.get("dimension_reviews", []) or []
        if isinstance(row, Mapping)
    ]
    dimensions = [str(row.get("dimension", "") or "") for row in dimension_rows]
    if dimensions != list(ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS):
        errors.append("theory execution preflight must review every dimension exactly once")
    estimator_rows = [
        row
        for row in packet.get("estimator_execution_checks", []) or []
        if isinstance(row, Mapping)
    ]
    estimator_ids = [str(row.get("estimator_id", "") or "") for row in estimator_rows]
    required_estimator_ids = [
        str(value) for value in material.get("required_estimator_ids", []) or []
    ]
    if estimator_ids != required_estimator_ids:
        errors.append("theory execution preflight must check every estimator exactly once")

    prior_finding_reviews = [
        row
        for row in packet.get("prior_finding_reviews", []) or []
        if isinstance(row, Mapping)
    ]
    expected_prior_finding_ids = [
        str(value)
        for value in material.get("active_prior_finding_ids", []) or []
        if str(value).strip()
    ]
    observed_prior_finding_ids = [
        str(row.get("finding_id", "") or "")
        for row in prior_finding_reviews
    ]
    if observed_prior_finding_ids != expected_prior_finding_ids:
        errors.append(
            "theory execution preflight must resolve every active prior "
            "finding_id exactly once; expected="
            + json.dumps(expected_prior_finding_ids)
            + "; observed="
            + json.dumps(observed_prior_finding_ids)
        )
    allowed_prior_statuses = {
        METRIC_PROTOCOL_FINDING_UNRESOLVED,
        METRIC_PROTOCOL_FINDING_RESOLVED_BY_CURRENT_THEORY,
    }
    if any(
        str(row.get("status", "") or "").strip().upper()
        not in allowed_prior_statuses
        for row in prior_finding_reviews
    ):
        errors.append("theory execution preflight prior finding status is invalid")

    for row_index, row in enumerate(estimator_rows):
        status = str(row.get("status", "") or "").strip().upper()
        invalid_declarations = _invalid_estimator_declarations(row)
        if status == "PASS" and invalid_declarations:
            estimator_id = str(row.get("estimator_id", "") or "").strip()
            errors.append(
                f"estimator_execution_checks[{row_index}] estimator_id="
                f"{estimator_id!r} status=PASS has false or missing declaration "
                "flags: "
                + ", ".join(
                    f"estimator_execution_checks[{row_index}].{field} "
                    f"({description})"
                    for field, description in invalid_declarations
                )
            )
    normalization_rows = packet.get("runtime_estimator_status_normalizations", [])
    if not isinstance(normalization_rows, list):
        errors.append(
            "theory execution preflight estimator status normalizations must be a list"
        )
        normalization_rows = []
    estimator_rows_by_id = {
        str(row.get("estimator_id", "") or "").strip(): row
        for row in estimator_rows
    }
    observed_normalization_ids: set[str] = set()
    for normalization in normalization_rows:
        if not isinstance(normalization, Mapping):
            errors.append(
                "theory execution preflight estimator status normalization is invalid"
            )
            continue
        estimator_id = str(normalization.get("estimator_id", "") or "").strip()
        row = estimator_rows_by_id.get(estimator_id)
        expected_fields = (
            [field for field, _description in _invalid_estimator_declarations(row)]
            if row is not None
            else []
        )
        if (
            not estimator_id
            or estimator_id in observed_normalization_ids
            or row is None
            or normalization.get("model_reported_status") != "PASS"
            or normalization.get("runtime_normalized_status") != "UNCERTAIN"
            or str(row.get("status", "") or "").strip().upper() != "UNCERTAIN"
            or list(
                normalization.get("false_or_missing_declaration_fields", []) or []
            )
            != expected_fields
            or not expected_fields
            or normalization.get("runtime_selected_semantics") is not False
        ):
            errors.append(
                "theory execution preflight estimator status normalization mismatch"
            )
        observed_normalization_ids.add(estimator_id)
    normalization_by_id = {
        str(row.get("estimator_id", "") or "").strip(): row
        for row in normalization_rows
        if isinstance(row, Mapping)
    }
    expected_estimator_identity_bindings: list[dict[str, Any]] = []
    for transport_index, row in enumerate(estimator_rows):
        estimator_id = str(row.get("estimator_id", "") or "").strip()
        model_row = {
            key: value
            for key, value in row.items()
            if key != "estimator_id"
        }
        normalization = normalization_by_id.get(estimator_id, {})
        model_reported_status = (
            normalization.get("model_reported_status")
            if normalization
            else model_row.get("status")
        )
        model_row["status"] = model_reported_status
        expected_estimator_identity_bindings.append(
            {
                "transport_index": transport_index,
                "estimator_id": estimator_id,
                "model_reported_status": model_reported_status,
                "model_row_fingerprint": stable_hash(model_row),
                "identity_source": "estimator_execution_checks_ordered_index",
                "runtime_selected_semantics": False,
            }
        )
    if packet.get("runtime_estimator_identity_bindings", []) != (
        expected_estimator_identity_bindings
    ):
        errors.append(
            "theory execution preflight estimator identity bindings mismatch"
        )
    if packet.get("derived_consistency_warnings", []) != (
        _derived_consistency_warnings(packet)
    ):
        errors.append("theory execution preflight consistency warnings mismatch")

    valid_anchor_ids = {
        str(row.get("anchor_id", "") or "")
        for row in material.get("anchor_catalog", []) or []
        if isinstance(row, Mapping)
    }
    cited_rows = [
        *dimension_rows,
        *estimator_rows,
        *prior_finding_reviews,
        *[
            row
            for row in packet.get("findings", []) or []
            if isinstance(row, Mapping)
        ],
    ]
    for row in cited_rows:
        refs = [str(value) for value in row.get("evidence_refs", []) or []]
        if not refs or any(ref not in valid_anchor_ids for ref in refs):
            errors.append("theory execution preflight uses missing or unknown evidence refs")
    valid_statuses = {"PASS", "FAIL", "UNCERTAIN"}
    if any(
        str(row.get("status", "") or "").strip().upper() not in valid_statuses
        for row in [*dimension_rows, *estimator_rows]
    ):
        errors.append("theory execution preflight status is invalid")
    findings = [
        row
        for row in packet.get("findings", []) or []
        if isinstance(row, Mapping)
    ]
    finding_ids = [
        str(row.get("finding_id", "") or "").strip()
        for row in findings
    ]
    if any(not finding_id for finding_id in finding_ids) or len(
        finding_ids
    ) != len(set(finding_ids)):
        errors.append(
            "theory execution preflight finding ids must be nonempty and unique"
        )
    expected_identity_bindings = [
        {
            "transport_index": transport_index,
            "prior_finding_id": finding_id,
            "canonical_finding_id": finding_id,
            "model_continuation_fingerprint": stable_hash(
                {
                    key: value
                    for key, value in row.items()
                    if key
                    not in {
                        "finding_id",
                        "prior_finding_id",
                        "repair_scope",
                    }
                }
            ),
            "identity_source": "prior_finding_reviews_ordered_index",
            "runtime_selected_semantics": False,
        }
        for transport_index, finding_id in enumerate(expected_prior_finding_ids)
        for row in findings
        if str(row.get("prior_finding_id", "") or "").strip()
        == finding_id
    ]
    if packet.get("runtime_prior_finding_identity_bindings", []) != (
        expected_identity_bindings
    ):
        errors.append(
            "theory execution preflight prior finding identity bindings mismatch"
        )
    unresolved_without_continuation: list[str] = []
    resolved_with_continuation: list[str] = []
    for prior_review in prior_finding_reviews:
        finding_id = str(prior_review.get("finding_id", "") or "").strip()
        status = str(prior_review.get("status", "") or "").strip().upper()
        linked_count = sum(
            str(row.get("finding_id", "") or "").strip() == finding_id
            for row in findings
        )
        if status == METRIC_PROTOCOL_FINDING_UNRESOLVED and linked_count != 1:
            unresolved_without_continuation.append(finding_id)
        if (
            status == METRIC_PROTOCOL_FINDING_RESOLVED_BY_CURRENT_THEORY
            and linked_count
        ):
            resolved_with_continuation.append(finding_id)
    if unresolved_without_continuation:
        errors.append(
            "each UNRESOLVED prior finding requires exactly one linked current "
            "finding; finding_ids="
            + json.dumps(unresolved_without_continuation)
        )
    if resolved_with_continuation:
        errors.append(
            "a RESOLVED_BY_CURRENT_THEORY prior finding cannot remain in current "
            "findings; finding_ids="
            + json.dumps(resolved_with_continuation)
        )
    if any(row.get("repair_scope") != "upstream_theory" for row in findings):
        errors.append("theory execution preflight findings must route upstream theory")
    expected_verdict = _derived_verdict(packet)
    if packet.get("overall_verdict") != expected_verdict:
        errors.append("theory execution preflight overall verdict is not runtime-derived")
    if not required_estimator_ids and expected_verdict != "REVISE":
        errors.append("theory execution preflight cannot accept without an estimator")
    repair_instructions = packet.get("repair_instructions", [])
    expected_repair_instructions = _derived_repair_instructions(packet)
    if repair_instructions != expected_repair_instructions:
        errors.append(
            "theory execution preflight repair instructions are not runtime-derived"
        )
    if expected_verdict == "REVISE" and not findings:
        errors.append(
            "REVISE theory execution preflight needs at least one finding"
        )
    for field in (
        "independent_agent",
        "independent_invocation",
        "pre_execution_review",
    ):
        if packet.get(field) is not True:
            errors.append(f"theory execution preflight requires {field}=true")
    for field in (
        "execution_results_observed",
        "generated_code_observed",
        "simulation_results_observed",
        "execution_authorized",
        "kernel_verified",
    ):
        if packet.get(field) is not False:
            errors.append(f"theory execution preflight requires {field}=false")
    if packet.get("proof_evidence_status") != ARCHITECT_THEORY_EXECUTION_PREFLIGHT_NOT_PROOF_EVIDENCE:
        errors.append("theory execution preflight proof boundary mismatch")
    expected_ledger = update_metric_protocol_finding_ledger(
        question_id=str(packet.get("question_id", "") or ""),
        prior_ledger=[
            dict(row)
            for row in material.get("prior_finding_ledger", []) or []
            if isinstance(row, Mapping)
        ],
        prior_finding_reviews=prior_finding_reviews,
        current_findings=findings,
        current_verdict=str(packet.get("overall_verdict", "") or ""),
        review_packet_id=str(packet.get("packet_id", "") or ""),
        revision_index=int(material.get("preflight_revision_index", 0) or 0),
    )
    if stable_hash(packet.get("cumulative_finding_ledger", [])) != stable_hash(
        expected_ledger
    ):
        errors.append("theory execution preflight finding ledger mismatch")
    expected_active_ids = [
        str(row.get("finding_id", "") or "")
        for row in active_metric_protocol_finding_ledger(expected_ledger)
        if str(row.get("finding_id", "") or "").strip()
    ]
    if list(packet.get("active_unresolved_finding_ids", []) or []) != (
        expected_active_ids
    ):
        errors.append("theory execution preflight active finding ids mismatch")
    expected_ledger_fingerprint = (
        metric_protocol_finding_ledger_fingerprint(expected_ledger)
        if expected_ledger
        else ""
    )
    if str(
        packet.get("cumulative_finding_ledger_fingerprint", "") or ""
    ) != expected_ledger_fingerprint:
        errors.append(
            "theory execution preflight finding ledger fingerprint mismatch"
        )
    errors.extend(_preflight_source_grounding_errors(packet))
    return sorted(set(errors))


ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SYSTEM_PROMPT = """\
You are the independent ArchitectMetricSemanticReviewer inside an AI Statistician
AgentRuntime. Before metric authoring or generated execution, audit whether a proposed
statistical theory is mathematically coherent and can be represented by a finite,
typed experiment. This is an execution-admissibility gate, not theorem peer review or
formal proof closure. Be adversarial about executable semantics, DGP alignment,
normalization, and measurement, but do not block execution solely because a theorem
proof is incomplete or an explicitly excluded regime is not robust. Do not write code,
use observed results, invent task-family rules, or claim proof evidence.
"""


def _review_architect_theory_execution_preflight_with_source_tools(
    *,
    provider: GeneratorBackend,
    question: OpenResearchQuestion,
    material: Mapping[str, Any],
    source_retriever: Any,
    request_model: str,
    model_tier: str,
    provider_name: str,
    max_tokens: int,
    temperature: float,
    review_output_token_cap: int,
) -> dict[str, Any]:
    submit_schema = _architect_theory_execution_preflight_submit_schema(
        material
    )
    tools = (
        ClientToolDefinition(
            name="search_preflight_sources",
            description=(
                "Search the current theory anchors, task-bound retrieval memory, "
                "and configured formal libraries. Write the query yourself. Cite "
                "the short returned source_ref handles in blocking findings; the "
                "runtime resolves them to immutable source_hit_id values."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["query", "source_scope", "k"],
                "properties": {
                    "query": {
                        "type": "string",
                        "minLength": 3,
                        "maxLength": 500,
                    },
                    "source_scope": {
                        "type": "string",
                        "enum": [
                            "theory",
                            "retrieval_memory",
                            "formal_library",
                            "all",
                        ],
                    },
                    "k": {"type": "integer", "minimum": 1, "maximum": 8},
                },
            },
        ),
        ClientToolDefinition(
            name="submit_theory_preflight_review",
            description=(
                "Submit the complete preflight review after source search. Every "
                "finding, including a continued prior finding, must cite one or "
                "more short source_ref handles returned in this loop."
            ),
            input_schema=submit_schema,
            terminal=True,
            strict=True,
        ),
    )
    prompt = build_architect_theory_execution_preflight_prompt(material)
    tool_prompt = (
        prompt.split("\n\n", 1)[-1]
        + "\n\nUse search_preflight_sources before submitting. Cite its short "
        "source_ref handles; runtime binds them to exact source identities. You own each "
        "statistical judgment and each search query. Runtime retrieval ranking, "
        "source identity checks, and packet validation do not choose semantics. "
        "Keep the two citation namespaces distinct: evidence_refs uses only exact "
        "theory anchor IDs allowed by the submit schema, while source_evidence_refs "
        "uses only S...H... handles returned by search_preflight_sources. "
        "Call submit_theory_preflight_review with the full typed review; do not "
        "answer in prose."
    )
    state: dict[str, Any] = {
        "searches": 0,
        "observations": [],
        "observation_ids": set(),
        "source_ref_by_hit_id": {},
    }

    def source_grounding_payload(**loop_metadata: Any) -> dict[str, Any]:
        observations = deepcopy(list(state["observations"]))
        return {
            "source_grounding_required": True,
            "source_grounding_transport": (
                ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SOURCE_TRANSPORT
            ),
            "preflight_source_observations": observations,
            "preflight_source_observations_fingerprint": stable_hash(
                observations
            ),
            "preflight_source_search_count": int(state["searches"]),
            "preflight_source_search_budget": (
                ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_SOURCE_SEARCHES
            ),
            "runtime_selected_review_semantics": False,
            **loop_metadata,
        }

    def normalize_submission(
        payload: Mapping[str, Any],
        *,
        source_grounding: Mapping[str, Any],
        response_model: str,
        response_provider: str,
    ) -> dict[str, Any]:
        return _normalize_packet(
            payload,
            question=question,
            material=material,
            model=response_model or request_model,
            model_tier=model_tier,
            provider_name=provider_name or response_provider,
            raw_response=json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ),
            source_grounding=source_grounding,
        )

    def execute_tool(
        call: ClientToolCall,
        _context: ClientToolExecutionContext,
    ) -> ClientToolExecutionResult:
        tool_input = dict(call.input)
        if call.name == "search_preflight_sources":
            if state["searches"] >= (
                ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_SOURCE_SEARCHES
            ):
                raise ClientToolInputError(
                    "preflight source-search budget exhausted"
                )
            query = str(tool_input.get("query", "") or "").strip()
            source_scope = str(
                tool_input.get("source_scope", "") or ""
            ).strip()
            try:
                k = int(tool_input.get("k", 0) or 0)
            except (TypeError, ValueError) as exc:
                raise ClientToolInputError("k must be an integer") from exc
            if not 3 <= len(query) <= 500:
                raise ClientToolInputError(
                    "query length must be between 3 and 500 characters"
                )
            if source_scope not in {
                "theory",
                "retrieval_memory",
                "formal_library",
                "all",
            }:
                raise ClientToolInputError("source_scope is invalid")
            if not 1 <= k <= 8:
                raise ClientToolInputError("k must be between 1 and 8")
            observation = _search_preflight_sources(
                material=material,
                source_retriever=source_retriever,
                query=query,
                source_scope=source_scope,
                k=k,
                search_index=int(state["searches"]) + 1,
                exclude_hit_ids=set(state["source_ref_by_hit_id"]),
                prior_source_refs=state["source_ref_by_hit_id"],
            )
            state["searches"] += 1
            for hit in observation.get("hits", []) or []:
                if not isinstance(hit, Mapping):
                    continue
                hit_id = str(hit.get("source_hit_id", "") or "").strip()
                source_ref = str(hit.get("source_ref", "") or "").strip()
                if hit_id and source_ref:
                    state["source_ref_by_hit_id"][hit_id] = source_ref
            observation_id = str(observation["observation_id"])
            if observation_id not in state["observation_ids"]:
                state["observation_ids"].add(observation_id)
                state["observations"].append(observation)
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    **observation,
                    "remaining_searches": (
                        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_SOURCE_SEARCHES
                        - state["searches"]
                    ),
                },
                state_changed=True,
                observation_key=observation_id,
            )

        if call.name == "submit_theory_preflight_review":
            if state["searches"] < 1:
                raise ClientToolInputError(
                    "search_preflight_sources must run before submission"
                )
            source_grounding = source_grounding_payload()
            packet = normalize_submission(
                tool_input,
                source_grounding=source_grounding,
                response_model=request_model,
                response_provider=provider_name,
            )
            errors = validate_architect_theory_execution_preflight_packet(
                packet,
                material=material,
            )
            if errors:
                anchor_ids = [
                    str(row.get("anchor_id", "") or "")
                    for row in material.get("anchor_catalog", []) or []
                    if isinstance(row, Mapping)
                    and str(row.get("anchor_id", "") or "").strip()
                ]
                source_handles = sorted(
                    {
                        str(value)
                        for value in state["source_ref_by_hit_id"].values()
                        if str(value).strip()
                    }
                )
                rejection = {
                    "ok": False,
                    "error": "preflight_submission_rejected",
                    "validation_errors": list(errors[:12]),
                    "field_contracts": {
                        "evidence_refs": {
                            "meaning": "theory anchor IDs from source_material",
                            "allowed_values": anchor_ids,
                        },
                        "source_evidence_refs": {
                            "meaning": (
                                "runtime-returned search_preflight_sources handles"
                            ),
                            "allowed_values": source_handles,
                        },
                    },
                    "repair_instruction": (
                        "Resubmit the complete typed review after correcting every "
                        "listed field error. Do not swap the two citation namespaces."
                    ),
                }
                return ClientToolExecutionResult(
                    content=rejection,
                    is_error=True,
                    observation_key=(
                        "preflight_submission_rejected:"
                        + stable_hash(rejection)
                    ),
                )
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "submitted": True,
                    "overall_verdict": packet.get("overall_verdict", ""),
                    "packet_fingerprint": stable_hash(packet),
                    "source_grounding_verified": True,
                    "proof_evidence_status": (
                        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_NOT_PROOF_EVIDENCE
                    ),
                },
                terminal=True,
                terminal_payload={"review_payload": tool_input},
                observation_key="preflight-submitted:" + stable_hash(packet),
            )
        raise ClientToolInputError("unsupported preflight client tool")

    request = ClientToolTurnRequest(
        system_prompt=(
            ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SYSTEM_PROMPT
            + "\nThis live review is source-query grounded. Search before deciding; "
            "do not cite a source you did not receive from the client tool."
        ),
        messages=({"role": "user", "content": tool_prompt},),
        tools=tools,
        model=request_model,
        max_tokens=min(max(1, int(max_tokens)), review_output_token_cap),
        temperature=temperature,
        tool_choice="any",
        disable_parallel_tool_use=True,
        metadata={
            "subsystem": "ArchitectMetricSemanticReviewer",
            "agent": "LLMArchitectMetricSemanticReviewerAgent",
            "review_stage": "theory_execution_preflight",
            "provider_name": provider_name,
            "model_tier": model_tier,
            "resolved_model": request_model,
            "client_tool_transport": True,
            "review_input_fingerprint": stable_hash(material),
            "review_protocol_version": (
                ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL_VERSION
            ),
            "source_grounding_transport": (
                ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SOURCE_TRANSPORT
            ),
        },
    )
    max_tool_calls = (
        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_SOURCE_SEARCHES
        + ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_TOOL_TURNS
    )

    def select_preflight_tools(
        _turn_index: int,
        available_tools: tuple[ClientToolDefinition, ...],
    ) -> tuple[ClientToolDefinition, ...]:
        if int(state["searches"]) < (
            ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_SOURCE_SEARCHES
        ):
            return available_tools
        return tuple(tool for tool in available_tools if tool.terminal)

    try:
        loop = run_bounded_client_tool_loop(
            backend=provider,
            request=request,
            execute_tool=execute_tool,
            max_turns=ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_TOOL_TURNS,
            max_tool_calls=max_tool_calls,
            max_no_progress_turns=(
                ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_NO_PROGRESS_TURNS
            ),
            max_terminal_recovery_turns=(
                ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_TERMINAL_RECOVERY_TURNS
            ),
            select_tools=select_preflight_tools,
        )
    except ClientToolLoopError as exc:
        raise PacketValidationError(
            validation_label=(
                "Architect theory-to-execution source-grounded preflight review"
            ),
            attempts=exc.turns,
            errors=[exc.reason],
            history=[deepcopy(dict(row)) for row in exc.history],
            recovery_checkpoint={
                "artifact_kind": (
                    "ArchitectTheoryExecutionPreflightSourceToolCheckpoint"
                ),
                "question_id": question.id,
                **source_grounding_payload(
                    client_tool_loop_turns=exc.turns,
                    client_tool_loop_tool_calls=exc.tool_calls,
                    client_tool_loop_runtime_executed_tool_calls=(
                        exc.runtime_executed_tool_calls
                    ),
                    client_tool_loop_transcript_fingerprint=(
                        exc.transcript_fingerprint
                    ),
                ),
                "proof_evidence_status": (
                    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_NOT_PROOF_EVIDENCE
                ),
            },
        ) from exc

    terminal = dict(loop.terminal_payload)
    review_payload = terminal.get("review_payload", {})
    if not isinstance(review_payload, Mapping):
        raise PacketValidationError(
            validation_label=(
                "Architect theory-to-execution source-grounded preflight review"
            ),
            attempts=loop.turns,
            errors=["terminal submission did not contain a review payload"],
            history=[deepcopy(dict(row)) for row in loop.history],
        )
    packet = normalize_submission(
        review_payload,
        source_grounding=source_grounding_payload(
            client_tool_loop_turns=loop.turns,
            client_tool_loop_tool_calls=loop.tool_calls,
            client_tool_loop_runtime_executed_tool_calls=(
                loop.runtime_executed_tool_calls
            ),
            client_tool_loop_transcript_fingerprint=(
                loop.transcript_fingerprint
            ),
            client_tool_loop_provider_usage=dict(loop.provider_usage),
            client_tool_loop_response_metadata=dict(
                loop.final_response_metadata
            ),
            client_tool_loop_history=[
                deepcopy(dict(row)) for row in loop.history
            ],
        ),
        response_model=loop.model,
        response_provider=loop.provider,
    )
    errors = validate_architect_theory_execution_preflight_packet(
        packet,
        material=material,
    )
    if errors:
        raise PacketValidationError(
            validation_label=(
                "Architect theory-to-execution source-grounded preflight review"
            ),
            attempts=loop.turns,
            errors=errors,
            history=[deepcopy(dict(row)) for row in loop.history],
        )
    return packet


def review_architect_theory_execution_preflight(
    *,
    provider: GeneratorBackend,
    question: OpenResearchQuestion,
    theory_protocol_material: Mapping[str, Any],
    upstream_research_contract: Mapping[str, Any],
    model: str,
    model_tier: str,
    max_tokens: int,
    temperature: float,
    provider_name: str,
    max_repair_attempts: int,
    prior_finding_ledger: Sequence[Mapping[str, Any]] = (),
    source_retriever: Any = None,
) -> dict[str, Any]:
    material = build_architect_theory_execution_preflight_material(
        question=question,
        theory_protocol_material=theory_protocol_material,
        upstream_research_contract=upstream_research_contract,
        prior_finding_ledger=prior_finding_ledger,
    )
    request_model = resolve_generator_model(
        provider_name=provider_name,
        requested_model=model,
        model_tier=model_tier,
    )
    prompt = build_architect_theory_execution_preflight_prompt(material)
    schema = architect_theory_execution_preflight_json_schema(material)
    review_estimator_count = len(material.get("required_estimator_ids", []) or [])
    review_prior_finding_count = len(
        material.get("active_prior_finding_ids", []) or []
    )
    review_output_token_cap = min(
        12000,
        5600
        + 1200 * max(0, review_estimator_count - 1)
        + 900 * review_prior_finding_count,
    )
    if callable(getattr(provider, "generate_client_tool_turn", None)):
        return _review_architect_theory_execution_preflight_with_source_tools(
            provider=provider,
            question=question,
            material=material,
            source_retriever=source_retriever,
            request_model=request_model,
            model_tier=model_tier,
            provider_name=provider_name,
            max_tokens=max_tokens,
            temperature=temperature,
            review_output_token_cap=review_output_token_cap,
        )
    request = GeneratorRequest(
        system_prompt=ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SYSTEM_PROMPT,
        user_prompt=prompt,
        model=request_model,
        max_tokens=min(max(1, int(max_tokens)), review_output_token_cap),
        temperature=temperature,
        schema=schema,
        metadata={
            "subsystem": "ArchitectMetricSemanticReviewer",
            "agent": "LLMArchitectMetricSemanticReviewerAgent",
            "review_stage": "theory_execution_preflight",
            "provider_name": provider_name,
            "model_tier": model_tier,
            "resolved_model": request_model,
            "provider_structured_output": True,
            "review_input_fingerprint": stable_hash(material),
            "review_protocol_version": ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL_VERSION,
            "review_prompt_chars": len(prompt),
            "review_schema_chars": len(json.dumps(schema, separators=(",", ":"))),
            "review_estimator_count": review_estimator_count,
            "review_prior_finding_count": review_prior_finding_count,
            "review_output_token_cap": review_output_token_cap,
        },
    )

    def build_packet(
        payload: Mapping[str, Any],
        response: Any,
        raw_text: str,
    ) -> dict[str, Any]:
        return _normalize_packet(
            payload,
            question=question,
            material=material,
            model=response.model or request_model,
            model_tier=model_tier,
            provider_name=provider_name or response.provider,
            raw_response=raw_text,
        )

    return generate_validated_json_packet(
        provider=provider,
        request=request,
        extract_payload=extract_json_object,
        build_packet=build_packet,
        validate_packet=lambda packet: validate_architect_theory_execution_preflight_packet(
            packet,
            material=material,
        ),
        validation_label="Architect theory-to-execution preflight review packet",
        max_repair_attempts=max_repair_attempts,
    )
