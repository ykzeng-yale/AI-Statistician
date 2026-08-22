from __future__ import annotations

import json
from copy import deepcopy

from ai_statistician.implementation_metric_handoff import (
    accepted_implementation_interface_handoff_errors,
    build_accepted_implementation_interface_handoff,
)
from ai_statistician.fingerprint import stable_hash


def _accepted_algorithm_handoff() -> dict[str, object]:
    interface_contract = {
        "request_fields": [
            {
                "name": "observations",
                "meaning": "sample used by the candidate estimator",
                "binding": "per_replicate_data",
            }
        ],
        "response_fields": [
            {
                "name": "estimate",
                "meaning": "estimate of the theory-owned target",
                "normalization": "unscaled finite-sample estimate",
                "sample_size_order": "constant output dimension",
                "derivation_ref": "derivation:estimate",
            }
        ],
    }
    interface_contract_id = (
        "estimator_interface_contract:"
        + stable_hash(interface_contract)[:20]
    )
    return {
        "handoff_id": "accepted_algorithm_handoff:source",
        "question_id": "question:domain-neutral",
        "theory_packet_id": "theory:domain-neutral",
        "algorithm_sandbox_manifest_id": "algorithm-manifest:1",
        "algorithm_sandbox_manifest_hash": "manifest-hash",
        "semantic_review_execution_id": "review-execution:1",
        "semantic_review_packet_id": "review-packet:1",
        "semantic_review_packet_hash": "review-packet-hash",
        "exact_algorithm_artifacts": [
            {
                "estimator_id": "candidate-estimator",
                "language": "python",
                "dependencies": ["numpy"],
                "exact_source_code": "SOURCE_SENTINEL = 731",
                "exact_source_hash": "source-hash",
                "exact_smoke_result": {"score": "RESULT_SENTINEL_947"},
                "exact_smoke_result_hash": "result-hash",
                "estimator_interface_contract_id": interface_contract_id,
                "estimator_interface_contract": interface_contract,
                "estimator_interface_contract_authority": {
                    "owner_agent": "TheoryDeveloper",
                    "source_theory_packet_id": "theory:domain-neutral",
                    "source_theory_packet_hash": "theory-hash",
                    "source_estimator_ref": "theory#/estimator_specs/0",
                    "transport_status": "RUNTIME_BOUND_FROM_THEORY",
                },
            }
        ],
    }


def test_interface_handoff_excludes_source_and_execution_results() -> None:
    source_handoff = _accepted_algorithm_handoff()
    source_contract_id = source_handoff["exact_algorithm_artifacts"][0][
        "estimator_interface_contract_id"
    ]
    handoff = build_accepted_implementation_interface_handoff(source_handoff)

    assert accepted_implementation_interface_handoff_errors(
        handoff,
        question_id="question:domain-neutral",
        theory_packet_id="theory:domain-neutral",
    ) == []
    serialized = json.dumps(handoff, sort_keys=True)
    assert "SOURCE_SENTINEL" not in serialized
    assert "RESULT_SENTINEL" not in serialized
    assert "exact_source_code" not in serialized
    assert "exact_smoke_result" not in serialized
    assert handoff["exact_source_included"] is False
    assert handoff["execution_results_included"] is False
    assert handoff["implementation_interfaces"] == [
        {
            "estimator_id": "candidate-estimator",
            "language": "python",
            "dependencies": ["numpy"],
            "exact_source_hash": "source-hash",
            "source_estimator_interface_contract_id": source_contract_id,
            "estimator_interface_contract_id": (
                handoff["implementation_interfaces"][0][
                    "estimator_interface_contract_id"
                ]
            ),
            "estimator_interface_contract": {
                "request_fields": [
                    {
                        "name": "observations",
                        "meaning": "sample used by the candidate estimator",
                        "binding": "per_replicate_data",
                    }
                ],
                "response_fields": [
                    {
                        "name": "estimate",
                        "meaning": "estimate of the theory-owned target",
                        "normalization": "unscaled finite-sample estimate",
                        "derivation_ref": "derivation:estimate",
                    }
                ],
            },
            "estimator_interface_contract_authority": {
                "owner_agent": "TheoryDeveloper",
                "source_theory_packet_id": "theory:domain-neutral",
                "source_theory_packet_hash": "theory-hash",
                "source_estimator_ref": "theory#/estimator_specs/0",
                "transport_status": "RUNTIME_BOUND_FROM_THEORY",
            },
        }
    ]
    assert source_contract_id != handoff["implementation_interfaces"][0][
        "estimator_interface_contract_id"
    ]
    assert "sample_size_order" not in serialized


