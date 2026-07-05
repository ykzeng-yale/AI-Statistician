from __future__ import annotations

import json
import sys
from pathlib import Path

from ai_statistician.cli import main
from ai_statistician.model_backend import GeneratorResponse, StaticJSONGeneratorBackend
from ai_statistician.source_theorem_exact_semantic_definition_authoring_worker import (
    AuthoringCandidateMaterializerConfig,
    AuthoringWorkerConfig,
    CANDIDATE_PROOF_EVIDENCE_STATUS,
    AUTHORING_WORKER_PROOF_EVIDENCE_STATUS,
    MATERIALIZER_PROOF_EVIDENCE_STATUS,
    STRUCTURAL_REFORMULATION_FAILURE_CLASSIFICATION,
    STRUCTURAL_REFORMULATION_QUEUE_STATUS,
    run_source_theorem_exact_semantic_definition_authoring_candidate_materializer,
    run_source_theorem_exact_semantic_definition_authoring_worker,
    validate_authoring_candidate_packet,
)
from ai_statistician.source_theorem_exact_semantic_definition_lean_repair_executor import (
    run_source_theorem_exact_semantic_definition_lean_repair_executor,
)


class _ExplodingExternalProvider:
    provider_name = "anthropic"

    def generate(self, request):  # pragma: no cover - must not be called
        raise AssertionError("external provider should not be called without approval")


class _StaticExternalProvider:
    provider_name = "anthropic"

    def __init__(self, response: dict) -> None:
        self.response = response
        self.calls = 0

    def generate(self, request):
        self.calls += 1
        return GeneratorResponse(
            text=json.dumps(self.response, sort_keys=True),
            provider=self.provider_name,
            model=request.model,
            metadata={"generator_only": True, "tools_available": False},
        )


class _ConnectionFailingProvider:
    provider_name = "anthropic"

    def generate(self, request):
        raise ConnectionError("Connection error.")


def _valid_authoring_response() -> dict:
    return {
        "placeholder_symbol": "covered",
        "definition_design": (
            "Coverage is represented as the held-out score event below q_hat."
        ),
        "lean_definition_candidate": (
            "def reviewedCovered (s : Fin (n2 + 1) → Ω → ℝ) "
            "(q_hat : Ω → ℝ) : Set Ω := {ω | s (Fin.last n2) ω ≤ q_hat ω}"
        ),
        "required_imports": ["Mathlib"],
        "binder_usage": [
            {"name": "s", "how_used": "score process"},
            {"name": "q_hat", "how_used": "threshold"},
        ],
        "semantic_alignment_notes": [
            "Uses the same event shape as the source theorem goal."
        ],
        "known_gaps": ["types Ω and n2 must be supplied by the candidate file"],
        "forbidden_shortcuts_absent": True,
        "requires_local_lean_check": True,
    }


def _write_authoring_tasks(path: Path) -> None:
    task = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionAuthoringTask",
        "authoring_task_id": "authoring:covered",
        "source_execution_result_id": "execution:covered",
        "source_lean_repair_task_id": "lean-repair:covered",
        "question_id": "conformal_prediction_coverage",
        "question_title": "Split conformal prediction interval coverage",
        "target_theorem_name": "split_conformal_coverage",
        "placeholder_symbol": "covered",
        "semantic_primitive": "covered",
        "semantic_primitive_requirements": ["covered"],
        "source_anchors": [
            {
                "kind": "pseudo_formal_block",
                "id": "pf:block:covered",
                "excerpt": "coverage event is grounded by q_hat and hC",
            }
        ],
        "source_pseudo_formal_work_order_id": "pseudo_formal_work_order:covered",
        "source_pseudo_formal_block_id": "pf:block:covered",
        "source_pseudo_formal_packet_id": "pseudo_formal_packet:coverage",
        "source_formalizer_proposal_id": "formalizer_proposal:pf_exact",
        "pseudo_formal_method_contract_id": (
            "pseudo_formalization_block_verification_calibration_v1"
        ),
        "pseudo_formal_pipeline_stage": "pseudo_formal_block_routing",
        "pseudo_formal_proof_evidence_status": (
            "PSEUDO_FORMAL_VERIFICATION_NOT_PROOF_EVIDENCE"
        ),
        "source_execution_status": (
            "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED"
        ),
        "authoring_trigger": (
            "EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR_REQUIRED"
        ),
        "authoring_mode": "repair_typechecked_semantic_definition_candidate",
        "lean_repair_action": "synthesize_exact_definition",
        "repair_strategy": "synthesize_reviewed_definition_from_source_references",
        "definition_only_candidate_artifact_path": "/tmp/candidate_defs_only.lean",
        "candidate_artifact_path": "/tmp/candidate_full.lean",
        "candidate_lean_project_hint": "/tmp/lean_project",
        "local_definition_lean_checked": True,
        "local_definition_lean_compiled": False,
        "local_lean_checked": True,
        "local_lean_compiled": False,
        "local_lean_returncode": 1,
        "local_lean_diagnostics": [
            "application type mismatch",
            "Unknown constant Nat.ceil",
            (
                "object file ./lake/.lake/packages/mathlib/.lake/build/lib/lean/"
                "Mathlib/Data/Int/Order.olean of module "
                "Mathlib.Data.Int.Order does not exist"
            ),
        ],
        "failure_classification": "local_lean_failed_unclassified",
        "recommended_next_action": "repair the definition-only candidate Lean errors",
        "source_definition_closure_work_order_id": (
            "source_theorem_exact_semantic_definition_closure_work_order:covered"
        ),
        "source_reference_hints": [
            {
                "path": "StatInference/Conformal/Split.lean",
                "line": 44,
                "snippet": "coverage event is the held-out score under q_hat",
            }
        ],
        "exact_source_theorem_binders": [
            {
                "name": "s",
                "role": "score_process_anchor",
                "type": "Fin (n2 + 1) → Ω → ℝ",
            },
            {"name": "q_hat", "role": "threshold_function_anchor", "type": "Ω → ℝ"},
            {
                "name": "C",
                "role": "prediction_set_family_anchor",
                "type": "(Ω → ℝ) → Set ℝ",
            },
            {"name": "hC", "role": "coverage_event_anchor", "type": "∀ ω, C ..."},
        ],
        "premise_semantic_anchor_binder_names": ["s", "q_hat", "C", "hC"],
        "source_to_bridge_adapter_instantiation_group_id": (
            "source_to_bridge_adapter_instantiation_group:covered"
        ),
        "source_to_bridge_grouped_premise_derivation_candidate_request_id": (
            "source_to_bridge_grouped_premise_derivation_candidate_request:covered"
        ),
        "source_to_bridge_adapter_object_names_requiring_source_instantiation": [
            "covered",
            "rank",
        ],
        "semantic_alignment_constraints": [
            "adapter object 'covered' must be defined from exact source theorem binders"
        ],
        "semantic_alignment_blockers": [
            "previous covered candidate ignored q_hat and hC"
        ],
        "candidate_definition_request": {
            "schema_version": 1,
            "request_kind": "source_theorem_exact_semantic_definition_candidate",
            "target_theorem_name": "split_conformal_coverage",
            "placeholder_symbol": "covered",
            "semantic_goal": (
                "Define the source coverage event/object from hC and q_hat."
            ),
            "required_anchor_names": ["s", "q_hat", "C", "hC"],
            "available_anchor_names": ["s", "q_hat", "C", "hC"],
            "missing_required_anchor_names": [],
            "forbidden_shortcuts": [
                "do not define the placeholder as True",
                "do not add axiom/sorry/admit/unsafe",
            ],
            "proof_evidence_status": (
                "EXACT_SEMANTIC_DEFINITION_AUTHORING_TASK_NOT_PROOF_EVIDENCE"
            ),
        },
        "runtime_queue_status": "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING",
        "source_theorem_kernel_verified": False,
        "semantic_definition_kernel_verified": False,
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_AUTHORING_TASK_NOT_PROOF_EVIDENCE"
        ),
    }
    path.write_text(json.dumps(task, sort_keys=True) + "\n", encoding="utf-8")


