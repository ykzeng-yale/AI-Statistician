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
    load_client_tool_session,
    persist_client_tool_session,
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
from .research_schema import OpenResearchQuestion, research_question_payload
from .research_source_library import (
    RESEARCH_SOURCE_NOT_PROOF_EVIDENCE,
    RESEARCH_SOURCE_READ_TOOL,
    RESEARCH_SOURCE_SEARCH_TOOL,
    ResearchSourceSnapshot,
    execute_research_source_client_tool,
    research_source_client_tools,
)
from .research_source_discovery import (
    RESEARCH_SOURCE_DISCOVERY_NOT_PROOF_EVIDENCE,
    RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
    RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL,
    ResearchSourceDiscovery,
    ResearchSourceDiscoveryError,
    ResearchSourceDiscoveryInputError,
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
    research_source_discovery_client_tools,
    search_theory_document_lines,
    theory_document_client_tools,
    theory_scratchpad_client_tool,
)

ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SCHEMA_VERSION = 28
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL_VERSION = 45
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
    "client_tool_model_directed_document_and_source_inspection_v18"
)
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_REVIEW_TRANSPORT = (
    "model_owned_markdown_referee_workspace_with_compact_disposition_v10"
)
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_REVIEW_AUTHORITY = "model_authored_markdown_referee_report"
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WRITE_REPORT_TOOL = "write_theory_preflight_report"
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_EDIT_REPORT_TOOL = "edit_theory_preflight_report"
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_READ_REPORT_TOOL = "read_theory_preflight_report"
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_REPORT_DRAFT_KIND = "TheoryExecutionPreflightReviewDraft"
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_SOURCE_SEARCHES = 3
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_TOOL_TURNS = 24
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_TOOL_CALLS = 48
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_NO_PROGRESS_TURNS = 2
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WORKSPACE_CHECKPOINT_KIND = (
    "ArchitectTheoryExecutionPreflightWorkspaceCheckpoint"
)
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_BOUNDARY = (
    "This independent review can reject mathematically inconsistent theory. It "
    "reviews a finite estimator handoff only when the frozen task contract requests "
    "executable evidence; it is not execution, empirical acceptance, or proof."
)
ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL = (
    (
        "The authoritative Markdown or LaTeX documents contain the candidate "
        "mathematics; the structured handoff is only an index and execution "
        "interface. Treat every active definition, assumption, equation, theorem, "
        "sanity check, and expected behavior as unverified. Use model-directed "
        "search and exact range reads, and do not invent task-specific mathematics, "
        "code, thresholds, observations, or proof claims."
    ),
    (
        "Run two distinct audits before deciding. First build the smallest dependency "
        "graph that reaches every requested conclusion or scope boundary. Trace the "
        "question, estimand, probability law, assumptions, regime, claimed object, and "
        "finite handoff. Reconstruct each load-bearing transition from its original "
        "definitions and compare it with the candidate's actual written intermediate. "
        "A correct endpoint cannot validate a false, circular, or unsupported step."
    ),
    (
        "Second sweep the complete active document, not only that dependency graph. Try "
        "to falsify definitions, explanatory justifications, assumptions, measure and "
        "type declarations, regularity claims, and scope statements with a symbolic "
        "reduction, special or boundary case, counterexample, scale check, or "
        "order-of-magnitude check. A materially false active assertion blocks ACCEPT even "
        "when the requested endpoint is correct or does not depend on it. A later "
        "correction does not deactivate earlier false text; only material clearly "
        "delimited as REJECTED or SCRATCH is nonauthoritative. Scratch and retrieval are "
        "observations for the referee to interpret, not proof or acceptance evidence."
    ),
    (
        "Separate mathematical coherence, proof completeness, executable handoff, and "
        "empirical confirmation. A false or internally contradictory active claim is a "
        "blocker. An honestly marked open step may remain UNCERTAIN when the finite "
        "handoff is still coherent, but reviewer-added premises, lemmas, or replacement "
        "proofs cannot support ACCEPT. Pre-review scratch is exploratory; if a judgment "
        "needs downstream execution or confirmatory simulation, disclose that missing "
        "evidence instead of manufacturing it."
    ),
    (
        "Write a findings-first Markdown review after both audits. Return every discrete "
        "blocker that the author would correct, one compact finding per blocker, citing "
        "exact read ranges. "
        "Do not add an executive summary, strengths, praise, or section-by-section "
        "verification. If no blocker survives both audits, say so briefly; "
        "do not reproduce the candidate or write a substitute proof. Reconcile later "
        "observations, close prior findings only from current evidence, and mark genuine "
        "uncertainty. The model-owned report owns judgment; runtime binds and persists it."
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
    estimator_specs, estimator_ids = _project_estimator_specs(
        semantic.get("estimator_specs", [])
    )

    sections: Sequence[tuple[str, str, Any]] = (
        (
            "question",
            "research_question",
            research_question_payload(question, include_task_intent=True),
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
            "content": deepcopy(content) if anchor_id == "question" else _compact_anchor_content(content),
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
    execution_handoff_required = not (
        isinstance(dimension_requirements, Mapping)
        and dimension_requirements
        and dimension_requirements.get("scientific_code")
        == dimension_requirements.get("empirical")
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
        "execution_handoff_required": execution_handoff_required,
        "execution_handoff_available": bool(estimator_ids),
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


def _runtime_review_scope(material: Mapping[str, Any]) -> dict[str, Any]:
    """Project task intent without turning candidate claims into a review agenda."""

    return {
        "execution_handoff_required": bool(
            material.get("execution_handoff_required", True)
        ),
        "execution_handoff_available": bool(
            material.get("execution_handoff_available", False)
        ),
        "formal_sources_applicable": _preflight_formal_sources_applicable(
            material
        ),
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
        key: deepcopy(material.get(key))
        for key in (
            "schema_version",
            "artifact_kind",
            "question_id",
            "source_theory_packet_id",
            "source_theory_packet_hash",
            "execution_results_available",
            "preflight_revision_index",
            "formal_sources_applicable",
            "proof_evidence_status",
            "boundary",
        )
        if key in material
    }
    # The frozen public objective is the review target, not context to summarize.
    source_material["research_question"] = deepcopy(
        anchor_by_id.get("question", {}).get("content", {})
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
    canonical_document_tool_context = bool(authoritative_documents) and not (
        include_authoritative_document_content
    )
    inline_structured_anchor_ids = {
        "theory.estimator_specs",
        "theory.simulation_ademp_spec",
    }
    current_theory_anchors: list[dict[str, Any]] = []
    for anchor in anchor_catalog:
        anchor_id = str(anchor.get("anchor_id", "") or "")
        artifact_role = str(anchor.get("artifact_role", "") or "")
        if anchor_id in {"question", "architect.upstream_research_contract"}:
            continue
        if (
            artifact_role == "authoritative_theory_document"
            and not include_authoritative_document_content
        ):
            continue
        row = {
            "anchor_id": anchor_id,
            "artifact_role": artifact_role,
        }
        if (
            not canonical_document_tool_context
            or artifact_role == "authoritative_theory_document"
            or anchor_id in inline_structured_anchor_ids
        ):
            row["content"] = deepcopy(anchor.get("content"))
        else:
            row["content_access"] = (
                "authoritative_document_tools_or_model_directed_compact_search"
                if compact_source_search_available
                else "authoritative_document_tools"
            )
        current_theory_anchors.append(row)
    source_material["current_theory_anchors"] = current_theory_anchors
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
            "Decide whether this theory handoff is mathematically coherent and, only "
            "when review_scope requests an execution handoff, representable by a "
            "finite generated-code and simulation workflow."
        ),
        "review_protocol_version": ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL_VERSION,
        "review_protocol": list(ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL),
        "review_scope": {
            **_runtime_review_scope(material),
            "active_prior_finding_slots": [
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
            "Return every discrete blocker and one ACCEPT or REVISE disposition in a "
            "findings-first Markdown report. ACCEPT requires both protocol audits to "
            "leave no material active falsehood or unsupported load-bearing step, and "
            "requires every prior finding to be closed by current evidence. A correct "
            "endpoint, reviewer reconstruction, or later correction cannot repair active "
            "candidate text. Ground each blocker in an exact inspected range plus a "
            "checkable derivation, reduction, or counterexample. Keep downstream proof "
            "obligations separate. Require a finite estimator only when review_scope "
            "marks the execution handoff required; otherwise do not invent one. The "
            "Markdown report owns judgment; "
            "the terminal envelope carries only its hash, disposition, findings, and "
            "ordered prior-finding statuses."
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
            "evidence_refs field is validated against hash-bound theory anchors."
        ),
    }
    prior_count = len(material.get("active_prior_finding_ids", []) or [])
    properties: dict[str, Any] = {
        "review_report_sha256": {
            "type": "string",
            "pattern": "^[0-9a-f]{64}$",
            "description": (
                "Exact SHA-256 returned by write_theory_preflight_report or "
                "edit_theory_preflight_report for the current model-owned Markdown "
                "referee report. The terminal envelope never regenerates its body."
            ),
        },
        "report_evidence_refs": {
            "type": "array",
            "minItems": 1,
            "maxItems": 32,
            "items": {
                "type": "string",
                "minLength": 1,
                "maxLength": 240,
            },
            "description": (
                "Theory documents and compact handoff anchors actually inspected and "
                "used by the Markdown report. Runtime validates these references "
                "against the hash-bound review material."
            ),
        },
        "overall_verdict": {
            "type": "string",
            "enum": ["ACCEPT", "REVISE"],
            "description": (
                "The independent referee's disposition. ACCEPT is valid only when "
                "the report identifies no blocking finding and closes every active "
                "prior finding; otherwise use REVISE."
            ),
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
        "review_report_sha256",
        "report_evidence_refs",
        "overall_verdict",
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
                "maxItems": 12,
                "items": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 240,
                },
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
    if operation not in {RESEARCH_SOURCE_SEARCH_TOOL, RESEARCH_SOURCE_READ_TOOL}:
        raise ClientToolInputError("unsupported research source operation")
    try:
        visible, _ = execute_research_source_client_tool(
            research_sources,
            tool_name=operation,
            tool_input=tool_input,
        )
    except ValueError as exc:
        raise ClientToolInputError(str(exc)) from exc

    if operation == RESEARCH_SOURCE_SEARCH_TOOL:
        source_scope = "research_sources"
        retrieval_fusion = "hash_bound_research_source_search_v1"
        raw_hits = list(visible.get("hits", []) or [])
        operation_query = str(visible.get("query", "") or "")
    else:
        source_scope = "research_source_read"
        retrieval_fusion = "hash_bound_research_source_exact_read_v1"
        raw_hits = [visible]
        operation_query = (
            f"{visible['document_id']}:{visible['line_start']}-"
            f"{visible['line_end']}"
        )

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


def _public_research_source_preflight_read_observation(
    *,
    visible: Mapping[str, Any],
    descriptor: Mapping[str, Any],
    source_index: int,
    exclude_hit_ids: set[str] | None = None,
    prior_source_refs: Mapping[str, str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    content = str(visible.get("content", "") or "")
    provider = str(
        visible.get("provider", "") or descriptor.get("provider", "") or ""
    ).strip()
    source_handle = str(visible.get("source_handle", "") or "").strip()
    revision = str(visible.get("revision", "") or "").strip()
    path = str(visible.get("path", "") or "").strip()
    content_sha256 = str(visible.get("content_sha256", "") or "").strip()
    observed_content_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    if not all((provider, source_handle, revision, path, content_sha256)):
        raise RuntimeError(
            "public research source read omitted an immutable source identity"
        )
    if (
        visible.get("content_truncated") is not True
        and content_sha256 != observed_content_sha256
    ):
        raise RuntimeError("public research source read content hash mismatch")

    source_identity = ":".join(
        (
            provider,
            source_handle,
            revision,
            path,
            content_sha256,
            observed_content_sha256,
        )
    )
    row = _preflight_source_row(
        source_kind="public_research_source_exact_read",
        source_identity=source_identity,
        title=str(visible.get("title", "") or source_handle),
        location=str(visible.get("url", "") or path),
        content={
            "provider": provider,
            "source_handle": source_handle,
            "source_kind": str(visible.get("source_kind", "") or ""),
            "revision": revision,
            "path": path,
            "content_sha256": content_sha256,
            "observed_content_sha256": observed_content_sha256,
            "content_truncated": bool(visible.get("content_truncated", False)),
            "citation_ref": str(visible.get("citation_ref", "") or ""),
        },
        provenance={
            "source_horizon": str(descriptor.get("source_horizon", "") or ""),
            "citation": str(visible.get("citation", "") or ""),
            "url": str(visible.get("url", "") or ""),
            "publication_date": str(
                visible.get("publication_date", "") or ""
            ),
            "model_selected_query_and_source": True,
            "independent_referee_session": True,
        },
        content_max_depth=4,
        content_list_limit=12,
        content_text_limit=500,
    )
    hit_id = str(row["source_hit_id"])
    excluded = set(exclude_hit_ids or set())
    prior_ref = str(dict(prior_source_refs or {}).get(hit_id, "") or "").strip()
    if hit_id in excluded and prior_ref:
        compact_hits: list[dict[str, Any]] = []
        duplicate_source_refs_reused = [prior_ref]
        source_ref = prior_ref
    else:
        source_ref = f"S{source_index}H1"
        compact_hits = [
            {
                **row,
                "source_ref": source_ref,
                "retrieval_channel": "public_research_source",
                "retrieval_rank_within_channel": 1,
                "retrieval_score": 1.0,
            }
        ]
        duplicate_source_refs_reused = []
    observation_core = {
        "query": f"{source_handle}:{revision}:{path}",
        "source_scope": "public_research_source_read",
        "hits": compact_hits,
        "duplicate_source_refs_reused": duplicate_source_refs_reused,
        "provider_errors": [],
        "retrieval_fusion": "model_directed_public_source_exact_read_v1",
    }
    persisted = {
        "observation_id": (
            "preflight_source_observation:"
            + stable_hash(observation_core)[:20]
        ),
        **observation_core,
        "boundary": (
            "This hash-bound public-source passage was independently selected and "
            "read by the reviewing model. It is literature or code evidence, not "
            "replication evidence, mathematical proof, or kernel evidence."
        ),
    }
    visible_result = {
        **dict(visible),
        "source_hit_id": hit_id,
        "source_ref": source_ref,
        "duplicate_source_refs_reused": duplicate_source_refs_reused,
        "proof_evidence_status": RESEARCH_SOURCE_DISCOVERY_NOT_PROOF_EVIDENCE,
    }
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


def _derived_verdict(
    packet: Mapping[str, Any], *, material: Mapping[str, Any]
) -> str:
    """Return the disposition consistent with review and finding lineage."""

    prior_finding_reviews = packet.get("prior_finding_reviews", [])
    all_prior_findings_resolved = all(
        isinstance(row, Mapping)
        and str(row.get("status", "") or "").strip().upper()
        in _PREFLIGHT_CLOSED_PRIOR_FINDING_STATUSES
        for row in prior_finding_reviews or []
    )
    execution_scope_ready = not bool(
        material.get("execution_handoff_required", True)
    ) or bool(material.get("execution_handoff_available", False))
    accepted = (
        execution_scope_ready
        and all_prior_findings_resolved
        and not packet.get("findings", [])
    )
    return "ACCEPT" if accepted else "REVISE"


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


def _preflight_review_draft_path(material: Mapping[str, Any]) -> Path:
    workspace_root = str(material.get("review_workspace_root", "") or "").strip()
    if not workspace_root:
        raise ValueError("theory preflight review workspace is unavailable")
    return (Path(workspace_root).expanduser().resolve() / "review-draft.md")


def _preflight_review_draft_manifest(
    *,
    content: str,
    material: Mapping[str, Any],
    version: int,
) -> dict[str, Any]:
    path = _preflight_review_draft_path(material)
    return {
        "schema_version": 1,
        "artifact_kind": (
            ARCHITECT_THEORY_EXECUTION_PREFLIGHT_REPORT_DRAFT_KIND
        ),
        "content_authority": ARCHITECT_THEORY_EXECUTION_PREFLIGHT_REVIEW_AUTHORITY,
        "media_type": "text/markdown",
        "relative_path": path.name,
        "path": str(path),
        "sha256": _preflight_text_sha256(content),
        "byte_size": len(content.encode("utf-8")),
        "version": version,
        "persisted": True,
        "proof_evidence_status": (
            ARCHITECT_THEORY_EXECUTION_PREFLIGHT_NOT_PROOF_EVIDENCE
        ),
    }


def _preflight_review_draft_content(
    draft: Mapping[str, Any],
    *,
    material: Mapping[str, Any],
) -> str:
    if (
        draft.get("schema_version") != 1
        or draft.get("artifact_kind")
        != ARCHITECT_THEORY_EXECUTION_PREFLIGHT_REPORT_DRAFT_KIND
        or draft.get("content_authority")
        != ARCHITECT_THEORY_EXECUTION_PREFLIGHT_REVIEW_AUTHORITY
        or draft.get("media_type") != "text/markdown"
        or draft.get("persisted") is not True
        or draft.get("proof_evidence_status")
        != ARCHITECT_THEORY_EXECUTION_PREFLIGHT_NOT_PROOF_EVIDENCE
        or isinstance(draft.get("version"), bool)
        or not isinstance(draft.get("version"), int)
        or int(draft.get("version", 0) or 0) < 1
    ):
        raise ValueError("theory preflight review draft identity is invalid")
    expected_path = _preflight_review_draft_path(material)
    observed_path = Path(str(draft.get("path", "") or "")).expanduser().resolve()
    if (
        observed_path != expected_path
        or observed_path.parent != expected_path.parent
        or str(draft.get("relative_path", "") or "") != expected_path.name
    ):
        raise ValueError("theory preflight review draft path is stale")
    if not observed_path.is_file():
        raise ValueError("theory preflight review draft file is missing")
    content = observed_path.read_text(encoding="utf-8")
    byte_size = draft.get("byte_size")
    if (
        not content.strip()
        or _preflight_text_sha256(content) != str(draft.get("sha256", "") or "")
        or isinstance(byte_size, bool)
        or not isinstance(byte_size, int)
        or len(content.encode("utf-8")) != byte_size
    ):
        raise ValueError("theory preflight review draft content is stale")
    return content


def _write_preflight_review_draft(
    *,
    content: str,
    material: Mapping[str, Any],
    prior_draft: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], bool]:
    if not content.strip():
        raise ClientToolInputError(
            "theory preflight review report must be nonempty Markdown"
        )
    prior = dict(prior_draft) if isinstance(prior_draft, Mapping) else {}
    if prior and str(prior.get("sha256", "") or "") == _preflight_text_sha256(
        content
    ):
        _preflight_review_draft_content(prior, material=material)
        return prior, False
    path = _preflight_review_draft_path(material)
    path.parent.mkdir(parents=True, exist_ok=True)
    content_sha256 = _preflight_text_sha256(content)
    snapshot_path = path.parent / f"review-draft-{content_sha256}.md"
    if snapshot_path.exists() and snapshot_path.read_text(encoding="utf-8") != content:
        raise ValueError("theory preflight report snapshot hash collision")
    snapshot_path.write_text(content, encoding="utf-8")
    path.write_text(content, encoding="utf-8")
    version = int(prior.get("version", 0) or 0) + 1
    draft = _preflight_review_draft_manifest(
        content=content,
        material=material,
        version=version,
    )
    _preflight_review_draft_content(draft, material=material)
    return draft, True


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
        "overall_verdict",
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
    if str(payload.get("overall_verdict", "") or "").strip().upper() not in {
        "ACCEPT",
        "REVISE",
    }:
        raise ClientToolInputError(
            "overall_verdict must be ACCEPT or REVISE"
        )
    array_fields = required_fields - {
        "review_report_markdown",
        "overall_verdict",
    }
    for field in sorted(array_fields):
        if not isinstance(payload.get(field), list):
            raise ClientToolInputError(f"{field} must be a JSON array")
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
    model_verdict = str(body.get("overall_verdict", "") or "").strip().upper()
    body["review_scope"] = _runtime_review_scope(material)
    if "prior_finding_statuses" in body:
        body["prior_finding_reviews"] = [
            {
                "status": str(status or "").strip().upper(),
                "review_report_ref": report_ref,
            }
            for status in body.get("prior_finding_statuses", []) or []
        ]
    for field in (
        "prior_finding_statuses",
        "report_evidence_refs",
    ):
        body.pop(field, None)
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
    body["overall_verdict"] = model_verdict
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
        content = persisted_content
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

    expected_review_scope = _runtime_review_scope(material)
    if packet.get("review_scope") != expected_review_scope:
        errors.append(
            "theory execution preflight task-intent review scope mismatch"
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
        if not report_ref or any(
            str(row.get("review_report_ref", "") or "") != report_ref
            for row in prior_finding_reviews
        ):
            errors.append(
                "theory execution preflight prior-finding statuses are not bound to the "
                "review report"
            )
    cited_rows = [
        row
        for row in packet.get("findings", []) or []
        if isinstance(row, Mapping)
    ]
    for row in cited_rows:
        refs = [str(value) for value in row.get("evidence_refs", []) or []]
        if not refs or any(ref not in valid_anchor_ids for ref in refs):
            errors.append("theory execution preflight uses missing or unknown evidence refs")
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
    expected_verdict = _derived_verdict(packet, material=material)
    if packet.get("overall_verdict") != expected_verdict:
        errors.append(
            "theory execution preflight overall verdict contradicts its blocking "
            "findings or prior-finding dispositions"
        )
    if (
        material.get("execution_handoff_required", True)
        and not material.get("execution_handoff_available", False)
        and packet.get("overall_verdict") == "ACCEPT"
    ):
        errors.append("theory execution preflight cannot accept without an estimator")
    if packet.get("overall_verdict") == "REVISE" and not findings:
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
You are the independent mathematical referee inside an AI Statistician AgentRuntime.
The exact frozen research question is your review target. Use the stable workspace tools to inspect authoritative Markdown or LaTeX. First reconstruct the requested load-bearing chain from definitions. Then sweep every other active assertion for contradictions, including explanatory reasons, assumptions, measure and type statements, regularity, and scope. A later correction does not deactivate earlier false text unless it is explicitly delimited as SCRATCH or REJECTED. Any material active falsehood blocks ACCEPT even when the requested endpoint is correct. Report every discrete blocker first, without praise or a verification essay, and never silently supply a repair. Keep mutations and terminal submission causally after their observations. The Markdown report owns your judgment; runtime owns only identity, persistence, and evidence boundaries.
Treat every tool result as an observation: never describe a rejected or failed run as passed.
"""


def _preflight_tool_history(history: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"turn_index": row.get("turn_index"), "tool_calls": [
            {"name": call.get("name"), "is_error": call.get("is_error"),
             "terminal": call.get("terminal"), "result_excerpt": call.get("result_excerpt") if call.get("is_error") else "[exact result in client_tool_session_ref]"}
            for call in row.get("tool_calls", []) if isinstance(call, Mapping)]}
        for row in history]


def seal_architect_theory_preflight_workspace_checkpoint(
    checkpoint: Mapping[str, Any],
) -> dict[str, Any]:
    """Content-address one exact independent-referee workspace checkpoint."""

    body = deepcopy(dict(checkpoint))
    body.pop("checkpoint_id", None)
    return {
        **body,
        "checkpoint_id": (
            "architect_theory_preflight_workspace_checkpoint:"
            + stable_hash(body)[:20]
        ),
    }


def _architect_theory_preflight_workspace_checkpoint_errors(
    checkpoint: Mapping[str, Any],
    *,
    question_id: str | None = None,
    review_material_fingerprint: str | None = None,
    source_theory_packet_id: str | None = None,
    source_theory_packet_hash: str | None = None,
    review_workspace_root: str | None = None,
    require_resumable: bool = True,
) -> list[str]:
    errors: list[str] = []
    if checkpoint.get("artifact_kind") != (
        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WORKSPACE_CHECKPOINT_KIND
    ):
        errors.append("checkpoint artifact kind is not the referee workspace kind")
    if checkpoint.get("schema_version") != 1:
        errors.append("checkpoint schema version is not supported")
    checkpoint_id = str(checkpoint.get("checkpoint_id", "") or "").strip()
    expected = seal_architect_theory_preflight_workspace_checkpoint(checkpoint)
    if checkpoint_id != expected["checkpoint_id"]:
        errors.append("checkpoint content identity is missing or stale")
    for expected_value, field, label in (
        (question_id, "question_id", "question"),
        (
            review_material_fingerprint,
            "review_material_fingerprint",
            "review material",
        ),
        (source_theory_packet_id, "source_theory_packet_id", "theory packet"),
        (source_theory_packet_hash, "source_theory_packet_hash", "theory hash"),
    ):
        observed = str(checkpoint.get(field, "") or "")
        if not observed:
            errors.append(f"checkpoint {label} binding is empty")
        if expected_value is not None and observed != str(expected_value):
            errors.append(f"checkpoint {label} binding is stale")
    if (
        checkpoint.get("independent_reviewer_workspace") is not True
        or checkpoint.get("runtime_selected_review_semantics") is not False
        or checkpoint.get("implementation_authorized") is not False
        or checkpoint.get("accepted") is not False
        or checkpoint.get("kernel_verified") is not False
    ):
        errors.append("checkpoint crosses the referee evidence boundary")

    observed_review_workspace_root = str(
        checkpoint.get("review_workspace_root", "") or ""
    ).strip()
    if observed_review_workspace_root and review_workspace_root is not None and (
        Path(observed_review_workspace_root).expanduser().resolve()
        != Path(review_workspace_root).expanduser().resolve()
    ):
        errors.append("checkpoint review workspace binding is stale")
    review_report_draft = checkpoint.get("review_report_draft", {})
    if not isinstance(review_report_draft, Mapping):
        errors.append("checkpoint referee report draft manifest is malformed")
    elif review_report_draft and not observed_review_workspace_root:
        errors.append("checkpoint report draft has no review workspace binding")
    elif review_report_draft:
        try:
            _preflight_review_draft_content(
                review_report_draft,
                material={
                    "review_workspace_root": observed_review_workspace_root,
                },
            )
        except (OSError, ValueError) as exc:
            errors.append(f"checkpoint referee report draft is stale: {exc}")

    counter_fields = (
        "searches",
        "source_operations",
        "scratch_runs",
        "client_tool_loop_turns",
        "client_tool_loop_tool_calls",
        "client_tool_loop_runtime_executed_tool_calls",
    )
    segment_starts = checkpoint.get("segment_start_counters", {})
    if not isinstance(segment_starts, Mapping):
        segment_starts = {}
        errors.append("checkpoint segment-start counters are malformed")
    for field in counter_fields:
        value = checkpoint.get(field, 0)
        start = segment_starts.get(field, 0)
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
            or isinstance(start, bool)
            or not isinstance(start, int)
            or start < 0
            or start > value
        ):
            errors.append(f"checkpoint {field} counter lineage is invalid")
    if int(checkpoint.get("searches", 0) or 0) > (
        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_SOURCE_SEARCHES
    ):
        errors.append("checkpoint source-search budget was exceeded")
    if int(checkpoint.get("source_operations", 0) or 0) < int(
        checkpoint.get("searches", 0) or 0
    ):
        errors.append("checkpoint source-operation count is inconsistent")

    observations = checkpoint.get("preflight_source_observations", [])
    if not isinstance(observations, list) or any(
        not isinstance(row, Mapping) for row in observations
    ):
        observations = []
        errors.append("checkpoint source observations are malformed")
    observation_ids = [
        str(row.get("observation_id", "") or "") for row in observations
    ]
    if any(not value for value in observation_ids) or len(observation_ids) != len(
        set(observation_ids)
    ):
        errors.append("checkpoint source observation identities are invalid")
    refs = checkpoint.get("source_ref_by_hit_id", {})
    if not isinstance(refs, Mapping) or any(
        not str(key).strip() or not str(value).strip()
        for key, value in (refs.items() if isinstance(refs, Mapping) else ())
    ):
        refs = {}
        errors.append("checkpoint source handles are malformed")
    derived_refs: dict[str, str] = {}
    for observation in observations:
        for hit in observation.get("hits", []) or []:
            if not isinstance(hit, Mapping):
                continue
            hit_id = str(hit.get("source_hit_id", "") or "").strip()
            source_ref = str(hit.get("source_ref", "") or "").strip()
            if hit_id and source_ref:
                derived_refs[hit_id] = source_ref
    if dict(refs) != derived_refs:
        errors.append("checkpoint source handles do not match exact observations")

    for field in (
        "theory_document_inspection_refs",
        "preflight_scratch_execution_refs",
    ):
        rows = checkpoint.get(field, [])
        if not isinstance(rows, list) or any(
            not isinstance(row, Mapping) for row in rows
        ):
            errors.append(f"checkpoint {field} are malformed")
    scratch_refs = checkpoint.get("preflight_scratch_execution_refs", [])
    if isinstance(scratch_refs, list) and int(
        checkpoint.get("scratch_runs", 0) or 0
    ) != len(scratch_refs):
        errors.append("checkpoint scratch count does not match exact executions")

    workspace_observations = checkpoint.get("workspace_observations", [])
    if not isinstance(workspace_observations, list) or any(
        not isinstance(row, Mapping) for row in workspace_observations
    ):
        workspace_observations = []
        errors.append("checkpoint model-visible observations are malformed")
    observed_fingerprints: list[str] = []
    for row in workspace_observations:
        body = deepcopy(dict(row))
        fingerprint = str(body.pop("observation_fingerprint", "") or "")
        expected_fingerprint = (
            "theory-preflight-workspace-observation:" + stable_hash(body)[:20]
        )
        if fingerprint != expected_fingerprint:
            errors.append("checkpoint model-visible observation identity is stale")
        observed_fingerprints.append(fingerprint)
    fingerprints = checkpoint.get("workspace_observation_fingerprints", [])
    if (
        not isinstance(fingerprints, list)
        or fingerprints != observed_fingerprints
        or any(not value for value in fingerprints)
        or len(fingerprints) != len(set(fingerprints))
    ):
        fingerprints = []
        errors.append("checkpoint workspace observation lineage is malformed")
    segment_start = checkpoint.get("segment_start_observation_count", 0)
    if (
        isinstance(segment_start, bool)
        or not isinstance(segment_start, int)
        or segment_start < 0
        or segment_start > len(fingerprints)
    ):
        segment_start = len(fingerprints)
        errors.append("checkpoint segment observation boundary is invalid")
    made_progress = len(fingerprints) > segment_start
    if checkpoint.get("resumable") is not made_progress:
        errors.append("checkpoint resumable status does not match observed progress")
    if checkpoint.get("model_owned_workspace_actions") is not made_progress:
        errors.append("checkpoint model-action status does not match observed progress")
    if require_resumable and not made_progress:
        errors.append("referee workspace made no new environment-observed progress")
    return sorted(set(errors))


def load_architect_theory_preflight_workspace_checkpoint(
    checkpoint: Mapping[str, Any],
    *,
    question_id: str,
    review_material_fingerprint: str,
    source_theory_packet_id: str,
    source_theory_packet_hash: str,
    review_workspace_root: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Restore exact independent-referee observations without accepting them."""

    errors = _architect_theory_preflight_workspace_checkpoint_errors(
        checkpoint,
        question_id=question_id,
        review_material_fingerprint=review_material_fingerprint,
        source_theory_packet_id=source_theory_packet_id,
        source_theory_packet_hash=source_theory_packet_hash,
        review_workspace_root=review_workspace_root,
    )
    if errors:
        raise PacketValidationError(
            validation_label="Architect theory preflight workspace checkpoint",
            attempts=1,
            errors=errors,
            history=[],
            recovery_checkpoint=checkpoint,
        )
    state = {
        "searches": int(checkpoint.get("searches", 0) or 0),
        "source_operations": int(
            checkpoint.get("source_operations", 0) or 0
        ),
        "observations": deepcopy(
            list(checkpoint.get("preflight_source_observations", []) or [])
        ),
        "observation_ids": {
            str(row.get("observation_id", "") or "")
            for row in checkpoint.get("preflight_source_observations", []) or []
            if isinstance(row, Mapping)
        },
        "source_ref_by_hit_id": {
            str(key): str(value)
            for key, value in dict(
                checkpoint.get("source_ref_by_hit_id", {}) or {}
            ).items()
        },
        "document_inspection_refs": deepcopy(
            list(checkpoint.get("theory_document_inspection_refs", []) or [])
        ),
        "scratch_runs": int(checkpoint.get("scratch_runs", 0) or 0),
        "scratch_execution_refs": deepcopy(
            list(checkpoint.get("preflight_scratch_execution_refs", []) or [])
        ),
        "review_report_draft": deepcopy(
            dict(checkpoint.get("review_report_draft", {}) or {})
        ),
        "workspace_observations": deepcopy(
            list(checkpoint.get("workspace_observations", []) or [])
        ),
        "workspace_observation_fingerprints": set(
            checkpoint.get("workspace_observation_fingerprints", []) or []
        ),
        "client_tool_loop_turns": int(
            checkpoint.get("client_tool_loop_turns", 0) or 0
        ),
        "client_tool_loop_tool_calls": int(
            checkpoint.get("client_tool_loop_tool_calls", 0) or 0
        ),
        "client_tool_loop_runtime_executed_tool_calls": int(
            checkpoint.get(
                "client_tool_loop_runtime_executed_tool_calls", 0
            )
            or 0
        ),
    }
    return state, {
        "resumed_from_checkpoint_id": str(
            checkpoint.get("checkpoint_id", "") or ""
        ),
        "resumed_from_model_checkpoint": True,
    }


def architect_theory_preflight_workspace_continuation_errors(
    checkpoint: Mapping[str, Any],
    *,
    prior_checkpoint: Mapping[str, Any] | None = None,
) -> list[str]:
    """Reject stale, unbound, or observation-free referee continuations."""

    errors = _architect_theory_preflight_workspace_checkpoint_errors(checkpoint)
    predecessor = prior_checkpoint if isinstance(prior_checkpoint, Mapping) else {}
    resumed_from = str(checkpoint.get("resumed_from_checkpoint_id", "") or "")
    if predecessor:
        if _architect_theory_preflight_workspace_checkpoint_errors(predecessor):
            errors.append("prior referee workspace checkpoint is invalid")
        prior_id = str(predecessor.get("checkpoint_id", "") or "")
        if resumed_from != prior_id:
            errors.append("referee workspace checkpoint predecessor is stale")
        prior_fingerprints = set(
            predecessor.get("workspace_observation_fingerprints", []) or []
        )
        current_fingerprints = set(
            checkpoint.get("workspace_observation_fingerprints", []) or []
        )
        if not prior_fingerprints < current_fingerprints:
            errors.append("referee workspace continuation added no new observation")
        if checkpoint.get("segment_start_observation_count") != len(
            prior_fingerprints
        ):
            errors.append("referee workspace observation boundary is stale")
        starts = checkpoint.get("segment_start_counters", {})
        for field in (
            "searches",
            "source_operations",
            "scratch_runs",
            "client_tool_loop_turns",
            "client_tool_loop_tool_calls",
            "client_tool_loop_runtime_executed_tool_calls",
        ):
            if not isinstance(starts, Mapping) or starts.get(field) != (
                predecessor.get(field)
            ):
                errors.append("referee workspace counter boundary is stale")
                break
    elif resumed_from:
        errors.append("referee workspace checkpoint has an unbound predecessor")
    return sorted(set(errors))


def _review_architect_theory_execution_preflight_with_source_tools(
    *,
    provider: GeneratorBackend,
    question: OpenResearchQuestion,
    material: Mapping[str, Any],
    source_retriever: Any,
    research_sources: ResearchSourceSnapshot | None,
    research_source_discovery: ResearchSourceDiscovery | None,
    theory_scratchpad: TheoryScratchpadConfig | None,
    request_model: str,
    model_tier: str,
    provider_name: str,
    max_tokens: int,
    temperature: float,
    max_tool_turns: int,
    max_tool_calls: int,
    max_no_progress_turns: int,
    recovery_checkpoint: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    submit_schema = _architect_theory_execution_preflight_submit_schema(
        material
    )
    authoritative_documents = _preflight_authoritative_theory_documents(material)
    allowed_source_scopes = _preflight_allowed_source_scopes(material)
    formal_sources_applicable = _preflight_formal_sources_applicable(material)
    public_source_descriptor: dict[str, Any] = {}
    if research_source_discovery is not None:
        descriptor = research_source_discovery.descriptor()
        if not isinstance(descriptor, Mapping):
            raise RuntimeError(
                "public research source discovery returned an invalid descriptor"
            )
        public_source_descriptor = dict(descriptor)
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
        *(
            research_source_discovery_client_tools()
            if research_source_discovery is not None
            else ()
        ),
        *compact_source_tools,
        *((theory_scratchpad_client_tool(),) if theory_scratchpad else ()),
        ClientToolDefinition(
            name=ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WRITE_REPORT_TOOL,
            description=(
                "Write one findings-first, source-grounded model-owned Markdown report. "
                "Return every blocker; omit praise and section-by-section verification. "
                "Exact bytes remain available for hash-bound edits and compact submission."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["content"],
                "properties": {
                    "content": {"type": "string", "minLength": 1},
                },
            },
        ),
        ClientToolDefinition(
            name=ARCHITECT_THEORY_EXECUTION_PREFLIGHT_EDIT_REPORT_TOOL,
            description=(
                "Apply one exact hash-bound local replacement to the current "
                "model-owned Markdown referee report."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["expected_sha256", "old_text", "new_text"],
                "properties": {
                    "expected_sha256": {
                        "type": "string",
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "old_text": {"type": "string", "minLength": 1},
                    "new_text": {"type": "string"},
                },
            },
        ),
        ClientToolDefinition(
            name=ARCHITECT_THEORY_EXECUTION_PREFLIGHT_READ_REPORT_TOOL,
            description=(
                "Read an exact inclusive line range from the current model-owned "
                "Markdown referee report, bound to its current SHA-256."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["expected_sha256", "line_start", "line_end"],
                "properties": {
                    "expected_sha256": {
                        "type": "string",
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "line_start": {"type": "integer", "minimum": 1},
                    "line_end": {"type": "integer", "minimum": 1},
                },
            },
        ),
        ClientToolDefinition(
            name="submit_theory_preflight_review",
            description=(
                "Submit the current hash-bound Markdown report with one compact "
                "disposition and actual findings. Use source_evidence_refs only when "
                "citing handles returned "
                "by an optional source tool."
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
        + "\n\nThis is a hash-bound catalog, not the theory text. Choose document "
        "searches and exact range reads yourself; independent read-only calls may be "
        "batched, while scratch, report mutation, and submission must follow the "
        "observations they use."
        + (
            " Task-bound research-source search and exact source reads are available."
            if research_sources is not None
            else ""
        )
        + (
            " An isolated public-source discovery session is also available; read a "
            "selected result before citing it."
            if research_source_discovery is not None
            else ""
        )
        + (
            " Compact runtime source search is available"
            + (", including formal declarations" if formal_sources_applicable else "")
            + "."
            if compact_source_search_available
            else ""
        )
        + (
            " An isolated Python/R scratchpad with SymPy is available for "
            "model-authored discriminating checks; expose both sides and a residual or "
            "witness from definitions, then interpret the raw result yourself."
            if theory_scratchpad is not None
            else ""
        )
        + " Cite only exact ranges or handles returned by tools. Keep evidence_refs "
        "for theory anchor IDs and source_evidence_refs for S...H... handles. No "
        "generated-code or confirmatory result exists here; disclose downstream "
        "uncertainty. Develop the judgment in the Markdown report, and submit only its "
        "current SHA-256, compact disposition, and findings. Do not copy the report into "
        "terminal JSON, write a replacement proof, or answer outside the tools."
    )
    review_workspace_root = str(
        material.get("review_workspace_root", "") or ""
    ).strip()
    review_session_id = "theory_preflight:" + stable_hash(
        [question.id, material.get("source_theory_packet_hash", "")]
    )[:20]
    client_tool_session_ref: dict[str, Any] = {}
    resumed_from_client_tool_session_ref: dict[str, Any] = {}
    state: dict[str, Any] = {
        "searches": 0,
        "source_operations": 0,
        "observations": [],
        "observation_ids": set(),
        "source_ref_by_hit_id": {},
        "document_inspection_refs": [],
        "scratch_runs": 0,
        "scratch_execution_refs": [],
        "review_report_draft": {},
        "workspace_observations": [],
        "workspace_observation_fingerprints": set(),
        "client_tool_loop_turns": 0,
        "client_tool_loop_tool_calls": 0,
        "client_tool_loop_runtime_executed_tool_calls": 0,
    }
    resume_metadata = {
        "resumed_from_checkpoint_id": "",
        "resumed_from_model_checkpoint": False,
    }
    if isinstance(recovery_checkpoint, Mapping) and recovery_checkpoint:
        restored_state, resume_metadata = (
            load_architect_theory_preflight_workspace_checkpoint(
                recovery_checkpoint,
                question_id=question.id,
                review_material_fingerprint=stable_hash(material),
                source_theory_packet_id=str(
                    material.get("source_theory_packet_id", "") or ""
                ),
                source_theory_packet_hash=str(
                    material.get("source_theory_packet_hash", "") or ""
                ),
                review_workspace_root=str(
                    material.get("review_workspace_root", "") or ""
                ),
            )
        )
        state.update(restored_state)
        tool_prompt += "\n\n" + json.dumps(
            {
                "artifact_kind": "ArchitectTheoryPreflightWorkspaceContinuation",
                "checkpoint_id": resume_metadata[
                    "resumed_from_checkpoint_id"
                ],
                "review_material_fingerprint": stable_hash(material),
                "prior_model_visible_tool_observations": state[
                    "workspace_observations"
                ],
                "review_report_draft": {
                    key: state["review_report_draft"].get(key)
                    for key in (
                        "relative_path",
                        "sha256",
                        "byte_size",
                        "version",
                    )
                    if isinstance(state["review_report_draft"], Mapping)
                    and state["review_report_draft"].get(key) is not None
                },
                "remaining_source_searches": (
                    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_SOURCE_SEARCHES
                    - int(state["searches"])
                ),
                "remaining_scratch_runs": (
                    max(0, theory_scratchpad.max_runs - int(state["scratch_runs"]))
                    if theory_scratchpad is not None
                    else 0
                ),
                "continuation_instruction": (
                    "Continue the same independent review from these exact prior "
                    "client-tool observations. They are observations, not accepted "
                    "review conclusions. Re-read only when genuinely needed. When a "
                    "review_report_draft is present, read or edit that exact hash "
                    "instead of regenerating its prose. Use the original tools "
                    "directly, and submit one complete review."
                ),
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
    segment_start_observation_count = len(
        state["workspace_observation_fingerprints"]
    )
    segment_start_counters = {
        field: int(state[field])
        for field in (
            "searches",
            "source_operations",
            "scratch_runs",
            "client_tool_loop_turns",
            "client_tool_loop_tool_calls",
            "client_tool_loop_runtime_executed_tool_calls",
        )
    }

    def record_workspace_observation(
        *,
        tool: str,
        tool_input: Mapping[str, Any],
        content: Any,
        is_error: bool = False,
    ) -> None:
        body = {
            "tool": str(tool),
            "tool_input": deepcopy(dict(tool_input)),
            "content": deepcopy(content),
            "is_error": bool(is_error),
        }
        fingerprint = (
            "theory-preflight-workspace-observation:" + stable_hash(body)[:20]
        )
        if fingerprint in state["workspace_observation_fingerprints"]:
            return
        state["workspace_observation_fingerprints"].add(fingerprint)
        state["workspace_observations"].append(
            {**body, "observation_fingerprint": fingerprint}
        )

    def source_grounding_payload(**loop_metadata: Any) -> dict[str, Any]:
        observations = deepcopy(list(state["observations"]))
        public_search_count = sum(
            row.get("tool") == RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL
            for row in state["workspace_observations"]
            if isinstance(row, Mapping) and row.get("is_error") is not True
        )
        public_read_count = sum(
            row.get("tool") == RESEARCH_SOURCE_DISCOVERY_READ_TOOL
            for row in state["workspace_observations"]
            if isinstance(row, Mapping) and row.get("is_error") is not True
        )
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
            "preflight_public_research_source_discovery": deepcopy(
                public_source_descriptor
            ),
            "preflight_public_research_source_search_count": public_search_count,
            "preflight_public_research_source_read_count": public_read_count,
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
            "workspace_resumed_from_checkpoint_id": str(
                resume_metadata["resumed_from_checkpoint_id"]
            ),
            "workspace_resumed_from_model_checkpoint": bool(
                resume_metadata["resumed_from_model_checkpoint"]
            ),
            "client_tool_session_ref": deepcopy(client_tool_session_ref),
            "resumed_from_client_tool_session_ref": deepcopy(
                resumed_from_client_tool_session_ref
            ),
            "client_tool_session_lineage_continued": bool(
                resumed_from_client_tool_session_ref
            ),
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
            record_workspace_observation(
                tool=call.name,
                tool_input=tool_input,
                content=observation,
            )
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
            record_workspace_observation(
                tool=call.name,
                tool_input=tool_input,
                content=observation,
            )
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
            record_workspace_observation(
                tool=call.name,
                tool_input=tool_input,
                content=execution_result.content,
                is_error=execution_result.is_error,
            )
            return execution_result

        if call.name == RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL:
            if research_source_discovery is None:
                raise ClientToolInputError(
                    "public research source discovery is unavailable"
                )
            if state["searches"] >= (
                ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_SOURCE_SEARCHES
            ):
                raise ClientToolInputError(
                    "preflight source-search budget exhausted"
                )
            if set(tool_input) - {"query", "source_kind", "top_k"}:
                raise ClientToolInputError(
                    "discover_research_sources accepts query, source_kind, and top_k"
                )
            try:
                result = research_source_discovery.search(
                    tool_input.get("query", ""),
                    source_kind=tool_input.get("source_kind", "all"),
                    top_k=tool_input.get("top_k", 5),
                )
            except ResearchSourceDiscoveryInputError as exc:
                raise ClientToolInputError(str(exc)) from exc
            except ResearchSourceDiscoveryError as exc:
                failure = {
                    "ok": False,
                    "error": "public_research_source_discovery_failed",
                    "detail": str(exc)[:1_200],
                    "model_may_continue_without_this_source": True,
                }
                record_workspace_observation(
                    tool=call.name,
                    tool_input=tool_input,
                    content=failure,
                    is_error=True,
                )
                return ClientToolExecutionResult(
                    content=failure,
                    is_error=True,
                    observation_key=(
                        "preflight-public-source-discovery-failed:"
                        + stable_hash([call.name, type(exc).__name__, str(exc)])
                    ),
                )
            if not isinstance(result, Mapping):
                raise RuntimeError(
                    "public research source discovery returned a non-object result"
                )
            state["searches"] += 1
            state["source_operations"] += 1
            model_observation = {
                **dict(result),
                "remaining_searches": (
                    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_SOURCE_SEARCHES
                    - state["searches"]
                ),
                "citation_instruction": (
                    "Search metadata has no source_ref. Read a selected source before "
                    "citing it in a finding."
                ),
            }
            record_workspace_observation(
                tool=call.name,
                tool_input=tool_input,
                content=model_observation,
            )
            return ClientToolExecutionResult(
                content=model_observation,
                state_changed=True,
                observation_key=(
                    "preflight-public-source-search:"
                    + stable_hash(
                        {
                            "query_hash": result.get("query_hash", ""),
                            "source_kind": result.get("source_kind", ""),
                            "results": result.get("results", []),
                        }
                    )
                ),
            )

        if call.name == RESEARCH_SOURCE_DISCOVERY_READ_TOOL:
            if research_source_discovery is None:
                raise ClientToolInputError(
                    "public research source discovery is unavailable"
                )
            if set(tool_input) - {"source_handle", "path", "revision"}:
                raise ClientToolInputError(
                    "read_discovered_research_source accepts source_handle, path, "
                    "and revision"
                )
            try:
                result = research_source_discovery.read(
                    tool_input.get("source_handle", ""),
                    path=tool_input.get("path", ""),
                    revision=tool_input.get("revision", ""),
                )
            except ResearchSourceDiscoveryInputError as exc:
                raise ClientToolInputError(str(exc)) from exc
            except ResearchSourceDiscoveryError as exc:
                failure = {
                    "ok": False,
                    "error": "public_research_source_discovery_failed",
                    "detail": str(exc)[:1_200],
                    "model_may_continue_without_this_source": True,
                }
                record_workspace_observation(
                    tool=call.name,
                    tool_input=tool_input,
                    content=failure,
                    is_error=True,
                )
                return ClientToolExecutionResult(
                    content=failure,
                    is_error=True,
                    observation_key=(
                        "preflight-public-source-read-failed:"
                        + stable_hash([call.name, type(exc).__name__, str(exc)])
                    ),
                )
            if not isinstance(result, Mapping):
                raise RuntimeError(
                    "public research source discovery read returned a non-object result"
                )
            observation, model_observation = (
                _public_research_source_preflight_read_observation(
                    visible=result,
                    descriptor=public_source_descriptor,
                    source_index=int(state["source_operations"]) + 1,
                    exclude_hit_ids=set(state["source_ref_by_hit_id"]),
                    prior_source_refs=state["source_ref_by_hit_id"],
                )
            )
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
            model_observation = {
                "ok": True,
                **model_observation,
                "observation_id": observation_id,
            }
            record_workspace_observation(
                tool=call.name,
                tool_input=tool_input,
                content=model_observation,
            )
            return ClientToolExecutionResult(
                content=model_observation,
                state_changed=True,
                observation_key=observation_id,
            )

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
            model_observation = {
                "ok": True,
                **visible_result,
                "observation_id": observation_id,
                "remaining_searches": (
                    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_SOURCE_SEARCHES
                    - state["searches"]
                ),
            }
            record_workspace_observation(
                tool=call.name,
                tool_input=tool_input,
                content=model_observation,
            )
            return ClientToolExecutionResult(
                content=model_observation,
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
            model_observation = {
                "ok": True,
                **observation,
                "remaining_searches": (
                    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_SOURCE_SEARCHES
                    - state["searches"]
                ),
            }
            record_workspace_observation(
                tool=call.name,
                tool_input=tool_input,
                content=model_observation,
            )
            return ClientToolExecutionResult(
                content=model_observation,
                state_changed=True,
                observation_key=observation_id,
            )

        if call.name == (
            ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WRITE_REPORT_TOOL
        ):
            if set(tool_input) != {"content"}:
                raise ClientToolInputError(
                    "write_theory_preflight_report requires exactly content"
                )
            content = str(tool_input.get("content", "") or "")
            draft, changed = _write_preflight_review_draft(
                content=content,
                material=material,
                prior_draft=state["review_report_draft"],
            )
            state["review_report_draft"] = draft
            observation = {
                "ok": True,
                "written": True,
                "relative_path": draft["relative_path"],
                "sha256": draft["sha256"],
                "byte_size": draft["byte_size"],
                "version": draft["version"],
                "changed": changed,
                "proof_evidence_status": (
                    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_NOT_PROOF_EVIDENCE
                ),
            }
            record_workspace_observation(
                tool=call.name,
                tool_input={
                    "content_sha256": draft["sha256"],
                    "byte_size": draft["byte_size"],
                },
                content=observation,
            )
            return ClientToolExecutionResult(
                content=observation,
                state_changed=changed,
                observation_key=(
                    "theory-preflight-report-write:" + str(draft["sha256"])
                ),
            )

        if call.name == (
            ARCHITECT_THEORY_EXECUTION_PREFLIGHT_EDIT_REPORT_TOOL
        ):
            if set(tool_input) != {
                "expected_sha256",
                "old_text",
                "new_text",
            }:
                raise ClientToolInputError(
                    "edit_theory_preflight_report requires exactly expected_sha256, "
                    "old_text, and new_text"
                )
            draft = state["review_report_draft"]
            if not isinstance(draft, Mapping) or not draft:
                raise ClientToolInputError(
                    "edit_theory_preflight_report requires a current report draft"
                )
            expected_sha256 = str(
                tool_input.get("expected_sha256", "") or ""
            )
            if expected_sha256 != str(draft.get("sha256", "") or ""):
                raise ClientToolInputError(
                    "edit_theory_preflight_report expected_sha256 is stale"
                )
            content = _preflight_review_draft_content(draft, material=material)
            old_text = str(tool_input.get("old_text", "") or "")
            new_text = str(tool_input.get("new_text", "") or "")
            if not old_text:
                raise ClientToolInputError(
                    "edit_theory_preflight_report old_text must be nonempty"
                )
            occurrences = content.count(old_text)
            if occurrences != 1:
                raise ClientToolInputError(
                    "edit_theory_preflight_report old_text must occur exactly once; "
                    f"observed={occurrences}"
                )
            revised = content.replace(old_text, new_text, 1)
            if not revised.strip() or revised == content:
                raise ClientToolInputError(
                    "edit_theory_preflight_report must leave changed nonempty Markdown"
                )
            updated, changed = _write_preflight_review_draft(
                content=revised,
                material=material,
                prior_draft=draft,
            )
            state["review_report_draft"] = updated
            observation = {
                "ok": True,
                "edited": True,
                "relative_path": updated["relative_path"],
                "sha256": updated["sha256"],
                "byte_size": updated["byte_size"],
                "version": updated["version"],
                "proof_evidence_status": (
                    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_NOT_PROOF_EVIDENCE
                ),
            }
            record_workspace_observation(
                tool=call.name,
                tool_input={
                    "expected_sha256": expected_sha256,
                    "old_text_sha256": _preflight_text_sha256(old_text),
                    "new_text_sha256": _preflight_text_sha256(new_text),
                },
                content=observation,
            )
            return ClientToolExecutionResult(
                content=observation,
                state_changed=changed,
                observation_key=(
                    "theory-preflight-report-edit:" + str(updated["sha256"])
                ),
            )

        if call.name == (
            ARCHITECT_THEORY_EXECUTION_PREFLIGHT_READ_REPORT_TOOL
        ):
            if set(tool_input) != {
                "expected_sha256",
                "line_start",
                "line_end",
            }:
                raise ClientToolInputError(
                    "read_theory_preflight_report requires exactly expected_sha256, "
                    "line_start, and line_end"
                )
            draft = state["review_report_draft"]
            if not isinstance(draft, Mapping) or not draft:
                raise ClientToolInputError(
                    "read_theory_preflight_report requires a current report draft"
                )
            expected_sha256 = str(
                tool_input.get("expected_sha256", "") or ""
            )
            if expected_sha256 != str(draft.get("sha256", "") or ""):
                raise ClientToolInputError(
                    "read_theory_preflight_report expected_sha256 is stale"
                )
            content = _preflight_review_draft_content(draft, material=material)
            lines = content.splitlines()
            line_start = tool_input.get("line_start")
            line_end = tool_input.get("line_end")
            if (
                isinstance(line_start, bool)
                or not isinstance(line_start, int)
                or isinstance(line_end, bool)
                or not isinstance(line_end, int)
                or line_start < 1
                or line_end < line_start
                or line_end > len(lines)
            ):
                raise ClientToolInputError(
                    "read_theory_preflight_report line range is invalid; "
                    f"line_count={len(lines)}"
                )
            selected = "\n".join(lines[line_start - 1 : line_end])
            observation = {
                "ok": True,
                "relative_path": draft["relative_path"],
                "sha256": draft["sha256"],
                "line_start": line_start,
                "line_end": line_end,
                "line_count": len(lines),
                "content": selected,
                "content_sha256": _preflight_text_sha256(selected),
                "proof_evidence_status": (
                    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_NOT_PROOF_EVIDENCE
                ),
            }
            record_workspace_observation(
                tool=call.name,
                tool_input=tool_input,
                content={
                    key: value
                    for key, value in observation.items()
                    if key != "content"
                },
            )
            return ClientToolExecutionResult(
                content=observation,
                observation_key=(
                    "theory-preflight-report-read:"
                    + stable_hash(
                        [draft["sha256"], line_start, line_end, selected]
                    )
                ),
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
                record_workspace_observation(
                    tool=call.name,
                    tool_input=tool_input,
                    content=rejection,
                    is_error=True,
                )
                return ClientToolExecutionResult(
                    content=rejection,
                    is_error=True,
                    observation_key="authoritative-theory-document-read-required",
                )
            draft = state["review_report_draft"]
            if not isinstance(draft, Mapping) or not draft:
                raise ClientToolInputError(
                    "submit_theory_preflight_review requires a model-owned Markdown "
                    "report written with write_theory_preflight_report"
                )
            submitted_report_sha256 = str(
                tool_input.get("review_report_sha256", "") or ""
            )
            if submitted_report_sha256 != str(draft.get("sha256", "") or ""):
                raise ClientToolInputError(
                    "submit_theory_preflight_review review_report_sha256 is stale"
                )
            report_content = _preflight_review_draft_content(
                draft,
                material=material,
            )
            materialized_tool_input = dict(tool_input)
            materialized_tool_input.pop("review_report_sha256", None)
            materialized_tool_input["review_report_markdown"] = report_content
            source_grounding = source_grounding_payload()
            packet = normalize_submission(
                materialized_tool_input,
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
                record_workspace_observation(
                    tool=call.name,
                    tool_input={
                        **tool_input,
                        "review_report_sha256": submitted_report_sha256,
                    },
                    content=rejection,
                    is_error=True,
                )
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
                terminal_payload={"review_payload": materialized_tool_input},
                observation_key="preflight-submitted:" + stable_hash(packet),
            )
        raise ClientToolInputError("unsupported preflight client tool")

    request = ClientToolTurnRequest(
        system_prompt=(
            ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SYSTEM_PROMPT
            + "\nThis live review can query task-bound sources and, when configured, "
            "an isolated public-source session. The reviewing model chooses every "
            "query and source. Do not cite search metadata or an external source you "
            "did not read through a client tool."
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
    if isinstance(recovery_checkpoint, Mapping):
        prior_session_ref = recovery_checkpoint.get(
            "client_tool_session_ref", {}
        )
        if isinstance(prior_session_ref, Mapping) and prior_session_ref:
            if not review_workspace_root:
                raise ValueError(
                    "referee client-tool session resume requires a review workspace"
                )
            load_client_tool_session(
                prior_session_ref,
                session_dir=Path(review_workspace_root),
                session_id=review_session_id,
                request=request,
            )
            resumed_from_client_tool_session_ref = deepcopy(dict(prior_session_ref))

    def persist_review_session(
        messages: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        if not review_workspace_root:
            return {}
        return persist_client_tool_session(
            session_dir=Path(review_workspace_root),
            session_id=review_session_id,
            request=request,
            messages=messages,
        )

    try:
        loop = run_bounded_client_tool_loop(
            backend=provider,
            request=request,
            execute_tool=execute_tool,
            max_turns=max_tool_turns,
            max_tool_calls=max_tool_calls,
            max_no_progress_turns=max_no_progress_turns,
        )
    except ClientToolLoopError as exc:
        client_tool_session_ref = persist_review_session(exc.messages)
        cumulative_turns = int(state["client_tool_loop_turns"]) + exc.turns
        cumulative_tool_calls = (
            int(state["client_tool_loop_tool_calls"]) + exc.tool_calls
        )
        cumulative_runtime_tool_calls = (
            int(state["client_tool_loop_runtime_executed_tool_calls"])
            + exc.runtime_executed_tool_calls
        )
        fingerprints = [
            str(row["observation_fingerprint"])
            for row in state["workspace_observations"]
        ]
        checkpoint = seal_architect_theory_preflight_workspace_checkpoint(
            {
                "schema_version": 1,
                "artifact_kind": (
                    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WORKSPACE_CHECKPOINT_KIND
                ),
                "question_id": question.id,
                "review_material_fingerprint": stable_hash(material),
                "source_theory_packet_id": str(
                    material.get("source_theory_packet_id", "") or ""
                ),
                "source_theory_packet_hash": str(
                    material.get("source_theory_packet_hash", "") or ""
                ),
                "review_workspace_root": str(
                    material.get("review_workspace_root", "") or ""
                ),
                "client_tool_session_ref": deepcopy(
                    client_tool_session_ref
                ),
                "review_report_draft": deepcopy(
                    dict(state["review_report_draft"])
                    if isinstance(state["review_report_draft"], Mapping)
                    else {}
                ),
                "resumed_from_checkpoint_id": str(
                    resume_metadata["resumed_from_checkpoint_id"]
                ),
                "searches": int(state["searches"]),
                "source_operations": int(state["source_operations"]),
                "scratch_runs": int(state["scratch_runs"]),
                "client_tool_loop_turns": cumulative_turns,
                "client_tool_loop_tool_calls": cumulative_tool_calls,
                "client_tool_loop_runtime_executed_tool_calls": (
                    cumulative_runtime_tool_calls
                ),
                "segment_start_counters": segment_start_counters,
                "preflight_source_observations": deepcopy(
                    list(state["observations"])
                ),
                "source_ref_by_hit_id": dict(state["source_ref_by_hit_id"]),
                "theory_document_inspection_refs": deepcopy(
                    list(state["document_inspection_refs"])
                ),
                "preflight_scratch_execution_refs": deepcopy(
                    list(state["scratch_execution_refs"])
                ),
                "workspace_observations": deepcopy(
                    list(state["workspace_observations"])
                ),
                "workspace_observation_fingerprints": fingerprints,
                "segment_start_observation_count": (
                    segment_start_observation_count
                ),
                "resumable": len(fingerprints) > segment_start_observation_count,
                "model_owned_workspace_actions": (
                    len(fingerprints) > segment_start_observation_count
                ),
                "independent_reviewer_workspace": True,
                "runtime_selected_review_semantics": False,
                "implementation_authorized": False,
                "accepted": False,
                "kernel_verified": False,
                "proof_evidence_status": (
                    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_NOT_PROOF_EVIDENCE
                ),
                "boundary": (
                    "This content-addressed checkpoint preserves exact observations "
                    "already seen by the independent theory referee. It is not a "
                    "review verdict, implementation authority, empirical evidence, "
                    "formal proof, or kernel evidence."
                ),
            }
        )
        raise PacketValidationError(
            validation_label=(
                "Architect theory-to-execution source-grounded preflight review"
            ),
            attempts=exc.turns,
            errors=[exc.reason],
            history=_preflight_tool_history(exc.history),
            recovery_checkpoint=checkpoint,
        ) from exc

    client_tool_session_ref = persist_review_session(loop.messages)

    terminal = dict(loop.terminal_payload)
    review_payload = terminal.get("review_payload", {})
    if not isinstance(review_payload, Mapping):
        raise PacketValidationError(
            validation_label=(
                "Architect theory-to-execution source-grounded preflight review"
            ),
            attempts=loop.turns,
            errors=["terminal submission did not contain a review payload"],
            history=_preflight_tool_history(loop.history),
        )
    packet = normalize_submission(
        review_payload,
        source_grounding=source_grounding_payload(
            client_tool_loop_turns=(
                int(state["client_tool_loop_turns"]) + loop.turns
            ),
            client_tool_loop_tool_calls=(
                int(state["client_tool_loop_tool_calls"]) + loop.tool_calls
            ),
            client_tool_loop_runtime_executed_tool_calls=(
                int(state["client_tool_loop_runtime_executed_tool_calls"])
                + loop.runtime_executed_tool_calls
            ),
            client_tool_loop_history=_preflight_tool_history(loop.history),
            client_tool_loop_provider_usage=dict(loop.provider_usage),
            client_tool_loop_response_metadata=dict(loop.final_response_metadata),
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
            history=_preflight_tool_history(loop.history),
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
            history=_preflight_tool_history(loop.history),
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
    max_tool_turns: int = ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_TOOL_TURNS,
    max_tool_calls: int = ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_TOOL_CALLS,
    max_no_progress_turns: int = ARCHITECT_THEORY_EXECUTION_PREFLIGHT_MAX_NO_PROGRESS_TURNS,
    prior_finding_ledger: Sequence[Mapping[str, Any]] = (),
    source_retriever: Any = None,
    research_sources: ResearchSourceSnapshot | None = None,
    research_source_discovery: ResearchSourceDiscovery | None = None,
    theory_scratchpad: TheoryScratchpadConfig | None = None,
    recovery_checkpoint: Mapping[str, Any] | None = None,
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
        research_source_discovery=research_source_discovery,
        theory_scratchpad=theory_scratchpad,
        request_model=request_model,
        model_tier=model_tier,
        provider_name=provider_name,
        max_tokens=max_tokens,
        temperature=temperature,
        max_tool_turns=max_tool_turns,
        max_tool_calls=max_tool_calls,
        max_no_progress_turns=max_no_progress_turns,
        recovery_checkpoint=recovery_checkpoint,
    )
