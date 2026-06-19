from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .fingerprint import stable_hash
from .formalization_gap_planner_adapter_registry import (
    ADAPTER_REGISTRY_ROW_SCHEMA_ID,
    validate_adapter_registry_row,
)
from .formalization_gap_planner_ablation_study import validate_ablation_study_row
from .formalization_gap_planner_benchmark import validate_benchmark_route_row
from .formalization_gap_planner_contract import (
    LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
    PORTABLE_FORMALIZATION_GAP_PLAN_ROW_SCHEMA_ID,
    validate_portable_gap_plan_payload,
    validate_portable_gap_plan_row,
)
from .formalization_gap_planner_component_resource_registry import (
    validate_component_resource_contract_row,
    validate_component_resource_registry_component_row,
    validate_component_resource_registry_resource_row,
    validate_component_resource_execution_plan_row,
)
from .formalization_gap_planner_cross_prover_matrix_audit import (
    CROSS_PROVER_MATRIX_AUDIT_ROW_SCHEMA_ID,
    CROSS_PROVER_TARGET_SUMMARY_SCHEMA_ID,
    validate_cross_prover_matrix_audit_row,
    validate_cross_prover_target_summary_payload,
)
from .formalization_gap_planner_evaluation import (
    QUALITY_CONTROL_FIELDS,
    validate_evaluation_row,
)
from .formalization_gap_planner_interactive_session import (
    validate_interactive_decision_policy_row,
    validate_interactive_session_row,
)
from .formalization_gap_planner_minimal_delta_audit import (
    MINIMAL_DELTA_DECISION_ROW_SCHEMA_ID,
    validate_minimal_delta_decision_row,
)
from .formalization_gap_planner_library_coverage_map import (
    LIBRARY_COVERAGE_MAP_ROW_SCHEMA_ID,
    validate_library_coverage_map_row,
)
from .formalization_gap_planner_local_formal_source_adapter import (
    LEGACY_FORMAL_SOURCE_ADAPTER_FIELD_ALIASES,
)
from .formalization_gap_planner_llm_route_planner import (
    FORMAL_GAP_BOUNDARY_MIN_SUPPORT_TOKENS,
    FORMAL_GAP_BOUNDARY_MIN_TWO_TOKEN_SUPPORT_CHARS,
    FORMAL_GAP_BOUNDARY_TEXT_STOPWORDS,
    LLM_ROUTE_PLANNER_LEGACY_RESPONSE_FIELD_ALIASES,
    LLM_ROUTE_PLANNER_LIBRARY_ALIGNMENT_SUMMARY_SCHEMA_ID,
    LLM_ROUTE_PLANNER_MANIFEST_SCHEMA_ID,
    LLM_ROUTE_PLANNER_MODEL_TIER_DECISION_LEDGER_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATOR_COMPONENT,
    LLM_ROUTE_PLANNER_PLANNER_NEXT_ACTION_HOOK_ALIASES,
    LLM_ROUTE_PLANNER_SEARCH_REQUEST_KIND_ALIASES,
    LLM_ROUTE_PLANNER_REQUEST_SCHEMA_ID,
    LLM_ROUTE_PLANNER_MODEL_TIER_POLICY_ID,
    LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_SCHEMA_ID,
    LLM_ROUTE_PLANNER_ROUTE_PLANNING_BRIEF_SCHEMA_ID,
    LLM_ROUTE_PLANNER_ROW_SCHEMA_ID,
    MINIMAL_DELTA_COST_POLICY_ID,
    PROOF_EVIDENCE_STATUS as LLM_ROUTE_PLANNER_PROOF_EVIDENCE_STATUS,
    llm_route_planner_route_planning_brief_json_schema,
    validate_llm_route_planner_request,
    validate_llm_route_planner_manifest,
    validate_llm_route_planner_response_payload_validation_manifest,
    validate_llm_route_planner_response_payload_validation_row,
    validate_llm_route_planner_row,
    _response_resource_request_alignment_errors as _llm_route_planner_resource_request_alignment_errors,
)
from .formalization_gap_planner_route_adoption_blockers import (
    ROUTE_ADOPTION_AWAITING_STATUS,
    ROUTE_ADOPTION_BLOCKER_FORMAL_GAP_BOUNDARIES,
    ROUTE_ADOPTION_BLOCKER_TAXONOMY_ID,
    ROUTE_ADOPTION_BLOCKER_TAXONOMY_MANIFEST_SCHEMA_ID,
    ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID,
    ROUTE_ADOPTION_BLOCKER_VALUES,
    ROUTE_ADOPTION_PENDING_STATUS,
    ROUTE_ADOPTION_READY_STATUS,
    ROUTE_ADOPTION_REJECTED_STATUS,
    route_adoption_blocker_taxonomy_manifest_json_schema,
    validate_route_adoption_blocker_taxonomy_payload,
)
from .formalization_gap_planner_primitive_action_queue import (
    PRIMITIVE_ACTION_QUEUE_ROW_SCHEMA_ID,
    validate_primitive_action_queue_row,
)
from .formalization_gap_planner_action_resource_plan import (
    ACTION_RESOURCE_PLAN_ROW_SCHEMA_ID,
    validate_action_resource_plan_row,
)
from .formalization_gap_planner_resource_request_queue import (
    RESOURCE_REQUEST_QUEUE_ROW_SCHEMA_ID,
    validate_resource_request_queue_row,
)
from .formalization_gap_planner_resource_response_ledger import (
    RESOURCE_RESPONSE_LEDGER_ROW_SCHEMA_ID,
    RESOURCE_RESPONSE_SCHEMA_ID,
    validate_resource_response_ledger_row,
)
from .formalization_gap_planner_portable_plan_audit import (
    PORTABLE_PLAN_AUDIT_ROW_SCHEMA_ID,
    validate_portable_plan_audit_row,
)
from .formalization_gap_planner_refinement_evidence import (
    validate_refinement_evidence_row,
    validate_refinement_tool_response_row,
)
from .formalization_gap_planner_refinement_queue import (
    REFINEMENT_WORK_ITEM_SCHEMA_ID,
    validate_refinement_work_item_row,
)
from .formalization_gap_planner_route_stability_audit import (
    validate_route_stability_audit_row,
)
from .formalization_gap_planner_route_revision_overlay import (
    validate_route_revision_overlay_row,
)
from .formalization_gap_planner_route_replan_handoff import (
    validate_route_replan_handoff_row,
)
from .formalization_gap_planner_route_replan_handoff_audit import (
    validate_route_replan_handoff_audit_row,
)
from .formalization_gap_planner_runtime_handoff_audit import (
    validate_runtime_handoff_audit_row,
)
from .formalization_gap_planner_publication_bundle import (
    FORMALIZATION_GAP_PLANNER_PUBLICATION_BUNDLE_MANIFEST_SCHEMA_ID,
    FORMALIZATION_GAP_PLANNER_SCHEMA_CATALOG_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_LEAN_LEGACY_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_TARGET_PROVER_SCHEMA_ID,
    LLM_MODEL_POLICY_COMPONENT_NAME,
    PUBLICATION_BUNDLE_COMPONENT_NAME,
    SCHEMA_CATALOG_COMPONENT_NAME,
    publication_bundle_manifest_json_schema,
    validate_schema_catalog_payload,
)
from .formalization_gap_planner_proof_state_triage import (
    validate_proof_state_triage_row,
)
from .formalization_gap_planner_prover_adapter_contract import (
    PROVER_ADAPTER_PACKET_SCHEMA_ID,
    PROVER_ADAPTER_RESPONSE_SCHEMA_ID,
    PROVER_ADAPTER_RESPONSE_VALIDATION_ROW_SCHEMA_ID,
    validate_prover_adapter_response_validation_row,
    validate_prover_adapter_packet_row,
)
from .formalization_gap_planner_standalone import (
    FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SEED_ROUTE_SELECTION_SCHEMA_ID,
    FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_ID,
    validate_llm_route_planner_seed_route_selection_payload,
    validate_standalone_input_payload,
)
from .formalization_gap_planner_source_grounding_audit import (
    SOURCE_GROUNDING_ROW_SCHEMA_ID,
    validate_source_grounding_row,
)
from .formalization_gap_planner_target_intake import (
    FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_SCHEMA_ID,
    FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_ROW_SCHEMA_ID,
    LEGACY_TARGET_INTAKE_FIELD_ALIASES,
    normalize_formalization_gap_planner_target_intake,
    validate_target_intake_row,
)
from .model_backend import (
    ANTHROPIC_MODEL_SOURCE_CHECKED_DATE,
    ANTHROPIC_MODEL_IDS_AND_VERSIONING_URL,
    ANTHROPIC_MODEL_ID_VERSIONING_POLICY,
    ANTHROPIC_MODELS_OVERVIEW_URL,
    CLAUDE_FAMILY_MODELS_OUTSIDE_COST_TIERS,
    DEFAULT_CLAUDE_GENERATOR_MODEL_ALIASES_BY_TIER,
    DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
    DEFAULT_CLAUDE_OPUS_GENERATOR_MODEL,
    DEFAULT_CLAUDE_SONNET_GENERATOR_MODEL,
    DEFAULT_LIVE_GENERATOR_PROVIDER,
    PROHIBITED_AGENT_GENERATOR_PROVIDERS,
)


FORMALIZATION_GAP_PLANNER_PUBLICATION_BUNDLE_AUDIT_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_PUBLICATION_BUNDLE_AUDIT_NOT_PROOF_EVIDENCE"
)
PROOF_EVIDENCE_BOUNDARY = (
    "Publication bundle audit rows verify packaging, portability contracts, "
    "and proof-boundary discipline. They are not theorem proof evidence."
)
REQUIRED_CORE_ARTIFACTS = (
    "portable_contract",
    "portable_schema",
    "schema_catalog",
    "schema_catalog_schema",
    "publication_bundle_manifest_schema",
    "portable_plan_row_schema",
    "prover_adapter_packet_schema",
    "prover_adapter_response_schema",
    "prover_adapter_response_validation_row_schema",
    "refinement_work_item_schema",
    "refinement_tool_response_schema",
    "refinement_evidence_row_schema",
    "interactive_session_row_schema",
    "interactive_decision_policy_row_schema",
    "minimal_delta_decision_row_schema",
    "portable_plan_audit_row_schema",
    "library_coverage_map_row_schema",
    "primitive_action_queue_row_schema",
    "action_resource_plan_row_schema",
    "resource_request_queue_row_schema",
    "resource_response_schema",
    "resource_response_ledger_row_schema",
    "source_grounding_row_schema",
    "llm_route_planner_request_schema",
    "llm_route_planner_route_planning_brief_schema",
    "llm_route_planner_response_schema",
    "llm_route_planner_response_payload_schema",
    "llm_route_planner_response_payload_lean_legacy_schema",
    "llm_route_planner_response_payload_target_prover_schema",
    "llm_route_planner_response_payload_validation_manifest_schema",
    "llm_route_planner_response_payload_validation_row_schema",
    "llm_route_planner_manifest_schema",
    "llm_route_planner_row_schema",
    "llm_route_planner_model_tier_decision_ledger_schema",
    "route_adoption_blocker_taxonomy_schema",
    "route_adoption_blocker_taxonomy_manifest_schema",
    "route_adoption_blocker_taxonomy_contract",
    "route_revision_overlay_row_schema",
    "route_stability_audit_row_schema",
    "route_replan_handoff_row_schema",
    "route_replan_handoff_audit_row_schema",
    "runtime_handoff_audit_row_schema",
    "proof_state_triage_row_schema",
    "ablation_study_row_schema",
    "route_alignment_edge_schema",
    "benchmark_route_schema",
    "evaluation_row_schema",
    "adapter_registry_row_schema",
    "cross_prover_matrix_audit_row_schema",
    "cross_prover_target_summary_schema",
    "standalone_input_schema",
    "target_intake_schema",
    "target_intake_row_schema",
    "component_execution_plan_schema",
    "component_resource_resource_row_schema",
    "component_resource_component_row_schema",
    "component_resource_contract_row_schema",
    "benchmark",
    "benchmark_audit",
    "adapter_registry",
    "component_resource_registry",
    "reproduction_manifest",
    "example_inputs",
)
REQUIRED_ADAPTER_IDS = (
    "local_literature_corpus",
    "local_formal_source_index",
    "local_lake_lean",
    "route_revision_overlay",
)
REQUIRED_DOCS = (
    "library_aware_formalization_gap_planner.md",
    "evaluation_benchmark_strategy.md",
)
REQUIRED_REUSE_TARGETS = ("lean4", "rocq", "isabelle", "agda")
REQUIRED_REPRODUCTION_ENTRYPOINTS = (
    "formalization-gap-planner-standalone-plan",
    "formalization-gap-planner-llm-route-planner",
    "formalization-gap-planner-llm-route-planner-response-payload-validate",
    "formalization-gap-planner-portable-plan-audit",
    "formalization-gap-planner-library-coverage-map",
    "formalization-gap-planner-primitive-action-queue",
    "formalization-gap-planner-minimal-delta-audit",
    "formalization-gap-planner-action-resource-plan",
    "formalization-gap-planner-resource-request-queue",
    "formalization-gap-planner-resource-response-ledger",
    "formalization-gap-planner-target-intake",
    "formalization-gap-planner-reuse-smoke",
    "formalization-gap-planner-benchmark-audit",
    "formalization-gap-planner-evaluation",
    "formalization-gap-planner-adapter-registry-audit",
    "formalization-gap-planner-route-adoption-blocker-taxonomy",
    "formalization-gap-planner-ablation-study",
    "formalization-gap-planner-component-resource-registry-audit",
    "formalization-gap-planner-prover-adapter-contract",
    "formalization-gap-planner-refinement-queue",
    "formalization-gap-planner-refinement-adapter-responses",
    "formalization-gap-planner-minimal-delta-audit-feedback",
    "formalization-gap-planner-local-literature-adapter",
    "formalization-gap-planner-local-formal-source-adapter",
    "formalization-gap-planner-local-proof-state-adapter",
    "formalization-gap-planner-prover-adapter-feedback",
    "formalization-gap-planner-refinement-evidence",
    "formalization-gap-planner-route-revision-overlay",
    "formalization-gap-planner-route-stability-audit",
    "formalization-gap-planner-route-replan-handoff",
    "formalization-gap-planner-route-replan-handoff-audit",
    "formalization-gap-planner-runtime-handoff-audit",
    "formalization-gap-planner-proof-state-triage",
    "formalization-gap-planner-interactive-session",
    "formalization-gap-planner-publication-bundle-audit",
)
REQUIRED_REPRODUCTION_COMMANDS = {
    "audit_downloaded_bundle": "formalization-gap-planner-publication-bundle-audit",
    "audit_adapter_registry": "formalization-gap-planner-adapter-registry-audit",
    "audit_benchmark": "formalization-gap-planner-benchmark-audit",
    "audit_component_resource_registry": (
        "formalization-gap-planner-component-resource-registry-audit"
    ),
    "run_evaluation": "formalization-gap-planner-evaluation",
    "run_ablation_study": "formalization-gap-planner-ablation-study",
    "run_standalone_planner": "formalization-gap-planner-standalone-plan",
    "run_llm_route_planner": "formalization-gap-planner-llm-route-planner",
    "validate_llm_route_payloads": (
        "formalization-gap-planner-llm-route-planner-response-payload-validate"
    ),
    "run_target_intake": "formalization-gap-planner-target-intake",
    "export_route_adoption_blocker_taxonomy": (
        "formalization-gap-planner-route-adoption-blocker-taxonomy"
    ),
    "run_reuse_smoke": "formalization-gap-planner-reuse-smoke",
    "run_runtime_handoff_reuse_smoke": "formalization-gap-planner-reuse-smoke",
    "audit_standalone_plan": "formalization-gap-planner-portable-plan-audit",
    "export_library_coverage_map": "formalization-gap-planner-library-coverage-map",
    "export_primitive_action_queue": (
        "formalization-gap-planner-primitive-action-queue"
    ),
    "run_minimal_delta_audit": "formalization-gap-planner-minimal-delta-audit",
    "export_action_resource_plan": "formalization-gap-planner-action-resource-plan",
    "export_resource_request_queue": (
        "formalization-gap-planner-resource-request-queue"
    ),
    "export_resource_response_ledger": (
        "formalization-gap-planner-resource-response-ledger"
    ),
    "export_target_prover_packets": "formalization-gap-planner-prover-adapter-contract",
    "run_refinement_queue": "formalization-gap-planner-refinement-queue",
    "run_refinement_adapter_responses": (
        "formalization-gap-planner-refinement-adapter-responses"
    ),
    "run_minimal_delta_audit_feedback": (
        "formalization-gap-planner-minimal-delta-audit-feedback"
    ),
    "run_local_literature_adapter": "formalization-gap-planner-local-literature-adapter",
    "run_local_formal_source_adapter": (
        "formalization-gap-planner-local-formal-source-adapter"
    ),
    "run_local_proof_state_adapter": (
        "formalization-gap-planner-local-proof-state-adapter"
    ),
    "run_prover_adapter_feedback": (
        "formalization-gap-planner-prover-adapter-feedback"
    ),
    "run_refinement_evidence": "formalization-gap-planner-refinement-evidence",
    "run_route_revision_overlay": "formalization-gap-planner-route-revision-overlay",
    "run_route_stability_audit": "formalization-gap-planner-route-stability-audit",
    "run_route_replan_handoff": "formalization-gap-planner-route-replan-handoff",
    "audit_route_replan_handoff": (
        "formalization-gap-planner-route-replan-handoff-audit"
    ),
    "audit_runtime_handoff": "formalization-gap-planner-runtime-handoff-audit",
    "run_proof_state_triage": "formalization-gap-planner-proof-state-triage",
    "run_interactive_session": "formalization-gap-planner-interactive-session",
    "run_feedback_llm_route_planner": "formalization-gap-planner-llm-route-planner",
    "validate_feedback_llm_route_payloads": (
        "formalization-gap-planner-llm-route-planner-response-payload-validate"
    ),
}
REQUIRED_COMPONENT_RESOURCE_IDS = (
    "target_theorem_intake",
    "literature_grounded_route_synthesis",
    "informal_route_dag_decomposition",
    "formal_library_coverage_mapping",
    "minimal_delta_and_or_planning",
    "prover_feedback_refinement",
    "route_revision_handoff",
    "cross_prover_public_reuse",
)


@dataclass(frozen=True)
class FormalizationGapPlannerPublicationBundleAuditCheck:
    schema_version: int
    check_id: str
    check_name: str
    category: str
    expected: str
    observed: str
    ok: bool
    severity: str
    errors: tuple[str, ...] = ()


def audit_formalization_gap_planner_publication_bundle(
    publication_bundle_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Audit a publication bundle for portable reuse and proof-boundary safety."""

    errors: list[str] = []
    bundle_dir = publication_bundle_dir
    manifest_path = (
        bundle_dir / "formalization_gap_planner_publication_bundle_manifest.json"
    )
    manifest = _read_json(manifest_path, errors)
    checks: list[FormalizationGapPlannerPublicationBundleAuditCheck] = []
    checks.extend(_manifest_checks(bundle_dir, manifest_path, manifest))
    checks.extend(_contract_checks(bundle_dir))
    checks.extend(_benchmark_checks(bundle_dir))
    checks.extend(_benchmark_audit_checks(bundle_dir))
    checks.extend(_adapter_registry_checks(bundle_dir))
    checks.extend(_component_resource_registry_checks(bundle_dir))
    checks.extend(_reproduction_checks(bundle_dir))
    checks.extend(_example_input_checks(bundle_dir))
    checks.extend(_doc_checks(bundle_dir))
    checks.extend(_optional_artifact_checks(bundle_dir, manifest))
    checks.extend(_bundle_boundary_checks(manifest))
    bundle_files = _bundle_files(bundle_dir)
    by_category: dict[str, int] = {}
    for check in checks:
        by_category[check.category] = by_category.get(check.category, 0) + 1
    optional_evaluation_rows = _optional_evaluation_rows_for_summary(bundle_dir)
    optional_realization_missing_selected = (
        _evaluation_realization_missing_selected_from_rows(optional_evaluation_rows)
    )
    optional_realization_missing_delta = (
        _evaluation_realization_missing_delta_from_rows(optional_evaluation_rows)
    )
    optional_realization_cost_hint_baseline = (
        _evaluation_realization_cost_hint_baseline_from_rows(optional_evaluation_rows)
    )
    optional_realization_omitted_cost_hint = (
        _evaluation_realization_omitted_cost_hint_from_rows(optional_evaluation_rows)
    )
    optional_realization_missing_by_route = (
        _evaluation_realization_missing_by_route_from_rows(optional_evaluation_rows)
    )
    optional_evaluation_route_adoption_status_counts = (
        _evaluation_route_adoption_status_counts_from_rows(optional_evaluation_rows)
    )
    optional_evaluation_route_adoption_blockers = (
        _evaluation_route_adoption_blockers_from_rows(optional_evaluation_rows)
    )
    optional_evaluation_route_option_selection_counts = (
        _evaluation_route_option_selection_counts_from_rows(optional_evaluation_rows)
    )
    optional_evaluation_quality_control_fields = (
        _evaluation_quality_control_fields_from_rows(optional_evaluation_rows)
    )
    optional_evaluation_quality_control_resource_contract_ids = (
        _evaluation_quality_control_values_from_rows(
            optional_evaluation_rows,
            "resource_contract_ids",
        )
    )
    optional_evaluation_quality_control_response_validation_signals = (
        _evaluation_quality_control_values_from_rows(
            optional_evaluation_rows,
            "response_validation_signals",
        )
    )
    optional_evaluation_quality_control_stop_conditions = (
        _evaluation_quality_control_values_from_rows(
            optional_evaluation_rows,
            "stop_conditions",
        )
    )
    optional_ablation_study_rows = _optional_ablation_study_rows_for_summary(
        bundle_dir
    )
    optional_ablation_route_adoption_drop_variant = (
        _ablation_study_largest_route_adoption_drop_variant(
            optional_ablation_study_rows
        )
    )
    optional_llm_seed_route_selection_counts = (
        _optional_llm_seed_route_selection_counts(
            bundle_dir,
            artifact_name="formalization_gap_planner_llm_route_planner",
        )
    )
    optional_feedback_llm_seed_route_selection_counts = (
        _optional_llm_seed_route_selection_counts(
            bundle_dir,
            artifact_name="formalization_gap_planner_feedback_llm_route_planner",
        )
    )
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_PUBLICATION_BUNDLE_AUDIT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_publication_bundle_audit",
        "publication_bundle_dir": str(bundle_dir),
        "publication_bundle_manifest": str(manifest_path),
        "bundle_manifest_exists": manifest_path.exists(),
        "bundle_id": str(manifest.get("bundle_id", "")),
        "portable_schema_id": str(manifest.get("portable_schema_id", "")),
        "n_checks": len(checks),
        "n_ok": sum(1 for check in checks if check.ok),
        "n_failed": sum(1 for check in checks if not check.ok),
        "n_error_severity": sum(
            1 for check in checks if not check.ok and check.severity == "error"
        ),
        "n_bundle_llm_route_planner_summary_checked": sum(
            1
            for check in checks
            if check.check_name == "bundle_llm_route_planner_summary_consistent"
        ),
        "n_bundle_llm_route_planner_summary_valid": sum(
            1
            for check in checks
            if check.check_name == "bundle_llm_route_planner_summary_consistent"
            and check.ok
        ),
        "n_bundle_feedback_llm_route_planner_summary_checked": sum(
            1
            for check in checks
            if check.check_name
            == "bundle_feedback_llm_route_planner_summary_consistent"
        ),
        "n_bundle_feedback_llm_route_planner_summary_valid": sum(
            1
            for check in checks
            if check.check_name
            == "bundle_feedback_llm_route_planner_summary_consistent"
            and check.ok
        ),
        "n_bundle_llm_route_planner_response_payload_validation_summary_checked": sum(
            1
            for check in checks
            if check.check_name
            == "bundle_llm_route_planner_response_payload_validation_summary_consistent"
        ),
        "n_bundle_llm_route_planner_response_payload_validation_summary_valid": sum(
            1
            for check in checks
            if check.check_name
            == "bundle_llm_route_planner_response_payload_validation_summary_consistent"
            and check.ok
        ),
        "n_component_execution_plan_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "component_resource_registry_execution_plan_row_"
            )
        ),
        "n_component_execution_plan_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "component_resource_registry_execution_plan_row_"
            )
            and check.ok
        ),
        "n_component_resource_component_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "component_resource_registry_component_row_"
            )
        ),
        "n_component_resource_component_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "component_resource_registry_component_row_"
            )
            and check.ok
        ),
        "n_component_resource_resource_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "component_resource_registry_resource_row_"
            )
        ),
        "n_component_resource_resource_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "component_resource_registry_resource_row_"
            )
            and check.ok
        ),
        "n_component_resource_contract_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "component_resource_registry_contract_row_"
            )
        ),
        "n_component_resource_contract_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "component_resource_registry_contract_row_"
            )
            and check.ok
        ),
        "n_benchmark_route_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("benchmark_route_row_")
        ),
        "n_benchmark_route_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("benchmark_route_row_") and check.ok
        ),
        "n_adapter_registry_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("adapter_registry_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_adapter_registry_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("adapter_registry_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_evaluation_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_evaluation_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_evaluation_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_evaluation_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_evaluation_ground_truth_file_checked": sum(
            1
            for check in checks
            if check.check_name
            in {
                "optional_evaluation_ground_truth_copy",
                "optional_evaluation_ground_truth_parse",
            }
        ),
        "n_optional_evaluation_ground_truth_file_valid": sum(
            1
            for check in checks
            if check.check_name
            in {
                "optional_evaluation_ground_truth_copy",
                "optional_evaluation_ground_truth_parse",
            }
            and check.ok
        ),
        "n_optional_evaluation_ground_truth_match_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_evaluation_row_")
            and check.check_name.endswith("_ground_truth_match")
        ),
        "n_optional_evaluation_ground_truth_match_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_evaluation_row_")
            and check.check_name.endswith("_ground_truth_match")
            and check.ok
        ),
        "n_optional_evaluation_ground_truth_primitive_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_evaluation_row_")
            and check.check_name.endswith("_ground_truth_primitives")
        ),
        "n_optional_evaluation_ground_truth_primitive_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_evaluation_row_")
            and check.check_name.endswith("_ground_truth_primitives")
            and check.ok
        ),
        "n_optional_evaluation_realization_missing_row_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_evaluation_row_")
            and check.check_name.endswith("_realization_missing_fields")
        ),
        "n_optional_evaluation_realization_missing_row_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_evaluation_row_")
            and check.check_name.endswith("_realization_missing_fields")
            and check.ok
        ),
        "n_optional_evaluation_realization_missing_manifest_checked": sum(
            1
            for check in checks
            if check.check_name == "optional_evaluation_realization_missing_manifest"
        ),
        "n_optional_evaluation_realization_missing_manifest_valid": sum(
            1
            for check in checks
            if check.check_name == "optional_evaluation_realization_missing_manifest"
            and check.ok
        ),
        "n_optional_evaluation_route_adoption_row_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_evaluation_row_")
            and check.check_name.endswith("_route_adoption_fields")
        ),
        "n_optional_evaluation_route_adoption_row_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_evaluation_row_")
            and check.check_name.endswith("_route_adoption_fields")
            and check.ok
        ),
        "n_optional_evaluation_route_adoption_manifest_checked": sum(
            1
            for check in checks
            if check.check_name == "optional_evaluation_route_adoption_manifest"
        ),
        "n_optional_evaluation_route_adoption_manifest_valid": sum(
            1
            for check in checks
            if check.check_name == "optional_evaluation_route_adoption_manifest"
            and check.ok
        ),
        "n_optional_evaluation_route_option_selection_manifest_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_evaluation_route_option_selection_manifest"
        ),
        "n_optional_evaluation_route_option_selection_manifest_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_evaluation_route_option_selection_manifest"
            and check.ok
        ),
        "n_optional_evaluation_quality_control_row_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_evaluation_row_")
            and check.check_name.endswith("_quality_control_fields")
        ),
        "n_optional_evaluation_quality_control_row_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_evaluation_row_")
            and check.check_name.endswith("_quality_control_fields")
            and check.ok
        ),
        "n_optional_evaluation_quality_control_manifest_checked": sum(
            1
            for check in checks
            if check.check_name == "optional_evaluation_quality_control_manifest"
        ),
        "n_optional_evaluation_quality_control_manifest_valid": sum(
            1
            for check in checks
            if check.check_name == "optional_evaluation_quality_control_manifest"
            and check.ok
        ),
        "n_optional_evaluation_residual_goal_context_manifest_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_evaluation_residual_goal_context_manifest"
        ),
        "n_optional_evaluation_residual_goal_context_manifest_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_evaluation_residual_goal_context_manifest"
            and check.ok
        ),
        "n_optional_evaluation_rows_with_route_adoption_status": sum(
            1
            for row in optional_evaluation_rows
            if str(row.get("llm_route_planner_route_adoption_status", "")).strip()
        ),
        "optional_evaluation_route_adoption_status_counts": dict(
            optional_evaluation_route_adoption_status_counts
        ),
        "n_optional_evaluation_rows_ready_for_route_adoption": (
            optional_evaluation_route_adoption_status_counts.get(
                "READY_FOR_STANDALONE_REPLAY",
                0,
            )
        ),
        "n_optional_evaluation_rows_pending_refinement_before_route_adoption": (
            optional_evaluation_route_adoption_status_counts.get(
                "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION",
                0,
            )
        ),
        "n_optional_evaluation_route_adoption_blockers": sum(
            len(_str_tuple(row.get("llm_route_planner_route_adoption_blockers", [])))
            for row in optional_evaluation_rows
        ),
        "optional_evaluation_route_adoption_blockers": (
            optional_evaluation_route_adoption_blockers
        ),
        "n_optional_evaluation_rows_with_route_adoption_preconditions": sum(
            1
            for row in optional_evaluation_rows
            if row.get(
                "llm_route_planner_route_adoption_precondition_present"
            )
            is True
        ),
        "n_optional_evaluation_rows_with_blocking_route_adoption_preconditions": sum(
            1
            for row in optional_evaluation_rows
            if row.get(
                "llm_route_planner_route_adoption_precondition_blocked_before_response"
            )
            is True
        ),
        "n_optional_evaluation_route_adoption_precondition_known_blockers": sum(
            len(
                _str_tuple(
                    row.get(
                        "llm_route_planner_route_adoption_precondition_known_blockers",
                        [],
                    )
                )
            )
            for row in optional_evaluation_rows
        ),
        "n_optional_evaluation_route_adoption_precondition_required_response_fields": sum(
            len(
                _str_tuple(
                    row.get(
                        "llm_route_planner_route_adoption_precondition_required_response_fields",
                        [],
                    )
                )
            )
            for row in optional_evaluation_rows
        ),
        "n_optional_evaluation_route_adoption_precondition_target_primitives": sum(
            len(
                _str_tuple(
                    row.get(
                        "llm_route_planner_route_adoption_precondition_target_primitives",
                        [],
                    )
                )
            )
            for row in optional_evaluation_rows
        ),
        "optional_evaluation_route_adoption_precondition_known_blockers": (
            _evaluation_route_adoption_precondition_values_from_rows(
                optional_evaluation_rows,
                "llm_route_planner_route_adoption_precondition_known_blockers",
            )
        ),
        "optional_evaluation_route_adoption_precondition_required_response_fields": (
            _evaluation_route_adoption_precondition_values_from_rows(
                optional_evaluation_rows,
                "llm_route_planner_route_adoption_precondition_required_response_fields",
            )
        ),
        "optional_evaluation_route_adoption_precondition_target_primitives": (
            _evaluation_route_adoption_precondition_values_from_rows(
                optional_evaluation_rows,
                "llm_route_planner_route_adoption_precondition_target_primitives",
            )
        ),
        "n_optional_evaluation_rows_with_route_option_selection_brief": (
            optional_evaluation_route_option_selection_counts[
                "n_rows_with_llm_route_planner_route_option_selection_brief"
            ]
        ),
        "n_optional_evaluation_route_option_selection_candidate_options": (
            optional_evaluation_route_option_selection_counts[
                "n_llm_route_planner_route_option_selection_candidate_options"
            ]
        ),
        "n_optional_evaluation_route_option_selection_candidate_primitives": (
            optional_evaluation_route_option_selection_counts[
                "n_llm_route_planner_route_option_selection_candidate_primitives"
            ]
        ),
        "n_optional_evaluation_route_option_selection_candidates_with_residual_goals": (
            optional_evaluation_route_option_selection_counts[
                "n_llm_route_planner_route_option_selection_candidates_with_residual_goals"
            ]
        ),
        "n_optional_evaluation_route_option_selection_candidate_residual_goals": (
            optional_evaluation_route_option_selection_counts[
                "n_llm_route_planner_route_option_selection_candidate_residual_goals"
            ]
        ),
        "n_optional_evaluation_route_option_selection_lower_bound_residual_goals": (
            optional_evaluation_route_option_selection_counts[
                "n_llm_route_planner_route_option_selection_lower_bound_residual_goals"
            ]
        ),
        "n_optional_evaluation_rows_with_route_option_selected_route_option": (
            optional_evaluation_route_option_selection_counts[
                "n_rows_with_llm_route_planner_route_option_selected_route_option"
            ]
        ),
        "n_optional_evaluation_route_option_selection_minimal_delta_selected_residual_goals": (
            optional_evaluation_route_option_selection_counts[
                "n_llm_route_planner_route_option_selection_minimal_delta_selected_residual_goals"
            ]
        ),
        "n_optional_evaluation_route_option_selection_lower_bound_matches_minimal_delta": (
            optional_evaluation_route_option_selection_counts[
                "n_llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta"
            ]
        ),
        "n_optional_evaluation_route_option_selection_lower_bound_mismatches_minimal_delta": (
            optional_evaluation_route_option_selection_counts[
                "n_llm_route_planner_route_option_selection_lower_bound_mismatches_minimal_delta"
            ]
        ),
        "n_optional_evaluation_route_option_selected_matches_lower_bound": (
            optional_evaluation_route_option_selection_counts[
                "n_llm_route_planner_route_option_selected_matches_lower_bound"
            ]
        ),
        "n_optional_evaluation_route_option_selected_mismatches_lower_bound": (
            optional_evaluation_route_option_selection_counts[
                "n_llm_route_planner_route_option_selected_mismatches_lower_bound"
            ]
        ),
        "n_optional_evaluation_route_option_selected_matches_minimal_delta": (
            optional_evaluation_route_option_selection_counts[
                "n_llm_route_planner_route_option_selected_matches_minimal_delta"
            ]
        ),
        "n_optional_evaluation_route_option_selected_mismatches_minimal_delta": (
            optional_evaluation_route_option_selection_counts[
                "n_llm_route_planner_route_option_selected_mismatches_minimal_delta"
            ]
        ),
        "n_optional_evaluation_rows_with_quality_controls": sum(
            1
            for row in optional_evaluation_rows
            if _quality_controls_from_evaluation_row(row)
        ),
        "n_optional_evaluation_quality_control_fields": sum(
            len(_quality_controls_from_evaluation_row(row))
            for row in optional_evaluation_rows
        ),
        "optional_evaluation_quality_control_fields": (
            optional_evaluation_quality_control_fields
        ),
        "optional_evaluation_quality_control_resource_contract_ids": (
            optional_evaluation_quality_control_resource_contract_ids
        ),
        "optional_evaluation_quality_control_response_validation_signals": (
            optional_evaluation_quality_control_response_validation_signals
        ),
        "optional_evaluation_quality_control_stop_conditions": (
            optional_evaluation_quality_control_stop_conditions
        ),
        "n_optional_evaluation_realization_missing_selected_formal_primitives": sum(
            len(_str_tuple(row.get("realization_missing_selected_formal_primitives", [])))
            for row in optional_evaluation_rows
        ),
        "optional_evaluation_realization_missing_selected_formal_primitives": (
            optional_realization_missing_selected
        ),
        "n_optional_evaluation_realization_missing_delta_alignment_primitives": sum(
            len(_str_tuple(row.get("realization_missing_delta_alignment_primitives", [])))
            for row in optional_evaluation_rows
        ),
        "optional_evaluation_realization_missing_delta_alignment_primitives": (
            optional_realization_missing_delta
        ),
        "n_optional_evaluation_rows_with_incomplete_cost_hint_baseline_coverage": sum(
            1
            for row in optional_evaluation_rows
            if row.get("realization_cost_hint_baseline_coverage_complete") is False
        ),
        "n_optional_evaluation_realization_cost_hint_baseline_primitives": sum(
            len(_str_tuple(row.get("realization_cost_hint_baseline_primitives", [])))
            for row in optional_evaluation_rows
        ),
        "optional_evaluation_realization_cost_hint_baseline_primitives": (
            optional_realization_cost_hint_baseline
        ),
        "n_optional_evaluation_realization_omitted_cost_hint_primitives": sum(
            len(_str_tuple(row.get("realization_omitted_cost_hint_primitives", [])))
            for row in optional_evaluation_rows
        ),
        "optional_evaluation_realization_omitted_cost_hint_primitives": (
            optional_realization_omitted_cost_hint
        ),
        "optional_evaluation_realization_missing_primitives_by_route": (
            optional_realization_missing_by_route
        ),
        "n_optional_interactive_decision_policy_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_interactive_decision_policy_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_interactive_decision_policy_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_interactive_decision_policy_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_interactive_decision_policy_link_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_interactive_decision_policy_row_")
            and (
                check.check_name.endswith("_component_links")
                or check.check_name.endswith("_resource_links")
                or check.check_name.endswith("_resource_contract_links")
                or check.check_name.endswith("_resource_contract_coverage")
            )
        ),
        "n_optional_interactive_decision_policy_link_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_interactive_decision_policy_row_")
            and (
                check.check_name.endswith("_component_links")
                or check.check_name.endswith("_resource_links")
                or check.check_name.endswith("_resource_contract_links")
                or check.check_name.endswith("_resource_contract_coverage")
            )
            and check.ok
        ),
        "n_optional_interactive_session_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_interactive_session_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_interactive_session_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_interactive_session_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_interactive_session_resource_response_status_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_interactive_session_row_")
            and check.check_name.endswith("_resource_response_status_consistency")
        ),
        "n_optional_interactive_session_resource_response_status_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_interactive_session_row_")
            and check.check_name.endswith("_resource_response_status_consistency")
            and check.ok
        ),
        "n_optional_interactive_session_generic_prover_fields_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_interactive_session_row_")
            and check.check_name.endswith("_generic_prover_fields")
        ),
        "n_optional_interactive_session_generic_prover_fields_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_interactive_session_row_")
            and check.check_name.endswith("_generic_prover_fields")
            and check.ok
        ),
        "n_optional_interactive_session_formal_attempt_queue_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_interactive_session_row_")
            and check.check_name.endswith("_formal_attempt_queue_consistency")
        ),
        "n_optional_interactive_session_formal_attempt_queue_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_interactive_session_row_")
            and check.check_name.endswith("_formal_attempt_queue_consistency")
            and check.ok
        ),
        "n_optional_interactive_session_route_precondition_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_interactive_session_row_")
            and check.check_name.endswith("_route_precondition_consistency")
        ),
        "n_optional_interactive_session_route_precondition_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_interactive_session_row_")
            and check.check_name.endswith("_route_precondition_consistency")
            and check.ok
        ),
        "n_optional_refinement_evidence_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_refinement_evidence_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_refinement_evidence_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_refinement_evidence_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_refinement_adapter_response_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_refinement_adapter_response_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_refinement_adapter_response_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_refinement_adapter_response_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_minimal_delta_audit_feedback_response_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "optional_minimal_delta_audit_feedback_response_"
            )
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_minimal_delta_audit_feedback_response_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "optional_minimal_delta_audit_feedback_response_"
            )
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_prover_adapter_feedback_response_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "optional_prover_adapter_feedback_response_"
            )
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_prover_adapter_feedback_response_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "optional_prover_adapter_feedback_response_"
            )
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_refinement_work_item_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_refinement_work_item_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_refinement_work_item_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_refinement_work_item_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_minimal_delta_decision_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_minimal_delta_decision_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_minimal_delta_decision_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_minimal_delta_decision_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_goal_plan_row_contract_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_goal_plan_row_")
            and check.check_name.endswith("_contract_valid")
        ),
        "n_optional_goal_plan_row_contract_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_goal_plan_row_")
            and check.check_name.endswith("_contract_valid")
            and check.ok
        ),
        "n_optional_goal_plan_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_goal_plan_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_goal_plan_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_goal_plan_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_source_grounding_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_source_grounding_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_source_grounding_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_source_grounding_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_target_intake_row_contract_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_target_intake_row_")
            and check.check_name.endswith("_contract_valid")
        ),
        "n_optional_target_intake_row_contract_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_target_intake_row_")
            and check.check_name.endswith("_contract_valid")
            and check.ok
        ),
        "n_optional_target_intake_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_target_intake_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_target_intake_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_target_intake_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_llm_route_planner_request_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_request_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_llm_route_planner_request_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_request_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_llm_route_planner_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_llm_route_planner_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_llm_route_planner_realization_witness_schema_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_realization_coverage_witness_schema"
        ),
        "n_optional_llm_route_planner_realization_witness_schema_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_realization_coverage_witness_schema"
            and check.ok
        ),
        "n_optional_llm_route_planner_seed_provenance_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_seed_provenance")
        ),
        "n_optional_llm_route_planner_seed_provenance_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_seed_provenance")
            and check.ok
        ),
        "n_optional_llm_route_planner_seed_model_provenance_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_seed_model_provenance")
        ),
        "n_optional_llm_route_planner_seed_model_provenance_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_seed_model_provenance")
            and check.ok
        ),
        "n_optional_llm_route_planner_seed_source_grounding_provenance_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_seed_source_grounding_provenance")
        ),
        "n_optional_llm_route_planner_seed_source_grounding_provenance_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_seed_source_grounding_provenance")
            and check.ok
        ),
        "n_optional_llm_route_planner_seed_realization_witness_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_seed_realization_witness_preservation")
        ),
        "n_optional_llm_route_planner_seed_realization_witness_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_seed_realization_witness_preservation")
            and check.ok
        ),
        "n_optional_llm_route_planner_seed_alignment_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_seed_alignment_preservation")
        ),
        "n_optional_llm_route_planner_seed_alignment_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_seed_alignment_preservation")
            and check.ok
        ),
        "n_optional_llm_route_planner_seed_dag_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_seed_dag_preservation")
        ),
        "n_optional_llm_route_planner_seed_dag_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_seed_dag_preservation")
            and check.ok
        ),
        "n_optional_llm_route_planner_seed_search_handoff_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_seed_search_handoff")
        ),
        "n_optional_llm_route_planner_seed_search_handoff_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_seed_search_handoff")
            and check.ok
        ),
        "n_optional_llm_route_planner_seed_route_adoption_readiness_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_seed_route_adoption_readiness")
        ),
        "n_optional_llm_route_planner_seed_route_adoption_readiness_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_seed_route_adoption_readiness")
            and check.ok
        ),
        "n_optional_llm_route_planner_seed_route_selection_summary_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_seed_route_selection_summary"
        ),
        "n_optional_llm_route_planner_seed_route_selection_summary_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_seed_route_selection_summary"
            and check.ok
        ),
        "n_optional_llm_route_planner_seed_route_selection_contract_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_seed_route_selection_contract"
        ),
        "n_optional_llm_route_planner_seed_route_selection_contract_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_seed_route_selection_contract"
            and check.ok
        ),
        "n_optional_llm_route_planner_seed_route_selection_schema_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_seed_route_selection_schema_id"
        ),
        "n_optional_llm_route_planner_seed_route_selection_schema_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_seed_route_selection_schema_id"
            and check.ok
        ),
        "n_optional_llm_route_planner_seed_route_selection_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_seed_route_selection")
        ),
        "n_optional_llm_route_planner_seed_route_selection_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_seed_route_selection")
            and check.ok
        ),
        "n_optional_llm_route_planner_seed_route_selection_candidates": optional_llm_seed_route_selection_counts[
            "n_route_candidates"
        ],
        "n_optional_llm_route_planner_seed_route_selection_adoptable_candidates": optional_llm_seed_route_selection_counts[
            "n_adoptable_route_candidates"
        ],
        "n_optional_llm_route_planner_seed_route_selection_selected_adoptable": optional_llm_seed_route_selection_counts[
            "n_selected_route_adoptable_for_standalone_replay"
        ],
        "n_optional_llm_route_planner_seed_route_selection_selected_not_adoptable": optional_llm_seed_route_selection_counts[
            "n_selected_route_candidates_not_adoptable"
        ],
        "n_optional_llm_route_planner_generic_formal_dag_checked": sum(
            1
            for check in checks
            if check.check_name == "optional_llm_route_planner_generic_formal_dag_fields"
        ),
        "n_optional_llm_route_planner_generic_formal_dag_valid": sum(
            1
            for check in checks
            if check.check_name == "optional_llm_route_planner_generic_formal_dag_fields"
            and check.ok
        ),
        "n_optional_llm_route_planner_request_evidence_bound_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_request_evidence_bound")
        ),
        "n_optional_llm_route_planner_request_evidence_bound_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_row_")
            and check.check_name.endswith("_request_evidence_bound")
            and check.ok
        ),
        "n_optional_llm_route_planner_request_registry_context_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_request_")
            and check.check_name.endswith("_registry_context")
        ),
        "n_optional_llm_route_planner_request_registry_context_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_request_")
            and check.check_name.endswith("_registry_context")
            and check.ok
        ),
        "n_optional_llm_route_planner_request_target_intake_context_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_request_")
            and check.check_name.endswith("_target_intake_context")
        ),
        "n_optional_llm_route_planner_request_target_intake_context_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_request_")
            and check.check_name.endswith("_target_intake_context")
            and check.ok
        ),
        "n_optional_llm_route_planner_request_generation_policy_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_request_")
            and check.check_name.endswith("_generation_policy")
        ),
        "n_optional_llm_route_planner_request_generation_policy_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_llm_route_planner_request_")
            and check.check_name.endswith("_generation_policy")
            and check.ok
        ),
        "n_optional_llm_route_planner_request_model_tier_mismatch_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_request_model_tier_mismatch_policy"
        ),
        "n_optional_llm_route_planner_request_model_tier_mismatch_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_request_model_tier_mismatch_policy"
            and check.ok
        ),
        "n_optional_llm_route_planner_generation_preflight_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_generation_preflight_policy"
        ),
        "n_optional_llm_route_planner_generation_preflight_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_generation_preflight_policy"
            and check.ok
        ),
        "n_optional_llm_route_planner_library_alignment_route_option_aggregate_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_library_alignment_route_option_aggregates"
        ),
        "n_optional_llm_route_planner_library_alignment_route_option_aggregate_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_library_alignment_route_option_aggregates"
            and check.ok
        ),
        "n_optional_llm_route_planner_route_adoption_blocker_summary_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_route_adoption_blocker_summary"
        ),
        "n_optional_llm_route_planner_route_adoption_blocker_summary_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_route_adoption_blocker_summary"
            and check.ok
        ),
        "n_optional_llm_route_planner_response_payload_validation_manifest_contract_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_response_payload_validation_manifest_schema_valid"
        ),
        "n_optional_llm_route_planner_response_payload_validation_manifest_contract_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_response_payload_validation_manifest_schema_valid"
            and check.ok
        ),
        "n_optional_llm_route_planner_response_payload_validation_count_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_response_payload_validation_count_consistency"
        ),
        "n_optional_llm_route_planner_response_payload_validation_count_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_response_payload_validation_count_consistency"
            and check.ok
        ),
        "n_optional_llm_route_planner_response_payload_validation_request_bound_accounting_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_response_payload_validation_request_bound_accounting"
        ),
        "n_optional_llm_route_planner_response_payload_validation_request_bound_accounting_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_response_payload_validation_request_bound_accounting"
            and check.ok
        ),
        "n_optional_llm_route_planner_response_payload_validation_request_bound_coverage_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_response_payload_validation_request_bound_coverage"
        ),
        "n_optional_llm_route_planner_response_payload_validation_request_bound_coverage_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_response_payload_validation_request_bound_coverage"
            and check.ok
        ),
        "n_optional_llm_route_planner_response_payload_validation_route_precondition_accounting_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_response_payload_validation_route_precondition_accounting"
        ),
        "n_optional_llm_route_planner_response_payload_validation_route_precondition_accounting_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_llm_route_planner_response_payload_validation_route_precondition_accounting"
            and check.ok
        ),
        "n_optional_llm_route_planner_response_payload_validation_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "optional_llm_route_planner_response_payload_validation_row_"
            )
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_llm_route_planner_response_payload_validation_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "optional_llm_route_planner_response_payload_validation_row_"
            )
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_request_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_request_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_feedback_llm_route_planner_request_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_request_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_feedback_llm_route_planner_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_realization_witness_schema_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_feedback_llm_route_planner_realization_coverage_witness_schema"
        ),
        "n_optional_feedback_llm_route_planner_realization_witness_schema_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_feedback_llm_route_planner_realization_coverage_witness_schema"
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_seed_provenance_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_row_")
            and check.check_name.endswith("_seed_provenance")
        ),
        "n_optional_feedback_llm_route_planner_seed_provenance_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_row_")
            and check.check_name.endswith("_seed_provenance")
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_seed_model_provenance_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_row_")
            and check.check_name.endswith("_seed_model_provenance")
        ),
        "n_optional_feedback_llm_route_planner_seed_model_provenance_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_row_")
            and check.check_name.endswith("_seed_model_provenance")
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_seed_source_grounding_provenance_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_row_")
            and check.check_name.endswith("_seed_source_grounding_provenance")
        ),
        "n_optional_feedback_llm_route_planner_seed_source_grounding_provenance_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_row_")
            and check.check_name.endswith("_seed_source_grounding_provenance")
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_seed_realization_witness_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_row_")
            and check.check_name.endswith("_seed_realization_witness_preservation")
        ),
        "n_optional_feedback_llm_route_planner_seed_realization_witness_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_row_")
            and check.check_name.endswith("_seed_realization_witness_preservation")
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_seed_alignment_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_row_")
            and check.check_name.endswith("_seed_alignment_preservation")
        ),
        "n_optional_feedback_llm_route_planner_seed_alignment_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_row_")
            and check.check_name.endswith("_seed_alignment_preservation")
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_seed_dag_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_row_")
            and check.check_name.endswith("_seed_dag_preservation")
        ),
        "n_optional_feedback_llm_route_planner_seed_dag_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_row_")
            and check.check_name.endswith("_seed_dag_preservation")
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_seed_search_handoff_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_row_")
            and check.check_name.endswith("_seed_search_handoff")
        ),
        "n_optional_feedback_llm_route_planner_seed_search_handoff_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_row_")
            and check.check_name.endswith("_seed_search_handoff")
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_seed_route_adoption_readiness_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_row_")
            and check.check_name.endswith("_seed_route_adoption_readiness")
        ),
        "n_optional_feedback_llm_route_planner_seed_route_adoption_readiness_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_row_")
            and check.check_name.endswith("_seed_route_adoption_readiness")
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_seed_route_selection_summary_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_feedback_llm_route_planner_seed_route_selection_summary"
        ),
        "n_optional_feedback_llm_route_planner_seed_route_selection_summary_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_feedback_llm_route_planner_seed_route_selection_summary"
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_seed_route_selection_contract_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_feedback_llm_route_planner_seed_route_selection_contract"
        ),
        "n_optional_feedback_llm_route_planner_seed_route_selection_contract_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_feedback_llm_route_planner_seed_route_selection_contract"
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_seed_route_selection_schema_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_feedback_llm_route_planner_seed_route_selection_schema_id"
        ),
        "n_optional_feedback_llm_route_planner_seed_route_selection_schema_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_feedback_llm_route_planner_seed_route_selection_schema_id"
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_seed_route_selection_checked": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "optional_feedback_llm_route_planner_row_"
            )
            and check.check_name.endswith("_seed_route_selection")
        ),
        "n_optional_feedback_llm_route_planner_seed_route_selection_valid": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "optional_feedback_llm_route_planner_row_"
            )
            and check.check_name.endswith("_seed_route_selection")
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_seed_route_selection_candidates": optional_feedback_llm_seed_route_selection_counts[
            "n_route_candidates"
        ],
        "n_optional_feedback_llm_route_planner_seed_route_selection_adoptable_candidates": optional_feedback_llm_seed_route_selection_counts[
            "n_adoptable_route_candidates"
        ],
        "n_optional_feedback_llm_route_planner_seed_route_selection_selected_adoptable": optional_feedback_llm_seed_route_selection_counts[
            "n_selected_route_adoptable_for_standalone_replay"
        ],
        "n_optional_feedback_llm_route_planner_seed_route_selection_selected_not_adoptable": optional_feedback_llm_seed_route_selection_counts[
            "n_selected_route_candidates_not_adoptable"
        ],
        "n_optional_feedback_llm_route_planner_generic_formal_dag_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_feedback_llm_route_planner_generic_formal_dag_fields"
        ),
        "n_optional_feedback_llm_route_planner_generic_formal_dag_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_feedback_llm_route_planner_generic_formal_dag_fields"
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_request_evidence_bound_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_row_")
            and check.check_name.endswith("_request_evidence_bound")
        ),
        "n_optional_feedback_llm_route_planner_request_evidence_bound_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_row_")
            and check.check_name.endswith("_request_evidence_bound")
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_request_registry_context_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_request_")
            and check.check_name.endswith("_registry_context")
        ),
        "n_optional_feedback_llm_route_planner_request_registry_context_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_request_")
            and check.check_name.endswith("_registry_context")
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_request_target_intake_context_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_request_")
            and check.check_name.endswith("_target_intake_context")
        ),
        "n_optional_feedback_llm_route_planner_request_target_intake_context_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_request_")
            and check.check_name.endswith("_target_intake_context")
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_request_generation_policy_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_request_")
            and check.check_name.endswith("_generation_policy")
        ),
        "n_optional_feedback_llm_route_planner_request_generation_policy_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_feedback_llm_route_planner_request_")
            and check.check_name.endswith("_generation_policy")
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_request_model_tier_mismatch_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_feedback_llm_route_planner_request_model_tier_mismatch_policy"
        ),
        "n_optional_feedback_llm_route_planner_request_model_tier_mismatch_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_feedback_llm_route_planner_request_model_tier_mismatch_policy"
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_generation_preflight_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_feedback_llm_route_planner_generation_preflight_policy"
        ),
        "n_optional_feedback_llm_route_planner_generation_preflight_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_feedback_llm_route_planner_generation_preflight_policy"
            and check.ok
        ),
        "n_optional_feedback_llm_route_planner_route_adoption_blocker_summary_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_feedback_llm_route_planner_route_adoption_blocker_summary"
        ),
        "n_optional_feedback_llm_route_planner_route_adoption_blocker_summary_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_feedback_llm_route_planner_route_adoption_blocker_summary"
            and check.ok
        ),
        "n_optional_adapter_registry_audit_check_contract_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_adapter_registry_audit_check_")
            and check.check_name.endswith("_contract_valid")
        ),
        "n_optional_adapter_registry_audit_check_contract_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_adapter_registry_audit_check_")
            and check.check_name.endswith("_contract_valid")
            and check.ok
        ),
        "n_optional_component_resource_registry_audit_check_contract_checked": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "optional_component_resource_registry_audit_check_"
            )
            and check.check_name.endswith("_contract_valid")
        ),
        "n_optional_component_resource_registry_audit_check_contract_valid": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "optional_component_resource_registry_audit_check_"
            )
            and check.check_name.endswith("_contract_valid")
            and check.ok
        ),
        "n_optional_local_adapter_response_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_local_adapter_response_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_local_adapter_response_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_local_adapter_response_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_local_formal_source_alias_contract_checked": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "optional_local_formal_source_adapter_legacy_alias_"
            )
        ),
        "n_optional_local_formal_source_alias_contract_valid": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "optional_local_formal_source_adapter_legacy_alias_"
            )
            and check.ok
        ),
        "n_optional_proof_state_triage_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_proof_state_triage_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_proof_state_triage_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_proof_state_triage_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_proof_state_triage_generic_prover_fields_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_proof_state_triage_row_")
            and check.check_name.endswith("_generic_prover_fields")
        ),
        "n_optional_proof_state_triage_generic_prover_fields_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_proof_state_triage_row_")
            and check.check_name.endswith("_generic_prover_fields")
            and check.ok
        ),
        "n_optional_route_stability_audit_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_stability_audit_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_route_stability_audit_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_stability_audit_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_route_stability_resource_response_status_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_stability_audit_row_")
            and check.check_name.endswith("_resource_response_status_consistency")
        ),
        "n_optional_route_stability_resource_response_status_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_stability_audit_row_")
            and check.check_name.endswith("_resource_response_status_consistency")
            and check.ok
        ),
        "n_optional_route_stability_generic_prover_fields_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_stability_audit_row_")
            and check.check_name.endswith("_generic_prover_fields")
        ),
        "n_optional_route_stability_generic_prover_fields_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_stability_audit_row_")
            and check.check_name.endswith("_generic_prover_fields")
            and check.ok
        ),
        "n_optional_route_revision_overlay_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_revision_overlay_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_route_revision_overlay_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_revision_overlay_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_route_revision_resource_response_evidence_ref_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_revision_overlay_row_")
            and check.check_name.endswith("_resource_response_evidence_refs")
        ),
        "n_optional_route_revision_resource_response_evidence_ref_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_revision_overlay_row_")
            and check.check_name.endswith("_resource_response_evidence_refs")
            and check.ok
        ),
        "n_optional_route_revision_resource_response_trace_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_revision_overlay_row_")
            and check.check_name.endswith("_resource_response_traces")
        ),
        "n_optional_route_revision_resource_response_trace_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_revision_overlay_row_")
            and check.check_name.endswith("_resource_response_traces")
            and check.ok
        ),
        "n_optional_route_revision_resource_response_status_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_revision_overlay_row_")
            and check.check_name.endswith("_resource_response_status_summary")
        ),
        "n_optional_route_revision_resource_response_status_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_revision_overlay_row_")
            and check.check_name.endswith("_resource_response_status_summary")
            and check.ok
        ),
        "n_optional_route_revision_generic_formal_dag_checked": sum(
            1
            for check in checks
            if check.check_name == "optional_route_revision_overlay_generic_formal_dag_fields"
        ),
        "n_optional_route_revision_generic_formal_dag_valid": sum(
            1
            for check in checks
            if check.check_name == "optional_route_revision_overlay_generic_formal_dag_fields"
            and check.ok
        ),
        "n_optional_route_replan_handoff_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_replan_handoff_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_route_replan_handoff_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_replan_handoff_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_route_replan_handoff_seed_alignment_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_replan_handoff_row_")
            and check.check_name.endswith("_seed_alignment_preservation")
        ),
        "n_optional_route_replan_handoff_seed_alignment_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_replan_handoff_row_")
            and check.check_name.endswith("_seed_alignment_preservation")
            and check.ok
        ),
        "n_optional_route_replan_handoff_seed_dag_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_replan_handoff_row_")
            and check.check_name.endswith("_seed_dag_preservation")
        ),
        "n_optional_route_replan_handoff_seed_dag_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_replan_handoff_row_")
            and check.check_name.endswith("_seed_dag_preservation")
            and check.ok
        ),
        "n_optional_route_replan_handoff_seed_target_context_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_replan_handoff_row_")
            and check.check_name.endswith("_seed_target_context_preservation")
        ),
        "n_optional_route_replan_handoff_seed_target_context_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_replan_handoff_row_")
            and check.check_name.endswith("_seed_target_context_preservation")
            and check.ok
        ),
        "n_optional_route_replan_handoff_seed_target_context_summary_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_replan_handoff_row_")
            and check.check_name.endswith("_seed_target_context_summary_preservation")
        ),
        "n_optional_route_replan_handoff_seed_target_context_summary_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_replan_handoff_row_")
            and check.check_name.endswith("_seed_target_context_summary_preservation")
            and check.ok
        ),
        "n_optional_route_replan_handoff_seed_route_planning_brief_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_replan_handoff_row_")
            and check.check_name.endswith("_seed_route_planning_brief_preservation")
        ),
        "n_optional_route_replan_handoff_seed_route_planning_brief_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_replan_handoff_row_")
            and check.check_name.endswith("_seed_route_planning_brief_preservation")
            and check.ok
        ),
        "n_optional_route_replan_handoff_seed_route_option_selection_brief_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_replan_handoff_row_")
            and check.check_name.endswith(
                "_seed_route_option_selection_brief_preservation"
            )
        ),
        "n_optional_route_replan_handoff_seed_route_option_selection_brief_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_replan_handoff_row_")
            and check.check_name.endswith(
                "_seed_route_option_selection_brief_preservation"
            )
            and check.ok
        ),
        "n_optional_route_replan_handoff_seed_primitive_evidence_matrix_witness_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_replan_handoff_row_")
            and check.check_name.endswith(
                "_seed_primitive_evidence_matrix_witness_preservation"
            )
        ),
        "n_optional_route_replan_handoff_seed_primitive_evidence_matrix_witness_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_replan_handoff_row_")
            and check.check_name.endswith(
                "_seed_primitive_evidence_matrix_witness_preservation"
            )
            and check.ok
        ),
        "n_optional_route_replan_handoff_seed_route_adoption_preconditions_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_replan_handoff_row_")
            and check.check_name.endswith(
                "_seed_route_adoption_preconditions_preservation"
            )
        ),
        "n_optional_route_replan_handoff_seed_route_adoption_preconditions_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_replan_handoff_row_")
            and check.check_name.endswith(
                "_seed_route_adoption_preconditions_preservation"
            )
            and check.ok
        ),
        "n_optional_route_replan_handoff_generic_formal_dag_checked": sum(
            1
            for check in checks
            if check.check_name == "optional_route_replan_handoff_generic_formal_dag_fields"
        ),
        "n_optional_route_replan_handoff_generic_formal_dag_valid": sum(
            1
            for check in checks
            if check.check_name == "optional_route_replan_handoff_generic_formal_dag_fields"
            and check.ok
        ),
        "n_optional_route_replan_handoff_audit_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_replan_handoff_audit_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_route_replan_handoff_audit_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_route_replan_handoff_audit_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_route_replan_handoff_audit_roundtrip_route_planning_brief_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_route_replan_handoff_audit_roundtrip_route_planning_brief_trace"
        ),
        "n_optional_route_replan_handoff_audit_roundtrip_route_planning_brief_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_route_replan_handoff_audit_roundtrip_route_planning_brief_trace"
            and check.ok
        ),
        "n_optional_route_replan_handoff_audit_roundtrip_target_context_summary_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_route_replan_handoff_audit_roundtrip_target_context_summary_trace"
        ),
        "n_optional_route_replan_handoff_audit_roundtrip_target_context_summary_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_route_replan_handoff_audit_roundtrip_target_context_summary_trace"
            and check.ok
        ),
        "n_optional_route_replan_handoff_audit_roundtrip_route_option_selection_brief_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_route_replan_handoff_audit_roundtrip_route_option_selection_brief_trace"
        ),
        "n_optional_route_replan_handoff_audit_roundtrip_route_option_selection_brief_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_route_replan_handoff_audit_roundtrip_route_option_selection_brief_trace"
            and check.ok
        ),
        "n_optional_route_replan_handoff_audit_roundtrip_primitive_evidence_matrix_witness_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_route_replan_handoff_audit_roundtrip_primitive_evidence_matrix_witness_trace"
        ),
        "n_optional_route_replan_handoff_audit_roundtrip_primitive_evidence_matrix_witness_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_route_replan_handoff_audit_roundtrip_primitive_evidence_matrix_witness_trace"
            and check.ok
        ),
        "n_optional_route_replan_handoff_audit_roundtrip_route_adoption_preconditions_checked": sum(
            1
            for check in checks
            if check.check_name
            == "optional_route_replan_handoff_audit_roundtrip_route_adoption_preconditions_trace"
        ),
        "n_optional_route_replan_handoff_audit_roundtrip_route_adoption_preconditions_valid": sum(
            1
            for check in checks
            if check.check_name
            == "optional_route_replan_handoff_audit_roundtrip_route_adoption_preconditions_trace"
            and check.ok
        ),
        "n_optional_runtime_handoff_audit_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_runtime_handoff_audit_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_runtime_handoff_audit_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_runtime_handoff_audit_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_runtime_handoff_audit_cost_control_checked": sum(
            1
            for check in checks
            if check.check_name
            in {
                "optional_runtime_handoff_audit_cost_control",
                "optional_runtime_handoff_audit_prompt_smoke",
                "optional_runtime_handoff_audit_prompt_tier_accounting",
                "optional_runtime_handoff_audit_standalone_smoke",
                "optional_runtime_handoff_audit_no_failures",
            }
        ),
        "n_optional_runtime_handoff_audit_cost_control_valid": sum(
            1
            for check in checks
            if check.check_name
            in {
                "optional_runtime_handoff_audit_cost_control",
                "optional_runtime_handoff_audit_prompt_smoke",
                "optional_runtime_handoff_audit_prompt_tier_accounting",
                "optional_runtime_handoff_audit_standalone_smoke",
                "optional_runtime_handoff_audit_no_failures",
            }
            and check.ok
        ),
        "n_optional_ablation_study_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_ablation_study_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_ablation_study_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_ablation_study_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_ablation_study_route_adoption_manifest_checked": sum(
            1
            for check in checks
            if check.check_name == "optional_ablation_study_route_adoption_manifest"
        ),
        "n_optional_ablation_study_route_adoption_manifest_valid": sum(
            1
            for check in checks
            if check.check_name == "optional_ablation_study_route_adoption_manifest"
            and check.ok
        ),
        "n_optional_ablation_study_rows_with_route_adoption_metrics": sum(
            1
            for row in optional_ablation_study_rows
            if _ablation_study_row_has_route_adoption_metrics(row)
        ),
        "optional_ablation_study_largest_route_adoption_ready_drop_variant": (
            optional_ablation_route_adoption_drop_variant
        ),
        "n_optional_portable_plan_audit_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_portable_plan_audit_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_portable_plan_audit_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_portable_plan_audit_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_library_coverage_map_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_library_coverage_map_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_library_coverage_map_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_library_coverage_map_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_primitive_action_queue_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_primitive_action_queue_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_primitive_action_queue_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_primitive_action_queue_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_action_resource_plan_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_action_resource_plan_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_action_resource_plan_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_action_resource_plan_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_resource_request_queue_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_resource_request_queue_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_resource_request_queue_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_resource_request_queue_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_resource_request_contract_alignment_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_resource_request_queue_row_")
            and check.check_name.endswith("_resource_contract_alignment")
        ),
        "n_optional_resource_request_contract_alignment_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_resource_request_queue_row_")
            and check.check_name.endswith("_resource_contract_alignment")
            and check.ok
        ),
        "n_optional_resource_request_action_plan_ref_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_resource_request_queue_row_")
            and check.check_name.endswith("_action_resource_plan_ref")
        ),
        "n_optional_resource_request_action_plan_ref_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_resource_request_queue_row_")
            and check.check_name.endswith("_action_resource_plan_ref")
            and check.ok
        ),
        "n_optional_resource_request_payload_identity_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_resource_request_queue_row_")
            and check.check_name.endswith("_request_payload_identity")
        ),
        "n_optional_resource_request_payload_identity_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_resource_request_queue_row_")
            and check.check_name.endswith("_request_payload_identity")
            and check.ok
        ),
        "n_optional_resource_request_dispatch_spec_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_resource_request_queue_row_")
            and check.check_name.endswith("_dispatch_spec_identity")
        ),
        "n_optional_resource_request_dispatch_spec_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_resource_request_queue_row_")
            and check.check_name.endswith("_dispatch_spec_identity")
            and check.ok
        ),
        "n_optional_resource_response_ledger_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_resource_response_ledger_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_resource_response_ledger_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_resource_response_ledger_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_resource_response_request_ref_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_resource_response_ledger_row_")
            and check.check_name.endswith("_request_ref")
        ),
        "n_optional_resource_response_request_ref_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_resource_response_ledger_row_")
            and check.check_name.endswith("_request_ref")
            and check.ok
        ),
        "n_optional_resource_response_contract_field_accounting_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_resource_response_ledger_row_")
            and check.check_name.endswith("_contract_field_accounting")
        ),
        "n_optional_resource_response_contract_field_accounting_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_resource_response_ledger_row_")
            and check.check_name.endswith("_contract_field_accounting")
            and check.ok
        ),
        "n_prover_adapter_packet_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_prover_adapter_packet_row_")
        ),
        "n_prover_adapter_packet_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_prover_adapter_packet_row_")
            and check.ok
        ),
        "n_prover_adapter_response_validation_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "optional_prover_adapter_response_validation_row_"
            )
            and check.check_name.endswith("_schema_valid")
        ),
        "n_prover_adapter_response_validation_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "optional_prover_adapter_response_validation_row_"
            )
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_cross_prover_matrix_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_cross_prover_matrix_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_cross_prover_matrix_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_cross_prover_matrix_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_cross_prover_packet_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_cross_prover_packet_row_")
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_cross_prover_packet_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_cross_prover_packet_row_")
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_cross_prover_packet_trace_checked": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_cross_prover_packet_row_")
            and check.check_name.endswith("_standalone_input_trace")
        ),
        "n_optional_cross_prover_packet_trace_valid": sum(
            1
            for check in checks
            if check.check_name.startswith("optional_cross_prover_packet_row_")
            and check.check_name.endswith("_standalone_input_trace")
            and check.ok
        ),
        "n_optional_cross_prover_response_validation_row_schema_checked": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "optional_cross_prover_response_validation_row_"
            )
            and check.check_name.endswith("_schema_valid")
        ),
        "n_optional_cross_prover_response_validation_row_schema_valid": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "optional_cross_prover_response_validation_row_"
            )
            and check.check_name.endswith("_schema_valid")
            and check.ok
        ),
        "n_optional_cross_prover_formal_attempt_dependency_checked": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "optional_cross_prover_formal_attempt_dependency_"
            )
        ),
        "n_optional_cross_prover_formal_attempt_dependency_valid": sum(
            1
            for check in checks
            if check.check_name.startswith(
                "optional_cross_prover_formal_attempt_dependency_"
            )
            and check.ok
        ),
        "by_category": dict(sorted(by_category.items())),
        "n_bundle_files": len(bundle_files),
        "bundle_files": tuple(str(path) for path in bundle_files),
        "bundle_audit_fingerprint": stable_hash(
            [
                str(path.relative_to(bundle_dir))
                + ":"
                + stable_hash(path.read_text(encoding="utf-8", errors="replace"))
                for path in bundle_files
            ]
        ),
        "all_ok": not errors and bool(checks) and all(check.ok for check in checks),
        "errors": errors,
        "checks": [asdict(check) for check in checks],
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "bundle audit validates packaging and contracts only",
            "proof claims still require target-prover replay/calibration outside this audit",
            "semantic adequacy of a route still depends on source review and downstream kernel attempts",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formalization_gap_planner_publication_bundle_audit_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_publication_bundle_audit.jsonl").write_text(
            "\n".join(json.dumps(asdict(check), sort_keys=True) for check in checks)
            + ("\n" if checks else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_publication_bundle_audit.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _manifest_checks(
    bundle_dir: Path,
    manifest_path: Path,
    manifest: dict[str, Any],
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    core_names = {
        str(row.get("artifact_name", ""))
        for row in manifest.get("core_artifacts", [])
        if isinstance(row, dict)
    }
    reuse_targets = set(_str_tuple(manifest.get("portable_reuse_targets", [])))
    evaluation_summary_errors = _bundle_evaluation_summary_errors(
        bundle_dir,
        manifest,
    )
    llm_route_planner_summary_errors = _bundle_llm_route_planner_summary_errors(
        bundle_dir,
        manifest,
        summary_field="llm_route_planner_summary",
        artifact_name="formalization_gap_planner_llm_route_planner",
    )
    feedback_llm_route_planner_summary_errors = (
        _bundle_llm_route_planner_summary_errors(
            bundle_dir,
            manifest,
            summary_field="feedback_llm_route_planner_summary",
            artifact_name="formalization_gap_planner_feedback_llm_route_planner",
        )
    )
    response_payload_validation_summary_errors = (
        _bundle_llm_route_planner_response_payload_validation_summary_errors(
            bundle_dir,
            manifest,
        )
    )
    checks = [
        _check(
            "bundle_manifest_exists",
            "manifest",
            "manifest file exists",
            str(manifest_path.exists()),
            manifest_path.exists(),
        ),
        _check(
            "bundle_component_name",
            "manifest",
            PUBLICATION_BUNDLE_COMPONENT_NAME,
            str(manifest.get("component_name", "")),
            manifest.get("component_name") == PUBLICATION_BUNDLE_COMPONENT_NAME,
        ),
        _check(
            "packaged_component",
            "manifest",
            LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
            str(manifest.get("packaged_component", "")),
            manifest.get("packaged_component") == LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
        ),
        _check(
            "portable_schema_id",
            "manifest",
            PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
            str(manifest.get("portable_schema_id", "")),
            manifest.get("portable_schema_id") == PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
        ),
        _check(
            "core_artifacts_declared",
            "manifest",
            ",".join(REQUIRED_CORE_ARTIFACTS),
            ",".join(sorted(core_names)),
            set(REQUIRED_CORE_ARTIFACTS).issubset(core_names),
        ),
        _check(
            "core_artifacts_ok",
            "manifest",
            "all required core artifacts ok",
            f"{manifest.get('n_core_artifacts_ok')}/{manifest.get('n_core_artifacts')}",
            int(manifest.get("n_core_artifacts_ok", 0) or 0)
            >= len(REQUIRED_CORE_ARTIFACTS)
            and bool(manifest.get("all_ok", False)),
        ),
        _check(
            "portable_reuse_targets",
            "manifest",
            ",".join(REQUIRED_REUSE_TARGETS),
            ",".join(sorted(reuse_targets)),
            set(REQUIRED_REUSE_TARGETS).issubset(reuse_targets),
        ),
        _check(
            "bundle_evaluation_summary_consistent",
            "manifest",
            "evaluation_summary matches packaged evaluation artifacts",
            "ok" if not evaluation_summary_errors else "; ".join(
                evaluation_summary_errors[:3]
            ),
            not evaluation_summary_errors,
            errors=evaluation_summary_errors,
        ),
        _check(
            "bundle_llm_route_planner_summary_consistent",
            "manifest",
            "llm_route_planner_summary matches packaged LLM route-planner artifacts",
            "ok" if not llm_route_planner_summary_errors else "; ".join(
                llm_route_planner_summary_errors[:3]
            ),
            not llm_route_planner_summary_errors,
            errors=llm_route_planner_summary_errors,
        ),
        _check(
            "bundle_feedback_llm_route_planner_summary_consistent",
            "manifest",
            "feedback_llm_route_planner_summary matches packaged feedback LLM route-planner artifacts",
            "ok" if not feedback_llm_route_planner_summary_errors else "; ".join(
                feedback_llm_route_planner_summary_errors[:3]
            ),
            not feedback_llm_route_planner_summary_errors,
            errors=feedback_llm_route_planner_summary_errors,
        ),
        _check(
            "bundle_llm_route_planner_response_payload_validation_summary_consistent",
            "manifest",
            "llm_route_planner_response_payload_validation_summary matches packaged response-payload validation artifacts",
            (
                "ok"
                if not response_payload_validation_summary_errors
                else "; ".join(response_payload_validation_summary_errors[:3])
            ),
            not response_payload_validation_summary_errors,
            errors=response_payload_validation_summary_errors,
        ),
        _check(
            "bundle_root_is_directory",
            "manifest",
            "bundle directory exists",
            str(bundle_dir.exists()),
            bundle_dir.is_dir(),
        ),
    ]
    return checks


def _bundle_evaluation_summary_errors(
    bundle_dir: Path,
    manifest: dict[str, Any],
) -> tuple[str, ...]:
    observed = manifest.get("evaluation_summary", {})
    if not isinstance(observed, dict):
        return ("evaluation_summary missing or not an object",)
    expected = _expected_bundle_evaluation_summary(bundle_dir)
    errors: list[str] = []
    for field_name, expected_value in expected.items():
        if field_name not in observed:
            errors.append(f"evaluation_summary.{field_name} missing")
            continue
        observed_value = observed.get(field_name)
        if isinstance(expected_value, bool):
            if bool(observed_value) != expected_value:
                errors.append(
                    f"evaluation_summary.{field_name} mismatch: "
                    f"observed={observed_value} expected={expected_value}"
                )
        elif isinstance(expected_value, int):
            if int(observed_value or 0) != expected_value:
                errors.append(
                    f"evaluation_summary.{field_name} mismatch: "
                    f"observed={observed_value} expected={expected_value}"
                )
        elif isinstance(expected_value, float):
            if float(observed_value or 0.0) != expected_value:
                errors.append(
                    f"evaluation_summary.{field_name} mismatch: "
                    f"observed={observed_value} expected={expected_value}"
                )
        elif isinstance(expected_value, tuple):
            observed_tuple = _str_tuple(observed_value)
            if observed_tuple != expected_value:
                errors.append(
                    f"evaluation_summary.{field_name} mismatch: "
                    f"observed={sorted(observed_tuple)} expected={sorted(expected_value)}"
                )
        elif isinstance(expected_value, dict):
            observed_dict = observed_value if isinstance(observed_value, dict) else {}
            has_nested_summary = any(
                isinstance(value, dict)
                for value in tuple(expected_value.values())
                + tuple(observed_dict.values())
            )
            if has_nested_summary:
                normalized_observed = _normalized_summary_dict(observed_dict)
                normalized_expected = _normalized_summary_dict(expected_value)
            else:
                normalized_observed = _int_mapping(observed_dict)
                normalized_expected = _int_mapping(expected_value)
            if normalized_observed != normalized_expected:
                errors.append(
                    f"evaluation_summary.{field_name} mismatch: "
                    f"observed={normalized_observed} expected={normalized_expected}"
                )
        elif str(observed_value) != str(expected_value):
            errors.append(
                f"evaluation_summary.{field_name} mismatch: "
                f"observed={observed_value} expected={expected_value}"
            )
    return tuple(errors)


def _bundle_llm_route_planner_summary_errors(
    bundle_dir: Path,
    manifest: dict[str, Any],
    *,
    summary_field: str,
    artifact_name: str,
) -> tuple[str, ...]:
    observed = manifest.get(summary_field, {})
    if not isinstance(observed, dict):
        return (f"{summary_field} missing or not an object",)
    expected = _expected_bundle_llm_route_planner_summary(bundle_dir, artifact_name)
    errors: list[str] = []
    for field_name, expected_value in expected.items():
        if field_name not in observed:
            errors.append(f"{summary_field}.{field_name} missing")
            continue
        observed_value = observed.get(field_name)
        if isinstance(expected_value, bool):
            if bool(observed_value) != expected_value:
                errors.append(
                    f"{summary_field}.{field_name} mismatch: "
                    f"observed={observed_value} expected={expected_value}"
                )
        elif isinstance(expected_value, int):
            if int(observed_value or 0) != expected_value:
                errors.append(
                    f"{summary_field}.{field_name} mismatch: "
                    f"observed={observed_value} expected={expected_value}"
                )
        elif isinstance(expected_value, tuple):
            observed_tuple = _str_tuple(observed_value)
            if observed_tuple != expected_value:
                errors.append(
                    f"{summary_field}.{field_name} mismatch: "
                    f"observed={sorted(observed_tuple)} expected={sorted(expected_value)}"
                )
        elif isinstance(expected_value, dict):
            observed_dict = observed_value if isinstance(observed_value, dict) else {}
            has_nested_summary = any(
                isinstance(value, dict)
                for value in tuple(expected_value.values())
                + tuple(observed_dict.values())
            )
            if has_nested_summary:
                normalized_observed = _normalized_summary_dict(observed_dict)
                normalized_expected = _normalized_summary_dict(expected_value)
            else:
                try:
                    normalized_observed = _int_mapping(observed_dict)
                    normalized_expected = _int_mapping(expected_value)
                except (TypeError, ValueError):
                    normalized_observed = _normalized_summary_dict(observed_dict)
                    normalized_expected = _normalized_summary_dict(expected_value)
            if normalized_observed != normalized_expected:
                errors.append(
                    f"{summary_field}.{field_name} mismatch: "
                    f"observed={normalized_observed} expected={normalized_expected}"
                )
        elif str(observed_value) != str(expected_value):
            errors.append(
                f"{summary_field}.{field_name} mismatch: "
                f"observed={observed_value} expected={expected_value}"
            )
    return tuple(errors)


def _bundle_llm_route_planner_response_payload_validation_summary_errors(
    bundle_dir: Path,
    manifest: dict[str, Any],
) -> tuple[str, ...]:
    summary_field = "llm_route_planner_response_payload_validation_summary"
    observed = manifest.get(summary_field, {})
    if not isinstance(observed, dict):
        return (f"{summary_field} missing or not an object",)
    expected = _expected_bundle_llm_route_planner_response_payload_validation_summary(
        bundle_dir
    )
    errors: list[str] = []
    for field_name, expected_value in expected.items():
        if field_name not in observed:
            errors.append(f"{summary_field}.{field_name} missing")
            continue
        observed_value = observed.get(field_name)
        if isinstance(expected_value, bool):
            if bool(observed_value) != expected_value:
                errors.append(
                    f"{summary_field}.{field_name} mismatch: "
                    f"observed={observed_value} expected={expected_value}"
                )
        elif isinstance(expected_value, int):
            if int(observed_value or 0) != expected_value:
                errors.append(
                    f"{summary_field}.{field_name} mismatch: "
                    f"observed={observed_value} expected={expected_value}"
                )
        elif isinstance(expected_value, dict):
            observed_dict = observed_value if isinstance(observed_value, dict) else {}
            if _int_mapping(observed_dict) != _int_mapping(expected_value):
                errors.append(
                    f"{summary_field}.{field_name} mismatch: "
                    f"observed={_int_mapping(observed_dict)} "
                    f"expected={_int_mapping(expected_value)}"
                )
        elif str(observed_value) != str(expected_value):
            errors.append(
                f"{summary_field}.{field_name} mismatch: "
                f"observed={observed_value} expected={expected_value}"
            )
    return tuple(errors)


def _expected_bundle_llm_route_planner_response_payload_validation_summary(
    bundle_dir: Path,
) -> dict[str, object]:
    artifact_dir = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_llm_route_planner_response_payload_validation"
    )
    manifest_path = (
        artifact_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.json"
    )
    rows_path = (
        artifact_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation.jsonl"
    )
    payload = _read_json_no_error(manifest_path)
    rows, _row_errors = _read_jsonl_dict_rows_no_error(rows_path)
    by_payload_target = payload.get("by_payload_target_prover_family", {})
    by_request_target = payload.get("by_request_context_target_prover_family", {})
    return {
        "requested": artifact_dir.exists(),
        "n_payloads": int(payload.get("n_payloads", 0) or 0),
        "n_valid_payloads": int(payload.get("n_valid_payloads", 0) or 0),
        "n_invalid_payloads": int(payload.get("n_invalid_payloads", 0) or 0),
        "n_request_context_packets": int(
            payload.get("n_request_context_packets", 0) or 0
        ),
        "n_request_contexts_with_context_packet_inventory": int(
            payload.get("n_request_contexts_with_context_packet_inventory", 0) or 0
        ),
        "n_request_context_inventory_total_rows": int(
            payload.get("n_request_context_inventory_total_rows", 0) or 0
        ),
        "n_request_bound_payloads": int(
            payload.get("n_request_bound_payloads", 0) or 0
        ),
        "n_request_bound_payloads_with_context_packet_inventory": int(
            payload.get(
                "n_request_bound_payloads_with_context_packet_inventory",
                0,
            )
            or 0
        ),
        "n_request_bound_payload_context_inventory_total_rows": int(
            payload.get("n_request_bound_payload_context_inventory_total_rows", 0)
            or 0
        ),
        "n_request_bound_payloads_with_route_adoption_preconditions": int(
            payload.get(
                "n_request_bound_payloads_with_route_adoption_preconditions",
                0,
            )
            or 0
        ),
        "n_request_bound_payloads_with_blocking_route_adoption_preconditions": int(
            payload.get(
                "n_request_bound_payloads_with_blocking_route_adoption_preconditions",
                0,
            )
            or 0
        ),
        "n_request_bound_payload_route_adoption_precondition_known_blockers": int(
            payload.get(
                "n_request_bound_payload_route_adoption_precondition_known_blockers",
                0,
            )
            or 0
        ),
        "n_request_bound_payload_route_adoption_precondition_required_response_fields": int(
            payload.get(
                "n_request_bound_payload_route_adoption_precondition_required_response_fields",
                0,
            )
            or 0
        ),
        "n_request_bound_payload_route_adoption_precondition_target_primitives": int(
            payload.get(
                "n_request_bound_payload_route_adoption_precondition_target_primitives",
                0,
            )
            or 0
        ),
        "n_payloads_with_formal_attempt_queue": int(
            payload.get(
                "n_payloads_with_formal_attempt_queue",
                sum(
                    1
                    for row in rows
                    if bool(row.get("payload_formal_attempt_queue_present", False))
                ),
            )
            or 0
        ),
        "n_payload_formal_attempt_queue_items": int(
            payload.get(
                "n_payload_formal_attempt_queue_items",
                sum(
                    int(row.get("payload_formal_attempt_queue_item_count", 0) or 0)
                    for row in rows
                ),
            )
            or 0
        ),
        "n_payloads_with_formal_attempt_queue_errors": int(
            payload.get(
                "n_payloads_with_formal_attempt_queue_errors",
                sum(
                    1
                    for row in rows
                    if int(row.get("n_formal_attempt_queue_errors", 0) or 0)
                ),
            )
            or 0
        ),
        "n_formal_attempt_queue_errors": int(
            payload.get(
                "n_formal_attempt_queue_errors",
                sum(
                    int(row.get("n_formal_attempt_queue_errors", 0) or 0)
                    for row in rows
                ),
            )
            or 0
        ),
        "n_payloads_with_declared_target_prover_family": int(
            payload.get("n_payloads_with_declared_target_prover_family", 0) or 0
        ),
        "n_request_bound_payloads_with_target_prover_family_mismatch": int(
            payload.get(
                "n_request_bound_payloads_with_target_prover_family_mismatch",
                0,
            )
            or 0
        ),
        "by_payload_target_prover_family": (
            dict(by_payload_target) if isinstance(by_payload_target, dict) else {}
        ),
        "by_request_context_target_prover_family": (
            dict(by_request_target) if isinstance(by_request_target, dict) else {}
        ),
        "n_schema_errors": int(payload.get("n_schema_errors", 0) or 0),
        "n_request_context_errors": int(
            payload.get("n_request_context_errors", 0) or 0
        ),
        "all_ok": bool(payload.get("all_ok", False)),
    }


def _expected_bundle_llm_route_planner_summary(
    bundle_dir: Path,
    artifact_name: str,
) -> dict[str, object]:
    artifact_dir = bundle_dir / "artifacts" / artifact_name
    manifest_path = (
        artifact_dir / "formalization_gap_planner_llm_route_planner_manifest.json"
    )
    rows_path = artifact_dir / "formalization_gap_planner_llm_route_planner.jsonl"
    payload = _read_json_no_error(manifest_path)
    rows, _row_errors = _read_jsonl_dict_rows_no_error(rows_path)
    request_packets = _dict_tuple(payload.get("request_packets", []))
    request_model_tier_counts = Counter(
        str(packet.get("model_tier", "") or "unknown") for packet in request_packets
    )
    request_route_adoption_preconditions = tuple(
        _dict_value(
            _dict_value(packet, "context_packet"),
            "route_adoption_preconditions",
        )
        for packet in request_packets
    )
    row_route_adoption_preconditions = tuple(
        _dict_value(row, "route_adoption_preconditions") for row in rows
    )
    model_tier_decision_ledger = _dict_tuple(
        payload.get("model_tier_decision_ledger", [])
    )
    decision_basis_counts = _llm_route_planner_decision_basis_counts(request_packets)
    model_tier_decision_evidence_rows = tuple(
        _dict_value(packet, "model_tier_decision_evidence")
        for packet in request_packets
    )
    route_option_selection_briefs = tuple(
        _dict_value(
            _dict_value(packet, "context_packet"),
            "route_option_selection_brief",
        )
        for packet in request_packets
    )
    acceptance_status_counts = Counter(
        str(row.get("acceptance_status", "") or "unknown") for row in rows
    )
    route_adoption_status_counts = _llm_route_planner_status_counts_for_summary(
        payload,
        rows,
    )
    route_adoption_blocker_counts = _llm_route_planner_blocker_counts_for_summary(
        payload,
        rows,
    )
    standalone_replay_gate = _dict_value(payload, "standalone_replay_gate")
    return {
        "requested": manifest_path.exists(),
        "provider_execution_mode": str(
            payload.get("provider_execution_mode", "") or ""
        ),
        "invoke_provider": bool(payload.get("invoke_provider", False)),
        "response_json_supplied": bool(payload.get("response_json_supplied", False)),
        "static_response_json_supplied": bool(
            payload.get("static_response_json_supplied", False)
        ),
        "generator_backend_supplied": bool(
            payload.get("generator_backend_supplied", False)
        ),
        "live_provider_backend_requested": bool(
            payload.get("live_provider_backend_requested", False)
        ),
        "static_generator_backend_requested": bool(
            payload.get("static_generator_backend_requested", False)
        ),
        "provider_generation_requested": bool(
            payload.get("provider_generation_requested", False)
        ),
        "n_request_packets": int(payload.get("n_request_packets", len(rows)) or 0),
        "n_requests_with_context_packet_inventory": int(
            payload.get("n_requests_with_context_packet_inventory", 0) or 0
        ),
        "n_request_context_inventory_total_rows": int(
            payload.get("n_request_context_inventory_total_rows", 0) or 0
        ),
        "n_rows_with_context_packet_inventory": int(
            payload.get(
                "n_rows_with_context_packet_inventory",
                sum(1 for row in rows if row.get("context_packet_inventory")),
            )
            or 0
        ),
        "n_requests_with_available_source_snippets": int(
            payload.get(
                "n_requests_with_available_source_snippets",
                sum(
                    1
                    for packet in request_packets
                    if _dict_tuple(
                        _dict_value(packet, "context_packet").get(
                            "available_source_snippets",
                            [],
                        )
                    )
                ),
            )
            or 0
        ),
        "n_request_available_source_snippets": int(
            payload.get(
                "n_request_available_source_snippets",
                sum(
                    len(
                        _dict_tuple(
                            _dict_value(packet, "context_packet").get(
                                "available_source_snippets",
                                [],
                            )
                        )
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_requests_with_target_intake_rows": int(
            payload.get(
                "n_requests_with_target_intake_rows",
                sum(
                    1
                    for packet in request_packets
                    if _dict_tuple(
                        _dict_value(packet, "context_packet").get(
                            "target_intake_rows",
                            [],
                        )
                    )
                ),
            )
            or 0
        ),
        "n_request_target_intake_rows": int(
            payload.get(
                "n_request_target_intake_rows",
                sum(
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
            )
            or 0
        ),
        "n_requests_with_current_goal_plan_rows": int(
            payload.get(
                "n_requests_with_current_goal_plan_rows",
                sum(
                    1
                    for packet in request_packets
                    if _dict_tuple(
                        _dict_value(packet, "context_packet").get(
                            "current_goal_plan_rows",
                            [],
                        )
                    )
                ),
            )
            or 0
        ),
        "n_request_current_goal_plan_rows": int(
            payload.get(
                "n_request_current_goal_plan_rows",
                sum(
                    len(
                        _dict_tuple(
                            _dict_value(packet, "context_packet").get(
                                "current_goal_plan_rows",
                                [],
                            )
                        )
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_requests_with_route_adoption_preconditions": int(
            payload.get(
                "n_requests_with_route_adoption_preconditions",
                sum(1 for value in request_route_adoption_preconditions if value),
            )
            or 0
        ),
        "n_request_route_adoption_precondition_known_blockers": int(
            payload.get(
                "n_request_route_adoption_precondition_known_blockers",
                sum(
                    int(
                        value.get(
                            "n_known_pre_response_blockers",
                            len(_str_tuple(value.get("known_pre_response_blockers", []))),
                        )
                        or 0
                    )
                    for value in request_route_adoption_preconditions
                ),
            )
            or 0
        ),
        "n_request_route_adoption_precondition_required_response_fields": int(
            payload.get(
                "n_request_route_adoption_precondition_required_response_fields",
                sum(
                    len(_str_tuple(value.get("response_required_fields", [])))
                    for value in request_route_adoption_preconditions
                ),
            )
            or 0
        ),
        "n_request_route_adoption_precondition_target_primitives": int(
            payload.get(
                "n_request_route_adoption_precondition_target_primitives",
                sum(
                    len(_str_tuple(value.get("target_primitives", [])))
                    for value in request_route_adoption_preconditions
                ),
            )
            or 0
        ),
        "n_requests_with_quality_control_obligation_inventory": int(
            payload.get(
                "n_requests_with_quality_control_obligation_inventory",
                0,
            )
            or 0
        ),
        "n_requests_with_pending_quality_control_obligation_inventory": int(
            payload.get(
                "n_requests_with_pending_quality_control_obligation_inventory",
                0,
            )
            or 0
        ),
        "n_request_quality_control_obligation_fields": int(
            payload.get("n_request_quality_control_obligation_fields", 0) or 0
        ),
        "n_request_quality_control_obligation_values": int(
            payload.get("n_request_quality_control_obligation_values", 0) or 0
        ),
        "n_request_pending_quality_control_fields": int(
            payload.get("n_request_pending_quality_control_fields", 0) or 0
        ),
        "n_request_pending_quality_control_values": int(
            payload.get("n_request_pending_quality_control_values", 0) or 0
        ),
        "n_request_discharged_quality_control_fields": int(
            payload.get("n_request_discharged_quality_control_fields", 0) or 0
        ),
        "n_request_discharged_quality_control_values": int(
            payload.get("n_request_discharged_quality_control_values", 0) or 0
        ),
        "n_requests_with_source_grounding_rows": int(
            payload.get("n_requests_with_source_grounding_rows", 0) or 0
        ),
        "n_request_source_grounding_rows": int(
            payload.get("n_request_source_grounding_rows", 0) or 0
        ),
        "n_requests_with_source_grounding_obligation_inventory": int(
            payload.get(
                "n_requests_with_source_grounding_obligation_inventory",
                0,
            )
            or 0
        ),
        "n_requests_with_pending_source_grounding_obligation_inventory": int(
            payload.get(
                "n_requests_with_pending_source_grounding_obligation_inventory",
                0,
            )
            or 0
        ),
        "n_request_source_grounding_unresolved_rows": int(
            payload.get("n_request_source_grounding_unresolved_rows", 0) or 0
        ),
        "n_request_residual_source_grounding_unresolved_rows": int(
            payload.get(
                "n_request_residual_source_grounding_unresolved_rows",
                0,
            )
            or 0
        ),
        "n_request_residual_goals": int(
            payload.get(
                "n_request_residual_goals",
                sum(
                    len(_str_tuple(packet.get("residual_goals", [])))
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_requests_with_residual_goal_contexts": int(
            payload.get(
                "n_requests_with_residual_goal_contexts",
                sum(
                    1
                    for packet in request_packets
                    if _dict_tuple(packet.get("residual_goal_contexts", []))
                ),
            )
            or 0
        ),
        "n_request_residual_goal_contexts": int(
            payload.get(
                "n_request_residual_goal_contexts",
                sum(
                    len(_dict_tuple(packet.get("residual_goal_contexts", [])))
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_request_context_residual_goal_contexts": int(
            payload.get(
                "n_request_context_residual_goal_contexts",
                sum(
                    len(
                        _dict_tuple(
                            _dict_value(packet, "context_packet").get(
                                "residual_goal_contexts",
                                [],
                            )
                        )
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_request_inventory_residual_goal_contexts": int(
            payload.get(
                "n_request_inventory_residual_goal_contexts",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "context_packet_inventory",
                        ).get("residual_goal_context_count", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_requests_with_resource_feedback_readiness_summary": int(
            payload.get(
                "n_requests_with_resource_feedback_readiness_summary",
                sum(
                    1
                    for packet in request_packets
                    if int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "resource_feedback_readiness_summary",
                        ).get("total_count", 0)
                        or 0
                    )
                ),
            )
            or 0
        ),
        "n_request_resource_feedback_readiness_rows": int(
            payload.get(
                "n_request_resource_feedback_readiness_rows",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "resource_feedback_readiness_summary",
                        ).get("total_count", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_request_resource_feedback_reuse_ready_rows": int(
            payload.get(
                "n_request_resource_feedback_reuse_ready_rows",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "resource_feedback_readiness_summary",
                        ).get("reuse_ready_count", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_feedback_loop_summary_prior_llm_route_planner_hook_traces": int(
            payload.get(
                "n_feedback_loop_summary_prior_llm_route_planner_hook_traces",
                0,
            )
            or 0
        ),
        "n_requests_with_feedback_loop_summary_prior_llm_route_planner_hook_traces": int(
            payload.get(
                "n_requests_with_feedback_loop_summary_prior_llm_route_planner_hook_traces",
                0,
            )
            or 0
        ),
        "n_feedback_loop_summary_interactive_resource_requests": int(
            payload.get("n_feedback_loop_summary_interactive_resource_requests", 0)
            or 0
        ),
        "n_feedback_loop_summary_interactive_resource_request_dispatch_summaries": int(
            payload.get(
                "n_feedback_loop_summary_interactive_resource_request_dispatch_summaries",
                0,
            )
            or 0
        ),
        "n_feedback_loop_summary_interactive_resource_request_execution_commands": int(
            payload.get(
                "n_feedback_loop_summary_interactive_resource_request_execution_commands",
                0,
            )
            or 0
        ),
        "n_requests_with_component_resource_registry_context": int(
            payload.get("n_requests_with_component_resource_registry_context", 0)
            or 0
        ),
        "n_component_resource_registry_resources_in_prompt": int(
            payload.get("n_component_resource_registry_resources_in_prompt", 0)
            or 0
        ),
        "n_component_resource_registry_contracts_in_prompt": int(
            payload.get("n_component_resource_registry_contracts_in_prompt", 0)
            or 0
        ),
        "n_requests_with_source_theorem_semantic_primitive_bridge_context": int(
            payload.get(
                "n_requests_with_source_theorem_semantic_primitive_bridge_context",
                0,
            )
            or 0
        ),
        "n_component_resource_registry_source_theorem_semantic_primitive_bridge_resources_in_prompt": int(
            payload.get(
                "n_component_resource_registry_source_theorem_semantic_primitive_bridge_resources_in_prompt",
                0,
            )
            or 0
        ),
        "n_component_resource_registry_source_theorem_semantic_primitive_bridge_contracts_in_prompt": int(
            payload.get(
                "n_component_resource_registry_source_theorem_semantic_primitive_bridge_contracts_in_prompt",
                0,
            )
            or 0
        ),
        "n_requests_with_source_theorem_semantic_primitive_from_proof_body_executor_bridge_context": int(
            payload.get(
                "n_requests_with_source_theorem_semantic_primitive_from_proof_body_executor_bridge_context",
                0,
            )
            or 0
        ),
        "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_resources_in_prompt": int(
            payload.get(
                "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_resources_in_prompt",
                0,
            )
            or 0
        ),
        "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_contracts_in_prompt": int(
            payload.get(
                "n_component_resource_registry_source_theorem_semantic_primitive_from_proof_body_executor_bridge_contracts_in_prompt",
                0,
            )
            or 0
        ),
        "n_requests_with_source_theorem_formal_environment_bridge_context": int(
            payload.get(
                "n_requests_with_source_theorem_formal_environment_bridge_context",
                0,
            )
            or 0
        ),
        "n_component_resource_registry_source_theorem_formal_environment_bridge_resources_in_prompt": int(
            payload.get(
                "n_component_resource_registry_source_theorem_formal_environment_bridge_resources_in_prompt",
                0,
            )
            or 0
        ),
        "n_component_resource_registry_source_theorem_formal_environment_bridge_contracts_in_prompt": int(
            payload.get(
                "n_component_resource_registry_source_theorem_formal_environment_bridge_contracts_in_prompt",
                0,
            )
            or 0
        ),
        "n_requests_with_exact_source_theorem_proof_body_executor_context": int(
            payload.get(
                "n_requests_with_exact_source_theorem_proof_body_executor_context",
                0,
            )
            or 0
        ),
        "n_component_resource_registry_exact_source_theorem_proof_body_executor_resources_in_prompt": int(
            payload.get(
                "n_component_resource_registry_exact_source_theorem_proof_body_executor_resources_in_prompt",
                0,
            )
            or 0
        ),
        "n_component_resource_registry_exact_source_theorem_proof_body_executor_contracts_in_prompt": int(
            payload.get(
                "n_component_resource_registry_exact_source_theorem_proof_body_executor_contracts_in_prompt",
                0,
            )
            or 0
        ),
        "n_requests_with_source_theorem_semantic_primitive_rows": int(
            payload.get(
                "n_requests_with_source_theorem_semantic_primitive_rows",
                0,
            )
            or 0
        ),
        "n_request_source_theorem_semantic_primitive_rows": int(
            payload.get("n_request_source_theorem_semantic_primitive_rows", 0)
            or 0
        ),
        "n_requests_with_proof_body_semantic_primitive_work_order_rows": int(
            payload.get(
                "n_requests_with_proof_body_semantic_primitive_work_order_rows",
                0,
            )
            or 0
        ),
        "n_request_proof_body_semantic_primitive_work_order_rows": int(
            payload.get(
                "n_request_proof_body_semantic_primitive_work_order_rows",
                0,
            )
            or 0
        ),
        "n_requests_with_source_theorem_formal_environment_rows": int(
            payload.get(
                "n_requests_with_source_theorem_formal_environment_rows",
                0,
            )
            or 0
        ),
        "n_request_source_theorem_formal_environment_rows": int(
            payload.get("n_request_source_theorem_formal_environment_rows", 0)
            or 0
        ),
        "n_requests_with_source_theorem_proof_body_execution_result_rows": int(
            payload.get(
                "n_requests_with_source_theorem_proof_body_execution_result_rows",
                0,
            )
            or 0
        ),
        "n_request_source_theorem_proof_body_execution_result_rows": int(
            payload.get(
                "n_request_source_theorem_proof_body_execution_result_rows",
                0,
            )
            or 0
        ),
        "n_requests_with_patch_rerun_residual_obligation_summary": int(
            payload.get(
                "n_requests_with_patch_rerun_residual_obligation_summary",
                sum(
                    1
                    for packet in request_packets
                    if _dict_value(packet, "context_packet").get(
                        "patch_rerun_residual_obligation_summary"
                    )
                ),
            )
            or 0
        ),
        "n_request_patch_rerun_residual_obligation_rows": int(
            payload.get(
                "n_request_patch_rerun_residual_obligation_rows",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "patch_rerun_residual_obligation_summary",
                        ).get("total_rows", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_request_patch_rerun_residual_obligation_source_discovery_needed": int(
            payload.get(
                "n_request_patch_rerun_residual_obligation_source_discovery_needed",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "patch_rerun_residual_obligation_summary",
                        ).get("source_discovery_needed_count", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_requests_with_patch_rerun_residual_followup_queue_summary": int(
            payload.get(
                "n_requests_with_patch_rerun_residual_followup_queue_summary",
                sum(
                    1
                    for packet in request_packets
                    if _dict_value(packet, "context_packet").get(
                        "patch_rerun_residual_followup_queue_summary"
                    )
                ),
            )
            or 0
        ),
        "n_request_patch_rerun_residual_followup_queue_rows": int(
            payload.get(
                "n_request_patch_rerun_residual_followup_queue_rows",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "patch_rerun_residual_followup_queue_summary",
                        ).get("total_rows", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_request_patch_rerun_residual_followup_queue_ready": int(
            payload.get(
                "n_request_patch_rerun_residual_followup_queue_ready",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "patch_rerun_residual_followup_queue_summary",
                        ).get("ready_count", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_request_patch_rerun_residual_followup_queue_source_discovery": int(
            payload.get(
                "n_request_patch_rerun_residual_followup_queue_source_discovery",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "patch_rerun_residual_followup_queue_summary",
                        ).get("source_discovery_count", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_requests_with_agentic_proof_strategy_plan_summary": int(
            payload.get(
                "n_requests_with_agentic_proof_strategy_plan_summary",
                sum(
                    1
                    for packet in request_packets
                    if _dict_value(packet, "context_packet").get(
                        "agentic_proof_strategy_plan_summary"
                    )
                ),
            )
            or 0
        ),
        "n_request_agentic_proof_strategy_plan_rows": int(
            payload.get(
                "n_request_agentic_proof_strategy_plan_rows",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "agentic_proof_strategy_plan_summary",
                        ).get("total_rows", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_request_agentic_proof_strategy_plan_ready": int(
            payload.get(
                "n_request_agentic_proof_strategy_plan_ready",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "agentic_proof_strategy_plan_summary",
                        ).get("ready_count", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_request_agentic_proof_strategy_plan_source_discovery_cache_items": int(
            payload.get(
                "n_request_agentic_proof_strategy_plan_source_discovery_cache_items",
                sum(
                    int(
                        _dict_value(
                            _dict_value(packet, "context_packet"),
                            "agentic_proof_strategy_plan_summary",
                        ).get("source_discovery_cache_item_count", 0)
                        or 0
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_rows": int(payload.get("n_rows", len(rows)) or 0),
        "n_response_present": int(
            payload.get(
                "n_response_present",
                sum(1 for row in rows if bool(row.get("response_present", False))),
            )
            or 0
        ),
        "n_response_contract_ok": int(
            payload.get(
                "n_response_contract_ok",
                sum(
                    1
                    for row in rows
                    if bool(row.get("response_contract_ok", False))
                ),
            )
            or 0
        ),
        "n_provider_failures": int(
            payload.get(
                "n_provider_failures",
                sum(1 for row in rows if bool(row.get("provider_failure", False))),
            )
            or 0
        ),
        "provider_usage_summary": _dict_value(payload, "provider_usage_summary"),
        "n_rows_with_provider_usage": int(
            payload.get(
                "n_rows_with_provider_usage",
                len(_dict_tuple(payload.get("provider_usage_rows", []))),
            )
            or 0
        ),
        "total_provider_input_tokens": int(
            payload.get(
                "total_provider_input_tokens",
                _dict_value(payload, "provider_usage_summary").get(
                    "input_tokens",
                    0,
                ),
            )
            or 0
        ),
        "total_provider_output_tokens": int(
            payload.get(
                "total_provider_output_tokens",
                _dict_value(payload, "provider_usage_summary").get(
                    "output_tokens",
                    0,
                ),
            )
            or 0
        ),
        "total_provider_cache_creation_input_tokens": int(
            payload.get(
                "total_provider_cache_creation_input_tokens",
                _dict_value(payload, "provider_usage_summary").get(
                    "cache_creation_input_tokens",
                    0,
                ),
            )
            or 0
        ),
        "total_provider_cache_read_input_tokens": int(
            payload.get(
                "total_provider_cache_read_input_tokens",
                _dict_value(payload, "provider_usage_summary").get(
                    "cache_read_input_tokens",
                    0,
                ),
            )
            or 0
        ),
        "total_provider_total_tokens": int(
            payload.get(
                "total_provider_total_tokens",
                _dict_value(payload, "provider_usage_summary").get(
                    "total_tokens",
                    0,
                ),
            )
            or 0
        ),
        "n_generated_responses_model_tier_escalated": int(
            payload.get(
                "n_generated_responses_model_tier_escalated",
                sum(1 for row in rows if _llm_row_model_tier_escalated(row)),
            )
            or 0
        ),
        "n_generated_responses_haiku_to_sonnet_escalated": int(
            payload.get(
                "n_generated_responses_haiku_to_sonnet_escalated",
                sum(1 for row in rows if _llm_row_haiku_to_sonnet_escalated(row)),
            )
            or 0
        ),
        "n_repair_attempt_ledger_model_tier_escalations": int(
            payload.get(
                "n_repair_attempt_ledger_model_tier_escalations",
                sum(
                    1
                    for row in rows
                    for ledger_row in _dict_tuple(row.get("repair_attempt_ledger"))
                    if bool(ledger_row.get("model_tier_escalated"))
                ),
            )
            or 0
        ),
        "n_model_tier_decision_ledger_rows": int(
            payload.get(
                "n_model_tier_decision_ledger_rows",
                len(model_tier_decision_ledger),
            )
            or 0
        ),
        "n_model_tier_decision_ledger_rows_with_escalation": int(
            payload.get(
                "n_model_tier_decision_ledger_rows_with_escalation",
                sum(
                    1
                    for row in model_tier_decision_ledger
                    if row.get("model_tier_escalated")
                ),
            )
            or 0
        ),
        "n_model_tier_decision_ledger_provider_failure_rows": int(
            payload.get(
                "n_model_tier_decision_ledger_provider_failure_rows",
                sum(1 for row in model_tier_decision_ledger if row.get("provider_failure")),
            )
            or 0
        ),
        "n_rows_with_model_tier_escalation": int(
            payload.get(
                "n_rows_with_model_tier_escalation",
                sum(1 for row in rows if _llm_row_model_tier_escalated(row)),
            )
            or 0
        ),
        "n_requests_with_model_tier_decision_evidence": int(
            payload.get(
                "n_requests_with_model_tier_decision_evidence",
                sum(
                    1
                    for packet in request_packets
                    if _dict_value(packet, "model_tier_decision_evidence")
                ),
            )
            or 0
        ),
        "n_request_model_tier_haiku": int(
            payload.get(
                "n_request_model_tier_haiku",
                request_model_tier_counts.get("haiku", 0),
            )
            or 0
        ),
        "n_request_model_tier_sonnet": int(
            payload.get(
                "n_request_model_tier_sonnet",
                request_model_tier_counts.get("sonnet", 0),
            )
            or 0
        ),
        "n_request_model_tier_opus": int(
            payload.get(
                "n_request_model_tier_opus",
                request_model_tier_counts.get("opus", 0),
            )
            or 0
        ),
        "by_request_model_tier": dict(
            payload.get(
                "by_request_model_tier",
                dict(sorted(request_model_tier_counts.items())),
            )
            or {}
        ),
        "n_request_model_tier_decision_auto_haiku_bounded": int(
            payload.get(
                "n_request_model_tier_decision_auto_haiku_bounded",
                decision_basis_counts.get("auto_haiku_bounded_route", 0),
            )
            or 0
        ),
        "n_request_model_tier_decision_auto_sonnet_triggered": int(
            payload.get(
                "n_request_model_tier_decision_auto_sonnet_triggered",
                decision_basis_counts.get("auto_sonnet_triggers", 0),
            )
            or 0
        ),
        "n_request_model_tier_decision_operator_override": int(
            payload.get(
                "n_request_model_tier_decision_operator_override",
                decision_basis_counts.get("operator_override", 0),
            )
            or 0
        ),
        "n_request_model_tier_decision_sonnet_triggers": int(
            payload.get(
                "n_request_model_tier_decision_sonnet_triggers",
                sum(
                    len(
                        _str_tuple(
                            _dict_value(
                                packet,
                                "model_tier_decision_evidence",
                            ).get("sonnet_triggers", [])
                        )
                    )
                    for packet in request_packets
                ),
            )
            or 0
        ),
        "n_request_model_tier_decision_resource_feedback_readiness_rows": int(
            payload.get(
                "n_request_model_tier_decision_resource_feedback_readiness_rows",
                sum(
                    _nonnegative_int(
                        _dict_value(row, "resource_feedback_readiness_counts").get(
                            "total_count",
                            0,
                        )
                    )
                    for row in model_tier_decision_evidence_rows
                ),
            )
            or 0
        ),
        "n_request_model_tier_decision_resource_feedback_reuse_ready_rows": int(
            payload.get(
                "n_request_model_tier_decision_resource_feedback_reuse_ready_rows",
                sum(
                    _nonnegative_int(
                        _dict_value(row, "resource_feedback_readiness_counts").get(
                            "reuse_ready_count",
                            0,
                        )
                    )
                    for row in model_tier_decision_evidence_rows
                ),
            )
            or 0
        ),
        "n_request_model_tier_decision_resource_feedback_sonnet_triggers": int(
            payload.get(
                "n_request_model_tier_decision_resource_feedback_sonnet_triggers",
                sum(
                    1
                    for row in model_tier_decision_evidence_rows
                    for trigger in _str_tuple(row.get("sonnet_triggers", []))
                    if "resource-feedback readiness row" in trigger
                ),
            )
            or 0
        ),
        "n_request_model_tier_decision_evidence_invalid": int(
            payload.get("n_request_model_tier_decision_evidence_invalid", 0) or 0
        ),
        "by_request_model_tier_decision_basis": dict(
            payload.get(
                "by_request_model_tier_decision_basis",
                decision_basis_counts,
            )
            or {}
        ),
        "n_requests_with_route_option_selection_brief": int(
            payload.get(
                "n_requests_with_route_option_selection_brief",
                sum(1 for brief in route_option_selection_briefs if brief),
            )
            or 0
        ),
        "n_request_route_option_selection_candidate_options": int(
            payload.get(
                "n_request_route_option_selection_candidate_options",
                sum(
                    len(_dict_tuple(brief.get("candidate_route_options", [])))
                    for brief in route_option_selection_briefs
                ),
            )
            or 0
        ),
        "n_request_route_option_selection_candidate_primitives": int(
            payload.get(
                "n_request_route_option_selection_candidate_primitives",
                sum(
                    _nonnegative_int(
                        brief.get("n_candidate_route_option_primitives", 0)
                    )
                    for brief in route_option_selection_briefs
                ),
            )
            or 0
        ),
        "n_request_route_option_selection_candidates_with_residual_goals": int(
            payload.get(
                "n_request_route_option_selection_candidates_with_residual_goals",
                sum(
                    _nonnegative_int(
                        brief.get(
                            "n_candidate_route_options_with_residual_goals",
                            0,
                        )
                    )
                    for brief in route_option_selection_briefs
                ),
            )
            or 0
        ),
        "n_request_route_option_selection_candidate_residual_goals": int(
            payload.get(
                "n_request_route_option_selection_candidate_residual_goals",
                sum(
                    _nonnegative_int(
                        brief.get(
                            "n_candidate_route_option_residual_goals",
                            0,
                        )
                    )
                    for brief in route_option_selection_briefs
                ),
            )
            or 0
        ),
        "n_request_route_option_selection_lower_bound_options": int(
            payload.get(
                "n_request_route_option_selection_lower_bound_options",
                sum(
                    1
                    for brief in route_option_selection_briefs
                    if str(
                        brief.get("lower_bound_selected_route_option_id", "")
                    ).strip()
                ),
            )
            or 0
        ),
        "n_request_route_option_selection_lower_bound_residual_goals": int(
            payload.get(
                "n_request_route_option_selection_lower_bound_residual_goals",
                sum(
                    _nonnegative_int(
                        brief.get(
                            "lower_bound_selected_residual_goal_count",
                            0,
                        )
                    )
                    for brief in route_option_selection_briefs
                ),
            )
            or 0
        ),
        "n_informal_knowledge_dag_nodes": int(
            payload.get(
                "n_informal_knowledge_dag_nodes",
                sum(
                    len(_dict_tuple(row.get("informal_knowledge_dag_nodes")))
                    for row in rows
                ),
            )
            or 0
        ),
        "n_formal_realization_dag_nodes": int(
            payload.get(
                "n_formal_realization_dag_nodes",
                sum(
                    len(_dict_tuple(row.get("formal_realization_dag_nodes")))
                    for row in rows
                ),
            )
            or 0
        ),
        "n_lean_realization_dag_nodes": int(
            payload.get(
                "n_lean_realization_dag_nodes",
                sum(
                    len(_dict_tuple(row.get("lean_realization_dag_nodes")))
                    for row in rows
                ),
            )
            or 0
        ),
        "n_route_alignment_edges": int(
            payload.get(
                "n_route_alignment_edges",
                sum(
                    len(_dict_tuple(row.get("route_alignment_edges")))
                    for row in rows
                ),
            )
            or 0
        ),
        "n_search_requests": int(
            payload.get(
                "n_search_requests",
                sum(len(_dict_tuple(row.get("search_requests"))) for row in rows),
            )
            or 0
        ),
        "n_planner_next_actions": int(
            payload.get(
                "n_planner_next_actions",
                sum(len(_dict_tuple(row.get("planner_next_actions"))) for row in rows),
            )
            or 0
        ),
        "n_rows_with_planner_next_actions": int(
            payload.get(
                "n_rows_with_planner_next_actions",
                sum(1 for row in rows if _dict_tuple(row.get("planner_next_actions"))),
            )
            or 0
        ),
        "n_rows_with_residual_goal_contexts": int(
            payload.get(
                "n_rows_with_residual_goal_contexts",
                sum(1 for row in rows if _dict_tuple(row.get("residual_goal_contexts"))),
            )
            or 0
        ),
        "n_row_residual_goal_contexts": int(
            payload.get(
                "n_row_residual_goal_contexts",
                sum(
                    len(_dict_tuple(row.get("residual_goal_contexts")))
                    for row in rows
                ),
            )
            or 0
        ),
        "n_uncertainty_flags": int(
            payload.get(
                "n_uncertainty_flags",
                sum(len(_str_tuple(row.get("uncertainty_flags", []))) for row in rows),
            )
            or 0
        ),
        "n_residual_interpretations": int(
            payload.get(
                "n_residual_interpretations",
                sum(len(_dict_tuple(row.get("residual_interpretations"))) for row in rows),
            )
            or 0
        ),
        "n_source_snippets": int(
            payload.get(
                "n_source_snippets",
                sum(len(_dict_tuple(row.get("source_snippets"))) for row in rows),
            )
            or 0
        ),
        "n_rows_with_source_snippets": int(
            payload.get(
                "n_rows_with_source_snippets",
                sum(1 for row in rows if _dict_tuple(row.get("source_snippets"))),
            )
            or 0
        ),
        "n_formal_attempt_queue_items": int(
            payload.get(
                "n_formal_attempt_queue_items",
                sum(
                    len(_dict_tuple(row.get("formal_attempt_queue")))
                    for row in rows
                ),
            )
            or 0
        ),
        "n_rows_with_formal_attempt_queue": int(
            payload.get(
                "n_rows_with_formal_attempt_queue",
                sum(1 for row in rows if _dict_tuple(row.get("formal_attempt_queue"))),
            )
            or 0
        ),
        "n_delta_action_witness_required_primitives": int(
            payload.get(
                "n_delta_action_witness_required_primitives",
                sum(
                    len(
                        _str_tuple(
                            _dict_value(
                                row,
                                "realization_coverage_witness",
                            ).get("delta_action_witness_required_primitives", [])
                        )
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_delta_action_witness_missing_primitives": int(
            payload.get(
                "n_delta_action_witness_missing_primitives",
                sum(
                    len(
                        _str_tuple(
                            _dict_value(
                                row,
                                "realization_coverage_witness",
                            ).get("delta_action_witness_missing_primitives", [])
                        )
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_rows_with_delta_action_witness_obligations": int(
            payload.get(
                "n_rows_with_delta_action_witness_obligations",
                sum(
                    1
                    for row in rows
                    if _str_tuple(
                        _dict_value(
                            row,
                            "realization_coverage_witness",
                        ).get("delta_action_witness_required_primitives", [])
                    )
                ),
            )
            or 0
        ),
        "n_rows_with_complete_delta_action_witness": int(
            payload.get(
                "n_rows_with_complete_delta_action_witness",
                sum(
                    1
                    for row in rows
                    if _str_tuple(
                        _dict_value(
                            row,
                            "realization_coverage_witness",
                        ).get("delta_action_witness_required_primitives", [])
                    )
                    and bool(
                        _dict_value(
                            row,
                            "realization_coverage_witness",
                        ).get("delta_action_witness_complete", False)
                    )
                ),
            )
            or 0
        ),
        "n_rows_with_route_adoption_preconditions": int(
            payload.get(
                "n_rows_with_route_adoption_preconditions",
                sum(1 for value in row_route_adoption_preconditions if value),
            )
            or 0
        ),
        "n_row_route_adoption_precondition_known_blockers": int(
            payload.get(
                "n_row_route_adoption_precondition_known_blockers",
                sum(
                    int(
                        value.get(
                            "n_known_pre_response_blockers",
                            len(_str_tuple(value.get("known_pre_response_blockers", []))),
                        )
                        or 0
                    )
                    for value in row_route_adoption_preconditions
                ),
            )
            or 0
        ),
        "n_row_route_adoption_precondition_target_primitives": int(
            payload.get(
                "n_row_route_adoption_precondition_target_primitives",
                sum(
                    len(_str_tuple(value.get("target_primitives", [])))
                    for value in row_route_adoption_preconditions
                ),
            )
            or 0
        ),
        "n_accepted_route_plans": int(
            payload.get(
                "n_accepted_route_plans",
                sum(
                    1
                    for row in rows
                    if str(row.get("acceptance_status", "")).startswith("ACCEPTED_")
                ),
            )
            or 0
        ),
        "n_accepted_with_formal_attempt_queue": int(
            payload.get(
                "n_accepted_with_formal_attempt_queue",
                acceptance_status_counts.get(
                    "ACCEPTED_WITH_FORMAL_ATTEMPT_QUEUE",
                    0,
                ),
            )
            or 0
        ),
        "n_route_adoption_ready": route_adoption_status_counts.get(
            ROUTE_ADOPTION_READY_STATUS,
            0,
        ),
        "n_route_adoption_pending_refinement": route_adoption_status_counts.get(
            ROUTE_ADOPTION_PENDING_STATUS,
            0,
        ),
        "n_route_adoption_awaiting_llm_response": route_adoption_status_counts.get(
            ROUTE_ADOPTION_AWAITING_STATUS,
            0,
        ),
        "n_route_adoption_rejected": route_adoption_status_counts.get(
            ROUTE_ADOPTION_REJECTED_STATUS,
            0,
        ),
        "n_route_adoption_blockers": sum(route_adoption_blocker_counts.values()),
        "n_route_adoption_pending_formal_gap_boundary_blockers": (
            route_adoption_blocker_counts.get(
                ROUTE_ADOPTION_BLOCKER_FORMAL_GAP_BOUNDARIES,
                0,
            )
        ),
        "route_adoption_blockers": tuple(route_adoption_blocker_counts),
        "route_adoption_blocker_counts": dict(route_adoption_blocker_counts),
        "by_route_adoption_status": dict(route_adoption_status_counts),
        "by_route_adoption_blocker": _llm_route_planner_blocker_summary_for_summary(
            payload,
            rows,
        ),
        "standalone_replay_gate": dict(standalone_replay_gate),
        "standalone_replay_gate_ok": bool(
            payload.get(
                "standalone_replay_gate_ok",
                standalone_replay_gate.get("gate_ok", False),
            )
        ),
        "n_standalone_replay_route_candidates": int(
            payload.get(
                "n_standalone_replay_route_candidates",
                standalone_replay_gate.get("n_route_candidates", 0),
            )
            or 0
        ),
        "n_standalone_replay_adoptable_route_candidates": int(
            payload.get(
                "n_standalone_replay_adoptable_route_candidates",
                standalone_replay_gate.get("n_adoptable_route_candidates", 0),
            )
            or 0
        ),
        "n_standalone_replay_blocked_route_candidates": int(
            payload.get(
                "n_standalone_replay_blocked_route_candidates",
                standalone_replay_gate.get("n_blocked_route_candidates", 0),
            )
            or 0
        ),
        "standalone_replay_gate_blockers": _str_tuple(
            payload.get(
                "standalone_replay_gate_blockers",
                standalone_replay_gate.get("gate_blockers", []),
            )
        ),
        "n_row_schema_valid": int(payload.get("n_row_schema_valid", 0) or 0),
        "n_row_schema_invalid": int(payload.get("n_row_schema_invalid", 0) or 0),
        "all_ok": bool(payload.get("all_ok", False)),
    }


def _llm_route_planner_status_counts_for_summary(
    payload: dict[str, object],
    rows: list[dict[str, Any]],
) -> dict[str, int]:
    manifest_counts = payload.get("by_route_adoption_status", {})
    if isinstance(manifest_counts, dict) and manifest_counts:
        return {
            str(status): int(count or 0)
            for status, count in sorted(manifest_counts.items())
        }
    return dict(
        sorted(
            Counter(
                str(row.get("route_adoption_status", "")).strip()
                for row in rows
                if str(row.get("route_adoption_status", "")).strip()
            ).items()
        )
    )


def _llm_row_model_tier_escalated(row: Mapping[str, Any]) -> bool:
    metadata = row.get("generator_metadata", {})
    metadata = metadata if isinstance(metadata, Mapping) else {}
    return bool(row.get("model_tier_escalated") or metadata.get("model_tier_escalated"))


def _llm_row_haiku_to_sonnet_escalated(row: Mapping[str, Any]) -> bool:
    if not _llm_row_model_tier_escalated(row):
        return False
    metadata = row.get("generator_metadata", {})
    metadata = metadata if isinstance(metadata, Mapping) else {}
    requested = str(
        row.get("requested_model_tier")
        or metadata.get("requested_model_tier")
        or ""
    ).strip().lower()
    effective = str(
        row.get("model_tier")
        or metadata.get("effective_model_tier")
        or ""
    ).strip().lower()
    return requested == "haiku" and effective == "sonnet"


def _llm_route_planner_decision_basis_counts(
    request_packets: tuple[dict[str, Any], ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for packet in request_packets:
        basis = str(
            _dict_value(packet, "model_tier_decision_evidence").get(
                "decision_basis",
                "",
            )
            or "missing"
        ).strip()
        if basis:
            counts[basis] = counts.get(basis, 0) + 1
    return dict(sorted(counts.items()))


def _llm_route_planner_blocker_counts_for_summary(
    payload: dict[str, object],
    rows: list[dict[str, Any]],
) -> dict[str, int]:
    manifest_counts = payload.get("route_adoption_blocker_counts", {})
    if isinstance(manifest_counts, dict) and manifest_counts:
        return {
            str(blocker): int(count or 0)
            for blocker, count in sorted(manifest_counts.items())
        }
    return _llm_route_adoption_blocker_counts_from_rows(rows)


def _llm_route_planner_blocker_summary_for_summary(
    payload: dict[str, object],
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, object]]:
    manifest_summary = payload.get("by_route_adoption_blocker", {})
    if isinstance(manifest_summary, dict) and manifest_summary:
        return {
            str(blocker): dict(summary)
            for blocker, summary in sorted(manifest_summary.items())
            if isinstance(summary, dict)
        }
    return _llm_route_adoption_blocker_summary_from_rows(rows)


def _expected_bundle_evaluation_summary(bundle_dir: Path) -> dict[str, object]:
    evaluation_manifest_path = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_evaluation"
        / "formalization_gap_planner_evaluation_manifest.json"
    )
    evaluation_manifest = _read_json_no_error(evaluation_manifest_path)
    rows = _optional_evaluation_rows_for_summary(bundle_dir)
    route_adoption_counts = _evaluation_route_adoption_status_counts_from_rows(rows)
    route_adoption_blocker_counts = _evaluation_route_adoption_blocker_counts_for_summary(
        evaluation_manifest,
        rows,
    )
    route_adoption_blocker_summary = _evaluation_route_adoption_blocker_summary_for_summary(
        evaluation_manifest,
        rows,
    )
    return {
        "requested": evaluation_manifest_path.exists(),
        "n_evaluation_rows": int(
            evaluation_manifest.get("n_evaluation_rows", len(rows)) or 0
        ),
        "n_evaluation_row_schema_valid": int(
            evaluation_manifest.get("n_evaluation_row_schema_valid", 0) or 0
        ),
        "n_evaluation_row_schema_invalid": int(
            evaluation_manifest.get("n_evaluation_row_schema_invalid", 0) or 0
        ),
        "n_matched_ground_truth": int(
            evaluation_manifest.get("n_matched_ground_truth", 0) or 0
        ),
        "n_missing_ground_truth": int(
            evaluation_manifest.get("n_missing_ground_truth", 0) or 0
        ),
        "n_alignment_contract_ok": int(
            evaluation_manifest.get("n_alignment_contract_ok", 0) or 0
        ),
        "n_feedback_loop_ready": int(
            evaluation_manifest.get("n_feedback_loop_ready", 0) or 0
        ),
        "n_unaligned_primitives": int(
            evaluation_manifest.get("n_unaligned_primitives", 0) or 0
        ),
        "n_minimal_delta_route_options": sum(
            int(row.get("minimal_delta_route_option_count", 0) or 0)
            for row in rows
        ),
        "mean_minimal_delta_selected_route_cost": _mean_float(
            row.get("minimal_delta_selected_route_cost", 0.0)
            for row in rows
            if row.get("minimal_delta_cost_graph_present") is True
        ),
        "n_kernel_verified_ground_truth": sum(
            1 for row in rows if row.get("kernel_verified_ground_truth") is True
        ),
        "n_kernel_verification_witnesses": sum(
            _kernel_verification_witness_count(row) for row in rows
        ),
        "n_kernel_verified_ground_truth_with_witnesses": sum(
            1
            for row in rows
            if row.get("kernel_verified_ground_truth") is True
            and _kernel_verification_witness_count(row) > 0
        ),
        "mean_alignment_coverage": _mean_float(
            row.get("alignment_coverage", 0.0) for row in rows
        ),
        "n_realization_missing_selected_formal_primitives": sum(
            len(_str_tuple(row.get("realization_missing_selected_formal_primitives", [])))
            for row in rows
        ),
        "n_realization_missing_delta_alignment_primitives": sum(
            len(_str_tuple(row.get("realization_missing_delta_alignment_primitives", [])))
            for row in rows
        ),
        "n_rows_with_incomplete_cost_hint_baseline_coverage": sum(
            1
            for row in rows
            if row.get("realization_cost_hint_baseline_coverage_complete") is False
        ),
        "n_realization_cost_hint_baseline_primitives": sum(
            len(_str_tuple(row.get("realization_cost_hint_baseline_primitives", [])))
            for row in rows
        ),
        "n_realization_omitted_cost_hint_primitives": sum(
            len(_str_tuple(row.get("realization_omitted_cost_hint_primitives", [])))
            for row in rows
        ),
        "realization_missing_selected_formal_primitives": (
            _evaluation_realization_missing_selected_from_rows(rows)
        ),
        "realization_missing_delta_alignment_primitives": (
            _evaluation_realization_missing_delta_from_rows(rows)
        ),
        "realization_cost_hint_baseline_primitives": (
            _evaluation_realization_cost_hint_baseline_from_rows(rows)
        ),
        "realization_omitted_cost_hint_primitives": (
            _evaluation_realization_omitted_cost_hint_from_rows(rows)
        ),
        "n_rows_with_llm_route_planner_residual_goal_contexts": int(
            evaluation_manifest.get(
                "n_rows_with_llm_route_planner_residual_goal_contexts",
                sum(
                    1
                    for row in rows
                    if int(
                        row.get(
                            "llm_route_planner_residual_goal_context_count",
                            0,
                        )
                        or 0
                    )
                ),
            )
            or 0
        ),
        "n_llm_route_planner_residual_goal_contexts": int(
            evaluation_manifest.get(
                "n_llm_route_planner_residual_goal_contexts",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_residual_goal_context_count",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_llm_route_planner_residual_goal_context_source_refs": int(
            evaluation_manifest.get(
                "n_llm_route_planner_residual_goal_context_source_refs",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_residual_goal_context_source_ref_count",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_llm_route_planner_residual_goal_context_provenance_values": int(
            evaluation_manifest.get(
                "n_llm_route_planner_residual_goal_context_provenance_values",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_residual_goal_context_provenance_count",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_llm_route_planner_residual_goals_with_context": int(
            evaluation_manifest.get(
                "n_llm_route_planner_residual_goals_with_context",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_residual_goals_with_context_count",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_llm_route_planner_residual_goals_without_context": int(
            evaluation_manifest.get(
                "n_llm_route_planner_residual_goals_without_context",
                sum(
                    len(
                        _str_tuple(
                            row.get(
                                "llm_route_planner_residual_goals_without_context",
                                [],
                            )
                        )
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_rows_with_llm_route_planner_route_option_selection_brief": int(
            evaluation_manifest.get(
                "n_rows_with_llm_route_planner_route_option_selection_brief",
                sum(
                    1
                    for row in rows
                    if row.get(
                        "llm_route_planner_route_option_selection_brief_present"
                    )
                    is True
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selection_candidate_options": int(
            evaluation_manifest.get(
                "n_llm_route_planner_route_option_selection_candidate_options",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_route_option_selection_candidate_count",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selection_candidate_primitives": int(
            evaluation_manifest.get(
                "n_llm_route_planner_route_option_selection_candidate_primitives",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_route_option_selection_candidate_primitive_count",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selection_candidates_with_residual_goals": int(
            evaluation_manifest.get(
                "n_llm_route_planner_route_option_selection_candidates_with_residual_goals",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_route_option_selection_candidates_with_residual_goals",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selection_candidate_residual_goals": int(
            evaluation_manifest.get(
                "n_llm_route_planner_route_option_selection_candidate_residual_goals",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_route_option_selection_candidate_residual_goal_count",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selection_lower_bound_residual_goals": int(
            evaluation_manifest.get(
                "n_llm_route_planner_route_option_selection_lower_bound_residual_goals",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_route_option_selection_lower_bound_residual_goal_count",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_rows_with_llm_route_planner_route_option_selected_route_option": int(
            evaluation_manifest.get(
                "n_rows_with_llm_route_planner_route_option_selected_route_option",
                sum(
                    1
                    for row in rows
                    if str(
                        row.get(
                            "llm_route_planner_route_option_selected_route_option_id",
                            "",
                        )
                        or ""
                    ).strip()
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selection_minimal_delta_selected_residual_goals": int(
            evaluation_manifest.get(
                "n_llm_route_planner_route_option_selection_minimal_delta_selected_residual_goals",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_route_option_selection_minimal_delta_selected_residual_goal_count",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selected_matches_lower_bound": int(
            evaluation_manifest.get(
                "n_llm_route_planner_route_option_selected_matches_lower_bound",
                sum(
                    1
                    for row in rows
                    if str(
                        row.get(
                            "llm_route_planner_route_option_selected_route_option_id",
                            "",
                        )
                        or ""
                    ).strip()
                    and row.get(
                        "llm_route_planner_route_option_selected_matches_lower_bound"
                    )
                    is True
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selected_mismatches_lower_bound": int(
            evaluation_manifest.get(
                "n_llm_route_planner_route_option_selected_mismatches_lower_bound",
                sum(
                    1
                    for row in rows
                    if str(
                        row.get(
                            "llm_route_planner_route_option_selected_route_option_id",
                            "",
                        )
                        or ""
                    ).strip()
                    and str(
                        row.get(
                            "llm_route_planner_route_option_selection_lower_bound_selected_route_option_id",
                            "",
                        )
                        or ""
                    ).strip()
                    and row.get(
                        "llm_route_planner_route_option_selected_matches_lower_bound"
                    )
                    is not True
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selected_matches_minimal_delta": int(
            evaluation_manifest.get(
                "n_llm_route_planner_route_option_selected_matches_minimal_delta",
                sum(
                    1
                    for row in rows
                    if str(
                        row.get(
                            "llm_route_planner_route_option_selected_route_option_id",
                            "",
                        )
                        or ""
                    ).strip()
                    and row.get(
                        "llm_route_planner_route_option_selected_matches_minimal_delta"
                    )
                    is True
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selected_mismatches_minimal_delta": int(
            evaluation_manifest.get(
                "n_llm_route_planner_route_option_selected_mismatches_minimal_delta",
                sum(
                    1
                    for row in rows
                    if str(
                        row.get(
                            "llm_route_planner_route_option_selected_route_option_id",
                            "",
                        )
                        or ""
                    ).strip()
                    and str(row.get("minimal_delta_selected_route_option_id", "") or "").strip()
                    and row.get(
                        "llm_route_planner_route_option_selected_matches_minimal_delta"
                    )
                    is not True
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta": int(
            evaluation_manifest.get(
                "n_llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta",
                sum(
                    1
                    for row in rows
                    if row.get(
                        "llm_route_planner_route_option_selection_brief_present"
                    )
                    is True
                    and row.get(
                        "llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta"
                    )
                    is True
                ),
            )
            or 0
        ),
        "n_llm_route_planner_route_option_selection_lower_bound_mismatches_minimal_delta": int(
            evaluation_manifest.get(
                "n_llm_route_planner_route_option_selection_lower_bound_mismatches_minimal_delta",
                sum(
                    1
                    for row in rows
                    if row.get(
                        "llm_route_planner_route_option_selection_brief_present"
                    )
                    is True
                    and row.get(
                        "llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta"
                    )
                    is not True
                ),
            )
            or 0
        ),
        "n_rows_with_llm_route_planner_route_adoption_status": sum(
            1
            for row in rows
            if str(row.get("llm_route_planner_route_adoption_status", "")).strip()
        ),
        "n_rows_ready_for_route_adoption": route_adoption_counts.get(
            "READY_FOR_STANDALONE_REPLAY",
            0,
        ),
        "n_rows_pending_refinement_before_route_adoption": route_adoption_counts.get(
            "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION",
            0,
        ),
        "n_rows_awaiting_llm_route_planner_response": route_adoption_counts.get(
            "AWAITING_LLM_ROUTE_PLANNER_RESPONSE",
            0,
        ),
        "n_rows_rejected_llm_route_plan": route_adoption_counts.get(
            "REJECTED_LLM_ROUTE_PLAN",
            0,
        ),
        "n_llm_route_adoption_blockers": sum(
            len(_str_tuple(row.get("llm_route_planner_route_adoption_blockers", [])))
            for row in rows
        ),
        "n_rows_with_llm_route_planner_route_adoption_preconditions": sum(
            1
            for row in rows
            if row.get(
                "llm_route_planner_route_adoption_precondition_present"
            )
            is True
        ),
        "n_rows_with_llm_route_planner_blocking_route_adoption_preconditions": sum(
            1
            for row in rows
            if row.get(
                "llm_route_planner_route_adoption_precondition_blocked_before_response"
            )
            is True
        ),
        "n_llm_route_planner_route_adoption_precondition_known_blockers": sum(
            len(
                _str_tuple(
                    row.get(
                        "llm_route_planner_route_adoption_precondition_known_blockers",
                        [],
                    )
                )
            )
            for row in rows
        ),
        "n_llm_route_planner_route_adoption_precondition_required_response_fields": sum(
            len(
                _str_tuple(
                    row.get(
                        "llm_route_planner_route_adoption_precondition_required_response_fields",
                        [],
                    )
                )
            )
            for row in rows
        ),
        "n_llm_route_planner_route_adoption_precondition_target_primitives": sum(
            len(
                _str_tuple(
                    row.get(
                        "llm_route_planner_route_adoption_precondition_target_primitives",
                        [],
                    )
                )
            )
            for row in rows
        ),
        "llm_route_planner_route_adoption_precondition_known_blockers": (
            _evaluation_route_adoption_precondition_values_from_rows(
                rows,
                "llm_route_planner_route_adoption_precondition_known_blockers",
            )
        ),
        "llm_route_planner_route_adoption_precondition_required_response_fields": (
            _evaluation_route_adoption_precondition_values_from_rows(
                rows,
                "llm_route_planner_route_adoption_precondition_required_response_fields",
            )
        ),
        "llm_route_planner_route_adoption_precondition_target_primitives": (
            _evaluation_route_adoption_precondition_values_from_rows(
                rows,
                "llm_route_planner_route_adoption_precondition_target_primitives",
            )
        ),
        "llm_route_adoption_blockers": _evaluation_route_adoption_blockers_from_rows(
            rows
        ),
        "llm_route_adoption_blocker_counts": dict(route_adoption_blocker_counts),
        "llm_route_adoption_status_counts": dict(route_adoption_counts),
        "evaluation_by_llm_route_adoption_blocker": route_adoption_blocker_summary,
        "llm_route_planner_provider_usage_summary": _dict_value(
            evaluation_manifest,
            "llm_route_planner_provider_usage_summary",
        ),
        "n_rows_with_llm_route_planner_provider_usage": int(
            evaluation_manifest.get(
                "n_rows_with_llm_route_planner_provider_usage",
                sum(
                    1
                    for row in rows
                    if row.get("llm_route_planner_has_provider_usage") is True
                ),
            )
            or 0
        ),
        "total_llm_route_planner_provider_input_tokens": int(
            evaluation_manifest.get(
                "total_llm_route_planner_provider_input_tokens",
                sum(
                    int(row.get("llm_route_planner_provider_input_tokens", 0) or 0)
                    for row in rows
                ),
            )
            or 0
        ),
        "total_llm_route_planner_provider_output_tokens": int(
            evaluation_manifest.get(
                "total_llm_route_planner_provider_output_tokens",
                sum(
                    int(row.get("llm_route_planner_provider_output_tokens", 0) or 0)
                    for row in rows
                ),
            )
            or 0
        ),
        "total_llm_route_planner_provider_cache_creation_input_tokens": int(
            evaluation_manifest.get(
                "total_llm_route_planner_provider_cache_creation_input_tokens",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_provider_cache_creation_input_tokens",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "total_llm_route_planner_provider_cache_read_input_tokens": int(
            evaluation_manifest.get(
                "total_llm_route_planner_provider_cache_read_input_tokens",
                sum(
                    int(
                        row.get(
                            "llm_route_planner_provider_cache_read_input_tokens",
                            0,
                        )
                        or 0
                    )
                    for row in rows
                ),
            )
            or 0
        ),
        "total_llm_route_planner_provider_total_tokens": int(
            evaluation_manifest.get(
                "total_llm_route_planner_provider_total_tokens",
                sum(
                    int(row.get("llm_route_planner_provider_total_tokens", 0) or 0)
                    for row in rows
                ),
            )
            or 0
        ),
        "n_rows_with_quality_controls": sum(
            1 for row in rows if _quality_controls_from_evaluation_row(row)
        ),
        "n_quality_control_fields": sum(
            len(_quality_controls_from_evaluation_row(row)) for row in rows
        ),
        "quality_control_fields": _evaluation_quality_control_fields_from_rows(rows),
        "quality_control_resource_contract_ids": (
            _evaluation_quality_control_values_from_rows(
                rows,
                "resource_contract_ids",
            )
        ),
        "quality_control_response_validation_signals": (
            _evaluation_quality_control_values_from_rows(
                rows,
                "response_validation_signals",
            )
        ),
        "quality_control_stop_conditions": _evaluation_quality_control_values_from_rows(
            rows,
            "stop_conditions",
        ),
        "all_ok": bool(evaluation_manifest.get("all_ok", False)),
    }


def _contract_checks(bundle_dir: Path) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    contract_path = bundle_dir / "contract" / "formalization_gap_planner_portable_contract.json"
    llm_model_policy_path = bundle_dir / "contract" / "ai_statistician_llm_model_policy.json"
    llm_model_policy_report_path = (
        bundle_dir / "contract" / "ai_statistician_llm_model_policy.md"
    )
    schema_path = bundle_dir / "contract" / "library_aware_formalization_gap_plan.schema.json"
    portable_plan_row_schema_path = (
        bundle_dir / "contract" / "library_aware_formalization_gap_plan_row.schema.json"
    )
    schema_catalog_path = (
        bundle_dir / "contract" / "formalization_gap_planner_schema_catalog.json"
    )
    schema_catalog_schema_path = (
        bundle_dir / "contract" / "formalization_gap_planner_schema_catalog.schema.json"
    )
    publication_bundle_manifest_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_publication_bundle_manifest.schema.json"
    )
    adapter_schema_path = (
        bundle_dir / "contract" / "formalization_gap_planner_prover_adapter_response.schema.json"
    )
    adapter_packet_schema_path = (
        bundle_dir / "contract" / "formalization_gap_planner_prover_adapter_packet.schema.json"
    )
    response_validation_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_prover_adapter_response_validation_row.schema.json"
    )
    refinement_tool_response_schema_path = (
        bundle_dir / "contract" / "formalization_gap_planner_refinement_tool_response.schema.json"
    )
    refinement_work_item_schema_path = (
        bundle_dir / "contract" / "formalization_gap_planner_refinement_work_item.schema.json"
    )
    refinement_evidence_row_schema_path = (
        bundle_dir / "contract" / "formalization_gap_planner_refinement_evidence_row.schema.json"
    )
    interactive_session_row_schema_path = (
        bundle_dir / "contract" / "formalization_gap_planner_interactive_session_row.schema.json"
    )
    interactive_decision_policy_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_interactive_decision_policy_row.schema.json"
    )
    minimal_delta_decision_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_minimal_delta_decision_row.schema.json"
    )
    portable_plan_audit_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_portable_plan_audit_row.schema.json"
    )
    library_coverage_map_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_library_coverage_map_row.schema.json"
    )
    primitive_action_queue_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_primitive_action_queue_row.schema.json"
    )
    action_resource_plan_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_action_resource_plan_row.schema.json"
    )
    resource_request_queue_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_resource_request_queue_row.schema.json"
    )
    resource_response_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_resource_response.schema.json"
    )
    resource_response_ledger_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_resource_response_ledger_row.schema.json"
    )
    source_grounding_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_source_grounding_row.schema.json"
    )
    llm_route_planner_request_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_llm_route_planner_request.schema.json"
    )
    llm_route_planner_route_planning_brief_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_llm_route_planner_route_planning_brief.schema.json"
    )
    llm_route_planner_response_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_llm_route_planner_response.schema.json"
    )
    llm_route_planner_response_payload_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_llm_route_planner_response_payload.schema.json"
    )
    llm_route_planner_response_payload_lean_legacy_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_llm_route_planner_response_payload_lean_legacy.schema.json"
    )
    llm_route_planner_response_payload_target_prover_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_llm_route_planner_response_payload_target_prover.schema.json"
    )
    llm_route_planner_response_payload_validation_manifest_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.schema.json"
    )
    llm_route_planner_response_payload_validation_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_row.schema.json"
    )
    llm_route_planner_manifest_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_llm_route_planner_manifest.schema.json"
    )
    llm_route_planner_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_llm_route_planner_row.schema.json"
    )
    llm_route_planner_model_tier_decision_ledger_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_llm_route_planner_model_tier_decision_ledger.schema.json"
    )
    route_adoption_blocker_taxonomy_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_route_adoption_blocker_taxonomy.schema.json"
    )
    route_adoption_blocker_taxonomy_manifest_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_route_adoption_blocker_taxonomy_manifest.schema.json"
    )
    route_adoption_blocker_taxonomy_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_route_adoption_blocker_taxonomy.json"
    )
    route_revision_overlay_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_route_revision_overlay_row.schema.json"
    )
    route_stability_audit_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_route_stability_audit_row.schema.json"
    )
    route_replan_handoff_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_route_replan_handoff_row.schema.json"
    )
    route_replan_handoff_audit_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_route_replan_handoff_audit_row.schema.json"
    )
    proof_state_triage_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_proof_state_triage_row.schema.json"
    )
    ablation_study_row_schema_path = (
        bundle_dir / "contract" / "formalization_gap_planner_ablation_study_row.schema.json"
    )
    route_alignment_edge_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_route_alignment_edge.schema.json"
    )
    benchmark_route_schema_path = (
        bundle_dir / "contract" / "formalization_gap_planner_benchmark_route.schema.json"
    )
    evaluation_row_schema_path = (
        bundle_dir / "contract" / "formalization_gap_planner_evaluation_row.schema.json"
    )
    adapter_registry_row_schema_path = (
        bundle_dir / "contract" / "formalization_gap_planner_adapter_registry_row.schema.json"
    )
    cross_prover_matrix_audit_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_cross_prover_matrix_audit_row.schema.json"
    )
    cross_prover_target_summary_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_cross_prover_target_summary.schema.json"
    )
    standalone_schema_path = (
        bundle_dir / "contract" / "formalization_gap_planner_standalone_input.schema.json"
    )
    llm_route_planner_seed_route_selection_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_llm_route_planner_seed_route_selection.schema.json"
    )
    target_intake_schema_path = (
        bundle_dir / "contract" / "formalization_gap_planner_target_intake.schema.json"
    )
    target_intake_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_target_intake_row.schema.json"
    )
    component_execution_plan_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_component_resource_execution_plan.schema.json"
    )
    component_resource_resource_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_component_resource_resource_row.schema.json"
    )
    component_resource_component_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_component_resource_component_row.schema.json"
    )
    component_resource_contract_row_schema_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_component_resource_contract_row.schema.json"
    )
    contract = _read_json_no_error(contract_path)
    schema = _read_json_no_error(schema_path)
    portable_plan_row_schema = _read_json_no_error(portable_plan_row_schema_path)
    schema_catalog = _read_json_no_error(schema_catalog_path)
    schema_catalog_schema = _read_json_no_error(schema_catalog_schema_path)
    publication_bundle_manifest_schema = _read_json_no_error(
        publication_bundle_manifest_schema_path
    )
    adapter_schema = _read_json_no_error(adapter_schema_path)
    adapter_packet_schema = _read_json_no_error(adapter_packet_schema_path)
    response_validation_row_schema = _read_json_no_error(
        response_validation_row_schema_path
    )
    refinement_tool_response_schema = _read_json_no_error(
        refinement_tool_response_schema_path
    )
    refinement_work_item_schema = _read_json_no_error(refinement_work_item_schema_path)
    refinement_evidence_row_schema = _read_json_no_error(
        refinement_evidence_row_schema_path
    )
    interactive_session_row_schema = _read_json_no_error(
        interactive_session_row_schema_path
    )
    interactive_decision_policy_row_schema = _read_json_no_error(
        interactive_decision_policy_row_schema_path
    )
    minimal_delta_decision_row_schema = _read_json_no_error(
        minimal_delta_decision_row_schema_path
    )
    portable_plan_audit_row_schema = _read_json_no_error(
        portable_plan_audit_row_schema_path
    )
    library_coverage_map_row_schema = _read_json_no_error(
        library_coverage_map_row_schema_path
    )
    primitive_action_queue_row_schema = _read_json_no_error(
        primitive_action_queue_row_schema_path
    )
    action_resource_plan_row_schema = _read_json_no_error(
        action_resource_plan_row_schema_path
    )
    resource_request_queue_row_schema = _read_json_no_error(
        resource_request_queue_row_schema_path
    )
    resource_response_schema = _read_json_no_error(resource_response_schema_path)
    resource_response_ledger_row_schema = _read_json_no_error(
        resource_response_ledger_row_schema_path
    )
    source_grounding_row_schema = _read_json_no_error(source_grounding_row_schema_path)
    llm_route_planner_request_schema = _read_json_no_error(
        llm_route_planner_request_schema_path
    )
    llm_route_planner_route_planning_brief_schema = _read_json_no_error(
        llm_route_planner_route_planning_brief_schema_path
    )
    llm_route_planner_response_schema = _read_json_no_error(
        llm_route_planner_response_schema_path
    )
    llm_route_planner_response_payload_schema = _read_json_no_error(
        llm_route_planner_response_payload_schema_path
    )
    llm_route_planner_response_payload_lean_legacy_schema = _read_json_no_error(
        llm_route_planner_response_payload_lean_legacy_schema_path
    )
    llm_route_planner_response_payload_target_prover_schema = _read_json_no_error(
        llm_route_planner_response_payload_target_prover_schema_path
    )
    llm_route_planner_response_payload_validation_manifest_schema = (
        _read_json_no_error(
            llm_route_planner_response_payload_validation_manifest_schema_path
        )
    )
    llm_route_planner_response_payload_validation_row_schema = _read_json_no_error(
        llm_route_planner_response_payload_validation_row_schema_path
    )
    llm_route_planner_manifest_schema = _read_json_no_error(
        llm_route_planner_manifest_schema_path
    )
    llm_route_planner_row_schema = _read_json_no_error(
        llm_route_planner_row_schema_path
    )
    llm_route_planner_model_tier_decision_ledger_schema = _read_json_no_error(
        llm_route_planner_model_tier_decision_ledger_schema_path
    )
    route_adoption_blocker_taxonomy_schema = _read_json_no_error(
        route_adoption_blocker_taxonomy_schema_path
    )
    route_adoption_blocker_taxonomy_manifest_schema = _read_json_no_error(
        route_adoption_blocker_taxonomy_manifest_schema_path
    )
    route_adoption_blocker_taxonomy = _read_json_no_error(
        route_adoption_blocker_taxonomy_path
    )
    route_adoption_blocker_taxonomy_errors = (
        validate_route_adoption_blocker_taxonomy_payload(
            route_adoption_blocker_taxonomy
        )
    )
    embedded_route_adoption_blocker_taxonomy_errors = (
        validate_route_adoption_blocker_taxonomy_payload(
            contract.get("route_adoption_blocker_taxonomy_contract", {})
            if isinstance(
                contract.get("route_adoption_blocker_taxonomy_contract", {}),
                dict,
            )
            else {}
        )
    )
    embedded_route_adoption_blocker_taxonomy_manifest_schema = contract.get(
        "route_adoption_blocker_taxonomy_manifest_schema_contract",
        {},
    )
    embedded_route_adoption_blocker_taxonomy_manifest_schema = (
        embedded_route_adoption_blocker_taxonomy_manifest_schema
        if isinstance(embedded_route_adoption_blocker_taxonomy_manifest_schema, dict)
        else {}
    )
    embedded_seed_route_selection_contract = contract.get(
        "llm_route_planner_seed_route_selection_contract",
        {},
    )
    embedded_seed_route_selection_contract = (
        embedded_seed_route_selection_contract
        if isinstance(embedded_seed_route_selection_contract, dict)
        else {}
    )
    row_schema_properties = llm_route_planner_row_schema.get("properties", {})
    row_schema_properties = (
        row_schema_properties if isinstance(row_schema_properties, dict) else {}
    )
    row_schema_route_adoption_status = row_schema_properties.get(
        "route_adoption_status",
        {},
    )
    row_schema_route_adoption_status = (
        row_schema_route_adoption_status
        if isinstance(row_schema_route_adoption_status, dict)
        else {}
    )
    row_schema_route_adoption_blockers = row_schema_properties.get(
        "route_adoption_blockers",
        {},
    )
    row_schema_route_adoption_blockers = (
        row_schema_route_adoption_blockers
        if isinstance(row_schema_route_adoption_blockers, dict)
        else {}
    )
    row_schema_route_adoption_blocker_items = (
        row_schema_route_adoption_blockers.get("items", {})
    )
    row_schema_route_adoption_blocker_items = (
        row_schema_route_adoption_blocker_items
        if isinstance(row_schema_route_adoption_blocker_items, dict)
        else {}
    )
    taxonomy_status_values = _str_tuple(
        route_adoption_blocker_taxonomy.get("status_values", [])
    )
    taxonomy_blocker_values = _str_tuple(
        route_adoption_blocker_taxonomy.get("blocker_values", [])
    )
    route_revision_overlay_row_schema = _read_json_no_error(
        route_revision_overlay_row_schema_path
    )
    route_stability_audit_row_schema = _read_json_no_error(
        route_stability_audit_row_schema_path
    )
    route_replan_handoff_row_schema = _read_json_no_error(
        route_replan_handoff_row_schema_path
    )
    route_replan_handoff_audit_row_schema = _read_json_no_error(
        route_replan_handoff_audit_row_schema_path
    )
    proof_state_triage_row_schema = _read_json_no_error(
        proof_state_triage_row_schema_path
    )
    ablation_study_row_schema = _read_json_no_error(ablation_study_row_schema_path)
    route_alignment_edge_schema = _read_json_no_error(route_alignment_edge_schema_path)
    benchmark_route_schema = _read_json_no_error(benchmark_route_schema_path)
    evaluation_row_schema = _read_json_no_error(evaluation_row_schema_path)
    adapter_registry_row_schema = _read_json_no_error(
        adapter_registry_row_schema_path
    )
    cross_prover_matrix_audit_row_schema = _read_json_no_error(
        cross_prover_matrix_audit_row_schema_path
    )
    cross_prover_target_summary_schema = _read_json_no_error(
        cross_prover_target_summary_schema_path
    )
    standalone_schema = _read_json_no_error(standalone_schema_path)
    llm_route_planner_seed_route_selection_schema = _read_json_no_error(
        llm_route_planner_seed_route_selection_schema_path
    )
    target_intake_schema = _read_json_no_error(target_intake_schema_path)
    target_intake_row_schema = _read_json_no_error(target_intake_row_schema_path)
    component_execution_plan_schema = _read_json_no_error(
        component_execution_plan_schema_path
    )
    component_resource_resource_row_schema = _read_json_no_error(
        component_resource_resource_row_schema_path
    )
    component_resource_component_row_schema = _read_json_no_error(
        component_resource_component_row_schema_path
    )
    component_resource_contract_row_schema = _read_json_no_error(
        component_resource_contract_row_schema_path
    )
    llm_model_policy = _read_json_no_error(llm_model_policy_path)
    llm_model_policy_source_evidence = (
        llm_model_policy.get("source_evidence", {})
        if isinstance(llm_model_policy.get("source_evidence", {}), dict)
        else {}
    )
    llm_model_selection_policy = (
        llm_model_policy.get("claude_model_selection", {})
        if isinstance(llm_model_policy.get("claude_model_selection", {}), dict)
        else {}
    )
    llm_model_selection_source_evidence = (
        llm_model_selection_policy.get("source_evidence", {})
        if isinstance(llm_model_selection_policy.get("source_evidence", {}), dict)
        else {}
    )
    llm_models_overview_url = str(
        llm_model_policy_source_evidence.get("models_overview_url", "")
    )
    llm_model_ids_and_versioning_url = str(
        llm_model_policy_source_evidence.get(
            "model_ids_and_versioning_url",
            "",
        )
    )
    llm_model_id_versioning_policy = str(
        llm_model_selection_policy.get("model_id_versioning")
        or ANTHROPIC_MODEL_ID_VERSIONING_POLICY
    )
    llm_models_by_tier = (
        llm_model_policy.get("latest_claude_models_by_tier", {})
        if isinstance(llm_model_policy.get("latest_claude_models_by_tier", {}), dict)
        else {}
    )
    llm_source_evidence_models_by_tier = (
        llm_model_policy_source_evidence.get("verified_latest_cost_tier_api_ids", {})
        if isinstance(
            llm_model_policy_source_evidence.get(
                "verified_latest_cost_tier_api_ids",
                {},
            ),
            dict,
        )
        else {}
    )
    llm_selection_models_by_tier = (
        llm_model_selection_policy.get("models_by_tier", {})
        if isinstance(llm_model_selection_policy.get("models_by_tier", {}), dict)
        else {}
    )
    llm_selection_source_evidence_models_by_tier = (
        llm_model_selection_source_evidence.get(
            "verified_latest_cost_tier_api_ids",
            {},
        )
        if isinstance(
            llm_model_selection_source_evidence.get(
                "verified_latest_cost_tier_api_ids",
                {},
            ),
            dict,
        )
        else {}
    )
    llm_outside_cost_tier_models = (
        llm_model_policy.get("latest_claude_family_models_outside_cost_tiers", {})
        if isinstance(
            llm_model_policy.get(
                "latest_claude_family_models_outside_cost_tiers",
                {},
            ),
            dict,
        )
        else {}
    )
    llm_api_aliases_by_tier = (
        llm_model_policy.get("latest_claude_api_aliases_by_tier", {})
        if isinstance(
            llm_model_policy.get("latest_claude_api_aliases_by_tier", {}),
            dict,
        )
        else {}
    )
    llm_source_evidence_api_aliases_by_tier = (
        llm_model_policy_source_evidence.get("verified_api_aliases_by_tier", {})
        if isinstance(
            llm_model_policy_source_evidence.get(
                "verified_api_aliases_by_tier",
                {},
            ),
            dict,
        )
        else {}
    )
    llm_selection_api_aliases_by_tier = (
        llm_model_selection_policy.get("api_aliases_by_tier", {})
        if isinstance(
            llm_model_selection_policy.get("api_aliases_by_tier", {}),
            dict,
        )
        else {}
    )
    supported_llm_providers = set(
        _str_tuple(llm_model_policy.get("supported_live_generator_providers", []))
    )
    prohibited_llm_providers = set(
        _str_tuple(llm_model_policy.get("prohibited_generator_providers", []))
    )
    request_time_resolution_policy = (
        llm_model_policy.get("request_time_model_resolution_policy", {})
        if isinstance(
            llm_model_policy.get("request_time_model_resolution_policy", {}),
            dict,
        )
        else {}
    )
    worker_default_tiers = (
        request_time_resolution_policy.get("worker_default_tiers", {})
        if isinstance(
            request_time_resolution_policy.get("worker_default_tiers", {}),
            dict,
        )
        else {}
    )
    interactive_route_contract = (
        contract.get("interactive_route_synthesis_contract", {})
        if isinstance(contract.get("interactive_route_synthesis_contract", {}), dict)
        else {}
    )
    evaluation_protocol_contract = (
        contract.get("evaluation_protocol", {})
        if isinstance(contract.get("evaluation_protocol", {}), dict)
        else {}
    )
    interactive_route_loop = _str_tuple(interactive_route_contract.get("loop", []))
    interactive_route_stage_aliases = (
        interactive_route_contract.get("legacy_stage_aliases", {})
        if isinstance(interactive_route_contract.get("legacy_stage_aliases", {}), dict)
        else {}
    )
    evaluation_primary_metrics = _str_tuple(
        evaluation_protocol_contract.get("primary_metrics", [])
    )
    evaluation_metric_aliases = (
        evaluation_protocol_contract.get("legacy_metric_aliases", {})
        if isinstance(evaluation_protocol_contract.get("legacy_metric_aliases", {}), dict)
        else {}
    )
    evaluation_ablations = _str_tuple(
        evaluation_protocol_contract.get("ablations", [])
    )
    evaluation_ablation_aliases = (
        evaluation_protocol_contract.get("legacy_ablation_aliases", {})
        if isinstance(evaluation_protocol_contract.get("legacy_ablation_aliases", {}), dict)
        else {}
    )
    schema_catalog_entries = [
        row
        for row in schema_catalog.get("schema_entries", [])
        if isinstance(row, dict)
    ]
    schema_catalog_entries_by_name = {
        str(row.get("artifact_name", "")): row for row in schema_catalog_entries
    }
    schema_catalog_entry_names = {
        str(row.get("artifact_name", "")) for row in schema_catalog_entries
    }
    schema_catalog_entry_paths_ok = _schema_catalog_entry_paths_exist(
        bundle_dir,
        tuple(schema_catalog_entries),
    )
    schema_catalog_contract_errors = validate_schema_catalog_payload(
        schema_catalog,
        bundle_dir=bundle_dir,
    )
    return [
        _check(
            "portable_contract_file",
            "contract",
            "contract file exists",
            str(contract_path.exists()),
            contract_path.exists(),
        ),
        _check(
            "portable_contract_schema_id",
            "contract",
            PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
            str(contract.get("schema_id", "")),
            contract.get("schema_id") == PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
        ),
        _check(
            "llm_model_policy_file",
            "contract",
            "LLM model policy file exists",
            str(llm_model_policy_path.exists()),
            llm_model_policy_path.exists(),
        ),
        _check(
            "llm_model_policy_report_file",
            "contract",
            "LLM model policy markdown exists",
            str(llm_model_policy_report_path.exists()),
            llm_model_policy_report_path.exists(),
        ),
        _check(
            "llm_model_policy_component",
            "contract",
            LLM_MODEL_POLICY_COMPONENT_NAME,
            str(llm_model_policy.get("component_name", "")),
            llm_model_policy.get("component_name") == LLM_MODEL_POLICY_COMPONENT_NAME,
        ),
        _check(
            "llm_model_policy_default_provider",
            "contract",
            DEFAULT_LIVE_GENERATOR_PROVIDER,
            str(llm_model_policy.get("default_live_generator_provider", "")),
            llm_model_policy.get("default_live_generator_provider")
            == DEFAULT_LIVE_GENERATOR_PROVIDER
            == "anthropic",
        ),
        _check(
            "llm_model_policy_supported_providers",
            "contract",
            "anthropic,openai,static",
            ",".join(sorted(supported_llm_providers)),
            supported_llm_providers == {"anthropic", "openai", "static"},
        ),
        _check(
            "llm_model_policy_rejects_codex",
            "contract",
            "agent-style CLI providers excluded from supported providers",
            ",".join(sorted(supported_llm_providers | prohibited_llm_providers)),
            set(PROHIBITED_AGENT_GENERATOR_PROVIDERS).issubset(
                prohibited_llm_providers
            )
            and not set(PROHIBITED_AGENT_GENERATOR_PROVIDERS).intersection(
                supported_llm_providers
            ),
        ),
        _check(
            "llm_model_policy_latest_claude_tiers",
            "contract",
            "latest Claude Haiku/Sonnet/Opus tier ids",
            json.dumps(llm_models_by_tier, sort_keys=True),
            llm_models_by_tier
            == {
                "haiku": DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
                "sonnet": DEFAULT_CLAUDE_SONNET_GENERATOR_MODEL,
                "opus": DEFAULT_CLAUDE_OPUS_GENERATOR_MODEL,
            },
        ),
        _check(
            "llm_model_policy_latest_claude_api_aliases",
            "contract",
            "latest Claude Haiku/Sonnet/Opus API aliases",
            json.dumps(llm_api_aliases_by_tier, sort_keys=True),
            llm_api_aliases_by_tier
            == DEFAULT_CLAUDE_GENERATOR_MODEL_ALIASES_BY_TIER
            and "Runtime calls use latest_claude_models_by_tier API IDs"
            in str(llm_model_policy.get("runtime_model_id_policy", "")),
        ),
        _check(
            "llm_model_policy_source_checked_date",
            "contract",
            ANTHROPIC_MODEL_SOURCE_CHECKED_DATE,
            str(llm_model_policy.get("source_checked_date", "")),
            llm_model_policy.get("source_checked_date")
            == ANTHROPIC_MODEL_SOURCE_CHECKED_DATE,
        ),
        _check(
            "llm_model_policy_embedded_source_evidence_consistent",
            "contract",
            "embedded Claude source evidence agrees with top-level tier policy",
            json.dumps(
                {
                    "top_level_models": llm_models_by_tier,
                    "source_evidence_models": llm_source_evidence_models_by_tier,
                    "selection_models": llm_selection_models_by_tier,
                    "selection_source_evidence_models": (
                        llm_selection_source_evidence_models_by_tier
                    ),
                    "top_level_aliases": llm_api_aliases_by_tier,
                    "source_evidence_aliases": (
                        llm_source_evidence_api_aliases_by_tier
                    ),
                    "selection_aliases": llm_selection_api_aliases_by_tier,
                },
                sort_keys=True,
            ),
            llm_source_evidence_models_by_tier == llm_models_by_tier
            and llm_selection_models_by_tier == llm_models_by_tier
            and llm_selection_source_evidence_models_by_tier == llm_models_by_tier
            and llm_api_aliases_by_tier
            == DEFAULT_CLAUDE_GENERATOR_MODEL_ALIASES_BY_TIER
            and llm_source_evidence_api_aliases_by_tier
            == DEFAULT_CLAUDE_GENERATOR_MODEL_ALIASES_BY_TIER
            and llm_selection_api_aliases_by_tier
            == DEFAULT_CLAUDE_GENERATOR_MODEL_ALIASES_BY_TIER
            and str(llm_model_selection_policy.get("source_checked_date", ""))
            == ANTHROPIC_MODEL_SOURCE_CHECKED_DATE,
        ),
        _check(
            "llm_model_policy_official_source_urls",
            "contract",
            "official Anthropic Claude model docs URLs",
            json.dumps(
                {
                    "models_overview_url": llm_models_overview_url,
                    "model_ids_and_versioning_url": (
                        llm_model_ids_and_versioning_url
                    ),
                },
                sort_keys=True,
            ),
            llm_models_overview_url == ANTHROPIC_MODELS_OVERVIEW_URL
            and llm_model_ids_and_versioning_url
            == ANTHROPIC_MODEL_IDS_AND_VERSIONING_URL
            and str(ANTHROPIC_MODELS_OVERVIEW_URL).startswith(
                "https://docs.anthropic.com/"
            )
            and str(ANTHROPIC_MODEL_IDS_AND_VERSIONING_URL).startswith(
                "https://docs.anthropic.com/"
            ),
        ),
        _check(
            "llm_model_policy_pinned_snapshot_versioning",
            "contract",
            "Claude 4.6+ model IDs are pinned snapshots, not evergreen aliases",
            llm_model_id_versioning_policy,
            "pinned snapshot" in llm_model_id_versioning_policy.lower()
            and "not evergreen" in llm_model_id_versioning_policy.lower(),
        ),
        _check(
            "llm_model_policy_outside_cost_tier_models",
            "contract",
            "Claude family models outside Opus/Sonnet/Haiku tier ids",
            json.dumps(llm_outside_cost_tier_models, sort_keys=True),
            llm_outside_cost_tier_models == CLAUDE_FAMILY_MODELS_OUTSIDE_COST_TIERS
            and "not automatic AI Statistician cost tiers"
            in str(llm_model_policy.get("outside_cost_tier_policy", "")),
        ),
        _check(
            "llm_model_policy_request_time_resolution",
            "contract",
            "empty model configs resolve by provider/model_tier at request time",
            json.dumps(request_time_resolution_policy, sort_keys=True),
            "request is built"
            in str(
                request_time_resolution_policy.get(
                    "empty_model_resolution",
                    "",
                )
            )
            and "Tier-specific Claude environment variables"
            in str(
                request_time_resolution_policy.get(
                    "tier_specific_env_overrides",
                    "",
                )
            )
            and worker_default_tiers.get("TheoryIntake") == "haiku"
            and worker_default_tiers.get("SimulationEngineer") == "haiku"
            and worker_default_tiers.get("AlgorithmEngineer") == "haiku"
            and worker_default_tiers.get("CriticEvaluator") == "haiku"
            and worker_default_tiers.get("ArchitectCoordinator") == "sonnet"
            and worker_default_tiers.get("TheoryDeveloper") == "sonnet"
            and worker_default_tiers.get("FormalizerProofEngineer") == "sonnet"
            and worker_default_tiers.get(
                "formalization_gap_planner_route_synthesis"
            )
            == "auto",
        ),
        _check(
            "portable_contract_has_llm_model_policy_contract",
            "contract",
            "llm_model_policy_contract",
            str("llm_model_policy_contract" in contract),
            "llm_model_policy_contract" in contract,
        ),
        _check(
            "portable_contract_target_prover_neutral_terms",
            "contract",
            "target-prover-neutral route/evaluation terms with Lean legacy aliases",
            json.dumps(
                {
                    "loop": interactive_route_loop,
                    "metrics": evaluation_primary_metrics,
                    "ablations": evaluation_ablations,
                    "stage_aliases": interactive_route_stage_aliases,
                    "metric_aliases": evaluation_metric_aliases,
                    "ablation_aliases": evaluation_ablation_aliases,
                },
                sort_keys=True,
            ),
            "formal_library_coverage_mapping" in interactive_route_loop
            and "lean_coverage_mapping" not in interactive_route_loop
            and interactive_route_stage_aliases.get("lean_coverage_mapping")
            == "formal_library_coverage_mapping"
            and "target_prover_effort_new_declarations"
            in evaluation_primary_metrics
            and "target_prover_effort_failed_attempts" in evaluation_primary_metrics
            and "lean_effort_new_declarations" not in evaluation_primary_metrics
            and evaluation_metric_aliases.get("lean_effort_new_declarations")
            == "target_prover_effort_new_declarations"
            and "no_formal_grounding" in evaluation_ablations
            and "no_proof_state_feedback" in evaluation_ablations
            and "no_lean_rag" not in evaluation_ablations
            and evaluation_ablation_aliases.get("no_lean_rag")
            == "no_formal_grounding",
        ),
        _check(
            "portable_plan_row_schema_file",
            "contract",
            "portable gap-plan row schema exists",
            str(portable_plan_row_schema_path.exists()),
            portable_plan_row_schema_path.exists(),
        ),
        _check(
            "portable_plan_row_schema_id",
            "contract",
            PORTABLE_FORMALIZATION_GAP_PLAN_ROW_SCHEMA_ID,
            str(portable_plan_row_schema.get("$id", "")),
            portable_plan_row_schema.get("$id")
            == PORTABLE_FORMALIZATION_GAP_PLAN_ROW_SCHEMA_ID,
        ),
        _check(
            "schema_catalog_schema_file",
            "contract",
            "schema catalog JSON schema exists",
            str(schema_catalog_schema_path.exists()),
            schema_catalog_schema_path.exists(),
        ),
        _check(
            "schema_catalog_schema_id",
            "contract",
            FORMALIZATION_GAP_PLANNER_SCHEMA_CATALOG_SCHEMA_ID,
            str(schema_catalog_schema.get("$id", "")),
            schema_catalog_schema.get("$id")
            == FORMALIZATION_GAP_PLANNER_SCHEMA_CATALOG_SCHEMA_ID,
        ),
        _check(
            "publication_bundle_manifest_schema_file",
            "contract",
            "publication bundle manifest JSON schema exists",
            str(publication_bundle_manifest_schema_path.exists()),
            publication_bundle_manifest_schema_path.exists(),
        ),
        _check(
            "publication_bundle_manifest_schema_id",
            "contract",
            FORMALIZATION_GAP_PLANNER_PUBLICATION_BUNDLE_MANIFEST_SCHEMA_ID,
            str(publication_bundle_manifest_schema.get("$id", "")),
            publication_bundle_manifest_schema.get("$id")
            == FORMALIZATION_GAP_PLANNER_PUBLICATION_BUNDLE_MANIFEST_SCHEMA_ID,
        ),
        _check(
            "publication_bundle_manifest_schema_matches_contract",
            "contract",
            publication_bundle_manifest_json_schema().get("$id", ""),
            str(publication_bundle_manifest_schema.get("$id", "")),
            publication_bundle_manifest_schema.get("$id")
            == publication_bundle_manifest_json_schema().get("$id"),
        ),
        _check(
            "schema_catalog_file",
            "contract",
            "schema catalog exists",
            str(schema_catalog_path.exists()),
            schema_catalog_path.exists(),
        ),
        _check(
            "schema_catalog_component",
            "contract",
            SCHEMA_CATALOG_COMPONENT_NAME,
            str(schema_catalog.get("component_name", "")),
            schema_catalog.get("component_name") == SCHEMA_CATALOG_COMPONENT_NAME,
        ),
        _check(
            "schema_catalog_payload_schema_id",
            "contract",
            FORMALIZATION_GAP_PLANNER_SCHEMA_CATALOG_SCHEMA_ID,
            str(schema_catalog.get("schema_id", "")),
            schema_catalog.get("schema_id")
            == FORMALIZATION_GAP_PLANNER_SCHEMA_CATALOG_SCHEMA_ID,
        ),
        _check(
            "schema_catalog_entries_present",
            "contract",
            "catalog includes reusable schema and contract entries",
            str(len(schema_catalog_entries)),
            len(schema_catalog_entries) >= 30,
        ),
        _check(
            "schema_catalog_required_entries",
            "contract",
            "portable_contract, portable_schema, target_intake_row_schema, llm route planner schemas, portable_plan_row_schema",
            ",".join(sorted(schema_catalog_entry_names)),
            {
                "portable_contract",
                "portable_schema",
                "publication_bundle_manifest_schema",
                "target_intake_row_schema",
                "llm_route_planner_request_schema",
                "llm_route_planner_route_planning_brief_schema",
                "llm_route_planner_response_schema",
                "llm_route_planner_response_payload_schema",
                "llm_route_planner_response_payload_lean_legacy_schema",
                "llm_route_planner_response_payload_target_prover_schema",
                "llm_route_planner_response_payload_validation_manifest_schema",
                "llm_route_planner_response_payload_validation_row_schema",
                "llm_route_planner_row_schema",
                "route_adoption_blocker_taxonomy_schema",
                "route_adoption_blocker_taxonomy_manifest_schema",
                "route_adoption_blocker_taxonomy_contract",
                "llm_route_planner_seed_route_selection_schema",
                "portable_plan_row_schema",
            }.issubset(schema_catalog_entry_names),
        ),
        _check(
            "schema_catalog_lean_legacy_payload_schema_targets",
            "contract",
            "lean4",
            ",".join(
                _str_tuple(
                    schema_catalog_entries_by_name.get(
                        "llm_route_planner_response_payload_lean_legacy_schema",
                        {},
                    ).get("target_prover_families", [])
                )
            ),
            _str_tuple(
                schema_catalog_entries_by_name.get(
                    "llm_route_planner_response_payload_lean_legacy_schema",
                    {},
                ).get("target_prover_families", [])
            )
            == ("lean4",),
        ),
        _check(
            "schema_catalog_target_prover_payload_schema_targets",
            "contract",
            "rocq,isabelle,agda",
            ",".join(
                _str_tuple(
                    schema_catalog_entries_by_name.get(
                        "llm_route_planner_response_payload_target_prover_schema",
                        {},
                    ).get("target_prover_families", [])
                )
            ),
            _str_tuple(
                schema_catalog_entries_by_name.get(
                    "llm_route_planner_response_payload_target_prover_schema",
                    {},
                ).get("target_prover_families", [])
            )
            == ("rocq", "isabelle", "agda"),
        ),
        _check(
            "schema_catalog_missing_schema_ids",
            "contract",
            "0",
            str(schema_catalog.get("n_missing_schema_ids", "")),
            schema_catalog.get("n_missing_schema_ids") == 0,
        ),
        _check(
            "schema_catalog_missing_schema_files",
            "contract",
            "0",
            str(schema_catalog.get("n_missing_schema_files", "")),
            schema_catalog.get("n_missing_schema_files") == 0,
        ),
        _check(
            "schema_catalog_entry_paths_resolve",
            "contract",
            "all catalog relative paths exist inside bundle",
            str(schema_catalog_entry_paths_ok),
            schema_catalog_entry_paths_ok,
        ),
        _check(
            "schema_catalog_contract_valid",
            "contract",
            "schema catalog payload validates against public contract",
            "; ".join(schema_catalog_contract_errors)
            if schema_catalog_contract_errors
            else "valid",
            not schema_catalog_contract_errors,
            errors=schema_catalog_contract_errors,
        ),
        _check(
            "schema_catalog_all_ok",
            "contract",
            "all_ok true",
            str(schema_catalog.get("all_ok", "")),
            bool(schema_catalog.get("all_ok", False)),
        ),
        _check(
            "schema_catalog_boundary",
            "contract",
            "not theorem proof evidence",
            str(schema_catalog.get("proof_evidence_boundary", ""))[:120],
            "not theorem proof evidence"
            in str(schema_catalog.get("proof_evidence_boundary", "")),
        ),
        _check(
            "portable_contract_has_work_packet_contract",
            "contract",
            "portable_work_packet_contract",
            str("portable_work_packet_contract" in contract),
            "portable_work_packet_contract" in contract,
        ),
        _check(
            "portable_contract_has_schema_catalog_contract",
            "contract",
            "schema_catalog_contract",
            str("schema_catalog_contract" in contract),
            "schema_catalog_contract" in contract,
        ),
        _check(
            "portable_contract_has_prover_adapter_contract",
            "contract",
            "prover_adapter_response_contract",
            str("prover_adapter_response_contract" in contract),
            "prover_adapter_response_contract" in contract,
        ),
        _check(
            "portable_contract_has_prover_adapter_packet_contract",
            "contract",
            "prover_adapter_packet_contract",
            str("prover_adapter_packet_contract" in contract),
            "prover_adapter_packet_contract" in contract,
        ),
        _check(
            "portable_contract_has_prover_adapter_response_validation_row_contract",
            "contract",
            "prover_adapter_response_validation_row_contract",
            str("prover_adapter_response_validation_row_contract" in contract),
            "prover_adapter_response_validation_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_refinement_tool_response_contract",
            "contract",
            "refinement_tool_response_contract",
            str("refinement_tool_response_contract" in contract),
            "refinement_tool_response_contract" in contract,
        ),
        _check(
            "portable_contract_has_refinement_work_item_contract",
            "contract",
            "refinement_work_item_contract",
            str("refinement_work_item_contract" in contract),
            "refinement_work_item_contract" in contract,
        ),
        _check(
            "portable_contract_has_refinement_evidence_row_contract",
            "contract",
            "refinement_evidence_row_contract",
            str("refinement_evidence_row_contract" in contract),
            "refinement_evidence_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_interactive_session_row_contract",
            "contract",
            "interactive_session_row_contract",
            str("interactive_session_row_contract" in contract),
            "interactive_session_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_interactive_decision_policy_row_contract",
            "contract",
            "interactive_decision_policy_row_contract",
            str("interactive_decision_policy_row_contract" in contract),
            "interactive_decision_policy_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_minimal_delta_decision_row_contract",
            "contract",
            "minimal_delta_decision_row_contract",
            str("minimal_delta_decision_row_contract" in contract),
            "minimal_delta_decision_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_portable_plan_audit_row_contract",
            "contract",
            "portable_plan_audit_row_contract",
            str("portable_plan_audit_row_contract" in contract),
            "portable_plan_audit_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_library_coverage_map_row_contract",
            "contract",
            "library_coverage_map_row_contract",
            str("library_coverage_map_row_contract" in contract),
            "library_coverage_map_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_primitive_action_queue_row_contract",
            "contract",
            "primitive_action_queue_row_contract",
            str("primitive_action_queue_row_contract" in contract),
            "primitive_action_queue_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_action_resource_plan_row_contract",
            "contract",
            "action_resource_plan_row_contract",
            str("action_resource_plan_row_contract" in contract),
            "action_resource_plan_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_resource_request_queue_row_contract",
            "contract",
            "resource_request_queue_row_contract",
            str("resource_request_queue_row_contract" in contract),
            "resource_request_queue_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_resource_response_contract",
            "contract",
            "resource_response_contract",
            str("resource_response_contract" in contract),
            "resource_response_contract" in contract,
        ),
        _check(
            "portable_contract_has_resource_response_ledger_row_contract",
            "contract",
            "resource_response_ledger_row_contract",
            str("resource_response_ledger_row_contract" in contract),
            "resource_response_ledger_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_source_grounding_row_contract",
            "contract",
            "source_grounding_row_contract",
            str("source_grounding_row_contract" in contract),
            "source_grounding_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_llm_route_planner_request_contract",
            "contract",
            "llm_route_planner_request_contract",
            str("llm_route_planner_request_contract" in contract),
            "llm_route_planner_request_contract" in contract,
        ),
        _check(
            "portable_contract_has_llm_route_planner_response_contract",
            "contract",
            "llm_route_planner_response_contract",
            str("llm_route_planner_response_contract" in contract),
            "llm_route_planner_response_contract" in contract,
        ),
        _check(
            "portable_contract_has_llm_route_planner_row_contract",
            "contract",
            "llm_route_planner_row_contract",
            str("llm_route_planner_row_contract" in contract),
            "llm_route_planner_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_route_revision_overlay_row_contract",
            "contract",
            "route_revision_overlay_row_contract",
            str("route_revision_overlay_row_contract" in contract),
            "route_revision_overlay_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_route_stability_audit_row_contract",
            "contract",
            "route_stability_audit_row_contract",
            str("route_stability_audit_row_contract" in contract),
            "route_stability_audit_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_route_replan_handoff_row_contract",
            "contract",
            "route_replan_handoff_row_contract",
            str("route_replan_handoff_row_contract" in contract),
            "route_replan_handoff_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_route_replan_handoff_audit_row_contract",
            "contract",
            "route_replan_handoff_audit_row_contract",
            str("route_replan_handoff_audit_row_contract" in contract),
            "route_replan_handoff_audit_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_proof_state_triage_row_contract",
            "contract",
            "proof_state_triage_row_contract",
            str("proof_state_triage_row_contract" in contract),
            "proof_state_triage_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_ablation_study_row_contract",
            "contract",
            "ablation_study_row_contract",
            str("ablation_study_row_contract" in contract),
            "ablation_study_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_route_alignment_edge_contract",
            "contract",
            "route_alignment_edge_contract",
            str("route_alignment_edge_contract" in contract),
            "route_alignment_edge_contract" in contract,
        ),
        _check(
            "portable_contract_has_portable_gap_plan_row_contract",
            "contract",
            "portable_gap_plan_row_contract",
            str("portable_gap_plan_row_contract" in contract),
            "portable_gap_plan_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_target_intake_contract",
            "contract",
            "target_intake_contract",
            str("target_intake_contract" in contract),
            "target_intake_contract" in contract,
        ),
        _check(
            "portable_contract_has_target_intake_row_contract",
            "contract",
            "target_intake_row_contract",
            str("target_intake_row_contract" in contract),
            "target_intake_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_component_execution_plan_contract",
            "contract",
            "component_resource_execution_plan_contract",
            str("component_resource_execution_plan_contract" in contract),
            "component_resource_execution_plan_contract" in contract,
        ),
        _check(
            "portable_contract_has_benchmark_route_contract",
            "contract",
            "benchmark_route_contract",
            str("benchmark_route_contract" in contract),
            "benchmark_route_contract" in contract,
        ),
        _check(
            "portable_contract_has_evaluation_row_contract",
            "contract",
            "evaluation_row_contract",
            str("evaluation_row_contract" in contract),
            "evaluation_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_adapter_registry_row_contract",
            "contract",
            "adapter_registry_row_contract",
            str("adapter_registry_row_contract" in contract),
            "adapter_registry_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_cross_prover_matrix_audit_row_contract",
            "contract",
            "cross_prover_matrix_audit_row_contract",
            str("cross_prover_matrix_audit_row_contract" in contract),
            "cross_prover_matrix_audit_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_cross_prover_target_summary_contract",
            "contract",
            "cross_prover_target_summary_contract",
            str("cross_prover_target_summary_contract" in contract),
            "cross_prover_target_summary_contract" in contract,
        ),
        _check(
            "portable_contract_has_component_resource_resource_row_contract",
            "contract",
            "component_resource_resource_row_contract",
            str("component_resource_resource_row_contract" in contract),
            "component_resource_resource_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_component_resource_component_row_contract",
            "contract",
            "component_resource_component_row_contract",
            str("component_resource_component_row_contract" in contract),
            "component_resource_component_row_contract" in contract,
        ),
        _check(
            "portable_contract_has_component_resource_contract_row_contract",
            "contract",
            "component_resource_contract_row_contract",
            str("component_resource_contract_row_contract" in contract),
            "component_resource_contract_row_contract" in contract,
        ),
        _check(
            "planner_schema_file",
            "contract",
            "schema file exists",
            str(schema_path.exists()),
            schema_path.exists(),
        ),
        _check(
            "planner_schema_id",
            "contract",
            PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
            str(schema.get("$id", "")),
            schema.get("$id") == PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
        ),
        _check(
            "prover_adapter_schema_file",
            "contract",
            "prover adapter response schema exists",
            str(adapter_schema_path.exists()),
            adapter_schema_path.exists(),
        ),
        _check(
            "prover_adapter_schema_id",
            "contract",
            PROVER_ADAPTER_RESPONSE_SCHEMA_ID,
            str(adapter_schema.get("$id", "")),
            adapter_schema.get("$id") == PROVER_ADAPTER_RESPONSE_SCHEMA_ID,
        ),
        _check(
            "prover_adapter_packet_schema_file",
            "contract",
            "prover adapter packet schema exists",
            str(adapter_packet_schema_path.exists()),
            adapter_packet_schema_path.exists(),
        ),
        _check(
            "prover_adapter_packet_schema_id",
            "contract",
            PROVER_ADAPTER_PACKET_SCHEMA_ID,
            str(adapter_packet_schema.get("$id", "")),
            adapter_packet_schema.get("$id") == PROVER_ADAPTER_PACKET_SCHEMA_ID,
        ),
        _check(
            "prover_adapter_response_validation_row_schema_file",
            "contract",
            "prover adapter response-validation row schema exists",
            str(response_validation_row_schema_path.exists()),
            response_validation_row_schema_path.exists(),
        ),
        _check(
            "prover_adapter_response_validation_row_schema_id",
            "contract",
            PROVER_ADAPTER_RESPONSE_VALIDATION_ROW_SCHEMA_ID,
            str(response_validation_row_schema.get("$id", "")),
            response_validation_row_schema.get("$id")
            == PROVER_ADAPTER_RESPONSE_VALIDATION_ROW_SCHEMA_ID,
        ),
        _check(
            "prover_adapter_schema_rejects_kernel_claim",
            "contract",
            "kernel_verified const false",
            json.dumps(adapter_schema.get("properties", {}).get("kernel_verified", {}), sort_keys=True),
            adapter_schema.get("properties", {}).get("kernel_verified", {}).get("const")
            is False,
        ),
        _check(
            "refinement_tool_response_schema_file",
            "contract",
            "refinement tool response schema exists",
            str(refinement_tool_response_schema_path.exists()),
            refinement_tool_response_schema_path.exists(),
        ),
        _check(
            "refinement_work_item_schema_file",
            "contract",
            "refinement work item schema exists",
            str(refinement_work_item_schema_path.exists()),
            refinement_work_item_schema_path.exists(),
        ),
        _check(
            "refinement_work_item_schema_id",
            "contract",
            "urn:ai-statistician:schemas:formalization-gap-planner-refinement-work-item:1",
            str(refinement_work_item_schema.get("$id", "")),
            refinement_work_item_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-refinement-work-item:1",
        ),
        _check(
            "refinement_tool_response_schema_id",
            "contract",
            "urn:ai-statistician:schemas:formalization-gap-planner-refinement-tool-response:1",
            str(refinement_tool_response_schema.get("$id", "")),
            refinement_tool_response_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-refinement-tool-response:1",
        ),
        _check(
            "refinement_evidence_row_schema_file",
            "contract",
            "refinement evidence row schema exists",
            str(refinement_evidence_row_schema_path.exists()),
            refinement_evidence_row_schema_path.exists(),
        ),
        _check(
            "refinement_evidence_row_schema_id",
            "contract",
            "urn:ai-statistician:schemas:formalization-gap-planner-refinement-evidence-row:1",
            str(refinement_evidence_row_schema.get("$id", "")),
            refinement_evidence_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-refinement-evidence-row:1",
        ),
        _check(
            "proof_state_triage_row_schema_file",
            "contract",
            "proof-state triage row schema exists",
            str(proof_state_triage_row_schema_path.exists()),
            proof_state_triage_row_schema_path.exists(),
        ),
        _check(
            "proof_state_triage_row_schema_id",
            "contract",
            "urn:ai-statistician:schemas:formalization-gap-planner-proof-state-triage-row:1",
            str(proof_state_triage_row_schema.get("$id", "")),
            proof_state_triage_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-proof-state-triage-row:1",
        ),
        _check(
            "interactive_session_row_schema_file",
            "contract",
            "interactive session row schema exists",
            str(interactive_session_row_schema_path.exists()),
            interactive_session_row_schema_path.exists(),
        ),
        _check(
            "interactive_session_row_schema_id",
            "contract",
            "urn:ai-statistician:schemas:formalization-gap-planner-interactive-session-row:1",
            str(interactive_session_row_schema.get("$id", "")),
            interactive_session_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-interactive-session-row:1",
        ),
        _check(
            "interactive_decision_policy_row_schema_file",
            "contract",
            "interactive decision-policy row schema exists",
            str(interactive_decision_policy_row_schema_path.exists()),
            interactive_decision_policy_row_schema_path.exists(),
        ),
        _check(
            "interactive_decision_policy_row_schema_id",
            "contract",
            "urn:ai-statistician:schemas:formalization-gap-planner-interactive-decision-policy-row:1",
            str(interactive_decision_policy_row_schema.get("$id", "")),
            interactive_decision_policy_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-interactive-decision-policy-row:1",
        ),
        _check(
            "minimal_delta_decision_row_schema_file",
            "contract",
            "minimal delta decision row schema exists",
            str(minimal_delta_decision_row_schema_path.exists()),
            minimal_delta_decision_row_schema_path.exists(),
        ),
        _check(
            "minimal_delta_decision_row_schema_id",
            "contract",
            "urn:ai-statistician:schemas:formalization-gap-planner-minimal-delta-decision-row:1",
            str(minimal_delta_decision_row_schema.get("$id", "")),
            minimal_delta_decision_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-minimal-delta-decision-row:1",
        ),
        _check(
            "portable_plan_audit_row_schema_file",
            "contract",
            "portable-plan audit row schema exists",
            str(portable_plan_audit_row_schema_path.exists()),
            portable_plan_audit_row_schema_path.exists(),
        ),
        _check(
            "portable_plan_audit_row_schema_id",
            "contract",
            PORTABLE_PLAN_AUDIT_ROW_SCHEMA_ID,
            str(portable_plan_audit_row_schema.get("$id", "")),
            portable_plan_audit_row_schema.get("$id")
            == PORTABLE_PLAN_AUDIT_ROW_SCHEMA_ID,
        ),
        _check(
            "library_coverage_map_row_schema_file",
            "contract",
            "library-coverage map row schema exists",
            str(library_coverage_map_row_schema_path.exists()),
            library_coverage_map_row_schema_path.exists(),
        ),
        _check(
            "library_coverage_map_row_schema_id",
            "contract",
            LIBRARY_COVERAGE_MAP_ROW_SCHEMA_ID,
            str(library_coverage_map_row_schema.get("$id", "")),
            library_coverage_map_row_schema.get("$id")
            == LIBRARY_COVERAGE_MAP_ROW_SCHEMA_ID,
        ),
        _check(
            "llm_route_planner_request_schema_file",
            "contract",
            "LLM route-planner request schema exists",
            str(llm_route_planner_request_schema_path.exists()),
            llm_route_planner_request_schema_path.exists(),
        ),
        _check(
            "llm_route_planner_request_schema_id",
            "contract",
            LLM_ROUTE_PLANNER_REQUEST_SCHEMA_ID,
            str(llm_route_planner_request_schema.get("$id", "")),
            llm_route_planner_request_schema.get("$id")
            == LLM_ROUTE_PLANNER_REQUEST_SCHEMA_ID,
        ),
        _check(
            "llm_route_planner_route_planning_brief_schema_file",
            "contract",
            "LLM route-planner route-planning brief schema exists",
            str(llm_route_planner_route_planning_brief_schema_path.exists()),
            llm_route_planner_route_planning_brief_schema_path.exists(),
        ),
        _check(
            "llm_route_planner_route_planning_brief_schema_id",
            "contract",
            LLM_ROUTE_PLANNER_ROUTE_PLANNING_BRIEF_SCHEMA_ID,
            str(llm_route_planner_route_planning_brief_schema.get("$id", "")),
            llm_route_planner_route_planning_brief_schema.get("$id")
            == LLM_ROUTE_PLANNER_ROUTE_PLANNING_BRIEF_SCHEMA_ID,
        ),
        _check(
            "llm_route_planner_route_planning_brief_schema_shape",
            "contract",
            "route-planning brief schema matches canonical builder",
            str(llm_route_planner_route_planning_brief_schema.get("$id", "")),
            llm_route_planner_route_planning_brief_schema
            == llm_route_planner_route_planning_brief_json_schema(),
        ),
        _check(
            "llm_route_planner_response_schema_file",
            "contract",
            "LLM route-planner response schema exists",
            str(llm_route_planner_response_schema_path.exists()),
            llm_route_planner_response_schema_path.exists(),
        ),
        _check(
            "llm_route_planner_response_schema_id",
            "contract",
            LLM_ROUTE_PLANNER_RESPONSE_SCHEMA_ID,
            str(llm_route_planner_response_schema.get("$id", "")),
            llm_route_planner_response_schema.get("$id")
            == LLM_ROUTE_PLANNER_RESPONSE_SCHEMA_ID,
        ),
        _check(
            "llm_route_planner_response_payload_schema_file",
            "contract",
            "LLM route-planner response-payload schema exists",
            str(llm_route_planner_response_payload_schema_path.exists()),
            llm_route_planner_response_payload_schema_path.exists(),
        ),
        _check(
            "llm_route_planner_response_payload_schema_id",
            "contract",
            LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID,
            str(llm_route_planner_response_payload_schema.get("$id", "")),
            llm_route_planner_response_payload_schema.get("$id")
            == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID,
        ),
        _check(
            "llm_route_planner_response_payload_lean_legacy_schema_file",
            "contract",
            "Lean-compatible LLM route-planner response-payload schema exists",
            str(llm_route_planner_response_payload_lean_legacy_schema_path.exists()),
            llm_route_planner_response_payload_lean_legacy_schema_path.exists(),
        ),
        _check(
            "llm_route_planner_response_payload_lean_legacy_schema_id",
            "contract",
            LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_LEAN_LEGACY_SCHEMA_ID,
            str(llm_route_planner_response_payload_lean_legacy_schema.get("$id", "")),
            llm_route_planner_response_payload_lean_legacy_schema.get("$id")
            == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_LEAN_LEGACY_SCHEMA_ID,
        ),
        _check(
            "llm_route_planner_response_payload_lean_legacy_schema_shape",
            "contract",
            "lean4 target and lean_realization_dag_nodes property",
            json.dumps(
                {
                    "targets": _str_tuple(
                        llm_route_planner_response_payload_lean_legacy_schema.get(
                            "x-target-prover-families",
                            [],
                        )
                    ),
                    "has_lean_alias": "lean_realization_dag_nodes"
                    in (
                        llm_route_planner_response_payload_lean_legacy_schema.get(
                            "properties",
                            {},
                        )
                        if isinstance(
                            llm_route_planner_response_payload_lean_legacy_schema.get(
                                "properties",
                                {},
                            ),
                            dict,
                        )
                        else {}
                    ),
                },
                sort_keys=True,
            ),
            _str_tuple(
                llm_route_planner_response_payload_lean_legacy_schema.get(
                    "x-target-prover-families",
                    [],
                )
            )
            == ("lean4",)
            and "lean_realization_dag_nodes"
            in (
                llm_route_planner_response_payload_lean_legacy_schema.get(
                    "properties",
                    {},
                )
                if isinstance(
                    llm_route_planner_response_payload_lean_legacy_schema.get(
                        "properties",
                        {},
                    ),
                    dict,
                )
                else {}
            ),
        ),
        _check(
            "llm_route_planner_response_payload_target_prover_schema_file",
            "contract",
            "portable target-prover LLM route-planner response-payload schema exists",
            str(llm_route_planner_response_payload_target_prover_schema_path.exists()),
            llm_route_planner_response_payload_target_prover_schema_path.exists(),
        ),
        _check(
            "llm_route_planner_response_payload_target_prover_schema_id",
            "contract",
            LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_TARGET_PROVER_SCHEMA_ID,
            str(llm_route_planner_response_payload_target_prover_schema.get("$id", "")),
            llm_route_planner_response_payload_target_prover_schema.get("$id")
            == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_TARGET_PROVER_SCHEMA_ID,
        ),
        _check(
            "llm_route_planner_response_payload_target_prover_schema_shape",
            "contract",
            "rocq,isabelle,agda target and no lean_realization_dag_nodes property",
            json.dumps(
                {
                    "targets": _str_tuple(
                        llm_route_planner_response_payload_target_prover_schema.get(
                            "x-target-prover-families",
                            [],
                        )
                    ),
                    "anyOf": llm_route_planner_response_payload_target_prover_schema.get(
                        "anyOf",
                        [],
                    ),
                    "has_lean_alias": "lean_realization_dag_nodes"
                    in (
                        llm_route_planner_response_payload_target_prover_schema.get(
                            "properties",
                            {},
                        )
                        if isinstance(
                            llm_route_planner_response_payload_target_prover_schema.get(
                                "properties",
                                {},
                            ),
                            dict,
                        )
                        else {}
                    ),
                },
                sort_keys=True,
            ),
            _str_tuple(
                llm_route_planner_response_payload_target_prover_schema.get(
                    "x-target-prover-families",
                    [],
                )
            )
            == ("rocq", "isabelle", "agda")
            and llm_route_planner_response_payload_target_prover_schema.get("anyOf")
            == [{"required": ["formal_realization_dag_nodes"]}]
            and "lean_realization_dag_nodes"
            not in (
                llm_route_planner_response_payload_target_prover_schema.get(
                    "properties",
                    {},
                )
                if isinstance(
                    llm_route_planner_response_payload_target_prover_schema.get(
                        "properties",
                        {},
                    ),
                    dict,
                )
                else {}
            ),
        ),
        _check(
            "llm_route_planner_response_payload_validation_manifest_schema_file",
            "contract",
            "LLM route-planner response-payload validation manifest schema exists",
            str(llm_route_planner_response_payload_validation_manifest_schema_path.exists()),
            llm_route_planner_response_payload_validation_manifest_schema_path.exists(),
        ),
        _check(
            "llm_route_planner_response_payload_validation_manifest_schema_id",
            "contract",
            LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID,
            str(
                llm_route_planner_response_payload_validation_manifest_schema.get(
                    "$id",
                    "",
                )
            ),
            llm_route_planner_response_payload_validation_manifest_schema.get("$id")
            == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID,
        ),
        _check(
            "llm_route_planner_response_payload_validation_row_schema_file",
            "contract",
            "LLM route-planner response-payload validation row schema exists",
            str(llm_route_planner_response_payload_validation_row_schema_path.exists()),
            llm_route_planner_response_payload_validation_row_schema_path.exists(),
        ),
        _check(
            "llm_route_planner_response_payload_validation_row_schema_id",
            "contract",
            LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID,
            str(
                llm_route_planner_response_payload_validation_row_schema.get(
                    "$id",
                    "",
                )
            ),
            llm_route_planner_response_payload_validation_row_schema.get("$id")
            == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID,
        ),
        _check(
            "llm_route_planner_manifest_schema_file",
            "contract",
            "LLM route-planner manifest schema exists",
            str(llm_route_planner_manifest_schema_path.exists()),
            llm_route_planner_manifest_schema_path.exists(),
        ),
        _check(
            "llm_route_planner_manifest_schema_id",
            "contract",
            LLM_ROUTE_PLANNER_MANIFEST_SCHEMA_ID,
            str(llm_route_planner_manifest_schema.get("$id", "")),
            llm_route_planner_manifest_schema.get("$id")
            == LLM_ROUTE_PLANNER_MANIFEST_SCHEMA_ID,
        ),
        _check(
            "llm_route_planner_manifest_schema_legacy_alias_contract",
            "contract",
            "lean_realization_dag_nodes aliases formal_realization_dag_nodes",
            _llm_legacy_response_alias_schema_observed(
                llm_route_planner_manifest_schema
            ),
            not _llm_legacy_response_alias_schema_errors(
                llm_route_planner_manifest_schema
            ),
            errors=_llm_legacy_response_alias_schema_errors(
                llm_route_planner_manifest_schema
            ),
        ),
        _check(
            "llm_route_planner_response_schema_rejects_kernel_claim",
            "contract",
            "kernel_verified const false",
            json.dumps(
                llm_route_planner_response_schema.get("properties", {}).get(
                    "kernel_verified",
                    {},
                ),
                sort_keys=True,
            ),
            llm_route_planner_response_schema.get("properties", {})
            .get("kernel_verified", {})
            .get("const")
            is False,
        ),
        _check(
            "llm_route_planner_row_schema_file",
            "contract",
            "LLM route-planner row schema exists",
            str(llm_route_planner_row_schema_path.exists()),
            llm_route_planner_row_schema_path.exists(),
        ),
        _check(
            "llm_route_planner_row_schema_id",
            "contract",
            LLM_ROUTE_PLANNER_ROW_SCHEMA_ID,
            str(llm_route_planner_row_schema.get("$id", "")),
            llm_route_planner_row_schema.get("$id")
            == LLM_ROUTE_PLANNER_ROW_SCHEMA_ID,
        ),
        _check(
            "llm_route_planner_model_tier_decision_ledger_schema_file",
            "contract",
            "LLM route-planner model-tier decision ledger schema exists",
            str(llm_route_planner_model_tier_decision_ledger_schema_path.exists()),
            llm_route_planner_model_tier_decision_ledger_schema_path.exists(),
        ),
        _check(
            "llm_route_planner_model_tier_decision_ledger_schema_id",
            "contract",
            LLM_ROUTE_PLANNER_MODEL_TIER_DECISION_LEDGER_SCHEMA_ID,
            str(llm_route_planner_model_tier_decision_ledger_schema.get("$id", "")),
            llm_route_planner_model_tier_decision_ledger_schema.get("$id")
            == LLM_ROUTE_PLANNER_MODEL_TIER_DECISION_LEDGER_SCHEMA_ID,
        ),
        _check(
            "route_adoption_blocker_taxonomy_schema_file",
            "contract",
            "route-adoption blocker taxonomy schema exists",
            str(route_adoption_blocker_taxonomy_schema_path.exists()),
            route_adoption_blocker_taxonomy_schema_path.exists(),
        ),
        _check(
            "route_adoption_blocker_taxonomy_schema_id",
            "contract",
            ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID,
            str(route_adoption_blocker_taxonomy_schema.get("$id", "")),
            route_adoption_blocker_taxonomy_schema.get("$id")
            == ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID,
        ),
        _check(
            "route_adoption_blocker_taxonomy_manifest_schema_file",
            "contract",
            "route-adoption blocker taxonomy export manifest schema exists",
            str(route_adoption_blocker_taxonomy_manifest_schema_path.exists()),
            route_adoption_blocker_taxonomy_manifest_schema_path.exists(),
        ),
        _check(
            "route_adoption_blocker_taxonomy_manifest_schema_id",
            "contract",
            ROUTE_ADOPTION_BLOCKER_TAXONOMY_MANIFEST_SCHEMA_ID,
            str(route_adoption_blocker_taxonomy_manifest_schema.get("$id", "")),
            route_adoption_blocker_taxonomy_manifest_schema.get("$id")
            == ROUTE_ADOPTION_BLOCKER_TAXONOMY_MANIFEST_SCHEMA_ID,
        ),
        _check(
            "route_adoption_blocker_taxonomy_manifest_schema_shape",
            "contract",
            "route-adoption blocker taxonomy export manifest schema matches canonical builder",
            str(
                route_adoption_blocker_taxonomy_manifest_schema.get(
                    "component_name",
                    route_adoption_blocker_taxonomy_manifest_schema.get("title", ""),
                )
            ),
            route_adoption_blocker_taxonomy_manifest_schema
            == route_adoption_blocker_taxonomy_manifest_json_schema(),
        ),
        _check(
            "route_adoption_blocker_taxonomy_file",
            "contract",
            "route-adoption blocker taxonomy contract exists",
            str(route_adoption_blocker_taxonomy_path.exists()),
            route_adoption_blocker_taxonomy_path.exists(),
        ),
        _check(
            "route_adoption_blocker_taxonomy_payload",
            "contract",
            "route-adoption blocker taxonomy validates",
            (
                "; ".join(route_adoption_blocker_taxonomy_errors)
                if route_adoption_blocker_taxonomy_errors
                else str(route_adoption_blocker_taxonomy.get("taxonomy_id", ""))
            ),
            not route_adoption_blocker_taxonomy_errors
            and route_adoption_blocker_taxonomy.get("taxonomy_id")
            == ROUTE_ADOPTION_BLOCKER_TAXONOMY_ID,
            errors=route_adoption_blocker_taxonomy_errors,
        ),
        _check(
            "portable_contract_has_route_adoption_blocker_taxonomy_contract",
            "contract",
            "route_adoption_blocker_taxonomy_contract",
            str("route_adoption_blocker_taxonomy_contract" in contract),
            "route_adoption_blocker_taxonomy_contract" in contract,
        ),
        _check(
            "portable_contract_has_route_adoption_blocker_taxonomy_manifest_schema_contract",
            "contract",
            "route_adoption_blocker_taxonomy_manifest_schema_contract",
            str(
                "route_adoption_blocker_taxonomy_manifest_schema_contract" in contract
            ),
            "route_adoption_blocker_taxonomy_manifest_schema_contract" in contract,
        ),
        _check(
            "portable_contract_route_adoption_blocker_taxonomy_manifest_schema_valid",
            "contract",
            "embedded route-adoption blocker taxonomy manifest schema matches canonical builder",
            str(
                embedded_route_adoption_blocker_taxonomy_manifest_schema.get(
                    "$id",
                    "",
                )
            ),
            embedded_route_adoption_blocker_taxonomy_manifest_schema
            == route_adoption_blocker_taxonomy_manifest_json_schema(),
        ),
        _check(
            "portable_contract_route_adoption_blocker_taxonomy_valid",
            "contract",
            "embedded route-adoption blocker taxonomy validates",
            (
                "; ".join(embedded_route_adoption_blocker_taxonomy_errors)
                if embedded_route_adoption_blocker_taxonomy_errors
                else "valid"
            ),
            not embedded_route_adoption_blocker_taxonomy_errors,
            errors=embedded_route_adoption_blocker_taxonomy_errors,
        ),
        _check(
            "llm_route_planner_row_schema_route_adoption_status_enum_matches_taxonomy",
            "contract",
            "row schema route_adoption_status enum matches taxonomy",
            ",".join(_str_tuple(row_schema_route_adoption_status.get("enum", []))),
            _str_tuple(row_schema_route_adoption_status.get("enum", []))
            == taxonomy_status_values,
        ),
        _check(
            "llm_route_planner_row_schema_route_adoption_blocker_enum_matches_taxonomy",
            "contract",
            "row schema route_adoption_blockers enum matches taxonomy",
            ",".join(
                _str_tuple(row_schema_route_adoption_blocker_items.get("enum", []))
            ),
            _str_tuple(row_schema_route_adoption_blocker_items.get("enum", []))
            == taxonomy_blocker_values,
        ),
        _check(
            "primitive_action_queue_row_schema_file",
            "contract",
            "primitive action-queue row schema exists",
            str(primitive_action_queue_row_schema_path.exists()),
            primitive_action_queue_row_schema_path.exists(),
        ),
        _check(
            "primitive_action_queue_row_schema_id",
            "contract",
            PRIMITIVE_ACTION_QUEUE_ROW_SCHEMA_ID,
            str(primitive_action_queue_row_schema.get("$id", "")),
            primitive_action_queue_row_schema.get("$id")
            == PRIMITIVE_ACTION_QUEUE_ROW_SCHEMA_ID,
        ),
        _check(
            "action_resource_plan_row_schema_file",
            "contract",
            "action-resource plan row schema exists",
            str(action_resource_plan_row_schema_path.exists()),
            action_resource_plan_row_schema_path.exists(),
        ),
        _check(
            "action_resource_plan_row_schema_id",
            "contract",
            ACTION_RESOURCE_PLAN_ROW_SCHEMA_ID,
            str(action_resource_plan_row_schema.get("$id", "")),
            action_resource_plan_row_schema.get("$id")
            == ACTION_RESOURCE_PLAN_ROW_SCHEMA_ID,
        ),
        _check(
            "resource_request_queue_row_schema_file",
            "contract",
            "resource request-queue row schema exists",
            str(resource_request_queue_row_schema_path.exists()),
            resource_request_queue_row_schema_path.exists(),
        ),
        _check(
            "resource_request_queue_row_schema_id",
            "contract",
            RESOURCE_REQUEST_QUEUE_ROW_SCHEMA_ID,
            str(resource_request_queue_row_schema.get("$id", "")),
            resource_request_queue_row_schema.get("$id")
            == RESOURCE_REQUEST_QUEUE_ROW_SCHEMA_ID,
        ),
        _check(
            "resource_response_schema_file",
            "contract",
            "resource response schema exists",
            str(resource_response_schema_path.exists()),
            resource_response_schema_path.exists(),
        ),
        _check(
            "resource_response_schema_id",
            "contract",
            RESOURCE_RESPONSE_SCHEMA_ID,
            str(resource_response_schema.get("$id", "")),
            resource_response_schema.get("$id") == RESOURCE_RESPONSE_SCHEMA_ID,
        ),
        _check(
            "resource_response_schema_rejects_kernel_claim",
            "contract",
            "kernel_verified const false",
            json.dumps(
                resource_response_schema.get("properties", {}).get(
                    "kernel_verified", {}
                ),
                sort_keys=True,
            ),
            resource_response_schema.get("properties", {})
            .get("kernel_verified", {})
            .get("const")
            is False,
        ),
        _check(
            "resource_response_ledger_row_schema_file",
            "contract",
            "resource response-ledger row schema exists",
            str(resource_response_ledger_row_schema_path.exists()),
            resource_response_ledger_row_schema_path.exists(),
        ),
        _check(
            "resource_response_ledger_row_schema_id",
            "contract",
            RESOURCE_RESPONSE_LEDGER_ROW_SCHEMA_ID,
            str(resource_response_ledger_row_schema.get("$id", "")),
            resource_response_ledger_row_schema.get("$id")
            == RESOURCE_RESPONSE_LEDGER_ROW_SCHEMA_ID,
        ),
        _check(
            "source_grounding_row_schema_file",
            "contract",
            "source grounding row schema exists",
            str(source_grounding_row_schema_path.exists()),
            source_grounding_row_schema_path.exists(),
        ),
        _check(
            "source_grounding_row_schema_id",
            "contract",
            "urn:ai-statistician:schemas:formalization-gap-planner-source-grounding-row:1",
            str(source_grounding_row_schema.get("$id", "")),
            source_grounding_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-source-grounding-row:1",
        ),
        _check(
            "route_stability_audit_row_schema_file",
            "contract",
            "route-stability audit row schema exists",
            str(route_stability_audit_row_schema_path.exists()),
            route_stability_audit_row_schema_path.exists(),
        ),
        _check(
            "route_stability_audit_row_schema_id",
            "contract",
            "urn:ai-statistician:schemas:formalization-gap-planner-route-stability-audit-row:1",
            str(route_stability_audit_row_schema.get("$id", "")),
            route_stability_audit_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-route-stability-audit-row:1",
        ),
        _check(
            "route_revision_overlay_row_schema_file",
            "contract",
            "route revision overlay row schema exists",
            str(route_revision_overlay_row_schema_path.exists()),
            route_revision_overlay_row_schema_path.exists(),
        ),
        _check(
            "route_revision_overlay_row_schema_id",
            "contract",
            "urn:ai-statistician:schemas:formalization-gap-planner-route-revision-overlay-row:1",
            str(route_revision_overlay_row_schema.get("$id", "")),
            route_revision_overlay_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-route-revision-overlay-row:1",
        ),
        _check(
            "route_replan_handoff_row_schema_file",
            "contract",
            "route replan handoff row schema exists",
            str(route_replan_handoff_row_schema_path.exists()),
            route_replan_handoff_row_schema_path.exists(),
        ),
        _check(
            "route_replan_handoff_row_schema_id",
            "contract",
            "urn:ai-statistician:schemas:formalization-gap-planner-route-replan-handoff-row:1",
            str(route_replan_handoff_row_schema.get("$id", "")),
            route_replan_handoff_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-route-replan-handoff-row:1",
        ),
        _check(
            "route_replan_handoff_audit_row_schema_file",
            "contract",
            "route replan handoff audit row schema exists",
            str(route_replan_handoff_audit_row_schema_path.exists()),
            route_replan_handoff_audit_row_schema_path.exists(),
        ),
        _check(
            "route_replan_handoff_audit_row_schema_id",
            "contract",
            "urn:ai-statistician:schemas:formalization-gap-planner-route-replan-handoff-audit-row:1",
            str(route_replan_handoff_audit_row_schema.get("$id", "")),
            route_replan_handoff_audit_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-route-replan-handoff-audit-row:1",
        ),
        _check(
            "ablation_study_row_schema_file",
            "contract",
            "ablation study row schema exists",
            str(ablation_study_row_schema_path.exists()),
            ablation_study_row_schema_path.exists(),
        ),
        _check(
            "ablation_study_row_schema_id",
            "contract",
            "urn:ai-statistician:schemas:formalization-gap-planner-ablation-study-row:1",
            str(ablation_study_row_schema.get("$id", "")),
            ablation_study_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-ablation-study-row:1",
        ),
        _check(
            "route_alignment_edge_schema_file",
            "contract",
            "route alignment edge schema exists",
            str(route_alignment_edge_schema_path.exists()),
            route_alignment_edge_schema_path.exists(),
        ),
        _check(
            "route_alignment_edge_schema_id",
            "contract",
            "urn:ai-statistician:schemas:formalization-gap-planner-route-alignment-edge:1",
            str(route_alignment_edge_schema.get("$id", "")),
            route_alignment_edge_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-route-alignment-edge:1",
        ),
        _check(
            "benchmark_route_schema_file",
            "contract",
            "benchmark route-row schema exists",
            str(benchmark_route_schema_path.exists()),
            benchmark_route_schema_path.exists(),
        ),
        _check(
            "benchmark_route_schema_id",
            "contract",
            "urn:ai-statistician:schemas:formalization-gap-planner-benchmark-route-row:1",
            str(benchmark_route_schema.get("$id", "")),
            benchmark_route_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-benchmark-route-row:1",
        ),
        _check(
            "evaluation_row_schema_file",
            "contract",
            "evaluation row schema exists",
            str(evaluation_row_schema_path.exists()),
            evaluation_row_schema_path.exists(),
        ),
        _check(
            "evaluation_row_schema_id",
            "contract",
            "urn:ai-statistician:schemas:formalization-gap-planner-evaluation-row:1",
            str(evaluation_row_schema.get("$id", "")),
            evaluation_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-evaluation-row:1",
        ),
        _check(
            "adapter_registry_row_schema_file",
            "contract",
            "adapter-registry row schema exists",
            str(adapter_registry_row_schema_path.exists()),
            adapter_registry_row_schema_path.exists(),
        ),
        _check(
            "adapter_registry_row_schema_id",
            "contract",
            ADAPTER_REGISTRY_ROW_SCHEMA_ID,
            str(adapter_registry_row_schema.get("$id", "")),
            adapter_registry_row_schema.get("$id") == ADAPTER_REGISTRY_ROW_SCHEMA_ID,
        ),
        _check(
            "cross_prover_matrix_audit_row_schema_file",
            "contract",
            "cross-prover matrix audit row schema exists",
            str(cross_prover_matrix_audit_row_schema_path.exists()),
            cross_prover_matrix_audit_row_schema_path.exists(),
        ),
        _check(
            "cross_prover_matrix_audit_row_schema_id",
            "contract",
            CROSS_PROVER_MATRIX_AUDIT_ROW_SCHEMA_ID,
            str(cross_prover_matrix_audit_row_schema.get("$id", "")),
            cross_prover_matrix_audit_row_schema.get("$id")
            == CROSS_PROVER_MATRIX_AUDIT_ROW_SCHEMA_ID,
        ),
        _check(
            "cross_prover_target_summary_schema_file",
            "contract",
            "cross-prover target summary schema exists",
            str(cross_prover_target_summary_schema_path.exists()),
            cross_prover_target_summary_schema_path.exists(),
        ),
        _check(
            "cross_prover_target_summary_schema_id",
            "contract",
            CROSS_PROVER_TARGET_SUMMARY_SCHEMA_ID,
            str(cross_prover_target_summary_schema.get("$id", "")),
            cross_prover_target_summary_schema.get("$id")
            == CROSS_PROVER_TARGET_SUMMARY_SCHEMA_ID,
        ),
        _check(
            "standalone_input_schema_file",
            "contract",
            "standalone input schema exists",
            str(standalone_schema_path.exists()),
            standalone_schema_path.exists(),
        ),
        _check(
            "standalone_input_schema_id",
            "contract",
            FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_ID,
            str(standalone_schema.get("$id", "")),
            standalone_schema.get("$id")
            == FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_ID,
        ),
        _check(
            "llm_route_planner_seed_route_selection_schema_file",
            "contract",
            "LLM route-planner seed route-selection schema exists",
            str(llm_route_planner_seed_route_selection_schema_path.exists()),
            llm_route_planner_seed_route_selection_schema_path.exists(),
        ),
        _check(
            "llm_route_planner_seed_route_selection_schema_id",
            "contract",
            FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SEED_ROUTE_SELECTION_SCHEMA_ID,
            str(llm_route_planner_seed_route_selection_schema.get("$id", "")),
            llm_route_planner_seed_route_selection_schema.get("$id")
            == FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SEED_ROUTE_SELECTION_SCHEMA_ID,
        ),
        _check(
            "portable_contract_has_llm_route_planner_seed_route_selection_contract",
            "contract",
            "llm_route_planner_seed_route_selection_contract",
            str("llm_route_planner_seed_route_selection_contract" in contract),
            "llm_route_planner_seed_route_selection_contract" in contract,
        ),
        _check(
            "portable_contract_llm_route_planner_seed_route_selection_contract_id",
            "contract",
            FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SEED_ROUTE_SELECTION_SCHEMA_ID,
            str(embedded_seed_route_selection_contract.get("$id", "")),
            embedded_seed_route_selection_contract.get("$id")
            == FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SEED_ROUTE_SELECTION_SCHEMA_ID,
        ),
        _check(
            "target_intake_schema_file",
            "contract",
            "target intake schema exists",
            str(target_intake_schema_path.exists()),
            target_intake_schema_path.exists(),
        ),
        _check(
            "target_intake_schema_id",
            "contract",
            FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_SCHEMA_ID,
            str(target_intake_schema.get("$id", "")),
            target_intake_schema.get("$id")
            == FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_SCHEMA_ID,
        ),
        _check(
            "target_intake_row_schema_file",
            "contract",
            "target intake row schema exists",
            str(target_intake_row_schema_path.exists()),
            target_intake_row_schema_path.exists(),
        ),
        _check(
            "target_intake_row_schema_id",
            "contract",
            FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_ROW_SCHEMA_ID,
            str(target_intake_row_schema.get("$id", "")),
            target_intake_row_schema.get("$id")
            == FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_ROW_SCHEMA_ID,
        ),
        _check(
            "component_execution_plan_schema_file",
            "contract",
            "component execution-plan schema exists",
            str(component_execution_plan_schema_path.exists()),
            component_execution_plan_schema_path.exists(),
        ),
        _check(
            "component_execution_plan_schema_id",
            "contract",
            "urn:ai-statistician:schemas:formalization-gap-planner-component-execution-plan:1",
            str(component_execution_plan_schema.get("$id", "")),
            component_execution_plan_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-component-execution-plan:1",
        ),
        _check(
            "component_resource_resource_row_schema_file",
            "contract",
            "component-resource resource-row schema exists",
            str(component_resource_resource_row_schema_path.exists()),
            component_resource_resource_row_schema_path.exists(),
        ),
        _check(
            "component_resource_resource_row_schema_id",
            "contract",
            "urn:ai-statistician:schemas:formalization-gap-planner-component-resource-registry-resource-row:1",
            str(component_resource_resource_row_schema.get("$id", "")),
            component_resource_resource_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-component-resource-registry-resource-row:1",
        ),
        _check(
            "component_resource_component_row_schema_file",
            "contract",
            "component-resource component-row schema exists",
            str(component_resource_component_row_schema_path.exists()),
            component_resource_component_row_schema_path.exists(),
        ),
        _check(
            "component_resource_component_row_schema_id",
            "contract",
            "urn:ai-statistician:schemas:formalization-gap-planner-component-resource-registry-component-row:1",
            str(component_resource_component_row_schema.get("$id", "")),
            component_resource_component_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-component-resource-registry-component-row:1",
        ),
        _check(
            "component_resource_contract_row_schema_file",
            "contract",
            "component-resource contract-row schema exists",
            str(component_resource_contract_row_schema_path.exists()),
            component_resource_contract_row_schema_path.exists(),
        ),
        _check(
            "component_resource_contract_row_schema_id",
            "contract",
            "urn:ai-statistician:schemas:formalization-gap-planner-component-resource-contract-row:1",
            str(component_resource_contract_row_schema.get("$id", "")),
            component_resource_contract_row_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-component-resource-contract-row:1",
        ),
    ]


def _benchmark_checks(bundle_dir: Path) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    manifest_path = bundle_dir / "benchmark" / "formalization_gap_planner_benchmark_manifest.json"
    routes_jsonl_path = bundle_dir / "benchmark" / "formalization_gap_planner_benchmark_routes.jsonl"
    route_schema_path = bundle_dir / "benchmark" / "formalization_gap_planner_benchmark_route.schema.json"
    manifest = _read_json_no_error(manifest_path)
    route_rows, route_errors = _read_jsonl_dict_rows_no_error(routes_jsonl_path)
    checks = [
        _check(
            "benchmark_manifest",
            "benchmark",
            "benchmark manifest exists",
            str(manifest_path.exists()),
            manifest_path.exists(),
        ),
        _check(
            "benchmark_all_ok",
            "benchmark",
            "all_ok true",
            str(manifest.get("all_ok", "")),
            bool(manifest.get("all_ok", False)),
        ),
        _check(
            "benchmark_routes_present",
            "benchmark",
            "at least one route",
            str(manifest.get("n_routes", 0)),
            int(manifest.get("n_routes", 0) or 0) > 0,
        ),
        _check(
            "benchmark_route_schema",
            "benchmark",
            "benchmark route-row schema exists",
            str(route_schema_path.exists()),
            route_schema_path.exists(),
        ),
        _check(
            "benchmark_route_jsonl",
            "benchmark",
            "benchmark route JSONL exists",
            str(routes_jsonl_path.exists()),
            routes_jsonl_path.exists(),
        ),
        _check(
            "benchmark_route_jsonl_parse",
            "benchmark",
            "benchmark route JSONL parses into object rows",
            "; ".join(route_errors) if route_errors else f"rows={len(route_rows)}",
            not route_errors,
            errors=route_errors,
        ),
        _check(
            "benchmark_route_jsonl_row_count",
            "benchmark",
            "benchmark route JSONL rows match manifest count",
            f"jsonl={len(route_rows)} manifest={manifest.get('n_routes', 0)}",
            len(route_rows) == int(manifest.get("n_routes", 0) or 0),
        ),
        _check(
            "benchmark_manifest_route_schema_valid_count",
            "benchmark",
            "benchmark manifest route-row schema-valid count matches route count",
            (
                f"{manifest.get('n_route_row_schema_valid', 0)}/"
                f"{manifest.get('n_routes', 0)}; "
                f"invalid={manifest.get('n_route_row_schema_invalid', 0)}"
            ),
            int(manifest.get("n_routes", 0) or 0) > 0
            and int(manifest.get("n_route_row_schema_valid", 0) or 0)
            == int(manifest.get("n_routes", 0) or 0)
            and int(manifest.get("n_route_row_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "benchmark_boundary",
            "benchmark",
            "not theorem proof evidence",
            str(manifest.get("proof_evidence_boundary", ""))[:120],
            "not theorem proof evidence"
            in str(manifest.get("proof_evidence_boundary", "")),
        ),
    ]
    for idx, row in enumerate(route_rows):
        schema_errors = validate_benchmark_route_row(row)
        checks.append(
            _check(
                f"benchmark_route_row_{idx}_schema_valid",
                "benchmark",
                "benchmark route row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
    return checks


def _benchmark_audit_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    manifest_path = (
        bundle_dir
        / "benchmark_audit"
        / "formalization_gap_planner_benchmark_audit_manifest.json"
    )
    jsonl_path = (
        bundle_dir
        / "benchmark_audit"
        / "formalization_gap_planner_benchmark_audit.jsonl"
    )
    manifest = _read_json_no_error(manifest_path)
    return [
        _check(
            "benchmark_audit_manifest",
            "benchmark_audit",
            "benchmark audit manifest exists",
            str(manifest_path.exists()),
            manifest_path.exists(),
        ),
        _check(
            "benchmark_audit_all_ok",
            "benchmark_audit",
            "all_ok true",
            str(manifest.get("all_ok", "")),
            bool(manifest.get("all_ok", False)),
        ),
        _check(
            "benchmark_audit_failed_zero",
            "benchmark_audit",
            "zero failed checks",
            str(manifest.get("n_failed", "")),
            int(manifest.get("n_failed", 0) or 0) == 0,
        ),
        _check(
            "benchmark_audit_splits",
            "benchmark_audit",
            "derived evaluation splits present",
            str(manifest.get("n_evaluation_splits", 0)),
            int(manifest.get("n_evaluation_splits", 0) or 0) >= 2,
        ),
        _check(
            "benchmark_audit_jsonl",
            "benchmark_audit",
            "split jsonl exists",
            str(jsonl_path.exists()),
            jsonl_path.exists(),
        ),
        _check(
            "benchmark_audit_boundary",
            "benchmark_audit",
            "not theorem proof evidence",
            str(manifest.get("proof_evidence_boundary", ""))[:120],
            "not theorem proof evidence"
            in str(manifest.get("proof_evidence_boundary", "")),
        ),
    ]


def _adapter_registry_checks(bundle_dir: Path) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    manifest_path = (
        bundle_dir
        / "adapter_registry"
        / "formalization_gap_planner_adapter_registry_manifest.json"
    )
    jsonl_path = (
        bundle_dir
        / "adapter_registry"
        / "formalization_gap_planner_adapter_registry.jsonl"
    )
    row_schema_path = (
        bundle_dir
        / "adapter_registry"
        / "formalization_gap_planner_adapter_registry_row.schema.json"
    )
    manifest = _read_json_no_error(manifest_path)
    row_schema = _read_json_no_error(row_schema_path)
    jsonl_rows, jsonl_errors = _read_jsonl_dict_rows_no_error(jsonl_path)
    adapter_ids = {
        str(row.get("adapter_id", ""))
        for row in manifest.get("rows", [])
        if isinstance(row, dict)
    }
    manifest_rows = [
        row for row in manifest.get("rows", []) if isinstance(row, dict)
    ]
    checks = [
        _check(
            "adapter_registry_manifest",
            "adapter_registry",
            "adapter registry manifest exists",
            str(manifest_path.exists()),
            manifest_path.exists(),
        ),
        _check(
            "adapter_registry_all_ok",
            "adapter_registry",
            "all_ok true",
            str(manifest.get("all_ok", "")),
            bool(manifest.get("all_ok", False)),
        ),
        _check(
            "adapter_registry_required_ids",
            "adapter_registry",
            ",".join(REQUIRED_ADAPTER_IDS),
            ",".join(sorted(adapter_ids)),
            set(REQUIRED_ADAPTER_IDS).issubset(adapter_ids),
        ),
        _check(
            "adapter_registry_boundary",
            "adapter_registry",
            "not theorem proof evidence",
            str(manifest.get("proof_evidence_boundary", ""))[:120],
            "not theorem proof evidence"
            in str(manifest.get("proof_evidence_boundary", "")),
        ),
        _check(
            "adapter_registry_jsonl_file",
            "adapter_registry",
            "adapter registry jsonl exists",
            str(jsonl_path.exists()),
            jsonl_path.exists(),
        ),
        _check(
            "adapter_registry_row_schema_file",
            "adapter_registry",
            "adapter registry row schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            "adapter_registry_row_schema_id",
            "adapter_registry",
            ADAPTER_REGISTRY_ROW_SCHEMA_ID,
            str(row_schema.get("$id", "")),
            row_schema.get("$id") == ADAPTER_REGISTRY_ROW_SCHEMA_ID,
        ),
        _check(
            "adapter_registry_jsonl_parse",
            "adapter_registry",
            "jsonl rows parse without errors",
            "; ".join(jsonl_errors[:3]),
            not jsonl_errors,
        ),
        _check(
            "adapter_registry_jsonl_row_count",
            "adapter_registry",
            "jsonl rows match manifest rows",
            f"{len(jsonl_rows)}/{len(manifest_rows)}",
            len(jsonl_rows) == len(manifest_rows),
        ),
        _check(
            "adapter_registry_manifest_schema_counts",
            "adapter_registry",
            "all manifest rows schema-valid",
            (
                f"{manifest.get('n_adapter_row_schema_valid', 0)}/"
                f"{manifest.get('n_adapters', 0)} invalid="
                f"{manifest.get('n_adapter_row_schema_invalid', 0)}"
            ),
            int(manifest.get("n_adapter_row_schema_valid", 0) or 0)
            == len(manifest_rows)
            and int(manifest.get("n_adapter_row_schema_invalid", 0) or 0) == 0,
        ),
    ]
    for idx, row in enumerate(jsonl_rows):
        row_errors = validate_adapter_registry_row(row, row_schema)
        checks.append(
            _check(
                f"adapter_registry_row_{idx}_schema_valid",
                "adapter_registry",
                "adapter registry row validates against schema",
                f"{row.get('adapter_id', idx)}: {'; '.join(row_errors[:3])}",
                not row_errors,
            )
        )
    return checks


def _component_resource_registry_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    manifest_path = (
        bundle_dir
        / "component_resource_registry"
        / "formalization_gap_planner_component_resource_registry_manifest.json"
    )
    execution_plan_jsonl_path = (
        bundle_dir
        / "component_resource_registry"
        / "formalization_gap_planner_component_resource_execution_plans.jsonl"
    )
    component_jsonl_path = (
        bundle_dir
        / "component_resource_registry"
        / "formalization_gap_planner_component_resource_registry.jsonl"
    )
    resource_jsonl_path = (
        bundle_dir
        / "component_resource_registry"
        / "formalization_gap_planner_component_resource_resources.jsonl"
    )
    resource_contract_jsonl_path = (
        bundle_dir
        / "component_resource_registry"
        / "formalization_gap_planner_component_resource_contracts.jsonl"
    )
    manifest = _read_json_no_error(manifest_path)
    component_rows, component_jsonl_errors = _read_jsonl_dict_rows_no_error(
        component_jsonl_path
    )
    resource_rows, resource_jsonl_errors = _read_jsonl_dict_rows_no_error(
        resource_jsonl_path
    )
    resource_contract_rows, resource_contract_jsonl_errors = (
        _read_jsonl_dict_rows_no_error(resource_contract_jsonl_path)
    )
    execution_plan_rows, execution_plan_jsonl_errors = _read_jsonl_dict_rows_no_error(
        execution_plan_jsonl_path
    )
    component_ids = {
        str(row.get("component_id", ""))
        for row in manifest.get("component_rows", [])
        if isinstance(row, dict)
    }
    checks = [
        _check(
            "component_resource_registry_manifest",
            "component_resource_registry",
            "component resource registry manifest exists",
            str(manifest_path.exists()),
            manifest_path.exists(),
        ),
        _check(
            "component_resource_registry_all_ok",
            "component_resource_registry",
            "all_ok true",
            str(manifest.get("all_ok", "")),
            bool(manifest.get("all_ok", False)),
        ),
        _check(
            "component_resource_registry_required_components",
            "component_resource_registry",
            ",".join(REQUIRED_COMPONENT_RESOURCE_IDS),
            ",".join(sorted(component_ids)),
            set(REQUIRED_COMPONENT_RESOURCE_IDS).issubset(component_ids),
        ),
        _check(
            "component_resource_registry_execution_plans",
            "component_resource_registry",
            "one execution plan per component row",
            f"{manifest.get('n_execution_plan_rows', 0)}/{manifest.get('n_component_rows', 0)}",
            int(manifest.get("n_component_rows", 0) or 0) > 0
            and int(manifest.get("n_execution_plan_rows", 0) or 0)
            == int(manifest.get("n_component_rows", 0) or 0)
            and int(manifest.get("n_execution_plan_rows_ok", 0) or 0)
            == int(manifest.get("n_execution_plan_rows", 0) or 0),
        ),
        _check(
            "component_resource_registry_execution_plan_jsonl",
            "component_resource_registry",
            "execution-plan JSONL exists",
            str(execution_plan_jsonl_path.exists()),
            execution_plan_jsonl_path.exists(),
        ),
        _check(
            "component_resource_registry_component_jsonl",
            "component_resource_registry",
            "component-row JSONL exists",
            str(component_jsonl_path.exists()),
            component_jsonl_path.exists(),
        ),
        _check(
            "component_resource_registry_component_jsonl_parse",
            "component_resource_registry",
            "component-row JSONL parses into object rows",
            "; ".join(component_jsonl_errors)
            if component_jsonl_errors
            else f"rows={len(component_rows)}",
            not component_jsonl_errors,
            errors=component_jsonl_errors,
        ),
        _check(
            "component_resource_registry_component_jsonl_row_count",
            "component_resource_registry",
            "component-row JSONL rows match manifest count",
            f"jsonl={len(component_rows)} manifest={manifest.get('n_component_rows', 0)}",
            len(component_rows) == int(manifest.get("n_component_rows", 0) or 0),
        ),
        _check(
            "component_resource_registry_resource_jsonl",
            "component_resource_registry",
            "resource-row JSONL exists",
            str(resource_jsonl_path.exists()),
            resource_jsonl_path.exists(),
        ),
        _check(
            "component_resource_registry_resource_jsonl_parse",
            "component_resource_registry",
            "resource-row JSONL parses into object rows",
            "; ".join(resource_jsonl_errors)
            if resource_jsonl_errors
            else f"rows={len(resource_rows)}",
            not resource_jsonl_errors,
            errors=resource_jsonl_errors,
        ),
        _check(
            "component_resource_registry_resource_jsonl_row_count",
            "component_resource_registry",
            "resource-row JSONL rows match manifest count",
            f"jsonl={len(resource_rows)} manifest={manifest.get('n_resources', 0)}",
            len(resource_rows) == int(manifest.get("n_resources", 0) or 0),
        ),
        _check(
            "component_resource_registry_contract_jsonl",
            "component_resource_registry",
            "resource-contract JSONL exists",
            str(resource_contract_jsonl_path.exists()),
            resource_contract_jsonl_path.exists(),
        ),
        _check(
            "component_resource_registry_contract_jsonl_parse",
            "component_resource_registry",
            "resource-contract JSONL parses into object rows",
            "; ".join(resource_contract_jsonl_errors)
            if resource_contract_jsonl_errors
            else f"rows={len(resource_contract_rows)}",
            not resource_contract_jsonl_errors,
            errors=resource_contract_jsonl_errors,
        ),
        _check(
            "component_resource_registry_contract_jsonl_row_count",
            "component_resource_registry",
            "resource-contract JSONL rows match manifest count",
            (
                f"jsonl={len(resource_contract_rows)} "
                f"manifest={manifest.get('n_resource_contract_rows', 0)}"
            ),
            len(resource_contract_rows)
            == int(manifest.get("n_resource_contract_rows", 0) or 0),
        ),
        _check(
            "component_resource_registry_execution_plan_jsonl_parse",
            "component_resource_registry",
            "execution-plan JSONL parses into object rows",
            "; ".join(execution_plan_jsonl_errors)
            if execution_plan_jsonl_errors
            else f"rows={len(execution_plan_rows)}",
            not execution_plan_jsonl_errors,
            errors=execution_plan_jsonl_errors,
        ),
        _check(
            "component_resource_registry_execution_plan_jsonl_row_count",
            "component_resource_registry",
            "execution-plan JSONL rows match manifest count",
            f"jsonl={len(execution_plan_rows)} manifest={manifest.get('n_execution_plan_rows', 0)}",
            len(execution_plan_rows)
            == int(manifest.get("n_execution_plan_rows", 0) or 0),
        ),
        _check(
            "component_resource_registry_frontier_floor",
            "component_resource_registry",
            "frontier resources present",
            str(manifest.get("n_frontier_resources", 0)),
            int(manifest.get("n_frontier_resources", 0) or 0) >= 10,
        ),
        _check(
            "component_resource_registry_mcp_cli_floor",
            "component_resource_registry",
            "MCP/CLI resources present",
            str(manifest.get("n_mcp_or_cli_resources", 0)),
            int(manifest.get("n_mcp_or_cli_resources", 0) or 0) >= 5,
        ),
        _check(
            "component_resource_registry_boundary",
            "component_resource_registry",
            "not theorem proof evidence",
            str(manifest.get("proof_evidence_boundary", ""))[:120],
            "not theorem proof evidence"
            in str(manifest.get("proof_evidence_boundary", "")),
        ),
    ]
    for idx, row in enumerate(component_rows):
        schema_errors = validate_component_resource_registry_component_row(row)
        checks.append(
            _check(
                f"component_resource_registry_component_row_{idx}_schema_valid",
                "component_resource_registry",
                "component JSONL row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
    for idx, row in enumerate(resource_rows):
        schema_errors = validate_component_resource_registry_resource_row(row)
        checks.append(
            _check(
                f"component_resource_registry_resource_row_{idx}_schema_valid",
                "component_resource_registry",
                "resource JSONL row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
    for idx, row in enumerate(resource_contract_rows):
        schema_errors = validate_component_resource_contract_row(row)
        checks.append(
            _check(
                f"component_resource_registry_contract_row_{idx}_schema_valid",
                "component_resource_registry",
                "resource contract JSONL row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
    for idx, row in enumerate(execution_plan_rows):
        schema_errors = validate_component_resource_execution_plan_row(row)
        checks.append(
            _check(
                f"component_resource_registry_execution_plan_row_{idx}_schema_valid",
                "component_resource_registry",
                "execution-plan JSONL row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
    return checks


def _reproduction_checks(bundle_dir: Path) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    manifest_path = (
        bundle_dir
        / "reproduce"
        / "formalization_gap_planner_reproduction_manifest.json"
    )
    report_path = (
        bundle_dir / "reproduce" / "formalization_gap_planner_reproduction.md"
    )
    manifest = _read_json_no_error(manifest_path)
    entrypoints = {
        str(row.get("entrypoint", ""))
        for row in manifest.get("entrypoints", [])
        if isinstance(row, dict)
    }
    commands = {
        str(row.get("name", "")): str(row.get("command", ""))
        for row in manifest.get("commands", [])
        if isinstance(row, dict)
    }
    optional_evaluation_truth_path = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_evaluation"
        / "formalization_gap_planner_evaluation_ground_truth.json"
    )
    expected_evaluation_truth = (
        "<bundle_dir>/artifacts/formalization_gap_planner_evaluation/"
        "formalization_gap_planner_evaluation_ground_truth.json"
        if optional_evaluation_truth_path.exists()
        else "<bundle_dir>/benchmark/formalization_gap_planner_ground_truth.json"
    )
    artifacts = set(_str_tuple(manifest.get("bundle_relative_artifacts", [])))
    required_command_names = set(REQUIRED_REPRODUCTION_COMMANDS)
    command_names = set(commands)
    required_commands_ok = all(
        name in commands and snippet in commands.get(name, "")
        for name, snippet in REQUIRED_REPRODUCTION_COMMANDS.items()
    )
    refinement_command_names = {
        "run_refinement_queue",
        "run_refinement_adapter_responses",
        "run_minimal_delta_audit_feedback",
        "run_refinement_evidence",
        "run_route_revision_overlay",
        "run_route_stability_audit",
        "run_route_replan_handoff",
        "audit_route_replan_handoff",
        "run_proof_state_triage",
        "run_interactive_session",
    }
    local_adapter_command_names = {
        "run_local_literature_adapter",
        "run_local_formal_source_adapter",
        "run_local_proof_state_adapter",
    }
    prover_feedback_command_names = {
        "run_prover_adapter_feedback",
        "run_refinement_evidence",
    }
    return [
        _check(
            "reproduction_manifest",
            "reproduction",
            "reproduction manifest exists",
            str(manifest_path.exists()),
            manifest_path.exists(),
        ),
        _check(
            "reproduction_report",
            "reproduction",
            "reproduction markdown exists",
            str(report_path.exists()),
            report_path.exists(),
        ),
        _check(
            "reproduction_component",
            "reproduction",
            "formalization_gap_planner_reproduction_manifest",
            str(manifest.get("component_name", "")),
            manifest.get("component_name")
            == "formalization_gap_planner_reproduction_manifest",
        ),
        _check(
            "reproduction_required_entrypoints",
            "reproduction",
            ",".join(REQUIRED_REPRODUCTION_ENTRYPOINTS),
            ",".join(sorted(entrypoints)),
            set(REQUIRED_REPRODUCTION_ENTRYPOINTS).issubset(entrypoints),
        ),
        _check(
            "reproduction_commands_present",
            "reproduction",
            "all required reproduction commands",
            str(len(commands)),
            len(commands) >= len(REQUIRED_REPRODUCTION_COMMANDS)
            and required_command_names.issubset(command_names),
        ),
        _check(
            "reproduction_required_commands",
            "reproduction",
            ",".join(sorted(REQUIRED_REPRODUCTION_COMMANDS)),
            ",".join(sorted(commands)),
            required_commands_ok,
        ),
        _check(
            "reproduction_bundle_audit_command",
            "reproduction",
            "publication-bundle-audit command present",
            commands.get("audit_downloaded_bundle", ""),
            "formalization-gap-planner-publication-bundle-audit"
            in commands.get("audit_downloaded_bundle", ""),
        ),
        _check(
            "reproduction_standalone_command",
            "reproduction",
            "standalone-plan command present",
            commands.get("run_standalone_planner", ""),
            "formalization-gap-planner-standalone-plan"
            in commands.get("run_standalone_planner", ""),
        ),
        _check(
            "reproduction_benchmark_audit_command",
            "reproduction",
            "benchmark-audit command present",
            commands.get("audit_benchmark", ""),
            "formalization-gap-planner-benchmark-audit"
            in commands.get("audit_benchmark", ""),
        ),
        _check(
            "reproduction_evaluation_command",
            "reproduction",
            "evaluation command present",
            commands.get("run_evaluation", ""),
            "formalization-gap-planner-evaluation"
            in commands.get("run_evaluation", ""),
        ),
        _check(
            "reproduction_evaluation_ground_truth_source",
            "reproduction",
            "evaluation command uses bundled evaluation truth when available",
            commands.get("run_evaluation", ""),
            expected_evaluation_truth in commands.get("run_evaluation", ""),
        ),
        _check(
            "reproduction_target_intake_command",
            "reproduction",
            "target-intake command present",
            commands.get("run_target_intake", ""),
            "formalization-gap-planner-target-intake"
            in commands.get("run_target_intake", ""),
        ),
        _check(
            "reproduction_route_adoption_blocker_taxonomy_command",
            "reproduction",
            "route-adoption blocker taxonomy export command present",
            commands.get("export_route_adoption_blocker_taxonomy", ""),
            "formalization-gap-planner-route-adoption-blocker-taxonomy"
            in commands.get("export_route_adoption_blocker_taxonomy", "")
            and "formalization_gap_planner_route_adoption_blocker_taxonomy"
            in commands.get("export_route_adoption_blocker_taxonomy", ""),
        ),
        _check(
            "reproduction_reuse_smoke_command",
            "reproduction",
            "public reuse-smoke command uses bundled target-intake example and prompt-only Anthropic staging",
            commands.get("run_reuse_smoke", ""),
            "formalization-gap-planner-reuse-smoke"
            in commands.get("run_reuse_smoke", "")
            and "examples/formalization_gap_planner_target_intake_example.json"
            in commands.get("run_reuse_smoke", "")
            and "--target-prover-family"
            in commands.get("run_reuse_smoke", "")
            and "--llm-route-planner-provider anthropic"
            in commands.get("run_reuse_smoke", "")
            and "--llm-route-planner-model-tier auto"
            in commands.get("run_reuse_smoke", "")
            and "--feedback-llm-route-planner-provider anthropic"
            in commands.get("run_reuse_smoke", "")
            and "--feedback-llm-route-planner-model-tier auto"
            in commands.get("run_reuse_smoke", "")
            and "--llm-route-planner-invoke-provider"
            not in commands.get("run_reuse_smoke", "")
            and "--feedback-llm-route-planner-invoke-provider"
            not in commands.get("run_reuse_smoke", ""),
        ),
        _check(
            "reproduction_runtime_handoff_reuse_smoke_command",
            "reproduction",
            "runtime handoff reuse-smoke command consumes runtime target-intake JSON and remains prompt-only",
            commands.get("run_runtime_handoff_reuse_smoke", ""),
            "formalization-gap-planner-reuse-smoke"
            in commands.get("run_runtime_handoff_reuse_smoke", "")
            and "runtime_formalization_gap_planner_target_intake"
            in commands.get("run_runtime_handoff_reuse_smoke", "")
            and "<runtime_target_intake_json>"
            in commands.get("run_runtime_handoff_reuse_smoke", "")
            and "--target-library-snapshot-ref <runtime-library-snapshot-ref>"
            in commands.get("run_runtime_handoff_reuse_smoke", "")
            and "--llm-route-planner-provider anthropic"
            in commands.get("run_runtime_handoff_reuse_smoke", "")
            and "--feedback-llm-route-planner-provider anthropic"
            in commands.get("run_runtime_handoff_reuse_smoke", "")
            and "--llm-route-planner-invoke-provider"
            not in commands.get("run_runtime_handoff_reuse_smoke", "")
            and "--feedback-llm-route-planner-invoke-provider"
            not in commands.get("run_runtime_handoff_reuse_smoke", ""),
        ),
        _check(
            "reproduction_llm_route_planner_command",
            "reproduction",
            "initial LLM route planner consumes target-intake seed, target-intake context, and component-resource registry context",
            commands.get("run_llm_route_planner", ""),
            "formalization-gap-planner-llm-route-planner"
            in commands.get("run_llm_route_planner", "")
            and "formalization_gap_planner_target_intake_standalone_seed.json"
            in commands.get("run_llm_route_planner", "")
            and "--formalization-gap-planner-target-intake-dir"
            in commands.get("run_llm_route_planner", "")
            and "formalization_gap_planner_target_intake"
            in commands.get("run_llm_route_planner", "")
            and "--formalization-gap-planner-component-resource-registry-dir"
            in commands.get("run_llm_route_planner", "")
            and "component_resource_registry"
            in commands.get("run_llm_route_planner", ""),
        ),
        _check(
            "reproduction_component_resource_registry_command",
            "reproduction",
            "component-resource-registry-audit command present",
            commands.get("audit_component_resource_registry", ""),
            "formalization-gap-planner-component-resource-registry-audit"
            in commands.get("audit_component_resource_registry", ""),
        ),
        _check(
            "reproduction_action_resource_plan_command",
            "reproduction",
            "action-resource-plan command consumes primitive queue and component registry",
            commands.get("export_action_resource_plan", ""),
            "formalization-gap-planner-action-resource-plan"
            in commands.get("export_action_resource_plan", "")
            and "formalization_gap_planner_primitive_action_queue"
            in commands.get("export_action_resource_plan", "")
            and "component_resource_registry"
            in commands.get("export_action_resource_plan", ""),
        ),
        _check(
            "reproduction_llm_route_payload_validation_command",
            "reproduction",
            "initial LLM route payload validator uses request-bound staged planner context",
            commands.get("validate_llm_route_payloads", ""),
            "formalization-gap-planner-llm-route-planner-response-payload-validate"
            in commands.get("validate_llm_route_payloads", "")
            and "--request-context"
            in commands.get("validate_llm_route_payloads", "")
            and "formalization_gap_planner_llm_route_planner"
            in commands.get("validate_llm_route_payloads", "")
            and "<reviewed_llm_route_payload_json>"
            in commands.get("validate_llm_route_payloads", ""),
        ),
        _check(
            "reproduction_resource_request_queue_command",
            "reproduction",
            "resource-request-queue command consumes action-resource plan output",
            commands.get("export_resource_request_queue", ""),
            "formalization-gap-planner-resource-request-queue"
            in commands.get("export_resource_request_queue", "")
            and "formalization_gap_planner_action_resource_plan"
            in commands.get("export_resource_request_queue", ""),
        ),
        _check(
            "reproduction_resource_response_ledger_command",
            "reproduction",
            "resource-response-ledger command consumes resource request-queue output",
            commands.get("export_resource_response_ledger", ""),
            "formalization-gap-planner-resource-response-ledger"
            in commands.get("export_resource_response_ledger", "")
            and "formalization_gap_planner_resource_request_queue"
            in commands.get("export_resource_response_ledger", ""),
        ),
        _check(
            "reproduction_minimal_delta_audit_command",
            "reproduction",
            "minimal-delta audit command consumes the portable planner output",
            commands.get("run_minimal_delta_audit", ""),
            "formalization-gap-planner-minimal-delta-audit"
            in commands.get("run_minimal_delta_audit", "")
            and "goal_conditioned_minimal_formalization_plan"
            in commands.get("run_minimal_delta_audit", ""),
        ),
        _check(
            "reproduction_route_revision_overlay_consumes_resource_response_ledger",
            "reproduction",
            "route-revision overlay command consumes validated resource-response ledger feedback",
            commands.get("run_route_revision_overlay", ""),
            "formalization-gap-planner-route-revision-overlay"
            in commands.get("run_route_revision_overlay", "")
            and "--formalization-gap-planner-resource-response-ledger-dir"
            in commands.get("run_route_revision_overlay", "")
            and "formalization_gap_planner_resource_response_ledger"
            in commands.get("run_route_revision_overlay", ""),
        ),
        _check(
            "reproduction_refinement_loop_commands",
            "reproduction",
            ",".join(sorted(refinement_command_names)),
            ",".join(sorted(command_names.intersection(refinement_command_names))),
            refinement_command_names.issubset(command_names)
            and all(
                "formalization_gap_planner_refinement_queue"
                in commands.get(name, "")
                for name in (
                    "run_refinement_adapter_responses",
                    "run_refinement_evidence",
                    "run_interactive_session",
                )
            ),
        ),
        _check(
            "reproduction_route_replan_commands",
            "reproduction",
            "handoff, handoff audit, triage, and interactive-session handoff inputs",
            " | ".join(
                commands.get(name, "")
                for name in (
                    "run_route_replan_handoff",
                    "audit_route_replan_handoff",
                    "run_proof_state_triage",
                    "run_interactive_session",
                )
            ),
            "formalization_gap_planner_route_revision_overlay"
            in commands.get("run_route_replan_handoff", "")
            and "formalization_gap_planner_route_stability_audit"
            in commands.get("run_route_replan_handoff", "")
            and "formalization_gap_planner_route_replan_handoff"
            in commands.get("audit_route_replan_handoff", "")
            and "formalization_gap_planner_route_revision_overlay"
            in commands.get("run_proof_state_triage", "")
            and "formalization_gap_planner_route_replan_handoff"
            in commands.get("run_interactive_session", "")
            and "formalization_gap_planner_proof_state_triage"
            in commands.get("run_interactive_session", ""),
        ),
        _check(
            "reproduction_feedback_llm_route_planner_command",
            "reproduction",
            "feedback LLM route planner consumes route-replan seed, target-intake context, and interactive-session context",
            commands.get("run_feedback_llm_route_planner", ""),
            "formalization-gap-planner-llm-route-planner"
            in commands.get("run_feedback_llm_route_planner", "")
            and "formalization_gap_planner_route_replan_handoff/"
            in commands.get("run_feedback_llm_route_planner", "")
            and "--formalization-gap-planner-target-intake-dir"
            in commands.get("run_feedback_llm_route_planner", "")
            and "formalization_gap_planner_target_intake"
            in commands.get("run_feedback_llm_route_planner", "")
            and "--formalization-gap-planner-interactive-session-dir"
            in commands.get("run_feedback_llm_route_planner", "")
            and "formalization_gap_planner_interactive_session"
            in commands.get("run_feedback_llm_route_planner", "")
            and "--formalization-gap-planner-route-revision-overlay-dir"
            in commands.get("run_feedback_llm_route_planner", "")
            and "--formalization-gap-planner-resource-response-ledger-dir"
            in commands.get("run_feedback_llm_route_planner", "")
            and "--formalization-gap-planner-component-resource-registry-dir"
            in commands.get("run_feedback_llm_route_planner", "")
            and "component_resource_registry"
            in commands.get("run_feedback_llm_route_planner", ""),
        ),
        _check(
            "reproduction_feedback_llm_route_payload_validation_command",
            "reproduction",
            "feedback LLM route payload validator uses request-bound staged planner context",
            commands.get("validate_feedback_llm_route_payloads", ""),
            "formalization-gap-planner-llm-route-planner-response-payload-validate"
            in commands.get("validate_feedback_llm_route_payloads", "")
            and "--request-context"
            in commands.get("validate_feedback_llm_route_payloads", "")
            and "formalization_gap_planner_feedback_llm_route_planner"
            in commands.get("validate_feedback_llm_route_payloads", "")
            and "<reviewed_feedback_llm_route_payload_json>"
            in commands.get("validate_feedback_llm_route_payloads", ""),
        ),
        _check(
            "reproduction_minimal_delta_audit_feedback_command",
            "reproduction",
            "minimal-delta audit feedback consumes audit decisions and baseline responses before local adapters",
            commands.get("run_minimal_delta_audit_feedback", ""),
            "formalization-gap-planner-minimal-delta-audit-feedback"
            in commands.get("run_minimal_delta_audit_feedback", "")
            and "formalization_gap_planner_minimal_delta_audit"
            in commands.get("run_minimal_delta_audit_feedback", "")
            and "formalization_gap_planner_refinement_adapter/"
            in commands.get("run_minimal_delta_audit_feedback", "")
            and "formalization_gap_planner_refinement_evidence_responses.jsonl"
            in commands.get("run_minimal_delta_audit_feedback", ""),
        ),
        _check(
            "reproduction_local_adapter_chain_commands",
            "reproduction",
            ",".join(sorted(local_adapter_command_names)),
            ",".join(sorted(command_names.intersection(local_adapter_command_names))),
            local_adapter_command_names.issubset(command_names)
            and "formalization_gap_planner_minimal_delta_audit_feedback_adapter/"
            in commands.get("run_local_literature_adapter", "")
            and "formalization_gap_planner_local_literature_adapter/"
            in commands.get("run_local_formal_source_adapter", "")
            and "formalization_gap_planner_local_formal_source_adapter/"
            in commands.get("run_local_proof_state_adapter", ""),
        ),
        _check(
            "reproduction_local_feedback_to_evidence_command",
            "reproduction",
            "target-prover feedback adapter consumes local proof-state responses before refinement evidence",
            commands.get("run_prover_adapter_feedback", ""),
            "formalization_gap_planner_local_proof_state_adapter/"
            in commands.get("run_prover_adapter_feedback", "")
            and "formalization_gap_planner_refinement_evidence_responses.jsonl"
            in commands.get("run_prover_adapter_feedback", ""),
        ),
        _check(
            "reproduction_prover_adapter_feedback_to_evidence_command",
            "reproduction",
            ",".join(sorted(prover_feedback_command_names)),
            " | ".join(commands.get(name, "") for name in sorted(prover_feedback_command_names)),
            prover_feedback_command_names.issubset(command_names)
            and "formalization-gap-planner-prover-adapter-feedback"
            in commands.get("run_prover_adapter_feedback", "")
            and "formalization_gap_planner_prover_adapter_contract"
            in commands.get("run_prover_adapter_feedback", "")
            and "formalization_gap_planner_cross_prover_matrix_audit"
            in commands.get("run_prover_adapter_feedback", "")
            and "formalization_gap_planner_prover_adapter_feedback_adapter/"
            in commands.get("run_refinement_evidence", "")
            and "formalization_gap_planner_refinement_evidence_responses.jsonl"
            in commands.get("run_refinement_evidence", ""),
        ),
        _check(
            "reproduction_contract_artifacts",
            "reproduction",
            "contract, adapter/component registries, and examples listed",
            ",".join(sorted(artifacts)),
            {
                "contract/formalization_gap_planner_portable_contract.json",
                "contract/ai_statistician_llm_model_policy.json",
                "contract/ai_statistician_llm_model_policy.md",
                "contract/formalization_gap_planner_standalone_input.schema.json",
                "contract/formalization_gap_planner_prover_adapter_packet.schema.json",
                "contract/formalization_gap_planner_prover_adapter_response_validation_row.schema.json",
                "contract/formalization_gap_planner_refinement_work_item.schema.json",
                "contract/formalization_gap_planner_refinement_tool_response.schema.json",
                "contract/formalization_gap_planner_refinement_evidence_row.schema.json",
                "contract/formalization_gap_planner_interactive_session_row.schema.json",
                "contract/formalization_gap_planner_interactive_decision_policy_row.schema.json",
                "contract/formalization_gap_planner_minimal_delta_decision_row.schema.json",
                "contract/formalization_gap_planner_portable_plan_audit_row.schema.json",
                "contract/formalization_gap_planner_library_coverage_map_row.schema.json",
                "contract/formalization_gap_planner_primitive_action_queue_row.schema.json",
                "contract/formalization_gap_planner_action_resource_plan_row.schema.json",
                "contract/formalization_gap_planner_resource_request_queue_row.schema.json",
                "contract/formalization_gap_planner_resource_response.schema.json",
                "contract/formalization_gap_planner_resource_response_ledger_row.schema.json",
                "contract/formalization_gap_planner_source_grounding_row.schema.json",
                "contract/formalization_gap_planner_route_revision_overlay_row.schema.json",
                "contract/formalization_gap_planner_route_stability_audit_row.schema.json",
                "contract/formalization_gap_planner_route_replan_handoff_row.schema.json",
                "contract/formalization_gap_planner_route_replan_handoff_audit_row.schema.json",
                "contract/formalization_gap_planner_proof_state_triage_row.schema.json",
                "contract/formalization_gap_planner_ablation_study_row.schema.json",
                "contract/formalization_gap_planner_route_alignment_edge.schema.json",
                "contract/formalization_gap_planner_llm_route_planner_route_planning_brief.schema.json",
                "contract/formalization_gap_planner_route_adoption_blocker_taxonomy.schema.json",
                "contract/formalization_gap_planner_route_adoption_blocker_taxonomy_manifest.schema.json",
                "contract/formalization_gap_planner_route_adoption_blocker_taxonomy.json",
                "contract/formalization_gap_planner_benchmark_route.schema.json",
                "contract/formalization_gap_planner_evaluation_row.schema.json",
                "contract/formalization_gap_planner_adapter_registry_row.schema.json",
                "contract/formalization_gap_planner_cross_prover_matrix_audit_row.schema.json",
                "contract/formalization_gap_planner_component_resource_resource_row.schema.json",
                "contract/formalization_gap_planner_component_resource_component_row.schema.json",
                "contract/formalization_gap_planner_component_resource_execution_plan.schema.json",
                "contract/formalization_gap_planner_component_resource_contract_row.schema.json",
                "benchmark/formalization_gap_planner_benchmark_routes.jsonl",
                "benchmark/formalization_gap_planner_benchmark_route.schema.json",
                "benchmark_audit/formalization_gap_planner_benchmark_audit_manifest.json",
                "adapter_registry/formalization_gap_planner_adapter_registry_manifest.json",
                "adapter_registry/formalization_gap_planner_adapter_registry.jsonl",
                "adapter_registry/formalization_gap_planner_adapter_registry_row.schema.json",
                "component_resource_registry/formalization_gap_planner_component_resource_registry_manifest.json",
                "component_resource_registry/formalization_gap_planner_component_resource_registry.jsonl",
                "component_resource_registry/formalization_gap_planner_component_resource_resources.jsonl",
                "component_resource_registry/formalization_gap_planner_component_resource_execution_plans.jsonl",
                "component_resource_registry/formalization_gap_planner_component_resource_contracts.jsonl",
                "component_resource_registry/formalization_gap_planner_component_resource_resource_row.schema.json",
                "component_resource_registry/formalization_gap_planner_component_resource_component_row.schema.json",
                "component_resource_registry/formalization_gap_planner_component_resource_execution_plan.schema.json",
                "component_resource_registry/formalization_gap_planner_component_resource_contract_row.schema.json",
                "examples/formalization_gap_planner_standalone_example.json",
                "examples/formalization_gap_planner_target_intake_example.json",
            }.issubset(artifacts),
        ),
        _check(
            "reproduction_reuse_targets",
            "reproduction",
            ",".join(REQUIRED_REUSE_TARGETS),
            ",".join(sorted(_str_tuple(manifest.get("portable_reuse_targets", [])))),
            set(REQUIRED_REUSE_TARGETS).issubset(
                set(_str_tuple(manifest.get("portable_reuse_targets", [])))
            ),
        ),
        _check(
            "reproduction_boundary",
            "proof_boundary",
            "not theorem proof evidence",
            str(manifest.get("proof_evidence_boundary", ""))[:160],
            "not theorem proof evidence"
            in str(manifest.get("proof_evidence_boundary", "")),
        ),
    ]


def _example_input_checks(bundle_dir: Path) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    standalone_path = bundle_dir / "examples" / "formalization_gap_planner_standalone_example.json"
    target_intake_path = (
        bundle_dir / "examples" / "formalization_gap_planner_target_intake_example.json"
    )
    standalone_payload = _read_json_no_error(standalone_path)
    target_intake_raw_payload = _read_json_no_error(target_intake_path)
    standalone_errors = validate_standalone_input_payload(standalone_payload)
    example_target_provers = {
        _target_prover_key(standalone_payload.get("target_prover_family", "")),
        _target_prover_key(target_intake_raw_payload.get("target_prover_family", "")),
    }
    example_target_provers.discard("")
    try:
        target_payload = normalize_formalization_gap_planner_target_intake(
            target_intake_path,
            None,
        )
        target_errors = tuple(str(error) for error in target_payload.get("errors", []))
        target_ok = bool(target_payload.get("all_ok", False))
    except Exception as exc:  # pragma: no cover - defensive audit surface
        target_errors = (f"{type(exc).__name__}: {exc}",)
        target_ok = False
    return [
        _check(
            "standalone_example_exists",
            "examples",
            "standalone example exists",
            str(standalone_path.exists()),
            standalone_path.exists(),
        ),
        _check(
            "standalone_example_valid",
            "examples",
            "validate_standalone_input_payload has no errors",
            "; ".join(standalone_errors),
            not standalone_errors,
        ),
        _check(
            "target_intake_example_exists",
            "examples",
            "target-intake example exists",
            str(target_intake_path.exists()),
            target_intake_path.exists(),
        ),
        _check(
            "target_intake_example_normalizes",
            "examples",
            "target-intake example normalizes all_ok",
            "; ".join(target_errors),
            target_ok,
        ),
        _check(
            "example_target_prover_coverage",
            "examples",
            "examples include lean4 and at least one non-Lean prover target",
            ",".join(sorted(example_target_provers)),
            "lean4" in example_target_provers
            and any(prover != "lean4" for prover in example_target_provers),
        ),
    ]


def _doc_checks(bundle_dir: Path) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    checks = []
    for filename in REQUIRED_DOCS:
        path = bundle_dir / "docs" / filename
        checks.append(
            _check(
                "doc_" + filename.replace(".", "_"),
                "docs",
                "doc exists",
                str(path.exists()),
                path.exists(),
            )
        )
    return checks


def _optional_artifact_checks(
    bundle_dir: Path,
    manifest: dict[str, Any],
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    checks = []
    for artifact in manifest.get("optional_artifacts", []):
        if not isinstance(artifact, dict) or not artifact.get("requested"):
            continue
        copied_files = _str_tuple(artifact.get("copied_files", []))
        missing_files = _str_tuple(artifact.get("missing_files", []))
        files_exist = all(Path(path).exists() for path in copied_files)
        inside_bundle = all(_is_inside(Path(path), bundle_dir) for path in copied_files)
        checks.append(
            _check(
                "optional_" + str(artifact.get("artifact_name", "")),
                "optional_artifacts",
                "requested artifact files copied inside bundle",
                f"copied={len(copied_files)} missing={len(missing_files)}",
                bool(copied_files)
                and not missing_files
                and files_exist
                and inside_bundle
                and bool(artifact.get("ok", False)),
            )
        )
        artifact_name = str(artifact.get("artifact_name", ""))
        if artifact_name == "formalization_gap_planner_target_intake":
            checks.extend(_target_intake_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_llm_route_planner":
            checks.extend(
                _llm_route_planner_optional_checks(
                    bundle_dir,
                    artifact_name="formalization_gap_planner_llm_route_planner",
                    check_prefix="optional_llm_route_planner",
                )
            )
        if artifact_name == "formalization_gap_planner_feedback_llm_route_planner":
            checks.extend(
                _llm_route_planner_optional_checks(
                    bundle_dir,
                    artifact_name="formalization_gap_planner_feedback_llm_route_planner",
                    check_prefix="optional_feedback_llm_route_planner",
                )
            )
        if (
            artifact_name
            == "formalization_gap_planner_llm_route_planner_response_payload_validation"
        ):
            checks.extend(
                _llm_route_planner_response_payload_validation_optional_checks(
                    bundle_dir
                )
            )
        if artifact_name == "goal_conditioned_minimal_formalization_plan":
            checks.extend(_goal_conditioned_plan_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_route_replan_handoff":
            checks.extend(_route_replan_handoff_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_route_replan_handoff_audit":
            checks.extend(_route_replan_handoff_audit_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_runtime_handoff_audit":
            checks.extend(_runtime_handoff_audit_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_cross_prover_matrix_audit":
            checks.extend(_cross_prover_matrix_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_adapter_registry_audit":
            checks.extend(
                _generic_audit_optional_checks(
                    bundle_dir,
                    artifact_name="formalization_gap_planner_adapter_registry_audit",
                    manifest_filename=(
                        "formalization_gap_planner_adapter_registry_audit_manifest.json"
                    ),
                    jsonl_filename="formalization_gap_planner_adapter_registry_audit.jsonl",
                    check_prefix="optional_adapter_registry_audit_check",
                )
            )
        if artifact_name == "formalization_gap_planner_component_resource_registry_audit":
            checks.extend(
                _generic_audit_optional_checks(
                    bundle_dir,
                    artifact_name=(
                        "formalization_gap_planner_component_resource_registry_audit"
                    ),
                    manifest_filename=(
                        "formalization_gap_planner_component_resource_registry_audit_manifest.json"
                    ),
                    jsonl_filename=(
                        "formalization_gap_planner_component_resource_registry_audit.jsonl"
                    ),
                    check_prefix="optional_component_resource_registry_audit_check",
                )
            )
        if artifact_name == "formalization_gap_planner_prover_adapter_contract":
            checks.extend(_prover_adapter_contract_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_evaluation":
            checks.extend(_evaluation_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_interactive_session":
            checks.extend(_interactive_session_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_refinement_evidence":
            checks.extend(_refinement_evidence_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_refinement_queue":
            checks.extend(_refinement_queue_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_minimal_delta_audit":
            checks.extend(_minimal_delta_audit_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_source_grounding_audit":
            checks.extend(_source_grounding_audit_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_refinement_adapter":
            checks.extend(_refinement_adapter_optional_checks(bundle_dir))
        if (
            artifact_name
            == "formalization_gap_planner_minimal_delta_audit_feedback_adapter"
        ):
            checks.extend(
                _minimal_delta_audit_feedback_adapter_optional_checks(bundle_dir)
            )
        if artifact_name == "formalization_gap_planner_prover_adapter_feedback_adapter":
            checks.extend(_prover_adapter_feedback_adapter_optional_checks(bundle_dir))
        if artifact_name in {
            "formalization_gap_planner_local_literature_adapter",
            "formalization_gap_planner_local_formal_source_adapter",
            "formalization_gap_planner_local_proof_state_adapter",
        }:
            checks.extend(_local_adapter_optional_checks(bundle_dir, artifact_name))
        if artifact_name == "formalization_gap_planner_route_stability_audit":
            checks.extend(_route_stability_audit_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_route_revision_overlay":
            checks.extend(_route_revision_overlay_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_proof_state_triage":
            checks.extend(_proof_state_triage_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_ablation_study":
            checks.extend(_ablation_study_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_portable_plan_audit":
            checks.extend(_portable_plan_audit_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_library_coverage_map":
            checks.extend(_library_coverage_map_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_primitive_action_queue":
            checks.extend(_primitive_action_queue_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_action_resource_plan":
            checks.extend(_action_resource_plan_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_resource_request_queue":
            checks.extend(_resource_request_queue_optional_checks(bundle_dir))
        if artifact_name == "formalization_gap_planner_resource_response_ledger":
            checks.extend(_resource_response_ledger_optional_checks(bundle_dir))
    return checks


def _target_intake_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = bundle_dir / "artifacts" / "formalization_gap_planner_target_intake"
    manifest_path = artifact_dir / "formalization_gap_planner_target_intake_manifest.json"
    rows_jsonl_path = artifact_dir / "formalization_gap_planner_target_intake.jsonl"
    standalone_seed_path = (
        artifact_dir / "formalization_gap_planner_target_intake_standalone_seed.json"
    )
    schema_path = artifact_dir / "formalization_gap_planner_target_intake.schema.json"
    row_schema_path = (
        artifact_dir / "formalization_gap_planner_target_intake_row.schema.json"
    )
    manifest = _read_json_no_error(manifest_path)
    input_schema = _read_json_no_error(schema_path)
    row_schema = _read_json_no_error(row_schema_path)
    seed_payload = _read_json_no_error(standalone_seed_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    seed_errors = validate_standalone_input_payload(seed_payload)
    checks = [
        _check(
            "optional_target_intake_all_ok",
            "optional_artifacts",
            "target-intake manifest all_ok",
            str(manifest.get("all_ok", "")),
            bool(manifest.get("all_ok", False)),
        ),
        _check(
            "optional_target_intake_component",
            "optional_artifacts",
            "formalization_gap_planner_target_intake",
            str(manifest.get("component_name", "")),
            manifest.get("component_name") == "formalization_gap_planner_target_intake",
        ),
        _check(
            "optional_target_intake_boundary",
            "optional_artifacts",
            "not theorem proof evidence",
            str(manifest.get("proof_evidence_boundary", ""))[:160],
            "not theorem proof evidence"
            in str(manifest.get("proof_evidence_boundary", "")).lower(),
        ),
        _check(
            "optional_target_intake_schema_file",
            "optional_artifacts",
            "optional target-intake input schema exists",
            str(schema_path.exists()),
            schema_path.exists(),
        ),
        _check(
            "optional_target_intake_schema_id",
            "optional_artifacts",
            FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_SCHEMA_ID,
            str(input_schema.get("$id", "")),
            input_schema.get("$id") == FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_SCHEMA_ID,
        ),
        _check(
            "optional_target_intake_row_schema_file",
            "optional_artifacts",
            "optional target-intake row schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            "optional_target_intake_row_schema_id",
            "optional_artifacts",
            FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_ROW_SCHEMA_ID,
            str(row_schema.get("$id", "")),
            row_schema.get("$id")
            == FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_ROW_SCHEMA_ID,
        ),
        _check(
            "optional_target_intake_jsonl_parse",
            "optional_artifacts",
            "target-intake JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_target_intake_jsonl_row_count",
            "optional_artifacts",
            "target-intake JSONL rows match manifest target count",
            f"jsonl={len(rows)} manifest={manifest.get('n_targets', 0)}",
            len(rows) == int(manifest.get("n_targets", 0) or 0),
        ),
        _check(
            "optional_target_intake_standalone_seed_contract",
            "optional_artifacts",
            "standalone seed validates against public standalone-input contract",
            "; ".join(seed_errors) if seed_errors else "ok",
            not seed_errors,
            errors=tuple(seed_errors),
        ),
    ]
    for idx, row in enumerate(rows):
        row_schema_errors = validate_target_intake_row(row, row_schema)
        checks.append(
            _check(
                f"optional_target_intake_row_{idx}_schema_valid",
                "optional_artifacts",
                "target-intake row validates against public row schema",
                "; ".join(row_schema_errors) if row_schema_errors else "ok",
                not row_schema_errors,
                errors=tuple(row_schema_errors),
            )
        )
        contract_errors = _target_intake_row_contract_errors(row)
        checks.append(
            _check(
                f"optional_target_intake_row_{idx}_contract_valid",
                "optional_artifacts",
                "target-intake row preserves public output contract",
                "; ".join(contract_errors) if contract_errors else "ok",
                not contract_errors,
                errors=contract_errors,
            )
        )
    return checks


def _llm_route_planner_response_payload_validation_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_llm_route_planner_response_payload_validation"
    )
    manifest_path = (
        artifact_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.json"
    )
    rows_jsonl_path = (
        artifact_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation.jsonl"
    )
    response_payload_schema_path = (
        artifact_dir
        / "formalization_gap_planner_llm_route_planner_response_payload.schema.json"
    )
    validation_manifest_schema_path = (
        artifact_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.schema.json"
    )
    validation_row_schema_path = (
        artifact_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_row.schema.json"
    )
    manifest = _read_json_no_error(manifest_path)
    response_payload_schema = _read_json_no_error(response_payload_schema_path)
    validation_manifest_schema = _read_json_no_error(validation_manifest_schema_path)
    validation_row_schema = _read_json_no_error(validation_row_schema_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    manifest_rows = _dict_tuple(manifest.get("rows", []))
    manifest_contract_errors = (
        validate_llm_route_planner_response_payload_validation_manifest(
            manifest,
            validation_manifest_schema,
        )
    )
    valid_rows = sum(1 for row in rows if bool(row.get("ok", False)))
    invalid_rows = len(rows) - valid_rows
    count_errors: list[str] = []
    if len(rows) != int(manifest.get("n_payloads", 0) or 0):
        count_errors.append("JSONL row count must match manifest n_payloads")
    if len(manifest_rows) != len(rows):
        count_errors.append("manifest embedded rows must match JSONL row count")
    if valid_rows != int(manifest.get("n_valid_payloads", 0) or 0):
        count_errors.append("valid JSONL rows must match manifest n_valid_payloads")
    if invalid_rows != int(manifest.get("n_invalid_payloads", 0) or 0):
        count_errors.append("invalid JSONL rows must match manifest n_invalid_payloads")
    manifest_request_bound_payloads = int(
        manifest.get("n_request_bound_payloads", 0) or 0
    )
    manifest_schema_errors = int(manifest.get("n_schema_errors", 0) or 0)
    manifest_request_context_errors = int(
        manifest.get("n_request_context_errors", 0) or 0
    )
    manifest_request_context_packets = int(
        manifest.get("n_request_context_packets", 0) or 0
    )
    manifest_request_contexts_with_inventory = int(
        manifest.get("n_request_contexts_with_context_packet_inventory", 0) or 0
    )
    manifest_request_bound_payloads_with_inventory = int(
        manifest.get(
            "n_request_bound_payloads_with_context_packet_inventory",
            0,
        )
        or 0
    )
    manifest_request_bound_context_inventory_total_rows = int(
        manifest.get(
            "n_request_bound_payload_context_inventory_total_rows",
            0,
        )
        or 0
    )
    manifest_request_bound_payloads_with_preconditions = int(
        manifest.get(
            "n_request_bound_payloads_with_route_adoption_preconditions",
            0,
        )
        or 0
    )
    manifest_request_bound_payloads_with_blocking_preconditions = int(
        manifest.get(
            "n_request_bound_payloads_with_blocking_route_adoption_preconditions",
            0,
        )
        or 0
    )
    manifest_request_bound_precondition_known_blockers = int(
        manifest.get(
            "n_request_bound_payload_route_adoption_precondition_known_blockers",
            0,
        )
        or 0
    )
    manifest_request_bound_precondition_required_fields = int(
        manifest.get(
            "n_request_bound_payload_route_adoption_precondition_required_response_fields",
            0,
        )
        or 0
    )
    manifest_request_bound_precondition_target_primitives = int(
        manifest.get(
            "n_request_bound_payload_route_adoption_precondition_target_primitives",
            0,
        )
        or 0
    )
    row_request_bound_payloads = sum(
        1
        for row in rows
        if str(row.get("request_context_validation_mode", ""))
        == "request_bound"
    )
    row_request_bound_payloads_with_inventory = sum(
        1
        for row in rows
        if str(row.get("request_context_validation_mode", ""))
        == "request_bound"
        and bool(row.get("request_context_inventory_present", False))
    )
    row_request_bound_context_inventory_total_rows = sum(
        int(row.get("request_context_inventory_total_rows", 0) or 0)
        for row in rows
        if str(row.get("request_context_validation_mode", ""))
        == "request_bound"
    )
    row_request_bound_payloads_with_preconditions = sum(
        1
        for row in rows
        if str(row.get("request_context_validation_mode", ""))
        == "request_bound"
        and bool(row.get("request_context_route_adoption_precondition_present", False))
    )
    row_request_bound_payloads_with_blocking_preconditions = sum(
        1
        for row in rows
        if str(row.get("request_context_validation_mode", ""))
        == "request_bound"
        and bool(
            row.get(
                "request_context_route_adoption_precondition_blocked_before_response",
                False,
            )
        )
    )
    row_request_bound_precondition_known_blockers = sum(
        int(
            row.get(
                "request_context_route_adoption_precondition_known_blocker_count",
                0,
            )
            or 0
        )
        for row in rows
        if str(row.get("request_context_validation_mode", ""))
        == "request_bound"
    )
    row_request_bound_precondition_required_fields = sum(
        int(
            row.get(
                "request_context_route_adoption_precondition_required_response_field_count",
                0,
            )
            or 0
        )
        for row in rows
        if str(row.get("request_context_validation_mode", ""))
        == "request_bound"
    )
    row_request_bound_precondition_target_primitives = sum(
        int(
            row.get(
                "request_context_route_adoption_precondition_target_primitive_count",
                0,
            )
            or 0
        )
        for row in rows
        if str(row.get("request_context_validation_mode", ""))
        == "request_bound"
    )
    row_schema_errors = sum(int(row.get("n_schema_errors", 0) or 0) for row in rows)
    row_request_context_errors = sum(
        int(row.get("n_request_context_errors", 0) or 0) for row in rows
    )
    request_bound_accounting_errors: list[str] = []
    if row_request_bound_payloads != manifest_request_bound_payloads:
        request_bound_accounting_errors.append(
            "request-bound JSONL rows must match manifest n_request_bound_payloads"
        )
    if row_schema_errors != manifest_schema_errors:
        request_bound_accounting_errors.append(
            "JSONL row schema-error counts must match manifest n_schema_errors"
        )
    if row_request_context_errors != manifest_request_context_errors:
        request_bound_accounting_errors.append(
            "JSONL row request-context-error counts must match manifest n_request_context_errors"
        )
    if (
        row_request_bound_payloads_with_inventory
        != manifest_request_bound_payloads_with_inventory
    ):
        request_bound_accounting_errors.append(
            "JSONL request-bound inventory rows must match manifest "
            "n_request_bound_payloads_with_context_packet_inventory"
        )
    if (
        row_request_bound_context_inventory_total_rows
        != manifest_request_bound_context_inventory_total_rows
    ):
        request_bound_accounting_errors.append(
            "JSONL request-bound inventory total rows must match manifest "
            "n_request_bound_payload_context_inventory_total_rows"
        )
    route_precondition_accounting_errors: list[str] = []
    if (
        row_request_bound_payloads_with_preconditions
        != manifest_request_bound_payloads_with_preconditions
    ):
        route_precondition_accounting_errors.append(
            "JSONL route-adoption precondition rows must match manifest "
            "n_request_bound_payloads_with_route_adoption_preconditions"
        )
    if (
        row_request_bound_payloads_with_blocking_preconditions
        != manifest_request_bound_payloads_with_blocking_preconditions
    ):
        route_precondition_accounting_errors.append(
            "JSONL blocking route-adoption precondition rows must match manifest "
            "n_request_bound_payloads_with_blocking_route_adoption_preconditions"
        )
    if (
        row_request_bound_precondition_known_blockers
        != manifest_request_bound_precondition_known_blockers
    ):
        route_precondition_accounting_errors.append(
            "JSONL route-adoption precondition blocker totals must match manifest "
            "n_request_bound_payload_route_adoption_precondition_known_blockers"
        )
    if (
        row_request_bound_precondition_required_fields
        != manifest_request_bound_precondition_required_fields
    ):
        route_precondition_accounting_errors.append(
            "JSONL route-adoption precondition required-field totals must match "
            "manifest n_request_bound_payload_route_adoption_precondition_required_response_fields"
        )
    if (
        row_request_bound_precondition_target_primitives
        != manifest_request_bound_precondition_target_primitives
    ):
        route_precondition_accounting_errors.append(
            "JSONL route-adoption precondition target-primitive totals must match "
            "manifest n_request_bound_payload_route_adoption_precondition_target_primitives"
        )
    request_context_path_present = bool(
        str(manifest.get("request_context_path", "")).strip()
    )
    request_bound_coverage_errors: list[str] = []
    if request_context_path_present or manifest_request_context_packets:
        if manifest_request_context_packets <= 0:
            request_bound_coverage_errors.append(
                "request-context validation must declare n_request_context_packets"
            )
        if (
            manifest_request_contexts_with_inventory
            != manifest_request_context_packets
        ):
            request_bound_coverage_errors.append(
                "request-context validation must carry context_packet_inventory "
                "for every request context"
            )
        if manifest_request_bound_payloads != int(manifest.get("n_payloads", 0) or 0):
            request_bound_coverage_errors.append(
                "request-context validation must bind every payload row"
            )
        if (
            manifest_request_bound_payloads_with_inventory
            != manifest_request_bound_payloads
        ):
            request_bound_coverage_errors.append(
                "request-bound validation must carry context_packet_inventory "
                "for every bound payload row"
            )
        if manifest_request_context_errors:
            request_bound_coverage_errors.append(
                "request-bound validation must have zero request-context errors"
            )
    checks = [
        _check(
            "optional_llm_route_planner_response_payload_validation_all_ok",
            "optional_artifacts",
            "LLM response-payload validation manifest all_ok",
            str(manifest.get("all_ok", "")),
            bool(manifest.get("all_ok", False)),
        ),
        _check(
            "optional_llm_route_planner_response_payload_validation_component",
            "optional_artifacts",
            LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATOR_COMPONENT,
            str(manifest.get("component_name", "")),
            manifest.get("component_name")
            == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATOR_COMPONENT,
        ),
        _check(
            "optional_llm_route_planner_response_payload_validation_boundary",
            "optional_artifacts",
            "not theorem proof evidence",
            str(manifest.get("proof_evidence_boundary", ""))[:160],
            "not theorem proof evidence"
            in str(manifest.get("proof_evidence_boundary", "")).lower(),
        ),
        _check(
            "optional_llm_route_planner_response_payload_validation_payload_schema_file",
            "optional_artifacts",
            "response-payload schema exists",
            str(response_payload_schema_path.exists()),
            response_payload_schema_path.exists(),
        ),
        _check(
            "optional_llm_route_planner_response_payload_validation_payload_schema_id",
            "optional_artifacts",
            LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID,
            str(response_payload_schema.get("$id", "")),
            response_payload_schema.get("$id")
            == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID,
        ),
        _check(
            "optional_llm_route_planner_response_payload_validation_manifest_schema_file",
            "optional_artifacts",
            "response-payload validation manifest schema exists",
            str(validation_manifest_schema_path.exists()),
            validation_manifest_schema_path.exists(),
        ),
        _check(
            "optional_llm_route_planner_response_payload_validation_manifest_schema_id",
            "optional_artifacts",
            LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID,
            str(validation_manifest_schema.get("$id", "")),
            validation_manifest_schema.get("$id")
            == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID,
        ),
        _check(
            "optional_llm_route_planner_response_payload_validation_row_schema_file",
            "optional_artifacts",
            "response-payload validation row schema exists",
            str(validation_row_schema_path.exists()),
            validation_row_schema_path.exists(),
        ),
        _check(
            "optional_llm_route_planner_response_payload_validation_row_schema_id",
            "optional_artifacts",
            LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID,
            str(validation_row_schema.get("$id", "")),
            validation_row_schema.get("$id")
            == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID,
        ),
        _check(
            "optional_llm_route_planner_response_payload_validation_manifest_schema_valid",
            "optional_artifacts",
            "validation manifest satisfies published schema",
            "; ".join(manifest_contract_errors) if manifest_contract_errors else "ok",
            not manifest_contract_errors,
            errors=tuple(manifest_contract_errors),
        ),
        _check(
            "optional_llm_route_planner_response_payload_validation_jsonl_parse",
            "optional_artifacts",
            "response-payload validation JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_llm_route_planner_response_payload_validation_count_consistency",
            "optional_artifacts",
            "response-payload validation JSONL counts match manifest counters",
            (
                f"jsonl={len(rows)} manifest={manifest.get('n_payloads', 0)} "
                f"valid={valid_rows}/{manifest.get('n_valid_payloads', 0)} "
                f"invalid={invalid_rows}/{manifest.get('n_invalid_payloads', 0)}"
            ),
            not count_errors,
            errors=tuple(count_errors),
        ),
        _check(
            "optional_llm_route_planner_response_payload_validation_request_bound_accounting",
            "optional_artifacts",
            "request-bound/schema-error counters match JSONL rows",
            (
                f"bound={row_request_bound_payloads}/{manifest_request_bound_payloads} "
                f"schema_errors={row_schema_errors}/{manifest_schema_errors} "
                f"context_errors={row_request_context_errors}/{manifest_request_context_errors} "
                f"inventory_rows={row_request_bound_payloads_with_inventory}/"
                f"{manifest_request_bound_payloads_with_inventory} "
                f"inventory_total_rows={row_request_bound_context_inventory_total_rows}/"
                f"{manifest_request_bound_context_inventory_total_rows}"
            ),
            not request_bound_accounting_errors,
            errors=tuple(request_bound_accounting_errors),
        ),
        _check(
            "optional_llm_route_planner_response_payload_validation_request_bound_coverage",
            "optional_artifacts",
            "request-context validation binds every payload when request context is supplied",
            (
                f"context_path_present={request_context_path_present} "
                f"context_packets={manifest_request_context_packets} "
                f"context_inventories={manifest_request_contexts_with_inventory} "
                f"request_bound={manifest_request_bound_payloads}/"
                f"{manifest.get('n_payloads', 0)} "
                f"bound_inventories={manifest_request_bound_payloads_with_inventory} "
                f"context_errors={manifest_request_context_errors}"
            ),
            not request_bound_coverage_errors,
            errors=tuple(request_bound_coverage_errors),
        ),
        _check(
            "optional_llm_route_planner_response_payload_validation_route_precondition_accounting",
            "optional_artifacts",
            "route-adoption precondition counters match JSONL rows",
            (
                f"preconditions={row_request_bound_payloads_with_preconditions}/"
                f"{manifest_request_bound_payloads_with_preconditions} "
                f"blocked={row_request_bound_payloads_with_blocking_preconditions}/"
                f"{manifest_request_bound_payloads_with_blocking_preconditions} "
                f"blockers={row_request_bound_precondition_known_blockers}/"
                f"{manifest_request_bound_precondition_known_blockers} "
                f"required_fields={row_request_bound_precondition_required_fields}/"
                f"{manifest_request_bound_precondition_required_fields}"
            ),
            not route_precondition_accounting_errors,
            errors=tuple(route_precondition_accounting_errors),
        ),
    ]
    for idx, row in enumerate(rows):
        schema_errors = validate_llm_route_planner_response_payload_validation_row(
            row,
            validation_row_schema,
        )
        checks.append(
            _check(
                f"optional_llm_route_planner_response_payload_validation_row_{idx}_schema_valid",
                "optional_artifacts",
                "response-payload validation row satisfies published row schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=tuple(schema_errors),
            )
        )
        checks.append(
            _check(
                f"optional_llm_route_planner_response_payload_validation_row_{idx}_payload_schema_id",
                "optional_artifacts",
                "validation row targets the published response-payload schema",
                str(row.get("payload_schema_id", "")),
                row.get("payload_schema_id")
                == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID,
            )
        )
    return checks


def _llm_route_planner_optional_checks(
    bundle_dir: Path,
    *,
    artifact_name: str = "formalization_gap_planner_llm_route_planner",
    check_prefix: str = "optional_llm_route_planner",
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = bundle_dir / "artifacts" / artifact_name
    manifest_path = (
        artifact_dir / "formalization_gap_planner_llm_route_planner_manifest.json"
    )
    manifest_schema_path = (
        artifact_dir
        / "formalization_gap_planner_llm_route_planner_manifest.schema.json"
    )
    requests_jsonl_path = (
        artifact_dir / "formalization_gap_planner_llm_route_planner_requests.jsonl"
    )
    library_alignment_summaries_jsonl_path = (
        artifact_dir
        / "formalization_gap_planner_llm_route_planner_library_alignment_summaries.jsonl"
    )
    route_planning_briefs_jsonl_path = (
        artifact_dir
        / "formalization_gap_planner_llm_route_planner_route_planning_briefs.jsonl"
    )
    rows_jsonl_path = artifact_dir / "formalization_gap_planner_llm_route_planner.jsonl"
    request_schema_path = (
        artifact_dir / "formalization_gap_planner_llm_route_planner_request.schema.json"
    )
    library_alignment_summary_schema_path = (
        artifact_dir
        / "formalization_gap_planner_llm_route_planner_library_alignment_summary.schema.json"
    )
    route_planning_brief_schema_path = (
        artifact_dir
        / "formalization_gap_planner_llm_route_planner_route_planning_brief.schema.json"
    )
    response_schema_path = (
        artifact_dir / "formalization_gap_planner_llm_route_planner_response.schema.json"
    )
    response_payload_schema_path = (
        artifact_dir
        / "formalization_gap_planner_llm_route_planner_response_payload.schema.json"
    )
    response_payload_validation_manifest_schema_path = (
        artifact_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.schema.json"
    )
    response_payload_validation_row_schema_path = (
        artifact_dir
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_row.schema.json"
    )
    row_schema_path = (
        artifact_dir / "formalization_gap_planner_llm_route_planner_row.schema.json"
    )
    seed_route_selection_schema_path = (
        artifact_dir
        / "formalization_gap_planner_llm_route_planner_seed_route_selection.schema.json"
    )
    standalone_seed_path = (
        artifact_dir
        / "formalization_gap_planner_llm_route_planner_standalone_seed.json"
    )
    manifest = _read_json_no_error(manifest_path)
    manifest_schema = _read_json_no_error(manifest_schema_path)
    request_schema = _read_json_no_error(request_schema_path)
    library_alignment_summary_schema = _read_json_no_error(
        library_alignment_summary_schema_path
    )
    route_planning_brief_schema = _read_json_no_error(
        route_planning_brief_schema_path
    )
    response_schema = _read_json_no_error(response_schema_path)
    response_payload_schema = _read_json_no_error(response_payload_schema_path)
    response_payload_validation_manifest_schema = _read_json_no_error(
        response_payload_validation_manifest_schema_path
    )
    response_payload_validation_row_schema = _read_json_no_error(
        response_payload_validation_row_schema_path
    )
    row_schema = _read_json_no_error(row_schema_path)
    seed_route_selection_schema = _read_json_no_error(
        seed_route_selection_schema_path
    )
    seed_payload = _read_json_no_error(standalone_seed_path)
    requests, request_errors = _read_jsonl_dict_rows_no_error(requests_jsonl_path)
    library_alignment_summary_rows, library_alignment_summary_errors = (
        _read_jsonl_dict_rows_no_error(library_alignment_summaries_jsonl_path)
    )
    route_planning_brief_rows, route_planning_brief_errors = (
        _read_jsonl_dict_rows_no_error(route_planning_briefs_jsonl_path)
    )
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    request_library_alignment_summaries = [
        _dict_value(_dict_value(request, "context_packet"), "library_alignment_summary")
        for request in requests
        if _dict_value(_dict_value(request, "context_packet"), "library_alignment_summary")
    ]
    request_route_planning_briefs = [
        _dict_value(_dict_value(request, "context_packet"), "route_planning_brief")
        for request in requests
        if _dict_value(_dict_value(request, "context_packet"), "route_planning_brief")
    ]
    seed_errors = validate_standalone_input_payload(seed_payload)
    seed_route_selection_contract_errors = (
        validate_llm_route_planner_seed_route_selection_payload(
            seed_payload.get("llm_route_planner_seed_route_selection", {})
        )
    )
    manifest_schema_errors = validate_llm_route_planner_manifest(
        manifest,
        manifest_schema if manifest_schema else None,
    )
    checks = [
        _check(
            f"{check_prefix}_all_ok",
            "optional_artifacts",
            "LLM route-planner manifest all_ok",
            str(manifest.get("all_ok", "")),
            bool(manifest.get("all_ok", False)),
        ),
        _check(
            f"{check_prefix}_component",
            "optional_artifacts",
            "formalization_gap_planner_llm_route_planner",
            str(manifest.get("component_name", "")),
            manifest.get("component_name")
            == "formalization_gap_planner_llm_route_planner",
        ),
        _check(
            f"{check_prefix}_boundary",
            "optional_artifacts",
            "not theorem proof evidence",
            str(manifest.get("proof_evidence_boundary", ""))[:160],
            "not theorem proof evidence"
            in str(manifest.get("proof_evidence_boundary", "")).lower(),
        ),
        _check(
            f"{check_prefix}_manifest_schema_file",
            "optional_artifacts",
            "LLM route-planner manifest schema exists",
            str(manifest_schema_path.exists()),
            manifest_schema_path.exists(),
        ),
        _check(
            f"{check_prefix}_manifest_schema_id",
            "optional_artifacts",
            LLM_ROUTE_PLANNER_MANIFEST_SCHEMA_ID,
            str(manifest_schema.get("$id", "")),
            manifest_schema.get("$id") == LLM_ROUTE_PLANNER_MANIFEST_SCHEMA_ID,
        ),
        _check(
            f"{check_prefix}_manifest_schema_valid",
            "optional_artifacts",
            "LLM route-planner manifest satisfies published manifest schema",
            "; ".join(manifest_schema_errors) if manifest_schema_errors else "ok",
            not manifest_schema_errors,
            errors=tuple(manifest_schema_errors),
        ),
        _check(
            f"{check_prefix}_legacy_response_alias_contract",
            "optional_artifacts",
            "LLM route-planner manifest records Lean legacy response-field aliases",
            _llm_legacy_response_alias_observed(manifest),
            not _llm_legacy_response_alias_errors(manifest),
            errors=_llm_legacy_response_alias_errors(manifest),
        ),
        _check(
            f"{check_prefix}_request_schema_file",
            "optional_artifacts",
            "LLM route-planner request schema exists",
            str(request_schema_path.exists()),
            request_schema_path.exists(),
        ),
        _check(
            f"{check_prefix}_request_schema_id",
            "optional_artifacts",
            LLM_ROUTE_PLANNER_REQUEST_SCHEMA_ID,
            str(request_schema.get("$id", "")),
            request_schema.get("$id") == LLM_ROUTE_PLANNER_REQUEST_SCHEMA_ID,
        ),
        _check(
            f"{check_prefix}_library_alignment_summary_schema_file",
            "optional_artifacts",
            "LLM route-planner library-alignment summary schema exists",
            str(library_alignment_summary_schema_path.exists()),
            library_alignment_summary_schema_path.exists(),
        ),
        _check(
            f"{check_prefix}_library_alignment_summary_schema_id",
            "optional_artifacts",
            LLM_ROUTE_PLANNER_LIBRARY_ALIGNMENT_SUMMARY_SCHEMA_ID,
            str(library_alignment_summary_schema.get("$id", "")),
            library_alignment_summary_schema.get("$id")
            == LLM_ROUTE_PLANNER_LIBRARY_ALIGNMENT_SUMMARY_SCHEMA_ID,
        ),
        _check(
            f"{check_prefix}_route_planning_brief_schema_file",
            "optional_artifacts",
            "LLM route-planner route-planning brief schema exists",
            str(route_planning_brief_schema_path.exists()),
            route_planning_brief_schema_path.exists(),
        ),
        _check(
            f"{check_prefix}_route_planning_brief_schema_id",
            "optional_artifacts",
            LLM_ROUTE_PLANNER_ROUTE_PLANNING_BRIEF_SCHEMA_ID,
            str(route_planning_brief_schema.get("$id", "")),
            route_planning_brief_schema.get("$id")
            == LLM_ROUTE_PLANNER_ROUTE_PLANNING_BRIEF_SCHEMA_ID,
        ),
        _check(
            f"{check_prefix}_route_planning_brief_schema_shape",
            "optional_artifacts",
            "route-planning brief schema matches canonical builder",
            str(route_planning_brief_schema.get("$id", "")),
            route_planning_brief_schema
            == llm_route_planner_route_planning_brief_json_schema(),
        ),
        _check(
            f"{check_prefix}_response_schema_file",
            "optional_artifacts",
            "LLM route-planner response schema exists",
            str(response_schema_path.exists()),
            response_schema_path.exists(),
        ),
        _check(
            f"{check_prefix}_response_schema_id",
            "optional_artifacts",
            LLM_ROUTE_PLANNER_RESPONSE_SCHEMA_ID,
            str(response_schema.get("$id", "")),
            response_schema.get("$id") == LLM_ROUTE_PLANNER_RESPONSE_SCHEMA_ID,
        ),
        _check(
            f"{check_prefix}_response_payload_schema_file",
            "optional_artifacts",
            "LLM route-planner response-payload schema exists",
            str(response_payload_schema_path.exists()),
            response_payload_schema_path.exists(),
        ),
        _check(
            f"{check_prefix}_response_payload_schema_id",
            "optional_artifacts",
            LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID,
            str(response_payload_schema.get("$id", "")),
            response_payload_schema.get("$id")
            == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID,
        ),
        _check(
            f"{check_prefix}_response_payload_validation_manifest_schema_file",
            "optional_artifacts",
            "LLM route-planner response-payload validation manifest schema exists",
            str(response_payload_validation_manifest_schema_path.exists()),
            response_payload_validation_manifest_schema_path.exists(),
        ),
        _check(
            f"{check_prefix}_response_payload_validation_manifest_schema_id",
            "optional_artifacts",
            LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID,
            str(response_payload_validation_manifest_schema.get("$id", "")),
            response_payload_validation_manifest_schema.get("$id")
            == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID,
        ),
        _check(
            f"{check_prefix}_response_payload_validation_row_schema_file",
            "optional_artifacts",
            "LLM route-planner response-payload validation row schema exists",
            str(response_payload_validation_row_schema_path.exists()),
            response_payload_validation_row_schema_path.exists(),
        ),
        _check(
            f"{check_prefix}_response_payload_validation_row_schema_id",
            "optional_artifacts",
            LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID,
            str(response_payload_validation_row_schema.get("$id", "")),
            response_payload_validation_row_schema.get("$id")
            == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID,
        ),
        _check(
            f"{check_prefix}_response_schema_rejects_kernel_claim",
            "optional_artifacts",
            "kernel_verified const false",
            json.dumps(
                response_schema.get("properties", {}).get("kernel_verified", {}),
                sort_keys=True,
            ),
            response_schema.get("properties", {})
            .get("kernel_verified", {})
            .get("const")
            is False,
        ),
        _check(
            f"{check_prefix}_row_schema_file",
            "optional_artifacts",
            "LLM route-planner row schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            f"{check_prefix}_row_schema_id",
            "optional_artifacts",
            LLM_ROUTE_PLANNER_ROW_SCHEMA_ID,
            str(row_schema.get("$id", "")),
            row_schema.get("$id") == LLM_ROUTE_PLANNER_ROW_SCHEMA_ID,
        ),
        _check(
            f"{check_prefix}_realization_coverage_witness_schema",
            "optional_artifacts",
            "LLM row schema publishes structured realization_coverage_witness",
            _llm_realization_witness_schema_observed(row_schema),
            not _llm_realization_witness_schema_errors(row_schema),
            errors=_llm_realization_witness_schema_errors(row_schema),
        ),
        _check(
            f"{check_prefix}_seed_route_selection_schema_file",
            "optional_artifacts",
            "LLM route-planner seed route-selection schema exists beside standalone seed",
            str(seed_route_selection_schema_path.exists()),
            seed_route_selection_schema_path.exists(),
        ),
        _check(
            f"{check_prefix}_seed_route_selection_schema_id",
            "optional_artifacts",
            FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SEED_ROUTE_SELECTION_SCHEMA_ID,
            str(seed_route_selection_schema.get("$id", "")),
            seed_route_selection_schema.get("$id")
            == FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SEED_ROUTE_SELECTION_SCHEMA_ID,
        ),
        _check(
            f"{check_prefix}_requests_parse",
            "optional_artifacts",
            "LLM route-planner requests JSONL parses into object rows",
            "; ".join(request_errors) if request_errors else f"rows={len(requests)}",
            not request_errors,
            errors=request_errors,
        ),
        _check(
            f"{check_prefix}_library_alignment_summaries_parse",
            "optional_artifacts",
            "LLM route-planner library-alignment summaries JSONL parses into object rows",
            (
                "; ".join(library_alignment_summary_errors)
                if library_alignment_summary_errors
                else f"rows={len(library_alignment_summary_rows)}"
            ),
            not library_alignment_summary_errors,
            errors=library_alignment_summary_errors,
        ),
        _check(
            f"{check_prefix}_route_planning_briefs_parse",
            "optional_artifacts",
            "LLM route-planner route-planning briefs JSONL parses into object rows",
            (
                "; ".join(route_planning_brief_errors)
                if route_planning_brief_errors
                else f"rows={len(route_planning_brief_rows)}"
            ),
            not route_planning_brief_errors,
            errors=route_planning_brief_errors,
        ),
        _check(
            f"{check_prefix}_rows_parse",
            "optional_artifacts",
            "LLM route-planner rows JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            f"{check_prefix}_request_count",
            "optional_artifacts",
            "LLM route-planner requests match manifest count",
            f"jsonl={len(requests)} manifest={manifest.get('n_request_packets', 0)}",
            len(requests) == int(manifest.get("n_request_packets", 0) or 0),
        ),
        _check(
            f"{check_prefix}_library_alignment_summary_count",
            "optional_artifacts",
            "LLM route-planner library-alignment summaries match manifest count",
            (
                f"jsonl={len(library_alignment_summary_rows)} "
                f"manifest={manifest.get('n_requests_with_library_alignment_summary', 0)}"
            ),
            len(library_alignment_summary_rows)
            == int(
                manifest.get("n_requests_with_library_alignment_summary", 0) or 0
            ),
        ),
        _check(
            f"{check_prefix}_library_alignment_summary_request_match",
            "optional_artifacts",
            "LLM route-planner library-alignment summaries match request packets",
            (
                f"jsonl={len(library_alignment_summary_rows)} "
                f"requests={len(request_library_alignment_summaries)}"
            ),
            library_alignment_summary_rows == request_library_alignment_summaries,
        ),
        _check(
            f"{check_prefix}_route_planning_brief_count",
            "optional_artifacts",
            "LLM route-planner route-planning briefs match manifest count",
            (
                f"jsonl={len(route_planning_brief_rows)} "
                f"manifest={manifest.get('n_route_planning_briefs', 0)}"
            ),
            len(route_planning_brief_rows)
            == int(manifest.get("n_route_planning_briefs", 0) or 0),
        ),
        _check(
            f"{check_prefix}_route_planning_brief_request_match",
            "optional_artifacts",
            "LLM route-planner route-planning briefs match request packets",
            (
                f"jsonl={len(route_planning_brief_rows)} "
                f"requests={len(request_route_planning_briefs)}"
            ),
            route_planning_brief_rows == request_route_planning_briefs,
        ),
        _check(
            f"{check_prefix}_library_alignment_route_option_aggregates",
            "optional_artifacts",
            "LLM route-planner route-option library-alignment aggregates match manifest counts",
            _llm_library_alignment_route_option_aggregate_observed(
                manifest,
                library_alignment_summary_rows,
            ),
            not _llm_library_alignment_route_option_aggregate_errors(
                manifest,
                library_alignment_summary_rows,
            ),
            errors=_llm_library_alignment_route_option_aggregate_errors(
                manifest,
                library_alignment_summary_rows,
            ),
        ),
        _check(
            f"{check_prefix}_request_model_tier_mismatch_policy",
            "optional_artifacts",
            "LLM route-planner manifest reports no Claude request model-tier mismatches",
            _llm_request_model_tier_mismatch_observed(manifest),
            not _llm_request_model_tier_mismatch_errors(manifest),
            errors=_llm_request_model_tier_mismatch_errors(manifest),
        ),
        _check(
            f"{check_prefix}_generation_preflight_policy",
            "optional_artifacts",
            "LLM route-planner manifest reports no generation preflight blocks",
            _llm_generation_preflight_observed(manifest),
            not _llm_generation_preflight_errors(manifest),
            errors=_llm_generation_preflight_errors(manifest),
        ),
        _check(
            f"{check_prefix}_row_count",
            "optional_artifacts",
            "LLM route-planner rows match manifest count",
            f"jsonl={len(rows)} manifest={manifest.get('n_rows', 0)}",
            len(rows) == int(manifest.get("n_rows", 0) or 0),
        ),
        _check(
            f"{check_prefix}_route_adoption_blocker_summary",
            "optional_artifacts",
            "LLM route-planner manifest blocker summaries match JSONL rows",
            _llm_route_adoption_blocker_summary_observed(manifest, rows),
            not _llm_route_adoption_blocker_summary_errors(manifest, rows),
            errors=_llm_route_adoption_blocker_summary_errors(manifest, rows),
        ),
        _check(
            f"{check_prefix}_standalone_seed_contract",
            "optional_artifacts",
            "LLM route-planner standalone seed validates against standalone contract",
            "; ".join(seed_errors) if seed_errors else "ok",
            not seed_errors,
            errors=tuple(seed_errors),
        ),
        _check(
            f"{check_prefix}_seed_route_selection_contract",
            "optional_artifacts",
            "LLM route-planner standalone seed route-selection summary validates against public route-selection contract",
            (
                "; ".join(seed_route_selection_contract_errors)
                if seed_route_selection_contract_errors
                else "ok"
            ),
            not seed_route_selection_contract_errors,
            errors=tuple(seed_route_selection_contract_errors),
        ),
        _check(
            f"{check_prefix}_generic_formal_dag_fields",
            "optional_artifacts",
            "accepted LLM route-planner rows and standalone seed publish prover-neutral formal-realization DAG fields",
            _llm_generic_formal_dag_observed(rows, seed_payload, manifest),
            not _llm_generic_formal_dag_errors(rows, seed_payload, manifest),
            errors=_llm_generic_formal_dag_errors(rows, seed_payload, manifest),
        ),
        _check(
            f"{check_prefix}_seed_route_selection_summary",
            "optional_artifacts",
            "LLM route-planner standalone seed publishes a coherent selected route summary",
            _llm_seed_route_selection_summary_observed(seed_payload, rows),
            not _llm_seed_route_selection_summary_errors(seed_payload, rows),
            errors=_llm_seed_route_selection_summary_errors(seed_payload, rows),
        ),
    ]
    for idx, request in enumerate(requests):
        schema_errors = validate_llm_route_planner_request(request, request_schema)
        checks.append(
            _check(
                f"{check_prefix}_request_{idx}_schema_valid",
                "optional_artifacts",
                "LLM route-planner request validates against public request schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=tuple(schema_errors),
            )
        )
        registry_errors = _llm_request_registry_context_errors(request)
        checks.append(
            _check(
                f"{check_prefix}_request_{idx}_registry_context",
                "optional_artifacts",
                "LLM route-planner request carries bounded component-resource registry context",
                _llm_request_registry_context_observed(request),
                not registry_errors,
                errors=registry_errors,
            )
        )
        target_intake_errors = _llm_request_target_intake_context_errors(request)
        checks.append(
            _check(
                f"{check_prefix}_request_{idx}_target_intake_context",
                "optional_artifacts",
                "LLM route-planner request carries target-intake theorem context",
                _llm_request_target_intake_context_observed(request),
                not target_intake_errors,
                errors=target_intake_errors,
            )
        )
        generation_policy_errors = _llm_request_generation_policy_errors(request)
        checks.append(
            _check(
                f"{check_prefix}_request_{idx}_generation_policy",
                "optional_artifacts",
                "LLM route-planner request carries a self-contained generator model policy matching its provider/model/tier",
                _llm_request_generation_policy_observed(request),
                not generation_policy_errors,
                errors=generation_policy_errors,
            )
        )
    for idx, row in enumerate(rows):
        schema_errors = validate_llm_route_planner_row(row, row_schema)
        checks.append(
            _check(
                f"{check_prefix}_row_{idx}_schema_valid",
                "optional_artifacts",
                "LLM route-planner row validates against public row schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=tuple(schema_errors),
            )
        )
        if _llm_route_planner_row_accepted(row):
            request = _llm_request_for_row(requests, row)
            evidence_errors = _llm_row_request_evidence_errors(row, request)
            checks.append(
                _check(
                    f"{check_prefix}_row_{idx}_request_evidence_bound",
                    "optional_artifacts",
                    "accepted LLM row source refs, declarations, and residuals are bounded by the request packet",
                    _llm_row_request_evidence_observed(row, request),
                    not evidence_errors,
                    errors=evidence_errors,
                )
            )
            seed_route = _llm_seed_route_for_row(seed_payload, row)
            provenance_errors = _llm_seed_provenance_errors(row, seed_route)
            checks.append(
                _check(
                    f"{check_prefix}_row_{idx}_seed_provenance",
                    "optional_artifacts",
                    "accepted LLM row provenance is preserved in standalone seed route metadata",
                    _llm_seed_provenance_observed(row, seed_route),
                    not provenance_errors,
                    errors=provenance_errors,
                )
            )
            model_provenance_errors = _llm_seed_model_provenance_errors(
                row,
                seed_route,
            )
            checks.append(
                _check(
                    f"{check_prefix}_row_{idx}_seed_model_provenance",
                    "optional_artifacts",
                    "accepted LLM row model tier, selection rationale, and generator metadata are preserved in standalone seed route metadata",
                    _llm_seed_model_provenance_observed(row, seed_route),
                    not model_provenance_errors,
                    errors=model_provenance_errors,
                )
            )
            source_grounding_errors = (
                _llm_seed_source_grounding_provenance_errors(row, seed_route)
            )
            checks.append(
                _check(
                    f"{check_prefix}_row_{idx}_seed_source_grounding_provenance",
                    "optional_artifacts",
                    "accepted LLM row source-grounding rows and obligations are preserved in standalone seed route metadata",
                    _llm_seed_source_grounding_provenance_observed(row, seed_route),
                    not source_grounding_errors,
                    errors=source_grounding_errors,
                )
            )
            witness_errors = _llm_seed_realization_witness_errors(row, seed_route)
            checks.append(
                _check(
                    f"{check_prefix}_row_{idx}_seed_realization_witness_preservation",
                    "optional_artifacts",
                    "accepted LLM row realization coverage witness is preserved in standalone seed",
                    _llm_seed_realization_witness_observed(row, seed_route),
                    not witness_errors,
                    errors=witness_errors,
                )
            )
            alignment_errors = _llm_seed_alignment_errors(row, seed_route)
            checks.append(
                _check(
                    f"{check_prefix}_row_{idx}_seed_alignment_preservation",
                    "optional_artifacts",
                    "accepted LLM row alignment edges are normalized and preserved in standalone seed",
                    _llm_seed_alignment_observed(row, seed_route),
                    not alignment_errors,
                    errors=alignment_errors,
                )
            )
            dag_errors = _llm_seed_dag_errors(row, seed_route)
            checks.append(
                _check(
                    f"{check_prefix}_row_{idx}_seed_dag_preservation",
                    "optional_artifacts",
                    "accepted LLM row informal and formal-realization DAG nodes are preserved in standalone seed",
                    _llm_seed_dag_observed(row, seed_route),
                    not dag_errors,
                    errors=dag_errors,
                )
            )
            search_handoff_errors = _llm_seed_search_handoff_errors(row, seed_route)
            checks.append(
                _check(
                    f"{check_prefix}_row_{idx}_seed_search_handoff",
                    "optional_artifacts",
                    "accepted LLM row search requests are preserved as interactive refinement hooks and route-revision triggers",
                    _llm_seed_search_handoff_observed(row, seed_route),
                    not search_handoff_errors,
                    errors=search_handoff_errors,
                )
            )
            route_adoption_errors = _llm_seed_route_adoption_readiness_errors(
                row,
                seed_route,
            )
            checks.append(
                _check(
                    f"{check_prefix}_row_{idx}_seed_route_adoption_readiness",
                    "optional_artifacts",
                    "accepted LLM row route-adoption readiness and blockers are preserved in standalone seed metadata",
                    _llm_seed_route_adoption_readiness_observed(row, seed_route),
                    not route_adoption_errors,
                    errors=route_adoption_errors,
                )
            )
            route_selection_errors = _llm_seed_route_selection_errors(row, seed_route)
            checks.append(
                _check(
                    f"{check_prefix}_row_{idx}_seed_route_selection",
                    "optional_artifacts",
                    "accepted LLM row seed-selection rank, selected flag, and minimal-delta cost are preserved in standalone seed metadata",
                    _llm_seed_route_selection_observed(row, seed_route),
                    not route_selection_errors,
                    errors=route_selection_errors,
                )
            )
    return checks


def _llm_library_alignment_route_option_aggregate_errors(
    manifest: dict[str, Any],
    summary_rows: list[dict[str, Any]],
) -> tuple[str, ...]:
    errors: list[str] = []
    expected = _llm_library_alignment_route_option_aggregates(summary_rows)
    for field_name in (
        "n_request_library_alignment_route_options",
        "n_request_library_alignment_route_option_primitives",
        "n_request_library_alignment_route_option_bridge_or_harder_primitives",
        "n_request_library_alignment_route_option_target_compatible_reuse_declarations",
    ):
        observed = _int_or_none(manifest.get(field_name))
        if observed is None:
            errors.append(f"{field_name} is not an integer")
            continue
        if observed != expected[field_name]:
            errors.append(
                f"{field_name} mismatch: observed={observed} "
                f"expected={expected[field_name]}"
            )
    cost_field = "total_request_library_alignment_route_option_minimum_base_cost"
    observed_cost = _float_or_none(manifest.get(cost_field))
    if observed_cost is None:
        errors.append(f"{cost_field} is not a number")
    elif abs(observed_cost - float(expected[cost_field])) > 1e-9:
        errors.append(
            f"{cost_field} mismatch: observed={observed_cost} "
            f"expected={expected[cost_field]}"
        )
    return tuple(errors)


def _llm_library_alignment_route_option_aggregate_observed(
    manifest: dict[str, Any],
    summary_rows: list[dict[str, Any]],
) -> str:
    expected = _llm_library_alignment_route_option_aggregates(summary_rows)
    return (
        "observed="
        + json.dumps(
            {field_name: manifest.get(field_name) for field_name in expected},
            sort_keys=True,
        )
        + "; expected="
        + json.dumps(expected, sort_keys=True)
    )


def _llm_library_alignment_route_option_aggregates(
    summary_rows: list[dict[str, Any]],
) -> dict[str, int | float]:
    route_option_rows = tuple(
        row
        for summary in _dict_tuple(summary_rows)
        for row in _dict_tuple(summary.get("route_option_alignment", []))
    )
    return {
        "n_request_library_alignment_route_options": len(route_option_rows),
        "n_request_library_alignment_route_option_primitives": sum(
            _nonnegative_int(row.get("n_selected_primitives"))
            for row in route_option_rows
        ),
        "n_request_library_alignment_route_option_bridge_or_harder_primitives": sum(
            _nonnegative_int(row.get("n_bridge_or_harder_primitives"))
            for row in route_option_rows
        ),
        "n_request_library_alignment_route_option_target_compatible_reuse_declarations": sum(
            _nonnegative_int(row.get("n_target_compatible_reuse_declarations"))
            for row in route_option_rows
        ),
        "total_request_library_alignment_route_option_minimum_base_cost": sum(
            _nonnegative_float(row.get("minimum_route_base_cost"))
            for row in route_option_rows
        ),
    }


def _nonnegative_int(value: Any) -> int:
    parsed = _int_or_none(value)
    if parsed is None:
        return 0
    return max(0, parsed)


def _nonnegative_float(value: Any) -> float:
    parsed = _float_or_none(value)
    if parsed is None:
        return 0.0
    return max(0.0, parsed)


def _llm_request_model_tier_mismatch_errors(
    manifest: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    raw_count = manifest.get("n_request_model_tier_mismatches", 0)
    try:
        mismatch_count = int(raw_count or 0)
    except (TypeError, ValueError):
        errors.append("n_request_model_tier_mismatches is not an integer")
        mismatch_count = -1
    mismatch_rows = manifest.get("request_model_tier_mismatches", [])
    if not isinstance(mismatch_rows, list):
        errors.append("request_model_tier_mismatches is not a list")
        mismatch_rows = []
    if mismatch_count != len(mismatch_rows):
        errors.append(
            "request_model_tier_mismatches count/list length mismatch: "
            f"count={mismatch_count} rows={len(mismatch_rows)}"
        )
    if mismatch_count:
        errors.append(
            f"manifest reports {mismatch_count} request model-tier mismatch(es)"
        )
    return tuple(errors)


def _llm_request_model_tier_mismatch_observed(manifest: dict[str, Any]) -> str:
    mismatch_rows = manifest.get("request_model_tier_mismatches", [])
    mismatch_rows = mismatch_rows if isinstance(mismatch_rows, list) else []
    return (
        f"count={manifest.get('n_request_model_tier_mismatches', 0)}; "
        f"rows={len(mismatch_rows)}"
    )


def _llm_generation_preflight_errors(
    manifest: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    raw_count = manifest.get("n_generation_preflight_blocked", 0)
    try:
        blocked_count = int(raw_count or 0)
    except (TypeError, ValueError):
        errors.append("n_generation_preflight_blocked is not an integer")
        blocked_count = -1
    preflight_rows = manifest.get("generation_preflight_errors", [])
    if not isinstance(preflight_rows, list):
        errors.append("generation_preflight_errors is not a list")
        preflight_rows = []
    if blocked_count != len(preflight_rows):
        errors.append(
            "generation_preflight_errors count/list length mismatch: "
            f"count={blocked_count} rows={len(preflight_rows)}"
        )
    raw_invalid = manifest.get("n_request_schema_invalid", 0)
    try:
        invalid_count = int(raw_invalid or 0)
    except (TypeError, ValueError):
        errors.append("n_request_schema_invalid is not an integer")
        invalid_count = -1
    if invalid_count != blocked_count:
        errors.append(
            "generation preflight count must match invalid request-schema count: "
            f"preflight={blocked_count} request_schema_invalid={invalid_count}"
        )
    if blocked_count:
        errors.append(
            f"manifest reports {blocked_count} generation preflight block(s)"
        )
    return tuple(errors)


def _llm_generation_preflight_observed(manifest: dict[str, Any]) -> str:
    preflight_rows = manifest.get("generation_preflight_errors", [])
    preflight_rows = preflight_rows if isinstance(preflight_rows, list) else []
    return (
        f"preflight={manifest.get('n_generation_preflight_blocked', 0)}; "
        f"rows={len(preflight_rows)}; "
        f"request_schema_invalid={manifest.get('n_request_schema_invalid', 0)}"
    )


def _llm_route_adoption_blocker_summary_errors(
    manifest: dict[str, Any],
    rows: list[dict[str, Any]],
) -> tuple[str, ...]:
    errors: list[str] = []
    expected_counts = _llm_route_adoption_blocker_counts_from_rows(rows)
    expected_summary = _llm_route_adoption_blocker_summary_from_rows(rows)
    observed_counts = _int_mapping(manifest.get("route_adoption_blocker_counts", {}))
    observed_by_blocker = manifest.get("by_route_adoption_blocker", {})
    observed_by_blocker = (
        observed_by_blocker if isinstance(observed_by_blocker, dict) else {}
    )
    if observed_counts != expected_counts:
        errors.append(
            "route_adoption_blocker_counts mismatch: "
            f"observed={observed_counts} expected={expected_counts}"
        )
    observed_keys = {
        str(key)
        for key, value in observed_by_blocker.items()
        if isinstance(value, dict)
    }
    if observed_keys != set(expected_summary):
        errors.append(
            "by_route_adoption_blocker keys mismatch: "
            f"observed={sorted(observed_keys)} expected={sorted(expected_summary)}"
        )
    for blocker, expected in expected_summary.items():
        observed = observed_by_blocker.get(blocker, {})
        if not isinstance(observed, dict):
            errors.append(f"by_route_adoption_blocker[{blocker}] missing")
            continue
        for field_name in (
            "n_rows",
            "n_blocker_occurrences",
            "n_response_present",
            "n_response_contract_ok",
            "n_provider_failures",
        ):
            observed_value = int(observed.get(field_name, -1) or 0)
            expected_value = int(expected.get(field_name, 0) or 0)
            if observed_value != expected_value:
                errors.append(
                    f"by_route_adoption_blocker[{blocker}].{field_name} "
                    f"mismatch: observed={observed_value} expected={expected_value}"
                )
        for field_name in ("by_route_adoption_status", "by_acceptance_status"):
            observed_map = _int_mapping(observed.get(field_name, {}))
            expected_map = _int_mapping(expected.get(field_name, {}))
            if observed_map != expected_map:
                errors.append(
                    f"by_route_adoption_blocker[{blocker}].{field_name} "
                    f"mismatch: observed={observed_map} expected={expected_map}"
                )
    return tuple(errors)


def _llm_route_adoption_blocker_summary_observed(
    manifest: dict[str, Any],
    rows: list[dict[str, Any]],
) -> str:
    observed_counts = _int_mapping(manifest.get("route_adoption_blocker_counts", {}))
    expected_counts = _llm_route_adoption_blocker_counts_from_rows(rows)
    observed_by_blocker = manifest.get("by_route_adoption_blocker", {})
    observed_by_blocker = (
        observed_by_blocker if isinstance(observed_by_blocker, dict) else {}
    )
    return (
        f"counts={observed_counts}; expected={expected_counts}; "
        f"by_keys={sorted(str(key) for key in observed_by_blocker)}"
    )


def _llm_route_adoption_blocker_counts_from_rows(
    rows: list[dict[str, Any]],
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(_str_tuple(row.get("route_adoption_blockers", [])))
    return dict(sorted(counts.items()))


def _llm_route_adoption_blocker_summary_from_rows(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, object]]:
    row_tuple = _dict_tuple(rows)
    counts = _llm_route_adoption_blocker_counts_from_rows(list(row_tuple))
    summaries: dict[str, dict[str, object]] = {}
    for blocker, count in counts.items():
        blocker_rows = [
            row
            for row in row_tuple
            if blocker in _str_tuple(row.get("route_adoption_blockers", []))
        ]
        summaries[blocker] = {
            "n_rows": len(blocker_rows),
            "n_blocker_occurrences": count,
            "by_route_adoption_status": dict(
                sorted(
                    Counter(
                        str(row.get("route_adoption_status", "")).strip()
                        for row in blocker_rows
                        if str(row.get("route_adoption_status", "")).strip()
                    ).items()
                )
            ),
            "by_acceptance_status": dict(
                sorted(
                    Counter(
                        str(row.get("acceptance_status", "")).strip()
                        for row in blocker_rows
                        if str(row.get("acceptance_status", "")).strip()
                    ).items()
                )
            ),
            "n_response_present": sum(
                1 for row in blocker_rows if bool(row.get("response_present", False))
            ),
            "n_response_contract_ok": sum(
                1
                for row in blocker_rows
                if bool(row.get("response_contract_ok", False))
            ),
            "n_provider_failures": sum(
                1 for row in blocker_rows if bool(row.get("provider_failure", False))
            ),
        }
    return summaries


def _llm_request_generation_policy_errors(
    request: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    policy = request.get("llm_generation_policy", {})
    if not isinstance(policy, dict):
        return ("llm_generation_policy missing or not object",)
    if str(policy.get("policy_id", "")).strip() != LLM_ROUTE_PLANNER_MODEL_TIER_POLICY_ID:
        errors.append("llm_generation_policy.policy_id mismatch")
    if str(policy.get("provider_name", "")).strip() != str(
        request.get("provider_name", "")
    ).strip():
        errors.append("llm_generation_policy.provider_name does not match request")
    if str(policy.get("resolved_model", "")).strip() != str(
        request.get("model", "")
    ).strip():
        errors.append("llm_generation_policy.resolved_model does not match request")
    if str(policy.get("selected_model_tier", "")).strip() != str(
        request.get("model_tier", "")
    ).strip():
        errors.append(
            "llm_generation_policy.selected_model_tier does not match request"
        )
    supported = set(_str_tuple(policy.get("supported_live_generator_providers", [])))
    if supported != {"anthropic", "openai", "static"}:
        errors.append(
            "llm_generation_policy.supported_live_generator_providers must be "
            "anthropic/openai/static"
        )
    prohibited = set(_str_tuple(policy.get("prohibited_generator_providers", [])))
    expected_prohibited = set(PROHIBITED_AGENT_GENERATOR_PROVIDERS)
    if not expected_prohibited.issubset(prohibited):
        errors.append(
            "llm_generation_policy.prohibited_generator_providers must include "
            "all known agent-style CLI providers"
        )
    if expected_prohibited.intersection(supported):
        errors.append(
            "llm_generation_policy.supported_live_generator_providers must exclude "
            "agent-style CLI providers"
        )
    claude_models = policy.get("claude_models_by_tier", {})
    if not isinstance(claude_models, dict):
        errors.append("llm_generation_policy.claude_models_by_tier must be object")
    elif claude_models != {
        "haiku": DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        "sonnet": DEFAULT_CLAUDE_SONNET_GENERATOR_MODEL,
        "opus": DEFAULT_CLAUDE_OPUS_GENERATOR_MODEL,
    }:
        errors.append("llm_generation_policy.claude_models_by_tier mismatch")
    if str(policy.get("claude_model_source_checked_date", "")).strip() != (
        ANTHROPIC_MODEL_SOURCE_CHECKED_DATE
    ):
        errors.append("llm_generation_policy.claude_model_source_checked_date mismatch")
    if "not evergreen aliases" not in str(
        policy.get("claude_model_id_versioning", "")
    ):
        errors.append(
            "llm_generation_policy.claude_model_id_versioning must mention "
            "not evergreen aliases"
        )
    auto_rules = policy.get("auto_tier_rules", [])
    if not isinstance(auto_rules, list) or not auto_rules:
        errors.append("llm_generation_policy.auto_tier_rules missing")
    elif not any(
        "source-grounding" in str(rule).lower()
        and "sonnet" in str(rule).lower()
        for rule in auto_rules
    ):
        errors.append(
            "llm_generation_policy.auto_tier_rules must route pending "
            "source-grounding obligations to Sonnet"
        )
    if policy.get("proof_evidence_status") != LLM_ROUTE_PLANNER_PROOF_EVIDENCE_STATUS:
        errors.append("llm_generation_policy.proof_evidence_status mismatch")
    if "not theorem proof evidence" not in str(
        policy.get("proof_evidence_boundary", "")
    ).lower():
        errors.append(
            "llm_generation_policy.proof_evidence_boundary must say not theorem proof evidence"
        )
    return tuple(errors)


def _llm_request_generation_policy_observed(request: dict[str, Any]) -> str:
    policy = request.get("llm_generation_policy", {})
    if not isinstance(policy, dict):
        return "policy=missing"
    return (
        f"provider={policy.get('provider_name', '')}; "
        f"model={policy.get('resolved_model', '')}; "
        f"tier={policy.get('selected_model_tier', '')}; "
        f"prohibited={','.join(_str_tuple(policy.get('prohibited_generator_providers', [])))}"
    )


def _llm_request_registry_context_errors(request: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    context = _dict_value(request, "context_packet")
    registry_context = _dict_value(context, "component_resource_registry_context")
    if not registry_context:
        return ("component_resource_registry_context missing",)
    component_rows = _dict_tuple(registry_context.get("component_rows", []))
    resource_rows = _dict_tuple(registry_context.get("resource_rows", []))
    contract_rows = _dict_tuple(registry_context.get("resource_contract_rows", []))
    execution_plan_rows = _dict_tuple(registry_context.get("execution_plan_rows", []))
    if not component_rows:
        errors.append("component_resource_registry_context.component_rows empty")
    if not resource_rows:
        errors.append("component_resource_registry_context.resource_rows empty")
    if not contract_rows:
        errors.append("component_resource_registry_context.resource_contract_rows empty")
    if not execution_plan_rows:
        errors.append("component_resource_registry_context.execution_plan_rows empty")
    if "not theorem proof evidence" not in str(
        registry_context.get("proof_evidence_boundary", "")
    ).lower():
        errors.append("component_resource_registry_context proof boundary missing")
    if len(component_rows) > 25:
        errors.append("component_resource_registry_context.component_rows unbounded")
    if len(resource_rows) > 50:
        errors.append("component_resource_registry_context.resource_rows unbounded")
    if len(contract_rows) > 50:
        errors.append("component_resource_registry_context.resource_contract_rows unbounded")
    if len(execution_plan_rows) > 25:
        errors.append("component_resource_registry_context.execution_plan_rows unbounded")
    resource_ids = {
        str(row.get("resource_id", "")).strip()
        for row in resource_rows
        if str(row.get("resource_id", "")).strip()
    }
    contract_resource_ids = {
        str(row.get("resource_id", "")).strip()
        for row in contract_rows
        if str(row.get("resource_id", "")).strip()
    }
    missing_contracts = sorted(resource_ids - contract_resource_ids)
    if missing_contracts:
        errors.append(
            "component_resource_registry_context resources missing contracts: "
            + ",".join(missing_contracts[:8])
        )
    component_ids = {
        str(row.get("component_id", "")).strip()
        for row in component_rows
        if str(row.get("component_id", "")).strip()
    }
    expected_components = {
        "literature_grounded_route_synthesis",
        "formal_library_coverage_mapping",
        "minimal_delta_and_or_planning",
        "prover_feedback_refinement",
    }
    missing_components = sorted(expected_components - component_ids)
    if missing_components:
        errors.append(
            "component_resource_registry_context missing planner components: "
            + ",".join(missing_components)
        )
    prompt_user = _dict_value(request, "prompt_messages").get("user", "")
    if "component_resource_registry_context" not in str(prompt_user):
        errors.append("prompt does not expose component_resource_registry_context")
    if "registry rows are not evidence" not in str(prompt_user):
        errors.append("prompt does not preserve registry non-evidence boundary")
    return tuple(errors)


def _llm_request_registry_context_observed(request: dict[str, Any]) -> str:
    context = _dict_value(request, "context_packet")
    registry_context = _dict_value(context, "component_resource_registry_context")
    component_rows = _dict_tuple(registry_context.get("component_rows", []))
    resource_rows = _dict_tuple(registry_context.get("resource_rows", []))
    contract_rows = _dict_tuple(registry_context.get("resource_contract_rows", []))
    execution_plan_rows = _dict_tuple(registry_context.get("execution_plan_rows", []))
    return (
        f"components={len(component_rows)}; "
        f"resources={len(resource_rows)}; "
        f"contracts={len(contract_rows)}; "
        f"execution_plans={len(execution_plan_rows)}"
    )


def _llm_request_target_intake_context_errors(request: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    context = _dict_value(request, "context_packet")
    rows = _dict_tuple(context.get("target_intake_rows", []))
    if not rows:
        return ("target_intake_rows missing",)
    if len(rows) > 25:
        errors.append("target_intake_rows unbounded")
    for index, row in enumerate(rows):
        if not str(row.get("theorem_statement", "")).strip():
            errors.append(f"target_intake_rows[{index}].theorem_statement missing")
        if not (
            _str_tuple(row.get("extracted_primitive_candidates", []))
            or _dict_tuple(row.get("primitive_seed_rows", []))
        ):
            errors.append(
                f"target_intake_rows[{index}] missing primitive candidates or seed rows"
            )
        if "not theorem proof evidence" not in str(
            row.get("proof_evidence_boundary", "")
        ).lower():
            errors.append(
                f"target_intake_rows[{index}] proof evidence boundary missing"
            )
    prompt_user = _dict_value(request, "prompt_messages").get("user", "")
    if "context_packet.target_intake_rows" not in str(prompt_user):
        errors.append("prompt does not expose target_intake_rows")
    if "target intake is not proof evidence" not in str(prompt_user):
        errors.append("prompt does not preserve target-intake non-evidence boundary")
    return tuple(errors)


def _llm_request_target_intake_context_observed(request: dict[str, Any]) -> str:
    context = _dict_value(request, "context_packet")
    rows = _dict_tuple(context.get("target_intake_rows", []))
    primitives = sum(
        len(_str_tuple(row.get("extracted_primitive_candidates", [])))
        for row in rows
    )
    literature_queries = sum(
        len(_str_tuple(row.get("literature_queries", []))) for row in rows
    )
    formal_library_queries = sum(
        len(
            _str_tuple(row.get("formal_library_grounding_queries", []))
            or _str_tuple(row.get("lean_grounding_queries", []))
        )
        for row in rows
    )
    return (
        f"target_intake_rows={len(rows)}; "
        f"primitive_candidates={primitives}; "
        f"literature_queries={literature_queries}; "
        f"formal_library_grounding_queries={formal_library_queries}"
    )


def _llm_route_planner_row_accepted(row: dict[str, Any]) -> bool:
    return (
        bool(row.get("response_contract_ok"))
        and str(row.get("acceptance_status", "")).startswith("ACCEPTED_")
        and isinstance(row.get("standalone_route", {}), dict)
        and bool(row.get("standalone_route", {}))
    )


def _llm_request_for_row(
    requests: list[dict[str, Any]],
    row: dict[str, Any],
) -> dict[str, Any]:
    request_id = str(row.get("request_id", ""))
    for request in requests:
        if str(request.get("request_id", "")) == request_id:
            return request
    route_id = str(row.get("route_id", ""))
    for request in requests:
        if str(request.get("route_id", "")) == route_id:
            return request
    return {}


def _llm_row_request_evidence_errors(
    row: dict[str, Any],
    request: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    if not request:
        return ("matching request packet missing",)
    errors.extend(_llm_row_request_model_policy_errors(row, request))
    available_sources = _llm_available_source_keys(request)
    row_sources = _llm_row_source_keys(row)
    missing_sources = sorted(row_sources - available_sources)
    if missing_sources:
        errors.append(
            "row source_refs not present in request available_source_refs: "
            + ",".join(missing_sources[:8])
        )
    available_declarations = _llm_available_declaration_keys(request)
    row_declarations = _llm_row_candidate_declaration_keys(row)
    missing_declarations = sorted(row_declarations - available_declarations)
    if missing_declarations:
        errors.append(
            "row candidate_declarations not present in request available_formal_declarations: "
            + ",".join(missing_declarations[:8])
        )
    errors.extend(_llm_row_target_prover_consistency_errors(row, request))
    request_residuals = _llm_request_residual_keys(request)
    row_residuals = _llm_row_residual_keys(row)
    if row_residuals and not request_residuals:
        errors.append("row residual_interpretations present but request residual_goals empty")
    invented_residuals = sorted(row_residuals - request_residuals)
    if invented_residuals:
        errors.append(
            "row residual_interpretations not present in request residual_goals: "
            + "; ".join(invented_residuals[:8])
        )
    missing_residuals = sorted(request_residuals - row_residuals)
    if request_residuals and missing_residuals:
        errors.append(
            "row residual_interpretations missing request residual_goals: "
            + "; ".join(missing_residuals[:8])
        )
    errors.extend(_llm_row_formal_gap_boundary_errors(row))
    errors.extend(_llm_row_residual_source_grounding_errors(row))
    errors.extend(_llm_row_search_request_contract_errors(row))
    errors.extend(_llm_row_planner_next_action_contract_errors(row))
    errors.extend(
        _llm_row_target_primitive_grounding_errors(
            row,
            request,
            collection_name="search_requests",
        )
    )
    errors.extend(
        _llm_row_target_primitive_grounding_errors(
            row,
            request,
            collection_name="planner_next_actions",
        )
    )
    errors.extend(_llm_row_resource_request_alignment_errors(row, request))
    errors.extend(_llm_row_source_search_obligation_errors(row))
    errors.extend(_llm_row_formal_search_obligation_errors(row))
    errors.extend(_llm_row_minimal_delta_cost_errors(row, request))
    errors.extend(_llm_row_alignment_reference_errors(row))
    errors.extend(_llm_row_route_option_realization_coverage_errors(row))
    errors.extend(_llm_row_primitive_evidence_errors(row, request))
    return tuple(errors)


def _llm_row_request_evidence_observed(
    row: dict[str, Any],
    request: dict[str, Any],
) -> str:
    if not request:
        return "matching_request=false"
    available_sources = _llm_available_source_keys(request)
    row_sources = _llm_row_source_keys(row)
    available_declarations = _llm_available_declaration_keys(request)
    row_declarations = _llm_row_candidate_declaration_keys(row)
    request_residuals = _llm_request_residual_keys(request)
    row_residuals = _llm_row_residual_keys(row)
    available_primitives = _llm_available_primitive_keys(request)
    row_primitives = _llm_row_selected_delta_primitive_keys(row)
    return (
        "matching_request=true; "
        f"provider={row.get('provider_name', '')}/{request.get('provider_name', '')}; "
        f"model_tier={row.get('model_tier', '')}/{request.get('model_tier', '')}; "
        f"source_refs={len(row_sources - available_sources)}_missing/{len(row_sources)}; "
        f"candidate_declarations={len(row_declarations - available_declarations)}_missing/{len(row_declarations)}; "
        f"residuals={len(row_residuals.intersection(request_residuals))}/{len(request_residuals)}; "
        f"introduced_primitives={len(row_primitives - available_primitives)}/{len(row_primitives)}"
    )


def _llm_row_request_model_policy_errors(
    row: dict[str, Any],
    request: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    row_provider = str(row.get("provider_name", "") or "").strip().lower()
    request_provider = str(request.get("provider_name", "") or "").strip().lower()
    row_model = str(row.get("model", "") or "").strip()
    request_model = str(request.get("model", "") or "").strip()
    row_tier = str(row.get("model_tier", "") or "").strip().lower()
    request_tier = str(request.get("model_tier", "") or "").strip().lower()
    row_evidence = _dict_value(row, "model_tier_decision_evidence")
    request_evidence = _dict_value(request, "model_tier_decision_evidence")

    if row_provider != request_provider:
        errors.append("row provider_name does not match request provider_name")

    if _llm_row_model_tier_escalated(row):
        errors.extend(
            _llm_row_request_model_escalation_errors(
                row,
                request,
                row_provider=row_provider,
                request_provider=request_provider,
                row_tier=row_tier,
                request_tier=request_tier,
                row_evidence=row_evidence,
                request_evidence=request_evidence,
            )
        )
    else:
        if row_tier != request_tier:
            errors.append("row model_tier does not match request model_tier")
        if request_provider in {"anthropic", "static"} and row_model != request_model:
            errors.append("row model does not match request model")
        if row_evidence != request_evidence:
            errors.append(
                "row model_tier_decision_evidence does not match request "
                "model_tier_decision_evidence"
            )

    metadata = _dict_value(row, "generator_metadata")
    if metadata:
        metadata_requested = str(
            metadata.get("requested_model_tier", "") or ""
        ).strip().lower()
        metadata_effective = str(
            metadata.get("effective_model_tier", "") or ""
        ).strip().lower()
        if metadata_requested and metadata_requested != request_tier:
            errors.append(
                "row generator_metadata.requested_model_tier does not match "
                "request model_tier"
            )
        if metadata_effective and metadata_effective != row_tier:
            errors.append(
                "row generator_metadata.effective_model_tier does not match "
                "row model_tier"
            )
    return tuple(errors)


def _llm_row_request_model_escalation_errors(
    row: dict[str, Any],
    request: dict[str, Any],
    *,
    row_provider: str,
    request_provider: str,
    row_tier: str,
    request_tier: str,
    row_evidence: dict[str, Any],
    request_evidence: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    if request_provider != "anthropic" or row_provider != "anthropic":
        errors.append("row model_tier_escalated is allowed only for Anthropic")
    if request_tier != "haiku":
        errors.append("row model_tier_escalated requires request model_tier haiku")
    if row_tier != "sonnet":
        errors.append("row model_tier_escalated requires row model_tier sonnet")

    metadata = _dict_value(row, "generator_metadata")
    reason = str(
        metadata.get("model_tier_escalation_reason", "")
        or row.get("model_tier_escalation_reason", "")
        or ""
    ).strip()
    if not reason:
        errors.append("row model_tier_escalated requires escalation reason")

    if not _llm_row_has_haiku_to_sonnet_repair_ledger(row):
        errors.append(
            "row model_tier_escalated requires repair_attempt_ledger "
            "documenting haiku-to-sonnet retry"
        )

    row_base = _llm_model_tier_decision_evidence_request_base(row_evidence)
    request_base = _llm_model_tier_decision_evidence_request_base(
        request_evidence
    )
    if row_base != request_base:
        errors.append(
            "row model_tier_decision_evidence changed request decision fields "
            "outside allowed repair escalation fields"
        )
    if str(row_evidence.get("effective_model_tier", "") or "").strip().lower() != (
        row_tier
    ):
        errors.append(
            "row model_tier_decision_evidence.effective_model_tier does not "
            "match row model_tier"
        )
    if not bool(row_evidence.get("model_tier_escalated", False)):
        errors.append(
            "row model_tier_decision_evidence.model_tier_escalated must be true"
        )
    if not str(
        row_evidence.get("model_tier_escalation_reason", "") or reason
    ).strip():
        errors.append(
            "row model_tier_decision_evidence.model_tier_escalation_reason missing"
        )
    return tuple(errors)


def _llm_model_tier_decision_evidence_request_base(
    evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        str(key): value
        for key, value in evidence.items()
        if str(key)
        not in {
            "effective_model_tier",
            "model_tier_escalated",
            "model_tier_escalation_reason",
        }
    }


def _llm_row_has_haiku_to_sonnet_repair_ledger(row: dict[str, Any]) -> bool:
    for item in _dict_tuple(row.get("repair_attempt_ledger", [])):
        escalation = str(item.get("model_tier_escalation", "") or "").strip().lower()
        failed_tier = str(
            item.get("failed_attempt_model_tier", "") or ""
        ).strip().lower()
        next_tier = str(item.get("next_repair_model_tier", "") or "").strip().lower()
        if escalation == "haiku_to_sonnet":
            return True
        if failed_tier == "haiku" and next_tier == "sonnet":
            return True
    return False


def _llm_row_residual_source_grounding_errors(row: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    search_requests = _dict_tuple(row.get("search_requests", []))
    for index, interpretation in enumerate(
        _dict_tuple(row.get("residual_interpretations", []))
    ):
        has_repair = bool(
            str(interpretation.get("route_repair", "")).strip()
            or str(interpretation.get("repair_action", "")).strip()
        )
        if not has_repair:
            continue
        if _llm_residual_interpretation_has_source_refs(interpretation):
            continue
        if _llm_residual_interpretation_has_formal_boundary(interpretation):
            continue
        if _llm_has_literature_search_request_for_residual_interpretation(
            search_requests,
            interpretation=interpretation,
        ):
            continue
        errors.append(
            "row residual_interpretations"
            f"[{index}] route repair requires source_refs/source_snippets, "
            "a matching literature/source search_request, or formal_gap_boundary"
        )
    return tuple(errors)


def _llm_row_formal_gap_boundary_errors(row: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    for location, item in _llm_row_formal_gap_boundary_locations(row):
        boundary = str(item.get("formal_gap_boundary", "") or "").strip()
        status_key = _llm_source_ref_key(item.get("source_search_status", ""))
        requires_boundary = bool(boundary) or status_key in {
            "formal_gap_boundary",
            "formal_boundary",
            "formal_boundary_declared",
        }
        if not requires_boundary:
            continue
        if not boundary:
            errors.append(
                f"{location}.formal_gap_boundary required when "
                "source_search_status declares a formal boundary"
            )
            continue
        if not _llm_formal_gap_boundary_is_substantive(boundary):
            errors.append(
                f"{location}.formal_gap_boundary must be a substantive formal "
                "boundary explanation, not a placeholder"
            )
    return tuple(errors)


def _llm_row_formal_gap_boundary_locations(
    row: dict[str, Any],
) -> tuple[tuple[str, dict[str, object]], ...]:
    locations: list[tuple[str, dict[str, object]]] = []
    for index, node in enumerate(
        _dict_tuple(row.get("informal_knowledge_dag_nodes", []))
    ):
        locations.append((f"row informal_knowledge_dag_nodes[{index}]", node))
    for index, residual in enumerate(
        _dict_tuple(row.get("residual_interpretations", []))
    ):
        locations.append((f"row residual_interpretations[{index}]", residual))
    for index, node in enumerate(_llm_formal_realization_nodes(row)):
        locations.append((f"row formal_realization_dag_nodes[{index}]", node))
    standalone_route = _dict_value(row, "standalone_route")
    locations.append(("row standalone_route", standalone_route))
    for index, primitive in enumerate(
        _dict_tuple(standalone_route.get("primitives", []))
    ):
        locations.append((f"row standalone_route.primitives[{index}]", primitive))
    return tuple(locations)


def _llm_formal_gap_boundary_is_substantive(text: object) -> bool:
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


def _llm_row_target_prover_consistency_errors(
    row: dict[str, Any],
    request: dict[str, Any],
) -> tuple[str, ...]:
    expected_raw = str(request.get("target_prover_family", "") or "").strip()
    expected = _target_prover_key(expected_raw)
    if not expected:
        return tuple()
    errors: list[str] = []
    target_checks: list[tuple[str, object]] = [
        ("row.target_prover_family", row.get("target_prover_family", "")),
    ]
    standalone_route = _dict_value(row, "standalone_route")
    target_checks.append(
        (
            "row standalone_route.target_prover_family",
            standalone_route.get("target_prover_family", ""),
        )
    )
    replan_metadata = _dict_value(standalone_route, "replan_metadata")
    target_checks.append(
        (
            "row standalone_route.replan_metadata.target_prover_family",
            replan_metadata.get("target_prover_family", ""),
        )
    )
    for index, node in enumerate(_llm_formal_realization_nodes(row)):
        target_checks.append(
            (
                f"row formal_realization_dag_nodes[{index}].target_prover_family",
                node.get("target_prover_family", ""),
            )
        )
    for location, hit in _llm_row_declaration_hit_locations(row):
        target_checks.append(
            (f"{location}.target_prover_family", hit.get("target_prover_family", ""))
        )
        target_checks.append((f"{location}.target_prover", hit.get("target_prover", "")))
    for location, raw_value in target_checks:
        value = str(raw_value or "").strip()
        if not value:
            continue
        if _target_prover_key(value) != expected:
            errors.append(
                f"{location} {value} does not match request target_prover_family "
                f"{expected_raw}"
            )
    if _is_non_lean_target_prover(expected_raw):
        if _dict_tuple(row.get("lean_realization_dag_nodes", [])):
            errors.append(
                "row lean_realization_dag_nodes is a Lean-only legacy alias "
                f"but request target_prover_family is {expected_raw}"
            )
        for location, _hit in _llm_row_lean_declaration_hit_locations(row):
            errors.append(
                f"{location} is a Lean-only legacy declaration field "
                f"but request target_prover_family is {expected_raw}"
            )
    return tuple(errors)


def _llm_row_declaration_hit_locations(
    row: dict[str, Any],
) -> tuple[tuple[str, dict[str, Any]], ...]:
    locations: list[tuple[str, dict[str, Any]]] = []
    containers: list[tuple[str, dict[str, Any]]] = [("row", row)]
    for index, node in enumerate(_llm_formal_realization_nodes(row)):
        containers.append((f"row formal_realization_dag_nodes[{index}]", node))
    standalone_route = _dict_value(row, "standalone_route")
    for index, primitive_row in enumerate(
        _dict_tuple(standalone_route.get("primitives", []))
    ):
        containers.append((f"row standalone_route.primitives[{index}]", primitive_row))
    for location, container in containers:
        for field_name in (
            "candidate_declaration_rows",
            "formal_declaration_hits",
            "lean_declaration_hits",
        ):
            for index, hit in enumerate(_dict_tuple(container.get(field_name, []))):
                locations.append((f"{location}.{field_name}[{index}]", hit))
    return tuple(locations)


def _llm_row_lean_declaration_hit_locations(
    row: dict[str, Any],
) -> tuple[tuple[str, dict[str, Any]], ...]:
    return tuple(
        (location, hit)
        for location, hit in _llm_row_declaration_hit_locations(row)
        if ".lean_declaration_hits[" in location
    )


def _llm_residual_interpretation_has_source_refs(
    interpretation: dict[str, object],
) -> bool:
    refs = list(_str_tuple(interpretation.get("source_refs", [])))
    for snippet in _dict_tuple(interpretation.get("source_snippets", [])):
        refs.extend(_llm_source_ref_values(snippet))
    return bool(_str_tuple(refs))


def _llm_residual_interpretation_has_formal_boundary(
    interpretation: dict[str, object],
) -> bool:
    if _llm_formal_gap_boundary_is_substantive(
        interpretation.get("formal_gap_boundary", "")
    ):
        return True
    return _llm_source_ref_key(interpretation.get("source_search_status", "")) in {
        "formal_gap_boundary",
        "formal_boundary_declared",
    }


def _llm_has_literature_search_request_for_residual_interpretation(
    search_requests: tuple[dict[str, object], ...],
    *,
    interpretation: dict[str, object],
) -> bool:
    primitives = _llm_residual_interpretation_search_primitives(interpretation)
    if primitives and _llm_has_literature_search_request_for_obligation(
        search_requests,
        primitives=primitives,
    ):
        return True
    residual_tokens = _llm_residual_interpretation_search_tokens(interpretation)
    if not residual_tokens:
        return False
    literature_kind_keys = ("literature", "source", "paper", "textbook")
    for request in search_requests:
        kind_key = _llm_primitive_key(request.get("request_kind", ""))
        if not any(key in kind_key for key in literature_kind_keys):
            continue
        request_tokens = _llm_search_text_tokens(
            " ".join(
                str(request.get(field_name, ""))
                for field_name in ("query", "reason", "action", "description")
            )
        )
        if residual_tokens & request_tokens:
            return True
    return False


def _llm_residual_interpretation_search_primitives(
    interpretation: dict[str, object],
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
            for primitive in (_llm_primitive_key(value) for value in primitives)
            if primitive
        )
    )


def _llm_residual_interpretation_search_tokens(
    interpretation: dict[str, object],
) -> set[str]:
    return _llm_search_text_tokens(
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


def _llm_search_text_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9_]+", _llm_source_ref_key(text))
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


def _llm_row_search_request_contract_errors(row: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    for index, request in enumerate(_dict_tuple(row.get("search_requests", []))):
        request_kind = _llm_source_ref_key(request.get("request_kind", ""))
        if not request_kind:
            errors.append(f"row search_requests[{index}].request_kind missing")
        elif request_kind not in LLM_ROUTE_PLANNER_SEARCH_REQUEST_KIND_ALIASES:
            errors.append(
                "row search_requests"
                f"[{index}].request_kind unsupported: {request.get('request_kind')}"
            )
        if not str(request.get("query", "")).strip():
            errors.append(f"row search_requests[{index}].query missing")
        if not str(request.get("reason", "")).strip():
            errors.append(f"row search_requests[{index}].reason missing")
    return tuple(errors)


def _llm_row_planner_next_action_contract_errors(row: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    for index, action in enumerate(_dict_tuple(row.get("planner_next_actions", []))):
        if not str(action.get("owner", "")).strip():
            errors.append(f"row planner_next_actions[{index}].owner missing")
        if not str(action.get("action", "")).strip():
            errors.append(f"row planner_next_actions[{index}].action missing")
        if not _llm_planner_next_action_has_supported_hook(action):
            errors.append(
                "row planner_next_actions"
                f"[{index}] does not resolve to a supported hook family"
            )
    return tuple(errors)


def _llm_row_target_primitive_grounding_errors(
    row: dict[str, Any],
    request: dict[str, Any],
    *,
    collection_name: str,
) -> tuple[str, ...]:
    allowed_primitives = _llm_row_bounded_action_allowed_primitive_keys(row, request)
    errors: list[str] = []
    for index, action in enumerate(_dict_tuple(row.get(collection_name, []))):
        target_primitives = _llm_planner_action_target_primitive_keys(action)
        if not target_primitives:
            continue
        ungrounded = sorted(target_primitives - allowed_primitives)
        if ungrounded:
            errors.append(
                f"row {collection_name}[{index}].target_primitives must be drawn "
                "from request, route, formal-realization, residual, or "
                "cost-hint primitive evidence; ungrounded target_primitives: "
                + ",".join(ungrounded[:8])
            )
    return tuple(errors)


def _llm_row_resource_request_alignment_errors(
    row: dict[str, Any],
    request: dict[str, Any],
) -> tuple[str, ...]:
    return tuple(
        "row " + error
        for error in _llm_route_planner_resource_request_alignment_errors(
            row,
            request,
        )
    )


def _llm_row_bounded_action_allowed_primitive_keys(
    row: dict[str, Any],
    request: dict[str, Any],
) -> set[str]:
    minimal_delta = _dict_value(row, "minimal_delta_plan")
    selected, delta_primitives = _llm_row_selected_and_delta_primitive_keys(row)
    allowed = set(_llm_available_primitive_keys(request))
    allowed.update(selected)
    allowed.update(delta_primitives)
    allowed.update(_llm_request_primitive_cost_hints_by_primitive(request))
    allowed.update(_llm_row_route_option_primitive_keys(row))
    for cost_row in _dict_tuple(minimal_delta.get("primitive_costs", [])):
        primitive = _llm_primitive_key(cost_row.get("primitive", ""))
        if primitive:
            allowed.add(primitive)
    for option in _dict_tuple(
        _dict_value(minimal_delta, "and_or_cost_graph").get("route_options", [])
    ):
        for cost_row in _dict_tuple(option.get("primitive_costs", [])):
            primitive = _llm_primitive_key(cost_row.get("primitive", ""))
            if primitive:
                allowed.add(primitive)
    for node in _llm_formal_realization_nodes(row):
        primitive = _llm_primitive_key(node.get("primitive", ""))
        if primitive:
            allowed.add(primitive)
    for primitive_row in _dict_tuple(
        _dict_value(row, "standalone_route").get("primitives", [])
    ):
        primitive = _llm_primitive_key(primitive_row.get("primitive", ""))
        if primitive:
            allowed.add(primitive)
    allowed.update(_llm_alignment_edges_by_primitive(row))
    for interpretation in _dict_tuple(row.get("residual_interpretations", [])):
        allowed.update(_llm_residual_interpretation_search_primitives(interpretation))
    allowed.discard("")
    return allowed


def _llm_planner_action_target_primitive_keys(
    action: dict[str, Any],
) -> set[str]:
    primitives: set[str] = set()
    for field_name in (
        "target_primitive",
        "target_primitives",
        "primitive",
        "primitives",
    ):
        primitives.update(
            primitive
            for primitive in (
                _llm_primitive_key(value)
                for value in _llm_primitive_values(action.get(field_name))
            )
            if primitive
        )
    return primitives


def _llm_planner_next_action_has_supported_hook(action: dict[str, Any]) -> bool:
    text_key = _llm_source_ref_key(
        " ".join(
            [
                *_llm_planner_action_queries(action),
                *_llm_planner_action_resource_refs(action),
            ]
        )
    )
    return any(
        _llm_text_key_contains_alias(text_key, alias)
        for alias in LLM_ROUTE_PLANNER_PLANNER_NEXT_ACTION_HOOK_ALIASES
    )


def _llm_planner_action_queries(action: dict[str, Any]) -> tuple[str, ...]:
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


def _llm_planner_action_resource_refs(action: dict[str, Any]) -> tuple[str, ...]:
    refs: list[str] = []
    _llm_collect_planner_action_resource_refs(action, refs)
    return _str_tuple(refs)


def _llm_collect_planner_action_resource_refs(value: Any, refs: list[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = _llm_primitive_key(key)
            if key_text in {
                "resource_request_id",
                "resource_request_ids",
                "resource_id",
                "resource_ids",
                "resource",
                "resources",
                "adapter_id",
                "adapter_ids",
                "mcp_or_cli_hint",
                "owner",
                "tool",
                "tools",
                "tool_name",
                "tool_names",
                "recommended_tool",
                "recommended_tools",
            }:
                refs.extend(_str_tuple(item))
            _llm_collect_planner_action_resource_refs(item, refs)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _llm_collect_planner_action_resource_refs(item, refs)


def _llm_text_key_contains_alias(text_key: str, alias: str) -> bool:
    return f"_{alias}_" in f"_{text_key}_"


def _llm_row_source_search_obligation_errors(row: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    search_requests = _dict_tuple(row.get("search_requests", []))
    for index, node in enumerate(
        _dict_tuple(row.get("informal_knowledge_dag_nodes", []))
    ):
        status = _llm_source_ref_key(node.get("source_search_status", ""))
        if not _llm_source_search_status_requires_request(status):
            continue
        primitives = _llm_informal_node_search_primitives(node)
        if not _llm_has_literature_search_request_for_obligation(
            search_requests,
            primitives=primitives,
        ):
            errors.append(
                "row informal_knowledge_dag_nodes"
                f"[{index}] SEARCH_REQUESTED requires a matching literature/source search_request"
            )
    route = _dict_value(row, "standalone_route")
    for index, primitive_row in enumerate(_dict_tuple(route.get("primitives", []))):
        status = _llm_source_ref_key(primitive_row.get("source_search_status", ""))
        if not _llm_source_search_status_requires_request(status):
            continue
        primitives = _str_tuple(
            [
                *_str_tuple(primitive_row.get("target_primitives", [])),
                *_str_tuple(primitive_row.get("primitive", "")),
            ]
        )
        if not _llm_has_literature_search_request_for_obligation(
            search_requests,
            primitives=tuple(_llm_primitive_key(primitive) for primitive in primitives),
        ):
            errors.append(
                "row standalone_route.primitives"
                f"[{index}] SEARCH_REQUESTED requires a matching literature/source search_request"
            )
    return tuple(errors)


def _llm_source_search_status_requires_request(status: str) -> bool:
    return status in {
        "search_requested",
        "source_search_requested",
        "source_search_pending",
        "literature_search_requested",
        "literature_search_pending",
    }


def _llm_informal_node_search_primitives(node: dict[str, object]) -> tuple[str, ...]:
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
            for primitive in (_llm_primitive_key(value) for value in primitives)
            if primitive
        )
    )


def _llm_has_literature_search_request_for_obligation(
    search_requests: tuple[dict[str, object], ...],
    *,
    primitives: tuple[str, ...],
) -> bool:
    literature_kind_keys = ("literature", "source", "paper", "textbook")
    if primitives:
        return any(
            _llm_has_search_request_for_primitive(
                search_requests,
                primitive=primitive,
                request_kind_keys=literature_kind_keys,
            )
            for primitive in primitives
        )
    return any(
        any(
            key in _llm_primitive_key(request.get("request_kind", ""))
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


def _llm_row_formal_search_obligation_errors(row: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    search_requests = _dict_tuple(row.get("search_requests", []))
    for index, node in enumerate(_llm_formal_realization_nodes(row)):
        if not _llm_formal_node_requires_library_search(node):
            continue
        primitives = _llm_formal_node_search_primitives(node)
        if not _llm_has_formal_library_search_request_for_obligation(
            search_requests,
            primitives=primitives,
        ):
            errors.append(
                "row formal_realization_dag_nodes"
                f"[{index}] unknown/formal-library-search-pending coverage requires a matching formal_library/library search_request"
            )
    route = _dict_value(row, "standalone_route")
    for index, primitive_row in enumerate(_dict_tuple(route.get("primitives", []))):
        if not _llm_formal_node_requires_library_search(primitive_row):
            continue
        primitives = _str_tuple(
            [
                *_str_tuple(primitive_row.get("target_primitives", [])),
                *_str_tuple(primitive_row.get("primitive", "")),
            ]
        )
        if not _llm_has_formal_library_search_request_for_obligation(
            search_requests,
            primitives=tuple(_llm_primitive_key(primitive) for primitive in primitives),
        ):
            errors.append(
                "row standalone_route.primitives"
                f"[{index}] unknown/formal-library-search-pending coverage requires a matching formal_library/library search_request"
            )
    return tuple(errors)


def _llm_formal_node_requires_library_search(node: dict[str, object]) -> bool:
    if _str_tuple(node.get("candidate_declarations", [])):
        return False
    if _llm_formal_gap_boundary_is_substantive(node.get("formal_gap_boundary", "")):
        return False
    markers = (
        node.get("coverage_bucket", ""),
        node.get("coverage_status", ""),
        node.get("formalization_action", ""),
        node.get("alignment_status", ""),
        node.get("formal_search_status", ""),
        node.get("library_search_status", ""),
    )
    if any(_llm_delta_formalization_marker(marker) for marker in markers):
        return False
    return any(_llm_formal_library_search_marker(marker) for marker in markers)


def _llm_formal_library_search_marker(value: object) -> bool:
    return _llm_primitive_key(value) in {
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


def _llm_formal_node_search_primitives(node: dict[str, object]) -> tuple[str, ...]:
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
            for primitive in (_llm_primitive_key(value) for value in primitives)
            if primitive
        )
    )


def _llm_has_formal_library_search_request_for_obligation(
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
            _llm_has_search_request_for_primitive(
                search_requests,
                primitive=primitive,
                request_kind_keys=formal_kind_keys,
            )
            for primitive in primitives
        )
    return any(
        any(
            key in _llm_primitive_key(request.get("request_kind", ""))
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


def _llm_row_minimal_delta_cost_errors(
    row: dict[str, Any],
    request: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    minimal_delta = _dict_value(row, "minimal_delta_plan")
    if str(minimal_delta.get("cost_model_version", "")).strip() != MINIMAL_DELTA_COST_POLICY_ID:
        errors.append(
            "row minimal_delta_plan.cost_model_version must equal "
            + MINIMAL_DELTA_COST_POLICY_ID
        )
    if not _nonnegative_number(minimal_delta.get("route_cost")):
        errors.append("row minimal_delta_plan.route_cost must be a nonnegative number")
    selected = {
        _llm_primitive_key(primitive)
        for primitive in _str_tuple(minimal_delta.get("selected_primitives", []))
        if _llm_primitive_key(primitive)
    }
    duplicate_selected_primitives = _llm_duplicate_primitive_keys(
        minimal_delta.get("selected_primitives", [])
    )
    if duplicate_selected_primitives:
        errors.append(
            "row minimal_delta_plan.selected_primitives must not contain duplicates: "
            + ", ".join(duplicate_selected_primitives[:8])
        )
    primitive_costs = _dict_tuple(minimal_delta.get("primitive_costs", []))
    if not primitive_costs:
        errors.append("row minimal_delta_plan.primitive_costs must be non-empty")
    if primitive_costs:
        cost_rows_by_primitive: dict[str, list[dict[str, object]]] = {}
        for index, cost_row in enumerate(primitive_costs):
            primitive = _llm_primitive_key(cost_row.get("primitive", ""))
            if not primitive:
                errors.append(
                    f"row minimal_delta_plan.primitive_costs[{index}].primitive missing"
                )
                continue
            cost_rows_by_primitive.setdefault(primitive, []).append(cost_row)
            if not _nonnegative_number(cost_row.get("total_cost")):
                errors.append(
                    "row minimal_delta_plan."
                    f"primitive_costs[{index}].total_cost must be a nonnegative number"
                )
            cost_dimension_error = _llm_row_primitive_cost_dimension_error(cost_row)
            if cost_dimension_error:
                errors.append(
                    "row minimal_delta_plan."
                    f"primitive_costs[{index}].{cost_dimension_error}"
                )
            if not str(cost_row.get("cost_rationale", "")).strip():
                errors.append(
                    f"row minimal_delta_plan.primitive_costs[{index}].cost_rationale missing"
                )
        missing = sorted(selected - set(cost_rows_by_primitive))
        if missing:
            errors.append(
                "row minimal_delta_plan.primitive_costs missing selected primitives: "
                + ", ".join(missing[:8])
            )
        route_option_primitives = _llm_minimal_delta_route_option_primitive_keys(
            minimal_delta
        )
        missing_route_option_cost_rows = sorted(
            route_option_primitives - set(cost_rows_by_primitive)
        )
        if missing_route_option_cost_rows:
            errors.append(
                "row minimal_delta_plan.primitive_costs missing route option primitives: "
                + ", ".join(missing_route_option_cost_rows[:8])
            )
        duplicate = sorted(
            primitive
            for primitive in selected
            if len(cost_rows_by_primitive.get(primitive, [])) != 1
        )
        if duplicate:
            errors.append(
                "row minimal_delta_plan.primitive_costs must contain exactly one row per selected primitive: "
                + ", ".join(duplicate[:8])
            )
        duplicate_route_option_cost_rows = sorted(
            primitive
            for primitive, rows in cost_rows_by_primitive.items()
            if primitive in route_option_primitives and len(rows) != 1
        )
        if duplicate_route_option_cost_rows:
            errors.append(
                "row minimal_delta_plan.primitive_costs must contain exactly one row per route option primitive: "
                + ", ".join(duplicate_route_option_cost_rows[:8])
            )
        route_cost_error = _llm_row_route_cost_selected_primitive_error(
            minimal_delta,
            selected=selected,
            cost_rows_by_primitive=cost_rows_by_primitive,
        )
        if route_cost_error:
            errors.append(route_cost_error)
        errors.extend(
            _llm_row_route_option_cost_accounting_errors(
                minimal_delta,
                global_cost_rows_by_primitive=cost_rows_by_primitive,
            )
        )
    errors.extend(
        _llm_row_and_or_cost_graph_errors(
            minimal_delta,
            selected=selected,
        )
    )
    errors.extend(
        _llm_row_route_option_primitive_hint_errors(
            minimal_delta,
            _llm_request_primitive_cost_hints_by_primitive(request),
        )
    )
    return tuple(errors)


def _llm_minimal_delta_route_option_primitive_keys(
    minimal_delta: Mapping[str, Any],
) -> set[str]:
    graph = _dict_value(minimal_delta, "and_or_cost_graph")
    primitives: set[str] = set()
    for option in _dict_tuple(graph.get("route_options", [])):
        primitives.update(
            primitive
            for primitive in (
                _llm_primitive_key(value)
                for value in _str_tuple(option.get("selected_primitives", []))
            )
            if primitive
        )
    return primitives


def _llm_row_primitive_cost_dimension_error(cost_row: dict[str, object]) -> str:
    dimension_fields = (
        "base_cost",
        "proof_difficulty_cost",
        "import_cone_cost",
        "definition_or_typeclass_cost",
        "semantic_risk_cost",
        "reuse_credit",
    )
    missing = [field_name for field_name in dimension_fields if field_name not in cost_row]
    if missing:
        return "cost dimension fields missing: " + ", ".join(missing)
    nonnumeric = [
        field_name
        for field_name in dimension_fields
        if not _nonnegative_number(cost_row.get(field_name))
    ]
    if nonnumeric:
        return "cost dimension fields must be nonnegative numbers: " + ", ".join(
            nonnumeric
        )
    if not _nonnegative_number(cost_row.get("total_cost")):
        return ""
    accounted = (
        float(cost_row.get("base_cost", 0) or 0)
        + float(cost_row.get("proof_difficulty_cost", 0) or 0)
        + float(cost_row.get("import_cone_cost", 0) or 0)
        + float(cost_row.get("definition_or_typeclass_cost", 0) or 0)
        + float(cost_row.get("semantic_risk_cost", 0) or 0)
        - float(cost_row.get("reuse_credit", 0) or 0)
    )
    if abs(accounted - float(cost_row.get("total_cost", 0))) > 1e-9:
        return (
            "total_cost must equal base_cost + proof_difficulty_cost + "
            "import_cone_cost + definition_or_typeclass_cost + "
            "semantic_risk_cost - reuse_credit"
        )
    return ""


def _llm_row_route_cost_selected_primitive_error(
    minimal_delta: dict[str, Any],
    *,
    selected: set[str],
    cost_rows_by_primitive: dict[str, list[dict[str, object]]],
) -> str:
    route_cost = minimal_delta.get("route_cost")
    if not selected or not _nonnegative_number(route_cost):
        return ""
    selected_rows: list[dict[str, object]] = []
    for primitive in sorted(selected):
        rows = cost_rows_by_primitive.get(primitive, [])
        if len(rows) != 1 or not _nonnegative_number(rows[0].get("total_cost")):
            return ""
        selected_rows.append(rows[0])
    primitive_total = sum(float(row.get("total_cost", 0) or 0) for row in selected_rows)
    if abs(primitive_total - float(route_cost)) > 1e-9:
        return (
            "row minimal_delta_plan.route_cost must equal the sum of selected "
            "primitive_costs total_cost values"
        )
    return ""


def _llm_row_route_option_cost_accounting_errors(
    minimal_delta: Mapping[str, Any],
    *,
    global_cost_rows_by_primitive: Mapping[str, list[dict[str, object]]],
) -> list[str]:
    errors: list[str] = []
    graph = _dict_value(minimal_delta, "and_or_cost_graph")
    for option_index, option in enumerate(_dict_tuple(graph.get("route_options", []))):
        route_cost = option.get("route_cost")
        if not _nonnegative_number(route_cost):
            continue
        option_primitives = tuple(
            dict.fromkeys(
                primitive
                for primitive in (
                    _llm_primitive_key(value)
                    for value in _str_tuple(option.get("selected_primitives", []))
                )
                if primitive
            )
        )
        if not option_primitives:
            continue
        option_cost_rows = _dict_tuple(option.get("primitive_costs", []))
        if option_cost_rows:
            cost_rows_by_primitive: dict[str, list[dict[str, object]]] = {}
            for row_index, cost_row in enumerate(option_cost_rows):
                primitive = _llm_primitive_key(cost_row.get("primitive", ""))
                if not primitive:
                    errors.append(
                        "row minimal_delta_plan.and_or_cost_graph."
                        f"route_options[{option_index}].primitive_costs"
                        f"[{row_index}].primitive missing"
                    )
                    continue
                cost_rows_by_primitive.setdefault(primitive, []).append(cost_row)
                if not _nonnegative_number(cost_row.get("total_cost")):
                    errors.append(
                        "row minimal_delta_plan.and_or_cost_graph."
                        f"route_options[{option_index}].primitive_costs"
                        f"[{row_index}].total_cost must be a nonnegative number"
                    )
                cost_dimension_error = _llm_row_primitive_cost_dimension_error(cost_row)
                if cost_dimension_error:
                    errors.append(
                        "row minimal_delta_plan.and_or_cost_graph."
                        f"route_options[{option_index}].primitive_costs"
                        f"[{row_index}].{cost_dimension_error}"
                    )
                if not str(cost_row.get("cost_rationale", "")).strip():
                    errors.append(
                        "row minimal_delta_plan.and_or_cost_graph."
                        f"route_options[{option_index}].primitive_costs"
                        f"[{row_index}].cost_rationale missing"
                    )
            option_primitive_set = set(option_primitives)
            unknown = sorted(set(cost_rows_by_primitive) - option_primitive_set)
            if unknown:
                errors.append(
                    "row minimal_delta_plan.and_or_cost_graph."
                    f"route_options[{option_index}].primitive_costs reference "
                    "primitives not selected by the route option: "
                    + ", ".join(unknown[:8])
                )
            missing = sorted(option_primitive_set - set(cost_rows_by_primitive))
            if missing:
                errors.append(
                    "row minimal_delta_plan.and_or_cost_graph."
                    f"route_options[{option_index}].primitive_costs missing "
                    "route option primitives: "
                    + ", ".join(missing[:8])
                )
            duplicate = sorted(
                primitive
                for primitive, rows in cost_rows_by_primitive.items()
                if primitive in option_primitive_set and len(rows) != 1
            )
            if duplicate:
                errors.append(
                    "row minimal_delta_plan.and_or_cost_graph."
                    f"route_options[{option_index}].primitive_costs must contain "
                    "exactly one row per route option primitive: "
                    + ", ".join(duplicate[:8])
                )
        else:
            cost_rows_by_primitive = {
                primitive: list(rows)
                for primitive, rows in global_cost_rows_by_primitive.items()
            }
        accounting_error = _llm_row_route_option_cost_accounting_error(
            route_cost,
            option_primitives=option_primitives,
            cost_rows_by_primitive=cost_rows_by_primitive,
        )
        if accounting_error:
            errors.append(
                "row minimal_delta_plan.and_or_cost_graph."
                f"route_options[{option_index}].route_cost "
                + accounting_error
            )
    return errors


def _llm_row_route_option_cost_accounting_error(
    route_cost: object,
    *,
    option_primitives: tuple[str, ...],
    cost_rows_by_primitive: Mapping[str, list[dict[str, object]]],
) -> str:
    if not _nonnegative_number(route_cost) or not option_primitives:
        return ""
    option_rows: list[dict[str, object]] = []
    for primitive in option_primitives:
        rows = cost_rows_by_primitive.get(primitive, [])
        if len(rows) != 1 or not _nonnegative_number(rows[0].get("total_cost")):
            return ""
        option_rows.append(rows[0])
    primitive_total = sum(float(row.get("total_cost", 0) or 0) for row in option_rows)
    if abs(primitive_total - float(route_cost)) > 1e-9:
        return (
            "must equal the sum of route option primitive_costs total_cost values "
            f"(route_cost={float(route_cost):g}, primitive_total={primitive_total:g}); "
            "add route_options[].primitive_costs when this option uses "
            "route-specific primitive costs"
        )
    return ""


def _llm_row_and_or_cost_graph_errors(
    minimal_delta: dict[str, Any],
    *,
    selected: set[str],
) -> tuple[str, ...]:
    errors: list[str] = []
    graph = _dict_value(minimal_delta, "and_or_cost_graph")
    if not graph:
        return ("row minimal_delta_plan.and_or_cost_graph must be non-empty",)
    if str(graph.get("graph_kind", "")).strip() != "AND_OR_ROUTE_COST_GRAPH":
        errors.append(
            "row minimal_delta_plan.and_or_cost_graph.graph_kind must equal "
            "AND_OR_ROUTE_COST_GRAPH"
        )
    selected_route_option_id = str(
        graph.get("selected_route_option_id", "")
    ).strip()
    if not selected_route_option_id:
        errors.append(
            "row minimal_delta_plan.and_or_cost_graph.selected_route_option_id missing"
        )
    route_options = _dict_tuple(graph.get("route_options", []))
    if not route_options:
        errors.append(
            "row minimal_delta_plan.and_or_cost_graph.route_options must be non-empty"
        )
        return tuple(errors)
    selected_options: list[dict[str, object]] = []
    selected_option_cost: float | None = None
    route_option_ids: set[str] = set()
    route_option_primitives: set[str] = set()
    route_option_primitives_by_id: dict[str, set[str]] = {}
    for index, option in enumerate(route_options):
        option_id = str(option.get("route_option_id", "")).strip()
        if not option_id:
            errors.append(
                "row minimal_delta_plan.and_or_cost_graph."
                f"route_options[{index}].route_option_id missing"
            )
        elif option_id in route_option_ids:
            errors.append(
                "row minimal_delta_plan.and_or_cost_graph."
                f"route_options[{index}].route_option_id duplicates another route option: "
                + option_id
            )
        else:
            route_option_ids.add(option_id)
        option_cost = option.get("route_cost")
        if not _nonnegative_number(option_cost):
            errors.append(
                "row minimal_delta_plan.and_or_cost_graph."
                f"route_options[{index}].route_cost must be a nonnegative number"
            )
        if not str(option.get("cost_rationale", "")).strip():
            errors.append(
                "row minimal_delta_plan.and_or_cost_graph."
                f"route_options[{index}].cost_rationale missing"
            )
        duplicate_option_primitives = _llm_duplicate_primitive_keys(
            option.get("selected_primitives", [])
        )
        if duplicate_option_primitives:
            errors.append(
                "row minimal_delta_plan.and_or_cost_graph."
                f"route_options[{index}].selected_primitives must not contain duplicates: "
                + ", ".join(duplicate_option_primitives[:8])
            )
        option_primitives = {
            _llm_primitive_key(primitive)
            for primitive in _str_tuple(option.get("selected_primitives", []))
            if _llm_primitive_key(primitive)
        }
        route_option_primitives.update(option_primitives)
        if option_id:
            route_option_primitives_by_id[option_id] = option_primitives
        if not option_primitives:
            errors.append(
                "row minimal_delta_plan.and_or_cost_graph."
                f"route_options[{index}].selected_primitives must be non-empty"
            )
        if bool(option.get("selected", False)):
            selected_options.append(option)
            if selected_route_option_id and option_id != selected_route_option_id:
                errors.append(
                    "row minimal_delta_plan.and_or_cost_graph selected option id "
                    "does not match selected_route_option_id"
                )
            if _nonnegative_number(option_cost):
                selected_option_cost = float(option_cost)
            if option_primitives != selected:
                errors.append(
                    "row minimal_delta_plan.and_or_cost_graph selected route option "
                    "selected_primitives must match selected_primitives"
                )
    if selected_route_option_id and selected_route_option_id not in route_option_ids:
        errors.append(
            "row minimal_delta_plan.and_or_cost_graph.selected_route_option_id "
            "references unknown route option: "
            + selected_route_option_id
        )
    errors.extend(
        _llm_row_and_or_cost_graph_structure_errors(
            graph,
            route_option_ids=route_option_ids,
            route_option_primitives=route_option_primitives,
            route_option_primitives_by_id=route_option_primitives_by_id,
        )
    )
    if len(selected_options) != 1:
        errors.append(
            "row minimal_delta_plan.and_or_cost_graph must mark exactly one selected route option"
        )
    route_cost = minimal_delta.get("route_cost")
    if selected_option_cost is not None and _nonnegative_number(route_cost):
        if abs(selected_option_cost - float(route_cost)) > 1e-9:
            errors.append(
                "row minimal_delta_plan.and_or_cost_graph selected route_cost must equal route_cost"
            )
        cheaper = [
            str(option.get("route_option_id", "")).strip() or f"route_options[{index}]"
            for index, option in enumerate(route_options)
            if _nonnegative_number(option.get("route_cost"))
            and float(option.get("route_cost", 0)) + 1e-9 < selected_option_cost
        ]
        if cheaper:
            errors.append(
                "row minimal_delta_plan.and_or_cost_graph selected route option is not minimal; "
                "cheaper options: "
                + ", ".join(cheaper[:8])
            )
    return tuple(errors)


def _llm_request_primitive_cost_hints_by_primitive(
    request: dict[str, Any],
) -> dict[str, dict[str, object]]:
    context = _dict_value(request, "context_packet")
    hints = _dict_value(context, "minimal_delta_cost_hints")
    by_primitive: dict[str, dict[str, object]] = {}
    for hint in _dict_tuple(hints.get("primitive_cost_hints", [])):
        primitive = _llm_primitive_key(hint.get("primitive", ""))
        if not primitive or not _nonnegative_number(hint.get("minimum_base_cost")):
            continue
        current = by_primitive.get(primitive)
        if current is None or float(hint.get("minimum_base_cost", 0) or 0) > float(
            current.get("minimum_base_cost", 0) or 0
        ):
            by_primitive[primitive] = dict(hint)
    return by_primitive


def _llm_row_route_option_primitive_hint_errors(
    minimal_delta: dict[str, Any],
    primitive_hints: dict[str, dict[str, object]],
) -> tuple[str, ...]:
    graph = _dict_value(minimal_delta, "and_or_cost_graph")
    errors: list[str] = []
    if not primitive_hints:
        return tuple(errors)
    for index, option in enumerate(_dict_tuple(graph.get("route_options", []))):
        option_cost = option.get("route_cost")
        if not _nonnegative_number(option_cost):
            continue
        option_primitives = tuple(
            dict.fromkeys(
                primitive
                for primitive in (
                    _llm_primitive_key(value)
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
                "row minimal_delta_plan.and_or_cost_graph.route_options"
                f"[{index}].route_cost underprices request primitive cost hints: "
                f"route_cost={float(option_cost or 0):g} but "
                f"minimum_known_base_cost={minimum_known_base_cost:g} "
                f"primitives={','.join(hinted_primitives)} "
                f"sources={','.join(dict.fromkeys(sources))} "
                f"markers={','.join(dict.fromkeys(markers))}"
            )
    return tuple(errors)


def _llm_row_and_or_cost_graph_structure_errors(
    graph: dict[str, Any],
    *,
    route_option_ids: set[str],
    route_option_primitives: set[str],
    route_option_primitives_by_id: dict[str, set[str]],
) -> list[str]:
    prefix = "row minimal_delta_plan.and_or_cost_graph"
    errors: list[str] = []
    or_nodes = _dict_tuple(graph.get("or_nodes", []))
    route_options_referenced_by_or_nodes: set[str] = set()
    if not or_nodes:
        errors.append(f"{prefix}.or_nodes must be non-empty")
    for index, node in enumerate(or_nodes):
        if not str(node.get("node_id", "")).strip():
            errors.append(f"{prefix}.or_nodes[{index}].node_id missing")
        choices = _str_tuple(node.get("choices", []))
        route_options_referenced_by_or_nodes.update(
            choice for choice in choices if choice in route_option_ids
        )
        if not choices:
            errors.append(f"{prefix}.or_nodes[{index}].choices must be non-empty")
        duplicate_choices = _llm_duplicate_string_keys(node.get("choices", []))
        if duplicate_choices:
            errors.append(
                f"{prefix}.or_nodes[{index}].choices must not contain duplicates: "
                + ", ".join(duplicate_choices[:8])
            )
        unknown_choices = [
            choice
            for choice in choices
            if choice not in route_option_ids
            and _llm_primitive_key(choice) not in route_option_primitives
        ]
        if unknown_choices:
            errors.append(
                f"{prefix}.or_nodes[{index}].choices reference unknown route options or primitives: "
                + ", ".join(unknown_choices[:8])
            )
        if not str(node.get("selection_rationale", "")).strip():
            errors.append(f"{prefix}.or_nodes[{index}].selection_rationale missing")
    unreachable_route_options = sorted(
        route_option_ids - route_options_referenced_by_or_nodes
    )
    if unreachable_route_options:
        errors.append(
            f"{prefix}.or_nodes choices must reference every route option; "
            "unreachable route options: "
            + ", ".join(unreachable_route_options[:8])
        )
    and_edges = _dict_tuple(graph.get("and_edges", []))
    route_options_referenced_by_and_edges: set[str] = set()
    and_edge_count_by_route_option: dict[str, int] = {}
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
        else:
            route_options_referenced_by_and_edges.add(option_id)
            and_edge_count_by_route_option[option_id] = (
                and_edge_count_by_route_option.get(option_id, 0) + 1
            )
        requires = _str_tuple(edge.get("requires", []))
        if not requires:
            errors.append(f"{prefix}.and_edges[{index}].requires must be non-empty")
        duplicate_requires = _llm_duplicate_primitive_keys(edge.get("requires", []))
        if duplicate_requires:
            errors.append(
                f"{prefix}.and_edges[{index}].requires must not contain duplicate primitives: "
                + ", ".join(duplicate_requires[:8])
            )
        require_primitives = {
            _llm_primitive_key(primitive)
            for primitive in requires
            if _llm_primitive_key(primitive)
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
            if _llm_primitive_key(primitive) not in route_option_primitives
        ]
        if unknown_requires:
            errors.append(
                f"{prefix}.and_edges[{index}].requires reference unknown primitives: "
                + ", ".join(unknown_requires[:8])
            )
    route_options_without_and_edges = sorted(
        route_option_ids - route_options_referenced_by_and_edges
    )
    if route_options_without_and_edges:
        errors.append(
            f"{prefix}.and_edges must include every route option; "
            "route options without AND edges: "
            + ", ".join(route_options_without_and_edges[:8])
        )
    route_options_with_duplicate_and_edges = sorted(
        option_id
        for option_id, count in and_edge_count_by_route_option.items()
        if count > 1
    )
    if route_options_with_duplicate_and_edges:
        errors.append(
            f"{prefix}.and_edges must include exactly one edge per route option; "
            "route options with duplicate AND edges: "
            + ", ".join(route_options_with_duplicate_and_edges[:8])
        )
    return errors


def _nonnegative_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0


def _numeric(value: object) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def _llm_available_source_keys(request: dict[str, Any]) -> set[str]:
    context = _dict_value(request, "context_packet")
    refs = list(_str_tuple(context.get("available_source_refs", [])))
    if not refs:
        _llm_collect_source_refs(request.get("target_route", {}), refs)
        _llm_collect_source_refs(context, refs)
    return {_llm_source_ref_key(ref) for ref in refs if _llm_source_ref_key(ref)}


def _llm_row_source_keys(row: dict[str, Any]) -> set[str]:
    refs: list[str] = []
    refs.extend(_str_tuple(row.get("source_refs", [])))
    for node in _dict_tuple(row.get("informal_knowledge_dag_nodes", [])):
        refs.extend(_str_tuple(node.get("source_refs", [])))
    for residual in _dict_tuple(row.get("residual_interpretations", [])):
        refs.extend(_str_tuple(residual.get("source_refs", [])))
    route = _dict_value(row, "standalone_route")
    refs.extend(_str_tuple(route.get("source_refs", [])))
    for primitive in _dict_tuple(route.get("primitives", [])):
        refs.extend(_str_tuple(primitive.get("source_refs", [])))
    return {_llm_source_ref_key(ref) for ref in refs if _llm_source_ref_key(ref)}


def _llm_collect_source_refs(value: Any, refs: list[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key) in {
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
                refs.extend(_llm_source_ref_values(item))
            _llm_collect_source_refs(item, refs)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _llm_collect_source_refs(item, refs)


def _llm_source_ref_values(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value.strip() else tuple()
    if isinstance(value, dict):
        refs: list[str] = []
        for key in ("source_ref", "source_id", "citation_key", "paper_id", "id"):
            if key in value:
                refs.extend(_llm_source_ref_values(value.get(key)))
        return _str_tuple(refs)
    if isinstance(value, (list, tuple, set)):
        refs: list[str] = []
        for item in value:
            refs.extend(_llm_source_ref_values(item))
        return _str_tuple(refs)
    return tuple()


def _llm_source_ref_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def _llm_available_declaration_keys(request: dict[str, Any]) -> set[str]:
    context = _dict_value(request, "context_packet")
    declarations = list(
        _llm_declaration_values(context.get("available_formal_declarations", []))
    )
    if not declarations:
        _llm_collect_declarations(request.get("target_route", {}), declarations)
        _llm_collect_declarations(context, declarations)
    return {
        _llm_declaration_key(declaration)
        for declaration in declarations
        if _llm_declaration_key(declaration)
    }


def _llm_row_candidate_declaration_keys(row: dict[str, Any]) -> set[str]:
    declarations: list[str] = []
    for node in _llm_formal_realization_nodes(row):
        declarations.extend(_llm_declaration_values(node.get("candidate_declarations", [])))
    route = _dict_value(row, "standalone_route")
    for primitive in _dict_tuple(route.get("primitives", [])):
        declarations.extend(
            _llm_declaration_values(primitive.get("candidate_declarations", []))
        )
    return {
        _llm_declaration_key(declaration)
        for declaration in declarations
        if _llm_declaration_key(declaration)
    }


def _llm_collect_declarations(value: Any, declarations: list[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key) in {
                "candidate_declaration",
                "candidate_declarations",
                "declaration",
                "declaration_name",
                "declaration_names",
                "lean_declaration",
                "lean_declarations",
                "lean_declaration_hits",
            }:
                declarations.extend(_llm_declaration_values(item))
            _llm_collect_declarations(item, declarations)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _llm_collect_declarations(item, declarations)


def _llm_declaration_values(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value.strip() else tuple()
    if isinstance(value, dict):
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
                declarations.extend(_llm_declaration_values(value.get(key)))
        return _str_tuple(declarations)
    if isinstance(value, (list, tuple, set)):
        declarations: list[str] = []
        for item in value:
            declarations.extend(_llm_declaration_values(item))
        return _str_tuple(declarations)
    return tuple()


def _llm_declaration_key(value: object) -> str:
    return re.sub(r"[^a-z0-9_'.]+", "_", str(value or "").strip().lower()).strip("_")


def _llm_formal_realization_nodes(row: dict[str, Any]) -> tuple[dict[str, object], ...]:
    nodes = _dict_tuple(row.get("formal_realization_dag_nodes", []))
    if nodes:
        return nodes
    if _is_non_lean_target_prover(_llm_target_prover_family(row)):
        return tuple()
    return _dict_tuple(row.get("lean_realization_dag_nodes", []))


def _llm_revised_formal_realization_nodes(row: dict[str, Any]) -> tuple[dict[str, object], ...]:
    nodes = _dict_tuple(row.get("revised_formal_realization_dag_nodes", []))
    if nodes:
        return nodes
    if _is_non_lean_target_prover(_llm_target_prover_family(row)):
        return tuple()
    return _dict_tuple(row.get("revised_lean_realization_dag_nodes", []))


def _llm_target_prover_family(row: dict[str, Any]) -> str:
    candidates: list[object] = [
        row.get("target_prover_family", ""),
        row.get("target_prover", ""),
    ]
    metadata = row.get("replan_metadata", {})
    if isinstance(metadata, dict):
        candidates.extend(
            [
                metadata.get("target_prover_family", ""),
                metadata.get("target_prover", ""),
            ]
        )
    standalone_route = row.get("standalone_route", {})
    if isinstance(standalone_route, dict):
        candidates.extend(
            [
                standalone_route.get("target_prover_family", ""),
                standalone_route.get("target_prover", ""),
            ]
        )
    for candidate in candidates:
        value = str(candidate or "").strip()
        if value:
            return value
    return ""


def _llm_request_residual_keys(request: dict[str, Any]) -> set[str]:
    return {
        _llm_residual_key(residual)
        for residual in _str_tuple(request.get("residual_goals", []))
        if _llm_residual_key(residual)
    }


def _llm_row_residual_keys(row: dict[str, Any]) -> set[str]:
    return {
        _llm_residual_key(residual.get("residual_goal", ""))
        for residual in _dict_tuple(row.get("residual_interpretations", []))
        if _llm_residual_key(residual.get("residual_goal", ""))
    }


def _llm_residual_key(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _llm_row_primitive_evidence_errors(
    row: dict[str, Any],
    request: dict[str, Any],
) -> tuple[str, ...]:
    selected, delta_primitives = _llm_row_selected_and_delta_primitive_keys(row)
    introduced = sorted((selected | delta_primitives) - _llm_available_primitive_keys(request))
    if not introduced:
        return tuple()
    errors: list[str] = []
    informal_by_node_id = {
        str(node.get("node_id", "")): node
        for node in _dict_tuple(row.get("informal_knowledge_dag_nodes", []))
        if str(node.get("node_id", "")).strip()
    }
    formal_by_node_id = {
        str(node.get("node_id", "")): node
        for node in _llm_formal_realization_nodes(row)
        if str(node.get("node_id", "")).strip()
    }
    alignment_edges_by_primitive = _llm_alignment_edges_by_primitive(row)
    search_requests = _dict_tuple(row.get("search_requests", []))
    missing_selected_alignment = sorted(
        primitive
        for primitive in introduced
        if primitive in selected and primitive not in alignment_edges_by_primitive
    )
    if missing_selected_alignment:
        errors.append(
            "introduced selected primitives missing route_alignment_edges: "
            + ",".join(missing_selected_alignment[:8])
        )
    for primitive in introduced:
        edges = alignment_edges_by_primitive.get(primitive, [])
        if not edges:
            errors.append(
                "introduced selected/delta primitive missing route_alignment_edges: "
                + primitive
            )
            continue
        informal_nodes = [
            informal_by_node_id[node_id]
            for node_id in _llm_aligned_node_ids(edges, "informal_node_id", "source")
            if node_id in informal_by_node_id
        ]
        formal_nodes = [
            formal_by_node_id[node_id]
            for node_id in _llm_aligned_node_ids(edges, "formal_node_id", "target")
            if node_id in formal_by_node_id
        ]
        if not any(
            _llm_informal_node_supports_introduced_primitive(
                node,
                primitive=primitive,
                search_requests=search_requests,
            )
            for node in informal_nodes
        ):
            errors.append(
                "introduced primitive requires aligned informal evidence: "
                + primitive
            )
        if not any(
            _llm_formal_node_supports_introduced_primitive(
                node,
                primitive=primitive,
                search_requests=search_requests,
            )
            for node in formal_nodes
        ):
            errors.append(
                "introduced primitive requires aligned formal realization evidence: "
                + primitive
            )
    return tuple(errors)


def _llm_row_route_option_realization_coverage_errors(
    row: dict[str, Any],
) -> tuple[str, ...]:
    route_option_primitives = _llm_row_route_option_primitive_keys(row)
    if not route_option_primitives:
        return tuple()
    standalone = {
        primitive
        for primitive in (
            _llm_primitive_key(item.get("primitive", ""))
            for item in _dict_tuple(_dict_value(row, "standalone_route").get("primitives", []))
        )
        if primitive
    }
    formal = {
        primitive
        for primitive in (
            _llm_primitive_key(node.get("primitive", ""))
            for node in _llm_formal_realization_nodes(row)
        )
        if primitive
    }
    errors: list[str] = []
    missing_route = sorted(route_option_primitives - standalone)
    if missing_route:
        errors.append(
            "row minimal_delta_plan.and_or_cost_graph route option primitives "
            "missing from standalone_route.primitives: "
            + ",".join(missing_route[:8])
        )
    missing_formal = sorted(route_option_primitives - formal)
    if missing_formal:
        errors.append(
            "row minimal_delta_plan.and_or_cost_graph route option primitives "
            "missing from formal_realization_dag_nodes: "
            + ",".join(missing_formal[:8])
        )
    return tuple(errors)


def _llm_row_alignment_reference_errors(row: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    informal_node_ids = {
        str(node.get("node_id", "")).strip()
        for node in _dict_tuple(row.get("informal_knowledge_dag_nodes", []))
        if str(node.get("node_id", "")).strip()
    }
    formal_node_ids = {
        str(node.get("node_id", "")).strip()
        for node in _llm_formal_realization_nodes(row)
        if str(node.get("node_id", "")).strip()
    }
    for index, edge in enumerate(_dict_tuple(row.get("route_alignment_edges", []))):
        informal_node_id = str(
            edge.get("informal_node_id") or edge.get("source") or ""
        ).strip()
        formal_node_id = str(
            edge.get("formal_node_id") or edge.get("target") or ""
        ).strip()
        if not informal_node_id:
            errors.append(f"row route_alignment_edges[{index}].informal_node_id missing")
        elif informal_node_id not in informal_node_ids:
            errors.append(
                "row route_alignment_edges"
                f"[{index}] references unknown informal_node_id: {informal_node_id}"
            )
        if not formal_node_id:
            errors.append(f"row route_alignment_edges[{index}].formal_node_id missing")
        elif formal_node_id not in formal_node_ids:
            errors.append(
                "row route_alignment_edges"
                f"[{index}] references unknown formal_node_id: {formal_node_id}"
            )
    return tuple(errors)


def _llm_available_primitive_keys(request: dict[str, Any]) -> set[str]:
    primitives: list[str] = []
    _llm_collect_primitives(request.get("target_route", {}), primitives)
    _llm_collect_primitives(_dict_value(request, "context_packet"), primitives)
    return {
        primitive
        for primitive in (_llm_primitive_key(value) for value in primitives)
        if primitive
    }


def _llm_row_selected_delta_primitive_keys(row: dict[str, Any]) -> set[str]:
    selected, delta_primitives = _llm_row_selected_and_delta_primitive_keys(row)
    return selected | delta_primitives


def _llm_row_route_option_primitive_keys(row: dict[str, Any]) -> set[str]:
    graph = _dict_value(_dict_value(row, "minimal_delta_plan"), "and_or_cost_graph")
    primitives: set[str] = set()
    for option in _dict_tuple(graph.get("route_options", [])):
        primitives.update(
            primitive
            for primitive in (
                _llm_primitive_key(value)
                for value in _str_tuple(option.get("selected_primitives", []))
            )
            if primitive
        )
    return primitives


def _llm_row_selected_and_delta_primitive_keys(
    row: dict[str, Any],
) -> tuple[set[str], set[str]]:
    minimal_delta = _dict_value(row, "minimal_delta_plan")
    selected = {
        _llm_primitive_key(primitive)
        for primitive in _str_tuple(minimal_delta.get("selected_primitives", []))
        if _llm_primitive_key(primitive)
    }
    explicit: set[str] = set()
    for field_name in (
        "wrapper_lemmas",
        "bridge_lemmas",
        "source_port_lemmas",
        "new_definitions",
        "new_theory_primitives",
        "first_principles_primitives",
    ):
        explicit.update(
            _llm_delta_primitives_from_action_field(
                minimal_delta,
                field_name,
                selected,
            )
        )
    return selected, explicit or set(selected)


def _llm_delta_primitives_from_action_field(
    minimal_delta: dict[str, Any],
    field_name: str,
    selected: set[str],
) -> set[str]:
    explicit: set[str] = set()
    candidate_primitives = _llm_minimal_delta_action_primitives_for_field(
        minimal_delta,
        field_name,
        selected,
    )
    for item in _llm_minimal_delta_action_item_texts(
        minimal_delta.get(field_name, [])
    ):
        item_key = _llm_primitive_key(item)
        if not item_key:
            continue
        prefix_matches = {
            primitive
            for primitive in candidate_primitives
            if item_key == primitive
            or item_key.startswith(f"{primitive}_")
            or item_key.startswith(f"{primitive}:")
        }
        matched = prefix_matches or {
            primitive
            for primitive in candidate_primitives
            if primitive in item_key or item_key in primitive
        }
        if matched:
            explicit.update(matched)
        else:
            explicit.add(item_key)
    return explicit


def _llm_minimal_delta_action_primitives_for_field(
    minimal_delta: dict[str, Any],
    field_name: str,
    selected: set[str],
) -> set[str]:
    candidates: set[str] = set()
    for row in _dict_tuple(minimal_delta.get("primitive_costs", [])):
        primitive = _llm_primitive_key(row.get("primitive", ""))
        if not primitive or primitive not in selected:
            continue
        for action_field in _llm_minimal_delta_action_fields_for_marker(
            row.get("coverage_bucket", "")
        ):
            if field_name in _llm_minimal_delta_action_witness_fields(action_field):
                candidates.add(primitive)
    return candidates or set(selected)


def _llm_minimal_delta_action_fields_for_marker(marker: object) -> tuple[str, ...]:
    key = _llm_primitive_key(marker)
    if key in {"wrapper", "wrapper_needed", "write_wrapper"}:
        return ("wrapper_lemmas",)
    if key in {"bridge", "bridge_needed", "prove_bridge"}:
        return ("bridge_lemmas",)
    if key in {"source_port", "source_port_needed", "port_external_source"}:
        return ("source_port_lemmas",)
    if key in {"define_new", "new_definition", "new_definitions"}:
        return ("new_definitions",)
    if key in {
        "definition_missing",
        "definition_or_theory_missing",
        "new_theory",
        "new_theory_needed",
        "first_principles",
        "design_from_first_principles",
        "missing",
        "theory_missing",
    }:
        return ("new_theory_primitives",)
    return tuple()


def _llm_minimal_delta_action_witness_fields(action_field: str) -> tuple[str, ...]:
    if action_field == "new_theory_primitives":
        return (
            "new_theory_primitives",
            "first_principles_primitives",
            "new_definitions",
        )
    return (action_field,)


def _llm_minimal_delta_action_item_texts(values: object) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values.strip() else tuple()
    if isinstance(values, dict):
        texts = [
            str(values.get(field_name, "") or "").strip()
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
            )
        ]
        return tuple(text for text in texts if text)
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    texts: list[str] = []
    for value in values:
        texts.extend(_llm_minimal_delta_action_item_texts(value))
    return tuple(texts)


def _llm_alignment_edges_by_primitive(
    row: dict[str, Any],
) -> dict[str, list[dict[str, object]]]:
    formal_primitive_by_node_id = {
        str(node.get("node_id", "")): _llm_primitive_key(node.get("primitive", ""))
        for node in _llm_formal_realization_nodes(row)
        if str(node.get("node_id", "")).strip()
    }
    by_primitive: dict[str, list[dict[str, object]]] = {}
    for edge in _dict_tuple(row.get("route_alignment_edges", [])):
        formal_node_id = str(edge.get("formal_node_id") or edge.get("target") or "").strip()
        primitive = _llm_primitive_key(edge.get("primitive", ""))
        if not primitive:
            primitive = formal_primitive_by_node_id.get(formal_node_id, "")
        if primitive:
            by_primitive.setdefault(primitive, []).append(edge)
    return by_primitive


def _llm_aligned_node_ids(
    edges: list[dict[str, object]],
    primary_field: str,
    fallback_field: str,
) -> tuple[str, ...]:
    return _str_tuple(
        [
            str(edge.get(primary_field) or edge.get(fallback_field) or "").strip()
            for edge in edges
        ]
    )


def _llm_informal_node_supports_introduced_primitive(
    node: dict[str, object],
    *,
    primitive: str,
    search_requests: tuple[dict[str, object], ...],
) -> bool:
    if _str_tuple(node.get("source_refs", [])):
        return True
    if _llm_formal_gap_boundary_is_substantive(node.get("formal_gap_boundary", "")):
        return True
    status = _llm_source_ref_key(node.get("source_search_status", ""))
    if status in {"formal_gap_boundary", "formal_boundary_declared"}:
        return True
    if status in {
        "search_requested",
        "source_search_requested",
        "source_search_pending",
        "literature_search_requested",
        "literature_search_pending",
    }:
        return _llm_has_search_request_for_primitive(
            search_requests,
            primitive=primitive,
            request_kind_keys=("literature", "source", "paper", "textbook"),
        )
    return False


def _llm_formal_node_supports_introduced_primitive(
    node: dict[str, object],
    *,
    primitive: str,
    search_requests: tuple[dict[str, object], ...],
) -> bool:
    if _llm_primitive_key(node.get("primitive", "")) != primitive:
        return False
    if _llm_formal_node_claims_existing_library(node):
        return bool(_str_tuple(node.get("candidate_declarations", [])))
    if _llm_formal_gap_boundary_is_substantive(node.get("formal_gap_boundary", "")):
        return True
    markers = (
        node.get("coverage_bucket", ""),
        node.get("coverage_status", ""),
        node.get("formalization_action", ""),
        node.get("alignment_status", ""),
    )
    if any(_llm_delta_formalization_marker(marker) for marker in markers):
        return True
    return _llm_has_search_request_for_primitive(
        search_requests,
        primitive=primitive,
        request_kind_keys=("formal_library", "library", "prover_feedback"),
    )


def _llm_formal_node_claims_existing_library(node: dict[str, object]) -> bool:
    markers = (
        node.get("coverage_bucket", ""),
        node.get("coverage_status", ""),
        node.get("formalization_action", ""),
        node.get("alignment_status", ""),
    )
    return any(_llm_existing_library_marker(marker) for marker in markers)


def _llm_existing_library_marker(value: object) -> bool:
    return _llm_primitive_key(value) in {
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


def _llm_delta_formalization_marker(value: object) -> bool:
    return _llm_primitive_key(value) in {
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


def _llm_has_search_request_for_primitive(
    search_requests: tuple[dict[str, object], ...],
    *,
    primitive: str,
    request_kind_keys: tuple[str, ...],
) -> bool:
    primitive_key = _llm_primitive_key(primitive)
    if not primitive_key:
        return False
    for request in search_requests:
        kind_key = _llm_primitive_key(request.get("request_kind", ""))
        if request_kind_keys and not any(key in kind_key for key in request_kind_keys):
            continue
        text_key = _llm_primitive_key(
            " ".join(
                str(request.get(field_name, ""))
                for field_name in ("query", "reason", "action", "description")
            )
        )
        if primitive_key in text_key:
            return True
    return False


def _llm_collect_primitives(value: Any, primitives: list[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            if key_text == "coverage_updates" and isinstance(item, dict):
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
                primitives.extend(_llm_primitive_values(item))
            _llm_collect_primitives(item, primitives)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _llm_collect_primitives(item, primitives)


def _llm_primitive_values(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value.strip() else tuple()
    if isinstance(value, dict):
        values: list[str] = []
        for key in ("primitive", "name", "id"):
            if key in value:
                values.extend(_llm_primitive_values(value.get(key)))
        return _str_tuple(values)
    if isinstance(value, (list, tuple, set)):
        values: list[str] = []
        for item in value:
            values.extend(_llm_primitive_values(item))
        return _str_tuple(values)
    return tuple()


def _llm_primitive_key(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def _llm_duplicate_primitive_keys(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        raw_values = (values,)
    elif isinstance(values, (list, tuple)):
        raw_values = values
    else:
        return tuple()
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in raw_values:
        primitive = _llm_primitive_key(value)
        if not primitive:
            continue
        if primitive in seen and primitive not in duplicates:
            duplicates.append(primitive)
        seen.add(primitive)
    return tuple(duplicates)


def _llm_duplicate_string_keys(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        raw_values = (values,)
    elif isinstance(values, (list, tuple)):
        raw_values = values
    else:
        return tuple()
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in raw_values:
        key = str(value or "").strip()
        if not key:
            continue
        if key in seen and key not in duplicates:
            duplicates.append(key)
        seen.add(key)
    return tuple(duplicates)


def _llm_seed_route_for_row(
    seed: dict[str, Any],
    row: dict[str, Any],
) -> dict[str, Any]:
    row_id = str(row.get("llm_route_planner_row_id", ""))
    for route in _seed_route_index(seed).values():
        metadata = route.get("replan_metadata", {})
        metadata = metadata if isinstance(metadata, dict) else {}
        if str(route.get("llm_route_planner_row_id", "")) == row_id:
            return route
        if str(metadata.get("llm_route_planner_row_id", "")) == row_id:
            return route
    standalone_route = row.get("standalone_route", {})
    if isinstance(standalone_route, dict):
        route_id = str(standalone_route.get("route_id", ""))
        route = _seed_route_index(seed).get(route_id, {})
        if route:
            return route
    return _seed_route_index(seed).get(str(row.get("route_id", "")), {})


def _llm_seed_provenance_errors(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    metadata = _seed_route_metadata(seed_route)
    if not seed_route:
        errors.append("seed route missing")
    if not isinstance(metadata, dict):
        errors.append("seed route replan_metadata missing")
        return tuple(errors)
    row_id = str(row.get("llm_route_planner_row_id", ""))
    if str(seed_route.get("llm_route_planner_row_id", "")) != row_id:
        errors.append("seed route llm_route_planner_row_id mismatch")
    if str(metadata.get("llm_route_planner_row_id", "")) != row_id:
        errors.append("seed metadata llm_route_planner_row_id mismatch")
    expected_fields = (
        ("request_id", "llm_route_planner_request_id"),
        ("provider_name", "llm_route_planner_provider"),
        ("model", "llm_route_planner_model"),
        ("acceptance_status", "llm_route_planner_acceptance_status"),
    )
    for row_field, metadata_field in expected_fields:
        if str(metadata.get(metadata_field, "")) != str(row.get(row_field, "")):
            errors.append(f"seed metadata {metadata_field} mismatch")
    if str(seed_route.get("llm_route_planner_acceptance_status", "")) != str(
        row.get("acceptance_status", "")
    ):
        errors.append("seed route llm_route_planner_acceptance_status mismatch")
    if "llm_route_planner" not in _str_tuple(metadata.get("applied_hook_kinds", [])):
        errors.append("seed metadata applied_hook_kinds missing llm_route_planner")
    if row_id not in _str_tuple(metadata.get("applied_proposal_ids", [])):
        errors.append("seed metadata applied_proposal_ids missing LLM row id")
    if _object_hashes([row.get("minimal_delta_plan", {})]) != _object_hashes(
        [metadata.get("llm_route_planner_minimal_delta_plan", {})]
    ):
        errors.append("seed metadata minimal delta plan mismatch")
    row_cost_graph = _dict_value(_dict_value(row, "minimal_delta_plan"), "and_or_cost_graph")
    if not row_cost_graph:
        errors.append("accepted LLM row minimal_delta_plan.and_or_cost_graph missing")
    if _object_hashes([row_cost_graph]) != _object_hashes(
        [seed_route.get("minimal_delta_and_or_cost_graph", {})]
    ):
        errors.append("seed route minimal_delta_and_or_cost_graph mismatch")
    if _object_hashes([row_cost_graph]) != _object_hashes(
        [metadata.get("minimal_delta_and_or_cost_graph", {})]
    ):
        errors.append("seed metadata minimal_delta_and_or_cost_graph mismatch")
    if not str(
        _dict_value(row, "minimal_delta_plan").get("minimality_rationale", "")
    ).strip():
        errors.append("accepted LLM row minimality_rationale missing")
    row_sources = set(_str_tuple(row.get("source_refs", [])))
    route_sources = set(_str_tuple(seed_route.get("source_refs", [])))
    metadata_sources = set(_str_tuple(metadata.get("source_refs", [])))
    if not row_sources.issubset(route_sources):
        errors.append("seed route source_refs do not include LLM row source_refs")
    if not row_sources.issubset(metadata_sources):
        errors.append("seed metadata source_refs do not include LLM row source_refs")
    if str(metadata.get("proof_evidence_boundary", "")).lower().find(
        "not theorem proof evidence"
    ) < 0:
        errors.append("seed metadata proof_evidence_boundary missing")
    return tuple(errors)


def _llm_seed_provenance_observed(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> str:
    metadata = _seed_route_metadata(seed_route)
    metadata = metadata if isinstance(metadata, dict) else {}
    row_sources = set(_str_tuple(row.get("source_refs", [])))
    route_sources = set(_str_tuple(seed_route.get("source_refs", [])))
    metadata_sources = set(_str_tuple(metadata.get("source_refs", [])))
    return (
        f"matched_seed_route={bool(seed_route)}; "
        f"row_id={row.get('llm_route_planner_row_id', '')}; "
        f"metadata_row_id={metadata.get('llm_route_planner_row_id', '')}; "
        f"source_refs_route={len(row_sources.intersection(route_sources))}/{len(row_sources)}; "
        f"source_refs_metadata={len(row_sources.intersection(metadata_sources))}/{len(row_sources)}; "
        f"has_cost_graph={bool(_dict_value(_dict_value(row, 'minimal_delta_plan'), 'and_or_cost_graph'))}"
    )


def _llm_seed_search_handoff_errors(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> tuple[str, ...]:
    search_requests = _dict_tuple(row.get("search_requests", []))
    if not search_requests:
        return tuple()
    errors: list[str] = []
    metadata = _seed_route_metadata(seed_route)
    if not seed_route:
        errors.append("seed route missing")
    if not isinstance(metadata, dict):
        errors.append("seed route replan_metadata missing")
        return tuple(errors)
    expected_request_hashes = _object_hashes(search_requests)
    metadata_request_hashes = _object_hashes(
        metadata.get("llm_route_planner_search_requests", [])
    )
    if expected_request_hashes != metadata_request_hashes:
        errors.append("seed metadata llm_route_planner_search_requests mismatch")
    route_hook_hashes = _llm_embedded_search_request_hashes(
        seed_route.get("interactive_refinement_hooks", [])
    )
    metadata_hook_hashes = _llm_embedded_search_request_hashes(
        metadata.get("llm_route_planner_interactive_refinement_hooks", [])
    )
    if not expected_request_hashes.issubset(route_hook_hashes):
        errors.append("seed route interactive_refinement_hooks missing LLM search requests")
    if not expected_request_hashes.issubset(metadata_hook_hashes):
        errors.append(
            "seed metadata llm_route_planner_interactive_refinement_hooks missing LLM search requests"
        )
    route_trigger_hashes = _llm_embedded_search_request_hashes(
        seed_route.get("route_revision_triggers", [])
    )
    metadata_trigger_hashes = _llm_embedded_search_request_hashes(
        metadata.get("llm_route_planner_route_revision_triggers", [])
    )
    if not expected_request_hashes.issubset(route_trigger_hashes):
        errors.append("seed route route_revision_triggers missing LLM search requests")
    if not expected_request_hashes.issubset(metadata_trigger_hashes):
        errors.append(
            "seed metadata llm_route_planner_route_revision_triggers missing LLM search requests"
        )
    return tuple(errors)


def _llm_seed_search_handoff_observed(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> str:
    metadata = _seed_route_metadata(seed_route)
    metadata = metadata if isinstance(metadata, dict) else {}
    expected = _object_hashes(row.get("search_requests", []))
    route_hook_hashes = _llm_embedded_search_request_hashes(
        seed_route.get("interactive_refinement_hooks", [])
    )
    metadata_hook_hashes = _llm_embedded_search_request_hashes(
        metadata.get("llm_route_planner_interactive_refinement_hooks", [])
    )
    route_trigger_hashes = _llm_embedded_search_request_hashes(
        seed_route.get("route_revision_triggers", [])
    )
    metadata_trigger_hashes = _llm_embedded_search_request_hashes(
        metadata.get("llm_route_planner_route_revision_triggers", [])
    )
    metadata_request_hashes = _object_hashes(
        metadata.get("llm_route_planner_search_requests", [])
    )
    return (
        f"search_requests={len(expected)}; "
        f"metadata_requests={len(expected.intersection(metadata_request_hashes))}/{len(expected)}; "
        f"route_hooks={len(expected.intersection(route_hook_hashes))}/{len(expected)}; "
        f"metadata_hooks={len(expected.intersection(metadata_hook_hashes))}/{len(expected)}; "
        f"route_triggers={len(expected.intersection(route_trigger_hashes))}/{len(expected)}; "
        f"metadata_triggers={len(expected.intersection(metadata_trigger_hashes))}/{len(expected)}"
    )


def _llm_embedded_search_request_hashes(values: Any) -> set[str]:
    hashes: set[str] = set()
    for row in _dict_tuple(values):
        request = row.get("llm_route_planner_search_request", {})
        if isinstance(request, dict):
            hashes.add(stable_hash(request))
    return hashes


def _llm_seed_route_adoption_readiness_errors(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    metadata = _seed_route_metadata(seed_route)
    if not seed_route:
        errors.append("seed route missing")
    if not isinstance(metadata, dict):
        errors.append("seed route replan_metadata missing")
        return tuple(errors)
    row_status = str(row.get("route_adoption_status", "")).strip()
    if not row_status:
        errors.append("accepted LLM row route_adoption_status missing")
    route_status = str(
        seed_route.get("llm_route_planner_route_adoption_status", "")
    ).strip()
    metadata_status = str(
        metadata.get("llm_route_planner_route_adoption_status", "")
    ).strip()
    valid_statuses = {
        ROUTE_ADOPTION_READY_STATUS,
        ROUTE_ADOPTION_PENDING_STATUS,
        ROUTE_ADOPTION_AWAITING_STATUS,
        ROUTE_ADOPTION_REJECTED_STATUS,
    }
    for label, status in (
        ("row", row_status),
        ("seed route", route_status),
        ("seed metadata", metadata_status),
    ):
        if status and status not in valid_statuses:
            errors.append(f"{label} unknown llm_route_planner_route_adoption_status")
    if row_status != route_status:
        errors.append("seed route llm_route_planner_route_adoption_status mismatch")
    if row_status != metadata_status:
        errors.append(
            "seed metadata llm_route_planner_route_adoption_status mismatch"
        )
    row_blockers = _str_tuple(row.get("route_adoption_blockers", []))
    route_blockers = _str_tuple(
        seed_route.get("llm_route_planner_route_adoption_blockers", [])
    )
    metadata_blockers = _str_tuple(
        metadata.get("llm_route_planner_route_adoption_blockers", [])
    )
    valid_blockers = set(ROUTE_ADOPTION_BLOCKER_VALUES)
    for label, blockers in (
        ("row", row_blockers),
        ("seed route", route_blockers),
        ("seed metadata", metadata_blockers),
    ):
        unknown_blockers = sorted(set(blockers) - valid_blockers)
        if unknown_blockers:
            errors.append(
                f"{label} unknown llm_route_planner_route_adoption_blockers: "
                + ", ".join(unknown_blockers)
            )
    if row_blockers != route_blockers:
        errors.append("seed route llm_route_planner_route_adoption_blockers mismatch")
    if row_blockers != metadata_blockers:
        errors.append(
            "seed metadata llm_route_planner_route_adoption_blockers mismatch"
        )
    return tuple(errors)


def _llm_seed_route_adoption_readiness_observed(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> str:
    metadata = _seed_route_metadata(seed_route)
    metadata = metadata if isinstance(metadata, dict) else {}
    row_blockers = _str_tuple(row.get("route_adoption_blockers", []))
    route_blockers = _str_tuple(
        seed_route.get("llm_route_planner_route_adoption_blockers", [])
    )
    metadata_blockers = _str_tuple(
        metadata.get("llm_route_planner_route_adoption_blockers", [])
    )
    return (
        f"row_status={row.get('route_adoption_status', '')}; "
        f"route_status={seed_route.get('llm_route_planner_route_adoption_status', '')}; "
        f"metadata_status={metadata.get('llm_route_planner_route_adoption_status', '')}; "
        f"route_blockers={len(set(row_blockers).intersection(route_blockers))}/{len(row_blockers)}; "
        f"metadata_blockers={len(set(row_blockers).intersection(metadata_blockers))}/{len(row_blockers)}"
    )


def _llm_seed_route_selection_summary_errors(
    seed_payload: dict[str, Any],
    rows: list[dict[str, Any]],
) -> tuple[str, ...]:
    seed_routes = _seed_route_index(seed_payload)
    accepted_rows = [row for row in rows if _llm_route_planner_row_accepted(row)]
    selection = _dict_value(seed_payload, "llm_route_planner_seed_route_selection")
    selection_rows = _dict_tuple(selection.get("selection_rows", []))
    if not seed_routes and not selection:
        return tuple()
    errors: list[str] = []
    if not selection:
        errors.append("seed llm_route_planner_seed_route_selection missing")
        return tuple(errors)
    if (
        str(selection.get("selection_kind", ""))
        != "formalization_gap_planner_llm_route_planner_seed_route_selection"
    ):
        errors.append("seed route-selection summary kind mismatch")
    route_candidate_count = _int_or_none(selection.get("n_route_candidates"))
    if route_candidate_count != len(selection_rows):
        errors.append("seed route-selection candidate count mismatch")
    selected_rows = [row for row in selection_rows if bool(row.get("selected", False))]
    if selection_rows and len(selected_rows) != 1:
        errors.append(
            f"seed route-selection summary must select exactly one route, found {len(selected_rows)}"
        )
    adoptable_count = _int_or_none(selection.get("n_adoptable_route_candidates"))
    computed_adoptable_count = sum(
        1
        for row in selection_rows
        if bool(row.get("adoptable_for_standalone_replay", False))
    )
    if adoptable_count != computed_adoptable_count:
        errors.append("seed route-selection adoptable candidate count mismatch")
    selected_not_adoptable_count = _int_or_none(
        selection.get("n_selected_route_candidates_not_adoptable")
    )
    computed_selected_not_adoptable_count = sum(
        1
        for row in selection_rows
        if bool(row.get("selected", False))
        and not bool(row.get("adoptable_for_standalone_replay", False))
    )
    if selected_not_adoptable_count != computed_selected_not_adoptable_count:
        errors.append(
            "seed route-selection selected-not-adoptable count mismatch"
        )
    ranks = [_int_or_none(row.get("selection_rank")) for row in selection_rows]
    if any(rank is None for rank in ranks) or sorted(
        rank for rank in ranks if rank is not None
    ) != list(range(1, len(selection_rows) + 1)):
        errors.append("seed route-selection ranks are not consecutive from 1")
    contract_valid_count = _int_or_none(
        selection.get("n_contract_valid_route_candidates")
    )
    if accepted_rows and contract_valid_count != len(accepted_rows):
        errors.append("seed route-selection contract-valid candidate count mismatch")
    for selection_row in selection_rows:
        seed_route_id = str(
            selection_row.get("seed_route_id", "")
            or selection_row.get("route_id", "")
        )
        seed_route = seed_routes.get(seed_route_id, {})
        if not seed_route:
            errors.append(f"selection row seed route missing: {seed_route_id}")
            continue
        metadata = _seed_route_metadata(seed_route)
        metadata = metadata if isinstance(metadata, dict) else {}
        selected = bool(selection_row.get("selected", False))
        rank = int(selection_row.get("selection_rank", 0) or 0)
        if bool(seed_route.get("llm_route_planner_seed_selected", False)) != selected:
            errors.append(f"seed route {seed_route_id} selected flag mismatch")
        if bool(metadata.get("llm_route_planner_seed_selected", False)) != selected:
            errors.append(f"seed metadata {seed_route_id} selected flag mismatch")
        if int(seed_route.get("llm_route_planner_seed_selection_rank", 0) or 0) != rank:
            errors.append(f"seed route {seed_route_id} selection rank mismatch")
        if int(metadata.get("llm_route_planner_seed_selection_rank", 0) or 0) != rank:
            errors.append(f"seed metadata {seed_route_id} selection rank mismatch")
    if selected_rows:
        selected = selected_rows[0]
        if str(selection.get("selected_route_id", "")) != str(selected.get("route_id", "")):
            errors.append("seed route-selection selected_route_id mismatch")
        if str(selection.get("selected_seed_route_id", "")) != str(
            selected.get("seed_route_id", "")
        ):
            errors.append("seed route-selection selected_seed_route_id mismatch")
        if str(selection.get("selected_llm_route_planner_row_id", "")) != str(
            selected.get("llm_route_planner_row_id", "")
        ):
            errors.append("seed route-selection selected row id mismatch")
        if int(selected.get("selection_rank", 0) or 0) != 1:
            errors.append("seed route-selection selected row must have rank 1")
        if bool(selection.get("selected_route_adoptable_for_standalone_replay", False)) != bool(
            selected.get("adoptable_for_standalone_replay", False)
        ):
            errors.append(
                "seed route-selection selected adoptability summary mismatch"
            )
    return tuple(errors)


def _llm_seed_route_selection_summary_observed(
    seed_payload: dict[str, Any],
    rows: list[dict[str, Any]],
) -> str:
    selection = _dict_value(seed_payload, "llm_route_planner_seed_route_selection")
    counts = _llm_seed_route_selection_counts(seed_payload)
    selection_rows = _dict_tuple(selection.get("selection_rows", []))
    selected_rows = [row for row in selection_rows if bool(row.get("selected", False))]
    accepted_rows = [row for row in rows if _llm_route_planner_row_accepted(row)]
    return (
        f"status={selection.get('selection_status', '')}; "
        f"candidates={len(selection_rows)}/{selection.get('n_route_candidates', 0)}; "
        f"selected={len(selected_rows)}; "
        f"adoptable={counts['n_adoptable_route_candidates']}; "
        f"selected_adoptable={counts['n_selected_route_adoptable_for_standalone_replay']}; "
        f"selected_not_adoptable={counts['n_selected_route_candidates_not_adoptable']}; "
        f"selected_seed_route_id={selection.get('selected_seed_route_id', '')}; "
        f"accepted_rows={len(accepted_rows)}; "
        f"contract_valid={selection.get('n_contract_valid_route_candidates', 0)}"
    )


def _optional_llm_seed_route_selection_counts(
    bundle_dir: Path,
    *,
    artifact_name: str,
) -> dict[str, int]:
    seed_path = (
        bundle_dir
        / "artifacts"
        / artifact_name
        / "formalization_gap_planner_llm_route_planner_standalone_seed.json"
    )
    return _llm_seed_route_selection_counts(_read_json_no_error(seed_path))


def _llm_seed_route_selection_counts(seed_payload: dict[str, Any]) -> dict[str, int]:
    selection = _dict_value(seed_payload, "llm_route_planner_seed_route_selection")
    selection_rows = _dict_tuple(selection.get("selection_rows", []))
    selected_rows = [row for row in selection_rows if bool(row.get("selected", False))]
    computed_adoptable = sum(
        1
        for row in selection_rows
        if bool(row.get("adoptable_for_standalone_replay", False))
    )
    computed_selected_not_adoptable = sum(
        1
        for row in selection_rows
        if bool(row.get("selected", False))
        and not bool(row.get("adoptable_for_standalone_replay", False))
    )
    selected_adoptable = sum(
        1
        for row in selected_rows
        if bool(row.get("adoptable_for_standalone_replay", False))
    )
    route_candidates = _int_or_none(selection.get("n_route_candidates"))
    adoptable_candidates = _int_or_none(
        selection.get("n_adoptable_route_candidates")
    )
    selected_not_adoptable = _int_or_none(
        selection.get("n_selected_route_candidates_not_adoptable")
    )
    return {
        "n_route_candidates": int(route_candidates or len(selection_rows)),
        "n_adoptable_route_candidates": int(
            adoptable_candidates
            if adoptable_candidates is not None
            else computed_adoptable
        ),
        "n_selected_route_adoptable_for_standalone_replay": int(
            bool(selection.get("selected_route_adoptable_for_standalone_replay", False))
            if selection
            else bool(selected_adoptable)
        ),
        "n_selected_route_candidates_not_adoptable": int(
            selected_not_adoptable
            if selected_not_adoptable is not None
            else computed_selected_not_adoptable
        ),
    }


def _llm_seed_route_selection_errors(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    metadata = _seed_route_metadata(seed_route)
    if not seed_route:
        errors.append("seed route missing")
    if not isinstance(metadata, dict):
        errors.append("seed route replan_metadata missing")
        return tuple(errors)
    route_rank = _int_or_none(seed_route.get("llm_route_planner_seed_selection_rank"))
    metadata_rank = _int_or_none(
        metadata.get("llm_route_planner_seed_selection_rank")
    )
    if route_rank is None or route_rank <= 0:
        errors.append("seed route llm_route_planner_seed_selection_rank missing")
    if metadata_rank is None or metadata_rank <= 0:
        errors.append("seed metadata llm_route_planner_seed_selection_rank missing")
    if route_rank != metadata_rank:
        errors.append("seed route and metadata selection rank mismatch")
    route_selected = bool(seed_route.get("llm_route_planner_seed_selected", False))
    metadata_selected = bool(
        metadata.get("llm_route_planner_seed_selected", False)
    )
    if route_selected != metadata_selected:
        errors.append("seed route and metadata selected flag mismatch")
    if route_selected and route_rank != 1:
        errors.append("selected seed route must have selection rank 1")
    row_adoptable = (
        bool(row.get("response_contract_ok", False))
        and str(row.get("route_adoption_status", ""))
        == "READY_FOR_STANDALONE_REPLAY"
        and not _str_tuple(row.get("route_adoption_blockers", []))
    )
    route_adoptable = bool(
        seed_route.get("llm_route_planner_seed_adoptable_for_standalone_replay", False)
    )
    metadata_adoptable = bool(
        metadata.get(
            "llm_route_planner_seed_adoptable_for_standalone_replay",
            False,
        )
    )
    if route_adoptable != row_adoptable:
        errors.append("seed route adoptability flag mismatch")
    if metadata_adoptable != row_adoptable:
        errors.append("seed metadata adoptability flag mismatch")
    if route_adoptable != metadata_adoptable:
        errors.append("seed route and metadata adoptability flag mismatch")
    if not str(seed_route.get("llm_route_planner_seed_selection_reason", "")).strip():
        errors.append("seed route selection reason missing")
    if not str(
        metadata.get("llm_route_planner_seed_selection_reason", "")
    ).strip():
        errors.append("seed metadata selection reason missing")
    row_cost = _float_or_none(_dict_value(row, "minimal_delta_plan").get("route_cost"))
    route_cost = _float_or_none(
        seed_route.get("llm_route_planner_seed_minimal_delta_route_cost")
    )
    metadata_cost = _float_or_none(
        metadata.get("llm_route_planner_seed_minimal_delta_route_cost")
    )
    if row_cost is not None and route_cost != row_cost:
        errors.append("seed route minimal-delta selection cost mismatch")
    if row_cost is not None and metadata_cost != row_cost:
        errors.append("seed metadata minimal-delta selection cost mismatch")
    if route_cost != metadata_cost:
        errors.append("seed route and metadata minimal-delta selection cost mismatch")
    return tuple(errors)


def _llm_seed_route_selection_observed(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> str:
    metadata = _seed_route_metadata(seed_route)
    metadata = metadata if isinstance(metadata, dict) else {}
    row_cost = _float_or_none(_dict_value(row, "minimal_delta_plan").get("route_cost"))
    return (
        f"row_id={row.get('llm_route_planner_row_id', '')}; "
        f"seed_selected={seed_route.get('llm_route_planner_seed_selected', '')}; "
        f"metadata_selected={metadata.get('llm_route_planner_seed_selected', '')}; "
        f"seed_adoptable={seed_route.get('llm_route_planner_seed_adoptable_for_standalone_replay', '')}; "
        f"metadata_adoptable={metadata.get('llm_route_planner_seed_adoptable_for_standalone_replay', '')}; "
        f"seed_rank={seed_route.get('llm_route_planner_seed_selection_rank', '')}; "
        f"metadata_rank={metadata.get('llm_route_planner_seed_selection_rank', '')}; "
        f"row_cost={row_cost}; "
        f"seed_cost={seed_route.get('llm_route_planner_seed_minimal_delta_route_cost', '')}; "
        f"metadata_cost={metadata.get('llm_route_planner_seed_minimal_delta_route_cost', '')}"
    )


def _llm_seed_model_provenance_errors(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    metadata = _seed_route_metadata(seed_route)
    if not seed_route:
        errors.append("seed route missing")
    if not isinstance(metadata, dict):
        errors.append("seed route replan_metadata missing")
        return tuple(errors)
    expected_fields = (
        ("model_tier", "llm_route_planner_model_tier"),
        ("model_selection_rationale", "llm_route_planner_model_selection_rationale"),
    )
    for row_field, metadata_field in expected_fields:
        if str(metadata.get(metadata_field, "")) != str(row.get(row_field, "")):
            errors.append(f"seed metadata {metadata_field} mismatch")
    row_generator_metadata = _dict_value(row, "generator_metadata")
    seed_generator_metadata = metadata.get("llm_route_planner_generator_metadata", {})
    if not isinstance(seed_generator_metadata, dict):
        errors.append("seed metadata llm_route_planner_generator_metadata is not an object")
        seed_generator_metadata = {}
    if _object_hashes([row_generator_metadata]) != _object_hashes(
        [seed_generator_metadata]
    ):
        errors.append("seed metadata llm_route_planner_generator_metadata mismatch")
    row_generator_keys = sorted(str(key) for key in row_generator_metadata)
    seed_generator_keys = sorted(
        _str_tuple(metadata.get("llm_route_planner_generator_metadata_keys", []))
    )
    if row_generator_keys != seed_generator_keys:
        errors.append("seed metadata llm_route_planner_generator_metadata_keys mismatch")
    return tuple(errors)


def _llm_seed_model_provenance_observed(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> str:
    metadata = _seed_route_metadata(seed_route)
    metadata = metadata if isinstance(metadata, dict) else {}
    row_generator_metadata = _dict_value(row, "generator_metadata")
    seed_generator_metadata = metadata.get("llm_route_planner_generator_metadata", {})
    seed_generator_metadata = (
        seed_generator_metadata if isinstance(seed_generator_metadata, dict) else {}
    )
    row_keys = sorted(str(key) for key in row_generator_metadata)
    seed_keys = sorted(
        _str_tuple(metadata.get("llm_route_planner_generator_metadata_keys", []))
    )
    return (
        f"row_model_tier={row.get('model_tier', '')}; "
        f"seed_model_tier={metadata.get('llm_route_planner_model_tier', '')}; "
        f"generator_metadata_keys={len(set(row_keys).intersection(seed_keys))}/{len(row_keys)}; "
        f"generator_metadata_preserved={_object_hashes([row_generator_metadata]) == _object_hashes([seed_generator_metadata])}"
    )


def _llm_seed_source_grounding_provenance_errors(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    metadata = _seed_route_metadata(seed_route)
    if not seed_route:
        errors.append("seed route missing")
    if not isinstance(metadata, dict):
        errors.append("seed route replan_metadata missing")
        return tuple(errors)
    row_rows = _dict_tuple(row.get("source_grounding_rows", []))
    route_rows = _dict_tuple(
        seed_route.get("llm_route_planner_source_grounding_rows", [])
    )
    metadata_rows = _dict_tuple(
        metadata.get("llm_route_planner_source_grounding_rows", [])
    )
    row_row_hashes = _object_hashes(row_rows)
    if row_row_hashes != _object_hashes(route_rows):
        errors.append("seed route llm_route_planner_source_grounding_rows mismatch")
    if row_row_hashes != _object_hashes(metadata_rows):
        errors.append("seed metadata llm_route_planner_source_grounding_rows mismatch")
    row_obligations = _as_dict(row.get("source_grounding_obligations", {}))
    route_obligations = _as_dict(
        seed_route.get("llm_route_planner_source_grounding_obligations", {})
    )
    metadata_obligations = _as_dict(
        metadata.get("llm_route_planner_source_grounding_obligations", {})
    )
    if row_obligations != route_obligations:
        errors.append(
            "seed route llm_route_planner_source_grounding_obligations mismatch"
        )
    if row_obligations != metadata_obligations:
        errors.append(
            "seed metadata llm_route_planner_source_grounding_obligations mismatch"
        )
    return tuple(errors)


def _llm_seed_source_grounding_provenance_observed(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> str:
    metadata = _seed_route_metadata(seed_route)
    metadata = metadata if isinstance(metadata, dict) else {}
    row_rows = _dict_tuple(row.get("source_grounding_rows", []))
    route_rows = _dict_tuple(
        seed_route.get("llm_route_planner_source_grounding_rows", [])
    )
    metadata_rows = _dict_tuple(
        metadata.get("llm_route_planner_source_grounding_rows", [])
    )
    row_row_hashes = _object_hashes(row_rows)
    route_row_hashes = _object_hashes(route_rows)
    metadata_row_hashes = _object_hashes(metadata_rows)
    row_obligations = _as_dict(row.get("source_grounding_obligations", {}))
    route_obligations = _as_dict(
        seed_route.get("llm_route_planner_source_grounding_obligations", {})
    )
    metadata_obligations = _as_dict(
        metadata.get("llm_route_planner_source_grounding_obligations", {})
    )
    return (
        f"row_rows={len(row_rows)}; "
        f"seed_route_rows={len(row_row_hashes.intersection(route_row_hashes))}/{len(row_row_hashes)}; "
        f"metadata_rows={len(row_row_hashes.intersection(metadata_row_hashes))}/{len(row_row_hashes)}; "
        f"row_pending={bool(row_obligations.get('pending', False))}; "
        f"route_obligations_preserved={row_obligations == route_obligations}; "
        f"metadata_obligations_preserved={row_obligations == metadata_obligations}"
    )


def _llm_seed_realization_witness_errors(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    metadata = _seed_route_metadata(seed_route)
    if not seed_route:
        errors.append("seed route missing")
    if not isinstance(metadata, dict):
        errors.append("seed route replan_metadata missing")
        return tuple(errors)
    row_witness = _dict_value(row, "realization_coverage_witness")
    route_witness = _dict_value(seed_route, "realization_coverage_witness")
    metadata_witness = _dict_value(
        metadata,
        "llm_route_planner_realization_coverage_witness",
    )
    if not row_witness:
        errors.append("accepted LLM row realization_coverage_witness missing")
    if not route_witness:
        errors.append("seed route realization_coverage_witness missing")
    if not metadata_witness:
        errors.append("seed metadata llm_route_planner_realization_coverage_witness missing")
    if row_witness and bool(row_witness.get("realization_coverage_complete", False)) is not True:
        errors.append("accepted LLM row realization_coverage_complete is not true")
    if route_witness and bool(route_witness.get("realization_coverage_complete", False)) is not True:
        errors.append("seed route realization_coverage_complete is not true")
    if metadata_witness and bool(metadata_witness.get("realization_coverage_complete", False)) is not True:
        errors.append("seed metadata realization_coverage_complete is not true")
    if row_witness and route_witness and _object_hashes([row_witness]) != _object_hashes(
        [route_witness]
    ):
        errors.append("seed route realization_coverage_witness mismatch")
    if row_witness and metadata_witness and _object_hashes([row_witness]) != _object_hashes(
        [metadata_witness]
    ):
        errors.append("seed metadata realization_coverage_witness mismatch")
    return tuple(errors)


def _llm_seed_realization_witness_observed(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> str:
    metadata = _seed_route_metadata(seed_route)
    metadata = metadata if isinstance(metadata, dict) else {}
    row_witness = _dict_value(row, "realization_coverage_witness")
    route_witness = _dict_value(seed_route, "realization_coverage_witness")
    metadata_witness = _dict_value(
        metadata,
        "llm_route_planner_realization_coverage_witness",
    )
    return (
        f"row_complete={bool(row_witness.get('realization_coverage_complete', False))}; "
        f"seed_route_complete={bool(route_witness.get('realization_coverage_complete', False))}; "
        f"metadata_complete={bool(metadata_witness.get('realization_coverage_complete', False))}; "
        f"row_hash={','.join(_object_hashes([row_witness]))}; "
        f"seed_route_hash={','.join(_object_hashes([route_witness]))}; "
        f"metadata_hash={','.join(_object_hashes([metadata_witness]))}"
    )


def _llm_seed_alignment_errors(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    metadata = _seed_route_metadata(seed_route)
    if not seed_route:
        errors.append("seed route missing")
    if not isinstance(metadata, dict):
        errors.append("seed route replan_metadata missing")
        return tuple(errors)
    row_triples = _llm_row_alignment_triples(row)
    route_triples = _llm_seed_alignment_triples(
        seed_route.get("revised_route_alignment_edges", [])
    )
    metadata_triples = _llm_seed_alignment_triples(
        metadata.get("revised_route_alignment_edges", [])
    )
    if not row_triples:
        errors.append("accepted LLM row route_alignment_edges empty")
    if row_triples != route_triples:
        errors.append("seed route revised_route_alignment_edges mismatch")
    if row_triples != metadata_triples:
        errors.append("seed metadata revised_route_alignment_edges mismatch")
    if _object_hashes(seed_route.get("revised_route_alignment_edges", [])) != _object_hashes(
        metadata.get("revised_route_alignment_edges", [])
    ):
        errors.append("seed route and metadata revised_route_alignment_edges differ")
    delta_primitives = _llm_delta_primitives(row)
    aligned_primitives = _alignment_primitives(
        seed_route.get("revised_route_alignment_edges", [])
    )
    missing_delta = sorted(delta_primitives - aligned_primitives)
    if missing_delta:
        errors.append(
            "seed revised_route_alignment_edges miss delta primitives: "
            + ",".join(missing_delta)
        )
    return tuple(errors)


def _llm_seed_alignment_observed(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> str:
    metadata = _seed_route_metadata(seed_route)
    metadata = metadata if isinstance(metadata, dict) else {}
    delta_primitives = _llm_delta_primitives(row)
    aligned_primitives = _alignment_primitives(
        seed_route.get("revised_route_alignment_edges", [])
    )
    missing_delta = sorted(delta_primitives - aligned_primitives)
    return (
        f"row_edges={len(_llm_row_alignment_triples(row))}; "
        f"seed_route_edges={len(_llm_seed_alignment_triples(seed_route.get('revised_route_alignment_edges', [])))}; "
        f"metadata_edges={len(_llm_seed_alignment_triples(metadata.get('revised_route_alignment_edges', [])))}; "
        f"missing_delta={','.join(missing_delta)}"
    )


def _llm_seed_dag_errors(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    metadata = _seed_route_metadata(seed_route)
    if not seed_route:
        errors.append("seed route missing")
    if not isinstance(metadata, dict):
        errors.append("seed route replan_metadata missing")
        return tuple(errors)
    row_informal = _node_ids(row.get("informal_knowledge_dag_nodes", []))
    route_informal = _node_ids(seed_route.get("revised_informal_knowledge_dag_nodes", []))
    metadata_informal = _node_ids(
        metadata.get("revised_informal_knowledge_dag_nodes", [])
    )
    if not row_informal:
        errors.append("accepted LLM row informal_knowledge_dag_nodes empty")
    if row_informal != route_informal:
        errors.append("seed route revised_informal_knowledge_dag_nodes mismatch")
    if row_informal != metadata_informal:
        errors.append("seed metadata revised_informal_knowledge_dag_nodes mismatch")
    for node in _dict_tuple(seed_route.get("revised_informal_knowledge_dag_nodes", [])):
        if str(node.get("node_source", "")) != "llm_route_planner_revised_informal_dag":
            errors.append("seed informal DAG node_source mismatch")
            break
    row_formal = _primitive_ids(_llm_formal_realization_nodes(row))
    route_formal = _primitive_ids(_llm_revised_formal_realization_nodes(seed_route))
    metadata_formal = _primitive_ids(
        _llm_revised_formal_realization_nodes(metadata)
    )
    if not row_formal:
        errors.append("accepted LLM row formal_realization_dag_nodes empty")
    if row_formal != route_formal:
        errors.append("seed route revised_formal_realization_dag_nodes mismatch")
    if row_formal != metadata_formal:
        errors.append("seed metadata revised_formal_realization_dag_nodes mismatch")
    if _object_hashes(
        seed_route.get("revised_informal_knowledge_dag_nodes", [])
    ) != _object_hashes(metadata.get("revised_informal_knowledge_dag_nodes", [])):
        errors.append("seed route and metadata revised informal DAG nodes differ")
    if _object_hashes(
        _llm_revised_formal_realization_nodes(seed_route)
    ) != _object_hashes(_llm_revised_formal_realization_nodes(metadata)):
        errors.append("seed route and metadata revised formal-realization DAG nodes differ")
    legacy_route = _dict_tuple(seed_route.get("revised_lean_realization_dag_nodes", []))
    legacy_metadata = _dict_tuple(metadata.get("revised_lean_realization_dag_nodes", []))
    if legacy_route and _object_hashes(legacy_route) != _object_hashes(
        _llm_revised_formal_realization_nodes(seed_route)
    ):
        errors.append("seed route legacy revised Lean DAG alias differs from formal DAG")
    if legacy_metadata and _object_hashes(legacy_metadata) != _object_hashes(
        _llm_revised_formal_realization_nodes(metadata)
    ):
        errors.append("seed metadata legacy revised Lean DAG alias differs from formal DAG")
    return tuple(errors)


def _llm_seed_dag_observed(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> str:
    metadata = _seed_route_metadata(seed_route)
    metadata = metadata if isinstance(metadata, dict) else {}
    return (
        f"informal:row={len(_node_ids(row.get('informal_knowledge_dag_nodes', [])))}"
        f",seed_route={len(_node_ids(seed_route.get('revised_informal_knowledge_dag_nodes', [])))}"
        f",metadata={len(_node_ids(metadata.get('revised_informal_knowledge_dag_nodes', [])))}; "
        f"formal:row={len(_primitive_ids(_llm_formal_realization_nodes(row)))}"
        f",seed_route={len(_primitive_ids(_llm_revised_formal_realization_nodes(seed_route)))}"
        f",metadata={len(_primitive_ids(_llm_revised_formal_realization_nodes(metadata)))}"
    )


def _llm_realization_witness_schema_errors(schema: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    props = _dict_value(schema, "properties")
    witness_prop = _dict_value(props, "realization_coverage_witness")
    if witness_prop.get("$ref") != "#/$defs/realization_coverage_witness":
        errors.append("realization_coverage_witness must reference $defs")
    defs = _dict_value(schema, "$defs")
    witness = _dict_value(defs, "realization_coverage_witness")
    if not witness:
        errors.append("$defs.realization_coverage_witness missing")
        return tuple(errors)
    required = set(_str_tuple(witness.get("required", [])))
    expected_required = {
        "selected_primitives",
        "delta_primitives",
        "introduced_primitives",
        "aligned_primitives",
        "selected_primitives_with_standalone_route_node",
        "selected_primitives_missing_standalone_route_node",
        "selected_primitives_with_formal_realization_node",
        "selected_primitives_missing_formal_realization_node",
        "route_option_primitives",
        "route_option_primitives_with_standalone_route_node",
        "route_option_primitives_missing_standalone_route_node",
        "route_option_primitives_with_formal_realization_node",
        "route_option_primitives_missing_formal_realization_node",
        "delta_primitives_with_route_alignment_edge",
        "delta_primitives_missing_route_alignment_edge",
        "introduced_primitives_with_route_alignment_edge",
        "introduced_primitives_missing_route_alignment_edge",
        "selected_route_coverage_complete",
        "selected_formal_coverage_complete",
        "route_option_route_coverage_complete",
        "route_option_formal_coverage_complete",
        "delta_alignment_complete",
        "introduced_alignment_complete",
        "realization_coverage_complete",
    }
    missing = sorted(expected_required - required)
    if missing:
        errors.append(
            "$defs.realization_coverage_witness.required missing: "
            + ",".join(missing)
        )
    witness_props = _dict_value(witness, "properties")
    for field_name in sorted(
        field for field in expected_required if field.endswith("_complete")
    ):
        if _dict_value(witness_props, field_name).get("type") != "boolean":
            errors.append(f"{field_name} must be boolean")
    for field_name in sorted(
        field for field in expected_required if not field.endswith("_complete")
    ):
        field_schema = _dict_value(witness_props, field_name)
        if field_schema.get("type") != "array":
            errors.append(f"{field_name} must be array")
        if _dict_value(field_schema, "items").get("type") != "string":
            errors.append(f"{field_name} items must be string")
    return tuple(errors)


def _llm_realization_witness_schema_observed(schema: dict[str, Any]) -> str:
    witness_prop = _dict_value(
        _dict_value(schema, "properties"),
        "realization_coverage_witness",
    )
    witness = _dict_value(
        _dict_value(schema, "$defs"),
        "realization_coverage_witness",
    )
    required = _str_tuple(witness.get("required", []))
    return (
        f"ref={witness_prop.get('$ref', '')}; "
        f"required={len(required)}; "
        f"has_complete={bool(_dict_value(witness.get('properties', {}), 'realization_coverage_complete'))}"
    )


def _llm_legacy_response_alias_schema_errors(
    schema: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    required = set(_str_tuple(schema.get("required", [])))
    if "legacy_response_field_aliases" not in required:
        errors.append("manifest schema must require legacy_response_field_aliases")
    alias_schema = _dict_value(
        _dict_value(schema, "properties"),
        "legacy_response_field_aliases",
    )
    alias_required = set(_str_tuple(alias_schema.get("required", [])))
    if "lean_realization_dag_nodes" not in alias_required:
        errors.append(
            "legacy_response_field_aliases schema must require lean_realization_dag_nodes"
        )
    actual = (
        _dict_value(
            _dict_value(alias_schema, "properties"),
            "lean_realization_dag_nodes",
        ).get("const")
    )
    expected = LLM_ROUTE_PLANNER_LEGACY_RESPONSE_FIELD_ALIASES[
        "lean_realization_dag_nodes"
    ]
    if actual != expected:
        errors.append(
            "legacy_response_field_aliases.lean_realization_dag_nodes "
            f"must const {expected}"
        )
    return tuple(errors)


def _llm_legacy_response_alias_schema_observed(schema: dict[str, Any]) -> str:
    alias_schema = _dict_value(
        _dict_value(schema, "properties"),
        "legacy_response_field_aliases",
    )
    actual = (
        _dict_value(
            _dict_value(alias_schema, "properties"),
            "lean_realization_dag_nodes",
        ).get("const", "")
    )
    return (
        f"required={'legacy_response_field_aliases' in set(_str_tuple(schema.get('required', [])))}; "
        f"lean_realization_dag_nodes={actual}"
    )


def _llm_legacy_response_alias_errors(
    manifest: dict[str, Any],
) -> tuple[str, ...]:
    aliases = manifest.get("legacy_response_field_aliases", {})
    if not isinstance(aliases, dict):
        return ("legacy_response_field_aliases must be an object",)
    expected = dict(LLM_ROUTE_PLANNER_LEGACY_RESPONSE_FIELD_ALIASES)
    if aliases != expected:
        return (
            "legacy_response_field_aliases must equal "
            f"{json.dumps(expected, sort_keys=True)}",
        )
    return ()


def _llm_legacy_response_alias_observed(manifest: dict[str, Any]) -> str:
    aliases = manifest.get("legacy_response_field_aliases", {})
    if isinstance(aliases, dict):
        return json.dumps(aliases, sort_keys=True)
    return str(type(aliases).__name__)


def _llm_generic_formal_dag_errors(
    rows: list[dict[str, Any]],
    seed_payload: dict[str, Any],
    manifest: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    expected = sum(
        len(_object_hashes(row.get("formal_realization_dag_nodes", [])))
        for row in rows
    )
    if "n_formal_realization_dag_nodes" not in manifest:
        errors.append("manifest n_formal_realization_dag_nodes missing")
    elif int(manifest.get("n_formal_realization_dag_nodes", 0) or 0) != expected:
        errors.append("manifest n_formal_realization_dag_nodes mismatch")
    seed_routes = _seed_route_index(seed_payload)
    for idx, row in enumerate(rows):
        if not _llm_route_planner_row_accepted(row):
            continue
        errors.extend(_generic_formal_dag_field_errors(f"row {idx}", row))
        seed_route = _llm_seed_route_for_row(seed_payload, row)
        seed_route_id = str(seed_route.get("route_id", "")) if seed_route else ""
        if not seed_route:
            errors.append(f"seed route for row {idx} missing")
            continue
        if seed_route_id and seed_route_id not in seed_routes:
            errors.append(f"seed route {seed_route_id} missing from seed index")
        errors.extend(
            _generic_revised_formal_dag_field_errors(
                f"seed route {seed_route_id or idx}",
                seed_route,
            )
        )
        metadata = _seed_route_metadata(seed_route)
        if not isinstance(metadata, dict):
            errors.append(f"seed metadata {seed_route_id or idx} missing")
            continue
        errors.extend(
            _generic_revised_formal_dag_field_errors(
                f"seed metadata {seed_route_id or idx}",
                metadata,
            )
        )
    return tuple(errors)


def _llm_generic_formal_dag_observed(
    rows: list[dict[str, Any]],
    seed_payload: dict[str, Any],
    manifest: dict[str, Any],
) -> str:
    accepted = [row for row in rows if _llm_route_planner_row_accepted(row)]
    row_generic = sum(
        len(_object_hashes(row.get("formal_realization_dag_nodes", [])))
        for row in accepted
    )
    row_legacy = sum(
        len(_object_hashes(row.get("lean_realization_dag_nodes", [])))
        for row in accepted
    )
    seed_generic = 0
    metadata_generic = 0
    for row in accepted:
        seed_route = _llm_seed_route_for_row(seed_payload, row)
        seed_generic += len(
            _object_hashes(seed_route.get("revised_formal_realization_dag_nodes", []))
        )
        metadata = _seed_route_metadata(seed_route)
        metadata = metadata if isinstance(metadata, dict) else {}
        metadata_generic += len(
            _object_hashes(metadata.get("revised_formal_realization_dag_nodes", []))
        )
    return (
        f"accepted={len(accepted)}; row_generic={row_generic}; row_legacy={row_legacy}; "
        f"seed_generic={seed_generic}; metadata_generic={metadata_generic}; "
        f"manifest={manifest.get('n_formal_realization_dag_nodes', 'missing')}"
    )


def _generic_formal_dag_field_errors(
    label: str,
    row: dict[str, Any],
) -> tuple[str, ...]:
    generic = _object_hashes(row.get("formal_realization_dag_nodes", []))
    legacy = _object_hashes(row.get("lean_realization_dag_nodes", []))
    errors: list[str] = []
    if not generic:
        errors.append(f"{label} formal_realization_dag_nodes missing")
    if legacy and generic and legacy != generic:
        errors.append(f"{label} lean_realization_dag_nodes differs from formal DAG")
    return tuple(errors)


def _llm_row_alignment_triples(row: dict[str, Any]) -> set[str]:
    formal_primitive_by_node_id = {
        str(node.get("node_id", "")): str(node.get("primitive") or node.get("label") or "")
        for node in _llm_formal_realization_nodes(row)
        if str(node.get("node_id", "")).strip()
    }
    fallback_primitives = _str_tuple(
        _dict_value(row, "minimal_delta_plan").get("selected_primitives", [])
    )
    triples: set[str] = set()
    for index, edge in enumerate(_dict_tuple(row.get("route_alignment_edges", []))):
        source = str(edge.get("source") or edge.get("informal_node_id") or "").strip()
        target = str(edge.get("target") or edge.get("formal_node_id") or "").strip()
        primitive = str(
            edge.get("primitive") or formal_primitive_by_node_id.get(target, "")
        ).strip()
        if not primitive and len(fallback_primitives) == 1:
            primitive = fallback_primitives[0]
        if not primitive:
            primitive = f"llm_alignment_edge_{index + 1}"
        triples.add(stable_hash([source, target, primitive]))
    return triples


def _llm_seed_alignment_triples(edges: Any) -> set[str]:
    return {
        stable_hash(
            [
                str(edge.get("source", "")).strip(),
                str(edge.get("target", "")).strip(),
                str(edge.get("primitive", "")).strip(),
            ]
        )
        for edge in _dict_tuple(edges)
    }


def _llm_delta_primitives(row: dict[str, Any]) -> set[str]:
    minimal_delta = _dict_value(row, "minimal_delta_plan")
    selected = {
        _llm_primitive_key(primitive)
        for primitive in _str_tuple(minimal_delta.get("selected_primitives", []))
        if _llm_primitive_key(primitive)
    }
    fields = (
        "wrapper_lemmas",
        "bridge_lemmas",
        "source_port_lemmas",
        "new_definitions",
        "new_theory_primitives",
        "first_principles_primitives",
    )
    primitives: set[str] = set()
    for field_name in fields:
        primitives.update(
            _llm_delta_primitives_from_action_field(
                minimal_delta,
                field_name,
                selected,
            )
        )
    primitives.discard("")
    return primitives


def _node_ids(values: Any) -> set[str]:
    return {
        str(value.get("node_id", "")).strip()
        for value in _dict_tuple(values)
        if str(value.get("node_id", "")).strip()
    }


def _primitive_ids(values: Any) -> set[str]:
    return {
        str(value.get("primitive") or value.get("label") or value.get("node_id") or "").strip()
        for value in _dict_tuple(values)
        if str(value.get("primitive") or value.get("label") or value.get("node_id") or "").strip()
    }


def _goal_conditioned_plan_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = (
        bundle_dir / "artifacts" / "goal_conditioned_minimal_formalization_plan"
    )
    manifest_path = (
        artifact_dir / "goal_conditioned_minimal_formalization_plan_manifest.json"
    )
    rows_jsonl_path = artifact_dir / "goal_conditioned_minimal_formalization_plan.jsonl"
    row_schema_path = artifact_dir / "library_aware_formalization_gap_plan_row.schema.json"
    manifest = _read_json_no_error(manifest_path)
    row_schema = _read_json_no_error(row_schema_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    contract_errors = validate_portable_gap_plan_payload(manifest)
    manifest_rows = [
        row for row in manifest.get("rows", []) if isinstance(row, dict)
    ]
    checks = [
        _check(
            "optional_goal_plan_all_ok",
            "optional_artifacts",
            "goal-conditioned plan manifest all_ok",
            str(manifest.get("all_ok", "")),
            bool(manifest.get("all_ok", False)),
        ),
        _check(
            "optional_goal_plan_portable_contract",
            "optional_artifacts",
            "goal-conditioned plan manifest validates against portable gap-plan contract",
            "; ".join(contract_errors) if contract_errors else "ok",
            not contract_errors,
            errors=tuple(contract_errors),
        ),
        _check(
            "optional_goal_plan_boundary",
            "optional_artifacts",
            "not theorem proof evidence",
            str(manifest.get("proof_evidence_boundary", ""))[:160],
            "not theorem proof evidence"
            in str(manifest.get("proof_evidence_boundary", "")).lower(),
        ),
        _check(
            "optional_goal_plan_row_schema_file",
            "optional_artifacts",
            "goal-conditioned plan row schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            "optional_goal_plan_row_schema_id",
            "optional_artifacts",
            PORTABLE_FORMALIZATION_GAP_PLAN_ROW_SCHEMA_ID,
            str(row_schema.get("$id", "")),
            row_schema.get("$id") == PORTABLE_FORMALIZATION_GAP_PLAN_ROW_SCHEMA_ID,
        ),
        _check(
            "optional_goal_plan_jsonl_parse",
            "optional_artifacts",
            "goal-conditioned plan JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_goal_plan_jsonl_row_count",
            "optional_artifacts",
            "goal-conditioned plan JSONL rows match manifest plan count",
            f"jsonl={len(rows)} manifest={manifest.get('n_goal_plans', 0)}",
            len(rows) == int(manifest.get("n_goal_plans", 0) or 0),
        ),
        _check(
            "optional_goal_plan_jsonl_manifest_row_count",
            "optional_artifacts",
            "goal-conditioned plan JSONL rows match embedded manifest rows",
            f"jsonl={len(rows)} manifest_rows={len(manifest_rows)}",
            len(rows) == len(manifest_rows),
        ),
    ]
    manifest_row_ids = {
        str(row.get("goal_plan_id", "")) for row in manifest_rows if row.get("goal_plan_id")
    }
    snapshot_ref = str(manifest.get("library_snapshot_ref", ""))
    for idx, row in enumerate(rows):
        row_schema_errors = validate_portable_gap_plan_row(
            row,
            row_schema,
            library_snapshot_ref=snapshot_ref,
        )
        checks.append(
            _check(
                f"optional_goal_plan_row_{idx}_schema_valid",
                "optional_artifacts",
                "goal-conditioned plan row validates against public row schema",
                "; ".join(row_schema_errors) if row_schema_errors else "ok",
                not row_schema_errors,
                errors=tuple(row_schema_errors),
            )
        )
        contract_errors = _goal_plan_row_contract_errors(row, manifest_row_ids)
        checks.append(
            _check(
                f"optional_goal_plan_row_{idx}_contract_valid",
                "optional_artifacts",
                "goal-conditioned plan row preserves portable route contract",
                "; ".join(contract_errors) if contract_errors else "ok",
                not contract_errors,
                errors=contract_errors,
            )
        )
    return checks


def _generic_audit_optional_checks(
    bundle_dir: Path,
    *,
    artifact_name: str,
    manifest_filename: str,
    jsonl_filename: str,
    check_prefix: str,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = bundle_dir / "artifacts" / artifact_name
    manifest_path = artifact_dir / manifest_filename
    rows_jsonl_path = artifact_dir / jsonl_filename
    manifest = _read_json_no_error(manifest_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    check_label = artifact_name.replace("formalization_gap_planner_", "")
    checks = [
        _check(
            f"{check_prefix}_all_ok",
            "optional_artifacts",
            f"{check_label} manifest all_ok",
            str(manifest.get("all_ok", "")),
            bool(manifest.get("all_ok", False)),
        ),
        _check(
            f"{check_prefix}_component",
            "optional_artifacts",
            artifact_name,
            str(manifest.get("component_name", "")),
            manifest.get("component_name") == artifact_name,
        ),
        _check(
            f"{check_prefix}_failed_count",
            "optional_artifacts",
            f"{check_label} manifest has zero failed checks",
            str(manifest.get("n_failed", "")),
            int(manifest.get("n_failed", 0) or 0) == 0,
        ),
        _check(
            f"{check_prefix}_boundary",
            "optional_artifacts",
            "not theorem proof evidence",
            str(manifest.get("proof_evidence_boundary", ""))[:160],
            "not theorem proof evidence"
            in str(manifest.get("proof_evidence_boundary", "")).lower(),
        ),
        _check(
            f"{check_prefix}_jsonl_parse",
            "optional_artifacts",
            f"{check_label} JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            f"{check_prefix}_jsonl_row_count",
            "optional_artifacts",
            f"{check_label} JSONL rows match manifest check count",
            f"jsonl={len(rows)} manifest={manifest.get('n_checks', 0)}",
            len(rows) == int(manifest.get("n_checks", 0) or 0),
        ),
    ]
    for idx, row in enumerate(rows):
        contract_errors = _audit_check_row_contract_errors(row)
        checks.append(
            _check(
                f"{check_prefix}_{idx}_contract_valid",
                "optional_artifacts",
                f"{check_label} check row preserves audit-row contract",
                "; ".join(contract_errors) if contract_errors else "ok",
                not contract_errors,
                errors=contract_errors,
            )
        )
    return checks


def _minimal_delta_audit_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = (
        bundle_dir / "artifacts" / "formalization_gap_planner_minimal_delta_audit"
    )
    manifest_path = (
        artifact_dir
        / "formalization_gap_planner_minimal_delta_audit_manifest.json"
    )
    rows_jsonl_path = (
        artifact_dir / "formalization_gap_planner_minimal_delta_decisions.jsonl"
    )
    row_schema_path = (
        artifact_dir
        / "formalization_gap_planner_minimal_delta_decision_row.schema.json"
    )
    manifest = _read_json_no_error(manifest_path)
    row_schema = _read_json_no_error(row_schema_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    checks = [
        _check(
            "optional_minimal_delta_audit_all_ok",
            "optional_artifacts",
            "minimal-delta audit manifest all_ok",
            str(manifest.get("all_ok", "")),
            bool(manifest.get("all_ok", False)),
        ),
        _check(
            "optional_minimal_delta_audit_boundary",
            "optional_artifacts",
            "not theorem proof evidence",
            str(manifest.get("proof_evidence_boundary", ""))[:160],
            "not theorem proof evidence"
            in str(manifest.get("proof_evidence_boundary", "")).lower(),
        ),
        _check(
            "optional_minimal_delta_decision_row_schema_file",
            "optional_artifacts",
            "optional minimal-delta decision row schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            "optional_minimal_delta_decision_row_schema_id",
            "optional_artifacts",
            MINIMAL_DELTA_DECISION_ROW_SCHEMA_ID,
            str(row_schema.get("$id", "")),
            row_schema.get("$id") == MINIMAL_DELTA_DECISION_ROW_SCHEMA_ID,
        ),
        _check(
            "optional_minimal_delta_decision_manifest_schema_valid_count",
            "optional_artifacts",
            "minimal-delta manifest decision-row schema-valid count matches row count",
            (
                f"{manifest.get('n_minimal_delta_decision_row_schema_valid', 0)}/"
                f"{manifest.get('n_minimal_delta_decision_rows', 0)}; "
                f"invalid={manifest.get('n_minimal_delta_decision_row_schema_invalid', 0)}"
            ),
            int(manifest.get("n_minimal_delta_decision_rows", 0) or 0) > 0
            and int(
                manifest.get("n_minimal_delta_decision_row_schema_valid", 0) or 0
            )
            == int(manifest.get("n_minimal_delta_decision_rows", 0) or 0)
            and int(
                manifest.get("n_minimal_delta_decision_row_schema_invalid", 0) or 0
            )
            == 0,
        ),
        _check(
            "optional_minimal_delta_decision_jsonl_parse",
            "optional_artifacts",
            "minimal-delta decision JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_minimal_delta_decision_jsonl_row_count",
            "optional_artifacts",
            "minimal-delta decision JSONL rows match manifest decision count",
            (
                f"jsonl={len(rows)} "
                f"manifest={manifest.get('n_minimal_delta_decision_rows', 0)}"
            ),
            len(rows)
            == int(manifest.get("n_minimal_delta_decision_rows", 0) or 0),
        ),
    ]
    for idx, row in enumerate(rows):
        schema_errors = validate_minimal_delta_decision_row(row)
        checks.append(
            _check(
                f"optional_minimal_delta_decision_row_{idx}_schema_valid",
                "optional_artifacts",
                "minimal-delta decision row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=tuple(schema_errors),
            )
        )
    return checks


def _source_grounding_audit_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = (
        bundle_dir / "artifacts" / "formalization_gap_planner_source_grounding_audit"
    )
    manifest_path = (
        artifact_dir
        / "formalization_gap_planner_source_grounding_audit_manifest.json"
    )
    rows_jsonl_path = (
        artifact_dir / "formalization_gap_planner_source_grounding_audit.jsonl"
    )
    row_schema_path = (
        artifact_dir / "formalization_gap_planner_source_grounding_row.schema.json"
    )
    manifest = _read_json_no_error(manifest_path)
    row_schema = _read_json_no_error(row_schema_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    checks = [
        _check(
            "optional_source_grounding_audit_all_ok",
            "optional_artifacts",
            "source-grounding audit manifest all_ok",
            str(manifest.get("all_ok", "")),
            bool(manifest.get("all_ok", False)),
        ),
        _check(
            "optional_source_grounding_audit_boundary",
            "optional_artifacts",
            "not theorem proof evidence",
            str(manifest.get("proof_evidence_boundary", ""))[:160],
            "not theorem proof evidence"
            in str(manifest.get("proof_evidence_boundary", "")).lower(),
        ),
        _check(
            "optional_source_grounding_row_schema_file",
            "optional_artifacts",
            "optional source-grounding row schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            "optional_source_grounding_row_schema_id",
            "optional_artifacts",
            SOURCE_GROUNDING_ROW_SCHEMA_ID,
            str(row_schema.get("$id", "")),
            row_schema.get("$id") == SOURCE_GROUNDING_ROW_SCHEMA_ID,
        ),
        _check(
            "optional_source_grounding_manifest_schema_valid_count",
            "optional_artifacts",
            "source-grounding manifest row schema-valid count matches row count",
            (
                f"{manifest.get('n_row_schema_valid', 0)}/"
                f"{manifest.get('n_source_grounding_rows', 0)}; "
                f"invalid={manifest.get('n_row_schema_invalid', 0)}"
            ),
            int(manifest.get("n_source_grounding_rows", 0) or 0) > 0
            and int(manifest.get("n_row_schema_valid", 0) or 0)
            == int(manifest.get("n_source_grounding_rows", 0) or 0)
            and int(manifest.get("n_row_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_source_grounding_jsonl_parse",
            "optional_artifacts",
            "source-grounding JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_source_grounding_jsonl_row_count",
            "optional_artifacts",
            "source-grounding JSONL rows match manifest count",
            f"jsonl={len(rows)} manifest={manifest.get('n_source_grounding_rows', 0)}",
            len(rows) == int(manifest.get("n_source_grounding_rows", 0) or 0),
        ),
        _check(
            "optional_source_grounding_residual_source_status",
            "optional_artifacts",
            "residual rows are source-backed, pending, or boundary-declared",
            (
                f"residual_rows={manifest.get('n_residual_grounding_rows', 0)} "
                f"unaccounted={manifest.get('n_residual_unaccounted', 0)} "
                f"ok={manifest.get('residual_source_grounding_ok', True)}"
            ),
            bool(manifest.get("residual_source_grounding_ok", True))
            and int(manifest.get("n_residual_unaccounted", 0) or 0) == 0,
        ),
    ]
    for idx, row in enumerate(rows):
        schema_errors = validate_source_grounding_row(row)
        checks.append(
            _check(
                f"optional_source_grounding_row_{idx}_schema_valid",
                "optional_artifacts",
                "source-grounding row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=tuple(schema_errors),
            )
        )
    return checks


def _refinement_queue_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = bundle_dir / "artifacts" / "formalization_gap_planner_refinement_queue"
    manifest_path = artifact_dir / "formalization_gap_planner_refinement_queue_manifest.json"
    rows_jsonl_path = artifact_dir / "formalization_gap_planner_refinement_queue.jsonl"
    row_schema_path = artifact_dir / "formalization_gap_planner_refinement_work_item.schema.json"
    manifest = _read_json_no_error(manifest_path)
    row_schema = _read_json_no_error(row_schema_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    checks = [
        _check(
            "optional_refinement_queue_all_ok",
            "optional_artifacts",
            "refinement queue manifest all_ok",
            str(manifest.get("all_ok", "")),
            bool(manifest.get("all_ok", False)),
        ),
        _check(
            "optional_refinement_queue_boundary",
            "optional_artifacts",
            "not theorem proof evidence",
            str(manifest.get("proof_evidence_boundary", ""))[:160],
            "not theorem proof evidence"
            in str(manifest.get("proof_evidence_boundary", "")).lower(),
        ),
        _check(
            "optional_refinement_work_item_row_schema_file",
            "optional_artifacts",
            "optional refinement work-item schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            "optional_refinement_work_item_row_schema_id",
            "optional_artifacts",
            REFINEMENT_WORK_ITEM_SCHEMA_ID,
            str(row_schema.get("$id", "")),
            row_schema.get("$id") == REFINEMENT_WORK_ITEM_SCHEMA_ID,
        ),
        _check(
            "optional_refinement_work_item_manifest_schema_valid_count",
            "optional_artifacts",
            "refinement manifest work-item schema-valid count matches row count",
            (
                f"{manifest.get('n_item_schema_valid', 0)}/"
                f"{manifest.get('n_refinement_items', 0)}; "
                f"invalid={manifest.get('n_item_schema_invalid', 0)}"
            ),
            int(manifest.get("n_refinement_items", 0) or 0) > 0
            and int(manifest.get("n_item_schema_valid", 0) or 0)
            == int(manifest.get("n_refinement_items", 0) or 0)
            and int(manifest.get("n_item_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_refinement_work_item_jsonl_parse",
            "optional_artifacts",
            "refinement work-item JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_refinement_work_item_jsonl_row_count",
            "optional_artifacts",
            "refinement work-item JSONL rows match manifest count",
            f"jsonl={len(rows)} manifest={manifest.get('n_refinement_items', 0)}",
            len(rows) == int(manifest.get("n_refinement_items", 0) or 0),
        ),
    ]
    for idx, row in enumerate(rows):
        schema_errors = validate_refinement_work_item_row(row)
        checks.append(
            _check(
                f"optional_refinement_work_item_row_{idx}_schema_valid",
                "optional_artifacts",
                "refinement work-item row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=tuple(schema_errors),
            )
        )
    return checks


def _library_coverage_map_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = (
        bundle_dir / "artifacts" / "formalization_gap_planner_library_coverage_map"
    )
    manifest_path = (
        artifact_dir / "formalization_gap_planner_library_coverage_map_manifest.json"
    )
    rows_jsonl_path = (
        artifact_dir / "formalization_gap_planner_library_coverage_map.jsonl"
    )
    row_schema_path = (
        artifact_dir / "formalization_gap_planner_library_coverage_map_row.schema.json"
    )
    manifest = _read_json_no_error(manifest_path)
    row_schema = _read_json_no_error(row_schema_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    checks = [
        _check(
            "optional_library_coverage_map_row_schema_file",
            "optional_artifacts",
            "optional library-coverage map row schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            "optional_library_coverage_map_row_schema_id",
            "optional_artifacts",
            LIBRARY_COVERAGE_MAP_ROW_SCHEMA_ID,
            str(row_schema.get("$id", "")),
            row_schema.get("$id") == LIBRARY_COVERAGE_MAP_ROW_SCHEMA_ID,
        ),
        _check(
            "optional_library_coverage_map_manifest_schema_valid_count",
            "optional_artifacts",
            "library-coverage map manifest row schema-valid count matches row count",
            (
                f"{manifest.get('n_row_schema_valid', 0)}/"
                f"{manifest.get('n_coverage_rows', 0)}; "
                f"invalid={manifest.get('n_row_schema_invalid', 0)}"
            ),
            int(manifest.get("n_coverage_rows", 0) or 0) > 0
            and int(manifest.get("n_row_schema_valid", 0) or 0)
            == int(manifest.get("n_coverage_rows", 0) or 0)
            and int(manifest.get("n_row_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_library_coverage_map_jsonl_parse",
            "optional_artifacts",
            "library-coverage map JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_library_coverage_map_jsonl_row_count",
            "optional_artifacts",
            "library-coverage map JSONL rows match manifest coverage-row count",
            f"jsonl={len(rows)} manifest={manifest.get('n_coverage_rows', 0)}",
            len(rows) == int(manifest.get("n_coverage_rows", 0) or 0),
        ),
    ]
    for idx, row in enumerate(rows):
        schema_errors = validate_library_coverage_map_row(row)
        checks.append(
            _check(
                f"optional_library_coverage_map_row_{idx}_schema_valid",
                "optional_artifacts",
                "library-coverage map row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
    return checks


def _primitive_action_queue_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = (
        bundle_dir / "artifacts" / "formalization_gap_planner_primitive_action_queue"
    )
    manifest_path = (
        artifact_dir
        / "formalization_gap_planner_primitive_action_queue_manifest.json"
    )
    rows_jsonl_path = (
        artifact_dir / "formalization_gap_planner_primitive_action_queue.jsonl"
    )
    row_schema_path = (
        artifact_dir
        / "formalization_gap_planner_primitive_action_queue_row.schema.json"
    )
    manifest = _read_json_no_error(manifest_path)
    row_schema = _read_json_no_error(row_schema_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    checks = [
        _check(
            "optional_primitive_action_queue_row_schema_file",
            "optional_artifacts",
            "optional primitive action-queue row schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            "optional_primitive_action_queue_row_schema_id",
            "optional_artifacts",
            PRIMITIVE_ACTION_QUEUE_ROW_SCHEMA_ID,
            str(row_schema.get("$id", "")),
            row_schema.get("$id") == PRIMITIVE_ACTION_QUEUE_ROW_SCHEMA_ID,
        ),
        _check(
            "optional_primitive_action_queue_manifest_schema_valid_count",
            "optional_artifacts",
            "primitive action-queue manifest row schema-valid count matches item count",
            (
                f"{manifest.get('n_row_schema_valid', 0)}/"
                f"{manifest.get('n_action_items', 0)}; "
                f"invalid={manifest.get('n_row_schema_invalid', 0)}"
            ),
            int(manifest.get("n_action_items", 0) or 0) > 0
            and int(manifest.get("n_row_schema_valid", 0) or 0)
            == int(manifest.get("n_action_items", 0) or 0)
            and int(manifest.get("n_row_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_primitive_action_queue_jsonl_parse",
            "optional_artifacts",
            "primitive action-queue JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_primitive_action_queue_jsonl_row_count",
            "optional_artifacts",
            "primitive action-queue JSONL rows match manifest action-item count",
            f"jsonl={len(rows)} manifest={manifest.get('n_action_items', 0)}",
            len(rows) == int(manifest.get("n_action_items", 0) or 0),
        ),
    ]
    for idx, row in enumerate(rows):
        schema_errors = validate_primitive_action_queue_row(row)
        checks.append(
            _check(
                f"optional_primitive_action_queue_row_{idx}_schema_valid",
                "optional_artifacts",
                "primitive action-queue row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
    return checks


def _action_resource_plan_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = (
        bundle_dir / "artifacts" / "formalization_gap_planner_action_resource_plan"
    )
    manifest_path = (
        artifact_dir
        / "formalization_gap_planner_action_resource_plan_manifest.json"
    )
    rows_jsonl_path = (
        artifact_dir / "formalization_gap_planner_action_resource_plan.jsonl"
    )
    row_schema_path = (
        artifact_dir
        / "formalization_gap_planner_action_resource_plan_row.schema.json"
    )
    manifest = _read_json_no_error(manifest_path)
    row_schema = _read_json_no_error(row_schema_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    checks = [
        _check(
            "optional_action_resource_plan_row_schema_file",
            "optional_artifacts",
            "optional action-resource plan row schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            "optional_action_resource_plan_row_schema_id",
            "optional_artifacts",
            ACTION_RESOURCE_PLAN_ROW_SCHEMA_ID,
            str(row_schema.get("$id", "")),
            row_schema.get("$id") == ACTION_RESOURCE_PLAN_ROW_SCHEMA_ID,
        ),
        _check(
            "optional_action_resource_plan_manifest_schema_valid_count",
            "optional_artifacts",
            "action-resource plan manifest row schema-valid count matches plan count",
            (
                f"{manifest.get('n_row_schema_valid', 0)}/"
                f"{manifest.get('n_resource_plan_rows', 0)}; "
                f"invalid={manifest.get('n_row_schema_invalid', 0)}"
            ),
            int(manifest.get("n_resource_plan_rows", 0) or 0) > 0
            and int(manifest.get("n_row_schema_valid", 0) or 0)
            == int(manifest.get("n_resource_plan_rows", 0) or 0)
            and int(manifest.get("n_row_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_action_resource_plan_jsonl_parse",
            "optional_artifacts",
            "action-resource plan JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_action_resource_plan_jsonl_row_count",
            "optional_artifacts",
            "action-resource plan JSONL rows match manifest resource-plan count",
            f"jsonl={len(rows)} manifest={manifest.get('n_resource_plan_rows', 0)}",
            len(rows) == int(manifest.get("n_resource_plan_rows", 0) or 0),
        ),
    ]
    for idx, row in enumerate(rows):
        schema_errors = validate_action_resource_plan_row(row)
        checks.append(
            _check(
                f"optional_action_resource_plan_row_{idx}_schema_valid",
                "optional_artifacts",
                "action-resource plan row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
    return checks


def _resource_request_queue_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = (
        bundle_dir / "artifacts" / "formalization_gap_planner_resource_request_queue"
    )
    manifest_path = (
        artifact_dir
        / "formalization_gap_planner_resource_request_queue_manifest.json"
    )
    rows_jsonl_path = (
        artifact_dir / "formalization_gap_planner_resource_request_queue.jsonl"
    )
    row_schema_path = (
        artifact_dir
        / "formalization_gap_planner_resource_request_queue_row.schema.json"
    )
    action_rows_jsonl_path = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_action_resource_plan"
        / "formalization_gap_planner_action_resource_plan.jsonl"
    )
    manifest = _read_json_no_error(manifest_path)
    row_schema = _read_json_no_error(row_schema_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    action_rows, action_row_errors = _read_jsonl_dict_rows_no_error(
        action_rows_jsonl_path
    )
    action_plan_index = _action_resource_plan_index(action_rows)
    checks = [
        _check(
            "optional_resource_request_queue_row_schema_file",
            "optional_artifacts",
            "optional resource request-queue row schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            "optional_resource_request_queue_row_schema_id",
            "optional_artifacts",
            RESOURCE_REQUEST_QUEUE_ROW_SCHEMA_ID,
            str(row_schema.get("$id", "")),
            row_schema.get("$id") == RESOURCE_REQUEST_QUEUE_ROW_SCHEMA_ID,
        ),
        _check(
            "optional_resource_request_queue_manifest_schema_valid_count",
            "optional_artifacts",
            "resource request-queue manifest row schema-valid count matches request count",
            (
                f"{manifest.get('n_row_schema_valid', 0)}/"
                f"{manifest.get('n_resource_request_rows', 0)}; "
                f"invalid={manifest.get('n_row_schema_invalid', 0)}"
            ),
            int(manifest.get("n_resource_request_rows", 0) or 0) > 0
            and int(manifest.get("n_row_schema_valid", 0) or 0)
            == int(manifest.get("n_resource_request_rows", 0) or 0)
            and int(manifest.get("n_row_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_resource_request_queue_jsonl_parse",
            "optional_artifacts",
            "resource request-queue JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_resource_request_queue_jsonl_row_count",
            "optional_artifacts",
            "resource request-queue JSONL rows match manifest request count",
            f"jsonl={len(rows)} manifest={manifest.get('n_resource_request_rows', 0)}",
            len(rows) == int(manifest.get("n_resource_request_rows", 0) or 0),
        ),
        _check(
            "optional_resource_request_queue_action_resource_plan_jsonl_parse",
            "optional_artifacts",
            "bundled action-resource plan JSONL parses for request alignment",
            (
                "; ".join(action_row_errors)
                if action_row_errors
                else f"rows={len(action_rows)}"
            ),
            not action_row_errors and bool(action_rows),
            errors=action_row_errors,
        ),
    ]
    for idx, row in enumerate(rows):
        schema_errors = validate_resource_request_queue_row(row)
        action_resource_plan_id = str(row.get("action_resource_plan_id", ""))
        action_row = action_plan_index.get(action_resource_plan_id)
        llm_trace_errors = _resource_request_llm_route_planner_trace_errors(row)
        ref_ok = action_row is not None or not llm_trace_errors
        payload_identity_errors = _resource_request_payload_identity_errors(row)
        dispatch_spec_errors = _resource_request_dispatch_spec_errors(row)
        alignment_errors = _resource_request_contract_alignment_errors(
            row,
            action_row,
            llm_trace_errors=llm_trace_errors,
        )
        checks.append(
            _check(
                f"optional_resource_request_queue_row_{idx}_schema_valid",
                "optional_artifacts",
                "resource request-queue row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
        checks.append(
            _check(
                f"optional_resource_request_queue_row_{idx}_action_resource_plan_ref",
                "optional_artifacts",
                (
                    "resource request resolves to a bundled action-resource "
                    "plan or a self-contained LLM route-planner trace"
                ),
                action_resource_plan_id,
                ref_ok,
                errors=()
                if ref_ok
                else (
                    (
                        "missing bundled action-resource plan or valid LLM "
                        "route-planner trace: "
                        + action_resource_plan_id
                    ),
                    *llm_trace_errors,
                ),
            )
        )
        checks.append(
            _check(
                f"optional_resource_request_queue_row_{idx}_request_payload_identity",
                "optional_artifacts",
                "resource request payload carries matching response-correlation fields",
                (
                    "; ".join(payload_identity_errors)
                    if payload_identity_errors
                    else "ok"
                ),
                not payload_identity_errors,
                errors=payload_identity_errors,
            )
        )
        checks.append(
            _check(
                f"optional_resource_request_queue_row_{idx}_resource_contract_alignment",
                "optional_artifacts",
                "resource request uses the selected resource's action-plan contract map",
                "; ".join(alignment_errors) if alignment_errors else "ok",
                not alignment_errors,
                errors=alignment_errors,
            )
        )
        checks.append(
            _check(
                f"optional_resource_request_queue_row_{idx}_dispatch_spec_identity",
                "optional_artifacts",
                "resource request dispatch spec matches row and nested payload",
                "; ".join(dispatch_spec_errors) if dispatch_spec_errors else "ok",
                not dispatch_spec_errors,
                errors=dispatch_spec_errors,
            )
        )
    return checks


def _action_resource_plan_index(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("action_resource_plan_id", "")): row
        for row in rows
        if row.get("action_resource_plan_id")
    }


def _resource_request_contract_alignment_errors(
    row: dict[str, Any],
    action_row: dict[str, Any] | None,
    *,
    llm_trace_errors: tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    if action_row is None:
        trace_errors = (
            llm_trace_errors
            if llm_trace_errors is not None
            else _resource_request_llm_route_planner_trace_errors(row)
        )
        if not trace_errors:
            return tuple()
        return ("resource request action_resource_plan_id does not resolve",)
    resource_id = str(row.get("resource_id", ""))
    errors: list[str] = []
    comparisons = (
        (
            "resource_contract_ids",
            _resource_map_values(
                action_row,
                "resource_contracts_by_resource",
                resource_id,
            ),
        ),
        (
            "request_contract_fields",
            _resource_map_values(
                action_row,
                "request_contract_fields_by_resource",
                resource_id,
            ),
        ),
        (
            "response_contract_fields",
            _resource_map_values(
                action_row,
                "response_contract_fields_by_resource",
                resource_id,
            ),
        ),
    )
    request_payload = row.get("request_payload", {})
    for field_name, expected in comparisons:
        observed = _str_tuple(row.get(field_name, []))
        payload_observed = (
            _str_tuple(request_payload.get(field_name, []))
            if isinstance(request_payload, dict)
            else tuple()
        )
        if not expected:
            errors.append(f"{field_name} missing map entry for {resource_id}")
            continue
        if set(observed) != set(expected):
            errors.append(
                f"{field_name} mismatch for {resource_id}: "
                f"observed={sorted(observed)} expected={sorted(expected)}"
            )
        if set(payload_observed) != set(expected):
            errors.append(
                f"request_payload.{field_name} mismatch for {resource_id}: "
                f"observed={sorted(payload_observed)} expected={sorted(expected)}"
            )
    return tuple(errors)


LLM_ROUTE_PLANNER_RESOURCE_REQUEST_SOURCE_KINDS = (
    "search_request",
    "planner_next_action",
    "residual_interpretation",
    "route_planning_brief_evidence_gap",
)


def _resource_request_llm_route_planner_trace_errors(
    row: dict[str, Any],
) -> tuple[str, ...]:
    request_payload = _as_dict(row.get("request_payload", {}))
    request_playbook = _as_dict(row.get("request_playbook", {}))
    action_resource_plan_id = str(row.get("action_resource_plan_id", "")).strip()
    errors: list[str] = []
    if not action_resource_plan_id.startswith(
        "formalization_gap_planner_llm_route_planner_action:"
    ):
        errors.append("action_resource_plan_id is not an LLM route-planner action")
    source_kind = str(
        request_payload.get("llm_route_planner_source_kind", "")
    ).strip()
    if source_kind not in LLM_ROUTE_PLANNER_RESOURCE_REQUEST_SOURCE_KINDS:
        errors.append("request_payload.llm_route_planner_source_kind is unsupported")
    if not str(request_payload.get("llm_route_planner_row_id", "")).strip():
        errors.append("request_payload.llm_route_planner_row_id is required")
    if not str(request_payload.get("llm_route_planner_hook_kind", "")).strip():
        errors.append("request_payload.llm_route_planner_hook_kind is required")
    source_item = _as_dict(request_payload.get("llm_route_planner_source_item", {}))
    if not source_item:
        errors.append("request_payload.llm_route_planner_source_item is required")
    if source_kind == "route_planning_brief_evidence_gap" and not str(
        source_item.get("route_planning_brief_gap_kind", "")
    ).strip():
        errors.append(
            "route_planning_brief_evidence_gap requires "
            "route_planning_brief_gap_kind"
        )
    for field_name in (
        "llm_route_planner_row_id",
        "llm_route_planner_source_kind",
        "llm_route_planner_source_index",
        "llm_route_planner_hook_kind",
    ):
        if request_playbook.get(field_name) != request_payload.get(field_name):
            errors.append(f"request_playbook.{field_name} must match request_payload")
    playbook_source_item = _as_dict(
        request_playbook.get("llm_route_planner_source_item", {})
    )
    if source_item and playbook_source_item != source_item:
        errors.append(
            "request_playbook.llm_route_planner_source_item must match request_payload"
        )
    payload_playbook = _as_dict(request_payload.get("request_playbook", {}))
    if payload_playbook and payload_playbook != request_playbook:
        errors.append("request_payload.request_playbook must match row.request_playbook")
    for field_name in (
        "resource_contract_ids",
        "request_contract_fields",
        "response_contract_fields",
    ):
        observed = _str_tuple(row.get(field_name, []))
        payload_observed = _str_tuple(request_payload.get(field_name, []))
        if not observed:
            errors.append(f"{field_name} must be non-empty")
        if set(payload_observed) != set(observed):
            errors.append(
                f"request_payload.{field_name} must match row.{field_name}"
            )
    return tuple(errors)


def _resource_request_payload_identity_errors(row: dict[str, Any]) -> tuple[str, ...]:
    request_payload = row.get("request_payload", {})
    if not isinstance(request_payload, dict):
        return ("request_payload must be object",)
    errors: list[str] = []
    for field_name in (
        "resource_request_id",
        "action_resource_plan_id",
        "primitive_action_id",
        "coverage_map_id",
        "goal_plan_id",
        "route_id",
        "primitive",
        "coverage_bucket",
        "queue_action_kind",
        "target_prover_family",
        "library_snapshot_ref",
        "resource_id",
        "request_phase",
        "expected_response_artifact",
    ):
        if request_payload.get(field_name) != row.get(field_name):
            errors.append(f"request_payload.{field_name} must match row.{field_name}")
    if request_payload.get("request_rank") != row.get("request_rank"):
        errors.append("request_payload.request_rank must match row.request_rank")
    return tuple(errors)


def _resource_request_dispatch_spec_errors(row: dict[str, Any]) -> tuple[str, ...]:
    dispatch_spec = row.get("dispatch_spec", {})
    if not isinstance(dispatch_spec, dict):
        return ("dispatch_spec must be object",)
    request_payload = row.get("request_payload", {})
    payload_dispatch_spec = (
        request_payload.get("dispatch_spec")
        if isinstance(request_payload, dict)
        else None
    )
    errors: list[str] = []
    expected_values = {
        "resource_id": str(row.get("resource_id", "")),
        "request_phase": str(row.get("request_phase", "")),
        "target_prover_family": str(row.get("target_prover_family", "")),
        "execution_command": str(row.get("execution_command", "")),
        "mcp_or_cli_hint": str(row.get("mcp_or_cli_hint", "")),
        "expected_response_artifact": str(row.get("expected_response_artifact", "")),
        "response_jsonl_contract": "formalization_gap_planner_resource_responses.jsonl",
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY_RESOURCE_REQUEST,
        "dispatch_kind": _resource_request_dispatch_kind(
            str(row.get("resource_id", "")),
            str(row.get("request_phase", "")),
        ),
        "adapter_surface": _resource_request_adapter_surface(
            str(row.get("resource_id", "")),
            str(row.get("request_phase", "")),
        ),
    }
    for field_name, expected in expected_values.items():
        if dispatch_spec.get(field_name) != expected:
            errors.append(f"dispatch_spec.{field_name} mismatch")
    if not isinstance(payload_dispatch_spec, dict):
        errors.append("request_payload.dispatch_spec must be object")
    elif payload_dispatch_spec != dispatch_spec:
        errors.append("request_payload.dispatch_spec must match row.dispatch_spec")
    return tuple(errors)


PROOF_EVIDENCE_BOUNDARY_RESOURCE_REQUEST = (
    "Formalization gap planner resource-request queue rows are executable "
    "dispatch packets for local-first resources, frontier MCP or CLI tools, "
    "and prover feedback adapters. They record what evidence should be "
    "requested and how responses should be accepted, but they are not "
    "theorem proof evidence."
)


def _resource_request_dispatch_kind(resource_id: str, phase: str) -> str:
    resource = resource_id.lower()
    if phase == "local_first":
        return "local_cli"
    if "mcp" in resource or any(
        token in resource
        for token in (
            "lsp",
            "loogle",
            "leansearch",
            "leanexplore",
            "paperclip",
            "serapi",
            "sledgehammer",
            "agda",
        )
    ):
        return "frontier_mcp_or_cli"
    if any(token in resource for token in ("paperqa", "openscholar", "semantic")):
        return "frontier_literature_service"
    if any(token in resource for token in ("agentic", "reprover", "dependency_graph")):
        return "frontier_prover_orchestration"
    return "resource_specific_adapter"


def _resource_request_adapter_surface(resource_id: str, phase: str) -> str:
    if phase == "local_first":
        return "ai_statistician_cli"
    resource = resource_id.lower()
    if "paperclip" in resource:
        return "paperclip_mcp_cli"
    if "paperqa" in resource:
        return "paperqa_api_or_cli"
    if "openscholar" in resource or "semantic" in resource:
        return "openscholar_semantic_scholar_api"
    if "loogle" in resource:
        return "loogle_api"
    if "leansearch" in resource:
        return "leansearch_api"
    if "leanexplore" in resource:
        return "leanexplore_mcp"
    if "serapi" in resource:
        return "rocq_serapi"
    if "lsp" in resource:
        return "target_prover_lsp_mcp"
    if "sledgehammer" in resource:
        return "isabelle_sledgehammer"
    if "agda" in resource:
        return "agda_search_or_automation"
    if "reprover" in resource:
        return "reprover_or_leandojo"
    if "agentic" in resource:
        return "agentic_prover_service"
    return "resource_specific_adapter"


def _resource_map_values(
    action_row: dict[str, Any],
    map_field_name: str,
    resource_id: str,
) -> tuple[str, ...]:
    value = action_row.get(map_field_name, {})
    if not isinstance(value, dict):
        return tuple()
    return _str_tuple(value.get(resource_id, []))


def _resource_response_ledger_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = (
        bundle_dir / "artifacts" / "formalization_gap_planner_resource_response_ledger"
    )
    manifest_path = (
        artifact_dir
        / "formalization_gap_planner_resource_response_ledger_manifest.json"
    )
    rows_jsonl_path = (
        artifact_dir / "formalization_gap_planner_resource_response_ledger.jsonl"
    )
    response_schema_path = (
        artifact_dir / "formalization_gap_planner_resource_response.schema.json"
    )
    row_schema_path = (
        artifact_dir
        / "formalization_gap_planner_resource_response_ledger_row.schema.json"
    )
    request_rows_jsonl_path = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_resource_request_queue"
        / "formalization_gap_planner_resource_request_queue.jsonl"
    )
    manifest = _read_json_no_error(manifest_path)
    response_schema = _read_json_no_error(response_schema_path)
    row_schema = _read_json_no_error(row_schema_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    request_rows, request_row_errors = _read_jsonl_dict_rows_no_error(
        request_rows_jsonl_path
    )
    request_index = _resource_request_queue_index(request_rows)
    checks = [
        _check(
            "optional_resource_response_schema_file",
            "optional_artifacts",
            "optional resource response schema exists",
            str(response_schema_path.exists()),
            response_schema_path.exists(),
        ),
        _check(
            "optional_resource_response_schema_id",
            "optional_artifacts",
            RESOURCE_RESPONSE_SCHEMA_ID,
            str(response_schema.get("$id", "")),
            response_schema.get("$id") == RESOURCE_RESPONSE_SCHEMA_ID,
        ),
        _check(
            "optional_resource_response_ledger_row_schema_file",
            "optional_artifacts",
            "optional resource response-ledger row schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            "optional_resource_response_ledger_row_schema_id",
            "optional_artifacts",
            RESOURCE_RESPONSE_LEDGER_ROW_SCHEMA_ID,
            str(row_schema.get("$id", "")),
            row_schema.get("$id") == RESOURCE_RESPONSE_LEDGER_ROW_SCHEMA_ID,
        ),
        _check(
            "optional_resource_response_ledger_manifest_schema_valid_count",
            "optional_artifacts",
            "resource response-ledger manifest row schema-valid count matches ledger-row count",
            (
                f"{manifest.get('n_ledger_row_schema_valid', 0)}/"
                f"{manifest.get('n_ledger_rows', 0)}; "
                f"invalid={manifest.get('n_ledger_row_schema_invalid', 0)}"
            ),
            int(manifest.get("n_ledger_rows", 0) or 0) > 0
            and int(manifest.get("n_ledger_row_schema_valid", 0) or 0)
            == int(manifest.get("n_ledger_rows", 0) or 0)
            and int(manifest.get("n_ledger_row_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_resource_response_ledger_jsonl_parse",
            "optional_artifacts",
            "resource response-ledger JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_resource_response_ledger_jsonl_row_count",
            "optional_artifacts",
            "resource response-ledger JSONL rows match manifest ledger-row count",
            f"jsonl={len(rows)} manifest={manifest.get('n_ledger_rows', 0)}",
            len(rows) == int(manifest.get("n_ledger_rows", 0) or 0),
        ),
        _check(
            "optional_resource_response_ledger_request_queue_jsonl_parse",
            "optional_artifacts",
            "bundled resource request-queue JSONL parses for ledger alignment",
            (
                "; ".join(request_row_errors)
                if request_row_errors
                else f"rows={len(request_rows)}"
            ),
            not request_row_errors and bool(request_rows),
            errors=request_row_errors,
        ),
    ]
    for idx, row in enumerate(rows):
        schema_errors = validate_resource_response_ledger_row(row)
        resource_request_id = str(row.get("resource_request_id", ""))
        request_row = request_index.get(resource_request_id)
        accounting_errors = _resource_response_contract_field_accounting_errors(
            row,
            request_row,
        )
        checks.append(
            _check(
                f"optional_resource_response_ledger_row_{idx}_schema_valid",
                "optional_artifacts",
                "resource response-ledger row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
        checks.append(
            _check(
                f"optional_resource_response_ledger_row_{idx}_request_ref",
                "optional_artifacts",
                "resource response-ledger row resolves to a bundled resource request",
                resource_request_id,
                request_row is not None,
                errors=()
                if request_row is not None
                else (
                    "missing bundled resource request: "
                    + resource_request_id,
                ),
            )
        )
        checks.append(
            _check(
                f"optional_resource_response_ledger_row_{idx}_contract_field_accounting",
                "optional_artifacts",
                "matched and missing response fields account for the request contract",
                "; ".join(accounting_errors) if accounting_errors else "ok",
                not accounting_errors,
                errors=accounting_errors,
            )
        )
    return checks


def _resource_request_queue_index(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("resource_request_id", "")): row
        for row in rows
        if row.get("resource_request_id")
    }


def _resource_response_contract_field_accounting_errors(
    row: dict[str, Any],
    request_row: dict[str, Any] | None,
) -> tuple[str, ...]:
    if request_row is None:
        return ("resource response-ledger resource_request_id does not resolve",)
    errors: list[str] = []
    field_comparisons = (
        "action_resource_plan_id",
        "primitive_action_id",
        "coverage_map_id",
        "goal_plan_id",
        "route_id",
        "resource_id",
        "expected_response_artifact",
    )
    for field_name in field_comparisons:
        observed = str(row.get(field_name, ""))
        expected = str(request_row.get(field_name, ""))
        if observed != expected:
            errors.append(
                f"{field_name} mismatch: observed={observed!r} expected={expected!r}"
            )
    if _dict_value(row, "dispatch_spec") != _dict_value(request_row, "dispatch_spec"):
        errors.append("dispatch_spec mismatch between ledger row and request row")
    if _candidate_declaration_rows(
        row.get("candidate_declaration_rows", [])
    ) != _candidate_declaration_rows(request_row.get("candidate_declaration_rows", [])):
        errors.append(
            "candidate_declaration_rows mismatch between ledger row and request row"
        )
    if set(_str_tuple(row.get("actionable_work_items", []))) != set(
        _str_tuple(request_row.get("actionable_work_items", []))
    ):
        errors.append(
            "actionable_work_items mismatch between ledger row and request row"
        )
    errors.extend(_resource_response_scope_errors(row, request_row))
    expected_fields = set(_str_tuple(request_row.get("response_contract_fields", [])))
    row_response_contract_fields = set(
        _str_tuple(row.get("response_contract_fields", []))
    )
    matched_fields = set(_str_tuple(row.get("matched_response_contract_fields", [])))
    missing_fields = set(_str_tuple(row.get("missing_response_contract_fields", [])))
    accounted_fields = matched_fields | missing_fields
    overlap = matched_fields & missing_fields
    response_contract_minimum_met = bool(row.get("response_contract_minimum_met", False))
    response_contract_ok = bool(row.get("response_contract_ok", False))
    request_playbook_present = bool(row.get("request_playbook_present", False))
    response_playbook_grounded = bool(row.get("response_playbook_grounded", False))
    acceptance_status = str(row.get("acceptance_status", ""))
    if row_response_contract_fields and row_response_contract_fields != expected_fields:
        errors.append(
            "ledger response_contract_fields mismatch request: "
            f"observed={sorted(row_response_contract_fields)} "
            f"expected={sorted(expected_fields)}"
        )
    if accounted_fields != expected_fields:
        errors.append(
            "response contract field accounting mismatch: "
            f"accounted={sorted(accounted_fields)} expected={sorted(expected_fields)}"
        )
    if overlap:
        errors.append(
            "response contract fields are both matched and missing: "
            + ",".join(sorted(overlap))
        )
    if response_contract_minimum_met != bool(matched_fields):
        errors.append(
            "response_contract_minimum_met must equal whether matched contract fields are non-empty"
        )
    if response_contract_ok and not response_contract_minimum_met:
        errors.append("response_contract_ok requires response_contract_minimum_met")
    if (
        response_contract_ok
        and request_playbook_present
        and not response_playbook_grounded
    ):
        errors.append(
            "response_contract_ok requires response_playbook_grounded when request_playbook_present"
        )
    if acceptance_status.startswith("ACCEPTED_") and not response_contract_minimum_met:
        errors.append("accepted resource response requires response_contract_minimum_met")
    if (
        acceptance_status.startswith("ACCEPTED_")
        and request_playbook_present
        and not response_playbook_grounded
    ):
        errors.append(
            "accepted resource response requires response_playbook_grounded when request_playbook_present"
        )
    return tuple(errors)


def _resource_response_scope_errors(
    row: dict[str, Any],
    request_row: dict[str, Any],
) -> tuple[str, ...]:
    allowed = set(_resource_request_target_primitives(request_row))
    if not allowed:
        return tuple()
    errors: list[str] = []
    payload = _dict_value(row, "response_payload")
    row_target_primitives = set(_str_tuple(row.get("target_primitives", [])))
    payload_target_primitives = set(_str_tuple(payload.get("target_primitives", [])))
    expanded_targets = sorted(
        (row_target_primitives | payload_target_primitives) - allowed
    )
    if expanded_targets:
        errors.append(
            "target_primitives must not expand beyond resource request target_primitives: "
            + ", ".join(expanded_targets[:8])
        )
    coverage_primitives = set(_str_tuple(list(_dict_value(row, "coverage_updates").keys())))
    coverage_primitives.update(
        _str_tuple(list(_dict_value(payload, "coverage_updates").keys()))
    )
    errors.extend(
        _resource_response_primitive_scope_errors(
            "coverage_updates",
            coverage_primitives,
            allowed,
        )
    )
    for field_name in ("revised_selected_primitives", "revised_delta_primitives"):
        observed_primitives = set(_str_tuple(row.get(field_name, [])))
        observed_primitives.update(_str_tuple(payload.get(field_name, [])))
        errors.extend(
            _resource_response_primitive_scope_errors(
                field_name,
                observed_primitives,
                allowed,
            )
        )
    for field_name in (
        "route_evidence_nodes",
        "source_snippets",
        "formal_declaration_hits",
        "lean_declaration_hits",
    ):
        field_rows = [
            *_dict_tuple(row.get(field_name, [])),
            *_dict_tuple(payload.get(field_name, [])),
        ]
        for index, evidence_row in enumerate(field_rows):
            errors.extend(
                _resource_response_primitive_scope_errors(
                    f"{field_name}[{index}]",
                    set(_resource_response_evidence_row_primitives(evidence_row)),
                    allowed,
                )
            )
    return tuple(errors)


def _resource_request_target_primitives(
    request_row: dict[str, Any],
) -> tuple[str, ...]:
    primitive = str(request_row.get("primitive", "")).strip()
    return _str_tuple(
        [
            *_str_tuple(request_row.get("target_primitives", [])),
            *([primitive] if primitive else []),
        ]
    )


def _resource_response_evidence_row_primitives(
    row: dict[str, Any],
) -> tuple[str, ...]:
    return _str_tuple(
        [
            str(row.get("primitive", "") or ""),
            *_str_tuple(row.get("target_primitives", [])),
        ]
    )


def _resource_response_primitive_scope_errors(
    field_name: str,
    observed_primitives: set[str],
    allowed_primitives: set[str],
) -> tuple[str, ...]:
    expanded = sorted(observed_primitives - allowed_primitives)
    if not expanded:
        return tuple()
    return (
        f"{field_name} primitives must not expand beyond resource request "
        "target_primitives: "
        + ", ".join(expanded[:8]),
    )


def _portable_plan_audit_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = bundle_dir / "artifacts" / "formalization_gap_planner_portable_plan_audit"
    manifest_path = artifact_dir / "formalization_gap_planner_portable_plan_audit_manifest.json"
    rows_jsonl_path = artifact_dir / "formalization_gap_planner_portable_plan_audit.jsonl"
    row_schema_path = (
        artifact_dir / "formalization_gap_planner_portable_plan_audit_row.schema.json"
    )
    manifest = _read_json_no_error(manifest_path)
    row_schema = _read_json_no_error(row_schema_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    checks = [
        _check(
            "optional_portable_plan_audit_row_schema_file",
            "optional_artifacts",
            "optional portable-plan audit row schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            "optional_portable_plan_audit_row_schema_id",
            "optional_artifacts",
            PORTABLE_PLAN_AUDIT_ROW_SCHEMA_ID,
            str(row_schema.get("$id", "")),
            row_schema.get("$id") == PORTABLE_PLAN_AUDIT_ROW_SCHEMA_ID,
        ),
        _check(
            "optional_portable_plan_audit_manifest_schema_valid_count",
            "optional_artifacts",
            "portable-plan audit manifest row schema-valid count matches check count",
            (
                f"{manifest.get('n_row_schema_valid', 0)}/"
                f"{manifest.get('n_checks', 0)}; "
                f"invalid={manifest.get('n_row_schema_invalid', 0)}"
            ),
            int(manifest.get("n_checks", 0) or 0) > 0
            and int(manifest.get("n_row_schema_valid", 0) or 0)
            == int(manifest.get("n_checks", 0) or 0)
            and int(manifest.get("n_row_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_portable_plan_audit_jsonl_parse",
            "optional_artifacts",
            "portable-plan audit JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_portable_plan_audit_jsonl_row_count",
            "optional_artifacts",
            "portable-plan audit JSONL rows match manifest check count",
            f"jsonl={len(rows)} manifest={manifest.get('n_checks', 0)}",
            len(rows) == int(manifest.get("n_checks", 0) or 0),
        ),
    ]
    for idx, row in enumerate(rows):
        schema_errors = validate_portable_plan_audit_row(row)
        checks.append(
            _check(
                f"optional_portable_plan_audit_row_{idx}_schema_valid",
                "optional_artifacts",
                "portable-plan audit row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
    return checks


def _refinement_adapter_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = bundle_dir / "artifacts" / "formalization_gap_planner_refinement_adapter"
    manifest_path = artifact_dir / "formalization_gap_planner_refinement_adapter_manifest.json"
    rows_jsonl_path = artifact_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl"
    response_schema_path = (
        artifact_dir / "formalization_gap_planner_refinement_tool_response.schema.json"
    )
    manifest = _read_json_no_error(manifest_path)
    response_schema = _read_json_no_error(response_schema_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    checks = [
        _check(
            "optional_refinement_adapter_response_schema_file",
            "optional_artifacts",
            "optional refinement adapter response schema exists",
            str(response_schema_path.exists()),
            response_schema_path.exists(),
        ),
        _check(
            "optional_refinement_adapter_response_schema_id",
            "optional_artifacts",
            "urn:ai-statistician:schemas:formalization-gap-planner-refinement-tool-response:1",
            str(response_schema.get("$id", "")),
            response_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-refinement-tool-response:1",
        ),
        _check(
            "optional_refinement_adapter_manifest_schema_valid_count",
            "optional_artifacts",
            "refinement adapter manifest response schema-valid count matches response count",
            (
                f"{manifest.get('n_response_schema_valid', 0)}/"
                f"{manifest.get('n_responses', 0)}; "
                f"invalid={manifest.get('n_response_schema_invalid', 0)}"
            ),
            int(manifest.get("n_responses", 0) or 0) > 0
            and int(manifest.get("n_response_schema_valid", 0) or 0)
            == int(manifest.get("n_responses", 0) or 0)
            and int(manifest.get("n_response_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_refinement_adapter_jsonl_parse",
            "optional_artifacts",
            "refinement adapter response JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_refinement_adapter_jsonl_row_count",
            "optional_artifacts",
            "refinement adapter response JSONL rows match manifest response count",
            f"jsonl={len(rows)} manifest={manifest.get('n_responses', 0)}",
            len(rows) == int(manifest.get("n_responses", 0) or 0),
        ),
    ]
    for idx, row in enumerate(rows):
        schema_errors = validate_refinement_tool_response_row(row)
        checks.append(
            _check(
                f"optional_refinement_adapter_response_row_{idx}_schema_valid",
                "optional_artifacts",
                "refinement adapter response row satisfies published refinement-tool schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
    return checks


def _local_adapter_optional_checks(
    bundle_dir: Path,
    artifact_name: str,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    local_count_fields = {
        "formalization_gap_planner_local_literature_adapter": (
            "n_local_literature_responses"
        ),
        "formalization_gap_planner_local_formal_source_adapter": (
            "n_local_formal_source_responses"
        ),
        "formalization_gap_planner_local_proof_state_adapter": (
            "n_local_proof_state_responses"
        ),
    }
    local_count_field = local_count_fields.get(artifact_name, "n_local_responses")
    artifact_dir = bundle_dir / "artifacts" / artifact_name
    slug = artifact_name.replace("formalization_gap_planner_", "")
    manifest_path = artifact_dir / f"{artifact_name}_manifest.json"
    local_rows_jsonl_path = artifact_dir / f"{artifact_name}_responses.jsonl"
    merged_rows_jsonl_path = (
        artifact_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl"
    )
    response_schema_path = (
        artifact_dir / "formalization_gap_planner_refinement_tool_response.schema.json"
    )
    manifest = _read_json_no_error(manifest_path)
    response_schema = _read_json_no_error(response_schema_path)
    local_rows, local_row_errors = _read_jsonl_dict_rows_no_error(local_rows_jsonl_path)
    merged_rows, merged_row_errors = _read_jsonl_dict_rows_no_error(
        merged_rows_jsonl_path
    )
    checks = [
        _check(
            f"optional_{slug}_response_schema_file",
            "optional_artifacts",
            "optional local adapter response schema exists",
            str(response_schema_path.exists()),
            response_schema_path.exists(),
        ),
        _check(
            f"optional_{slug}_response_schema_id",
            "optional_artifacts",
            "urn:ai-statistician:schemas:formalization-gap-planner-refinement-tool-response:1",
            str(response_schema.get("$id", "")),
            response_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-refinement-tool-response:1",
        ),
        _check(
            f"optional_{slug}_local_manifest_schema_valid_count",
            "optional_artifacts",
            "local adapter manifest local response schema-valid count matches local response count",
            (
                f"{manifest.get('n_local_response_schema_valid', 0)}/"
                f"{manifest.get(local_count_field, 0)}; "
                f"invalid={manifest.get('n_local_response_schema_invalid', 0)}"
            ),
            int(manifest.get("n_local_response_schema_valid", 0) or 0)
            == int(manifest.get(local_count_field, 0) or 0)
            and int(manifest.get("n_local_response_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            f"optional_{slug}_merged_manifest_schema_valid_count",
            "optional_artifacts",
            "local adapter manifest merged response schema-valid count matches merged response count",
            (
                f"{manifest.get('n_merged_response_schema_valid', 0)}/"
                f"{manifest.get('n_merged_responses', 0)}; "
                f"invalid={manifest.get('n_merged_response_schema_invalid', 0)}"
            ),
            int(manifest.get("n_merged_response_schema_valid", 0) or 0)
            == int(manifest.get("n_merged_responses", 0) or 0)
            and int(manifest.get("n_merged_response_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            f"optional_{slug}_local_jsonl_parse",
            "optional_artifacts",
            "local adapter response JSONL parses into object rows",
            "; ".join(local_row_errors) if local_row_errors else f"rows={len(local_rows)}",
            not local_row_errors,
            errors=local_row_errors,
        ),
        _check(
            f"optional_{slug}_local_jsonl_row_count",
            "optional_artifacts",
            "local adapter response JSONL rows match manifest local response count",
            f"jsonl={len(local_rows)} manifest={manifest.get(local_count_field, 0)}",
            len(local_rows) == int(manifest.get(local_count_field, 0) or 0),
        ),
        _check(
            f"optional_{slug}_merged_jsonl_parse",
            "optional_artifacts",
            "local adapter merged response JSONL parses into object rows",
            "; ".join(merged_row_errors)
            if merged_row_errors
            else f"rows={len(merged_rows)}",
            not merged_row_errors,
            errors=merged_row_errors,
        ),
        _check(
            f"optional_{slug}_merged_jsonl_row_count",
            "optional_artifacts",
            "local adapter merged response JSONL rows match manifest merged response count",
            f"jsonl={len(merged_rows)} manifest={manifest.get('n_merged_responses', 0)}",
            len(merged_rows) == int(manifest.get("n_merged_responses", 0) or 0),
        ),
    ]
    if artifact_name == "formalization_gap_planner_local_formal_source_adapter":
        n_local_rows_with_lean_alias = sum(
            1 for row in local_rows if _dict_tuple(row.get("lean_declaration_hits", []))
        )
        checks.extend(
            [
                _check(
                    "optional_local_formal_source_adapter_legacy_alias_contract",
                    "optional_artifacts",
                    "local formal-source adapter manifest publishes Lean declaration-hit legacy alias contract",
                    str(manifest.get("legacy_formal_source_adapter_field_aliases", {})),
                    manifest.get("legacy_formal_source_adapter_field_aliases")
                    == LEGACY_FORMAL_SOURCE_ADAPTER_FIELD_ALIASES,
                ),
                _check(
                    "optional_local_formal_source_adapter_legacy_alias_count",
                    "optional_artifacts",
                    "local formal-source adapter manifest Lean-alias response count matches local rows",
                    (
                        "manifest="
                        f"{manifest.get('n_responses_with_legacy_lean_declaration_hits', 0)} "
                        f"jsonl={n_local_rows_with_lean_alias}"
                    ),
                    int(
                        manifest.get(
                            "n_responses_with_legacy_lean_declaration_hits",
                            0,
                        )
                        or 0
                    )
                    == n_local_rows_with_lean_alias,
                ),
            ]
        )
    for scope, rows in (("local", local_rows), ("merged", merged_rows)):
        for idx, row in enumerate(rows):
            schema_errors = validate_refinement_tool_response_row(row)
            checks.append(
                _check(
                    f"optional_local_adapter_response_{slug}_{scope}_row_{idx}_schema_valid",
                    "optional_artifacts",
                    "local adapter response row satisfies published refinement-tool schema",
                    "; ".join(schema_errors) if schema_errors else "ok",
                    not schema_errors,
                    errors=schema_errors,
                )
            )
    return checks


def _minimal_delta_audit_feedback_adapter_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_minimal_delta_audit_feedback_adapter"
    )
    manifest_path = (
        artifact_dir
        / "formalization_gap_planner_minimal_delta_audit_feedback_adapter_manifest.json"
    )
    generated_rows_jsonl_path = (
        artifact_dir
        / "formalization_gap_planner_minimal_delta_audit_feedback_responses.jsonl"
    )
    merged_rows_jsonl_path = (
        artifact_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl"
    )
    response_schema_path = (
        artifact_dir / "formalization_gap_planner_refinement_tool_response.schema.json"
    )
    manifest = _read_json_no_error(manifest_path)
    response_schema = _read_json_no_error(response_schema_path)
    generated_rows, generated_row_errors = _read_jsonl_dict_rows_no_error(
        generated_rows_jsonl_path
    )
    merged_rows, merged_row_errors = _read_jsonl_dict_rows_no_error(
        merged_rows_jsonl_path
    )
    checks = [
        _check(
            "optional_minimal_delta_audit_feedback_response_schema_file",
            "optional_artifacts",
            "optional minimal-delta audit feedback response schema exists",
            str(response_schema_path.exists()),
            response_schema_path.exists(),
        ),
        _check(
            "optional_minimal_delta_audit_feedback_response_schema_id",
            "optional_artifacts",
            "urn:ai-statistician:schemas:formalization-gap-planner-refinement-tool-response:1",
            str(response_schema.get("$id", "")),
            response_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-refinement-tool-response:1",
        ),
        _check(
            "optional_minimal_delta_audit_feedback_generated_manifest_schema_valid_count",
            "optional_artifacts",
            "minimal-delta audit feedback manifest generated response schema-valid count matches generated response count",
            (
                f"{manifest.get('n_response_schema_valid', 0)}/"
                f"{manifest.get('n_generated_feedback_responses', 0)}; "
                f"invalid={manifest.get('n_response_schema_invalid', 0)}"
            ),
            int(manifest.get("n_response_schema_valid", 0) or 0)
            == int(manifest.get("n_generated_feedback_responses", 0) or 0)
            and int(manifest.get("n_response_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_minimal_delta_audit_feedback_merged_manifest_schema_valid_count",
            "optional_artifacts",
            "minimal-delta audit feedback manifest merged response schema-valid count matches merged response count",
            (
                f"{manifest.get('n_merged_response_schema_valid', 0)}/"
                f"{manifest.get('n_merged_responses', 0)}; "
                f"invalid={manifest.get('n_merged_response_schema_invalid', 0)}"
            ),
            int(manifest.get("n_merged_response_schema_valid", 0) or 0)
            == int(manifest.get("n_merged_responses", 0) or 0)
            and int(manifest.get("n_merged_response_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_minimal_delta_audit_feedback_generated_jsonl_parse",
            "optional_artifacts",
            "minimal-delta audit feedback generated response JSONL parses into object rows",
            "; ".join(generated_row_errors)
            if generated_row_errors
            else f"rows={len(generated_rows)}",
            not generated_row_errors,
            errors=generated_row_errors,
        ),
        _check(
            "optional_minimal_delta_audit_feedback_generated_jsonl_row_count",
            "optional_artifacts",
            "minimal-delta audit feedback generated response JSONL rows match manifest generated response count",
            (
                f"jsonl={len(generated_rows)} "
                f"manifest={manifest.get('n_generated_feedback_responses', 0)}"
            ),
            len(generated_rows)
            == int(manifest.get("n_generated_feedback_responses", 0) or 0),
        ),
        _check(
            "optional_minimal_delta_audit_feedback_merged_jsonl_parse",
            "optional_artifacts",
            "minimal-delta audit feedback merged response JSONL parses into object rows",
            "; ".join(merged_row_errors)
            if merged_row_errors
            else f"rows={len(merged_rows)}",
            not merged_row_errors,
            errors=merged_row_errors,
        ),
        _check(
            "optional_minimal_delta_audit_feedback_merged_jsonl_row_count",
            "optional_artifacts",
            "minimal-delta audit feedback merged response JSONL rows match manifest merged response count",
            f"jsonl={len(merged_rows)} manifest={manifest.get('n_merged_responses', 0)}",
            len(merged_rows) == int(manifest.get("n_merged_responses", 0) or 0),
        ),
    ]
    for scope, rows in (("generated", generated_rows), ("merged", merged_rows)):
        for idx, row in enumerate(rows):
            schema_errors = validate_refinement_tool_response_row(row)
            checks.append(
                _check(
                    f"optional_minimal_delta_audit_feedback_response_{scope}_row_{idx}_schema_valid",
                    "optional_artifacts",
                    "minimal-delta audit feedback response row satisfies published refinement-tool schema",
                    "; ".join(schema_errors) if schema_errors else "ok",
                    not schema_errors,
                    errors=schema_errors,
                )
            )
    return checks


def _prover_adapter_feedback_adapter_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_prover_adapter_feedback_adapter"
    )
    manifest_path = (
        artifact_dir
        / "formalization_gap_planner_prover_adapter_feedback_adapter_manifest.json"
    )
    generated_rows_jsonl_path = (
        artifact_dir / "formalization_gap_planner_prover_adapter_feedback_responses.jsonl"
    )
    merged_rows_jsonl_path = (
        artifact_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl"
    )
    response_schema_path = (
        artifact_dir / "formalization_gap_planner_refinement_tool_response.schema.json"
    )
    manifest = _read_json_no_error(manifest_path)
    response_schema = _read_json_no_error(response_schema_path)
    generated_rows, generated_row_errors = _read_jsonl_dict_rows_no_error(
        generated_rows_jsonl_path
    )
    merged_rows, merged_row_errors = _read_jsonl_dict_rows_no_error(
        merged_rows_jsonl_path
    )
    checks = [
        _check(
            "optional_prover_adapter_feedback_response_schema_file",
            "optional_artifacts",
            "optional prover-adapter feedback response schema exists",
            str(response_schema_path.exists()),
            response_schema_path.exists(),
        ),
        _check(
            "optional_prover_adapter_feedback_response_schema_id",
            "optional_artifacts",
            "urn:ai-statistician:schemas:formalization-gap-planner-refinement-tool-response:1",
            str(response_schema.get("$id", "")),
            response_schema.get("$id")
            == "urn:ai-statistician:schemas:formalization-gap-planner-refinement-tool-response:1",
        ),
        _check(
            "optional_prover_adapter_feedback_generated_manifest_schema_valid_count",
            "optional_artifacts",
            "prover-adapter feedback manifest generated response schema-valid count matches generated response count",
            (
                f"{manifest.get('n_response_schema_valid', 0)}/"
                f"{manifest.get('n_generated_feedback_responses', 0)}; "
                f"invalid={manifest.get('n_response_schema_invalid', 0)}"
            ),
            int(manifest.get("n_generated_feedback_responses", 0) or 0) > 0
            and int(manifest.get("n_response_schema_valid", 0) or 0)
            == int(manifest.get("n_generated_feedback_responses", 0) or 0)
            and int(manifest.get("n_response_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_prover_adapter_feedback_merged_manifest_schema_valid_count",
            "optional_artifacts",
            "prover-adapter feedback manifest merged response schema-valid count matches merged response count",
            (
                f"{manifest.get('n_merged_response_schema_valid', 0)}/"
                f"{manifest.get('n_merged_responses', 0)}; "
                f"invalid={manifest.get('n_merged_response_schema_invalid', 0)}"
            ),
            int(manifest.get("n_merged_responses", 0) or 0) > 0
            and int(manifest.get("n_merged_response_schema_valid", 0) or 0)
            == int(manifest.get("n_merged_responses", 0) or 0)
            and int(manifest.get("n_merged_response_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_prover_adapter_feedback_generated_jsonl_parse",
            "optional_artifacts",
            "prover-adapter feedback generated response JSONL parses into object rows",
            "; ".join(generated_row_errors)
            if generated_row_errors
            else f"rows={len(generated_rows)}",
            not generated_row_errors,
            errors=generated_row_errors,
        ),
        _check(
            "optional_prover_adapter_feedback_generated_jsonl_row_count",
            "optional_artifacts",
            "prover-adapter feedback generated response JSONL rows match manifest generated response count",
            (
                f"jsonl={len(generated_rows)} "
                f"manifest={manifest.get('n_generated_feedback_responses', 0)}"
            ),
            len(generated_rows)
            == int(manifest.get("n_generated_feedback_responses", 0) or 0),
        ),
        _check(
            "optional_prover_adapter_feedback_merged_jsonl_parse",
            "optional_artifacts",
            "prover-adapter feedback merged response JSONL parses into object rows",
            "; ".join(merged_row_errors)
            if merged_row_errors
            else f"rows={len(merged_rows)}",
            not merged_row_errors,
            errors=merged_row_errors,
        ),
        _check(
            "optional_prover_adapter_feedback_merged_jsonl_row_count",
            "optional_artifacts",
            "prover-adapter feedback merged response JSONL rows match manifest merged response count",
            f"jsonl={len(merged_rows)} manifest={manifest.get('n_merged_responses', 0)}",
            len(merged_rows) == int(manifest.get("n_merged_responses", 0) or 0),
        ),
    ]
    for scope, rows in (("generated", generated_rows), ("merged", merged_rows)):
        for idx, row in enumerate(rows):
            schema_errors = validate_refinement_tool_response_row(row)
            checks.append(
                _check(
                    f"optional_prover_adapter_feedback_response_{scope}_row_{idx}_schema_valid",
                    "optional_artifacts",
                    "prover-adapter feedback response row satisfies published refinement-tool schema",
                    "; ".join(schema_errors) if schema_errors else "ok",
                    not schema_errors,
                    errors=schema_errors,
                )
            )
    return checks


def _ablation_study_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = bundle_dir / "artifacts" / "formalization_gap_planner_ablation_study"
    manifest_path = artifact_dir / "formalization_gap_planner_ablation_study_manifest.json"
    rows_jsonl_path = artifact_dir / "formalization_gap_planner_ablation_study.jsonl"
    row_schema_path = artifact_dir / "formalization_gap_planner_ablation_study_row.schema.json"
    manifest = _read_json_no_error(manifest_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    checks = [
        _check(
            "optional_ablation_study_row_schema_file",
            "optional_artifacts",
            "optional ablation study row schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            "optional_ablation_study_manifest_schema_valid_count",
            "optional_artifacts",
            "ablation study manifest schema-valid count matches row count",
            (
                f"{manifest.get('n_row_schema_valid', 0)}/"
                f"{manifest.get('n_ablation_variants', 0)}; "
                f"invalid={manifest.get('n_row_schema_invalid', 0)}"
            ),
            int(manifest.get("n_ablation_variants", 0) or 0) > 0
            and int(manifest.get("n_row_schema_valid", 0) or 0)
            == int(manifest.get("n_ablation_variants", 0) or 0)
            and int(manifest.get("n_row_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_ablation_study_jsonl_parse",
            "optional_artifacts",
            "ablation study JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_ablation_study_jsonl_row_count",
            "optional_artifacts",
            "ablation study JSONL rows match manifest variant count",
            f"jsonl={len(rows)} manifest={manifest.get('n_ablation_variants', 0)}",
            len(rows) == int(manifest.get("n_ablation_variants", 0) or 0),
        ),
    ]
    for idx, row in enumerate(rows):
        schema_errors = validate_ablation_study_row(row)
        checks.append(
            _check(
                f"optional_ablation_study_row_{idx}_schema_valid",
                "optional_artifacts",
                "ablation study row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
    route_adoption_errors = _ablation_study_route_adoption_manifest_errors(
        manifest,
        rows,
    )
    checks.append(
        _check(
            "optional_ablation_study_route_adoption_manifest",
            "optional_artifacts",
            "ablation study manifest preserves route-adoption-ready drop aggregates",
            "; ".join(route_adoption_errors) if route_adoption_errors else "ok",
            not route_adoption_errors,
            errors=route_adoption_errors,
        )
    )
    return checks


def _route_stability_audit_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = bundle_dir / "artifacts" / "formalization_gap_planner_route_stability_audit"
    manifest_path = artifact_dir / "formalization_gap_planner_route_stability_audit_manifest.json"
    rows_jsonl_path = artifact_dir / "formalization_gap_planner_route_stability_audit.jsonl"
    row_schema_path = artifact_dir / "formalization_gap_planner_route_stability_audit_row.schema.json"
    overlay_rows_jsonl_path = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_route_revision_overlay"
        / "formalization_gap_planner_route_revision_overlay.jsonl"
    )
    manifest = _read_json_no_error(manifest_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    overlay_rows, overlay_row_errors = (
        _read_jsonl_dict_rows_no_error(overlay_rows_jsonl_path)
        if overlay_rows_jsonl_path.exists()
        else ([], tuple())
    )
    overlay_index = _route_identity_row_index(overlay_rows)
    overlay_status_present = any(
        _route_revision_row_has_resource_response_status(row) for row in overlay_rows
    )
    checks = [
        _check(
            "optional_route_stability_audit_row_schema_file",
            "optional_artifacts",
            "optional route-stability audit row schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            "optional_route_stability_audit_manifest_schema_valid_count",
            "optional_artifacts",
            "route-stability manifest schema-valid count matches row count",
            (
                f"{manifest.get('n_row_schema_valid', 0)}/"
                f"{manifest.get('n_stability_rows', 0)}; "
                f"invalid={manifest.get('n_row_schema_invalid', 0)}"
            ),
            int(manifest.get("n_stability_rows", 0) or 0) > 0
            and int(manifest.get("n_row_schema_valid", 0) or 0)
            == int(manifest.get("n_stability_rows", 0) or 0)
            and int(manifest.get("n_row_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_route_stability_audit_jsonl_parse",
            "optional_artifacts",
            "route-stability audit JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_route_stability_audit_jsonl_row_count",
            "optional_artifacts",
            "route-stability audit JSONL rows match manifest count",
            f"jsonl={len(rows)} manifest={manifest.get('n_stability_rows', 0)}",
            len(rows) == int(manifest.get("n_stability_rows", 0) or 0),
        ),
    ]
    if overlay_status_present:
        checks.append(
            _check(
                "optional_route_stability_audit_overlay_jsonl_parse",
                "optional_artifacts",
                "bundled route-revision overlay JSONL parses for stability/status consistency",
                (
                    "; ".join(overlay_row_errors)
                    if overlay_row_errors
                    else f"rows={len(overlay_rows)}"
                ),
                not overlay_row_errors and bool(overlay_rows),
                errors=overlay_row_errors,
            )
        )
    for idx, row in enumerate(rows):
        schema_errors = validate_route_stability_audit_row(row)
        overlay_row = _first_identity_match(row, overlay_index)
        status_errors = _route_stability_resource_response_status_errors(
            row,
            overlay_row,
        )
        generic_prover_errors = _route_stability_generic_prover_field_errors(row)
        checks.append(
            _check(
                f"optional_route_stability_audit_row_{idx}_schema_valid",
                "optional_artifacts",
                "route-stability audit row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
        if _route_stability_generic_prover_fields_observed(row):
            checks.append(
                _check(
                    f"optional_route_stability_audit_row_{idx}_generic_prover_fields",
                    "optional_artifacts",
                    "route-stability proof-state feedback preserves generic prover class/family fields",
                    "; ".join(generic_prover_errors) if generic_prover_errors else "ok",
                    not generic_prover_errors,
                    errors=generic_prover_errors,
                )
            )
        if overlay_status_present:
            checks.append(
                _check(
                    f"optional_route_stability_audit_row_{idx}_resource_response_status_consistency",
                    "optional_artifacts",
                    "route-stability decision reflects overlay resource-response status",
                    "; ".join(status_errors) if status_errors else "ok",
                    not status_errors,
                    errors=status_errors,
                )
            )
    return checks


def _route_revision_overlay_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = (
        bundle_dir / "artifacts" / "formalization_gap_planner_route_revision_overlay"
    )
    manifest_path = (
        artifact_dir / "formalization_gap_planner_route_revision_overlay_manifest.json"
    )
    rows_jsonl_path = artifact_dir / "formalization_gap_planner_route_revision_overlay.jsonl"
    row_schema_path = artifact_dir / "formalization_gap_planner_route_revision_overlay_row.schema.json"
    resource_response_ledger_jsonl_path = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_resource_response_ledger"
        / "formalization_gap_planner_resource_response_ledger.jsonl"
    )
    manifest = _read_json_no_error(manifest_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    resource_response_ledger_artifact_present = (
        resource_response_ledger_jsonl_path.exists()
    )
    resource_response_ledger_rows, resource_response_ledger_errors = (
        _read_jsonl_dict_rows_no_error(resource_response_ledger_jsonl_path)
        if resource_response_ledger_artifact_present
        else ([], tuple())
    )
    resource_response_ledger_index = _resource_response_ledger_index(
        resource_response_ledger_rows
    )
    resource_response_ledger_route_index = _resource_response_ledger_route_index(
        resource_response_ledger_rows
    )
    n_rows = int(manifest.get("n_overlay_rows", 0) or 0)
    n_unaligned = int(manifest.get("n_unaligned_primitives", 0) or 0)
    status_summary_manifest_present = any(
        key in manifest
        for key in (
            "n_resource_response_ledger_status_rows",
            "n_resource_response_ledger_awaiting",
            "n_resource_response_ledger_rejected",
        )
    )
    resource_ledger_hooks = sum(
        1
        for row in rows
        for hook_kind in _str_tuple(row.get("applied_hook_kinds", []))
        if hook_kind == "resource_response_ledger"
    )
    checks = [
        _check(
            "optional_route_revision_overlay_row_schema_file",
            "optional_artifacts",
            "optional route-revision overlay row schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            "optional_route_revision_overlay_manifest_schema_valid_count",
            "optional_artifacts",
            "route-revision overlay manifest schema-valid count matches row count",
            (
                f"{manifest.get('n_row_schema_valid', 0)}/"
                f"{manifest.get('n_overlay_rows', 0)}; "
                f"invalid={manifest.get('n_row_schema_invalid', 0)}"
            ),
            n_rows > 0
            and int(manifest.get("n_row_schema_valid", 0) or 0) == n_rows
            and int(manifest.get("n_row_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_route_revision_overlay_jsonl_parse",
            "optional_artifacts",
            "route-revision overlay JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_route_revision_overlay_jsonl_row_count",
            "optional_artifacts",
            "route-revision overlay JSONL rows match manifest row count",
            f"jsonl={len(rows)} manifest={n_rows}",
            len(rows) == n_rows,
        ),
        _check(
            "optional_route_revision_overlay_no_unaligned_primitives",
            "optional_artifacts",
            "route-revision overlay has zero unaligned revised primitives",
            str(n_unaligned),
            n_unaligned == 0
            and all(not row.get("unaligned_primitives") for row in rows),
        ),
        _check(
            "optional_route_revision_overlay_alignment_contract",
            "optional_artifacts",
            "every overlay row satisfies revised route-alignment contract",
            (
                f"{manifest.get('n_rows_with_alignment_contract', 0)}/"
                f"{manifest.get('n_overlay_rows', 0)}"
            ),
            n_rows > 0
            and int(manifest.get("n_rows_with_alignment_contract", 0) or 0)
            == n_rows,
        ),
        _check(
            "optional_route_revision_overlay_generic_formal_dag_fields",
            "optional_artifacts",
            "route-revision overlay publishes prover-neutral revised formal-realization DAG fields",
            _route_revision_overlay_generic_formal_dag_observed(rows, manifest),
            not _route_revision_overlay_generic_formal_dag_errors(rows, manifest),
            errors=_route_revision_overlay_generic_formal_dag_errors(rows, manifest),
        ),
        _check(
            "optional_route_revision_overlay_resource_response_ledger_proposals",
            "optional_artifacts",
            "resource-response-ledger proposal count matches applied overlay hooks",
            (
                f"hooks={resource_ledger_hooks}; "
                f"manifest={manifest.get('n_resource_response_ledger_route_revision_proposals', 0)}"
            ),
            resource_ledger_hooks
            == int(
                manifest.get("n_resource_response_ledger_route_revision_proposals", 0)
                or 0
            ),
        ),
    ]
    if resource_ledger_hooks and resource_response_ledger_artifact_present:
        checks.append(
            _check(
                "optional_route_revision_overlay_resource_response_ledger_jsonl_parse",
                "optional_artifacts",
                "bundled resource-response ledger JSONL parses for overlay provenance",
                (
                    "; ".join(resource_response_ledger_errors)
                    if resource_response_ledger_errors
                    else f"rows={len(resource_response_ledger_rows)}"
                ),
                not resource_response_ledger_errors
                and bool(resource_response_ledger_rows),
                errors=resource_response_ledger_errors,
            )
        )
    for idx, row in enumerate(rows):
        schema_errors = validate_route_revision_overlay_row(row)
        evidence_ref_errors = _route_revision_resource_response_evidence_errors(
            row,
            resource_response_ledger_index,
        )
        trace_errors = _route_revision_resource_response_trace_errors(
            row,
            resource_response_ledger_index,
        )
        status_errors = _route_revision_resource_response_status_errors(
            row,
            _matched_resource_response_ledger_route_rows(
                row,
                resource_response_ledger_route_index,
            ),
        )
        checks.append(
            _check(
                f"optional_route_revision_overlay_row_{idx}_schema_valid",
                "optional_artifacts",
                "route-revision overlay row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
        if resource_response_ledger_artifact_present and "resource_response_ledger" in _str_tuple(
            row.get("applied_hook_kinds", [])
        ):
            checks.append(
                _check(
                    f"optional_route_revision_overlay_row_{idx}_resource_response_evidence_refs",
                    "optional_artifacts",
                    "resource-response overlay evidence ids resolve to accepted ledger rows",
                    "; ".join(evidence_ref_errors) if evidence_ref_errors else "ok",
                    not evidence_ref_errors,
                    errors=evidence_ref_errors,
                )
            )
            checks.append(
                _check(
                    f"optional_route_revision_overlay_row_{idx}_resource_response_traces",
                    "optional_artifacts",
                    "resource-response traces match bundled ledger rows",
                    "; ".join(trace_errors) if trace_errors else "ok",
                    not trace_errors,
                    errors=trace_errors,
                )
            )
        if (
            resource_response_ledger_artifact_present
            and (
                status_summary_manifest_present
                or _route_revision_row_has_resource_response_status(row)
            )
        ):
            checks.append(
                _check(
                    f"optional_route_revision_overlay_row_{idx}_resource_response_status_summary",
                    "optional_artifacts",
                    "resource-response status summary matches bundled ledger rows for the route",
                    "; ".join(status_errors) if status_errors else "ok",
                    not status_errors,
                    errors=status_errors,
                )
            )
    return checks


def _resource_response_ledger_index(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("resource_response_ledger_id", "")): row
        for row in rows
        if row.get("resource_response_ledger_id")
    }


def _route_identity_row_index(
    rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        for key in _route_identity_keys(row):
            index.setdefault(key, []).append(row)
    return index


def _first_identity_match(
    row: dict[str, Any],
    index: dict[str, list[dict[str, Any]]],
) -> dict[str, Any] | None:
    seen: set[str] = set()
    matches: list[dict[str, Any]] = []
    for key in _route_identity_keys(row):
        for candidate in index.get(key, []):
            candidate_hash = stable_hash(candidate)
            if candidate_hash in seen:
                continue
            seen.add(candidate_hash)
            matches.append(candidate)
    if not matches:
        return None
    return sorted(
        matches,
        key=lambda candidate: (
            str(candidate.get("revision_status", "")) == "ORPHAN_ROUTE_REVISION_PROPOSAL",
            str(candidate.get("route_id", "")),
            str(candidate.get("goal_plan_id", "")),
            str(candidate.get("display_name", "")),
        ),
    )[0]


def _route_stability_resource_response_status_errors(
    stability_row: dict[str, Any],
    overlay_row: dict[str, Any] | None,
) -> tuple[str, ...]:
    if overlay_row is None:
        return ("route-stability row has no matching route-revision overlay row",)
    if not _route_revision_row_has_resource_response_status(overlay_row):
        return tuple()
    awaiting_ids = _str_tuple(
        overlay_row.get("resource_response_awaiting_request_ids", [])
    )
    rejected_ids = _str_tuple(
        overlay_row.get("resource_response_rejected_request_ids", [])
    )
    stability_awaiting_ids = _str_tuple(
        stability_row.get("resource_response_awaiting_request_ids", [])
    )
    stability_rejected_ids = _str_tuple(
        stability_row.get("resource_response_rejected_request_ids", [])
    )
    if not awaiting_ids and not rejected_ids:
        return tuple()
    decision = str(stability_row.get("stability_decision", ""))
    awaiting_hooks = _str_tuple(stability_row.get("awaiting_hook_kinds", []))
    rejected_hooks = _str_tuple(stability_row.get("rejected_hook_kinds", []))
    summary_by_hook = _dict_value(stability_row, "response_summary_by_hook")
    resource_summary = (
        summary_by_hook.get("resource_response_ledger", {})
        if isinstance(summary_by_hook.get("resource_response_ledger", {}), dict)
        else {}
    )
    errors: list[str] = []
    if awaiting_ids:
        if stability_awaiting_ids != awaiting_ids:
            errors.append(
                "resource_response_awaiting_request_ids mismatch: "
                + f"{stability_awaiting_ids}!={awaiting_ids}"
            )
        if decision != "AWAITING_REFINEMENT_RESPONSES":
            errors.append(
                "awaiting resource responses require AWAITING_REFINEMENT_RESPONSES"
            )
        if "resource_response_ledger" not in awaiting_hooks:
            errors.append(
                "awaiting_hook_kinds missing resource_response_ledger"
            )
        awaiting_count = _integer_count(resource_summary, "awaiting")
        if awaiting_count is None:
            errors.append("response_summary_by_hook resource awaiting count is not integer")
        elif awaiting_count < len(awaiting_ids):
            errors.append("response_summary_by_hook resource awaiting count is stale")
        return tuple(errors)
    if rejected_ids:
        if stability_rejected_ids != rejected_ids:
            errors.append(
                "resource_response_rejected_request_ids mismatch: "
                + f"{stability_rejected_ids}!={rejected_ids}"
            )
        if decision != "REPAIR_REFINEMENT_RESPONSE_CONTRACT":
            errors.append(
                "rejected resource responses require REPAIR_REFINEMENT_RESPONSE_CONTRACT"
            )
        if "resource_response_ledger" not in rejected_hooks:
            errors.append(
                "rejected_hook_kinds missing resource_response_ledger"
            )
        rejected_count = _integer_count(resource_summary, "rejected")
        if rejected_count is None:
            errors.append("response_summary_by_hook resource rejected count is not integer")
        elif rejected_count < len(rejected_ids):
            errors.append("response_summary_by_hook resource rejected count is stale")
    return tuple(errors)


def _route_stability_row_has_resource_response_status(row: dict[str, Any]) -> bool:
    return bool(
        _str_tuple(row.get("resource_response_awaiting_request_ids", []))
        or _str_tuple(row.get("resource_response_rejected_request_ids", []))
    )


def _interactive_session_rows_have_resource_status(
    rows: list[dict[str, Any]],
) -> bool:
    return any(_interactive_session_row_has_resource_status(row) for row in rows)


def _interactive_session_row_has_resource_status(row: dict[str, Any]) -> bool:
    return bool(
        _str_tuple(row.get("resource_response_awaiting_request_ids", []))
        or _str_tuple(row.get("resource_response_rejected_request_ids", []))
    )


def _interactive_session_rows_have_route_preconditions(
    rows: list[dict[str, Any]],
) -> bool:
    return any(_interactive_session_row_has_route_preconditions(row) for row in rows)


def _interactive_session_row_has_route_preconditions(row: dict[str, Any]) -> bool:
    return bool(
        row.get("route_adoption_precondition_present", False)
        or row.get("route_adoption_precondition_unresolved", False)
        or _dict_value(row, "route_adoption_preconditions")
        or _str_tuple(row.get("route_adoption_precondition_known_blockers", []))
        or _str_tuple(
            row.get("route_adoption_precondition_required_response_fields", [])
        )
    )


def _route_stability_row_has_route_preconditions(row: dict[str, Any]) -> bool:
    return bool(
        row.get("route_adoption_precondition_present", False)
        or row.get("route_adoption_precondition_unresolved", False)
        or _dict_value(row, "route_adoption_preconditions")
        or _str_tuple(row.get("route_adoption_precondition_known_blockers", []))
        or _str_tuple(
            row.get("route_adoption_precondition_required_response_fields", [])
        )
    )


def _interactive_session_resource_response_status_errors(
    session_row: dict[str, Any],
    stability_row: dict[str, Any] | None,
) -> tuple[str, ...]:
    session_awaiting = _str_tuple(
        session_row.get("resource_response_awaiting_request_ids", [])
    )
    session_rejected = _str_tuple(
        session_row.get("resource_response_rejected_request_ids", [])
    )
    if stability_row is None:
        if session_awaiting or session_rejected:
            return ("interactive-session row has no matching route-stability row",)
        return tuple()
    stability_awaiting = _str_tuple(
        stability_row.get("resource_response_awaiting_request_ids", [])
    )
    stability_rejected = _str_tuple(
        stability_row.get("resource_response_rejected_request_ids", [])
    )
    errors: list[str] = []
    if session_awaiting != stability_awaiting:
        errors.append(
            "resource_response_awaiting_request_ids mismatch: "
            + f"{session_awaiting}!={stability_awaiting}"
        )
    if session_rejected != stability_rejected:
        errors.append(
            "resource_response_rejected_request_ids mismatch: "
            + f"{session_rejected}!={stability_rejected}"
        )
    if stability_awaiting or stability_rejected:
        if str(session_row.get("next_interaction_kind", "")) != "await_refinement_response":
            errors.append(
                "resource response status requires await_refinement_response next interaction"
            )
        if "resource_response_ledger" not in _str_tuple(session_row.get("next_tools", [])):
            errors.append("next_tools missing resource_response_ledger")
        commands = tuple(str(command) for command in session_row.get("next_commands", []))
        for request_id in (*stability_awaiting, *stability_rejected):
            if not any(f"resource_request_id={request_id}" in command for command in commands):
                errors.append(f"next_commands missing resource_request_id={request_id}")
    return tuple(errors)


def _interactive_session_route_precondition_errors(
    session_row: dict[str, Any],
    stability_row: dict[str, Any] | None,
) -> tuple[str, ...]:
    if stability_row is None:
        if _interactive_session_row_has_route_preconditions(session_row):
            return ("interactive-session row has no matching route-stability row",)
        return tuple()
    if not _route_stability_row_has_route_preconditions(stability_row):
        return tuple()
    errors: list[str] = []
    for field_name in (
        "llm_route_planner_route_adoption_status",
        "route_adoption_precondition_present",
        "route_adoption_precondition_blocked_before_response",
        "route_adoption_precondition_unresolved",
        "route_adoption_precondition_known_blocker_count",
        "route_adoption_precondition_required_response_field_count",
    ):
        if session_row.get(field_name) != stability_row.get(field_name):
            errors.append(f"{field_name} mismatch")
    if _dict_value(session_row, "route_adoption_preconditions") != _dict_value(
        stability_row,
        "route_adoption_preconditions",
    ):
        errors.append("route_adoption_preconditions mismatch")
    for field_name in (
        "route_adoption_precondition_known_blockers",
        "route_adoption_precondition_required_response_fields",
    ):
        if _str_tuple(session_row.get(field_name, [])) != _str_tuple(
            stability_row.get(field_name, [])
        ):
            errors.append(f"{field_name} mismatch")
    if bool(stability_row.get("route_adoption_precondition_unresolved", False)):
        if str(session_row.get("session_state", "")) != "AWAITING_REFINEMENT_RESPONSES":
            errors.append(
                "unresolved route-adoption preconditions require "
                "AWAITING_REFINEMENT_RESPONSES session state"
            )
        if str(session_row.get("next_interaction_kind", "")) != "await_refinement_response":
            errors.append(
                "unresolved route-adoption preconditions require "
                "await_refinement_response next interaction"
            )
        if "resource_response_ledger" not in _str_tuple(session_row.get("next_tools", [])):
            errors.append("next_tools missing resource_response_ledger")
        commands = tuple(str(command) for command in session_row.get("next_commands", []))
        if not any("route-adoption precondition" in command for command in commands):
            errors.append("next_commands missing route-adoption precondition guidance")
    return tuple(errors)


def _integer_count(row: dict[str, Any], key: str) -> int | None:
    value = row.get(key, 0)
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _resource_response_ledger_route_index(
    rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    return _route_identity_row_index(rows)


def _matched_resource_response_ledger_route_rows(
    row: dict[str, Any],
    route_index: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    matched: list[dict[str, Any]] = []
    seen: set[str] = set()
    for key in _route_identity_keys(row):
        for ledger_row in route_index.get(key, []):
            ledger_id = str(ledger_row.get("resource_response_ledger_id", "")) or stable_hash(
                ledger_row
            )
            if ledger_id in seen:
                continue
            seen.add(ledger_id)
            matched.append(ledger_row)
    return sorted(
        matched,
        key=lambda ledger_row: (
            str(ledger_row.get("acceptance_status", "")),
            str(ledger_row.get("resource_request_id", "")),
            str(ledger_row.get("resource_response_ledger_id", "")),
        ),
    )


def _route_identity_keys(row: dict[str, Any]) -> tuple[str, ...]:
    keys = []
    for field_name in ("route_id", "goal_plan_id", "display_name"):
        value = str(row.get(field_name, ""))
        if value:
            keys.append(f"{field_name}:{value}")
    return tuple(keys)


def _route_revision_row_has_resource_response_status(row: dict[str, Any]) -> bool:
    return any(
        field_name in row
        for field_name in (
            "resource_response_summary",
            "resource_response_summary_by_acceptance_status",
            "resource_response_awaiting_request_ids",
            "resource_response_rejected_request_ids",
        )
    )


def _route_revision_resource_response_status_errors(
    row: dict[str, Any],
    ledger_rows: list[dict[str, Any]],
) -> tuple[str, ...]:
    if not _route_revision_row_has_resource_response_status(row):
        return tuple()
    expected_summary = _resource_response_status_summary(ledger_rows)
    expected_by_status = _resource_response_summary_by_acceptance_status(ledger_rows)
    expected_awaiting = _resource_response_request_ids_by_status(
        ledger_rows,
        awaiting=True,
    )
    expected_rejected = _resource_response_request_ids_by_status(
        ledger_rows,
        rejected=True,
    )
    errors: list[str] = []
    actual_summary = _dict_value(row, "resource_response_summary")
    for key, expected_value in expected_summary.items():
        actual_value = actual_summary.get(key, 0)
        if not isinstance(actual_value, int) or isinstance(actual_value, bool):
            errors.append(f"resource_response_summary.{key} must be integer")
            continue
        if actual_value != expected_value:
            errors.append(
                f"resource_response_summary.{key} mismatch: "
                f"{actual_value}!={expected_value}"
            )
    actual_by_status = _dict_value(
        row,
        "resource_response_summary_by_acceptance_status",
    )
    normalized_actual_by_status = {
        str(key): value
        for key, value in actual_by_status.items()
        if isinstance(value, int) and not isinstance(value, bool)
    }
    if normalized_actual_by_status != expected_by_status:
        errors.append(
            "resource_response_summary_by_acceptance_status mismatch: "
            + f"{normalized_actual_by_status}!={expected_by_status}"
        )
    actual_awaiting = _str_tuple(row.get("resource_response_awaiting_request_ids", []))
    actual_rejected = _str_tuple(row.get("resource_response_rejected_request_ids", []))
    if actual_awaiting != expected_awaiting:
        errors.append(
            "resource_response_awaiting_request_ids mismatch: "
            + f"{actual_awaiting}!={expected_awaiting}"
        )
    if actual_rejected != expected_rejected:
        errors.append(
            "resource_response_rejected_request_ids mismatch: "
            + f"{actual_rejected}!={expected_rejected}"
        )
    return tuple(errors)


def _resource_response_status_summary(
    rows: list[dict[str, Any]],
) -> dict[str, int]:
    summary = {
        "queued": 0,
        "responded": 0,
        "contract_ok": 0,
        "awaiting": 0,
        "rejected": 0,
        "accepted": 0,
        "route_revision_recommended": 0,
    }
    for row in rows:
        status = str(row.get("acceptance_status", ""))
        summary["queued"] += 1
        if bool(row.get("response_present", False)) or (
            bool(status) and status != "AWAITING_RESOURCE_RESPONSE"
        ):
            summary["responded"] += 1
        if bool(row.get("response_contract_ok", False)) or status.startswith("ACCEPTED_"):
            summary["contract_ok"] += 1
        if status == "AWAITING_RESOURCE_RESPONSE":
            summary["awaiting"] += 1
        if status.startswith("REJECTED_"):
            summary["rejected"] += 1
        if status.startswith("ACCEPTED_"):
            summary["accepted"] += 1
        if bool(row.get("route_revision_recommended", False)):
            summary["route_revision_recommended"] += 1
    return summary


def _resource_response_summary_by_acceptance_status(
    rows: list[dict[str, Any]],
) -> dict[str, int]:
    statuses: dict[str, int] = {}
    for row in rows:
        status = str(row.get("acceptance_status", ""))
        if not status:
            continue
        statuses[status] = statuses.get(status, 0) + 1
    return dict(sorted(statuses.items()))


def _resource_response_request_ids_by_status(
    rows: list[dict[str, Any]],
    *,
    awaiting: bool = False,
    rejected: bool = False,
) -> tuple[str, ...]:
    request_ids: list[str] = []
    for row in rows:
        status = str(row.get("acceptance_status", ""))
        if awaiting and status != "AWAITING_RESOURCE_RESPONSE":
            continue
        if rejected and not status.startswith("REJECTED_"):
            continue
        if not awaiting and not rejected:
            continue
        request_id = str(row.get("resource_request_id", "")) or str(
            row.get("resource_response_ledger_id", "")
        )
        if request_id:
            request_ids.append(request_id)
    return _str_tuple(request_ids)


def _route_revision_resource_response_evidence_errors(
    row: dict[str, Any],
    ledger_index: dict[str, dict[str, Any]],
) -> tuple[str, ...]:
    evidence_ids = tuple(
        evidence_id
        for evidence_id in _str_tuple(row.get("applied_refinement_evidence_ids", []))
        if evidence_id.startswith("resource_response_ledger:")
    )
    if not evidence_ids:
        return ("resource_response_ledger hook has no resource_response_ledger evidence id",)
    errors: list[str] = []
    for evidence_id in evidence_ids:
        ledger_id = evidence_id.removeprefix("resource_response_ledger:")
        ledger_row = ledger_index.get(ledger_id)
        if ledger_row is None:
            errors.append(f"missing resource response-ledger row: {ledger_id}")
            continue
        acceptance_status = str(ledger_row.get("acceptance_status", ""))
        if not bool(ledger_row.get("ok", False)):
            errors.append(f"ledger row is not ok: {ledger_id}")
        if not bool(ledger_row.get("response_present", False)):
            errors.append(f"ledger row has no response: {ledger_id}")
        if not bool(ledger_row.get("response_contract_ok", False)):
            errors.append(f"ledger row contract is not ok: {ledger_id}")
        if not bool(ledger_row.get("response_contract_minimum_met", False)):
            errors.append(f"ledger row contract minimum is not met: {ledger_id}")
        if acceptance_status.startswith("REJECTED_"):
            errors.append(f"ledger row is rejected: {ledger_id}")
        if acceptance_status == "AWAITING_RESOURCE_RESPONSE":
            errors.append(f"ledger row is awaiting response: {ledger_id}")
        if "not theorem proof evidence" not in str(
            ledger_row.get("proof_evidence_boundary", "")
        ).lower():
            errors.append(f"ledger row proof boundary is missing: {ledger_id}")
    return tuple(errors)


_RESOURCE_RESPONSE_TRACE_STRING_FIELDS = (
    "resource_request_id",
    "action_resource_plan_id",
    "primitive_action_id",
    "coverage_map_id",
    "goal_plan_id",
    "route_id",
    "primitive",
    "resource_id",
    "request_phase",
    "expected_response_artifact",
    "acceptance_gate",
    "acceptance_status",
    "prover_attempt_status",
    "prover_diagnostic_signature",
    "proof_evidence_status",
)
_RESOURCE_RESPONSE_TRACE_STRING_ARRAY_FIELDS = (
    "response_contract_fields",
    "matched_response_contract_fields",
    "missing_response_contract_fields",
    "response_artifacts",
    "actionable_work_items",
)
_RESOURCE_RESPONSE_TRACE_BOOLEAN_FIELDS = (
    "response_present",
    "response_contract_minimum_met",
    "response_contract_ok",
    "route_revision_recommended",
)


def _route_revision_resource_response_trace_errors(
    row: dict[str, Any],
    ledger_index: dict[str, dict[str, Any]],
) -> tuple[str, ...]:
    traces = tuple(
        trace
        for trace in row.get("applied_resource_response_traces", []) or []
        if isinstance(trace, dict)
    )
    evidence_ledger_ids = {
        evidence_id.removeprefix("resource_response_ledger:")
        for evidence_id in _str_tuple(row.get("applied_refinement_evidence_ids", []))
        if evidence_id.startswith("resource_response_ledger:")
    }
    if not traces:
        return ("resource_response_ledger hook has no applied_resource_response_traces",)

    errors: list[str] = []
    trace_ledger_ids: set[str] = set()
    for trace_index, trace in enumerate(traces):
        ledger_id = str(trace.get("resource_response_ledger_id", ""))
        if not ledger_id:
            errors.append(f"trace {trace_index} missing resource_response_ledger_id")
            continue
        trace_ledger_ids.add(ledger_id)
        ledger_row = ledger_index.get(ledger_id)
        if ledger_row is None:
            errors.append(f"trace references missing resource response-ledger row: {ledger_id}")
            continue
        for field_name in _RESOURCE_RESPONSE_TRACE_STRING_FIELDS:
            if str(trace.get(field_name, "")) != str(ledger_row.get(field_name, "")):
                errors.append(f"trace {ledger_id} {field_name} mismatch")
        for field_name in _RESOURCE_RESPONSE_TRACE_STRING_ARRAY_FIELDS:
            if set(_str_tuple(trace.get(field_name, []))) != set(
                _str_tuple(ledger_row.get(field_name, []))
            ):
                errors.append(f"trace {ledger_id} {field_name} mismatch")
        for field_name in _RESOURCE_RESPONSE_TRACE_BOOLEAN_FIELDS:
            if bool(trace.get(field_name, False)) != bool(
                ledger_row.get(field_name, False)
            ):
                errors.append(f"trace {ledger_id} {field_name} mismatch")
        if _dict_value(trace, "dispatch_spec") != _dict_value(
            ledger_row,
            "dispatch_spec",
        ):
            errors.append(f"trace {ledger_id} dispatch_spec mismatch")
        if _candidate_declaration_rows(
            trace.get("candidate_declaration_rows", [])
        ) != _candidate_declaration_rows(
            ledger_row.get("candidate_declaration_rows", [])
        ):
            errors.append(f"trace {ledger_id} candidate_declaration_rows mismatch")
        if "not theorem proof evidence" not in str(
            trace.get("proof_evidence_boundary", "")
        ).lower():
            errors.append(f"trace {ledger_id} proof boundary is missing")

    missing_trace_ids = sorted(evidence_ledger_ids - trace_ledger_ids)
    extra_trace_ids = sorted(trace_ledger_ids - evidence_ledger_ids)
    if missing_trace_ids:
        errors.append(
            "resource_response_ledger evidence ids missing from traces: "
            + ",".join(missing_trace_ids)
        )
    if extra_trace_ids:
        errors.append(
            "applied_resource_response_traces include non-evidence ledger ids: "
            + ",".join(extra_trace_ids)
        )
    return tuple(errors)


def _proof_state_triage_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = bundle_dir / "artifacts" / "formalization_gap_planner_proof_state_triage"
    manifest_path = artifact_dir / "formalization_gap_planner_proof_state_triage_manifest.json"
    rows_jsonl_path = artifact_dir / "formalization_gap_planner_proof_state_triage.jsonl"
    row_schema_path = artifact_dir / "formalization_gap_planner_proof_state_triage_row.schema.json"
    manifest = _read_json_no_error(manifest_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    checks = [
        _check(
            "optional_proof_state_triage_row_schema_file",
            "optional_artifacts",
            "optional proof-state triage row schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            "optional_proof_state_triage_manifest_schema_valid_count",
            "optional_artifacts",
            "proof-state triage manifest schema-valid count matches row count",
            (
                f"{manifest.get('n_row_schema_valid', 0)}/"
                f"{manifest.get('n_triage_items', 0)}; "
                f"invalid={manifest.get('n_row_schema_invalid', 0)}"
            ),
            int(manifest.get("n_triage_items", 0) or 0) > 0
            and int(manifest.get("n_row_schema_valid", 0) or 0)
            == int(manifest.get("n_triage_items", 0) or 0)
            and int(manifest.get("n_row_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_proof_state_triage_jsonl_parse",
            "optional_artifacts",
            "proof-state triage JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_proof_state_triage_jsonl_row_count",
            "optional_artifacts",
            "proof-state triage JSONL rows match manifest count",
            f"jsonl={len(rows)} manifest={manifest.get('n_triage_items', 0)}",
            len(rows) == int(manifest.get("n_triage_items", 0) or 0),
        ),
    ]
    for idx, row in enumerate(rows):
        schema_errors = validate_proof_state_triage_row(row)
        generic_prover_errors = _proof_state_triage_generic_prover_field_errors(row)
        checks.append(
            _check(
                f"optional_proof_state_triage_row_{idx}_schema_valid",
                "optional_artifacts",
                "proof-state triage row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
        if _proof_state_triage_generic_prover_fields_observed(row):
            checks.append(
                _check(
                    f"optional_proof_state_triage_row_{idx}_generic_prover_fields",
                    "optional_artifacts",
                    "proof-state triage preserves generic prover triage/class/family fields",
                    "; ".join(generic_prover_errors) if generic_prover_errors else "ok",
                    not generic_prover_errors,
                    errors=generic_prover_errors,
                )
            )
    return checks


def _refinement_evidence_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = bundle_dir / "artifacts" / "formalization_gap_planner_refinement_evidence"
    manifest_path = artifact_dir / "formalization_gap_planner_refinement_evidence_manifest.json"
    rows_jsonl_path = artifact_dir / "formalization_gap_planner_refinement_evidence.jsonl"
    row_schema_path = artifact_dir / "formalization_gap_planner_refinement_evidence_row.schema.json"
    manifest = _read_json_no_error(manifest_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    checks = [
        _check(
            "optional_refinement_evidence_row_schema_file",
            "optional_artifacts",
            "optional refinement evidence row schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            "optional_refinement_evidence_manifest_schema_valid_count",
            "optional_artifacts",
            "refinement-evidence manifest schema-valid count matches row count",
            (
                f"{manifest.get('n_evidence_row_schema_valid', 0)}/"
                f"{manifest.get('n_evidence_rows', 0)}; "
                f"invalid={manifest.get('n_evidence_row_schema_invalid', 0)}"
            ),
            int(manifest.get("n_evidence_rows", 0) or 0) > 0
            and int(manifest.get("n_evidence_row_schema_valid", 0) or 0)
            == int(manifest.get("n_evidence_rows", 0) or 0)
            and int(manifest.get("n_evidence_row_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_refinement_evidence_jsonl_parse",
            "optional_artifacts",
            "refinement evidence JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_refinement_evidence_jsonl_row_count",
            "optional_artifacts",
            "refinement evidence JSONL rows match manifest count",
            f"jsonl={len(rows)} manifest={manifest.get('n_evidence_rows', 0)}",
            len(rows) == int(manifest.get("n_evidence_rows", 0) or 0),
        ),
    ]
    for idx, row in enumerate(rows):
        schema_errors = validate_refinement_evidence_row(row)
        checks.append(
            _check(
                f"optional_refinement_evidence_row_{idx}_schema_valid",
                "optional_artifacts",
                "refinement evidence row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
    return checks


def _interactive_session_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = bundle_dir / "artifacts" / "formalization_gap_planner_interactive_session"
    manifest_path = artifact_dir / "formalization_gap_planner_interactive_session_manifest.json"
    session_rows_jsonl_path = (
        artifact_dir / "formalization_gap_planner_interactive_session.jsonl"
    )
    session_row_schema_path = (
        artifact_dir / "formalization_gap_planner_interactive_session_row.schema.json"
    )
    rows_jsonl_path = (
        artifact_dir / "formalization_gap_planner_interactive_decision_policy.jsonl"
    )
    row_schema_path = (
        artifact_dir
        / "formalization_gap_planner_interactive_decision_policy_row.schema.json"
    )
    stability_rows_jsonl_path = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_route_stability_audit"
        / "formalization_gap_planner_route_stability_audit.jsonl"
    )
    component_jsonl_path = (
        bundle_dir
        / "component_resource_registry"
        / "formalization_gap_planner_component_resource_registry.jsonl"
    )
    resource_jsonl_path = (
        bundle_dir
        / "component_resource_registry"
        / "formalization_gap_planner_component_resource_resources.jsonl"
    )
    resource_contract_jsonl_path = (
        bundle_dir
        / "component_resource_registry"
        / "formalization_gap_planner_component_resource_contracts.jsonl"
    )
    manifest = _read_json_no_error(manifest_path)
    session_rows, session_row_errors = _read_jsonl_dict_rows_no_error(
        session_rows_jsonl_path
    )
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    stability_rows, stability_row_errors = (
        _read_jsonl_dict_rows_no_error(stability_rows_jsonl_path)
        if stability_rows_jsonl_path.exists()
        else ([], tuple())
    )
    stability_index = _route_identity_row_index(stability_rows)
    session_artifact_present = "n_session_rows" in manifest or bool(session_rows)
    component_rows, _component_errors = _read_jsonl_dict_rows_no_error(
        component_jsonl_path
    )
    resource_rows, _resource_errors = _read_jsonl_dict_rows_no_error(
        resource_jsonl_path
    )
    resource_contract_rows, _contract_errors = _read_jsonl_dict_rows_no_error(
        resource_contract_jsonl_path
    )
    component_ids = {
        str(row.get("component_id", ""))
        for row in component_rows
        if row.get("component_id")
    }
    resource_ids = {
        str(row.get("resource_id", ""))
        for row in resource_rows
        if row.get("resource_id")
    }
    contract_resource_by_id = {
        str(row.get("resource_contract_id", "")): str(row.get("resource_id", ""))
        for row in resource_contract_rows
        if row.get("resource_contract_id")
    }
    resource_contract_ids = set(contract_resource_by_id)
    checks = [
        _check(
            "optional_interactive_decision_policy_row_schema_file",
            "optional_artifacts",
            "optional interactive decision-policy row schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            "optional_interactive_decision_policy_manifest_schema_valid_count",
            "optional_artifacts",
            "decision-policy manifest schema-valid count matches row count",
            (
                f"{manifest.get('n_decision_policy_row_schema_valid', 0)}/"
                f"{manifest.get('n_decision_policy_rows', 0)}; "
                f"invalid={manifest.get('n_decision_policy_row_schema_invalid', 0)}"
            ),
            int(manifest.get("n_decision_policy_rows", 0) or 0) > 0
            and int(manifest.get("n_decision_policy_row_schema_valid", 0) or 0)
            == int(manifest.get("n_decision_policy_rows", 0) or 0)
            and int(manifest.get("n_decision_policy_row_schema_invalid", 0) or 0)
            == 0,
        ),
        _check(
            "optional_interactive_decision_policy_jsonl_parse",
            "optional_artifacts",
            "decision-policy JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_interactive_decision_policy_jsonl_row_count",
            "optional_artifacts",
            "decision-policy JSONL rows match manifest count",
            f"jsonl={len(rows)} manifest={manifest.get('n_decision_policy_rows', 0)}",
            len(rows) == int(manifest.get("n_decision_policy_rows", 0) or 0),
        ),
    ]
    if session_artifact_present:
        checks.extend(
            [
                _check(
                    "optional_interactive_session_row_schema_file",
                    "optional_artifacts",
                    "optional interactive session row schema exists",
                    str(session_row_schema_path.exists()),
                    session_row_schema_path.exists(),
                ),
                _check(
                    "optional_interactive_session_manifest_schema_valid_count",
                    "optional_artifacts",
                    "interactive-session manifest schema-valid count matches row count",
                    (
                        f"{manifest.get('n_row_schema_valid', 0)}/"
                        f"{manifest.get('n_session_rows', 0)}; "
                        f"invalid={manifest.get('n_row_schema_invalid', 0)}"
                    ),
                    int(manifest.get("n_session_rows", 0) or 0) > 0
                    and int(manifest.get("n_row_schema_valid", 0) or 0)
                    == int(manifest.get("n_session_rows", 0) or 0)
                    and int(manifest.get("n_row_schema_invalid", 0) or 0) == 0,
                ),
                _check(
                    "optional_interactive_session_jsonl_parse",
                    "optional_artifacts",
                    "interactive-session JSONL parses into object rows",
                    (
                        "; ".join(session_row_errors)
                        if session_row_errors
                        else f"rows={len(session_rows)}"
                    ),
                    not session_row_errors,
                    errors=session_row_errors,
                ),
                _check(
                    "optional_interactive_session_jsonl_row_count",
                    "optional_artifacts",
                    "interactive-session JSONL rows match manifest count",
                    f"jsonl={len(session_rows)} manifest={manifest.get('n_session_rows', 0)}",
                    len(session_rows) == int(manifest.get("n_session_rows", 0) or 0),
                ),
            ]
        )
    if session_artifact_present and (
        _interactive_session_rows_have_resource_status(session_rows)
        or _interactive_session_rows_have_route_preconditions(session_rows)
    ):
        checks.append(
            _check(
                "optional_interactive_session_route_stability_jsonl_parse",
                "optional_artifacts",
                "bundled route-stability JSONL parses for interactive/resource-status consistency",
                (
                    "; ".join(stability_row_errors)
                    if stability_row_errors
                    else f"rows={len(stability_rows)}"
                ),
                not stability_row_errors and bool(stability_rows),
                errors=stability_row_errors,
            )
        )
    for idx, row in enumerate(session_rows if session_artifact_present else []):
        schema_errors = validate_interactive_session_row(row)
        stability_row = _first_identity_match(row, stability_index)
        status_errors = _interactive_session_resource_response_status_errors(
            row,
            stability_row,
        )
        route_precondition_errors = (
            _interactive_session_route_precondition_errors(row, stability_row)
        )
        generic_prover_errors = _interactive_session_generic_prover_field_errors(row)
        formal_attempt_queue_errors = (
            _interactive_session_formal_attempt_queue_errors(row)
        )
        checks.append(
            _check(
                f"optional_interactive_session_row_{idx}_schema_valid",
                "optional_artifacts",
                "interactive-session row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
        if _interactive_session_generic_prover_fields_observed(row):
            checks.append(
                _check(
                    f"optional_interactive_session_row_{idx}_generic_prover_fields",
                    "optional_artifacts",
                    "interactive-session proof-state routing preserves generic prover triage/class/family fields",
                    "; ".join(generic_prover_errors) if generic_prover_errors else "ok",
                    not generic_prover_errors,
                    errors=generic_prover_errors,
                )
            )
        if _interactive_session_row_has_formal_attempt_queue(row):
            checks.append(
                _check(
                    f"optional_interactive_session_row_{idx}_formal_attempt_queue_consistency",
                    "optional_artifacts",
                    "interactive-session formal-attempt queue counts and ready-item commands are internally consistent",
                    (
                        "; ".join(formal_attempt_queue_errors)
                        if formal_attempt_queue_errors
                        else "ok"
                    ),
                    not formal_attempt_queue_errors,
                    errors=formal_attempt_queue_errors,
                )
            )
        if _interactive_session_row_has_resource_status(row) or (
            stability_row is not None
            and _route_stability_row_has_resource_response_status(stability_row)
        ):
            checks.append(
                _check(
                    f"optional_interactive_session_row_{idx}_resource_response_status_consistency",
                    "optional_artifacts",
                    "interactive-session resource-response request ids match route-stability rows",
                    "; ".join(status_errors) if status_errors else "ok",
                    not status_errors,
                    errors=status_errors,
                )
            )
        if _interactive_session_row_has_route_preconditions(row) or (
            stability_row is not None
            and _route_stability_row_has_route_preconditions(stability_row)
        ):
            checks.append(
                _check(
                    f"optional_interactive_session_row_{idx}_route_precondition_consistency",
                    "optional_artifacts",
                    "interactive-session route-adoption preconditions match route-stability rows",
                    (
                        "; ".join(route_precondition_errors)
                        if route_precondition_errors
                        else "ok"
                    ),
                    not route_precondition_errors,
                    errors=route_precondition_errors,
                )
            )
    for idx, row in enumerate(rows):
        schema_errors = validate_interactive_decision_policy_row(row)
        checks.append(
            _check(
                f"optional_interactive_decision_policy_row_{idx}_schema_valid",
                "optional_artifacts",
                "interactive decision-policy row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
        row_component_ids = _str_tuple(row.get("component_ids", []))
        row_local_resource_ids = _str_tuple(row.get("local_first_resource_ids", []))
        row_frontier_resource_ids = _str_tuple(
            row.get("frontier_escalation_resource_ids", [])
        )
        row_resource_ids = _str_tuple(
            [*row_local_resource_ids, *row_frontier_resource_ids]
        )
        row_contract_ids = _str_tuple(row.get("resource_contract_ids", []))
        missing_components = tuple(
            component_id
            for component_id in row_component_ids
            if component_id not in component_ids
        )
        missing_resources = tuple(
            resource_id for resource_id in row_resource_ids if resource_id not in resource_ids
        )
        missing_contracts = tuple(
            contract_id
            for contract_id in row_contract_ids
            if contract_id not in resource_contract_ids
        )
        covered_resource_ids = {
            contract_resource_by_id.get(contract_id, "")
            for contract_id in row_contract_ids
            if contract_id in contract_resource_by_id
        }
        uncovered_resources = tuple(
            resource_id
            for resource_id in row_resource_ids
            if resource_id not in covered_resource_ids
        )
        extra_contract_resources = tuple(
            resource_id
            for resource_id in sorted(covered_resource_ids)
            if resource_id and resource_id not in row_resource_ids
        )
        checks.extend(
            [
                _check(
                    f"optional_interactive_decision_policy_row_{idx}_component_links",
                    "optional_artifacts",
                    "all provided component ids resolve to bundled component-resource rows",
                    "; ".join(missing_components)
                    if missing_components
                    else f"components={len(row_component_ids)}",
                    not missing_components,
                    errors=missing_components,
                ),
                _check(
                    f"optional_interactive_decision_policy_row_{idx}_resource_links",
                    "optional_artifacts",
                    "all provided local/frontier resource ids resolve to bundled resource rows",
                    "; ".join(missing_resources)
                    if missing_resources
                    else f"resources={len(row_resource_ids)}",
                    not missing_resources,
                    errors=missing_resources,
                ),
                _check(
                    f"optional_interactive_decision_policy_row_{idx}_resource_contract_links",
                    "optional_artifacts",
                    "all provided resource contract ids resolve to bundled contract rows",
                    "; ".join(missing_contracts)
                    if missing_contracts
                    else f"contracts={len(row_contract_ids)}",
                    not missing_contracts,
                    errors=missing_contracts,
                ),
                _check(
                    f"optional_interactive_decision_policy_row_{idx}_resource_contract_coverage",
                    "optional_artifacts",
                    "provided resource contracts cover the provided local/frontier resources",
                    (
                        "uncovered="
                        + ",".join(uncovered_resources)
                        + "; extra="
                        + ",".join(extra_contract_resources)
                    )
                    if uncovered_resources or extra_contract_resources
                    else f"covered={len(row_resource_ids)}",
                    not uncovered_resources and not extra_contract_resources,
                    errors=tuple([*uncovered_resources, *extra_contract_resources]),
                ),
            ]
        )
    return checks


def _evaluation_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = bundle_dir / "artifacts" / "formalization_gap_planner_evaluation"
    manifest_path = artifact_dir / "formalization_gap_planner_evaluation_manifest.json"
    rows_jsonl_path = artifact_dir / "formalization_gap_planner_evaluation.jsonl"
    row_schema_path = artifact_dir / "formalization_gap_planner_evaluation_row.schema.json"
    ground_truth_filename = "formalization_gap_planner_evaluation_ground_truth.json"
    ground_truth_path = artifact_dir / ground_truth_filename
    manifest = _read_json_no_error(manifest_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    ground_truth_payload = _read_json_no_error(ground_truth_path)
    ground_truth_rows = _evaluation_ground_truth_rows(ground_truth_payload)
    ground_truth_index = _evaluation_ground_truth_index(ground_truth_rows)
    checks = [
        _check(
            "optional_evaluation_row_schema_file",
            "optional_artifacts",
            "optional evaluation row schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            "optional_evaluation_ground_truth_copy",
            "optional_artifacts",
            "optional evaluation carries its exact route-truth input",
            str(ground_truth_path.exists()),
            ground_truth_path.exists()
            and str(
                manifest.get(
                    "bundled_ground_truth_filename",
                    ground_truth_filename,
                )
            )
            == ground_truth_filename,
        ),
        _check(
            "optional_evaluation_ground_truth_parse",
            "optional_artifacts",
            "copied evaluation ground truth parses into route rows",
            f"rows={len(ground_truth_rows)}",
            bool(ground_truth_rows),
        ),
        _check(
            "optional_evaluation_manifest_schema_valid_count",
            "optional_artifacts",
            "evaluation manifest row schema-valid count matches row count",
            (
                f"{manifest.get('n_evaluation_row_schema_valid', 0)}/"
                f"{manifest.get('n_evaluation_rows', 0)}; "
                f"invalid={manifest.get('n_evaluation_row_schema_invalid', 0)}"
            ),
            int(manifest.get("n_evaluation_rows", 0) or 0) > 0
            and int(manifest.get("n_evaluation_row_schema_valid", 0) or 0)
            == int(manifest.get("n_evaluation_rows", 0) or 0)
            and int(manifest.get("n_evaluation_row_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_evaluation_jsonl_parse",
            "optional_artifacts",
            "evaluation JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_evaluation_jsonl_row_count",
            "optional_artifacts",
            "evaluation JSONL rows match manifest count",
            f"jsonl={len(rows)} manifest={manifest.get('n_evaluation_rows', 0)}",
            len(rows) == int(manifest.get("n_evaluation_rows", 0) or 0),
        ),
    ]
    realization_manifest_errors = _evaluation_realization_missing_manifest_errors(
        manifest,
        rows,
    )
    route_adoption_manifest_errors = _evaluation_route_adoption_manifest_errors(
        manifest,
        rows,
    )
    route_option_selection_manifest_errors = (
        _evaluation_route_option_selection_manifest_errors(
            manifest,
            rows,
        )
    )
    quality_control_manifest_errors = _evaluation_quality_control_manifest_errors(
        manifest,
        rows,
    )
    residual_goal_context_manifest_errors = (
        _evaluation_residual_goal_context_manifest_errors(
            manifest,
            rows,
        )
    )
    checks.append(
        _check(
            "optional_evaluation_realization_missing_manifest",
            "optional_artifacts",
            "evaluation manifest preserves realization-missing primitive aggregates",
            "; ".join(realization_manifest_errors) if realization_manifest_errors else "ok",
            not realization_manifest_errors,
            errors=realization_manifest_errors,
        )
    )
    checks.append(
        _check(
            "optional_evaluation_route_adoption_manifest",
            "optional_artifacts",
            "evaluation manifest preserves LLM route-adoption readiness aggregates",
            (
                "; ".join(route_adoption_manifest_errors)
                if route_adoption_manifest_errors
                else "ok"
            ),
            not route_adoption_manifest_errors,
            errors=route_adoption_manifest_errors,
        )
    )
    checks.append(
        _check(
            "optional_evaluation_route_option_selection_manifest",
            "optional_artifacts",
            "evaluation manifest preserves LLM route-option selection aggregates",
            (
                "; ".join(route_option_selection_manifest_errors)
                if route_option_selection_manifest_errors
                else "ok"
            ),
            not route_option_selection_manifest_errors,
            errors=route_option_selection_manifest_errors,
        )
    )
    checks.append(
        _check(
            "optional_evaluation_quality_control_manifest",
            "optional_artifacts",
            "evaluation manifest preserves quality-control policy aggregates",
            (
                "; ".join(quality_control_manifest_errors)
                if quality_control_manifest_errors
                else "ok"
            ),
            not quality_control_manifest_errors,
            errors=quality_control_manifest_errors,
        )
    )
    checks.append(
        _check(
            "optional_evaluation_residual_goal_context_manifest",
            "optional_artifacts",
            "evaluation manifest preserves residual-goal context aggregates",
            (
                "; ".join(residual_goal_context_manifest_errors)
                if residual_goal_context_manifest_errors
                else "ok"
            ),
            not residual_goal_context_manifest_errors,
            errors=residual_goal_context_manifest_errors,
        )
    )
    for idx, row in enumerate(rows):
        schema_errors = validate_evaluation_row(row)
        matched = bool(row.get("matched_ground_truth", False))
        match_key = str(row.get("match_key", ""))
        matched_truth = ground_truth_index.get(match_key) if match_key else None
        match_resolves = (not matched) or matched_truth is not None
        truth_errors = _evaluation_ground_truth_consistency_errors(
            row,
            matched_truth,
        )
        realization_errors = _evaluation_realization_missing_row_errors(row)
        route_adoption_errors = _evaluation_route_adoption_row_errors(row)
        quality_control_errors = _evaluation_quality_control_row_errors(row)
        checks.append(
            _check(
                f"optional_evaluation_row_{idx}_schema_valid",
                "optional_artifacts",
                "evaluation row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
        checks.append(
            _check(
                f"optional_evaluation_row_{idx}_ground_truth_match",
                "optional_artifacts",
                "matched evaluation row resolves against copied route truth",
                match_key or "unmatched",
                match_resolves,
                errors=()
                if match_resolves
                else (f"missing copied route truth match: {match_key}",),
            )
        )
        checks.append(
            _check(
                f"optional_evaluation_row_{idx}_ground_truth_primitives",
                "optional_artifacts",
                "evaluation ground-truth primitive fields match copied route truth",
                "; ".join(truth_errors) if truth_errors else "ok",
                not truth_errors,
                errors=truth_errors,
            )
        )
        checks.append(
            _check(
                f"optional_evaluation_row_{idx}_realization_missing_fields",
                "optional_artifacts",
                "evaluation row preserves realization-missing primitive diagnostics",
                "; ".join(realization_errors) if realization_errors else "ok",
                not realization_errors,
                errors=realization_errors,
            )
        )
        checks.append(
            _check(
                f"optional_evaluation_row_{idx}_route_adoption_fields",
                "optional_artifacts",
                "evaluation row preserves LLM route-adoption readiness fields",
                (
                    "; ".join(route_adoption_errors)
                    if route_adoption_errors
                    else "ok"
                ),
                not route_adoption_errors,
                errors=route_adoption_errors,
            )
        )
        checks.append(
            _check(
                f"optional_evaluation_row_{idx}_quality_control_fields",
                "optional_artifacts",
                "evaluation row preserves quality-control policy fields",
                (
                    "; ".join(quality_control_errors)
                    if quality_control_errors
                    else "ok"
                ),
                not quality_control_errors,
                errors=quality_control_errors,
            )
        )
    return checks


def _optional_evaluation_rows_for_summary(
    bundle_dir: Path,
) -> tuple[dict[str, Any], ...]:
    rows_jsonl_path = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_evaluation"
        / "formalization_gap_planner_evaluation.jsonl"
    )
    if not rows_jsonl_path.exists():
        return tuple()
    rows, errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    return tuple() if errors else tuple(rows)


def _kernel_verification_witness_count(row: Mapping[str, Any]) -> int:
    witnesses = row.get("kernel_verification_witnesses", [])
    if isinstance(witnesses, (list, tuple)):
        return sum(1 for witness in witnesses if isinstance(witness, Mapping))
    if isinstance(witnesses, Mapping):
        return 1
    return 0


def _optional_ablation_study_rows_for_summary(
    bundle_dir: Path,
) -> tuple[dict[str, Any], ...]:
    rows_jsonl_path = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_ablation_study"
        / "formalization_gap_planner_ablation_study.jsonl"
    )
    if not rows_jsonl_path.exists():
        return tuple()
    rows, errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    return tuple() if errors else tuple(rows)


def _evaluation_realization_missing_row_errors(
    row: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    for field_name in (
        "realization_missing_selected_formal_primitives",
        "realization_missing_delta_alignment_primitives",
        "realization_cost_hint_baseline_primitives",
        "realization_omitted_cost_hint_primitives",
    ):
        if field_name not in row:
            errors.append(f"{field_name} missing")
            continue
        value = row.get(field_name)
        if not isinstance(value, (list, tuple, set)):
            errors.append(f"{field_name} is not an array")
    missing_selected = _str_tuple(
        row.get("realization_missing_selected_formal_primitives", [])
    )
    missing_delta = _str_tuple(
        row.get("realization_missing_delta_alignment_primitives", [])
    )
    omitted_cost_hint = _str_tuple(
        row.get("realization_omitted_cost_hint_primitives", [])
    )
    if "realization_cost_hint_baseline_coverage_complete" not in row:
        errors.append("realization_cost_hint_baseline_coverage_complete missing")
    elif not isinstance(
        row.get("realization_cost_hint_baseline_coverage_complete"),
        bool,
    ):
        errors.append("realization_cost_hint_baseline_coverage_complete is not a boolean")
    if bool(row.get("realization_coverage_complete", False)) and (
        missing_selected or missing_delta
    ):
        errors.append(
            "realization_coverage_complete is true but missing primitives are nonempty"
        )
    if (
        bool(row.get("realization_cost_hint_baseline_coverage_complete", True))
        and omitted_cost_hint
    ):
        errors.append(
            "realization_cost_hint_baseline_coverage_complete is true but omitted cost-hint primitives are nonempty"
        )
    return tuple(errors)


def _evaluation_route_adoption_row_errors(
    row: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    status_field = "llm_route_planner_route_adoption_status"
    blockers_field = "llm_route_planner_route_adoption_blockers"
    if status_field not in row:
        errors.append(f"{status_field} missing")
        status = ""
    else:
        status_value = row.get(status_field, "")
        if not isinstance(status_value, str):
            errors.append(f"{status_field} is not a string")
        status = str(status_value).strip()
    if blockers_field not in row:
        errors.append(f"{blockers_field} missing")
        blockers = tuple()
    else:
        blockers_value = row.get(blockers_field)
        if not isinstance(blockers_value, (list, tuple, set)):
            errors.append(f"{blockers_field} is not an array")
        blockers = _str_tuple(blockers_value if blockers_value is not None else [])
    valid_statuses = {
        ROUTE_ADOPTION_READY_STATUS,
        ROUTE_ADOPTION_PENDING_STATUS,
        ROUTE_ADOPTION_AWAITING_STATUS,
        ROUTE_ADOPTION_REJECTED_STATUS,
    }
    if status and status not in valid_statuses:
        errors.append(f"unknown llm route-adoption status: {status}")
    unknown_blockers = sorted(set(blockers) - set(ROUTE_ADOPTION_BLOCKER_VALUES))
    if unknown_blockers:
        errors.append(
            "unknown llm route-adoption blockers: " + ", ".join(unknown_blockers)
        )
    if bool(row.get("llm_route_planner_trace_present", False)) and not status:
        errors.append("LLM route-planner trace is present but route-adoption status is empty")
    if status == ROUTE_ADOPTION_READY_STATUS and blockers:
        errors.append("ready route-adoption status must not carry blockers")
    if status == ROUTE_ADOPTION_PENDING_STATUS and not blockers:
        errors.append("pending route-adoption status must explain at least one blocker")
    return tuple(errors)


def _evaluation_quality_control_row_errors(
    row: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    raw_controls = row.get("quality_controls", {})
    if not isinstance(raw_controls, dict):
        errors.append("quality_controls is not an object")
        controls: dict[str, tuple[str, ...]] = {}
    else:
        controls = _quality_controls_from_evaluation_row(row)
        unknown_fields = sorted(set(raw_controls) - set(QUALITY_CONTROL_FIELDS))
        if unknown_fields:
            errors.append("unknown quality_control fields: " + ", ".join(unknown_fields))
    expected_present = bool(controls)
    observed_present = row.get("quality_controls_present", False)
    if not isinstance(observed_present, bool):
        errors.append("quality_controls_present is not a boolean")
    elif observed_present != expected_present:
        errors.append(
            "quality_controls_present mismatch: "
            f"observed={observed_present} expected={expected_present}"
        )
    expected_fields = tuple(sorted(controls))
    observed_fields = _str_tuple(row.get("quality_control_fields", []))
    if observed_fields != expected_fields:
        errors.append(
            "quality_control_fields mismatch: "
            f"observed={sorted(observed_fields)} expected={sorted(expected_fields)}"
        )
    comparisons = (
        ("quality_control_resource_contract_ids", "resource_contract_ids"),
        (
            "quality_control_response_validation_signals",
            "response_validation_signals",
        ),
        ("quality_control_stop_conditions", "stop_conditions"),
    )
    for row_field_name, control_field_name in comparisons:
        observed = _str_tuple(row.get(row_field_name, []))
        expected = controls.get(control_field_name, tuple())
        if observed != expected:
            errors.append(
                f"{row_field_name} mismatch: observed={sorted(observed)} "
                f"expected={sorted(expected)}"
            )
    return tuple(errors)


def _evaluation_realization_missing_manifest_errors(
    manifest: dict[str, Any],
    rows: list[dict[str, Any]],
) -> tuple[str, ...]:
    errors: list[str] = []
    expected_selected_total = sum(
        len(_str_tuple(row.get("realization_missing_selected_formal_primitives", [])))
        for row in rows
    )
    expected_delta_total = sum(
        len(_str_tuple(row.get("realization_missing_delta_alignment_primitives", [])))
        for row in rows
    )
    expected_cost_hint_baseline_total = sum(
        len(_str_tuple(row.get("realization_cost_hint_baseline_primitives", [])))
        for row in rows
    )
    expected_omitted_cost_hint_total = sum(
        len(_str_tuple(row.get("realization_omitted_cost_hint_primitives", [])))
        for row in rows
    )
    expected_incomplete_cost_hint_rows = sum(
        1
        for row in _dict_tuple(rows)
        if row.get("realization_cost_hint_baseline_coverage_complete") is False
    )
    expected_selected = _evaluation_realization_missing_selected_from_rows(rows)
    expected_delta = _evaluation_realization_missing_delta_from_rows(rows)
    expected_cost_hint_baseline = _evaluation_realization_cost_hint_baseline_from_rows(rows)
    expected_omitted_cost_hint = _evaluation_realization_omitted_cost_hint_from_rows(rows)
    expected_by_route = _evaluation_realization_missing_route_keys(
        _evaluation_realization_missing_by_route_from_rows(rows)
    )
    observed_by_route = _evaluation_realization_missing_route_keys(
        _dict_tuple(manifest.get("realization_missing_primitives_by_route", []))
    )
    observed_selected_total = int(
        manifest.get("n_realization_missing_selected_formal_primitives", -1) or 0
    )
    observed_delta_total = int(
        manifest.get("n_realization_missing_delta_alignment_primitives", -1) or 0
    )
    observed_cost_hint_baseline_total = int(
        manifest.get("n_realization_cost_hint_baseline_primitives", -1) or 0
    )
    observed_omitted_cost_hint_total = int(
        manifest.get("n_realization_omitted_cost_hint_primitives", -1) or 0
    )
    observed_incomplete_cost_hint_rows = int(
        manifest.get("n_rows_with_incomplete_cost_hint_baseline_coverage", -1) or 0
    )
    observed_selected = set(
        _str_tuple(manifest.get("realization_missing_selected_formal_primitives", []))
    )
    observed_delta = set(
        _str_tuple(manifest.get("realization_missing_delta_alignment_primitives", []))
    )
    observed_cost_hint_baseline = set(
        _str_tuple(manifest.get("realization_cost_hint_baseline_primitives", []))
    )
    observed_omitted_cost_hint = set(
        _str_tuple(manifest.get("realization_omitted_cost_hint_primitives", []))
    )
    if observed_selected_total != expected_selected_total:
        errors.append(
            "n_realization_missing_selected_formal_primitives mismatch: "
            f"observed={observed_selected_total} expected={expected_selected_total}"
        )
    if observed_delta_total != expected_delta_total:
        errors.append(
            "n_realization_missing_delta_alignment_primitives mismatch: "
            f"observed={observed_delta_total} expected={expected_delta_total}"
        )
    if observed_cost_hint_baseline_total != expected_cost_hint_baseline_total:
        errors.append(
            "n_realization_cost_hint_baseline_primitives mismatch: "
            f"observed={observed_cost_hint_baseline_total} expected={expected_cost_hint_baseline_total}"
        )
    if observed_omitted_cost_hint_total != expected_omitted_cost_hint_total:
        errors.append(
            "n_realization_omitted_cost_hint_primitives mismatch: "
            f"observed={observed_omitted_cost_hint_total} expected={expected_omitted_cost_hint_total}"
        )
    if observed_incomplete_cost_hint_rows != expected_incomplete_cost_hint_rows:
        errors.append(
            "n_rows_with_incomplete_cost_hint_baseline_coverage mismatch: "
            f"observed={observed_incomplete_cost_hint_rows} expected={expected_incomplete_cost_hint_rows}"
        )
    if observed_selected != set(expected_selected):
        errors.append(
            "realization_missing_selected_formal_primitives mismatch: "
            f"observed={sorted(observed_selected)} expected={sorted(expected_selected)}"
        )
    if observed_delta != set(expected_delta):
        errors.append(
            "realization_missing_delta_alignment_primitives mismatch: "
            f"observed={sorted(observed_delta)} expected={sorted(expected_delta)}"
        )
    if observed_cost_hint_baseline != set(expected_cost_hint_baseline):
        errors.append(
            "realization_cost_hint_baseline_primitives mismatch: "
            f"observed={sorted(observed_cost_hint_baseline)} expected={sorted(expected_cost_hint_baseline)}"
        )
    if observed_omitted_cost_hint != set(expected_omitted_cost_hint):
        errors.append(
            "realization_omitted_cost_hint_primitives mismatch: "
            f"observed={sorted(observed_omitted_cost_hint)} expected={sorted(expected_omitted_cost_hint)}"
        )
    if observed_by_route != expected_by_route:
        errors.append(
            "realization_missing_primitives_by_route mismatch: "
            f"observed={sorted(observed_by_route)} expected={sorted(expected_by_route)}"
        )
    return tuple(errors)


def _evaluation_residual_goal_context_manifest_errors(
    manifest: dict[str, Any],
    rows: list[dict[str, Any]],
) -> tuple[str, ...]:
    errors: list[str] = []
    row_tuple = _dict_tuple(rows)

    def row_count(row: dict[str, Any], field_name: str) -> int:
        value = _int_or_none(row.get(field_name))
        if value is None or value < 0:
            return 0
        return value

    expected_counts = {
        "n_rows_with_llm_route_planner_residual_goal_contexts": sum(
            1
            for row in row_tuple
            if row_count(row, "llm_route_planner_residual_goal_context_count") > 0
        ),
        "n_llm_route_planner_residual_goal_contexts": sum(
            row_count(row, "llm_route_planner_residual_goal_context_count")
            for row in row_tuple
        ),
        "n_llm_route_planner_residual_goal_context_source_refs": sum(
            row_count(row, "llm_route_planner_residual_goal_context_source_ref_count")
            for row in row_tuple
        ),
        "n_llm_route_planner_residual_goal_context_provenance_values": sum(
            row_count(row, "llm_route_planner_residual_goal_context_provenance_count")
            for row in row_tuple
        ),
        "n_llm_route_planner_residual_goals_with_context": sum(
            row_count(row, "llm_route_planner_residual_goals_with_context_count")
            for row in row_tuple
        ),
        "n_llm_route_planner_residual_goals_without_context": sum(
            len(
                _str_tuple(
                    row.get(
                        "llm_route_planner_residual_goals_without_context",
                        [],
                    )
                )
            )
            for row in row_tuple
        ),
    }
    for field_name, expected in expected_counts.items():
        observed = _int_or_none(manifest.get(field_name))
        if observed != expected:
            errors.append(
                f"{field_name} mismatch: observed={observed} expected={expected}"
            )
    return tuple(errors)


def _evaluation_route_option_selection_counts_from_rows(
    rows: Iterable[dict[str, Any]],
) -> dict[str, int]:
    row_tuple = _dict_tuple(rows)

    def row_count(row: dict[str, Any], field_name: str) -> int:
        value = _int_or_none(row.get(field_name))
        if value is None or value < 0:
            return 0
        return value

    return {
        "n_rows_with_llm_route_planner_route_option_selection_brief": sum(
            1
            for row in row_tuple
            if row.get("llm_route_planner_route_option_selection_brief_present")
            is True
        ),
        "n_llm_route_planner_route_option_selection_candidate_options": sum(
            row_count(
                row,
                "llm_route_planner_route_option_selection_candidate_count",
            )
            for row in row_tuple
        ),
        "n_llm_route_planner_route_option_selection_candidate_primitives": sum(
            row_count(
                row,
                "llm_route_planner_route_option_selection_candidate_primitive_count",
            )
            for row in row_tuple
        ),
        "n_llm_route_planner_route_option_selection_candidates_with_residual_goals": sum(
            row_count(
                row,
                "llm_route_planner_route_option_selection_candidates_with_residual_goals",
            )
            for row in row_tuple
        ),
        "n_llm_route_planner_route_option_selection_candidate_residual_goals": sum(
            row_count(
                row,
                "llm_route_planner_route_option_selection_candidate_residual_goal_count",
            )
            for row in row_tuple
        ),
        "n_llm_route_planner_route_option_selection_lower_bound_residual_goals": sum(
            row_count(
                row,
                "llm_route_planner_route_option_selection_lower_bound_residual_goal_count",
            )
            for row in row_tuple
        ),
        "n_rows_with_llm_route_planner_route_option_selected_route_option": sum(
            1
            for row in row_tuple
            if str(
                row.get(
                    "llm_route_planner_route_option_selected_route_option_id",
                    "",
                )
                or ""
            ).strip()
        ),
        "n_llm_route_planner_route_option_selection_minimal_delta_selected_residual_goals": sum(
            row_count(
                row,
                "llm_route_planner_route_option_selection_minimal_delta_selected_residual_goal_count",
            )
            for row in row_tuple
        ),
        "n_llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta": sum(
            1
            for row in row_tuple
            if row.get("llm_route_planner_route_option_selection_brief_present")
            is True
            and row.get(
                "llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta"
            )
            is True
        ),
        "n_llm_route_planner_route_option_selection_lower_bound_mismatches_minimal_delta": sum(
            1
            for row in row_tuple
            if row.get("llm_route_planner_route_option_selection_brief_present")
            is True
            and row.get(
                "llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta"
            )
            is not True
        ),
        "n_llm_route_planner_route_option_selected_matches_lower_bound": sum(
            1
            for row in row_tuple
            if str(
                row.get(
                    "llm_route_planner_route_option_selected_route_option_id",
                    "",
                )
                or ""
            ).strip()
            and row.get(
                "llm_route_planner_route_option_selected_matches_lower_bound"
            )
            is True
        ),
        "n_llm_route_planner_route_option_selected_mismatches_lower_bound": sum(
            1
            for row in row_tuple
            if str(
                row.get(
                    "llm_route_planner_route_option_selected_route_option_id",
                    "",
                )
                or ""
            ).strip()
            and str(
                row.get(
                    "llm_route_planner_route_option_selection_lower_bound_selected_route_option_id",
                    "",
                )
                or ""
            ).strip()
            and row.get(
                "llm_route_planner_route_option_selected_matches_lower_bound"
            )
            is not True
        ),
        "n_llm_route_planner_route_option_selected_matches_minimal_delta": sum(
            1
            for row in row_tuple
            if str(
                row.get(
                    "llm_route_planner_route_option_selected_route_option_id",
                    "",
                )
                or ""
            ).strip()
            and row.get(
                "llm_route_planner_route_option_selected_matches_minimal_delta"
            )
            is True
        ),
        "n_llm_route_planner_route_option_selected_mismatches_minimal_delta": sum(
            1
            for row in row_tuple
            if str(
                row.get(
                    "llm_route_planner_route_option_selected_route_option_id",
                    "",
                )
                or ""
            ).strip()
            and str(
                row.get("minimal_delta_selected_route_option_id", "") or ""
            ).strip()
            and row.get(
                "llm_route_planner_route_option_selected_matches_minimal_delta"
            )
            is not True
        ),
    }


def _evaluation_route_option_selection_manifest_errors(
    manifest: dict[str, Any],
    rows: list[dict[str, Any]],
) -> tuple[str, ...]:
    errors: list[str] = []
    expected_counts = _evaluation_route_option_selection_counts_from_rows(rows)
    for field_name, expected in expected_counts.items():
        observed = _int_or_none(manifest.get(field_name))
        if observed != expected:
            errors.append(
                f"{field_name} mismatch: observed={observed} expected={expected}"
            )
    return tuple(errors)


def _evaluation_quality_control_manifest_errors(
    manifest: dict[str, Any],
    rows: list[dict[str, Any]],
) -> tuple[str, ...]:
    errors: list[str] = []
    row_tuple = _dict_tuple(rows)
    expected_rows_with = sum(
        1 for row in row_tuple if _quality_controls_from_evaluation_row(row)
    )
    expected_field_total = sum(
        len(_quality_controls_from_evaluation_row(row)) for row in row_tuple
    )
    expected_fields = set(_evaluation_quality_control_fields_from_rows(row_tuple))
    expected_resource_contract_ids = set(
        _evaluation_quality_control_values_from_rows(
            row_tuple,
            "resource_contract_ids",
        )
    )
    expected_response_validation_signals = set(
        _evaluation_quality_control_values_from_rows(
            row_tuple,
            "response_validation_signals",
        )
    )
    expected_stop_conditions = set(
        _evaluation_quality_control_values_from_rows(row_tuple, "stop_conditions")
    )
    observed_rows_with = int(
        manifest.get("n_rows_with_quality_controls", -1) or 0
    )
    observed_field_total = int(
        manifest.get("n_quality_control_fields", -1) or 0
    )
    observed_fields = set(_str_tuple(manifest.get("quality_control_fields", [])))
    observed_resource_contract_ids = set(
        _str_tuple(manifest.get("quality_control_resource_contract_ids", []))
    )
    observed_response_validation_signals = set(
        _str_tuple(
            manifest.get("quality_control_response_validation_signals", [])
        )
    )
    observed_stop_conditions = set(
        _str_tuple(manifest.get("quality_control_stop_conditions", []))
    )
    if observed_rows_with != expected_rows_with:
        errors.append(
            "n_rows_with_quality_controls mismatch: "
            f"observed={observed_rows_with} expected={expected_rows_with}"
        )
    if observed_field_total != expected_field_total:
        errors.append(
            "n_quality_control_fields mismatch: "
            f"observed={observed_field_total} expected={expected_field_total}"
        )
    if observed_fields != expected_fields:
        errors.append(
            "quality_control_fields mismatch: "
            f"observed={sorted(observed_fields)} expected={sorted(expected_fields)}"
        )
    if observed_resource_contract_ids != expected_resource_contract_ids:
        errors.append(
            "quality_control_resource_contract_ids mismatch: "
            f"observed={sorted(observed_resource_contract_ids)} "
            f"expected={sorted(expected_resource_contract_ids)}"
        )
    if observed_response_validation_signals != expected_response_validation_signals:
        errors.append(
            "quality_control_response_validation_signals mismatch: "
            f"observed={sorted(observed_response_validation_signals)} "
            f"expected={sorted(expected_response_validation_signals)}"
        )
    if observed_stop_conditions != expected_stop_conditions:
        errors.append(
            "quality_control_stop_conditions mismatch: "
            f"observed={sorted(observed_stop_conditions)} "
            f"expected={sorted(expected_stop_conditions)}"
        )
    observed_by_field = manifest.get("evaluation_by_quality_control_field", {})
    observed_by_field = observed_by_field if isinstance(observed_by_field, dict) else {}
    for field_name in expected_fields:
        field_rows = [
            row
            for row in row_tuple
            if field_name in _quality_controls_from_evaluation_row(row)
        ]
        expected_values = set(
            value
            for row in field_rows
            for value in _quality_controls_from_evaluation_row(row).get(
                field_name,
                tuple(),
            )
        )
        observed_summary = observed_by_field.get(field_name, {})
        observed_summary = (
            observed_summary if isinstance(observed_summary, dict) else {}
        )
        observed_n_rows = int(observed_summary.get("n_rows", -1) or 0)
        observed_n_values = int(observed_summary.get("n_values", -1) or 0)
        observed_values = set(_str_tuple(observed_summary.get("values", [])))
        if observed_n_rows != len(field_rows):
            errors.append(
                f"evaluation_by_quality_control_field.{field_name}.n_rows "
                f"mismatch: observed={observed_n_rows} expected={len(field_rows)}"
            )
        if observed_n_values != len(expected_values):
            errors.append(
                f"evaluation_by_quality_control_field.{field_name}.n_values "
                f"mismatch: observed={observed_n_values} expected={len(expected_values)}"
            )
        if observed_values != expected_values:
            errors.append(
                f"evaluation_by_quality_control_field.{field_name}.values "
                f"mismatch: observed={sorted(observed_values)} "
                f"expected={sorted(expected_values)}"
            )
    if set(observed_by_field) != expected_fields:
        errors.append(
            "evaluation_by_quality_control_field keys mismatch: "
            f"observed={sorted(observed_by_field)} expected={sorted(expected_fields)}"
        )
    return tuple(errors)


def _evaluation_route_adoption_manifest_errors(
    manifest: dict[str, Any],
    rows: list[dict[str, Any]],
) -> tuple[str, ...]:
    errors: list[str] = []
    status_counts = _evaluation_route_adoption_status_counts_from_rows(rows)
    expected_status_count = sum(status_counts.values())
    expected_ready = status_counts.get("READY_FOR_STANDALONE_REPLAY", 0)
    expected_pending = status_counts.get(
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION",
        0,
    )
    expected_awaiting = status_counts.get("AWAITING_LLM_ROUTE_PLANNER_RESPONSE", 0)
    expected_rejected = status_counts.get("REJECTED_LLM_ROUTE_PLAN", 0)
    expected_blocker_total = sum(
        len(_str_tuple(row.get("llm_route_planner_route_adoption_blockers", [])))
        for row in _dict_tuple(rows)
    )
    expected_quality_control_blockers = sum(
        1
        for row in _dict_tuple(rows)
        if "quality_control_obligations_pending"
        in _str_tuple(row.get("llm_route_planner_route_adoption_blockers", []))
    )
    expected_source_grounding_blockers = sum(
        1
        for row in _dict_tuple(rows)
        if "source_grounding_obligations_pending"
        in _str_tuple(row.get("llm_route_planner_route_adoption_blockers", []))
    )
    expected_blockers = set(_evaluation_route_adoption_blockers_from_rows(rows))
    expected_blocker_counts = _evaluation_route_adoption_blocker_counts_from_rows(rows)
    expected_by_blocker = _evaluation_route_adoption_blocker_summary_from_rows(rows)
    expected_precondition_rows = sum(
        1
        for row in _dict_tuple(rows)
        if row.get("llm_route_planner_route_adoption_precondition_present") is True
    )
    expected_blocking_precondition_rows = sum(
        1
        for row in _dict_tuple(rows)
        if row.get(
            "llm_route_planner_route_adoption_precondition_blocked_before_response"
        )
        is True
    )
    expected_precondition_known_blockers = sum(
        len(
            _str_tuple(
                row.get(
                    "llm_route_planner_route_adoption_precondition_known_blockers",
                    [],
                )
            )
        )
        for row in _dict_tuple(rows)
    )
    expected_precondition_required_fields = sum(
        len(
            _str_tuple(
                row.get(
                    "llm_route_planner_route_adoption_precondition_required_response_fields",
                    [],
                )
            )
        )
        for row in _dict_tuple(rows)
    )
    expected_precondition_target_primitives = sum(
        len(
            _str_tuple(
                row.get(
                    "llm_route_planner_route_adoption_precondition_target_primitives",
                    [],
                )
            )
        )
        for row in _dict_tuple(rows)
    )
    expected_precondition_blocker_values = set(
        _evaluation_route_adoption_precondition_values_from_rows(
            rows,
            "llm_route_planner_route_adoption_precondition_known_blockers",
        )
    )
    expected_precondition_required_field_values = set(
        _evaluation_route_adoption_precondition_values_from_rows(
            rows,
            "llm_route_planner_route_adoption_precondition_required_response_fields",
        )
    )
    expected_precondition_target_primitive_values = set(
        _evaluation_route_adoption_precondition_values_from_rows(
            rows,
            "llm_route_planner_route_adoption_precondition_target_primitives",
        )
    )
    observed_status_count = int(
        manifest.get("n_rows_with_llm_route_planner_route_adoption_status", -1) or 0
    )
    observed_ready = int(manifest.get("n_rows_ready_for_route_adoption", -1) or 0)
    observed_pending = int(
        manifest.get("n_rows_pending_refinement_before_route_adoption", -1) or 0
    )
    observed_awaiting = int(
        manifest.get("n_rows_awaiting_llm_route_planner_response", -1) or 0
    )
    observed_rejected = int(manifest.get("n_rows_rejected_llm_route_plan", -1) or 0)
    observed_blocker_total = int(manifest.get("n_llm_route_adoption_blockers", -1) or 0)
    observed_quality_control_blockers = int(
        manifest.get(
            "n_llm_route_adoption_pending_quality_control_blockers",
            -1,
        )
        or 0
    )
    observed_source_grounding_blockers = int(
        manifest.get(
            "n_llm_route_adoption_pending_source_grounding_blockers",
            -1,
        )
        or 0
    )
    observed_blockers = set(_str_tuple(manifest.get("llm_route_adoption_blockers", [])))
    observed_precondition_rows = int(
        manifest.get(
            "n_rows_with_llm_route_planner_route_adoption_preconditions",
            -1,
        )
        or 0
    )
    observed_blocking_precondition_rows = int(
        manifest.get(
            "n_rows_with_llm_route_planner_blocking_route_adoption_preconditions",
            -1,
        )
        or 0
    )
    observed_precondition_known_blockers = int(
        manifest.get(
            "n_llm_route_planner_route_adoption_precondition_known_blockers",
            -1,
        )
        or 0
    )
    observed_precondition_required_fields = int(
        manifest.get(
            "n_llm_route_planner_route_adoption_precondition_required_response_fields",
            -1,
        )
        or 0
    )
    observed_precondition_target_primitives = int(
        manifest.get(
            "n_llm_route_planner_route_adoption_precondition_target_primitives",
            -1,
        )
        or 0
    )
    observed_precondition_blocker_values = set(
        _str_tuple(
            manifest.get(
                "llm_route_planner_route_adoption_precondition_known_blockers",
                [],
            )
        )
    )
    observed_precondition_required_field_values = set(
        _str_tuple(
            manifest.get(
                "llm_route_planner_route_adoption_precondition_required_response_fields",
                [],
            )
        )
    )
    observed_precondition_target_primitive_values = set(
        _str_tuple(
            manifest.get(
                "llm_route_planner_route_adoption_precondition_target_primitives",
                [],
            )
        )
    )
    observed_blocker_counts = _int_mapping(
        manifest.get("llm_route_adoption_blocker_counts", {})
    )
    observed_by_status = manifest.get("evaluation_by_llm_route_adoption_status", {})
    observed_by_status = observed_by_status if isinstance(observed_by_status, dict) else {}
    observed_status_keys = {
        str(key)
        for key, value in observed_by_status.items()
        if isinstance(value, dict) and int(value.get("n_rows", 0) or 0) > 0
    }
    observed_by_blocker = manifest.get("evaluation_by_llm_route_adoption_blocker", {})
    observed_by_blocker = (
        observed_by_blocker if isinstance(observed_by_blocker, dict) else {}
    )
    observed_blocker_keys = {
        str(key)
        for key, value in observed_by_blocker.items()
        if isinstance(value, dict) and int(value.get("n_rows", 0) or 0) > 0
    }
    if observed_status_count != expected_status_count:
        errors.append(
            "n_rows_with_llm_route_planner_route_adoption_status mismatch: "
            f"observed={observed_status_count} expected={expected_status_count}"
        )
    if observed_ready != expected_ready:
        errors.append(
            "n_rows_ready_for_route_adoption mismatch: "
            f"observed={observed_ready} expected={expected_ready}"
        )
    if observed_pending != expected_pending:
        errors.append(
            "n_rows_pending_refinement_before_route_adoption mismatch: "
            f"observed={observed_pending} expected={expected_pending}"
        )
    if observed_awaiting != expected_awaiting:
        errors.append(
            "n_rows_awaiting_llm_route_planner_response mismatch: "
            f"observed={observed_awaiting} expected={expected_awaiting}"
        )
    if observed_rejected != expected_rejected:
        errors.append(
            "n_rows_rejected_llm_route_plan mismatch: "
            f"observed={observed_rejected} expected={expected_rejected}"
        )
    if observed_blocker_total != expected_blocker_total:
        errors.append(
            "n_llm_route_adoption_blockers mismatch: "
            f"observed={observed_blocker_total} expected={expected_blocker_total}"
        )
    if observed_quality_control_blockers != expected_quality_control_blockers:
        errors.append(
            "n_llm_route_adoption_pending_quality_control_blockers mismatch: "
            f"observed={observed_quality_control_blockers} "
            f"expected={expected_quality_control_blockers}"
        )
    if observed_source_grounding_blockers != expected_source_grounding_blockers:
        errors.append(
            "n_llm_route_adoption_pending_source_grounding_blockers mismatch: "
            f"observed={observed_source_grounding_blockers} "
            f"expected={expected_source_grounding_blockers}"
        )
    if observed_blockers != expected_blockers:
        errors.append(
            "llm_route_adoption_blockers mismatch: "
            f"observed={sorted(observed_blockers)} expected={sorted(expected_blockers)}"
        )
    if observed_precondition_rows != expected_precondition_rows:
        errors.append(
            "n_rows_with_llm_route_planner_route_adoption_preconditions mismatch: "
            f"observed={observed_precondition_rows} "
            f"expected={expected_precondition_rows}"
        )
    if observed_blocking_precondition_rows != expected_blocking_precondition_rows:
        errors.append(
            "n_rows_with_llm_route_planner_blocking_route_adoption_preconditions mismatch: "
            f"observed={observed_blocking_precondition_rows} "
            f"expected={expected_blocking_precondition_rows}"
        )
    if observed_precondition_known_blockers != expected_precondition_known_blockers:
        errors.append(
            "n_llm_route_planner_route_adoption_precondition_known_blockers mismatch: "
            f"observed={observed_precondition_known_blockers} "
            f"expected={expected_precondition_known_blockers}"
        )
    if observed_precondition_required_fields != expected_precondition_required_fields:
        errors.append(
            "n_llm_route_planner_route_adoption_precondition_required_response_fields mismatch: "
            f"observed={observed_precondition_required_fields} "
            f"expected={expected_precondition_required_fields}"
        )
    if observed_precondition_target_primitives != expected_precondition_target_primitives:
        errors.append(
            "n_llm_route_planner_route_adoption_precondition_target_primitives mismatch: "
            f"observed={observed_precondition_target_primitives} "
            f"expected={expected_precondition_target_primitives}"
        )
    if observed_precondition_blocker_values != expected_precondition_blocker_values:
        errors.append(
            "llm_route_planner_route_adoption_precondition_known_blockers mismatch: "
            f"observed={sorted(observed_precondition_blocker_values)} "
            f"expected={sorted(expected_precondition_blocker_values)}"
        )
    if (
        observed_precondition_required_field_values
        != expected_precondition_required_field_values
    ):
        errors.append(
            "llm_route_planner_route_adoption_precondition_required_response_fields mismatch: "
            f"observed={sorted(observed_precondition_required_field_values)} "
            f"expected={sorted(expected_precondition_required_field_values)}"
        )
    if (
        observed_precondition_target_primitive_values
        != expected_precondition_target_primitive_values
    ):
        errors.append(
            "llm_route_planner_route_adoption_precondition_target_primitives mismatch: "
            f"observed={sorted(observed_precondition_target_primitive_values)} "
            f"expected={sorted(expected_precondition_target_primitive_values)}"
        )
    if observed_blocker_counts != expected_blocker_counts:
        errors.append(
            "llm_route_adoption_blocker_counts mismatch: "
            f"observed={observed_blocker_counts} expected={expected_blocker_counts}"
        )
    if observed_status_keys != set(status_counts):
        errors.append(
            "evaluation_by_llm_route_adoption_status keys mismatch: "
            f"observed={sorted(observed_status_keys)} expected={sorted(status_counts)}"
        )
    if observed_blocker_keys != set(expected_by_blocker):
        errors.append(
            "evaluation_by_llm_route_adoption_blocker keys mismatch: "
            f"observed={sorted(observed_blocker_keys)} "
            f"expected={sorted(expected_by_blocker)}"
        )
    for status, expected_count in status_counts.items():
        summary = observed_by_status.get(status, {})
        if not isinstance(summary, dict):
            errors.append(f"evaluation_by_llm_route_adoption_status[{status}] missing")
            continue
        observed_count = int(summary.get("n_rows", -1) or 0)
        observed_status_blockers = int(
            summary.get("n_route_adoption_blockers", -1) or 0
        )
        expected_status_blockers = sum(
            len(_str_tuple(row.get("llm_route_planner_route_adoption_blockers", [])))
            for row in _dict_tuple(rows)
            if str(row.get("llm_route_planner_route_adoption_status", "")).strip()
            == status
        )
        if observed_count != expected_count:
            errors.append(
                f"evaluation_by_llm_route_adoption_status[{status}].n_rows "
                f"mismatch: observed={observed_count} expected={expected_count}"
            )
        if observed_status_blockers != expected_status_blockers:
            errors.append(
                "evaluation_by_llm_route_adoption_status"
                f"[{status}].n_route_adoption_blockers mismatch: "
                f"observed={observed_status_blockers} "
                f"expected={expected_status_blockers}"
            )
    for blocker, expected_summary in expected_by_blocker.items():
        summary = observed_by_blocker.get(blocker, {})
        if not isinstance(summary, dict):
            errors.append(f"evaluation_by_llm_route_adoption_blocker[{blocker}] missing")
            continue
        observed_rows = int(summary.get("n_rows", -1) or 0)
        observed_occurrences = int(summary.get("n_blocker_occurrences", -1) or 0)
        observed_by_blocker_status = _int_mapping(
            summary.get("by_route_adoption_status", {})
        )
        expected_by_blocker_status = _int_mapping(
            expected_summary.get("by_route_adoption_status", {})
        )
        if observed_rows != int(expected_summary.get("n_rows", 0) or 0):
            errors.append(
                f"evaluation_by_llm_route_adoption_blocker[{blocker}].n_rows "
                f"mismatch: observed={observed_rows} "
                f"expected={expected_summary.get('n_rows')}"
            )
        if observed_occurrences != int(
            expected_summary.get("n_blocker_occurrences", 0) or 0
        ):
            errors.append(
                "evaluation_by_llm_route_adoption_blocker"
                f"[{blocker}].n_blocker_occurrences mismatch: "
                f"observed={observed_occurrences} "
                f"expected={expected_summary.get('n_blocker_occurrences')}"
            )
        if observed_by_blocker_status != expected_by_blocker_status:
            errors.append(
                "evaluation_by_llm_route_adoption_blocker"
                f"[{blocker}].by_route_adoption_status mismatch: "
                f"observed={observed_by_blocker_status} "
                f"expected={expected_by_blocker_status}"
            )
    return tuple(errors)


def _ablation_study_route_adoption_manifest_errors(
    manifest: dict[str, Any],
    rows: list[dict[str, Any]],
) -> tuple[str, ...]:
    errors: list[str] = []
    expected_variant = _ablation_study_largest_route_adoption_drop_variant(rows)
    observed_variant = str(
        manifest.get("largest_route_adoption_ready_drop_variant", "")
    ).strip()
    metric_rows = sum(
        1 for row in rows if _ablation_study_row_has_route_adoption_metrics(row)
    )
    if rows and not observed_variant:
        errors.append("largest_route_adoption_ready_drop_variant missing")
    if expected_variant and observed_variant != expected_variant:
        errors.append(
            "largest_route_adoption_ready_drop_variant mismatch: "
            f"observed={observed_variant} expected={expected_variant}"
        )
    if metric_rows != len(rows):
        errors.append(
            "ablation route-adoption metric rows mismatch: "
            f"observed={metric_rows} expected={len(rows)}"
        )
    for idx, row in enumerate(rows):
        variant = str(row.get("ablation_variant", "")).strip()
        ready = _numeric(row.get("route_adoption_ready_rate", 0.0))
        pending = _numeric(row.get("route_adoption_pending_refinement_rate", 0.0))
        if ready + pending > 1.0 + 1e-9:
            errors.append(
                f"row {idx} route adoption ready+pending exceeds 1.0: "
                f"{ready + pending}"
            )
        if variant == "full_planner_observed":
            drop = _numeric(row.get("relative_route_adoption_ready_drop", 0.0))
            if abs(drop) > 1e-9:
                errors.append(
                    "full_planner_observed relative_route_adoption_ready_drop "
                    f"must be 0.0: observed={drop}"
                )
    return tuple(errors)


def _ablation_study_largest_route_adoption_drop_variant(rows: Any) -> str:
    row_tuple = _dict_tuple(rows)
    if not row_tuple:
        return ""
    ablated_rows = [
        row
        for row in row_tuple
        if str(row.get("ablation_variant", "")).strip() != "full_planner_observed"
    ]
    candidate_rows = ablated_rows or list(row_tuple)
    best = max(
        candidate_rows,
        key=lambda row: _numeric(row.get("relative_route_adoption_ready_drop", 0.0)),
    )
    return str(best.get("ablation_variant", "")).strip()


def _ablation_study_row_has_route_adoption_metrics(row: dict[str, Any]) -> bool:
    return all(
        _nonnegative_number(row.get(field_name))
        for field_name in (
            "route_adoption_ready_rate",
            "route_adoption_pending_refinement_rate",
            "mean_route_adoption_blockers",
            "mean_route_adoption_pending_quality_control_blockers",
            "mean_route_adoption_pending_source_grounding_blockers",
            "mean_route_adoption_precondition_known_blockers",
            "mean_route_adoption_precondition_required_response_fields",
            "relative_route_adoption_ready_drop",
        )
    )


def _evaluation_realization_missing_selected_from_rows(
    rows: Any,
) -> tuple[str, ...]:
    values: list[str] = []
    for row in _dict_tuple(rows):
        values.extend(
            _str_tuple(row.get("realization_missing_selected_formal_primitives", []))
        )
    return tuple(dict.fromkeys(values))


def _evaluation_route_adoption_status_counts_from_rows(rows: Any) -> Counter[str]:
    return Counter(
        status
        for row in _dict_tuple(rows)
        for status in [
            str(row.get("llm_route_planner_route_adoption_status", "")).strip()
        ]
        if status
    )


def _evaluation_route_adoption_blockers_from_rows(rows: Any) -> tuple[str, ...]:
    values: list[str] = []
    for row in _dict_tuple(rows):
        values.extend(
            _str_tuple(row.get("llm_route_planner_route_adoption_blockers", []))
        )
    return tuple(dict.fromkeys(values))


def _evaluation_route_adoption_blocker_counts_from_rows(rows: Any) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in _dict_tuple(rows):
        counts.update(
            _str_tuple(row.get("llm_route_planner_route_adoption_blockers", []))
        )
    return dict(sorted(counts.items()))


def _evaluation_route_adoption_precondition_values_from_rows(
    rows: Any,
    field_name: str,
) -> tuple[str, ...]:
    values: list[str] = []
    for row in _dict_tuple(rows):
        values.extend(_str_tuple(row.get(field_name, [])))
    return tuple(dict.fromkeys(values))


def _evaluation_route_adoption_blocker_summary_from_rows(
    rows: Any,
) -> dict[str, dict[str, object]]:
    row_tuple = _dict_tuple(rows)
    counts = _evaluation_route_adoption_blocker_counts_from_rows(row_tuple)
    summaries: dict[str, dict[str, object]] = {}
    for blocker, count in counts.items():
        blocker_rows = [
            row
            for row in row_tuple
            if blocker
            in _str_tuple(row.get("llm_route_planner_route_adoption_blockers", []))
        ]
        by_status: Counter[str] = Counter(
            status
            for row in blocker_rows
            for status in [
                str(row.get("llm_route_planner_route_adoption_status", "")).strip()
            ]
            if status
        )
        summaries[blocker] = {
            "n_rows": len(blocker_rows),
            "n_blocker_occurrences": count,
            "by_route_adoption_status": dict(sorted(by_status.items())),
        }
    return summaries


def _evaluation_route_adoption_blocker_counts_for_summary(
    evaluation_manifest: dict[str, Any],
    rows: Any,
) -> dict[str, int]:
    manifest_counts = _int_mapping(
        evaluation_manifest.get("llm_route_adoption_blocker_counts", {})
    )
    if manifest_counts:
        return manifest_counts
    return _evaluation_route_adoption_blocker_counts_from_rows(rows)


def _evaluation_route_adoption_blocker_summary_for_summary(
    evaluation_manifest: dict[str, Any],
    rows: Any,
) -> dict[str, dict[str, object]]:
    manifest_summary = evaluation_manifest.get(
        "evaluation_by_llm_route_adoption_blocker",
        {},
    )
    if isinstance(manifest_summary, dict) and manifest_summary:
        return {
            str(blocker): _normalized_summary_dict(summary)
            for blocker, summary in sorted(manifest_summary.items())
            if isinstance(summary, dict)
        }
    return _evaluation_route_adoption_blocker_summary_from_rows(rows)


def _evaluation_quality_control_fields_from_rows(rows: Any) -> tuple[str, ...]:
    fields: list[str] = []
    for row in _dict_tuple(rows):
        fields.extend(_quality_controls_from_evaluation_row(row).keys())
    return tuple(dict.fromkeys(sorted(fields)))


def _evaluation_quality_control_values_from_rows(
    rows: Any,
    field_name: str,
) -> tuple[str, ...]:
    values: list[str] = []
    for row in _dict_tuple(rows):
        values.extend(
            _quality_controls_from_evaluation_row(row).get(field_name, tuple())
        )
    return tuple(dict.fromkeys(values))


def _quality_controls_from_evaluation_row(
    row: dict[str, Any],
) -> dict[str, tuple[str, ...]]:
    controls = row.get("quality_controls", {})
    if not isinstance(controls, dict):
        return {}
    return {
        field_name: _str_tuple(controls.get(field_name, []))
        for field_name in QUALITY_CONTROL_FIELDS
        if _str_tuple(controls.get(field_name, []))
    }


def _evaluation_realization_missing_delta_from_rows(
    rows: Any,
) -> tuple[str, ...]:
    values: list[str] = []
    for row in _dict_tuple(rows):
        values.extend(
            _str_tuple(row.get("realization_missing_delta_alignment_primitives", []))
        )
    return tuple(dict.fromkeys(values))


def _evaluation_realization_cost_hint_baseline_from_rows(
    rows: Any,
) -> tuple[str, ...]:
    values: list[str] = []
    for row in _dict_tuple(rows):
        values.extend(_str_tuple(row.get("realization_cost_hint_baseline_primitives", [])))
    return tuple(dict.fromkeys(values))


def _evaluation_realization_omitted_cost_hint_from_rows(
    rows: Any,
) -> tuple[str, ...]:
    values: list[str] = []
    for row in _dict_tuple(rows):
        values.extend(_str_tuple(row.get("realization_omitted_cost_hint_primitives", [])))
    return tuple(dict.fromkeys(values))


def _evaluation_realization_missing_by_route_from_rows(
    rows: Any,
) -> tuple[dict[str, Any], ...]:
    by_route: list[dict[str, Any]] = []
    for row in _dict_tuple(rows):
        missing_selected = _str_tuple(
            row.get("realization_missing_selected_formal_primitives", [])
        )
        missing_delta = _str_tuple(
            row.get("realization_missing_delta_alignment_primitives", [])
        )
        omitted_cost_hint = _str_tuple(
            row.get("realization_omitted_cost_hint_primitives", [])
        )
        if not missing_selected and not missing_delta and not omitted_cost_hint:
            continue
        by_route.append(
            {
                "route_id": str(row.get("route_id", "")),
                "goal_plan_id": str(row.get("goal_plan_id", "")),
                "display_name": str(row.get("display_name", "")),
                "missing_selected_formal_primitives": missing_selected,
                "missing_delta_alignment_primitives": missing_delta,
                "omitted_cost_hint_primitives": omitted_cost_hint,
            }
        )
    return tuple(by_route)


def _evaluation_realization_missing_route_keys(
    rows: Any,
) -> set[str]:
    keys: set[str] = set()
    for row in _dict_tuple(rows):
        keys.add(
            "route_id={route_id}|goal_plan_id={goal_plan_id}|display_name={display}|"
            "selected={selected}|delta={delta}|omitted={omitted}".format(
                route_id=str(row.get("route_id", "")),
                goal_plan_id=str(row.get("goal_plan_id", "")),
                display=str(row.get("display_name", "")),
                selected=",".join(
                    sorted(_str_tuple(row.get("missing_selected_formal_primitives", [])))
                ),
                delta=",".join(
                    sorted(_str_tuple(row.get("missing_delta_alignment_primitives", [])))
                ),
                omitted=",".join(
                    sorted(_str_tuple(row.get("omitted_cost_hint_primitives", [])))
                ),
            )
        )
    return keys


def _evaluation_ground_truth_rows(payload: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    for field_name in ("routes", "rows", "ground_truth_routes"):
        rows = payload.get(field_name, [])
        if isinstance(rows, list):
            return tuple(row for row in rows if isinstance(row, dict))
    return tuple()


def _evaluation_ground_truth_index(
    rows: tuple[dict[str, Any], ...],
) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        for field_name in ("goal_plan_id", "route_id", "display_name"):
            value = str(row.get(field_name, ""))
            if value:
                index[f"{field_name}:{value}"] = row
    return index


def _evaluation_ground_truth_consistency_errors(
    row: dict[str, Any],
    truth_row: dict[str, Any] | None,
) -> tuple[str, ...]:
    if not bool(row.get("matched_ground_truth", False)):
        return tuple()
    if truth_row is None:
        return ("matched evaluation row has no copied route-truth row",)
    errors: list[str] = []
    comparisons = (
        (
            "ground_truth_route_primitives",
            _truth_route_primitives_for_evaluation_audit(truth_row),
        ),
        (
            "ground_truth_delta_primitives",
            _truth_delta_primitives_for_evaluation_audit(truth_row),
        ),
        (
            "ground_truth_residual_primitives",
            _truth_residual_primitives_for_evaluation_audit(truth_row),
        ),
        (
            "ground_truth_existing_reuse_primitives",
            _str_tuple(truth_row.get("actual_existing_reuse_primitives", [])),
        ),
    )
    for field_name, expected in comparisons:
        observed = _str_tuple(row.get(field_name, []))
        if set(observed) != set(expected):
            errors.append(
                f"{field_name} mismatch: observed={sorted(observed)} "
                f"expected={sorted(expected)}"
            )
    return tuple(errors)


def _truth_route_primitives_for_evaluation_audit(
    truth_row: dict[str, Any],
) -> tuple[str, ...]:
    for field_name in ("required_primitives", "actual_dependencies", "route_primitives"):
        values = _str_tuple(truth_row.get(field_name, []))
        if values:
            return values
    return tuple()


def _truth_delta_primitives_for_evaluation_audit(
    truth_row: dict[str, Any],
) -> tuple[str, ...]:
    explicit = _str_tuple(truth_row.get("actual_delta_primitives", []))
    if explicit:
        return explicit
    route = set(_truth_route_primitives_for_evaluation_audit(truth_row))
    existing = set(_str_tuple(truth_row.get("actual_existing_reuse_primitives", [])))
    return tuple(sorted(route - existing))


def _truth_residual_primitives_for_evaluation_audit(
    truth_row: dict[str, Any],
) -> tuple[str, ...]:
    for field_name in (
        "expected_residual_primitives",
        "actual_residual_primitives",
        "residual_primitives",
        "expected_side_condition_primitives",
    ):
        values = _str_tuple(truth_row.get(field_name, []))
        if values:
            return values
    return tuple()


def _prover_adapter_contract_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = bundle_dir / "artifacts" / "formalization_gap_planner_prover_adapter_contract"
    manifest_path = artifact_dir / "formalization_gap_planner_prover_adapter_contract_manifest.json"
    packet_jsonl_path = artifact_dir / "formalization_gap_planner_prover_adapter_packets.jsonl"
    packet_schema_path = artifact_dir / "formalization_gap_planner_prover_adapter_packet.schema.json"
    response_validation_jsonl_path = (
        artifact_dir / "formalization_gap_planner_prover_adapter_response_validation.jsonl"
    )
    response_validation_row_schema_path = (
        artifact_dir
        / "formalization_gap_planner_prover_adapter_response_validation_row.schema.json"
    )
    manifest = _read_json_no_error(manifest_path)
    packet_rows, packet_errors = _read_jsonl_dict_rows_no_error(packet_jsonl_path)
    response_validation_rows, response_validation_errors = (
        _read_jsonl_dict_rows_no_error(response_validation_jsonl_path)
    )
    checks = [
        _check(
            "optional_prover_adapter_packet_schema_file",
            "optional_artifacts",
            "optional prover-adapter packet schema exists",
            str(packet_schema_path.exists()),
            packet_schema_path.exists(),
        ),
        _check(
            "optional_prover_adapter_packet_manifest_schema_valid_count",
            "optional_artifacts",
            "prover-adapter manifest packet schema-valid count matches packet count",
            f"{manifest.get('n_packet_schema_valid', 0)}/{manifest.get('n_packets', 0)}",
            int(manifest.get("n_packets", 0) or 0) > 0
            and int(manifest.get("n_packet_schema_valid", 0) or 0)
            == int(manifest.get("n_packets", 0) or 0),
        ),
        _check(
            "optional_prover_adapter_packet_jsonl_parse",
            "optional_artifacts",
            "prover-adapter packet JSONL parses into object rows",
            "; ".join(packet_errors) if packet_errors else f"rows={len(packet_rows)}",
            not packet_errors,
            errors=packet_errors,
        ),
        _check(
            "optional_prover_adapter_packet_jsonl_row_count",
            "optional_artifacts",
            "packet JSONL rows match manifest count",
            f"jsonl={len(packet_rows)} manifest={manifest.get('n_packets', 0)}",
            len(packet_rows) == int(manifest.get("n_packets", 0) or 0),
        ),
        _check(
            "optional_prover_adapter_response_validation_row_schema_file",
            "optional_artifacts",
            "optional prover-adapter response-validation row schema exists",
            str(response_validation_row_schema_path.exists()),
            response_validation_row_schema_path.exists(),
        ),
        _check(
            "optional_prover_adapter_response_validation_manifest_schema_valid_count",
            "optional_artifacts",
            "prover-adapter response-validation schema-valid count matches row count",
            (
                f"{manifest.get('n_response_validation_row_schema_valid', 0)}/"
                f"{manifest.get('n_packets', 0)}; invalid="
                f"{manifest.get('n_response_validation_row_schema_invalid', 0)}"
            ),
            int(manifest.get("n_packets", 0) or 0) > 0
            and int(manifest.get("n_response_validation_row_schema_valid", 0) or 0)
            == int(manifest.get("n_packets", 0) or 0)
            and int(manifest.get("n_response_validation_row_schema_invalid", 0) or 0)
            == 0,
        ),
        _check(
            "optional_prover_adapter_response_validation_jsonl_parse",
            "optional_artifacts",
            "response-validation JSONL parses into object rows",
            (
                "; ".join(response_validation_errors)
                if response_validation_errors
                else f"rows={len(response_validation_rows)}"
            ),
            not response_validation_errors,
            errors=response_validation_errors,
        ),
        _check(
            "optional_prover_adapter_response_validation_jsonl_row_count",
            "optional_artifacts",
            "response-validation JSONL rows match manifest packet count",
            f"jsonl={len(response_validation_rows)} manifest={manifest.get('n_packets', 0)}",
            len(response_validation_rows) == int(manifest.get("n_packets", 0) or 0),
        ),
    ]
    for idx, row in enumerate(packet_rows):
        schema_errors = validate_prover_adapter_packet_row(row)
        checks.append(
            _check(
                f"optional_prover_adapter_packet_row_{idx}_schema_valid",
                "optional_artifacts",
                "prover-adapter packet row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
    for idx, row in enumerate(response_validation_rows):
        schema_errors = validate_prover_adapter_response_validation_row(row)
        checks.append(
            _check(
                f"optional_prover_adapter_response_validation_row_{idx}_schema_valid",
                "optional_artifacts",
                "prover-adapter response-validation row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
    return checks


def _cross_prover_matrix_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_cross_prover_matrix_audit"
    )
    manifest_path = artifact_dir / "formalization_gap_planner_cross_prover_matrix_audit_manifest.json"
    matrix_jsonl_path = artifact_dir / "formalization_gap_planner_cross_prover_matrix_audit.jsonl"
    matrix_row_schema_path = (
        artifact_dir / "formalization_gap_planner_cross_prover_matrix_audit_row.schema.json"
    )
    target_summary_path = (
        artifact_dir / "formalization_gap_planner_cross_prover_target_summary.json"
    )
    target_summary_schema_path = (
        artifact_dir
        / "formalization_gap_planner_cross_prover_target_summary.schema.json"
    )
    packet_jsonl_path = artifact_dir / "formalization_gap_planner_cross_prover_packets.jsonl"
    packet_schema_path = artifact_dir / "formalization_gap_planner_prover_adapter_packet.schema.json"
    response_validation_jsonl_path = (
        artifact_dir / "formalization_gap_planner_cross_prover_response_validation.jsonl"
    )
    response_validation_row_schema_path = (
        artifact_dir
        / "formalization_gap_planner_prover_adapter_response_validation_row.schema.json"
    )
    manifest = _read_json_no_error(manifest_path)
    target_summary = _read_json_no_error(target_summary_path)
    target_summary_schema = _read_json_no_error(target_summary_schema_path)
    target_summary_errors = validate_cross_prover_target_summary_payload(
        target_summary,
        target_summary_schema or None,
    )
    matrix_rows, matrix_errors = _read_jsonl_dict_rows_no_error(matrix_jsonl_path)
    packet_rows, packet_errors = _read_jsonl_dict_rows_no_error(packet_jsonl_path)
    response_validation_rows, response_validation_errors = (
        _read_jsonl_dict_rows_no_error(response_validation_jsonl_path)
    )
    n_targets = int(manifest.get("n_targets", 0) or 0)
    n_targets_ok = int(manifest.get("n_targets_ok", 0) or 0)
    n_packets = int(manifest.get("n_total_packets", 0) or 0)
    n_schema_valid = int(manifest.get("n_total_packet_schema_valid", 0) or 0)
    n_schema_invalid = int(manifest.get("n_total_packets_schema_invalid", 0) or 0)
    n_aligned = int(manifest.get("n_total_packets_with_alignment", 0) or 0)
    n_missing_alignment = int(
        manifest.get("n_total_packets_missing_alignment", 0) or 0
    )
    n_trace = int(
        manifest.get("n_total_packets_with_standalone_input_trace", 0) or 0
    )
    n_missing_trace = int(
        manifest.get("n_total_packets_missing_standalone_input_trace", 0) or 0
    )
    n_replan_trace = int(
        manifest.get("n_total_packets_with_replan_metadata_trace", 0) or 0
    )
    n_jsonl_trace = sum(
        1
        for row in packet_rows
        if isinstance(row.get("standalone_input_trace"), dict)
        and row.get("standalone_input_trace")
    )
    n_jsonl_replan_trace = sum(
        1
        for row in packet_rows
        if isinstance(row.get("standalone_input_trace"), dict)
        and row["standalone_input_trace"].get("has_replan_metadata")
    )
    n_attempt_dependency = int(
        manifest.get("n_total_packets_with_formal_attempt_dependency", 0) or 0
    )
    n_attempt_ready = int(
        manifest.get("n_total_packets_formal_attempt_initial_ready", 0) or 0
    )
    n_attempt_waiting = int(
        manifest.get("n_total_packets_formal_attempt_waiting", 0) or 0
    )
    n_attempt_missing = int(
        manifest.get("n_total_packets_formal_attempt_missing_prerequisites", 0)
        or 0
    )
    attempt_manifest_counts = _int_mapping(
        manifest.get("by_total_packet_formal_attempt_dependency_status")
    )
    attempt_target_counts = _int_mapping(
        target_summary.get("by_total_packet_formal_attempt_dependency_status")
    )
    attempt_packet_counts = dict(
        sorted(
            Counter(
                str(row.get("formal_attempt_dependency_status", "") or "")
                for row in packet_rows
            ).items()
        )
    )
    attempt_dependency_statuses = {
        "ready_no_formal_prerequisites",
        "waiting_for_formal_prerequisite_attempts",
        "missing_formal_prerequisite_attempts",
    }
    n_attempt_dependency_from_histogram = sum(
        count
        for status, count in attempt_manifest_counts.items()
        if status in attempt_dependency_statuses
    )
    attempt_manifest_counts_ok = (
        sum(attempt_manifest_counts.values()) == n_packets
        and n_attempt_ready
        == attempt_manifest_counts.get("ready_no_formal_prerequisites", 0)
        and n_attempt_waiting
        == attempt_manifest_counts.get("waiting_for_formal_prerequisite_attempts", 0)
        and n_attempt_missing
        == attempt_manifest_counts.get("missing_formal_prerequisite_attempts", 0)
        and n_attempt_dependency
        == n_attempt_ready + n_attempt_waiting + n_attempt_missing
        == n_attempt_dependency_from_histogram
    )
    attempt_target_counts_ok = (
        int(target_summary.get("n_total_packets", 0) or 0) == n_packets
        and int(
            target_summary.get(
                "n_total_packets_with_formal_attempt_dependency", 0
            )
            or 0
        )
        == n_attempt_dependency
        and int(
            target_summary.get(
                "n_total_packets_formal_attempt_initial_ready", 0
            )
            or 0
        )
        == n_attempt_ready
        and int(
            target_summary.get("n_total_packets_formal_attempt_waiting", 0)
            or 0
        )
        == n_attempt_waiting
        and int(
            target_summary.get(
                "n_total_packets_formal_attempt_missing_prerequisites", 0
            )
            or 0
        )
        == n_attempt_missing
        and attempt_target_counts == attempt_manifest_counts
    )
    checks = [
        _check(
            "optional_cross_prover_targets_ok",
            "optional_artifacts",
            "all cross-prover target exports ok",
            f"{n_targets_ok}/{n_targets}",
            n_targets > 0 and n_targets_ok == n_targets,
        ),
        _check(
            "optional_cross_prover_packet_schema_valid",
            "optional_artifacts",
            "every cross-prover packet satisfies the prover-adapter packet schema",
            f"schema_valid={n_schema_valid}; packets={n_packets}; invalid={n_schema_invalid}",
            n_packets > 0 and n_schema_valid == n_packets and n_schema_invalid == 0,
        ),
        _check(
            "optional_cross_prover_alignment_packets",
            "optional_artifacts",
            "every cross-prover packet carries route-alignment evidence",
            f"aligned={n_aligned}; packets={n_packets}; missing={n_missing_alignment}",
            n_packets > 0 and n_aligned == n_packets and n_missing_alignment == 0,
        ),
        _check(
            "optional_cross_prover_alignment_count_consistent",
            "optional_artifacts",
            "alignment packet counts are consistent across target provers",
            str(manifest.get("alignment_packet_count_consistent", "")),
            bool(manifest.get("alignment_packet_count_consistent", False)),
        ),
        _check(
            "optional_cross_prover_standalone_trace_packets",
            "optional_artifacts",
            "every cross-prover packet carries standalone input trace provenance",
            f"trace={n_trace}; packets={n_packets}; missing={n_missing_trace}",
            n_packets > 0 and n_trace == n_packets and n_missing_trace == 0,
        ),
        _check(
            "optional_cross_prover_standalone_trace_count_consistent",
            "optional_artifacts",
            "standalone input trace packet counts are consistent across target provers",
            str(manifest.get("standalone_input_trace_packet_count_consistent", "")),
            bool(
                manifest.get(
                    "standalone_input_trace_packet_count_consistent",
                    False,
                )
            ),
        ),
        _check(
            "optional_cross_prover_standalone_trace_jsonl_count_consistent",
            "optional_artifacts",
            "manifest standalone input trace counts match cross-prover packet JSONL",
            (
                f"manifest_trace={n_trace}; jsonl_trace={n_jsonl_trace}; "
                f"manifest_replan_trace={n_replan_trace}; "
                f"jsonl_replan_trace={n_jsonl_replan_trace}"
            ),
            n_trace == n_jsonl_trace
            and n_replan_trace == n_jsonl_replan_trace
            and n_missing_trace == max(0, len(packet_rows) - n_jsonl_trace),
        ),
        _check(
            "optional_cross_prover_formal_attempt_dependency_manifest_counts",
            "optional_artifacts",
            "cross-prover formal-attempt dependency manifest counts are internally consistent",
            (
                f"dependency={n_attempt_dependency}; ready={n_attempt_ready}; "
                f"waiting={n_attempt_waiting}; missing={n_attempt_missing}; "
                f"histogram={attempt_manifest_counts}; packets={n_packets}"
            ),
            attempt_manifest_counts_ok,
        ),
        _check(
            "optional_cross_prover_formal_attempt_dependency_target_summary_consistent",
            "optional_artifacts",
            "cross-prover formal-attempt dependency counts match the target summary",
            (
                f"manifest={attempt_manifest_counts}; "
                f"target_summary={attempt_target_counts}"
            ),
            attempt_target_counts_ok,
        ),
        _check(
            "optional_cross_prover_formal_attempt_dependency_jsonl_consistent",
            "optional_artifacts",
            "cross-prover packet JSONL formal-attempt dependency statuses match the manifest histogram",
            (
                f"manifest={attempt_manifest_counts}; "
                f"jsonl={attempt_packet_counts}"
            ),
            attempt_packet_counts == attempt_manifest_counts,
        ),
        _check(
            "optional_cross_prover_matrix_row_schema_file",
            "optional_artifacts",
            "cross-prover matrix row schema exists",
            str(matrix_row_schema_path.exists()),
            matrix_row_schema_path.exists(),
        ),
        _check(
            "optional_cross_prover_target_summary_file",
            "optional_artifacts",
            "cross-prover target summary exists",
            str(target_summary_path.exists()),
            target_summary_path.exists(),
        ),
        _check(
            "optional_cross_prover_target_summary_schema_file",
            "optional_artifacts",
            "cross-prover target summary schema exists",
            str(target_summary_schema_path.exists()),
            target_summary_schema_path.exists(),
        ),
        _check(
            "optional_cross_prover_target_summary_schema_id",
            "optional_artifacts",
            CROSS_PROVER_TARGET_SUMMARY_SCHEMA_ID,
            str(target_summary_schema.get("$id", "")),
            target_summary_schema.get("$id") == CROSS_PROVER_TARGET_SUMMARY_SCHEMA_ID,
        ),
        _check(
            "optional_cross_prover_target_summary_contract_valid",
            "optional_artifacts",
            "cross-prover target summary validates against public schema",
            "; ".join(target_summary_errors) if target_summary_errors else "valid",
            not target_summary_errors,
            errors=target_summary_errors,
        ),
        _check(
            "optional_cross_prover_packet_schema_file",
            "optional_artifacts",
            "cross-prover packet schema exists",
            str(packet_schema_path.exists()),
            packet_schema_path.exists(),
        ),
        _check(
            "optional_cross_prover_response_validation_row_schema_file",
            "optional_artifacts",
            "cross-prover response-validation row schema exists",
            str(response_validation_row_schema_path.exists()),
            response_validation_row_schema_path.exists(),
        ),
        _check(
            "optional_cross_prover_matrix_manifest_schema_valid_count",
            "optional_artifacts",
            "matrix manifest row schema-valid count matches target count",
            (
                f"{manifest.get('n_matrix_row_schema_valid', 0)}/{n_targets}; "
                f"invalid={manifest.get('n_matrix_row_schema_invalid', 0)}"
            ),
            n_targets > 0
            and int(manifest.get("n_matrix_row_schema_valid", 0) or 0) == n_targets
            and int(manifest.get("n_matrix_row_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_cross_prover_packet_manifest_schema_valid_count",
            "optional_artifacts",
            "matrix manifest packet row schema-valid count matches packet count",
            (
                f"{manifest.get('n_packet_row_schema_valid', 0)}/{n_packets}; "
                f"invalid={manifest.get('n_packet_row_schema_invalid', 0)}"
            ),
            n_packets > 0
            and int(manifest.get("n_packet_row_schema_valid", 0) or 0) == n_packets
            and int(manifest.get("n_packet_row_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_cross_prover_response_validation_manifest_schema_valid_count",
            "optional_artifacts",
            "matrix manifest response-validation schema-valid count matches packet count",
            (
                f"{manifest.get('n_response_validation_row_schema_valid', 0)}/"
                f"{n_packets}; invalid="
                f"{manifest.get('n_response_validation_row_schema_invalid', 0)}"
            ),
            n_packets > 0
            and int(manifest.get("n_response_validation_row_schema_valid", 0) or 0)
            == n_packets
            and int(
                manifest.get("n_response_validation_row_schema_invalid", 0) or 0
            )
            == 0,
        ),
        _check(
            "optional_cross_prover_matrix_jsonl_parse",
            "optional_artifacts",
            "matrix JSONL parses into object rows",
            "; ".join(matrix_errors) if matrix_errors else f"rows={len(matrix_rows)}",
            not matrix_errors,
            errors=matrix_errors,
        ),
        _check(
            "optional_cross_prover_matrix_jsonl_row_count",
            "optional_artifacts",
            "matrix JSONL rows match target count",
            f"jsonl={len(matrix_rows)} targets={n_targets}",
            len(matrix_rows) == n_targets,
        ),
        _check(
            "optional_cross_prover_packet_jsonl_parse",
            "optional_artifacts",
            "cross-prover packet JSONL parses into object rows",
            "; ".join(packet_errors) if packet_errors else f"rows={len(packet_rows)}",
            not packet_errors,
            errors=packet_errors,
        ),
        _check(
            "optional_cross_prover_packet_jsonl_row_count",
            "optional_artifacts",
            "cross-prover packet JSONL rows match manifest count",
            f"jsonl={len(packet_rows)} packets={n_packets}",
            len(packet_rows) == n_packets,
        ),
        _check(
            "optional_cross_prover_response_validation_jsonl_parse",
            "optional_artifacts",
            "cross-prover response-validation JSONL parses into object rows",
            (
                "; ".join(response_validation_errors)
                if response_validation_errors
                else f"rows={len(response_validation_rows)}"
            ),
            not response_validation_errors,
            errors=response_validation_errors,
        ),
        _check(
            "optional_cross_prover_response_validation_jsonl_row_count",
            "optional_artifacts",
            "cross-prover response-validation JSONL rows match packet count",
            f"jsonl={len(response_validation_rows)} packets={n_packets}",
            len(response_validation_rows) == n_packets,
        ),
    ]
    for idx, row in enumerate(matrix_rows):
        schema_errors = validate_cross_prover_matrix_audit_row(row)
        checks.append(
            _check(
                f"optional_cross_prover_matrix_row_{idx}_schema_valid",
                "optional_artifacts",
                "cross-prover matrix row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
    for idx, row in enumerate(packet_rows):
        schema_errors = validate_prover_adapter_packet_row(row)
        standalone_input_trace = row.get("standalone_input_trace")
        checks.append(
            _check(
                f"optional_cross_prover_packet_row_{idx}_schema_valid",
                "optional_artifacts",
                "cross-prover packet row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
        checks.append(
            _check(
                f"optional_cross_prover_packet_row_{idx}_standalone_input_trace",
                "optional_artifacts",
                "cross-prover packet row carries standalone input trace provenance",
                (
                    "present"
                    if isinstance(standalone_input_trace, dict)
                    and bool(standalone_input_trace)
                    else "missing"
                ),
                isinstance(standalone_input_trace, dict)
                and bool(standalone_input_trace),
            )
        )
    for idx, row in enumerate(response_validation_rows):
        schema_errors = validate_prover_adapter_response_validation_row(row)
        checks.append(
            _check(
                f"optional_cross_prover_response_validation_row_{idx}_schema_valid",
                "optional_artifacts",
                "cross-prover response-validation row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
    return checks


def _route_replan_handoff_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = (
        bundle_dir / "artifacts" / "formalization_gap_planner_route_replan_handoff"
    )
    manifest_path = (
        artifact_dir
        / "formalization_gap_planner_route_replan_handoff_manifest.json"
    )
    seed_path = artifact_dir / "formalization_gap_planner_route_replan_standalone_seed.json"
    seed_schema_path = (
        artifact_dir
        / "formalization_gap_planner_route_replan_standalone_seed.schema.json"
    )
    rows_jsonl_path = artifact_dir / "formalization_gap_planner_route_replan_handoff.jsonl"
    manifest = _read_json_no_error(manifest_path)
    seed = _read_json_no_error(seed_path)
    seed_schema = _read_json_no_error(seed_schema_path)
    jsonl_rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    rows = [row for row in manifest.get("rows", []) if isinstance(row, dict)]
    n_rows = int(manifest.get("n_handoff_rows", 0) or 0)
    n_edges = int(manifest.get("n_route_alignment_edges", 0) or 0)
    n_unaligned = int(manifest.get("n_unaligned_primitives", 0) or 0)
    resource_feedback_rows = sum(
        1
        for row in rows
        if "resource_response_ledger" in _str_tuple(row.get("applied_hook_kinds", []))
    )
    seed_resource_feedback_rows = _seed_resource_feedback_route_count(seed)
    row_signatures = _distinct_row_signatures(rows)
    checks = [
        _check(
            "optional_route_replan_handoff_alignment_edges",
            "optional_artifacts",
            "route-replan handoff preserves at least one alignment edge per row",
            f"edges={n_edges}; rows={n_rows}",
            n_rows > 0 and n_edges >= n_rows,
        ),
        _check(
            "optional_route_replan_handoff_no_unaligned_primitives",
            "optional_artifacts",
            "zero unaligned revised primitives",
            str(n_unaligned),
            n_unaligned == 0
            and all(not row.get("unaligned_primitives") for row in rows),
        ),
        _check(
            "optional_route_replan_handoff_row_alignment_edges",
            "optional_artifacts",
            "every handoff row carries revised route alignment edges",
            f"{sum(1 for row in rows if row.get('revised_route_alignment_edges'))}/{len(rows)}",
            bool(rows)
            and all(bool(row.get("revised_route_alignment_edges")) for row in rows),
        ),
        _check(
            "optional_route_replan_handoff_jsonl_parse",
            "optional_artifacts",
            "route-replan handoff JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(jsonl_rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_route_replan_handoff_jsonl_row_count",
            "optional_artifacts",
            "route-replan handoff JSONL rows match manifest row count",
            f"jsonl={len(jsonl_rows)} manifest={n_rows}",
            len(jsonl_rows) == n_rows,
        ),
        _check(
            "optional_route_replan_handoff_seed_provenance_metadata",
            "optional_artifacts",
            "seed route replan metadata preserves handoff-row provenance fields",
            _handoff_seed_provenance_observed(rows, seed),
            bool(rows) and _handoff_seed_provenance_ok(rows, seed),
        ),
        _check(
            "optional_route_replan_handoff_seed_schema_file",
            "optional_artifacts",
            "route-replan standalone seed schema exists",
            str(seed_schema_path.exists()),
            seed_schema_path.exists(),
        ),
        _check(
            "optional_route_replan_handoff_seed_schema_id",
            "optional_artifacts",
            FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_ID,
            str(seed_schema.get("$id", "")),
            seed_schema.get("$id")
            == FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_ID,
        ),
        _check(
            "optional_route_replan_handoff_seed_schema_replan_metadata",
            "optional_artifacts",
            "standalone seed schema publishes replan DAG/alignment metadata fields",
            _standalone_seed_schema_replan_metadata_observed(seed_schema),
            _standalone_seed_schema_replan_metadata_ok(seed_schema),
        ),
        _check(
            "optional_route_replan_handoff_generic_formal_dag_fields",
            "optional_artifacts",
            "route-replan handoff rows and standalone seed publish prover-neutral revised formal-realization DAG fields",
            _handoff_generic_formal_dag_observed(rows, seed, manifest),
            not _handoff_generic_formal_dag_errors(rows, seed, manifest),
            errors=_handoff_generic_formal_dag_errors(rows, seed, manifest),
        ),
        _check(
            "optional_route_replan_handoff_resource_feedback_count",
            "optional_artifacts",
            "resource-response-ledger handoff rows match manifest and seed metadata",
            (
                f"rows={resource_feedback_rows}; seed={seed_resource_feedback_rows}; "
                f"manifest={manifest.get('n_routes_with_resource_response_ledger_feedback', 0)}"
            ),
            resource_feedback_rows
            == int(
                manifest.get("n_routes_with_resource_response_ledger_feedback", 0)
                or 0
            )
            == seed_resource_feedback_rows,
        ),
        _check(
            "optional_route_replan_handoff_prover_diagnostic_signature_count",
            "optional_artifacts",
            "distinct prover diagnostic signatures match handoff manifest",
            (
                f"rows={len(row_signatures)}; "
                f"manifest={manifest.get('n_distinct_prover_diagnostic_signatures', 0)}"
            ),
            len(row_signatures)
            == int(manifest.get("n_distinct_prover_diagnostic_signatures", 0) or 0),
        ),
    ]
    seed_routes = _seed_route_index(seed)
    for idx, row in enumerate(rows):
        seed_route = seed_routes.get(str(row.get("standalone_route_id", "")), {})
        alignment_errors = _handoff_seed_alignment_errors(row, seed_route)
        checks.append(
            _check(
                f"optional_route_replan_handoff_row_{idx}_seed_alignment_preservation",
                "optional_artifacts",
                "seed route and replan metadata exactly preserve revised alignment edges",
                _handoff_seed_alignment_observed(row, seed_route),
                not alignment_errors,
                errors=alignment_errors,
            )
        )
        dag_errors = _handoff_seed_dag_errors(row, seed_route)
        checks.append(
            _check(
                f"optional_route_replan_handoff_row_{idx}_seed_dag_preservation",
                "optional_artifacts",
                "seed route and replan metadata preserve revised informal and formal DAG nodes",
                _handoff_seed_dag_observed(row, seed_route),
                not dag_errors,
                errors=dag_errors,
            )
        )
        target_context_errors = _handoff_seed_target_context_errors(row, seed_route)
        checks.append(
            _check(
                f"optional_route_replan_handoff_row_{idx}_seed_target_context_preservation",
                "optional_artifacts",
                "seed route and replan metadata preserve target theorem context packet",
                _handoff_seed_target_context_observed(row, seed_route),
                not target_context_errors,
                errors=target_context_errors,
            )
        )
        target_summary_errors = _handoff_seed_target_context_summary_errors(
            row,
            seed_route,
        )
        checks.append(
            _check(
                f"optional_route_replan_handoff_row_{idx}_seed_target_context_summary_preservation",
                "optional_artifacts",
                "seed route and replan metadata preserve LLM target context summary",
                _handoff_seed_target_context_summary_observed(row, seed_route),
                not target_summary_errors,
                errors=target_summary_errors,
            )
        )
        brief_errors = _handoff_seed_route_planning_brief_errors(row, seed_route)
        checks.append(
            _check(
                f"optional_route_replan_handoff_row_{idx}_seed_route_planning_brief_preservation",
                "optional_artifacts",
                "seed route and replan metadata preserve LLM route-planning brief",
                _handoff_seed_route_planning_brief_observed(row, seed_route),
                not brief_errors,
                errors=brief_errors,
            )
        )
        route_option_brief_errors = (
            _handoff_seed_route_option_selection_brief_errors(row, seed_route)
        )
        checks.append(
            _check(
                f"optional_route_replan_handoff_row_{idx}_seed_route_option_selection_brief_preservation",
                "optional_artifacts",
                "seed route and replan metadata preserve LLM route-option selection brief",
                _handoff_seed_route_option_selection_brief_observed(
                    row,
                    seed_route,
                ),
                not route_option_brief_errors,
                errors=route_option_brief_errors,
            )
        )
        matrix_witness_errors = (
            _handoff_seed_primitive_evidence_matrix_witness_errors(
                row,
                seed_route,
            )
        )
        checks.append(
            _check(
                f"optional_route_replan_handoff_row_{idx}_seed_primitive_evidence_matrix_witness_preservation",
                "optional_artifacts",
                "seed route and replan metadata preserve LLM primitive-evidence matrix witness",
                _handoff_seed_primitive_evidence_matrix_witness_observed(
                    row,
                    seed_route,
                ),
                not matrix_witness_errors,
                errors=matrix_witness_errors,
            )
        )
        precondition_errors = _handoff_seed_route_adoption_preconditions_errors(
            row,
            seed_route,
        )
        checks.append(
            _check(
                f"optional_route_replan_handoff_row_{idx}_seed_route_adoption_preconditions_preservation",
                "optional_artifacts",
                "seed route and replan metadata preserve LLM route-adoption preconditions",
                _handoff_seed_route_adoption_preconditions_observed(
                    row,
                    seed_route,
                ),
                not precondition_errors,
                errors=precondition_errors,
            )
        )
    for idx, row in enumerate(jsonl_rows):
        schema_errors = validate_route_replan_handoff_row(row)
        checks.append(
            _check(
                f"optional_route_replan_handoff_row_{idx}_schema_valid",
                "optional_artifacts",
                "route-replan handoff row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
    return checks


def _route_replan_handoff_audit_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = (
        bundle_dir / "artifacts" / "formalization_gap_planner_route_replan_handoff_audit"
    )
    manifest_path = artifact_dir / "formalization_gap_planner_route_replan_handoff_audit_manifest.json"
    rows_jsonl_path = artifact_dir / "formalization_gap_planner_route_replan_handoff_audit.jsonl"
    row_schema_path = (
        artifact_dir / "formalization_gap_planner_route_replan_handoff_audit_row.schema.json"
    )
    manifest = _read_json_no_error(manifest_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    n_seed_routes = int(manifest.get("n_seed_routes", 0) or 0)
    n_roundtrip_routes = int(manifest.get("n_roundtrip_goal_plans", 0) or 0)
    n_roundtrip_edges = int(manifest.get("n_roundtrip_route_alignment_edges", 0) or 0)
    ok_check_names = {
        str(row.get("check_name", ""))
        for row in manifest.get("checks", [])
        if isinstance(row, dict) and row.get("ok")
    }
    required_alignment_checks = {
        "handoff_alignment_edges_present",
        "handoff_no_unaligned_primitives",
        "roundtrip_alignment_edges",
        "roundtrip_alignment_contract",
    }
    required_trace_checks = {
        "roundtrip_standalone_input_trace",
        "roundtrip_llm_target_context_summary_trace",
        "roundtrip_llm_route_planning_brief_trace",
        "roundtrip_llm_route_option_selection_brief_trace",
        "roundtrip_llm_primitive_evidence_matrix_witness_trace",
        "roundtrip_llm_route_adoption_preconditions_trace",
        "roundtrip_llm_route_planner_hook_trace",
    }
    provenance_check_names = {
        check_name
        for check_name in ok_check_names
        if check_name.endswith("_seed_route_provenance_metadata")
    }
    checks = [
        _check(
            "optional_route_replan_handoff_audit_row_schema_file",
            "optional_artifacts",
            "optional route-replan handoff audit row schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            "optional_route_replan_handoff_audit_manifest_schema_valid_count",
            "optional_artifacts",
            "route-replan handoff audit manifest schema-valid count matches row count",
            (
                f"{manifest.get('n_row_schema_valid', 0)}/"
                f"{manifest.get('n_checks', 0)}; "
                f"invalid={manifest.get('n_row_schema_invalid', 0)}"
            ),
            int(manifest.get("n_checks", 0) or 0) > 0
            and int(manifest.get("n_row_schema_valid", 0) or 0)
            == int(manifest.get("n_checks", 0) or 0)
            and int(manifest.get("n_row_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_route_replan_handoff_audit_jsonl_parse",
            "optional_artifacts",
            "route-replan handoff audit JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_route_replan_handoff_audit_jsonl_row_count",
            "optional_artifacts",
            "route-replan handoff audit JSONL rows match manifest check count",
            f"jsonl={len(rows)} manifest={manifest.get('n_checks', 0)}",
            len(rows) == int(manifest.get("n_checks", 0) or 0),
        ),
        _check(
            "optional_route_replan_handoff_audit_roundtrip_alignment_edges",
            "optional_artifacts",
            "roundtrip regenerates at least one alignment edge per seed route",
            f"edges={n_roundtrip_edges}; seed_routes={n_seed_routes}",
            n_seed_routes > 0 and n_roundtrip_edges >= n_seed_routes,
        ),
        _check(
            "optional_route_replan_handoff_audit_roundtrip_routes",
            "optional_artifacts",
            "roundtrip route count matches seed route count",
            f"roundtrip={n_roundtrip_routes}; seed={n_seed_routes}",
            n_seed_routes > 0 and n_roundtrip_routes == n_seed_routes,
        ),
        _check(
            "optional_route_replan_handoff_audit_alignment_checks",
            "optional_artifacts",
            "handoff and roundtrip alignment checks passed",
            ",".join(sorted(required_alignment_checks.intersection(ok_check_names))),
            required_alignment_checks.issubset(ok_check_names),
        ),
        _check(
            "optional_route_replan_handoff_audit_provenance_checks",
            "optional_artifacts",
            "handoff audit includes at least one passing row-to-seed provenance check",
            ",".join(sorted(provenance_check_names)),
            bool(provenance_check_names),
        ),
        _check(
            "optional_route_replan_handoff_audit_roundtrip_trace_checks",
            "optional_artifacts",
            "handoff audit includes passing roundtrip standalone-input trace check",
            ",".join(sorted(required_trace_checks.intersection(ok_check_names))),
            required_trace_checks.issubset(ok_check_names),
        ),
        _check(
            "optional_route_replan_handoff_audit_roundtrip_target_context_summary_trace",
            "optional_artifacts",
            "handoff audit manifest exposes roundtrip target-context-summary trace count",
            (
                "traces_with_summary="
                f"{manifest.get('n_roundtrip_standalone_input_traces_with_llm_target_context_summary', 'missing')}; "
                f"seed_routes={n_seed_routes}"
            ),
            "n_roundtrip_standalone_input_traces_with_llm_target_context_summary"
            in manifest
            and int(
                manifest.get(
                    "n_roundtrip_standalone_input_traces_with_llm_target_context_summary",
                    0,
                )
                or 0
            )
            >= 0,
        ),
        _check(
            "optional_route_replan_handoff_audit_roundtrip_route_planning_brief_trace",
            "optional_artifacts",
            "handoff audit manifest exposes roundtrip route-planning-brief trace count",
            (
                "traces_with_brief="
                f"{manifest.get('n_roundtrip_standalone_input_traces_with_llm_route_planning_brief', 'missing')}; "
                f"seed_routes={n_seed_routes}"
            ),
            "n_roundtrip_standalone_input_traces_with_llm_route_planning_brief"
            in manifest
            and int(
                manifest.get(
                    "n_roundtrip_standalone_input_traces_with_llm_route_planning_brief",
                    0,
                )
                or 0
            )
            >= 0,
        ),
        _check(
            "optional_route_replan_handoff_audit_roundtrip_route_option_selection_brief_trace",
            "optional_artifacts",
            "handoff audit manifest exposes roundtrip route-option-selection-brief trace count",
            (
                "traces_with_brief="
                f"{manifest.get('n_roundtrip_standalone_input_traces_with_llm_route_option_selection_brief', 'missing')}; "
                f"seed_routes={n_seed_routes}"
            ),
            "n_roundtrip_standalone_input_traces_with_llm_route_option_selection_brief"
            in manifest
            and int(
                manifest.get(
                    "n_roundtrip_standalone_input_traces_with_llm_route_option_selection_brief",
                    0,
                )
                or 0
            )
            >= 0,
        ),
        _check(
            "optional_route_replan_handoff_audit_roundtrip_primitive_evidence_matrix_witness_trace",
            "optional_artifacts",
            "handoff audit manifest exposes roundtrip primitive-evidence-matrix witness trace count",
            (
                "traces_with_witness="
                f"{manifest.get('n_roundtrip_standalone_input_traces_with_llm_primitive_evidence_matrix_witness', 'missing')}; "
                f"seed_routes={n_seed_routes}; "
                "repair_obligations="
                f"{manifest.get('n_roundtrip_standalone_input_trace_llm_primitive_evidence_matrix_repair_obligations', 'missing')}"
            ),
            "n_roundtrip_standalone_input_traces_with_llm_primitive_evidence_matrix_witness"
            in manifest
            and "n_roundtrip_standalone_input_trace_llm_primitive_evidence_matrix_repair_obligations"
            in manifest
            and int(
                manifest.get(
                    "n_roundtrip_standalone_input_traces_with_llm_primitive_evidence_matrix_witness",
                    0,
                )
                or 0
            )
            >= 0,
        ),
        _check(
            "optional_route_replan_handoff_audit_roundtrip_route_adoption_preconditions_trace",
            "optional_artifacts",
            "handoff audit manifest exposes roundtrip route-adoption-precondition trace count",
            (
                "traces_with_preconditions="
                f"{manifest.get('n_roundtrip_standalone_input_traces_with_llm_route_adoption_preconditions', 'missing')}; "
                f"seed_routes={n_seed_routes}"
            ),
            "n_roundtrip_standalone_input_traces_with_llm_route_adoption_preconditions"
            in manifest
            and int(
                manifest.get(
                    "n_roundtrip_standalone_input_traces_with_llm_route_adoption_preconditions",
                    0,
                )
                or 0
            )
            >= 0,
        ),
    ]
    for idx, row in enumerate(rows):
        schema_errors = validate_route_replan_handoff_audit_row(row)
        checks.append(
            _check(
                f"optional_route_replan_handoff_audit_row_{idx}_schema_valid",
                "optional_artifacts",
                "route-replan handoff audit row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=schema_errors,
            )
        )
    return checks


def _runtime_handoff_audit_optional_checks(
    bundle_dir: Path,
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    artifact_dir = (
        bundle_dir / "artifacts" / "formalization_gap_planner_runtime_handoff_audit"
    )
    manifest_path = (
        artifact_dir / "formalization_gap_planner_runtime_handoff_audit_manifest.json"
    )
    rows_jsonl_path = artifact_dir / "formalization_gap_planner_runtime_handoff_audit.jsonl"
    row_schema_path = (
        artifact_dir / "formalization_gap_planner_runtime_handoff_audit_row.schema.json"
    )
    manifest = _read_json_no_error(manifest_path)
    rows, row_errors = _read_jsonl_dict_rows_no_error(rows_jsonl_path)
    n_handoffs = int(manifest.get("n_handoffs", 0) or 0)
    n_checks = int(manifest.get("n_checks", 0) or 0)
    n_prompt_packets = int(manifest.get("n_llm_prompt_packets", 0) or 0)
    n_tier_haiku = int(manifest.get("n_llm_prompt_model_tier_haiku", 0) or 0)
    n_tier_sonnet = int(manifest.get("n_llm_prompt_model_tier_sonnet", 0) or 0)
    n_tier_opus = int(manifest.get("n_llm_prompt_model_tier_opus", 0) or 0)
    n_tier_accounted = n_tier_haiku + n_tier_sonnet + n_tier_opus
    checks = [
        _check(
            "optional_runtime_handoff_audit_row_schema_file",
            "optional_artifacts",
            "optional runtime handoff audit row schema exists",
            str(row_schema_path.exists()),
            row_schema_path.exists(),
        ),
        _check(
            "optional_runtime_handoff_audit_manifest_schema_valid_count",
            "optional_artifacts",
            "runtime handoff audit manifest schema-valid count matches row count",
            (
                f"{manifest.get('n_row_schema_valid', 0)}/"
                f"{manifest.get('n_checks', 0)}; "
                f"invalid={manifest.get('n_row_schema_invalid', 0)}"
            ),
            n_checks > 0
            and int(manifest.get("n_row_schema_valid", 0) or 0) == n_checks
            and int(manifest.get("n_row_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "optional_runtime_handoff_audit_jsonl_parse",
            "optional_artifacts",
            "runtime handoff audit JSONL parses into object rows",
            "; ".join(row_errors) if row_errors else f"rows={len(rows)}",
            not row_errors,
            errors=row_errors,
        ),
        _check(
            "optional_runtime_handoff_audit_jsonl_row_count",
            "optional_artifacts",
            "runtime handoff audit JSONL rows match manifest check count",
            f"jsonl={len(rows)} manifest={n_checks}",
            len(rows) == n_checks,
        ),
        _check(
            "optional_runtime_handoff_audit_cost_control",
            "optional_artifacts",
            "all runtime handoffs preserve prompt-only cost control",
            (
                f"cost={manifest.get('n_cost_control_ok', 0)}/"
                f"{n_handoffs}; live={manifest.get('n_live_explicit_ok', 0)}/"
                f"{n_handoffs}"
            ),
            n_handoffs > 0
            and int(manifest.get("n_cost_control_ok", 0) or 0) == n_handoffs
            and int(manifest.get("n_live_explicit_ok", 0) or 0) == n_handoffs,
        ),
        _check(
            "optional_runtime_handoff_audit_prompt_smoke",
            "optional_artifacts",
            "prompt-only route-planner smoke staged requests without provider invocation",
            (
                f"prompt_smoke={manifest.get('n_llm_prompt_smoke_ok', 0)}/"
                f"{n_handoffs}; packets={n_prompt_packets}"
            ),
            n_handoffs > 0
            and int(manifest.get("n_llm_prompt_smoke_ok", 0) or 0) == n_handoffs
            and n_prompt_packets >= n_handoffs,
        ),
        _check(
            "optional_runtime_handoff_audit_prompt_tier_accounting",
            "optional_artifacts",
            "runtime handoff prompt packets expose accounted Claude tier distribution",
            (
                f"packets={n_prompt_packets}; "
                f"haiku={n_tier_haiku}; sonnet={n_tier_sonnet}; "
                f"opus={n_tier_opus}; "
                f"mismatches={manifest.get('n_llm_prompt_model_tier_mismatches', 0)}"
            ),
            n_prompt_packets > 0
            and n_tier_accounted == n_prompt_packets
            and int(manifest.get("n_llm_prompt_model_tier_mismatches", 0) or 0)
            == 0,
        ),
        _check(
            "optional_runtime_handoff_audit_component_resource_registry_smoke",
            "optional_artifacts",
            "component-resource registry smoke passed for each runtime handoff",
            (
                f"registry_smoke={manifest.get('n_component_resource_registry_smoke_ok', 0)}/"
                f"{n_handoffs}"
            ),
            n_handoffs > 0
            and int(
                manifest.get("n_component_resource_registry_smoke_ok", 0) or 0
            )
            == n_handoffs,
        ),
        _check(
            "optional_runtime_handoff_audit_registry_context_in_prompt",
            "optional_artifacts",
            "runtime handoff prompt packets preserve component/resource/contract context",
            (
                "components="
                f"{manifest.get('n_component_resource_registry_components_in_prompt', 0)}; "
                "resources="
                f"{manifest.get('n_component_resource_registry_resources_in_prompt', 0)}; "
                "contracts="
                f"{manifest.get('n_component_resource_registry_contracts_in_prompt', 0)}"
            ),
            n_handoffs > 0
            and int(
                manifest.get(
                    "n_component_resource_registry_components_in_prompt",
                    0,
                )
                or 0
            )
            > 0
            and int(
                manifest.get(
                    "n_component_resource_registry_resources_in_prompt",
                    0,
                )
                or 0
            )
            > 0
            and int(
                manifest.get(
                    "n_component_resource_registry_contracts_in_prompt",
                    0,
                )
                or 0
            )
            > 0,
        ),
        _check(
            "optional_runtime_handoff_audit_standalone_smoke",
            "optional_artifacts",
            "standalone planner smoke passed for each runtime handoff seed",
            f"{manifest.get('n_standalone_smoke_ok', 0)}/{n_handoffs}",
            n_handoffs > 0
            and int(manifest.get("n_standalone_smoke_ok", 0) or 0) == n_handoffs,
        ),
        _check(
            "optional_runtime_handoff_audit_no_failures",
            "optional_artifacts",
            "runtime handoff audit manifest reports no failed checks",
            f"failed={manifest.get('n_failed', 0)} all_ok={manifest.get('all_ok')}",
            int(manifest.get("n_failed", 0) or 0) == 0
            and bool(manifest.get("all_ok", False)),
        ),
    ]
    for idx, row in enumerate(rows):
        schema_errors = validate_runtime_handoff_audit_row(row)
        checks.append(
            _check(
                f"optional_runtime_handoff_audit_row_{idx}_schema_valid",
                "optional_artifacts",
                "runtime handoff audit row satisfies published schema",
                "; ".join(schema_errors) if schema_errors else "ok",
                not schema_errors,
                errors=tuple(schema_errors),
            )
        )
    return checks


_HANDOFF_PROVENANCE_STRING_FIELDS = (
    "applied_proposal_ids",
    "applied_refinement_evidence_ids",
    "applied_hook_kinds",
    "resource_response_awaiting_request_ids",
    "resource_response_rejected_request_ids",
    "applied_prover_attempt_statuses",
    "applied_prover_diagnostic_signatures",
    "route_revision_reasons",
    "route_revision_summaries",
    "residual_goals",
    "source_refs",
)
_HANDOFF_REVISED_DAG_FIELD_GROUPS = (
    ("revised_informal_knowledge_dag_nodes",),
    ("revised_formal_realization_dag_nodes", "revised_lean_realization_dag_nodes"),
)
_HANDOFF_SEED_SCHEMA_REVISED_DAG_FIELDS = (
    "revised_informal_knowledge_dag_nodes",
    "revised_formal_realization_dag_nodes",
    "revised_lean_realization_dag_nodes",
)
_HANDOFF_SEED_SCHEMA_ROUTE_FIELDS = (
    *_HANDOFF_SEED_SCHEMA_REVISED_DAG_FIELDS,
    "revised_route_alignment_edges",
    "minimal_delta_and_or_cost_graph",
    "llm_route_planner_target_context_summary",
    "llm_route_planner_route_planning_brief",
    "llm_route_planner_route_option_selection_brief",
    "llm_route_planner_primitive_evidence_matrix_witness",
    "llm_route_planner_route_adoption_preconditions",
    "replan_metadata",
)
_HANDOFF_SEED_SCHEMA_METADATA_FIELDS = (
    "applied_proposal_ids",
    "applied_refinement_evidence_ids",
    "applied_hook_kinds",
    "applied_resource_response_traces",
    "resource_response_awaiting_request_ids",
    "resource_response_rejected_request_ids",
    "applied_prover_attempt_statuses",
    "applied_prover_diagnostic_signatures",
    "route_revision_reasons",
    "route_revision_summaries",
    "residual_goals",
    "source_refs",
    "formal_declaration_hits",
    "lean_declaration_hits",
    *_HANDOFF_SEED_SCHEMA_REVISED_DAG_FIELDS,
    "revised_route_alignment_edges",
    "minimal_delta_and_or_cost_graph",
    "llm_route_planner_target_context_summary",
    "llm_route_planner_route_planning_brief",
    "llm_route_planner_route_option_selection_brief",
    "llm_route_planner_primitive_evidence_matrix_witness",
    "llm_route_planner_route_adoption_preconditions",
    "alignment_edge_primitives",
)


def _handoff_seed_provenance_ok(
    rows: list[dict[str, Any]],
    seed: dict[str, Any],
) -> bool:
    seed_routes = _seed_route_index(seed)
    if not seed_routes:
        return False
    for row in rows:
        seed_route_id = str(row.get("standalone_route_id", ""))
        seed_route = seed_routes.get(seed_route_id, {})
        seed_route = seed_route if isinstance(seed_route, dict) else {}
        metadata = (
            seed_route.get("replan_metadata", {})
        )
        if not isinstance(metadata, dict):
            return False
        for field_name in _HANDOFF_PROVENANCE_STRING_FIELDS:
            if _str_tuple(row.get(field_name, [])) != _str_tuple(
                metadata.get(field_name, [])
            ):
                return False
        target_prover_family = _handoff_seed_target_prover_family(
            row,
            seed_route,
            metadata,
        )
        if _is_non_lean_target_prover(target_prover_family) and (
            _dict_tuple(row.get("lean_declaration_hits", []))
            or _dict_tuple(seed_route.get("lean_declaration_hits", []))
            or _dict_tuple(metadata.get("lean_declaration_hits", []))
        ):
            return False
        if _handoff_seed_declaration_target_mismatches(
            row,
            seed_route,
            metadata,
            target_prover_family=target_prover_family,
        ):
            return False
        if _declaration_set(
            _formal_declaration_hits_for_target(row, target_prover_family)
        ) != _declaration_set(
            _formal_declaration_hits_for_target(metadata, target_prover_family)
        ):
            return False
        if _declaration_set(
            _lean_declaration_hits_for_target(row, target_prover_family)
        ) != _declaration_set(
            _lean_declaration_hits_for_target(metadata, target_prover_family)
        ):
            return False
        if _object_hashes(row.get("applied_resource_response_traces", [])) != _object_hashes(
            metadata.get("applied_resource_response_traces", [])
        ):
            return False
    return True


def _handoff_seed_provenance_observed(
    rows: list[dict[str, Any]],
    seed: dict[str, Any],
) -> str:
    seed_routes = _seed_route_index(seed)
    matched = sum(
        1 for row in rows if str(row.get("standalone_route_id", "")) in seed_routes
    )
    resource_rows = sum(
        1
        for row in rows
        if "resource_response_ledger" in _str_tuple(row.get("applied_hook_kinds", []))
    )
    non_lean_legacy_hits = 0
    declaration_target_mismatches = 0
    for row in rows:
        seed_route = seed_routes.get(str(row.get("standalone_route_id", "")), {})
        if not isinstance(seed_route, dict):
            continue
        metadata = seed_route.get("replan_metadata", {})
        metadata = metadata if isinstance(metadata, dict) else {}
        target_prover_family = _handoff_seed_target_prover_family(
            row,
            seed_route,
            metadata,
        )
        if _is_non_lean_target_prover(target_prover_family):
            non_lean_legacy_hits += len(_dict_tuple(row.get("lean_declaration_hits", [])))
            non_lean_legacy_hits += len(
                _dict_tuple(seed_route.get("lean_declaration_hits", []))
            )
            non_lean_legacy_hits += len(
                _dict_tuple(metadata.get("lean_declaration_hits", []))
            )
        declaration_target_mismatches += len(
            _handoff_seed_declaration_target_mismatches(
                row,
                seed_route,
                metadata,
                target_prover_family=target_prover_family,
            )
        )
    return (
        f"matched_seed_routes={matched}/{len(rows)}; "
        f"resource_feedback_rows={resource_rows}; "
        f"diagnostic_signatures={len(_distinct_row_signatures(rows))}; "
        f"non_lean_legacy_lean_declaration_hits={non_lean_legacy_hits}; "
        f"declaration_hit_target_mismatches={declaration_target_mismatches}"
    )


def _handoff_seed_target_prover_family(
    row: dict[str, Any],
    seed_route: dict[str, Any],
    metadata: dict[str, Any],
) -> str:
    standalone_route = row.get("standalone_route", {})
    standalone_route = standalone_route if isinstance(standalone_route, dict) else {}
    standalone_metadata = standalone_route.get("replan_metadata", {})
    standalone_metadata = (
        standalone_metadata if isinstance(standalone_metadata, dict) else {}
    )
    values: list[object] = [
        row.get("target_prover_family", ""),
        standalone_route.get("target_prover_family", ""),
        standalone_metadata.get("target_prover_family", ""),
        seed_route.get("target_prover_family", ""),
        metadata.get("target_prover_family", ""),
    ]
    for container in (row, seed_route, metadata, standalone_route, standalone_metadata):
        values.extend(_target_prover_family_values_from_declaration_hits(container))
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _target_prover_family_values_from_declaration_hits(
    row: dict[str, Any],
) -> tuple[object, ...]:
    values: list[object] = []
    for field_name in ("formal_declaration_hits", "lean_declaration_hits"):
        values.extend(
            hit.get("target_prover_family", "")
            for hit in _dict_tuple(row.get(field_name, []))
        )
    return tuple(values)


def _handoff_seed_declaration_target_mismatches(
    row: dict[str, Any],
    seed_route: dict[str, Any],
    metadata: dict[str, Any],
    *,
    target_prover_family: str,
) -> tuple[str, ...]:
    target_key = _target_prover_key(target_prover_family)
    if not target_key:
        return tuple()
    mismatches: list[str] = []
    for container_name, container in (
        ("handoff_row", row),
        ("seed_route", seed_route),
        ("seed_replan_metadata", metadata),
    ):
        for field_name in ("formal_declaration_hits", "lean_declaration_hits"):
            for index, hit in enumerate(_dict_tuple(container.get(field_name, []))):
                hit_family = str(hit.get("target_prover_family", "") or "").strip()
                if hit_family and _target_prover_key(hit_family) != target_key:
                    mismatches.append(
                        f"{container_name}.{field_name}[{index}] target_prover_family"
                    )
                    continue
                source_type_family = _declaration_hit_source_type_target_key(hit)
                if (
                    not hit_family
                    and source_type_family
                    and source_type_family != target_key
                ):
                    mismatches.append(
                        f"{container_name}.{field_name}[{index}] source_type"
                    )
    return tuple(mismatches)


def _declaration_hit_source_type_target_key(row: dict[str, object]) -> str:
    source_type = (
        row.get("source_type")
        or row.get("source_kind")
        or row.get("library_family")
        or row.get("source_prover_family")
        or row.get("prover_family")
        or ""
    )
    return _source_type_target_prover_key(source_type)


def _source_type_target_prover_key(value: object) -> str:
    key = _target_prover_key(value)
    if not key:
        return ""
    tokens = {token for token in re.split(r"[^a-z0-9]+", key) if token}
    if key in {"mathlib", "lean4_library"} or {"lean", "lean4", "mathlib"} & tokens:
        return "lean4"
    if key in {"coq", "coq8", "coq_library", "rocq_library"} or {
        "coq",
        "coq8",
        "rocq",
    } & tokens:
        return "rocq"
    if key in {"isabelle_hol", "isabelle_library"} or "isabelle" in tokens:
        return "isabelle"
    if key in {"agda_library"} or "agda" in tokens:
        return "agda"
    return ""


def _formal_declaration_hits_for_target(
    row: dict[str, Any],
    target_prover_family: str,
) -> tuple[dict[str, Any], ...]:
    if "formal_declaration_hits" in row:
        return _dict_tuple(row.get("formal_declaration_hits", []))
    if not _is_non_lean_target_prover(target_prover_family):
        return _dict_tuple(row.get("lean_declaration_hits", []))
    return tuple()


def _lean_declaration_hits_for_target(
    row: dict[str, Any],
    target_prover_family: str,
) -> tuple[dict[str, Any], ...]:
    if _is_non_lean_target_prover(target_prover_family):
        return tuple()
    if "lean_declaration_hits" in row:
        return _dict_tuple(row.get("lean_declaration_hits", []))
    return _dict_tuple(row.get("formal_declaration_hits", []))


def _is_non_lean_target_prover(target_prover_family: str) -> bool:
    target_key = _target_prover_key(target_prover_family)
    return bool(target_key) and target_key != "lean4"


def _standalone_seed_schema_replan_metadata_ok(schema: dict[str, Any]) -> bool:
    route_props, metadata_props = _standalone_seed_schema_replan_metadata_props(schema)
    if not route_props or not metadata_props:
        return False
    if not set(_HANDOFF_SEED_SCHEMA_ROUTE_FIELDS).issubset(route_props):
        return False
    if not set(_HANDOFF_SEED_SCHEMA_METADATA_FIELDS).issubset(metadata_props):
        return False
    return (
        _schema_ref(
            route_props.get("revised_informal_knowledge_dag_nodes", {}),
            "items",
        )
        == "#/$defs/dag_node"
        and _schema_ref(
            route_props.get("revised_route_alignment_edges", {}),
            "items",
        )
        == "#/$defs/route_alignment_edge"
        and _schema_ref(
            route_props.get("revised_formal_realization_dag_nodes", {}),
            "items",
        )
        == "#/$defs/dag_node"
        and _schema_ref(
            route_props.get("minimal_delta_and_or_cost_graph", {}),
        )
        == "#/$defs/minimal_delta_and_or_cost_graph"
        and _schema_ref(
            metadata_props.get("formal_declaration_hits", {}),
            "items",
        )
        == "#/$defs/formal_declaration_hit"
        and _schema_ref(
            metadata_props.get("lean_declaration_hits", {}),
            "items",
        )
        == "#/$defs/lean_declaration_hit"
        and _schema_ref(
            metadata_props.get("revised_formal_realization_dag_nodes", {}),
            "items",
        )
        == "#/$defs/dag_node"
        and _schema_ref(
            metadata_props.get("revised_route_alignment_edges", {}),
            "items",
        )
        == "#/$defs/route_alignment_edge"
        and _schema_ref(
            metadata_props.get("minimal_delta_and_or_cost_graph", {}),
        )
        == "#/$defs/minimal_delta_and_or_cost_graph"
    )


def _standalone_seed_schema_replan_metadata_observed(schema: dict[str, Any]) -> str:
    route_props, metadata_props = _standalone_seed_schema_replan_metadata_props(schema)
    route_fields = set(route_props)
    metadata_fields = set(metadata_props)
    missing_route = sorted(set(_HANDOFF_SEED_SCHEMA_ROUTE_FIELDS) - route_fields)
    missing_metadata = sorted(
        set(_HANDOFF_SEED_SCHEMA_METADATA_FIELDS) - metadata_fields
    )
    return (
        f"missing_route={','.join(missing_route)}; "
        f"missing_metadata={','.join(missing_metadata)}"
    )


def _standalone_seed_schema_replan_metadata_props(
    schema: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    defs = schema.get("$defs", {})
    if not isinstance(defs, dict):
        return {}, {}
    route = defs.get("route", {})
    metadata = defs.get("replan_metadata", {})
    route_props = route.get("properties", {}) if isinstance(route, dict) else {}
    metadata_props = (
        metadata.get("properties", {}) if isinstance(metadata, dict) else {}
    )
    return (
        route_props if isinstance(route_props, dict) else {},
        metadata_props if isinstance(metadata_props, dict) else {},
    )


def _route_revision_overlay_generic_formal_dag_errors(
    rows: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    if not rows:
        errors.append("no overlay rows")
    expected = sum(
        len(_object_hashes(row.get("revised_formal_realization_dag_nodes", [])))
        for row in rows
    )
    if "n_formal_realization_dag_nodes" not in manifest:
        errors.append("manifest n_formal_realization_dag_nodes missing")
    elif int(manifest.get("n_formal_realization_dag_nodes", 0) or 0) != expected:
        errors.append("manifest n_formal_realization_dag_nodes mismatch")
    for idx, row in enumerate(rows):
        errors.extend(_generic_revised_formal_dag_field_errors(f"row {idx}", row))
    return tuple(errors)


def _route_revision_overlay_generic_formal_dag_observed(
    rows: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> str:
    generic = sum(
        len(_object_hashes(row.get("revised_formal_realization_dag_nodes", [])))
        for row in rows
    )
    legacy = sum(
        len(_object_hashes(row.get("revised_lean_realization_dag_nodes", [])))
        for row in rows
    )
    return (
        f"rows={len(rows)}; generic={generic}; legacy={legacy}; "
        f"manifest={manifest.get('n_formal_realization_dag_nodes', 'missing')}"
    )


def _handoff_generic_formal_dag_errors(
    rows: list[dict[str, Any]],
    seed: dict[str, Any],
    manifest: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    if not rows:
        errors.append("no handoff rows")
    expected = sum(
        len(_object_hashes(row.get("revised_formal_realization_dag_nodes", [])))
        for row in rows
    )
    if "n_revised_formal_realization_dag_nodes" not in manifest:
        errors.append("manifest n_revised_formal_realization_dag_nodes missing")
    elif int(manifest.get("n_revised_formal_realization_dag_nodes", 0) or 0) != expected:
        errors.append("manifest n_revised_formal_realization_dag_nodes mismatch")
    seed_routes = _seed_route_index(seed)
    for idx, row in enumerate(rows):
        errors.extend(_generic_revised_formal_dag_field_errors(f"row {idx}", row))
        seed_route_id = str(row.get("standalone_route_id", ""))
        seed_route = seed_routes.get(seed_route_id, {})
        if not seed_route:
            errors.append(f"seed route {seed_route_id} missing")
            continue
        errors.extend(
            _generic_revised_formal_dag_field_errors(
                f"seed route {seed_route_id}",
                seed_route,
            )
        )
        metadata = _seed_route_metadata(seed_route)
        if not isinstance(metadata, dict):
            errors.append(f"seed metadata {seed_route_id} missing")
            continue
        errors.extend(
            _generic_revised_formal_dag_field_errors(
                f"seed metadata {seed_route_id}",
                metadata,
            )
        )
    return tuple(errors)


def _handoff_generic_formal_dag_observed(
    rows: list[dict[str, Any]],
    seed: dict[str, Any],
    manifest: dict[str, Any],
) -> str:
    seed_routes = _seed_route_index(seed)
    seed_generic = 0
    metadata_generic = 0
    for row in rows:
        seed_route = seed_routes.get(str(row.get("standalone_route_id", "")), {})
        seed_generic += len(
            _object_hashes(seed_route.get("revised_formal_realization_dag_nodes", []))
        )
        metadata = _seed_route_metadata(seed_route)
        metadata = metadata if isinstance(metadata, dict) else {}
        metadata_generic += len(
            _object_hashes(metadata.get("revised_formal_realization_dag_nodes", []))
        )
    row_generic = sum(
        len(_object_hashes(row.get("revised_formal_realization_dag_nodes", [])))
        for row in rows
    )
    row_legacy = sum(
        len(_object_hashes(row.get("revised_lean_realization_dag_nodes", [])))
        for row in rows
    )
    return (
        f"rows={len(rows)}; row_generic={row_generic}; row_legacy={row_legacy}; "
        f"seed_generic={seed_generic}; metadata_generic={metadata_generic}; "
        f"manifest={manifest.get('n_revised_formal_realization_dag_nodes', 'missing')}"
    )


def _generic_revised_formal_dag_field_errors(
    label: str,
    row: dict[str, Any],
) -> tuple[str, ...]:
    generic = _object_hashes(row.get("revised_formal_realization_dag_nodes", []))
    legacy = _object_hashes(row.get("revised_lean_realization_dag_nodes", []))
    errors: list[str] = []
    if not generic:
        errors.append(f"{label} revised_formal_realization_dag_nodes missing")
    if legacy and generic and legacy != generic:
        errors.append(
            f"{label} revised_lean_realization_dag_nodes differs from formal DAG"
        )
    return tuple(errors)


def _schema_ref(schema: Any, field_name: str = "") -> str:
    if not isinstance(schema, dict):
        return ""
    if not field_name:
        return str(schema.get("$ref", ""))
    field = schema.get(field_name, {})
    if not isinstance(field, dict):
        return ""
    return str(field.get("$ref", ""))


def _handoff_seed_alignment_errors(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    metadata = _seed_route_metadata(seed_route)
    if not seed_route:
        errors.append("seed route missing")
    if not isinstance(metadata, dict):
        errors.append("seed route replan_metadata missing")
        return tuple(errors)
    if "revised_route_alignment_edges" not in row:
        errors.append("row revised_route_alignment_edges missing")
    if "revised_route_alignment_edges" not in seed_route:
        errors.append("seed route revised_route_alignment_edges missing")
    if "revised_route_alignment_edges" not in metadata:
        errors.append("seed metadata revised_route_alignment_edges missing")
    row_hashes = _object_hashes(row.get("revised_route_alignment_edges", []))
    metadata_hashes = _object_hashes(metadata.get("revised_route_alignment_edges", []))
    route_hashes = _object_hashes(seed_route.get("revised_route_alignment_edges", []))
    if not row_hashes:
        errors.append("row revised_route_alignment_edges empty")
    if row_hashes != metadata_hashes:
        errors.append("seed metadata revised_route_alignment_edges mismatch")
    if row_hashes != route_hashes:
        errors.append("seed route revised_route_alignment_edges mismatch")
    selected = set(_str_tuple(row.get("revised_selected_primitives", [])))
    aligned = _alignment_primitives(row.get("revised_route_alignment_edges", []))
    missing = sorted(selected - aligned)
    if missing:
        errors.append(
            "row revised_route_alignment_edges miss selected primitives: "
            + ",".join(missing)
        )
    return tuple(errors)


def _handoff_seed_alignment_observed(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> str:
    metadata = _seed_route_metadata(seed_route)
    metadata = metadata if isinstance(metadata, dict) else {}
    selected = set(_str_tuple(row.get("revised_selected_primitives", [])))
    aligned = _alignment_primitives(row.get("revised_route_alignment_edges", []))
    missing = sorted(selected - aligned)
    return (
        f"row_edges={len(_object_hashes(row.get('revised_route_alignment_edges', [])))}; "
        f"metadata_edges={len(_object_hashes(metadata.get('revised_route_alignment_edges', [])))}; "
        f"seed_route_edges={len(_object_hashes(seed_route.get('revised_route_alignment_edges', [])))}; "
        f"missing_selected={','.join(missing)}"
    )


def _handoff_seed_dag_errors(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    metadata = _seed_route_metadata(seed_route)
    if not seed_route:
        errors.append("seed route missing")
    if not isinstance(metadata, dict):
        errors.append("seed route replan_metadata missing")
        return tuple(errors)
    for field_names in _HANDOFF_REVISED_DAG_FIELD_GROUPS:
        field_label = field_names[0]
        row_hashes = _first_field_object_hashes(row, field_names)
        seed_hashes = _first_field_object_hashes(seed_route, field_names)
        metadata_hashes = _first_field_object_hashes(metadata, field_names)
        if not row_hashes:
            errors.append(f"row {field_label} missing")
        if not seed_hashes:
            errors.append(f"seed route {field_label} missing")
        if not metadata_hashes:
            errors.append(f"seed metadata {field_label} missing")
        if row_hashes != seed_hashes:
            errors.append(f"seed route {field_label} mismatch")
        if row_hashes != metadata_hashes:
            errors.append(f"seed metadata {field_label} mismatch")
    return tuple(errors)


def _handoff_seed_dag_observed(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> str:
    metadata = _seed_route_metadata(seed_route)
    metadata = metadata if isinstance(metadata, dict) else {}
    parts = []
    for field_names in _HANDOFF_REVISED_DAG_FIELD_GROUPS:
        field_name = field_names[0]
        parts.append(
            f"{field_name}:row={len(_first_field_object_hashes(row, field_names))}"
            f",metadata={len(_first_field_object_hashes(metadata, field_names))}"
            f",seed_route={len(_first_field_object_hashes(seed_route, field_names))}"
        )
    return "; ".join(parts)


def _handoff_seed_target_context_errors(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    metadata = _seed_route_metadata(seed_route)
    if not seed_route:
        errors.append("seed route missing")
    if not isinstance(metadata, dict):
        errors.append("seed route replan_metadata missing")
        return tuple(errors)
    row_packet = _as_dict(row.get("target_theorem_context_packet", {}))
    route_packet = _as_dict(seed_route.get("target_theorem_context_packet", {}))
    metadata_packet = _as_dict(metadata.get("target_theorem_context_packet", {}))
    metadata_llm_packet = _as_dict(
        metadata.get("llm_route_planner_target_theorem_context_packet", {})
    )
    if not row_packet:
        if route_packet or metadata_packet or metadata_llm_packet:
            errors.append("seed route carries target context absent from handoff row")
        return tuple(errors)
    if route_packet != row_packet:
        errors.append("seed route target_theorem_context_packet mismatch")
    if metadata_packet != row_packet:
        errors.append("seed metadata target_theorem_context_packet mismatch")
    if metadata_llm_packet and metadata_llm_packet != row_packet:
        errors.append(
            "seed metadata llm_route_planner_target_theorem_context_packet mismatch"
        )
    target_prover_family = _handoff_seed_target_prover_family(
        row,
        seed_route,
        metadata,
    )
    packet_target = str(row_packet.get("target_prover_family", "")).strip()
    if (
        packet_target
        and target_prover_family
        and _target_prover_key(packet_target)
        != _target_prover_key(target_prover_family)
    ):
        errors.append("target_theorem_context_packet target_prover_family mismatch")
    return tuple(errors)


def _handoff_seed_target_context_observed(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> str:
    metadata = _seed_route_metadata(seed_route)
    metadata = metadata if isinstance(metadata, dict) else {}
    row_packet = _as_dict(row.get("target_theorem_context_packet", {}))
    route_packet = _as_dict(seed_route.get("target_theorem_context_packet", {}))
    metadata_packet = _as_dict(metadata.get("target_theorem_context_packet", {}))
    metadata_llm_packet = _as_dict(
        metadata.get("llm_route_planner_target_theorem_context_packet", {})
    )
    return (
        f"row_packet={bool(row_packet)}; "
        f"seed_route_packet={bool(route_packet)}; "
        f"metadata_packet={bool(metadata_packet)}; "
        f"metadata_llm_packet={bool(metadata_llm_packet)}; "
        f"packet_target={row_packet.get('target_prover_family', '')}"
    )


def _handoff_seed_target_context_summary_errors(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    metadata = _seed_route_metadata(seed_route)
    if not seed_route:
        errors.append("seed route missing")
    if not isinstance(metadata, dict):
        errors.append("seed route replan_metadata missing")
        return tuple(errors)
    row_summary = _as_dict(row.get("target_context_summary", {}))
    route_summary = _as_dict(
        seed_route.get("llm_route_planner_target_context_summary", {})
    )
    metadata_summary = _as_dict(
        metadata.get("llm_route_planner_target_context_summary", {})
    )
    if not row_summary:
        if route_summary or metadata_summary:
            errors.append(
                "seed route carries target-context summary absent from handoff row"
            )
        return tuple(errors)
    if route_summary != row_summary:
        errors.append("seed route llm_route_planner_target_context_summary mismatch")
    if metadata_summary != row_summary:
        errors.append(
            "seed metadata llm_route_planner_target_context_summary mismatch"
        )
    return tuple(errors)


def _handoff_seed_target_context_summary_observed(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> str:
    metadata = _seed_route_metadata(seed_route)
    metadata = metadata if isinstance(metadata, dict) else {}
    row_summary = _as_dict(row.get("target_context_summary", {}))
    route_summary = _as_dict(
        seed_route.get("llm_route_planner_target_context_summary", {})
    )
    metadata_summary = _as_dict(
        metadata.get("llm_route_planner_target_context_summary", {})
    )
    return (
        f"row_summary={bool(row_summary)}; "
        f"seed_route_summary={bool(route_summary)}; "
        f"metadata_summary={bool(metadata_summary)}; "
        f"route_matches={route_summary == row_summary if row_summary else not route_summary}; "
        f"metadata_matches={metadata_summary == row_summary if row_summary else not metadata_summary}"
    )


def _handoff_seed_route_planning_brief_errors(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    metadata = _seed_route_metadata(seed_route)
    if not seed_route:
        errors.append("seed route missing")
    if not isinstance(metadata, dict):
        errors.append("seed route replan_metadata missing")
        return tuple(errors)
    row_brief = _as_dict(row.get("route_planning_brief", {}))
    route_brief = _as_dict(seed_route.get("llm_route_planner_route_planning_brief", {}))
    metadata_brief = _as_dict(
        metadata.get("llm_route_planner_route_planning_brief", {})
    )
    if not row_brief:
        if route_brief or metadata_brief:
            errors.append("seed route carries route-planning brief absent from handoff row")
        return tuple(errors)
    if route_brief != row_brief:
        errors.append("seed route llm_route_planner_route_planning_brief mismatch")
    if metadata_brief != row_brief:
        errors.append(
            "seed metadata llm_route_planner_route_planning_brief mismatch"
        )
    return tuple(errors)


def _handoff_seed_route_planning_brief_observed(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> str:
    metadata = _seed_route_metadata(seed_route)
    metadata = metadata if isinstance(metadata, dict) else {}
    row_brief = _as_dict(row.get("route_planning_brief", {}))
    route_brief = _as_dict(seed_route.get("llm_route_planner_route_planning_brief", {}))
    metadata_brief = _as_dict(
        metadata.get("llm_route_planner_route_planning_brief", {})
    )
    return (
        f"row_brief={bool(row_brief)}; "
        f"seed_route_brief={bool(route_brief)}; "
        f"metadata_brief={bool(metadata_brief)}; "
        f"route_matches={route_brief == row_brief if row_brief else not route_brief}; "
        f"metadata_matches={metadata_brief == row_brief if row_brief else not metadata_brief}"
    )


def _handoff_seed_route_option_selection_brief_errors(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    metadata = _seed_route_metadata(seed_route)
    if not seed_route:
        errors.append("seed route missing")
    if not isinstance(metadata, dict):
        errors.append("seed route replan_metadata missing")
        return tuple(errors)
    row_brief = _as_dict(row.get("route_option_selection_brief", {}))
    route_brief = _as_dict(
        seed_route.get("llm_route_planner_route_option_selection_brief", {})
    )
    metadata_brief = _as_dict(
        metadata.get("llm_route_planner_route_option_selection_brief", {})
    )
    if not row_brief:
        if route_brief or metadata_brief:
            errors.append(
                "seed route carries route-option selection brief absent from "
                "handoff row"
            )
        return tuple(errors)
    if route_brief != row_brief:
        errors.append(
            "seed route llm_route_planner_route_option_selection_brief mismatch"
        )
    if metadata_brief != row_brief:
        errors.append(
            "seed metadata llm_route_planner_route_option_selection_brief mismatch"
        )
    return tuple(errors)


def _handoff_seed_route_option_selection_brief_observed(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> str:
    metadata = _seed_route_metadata(seed_route)
    metadata = metadata if isinstance(metadata, dict) else {}
    row_brief = _as_dict(row.get("route_option_selection_brief", {}))
    route_brief = _as_dict(
        seed_route.get("llm_route_planner_route_option_selection_brief", {})
    )
    metadata_brief = _as_dict(
        metadata.get("llm_route_planner_route_option_selection_brief", {})
    )
    return (
        f"row_brief={bool(row_brief)}; "
        f"seed_route_brief={bool(route_brief)}; "
        f"metadata_brief={bool(metadata_brief)}; "
        f"route_matches={route_brief == row_brief if row_brief else not route_brief}; "
        f"metadata_matches={metadata_brief == row_brief if row_brief else not metadata_brief}"
    )


def _handoff_seed_primitive_evidence_matrix_witness_errors(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    metadata = _seed_route_metadata(seed_route)
    if not seed_route:
        errors.append("seed route missing")
    if not isinstance(metadata, dict):
        errors.append("seed route replan_metadata missing")
        return tuple(errors)
    row_witness = _as_dict(row.get("primitive_evidence_matrix_witness", {}))
    route_witness = _as_dict(
        seed_route.get("llm_route_planner_primitive_evidence_matrix_witness", {})
    )
    metadata_witness = _as_dict(
        metadata.get("llm_route_planner_primitive_evidence_matrix_witness", {})
    )
    if not row_witness:
        if route_witness or metadata_witness:
            errors.append(
                "seed route carries primitive-evidence matrix witness absent from "
                "handoff row"
            )
        return tuple(errors)
    if route_witness != row_witness:
        errors.append(
            "seed route llm_route_planner_primitive_evidence_matrix_witness mismatch"
        )
    if metadata_witness != row_witness:
        errors.append(
            "seed metadata llm_route_planner_primitive_evidence_matrix_witness mismatch"
        )
    return tuple(errors)


def _handoff_seed_primitive_evidence_matrix_witness_observed(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> str:
    metadata = _seed_route_metadata(seed_route)
    metadata = metadata if isinstance(metadata, dict) else {}
    row_witness = _as_dict(row.get("primitive_evidence_matrix_witness", {}))
    route_witness = _as_dict(
        seed_route.get("llm_route_planner_primitive_evidence_matrix_witness", {})
    )
    metadata_witness = _as_dict(
        metadata.get("llm_route_planner_primitive_evidence_matrix_witness", {})
    )
    return (
        f"row_witness={bool(row_witness)}; "
        f"seed_route_witness={bool(route_witness)}; "
        f"metadata_witness={bool(metadata_witness)}; "
        f"route_matches={route_witness == row_witness if row_witness else not route_witness}; "
        "metadata_matches="
        f"{metadata_witness == row_witness if row_witness else not metadata_witness}"
    )


def _handoff_seed_route_adoption_preconditions_errors(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    metadata = _seed_route_metadata(seed_route)
    if not seed_route:
        errors.append("seed route missing")
    if not isinstance(metadata, dict):
        errors.append("seed route replan_metadata missing")
        return tuple(errors)
    row_preconditions = _as_dict(row.get("route_adoption_preconditions", {}))
    route_preconditions = _as_dict(
        seed_route.get("llm_route_planner_route_adoption_preconditions", {})
    )
    metadata_preconditions = _as_dict(
        metadata.get("llm_route_planner_route_adoption_preconditions", {})
    )
    if not row_preconditions:
        if route_preconditions or metadata_preconditions:
            errors.append(
                "seed route carries route-adoption preconditions absent from handoff row"
            )
        return tuple(errors)
    if route_preconditions != row_preconditions:
        errors.append(
            "seed route llm_route_planner_route_adoption_preconditions mismatch"
        )
    if metadata_preconditions != row_preconditions:
        errors.append(
            "seed metadata llm_route_planner_route_adoption_preconditions mismatch"
        )
    return tuple(errors)


def _handoff_seed_route_adoption_preconditions_observed(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> str:
    metadata = _seed_route_metadata(seed_route)
    metadata = metadata if isinstance(metadata, dict) else {}
    row_preconditions = _as_dict(row.get("route_adoption_preconditions", {}))
    route_preconditions = _as_dict(
        seed_route.get("llm_route_planner_route_adoption_preconditions", {})
    )
    metadata_preconditions = _as_dict(
        metadata.get("llm_route_planner_route_adoption_preconditions", {})
    )
    blockers = _str_tuple(
        row_preconditions.get("known_pre_response_blockers", [])
    )
    required_fields = _str_tuple(
        row_preconditions.get("response_required_fields", [])
    )
    return (
        f"row_preconditions={bool(row_preconditions)}; "
        f"seed_route_preconditions={bool(route_preconditions)}; "
        f"metadata_preconditions={bool(metadata_preconditions)}; "
        f"route_matches={route_preconditions == row_preconditions if row_preconditions else not route_preconditions}; "
        f"metadata_matches={metadata_preconditions == row_preconditions if row_preconditions else not metadata_preconditions}; "
        f"blockers={len(blockers)}; required_fields={len(required_fields)}"
    )


def _seed_route_metadata(seed_route: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(seed_route, dict):
        return None
    metadata = seed_route.get("replan_metadata", {})
    return metadata if isinstance(metadata, dict) else None


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _seed_resource_feedback_route_count(seed: dict[str, Any]) -> int:
    count = 0
    for seed_route in _seed_route_index(seed).values():
        metadata = seed_route.get("replan_metadata", {})
        if not isinstance(metadata, dict):
            continue
        if "resource_response_ledger" in _str_tuple(metadata.get("applied_hook_kinds", [])):
            count += 1
    return count


def _seed_route_index(seed: dict[str, Any]) -> dict[str, dict[str, Any]]:
    routes = seed.get("routes", [])
    if not isinstance(routes, list):
        return {}
    return {
        str(route.get("route_id", "")): route
        for route in routes
        if isinstance(route, dict) and str(route.get("route_id", ""))
    }


def _distinct_row_signatures(rows: list[dict[str, Any]]) -> set[str]:
    return {
        signature
        for row in rows
        for signature in _str_tuple(row.get("applied_prover_diagnostic_signatures", []))
    }


def _object_hashes(values: Any) -> set[str]:
    if not isinstance(values, (list, tuple, set)):
        return set()
    return {stable_hash(value) for value in values if isinstance(value, dict)}


def _first_field_object_hashes(
    row: dict[str, Any],
    field_names: tuple[str, ...],
) -> set[str]:
    for field_name in field_names:
        hashes = _object_hashes(row.get(field_name, []))
        if hashes:
            return hashes
    return set()


def _alignment_primitives(edges: Any) -> set[str]:
    if not isinstance(edges, (list, tuple, set)):
        return set()
    return {
        str(edge.get("primitive", "")).strip()
        for edge in edges
        if isinstance(edge, dict)
        and str(edge.get("kind", "")) == "aligned_to_formal_realization_candidate"
        and str(edge.get("source", "")).strip()
        and str(edge.get("target", "")).strip()
        and str(edge.get("primitive", "")).strip()
    }


def _declaration_set(values: Any) -> set[str]:
    if not isinstance(values, (list, tuple, set)):
        return set()
    declarations: set[str] = set()
    for value in values:
        if not isinstance(value, dict):
            continue
        declaration = str(
            value.get("declaration", "")
            or value.get("declaration_name", "")
            or value.get("name", "")
        ).strip()
        if declaration:
            declarations.add(declaration)
    return declarations


def _bundle_boundary_checks(
    manifest: dict[str, Any],
) -> list[FormalizationGapPlannerPublicationBundleAuditCheck]:
    boundary = str(manifest.get("proof_evidence_boundary", ""))
    status = str(manifest.get("proof_evidence_status", ""))
    return [
        _check(
            "bundle_boundary_text",
            "proof_boundary",
            "not theorem proof evidence",
            boundary[:160],
            "not theorem proof evidence" in boundary,
        ),
        _check(
            "bundle_evidence_status",
            "proof_boundary",
            "not proof evidence status",
            status,
            "NOT_PROOF_EVIDENCE" in status,
        ),
    ]


def _target_intake_row_contract_errors(row: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    required_fields = (
        "schema_version",
        "target_intake_id",
        "target_id",
        "display_name",
        "target_prover_family",
        "library_snapshot_ref",
        "theorem_statement",
        "standalone_route_id",
        "primitive_seed_rows",
        "literature_queries",
        "formal_library_grounding_queries",
        "proof_evidence_status",
        "proof_evidence_boundary",
        "ok",
    )
    for field_name in required_fields:
        if field_name not in row:
            errors.append(f"{field_name} required")
    for field_name in (
        "target_intake_id",
        "target_id",
        "display_name",
        "target_prover_family",
        "library_snapshot_ref",
        "theorem_statement",
        "standalone_route_id",
    ):
        if field_name in row and not str(row.get(field_name, "")).strip():
            errors.append(f"{field_name} must be non-empty")
    for field_name in (
        "primitive_seed_rows",
        "literature_queries",
        "formal_library_grounding_queries",
        "lean_grounding_queries",
    ):
        if field_name in row and not isinstance(row.get(field_name), list):
            errors.append(f"{field_name} must be an array")
    for legacy_field, portable_field in LEGACY_TARGET_INTAKE_FIELD_ALIASES.items():
        if legacy_field in row and portable_field in row:
            if _str_tuple(row[legacy_field]) != _str_tuple(row[portable_field]):
                errors.append(f"{legacy_field} must match {portable_field}")
    if row.get("primitive_seed_rows") == []:
        errors.append("primitive_seed_rows must not be empty")
    if "NOT_PROOF_EVIDENCE" not in str(row.get("proof_evidence_status", "")):
        errors.append("proof_evidence_status must preserve non-proof boundary")
    if "not theorem proof evidence" not in str(
        row.get("proof_evidence_boundary", "")
    ).lower():
        errors.append("proof_evidence_boundary must say not theorem proof evidence")
    if not isinstance(row.get("ok", False), bool):
        errors.append("ok must be boolean")
    return tuple(errors)


def _goal_plan_row_contract_errors(
    row: dict[str, Any],
    manifest_row_ids: set[str],
) -> tuple[str, ...]:
    errors: list[str] = []
    required_fields = (
        "schema_version",
        "planner_component",
        "target_prover_family",
        "library_snapshot_ref",
        "goal_plan_id",
        "route_id",
        "display_name",
        "selected_primitives",
        "and_or_plan_nodes",
        "and_or_plan_edges",
        "informal_knowledge_dag_nodes",
        "formal_realization_dag_nodes",
        "route_alignment_edges",
        "interactive_refinement_hooks",
        "portable_work_packet_contract",
        "proof_evidence_status",
        "proof_evidence_boundary",
        "ok",
    )
    for field_name in required_fields:
        if field_name not in row:
            errors.append(f"{field_name} required")
    goal_plan_id = str(row.get("goal_plan_id", ""))
    if not goal_plan_id:
        errors.append("goal_plan_id must be non-empty")
    elif manifest_row_ids and goal_plan_id not in manifest_row_ids:
        errors.append("goal_plan_id not present in embedded manifest rows")
    if row.get("planner_component") != LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME:
        errors.append("planner_component is not library_aware_formalization_gap_planner")
    for field_name in (
        "selected_primitives",
        "and_or_plan_nodes",
        "and_or_plan_edges",
        "informal_knowledge_dag_nodes",
        "formal_realization_dag_nodes",
        "lean_realization_dag_nodes",
        "route_alignment_edges",
        "interactive_refinement_hooks",
    ):
        if field_name in row and not isinstance(row.get(field_name), list):
            errors.append(f"{field_name} must be an array")
    if row.get("selected_primitives") == []:
        errors.append("selected_primitives must not be empty")
    if row.get("route_alignment_edges") == []:
        errors.append("route_alignment_edges must not be empty")
    if "NOT_PROOF_EVIDENCE" not in str(row.get("proof_evidence_status", "")):
        errors.append("proof_evidence_status must preserve non-proof boundary")
    if "not theorem proof evidence" not in str(
        row.get("proof_evidence_boundary", "")
    ).lower():
        errors.append("proof_evidence_boundary must say not theorem proof evidence")
    if not isinstance(row.get("ok", False), bool):
        errors.append("ok must be boolean")
    return tuple(errors)


def _audit_check_row_contract_errors(row: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    required_fields = (
        "schema_version",
        "check_id",
        "check_name",
        "category",
        "expected",
        "observed",
        "ok",
        "severity",
        "errors",
    )
    for field_name in required_fields:
        if field_name not in row:
            errors.append(f"{field_name} required")
    for field_name in ("check_id", "check_name", "category", "expected"):
        if field_name in row and not str(row.get(field_name, "")).strip():
            errors.append(f"{field_name} must be non-empty")
    if "schema_version" in row and (
        not isinstance(row.get("schema_version"), int)
        or isinstance(row.get("schema_version"), bool)
    ):
        errors.append("schema_version must be integer")
    if "ok" in row and not isinstance(row.get("ok"), bool):
        errors.append("ok must be boolean")
    if row.get("severity") not in {"error", "warning", "info"}:
        errors.append("severity must be error, warning, or info")
    if "errors" in row and not isinstance(row.get("errors"), list):
        errors.append("errors must be an array")
    if row.get("ok") is True and row.get("errors") not in ([], None):
        errors.append("ok rows must not carry errors")
    return tuple(errors)


def _route_stability_generic_prover_fields_observed(row: dict[str, Any]) -> bool:
    return bool(
        _str_tuple(row.get("prover_attempt_statuses", []))
        or _str_tuple(row.get("prover_attempt_classes", []))
        or _str_tuple(row.get("target_prover_families", []))
        or _str_tuple(row.get("residual_goals", []))
        or row.get("needs_more_proof_state_feedback") is True
    )


def _route_stability_generic_prover_field_errors(
    row: dict[str, Any],
) -> tuple[str, ...]:
    statuses = _str_tuple(row.get("prover_attempt_statuses", []))
    classes = _str_tuple(row.get("prover_attempt_classes", []))
    families = _str_tuple(row.get("target_prover_families", []))
    errors: list[str] = []
    if statuses and not classes:
        errors.append("prover_attempt_statuses present but prover_attempt_classes empty")
    errors.extend(_generic_prover_class_legacy_errors("prover_attempt_classes", classes))
    if _prover_classes_require_target_family(classes) and not families:
        errors.append("target prover attempt classes present but target_prover_families empty")
    return tuple(errors)


def _proof_state_triage_generic_prover_fields_observed(row: dict[str, Any]) -> bool:
    return bool(
        str(row.get("triage_class", "")).strip()
        or str(row.get("prover_triage_class", "")).strip()
        or _str_tuple(row.get("applied_prover_attempt_statuses", []))
        or _str_tuple(row.get("applied_prover_attempt_classes", []))
        or _str_tuple(row.get("target_prover_families", []))
    )


def _proof_state_triage_generic_prover_field_errors(
    row: dict[str, Any],
) -> tuple[str, ...]:
    triage_class = str(row.get("triage_class", "")).strip()
    prover_triage_class = str(row.get("prover_triage_class", "")).strip()
    statuses = _str_tuple(row.get("applied_prover_attempt_statuses", []))
    classes = _str_tuple(row.get("applied_prover_attempt_classes", []))
    families = _str_tuple(row.get("target_prover_families", []))
    errors: list[str] = []
    if triage_class and not prover_triage_class:
        errors.append("triage_class present but prover_triage_class empty")
    if statuses and not classes:
        errors.append(
            "applied_prover_attempt_statuses present but applied_prover_attempt_classes empty"
        )
    errors.extend(
        _generic_prover_triage_legacy_errors(
            "prover_triage_class",
            prover_triage_class,
        )
    )
    errors.extend(
        _generic_prover_class_legacy_errors(
            "applied_prover_attempt_classes",
            classes,
        )
    )
    if _prover_classes_require_target_family(classes) and not families:
        errors.append(
            "target prover attempt classes present but target_prover_families empty"
        )
    return tuple(errors)


def _interactive_session_generic_prover_fields_observed(row: dict[str, Any]) -> bool:
    return bool(
        str(row.get("triage_class", "")).strip()
        or str(row.get("prover_triage_class", "")).strip()
        or _str_tuple(row.get("applied_prover_attempt_classes", []))
        or _str_tuple(row.get("target_prover_families", []))
        or _str_tuple(row.get("residual_goals", []))
        or row.get("needs_more_proof_state_feedback") is True
        or str(row.get("next_interaction_kind", "")).strip() == "proof_state_feedback"
    )


def _interactive_session_generic_prover_field_errors(
    row: dict[str, Any],
) -> tuple[str, ...]:
    triage_class = str(row.get("triage_class", "")).strip()
    prover_triage_class = str(row.get("prover_triage_class", "")).strip()
    classes = _str_tuple(row.get("applied_prover_attempt_classes", []))
    families = _str_tuple(row.get("target_prover_families", []))
    errors: list[str] = []
    if triage_class and not prover_triage_class:
        errors.append("triage_class present but prover_triage_class empty")
    if classes and not prover_triage_class:
        errors.append(
            "applied_prover_attempt_classes present but prover_triage_class empty"
        )
    errors.extend(
        _generic_prover_triage_legacy_errors(
            "prover_triage_class",
            prover_triage_class,
        )
    )
    errors.extend(
        _generic_prover_class_legacy_errors(
            "applied_prover_attempt_classes",
            classes,
        )
    )
    if _prover_classes_require_target_family(classes) and not families:
        errors.append(
            "target prover attempt classes present but target_prover_families empty"
        )
    return tuple(errors)


def _interactive_session_row_has_formal_attempt_queue(row: dict[str, Any]) -> bool:
    return bool(
        _dict_tuple(row.get("formal_attempt_queue_items", []))
        or _str_tuple(row.get("formal_attempt_queue_attempt_ids", []))
        or _str_tuple(row.get("formal_attempt_queue_ready_attempt_ids", []))
        or _str_tuple(row.get("formal_attempt_queue_execution_commands", []))
        or int(row.get("formal_attempt_queue_item_count", 0) or 0) > 0
        or int(row.get("formal_attempt_queue_ready_item_count", 0) or 0) > 0
        or int(row.get("formal_attempt_queue_blocked_item_count", 0) or 0) > 0
    )


def _interactive_session_formal_attempt_queue_errors(
    row: dict[str, Any],
) -> tuple[str, ...]:
    items = _dict_tuple(row.get("formal_attempt_queue_items", []))
    ready_items = tuple(
        item for item in items if _formal_attempt_queue_item_ready(item)
    )
    blocked_items = tuple(item for item in items if item not in ready_items)
    attempt_ids = _str_tuple([item.get("attempt_id", "") for item in items])
    ready_attempt_ids = _str_tuple(
        [item.get("attempt_id", "") for item in ready_items]
    )
    blocked_attempt_ids = _str_tuple(
        [item.get("attempt_id", "") for item in blocked_items]
    )
    reported_attempt_ids = _str_tuple(row.get("formal_attempt_queue_attempt_ids", []))
    reported_ready_attempt_ids = _str_tuple(
        row.get("formal_attempt_queue_ready_attempt_ids", [])
    )
    commands = _str_tuple(row.get("formal_attempt_queue_execution_commands", []))
    command_blob = "\n".join(commands)
    errors: list[str] = []
    if int(row.get("formal_attempt_queue_item_count", 0) or 0) != len(items):
        errors.append("formal_attempt_queue_item_count mismatch")
    if int(row.get("formal_attempt_queue_ready_item_count", 0) or 0) != len(
        ready_items
    ):
        errors.append("formal_attempt_queue_ready_item_count mismatch")
    if int(row.get("formal_attempt_queue_blocked_item_count", 0) or 0) != len(
        blocked_items
    ):
        errors.append("formal_attempt_queue_blocked_item_count mismatch")
    if reported_attempt_ids != attempt_ids:
        errors.append("formal_attempt_queue_attempt_ids mismatch")
    if reported_ready_attempt_ids != ready_attempt_ids:
        errors.append("formal_attempt_queue_ready_attempt_ids mismatch")
    if int(row.get("formal_attempt_queue_execution_command_count", len(commands)) or 0) != len(
        commands
    ):
        errors.append("formal_attempt_queue_execution_command_count mismatch")
    if commands and not any(
        "formalization-gap-planner-prover-adapter-contract" in command
        for command in commands
    ):
        errors.append("formal_attempt_queue commands missing prover-adapter contract")
    for attempt_id in ready_attempt_ids:
        if attempt_id and attempt_id not in command_blob:
            errors.append(
                f"ready formal_attempt_queue attempt missing command: {attempt_id}"
            )
    for attempt_id in blocked_attempt_ids:
        if attempt_id and attempt_id in command_blob:
            errors.append(
                f"blocked formal_attempt_queue attempt appears in command: {attempt_id}"
            )
    next_kind = str(row.get("next_interaction_kind", "")).strip()
    if (
        ready_items
        and next_kind in {"proof_state_feedback", "target_prover_replay"}
        and not commands
    ):
        errors.append(
            "dependency-ready formal_attempt_queue items have no execution commands"
        )
    if next_kind not in {"proof_state_feedback", "target_prover_replay"} and commands:
        errors.append(
            "formal_attempt_queue execution commands emitted outside prover replay/feedback"
        )
    return tuple(errors)


def _formal_attempt_queue_item_ready(item: dict[str, Any]) -> bool:
    return (
        str(item.get("formal_attempt_dependency_status", "")).strip()
        == "ready_no_formal_prerequisites"
        or bool(item.get("formal_attempt_initial_ready", False))
    )


def _prover_classes_require_target_family(classes: tuple[str, ...]) -> bool:
    return any(
        attempt_class.startswith("target_prover_")
        or "target_prover" in attempt_class
        for attempt_class in classes
    )


def _generic_prover_class_legacy_errors(
    field_name: str,
    classes: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(
        f"{field_name} contains legacy local-Lean class {attempt_class}"
        for attempt_class in classes
        if "local_lean" in attempt_class
    )


def _generic_prover_triage_legacy_errors(
    field_name: str,
    triage_class: str,
) -> tuple[str, ...]:
    legacy = (
        "repair_local_lean_proof_state",
        "materialize_lean_command",
        "configure_local_lean_environment",
    )
    if triage_class in legacy or "local_lean" in triage_class:
        return (f"{field_name} contains legacy local-Lean triage {triage_class}",)
    return tuple()


def _schema_catalog_entry_paths_exist(
    bundle_dir: Path,
    entries: tuple[dict[str, Any], ...],
) -> bool:
    if not entries:
        return False
    try:
        bundle_root = bundle_dir.resolve()
    except Exception:
        return False
    for entry in entries:
        relative_path = str(entry.get("relative_path", ""))
        if not relative_path:
            return False
        entry_path = Path(relative_path)
        if entry_path.is_absolute():
            return False
        candidate = (bundle_dir / entry_path).resolve()
        try:
            candidate.relative_to(bundle_root)
        except ValueError:
            return False
        if not candidate.exists():
            return False
    return True


def _check(
    check_name: str,
    category: str,
    expected: str,
    observed: str,
    ok: bool,
    *,
    severity: str = "error",
    errors: tuple[str, ...] = (),
) -> FormalizationGapPlannerPublicationBundleAuditCheck:
    return FormalizationGapPlannerPublicationBundleAuditCheck(
        schema_version=FORMALIZATION_GAP_PLANNER_PUBLICATION_BUNDLE_AUDIT_SCHEMA_VERSION,
        check_id="formalization_gap_planner_publication_bundle_audit:"
        + stable_hash([check_name, category, expected])[:16],
        check_name=check_name,
        category=category,
        expected=expected,
        observed=observed,
        ok=ok,
        severity=severity,
        errors=errors if not ok else (),
    )


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON file: {path}")
        return {}
    except Exception as exc:
        errors.append(f"failed to parse {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_json_no_error(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_jsonl_dict_rows_no_error(path: Path) -> tuple[list[dict[str, Any]], tuple[str, ...]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        return [], (f"failed to read JSONL: {type(exc).__name__}: {exc}",)
    for lineno, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except Exception as exc:
            errors.append(f"line {lineno}: {type(exc).__name__}: {exc}")
            continue
        if isinstance(payload, dict):
            rows.append(payload)
        else:
            errors.append(f"line {lineno}: row is not an object")
    return rows, tuple(errors)


def _bundle_files(bundle_dir: Path) -> tuple[Path, ...]:
    if not bundle_dir.exists():
        return tuple()
    return tuple(sorted(path for path in bundle_dir.rglob("*") if path.is_file()))


def _is_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except Exception:
        return False
    return True


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(dict.fromkeys(str(item) for item in values if str(item)))


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float_or_none(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_mapping(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): int(item or 0)
        for key, item in sorted(value.items())
        if item is not None
    }


def _mean_float(values: Any) -> float:
    items = [float(value or 0.0) for value in values]
    if not items:
        return 0.0
    return sum(items) / len(items)


def _normalized_summary_dict(value: Any) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, object] = {}
    for key, item in sorted(value.items()):
        if isinstance(item, dict):
            normalized[str(key)] = _normalized_summary_dict(item)
        elif isinstance(item, bool):
            normalized[str(key)] = bool(item)
        elif isinstance(item, int):
            normalized[str(key)] = int(item)
        elif isinstance(item, float):
            normalized[str(key)] = float(item)
        elif isinstance(item, (list, tuple, set)):
            normalized[str(key)] = tuple(str(entry) for entry in item)
        else:
            normalized[str(key)] = item
    return normalized


def _dict_tuple(values: Any) -> tuple[dict[str, Any], ...]:
    if isinstance(values, dict):
        return (values,)
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(value for value in values if isinstance(value, dict))


def _candidate_declaration_rows(values: Any) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for item in _dict_tuple(values):
        declaration = str(
            item.get("declaration")
            or item.get("declaration_name")
            or item.get("lean_declaration")
            or ""
        ).strip()
        if not declaration:
            continue
        target = str(
            item.get("target_prover_family", "") or item.get("target_prover", "")
        ).strip()
        key = (_declaration_key(declaration), _target_prover_key(target))
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "declaration": declaration,
                "target_prover_family": target,
                "source_field": str(
                    item.get("source_field", "") or "candidate_declaration_rows"
                ).strip(),
            }
        )
    return tuple(rows)


def _declaration_key(value: object) -> str:
    return re.sub(r"\s+", " ", str(value).strip()).lower()


def _target_prover_key(value: object) -> str:
    key = str(value).strip().lower().replace("-", "_")
    aliases = {
        "coq": "rocq",
        "coq8": "rocq",
        "lean": "lean4",
        "lean_4": "lean4",
        "isabelle_hol": "isabelle",
    }
    return aliases.get(key, key)


def _dict_value(row: dict[str, Any], key: str) -> dict[str, Any]:
    value = row.get(key, {})
    return value if isinstance(value, dict) else {}


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Publication Bundle Audit",
        "",
        f"- Bundle: `{payload.get('bundle_id')}`",
        f"- Checks: {payload.get('n_ok')}/{payload.get('n_checks')}",
        f"- Failed: {payload.get('n_failed')}",
        f"- Component-resource component schema valid: {payload.get('n_component_resource_component_row_schema_valid')}/{payload.get('n_component_resource_component_row_schema_checked')}",
        f"- Component-resource resource schema valid: {payload.get('n_component_resource_resource_row_schema_valid')}/{payload.get('n_component_resource_resource_row_schema_checked')}",
        f"- Component-resource contract schema valid: {payload.get('n_component_resource_contract_row_schema_valid')}/{payload.get('n_component_resource_contract_row_schema_checked')}",
        f"- Component execution-plan schema valid: {payload.get('n_component_execution_plan_schema_valid')}/{payload.get('n_component_execution_plan_schema_checked')}",
        f"- Benchmark route-row schema valid: {payload.get('n_benchmark_route_row_schema_valid')}/{payload.get('n_benchmark_route_row_schema_checked')}",
        f"- Optional evaluation-row schema valid: {payload.get('n_optional_evaluation_row_schema_valid')}/{payload.get('n_optional_evaluation_row_schema_checked')}",
        f"- Optional evaluation realization-missing rows valid: {payload.get('n_optional_evaluation_realization_missing_row_valid')}/{payload.get('n_optional_evaluation_realization_missing_row_checked')}",
        f"- Optional evaluation realization-missing manifest valid: {payload.get('n_optional_evaluation_realization_missing_manifest_valid')}/{payload.get('n_optional_evaluation_realization_missing_manifest_checked')}",
        f"- Optional evaluation route-adoption manifest valid: {payload.get('n_optional_evaluation_route_adoption_manifest_valid')}/{payload.get('n_optional_evaluation_route_adoption_manifest_checked')}",
        f"- Optional evaluation route-option selection manifest valid: {payload.get('n_optional_evaluation_route_option_selection_manifest_valid')}/{payload.get('n_optional_evaluation_route_option_selection_manifest_checked')}",
        f"- Optional evaluation quality-control rows valid: {payload.get('n_optional_evaluation_quality_control_row_valid')}/{payload.get('n_optional_evaluation_quality_control_row_checked')}",
        f"- Optional evaluation quality-control manifest valid: {payload.get('n_optional_evaluation_quality_control_manifest_valid')}/{payload.get('n_optional_evaluation_quality_control_manifest_checked')}",
        f"- Optional evaluation residual-goal context manifest valid: {payload.get('n_optional_evaluation_residual_goal_context_manifest_valid')}/{payload.get('n_optional_evaluation_residual_goal_context_manifest_checked')}",
        f"- Bundle LLM route-planner summary valid: {payload.get('n_bundle_llm_route_planner_summary_valid')}/{payload.get('n_bundle_llm_route_planner_summary_checked')}",
        f"- Bundle feedback LLM route-planner summary valid: {payload.get('n_bundle_feedback_llm_route_planner_summary_valid')}/{payload.get('n_bundle_feedback_llm_route_planner_summary_checked')}",
        (
            "- Optional evaluation route-adoption ready/pending/blockers: "
            f"{payload.get('n_optional_evaluation_rows_ready_for_route_adoption')}/"
            f"{payload.get('n_optional_evaluation_rows_pending_refinement_before_route_adoption')}/"
            f"{payload.get('n_optional_evaluation_route_adoption_blockers')}"
        ),
        (
            "- Optional evaluation route-option selection "
            "rows/options/primitives/residual-options/residual-goals/"
            "lower-bound-residuals/selected-residuals/matches/mismatches: "
            f"{payload.get('n_optional_evaluation_rows_with_route_option_selection_brief')}/"
            f"{payload.get('n_optional_evaluation_route_option_selection_candidate_options')}/"
            f"{payload.get('n_optional_evaluation_route_option_selection_candidate_primitives')}/"
            f"{payload.get('n_optional_evaluation_route_option_selection_candidates_with_residual_goals')}/"
            f"{payload.get('n_optional_evaluation_route_option_selection_candidate_residual_goals')}/"
            f"{payload.get('n_optional_evaluation_route_option_selection_lower_bound_residual_goals')}/"
            f"{payload.get('n_optional_evaluation_route_option_selection_minimal_delta_selected_residual_goals')}/"
            f"{payload.get('n_optional_evaluation_route_option_selection_lower_bound_matches_minimal_delta')}/"
            f"{payload.get('n_optional_evaluation_route_option_selection_lower_bound_mismatches_minimal_delta')}/"
            f"{payload.get('n_optional_evaluation_rows_with_route_option_selected_route_option')}/"
            f"{payload.get('n_optional_evaluation_route_option_selected_matches_lower_bound')}/"
            f"{payload.get('n_optional_evaluation_route_option_selected_matches_minimal_delta')}"
        ),
        (
            "- Optional evaluation quality controls: "
            f"rows={payload.get('n_optional_evaluation_rows_with_quality_controls')} "
            f"fields={payload.get('optional_evaluation_quality_control_fields')}"
        ),
        (
            "- Optional evaluation missing realization primitives: "
            f"selected={payload.get('optional_evaluation_realization_missing_selected_formal_primitives')} "
            f"delta={payload.get('optional_evaluation_realization_missing_delta_alignment_primitives')}"
        ),
        (
            "- Optional evaluation omitted cost-hint primitives: "
            f"baseline={payload.get('optional_evaluation_realization_cost_hint_baseline_primitives')} "
            f"omitted={payload.get('optional_evaluation_realization_omitted_cost_hint_primitives')} "
            f"incomplete_rows={payload.get('n_optional_evaluation_rows_with_incomplete_cost_hint_baseline_coverage')}"
        ),
        f"- Optional LLM route-planner requests valid: {payload.get('n_optional_llm_route_planner_request_schema_valid')}/{payload.get('n_optional_llm_route_planner_request_schema_checked')}",
        f"- Optional LLM route-planner rows valid: {payload.get('n_optional_llm_route_planner_row_schema_valid')}/{payload.get('n_optional_llm_route_planner_row_schema_checked')}",
        f"- Optional LLM route-planner seed provenance preserved: {payload.get('n_optional_llm_route_planner_seed_provenance_valid')}/{payload.get('n_optional_llm_route_planner_seed_provenance_checked')}",
        f"- Optional LLM route-planner seed source-grounding provenance preserved: {payload.get('n_optional_llm_route_planner_seed_source_grounding_provenance_valid')}/{payload.get('n_optional_llm_route_planner_seed_source_grounding_provenance_checked')}",
        f"- Optional LLM route-planner seed realization witness preserved: {payload.get('n_optional_llm_route_planner_seed_realization_witness_valid')}/{payload.get('n_optional_llm_route_planner_seed_realization_witness_checked')}",
        f"- Optional LLM route-planner seed alignment preserved: {payload.get('n_optional_llm_route_planner_seed_alignment_valid')}/{payload.get('n_optional_llm_route_planner_seed_alignment_checked')}",
        f"- Optional LLM route-planner seed DAG preserved: {payload.get('n_optional_llm_route_planner_seed_dag_valid')}/{payload.get('n_optional_llm_route_planner_seed_dag_checked')}",
        f"- Optional LLM route-planner seed search handoff preserved: {payload.get('n_optional_llm_route_planner_seed_search_handoff_valid')}/{payload.get('n_optional_llm_route_planner_seed_search_handoff_checked')}",
        f"- Optional LLM route-planner seed route-adoption readiness preserved: {payload.get('n_optional_llm_route_planner_seed_route_adoption_readiness_valid')}/{payload.get('n_optional_llm_route_planner_seed_route_adoption_readiness_checked')}",
        f"- Optional LLM route-planner seed route-selection schema valid: {payload.get('n_optional_llm_route_planner_seed_route_selection_schema_valid')}/{payload.get('n_optional_llm_route_planner_seed_route_selection_schema_checked')}",
        f"- Optional LLM route-planner seed route-selection contract valid: {payload.get('n_optional_llm_route_planner_seed_route_selection_contract_valid')}/{payload.get('n_optional_llm_route_planner_seed_route_selection_contract_checked')}",
        f"- Optional LLM route-planner seed route-selection summary valid: {payload.get('n_optional_llm_route_planner_seed_route_selection_summary_valid')}/{payload.get('n_optional_llm_route_planner_seed_route_selection_summary_checked')}",
        f"- Optional LLM route-planner seed route-selection candidates/adoptable/selected-adoptable/selected-not-adoptable: {payload.get('n_optional_llm_route_planner_seed_route_selection_candidates')}/{payload.get('n_optional_llm_route_planner_seed_route_selection_adoptable_candidates')}/{payload.get('n_optional_llm_route_planner_seed_route_selection_selected_adoptable')}/{payload.get('n_optional_llm_route_planner_seed_route_selection_selected_not_adoptable')}",
        f"- Optional LLM route-planner seed route-selection traces preserved: {payload.get('n_optional_llm_route_planner_seed_route_selection_valid')}/{payload.get('n_optional_llm_route_planner_seed_route_selection_checked')}",
        f"- Optional LLM route-planner request evidence bounds valid: {payload.get('n_optional_llm_route_planner_request_evidence_bound_valid')}/{payload.get('n_optional_llm_route_planner_request_evidence_bound_checked')}",
        f"- Optional LLM route-planner request registry context valid: {payload.get('n_optional_llm_route_planner_request_registry_context_valid')}/{payload.get('n_optional_llm_route_planner_request_registry_context_checked')}",
        f"- Optional LLM route-planner request target-intake context valid: {payload.get('n_optional_llm_route_planner_request_target_intake_context_valid')}/{payload.get('n_optional_llm_route_planner_request_target_intake_context_checked')}",
        f"- Optional LLM route-planner request generation policy valid: {payload.get('n_optional_llm_route_planner_request_generation_policy_valid')}/{payload.get('n_optional_llm_route_planner_request_generation_policy_checked')}",
        f"- Optional LLM route-planner request model-tier mismatch policy valid: {payload.get('n_optional_llm_route_planner_request_model_tier_mismatch_valid')}/{payload.get('n_optional_llm_route_planner_request_model_tier_mismatch_checked')}",
        f"- Optional LLM route-planner generation preflight policy valid: {payload.get('n_optional_llm_route_planner_generation_preflight_valid')}/{payload.get('n_optional_llm_route_planner_generation_preflight_checked')}",
        f"- Optional LLM route-planner blocker summary valid: {payload.get('n_optional_llm_route_planner_route_adoption_blocker_summary_valid')}/{payload.get('n_optional_llm_route_planner_route_adoption_blocker_summary_checked')}",
        f"- Optional feedback LLM route-planner requests valid: {payload.get('n_optional_feedback_llm_route_planner_request_schema_valid')}/{payload.get('n_optional_feedback_llm_route_planner_request_schema_checked')}",
        f"- Optional feedback LLM route-planner rows valid: {payload.get('n_optional_feedback_llm_route_planner_row_schema_valid')}/{payload.get('n_optional_feedback_llm_route_planner_row_schema_checked')}",
        f"- Optional feedback LLM route-planner seed provenance preserved: {payload.get('n_optional_feedback_llm_route_planner_seed_provenance_valid')}/{payload.get('n_optional_feedback_llm_route_planner_seed_provenance_checked')}",
        f"- Optional feedback LLM route-planner seed source-grounding provenance preserved: {payload.get('n_optional_feedback_llm_route_planner_seed_source_grounding_provenance_valid')}/{payload.get('n_optional_feedback_llm_route_planner_seed_source_grounding_provenance_checked')}",
        f"- Optional feedback LLM route-planner seed realization witness preserved: {payload.get('n_optional_feedback_llm_route_planner_seed_realization_witness_valid')}/{payload.get('n_optional_feedback_llm_route_planner_seed_realization_witness_checked')}",
        f"- Optional feedback LLM route-planner seed alignment preserved: {payload.get('n_optional_feedback_llm_route_planner_seed_alignment_valid')}/{payload.get('n_optional_feedback_llm_route_planner_seed_alignment_checked')}",
        f"- Optional feedback LLM route-planner seed DAG preserved: {payload.get('n_optional_feedback_llm_route_planner_seed_dag_valid')}/{payload.get('n_optional_feedback_llm_route_planner_seed_dag_checked')}",
        f"- Optional feedback LLM route-planner seed search handoff preserved: {payload.get('n_optional_feedback_llm_route_planner_seed_search_handoff_valid')}/{payload.get('n_optional_feedback_llm_route_planner_seed_search_handoff_checked')}",
        f"- Optional feedback LLM route-planner seed route-adoption readiness preserved: {payload.get('n_optional_feedback_llm_route_planner_seed_route_adoption_readiness_valid')}/{payload.get('n_optional_feedback_llm_route_planner_seed_route_adoption_readiness_checked')}",
        f"- Optional feedback LLM route-planner seed route-selection schema valid: {payload.get('n_optional_feedback_llm_route_planner_seed_route_selection_schema_valid')}/{payload.get('n_optional_feedback_llm_route_planner_seed_route_selection_schema_checked')}",
        f"- Optional feedback LLM route-planner seed route-selection contract valid: {payload.get('n_optional_feedback_llm_route_planner_seed_route_selection_contract_valid')}/{payload.get('n_optional_feedback_llm_route_planner_seed_route_selection_contract_checked')}",
        f"- Optional feedback LLM route-planner seed route-selection summary valid: {payload.get('n_optional_feedback_llm_route_planner_seed_route_selection_summary_valid')}/{payload.get('n_optional_feedback_llm_route_planner_seed_route_selection_summary_checked')}",
        f"- Optional feedback LLM route-planner seed route-selection candidates/adoptable/selected-adoptable/selected-not-adoptable: {payload.get('n_optional_feedback_llm_route_planner_seed_route_selection_candidates')}/{payload.get('n_optional_feedback_llm_route_planner_seed_route_selection_adoptable_candidates')}/{payload.get('n_optional_feedback_llm_route_planner_seed_route_selection_selected_adoptable')}/{payload.get('n_optional_feedback_llm_route_planner_seed_route_selection_selected_not_adoptable')}",
        f"- Optional feedback LLM route-planner seed route-selection traces preserved: {payload.get('n_optional_feedback_llm_route_planner_seed_route_selection_valid')}/{payload.get('n_optional_feedback_llm_route_planner_seed_route_selection_checked')}",
        f"- Optional feedback LLM route-planner request evidence bounds valid: {payload.get('n_optional_feedback_llm_route_planner_request_evidence_bound_valid')}/{payload.get('n_optional_feedback_llm_route_planner_request_evidence_bound_checked')}",
        f"- Optional feedback LLM route-planner request registry context valid: {payload.get('n_optional_feedback_llm_route_planner_request_registry_context_valid')}/{payload.get('n_optional_feedback_llm_route_planner_request_registry_context_checked')}",
        f"- Optional feedback LLM route-planner request target-intake context valid: {payload.get('n_optional_feedback_llm_route_planner_request_target_intake_context_valid')}/{payload.get('n_optional_feedback_llm_route_planner_request_target_intake_context_checked')}",
        f"- Optional feedback LLM route-planner request generation policy valid: {payload.get('n_optional_feedback_llm_route_planner_request_generation_policy_valid')}/{payload.get('n_optional_feedback_llm_route_planner_request_generation_policy_checked')}",
        f"- Optional feedback LLM route-planner request model-tier mismatch policy valid: {payload.get('n_optional_feedback_llm_route_planner_request_model_tier_mismatch_valid')}/{payload.get('n_optional_feedback_llm_route_planner_request_model_tier_mismatch_checked')}",
        f"- Optional feedback LLM route-planner generation preflight policy valid: {payload.get('n_optional_feedback_llm_route_planner_generation_preflight_valid')}/{payload.get('n_optional_feedback_llm_route_planner_generation_preflight_checked')}",
        f"- Optional feedback LLM route-planner blocker summary valid: {payload.get('n_optional_feedback_llm_route_planner_route_adoption_blocker_summary_valid')}/{payload.get('n_optional_feedback_llm_route_planner_route_adoption_blocker_summary_checked')}",
        f"- Optional interactive-session schema valid: {payload.get('n_optional_interactive_session_row_schema_valid')}/{payload.get('n_optional_interactive_session_row_schema_checked')}",
        f"- Optional interactive-session resource-response status consistent: {payload.get('n_optional_interactive_session_resource_response_status_valid')}/{payload.get('n_optional_interactive_session_resource_response_status_checked')}",
        f"- Optional interactive-session route-precondition status consistent: {payload.get('n_optional_interactive_session_route_precondition_valid')}/{payload.get('n_optional_interactive_session_route_precondition_checked')}",
        f"- Optional interactive-session generic prover fields valid: {payload.get('n_optional_interactive_session_generic_prover_fields_valid')}/{payload.get('n_optional_interactive_session_generic_prover_fields_checked')}",
        f"- Optional interactive-session formal-attempt queue valid: {payload.get('n_optional_interactive_session_formal_attempt_queue_valid')}/{payload.get('n_optional_interactive_session_formal_attempt_queue_checked')}",
        f"- Optional interactive decision-policy schema valid: {payload.get('n_optional_interactive_decision_policy_row_schema_valid')}/{payload.get('n_optional_interactive_decision_policy_row_schema_checked')}",
        f"- Optional refinement-evidence schema valid: {payload.get('n_optional_refinement_evidence_row_schema_valid')}/{payload.get('n_optional_refinement_evidence_row_schema_checked')}",
        f"- Optional refinement-adapter response schema valid: {payload.get('n_optional_refinement_adapter_response_schema_valid')}/{payload.get('n_optional_refinement_adapter_response_schema_checked')}",
        f"- Optional local-adapter response schema valid: {payload.get('n_optional_local_adapter_response_schema_valid')}/{payload.get('n_optional_local_adapter_response_schema_checked')}",
        f"- Optional route-stability schema valid: {payload.get('n_optional_route_stability_audit_row_schema_valid')}/{payload.get('n_optional_route_stability_audit_row_schema_checked')}",
        f"- Optional route-stability resource-response status consistent: {payload.get('n_optional_route_stability_resource_response_status_valid')}/{payload.get('n_optional_route_stability_resource_response_status_checked')}",
        f"- Optional route-stability generic prover fields valid: {payload.get('n_optional_route_stability_generic_prover_fields_valid')}/{payload.get('n_optional_route_stability_generic_prover_fields_checked')}",
        f"- Optional route-revision resource-response evidence refs valid: {payload.get('n_optional_route_revision_resource_response_evidence_ref_valid')}/{payload.get('n_optional_route_revision_resource_response_evidence_ref_checked')}",
        f"- Optional route-revision resource-response traces valid: {payload.get('n_optional_route_revision_resource_response_trace_valid')}/{payload.get('n_optional_route_revision_resource_response_trace_checked')}",
        f"- Optional route-revision resource-response status summaries valid: {payload.get('n_optional_route_revision_resource_response_status_valid')}/{payload.get('n_optional_route_revision_resource_response_status_checked')}",
        f"- Optional route-revision generic formal DAG valid: {payload.get('n_optional_route_revision_generic_formal_dag_valid')}/{payload.get('n_optional_route_revision_generic_formal_dag_checked')}",
        f"- Optional route-replan handoff seed alignment preserved: {payload.get('n_optional_route_replan_handoff_seed_alignment_valid')}/{payload.get('n_optional_route_replan_handoff_seed_alignment_checked')}",
        f"- Optional route-replan handoff seed DAG preserved: {payload.get('n_optional_route_replan_handoff_seed_dag_valid')}/{payload.get('n_optional_route_replan_handoff_seed_dag_checked')}",
        f"- Optional route-replan handoff target context preserved: {payload.get('n_optional_route_replan_handoff_seed_target_context_valid')}/{payload.get('n_optional_route_replan_handoff_seed_target_context_checked')}",
        f"- Optional route-replan handoff target context summary preserved: {payload.get('n_optional_route_replan_handoff_seed_target_context_summary_valid')}/{payload.get('n_optional_route_replan_handoff_seed_target_context_summary_checked')}",
        f"- Optional route-replan handoff route-planning brief preserved: {payload.get('n_optional_route_replan_handoff_seed_route_planning_brief_valid')}/{payload.get('n_optional_route_replan_handoff_seed_route_planning_brief_checked')}",
        f"- Optional route-replan handoff route-option selection brief preserved: {payload.get('n_optional_route_replan_handoff_seed_route_option_selection_brief_valid')}/{payload.get('n_optional_route_replan_handoff_seed_route_option_selection_brief_checked')}",
        f"- Optional route-replan handoff primitive-evidence matrix witness preserved: {payload.get('n_optional_route_replan_handoff_seed_primitive_evidence_matrix_witness_valid')}/{payload.get('n_optional_route_replan_handoff_seed_primitive_evidence_matrix_witness_checked')}",
        f"- Optional route-replan handoff route-adoption preconditions preserved: {payload.get('n_optional_route_replan_handoff_seed_route_adoption_preconditions_valid')}/{payload.get('n_optional_route_replan_handoff_seed_route_adoption_preconditions_checked')}",
        f"- Optional route-replan handoff generic formal DAG valid: {payload.get('n_optional_route_replan_handoff_generic_formal_dag_valid')}/{payload.get('n_optional_route_replan_handoff_generic_formal_dag_checked')}",
        f"- Optional route-replan handoff-audit schema valid: {payload.get('n_optional_route_replan_handoff_audit_row_schema_valid')}/{payload.get('n_optional_route_replan_handoff_audit_row_schema_checked')}",
        f"- Optional route-replan handoff-audit route-planning brief trace valid: {payload.get('n_optional_route_replan_handoff_audit_roundtrip_route_planning_brief_valid')}/{payload.get('n_optional_route_replan_handoff_audit_roundtrip_route_planning_brief_checked')}",
        f"- Optional route-replan handoff-audit route-option selection brief trace valid: {payload.get('n_optional_route_replan_handoff_audit_roundtrip_route_option_selection_brief_valid')}/{payload.get('n_optional_route_replan_handoff_audit_roundtrip_route_option_selection_brief_checked')}",
        f"- Optional route-replan handoff-audit primitive-evidence matrix witness trace valid: {payload.get('n_optional_route_replan_handoff_audit_roundtrip_primitive_evidence_matrix_witness_valid')}/{payload.get('n_optional_route_replan_handoff_audit_roundtrip_primitive_evidence_matrix_witness_checked')}",
        f"- Optional route-replan handoff-audit route-adoption precondition trace valid: {payload.get('n_optional_route_replan_handoff_audit_roundtrip_route_adoption_preconditions_valid')}/{payload.get('n_optional_route_replan_handoff_audit_roundtrip_route_adoption_preconditions_checked')}",
        f"- Optional route-replan handoff-audit target-context-summary trace valid: {payload.get('n_optional_route_replan_handoff_audit_roundtrip_target_context_summary_valid')}/{payload.get('n_optional_route_replan_handoff_audit_roundtrip_target_context_summary_checked')}",
        f"- Optional runtime handoff-audit schema valid: {payload.get('n_optional_runtime_handoff_audit_row_schema_valid')}/{payload.get('n_optional_runtime_handoff_audit_row_schema_checked')}",
        f"- Optional runtime handoff-audit cost controls valid: {payload.get('n_optional_runtime_handoff_audit_cost_control_valid')}/{payload.get('n_optional_runtime_handoff_audit_cost_control_checked')}",
        f"- Optional ablation-study schema valid: {payload.get('n_optional_ablation_study_row_schema_valid')}/{payload.get('n_optional_ablation_study_row_schema_checked')}",
        f"- Optional ablation-study route-adoption manifest valid: {payload.get('n_optional_ablation_study_route_adoption_manifest_valid')}/{payload.get('n_optional_ablation_study_route_adoption_manifest_checked')}",
        (
            "- Optional ablation-study largest route-adoption-ready drop: "
            f"`{payload.get('optional_ablation_study_largest_route_adoption_ready_drop_variant')}`"
        ),
        f"- Optional portable-plan audit schema valid: {payload.get('n_optional_portable_plan_audit_row_schema_valid')}/{payload.get('n_optional_portable_plan_audit_row_schema_checked')}",
        f"- Optional library-coverage map schema valid: {payload.get('n_optional_library_coverage_map_row_schema_valid')}/{payload.get('n_optional_library_coverage_map_row_schema_checked')}",
        f"- Optional primitive action-queue schema valid: {payload.get('n_optional_primitive_action_queue_row_schema_valid')}/{payload.get('n_optional_primitive_action_queue_row_schema_checked')}",
        f"- Optional action-resource plan schema valid: {payload.get('n_optional_action_resource_plan_row_schema_valid')}/{payload.get('n_optional_action_resource_plan_row_schema_checked')}",
        f"- Optional resource request-queue schema valid: {payload.get('n_optional_resource_request_queue_row_schema_valid')}/{payload.get('n_optional_resource_request_queue_row_schema_checked')}",
        f"- Optional resource request action-plan refs valid: {payload.get('n_optional_resource_request_action_plan_ref_valid')}/{payload.get('n_optional_resource_request_action_plan_ref_checked')}",
        f"- Optional resource request payload identity valid: {payload.get('n_optional_resource_request_payload_identity_valid')}/{payload.get('n_optional_resource_request_payload_identity_checked')}",
        f"- Optional resource request dispatch specs valid: {payload.get('n_optional_resource_request_dispatch_spec_valid')}/{payload.get('n_optional_resource_request_dispatch_spec_checked')}",
        f"- Optional resource request contract alignment valid: {payload.get('n_optional_resource_request_contract_alignment_valid')}/{payload.get('n_optional_resource_request_contract_alignment_checked')}",
        f"- Optional resource response-ledger schema valid: {payload.get('n_optional_resource_response_ledger_row_schema_valid')}/{payload.get('n_optional_resource_response_ledger_row_schema_checked')}",
        f"- Optional resource response request refs valid: {payload.get('n_optional_resource_response_request_ref_valid')}/{payload.get('n_optional_resource_response_request_ref_checked')}",
        f"- Optional resource response contract accounting valid: {payload.get('n_optional_resource_response_contract_field_accounting_valid')}/{payload.get('n_optional_resource_response_contract_field_accounting_checked')}",
        f"- Optional proof-state triage schema valid: {payload.get('n_optional_proof_state_triage_row_schema_valid')}/{payload.get('n_optional_proof_state_triage_row_schema_checked')}",
        f"- Optional proof-state triage generic prover fields valid: {payload.get('n_optional_proof_state_triage_generic_prover_fields_valid')}/{payload.get('n_optional_proof_state_triage_generic_prover_fields_checked')}",
        f"- Prover-adapter packet schema valid: {payload.get('n_prover_adapter_packet_schema_valid')}/{payload.get('n_prover_adapter_packet_schema_checked')}",
        f"- Prover-adapter response-validation schema valid: {payload.get('n_prover_adapter_response_validation_row_schema_valid')}/{payload.get('n_prover_adapter_response_validation_row_schema_checked')}",
        f"- Optional cross-prover matrix schema valid: {payload.get('n_optional_cross_prover_matrix_row_schema_valid')}/{payload.get('n_optional_cross_prover_matrix_row_schema_checked')}",
        f"- Optional cross-prover packet schema valid: {payload.get('n_optional_cross_prover_packet_row_schema_valid')}/{payload.get('n_optional_cross_prover_packet_row_schema_checked')}",
        f"- Optional cross-prover packet trace valid: {payload.get('n_optional_cross_prover_packet_trace_valid')}/{payload.get('n_optional_cross_prover_packet_trace_checked')}",
        f"- Optional cross-prover response-validation schema valid: {payload.get('n_optional_cross_prover_response_validation_row_schema_valid')}/{payload.get('n_optional_cross_prover_response_validation_row_schema_checked')}",
        f"- Optional cross-prover formal-attempt dependency valid: {payload.get('n_optional_cross_prover_formal_attempt_dependency_valid')}/{payload.get('n_optional_cross_prover_formal_attempt_dependency_checked')}",
        f"- Bundle files: {payload.get('n_bundle_files')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Failed Checks",
        "",
    ]
    failed = [
        check
        for check in payload.get("checks", [])
        if isinstance(check, dict) and not check.get("ok")
    ]
    if not failed:
        lines.append("- None")
    for check in failed:
        lines.append(
            f"- `{check.get('check_name')}` expected={check.get('expected')} "
            f"observed={check.get('observed')}"
        )
    return "\n".join(lines) + "\n"
