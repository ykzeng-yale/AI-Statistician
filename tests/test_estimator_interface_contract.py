from __future__ import annotations

import json
from copy import deepcopy

import pytest

import ai_statistician.research_architect as research_architect_module
from ai_statistician.estimator_interface_contract import (
    estimator_interface_contract_errors,
    frozen_estimator_execution_contract_alignment_errors,
    frozen_estimator_execution_contract_clause_ids,
    frozen_estimator_execution_contract_empirical_claim_ids,
    frozen_estimator_execution_contract_errors,
    frozen_estimator_execution_contract_id,
    normalize_theory_estimator_interface_contracts,
    project_executable_estimator_spec,
)
from ai_statistician.algorithm_engineer_llm import (
    ALGORITHM_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT,
    materialize_algorithm_source_workspace_record,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_agent_runtime import (
    _question_from_payload,
    _question_to_payload,
)
from ai_statistician.research_lab import load_open_research_questions
from ai_statistician.research_schema import (
    OpenResearchQuestion,
    research_question_payload,
)
from ai_statistician.simulation_engineer_llm import (
    SIMULATION_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT,
)


def _frozen_contract() -> dict:
    return {
        "schema_version": 1,
        "estimator_id": "est_example",
        "entrypoint": "run_estimator",
        "request_fields": [
            {
                "clause_id": "request.sample",
                "name": "sample",
                "meaning": "Observed real-valued sample.",
                "json_type": "array[number]",
                "shape": "length n with n >= 2",
                "units": "measurement units",
                "indexing": "observation order",
                "edge_cases": "Reject nonfinite values and n < 2.",
                "binding": "per_replicate_data",
            }
        ],
        "response_fields": [
            {
                "clause_id": "response.estimate",
                "name": "estimate",
                "meaning": "Arithmetic mean of the supplied sample.",
                "json_type": "number",
                "shape": "scalar",
                "units": "measurement units",
                "indexing": "not_applicable",
                "edge_cases": "Must be JSON-finite.",
                "normalization": "sum(sample) / n",
            }
        ],
        "invariants": [
            {
                "clause_id": "invariant.translation",
                "meaning": "Adding c to every observation adds c to estimate.",
            }
        ],
        "empirical_claims": [
            {
                "clause_id": "claim.empirical.mean_behavior",
                "meaning": "A frozen empirical assessment checks the mean behavior with Monte Carlo uncertainty.",
            }
        ],
    }


def test_frozen_estimator_execution_contract_has_stable_public_clauses() -> None:
    contract = _frozen_contract()

    assert frozen_estimator_execution_contract_errors(
        contract,
        label="contract",
        required=True,
    ) == []
    assert frozen_estimator_execution_contract_clause_ids(contract) == {
        "request.sample",
        "response.estimate",
        "invariant.translation",
        "claim.empirical.mean_behavior",
    }
    assert frozen_estimator_execution_contract_empirical_claim_ids(
        contract
    ) == {"claim.empirical.mean_behavior"}
    assert frozen_estimator_execution_contract_id(contract).startswith(
        "frozen_estimator_execution_contract:"
    )


def test_frozen_estimator_execution_contract_rejects_ambiguous_field_semantics() -> None:
    contract = _frozen_contract()
    contract["response_fields"][0]["meaning"] = ""
    contract["response_fields"][0]["clause_id"] = "request.sample"

    errors = frozen_estimator_execution_contract_errors(
        contract,
        label="contract",
        required=True,
    )

    assert "contract response_fields[0] missing meaning" in errors
    assert "contract clause_id values must be unique" in errors


def test_frozen_estimator_execution_contract_rejects_invalid_empirical_claim() -> None:
    contract = _frozen_contract()
    del contract["empirical_claims"][0]["meaning"]

    errors = frozen_estimator_execution_contract_errors(
        contract,
        label="contract",
        required=True,
    )

    assert "contract empirical_claims[0] missing meaning" in errors


def _model_theory_handoff_for_frozen_contract(contract: dict) -> dict:
    return {
        "estimator_specs": [
            {
                "id": contract["estimator_id"],
                "estimator_interface_contract": {
                    "request_fields": [
                        {
                            "name": row["name"],
                            "meaning": row["meaning"],
                            "binding": row["binding"],
                        }
                        for row in contract["request_fields"]
                    ],
                    "response_fields": [
                        {
                            "name": row["name"],
                            "meaning": row["meaning"],
                            "normalization": row["normalization"],
                            "derivation_ref": "C1",
                        }
                        for row in contract["response_fields"]
                    ],
                },
            }
        ]
    }


@pytest.mark.parametrize("field", ["meaning", "normalization", "name"])
def test_frozen_estimator_alignment_preserves_public_semantics(field: str) -> None:
    frozen = _frozen_contract()
    packet = _model_theory_handoff_for_frozen_contract(frozen)

    assert frozen_estimator_execution_contract_alignment_errors(
        packet,
        frozen,
    ) == []

    packet["estimator_specs"][0]["estimator_interface_contract"][
        "response_fields"
    ][0][field] = "A different model-authored statistical meaning."
    errors = frozen_estimator_execution_contract_alignment_errors(packet, frozen)
    assert len(errors) == 1
    assert "response_fields must match the frozen executable ABI" in errors[0]


def test_frozen_estimator_alignment_rejects_model_renamed_identity() -> None:
    frozen = _frozen_contract()
    packet = _model_theory_handoff_for_frozen_contract(frozen)
    packet["estimator_specs"][0]["id"] = "est.renamed"

    errors = frozen_estimator_execution_contract_alignment_errors(packet, frozen)

    assert errors == [
        "theory packet estimator_specs must contain exact frozen estimator id "
        "'est_example'; observed: est.renamed"
    ]


def test_frozen_estimator_alignment_rejects_field_or_binding_drift() -> None:
    frozen = _frozen_contract()
    frozen["request_fields"].append(
        {
            **frozen["request_fields"][0],
            "clause_id": "request.scale",
            "name": "scale",
            "binding": "fixed_before_all_replicates",
        }
    )
    packet = _model_theory_handoff_for_frozen_contract(frozen)
    request_fields = packet["estimator_specs"][0][
        "estimator_interface_contract"
    ]["request_fields"]
    request_fields.reverse()
    request_fields[0]["binding"] = "runtime_control"

    errors = frozen_estimator_execution_contract_alignment_errors(packet, frozen)

    assert len(errors) == 1
    assert "request_fields must match the frozen executable ABI" in errors[0]
    assert "name, meaning, binding and order" in errors[0]


def test_frozen_estimator_reference_binds_unchanged_abi_without_authoring_it() -> None:
    frozen = _frozen_contract()
    original = deepcopy(frozen)
    packet = {"estimator_specs": [{"id": "est_example", "name": "Example", "document_path": "theory/estimator.tex"}]}
    authored_spec = packet["estimator_specs"][0]
    normalize_theory_estimator_interface_contracts(packet, frozen_contract=frozen)
    spec = packet["estimator_specs"][0]

    assert authored_spec == {"id": "est_example", "name": "Example", "document_path": "theory/estimator.tex"}
    assert frozen == original
    assert frozen_estimator_execution_contract_alignment_errors(packet, frozen) == []
    assert spec["estimator_interface_contract"]["response_fields"][0] == {
        "name": "estimate", "meaning": frozen["response_fields"][0]["meaning"],
        "normalization": frozen["response_fields"][0]["normalization"],
        "derivation_ref": "theory/estimator.tex",
    }
    once = deepcopy(packet)
    normalize_theory_estimator_interface_contracts(packet, frozen_contract=frozen)
    assert packet == once
    # The question's full public shape/units contract remains independent of the ABI projection.
    changed = deepcopy(frozen)
    changed["response_fields"][0]["shape"] = "length 2"
    assert frozen_estimator_execution_contract_id(changed) != frozen_estimator_execution_contract_id(frozen)


@pytest.mark.parametrize("replacement", [None, {}, {"request_fields": []}])
def test_frozen_binding_does_not_repair_an_authored_invalid_contract(replacement) -> None:
    packet = {"estimator_specs": [{
        "id": "est_example", "estimator_interface_contract": replacement,
    }]}
    normalize_theory_estimator_interface_contracts(packet, frozen_contract=_frozen_contract())
    assert packet["estimator_specs"][0]["estimator_interface_contract"] == replacement
    assert frozen_estimator_execution_contract_alignment_errors(packet, _frozen_contract())


def test_frozen_binding_never_infers_a_document_from_the_estimator_id() -> None:
    packet = {"estimator_specs": [{"id": "est_example", "name": "Example"}]}
    normalize_theory_estimator_interface_contracts(packet, frozen_contract=_frozen_contract())
    contract = packet["estimator_specs"][0]["estimator_interface_contract"]
    assert all(row["derivation_ref"] == "" for row in contract["response_fields"])
    assert any("missing derivation_ref" in error for error in estimator_interface_contract_errors(
        contract, label="test", required=True,
    ))


def test_unfrozen_estimator_still_requires_model_authored_interface() -> None:
    packet = {"estimator_specs": [{"id": "different", "name": "New estimator"}]}
    normalize_theory_estimator_interface_contracts(packet, frozen_contract=_frozen_contract())
    assert "estimator_interface_contract" not in packet["estimator_specs"][0]


def test_absent_frozen_estimator_contract_adds_no_legacy_constraint() -> None:
    packet = {"estimator_specs": [{"id": "model_owned"}]}

    assert frozen_estimator_execution_contract_alignment_errors(packet, {}) == []


def test_question_loader_preserves_frozen_estimator_execution_contract(
    tmp_path,
) -> None:
    contract = _frozen_contract()
    path = tmp_path / "questions.json"
    path.write_text(
        json.dumps(
            {
                "questions": [
                    {
                        "id": "example",
                        "title": "Example",
                        "description": "Estimate one public target.",
                        "task_intent": {"scientific_code": "required"},
                        "estimator_execution_contract": contract,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    question = load_open_research_questions(path)[0]

    assert question.estimator_execution_contract == contract
    assert question.estimator_execution_contract is not contract


def test_frozen_contract_reaches_runtime_and_scientific_agent_contexts() -> None:
    contract = _frozen_contract()
    question = OpenResearchQuestion(
        id="example",
        title="Example",
        description="Estimate one public target.",
        task_intent={"scientific_code": "required", "empirical": "required"},
        estimator_execution_contract=contract,
    )

    payload = _question_to_payload(question)
    assert payload["estimator_execution_contract"] == contract
    assert _question_from_payload(payload).estimator_execution_contract == contract

    theory_artifacts = (
        research_architect_module._initial_theory_workspace_read_only_artifacts(
            question=question,
            architect_context={},
            theory_prompt_mode=(
                research_architect_module.THEORY_PROMPT_MODE_COMPACT
            ),
            max_tool_calls=48,
            formalization_authoring_required=True,
        )
    )
    prompts = (
        json.dumps(theory_artifacts, default=str),
        json.dumps(
            {"question": research_question_payload(question)},
            default=str,
        ),
    )
    assert all("response.estimate" in prompt for prompt in prompts)
    assert all("Arithmetic mean of the supplied sample" in prompt for prompt in prompts)
    assert "question.estimator_execution_contract" in (
        ALGORITHM_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT
    )
    assert "outranks Theory summaries" in (
        ALGORITHM_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT
    )
    assert "question.estimator_execution_contract" in (
        SIMULATION_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT
    )
    assert "estimator_execution_contract" not in research_question_payload(
        question,
        include_estimator_execution_contract=False,
    )


@pytest.mark.parametrize("with_theory", [False, True])
def test_source_materialization_binds_frozen_question_abi(with_theory: bool) -> None:
    contract = _frozen_contract()
    theory = {"packet_id": "theory:test", "estimator_specs": [{"id": "est_example"}]} if with_theory else {}
    normalize_theory_estimator_interface_contracts(theory, frozen_contract=contract)
    source = "def run_estimator(request): return {'estimate': 0.0}\n"
    packet = materialize_algorithm_source_workspace_record(
        question=OpenResearchQuestion(
            id="theory-free",
            title="Theory-free code task",
            description="Implement one frozen public ABI.",
            task_intent={
                "theory": "not_applicable",
                "scientific_code": "required",
            },
            estimator_execution_contract=contract,
        ),
        theory_packet=theory,
        implementation_gaps=[{"estimator_id": "est_example"}],
        source_rows=[
            {
                "estimator_id": "est_example",
                "source_code": source,
                "script_hash": stable_hash(source),
                "smoke_passed": True,
                "scientific_code_workspace": {
                    "artifact_id": "theory-free:est_example",
                    "provider": "anthropic",
                    "model": "claude-haiku-4-5-20251001",
                    "model_tier": "haiku",
                    "accepted": True,
                    "model_owned_source": True,
                    "runtime_edited_source": False,
                    "transcript_fingerprint": "transcript:theory-free",
                },
            }
        ],
    )

    target = packet["implementation_targets"][0]
    assert target["estimator_interface_contract"]["response_fields"][0][
        "derivation_ref"
    ] == "response.estimate"
    assert target["estimator_interface_contract_authority"] == {
        "owner_agent": "FrozenResearchQuestion",
        "source_theory_packet_id": "theory:test" if with_theory else "",
        "source_theory_packet_hash": stable_hash(contract),
        "source_estimator_ref": "question#/estimator_execution_contract",
        "transport_status": "RUNTIME_BOUND_FROM_FROZEN_QUESTION",
    }


def test_absent_frozen_contract_does_not_change_question_payload() -> None:
    question = OpenResearchQuestion(
        id="legacy",
        title="Legacy",
        description="A task without a frozen executable ABI.",
    )

    assert "estimator_execution_contract" not in _question_to_payload(question)


def test_executable_estimator_projection_removes_legacy_theory_prose() -> None:
    projected = project_executable_estimator_spec(
        {
            "id": "est_example",
            "name": "Example estimator",
            "document_path": "theory/estimator.md",
            "formula": "theory-document-only formula",
            "algorithm_sketch": "theory-document-only algorithm",
            "estimator_interface_contract_id": "abi:example",
            "estimator_interface_contract": {
                "request_fields": [
                    {
                        "name": "sample",
                        "meaning": "Observed sample.",
                        "binding": "per_replicate_data",
                        "legacy_theory_note": "do not forward",
                    }
                ],
                "response_fields": [
                    {
                        "name": "estimate",
                        "meaning": "Finite estimate.",
                        "normalization": "Declared in the ABI.",
                        "derivation_ref": "C1",
                        "sample_size_rate": {"scale": "legacy"},
                    }
                ],
            },
        }
    )

    assert set(projected) == {
        "id",
        "name",
        "document_path",
        "estimator_interface_contract_id",
        "estimator_interface_contract",
    }
    serialized = json.dumps(projected, sort_keys=True)
    assert projected["document_path"] == "theory/estimator.md"
    assert "theory-document-only" not in serialized
    assert "legacy_theory_note" not in serialized
    assert "sample_size_rate" not in serialized
    assert projected["estimator_interface_contract"]["response_fields"][0][
        "derivation_ref"
    ] == "C1"
