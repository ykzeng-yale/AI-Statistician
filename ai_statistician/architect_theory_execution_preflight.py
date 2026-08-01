from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash
from .llm_json_repair import extract_json_object, generate_validated_json_packet
from .model_backend import GeneratorBackend, GeneratorRequest, resolve_generator_model
from .metric_protocol_finding_ledger import (
    METRIC_PROTOCOL_FINDING_RESOLVED_BY_CURRENT_THEORY,
    METRIC_PROTOCOL_FINDING_UNRESOLVED,
    active_metric_protocol_finding_ledger,
    metric_protocol_finding_ledger_fingerprint,
    normalize_metric_protocol_findings,
    update_metric_protocol_finding_ledger,
)
from .research_schema import OpenResearchQuestion


ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SCHEMA_VERSION = 3
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL_VERSION = 4
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS = (
    "question_estimand_dgp_and_regime_alignment",
    "primitive_mathematical_consistency",
    "ideal_to_executable_observation_mapping",
    "termination_censoring_and_resource_feasibility",
    "guarantee_transport_and_measurement_identifiability",
)
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_NOT_PROOF_EVIDENCE = (
    "ARCHITECT_THEORY_EXECUTION_PREFLIGHT_NOT_PROOF_EVIDENCE"
)
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
        "Resolve every active prior finding by its supplied finding_id. Mark it "
        "RESOLVED_BY_CURRENT_THEORY only when current source anchors show the required "
        "change; otherwise mark it UNRESOLVED and link exactly one current finding to "
        "that id. Do not disguise a persistent defect as a newly worded finding."
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
        "repair_instructions",
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
    if active_prior_finding_ids:
        finding_properties["prior_finding_id"] = {
            "type": "string",
            "enum": active_prior_finding_ids,
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
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "finding_id",
                        "status",
                        "rationale",
                        "evidence_refs",
                    ],
                    "properties": {
                        "finding_id": {
                            "type": "string",
                            "enum": active_prior_finding_ids,
                        },
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
                    },
                },
            },
            "dimension_reviews": {
                "type": "object",
                "additionalProperties": False,
                "required": list(
                    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS
                ),
                "properties": {
                    dimension: {
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
                    for dimension in (
                        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS
                    )
                },
            },
            "estimator_execution_checks": {
                "type": "array",
                "minItems": len(estimator_ids),
                "maxItems": len(estimator_ids),
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "estimator_id",
                        "ideal_procedure_semantics",
                        "procedure_identity_recomputation",
                        "selection_conditioning_or_operator_audit",
                        "procedure_identity_declared_valid",
                        "theorem_hypothesis_measure_audit",
                        "theorem_applications_declared_valid",
                        "executable_observation_semantics",
                        "ideal_to_executable_mapping_declared",
                        "termination_or_censoring_analysis",
                        "total_or_typed_bounded_outcome_declared",
                        "guarantee_transport_analysis",
                        "guarantee_transport_argument_declared",
                        "boundary_or_counterexample",
                        "status",
                        "evidence_refs",
                    ],
                    "properties": {
                        "estimator_id": {"type": "string", "enum": estimator_ids},
                        "ideal_procedure_semantics": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 280,
                            "description": "State only the ideal procedure declared by the source.",
                        },
                        "procedure_identity_recomputation": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 420,
                            "description": (
                                "Reconstruct the central invariant or guarantee-carrying "
                                "identity from the primitive DGP. Do not restate source prose."
                            ),
                        },
                        "selection_conditioning_or_operator_audit": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 420,
                            "description": (
                                "Audit data-dependent selection, conditioning, stopping, "
                                "optimization, extrema, and nonlinear operators. State why "
                                "the claimed property survives, or give the failure."
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
                        "theorem_hypothesis_measure_audit": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 420,
                            "description": (
                                "For every theorem used to carry a guarantee, name its "
                                "conclusion law or measure and audit each hypothesis under "
                                "that same law. Say NOT_APPLICABLE only when no theorem is used."
                            ),
                        },
                        "theorem_applications_declared_valid": {
                            "type": "boolean",
                            "description": (
                                "True only when the source establishes every invoked "
                                "theorem hypothesis under the law governing its conclusion."
                            ),
                        },
                        "executable_observation_semantics": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 280,
                            "description": (
                                "State only executable behavior explicitly declared by "
                                "the source. Say MISSING when absent; never insert a repair."
                            ),
                        },
                        "ideal_to_executable_mapping_declared": {
                            "type": "boolean",
                            "description": (
                                "True only when the source explicitly maps every ideal "
                                "outcome to an executable observation."
                            ),
                        },
                        "termination_or_censoring_analysis": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 280,
                            "description": (
                                "Audit source-declared totality or bounded outcomes. Put "
                                "proposed timeout or censoring behavior only in findings."
                            ),
                        },
                        "total_or_typed_bounded_outcome_declared": {
                            "type": "boolean",
                            "description": (
                                "True only when the source establishes total return or "
                                "declares timeout, truncation, or censoring as a typed outcome."
                            ),
                        },
                        "guarantee_transport_analysis": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 280,
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
                            "maxLength": 280,
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
                    "Only defects that block metric authoring or finite execution. "
                    "Exclude downstream proof obligations and robustness outside the "
                    "admitted DGP."
                ),
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "severity",
                        "category",
                        "summary",
                        "required_change",
                        "evidence_refs",
                    ],
                    "properties": finding_properties,
                },
            },
            "repair_instructions": {
                "type": "array",
                "maxItems": 3,
                "description": (
                    "Minimum upstream changes needed to remove current execution "
                    "blockers; do not request theorem-proof closure here."
                ),
                "items": {"type": "string", "minLength": 1, "maxLength": 280},
            },
        },
    }
    if not active_prior_finding_ids:
        schema["properties"].pop("prior_finding_reviews", None)
    return schema


