from __future__ import annotations

import json
from pathlib import Path

from ai_statistician.cli import main
from ai_statistician.source_theorem_exact_semantic_definition_proofengineer_bridge import (
    resolve_source_theorem_exact_semantic_definition_review_packets_path,
    run_source_theorem_exact_semantic_definition_proofengineer_bridge,
)


def _write_review_packets(path: Path) -> None:
    rows = [
        {
            "schema_version": 1,
            "artifact_kind": (
                "RuntimeSourceTheoremExactSemanticDefinitionClosureReviewPacket"
            ),
            "review_packet_id": "review:exchangeable",
            "source_definition_closure_work_order_id": "closure:exchangeable",
            "source_lookup_id": "lookup:exchangeable",
            "question_id": "conformal_prediction_coverage",
            "question_title": "Split conformal prediction interval coverage",
            "target_theorem_name": "split_conformal_coverage",
            "placeholder_symbol": "Exchangeable",
            "lookup_status": "CANDIDATE_SOURCE_REFERENCES_FOUND",
            "candidate_source_declarations": [],
            "candidate_source_references": [
                {
                    "candidate_kind": "lean_source_text_match",
                    "path": "StatInference/Conformal/Exchangeability.lean",
                    "line": 12,
                    "snippet": "finite exchangeability handoff",
                }
            ],
            "definition_contract": {
                "semantic_intent": "finite permutation-invariant joint law",
                "forbidden_shortcuts": ["do not define Exchangeable as True"],
            },
            "semantic_alignment_blockers": [
                "pairwise order-probability symmetry is too weak"
            ],
            "source_theorem_exact_semantic_definition_typechecked_candidate": {
                "definition_only_candidate_artifact_path": (
                    "runs/candidate_artifacts/exchangeable_defs_only.lean"
                ),
                "local_definition_lean_compiled": True,
                "semantic_definition_typecheck_evidence_status": (
                    "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
                ),
            },
            "definition_only_candidate_artifact_path": (
                "runs/candidate_artifacts/exchangeable_defs_only.lean"
            ),
            "candidate_lean_project_hint": "/tmp/lean-practice",
            "candidate_artifact_path": "runs/candidate_artifacts/exchangeable_full.lean",
            "local_definition_lean_checked": True,
            "local_definition_lean_compiled": True,
            "semantic_definition_typecheck_evidence_status": (
                "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
            ),
            "required_next_checks": [
                "write or import the exact Lean definition that replaces the placeholder"
            ],
            "target_behavior": (
                "Turn the closure work order into a reviewed exact Lean definition."
            ),
            "proof_evidence_status": (
                "DEFINITION_CLOSURE_REVIEW_PACKET_NOT_PROOF_EVIDENCE"
            ),
        },
        {
            "schema_version": 1,
            "artifact_kind": (
                "RuntimeSourceTheoremExactSemanticDefinitionClosureReviewPacket"
            ),
            "review_packet_id": "review:orderStat",
            "source_definition_closure_work_order_id": "closure:orderStat",
            "source_lookup_id": "lookup:orderStat",
            "question_id": "conformal_prediction_coverage",
            "question_title": "Split conformal prediction interval coverage",
            "target_theorem_name": "split_conformal_coverage",
            "placeholder_symbol": "orderStat",
            "lookup_status": "CANDIDATE_SOURCE_DECLARATIONS_FOUND",
            "candidate_source_declarations": [
                {
                    "candidate_kind": "lean_declaration",
                    "path": "StatInference/Conformal/Quantile.lean",
                    "line": 45,
                    "snippet": "def reviewedOrderStat",
                }
            ],
            "candidate_source_references": [],
            "definition_contract": {
                "semantic_intent": "finite conformal order statistic",
                "forbidden_shortcuts": [
                    "do not define orderStat as a constant unrelated to scores"
                ],
            },
            "semantic_alignment_blockers": [
                "draft finite maximum ignores rank k"
            ],
            "required_next_checks": [
                "review candidate source declarations against theorem semantics"
            ],
            "target_behavior": (
                "Turn the closure work order into a reviewed exact Lean definition."
            ),
            "proof_evidence_status": (
                "DEFINITION_CLOSURE_REVIEW_PACKET_NOT_PROOF_EVIDENCE"
            ),
        },
    ]
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_exact_semantic_definition_proofengineer_bridge_exports_repair_packets(
    tmp_path: Path,
) -> None:
    review_packets = tmp_path / "review_packets.jsonl"
    _write_review_packets(review_packets)

    manifest = run_source_theorem_exact_semantic_definition_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        review_packets_jsonl=review_packets,
        question_id="conformal_prediction_coverage",
    )

    assert manifest["n_review_packets"] == 2
    assert manifest["n_repair_packets"] == 2
    assert manifest["n_lean_repair_tasks"] == 2
    assert manifest["n_import_candidate_declaration_packets"] == 1
    assert manifest["n_lean_import_candidate_tasks"] == 1
    assert manifest["n_lean_synthesize_definition_tasks"] == 0
    assert manifest["n_synthesize_from_references_packets"] == 0
    assert manifest["n_review_typechecked_candidate_packets"] == 1
    assert manifest["n_lean_review_typechecked_candidate_tasks"] == 1
    assert manifest["lean_repair_task_proof_evidence_status"] == (
        "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
    )
    assert manifest["proof_evidence_status"] == (
        "EXACT_SEMANTIC_DEFINITION_PROOFENGINEER_BRIDGE_NOT_PROOF_EVIDENCE"
    )
    packets = [
        json.loads(line)
        for line in Path(manifest["repair_packets_jsonl"]).read_text().splitlines()
    ]
    by_symbol = {row["placeholder_symbol"]: row for row in packets}
    assert by_symbol["Exchangeable"]["repair_strategy"] == (
        "review_typechecked_exact_definition_candidate"
    )
    assert by_symbol["orderStat"]["repair_strategy"] == (
        "review_import_candidate_source_declaration"
    )
    assert by_symbol["orderStat"]["local_lean_required_before_proof_body"] is True
    assert by_symbol["orderStat"]["source_theorem_kernel_evidence_eligible"] is False
    assert by_symbol["orderStat"]["proof_evidence_status"] == (
        "EXACT_SEMANTIC_DEFINITION_PROOFENGINEER_BRIDGE_NOT_PROOF_EVIDENCE"
    )
    assert by_symbol["Exchangeable"]["definition_only_candidate_artifact_path"] == (
        "runs/candidate_artifacts/exchangeable_defs_only.lean"
    )
    assert by_symbol["Exchangeable"]["candidate_lean_project_hint"] == (
        "/tmp/lean-practice"
    )
    assert by_symbol["Exchangeable"]["local_definition_lean_compiled"] is True
    assert by_symbol["Exchangeable"][
        "semantic_definition_typecheck_evidence_status"
    ] == "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
    lean_tasks = [
        json.loads(line)
        for line in Path(manifest["lean_repair_tasks_jsonl"]).read_text().splitlines()
    ]
    lean_tasks_by_symbol = {row["placeholder_symbol"]: row for row in lean_tasks}
    assert lean_tasks_by_symbol["Exchangeable"]["lean_repair_action"] == (
        "review_typechecked_exact_definition_candidate"
    )
    assert lean_tasks_by_symbol["Exchangeable"][
        "definition_only_candidate_artifact_path"
    ] == "runs/candidate_artifacts/exchangeable_defs_only.lean"
    assert lean_tasks_by_symbol["Exchangeable"]["candidate_lean_project_hint"] == (
        "/tmp/lean-practice"
    )
    assert lean_tasks_by_symbol["Exchangeable"][
        "local_definition_lean_compiled"
    ] is True
    assert lean_tasks_by_symbol["Exchangeable"][
        "semantic_definition_typecheck_evidence_status"
    ] == "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
    assert lean_tasks_by_symbol["orderStat"]["lean_repair_action"] == (
        "review_import_source_declaration"
    )
    assert lean_tasks_by_symbol["orderStat"]["local_lean_attempted"] is False
    assert lean_tasks_by_symbol["orderStat"]["local_lean_kernel_verified"] is False
    candidate_import = lean_tasks_by_symbol["orderStat"]["candidate_import_declarations"][0]
    assert candidate_import["candidate_kind"] == "lean_declaration"
    assert candidate_import["line"] == 45
    assert candidate_import["path"] == "StatInference/Conformal/Quantile.lean"
    assert candidate_import["snippet"] == "def reviewedOrderStat"
    assert candidate_import["semantic_import_candidate_allowed"] is True
    assert lean_tasks_by_symbol["orderStat"]["proof_evidence_status"] == (
        "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
    )
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    assert {row["learning_task"] for row in learning_rows} == {
        "source_theorem_exact_semantic_definition_proofengineer_bridge"
    }
    assert {
        row["input_summary"]["repair_strategy"] for row in learning_rows
    } == {
        "review_typechecked_exact_definition_candidate",
        "review_import_candidate_source_declaration",
    }
    exchangeable_learning = next(
        row for row in learning_rows if row["placeholder_symbol"] == "Exchangeable"
    )
    assert exchangeable_learning["input_summary"][
        "definition_only_candidate_artifact_path"
    ] == "runs/candidate_artifacts/exchangeable_defs_only.lean"
    assert exchangeable_learning["input_summary"]["candidate_lean_project_hint"] == (
        "/tmp/lean-practice"
    )
    assert exchangeable_learning["input_summary"][
        "local_definition_lean_compiled"
    ] is True
    assert all(
        row["proof_evidence_status"]
        == "EXACT_SEMANTIC_DEFINITION_PROOFENGINEER_BRIDGE_NOT_PROOF_EVIDENCE"
        for row in learning_rows
    )


