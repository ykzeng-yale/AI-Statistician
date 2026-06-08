from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.cli import main
from ai_statistician.formalization_gap_planner_prover_adapter_feedback_adapter import (
    export_formalization_gap_planner_prover_adapter_feedback_responses,
)
from ai_statistician.formalization_gap_planner_refinement_evidence import (
    export_formalization_gap_planner_refinement_evidence,
)


def test_prover_adapter_feedback_feeds_refinement_evidence() -> None:
    root = Path("runs/test_formalization_gap_planner_prover_adapter_feedback_adapter")
    queue_dir = root / "queue"
    contract_dir = root / "contract"
    adapter_dir = root / "adapter"
    evidence_dir = root / "evidence"
    shutil.rmtree(root, ignore_errors=True)
    queue_dir.mkdir(parents=True, exist_ok=True)
    contract_dir.mkdir(parents=True, exist_ok=True)
    _write_queue(queue_dir)
    _write_validation_jsonl(
        contract_dir / "formalization_gap_planner_prover_adapter_response_validation.jsonl"
    )

    payload = export_formalization_gap_planner_prover_adapter_feedback_responses(
        queue_dir,
        adapter_dir,
        formalization_gap_planner_prover_adapter_contract_dir=contract_dir,
    )

    assert payload["all_ok"]
    assert payload["n_generated_feedback_responses"] == 1
    assert payload["n_route_revision_recommended"] == 1
    assert payload["n_response_schema_valid"] == 1
    assert payload["n_response_schema_invalid"] == 0
    assert payload["by_mapping_status"] == {"needs_library_grounding": 1}
    response = payload["responses"][0]
    assert response["attempt_status"] == "prover_adapter_needs_library_grounding"
    assert response["prover_attempt_class"] == "target_prover_mapping_gap"
    assert response["target_prover_family"] == "rocq"
    assert response["revised_delta_primitives"] == ("rank_uniformity",)
    assert any(
        "missing finite rank uniformity lemma" in item
        for item in response["residual_goals"]
    )
    assert (
        adapter_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl"
    ).exists()

    evidence_payload = export_formalization_gap_planner_refinement_evidence(
        queue_dir,
        evidence_dir,
        response_jsonl=(
            adapter_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl"
        ),
    )
    assert evidence_payload["all_ok"]
    assert evidence_payload["n_route_revision_proposals"] == 1
    assert evidence_payload["by_prover_attempt_status"] == {
        "prover_adapter_needs_library_grounding": 1
    }
    proposal = evidence_payload["route_revision_proposals"][0]
    assert proposal["target_prover_family"] == "rocq"
    assert proposal["revised_delta_primitives"] == ("rank_uniformity",)