def test_authoring_worker_dry_run_writes_prompt_packets_without_proof_evidence(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "authoring_tasks.jsonl"
    _write_authoring_tasks(tasks_path)

    manifest = run_source_theorem_exact_semantic_definition_authoring_worker(
        out_dir=tmp_path / "authoring_worker",
        authoring_tasks_jsonl=tasks_path,
        config=AuthoringWorkerConfig(provider_name="none", dry_run=True),
    )

    assert manifest["n_authoring_tasks"] == 1
    assert manifest["n_prompt_packets"] == 1
    assert manifest["n_llm_attempted"] == 0
    assert manifest["n_candidate_packets"] == 0
    assert manifest["placeholder_symbols"] == ["covered"]
    assert manifest["lean_repair_action_counts"] == {
        "synthesize_exact_definition": 1
    }
    assert manifest["repair_strategy_counts"] == {
        "synthesize_reviewed_definition_from_source_references": 1
    }
    assert manifest["n_external_llm_export_review_packets"] == 0
    assert manifest["n_external_export_blocked_tasks"] == 0
    assert manifest["n_local_lean_checked"] == 0
    assert manifest["source_theorem_kernel_verified"] is False
    assert manifest["semantic_definition_kernel_verified"] is False
    assert manifest["proof_evidence_status"] == AUTHORING_WORKER_PROOF_EVIDENCE_STATUS
    prompt_packets = [
        json.loads(line)
        for line in Path(manifest["authoring_prompt_packets_jsonl"]).read_text().splitlines()
    ]
    assert prompt_packets[0]["placeholder_symbol"] == "covered"
    assert prompt_packets[0]["source_execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED"
    )
    assert prompt_packets[0]["authoring_trigger"] == (
        "EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR_REQUIRED"
    )
    assert prompt_packets[0]["authoring_mode"] == (
        "repair_typechecked_semantic_definition_candidate"
    )
    assert prompt_packets[0]["lean_repair_action"] == "synthesize_exact_definition"
    assert prompt_packets[0]["repair_strategy"] == (
        "synthesize_reviewed_definition_from_source_references"
    )
    assert prompt_packets[0]["source_definition_closure_work_order_id"] == (
        "source_theorem_exact_semantic_definition_closure_work_order:covered"
    )
    assert prompt_packets[0]["semantic_primitive"] == "covered"
    assert prompt_packets[0]["semantic_primitive_requirements"] == ["covered"]
    assert prompt_packets[0]["source_anchors"] == [
        {
            "kind": "pseudo_formal_block",
            "id": "pf:block:covered",
            "excerpt": "coverage event is grounded by q_hat and hC",
        }
    ]
    assert prompt_packets[0]["source_pseudo_formal_work_order_id"] == (
        "pseudo_formal_work_order:covered"
    )
    assert prompt_packets[0]["source_to_bridge_adapter_instantiation_group_id"] == (
        "source_to_bridge_adapter_instantiation_group:covered"
    )
    assert prompt_packets[0][
        "source_to_bridge_grouped_premise_derivation_candidate_request_id"
    ] == "source_to_bridge_grouped_premise_derivation_candidate_request:covered"
    assert prompt_packets[0][
        "source_to_bridge_adapter_object_names_requiring_source_instantiation"
    ] == ["covered", "rank"]
    assert (
        "adapter object 'covered' must be defined from exact source theorem binders"
        in prompt_packets[0]["semantic_alignment_constraints"]
    )
    assert prompt_packets[0]["semantic_alignment_blockers"] == [
        "previous covered candidate ignored q_hat and hC"
    ]
    assert prompt_packets[0]["candidate_definition_request"]["required_anchor_names"] == [
        "s",
        "q_hat",
        "C",
        "hC",
    ]
    assert prompt_packets[0]["source_theorem_kernel_verified"] is False
    assert prompt_packets[0]["semantic_definition_kernel_verified"] is False
    assert "lean_definition_candidate" in prompt_packets[0]["response_schema"]["required"]
    assert prompt_packets[0]["candidate_repair_feedback"][
        "definition_only_candidate_artifact_path"
    ] == "/tmp/candidate_defs_only.lean"
    assert prompt_packets[0]["candidate_repair_feedback"][
        "failure_classification"
    ] == "local_lean_failed_unclassified"
    prompt_payload = json.loads(prompt_packets[0]["user_prompt"])
    assert prompt_payload["semantic_alignment_blockers"] == [
        "previous covered candidate ignored q_hat and hC"
    ]
    assert prompt_payload["authoring_trigger"] == (
        "EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR_REQUIRED"
    )
    exact_context = prompt_payload["exact_semantic_definition_context"]
    assert exact_context["semantic_primitive"] == "covered"
    assert exact_context["semantic_primitive_requirements"] == ["covered"]
    assert exact_context["source_anchors"] == [
        {
            "kind": "pseudo_formal_block",
            "id": "pf:block:covered",
            "excerpt": "coverage event is grounded by q_hat and hC",
        }
    ]
    assert exact_context["source_pseudo_formal_work_order_id"] == (
        "pseudo_formal_work_order:covered"
    )
    assert exact_context["pseudo_formal_proof_evidence_status"] == (
        "PSEUDO_FORMAL_VERIFICATION_NOT_PROOF_EVIDENCE"
    )
    assert prompt_payload["candidate_repair_feedback"]["local_lean_diagnostics"] == [
        "application type mismatch",
        "Unknown constant Nat.ceil",
        (
            "object file ./lake/.lake/packages/mathlib/.lake/build/lib/lean/"
            "Mathlib/Data/Int/Order.olean of module "
            "Mathlib.Data.Int.Order does not exist"
        ),
    ]
    assert prompt_payload["candidate_repair_feedback"]["recommended_next_action"] == (
        "repair the definition-only candidate Lean errors"
    )
    environment_contract = prompt_payload["lean_authoring_environment_contract"]
    assert environment_contract["candidate_scope"] == "definition_or_abbrev_only"
    assert environment_contract["required_anchor_names"] == [
        "s",
        "q_hat",
        "C",
        "hC",
    ]
    assert any(
        "smallest import list" in row
        for row in environment_contract["import_policy"]
    )
    assert any(
        "explicit parameter" in row
        for row in environment_contract["binder_policy"]
    )
    assert any(
        "not proof evidence" in row
        for row in environment_contract["local_lean_policy"]
    )
    assert environment_contract["local_lean_feedback"][
        "unknown_identifiers_from_last_check"
    ] == ["Nat.ceil"]
    assert environment_contract["local_lean_feedback"][
        "unavailable_imports_from_last_check"
    ] == ["Mathlib.Data.Int.Order"]
    assert any(
        "Do not introduce a new import" in row
        for row in environment_contract["repair_policy"]
    )
    assert any(
        "unverified identifier/import" in row
        for row in environment_contract["repair_policy"]
    )
    assert prompt_packets[0]["lean_authoring_environment_contract"][
        "local_lean_feedback"
    ] == environment_contract["local_lean_feedback"]
    assert prompt_packets[0]["lean_authoring_environment_contract"][
        "repair_policy"
    ] == environment_contract["repair_policy"]
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    assert learning_rows[0]["runtime_queue_status"] == (
        "PENDING_LIVE_LLM_EXACT_SEMANTIC_DEFINITION_AUTHORING"
    )
    assert learning_rows[0]["work_order_id"] == prompt_packets[0]["prompt_packet_id"]
    assert learning_rows[0]["source_prompt_packet_id"] == prompt_packets[0][
        "prompt_packet_id"
    ]
    assert learning_rows[0]["provider_requested"] is False
    assert learning_rows[0]["external_export_blocked"] is False
    assert "approved live/backend provider" in learning_rows[0][
        "recommended_next_action"
    ]
    assert "local Lean/AXLE" in learning_rows[0]["acceptance_gate"]
    assert learning_rows[0]["placeholder_symbol"] == "covered"
    assert learning_rows[0]["semantic_alignment_blockers"] == [
        "previous covered candidate ignored q_hat and hC"
    ]
    assert learning_rows[0]["authoring_trigger"] == (
        "EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR_REQUIRED"
    )
    assert learning_rows[0]["authoring_mode"] == (
        "repair_typechecked_semantic_definition_candidate"
    )
    assert learning_rows[0]["lean_repair_action"] == "synthesize_exact_definition"
    assert learning_rows[0]["repair_strategy"] == (
        "synthesize_reviewed_definition_from_source_references"
    )
    assert learning_rows[0]["input_summary"]["placeholder_symbol"] == "covered"
    assert learning_rows[0]["input_summary"]["lean_repair_action"] == (
        "synthesize_exact_definition"
    )
    assert learning_rows[0]["input_summary"]["repair_strategy"] == (
        "synthesize_reviewed_definition_from_source_references"
    )
    assert learning_rows[0]["input_summary"]["semantic_alignment_blockers"] == [
        "previous covered candidate ignored q_hat and hC"
    ]
    assert learning_rows[0]["input_summary"][
        "source_to_bridge_adapter_instantiation_group_id"
    ] == "source_to_bridge_adapter_instantiation_group:covered"
    assert learning_rows[0]["input_summary"][
        "source_to_bridge_grouped_premise_derivation_candidate_request_id"
    ] == "source_to_bridge_grouped_premise_derivation_candidate_request:covered"
    assert learning_rows[0]["proof_evidence_status"] == (
        AUTHORING_WORKER_PROOF_EVIDENCE_STATUS
    )


def test_authoring_worker_prompt_contract_reports_project_verified_import_inventory(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "authoring_tasks.jsonl"
    _write_authoring_tasks(tasks_path)
    project = tmp_path / "LeanProject"
    compiled_root = (
        project
        / ".lake"
        / "packages"
        / "mathlib"
        / ".lake"
        / "build"
        / "lib"
        / "lean"
    )
    for module in [
        "Mathlib.Data.Real.Basic",
        "Mathlib.Data.Int.Basic",
        "Mathlib.Data.Real.Archimedean",
    ]:
        path = compiled_root / Path(*module.split(".")).with_suffix(".olean")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"")
    candidate = tmp_path / "candidate_defs_only.lean"
    candidate.write_text(
        "import Mathlib.Data.Real.Basic\n"
        "import Mathlib.Data.Int.Order\n\n"
        "def reviewedCovered : Nat := 0\n",
        encoding="utf-8",
    )
    row = json.loads(tasks_path.read_text(encoding="utf-8"))
    row["candidate_lean_project_hint"] = str(project)
    row["definition_only_candidate_artifact_path"] = str(candidate)
    row["candidate_artifact_path"] = str(candidate)
    row["local_lean_diagnostics"] = [
        (
            f"{candidate}:2:0: error: object file "
            f"'{compiled_root / 'Mathlib' / 'Data' / 'Int' / 'Order.olean'}' "
            "of module Mathlib.Data.Int.Order does not exist"
        )
    ]
    tasks_path.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_authoring_worker(
        out_dir=tmp_path / "authoring_worker",
        authoring_tasks_jsonl=tasks_path,
        config=AuthoringWorkerConfig(provider_name="none", dry_run=True),
    )

    prompt_packets = [
        json.loads(line)
        for line in Path(manifest["authoring_prompt_packets_jsonl"]).read_text().splitlines()
    ]
    contract = prompt_packets[0]["lean_authoring_environment_contract"]
    inventory = contract["project_verified_import_inventory"]
    assert inventory["project_import_inventory_status"] == "available"
    assert inventory["compiled_import_module_count"] == 3
    assert inventory["candidate_import_modules"] == [
        "Mathlib.Data.Real.Basic",
        "Mathlib.Data.Int.Order",
    ]
    assert inventory["verified_candidate_import_modules"] == [
        "Mathlib.Data.Real.Basic"
    ]
    assert inventory["unverified_candidate_import_modules"] == [
        "Mathlib.Data.Int.Order"
    ]
    nearest = inventory["nearby_verified_import_modules_by_unavailable_import"][0]
    assert nearest["unavailable_import"] == "Mathlib.Data.Int.Order"
    assert "Mathlib.Data.Int.Basic" in nearest["nearest_verified_modules"]
    assert any(
        "unverified_candidate_import_modules" in row
        for row in contract["repair_policy"]
    )
    prompt_payload = json.loads(prompt_packets[0]["user_prompt"])
    assert prompt_payload["lean_authoring_environment_contract"][
        "project_verified_import_inventory"
    ] == inventory


def test_authoring_worker_prompt_contract_prefers_compiled_import_descendants(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "authoring_tasks.jsonl"
    _write_authoring_tasks(tasks_path)
    project = tmp_path / "LeanProject"
    compiled_root = (
        project
        / ".lake"
        / "packages"
        / "mathlib"
        / ".lake"
        / "build"
        / "lib"
        / "lean"
    )
    for module in [
        "Mathlib.Data.Real.Basic",
        "Mathlib.Algebra.Order.Floor.Defs",
        "Mathlib.Algebra.Order.Floor.Ring",
        "Mathlib.Topology.Algebra.Order.Floor",
    ]:
        path = compiled_root / Path(*module.split(".")).with_suffix(".olean")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"")
    candidate = tmp_path / "candidate_defs_only.lean"
    candidate.write_text(
        "import Mathlib.Data.Real.Basic\n"
        "import Mathlib.Algebra.Order.Floor\n\n"
        "def reviewedCovered : Nat := 0\n",
        encoding="utf-8",
    )
    row = json.loads(tasks_path.read_text(encoding="utf-8"))
    row["candidate_lean_project_hint"] = str(project)
    row["definition_only_candidate_artifact_path"] = str(candidate)
    row["candidate_artifact_path"] = str(candidate)
    row["local_lean_diagnostics"] = [
        (
            f"{candidate}:2:0: error: object file "
            f"'{compiled_root / 'Mathlib' / 'Algebra' / 'Order' / 'Floor.olean'}' "
            "of module Mathlib.Algebra.Order.Floor does not exist"
        )
    ]
    tasks_path.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_authoring_worker(
        out_dir=tmp_path / "authoring_worker",
        authoring_tasks_jsonl=tasks_path,
        config=AuthoringWorkerConfig(provider_name="none", dry_run=True),
    )

    prompt_packets = [
        json.loads(line)
        for line in Path(manifest["authoring_prompt_packets_jsonl"]).read_text().splitlines()
    ]
    contract = prompt_packets[0]["lean_authoring_environment_contract"]
    inventory = contract["project_verified_import_inventory"]
    repair_row = inventory["unavailable_import_repair_rows"][0]
    assert repair_row["unavailable_import"] == "Mathlib.Algebra.Order.Floor"
    assert repair_row["verified_exact_or_descendant_modules"][:2] == [
        "Mathlib.Algebra.Order.Floor.Defs",
        "Mathlib.Algebra.Order.Floor.Ring",
    ]
    assert repair_row["nearest_verified_modules"][:2] == [
        "Mathlib.Algebra.Order.Floor.Defs",
        "Mathlib.Algebra.Order.Floor.Ring",
    ]
    assert "Mathlib.Topology.Algebra.Order.Floor" in repair_row[
        "nearest_verified_modules"
    ]
    assert any(
        "replace the unavailable import with one verified_exact_or_descendant_module"
        in option
        for option in repair_row["repair_options"]
    )
    assert any(
        "unavailable_import_repair_rows" in item
        for item in contract["repair_policy"]
    )
    assert any(
        "verified_exact_or_descendant_modules" in item
        for item in contract["import_policy"]
    )
    prompt_payload = json.loads(prompt_packets[0]["user_prompt"])
    assert prompt_payload["lean_authoring_environment_contract"][
        "project_verified_import_inventory"
    ] == inventory


def test_authoring_worker_prompt_contract_reports_unknown_identifier_source_lookup(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "authoring_tasks.jsonl"
    _write_authoring_tasks(tasks_path)
    project = tmp_path / "LeanProject"
    compiled_root = (
        project
        / ".lake"
        / "packages"
        / "mathlib"
        / ".lake"
        / "build"
        / "lib"
        / "lean"
    )
    for module in [
        "Mathlib.Data.Real.Basic",
        "Mathlib.Algebra.Order.Floor.Defs",
    ]:
        path = compiled_root / Path(*module.split(".")).with_suffix(".olean")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"")
    source_path = (
        project
        / ".lake"
        / "packages"
        / "mathlib"
        / "Mathlib"
        / "Algebra"
        / "Order"
        / "Floor"
        / "Defs.lean"
    )
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        "namespace Int\n\n"
        "/-- `Int.ceil a` is the smallest integer above `a`. -/\n"
        "def ceil : α → ℤ := FloorRing.ceil\n\n"
        "end Int\n",
        encoding="utf-8",
    )
    candidate = tmp_path / "candidate_defs_only.lean"
    candidate.write_text(
        "import Mathlib.Data.Real.Basic\n\n"
        "def reviewedCovered : Nat := (Int.ceil (0 : ℝ)).toNat\n",
        encoding="utf-8",
    )
    row = json.loads(tasks_path.read_text(encoding="utf-8"))
    row["candidate_lean_project_hint"] = str(project)
    row["definition_only_candidate_artifact_path"] = str(candidate)
    row["candidate_artifact_path"] = str(candidate)
    row["local_lean_diagnostics"] = [
        f"{candidate}:3:28: error(lean.unknownIdentifier): Unknown constant `Int.ceil`"
    ]
    tasks_path.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_authoring_worker(
        out_dir=tmp_path / "authoring_worker",
        authoring_tasks_jsonl=tasks_path,
        config=AuthoringWorkerConfig(provider_name="none", dry_run=True),
    )

    prompt_packets = [
        json.loads(line)
        for line in Path(manifest["authoring_prompt_packets_jsonl"]).read_text().splitlines()
    ]
    contract = prompt_packets[0]["lean_authoring_environment_contract"]
    lookup = contract["project_identifier_lookup"]
    assert lookup["project_identifier_lookup_status"] == "available"
    row = lookup["unknown_identifier_rows"][0]
    assert row["unknown_identifier"] == "Int.ceil"
    assert row["source_lookup_status"] == "hits_found"
    assert row["verified_declaration_modules"] == [
        "Mathlib.Algebra.Order.Floor.Defs"
    ]
    assert row["declaration_hits"][0]["candidate_kind"] == (
        "lean_declaration_name_match"
    )
    assert row["declaration_hits"][0]["declaration_name"] == "Int.ceil"
    assert row["declaration_hits"][0]["module"] == (
        "Mathlib.Algebra.Order.Floor.Defs"
    )
    assert row["declaration_hits"][0]["module_compiled"] is True
    assert any(
        "add one verified_declaration_module" in option
        for option in row["repair_options"]
    )
    assert any(
        "do not replace this identifier with a sibling API" in option
        for option in row["repair_options"]
    )
    assert any(
        "project_identifier_lookup" in item
        for item in contract["repair_policy"]
    )
    assert any(
        "Do not swap to a sibling API" in item
        for item in contract["repair_policy"]
    )
    prompt_payload = json.loads(prompt_packets[0]["user_prompt"])
    assert prompt_payload["lean_authoring_environment_contract"][
        "project_identifier_lookup"
    ] == lookup