def test_exact_semantic_definition_bridge_ignores_placeholder_only_candidate_shell(
    tmp_path: Path,
) -> None:
    review_packets = tmp_path / "review_packets.jsonl"
    review_packet = {
        "schema_version": 1,
        "artifact_kind": (
            "RuntimeSourceTheoremExactSemanticDefinitionClosureReviewPacket"
        ),
        "review_packet_id": "review:good_rank_event",
        "source_definition_closure_work_order_id": "closure:good_rank_event",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "placeholder_symbol": "good_rank_event",
        "lookup_status": "NO_REVIEWED_FORMAL_DEFINITION_FOUND",
        "candidate_source_declarations": [],
        "candidate_source_references": [],
        "source_theorem_exact_semantic_definition_typechecked_candidate": {
            "local_definition_lean_checked": False,
            "local_definition_lean_compiled": False,
            "placeholder_symbol": "good_rank_event",
            "target_theorem_name": "split_conformal_coverage",
        },
        "definition_contract": {
            "semantic_intent": "source good-rank event used by the coverage proof",
        },
        "proof_evidence_status": (
            "DEFINITION_CLOSURE_REVIEW_PACKET_NOT_PROOF_EVIDENCE"
        ),
    }
    review_packets.write_text(json.dumps(review_packet) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        review_packets_jsonl=review_packets,
        question_id="conformal_prediction_coverage",
    )

    assert manifest["n_review_typechecked_candidate_packets"] == 0
    assert manifest["n_no_source_hit_packets"] == 1
    packets = [
        json.loads(line)
        for line in Path(manifest["repair_packets_jsonl"]).read_text().splitlines()
    ]
    packet = packets[0]
    assert packet["repair_strategy"] == "author_reviewed_definition_from_contract"
    assert packet["definition_only_candidate_artifact_path"] == ""
    assert packet["local_definition_lean_compiled"] is False
    tasks = [
        json.loads(line)
        for line in Path(manifest["lean_repair_tasks_jsonl"]).read_text().splitlines()
    ]
    assert tasks[0]["lean_repair_action"] == "author_exact_definition"