def test_prover_adapter_feedback_cli_reads_cross_prover_matrix() -> None:
    root = Path("runs/test_formalization_gap_planner_prover_adapter_feedback_cli")
    queue_dir = root / "queue"
    cross_dir = root / "cross"
    out_dir = root / "out"
    shutil.rmtree(root, ignore_errors=True)
    queue_dir.mkdir(parents=True, exist_ok=True)
    cross_dir.mkdir(parents=True, exist_ok=True)
    _write_queue(queue_dir)
    _write_validation_jsonl(
        cross_dir / "formalization_gap_planner_cross_prover_response_validation.jsonl"
    )

    rc = main(
        [
            "formalization-gap-planner-prover-adapter-feedback",
            "--formalization-gap-planner-refinement-queue-dir",
            str(queue_dir),
            "--formalization-gap-planner-cross-prover-matrix-audit-dir",
            str(cross_dir),
            "--target-prover-family",
            "rocq",
            "--out",
            str(out_dir),
        ]
    )

    assert rc == 0
    manifest = json.loads(
        (
            out_dir
            / "formalization_gap_planner_prover_adapter_feedback_adapter_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["all_ok"]
    assert manifest["n_generated_feedback_responses"] == 1
    assert manifest["by_target_prover_family"] == {"rocq": 1}
    assert (
        out_dir / "formalization_gap_planner_prover_adapter_feedback_responses.jsonl"
    ).exists()


def test_prover_adapter_feedback_keeps_awaiting_rows_neutral() -> None:
    root = Path("runs/test_formalization_gap_planner_prover_adapter_feedback_awaiting")
    queue_dir = root / "queue"
    contract_dir = root / "contract"
    adapter_dir = root / "adapter"
    shutil.rmtree(root, ignore_errors=True)
    queue_dir.mkdir(parents=True, exist_ok=True)
    contract_dir.mkdir(parents=True, exist_ok=True)
    _write_queue(queue_dir)
    _write_validation_jsonl(
        contract_dir / "formalization_gap_planner_prover_adapter_response_validation.jsonl",
        response_present=False,
        response_contract_ok=False,
        mapping_status="",
        residual_translation_gaps=[],
        acceptance_status="AWAITING_PROVER_ADAPTER_MAPPING",
        semantic_alignment_notes="",
    )

    payload = export_formalization_gap_planner_prover_adapter_feedback_responses(
        queue_dir,
        adapter_dir,
        formalization_gap_planner_prover_adapter_contract_dir=contract_dir,
    )

    assert payload["all_ok"]
    response = payload["responses"][0]
    assert response["attempt_status"] == "awaiting_prover_adapter_mapping"
    assert response["prover_attempt_class"] == "target_prover_mapping_awaiting"
    assert response["route_revision_recommended"] is False
    assert response["route_revision_reasons"] == ()
    assert any("awaiting prover adapter mapping" in item for item in response["residual_goals"])


def _write_queue(queue_dir: Path) -> None:
    rows = [
        {
            "refinement_item_id": "refinement:rocq-rank",
            "goal_plan_id": "goal:rank",
            "route_id": "route:rank",
            "display_name": "rank route",
            "hook_kind": "proof_state_feedback",
            "refinement_stage": "target_prover_adapter_feedback",
            "owner_agent": "target_prover_adapter",
            "target_primitives": ["rank_uniformity"],
            "queries": ["rocq rank_uniformity mapping"],
            "resource_request_ids": ["request:rocq-rank"],
            "resource_ids": ["prover-adapter:rocq"],
            "resource_request_bindings": [
                {
                    "resource_request_id": "request:rocq-rank",
                    "resource_id": "prover-adapter:rocq",
                }
            ],
            "llm_route_planner_hook_trace": {
                "hook_id": "hook:rocq-rank",
                "required_gate": "target-prover adapter feedback before route adoption",
            },
        }
    ]
    (queue_dir / "formalization_gap_planner_refinement_queue_manifest.json").write_text(
        json.dumps({"rows": rows}, indent=2),
        encoding="utf-8",
    )


def _write_validation_jsonl(path: Path, **overrides: object) -> None:
    row = {
        "schema_version": 1,
        "response_validation_id": "validation:rocq-rank",
        "prover_adapter_packet_id": "packet:rocq-rank",
        "goal_plan_id": "goal:rank",
        "route_id": "route:rank",
        "display_name": "rank route",
        "primitive": "rank_uniformity",
        "target_prover_family": "rocq",
        "response_present": True,
        "response_contract_ok": True,
        "mapping_status": "needs_library_grounding",
        "translated_statement": "Theorem rank_uniformity : True.",
        "translated_imports": [],
        "verifier_command": "coqc RankUniformity.v",
        "library_snapshot_ref": "rocq_snapshot",
        "semantic_alignment_notes": "Rocq library lacks rank lemma import",
        "residual_translation_gaps": [
            "missing finite rank uniformity lemma in Rocq library"
        ],
        "kernel_verified_claimed": False,
        "acceptance_status": (
            "PROVER_ADAPTER_MAPPING_RECORDED_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_status": (
            "FORMALIZATION_GAP_PLANNER_PROVER_ADAPTER_CONTRACT_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": (
            "Adapter mapping rows are not theorem proof evidence."
        ),
        "ok": True,
        "errors": [],
    }
    row.update(overrides)
    path.write_text(
        json.dumps(row, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
