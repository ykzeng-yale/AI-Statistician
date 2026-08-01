from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash
from .llm_json_repair import extract_json_object, generate_validated_json_packet
from .model_backend import GeneratorBackend, GeneratorRequest, resolve_generator_model
from .research_schema import OpenResearchQuestion


ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SCHEMA_VERSION = 1
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL_VERSION = 1
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
    "executable experiment. It is not generated execution, empirical acceptance, "
    "or theorem proof evidence."
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
        "For every estimator, distinguish the ideal mathematical procedure from the "
        "finite executable observation returned to AlgorithmEngineer or "
        "SimulationEngineer. A finite input interface cannot silently implement a "
        "procedure that may require unbounded data. Describe only behavior explicitly "
        "declared by the source; a proposed repair is not current semantics."
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
                "estimator_interface_contract",
            )
            if key in raw_row
        }
        projected.append(
            {
                "preflight_estimator_id": estimator_id,
                "source_estimator": _compact_value(
                    selected,
                    max_depth=6,
                    list_limit=8,
                    text_limit=420,
                ),
            }
        )
    return projected, estimator_ids


def build_architect_theory_execution_preflight_material(
    *,
    question: OpenResearchQuestion,
    theory_protocol_material: Mapping[str, Any],
    upstream_research_contract: Mapping[str, Any],
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
            "theory.theorem_cards",
            "theorem_cards",
            semantic.get("theorem_cards", []),
        ),
        ("theory.lemma_cards", "lemma_cards", semantic.get("lemma_cards", [])),
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
    evidence_refs = {
        "type": "array",
        "minItems": 1,
        "maxItems": min(6, max(1, len(anchor_ids))),
        "items": {"type": "string", "enum": anchor_ids},
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "dimension_reviews",
            "estimator_execution_checks",
            "findings",
            "repair_instructions",
        ],
        "properties": {
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
                "maxItems": 3,
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
                    "properties": {
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
                    },
                },
            },
            "repair_instructions": {
                "type": "array",
                "maxItems": 3,
                "items": {"type": "string", "minLength": 1, "maxLength": 280},
            },
        },
    }


def build_architect_theory_execution_preflight_prompt(
    material: Mapping[str, Any],
) -> str:
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
        "source_material": material,
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
    all_pass = bool(dimension_rows) and all(
        isinstance(row, Mapping)
        and str(row.get("status", "") or "").strip().upper() == "PASS"
        for row in dimension_rows
    )
    all_estimators_pass = all(
        isinstance(row, Mapping)
        and str(row.get("status", "") or "").strip().upper() == "PASS"
        for row in estimator_rows or []
    )
    return (
        "ACCEPT"
        if all_pass and all_estimators_pass and not packet.get("findings", [])
        else "REVISE"
    )


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
    body["estimator_execution_checks"] = [
        dict(row)
        for row in body.get("estimator_execution_checks", []) or []
        if isinstance(row, Mapping)
    ]
    body["findings"] = [
        {**dict(row), "repair_scope": "upstream_theory"}
        for row in body.get("findings", []) or []
        if isinstance(row, Mapping)
    ]
    body["repair_instructions"] = [
        str(value)
        for value in body.get("repair_instructions", []) or []
        if str(value).strip()
    ]
    body["overall_verdict"] = _derived_verdict(body)
    packet_id = "architect_theory_execution_preflight:" + stable_hash(
        [
            question.id,
            material.get("source_theory_packet_id", ""),
            material.get("source_theory_packet_hash", ""),
            body,
        ]
    )[:20]
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
    for row in estimator_rows:
        status = str(row.get("status", "") or "").strip().upper()
        declaration_flags = (
            row.get("ideal_to_executable_mapping_declared"),
            row.get("total_or_typed_bounded_outcome_declared"),
            row.get("guarantee_transport_argument_declared"),
        )
        if status == "PASS" and any(value is not True for value in declaration_flags):
            errors.append(
                "PASS estimator preflight requires source-declared executable "
                "mapping, bounded outcome, and guarantee transport"
            )

    valid_anchor_ids = {
        str(row.get("anchor_id", "") or "")
        for row in material.get("anchor_catalog", []) or []
        if isinstance(row, Mapping)
    }
    cited_rows = [
        *dimension_rows,
        *estimator_rows,
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
    return sorted(set(errors))


ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SYSTEM_PROMPT = """\
You are the independent ArchitectMetricSemanticReviewer inside an AI Statistician
AgentRuntime. Before metric authoring or generated execution, audit whether a proposed
statistical theory is mathematically coherent and can be represented by a finite,
typed experiment. Be adversarial and domain-general. Do not write code, use observed
results, invent task-family rules, or claim proof evidence.
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
) -> dict[str, Any]:
    material = build_architect_theory_execution_preflight_material(
        question=question,
        theory_protocol_material=theory_protocol_material,
        upstream_research_contract=upstream_research_contract,
    )
    request_model = resolve_generator_model(
        provider_name=provider_name,
        requested_model=model,
        model_tier=model_tier,
    )
    prompt = build_architect_theory_execution_preflight_prompt(material)
    schema = architect_theory_execution_preflight_json_schema(material)
    request = GeneratorRequest(
        system_prompt=ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SYSTEM_PROMPT,
        user_prompt=prompt,
        model=request_model,
        max_tokens=min(max(1, int(max_tokens)), 3200),
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
            "review_estimator_count": len(
                material.get("required_estimator_ids", []) or []
            ),
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
        repair_context_builder=lambda **kwargs: {
            "task": "Repair only the invalid fields in the preflight review packet.",
            "local_validation_errors": [
                str(value) for value in kwargs.get("errors", [])
            ],
            "current_invalid_packet": kwargs.get("invalid_packet", {}),
            "required_dimensions": list(
                ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS
            ),
            "required_estimator_ids": list(
                material.get("required_estimator_ids", []) or []
            ),
            "allowed_evidence_anchor_ids": [
                str(row.get("anchor_id", "") or "")
                for row in material.get("anchor_catalog", []) or []
                if isinstance(row, Mapping)
            ],
            "consistency_policy": (
                "Repair statuses, findings, and instructions together. Preserve "
                "semantic judgments unless a listed validation error requires change."
            ),
        },
        semantic_patch_repair=True,
        allow_progress_repair_extension=True,
    )