def test_authoring_worker_prompt_contract_reports_typeclass_failure_lookup(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "authoring_tasks.jsonl"
    _write_authoring_tasks(tasks_path)
    project = tmp_path / "LeanProject"
    compiled_root = (
        project
        / ".lake"
        / "packages"
        / "mathlib"
        / ".lake"
        / "build"
        / "lib"
        / "lean"
    )
    module = "Mathlib.Algebra.Order.Floor.Defs"
    compiled_path = compiled_root / Path(*module.split(".")).with_suffix(".olean")
    compiled_path.parent.mkdir(parents=True, exist_ok=True)
    compiled_path.write_bytes(b"")
    source_path = (
        project
        / ".lake"
        / "packages"
        / "mathlib"
        / "Mathlib"
        / "Algebra"
        / "Order"
        / "Floor"
        / "Defs.lean"
    )
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        "/-- A type with integer-valued floor and ceil. -/\n"
        "class FloorRing (α) [Ring α] [LinearOrder α] where\n"
        "  floor : α → ℤ\n",
        encoding="utf-8",
    )
    candidate = tmp_path / "candidate_defs_only.lean"
    candidate.write_text(
        "import Mathlib.Algebra.Order.Floor.Defs\n\n"
        "def reviewedCovered : Nat := 0\n",
        encoding="utf-8",
    )
    row = json.loads(tasks_path.read_text(encoding="utf-8"))
    row["candidate_lean_project_hint"] = str(project)
    row["definition_only_candidate_artifact_path"] = str(candidate)
    row["candidate_artifact_path"] = str(candidate)
    row["local_lean_diagnostics"] = [
        (
            f"{candidate}:3:21: error(lean.synthInstanceFailed): "
            "failed to synthesize instance of type class"
        ),
        "  FloorRing ℝ",
        (
            "Hint: Type class instance resolution failures can be inspected with "
            "the `set_option trace.Meta.synthInstance true` command."
        ),
    ]
    tasks_path.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_authoring_worker(
        out_dir=tmp_path / "authoring_worker",
        authoring_tasks_jsonl=tasks_path,
        config=AuthoringWorkerConfig(provider_name="none", dry_run=True),
    )

    prompt_packets = [
        json.loads(line)
        for line in Path(manifest["authoring_prompt_packets_jsonl"]).read_text().splitlines()
    ]
    contract = prompt_packets[0]["lean_authoring_environment_contract"]
    feedback = contract["local_lean_feedback"]
    assert feedback["typeclass_failures_from_last_check"] == [
        {
            "diagnostic_excerpt": (
                f"{candidate}:3:21: error(lean.synthInstanceFailed): "
                "failed to synthesize instance of type class"
            ),
            "failed_instance_type": "FloorRing ℝ",
            "failed_typeclass": "FloorRing",
        }
    ]
    lookup = contract["project_identifier_lookup"]
    row = lookup["identifier_lookup_rows"][0]
    assert row["lookup_reason"] == "typeclass_synthesis_failure"
    assert row["lookup_identifier"] == "FloorRing"
    assert row["typeclass_failure"]["failed_instance_type"] == "FloorRing ℝ"
    assert row["verified_declaration_modules"] == [
        "Mathlib.Algebra.Order.Floor.Defs"
    ]
    assert row["declaration_hits"][0]["declaration_kind"] == "class"
    assert row["declaration_hits"][0]["declaration_name"] == "FloorRing"
    assert any(
        "do not treat a class declaration module as evidence that an instance exists"
        in option
        for option in row["repair_options"]
    )
    assert any(
        "do not replace the failed operation with a new named API" in option
        for option in row["repair_options"]
    )
    assert any(
        "typeclass_synthesis_failure" in item
        for item in contract["repair_policy"]
    )
    assert any(
        "Any replacement operation must have its own source lookup" in item
        for item in contract["repair_policy"]
    )
    assert not any(
        item.startswith("For unknown identifiers, consult project_identifier_lookup")
        for item in contract["repair_policy"]
    )
    prompt_payload = json.loads(prompt_packets[0]["user_prompt"])
    assert prompt_payload["lean_authoring_environment_contract"][
        "project_identifier_lookup"
    ] == lookup