def test_exact_semantic_definition_proofengineer_bridge_resolves_lookup_manifest(
    tmp_path: Path,
) -> None:
    review_packets = tmp_path / "review_packets.jsonl"
    lookup_manifest = tmp_path / "lookup_manifest.json"
    _write_review_packets(review_packets)
    lookup_manifest.write_text(
        json.dumps(
            {
                "definition_closure_review_packets_jsonl": str(review_packets),
            }
        ),
        encoding="utf-8",
    )

    manifest = run_source_theorem_exact_semantic_definition_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        lookup_manifest=lookup_manifest,
    )

    assert manifest["source_review_packets_jsonl"] == str(review_packets)
    assert manifest["n_repair_packets"] == 2


def test_exact_semantic_definition_proofengineer_bridge_consumes_typechecked_review_packet(
    tmp_path: Path,
) -> None:
    review_packets = tmp_path / "typechecked_review_packets.jsonl"
    review_packet = {
        "schema_version": 1,
        "artifact_kind": (
            "SourceTheoremExactSemanticDefinitionTypecheckedCandidateReviewPacket"
        ),
        "review_packet_id": "typechecked-review:covered",
        "source_execution_result_id": "lean-repair-result:covered",
        "source_lean_repair_task_id": "lean-repair-task:covered",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "placeholder_symbol": "covered",
        "definition_only_candidate_artifact_path": (
            "runs/candidate_artifacts/covered_defs_only.lean"
        ),
        "candidate_artifact_path": "runs/candidate_artifacts/covered_full.lean",
        "local_definition_lean_checked": True,
        "local_definition_lean_compiled": True,
        "semantic_definition_typecheck_evidence_status": (
            "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
        ),
        "source_theorem_exact_semantic_definition_typechecked_candidate": {
            "definition_only_candidate_artifact_path": (
                "runs/candidate_artifacts/covered_defs_only.lean"
            ),
            "candidate_artifact_path": "runs/candidate_artifacts/covered_full.lean",
            "local_definition_lean_checked": True,
            "local_definition_lean_compiled": True,
            "semantic_definition_typecheck_evidence_status": (
                "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
            ),
        },
        "candidate_definition_request": {
            "placeholder_symbol": "covered",
            "semantic_intent": "exact source coverage event tied to hC",
        },
        "semantic_review_required_before_proof_body": True,
        "source_theorem_ready_for_exact_proof_body": False,
        "source_theorem_kernel_verified": False,
        "proof_evidence_status": (
            "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW_NOT_PROOF_EVIDENCE"
        ),
    }
    review_packets.write_text(json.dumps(review_packet) + "\n", encoding="utf-8")

    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    runtime_manifest = runtime_dir / "research_agent_runtime_manifest.json"
    runtime_manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifacts": {
                    "runtime_source_theorem_exact_semantic_definition_materialized_typechecked_candidate_review_packets_jsonl": (
                        str(review_packets)
                    )
                },
            }
        ),
        encoding="utf-8",
    )

    resolved = resolve_source_theorem_exact_semantic_definition_review_packets_path(
        runtime_dir=runtime_dir,
    )
    assert resolved == review_packets

    manifest = run_source_theorem_exact_semantic_definition_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        runtime_dir=runtime_dir,
        question_id="conformal_prediction_coverage",
    )

    assert manifest["n_review_packets"] == 1
    assert manifest["n_review_typechecked_candidate_packets"] == 1
    assert manifest["n_lean_review_typechecked_candidate_tasks"] == 1
    packets = [
        json.loads(line)
        for line in Path(manifest["repair_packets_jsonl"]).read_text().splitlines()
    ]
    packet = packets[0]
    assert packet["repair_strategy"] == "review_typechecked_exact_definition_candidate"
    assert packet["placeholder_symbol"] == "covered"
    assert packet["definition_only_candidate_artifact_path"] == (
        "runs/candidate_artifacts/covered_defs_only.lean"
    )
    assert packet["local_definition_lean_compiled"] is True
    assert packet["source_theorem_kernel_evidence_eligible"] is False
    tasks = [
        json.loads(line)
        for line in Path(manifest["lean_repair_tasks_jsonl"]).read_text().splitlines()
    ]
    task = tasks[0]
    assert task["lean_repair_action"] == "review_typechecked_exact_definition_candidate"
    assert task["definition_only_candidate_artifact_path"] == (
        "runs/candidate_artifacts/covered_defs_only.lean"
    )
    assert task["local_lean_kernel_verified"] is False
    assert task["proof_evidence_status"] == (
        "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
    )


