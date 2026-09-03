from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import ai_statistician.prover_component_audit as audit_module


def _write_status(root: Path) -> None:
    status_dir = root / "docs"
    status_dir.mkdir(parents=True)
    (status_dir / "main_worker_status.json").write_text(
        json.dumps(
            {
                "validated_code_head": "abcdef12",
                "goal_status": "active",
                "capability_facts": {
                    "trusted_full_task_credit": (
                        "7/113 consumed tasks receive trustworthy capability credit"
                    ),
                    "strict_formal_completion_rate": "0%",
                    "development_panel_exact_lean_closure": "unchanged at 0/2",
                    "strict_formal_boundary": (
                        "The authoritative strict-formal fact is 0/2."
                    ),
                },
                "maturity_estimate": {
                    "fully_gold_covered_research_tasks": "legacy value",
                    "frozen_strict_protocol_completion_rate": "legacy value",
                    "boundary": "legacy value",
                },
            }
        ),
        encoding="utf-8",
    )


def test_live_capability_evidence_is_explicit_and_fail_closed(
    tmp_path: Path,
) -> None:
    missing = audit_module._live_capability_evidence(tmp_path)
    assert missing["status"] == "UNAVAILABLE"
    assert missing["trusted_full_task_credit"] == "unavailable"

    _write_status(tmp_path)
    evidence = audit_module._live_capability_evidence(tmp_path)
    assert evidence == {
        "status": "AVAILABLE",
        "status_path": str(tmp_path / "docs" / "main_worker_status.json"),
        "goal_status": "active",
        "validated_code_head": "abcdef12",
        "trusted_full_task_credit": (
            "7/113 consumed tasks receive trustworthy capability credit"
        ),
        "strict_formal_completion_rate": "0%",
        "development_panel_exact_lean_closure": "unchanged at 0/2",
        "strict_formal_boundary": "The authoritative strict-formal fact is 0/2.",
    }


def test_component_audit_separates_harness_from_live_capability(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _write_status(tmp_path)
    monkeypatch.setattr(
        audit_module, "load_open_research_questions", lambda _path: [object()]
    )
    monkeypatch.setattr(
        audit_module,
        "audit_frontier_coverage",
        lambda **_kwargs: {
            "n_supported": 60,
            "n_questions": 60,
            "n_unsupported": 0,
        },
    )
    monkeypatch.setattr(
        audit_module,
        "build_research_source_inventory",
        lambda: {"n_ok": 35, "n_sources": 35},
    )
    monkeypatch.setattr(
        audit_module,
        "build_autoform_harness_profile",
        lambda: SimpleNamespace(
            exists=True,
            has_statement_extraction=True,
            has_lean_eval=True,
            git_commit="f137da6cc9a6",
        ),
    )
    monkeypatch.setattr(
        audit_module,
        "all_research_algorithm_specs",
        lambda: [SimpleNamespace(registry_status="vetted")],
    )
    monkeypatch.setattr(audit_module, "all_obligations", lambda: [object()])
    monkeypatch.setattr(audit_module, "build_formal_source_index", lambda: [object()])
    monkeypatch.setattr(audit_module, "proof_bank_fingerprint", lambda: "proof")
    monkeypatch.setattr(
        audit_module, "formal_source_index_fingerprint", lambda _rows: "formal"
    )
    monkeypatch.setattr(
        audit_module, "research_source_inventory_fingerprint", lambda: "sources"
    )
    monkeypatch.setattr(
        audit_module, "research_algorithm_registry_fingerprint", lambda: "algorithms"
    )

    payload = audit_module.build_prover_component_audit(root=tmp_path)
    rows = {row["component"]: row for row in payload["rows"]}

    assert payload["schema_version"] == 2
    assert payload["summary"] == {
        "components": 16,
        "ready": 2,
        "harness_ready_live_partial": 1,
        "partial": 14,
        "missing_or_not_trained": 0,
        "honest_goal_complete": False,
        "evidence_boundary": (
            "Component presence and benchmark coverage do not imply live "
            "scientific or theorem-solving capability."
        ),
    }
    assert rows["formal data and frontier benchmarks"]["status"] == (
        "BENCHMARK_SURFACE_ONLY"
    )
    assert rows["simulation/evaluator loop for statistical claims"]["status"] == (
        "HARNESS_READY_LIVE_PARTIAL"
    )
    retrieval = rows["premise retrieval / Lean RAG / formal-source search"]
    assert retrieval["status"] == "PARTIAL_DIRECT_PROOF_STATE"
    assert any(
        "inspect_lean_state" in item for item in retrieval["current_evidence"]
    )
    assert all(
        "No embedding index" not in item for item in retrieval["missing_or_next"]
    )
    assert payload["live_capability_evidence"]["strict_formal_completion_rate"] == (
        "0%"
    )
    report = audit_module._component_audit_markdown(payload)
    assert "Trusted full-task credit: 7/113" in report
    assert "Harness-ready but live-partial components: 1" in report
