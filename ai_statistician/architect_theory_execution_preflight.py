from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .client_tool_loop import (
    ClientToolExecutionContext,
    ClientToolExecutionResult,
    ClientToolInputError,
    ClientToolLoopError,
    run_bounded_client_tool_loop,
)
from .fingerprint import stable_hash
from .structured_output_retry import PacketValidationError
from .model_backend import (
    ClientToolCall,
    ClientToolDefinition,
    ClientToolTurnRequest,
    GeneratorBackend,
    resolve_generator_model,
)
from .metric_protocol_finding_ledger import (
    METRIC_PROTOCOL_FINDING_RETRACTED_BY_CURRENT_EVIDENCE,
    METRIC_PROTOCOL_FINDING_RESOLVED_BY_CURRENT_THEORY,
    METRIC_PROTOCOL_FINDING_UNRESOLVED,
    active_metric_protocol_finding_ledger,
    metric_protocol_finding_ledger_fingerprint,
    normalize_metric_protocol_findings,
    update_metric_protocol_finding_ledger,
)
from .research_schema import OpenResearchQuestion
from .research_source_library import (
    RESEARCH_SOURCE_NOT_PROOF_EVIDENCE,
    RESEARCH_SOURCE_READ_TOOL,
    RESEARCH_SOURCE_SEARCH_TOOL,
    ResearchSourceSnapshot,
)
from .theory_workspace import (
    MAX_THEORY_DOCUMENT_SEARCH_HITS,
    THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE,
    THEORY_SCRATCHPAD_TOOL,
    THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
    THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
    TheoryScratchpadConfig,
    execute_theory_scratchpad_tool,
    load_theory_workspace_document_rows,
    read_theory_document_lines,
    research_source_client_tools,
    search_theory_document_lines,
    theory_document_client_tools,
    theory_scratchpad_client_tool,
)

ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SCHEMA_VERSION = 19
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL_VERSION = 26
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS = (
    "question_estimand_dgp_and_regime_alignment",
    "primitive_mathematical_consistency",
    "ideal_to_executable_observation_mapping",
    "termination_censoring_and_resource_feasibility",
    "guarantee_transport_and_measurement_identifiability",
    "exploratory_confirmatory_evidence_chronology",
)
_PREFLIGHT_CLOSED_PRIOR_FINDING_STATUSES = frozenset(
    {
        METRIC_PROTOCOL_FINDING_RESOLVED_BY_CURRENT_THEORY,
        METRIC_PROTOCOL_FINDING_RETRACTED_BY_CURRENT_EVIDENCE,
    }
)
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_NOT_PROOF_EVIDENCE = (
    "ARCHITECT_THEORY_EXECUTION_PREFLIGHT_NOT_PROOF_EVIDENCE"
)
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SOURCE_TRANSPORT = (
    "client_tool_document_inspection_and_task_bound_source_query_v13"
)
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_REVIEW_TRANSPORT = (
    "model_authored_markdown_referee_report_with_compact_status_envelope_v1"
)
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_REVIEW_AUTHORITY = (
    "model_authored_markdown_referee_report"
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
        "Treat every candidate definition, assumption, equation, theorem, sanity "
        "check, and expected behavior as unverified. The Markdown or LaTeX documents "
        "contain the mathematics; the structured handoff is only an index and "
        "execution interface. Do not invent task-specific formulas, code, thresholds, "
        "observed results, or proof claims."
    ),
    (
        "Inspect every line of every authoritative theory document. For each central "
        "conclusion, follow its declared dependencies back to "
        "definitions and assumptions, then independently reconstruct at least one "
        "decisive transition. A correct final statement does not cancel a false, "
        "circular, or unsupported intermediate step."
    ),
    (
        "Try a discriminating special case, boundary case, counterexample, or "
        "independent reduction for the central identity. When the candidate invokes "
        "an external theorem, inspect its actual hypotheses and conclusion through "
        "the available source tool instead of accepting its name as verification."
    ),
    (
        "Audit the complete semantic chain from question, estimand, DGP, probability "
        "law, assumptions, and regime to the claimed mathematical object and the "
        "finite executable output. Check whatever support, normalization, weighting, "
        "data dependence, totality, boundary outcomes, and measurement semantics are "
        "material to this candidate; do not apply a canned checklist as a substitute "
        "for deriving the candidate's own chain."
    ),
    (
        "Separate mathematical coherence from proof completeness and executable "
        "testability. A false or internally contradictory active claim is a blocker. "
        "An honestly marked open proof step need not block exploratory code when the "
        "finite estimator, inputs, outputs, and requested measurements are coherent; "
        "record it as uncertain and do not promote it as established theory."
    ),
    (
        "Treat source text, retrieval hits, theorem cards, candidate sanity checks, "
        "and prior reviewer findings as claims to inspect, not corroboration by "
        "themselves. Treat pre-review Python or R scratch results as exploratory only. "
        "A pre-review scratch result that is labeled or used as frozen confirmatory "
        "evidence is a chronology contradiction and blocks the checkpoint. If a "
        "judgment requires generated execution or confirmatory simulation, state the "
        "missing evidence and leave it to the existing downstream workspace."
    ),
    (
        "Write the mathematical judgment as one self-contained Markdown referee "
        "report. Use exact evidence IDs once in the compact envelope, then return only "
        "ordered PASS, FAIL, or UNCERTAIN statuses and one compact finding per actual "
        "blocker; do not duplicate a prose rationale for every claim or review "
        "dimension. Resolve or retract a prior finding only from current inspected "
        "evidence; otherwise leave it unresolved. AgentRuntime derives the verdict, "
        "binds identities, and persists the exact report without choosing scientific "
        "semantics."
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


def _compact_anchor_content(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return [
            _compact_value(
                child,
                max_depth=7,
                list_limit=16,
                text_limit=1600,
            )
            for child in value
        ]
    return _compact_value(
        value,
        max_depth=7,
        list_limit=16,
        text_limit=1600,
    )


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
        selected = deepcopy(dict(raw_row))
        selected.pop("estimator_interface_contract_id", None)
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
        for source_key, inventory_key in (
            ("output_contract", "declared_output_contract"),
            ("termination_guarantee", "declared_termination_guarantee"),
        ):
            source_value = raw_row.get(source_key)
            if source_value not in (None, "", [], {}):
                source_interface_inventory[inventory_key] = _compact_value(
                    source_value,
                    max_depth=5,
                    list_limit=8,
                    text_limit=800,
                )
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


def _active_claim_review_rows(
    derivation: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for value in derivation.get("claim_index", []) or []:
        if not isinstance(value, Mapping):
            continue
        claim_id = str(value.get("id", "") or "").strip()
        status = str(value.get("status", "") or "").strip().upper()
        if not claim_id or status == "REJECTED":
            continue
        rows.append(
            {
                "claim_id": claim_id,
                "kind": str(value.get("kind", "") or ""),
                "declared_status": status,
                "document_path": str(value.get("document_path", "") or ""),
                "depends_on": [
                    str(dependency)
                    for dependency in value.get("depends_on", []) or []
                    if str(dependency).strip()
                ],
            }
        )
    return rows


def _preflight_review_workspace_root(
    semantic: Mapping[str, Any],
    *,
    question_id: str,
    source_theory_packet_hash: str,
) -> str:
    manifest = semantic.get("theory_workspace_manifest", {})
    if not isinstance(manifest, Mapping):
        return ""
    workspace_root = str(manifest.get("workspace_root", "") or "").strip()
    if not workspace_root:
        return ""
    source_root = Path(workspace_root).expanduser().resolve()
    run_root = source_root.parent.parent
    review_id = stable_hash(
        [question_id, source_theory_packet_hash, "theory_preflight_review"]
    )[:20]
    return str((run_root / "theory_reviews" / f"preflight-{review_id}").resolve())


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
    required_claim_reviews = _active_claim_review_rows(derivation)
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
            "theory.claim_index",
            "document_claim_dependency_index",
            derivation.get("claim_index", []),
        ),
        (
            "theory.sanity_check_index",
            "document_sanity_check_index",
            derivation.get("sanity_check_index", []),
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
            "architect.upstream_research_contract",
            "upstream_research_contract",
            upstream_research_contract,
        ),
    )
    claim_revision_delta = theory_protocol_material.get(
        "theory_claim_revision_delta", {}
    )
    if isinstance(claim_revision_delta, Mapping) and claim_revision_delta:
        sections = (
            *sections,
            (
                "theory.claim_revision_delta",
                "claim_revision_delta",
                claim_revision_delta,
            ),
        )
    anchor_catalog = [
        {
            "anchor_id": anchor_id,
            "artifact_role": artifact_role,
            "content": _compact_anchor_content(content),
        }
        for anchor_id, artifact_role, content in sections
    ]
    for document in load_theory_workspace_document_rows(semantic):
        anchor_catalog.append(
            {
                "anchor_id": f"theory.document:{document['path']}",
                "artifact_role": "authoritative_theory_document",
                "content": document["content"],
                "content_sha256": document["sha256"],
                "content_line_count": len(document["content"].splitlines()),
                "content_byte_size": len(document["content"].encode("utf-8")),
            }
        )
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
    dimension_requirements = upstream_research_contract.get(
        "dimension_requirements", {}
    )
    formal_sources_applicable = not (
        isinstance(dimension_requirements, Mapping)
        and str(dimension_requirements.get("formal", "") or "").strip()
        == "not_applicable"
    )
    source_theory_packet_hash = str(
        theory_protocol_material.get("source_theory_packet_hash", "") or ""
    )
    return {
        "schema_version": ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SCHEMA_VERSION,
        "artifact_kind": "ArchitectTheoryExecutionPreflightMaterial",
        "question_id": question.id,
        "source_theory_packet_id": str(
            theory_protocol_material.get("source_theory_packet_id", "") or ""
        ),
        "source_theory_packet_hash": source_theory_packet_hash,
        "execution_results_available": False,
        "required_estimator_ids": estimator_ids,
        "required_claim_reviews": required_claim_reviews,
        "required_claim_review_ids": [
            row["claim_id"] for row in required_claim_reviews
        ],
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
        "formal_sources_applicable": formal_sources_applicable,
        "review_workspace_root": _preflight_review_workspace_root(
            semantic,
            question_id=question.id,
            source_theory_packet_hash=source_theory_packet_hash,
        ),
        "proof_evidence_status": ARCHITECT_THEORY_EXECUTION_PREFLIGHT_NOT_PROOF_EVIDENCE,
        "boundary": ARCHITECT_THEORY_EXECUTION_PREFLIGHT_BOUNDARY,
    }


def build_architect_theory_execution_preflight_prompt(
    material: Mapping[str, Any],
    *,
    include_authoritative_document_content: bool = True,
    compact_source_search_available: bool = True,
) -> str:
    anchor_catalog = [
        dict(row)
        for row in material.get("anchor_catalog", []) or []
        if isinstance(row, Mapping)
    ]
    anchor_by_id = {
        str(row.get("anchor_id", "") or ""): row
        for row in anchor_catalog
        if str(row.get("anchor_id", "") or "").strip()
    }

    source_material = {
        key: value
        for key, value in material.items()
        if key
        not in {
            "active_prior_finding_ids",
            "active_prior_finding_ledger",
            "anchor_catalog",
            "prior_finding_ledger",
            "retrieval_context",
            "review_workspace_root",
        }
    }
    source_material["research_question"] = _compact_value(
        anchor_by_id.get("question", {}).get("content", {}),
        max_depth=5,
        list_limit=16,
        text_limit=800,
    )
    source_material["upstream_research_contract"] = _compact_value(
        anchor_by_id.get("architect.upstream_research_contract", {}).get(
            "content", {}
        ),
        max_depth=5,
        list_limit=16,
        text_limit=800,
    )
    authoritative_documents = [
        {
            "anchor_id": str(anchor.get("anchor_id", "") or ""),
            "path": str(anchor.get("anchor_id", "") or "").removeprefix(
                "theory.document:"
            ),
            "sha256": str(anchor.get("content_sha256", "") or ""),
            "line_count": int(anchor.get("content_line_count", 0) or 0),
            "byte_size": int(anchor.get("content_byte_size", 0) or 0),
        }
        for anchor in anchor_catalog
        if str(anchor.get("artifact_role", "") or "")
        == "authoritative_theory_document"
    ]
    source_material["authoritative_theory_documents"] = authoritative_documents
    source_material["current_theory_anchors"] = [
        {
            "anchor_id": str(anchor.get("anchor_id", "") or ""),
            "artifact_role": str(anchor.get("artifact_role", "") or ""),
            "content": deepcopy(anchor.get("content")),
        }
        for anchor in anchor_catalog
        if str(anchor.get("anchor_id", "") or "")
        not in {"question", "architect.upstream_research_contract"}
        and (
            include_authoritative_document_content
            or str(anchor.get("artifact_role", "") or "")
            != "authoritative_theory_document"
        )
    ]
    retrieval_context = material.get("retrieval_context", {})
    retrieval_context = (
        retrieval_context if isinstance(retrieval_context, Mapping) else {}
    )
    formal_source_groups = (
        [
            row
            for row in retrieval_context.get("formal_source_hits", []) or []
            if isinstance(row, Mapping)
        ]
        if _preflight_formal_sources_applicable(material)
        else []
    )
    active_prior_rows = {
        str(row.get("finding_id", "") or "").strip(): dict(row)
        for row in material.get("active_prior_finding_ledger", []) or []
        if isinstance(row, Mapping)
        and str(row.get("finding_id", "") or "").strip()
    }

    def prior_review_slot(index: int, finding_id: Any) -> dict[str, Any]:
        canonical_id = str(finding_id)
        finding_row = active_prior_rows.get(canonical_id, {})
        finding = finding_row.get("finding", {})
        finding = dict(finding) if isinstance(finding, Mapping) else {}
        return {
            "output_slot": f"slot_{index}",
            "finding_id": canonical_id,
            "prior_obligation": {
                key: deepcopy(finding[key])
                for key in (
                    "severity",
                    "category",
                    "summary",
                    "expected_behavior",
                    "evidence_refs",
                )
                if key in finding
            },
            "review_basis": "current_theory_anchors_only",
        }

    payload = {
        "task": (
            "Decide whether this theory handoff is mathematically coherent and "
            "representable by a finite generated-code and simulation workflow before "
            "metric authoring or execution."
        ),
        "review_protocol_version": ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL_VERSION,
        "review_protocol": list(ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL),
        "ordered_review_slots": {
            "claim_statuses": [
                {
                    "output_slot": f"slot_{index}",
                    **deepcopy(dict(claim)),
                }
                for index, claim in enumerate(
                    material.get("required_claim_reviews", []) or []
                )
                if isinstance(claim, Mapping)
            ],
            "dimension_statuses": [
                {
                    "output_slot": f"slot_{index}",
                    "dimension": dimension,
                }
                for index, dimension in enumerate(
                    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS
                )
            ],
            "estimator_execution_checks": [
                {
                    "output_slot": f"slot_{index}",
                    "estimator_id": str(estimator_id),
                }
                for index, estimator_id in enumerate(
                    material.get("required_estimator_ids", []) or []
                )
            ],
            "prior_finding_statuses": [
                prior_review_slot(index, finding_id)
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
                (
                    "Use search_preflight_sources in client-tool mode. "
                    if compact_source_search_available
                    else (
                        "Use the dedicated theory-document and task-bound research-"
                        "source tools; compact runtime source search is not exposed "
                        "for this non-formal review. "
                    )
                )
                + "Retrieval rows are context, not proof or automatic semantic "
                "authority. Formal library retrieval is available only when the task "
                "evidence contract marks formalization applicable."
            ),
        },
        "verdict_policy": (
            "Do not return an overall verdict. AgentRuntime derives it from the "
            "ordered claim and dimension statuses, compact estimator checks, and "
            "findings. Put the independent mathematical argument in one Markdown "
            "referee report rather than repeating a rationale in every slot. "
            + "A blocking finding, "
            "including an UNRESOLVED prior finding, requires at least one FAIL or "
            "UNCERTAIN claim, dimension, or estimator row. If every review row "
            "is PASS, return no new findings. Resolve a prior finding only when current "
            "inspected documents or indexed artifacts establish the required change; "
            "retract it only when the "
            "current derivation or independent source evidence defeats its premise. "
            "Every active claim must receive its own independent check; any FAIL or "
            "UNCERTAIN claim prevents acceptance. Otherwise keep prior findings "
            "unresolved. Every blocker needs a checkable independent "
            "derivation, reduction, or counterexample grounded in exact inspected "
            "documents or indexed artifacts; quoting candidate self-critique or prior "
            "reviewer prose is not "
            "independent support. Keep each rationale to the decisive calculation or "
            "observation and do not carry downstream proof obligations as execution "
            "blockers."
        ),
    }
    return (
        "Review the following typed packet with the available client tools. "
        "Submit the mathematical review only through the terminal review tool.\n\n"
        + json.dumps(
            payload,
            separators=(",", ":"),
            default=str,
        )
    )


def _preflight_text_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _preflight_authoritative_theory_documents(
    material: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    documents: dict[str, dict[str, Any]] = {}
    for anchor in material.get("anchor_catalog", []) or []:
        if not isinstance(anchor, Mapping) or str(
            anchor.get("artifact_role", "") or ""
        ) != "authoritative_theory_document":
            continue
        anchor_id = str(anchor.get("anchor_id", "") or "").strip()
        if not anchor_id.startswith("theory.document:"):
            continue
        path = anchor_id.removeprefix("theory.document:")
        content = anchor.get("content")
        if not path or not isinstance(content, str):
            continue
        content_sha256 = _preflight_text_sha256(content)
        if content_sha256 != str(anchor.get("content_sha256", "") or ""):
            raise ValueError(f"authoritative theory document hash mismatch: {path}")
        documents[path] = {
            "anchor_id": anchor_id,
            "path": path,
            "content": content,
            "sha256": content_sha256,
            "line_count": len(content.splitlines()),
            "byte_size": len(content.encode("utf-8")),
        }
    return documents


def _preflight_partially_unread_theory_documents(
    *,
    material: Mapping[str, Any],
    inspection_refs: Sequence[Mapping[str, Any]],
) -> list[str]:
    documents = _preflight_authoritative_theory_documents(material)
    reads_by_path: dict[str, list[tuple[int, int]]] = {}
    for ref in inspection_refs:
        if str(ref.get("tool", "") or "") != THEORY_WORKSPACE_READ_DOCUMENT_TOOL:
            continue
        path = str(ref.get("path", "") or "")
        line_start = ref.get("line_start")
        line_end = ref.get("line_end")
        if (
            path not in documents
            or isinstance(line_start, bool)
            or not isinstance(line_start, int)
            or isinstance(line_end, bool)
            or not isinstance(line_end, int)
        ):
            continue
        reads_by_path.setdefault(path, []).append((line_start, line_end))

    partially_unread: list[str] = []
    for path, document in sorted(documents.items()):
        next_unread_line = 1
        for line_start, line_end in sorted(reads_by_path.get(path, [])):
            if line_end < next_unread_line:
                continue
            if line_start > next_unread_line:
                break
            next_unread_line = max(next_unread_line, line_end + 1)
        if next_unread_line <= int(document["line_count"]):
            partially_unread.append(path)
    return partially_unread


def _search_preflight_theory_documents(
    *,
    material: Mapping[str, Any],
    query: Any,
    document_paths: Any,
    max_results: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    documents = {
        path: row["content"]
        for path, row in _preflight_authoritative_theory_documents(material).items()
    }
    observation, inspection_ref = search_theory_document_lines(
        documents,
        query=query,
        document_paths=document_paths,
        max_results=max_results,
    )
    inspection_ref["source_theory_packet_hash"] = str(
        material.get("source_theory_packet_hash", "") or ""
    )
    return observation, inspection_ref


def _read_preflight_theory_document(
    *,
    material: Mapping[str, Any],
    path: Any,
    line_start: Any,
    line_end: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    documents = {
        document_path: row["content"]
        for document_path, row in _preflight_authoritative_theory_documents(
            material
        ).items()
    }
    observation, inspection_ref = read_theory_document_lines(
        documents,
        path=path,
        line_start=line_start,
        line_end=line_end,
    )
    inspection_ref["source_theory_packet_hash"] = str(
        material.get("source_theory_packet_hash", "") or ""
    )
    return observation, inspection_ref


def _preflight_finding_submit_schema(
    material: Mapping[str, Any],
) -> dict[str, Any]:
    active_prior_count = len(material.get("active_prior_finding_ids", []) or [])
    properties: dict[str, Any] = {
        "severity": {
            "type": "string",
            "enum": ["medium", "high", "critical"],
        },
        "category": {"type": "string", "minLength": 1},
        "summary": {"type": "string", "minLength": 1},
        "observed_behavior": {"type": "string", "minLength": 1},
        "expected_behavior": {"type": "string", "minLength": 1},
        "evidence_refs": {"$ref": "#/$defs/evidence_refs"},
        "source_evidence_refs": {"$ref": "#/$defs/source_evidence_refs"},
    }
    required = [
        "severity",
        "category",
        "summary",
        "observed_behavior",
        "expected_behavior",
        "evidence_refs",
    ]
    if active_prior_count:
        properties["prior_finding_index"] = {
            "type": "integer",
            "minimum": -1,
            "maximum": active_prior_count - 1,
            "description": (
                "Select the ordered prior-finding slot with the same invariant. "
                "Use -1 only for a genuinely new defect."
            ),
        }
        required.append("prior_finding_index")
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }


def _architect_theory_execution_preflight_submit_schema(
    material: Mapping[str, Any],
) -> dict[str, Any]:
    source_evidence_refs = {
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
            "Short source_ref handles returned by the available source tools that "
            "support this blocking finding. Use S...H... handles here only. Runtime "
            "resolves them to immutable source_hit_id values. The separate "
            "evidence_refs field accepts only theory anchor IDs from its enum."
        ),
    }
    anchor_ids = [
        str(row.get("anchor_id", "") or "")
        for row in material.get("anchor_catalog", []) or []
        if isinstance(row, Mapping)
        and str(row.get("anchor_id", "") or "").strip()
    ]
    claim_count = len(material.get("required_claim_review_ids", []) or [])
    estimator_count = len(material.get("required_estimator_ids", []) or [])
    prior_count = len(material.get("active_prior_finding_ids", []) or [])
    def status_array(count: int, description: str) -> dict[str, Any]:
        return {
            "type": "array",
            "minItems": count,
            "maxItems": count,
            "description": description,
            "items": {
                "type": "string",
                "enum": ["PASS", "FAIL", "UNCERTAIN"],
            },
        }
    properties: dict[str, Any] = {
        "review_report_markdown": {
            "type": "string",
            "minLength": 1,
            "description": (
                "The complete mathematical referee report in readable Markdown with "
                "LaTeX equations where useful. Reconstruct decisive steps, identify "
                "counterexamples or uncertainties, and explain the final judgment "
                "here instead of duplicating prose in every status slot."
            ),
        },
        "report_evidence_refs": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string", "enum": anchor_ids},
            "description": (
                "Theory documents and compact handoff anchors actually inspected and "
                "used by the Markdown report."
            ),
        },
        "claim_statuses": status_array(
            claim_count,
            "One status per ordered claim slot. Detailed reasoning belongs in the report.",
        ),
        "dimension_statuses": status_array(
            len(ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS),
            "One status per ordered review dimension. Detailed reasoning belongs in the report.",
        ),
        "estimator_execution_checks": {
            "type": "array",
            "minItems": estimator_count,
            "maxItems": estimator_count,
            "description": (
                "One compact row per ordered estimator slot. Put mathematical and "
                "execution analysis in the Markdown report; list only actual blockers here."
            ),
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["status", "blocking_gaps"],
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["PASS", "FAIL", "UNCERTAIN"],
                    },
                    "blocking_gaps": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "minLength": 1,
                        },
                    },
                },
            },
        },
        "findings": {
            "type": "array",
            "description": (
                "Only actual blockers. The Markdown report carries the full audit; "
                "these compact findings drive bounded upstream revision."
            ),
            "items": {"$ref": "#/$defs/finding"},
        },
    }
    required = [
        "review_report_markdown",
        "report_evidence_refs",
        "claim_statuses",
        "dimension_statuses",
        "estimator_execution_checks",
        "findings",
    ]
    if prior_count:
        properties["prior_finding_statuses"] = {
            "type": "array",
            "minItems": prior_count,
            "maxItems": prior_count,
            "description": (
                "One status per ordered prior-finding slot. Explain resolution or "
                "continued uncertainty in the Markdown report."
            ),
            "items": {
                "type": "string",
                "enum": [
                    METRIC_PROTOCOL_FINDING_UNRESOLVED,
                    METRIC_PROTOCOL_FINDING_RESOLVED_BY_CURRENT_THEORY,
                    METRIC_PROTOCOL_FINDING_RETRACTED_BY_CURRENT_EVIDENCE,
                ],
            },
        }
        required.append("prior_finding_statuses")
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
        "$defs": {
            "evidence_refs": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "string", "enum": anchor_ids},
            },
            "source_evidence_refs": source_evidence_refs,
            "finding": _preflight_finding_submit_schema(material),
        },
    }


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
    content_max_depth: int = 4,
    content_list_limit: int = 6,
    content_text_limit: int = 420,
) -> dict[str, Any]:
    row = {
        "source_kind": str(source_kind),
        "source_identity": str(source_identity),
        "title": str(title)[:240],
        "location": str(location)[:500],
        "content": _compact_value(
            content,
            max_depth=content_max_depth,
            list_limit=content_list_limit,
            text_limit=content_text_limit,
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


def _preflight_formal_sources_applicable(material: Mapping[str, Any]) -> bool:
    return material.get("formal_sources_applicable") is not False


def _preflight_allowed_source_scopes(
    material: Mapping[str, Any],
) -> tuple[str, ...]:
    if _preflight_formal_sources_applicable(material):
        return ("theory", "retrieval_memory", "formal_library", "all")
    return ("theory", "retrieval_memory", "all")


def _preflight_source_catalog(material: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for anchor in material.get("anchor_catalog", []) or []:
        if not isinstance(anchor, Mapping):
            continue
        anchor_id = str(anchor.get("anchor_id", "") or "").strip()
        if not anchor_id:
            continue
        if str(anchor.get("artifact_role", "") or "") == (
            "authoritative_theory_document"
        ):
            continue
        content = anchor.get("content")
        is_collection = isinstance(content, (list, tuple))
        anchor_item_count = len(content) if is_collection else 1
        content_items = list(content) if is_collection and content else [content]
        for item_index, item in enumerate(content_items):
            is_indexed_item = is_collection and anchor_item_count > 0
            source_identity = (
                f"{anchor_id}[{item_index}]" if is_indexed_item else anchor_id
            )
            location = (
                f"{anchor_id}/{item_index}" if is_indexed_item else anchor_id
            )
            rows.append(
                _preflight_source_row(
                    source_kind="theory_anchor",
                    source_identity=source_identity,
                    title=str(anchor.get("artifact_role", "") or anchor_id),
                    location=location,
                    content=item,
                    provenance={
                        "anchor_id": anchor_id,
                        "anchor_item_index": (
                            item_index if is_indexed_item else None
                        ),
                        "anchor_item_count": anchor_item_count,
                        "source_theory_packet_id": material.get(
                            "source_theory_packet_id", ""
                        ),
                        "source_theory_packet_hash": material.get(
                            "source_theory_packet_hash", ""
                        ),
                    },
                    content_max_depth=7,
                    content_list_limit=16,
                    content_text_limit=1600,
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
    if _preflight_formal_sources_applicable(material):
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
    allowed_scopes = _preflight_allowed_source_scopes(material)
    if source_scope not in allowed_scopes:
        raise ClientToolInputError(
            "source_scope is unavailable for this task evidence contract"
        )
    formal_sources_applicable = _preflight_formal_sources_applicable(material)
    allowed_kinds = {
        "theory": {"theory_anchor"},
        "retrieval_memory": {
            "retrieval_knowledge_card",
            "retrieval_paper_source",
            *(
                {"formal_library_declaration"}
                if formal_sources_applicable
                else set()
            ),
        },
        "formal_library": {"formal_library_declaration"},
        "all": {
            "theory_anchor",
            "retrieval_knowledge_card",
            "retrieval_paper_source",
            *(
                {"formal_library_declaration"}
                if formal_sources_applicable
                else set()
            ),
        },
    }[source_scope]
    theory_ranked: list[tuple[float, dict[str, Any]]] = []
    retrieval_ranked: list[tuple[float, dict[str, Any]]] = []
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
        if row["source_kind"] == "formal_library_declaration":
            ranked = formal_ranked
        elif row["source_kind"] == "theory_anchor":
            ranked = theory_ranked
        else:
            ranked = retrieval_ranked
        ranked.append((float(len(overlap)) + phrase_bonus, row))

    provider_errors: list[dict[str, str]] = []
    if (
        formal_sources_applicable
        and source_scope in {"formal_library", "all"}
        and source_retriever is not None
    ):
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

    theory = deduplicate_ranked(
        theory_ranked,
        channel="theory",
    )
    retrieval = deduplicate_ranked(
        retrieval_ranked,
        channel="retrieval_memory",
    )
    formal = deduplicate_ranked(
        formal_ranked,
        channel="formal_library",
    )
    if source_scope == "formal_library":
        fused = formal
    elif source_scope == "theory":
        fused = theory
    elif source_scope == "retrieval_memory":
        fused = retrieval
    else:
        fused = []
        channels = (theory, retrieval, formal)
        for rank in range(max((len(rows) for rows in channels), default=0)):
            for rows in channels:
                if rank < len(rows):
                    fused.append(rows[rank])
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
            "round_robin_theory_retrieval_formal_v3_cross_turn_deduplicated"
            if source_scope == "all"
            else f"single_channel_{source_scope}_rank_v2"
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


def _research_source_preflight_observation(
    *,
    research_sources: ResearchSourceSnapshot,
    operation: str,
    tool_input: Mapping[str, Any],
    source_index: int,
    exclude_hit_ids: set[str] | None = None,
    prior_source_refs: Mapping[str, str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if operation == RESEARCH_SOURCE_SEARCH_TOOL:
        query = tool_input.get("query")
        top_k = tool_input.get("top_k", 5)
        if not isinstance(query, str):
            raise ClientToolInputError("research source query must be text")
        if isinstance(top_k, bool) or not isinstance(top_k, int):
            raise ClientToolInputError(
                "research source top_k must be an integer"
            )
        try:
            visible = research_sources.search(query, top_k=top_k)
        except ValueError as exc:
            raise ClientToolInputError(str(exc)) from exc
        source_scope = "research_sources"
        retrieval_fusion = "hash_bound_research_source_search_v1"
        raw_hits = list(visible.get("hits", []) or [])
        operation_query = str(visible.get("query", query) or query)
    elif operation == RESEARCH_SOURCE_READ_TOOL:
        document_id = tool_input.get("document_id")
        line_start = tool_input.get("line_start")
        line_end = tool_input.get("line_end")
        if not isinstance(document_id, str):
            raise ClientToolInputError(
                "research source document_id must be text"
            )
        if any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in (line_start, line_end)
        ):
            raise ClientToolInputError(
                "research source line_start and line_end must be integers"
            )
        try:
            visible = research_sources.read(
                document_id,
                line_start=line_start,
                line_end=line_end,
            )
        except ValueError as exc:
            raise ClientToolInputError(str(exc)) from exc
        source_scope = "research_source_read"
        retrieval_fusion = "hash_bound_research_source_exact_read_v1"
        raw_hits = [visible]
        operation_query = f"{document_id}:{line_start}-{line_end}"
    else:
        raise ClientToolInputError("unsupported research source operation")

    excluded = set(exclude_hit_ids or set())
    source_refs = dict(prior_source_refs or {})
    compact_hits: list[dict[str, Any]] = []
    visible_hits: list[dict[str, Any]] = []
    duplicate_source_refs_reused: list[str] = []
    for raw_hit in raw_hits:
        if not isinstance(raw_hit, Mapping):
            continue
        excerpt = str(
            raw_hit.get("excerpt", "")
            or raw_hit.get("content", "")
            or ""
        )
        document_id = str(raw_hit.get("document_id", "") or "").strip()
        line_start = int(raw_hit.get("line_start", 0) or 0)
        line_end = int(raw_hit.get("line_end", 0) or 0)
        document_sha256 = str(raw_hit.get("sha256", "") or "").strip()
        source_identity = ":".join(
            (
                research_sources.snapshot_hash,
                document_id,
                document_sha256,
                str(line_start),
                str(line_end),
                hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
            )
        )
        row = _preflight_source_row(
            source_kind=(
                "research_source_exact_passage"
                if operation == RESEARCH_SOURCE_READ_TOOL
                else "research_source_search_passage"
            ),
            source_identity=source_identity,
            title=str(raw_hit.get("title", "") or document_id),
            location=f"{document_id}:{line_start}-{line_end}",
            content={
                "document_id": document_id,
                "document_sha256": document_sha256,
                "line_start": line_start,
                "line_end": line_end,
                "content_sha256": hashlib.sha256(
                    excerpt.encode("utf-8")
                ).hexdigest(),
                "citation_ref": str(raw_hit.get("citation_ref", "") or ""),
                "matched_terms": list(raw_hit.get("matched_terms", []) or []),
            },
            provenance={
                "snapshot_id": research_sources.snapshot_id,
                "snapshot_hash": research_sources.snapshot_hash,
                "source_horizon": research_sources.source_horizon,
                "citation": str(raw_hit.get("citation", "") or ""),
                "url": str(raw_hit.get("url", "") or ""),
                "publication_date": str(
                    raw_hit.get("publication_date", "") or ""
                ),
                "git_commit": str(raw_hit.get("git_commit", "") or ""),
            },
            content_max_depth=4,
            content_list_limit=12,
            content_text_limit=500,
        )
        hit_id = str(row["source_hit_id"])
        if hit_id in excluded:
            prior_ref = str(source_refs.get(hit_id, "") or "").strip()
            if prior_ref and prior_ref not in duplicate_source_refs_reused:
                duplicate_source_refs_reused.append(prior_ref)
            continue
        source_ref = f"S{source_index}H{len(compact_hits) + 1}"
        compact_hit = {
            **row,
            "source_ref": source_ref,
            "retrieval_channel": "research_sources",
            "retrieval_rank_within_channel": len(compact_hits) + 1,
            "retrieval_score": float(raw_hit.get("score", 0.0) or 0.0),
        }
        compact_hits.append(compact_hit)
        visible_hits.append(
            {
                **dict(raw_hit),
                "source_hit_id": hit_id,
                "source_ref": source_ref,
                "proof_evidence_status": RESEARCH_SOURCE_NOT_PROOF_EVIDENCE,
            }
        )

    observation_core = {
        "query": operation_query,
        "source_scope": source_scope,
        "hits": compact_hits,
        "duplicate_source_refs_reused": duplicate_source_refs_reused,
        "provider_errors": [],
        "retrieval_fusion": retrieval_fusion,
    }
    persisted = {
        "observation_id": (
            "preflight_source_observation:"
            + stable_hash(observation_core)[:20]
        ),
        **observation_core,
        "boundary": (
            "This is a hash-bound model-visible research-source observation. "
            "The reviewing model owns the semantic judgment; source text is not "
            "mathematical proof or automatic support."
        ),
    }
    visible_result = {
        **dict(visible),
        "hits": visible_hits,
        "duplicate_source_refs_reused": duplicate_source_refs_reused,
        "proof_evidence_status": RESEARCH_SOURCE_NOT_PROOF_EVIDENCE,
    }
    if operation == RESEARCH_SOURCE_READ_TOOL:
        visible_result.update(visible_hits[0] if visible_hits else {})
    return persisted, visible_result


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
    for index, review in enumerate(
        row
        for row in packet.get("prior_finding_reviews", []) or []
        if isinstance(row, Mapping)
    ):
        refs = [
            str(value).strip()
            for value in review.get("source_evidence_refs", []) or []
            if str(value).strip()
        ]
        invalid_refs = [ref for ref in refs if ref not in hit_ids]
        if invalid_refs:
            errors.append(
                f"prior_finding_reviews[{index}] cites source refs that were not "
                "returned by the runtime; invalid refs: "
                + ", ".join(invalid_refs[:6])
            )
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
        if invalid_refs:
            errors.append(
                "preflight finding cites source refs that were not returned by "
                "the runtime; invalid refs: "
                + ", ".join(invalid_refs[:6])
                + (
                    "; available handles: "
                    + ", ".join(sorted(source_refs)[:12])
                    if source_refs
                    else ""
                )
            )
        if refs:
            expected_bindings.append(
                {
                    "finding_id": str(finding.get("finding_id", "") or ""),
                    "source_evidence_refs": refs,
                    "runtime_verified_source_refs": all(
                        ref in hit_ids for ref in refs
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


def _preflight_scratchpad_evidence_errors(
    packet: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    enabled = packet.get("preflight_scratchpad_enabled")
    if not isinstance(enabled, bool):
        errors.append("preflight scratchpad availability is invalid")
        enabled = False
    refs = [
        dict(row)
        for row in packet.get("preflight_scratch_execution_refs", []) or []
        if isinstance(row, Mapping)
    ]
    run_count = packet.get("preflight_scratch_runs")
    if isinstance(run_count, bool) or not isinstance(run_count, int):
        errors.append("preflight scratch run count is invalid")
    elif run_count != len(refs):
        errors.append("preflight scratch run count mismatch")
    expected_fingerprint = stable_hash(refs) if refs else ""
    if str(
        packet.get("preflight_scratch_execution_fingerprint", "") or ""
    ) != expected_fingerprint:
        errors.append("preflight scratch execution fingerprint mismatch")
    if refs and not enabled:
        errors.append("preflight scratch evidence exists while tool is unavailable")
    for index, ref in enumerate(refs):
        if ref.get("scratch_run") != index + 1:
            errors.append(f"preflight scratch execution {index} order mismatch")
        if not str(ref.get("code_hash", "") or "").strip():
            errors.append(f"preflight scratch execution {index} code hash is missing")
        if not str(ref.get("request_hash", "") or "").strip():
            errors.append(
                f"preflight scratch execution {index} request hash is missing"
            )
        if ref.get("runtime_edited_source") is not False:
            errors.append(
                f"preflight scratch execution {index} runtime source boundary failed"
            )
        if ref.get("runtime_edited_theory") is not False:
            errors.append(
                f"preflight scratch execution {index} runtime theory boundary failed"
            )
        if ref.get("proof_evidence_status") != (
            THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE
        ):
            errors.append(
                f"preflight scratch execution {index} proof boundary mismatch"
            )
    return errors


def _preflight_theory_document_inspection_errors(
    packet: Mapping[str, Any],
    *,
    material: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    refs = [
        dict(row)
        for row in packet.get("theory_document_inspection_refs", []) or []
        if isinstance(row, Mapping)
    ]
    if int(packet.get("theory_document_inspection_count", -1) or 0) != len(refs):
        errors.append("theory document inspection count mismatch")
    expected_fingerprint = stable_hash(refs) if refs else ""
    if str(
        packet.get("theory_document_inspection_fingerprint", "") or ""
    ) != expected_fingerprint:
        errors.append("theory document inspection fingerprint mismatch")

    client_tool_transport = packet.get("source_grounding_transport") == (
        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SOURCE_TRANSPORT
    )
    documents = _preflight_authoritative_theory_documents(material)
    expected_required = bool(documents) and client_tool_transport
    if bool(packet.get("theory_document_inspection_required")) != expected_required:
        errors.append("theory document inspection requirement mismatch")
    if expected_required and not any(
        ref.get("tool") == THEORY_WORKSPACE_READ_DOCUMENT_TOOL for ref in refs
    ):
        errors.append("authoritative theory document read evidence is required")

    source_theory_packet_hash = str(
        material.get("source_theory_packet_hash", "") or ""
    )
    for index, ref in enumerate(refs):
        if str(ref.get("source_theory_packet_hash", "") or "") != (
            source_theory_packet_hash
        ):
            errors.append(
                f"theory document inspection {index} source packet hash mismatch"
            )
        tool = str(ref.get("tool", "") or "")
        if tool == THEORY_WORKSPACE_READ_DOCUMENT_TOOL:
            path = str(ref.get("path", "") or "")
            document = documents.get(path)
            if document is None:
                errors.append(
                    f"theory document inspection {index} has unknown path"
                )
                continue
            if ref.get("document_sha256") != document["sha256"]:
                errors.append(
                    f"theory document inspection {index} document hash mismatch"
                )
            line_start = ref.get("line_start")
            line_end = ref.get("line_end")
            if any(
                isinstance(value, bool) or not isinstance(value, int)
                for value in (line_start, line_end)
            ):
                errors.append(
                    f"theory document inspection {index} line range is invalid"
                )
                continue
            lines = document["content"].splitlines()
            if line_start < 1 or line_end < line_start or line_end > len(lines):
                errors.append(
                    f"theory document inspection {index} line range is out of bounds"
                )
                continue
            content = "\n".join(lines[line_start - 1 : line_end])
            if ref.get("content_sha256") != _preflight_text_sha256(content):
                errors.append(
                    f"theory document inspection {index} range hash mismatch"
                )
        elif tool == THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL:
            document_hashes = ref.get("document_hashes", {})
            if not isinstance(document_hashes, Mapping) or not document_hashes:
                errors.append(
                    f"theory document inspection {index} search hashes are missing"
                )
                continue
            for path, document_hash in document_hashes.items():
                document = documents.get(str(path))
                if document is None or document_hash != document["sha256"]:
                    errors.append(
                        f"theory document inspection {index} search hash mismatch"
                    )
            for hit in ref.get("hits", []) or []:
                if not isinstance(hit, Mapping):
                    errors.append(
                        f"theory document inspection {index} search hit is invalid"
                    )
                    continue
                path = str(hit.get("path", "") or "")
                document = documents.get(path)
                line_number = hit.get("line_number")
                if (
                    document is None
                    or isinstance(line_number, bool)
                    or not isinstance(line_number, int)
                    or line_number < 1
                    or line_number > document["line_count"]
                ):
                    errors.append(
                        f"theory document inspection {index} search hit is out of bounds"
                    )
                    continue
                line = document["content"].splitlines()[line_number - 1]
                if hit.get("line_sha256") != _preflight_text_sha256(line):
                    errors.append(
                        f"theory document inspection {index} search hit hash mismatch"
                    )
        else:
            errors.append(f"theory document inspection {index} tool is invalid")
    if expected_required:
        partially_unread_documents = _preflight_partially_unread_theory_documents(
            material=material,
            inspection_refs=refs,
        )
        if partially_unread_documents:
            errors.append(
                "authoritative theory documents were not fully read: "
                + ", ".join(partially_unread_documents[:16])
            )
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


def _all_execution_review_rows_pass(packet: Mapping[str, Any]) -> bool:
    claim_rows = packet.get("claim_reviews", [])
    dimension_rows = packet.get("dimension_reviews", [])
    estimator_rows = packet.get("estimator_execution_checks", [])
    return bool(dimension_rows) and bool(estimator_rows) and all(
        isinstance(row, Mapping)
        and str(row.get("status", "") or "").strip().upper() == "PASS"
        for row in claim_rows
    ) and all(
        isinstance(row, Mapping)
        and str(row.get("status", "") or "").strip().upper() == "PASS"
        for row in dimension_rows
    ) and all(
        isinstance(row, Mapping)
        and str(row.get("status", "") or "").strip().upper() == "PASS"
        and not list(row.get("blocking_gaps", []) or [])
        for row in estimator_rows
    )


def _derived_verdict(packet: Mapping[str, Any]) -> str:
    prior_finding_reviews = packet.get("prior_finding_reviews", [])
    all_prior_findings_resolved = all(
        isinstance(row, Mapping)
        and str(row.get("status", "") or "").strip().upper()
        in _PREFLIGHT_CLOSED_PRIOR_FINDING_STATUSES
        for row in prior_finding_reviews or []
    )
    return (
        "ACCEPT"
        if _all_execution_review_rows_pass(packet)
        and all_prior_findings_resolved
        and not packet.get("findings", [])
        else "REVISE"
    )


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


def _prior_finding_semantics(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: deepcopy(item)
        for key, item in value.items()
        if key
        not in {
            "finding_id",
            "prior_finding_id",
            "repair_scope",
            "source_evidence_refs",
        }
    }


def _preflight_review_report_manifest(
    *,
    content: str,
    material: Mapping[str, Any],
    evidence_refs: Sequence[str],
) -> dict[str, Any]:
    content_sha256 = _preflight_text_sha256(content)
    report_id = "theory_preflight_review_document:" + content_sha256[:20]
    workspace_root = str(material.get("review_workspace_root", "") or "").strip()
    path = (
        str((Path(workspace_root) / f"review-{content_sha256[:20]}.md").resolve())
        if workspace_root
        else ""
    )
    return {
        "schema_version": 1,
        "artifact_kind": "TheoryExecutionPreflightReviewDocument",
        "document_id": report_id,
        "content_authority": ARCHITECT_THEORY_EXECUTION_PREFLIGHT_REVIEW_AUTHORITY,
        "media_type": "text/markdown",
        "path": path,
        "sha256": content_sha256,
        "byte_size": len(content.encode("utf-8")),
        "evidence_refs": list(evidence_refs),
        "persisted": False,
        "proof_evidence_status": (
            ARCHITECT_THEORY_EXECUTION_PREFLIGHT_NOT_PROOF_EVIDENCE
        ),
    }


def _materialize_preflight_review_report(
    packet: Mapping[str, Any],
    *,
    material: Mapping[str, Any],
) -> dict[str, Any]:
    materialized = deepcopy(dict(packet))
    if materialized.get("review_transport") != (
        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_REVIEW_TRANSPORT
    ):
        return materialized
    content = str(materialized.pop("review_report_markdown", "") or "")
    report = materialized.get("review_report", {})
    report = dict(report) if isinstance(report, Mapping) else {}
    path = str(report.get("path", "") or "").strip()
    if not content or not path:
        raise ValueError(
            "compact theory preflight report requires model-authored Markdown and a "
            "runtime review workspace"
        )
    report_path = Path(path).expanduser().resolve()
    workspace_root = str(material.get("review_workspace_root", "") or "").strip()
    if not workspace_root:
        raise ValueError("theory preflight review workspace is unavailable")
    expected_root = Path(workspace_root).expanduser().resolve()
    try:
        report_path.relative_to(expected_root)
    except ValueError as exc:
        raise ValueError(
            "theory preflight report path escapes its runtime review workspace"
        ) from exc
    if report_path.parent != expected_root:
        raise ValueError(
            "theory preflight report must be a direct review-workspace artifact"
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if report_path.exists():
        existing = report_path.read_text(encoding="utf-8")
        if existing != content:
            raise ValueError("theory preflight report path already has different content")
    else:
        report_path.write_text(content, encoding="utf-8")
    if _preflight_text_sha256(report_path.read_text(encoding="utf-8")) != str(
        report.get("sha256", "") or ""
    ):
        raise ValueError("persisted theory preflight report hash mismatch")
    report["persisted"] = True
    materialized["review_report"] = report
    return materialized


def _validate_compact_preflight_submission(
    payload: Mapping[str, Any],
    *,
    material: Mapping[str, Any],
) -> None:
    required_fields = {
        "review_report_markdown",
        "report_evidence_refs",
        "claim_statuses",
        "dimension_statuses",
        "estimator_execution_checks",
        "findings",
    }
    if material.get("active_prior_finding_ids", []) or []:
        required_fields.add("prior_finding_statuses")
    observed_fields = set(payload)
    missing = sorted(required_fields - observed_fields)
    unknown = sorted(observed_fields - required_fields)
    if missing or unknown:
        raise ClientToolInputError(
            "submit_theory_preflight_review requires the compact Markdown report "
            f"envelope; missing={missing} unknown={unknown}"
        )
    if not str(payload.get("review_report_markdown", "") or "").strip():
        raise ClientToolInputError(
            "review_report_markdown must contain the mathematical referee report"
        )
    array_fields = required_fields - {"review_report_markdown"}
    for field in sorted(array_fields):
        if not isinstance(payload.get(field), list):
            raise ClientToolInputError(f"{field} must be a JSON array")
    for index, row in enumerate(
        payload.get("estimator_execution_checks", []) or []
    ):
        if not isinstance(row, Mapping) or set(row) != {
            "status",
            "blocking_gaps",
        }:
            raise ClientToolInputError(
                "estimator_execution_checks must contain only status and "
                f"blocking_gaps; invalid row index={index}"
            )
    if any(
        not isinstance(row, Mapping)
        for row in payload.get("findings", []) or []
    ):
        raise ClientToolInputError("findings must contain JSON objects")


def _normalize_packet(
    payload: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    material: Mapping[str, Any],
    model: str,
    model_tier: str,
    provider_name: str,
    raw_response: str,
    source_grounding: Mapping[str, Any],
) -> dict[str, Any]:
    _validate_compact_preflight_submission(payload, material=material)
    body = dict(payload)
    grounding = deepcopy(dict(source_grounding))
    body.update(grounding)
    compact_report = str(body.get("review_report_markdown", "") or "")
    compact_report_refs = [
        str(value).strip()
        for value in body.get("report_evidence_refs", []) or []
        if str(value).strip()
    ]
    body["review_transport"] = (
        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_REVIEW_TRANSPORT
    )
    body["review_report_markdown"] = compact_report
    body["review_report"] = _preflight_review_report_manifest(
        content=compact_report,
        material=material,
        evidence_refs=compact_report_refs,
    )
    report_ref = str(body["review_report"]["document_id"])
    body["claim_reviews"] = [
        {
            "status": str(status or "").strip().upper(),
            "review_report_ref": report_ref,
        }
        for status in body.get("claim_statuses", []) or []
    ]
    body["dimension_reviews"] = [
        {
            "status": str(status or "").strip().upper(),
            "review_report_ref": report_ref,
        }
        for status in body.get("dimension_statuses", []) or []
    ]
    body["estimator_execution_checks"] = [
        {
            **dict(row),
            "status": str(row.get("status", "") or "").strip().upper(),
            "review_report_ref": report_ref,
        }
        for row in body.get("estimator_execution_checks", []) or []
    ]
    if "prior_finding_statuses" in body:
        body["prior_finding_reviews"] = [
            {
                "status": str(status or "").strip().upper(),
                "review_report_ref": report_ref,
            }
            for status in body.get("prior_finding_statuses", []) or []
        ]
    for field in (
        "claim_statuses",
        "dimension_statuses",
        "prior_finding_statuses",
        "report_evidence_refs",
    ):
        body.pop(field, None)
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
    required_claim_review_ids = list(
        material.get("required_claim_review_ids", []) or []
    )
    raw_claim_reviews = _ordered_review_slot_rows(
        body.get("claim_reviews", {}),
        expected_count=len(required_claim_review_ids),
    )
    claim_reviews: list[dict[str, Any]] = []
    claim_identity_bindings: list[dict[str, Any]] = []
    for transport_index, raw_claim_id in enumerate(required_claim_review_ids):
        if transport_index not in raw_claim_reviews:
            continue
        claim_id = str(raw_claim_id)
        model_row = {
            key: (
                str(value or "").strip().upper()
                if key == "status"
                else value
            )
            for key, value in raw_claim_reviews[transport_index].items()
            if key != "claim_id"
        }
        claim_reviews.append({"claim_id": claim_id, **model_row})
        claim_identity_bindings.append(
            {
                "transport_index": transport_index,
                "claim_id": claim_id,
                "model_reported_status": model_row.get("status"),
                "model_row_fingerprint": stable_hash(model_row),
                "identity_source": "claim_reviews_ordered_index",
                "runtime_selected_semantics": False,
            }
        )
    body["claim_reviews"] = claim_reviews
    body["runtime_claim_identity_bindings"] = claim_identity_bindings
    active_prior_finding_ids = list(
        material.get("active_prior_finding_ids", []) or []
    )
    raw_prior_finding_reviews = _ordered_review_slot_rows(
        body.get("prior_finding_reviews", {}),
        expected_count=len(active_prior_finding_ids),
    )
    active_prior_rows_by_id = {
        str(row.get("finding_id", "") or "").strip(): dict(row)
        for row in material.get("active_prior_finding_ledger", []) or []
        if isinstance(row, Mapping)
        and str(row.get("finding_id", "") or "").strip()
    }
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
            if key not in {"finding_id", "prior_finding_id", "current_finding"}
        }
        if body.get("source_grounding_required") is True:
            source_refs = _canonical_preflight_source_refs(
                review.get("source_evidence_refs", []),
                source_grounding=grounding,
            )
            if source_refs:
                review["source_evidence_refs"] = source_refs
            else:
                review.pop("source_evidence_refs", None)
        else:
            review.pop("source_evidence_refs", None)
        normalized_prior_reviews.append({"finding_id": finding_id, **review})
        if review.get("status") == METRIC_PROTOCOL_FINDING_UNRESOLVED:
            prior_row = active_prior_rows_by_id.get(finding_id, {})
            prior_finding = prior_row.get("finding", {})
            if isinstance(prior_finding, Mapping) and prior_finding:
                continuation = deepcopy(dict(prior_finding))
                continuation.update(
                    {
                        "prior_finding_id": finding_id,
                        "finding_id": finding_id,
                    }
                )
                if body.get("source_grounding_required") is True:
                    continuation["source_evidence_refs"] = list(
                        review.get("source_evidence_refs", []) or []
                    )
                prior_finding_continuations.append(continuation)
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
    body["estimator_execution_checks"] = estimator_rows
    body["runtime_estimator_identity_bindings"] = estimator_identity_bindings
    normalized_findings: list[dict[str, Any]] = list(
        prior_finding_continuations
    )
    for raw_finding in body.get("findings", []) or []:
        if not isinstance(raw_finding, Mapping):
            continue
        finding = dict(raw_finding)
        raw_prior_finding_index = finding.pop("prior_finding_index", -1)
        try:
            prior_finding_index = int(raw_prior_finding_index)
        except (TypeError, ValueError):
            prior_finding_index = -1
        prior_finding_id = str(
            finding.get("prior_finding_id", "") or ""
        ).strip()
        if 0 <= prior_finding_index < len(active_prior_finding_ids):
            prior_finding_id = str(
                active_prior_finding_ids[prior_finding_index]
            )
            finding["prior_finding_id"] = prior_finding_id
        if prior_finding_id:
            finding["finding_id"] = prior_finding_id
        else:
            finding = normalize_metric_protocol_findings(
                question_id=question.id,
                findings=[finding],
                preserve_existing_ids=False,
            )[0]
        normalized_findings.append(finding)
    deduplicated_findings: list[dict[str, Any]] = []
    seen_finding_ids: set[str] = set()
    for finding in normalized_findings:
        finding_id = str(finding.get("finding_id", "") or "").strip()
        if finding_id and finding_id in seen_finding_ids:
            continue
        if finding_id:
            seen_finding_ids.add(finding_id)
        deduplicated_findings.append(finding)
    normalized_findings = deduplicated_findings
    body["findings"] = normalized_findings
    if body.get("source_grounding_required") is True:
        for finding in normalized_findings:
            source_refs = _canonical_preflight_source_refs(
                finding.get("source_evidence_refs", []),
                source_grounding=grounding,
            )
            if source_refs:
                finding["source_evidence_refs"] = source_refs
            else:
                finding.pop("source_evidence_refs", None)
    else:
        for finding in normalized_findings:
            finding.pop("source_evidence_refs", None)
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
        if finding.get("source_evidence_refs")
    ] if body.get("source_grounding_required") is True else []
    body["runtime_prior_finding_identity_bindings"] = []
    for transport_index, finding_id in enumerate(active_prior_finding_ids):
        prior_row = active_prior_rows_by_id.get(str(finding_id), {})
        prior_finding = prior_row.get("finding", {})
        carried = next(
            (
                row
                for row in normalized_findings
                if str(row.get("prior_finding_id", "") or "").strip()
                == str(finding_id)
            ),
            None,
        )
        if not isinstance(prior_finding, Mapping) or not isinstance(
            carried, Mapping
        ):
            continue
        body["runtime_prior_finding_identity_bindings"].append(
            {
                "transport_index": transport_index,
                "prior_finding_id": str(finding_id),
                "canonical_finding_id": str(finding_id),
                "prior_ledger_semantic_fingerprint": stable_hash(
                    _prior_finding_semantics(prior_finding)
                ),
                "carried_semantic_fingerprint": stable_hash(
                    _prior_finding_semantics(carried)
                ),
                "identity_source": "prior_finding_reviews_ordered_index",
                "semantic_source": "active_prior_finding_ledger",
                "runtime_selected_semantics": False,
            }
        )
    body["overall_verdict"] = _derived_verdict(body)
    packet_identity_body = deepcopy(body)
    packet_identity_body.pop("review_report_markdown", None)
    report_identity = packet_identity_body.get("review_report", {})
    if isinstance(report_identity, Mapping):
        report_identity = dict(report_identity)
        report_identity.pop("path", None)
        report_identity.pop("persisted", None)
        packet_identity_body["review_report"] = report_identity
    packet_id = "architect_theory_execution_preflight:" + stable_hash(
        [
            question.id,
            material.get("source_theory_packet_id", ""),
            material.get("source_theory_packet_hash", ""),
            packet_identity_body,
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
    retracted_prior_ids = [
        str(row.get("finding_id", "") or "")
        for row in body["prior_finding_reviews"]
        if str(row.get("status", "") or "").strip().upper()
        == METRIC_PROTOCOL_FINDING_RETRACTED_BY_CURRENT_EVIDENCE
    ]
    closed_prior_ids = [*resolved_prior_ids, *retracted_prior_ids]
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
        closed_prior_ids
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
        "retracted_prior_finding_ids": retracted_prior_ids,
        "closed_prior_finding_ids": closed_prior_ids,
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


def _preflight_review_report_errors(
    packet: Mapping[str, Any],
    *,
    material: Mapping[str, Any],
) -> list[str]:
    if packet.get("review_transport") != (
        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_REVIEW_TRANSPORT
    ):
        return []
    errors: list[str] = []
    report = packet.get("review_report", {})
    report = dict(report) if isinstance(report, Mapping) else {}
    if report.get("artifact_kind") != "TheoryExecutionPreflightReviewDocument":
        errors.append("theory execution preflight review report kind mismatch")
    if report.get("content_authority") != (
        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_REVIEW_AUTHORITY
    ):
        errors.append("theory execution preflight review report authority mismatch")
    content = str(packet.get("review_report_markdown", "") or "")
    path = str(report.get("path", "") or "").strip()
    workspace_root = str(material.get("review_workspace_root", "") or "").strip()
    if not workspace_root:
        errors.append("theory execution preflight review workspace is unavailable")
    elif path:
        expected_root = Path(workspace_root).expanduser().resolve()
        report_path = Path(path).expanduser().resolve()
        try:
            report_path.relative_to(expected_root)
        except ValueError:
            errors.append(
                "theory execution preflight review report path escapes its workspace"
            )
        else:
            if report_path.parent != expected_root:
                errors.append(
                    "theory execution preflight review report is not a direct "
                    "workspace artifact"
                )
    if content:
        observed_sha256 = _preflight_text_sha256(content)
        observed_byte_size = len(content.encode("utf-8"))
    elif path and report.get("persisted") is True:
        try:
            persisted_content = Path(path).expanduser().resolve().read_text(
                encoding="utf-8"
            )
        except (OSError, UnicodeError):
            errors.append("theory execution preflight review report is unavailable")
            persisted_content = ""
        observed_sha256 = (
            _preflight_text_sha256(persisted_content) if persisted_content else ""
        )
        observed_byte_size = len(persisted_content.encode("utf-8"))
    else:
        errors.append("theory execution preflight review report content is missing")
        observed_sha256 = ""
        observed_byte_size = 0
    if observed_sha256 != str(report.get("sha256", "") or ""):
        errors.append("theory execution preflight review report hash mismatch")
    if observed_byte_size != int(report.get("byte_size", 0) or 0):
        errors.append("theory execution preflight review report byte size mismatch")
    evidence_refs = [
        str(value).strip()
        for value in report.get("evidence_refs", []) or []
        if str(value).strip()
    ]
    if not evidence_refs:
        errors.append("theory execution preflight review report has no evidence refs")
    return errors


def validate_architect_theory_execution_preflight_packet(
    packet: Mapping[str, Any],
    *,
    material: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    compact_report = packet.get("review_transport") == (
        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_REVIEW_TRANSPORT
    )
    errors.extend(_preflight_review_report_errors(packet, material=material))
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
        errors.append(
            "theory execution preflight dimension slot mismatch: "
            f"expected_count={len(ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS)} "
            f"observed_count={len(dimensions)} observed_dimensions={dimensions}"
        )
    claim_rows = [
        row
        for row in packet.get("claim_reviews", []) or []
        if isinstance(row, Mapping)
    ]
    claim_ids = [str(row.get("claim_id", "") or "") for row in claim_rows]
    required_claim_ids = [
        str(value)
        for value in material.get("required_claim_review_ids", []) or []
    ]
    if claim_ids != required_claim_ids:
        errors.append(
            "theory execution preflight claim slot mismatch: "
            f"expected_ids={required_claim_ids} observed_ids={claim_ids}"
        )
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
        errors.append(
            "theory execution preflight estimator slot mismatch: "
            f"expected_ids={required_estimator_ids} observed_ids={estimator_ids}"
        )

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
        METRIC_PROTOCOL_FINDING_RETRACTED_BY_CURRENT_EVIDENCE,
    }
    if any(
        str(row.get("status", "") or "").strip().upper()
        not in allowed_prior_statuses
        for row in prior_finding_reviews
    ):
        errors.append("theory execution preflight prior finding status is invalid")

    for row_index, row in enumerate(estimator_rows):
        status = str(row.get("status", "") or "").strip().upper()
        estimator_id = str(row.get("estimator_id", "") or "").strip()
        if not compact_report:
            for field in (
                "audit_rationale",
                "identity_check",
                "boundary_or_counterexample",
            ):
                if not str(row.get(field, "") or "").strip():
                    errors.append(
                        f"estimator_execution_checks[{row_index}] estimator_id="
                        f"{estimator_id!r} missing model-authored {field}"
                    )
        blocking_gaps = row.get("blocking_gaps", [])
        valid_blocking_gaps = isinstance(blocking_gaps, list) and all(
            str(value or "").strip() for value in blocking_gaps
        )
        if not valid_blocking_gaps:
            errors.append(
                f"estimator_execution_checks[{row_index}] estimator_id="
                f"{estimator_id!r} blocking_gaps must be an array of nonempty strings"
            )
            blocking_gaps = []
        if status == "PASS" and blocking_gaps:
            errors.append(
                f"estimator_execution_checks[{row_index}] estimator_id="
                f"{estimator_id!r} status=PASS cannot report blocking_gaps"
            )
        if status in {"FAIL", "UNCERTAIN"} and not blocking_gaps:
            errors.append(
                f"estimator_execution_checks[{row_index}] estimator_id="
                f"{estimator_id!r} status={status} requires a model-authored blocking gap"
            )
    for row_index, row in enumerate(claim_rows):
        claim_id = str(row.get("claim_id", "") or "").strip()
        if not compact_report:
            for field in ("independent_check", "rationale"):
                if not str(row.get(field, "") or "").strip():
                    errors.append(
                        f"claim_reviews[{row_index}] claim_id={claim_id!r} "
                        f"missing model-authored {field}"
                    )
    expected_claim_identity_bindings: list[dict[str, Any]] = []
    for transport_index, row in enumerate(claim_rows):
        claim_id = str(row.get("claim_id", "") or "").strip()
        model_row = {
            key: value for key, value in row.items() if key != "claim_id"
        }
        expected_claim_identity_bindings.append(
            {
                "transport_index": transport_index,
                "claim_id": claim_id,
                "model_reported_status": model_row.get("status"),
                "model_row_fingerprint": stable_hash(model_row),
                "identity_source": "claim_reviews_ordered_index",
                "runtime_selected_semantics": False,
            }
        )
    if packet.get("runtime_claim_identity_bindings", []) != (
        expected_claim_identity_bindings
    ):
        errors.append("theory execution preflight claim identity bindings mismatch")
    expected_estimator_identity_bindings: list[dict[str, Any]] = []
    for transport_index, row in enumerate(estimator_rows):
        estimator_id = str(row.get("estimator_id", "") or "").strip()
        model_row = {
            key: value
            for key, value in row.items()
            if key != "estimator_id"
        }
        model_reported_status = model_row.get("status")
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
    valid_anchor_ids = {
        str(row.get("anchor_id", "") or "")
        for row in material.get("anchor_catalog", []) or []
        if isinstance(row, Mapping)
    }
    if compact_report:
        report = packet.get("review_report", {})
        report = dict(report) if isinstance(report, Mapping) else {}
        report_ref = str(report.get("document_id", "") or "").strip()
        report_evidence_refs = [
            str(value).strip()
            for value in report.get("evidence_refs", []) or []
            if str(value).strip()
        ]
        if any(ref not in valid_anchor_ids for ref in report_evidence_refs):
            errors.append(
                "theory execution preflight review report uses unknown evidence refs"
            )
        compact_rows = [
            *claim_rows,
            *dimension_rows,
            *estimator_rows,
            *prior_finding_reviews,
        ]
        if not report_ref or any(
            str(row.get("review_report_ref", "") or "") != report_ref
            for row in compact_rows
        ):
            errors.append(
                "theory execution preflight compact statuses are not bound to the "
                "review report"
            )
    cited_rows = [
        row
        for row in packet.get("findings", []) or []
        if isinstance(row, Mapping)
    ]
    if not compact_report:
        cited_rows = [
            *claim_rows,
            *dimension_rows,
            *estimator_rows,
            *prior_finding_reviews,
            *cited_rows,
        ]
    for row in cited_rows:
        refs = [str(value) for value in row.get("evidence_refs", []) or []]
        if not refs or any(ref not in valid_anchor_ids for ref in refs):
            errors.append("theory execution preflight uses missing or unknown evidence refs")
    valid_statuses = {"PASS", "FAIL", "UNCERTAIN"}
    if any(
        str(row.get("status", "") or "").strip().upper() not in valid_statuses
        for row in [*claim_rows, *dimension_rows, *estimator_rows]
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
    active_prior_rows_by_id = {
        str(row.get("finding_id", "") or "").strip(): dict(row)
        for row in material.get("active_prior_finding_ledger", []) or []
        if isinstance(row, Mapping)
        and str(row.get("finding_id", "") or "").strip()
    }
    expected_identity_bindings: list[dict[str, Any]] = []
    for transport_index, finding_id in enumerate(expected_prior_finding_ids):
        prior_finding = active_prior_rows_by_id.get(finding_id, {}).get(
            "finding", {}
        )
        carried = next(
            (
                row
                for row in findings
                if str(row.get("prior_finding_id", "") or "").strip()
                == finding_id
            ),
            None,
        )
        if not isinstance(prior_finding, Mapping) or not isinstance(
            carried, Mapping
        ):
            continue
        prior_semantics = _prior_finding_semantics(prior_finding)
        carried_semantics = _prior_finding_semantics(carried)
        if stable_hash(carried_semantics) != stable_hash(prior_semantics):
            errors.append(
                "runtime-carried prior finding semantics differ from the immutable "
                f"ledger; finding_id={finding_id}"
            )
        expected_identity_bindings.append(
            {
                "transport_index": transport_index,
                "prior_finding_id": finding_id,
                "canonical_finding_id": finding_id,
                "prior_ledger_semantic_fingerprint": stable_hash(
                    prior_semantics
                ),
                "carried_semantic_fingerprint": stable_hash(
                    carried_semantics
                ),
                "identity_source": "prior_finding_reviews_ordered_index",
                "semantic_source": "active_prior_finding_ledger",
                "runtime_selected_semantics": False,
            }
        )
    if packet.get("runtime_prior_finding_identity_bindings", []) != (
        expected_identity_bindings
    ):
        errors.append(
            "theory execution preflight prior finding identity bindings mismatch"
        )
    unresolved_without_continuation: list[str] = []
    closed_with_continuation: list[str] = []
    for prior_review in prior_finding_reviews:
        finding_id = str(prior_review.get("finding_id", "") or "").strip()
        status = str(prior_review.get("status", "") or "").strip().upper()
        linked_count = sum(
            str(row.get("finding_id", "") or "").strip() == finding_id
            for row in findings
        )
        if status == METRIC_PROTOCOL_FINDING_UNRESOLVED and linked_count != 1:
            unresolved_without_continuation.append(finding_id)
        if status in _PREFLIGHT_CLOSED_PRIOR_FINDING_STATUSES and linked_count:
            closed_with_continuation.append(finding_id)
    if unresolved_without_continuation:
        errors.append(
            "runtime must carry each UNRESOLVED prior finding forward exactly once; "
            "finding_ids="
            + json.dumps(unresolved_without_continuation)
        )
    if closed_with_continuation:
        errors.append(
            "a closed prior finding cannot remain in current "
            "findings; finding_ids="
            + json.dumps(closed_with_continuation)
        )
    if findings and _all_execution_review_rows_pass(packet):
        errors.append(
            "blocking theory execution preflight findings contradict the all-PASS "
            "dimension and estimator rows; submit a complete self-consistent review "
            "with at least one FAIL or UNCERTAIN execution row, or remove new "
            "findings and close prior findings from current evidence. Downstream "
            "proof obligations are not execution blockers"
        )
    expected_verdict = _derived_verdict(packet)
    if packet.get("overall_verdict") != expected_verdict:
        errors.append("theory execution preflight overall verdict is not runtime-derived")
    if not required_estimator_ids and expected_verdict != "REVISE":
        errors.append("theory execution preflight cannot accept without an estimator")
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
    errors.extend(_preflight_scratchpad_evidence_errors(packet))
    errors.extend(
        _preflight_theory_document_inspection_errors(
            packet,
            material=material,
        )
    )
    return sorted(set(errors))


ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SYSTEM_PROMPT = """\
You are the independent ArchitectMetricSemanticReviewer inside an AI Statistician
AgentRuntime. Before metric authoring or generated execution, audit whether a proposed
statistical theory is mathematically coherent and can be represented by a finite,
typed experiment. Read every line of every authoritative Markdown or LaTeX document
and follow declared claim dependencies; the structured packet is only an index.
Independently reconstruct decisive algebraic or probabilistic transitions and try a
discriminating special case, boundary case, or counterexample. Do not treat a correct
final statement, theorem card, research question, source restatement, or passing sanity
check as validation of the intermediate derivation.

This is a rigorous mathematical checkpoint, not theorem peer review or formal proof
closure. A false, circular, or internally contradictory active claim is a blocker even
when code could run. An honestly identified open proof step may be UNCERTAIN and must not
be promoted to established theory, but need not block exploratory execution when the
finite estimator and measurement contract are coherent. Audit the candidate's own DGP,
law, assumptions, normalization, data dependence, executable mapping, boundary outcomes,
and measurements without importing a task-family checklist or formula.

Source text and retrieval are context, not proof. A pre-review Python or R scratchpad
result is exploratory only; confirmatory evidence belongs to the frozen downstream lane.
Reject a checkpoint that labels or uses pre-review scratch output as frozen confirmatory
evidence, even when its numbers happen to agree with the theory.
If a judgment requires generated execution, state the missing evidence rather than
inventing a result. Report findings, not repairs, and never claim proof evidence.
Write one coherent Markdown referee report containing the actual mathematics. Its tool
envelope is only a compact identity and routing ABI: cite the
inspected anchors once, return ordered statuses, and list actual blockers without
duplicating the report.
"""


def _preflight_evidence_history(
    history: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    persisted = [deepcopy(dict(row)) for row in history]
    for turn in persisted:
        tool_calls = turn.get("tool_calls", [])
        if not isinstance(tool_calls, list):
            continue
        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                continue
            tool_name = str(tool_call.get("name", "") or "")
            if tool_name in {
                THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
                THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
            }:
                tool_call["result_excerpt"] = (
                    "[authoritative theory text omitted from persisted review "
                    "history; use hash-bound document inspection refs]"
                )
            elif tool_name in {
                RESEARCH_SOURCE_SEARCH_TOOL,
                RESEARCH_SOURCE_READ_TOOL,
            }:
                tool_call["result_excerpt"] = (
                    "[research-source text omitted from persisted review history; "
                    "use hash-bound preflight source observations]"
                )
            elif tool_name == THEORY_SCRATCHPAD_TOOL:
                tool_call["result_excerpt"] = (
                    "[exploratory scratch output omitted from persisted review "
                    "history; use hash-bound preflight scratch execution refs]"
                )
    return persisted


def _review_architect_theory_execution_preflight_with_source_tools(
    *,
    provider: GeneratorBackend,
    question: OpenResearchQuestion,
    material: Mapping[str, Any],
    source_retriever: Any,
    research_sources: ResearchSourceSnapshot | None,
    theory_scratchpad: TheoryScratchpadConfig | None,
    request_model: str,
    model_tier: str,
    provider_name: str,
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    submit_schema = _architect_theory_execution_preflight_submit_schema(
        material
    )
    authoritative_documents = _preflight_authoritative_theory_documents(material)
    allowed_source_scopes = _preflight_allowed_source_scopes(material)
    formal_sources_applicable = _preflight_formal_sources_applicable(material)
    compact_source_search_available = not (
        authoritative_documents
        and research_sources is not None
        and not formal_sources_applicable
    )
    compact_source_tools = (
        ClientToolDefinition(
            name="search_preflight_sources",
            description=(
                "Search compact structured theory anchors, task-bound retrieval "
                "memory"
                + (
                    ", and configured formal libraries. "
                    if formal_sources_applicable
                    else ". Formal-library retrieval is intentionally absent for this "
                    "task intent. "
                )
                + "Write the query yourself. "
                "Use the dedicated document tools for authoritative theory text, and "
                "use search_research_sources/read_research_source for exact papers, "
                "code, or documentation when those tools are available. Cite short "
                "returned source_ref handles in blocking findings; the runtime resolves "
                "them to immutable source_hit_id values."
                + (
                    " Use the formal-library scope for Lean declarations, not as a "
                    "substitute for task-bound statistical source material."
                    if formal_sources_applicable
                    else ""
                )
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
                        "enum": list(allowed_source_scopes),
                    },
                    "k": {"type": "integer", "minimum": 1, "maximum": 8},
                },
            },
        ),
    ) if compact_source_search_available else ()
    tools = (
        *theory_document_client_tools(),
        *(
            research_source_client_tools()
            if research_sources is not None
            else ()
        ),
        *compact_source_tools,
        *((theory_scratchpad_client_tool(),) if theory_scratchpad else ()),
        ClientToolDefinition(
            name="submit_theory_preflight_review",
            description=(
                "Submit the complete preflight review. Use source_evidence_refs only "
                "when citing handles returned by an optional source tool."
            ),
            input_schema=submit_schema,
            terminal=True,
            strict=False,
        ),
    )
    prompt = build_architect_theory_execution_preflight_prompt(
        material,
        include_authoritative_document_content=False,
        compact_source_search_available=compact_source_search_available,
    )
    tool_prompt = (
        prompt.split("\n\n", 1)[-1]
        + "\n\nThe prompt contains a hash-bound catalog, not duplicated full theory "
        "documents. Read every line of every authoritative theory document; split long "
        "documents into adjacent ranges, and independent reads may be issued together. "
        "Coverage proves inspection only, so you must still "
        "follow dependencies, reconstruct decisive transitions, and challenge them. "
        "Choose all searches and ranges yourself. When available, use "
        "search_research_sources and read_research_source for task-bound papers, code, "
        "and documentation"
        + (
            "; use search_preflight_sources for compact runtime context"
            + (" or formal declarations" if formal_sources_applicable else "")
            if compact_source_search_available
            else ""
        )
        + ". Cite only handles returned by available source tools. Runtime binds "
        "identities but never chooses semantics. "
        + (
            "An isolated exploratory Python/R scratchpad is available. Use it only "
            "when a model-authored numerical special case or counterexample would "
            "discriminate a mathematical claim; interpret the raw result yourself. "
            "Scratch output is neither confirmatory evidence nor proof. "
            if theory_scratchpad is not None
            else ""
        )
        + "No generated-code or simulation results exist at this stage; mark a question "
        "UNCERTAIN when it genuinely requires that downstream evidence. Keep citation "
        "namespaces distinct: evidence_refs accepts theory anchor IDs, while "
        "source_evidence_refs accepts only S...H... source handles. "
        "Call submit_theory_preflight_review with one complete Markdown referee "
        "report plus the compact status and finding envelope. Do not duplicate a "
        "separate prose rationale for every claim or dimension, and do not answer "
        "outside the tool."
    )
    state: dict[str, Any] = {
        "searches": 0,
        "source_operations": 0,
        "observations": [],
        "observation_ids": set(),
        "source_ref_by_hit_id": {},
        "document_inspection_refs": [],
        "scratch_runs": 0,
        "scratch_execution_refs": [],
    }

    def source_grounding_payload(**loop_metadata: Any) -> dict[str, Any]:
        observations = deepcopy(list(state["observations"]))
        return {
            "source_grounding_required": bool(observations),
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
            "preflight_scratchpad_enabled": theory_scratchpad is not None,
            "preflight_scratch_runs": int(state["scratch_runs"]),
            "preflight_scratch_execution_refs": deepcopy(
                list(state["scratch_execution_refs"])
            ),
            "preflight_scratch_execution_fingerprint": (
                stable_hash(list(state["scratch_execution_refs"]))
                if state["scratch_execution_refs"]
                else ""
            ),
            "theory_document_inspection_required": bool(
                authoritative_documents
            ),
            "theory_document_inspection_refs": deepcopy(
                list(state["document_inspection_refs"])
            ),
            "theory_document_inspection_fingerprint": stable_hash(
                list(state["document_inspection_refs"])
            )
            if state["document_inspection_refs"]
            else "",
            "theory_document_inspection_count": len(
                state["document_inspection_refs"]
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
        if call.name == THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL:
            if set(tool_input) - {"query", "document_paths", "max_results"}:
                raise ClientToolInputError(
                    "search_theory_documents accepts query, document_paths, and "
                    "optional max_results"
                )
            observation, inspection_ref = _search_preflight_theory_documents(
                material=material,
                query=tool_input.get("query"),
                document_paths=tool_input.get("document_paths", []),
                max_results=tool_input.get(
                    "max_results", MAX_THEORY_DOCUMENT_SEARCH_HITS
                ),
            )
            state["document_inspection_refs"].append(inspection_ref)
            return ClientToolExecutionResult(
                content=observation,
                observation_key="preflight-theory-document-search:"
                + stable_hash(inspection_ref),
            )

        if call.name == THEORY_WORKSPACE_READ_DOCUMENT_TOOL:
            if set(tool_input) != {"path", "line_start", "line_end"}:
                raise ClientToolInputError(
                    "read_theory_document requires path, line_start, and line_end"
                )
            observation, inspection_ref = _read_preflight_theory_document(
                material=material,
                path=tool_input.get("path"),
                line_start=tool_input.get("line_start"),
                line_end=tool_input.get("line_end"),
            )
            state["document_inspection_refs"].append(inspection_ref)
            return ClientToolExecutionResult(
                content=observation,
                observation_key="preflight-theory-document-read:"
                + stable_hash(inspection_ref),
            )

        if call.name == THEORY_SCRATCHPAD_TOOL:
            if theory_scratchpad is None:
                raise ClientToolInputError(
                    "independent theory referee scratchpad is unavailable"
                )
            if state["scratch_runs"] >= theory_scratchpad.max_runs:
                raise ClientToolInputError(
                    "independent theory referee scratchpad run budget is exhausted"
                )
            run_index = int(state["scratch_runs"]) + 1
            execution_result, execution_ref = execute_theory_scratchpad_tool(
                tool_input=tool_input,
                scratchpad=theory_scratchpad,
                sandbox_binding=[
                    question.id,
                    material.get("source_theory_packet_hash", ""),
                    "independent_theory_referee",
                ],
                artifact_id=(
                    "theory-referee-scratch-"
                    + stable_hash(
                        [
                            question.id,
                            material.get("source_theory_packet_hash", ""),
                        ]
                    )[:12]
                    + f"-{run_index}"
                ),
                run_index=run_index,
                owner_label="independent theory referee",
            )
            state["scratch_runs"] = run_index
            state["scratch_execution_refs"].append(execution_ref)
            return execution_result

        if call.name in {
            RESEARCH_SOURCE_SEARCH_TOOL,
            RESEARCH_SOURCE_READ_TOOL,
        }:
            if research_sources is None:
                raise ClientToolInputError(
                    "research source snapshot is unavailable"
                )
            if call.name == RESEARCH_SOURCE_SEARCH_TOOL:
                if state["searches"] >= (
                    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_SOURCE_SEARCHES
                ):
                    raise ClientToolInputError(
                        "preflight source-search budget exhausted"
                    )
                if set(tool_input) - {"query", "top_k"}:
                    raise ClientToolInputError(
                        "search_research_sources accepts query and optional top_k"
                    )
            elif set(tool_input) != {
                "document_id",
                "line_start",
                "line_end",
            }:
                raise ClientToolInputError(
                    "read_research_source requires document_id, line_start, and "
                    "line_end"
                )
            observation, visible_result = _research_source_preflight_observation(
                research_sources=research_sources,
                operation=call.name,
                tool_input=tool_input,
                source_index=int(state["source_operations"]) + 1,
                exclude_hit_ids=set(state["source_ref_by_hit_id"]),
                prior_source_refs=state["source_ref_by_hit_id"],
            )
            state["source_operations"] += 1
            if call.name == RESEARCH_SOURCE_SEARCH_TOOL:
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
                    **visible_result,
                    "observation_id": observation_id,
                    "remaining_searches": (
                        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_SOURCE_SEARCHES
                        - state["searches"]
                    ),
                },
                state_changed=True,
                observation_key=observation_id,
            )

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
            if source_scope not in allowed_source_scopes:
                raise ClientToolInputError("source_scope is invalid")
            if not 1 <= k <= 8:
                raise ClientToolInputError("k must be between 1 and 8")
            observation = _search_preflight_sources(
                material=material,
                source_retriever=source_retriever,
                query=query,
                source_scope=source_scope,
                k=k,
                search_index=int(state["source_operations"]) + 1,
                exclude_hit_ids=set(state["source_ref_by_hit_id"]),
                prior_source_refs=state["source_ref_by_hit_id"],
            )
            state["searches"] += 1
            state["source_operations"] += 1
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
            if authoritative_documents and not any(
                ref.get("tool") == THEORY_WORKSPACE_READ_DOCUMENT_TOOL
                for ref in state["document_inspection_refs"]
                if isinstance(ref, Mapping)
            ):
                rejection = {
                    "ok": False,
                    "error": "authoritative_theory_document_read_required",
                    "available_documents": [
                        {
                            "path": row["path"],
                            "sha256": row["sha256"],
                            "line_count": row["line_count"],
                        }
                        for row in authoritative_documents.values()
                    ],
                    "regeneration_instruction": (
                        "Read at least one exact range containing a central definition "
                        "or derivation, then independently submit the complete review."
                    ),
                }
                return ClientToolExecutionResult(
                    content=rejection,
                    is_error=True,
                    observation_key="authoritative-theory-document-read-required",
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
                    "regeneration_instruction": (
                        "Submit a complete new typed review after using every listed "
                        "validation observation. Do not swap the citation namespaces."
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
                    "source_grounding_verified": bool(state["observations"]),
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
            + "\nThis live review can query task-bound sources when useful. Do not "
            "cite an external source you did not receive from the client tool."
        ),
        messages=({"role": "user", "content": tool_prompt},),
        tools=tools,
        model=request_model,
        max_tokens=max(1, int(max_tokens)),
        temperature=temperature,
        tool_choice="any",
        disable_parallel_tool_use=False,
        enable_prompt_caching=True,
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
        )
    except ClientToolLoopError as exc:
        raise PacketValidationError(
            validation_label=(
                "Architect theory-to-execution source-grounded preflight review"
            ),
            attempts=exc.turns,
            errors=[exc.reason],
            history=_preflight_evidence_history(exc.history),
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
            history=_preflight_evidence_history(loop.history),
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
            client_tool_loop_history=_preflight_evidence_history(loop.history),
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
            history=_preflight_evidence_history(loop.history),
        )
    packet = _materialize_preflight_review_report(packet, material=material)
    persisted_errors = validate_architect_theory_execution_preflight_packet(
        packet,
        material=material,
    )
    if persisted_errors:
        raise PacketValidationError(
            validation_label=(
                "Architect theory-to-execution source-grounded preflight review"
            ),
            attempts=loop.turns,
            errors=persisted_errors,
            history=_preflight_evidence_history(loop.history),
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
    prior_finding_ledger: Sequence[Mapping[str, Any]] = (),
    source_retriever: Any = None,
    research_sources: ResearchSourceSnapshot | None = None,
    theory_scratchpad: TheoryScratchpadConfig | None = None,
) -> dict[str, Any]:
    if not callable(getattr(provider, "generate_client_tool_turn", None)):
        raise ValueError(
            "theory execution preflight requires native client-tool turns; "
            "JSON-only mathematical review is disabled"
        )
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
    return _review_architect_theory_execution_preflight_with_source_tools(
        provider=provider,
        question=question,
        material=material,
        source_retriever=source_retriever,
        research_sources=research_sources,
        theory_scratchpad=theory_scratchpad,
        request_model=request_model,
        model_tier=model_tier,
        provider_name=provider_name,
        max_tokens=max_tokens,
        temperature=temperature,
    )