def test_exact_semantic_definition_proofengineer_bridge_consumes_repair_queue(
    tmp_path: Path,
) -> None:
    repair_queue = tmp_path / "semantic_definition_repair_queue.jsonl"
    repair_queue.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "RuntimeSourceTheoremExactSemanticDefinitionRepairQueueRow"
                ),
                "repair_queue_id": (
                    "source_theorem_exact_semantic_definition_repair_queue:orderStat"
                ),
                "source_review_packet_id": "review:orderStat",
                "source_definition_closure_work_order_id": "closure:orderStat",
                "question_id": "conformal_prediction_coverage",
                "target_theorem_name": "split_conformal_coverage",
                "placeholder_symbol": "orderStat",
                "definition_contract": {
                    "semantic_intent": "finite conformal order statistic"
                },
                "candidate_artifact_path": "runs/candidate_artifacts/full.lean",
                "synthesized_candidate_artifact_path": (
                    "runs/candidate_artifacts/full_repaired.lean"
                ),
                "definition_only_candidate_artifact_path": (
                    "runs/candidate_artifacts/defs_only.lean"
                ),
                "local_definition_lean_checked": True,
                "local_definition_lean_compiled": True,
                "semantic_definition_typecheck_evidence_status": (
                    "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
                ),
                "source_theorem_exact_semantic_definition_typechecked_candidate": {
                    "definition_only_candidate_artifact_path": (
                        "runs/candidate_artifacts/defs_only.lean"
                    ),
                    "candidate_artifact_path": "runs/candidate_artifacts/full.lean",
                    "local_definition_lean_checked": True,
                    "local_definition_lean_compiled": True,
                    "semantic_definition_typecheck_evidence_status": (
                        "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
                    ),
                },
                "semantic_alignment_blockers": [
                    "draft finite maximum ignores rank k"
                ],
                "proof_evidence_status": (
                    "SEMANTIC_DEFINITION_REPAIR_QUEUE_NOT_PROOF_EVIDENCE"
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_exact_semantic_definition_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        review_packets_jsonl=repair_queue,
        question_id="conformal_prediction_coverage",
    )

    assert manifest["n_repair_packets"] == 1
    assert manifest["n_lean_repair_tasks"] == 1
    packets = [
        json.loads(line)
        for line in Path(manifest["repair_packets_jsonl"]).read_text().splitlines()
    ]
    packet = packets[0]
    assert packet["source_review_packet_id"] == "review:orderStat"
    assert packet["source_repair_queue_id"] == (
        "source_theorem_exact_semantic_definition_repair_queue:orderStat"
    )
    assert packet["repair_strategy"] == "author_reviewed_definition_from_contract"
    assert packet["definition_only_candidate_artifact_path"] == (
        "runs/candidate_artifacts/defs_only.lean"
    )
    assert packet["local_definition_lean_compiled"] is True
    assert packet["semantic_definition_typecheck_evidence_status"] == (
        "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
    )
    tasks = [
        json.loads(line)
        for line in Path(manifest["lean_repair_tasks_jsonl"]).read_text().splitlines()
    ]
    task = tasks[0]
    assert task["source_repair_queue_id"] == (
        "source_theorem_exact_semantic_definition_repair_queue:orderStat"
    )
    assert task["lean_repair_action"] == "author_exact_definition"
    assert task["definition_only_candidate_artifact_path"] == (
        "runs/candidate_artifacts/defs_only.lean"
    )
    assert task["local_definition_lean_compiled"] is True
    assert task["proof_evidence_status"] == (
        "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
    )


def test_exact_semantic_definition_proofengineer_bridge_cli(
    tmp_path: Path,
) -> None:
    review_packets = tmp_path / "review_packets.jsonl"
    out_dir = tmp_path / "bridge"
    _write_review_packets(review_packets)

    rc = main(
        [
            "source-theorem-exact-semantic-definition-proofengineer-bridge",
            "--review-packets-jsonl",
            str(review_packets),
            "--out",
            str(out_dir),
        ]
    )

    assert rc == 0
    manifest_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_proofengineer_bridge_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["n_repair_packets"] == 2
    assert manifest["n_lean_repair_tasks"] == 2
    assert Path(manifest["runtime_learning_rows_jsonl"]).exists()
    assert Path(manifest["lean_repair_tasks_jsonl"]).exists()