def build_architect_theory_execution_preflight_prompt(
    material: Mapping[str, Any],
) -> str:
    source_material = {
        key: value
        for key, value in material.items()
        if key != "prior_finding_ledger"
    }
    payload = {
        "task": (
            "Decide whether this theory handoff is mathematically coherent and "
            "representable by a finite generated-code and simulation workflow before "
            "metric authoring or execution."
        ),
        "review_protocol_version": ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL_VERSION,
        "review_protocol": list(ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL),
        "required_dimensions": list(
            ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS
        ),
        "required_estimator_ids": list(
            material.get("required_estimator_ids", []) or []
        ),
        "source_material": source_material,
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
        and row.get("procedure_identity_declared_valid") is True
        and row.get("theorem_applications_declared_valid") is True
        and row.get("ideal_to_executable_mapping_declared") is True
        and row.get("total_or_typed_bounded_outcome_declared") is True
        and row.get("guarantee_transport_argument_declared") is True
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


def _normalize_packet(
    payload: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    material: Mapping[str, Any],
    model: str,
    model_tier: str,
    provider_name: str,
    raw_response: str,
) -> dict[str, Any]:
    body = dict(payload)
    raw_dimension_reviews = body.get("dimension_reviews", {})
    if isinstance(raw_dimension_reviews, Mapping):
        body["dimension_reviews"] = [
            {
                "dimension": dimension,
                **dict(raw_dimension_reviews.get(dimension, {}) or {}),
            }
            for dimension in ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS
            if isinstance(raw_dimension_reviews.get(dimension, {}), Mapping)
        ]
    else:
        body["dimension_reviews"] = [
            dict(row)
            for row in raw_dimension_reviews or []
            if isinstance(row, Mapping)
        ]
    body["prior_finding_reviews"] = [
        dict(row)
        for row in body.get("prior_finding_reviews", []) or []
        if isinstance(row, Mapping)
    ]
    body["estimator_execution_checks"] = [
        dict(row)
        for row in body.get("estimator_execution_checks", []) or []
        if isinstance(row, Mapping)
    ]
    normalized_findings: list[dict[str, Any]] = []
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
    body["repair_instructions"] = [
        str(value)
        for value in body.get("repair_instructions", []) or []
        if str(value).strip()
    ]
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
        "progress_made": bool(resolved_prior_ids),
        "stalled": bool(prior_active_ids and not resolved_prior_ids),
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
    if sorted(dimensions) != sorted(ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS):
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
    if sorted(estimator_ids) != sorted(required_estimator_ids):
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
    if sorted(observed_prior_finding_ids) != sorted(
        expected_prior_finding_ids
    ) or len(observed_prior_finding_ids) != len(expected_prior_finding_ids):
        errors.append(
            "theory execution preflight must resolve every active prior "
            "finding_id exactly once"
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

    for row in estimator_rows:
        status = str(row.get("status", "") or "").strip().upper()
        declaration_flags = (
            row.get("procedure_identity_declared_valid"),
            row.get("theorem_applications_declared_valid"),
            row.get("ideal_to_executable_mapping_declared"),
            row.get("total_or_typed_bounded_outcome_declared"),
            row.get("guarantee_transport_argument_declared"),
        )
        if status == "PASS" and any(value is not True for value in declaration_flags):
            errors.append(
                "PASS estimator preflight requires an established procedure "
                "identity, valid theorem applications, source-declared executable "
                "mapping, bounded outcome, and guarantee transport"
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
    for prior_review in prior_finding_reviews:
        finding_id = str(prior_review.get("finding_id", "") or "").strip()
        status = str(prior_review.get("status", "") or "").strip().upper()
        linked_count = sum(
            str(row.get("finding_id", "") or "").strip() == finding_id
            for row in findings
        )
        if status == METRIC_PROTOCOL_FINDING_UNRESOLVED and linked_count != 1:
            errors.append(
                "each UNRESOLVED prior finding requires exactly one linked "
                "current finding"
            )
        if (
            status == METRIC_PROTOCOL_FINDING_RESOLVED_BY_CURRENT_THEORY
            and linked_count
        ):
            errors.append(
                "a RESOLVED_BY_CURRENT_THEORY prior finding cannot remain in "
                "current findings"
            )
    if any(row.get("repair_scope") != "upstream_theory" for row in findings):
        errors.append("theory execution preflight findings must route upstream theory")
    expected_verdict = _derived_verdict(packet)
    if packet.get("overall_verdict") != expected_verdict:
        errors.append("theory execution preflight overall verdict is not runtime-derived")
    if not required_estimator_ids and expected_verdict != "REVISE":
        errors.append("theory execution preflight cannot accept without an estimator")
    repair_instructions = packet.get("repair_instructions", [])
    if expected_verdict == "REVISE" and (
        not findings
        or not isinstance(repair_instructions, list)
        or not any(str(value).strip() for value in repair_instructions)
    ):
        errors.append("REVISE theory execution preflight needs findings and repair instructions")
    if expected_verdict == "ACCEPT" and repair_instructions:
        errors.append("ACCEPT theory execution preflight cannot request repair")
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
    review_output_token_cap = min(
        5600,
        4000 + 1200 * max(0, review_estimator_count - 1),
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

    def build_repair_context(**kwargs: Any) -> dict[str, Any]:
        invalid_payload = kwargs.get("invalid_payload", {})
        raw_estimator_rows = (
            invalid_payload.get("estimator_execution_checks", [])
            if isinstance(invalid_payload, Mapping)
            else []
        )
        estimator_paths = [
            {
                "estimator_id": str(row.get("estimator_id", "") or ""),
                "path": ["estimator_execution_checks", index],
            }
            for index, row in enumerate(raw_estimator_rows or [])
            if isinstance(row, Mapping)
            and str(row.get("estimator_id", "") or "").strip()
        ]
        raw_prior_finding_reviews = (
            invalid_payload.get("prior_finding_reviews", [])
            if isinstance(invalid_payload, Mapping)
            else []
        )
        prior_finding_paths = [
            {
                "finding_id": str(row.get("finding_id", "") or ""),
                "path": ["prior_finding_reviews", index],
            }
            for index, row in enumerate(raw_prior_finding_reviews or [])
            if isinstance(row, Mapping)
            and str(row.get("finding_id", "") or "").strip()
        ]
        return {
            "task": "Repair only the invalid fields in the preflight review packet.",
            "local_validation_errors": [
                str(value) for value in kwargs.get("errors", [])
            ],
            "typed_patch_path_basis": (
                "raw provider transport payload; do not use indices from the "
                "normalized review artifact"
            ),
            "dimension_review_patch_paths": {
                dimension: ["dimension_reviews", dimension]
                for dimension in ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS
            },
            "estimator_execution_check_patch_paths": estimator_paths,
            "prior_finding_review_patch_paths": prior_finding_paths,
            "required_dimensions": list(
                ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS
            ),
            "required_estimator_ids": list(
                material.get("required_estimator_ids", []) or []
            ),
            "active_prior_finding_ledger": list(
                material.get("active_prior_finding_ledger", []) or []
            ),
            "required_prior_finding_ids": list(
                material.get("active_prior_finding_ids", []) or []
            ),
            "source_interface_inventories": [
                {"estimator_id": estimator_id, **inventory}
                for estimator_id, inventory in _source_interface_inventories(
                    material
                ).items()
            ],
            "allowed_evidence_anchor_ids": [
                str(row.get("anchor_id", "") or "")
                for row in material.get("anchor_catalog", []) or []
                if isinstance(row, Mapping)
            ],
            "consistency_policy": (
                "Repair statuses, findings, and instructions together. Preserve "
                "semantic judgments unless a listed validation error requires change."
            ),
            "repair_prompt_priority_instructions": [
                (
                    "Copy typed patch path prefixes exactly from "
                    "dimension_review_patch_paths or "
                    "estimator_execution_check_patch_paths or "
                    "prior_finding_review_patch_paths."
                ),
                (
                    "Treat source_interface_inventories as exact source facts. Do not "
                    "label listed outputs or request/response fields MISSING; describe "
                    "only the unresolved semantic mapping."
                ),
                (
                    "When a theorem application or procedure identity is invalid, "
                    "primitive_mathematical_consistency must be non-PASS and the "
                    "finding must preserve the same mathematical reason."
                ),
            ],
        }

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
        repair_context_builder=build_repair_context,
        semantic_patch_repair=True,
        allow_progress_repair_extension=True,
    )