def test_interface_handoff_rejects_result_or_source_injection() -> None:
    handoff = build_accepted_implementation_interface_handoff(
        _accepted_algorithm_handoff()
    )
    tampered = deepcopy(handoff)
    tampered["implementation_interfaces"][0]["result"] = {"score": 0.9}

    errors = accepted_implementation_interface_handoff_errors(
        tampered,
        question_id="question:domain-neutral",
        theory_packet_id="theory:domain-neutral",
    )

    assert any("forbidden source/result fields" in error for error in errors)
    assert any("identity hash mismatch" in error for error in errors)


def test_interface_handoff_rejects_renamed_result_fields_after_rehash() -> None:
    handoff = build_accepted_implementation_interface_handoff(
        _accepted_algorithm_handoff()
    )
    tampered = deepcopy(handoff)
    tampered["implementation_interfaces"][0]["observed_score"] = 0.9
    tampered_without_id = deepcopy(tampered)
    tampered_without_id.pop("handoff_id")
    tampered["handoff_id"] = (
        "accepted_implementation_interface_handoff:"
        + stable_hash(tampered_without_id)[:20]
    )

    errors = accepted_implementation_interface_handoff_errors(
        tampered,
        question_id="question:domain-neutral",
        theory_packet_id="theory:domain-neutral",
    )

    assert any("row 0 has unexpected fields" in error for error in errors)


def test_interface_handoff_rejects_rehashed_evidence_boundary_tampering() -> None:
    handoff = build_accepted_implementation_interface_handoff(
        _accepted_algorithm_handoff()
    )
    tampered = deepcopy(handoff)
    tampered["proof_evidence_status"] = "EMPIRICAL_ACCEPTED"
    tampered["boundary"] = "This artifact authorizes acceptance."
    tampered_without_id = deepcopy(tampered)
    tampered_without_id.pop("handoff_id")
    tampered["handoff_id"] = (
        "accepted_implementation_interface_handoff:"
        + stable_hash(tampered_without_id)[:20]
    )

    errors = accepted_implementation_interface_handoff_errors(
        tampered,
        question_id="question:domain-neutral",
        theory_packet_id="theory:domain-neutral",
    )

    assert "accepted implementation interface proof evidence status mismatch" in errors
    assert "accepted implementation interface boundary mismatch" in errors


def test_interface_handoff_rejects_stale_question_or_theory_lineage() -> None:
    handoff = build_accepted_implementation_interface_handoff(
        _accepted_algorithm_handoff()
    )

    assert "accepted implementation interface question mismatch" in (
        accepted_implementation_interface_handoff_errors(
            handoff,
            question_id="question:other",
            theory_packet_id="theory:domain-neutral",
        )
    )
    assert "accepted implementation interface theory mismatch" in (
        accepted_implementation_interface_handoff_errors(
            handoff,
            question_id="question:domain-neutral",
            theory_packet_id="theory:other",
        )
    )


def test_interface_handoff_rejects_tampered_contract_identity() -> None:
    handoff = build_accepted_implementation_interface_handoff(
        _accepted_algorithm_handoff()
    )
    tampered = deepcopy(handoff)
    tampered["implementation_interfaces"][0][
        "estimator_interface_contract_id"
    ] = "estimator_interface_contract:tampered"

    errors = accepted_implementation_interface_handoff_errors(
        tampered,
        question_id="question:domain-neutral",
        theory_packet_id="theory:domain-neutral",
    )

    assert any("contract identity hash mismatch" in error for error in errors)


def test_interface_handoff_rejects_non_theory_owned_or_extended_abi() -> None:
    handoff = build_accepted_implementation_interface_handoff(
        _accepted_algorithm_handoff()
    )
    tampered = deepcopy(handoff)
    interface = tampered["implementation_interfaces"][0]
    interface["estimator_interface_contract_authority"]["owner_agent"] = (
        "AlgorithmEngineer"
    )
    interface["estimator_interface_contract"]["observed_result"] = 0.99
    interface["estimator_interface_contract_id"] = (
        "estimator_interface_contract:"
        + stable_hash(interface["estimator_interface_contract"])[:20]
    )
    tampered_without_id = deepcopy(tampered)
    tampered_without_id.pop("handoff_id")
    tampered["handoff_id"] = (
        "accepted_implementation_interface_handoff:"
        + stable_hash(tampered_without_id)[:20]
    )

    errors = accepted_implementation_interface_handoff_errors(
        tampered,
        question_id="question:domain-neutral",
        theory_packet_id="theory:domain-neutral",
    )

    assert any("unexpected fields" in error for error in errors)
    assert any("TheoryDeveloper-owned ABI" in error for error in errors)