def test_authoring_worker_preserves_review_decision_without_proof_body_readiness(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "authoring_tasks.jsonl"
    _write_authoring_tasks(tasks_path)
    task = json.loads(tasks_path.read_text(encoding="utf-8"))
    task.update(
        {
            "source_execution_status": (
                "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_REVIEW_REQUIRED"
            ),
            "authoring_trigger": (
                "EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW_REQUIRED"
            ),
            "authoring_mode": "review_typechecked_semantic_definition_candidate",
            "runtime_queue_status": (
                "PENDING_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW_AUTHORING"
            ),
            "semantic_alignment_blockers": [],
            "local_definition_lean_compiled": True,
            "semantic_review_required_before_proof_body": True,
            "source_theorem_ready_for_exact_proof_body": False,
            "semantic_review_contract": {
                "review_decision_values": [
                    "approved_definition_candidate",
                    "repair_required",
                    "blocked_or_insufficient_context",
                ],
                "source_theorem_ready_for_exact_proof_body": False,
                "proof_body_promotion_gate": (
                    "LLM semantic review evidence is not source theorem proof."
                ),
            },
        }
    )
    tasks_path.write_text(json.dumps(task, sort_keys=True) + "\n", encoding="utf-8")
    static_response = {
        **_valid_authoring_response(),
        "known_gaps": [],
        "resolved_gap_evidence": [
            "candidate uses the recovered source score and q_hat binders"
        ],
        "proof_body_obligations": [
            "downstream proof body must prove the event has the required measurability"
        ],
        "semantic_review_decision": "approved",
        "semantic_review_evidence": [
            "checked s and q_hat against the source theorem binders",
            "checked required adapter dependencies",
        ],
        "semantic_review_required_before_proof_body": False,
        "source_theorem_ready_for_exact_proof_body": True,
    }

    authoring_manifest = run_source_theorem_exact_semantic_definition_authoring_worker(
        out_dir=tmp_path / "authoring_worker",
        authoring_tasks_jsonl=tasks_path,
        provider=StaticJSONGeneratorBackend(static_response),
        config=AuthoringWorkerConfig(
            provider_name="static",
            model="static",
            dry_run=False,
            max_repair_attempts=0,
        ),
    )

    assert authoring_manifest["n_semantic_review_prompt_packets"] == 1
    assert (
        authoring_manifest["n_candidate_packets_with_semantic_review_decision"]
        == 1
    )
    prompt_packets = [
        json.loads(line)
        for line in Path(
            authoring_manifest["authoring_prompt_packets_jsonl"]
        ).read_text().splitlines()
    ]
    prompt_payload = json.loads(prompt_packets[0]["user_prompt"])
    assert prompt_payload["authoring_mode"] == (
        "review_typechecked_semantic_definition_candidate"
    )
    assert prompt_payload["semantic_review_required_before_proof_body"] is True
    assert prompt_payload["source_theorem_ready_for_exact_proof_body"] is False
    assert prompt_payload["semantic_review_contract"][
        "source_theorem_ready_for_exact_proof_body"
    ] is False
    assert "known_gaps must be []" in prompt_payload[
        "semantic_review_output_policy"
    ]["review_mode_gate"]
    assert "unresolved definition-level" in prompt_payload[
        "required_output_contract"
    ]["known_gaps"][0]
    assert prompt_payload["semantic_review_contract"][
        "known_gap_classification_policy"
    ]["review_mode_gate"] == prompt_payload["semantic_review_output_policy"][
        "review_mode_gate"
    ]
    assert "semantic_review_decision" in prompt_packets[0]["response_schema"][
        "properties"
    ]
    candidate_packets = [
        json.loads(line)
        for line in Path(
            authoring_manifest["authoring_candidate_packets_jsonl"]
        ).read_text().splitlines()
    ]
    assert candidate_packets[0]["semantic_review_decision"] == (
        "approved_definition_candidate"
    )
    assert candidate_packets[0]["semantic_review_status"] == (
        "llm_semantic_review_approved_definition_candidate_not_proof"
    )
    assert candidate_packets[0]["semantic_review_required_before_proof_body"] is True
    assert candidate_packets[0]["source_theorem_ready_for_exact_proof_body"] is False
    assert (
        candidate_packets[0]["llm_claimed_source_theorem_ready_for_exact_proof_body"]
        is True
    )
    assert candidate_packets[0]["source_theorem_kernel_verified"] is False
    assert candidate_packets[0]["semantic_definition_kernel_verified"] is False

    materializer_manifest = (
        run_source_theorem_exact_semantic_definition_authoring_candidate_materializer(
            out_dir=tmp_path / "materializer",
            authoring_worker_manifest=Path(authoring_manifest["manifest_path"]),
            config=AuthoringCandidateMaterializerConfig(),
        )
    )

    assert (
        materializer_manifest[
            "n_materialized_candidates_with_semantic_review_decision"
        ]
        == 1
    )
    rows = [
        json.loads(line)
        for line in Path(
            materializer_manifest["materialization_rows_jsonl"]
        ).read_text().splitlines()
    ]
    assert rows[0]["semantic_review_decision"] == "approved_definition_candidate"
    assert rows[0]["semantic_review_required_before_proof_body"] is True
    assert rows[0]["source_theorem_ready_for_exact_proof_body"] is False
    repair_tasks = [
        json.loads(line)
        for line in Path(
            materializer_manifest["materialized_lean_repair_tasks_jsonl"]
        ).read_text().splitlines()
    ]
    assert repair_tasks[0]["authoring_mode"] == (
        "review_typechecked_semantic_definition_candidate"
    )
    assert repair_tasks[0]["semantic_review_decision"] == (
        "approved_definition_candidate"
    )
    assert repair_tasks[0]["semantic_review_required_before_proof_body"] is True
    assert repair_tasks[0]["source_theorem_ready_for_exact_proof_body"] is False
    assert repair_tasks[0]["definition_contract"]["semantic_review_status"] == (
        "llm_semantic_review_approved_definition_candidate_not_proof"
    )


def test_authoring_worker_rejects_approved_review_packet_with_known_gaps() -> None:
    packet = {
        **_valid_authoring_response(),
        "authoring_mode": "review_typechecked_semantic_definition_candidate",
        "semantic_review_decision": "approved_definition_candidate",
        "semantic_review_evidence": [
            "checked source theorem binders against the candidate"
        ],
        "forbidden_shortcuts_absent": True,
        "requires_local_lean_check": True,
        "local_definition_lean_checked": False,
        "local_definition_lean_compiled": False,
        "semantic_definition_kernel_verified": False,
        "source_theorem_kernel_verified": False,
        "proof_evidence_status": CANDIDATE_PROOF_EVIDENCE_STATUS,
    }

    errors = validate_authoring_candidate_packet(packet)

    assert any("known_gaps empty" in error for error in errors)


def test_authoring_worker_filters_by_placeholder_symbol(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "authoring_tasks.jsonl"
    _write_authoring_tasks(tasks_path)
    rank_task = json.loads(tasks_path.read_text(encoding="utf-8"))
    rank_task.pop("candidate_definition_request", None)
    rank_task.update(
        {
            "authoring_task_id": "authoring:rank",
            "source_execution_result_id": "execution:rank",
            "source_lean_repair_task_id": "lean-repair:rank",
            "placeholder_symbol": "rank",
            "source_definition_closure_work_order_id": (
                "source_theorem_exact_semantic_definition_closure_work_order:rank"
            ),
            "source_to_bridge_adapter_instantiation_group_id": (
                "source_to_bridge_adapter_instantiation_group:covered"
            ),
            "source_to_bridge_grouped_premise_derivation_candidate_request_id": (
                "source_to_bridge_grouped_premise_derivation_candidate_request:rank"
            ),
            "semantic_alignment_constraints": [
                "adapter object 'rank' must be defined from exact source theorem binders"
            ],
            "premise_semantic_anchor_binders": [
                {"name": "n2", "role": "calibration_size_anchor", "type": "ℕ"},
                {
                    "name": "s",
                    "role": "score_process_anchor",
                    "type": "Fin (n2 + 1) → Ω → ℝ",
                },
                {
                    "name": "q_hat",
                    "role": "threshold_function_anchor",
                    "type": "Ω → ℝ",
                },
                {
                    "name": "hq",
                    "role": "quantile_definition_anchor",
                    "type": "q_hat = fun ω => orderStat s k ω",
                },
            ],
        }
    )
    with tasks_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(rank_task, sort_keys=True) + "\n")

    manifest = run_source_theorem_exact_semantic_definition_authoring_worker(
        out_dir=tmp_path / "authoring_worker",
        authoring_tasks_jsonl=tasks_path,
        config=AuthoringWorkerConfig(
            provider_name="none",
            dry_run=True,
            placeholder_symbols=("rank",),
        ),
    )

    assert manifest["n_authoring_tasks_before_placeholder_filter"] == 2
    assert manifest["n_authoring_tasks_after_placeholder_filter"] == 1
    assert manifest["n_authoring_tasks"] == 1
    assert manifest["placeholder_symbol_filter"] == ["rank"]
    assert manifest["normalized_placeholder_symbol_filter"] == ["rank"]
    assert manifest["n_candidate_definition_requests_autofilled"] == 1
    assert manifest["placeholder_symbols"] == ["rank"]
    prompt_packets = [
        json.loads(line)
        for line in Path(manifest["authoring_prompt_packets_jsonl"]).read_text().splitlines()
    ]
    assert len(prompt_packets) == 1
    assert prompt_packets[0]["placeholder_symbol"] == "rank"
    assert prompt_packets[0]["candidate_definition_request_autofilled"] is True
    request = prompt_packets[0]["candidate_definition_request"]
    assert request["placeholder_symbol"] == "rank"
    assert request["placeholder_policy_id"] == "split_conformal_coverage.rank"
    assert request["placeholder_policy_scope"] == "split_conformal_coverage"
    assert request["required_anchor_names"] == ["n2", "s", "q_hat", "hq"]
    assert request["missing_required_anchor_names"] == []
    assert [binder["name"] for binder in request["required_binders"]] == [
        "n2",
        "s",
        "q_hat",
        "hq",
    ]
    assert "order-statistic threshold equation hq" in request["semantic_goal"]


def test_authoring_worker_marks_provider_connection_failure_retryable(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "authoring_tasks.jsonl"
    _write_authoring_tasks(tasks_path)
    task = json.loads(tasks_path.read_text(encoding="utf-8"))
    task.pop("candidate_definition_request", None)
    task.update(
        {
            "placeholder_symbol": "rank",
            "exact_source_theorem_binders": [
                {"name": "n2", "role": "calibration_size_anchor", "type": "ℕ"},
                {
                    "name": "s",
                    "role": "score_process_anchor",
                    "type": "Fin (n2 + 1) → Ω → ℝ",
                },
                {
                    "name": "q_hat",
                    "role": "threshold_function_anchor",
                    "type": "Ω → ℝ",
                },
            ],
            "premise_semantic_anchor_binders": [
                {
                    "name": "hq",
                    "role": "quantile_definition_anchor",
                    "type": "q_hat = fun ω => orderStat s k ω",
                }
            ],
            "premise_semantic_anchor_binder_names": ["n2", "s", "q_hat", "hq"],
        }
    )
    tasks_path.write_text(json.dumps(task, sort_keys=True) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_authoring_worker(
        out_dir=tmp_path / "authoring_worker",
        authoring_tasks_jsonl=tasks_path,
        provider=_ConnectionFailingProvider(),
        config=AuthoringWorkerConfig(
            provider_name="anthropic",
            model="claude-sonnet-4-6",
            model_tier="sonnet",
            dry_run=False,
            allow_external_export=True,
            max_repair_attempts=0,
        ),
    )

    assert manifest["n_llm_attempted"] == 1
    assert manifest["n_candidate_packets"] == 1
    assert manifest["n_candidate_packets_ok"] == 0
    assert manifest["n_retryable_provider_failures"] == 1
    assert manifest["n_retryable_authoring_tasks"] == 1
    candidates = [
        json.loads(line)
        for line in Path(manifest["authoring_candidate_packets_jsonl"]).read_text().splitlines()
    ]
    candidate = candidates[0]
    assert candidate["runtime_queue_status"] == (
        "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_RETRY"
    )
    assert candidate["authoring_mode"] == (
        "repair_typechecked_semantic_definition_candidate"
    )
    assert candidate["source_execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED"
    )
    assert candidate["failure_classification"] == "provider_connection_error"
    assert candidate["candidate_definition_request"]["placeholder_symbol"] == "rank"
    assert candidate["candidate_definition_request"]["missing_required_anchor_names"] == []
    assert candidate["recommended_next_action"].startswith("retry the same")
    retry_tasks = [
        json.loads(line)
        for line in Path(manifest["retryable_authoring_tasks_jsonl"]).read_text().splitlines()
    ]
    assert len(retry_tasks) == 1
    assert retry_tasks[0]["runtime_queue_status"] == (
        "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_RETRY"
    )
    assert retry_tasks[0]["retry_of_authoring_failure"] is True
    assert retry_tasks[0]["retry_failure_classification"] == (
        "provider_connection_error"
    )
    assert retry_tasks[0]["placeholder_symbol"] == "rank"
    assert retry_tasks[0]["candidate_definition_request"]["placeholder_symbol"] == (
        "rank"
    )
    assert retry_tasks[0]["candidate_definition_request"][
        "missing_required_anchor_names"
    ] == []
    assert retry_tasks[0]["source_theorem_kernel_verified"] is False
    assert retry_tasks[0]["semantic_definition_kernel_verified"] is False
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    candidate_learning = next(row for row in learning_rows if row.get("candidate_packet_id"))
    assert candidate_learning["runtime_queue_status"] == (
        "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_RETRY"
    )
    assert candidate_learning["candidate_definition_request"]["placeholder_symbol"] == (
        "rank"
    )


def test_authoring_worker_blocks_external_provider_without_export_approval(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "authoring_tasks.jsonl"
    _write_authoring_tasks(tasks_path)

    manifest = run_source_theorem_exact_semantic_definition_authoring_worker(
        out_dir=tmp_path / "authoring_worker",
        authoring_tasks_jsonl=tasks_path,
        provider=_ExplodingExternalProvider(),
        config=AuthoringWorkerConfig(
            provider_name="anthropic",
            dry_run=False,
            allow_external_export=False,
        ),
    )

    assert manifest["provider_requested"] is False
    assert manifest["external_export_requested"] is True
    assert manifest["external_export_allowed"] is False
    assert manifest["external_export_blocked"] is True
    assert manifest["n_llm_attempted"] == 0
    assert manifest["n_candidate_packets"] == 0
    assert manifest["n_external_llm_export_review_packets"] == 1
    assert manifest["n_external_export_blocked_tasks"] == 1
    review_packets = [
        json.loads(line)
        for line in Path(
            manifest["external_llm_export_review_packets_jsonl"]
        ).read_text().splitlines()
    ]
    assert review_packets[0]["runtime_queue_status"] == (
        "BLOCKED_EXTERNAL_LLM_EXPORT_REVIEW_REQUIRED"
    )
    assert review_packets[0]["export_payload_summary"]["n_source_theorem_binders"] == 4
    assert review_packets[0]["source_theorem_kernel_verified"] is False
    assert review_packets[0]["semantic_definition_kernel_verified"] is False
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    assert {
        row["runtime_queue_status"] for row in learning_rows
    } == {"BLOCKED_EXTERNAL_LLM_EXPORT_REVIEW_REQUIRED"}


def test_authoring_worker_redacted_external_export_removes_paths_and_snippets(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "authoring_tasks.jsonl"
    _write_authoring_tasks(tasks_path)

    manifest = run_source_theorem_exact_semantic_definition_authoring_worker(
        out_dir=tmp_path / "authoring_worker",
        authoring_tasks_jsonl=tasks_path,
        provider=_ExplodingExternalProvider(),
        config=AuthoringWorkerConfig(
            provider_name="anthropic",
            dry_run=False,
            allow_external_export=False,
            external_export_mode="redacted",
        ),
    )

    assert manifest["external_export_mode"] == "redacted"
    assert manifest["external_export_blocked"] is True
    assert manifest["n_llm_attempted"] == 0
    prompt_packets = [
        json.loads(line)
        for line in Path(manifest["authoring_prompt_packets_jsonl"]).read_text().splitlines()
    ]
    prompt_payload = json.loads(prompt_packets[0]["user_prompt"])
    assert prompt_payload["external_export_mode"] == "redacted"
    assert prompt_payload["export_redaction_applied"] is True
    refs = prompt_payload["source_reference_hints"]
    assert refs
    assert all("path" not in row for row in refs)
    assert all("snippet" not in row for row in refs)
    assert all(row["path_redacted"] is True for row in refs)
    assert all(row["snippet_redacted"] is True for row in refs)
    exact_context = prompt_payload["exact_semantic_definition_context"]
    assert exact_context["semantic_primitive_requirements"] == ["covered"]
    assert exact_context["source_anchors"] == [
        {
            "anchor_index": 0,
            "kind": "pseudo_formal_block",
            "id": "pf:block:covered",
            "excerpt_redacted": True,
            "excerpt_chars": len("coverage event is grounded by q_hat and hC"),
        }
    ]
    summary = prompt_payload["source_reference_redaction_summary"]
    assert summary["redaction_applied"] is True
    assert summary["paths_redacted"] == 1
    assert summary["snippets_redacted"] == 1
    review_packets = [
        json.loads(line)
        for line in Path(
            manifest["external_llm_export_review_packets_jsonl"]
        ).read_text().splitlines()
    ]
    review_summary = review_packets[0]["export_payload_summary"]
    assert review_packets[0]["external_export_mode"] == "redacted"
    assert review_packets[0]["export_redaction_applied"] is True
    assert review_summary["contains_local_paths"] is False
    assert review_summary["contains_lean_source_snippets"] is False
    assert review_summary["source_reference_paths"] == [""]
    assert review_summary["source_reference_redaction_summary"]["paths_redacted"] == 1


def test_authoring_worker_external_export_approval_manifest_allows_exact_task(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "authoring_tasks.jsonl"
    _write_authoring_tasks(tasks_path)

    preflight_manifest = run_source_theorem_exact_semantic_definition_authoring_worker(
        out_dir=tmp_path / "preflight",
        authoring_tasks_jsonl=tasks_path,
        provider=_ExplodingExternalProvider(),
        config=AuthoringWorkerConfig(
            provider_name="anthropic",
            dry_run=False,
            allow_external_export=False,
            external_export_mode="redacted",
        ),
    )
    review_packet = json.loads(
        Path(preflight_manifest["external_llm_export_review_packets_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    approval_manifest = tmp_path / "external_export_approval.json"
    approval_manifest.write_text(
        json.dumps(
            {
                "approval_rows": [
                    {
                        "approved": True,
                        "source_prompt_packet_id": review_packet[
                            "source_prompt_packet_id"
                        ],
                        "provider_name": "anthropic",
                        "external_export_mode": "redacted",
                    }
                ]
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    provider = _StaticExternalProvider(_valid_authoring_response())

    manifest = run_source_theorem_exact_semantic_definition_authoring_worker(
        out_dir=tmp_path / "approved_authoring_worker",
        authoring_tasks_jsonl=tasks_path,
        provider=provider,
        config=AuthoringWorkerConfig(
            provider_name="anthropic",
            model="claude-sonnet-4-6",
            dry_run=False,
            allow_external_export=False,
            external_export_mode="redacted",
            external_export_approval_manifest=str(approval_manifest),
            max_repair_attempts=0,
        ),
    )

    assert provider.calls == 1
    assert manifest["provider_requested"] is True
    assert manifest["external_export_requested"] is True
    assert manifest["external_export_allowed"] is False
    assert manifest["external_export_approval_manifest_loaded"] is True
    assert manifest["external_export_blocked"] is False
    assert manifest["n_external_export_approved_tasks"] == 1
    assert manifest["n_external_export_blocked_tasks"] == 0
    assert manifest["n_external_llm_export_review_packets"] == 0
    assert manifest["n_llm_attempted"] == 1
    assert manifest["n_candidate_packets_ok"] == 1
    candidates = [
        json.loads(line)
        for line in Path(manifest["authoring_candidate_packets_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert candidates[0]["provider"] == "anthropic"
    assert candidates[0]["proof_evidence_status"] == CANDIDATE_PROOF_EVIDENCE_STATUS
    assert candidates[0]["source_theorem_kernel_verified"] is False


def test_authoring_worker_external_export_approval_manifest_mismatch_blocks(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "authoring_tasks.jsonl"
    _write_authoring_tasks(tasks_path)

    preflight_manifest = run_source_theorem_exact_semantic_definition_authoring_worker(
        out_dir=tmp_path / "preflight",
        authoring_tasks_jsonl=tasks_path,
        provider=_ExplodingExternalProvider(),
        config=AuthoringWorkerConfig(
            provider_name="anthropic",
            dry_run=False,
            allow_external_export=False,
            external_export_mode="redacted",
        ),
    )
    review_packet = json.loads(
        Path(preflight_manifest["external_llm_export_review_packets_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    approval_manifest = tmp_path / "external_export_approval_mismatch.json"
    approval_manifest.write_text(
        json.dumps(
            {
                "approval_rows": [
                    {
                        "approved": True,
                        "source_prompt_packet_id": review_packet[
                            "source_prompt_packet_id"
                        ],
                        "provider_name": "openai",
                        "external_export_mode": "redacted",
                    }
                ]
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    manifest = run_source_theorem_exact_semantic_definition_authoring_worker(
        out_dir=tmp_path / "blocked_authoring_worker",
        authoring_tasks_jsonl=tasks_path,
        provider=_ExplodingExternalProvider(),
        config=AuthoringWorkerConfig(
            provider_name="anthropic",
            dry_run=False,
            allow_external_export=False,
            external_export_mode="redacted",
            external_export_approval_manifest=str(approval_manifest),
        ),
    )

    assert manifest["provider_requested"] is False
    assert manifest["external_export_approval_manifest_loaded"] is True
    assert manifest["external_export_blocked"] is True
    assert manifest["n_external_export_approved_tasks"] == 0
    assert manifest["n_external_export_blocked_tasks"] == 1
    assert manifest["n_external_llm_export_review_packets"] == 1
    assert manifest["n_llm_attempted"] == 0


def test_authoring_worker_static_candidate_preserves_kernel_boundary(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "authoring_tasks.jsonl"
    _write_authoring_tasks(tasks_path)
    static_response = _valid_authoring_response()

    manifest = run_source_theorem_exact_semantic_definition_authoring_worker(
        out_dir=tmp_path / "authoring_worker",
        authoring_tasks_jsonl=tasks_path,
        provider=StaticJSONGeneratorBackend(static_response),
        config=AuthoringWorkerConfig(
            provider_name="static",
            model="static",
            dry_run=False,
            max_repair_attempts=0,
        ),
    )

    assert manifest["n_llm_attempted"] == 1
    assert manifest["n_candidate_packets"] == 1
    assert manifest["n_candidate_packets_ok"] == 1
    assert manifest["n_local_lean_checked"] == 0
    assert manifest["source_theorem_kernel_verified"] is False
    assert manifest["semantic_definition_kernel_verified"] is False
    candidates = [
        json.loads(line)
        for line in Path(manifest["authoring_candidate_packets_jsonl"]).read_text().splitlines()
    ]
    candidate = candidates[0]
    assert candidate["ok"] is True
    assert candidate["provider"] == "static"
    assert candidate["placeholder_symbol"] == "covered"
    assert candidate["source_execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED"
    )
    assert candidate["authoring_mode"] == (
        "repair_typechecked_semantic_definition_candidate"
    )
    assert candidate["candidate_repair_feedback"]["failure_classification"] == (
        "local_lean_failed_unclassified"
    )
    assert candidate["local_definition_lean_checked"] is False
    assert candidate["local_definition_lean_compiled"] is False
    assert candidate["semantic_definition_kernel_verified"] is False
    assert candidate["source_theorem_kernel_verified"] is False
    assert candidate["proof_evidence_status"] == CANDIDATE_PROOF_EVIDENCE_STATUS
    assert candidate["runtime_queue_status"] == (
        "PENDING_EXACT_SEMANTIC_DEFINITION_CANDIDATE_MATERIALIZATION"
    )
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    candidate_learning = next(row for row in learning_rows if row.get("candidate_packet_id"))
    assert candidate_learning["runtime_queue_status"] == (
        "PENDING_EXACT_SEMANTIC_DEFINITION_CANDIDATE_MATERIALIZATION"
    )
    assert candidate_learning["authoring_mode"] == (
        "repair_typechecked_semantic_definition_candidate"
    )
    assert candidate_learning["input_summary"]["source_execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED"
    )
    assert candidate_learning["candidate_repair_feedback"][
        "failure_classification"
    ] == "local_lean_failed_unclassified"
    assert candidate_learning["input_summary"]["local_definition_lean_checked"] is False
    assert candidate_learning["input_summary"]["source_theorem_kernel_verified"] is False


def test_authoring_worker_rejects_forbidden_shortcut_candidate(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "authoring_tasks.jsonl"
    _write_authoring_tasks(tasks_path)
    static_response = {
        "placeholder_symbol": "covered",
        "definition_design": "Shortcut placeholder.",
        "lean_definition_candidate": "def covered : Prop := True",
        "required_imports": [],
        "binder_usage": [],
        "semantic_alignment_notes": [],
        "known_gaps": [],
        "forbidden_shortcuts_absent": True,
        "requires_local_lean_check": True,
    }

    manifest = run_source_theorem_exact_semantic_definition_authoring_worker(
        out_dir=tmp_path / "authoring_worker",
        authoring_tasks_jsonl=tasks_path,
        provider=StaticJSONGeneratorBackend(static_response),
        config=AuthoringWorkerConfig(
            provider_name="static",
            model="static",
            dry_run=False,
            max_repair_attempts=0,
        ),
    )

    assert manifest["n_candidate_packets"] == 1
    assert manifest["n_candidate_packets_ok"] == 0
    assert manifest["n_candidate_packets_failed"] == 1
    candidates = [
        json.loads(line)
        for line in Path(manifest["authoring_candidate_packets_jsonl"]).read_text().splitlines()
    ]
    assert candidates[0]["ok"] is False
    assert candidates[0]["runtime_queue_status"] == (
        "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR"
    )
    assert "forbidden shortcut" in candidates[0]["validation_errors"][0]
    assert candidates[0]["source_theorem_kernel_verified"] is False
    assert candidates[0]["semantic_definition_kernel_verified"] is False


def test_authoring_worker_retry_prompt_carries_response_validation_feedback(
    tmp_path: Path,
) -> None:
    project = tmp_path / "lean_project"
    compiled_basic = (
        project
        / ".lake"
        / "build"
        / "lib"
        / "lean"
        / "Mathlib"
        / "Data"
        / "Real"
        / "Basic.olean"
    )
    compiled_basic.parent.mkdir(parents=True)
    compiled_basic.write_bytes(b"")
    prior_candidate = tmp_path / "PriorCandidate.lean"
    prior_candidate.write_text(
        "import Mathlib.Data.Real.Basic\n\ndef priorRank : Nat := 0\n",
        encoding="utf-8",
    )
    tasks_path = tmp_path / "authoring_tasks.jsonl"
    tasks_path.write_text(
        json.dumps(
            {
                "artifact_kind": "SourceTheoremExactSemanticDefinitionAuthoringTask",
                "authoring_task_id": "authoring_task:rank-validation-retry",
                "target_theorem_name": "split_conformal_coverage",
                "placeholder_symbol": "rank",
                "candidate_lean_project_hint": str(project),
                "definition_only_candidate_artifact_path": str(prior_candidate),
                "runtime_queue_status": (
                    "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR"
                ),
                "source_execution_status": (
                    "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LOCAL_LEAN_FAILED"
                ),
                "candidate_definition_request": {
                    "request_kind": (
                        "source_theorem_exact_semantic_definition_candidate"
                    ),
                    "target_theorem_name": "split_conformal_coverage",
                    "placeholder_symbol": "rank",
                    "semantic_goal": "Repair the exact semantic definition.",
                    "required_anchor_names": ["n2"],
                    "available_anchor_names": ["n2"],
                    "missing_required_anchor_names": [],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    static_response = {
        "placeholder_symbol": "rank",
        "definition_design": "Incorrectly add an unverified rational import.",
        "lean_definition_candidate": (
            "import Mathlib.Data.Real.Basic\n"
            "import Mathlib.Data.Rat.Basic\n\n"
            "def repairedRank : Nat := 0"
        ),
        "required_imports": [
            "Mathlib.Data.Real.Basic",
            "Mathlib.Data.Rat.Basic",
        ],
        "binder_usage": [],
        "semantic_alignment_notes": ["diagnostic only"],
        "known_gaps": [],
        "forbidden_shortcuts_absent": True,
        "requires_local_lean_check": True,
    }

    failed_manifest = run_source_theorem_exact_semantic_definition_authoring_worker(
        out_dir=tmp_path / "authoring_worker_failed",
        authoring_tasks_jsonl=tasks_path,
        provider=StaticJSONGeneratorBackend(static_response),
        config=AuthoringWorkerConfig(
            provider_name="static",
            model="static",
            dry_run=False,
            max_repair_attempts=0,
        ),
    )
    candidate = json.loads(
        Path(failed_manifest["authoring_candidate_packets_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    retry_task = json.loads(
        Path(failed_manifest["retryable_authoring_tasks_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )

    assert candidate["ok"] is False
    assert "Mathlib.Data.Rat.Basic" in candidate["validation_errors"][0]
    assert retry_task["retry_failure_classification"] == (
        "authoring_candidate_validation_failed"
    )
    assert "Mathlib.Data.Rat.Basic" in retry_task["retry_validation_errors"][0]

    retry_manifest = run_source_theorem_exact_semantic_definition_authoring_worker(
        out_dir=tmp_path / "authoring_worker_retry_prompt",
        authoring_tasks_jsonl=Path(failed_manifest["retryable_authoring_tasks_jsonl"]),
        config=AuthoringWorkerConfig(provider_name="none", dry_run=True),
    )
    prompt_packet = json.loads(
        Path(retry_manifest["authoring_prompt_packets_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    prompt_payload = json.loads(prompt_packet["user_prompt"])
    feedback = prompt_payload["response_validation_feedback"]
    contract = prompt_payload["lean_authoring_environment_contract"]

    assert prompt_packet["retry_validation_errors"] == [
        candidate["validation_errors"][0]
    ]
    assert feedback["failure_classification"] == (
        "authoring_candidate_validation_failed"
    )
    assert feedback["unverified_required_imports"] == [
        "Mathlib.Data.Rat.Basic"
    ]
    assert "Mathlib.Data.Rat.Basic" in prompt_packet["user_prompt"]
    assert contract["response_validation_feedback"]["validation_errors"] == [
        candidate["validation_errors"][0]
    ]
    assert contract["hard_local_negative_constraints"][
        "unverified_imports_rejected_by_response_validator"
    ] == ["Mathlib.Data.Rat.Basic"]
    assert any(
        "response_validation_feedback.unverified_required_imports" in row
        for row in contract["repair_policy"]
    )


def test_authoring_worker_structural_route_carries_response_validation_feedback(
    tmp_path: Path,
) -> None:
    project = tmp_path / "lean_project"
    compiled_basic = (
        project
        / ".lake"
        / "build"
        / "lib"
        / "lean"
        / "Mathlib"
        / "Data"
        / "Real"
        / "Basic.olean"
    )
    compiled_basic.parent.mkdir(parents=True)
    compiled_basic.write_bytes(b"")
    prior_candidate = tmp_path / "PriorCandidate.lean"
    prior_candidate.write_text(
        "import Mathlib.Data.Real.Basic\n\ndef priorCn : Nat := 0\n",
        encoding="utf-8",
    )
    tasks_path = tmp_path / "authoring_tasks.jsonl"
    tasks_path.write_text(
        json.dumps(
            {
                "artifact_kind": "SourceTheoremExactSemanticDefinitionAuthoringTask",
                "authoring_task_id": "authoring_task:structural-validation",
                "target_theorem_name": "split_conformal_coverage",
                "placeholder_symbol": "C_n",
                "candidate_lean_project_hint": str(project),
                "definition_only_candidate_artifact_path": str(prior_candidate),
                "runtime_queue_status": (
                    "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR"
                ),
                "source_execution_status": (
                    "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LOCAL_LEAN_FAILED"
                ),
                "local_lean_checked": True,
                "local_lean_compiled": False,
                "local_lean_diagnostics": [
                    "error(lean.unknownIdentifier): Unknown constant `List.get?`",
                ],
                "candidate_definition_request": {
                    "request_kind": (
                        "source_theorem_exact_semantic_definition_candidate"
                    ),
                    "target_theorem_name": "split_conformal_coverage",
                    "placeholder_symbol": "C_n",
                    "semantic_goal": (
                        "Repair C_n without guessing unavailable list APIs."
                    ),
                    "required_anchor_names": ["scores"],
                    "available_anchor_names": ["scores"],
                    "missing_required_anchor_names": [],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    static_response = {
        "placeholder_symbol": "C_n",
        "definition_design": (
            "Incorrectly reuse unresolved List.get? and guess a new import."
        ),
        "lean_definition_candidate": (
            "import Mathlib.Data.Real.Basic\n"
            "import Mathlib.Data.Int.Order\n\n"
            "def repairedCn (scores : List Nat) : Nat :=\n"
            "  match List.get? scores 0 with\n"
            "  | some value => value\n"
            "  | none => 0"
        ),
        "required_imports": [
            "Mathlib.Data.Real.Basic",
            "Mathlib.Data.Int.Order",
        ],
        "binder_usage": [{"name": "scores", "how_used": "candidate list"}],
        "semantic_alignment_notes": ["diagnostic only"],
        "known_gaps": [],
        "forbidden_shortcuts_absent": True,
        "requires_local_lean_check": True,
    }

    manifest = run_source_theorem_exact_semantic_definition_authoring_worker(
        out_dir=tmp_path / "authoring_worker",
        authoring_tasks_jsonl=tasks_path,
        provider=StaticJSONGeneratorBackend(static_response),
        config=AuthoringWorkerConfig(
            provider_name="static",
            model="static",
            dry_run=False,
            max_repair_attempts=0,
        ),
    )
    candidate = json.loads(
        Path(manifest["authoring_candidate_packets_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    retry_task = json.loads(
        Path(manifest["retryable_authoring_tasks_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )

    assert candidate["ok"] is False
    assert candidate["runtime_queue_status"] == STRUCTURAL_REFORMULATION_QUEUE_STATUS
    assert candidate["failure_classification"] == (
        STRUCTURAL_REFORMULATION_FAILURE_CLASSIFICATION
    )
    assert "Mathlib.Data.Int.Order" in " ".join(candidate["validation_errors"])
    assert "List.get?" in " ".join(candidate["validation_errors"])
    feedback = candidate["response_validation_feedback"]
    assert feedback["source_failed_candidate_packet_id"] == (
        candidate["candidate_packet_id"]
    )
    assert feedback["unverified_required_imports"] == ["Mathlib.Data.Int.Order"]
    route = candidate[
        "source_theorem_exact_semantic_definition_structural_reformulation_route"
    ]
    assert route["response_validation_feedback"] == feedback
    assert route["unverified_required_imports"] == ["Mathlib.Data.Int.Order"]
    assert route["pseudo_formalization_required"] is True
    assert route["target_lanes"] == [
        "source_theorem_exact_semantic_definition",
        "lean_rag",
        "source_to_bridge",
    ]
    candidate_learning_row = learning_rows[-1]
    assert candidate_learning_row["runtime_queue_status"] == (
        STRUCTURAL_REFORMULATION_QUEUE_STATUS
    )
    assert candidate_learning_row["retry_validation_errors"] == (
        candidate["validation_errors"]
    )
    assert candidate_learning_row["response_validation_feedback"] == feedback
    assert retry_task["response_validation_feedback"] == feedback
    assert retry_task["retry_validation_errors"] == candidate["validation_errors"]


def test_authoring_candidate_materializer_writes_lean_repair_task(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "authoring_tasks.jsonl"
    _write_authoring_tasks(tasks_path)
    static_response = {
        "placeholder_symbol": "covered",
        "definition_design": (
            "Coverage is represented as the held-out score event below q_hat."
        ),
        "lean_definition_candidate": (
            "import Mathlib.Data.Set.Basic\n"
            "import Mathlib.Data.Fin.Basic\n\n"
            "def reviewedCovered : Nat := 0"
        ),
        "required_imports": [
            "Mathlib.Data.Set.Basic",
            "Mathlib.Data.Fin.Basic",
            "import Mathlib.Data.Set.Basic",
        ],
        "binder_usage": [{"name": "hC", "how_used": "semantic anchor"}],
        "semantic_alignment_notes": [
            "Draft is intentionally definition-only and must be reviewed."
        ],
        "known_gaps": ["semantic alignment still requires human/critic review"],
        "forbidden_shortcuts_absent": True,
        "requires_local_lean_check": True,
    }
    authoring_manifest = run_source_theorem_exact_semantic_definition_authoring_worker(
        out_dir=tmp_path / "authoring_worker",
        authoring_tasks_jsonl=tasks_path,
        provider=StaticJSONGeneratorBackend(static_response),
        config=AuthoringWorkerConfig(
            provider_name="static",
            model="static",
            dry_run=False,
            max_repair_attempts=0,
        ),
    )

    materializer_manifest = (
        run_source_theorem_exact_semantic_definition_authoring_candidate_materializer(
            out_dir=tmp_path / "materializer",
            authoring_worker_manifest=Path(authoring_manifest["manifest_path"]),
            config=AuthoringCandidateMaterializerConfig(),
        )
    )

    assert materializer_manifest["n_candidate_packets"] == 1
    assert materializer_manifest["n_materialized_definition_only_candidates"] == 1
    assert materializer_manifest["n_materialized_lean_repair_tasks"] == 1
    assert materializer_manifest["n_local_lean_checked"] == 0
    assert materializer_manifest["source_theorem_kernel_verified"] is False
    assert materializer_manifest["semantic_definition_kernel_verified"] is False
    assert materializer_manifest["proof_evidence_status"] == (
        MATERIALIZER_PROOF_EVIDENCE_STATUS
    )
    rows = [
        json.loads(line)
        for line in Path(
            materializer_manifest["materialization_rows_jsonl"]
        ).read_text().splitlines()
    ]
    assert rows[0]["materialization_status"] == (
        "EXACT_SEMANTIC_DEFINITION_CANDIDATE_MATERIALIZED_PENDING_LOCAL_LEAN"
    )
    assert rows[0]["source_execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED"
    )
    assert rows[0]["authoring_mode"] == (
        "repair_typechecked_semantic_definition_candidate"
    )
    assert rows[0]["source_repair_strategy"] == (
        "synthesize_reviewed_definition_from_source_references"
    )
    assert rows[0]["candidate_repair_feedback"]["failure_classification"] == (
        "local_lean_failed_unclassified"
    )
    definition_path = Path(rows[0]["definition_only_candidate_artifact_path"])
    assert definition_path.exists()
    definition_text = definition_path.read_text()
    assert "def reviewedCovered : Nat := 0" in definition_text
    assert "source_execution_status:" in definition_text
    assert "authoring_mode: repair_typechecked_semantic_definition_candidate" in (
        definition_text
    )
    assert definition_text.count("import Mathlib.Data.Set.Basic") == 1
    assert definition_text.count("import Mathlib.Data.Fin.Basic") == 1
    assert definition_text.index("import Mathlib.Data.Fin.Basic") < definition_text.index(
        "/-"
    )
    assert rows[0]["required_imports"] == [
        "Mathlib.Data.Set.Basic",
        "Mathlib.Data.Fin.Basic",
    ]
    assert rows[0]["extracted_candidate_imports"] == [
        "Mathlib.Data.Set.Basic",
        "Mathlib.Data.Fin.Basic",
    ]
    repair_tasks = [
        json.loads(line)
        for line in Path(
            materializer_manifest["materialized_lean_repair_tasks_jsonl"]
        ).read_text().splitlines()
    ]
    assert repair_tasks[0]["lean_repair_action"] == "author_exact_definition"
    assert repair_tasks[0]["source_execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED"
    )
    assert repair_tasks[0]["authoring_mode"] == (
        "repair_typechecked_semantic_definition_candidate"
    )
    assert repair_tasks[0]["source_repair_strategy"] == (
        "synthesize_reviewed_definition_from_source_references"
    )
    assert repair_tasks[0]["candidate_repair_feedback"][
        "failure_classification"
    ] == "local_lean_failed_unclassified"
    assert repair_tasks[0]["runtime_queue_status"] == (
        "PENDING_EXACT_SEMANTIC_DEFINITION_MATERIALIZED_LOCAL_LEAN_CHECK"
    )
    assert repair_tasks[0]["semantic_alignment_blockers"]
    assert any(
        "does not reference required source anchor" in blocker
        for blocker in repair_tasks[0]["semantic_alignment_blockers"]
    )
    assert repair_tasks[0]["definition_only_candidate_artifact_path"] == str(
        definition_path
    )
    assert repair_tasks[0]["source_theorem_kernel_verified"] is False

    repair_manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "repair_executor",
        materializer_manifest=Path(materializer_manifest["manifest_path"]),
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )
    assert repair_manifest["n_local_lean_checked"] == 1
    assert repair_manifest["n_local_lean_compiled"] == 1
    assert repair_manifest["n_typechecked_candidate_review_ready"] == 0
    assert repair_manifest["n_typechecked_candidate_semantic_review_blocked"] == 1
    assert repair_manifest["source_materializer_manifest"] == str(
        materializer_manifest["manifest_path"]
    )
    assert repair_manifest["source_theorem_kernel_verified"] is False
    assert repair_manifest["semantic_definition_kernel_verified"] is False


def test_authoring_candidate_materializer_orders_grouped_adapter_dependencies(
    tmp_path: Path,
) -> None:
    candidate_path = tmp_path / "candidate_packets.jsonl"
    group_id = "source_to_bridge_adapter_instantiation_group:split-conformal"
    alpha_total = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionAuthoringCandidatePacket",
        "candidate_packet_id": "candidate:alpha-total",
        "source_prompt_packet_id": "prompt:alpha-total",
        "source_authoring_task_id": "authoring:alpha-total",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "placeholder_symbol": "α_total",
        "candidate_definition_request": {
            "source_to_bridge_adapter_instantiation_group_id": group_id,
            "required_adapter_object_names": ["BadRanks"],
            "available_adapter_object_names": ["BadRanks", "α_total"],
            "missing_required_adapter_object_names": [],
        },
        "definition_design": "Total bad-rank budget depends on BadRanks.",
        "lean_definition_candidate": "def alphaTotalCandidate : Nat := 1",
        "required_imports": [],
        "binder_usage": [{"name": "BadRanks", "how_used": "dependency"}],
        "semantic_alignment_notes": ["dependency ordering is required"],
        "known_gaps": [],
        "forbidden_shortcuts_absent": True,
        "requires_local_lean_check": True,
        "local_definition_lean_checked": False,
        "local_definition_lean_compiled": False,
        "semantic_definition_kernel_verified": False,
        "source_theorem_kernel_verified": False,
        "proof_evidence_status": CANDIDATE_PROOF_EVIDENCE_STATUS,
        "ok": True,
    }
    bad_ranks = {
        **alpha_total,
        "candidate_packet_id": "candidate:bad-ranks",
        "source_prompt_packet_id": "prompt:bad-ranks",
        "source_authoring_task_id": "authoring:bad-ranks",
        "placeholder_symbol": "BadRanks",
        "candidate_definition_request": {
            "source_to_bridge_adapter_instantiation_group_id": group_id,
            "required_adapter_object_names": [],
            "available_adapter_object_names": ["BadRanks", "α_total"],
            "missing_required_adapter_object_names": [],
        },
        "definition_design": "BadRanks is the finite set of bad ranks.",
        "lean_definition_candidate": "def badRanksCandidate : Nat := 0",
        "binder_usage": [{"name": "rank", "how_used": "semantic dependency"}],
    }
    candidate_path.write_text(
        json.dumps(alpha_total, sort_keys=True)
        + "\n"
        + json.dumps(bad_ranks, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_exact_semantic_definition_authoring_candidate_materializer(
        out_dir=tmp_path / "materializer",
        candidate_packets_jsonl=candidate_path,
    )

    rows = [
        json.loads(line)
        for line in Path(manifest["materialization_rows_jsonl"]).read_text().splitlines()
    ]
    assert [row["placeholder_symbol"] for row in rows] == ["BadRanks", "α_total"]
    assert [row["materialization_order_index"] for row in rows] == [1, 2]
    assert rows[1]["required_adapter_object_names"] == ["BadRanks"]
    assert rows[1]["missing_required_adapter_object_names"] == []
    assert manifest["n_source_to_bridge_adapter_materialization_groups"] == 1
    group_order = manifest["source_to_bridge_adapter_group_materialization_orders"][0]
    assert group_order["placeholder_symbols_in_materialization_order"] == [
        "BadRanks",
        "α_total",
    ]
    assert group_order["adapter_dependency_edges"] == [
        {"placeholder_symbol": "BadRanks", "depends_on": []},
        {"placeholder_symbol": "α_total", "depends_on": ["BadRanks"]},
    ]
    repair_tasks = [
        json.loads(line)
        for line in Path(
            manifest["materialized_lean_repair_tasks_jsonl"]
        ).read_text().splitlines()
    ]
    assert [row["placeholder_symbol"] for row in repair_tasks] == [
        "BadRanks",
        "α_total",
    ]
    assert repair_tasks[1]["required_adapter_object_names"] == ["BadRanks"]
    repair_manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "repair_executor",
        materializer_manifest=Path(manifest["manifest_path"]),
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )
    execution_rows = [
        json.loads(line)
        for line in Path(
            repair_manifest["execution_results_jsonl"]
        ).read_text().splitlines()
    ]
    assert [row["placeholder_symbol"] for row in execution_rows] == [
        "BadRanks",
        "α_total",
    ]
    assert [row["materialization_order_index"] for row in execution_rows] == [1, 2]
    assert execution_rows[1]["required_adapter_object_names"] == ["BadRanks"]


def test_authoring_candidate_materializer_blocks_invalid_candidate(
    tmp_path: Path,
) -> None:
    candidate_path = tmp_path / "candidate_packets.jsonl"
    candidate = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionAuthoringCandidatePacket",
        "candidate_packet_id": "candidate:bad",
        "source_prompt_packet_id": "prompt:bad",
        "source_authoring_task_id": "authoring:bad",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "placeholder_symbol": "covered",
        "definition_design": "Bad shortcut.",
        "lean_definition_candidate": "def covered : Prop := True",
        "required_imports": [],
        "binder_usage": [],
        "semantic_alignment_notes": [],
        "known_gaps": [],
        "forbidden_shortcuts_absent": True,
        "requires_local_lean_check": True,
        "local_definition_lean_checked": False,
        "local_definition_lean_compiled": False,
        "semantic_definition_kernel_verified": False,
        "source_theorem_kernel_verified": False,
        "proof_evidence_status": CANDIDATE_PROOF_EVIDENCE_STATUS,
        "ok": True,
    }
    candidate_path.write_text(
        json.dumps(candidate, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_exact_semantic_definition_authoring_candidate_materializer(
        out_dir=tmp_path / "materializer",
        candidate_packets_jsonl=candidate_path,
    )

    assert manifest["n_candidate_packets"] == 1
    assert manifest["n_materialized_definition_only_candidates"] == 0
    assert manifest["n_materialized_lean_repair_tasks"] == 0
    assert manifest["n_blocked_candidates"] == 1
    rows = [
        json.loads(line)
        for line in Path(manifest["materialization_rows_jsonl"]).read_text().splitlines()
    ]
    assert rows[0]["materialization_status"] == (
        "EXACT_SEMANTIC_DEFINITION_CANDIDATE_MATERIALIZATION_BLOCKED"
    )
    assert "forbidden shortcut" in rows[0]["validation_errors"][0]
    assert rows[0]["definition_only_candidate_artifact_path"] == ""
    repair_tasks = Path(manifest["materialized_lean_repair_tasks_jsonl"]).read_text()
    assert repair_tasks == ""


def test_authoring_worker_cli_reports_live_and_static_attempts(
    tmp_path: Path,
    capsys,
) -> None:
    tasks_path = tmp_path / "authoring_tasks.jsonl"
    _write_authoring_tasks(tasks_path)
    static_response = tmp_path / "static_response.json"
    static_response.write_text(
        json.dumps(_valid_authoring_response(), sort_keys=True),
        encoding="utf-8",
    )

    code = main(
        [
            "source-theorem-exact-semantic-definition-authoring-worker",
            "--authoring-tasks-jsonl",
            str(tasks_path),
            "--provider",
            "static",
            "--static-response-file",
            str(static_response),
            "--out",
            str(tmp_path / "authoring_worker_cli"),
        ]
    )

    captured = capsys.readouterr().out
    assert code == 0
    assert "provider=static" in captured
    assert "backend_provider=static" in captured
    assert "llm_attempted=1" in captured
    assert "live_llm_attempted=0" in captured
    assert "static_or_fixture_llm_attempted=1" in captured
