from __future__ import annotations

import json

from ai_statistician.estimator_interface_contract import (
    frozen_estimator_execution_contract_clause_ids,
    frozen_estimator_execution_contract_empirical_claim_ids,
    frozen_estimator_execution_contract_errors,
    frozen_estimator_execution_contract_id,
)
from ai_statistician.algorithm_engineer_llm import build_algorithm_engineer_prompt
from ai_statistician.research_agent_runtime import (
    _question_from_payload,
    _question_to_payload,
)
from ai_statistician.research_architect import build_theory_developer_prompt
from ai_statistician.research_lab import load_open_research_questions
from ai_statistician.research_schema import (
    OpenResearchQuestion,
    research_question_payload,
)
from ai_statistician.simulation_engineer_llm import (
    build_simulation_engineer_prompt,
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

    prompts = (
        build_theory_developer_prompt(question, architect_context={}),
        build_algorithm_engineer_prompt(
            question=question,
            theory_packet={},
            simulation_manifest={},
            implementation_gaps=[],
        ),
        build_simulation_engineer_prompt(
            question=question,
            theory_packet={},
            registered_problem={},
            registered_procedures=[],
            n_runs=10,
            seed=1,
        ),
    )
    assert all("response.estimate" in prompt for prompt in prompts)
    assert all("Arithmetic mean of the supplied sample" in prompt for prompt in prompts)
    assert "estimator_execution_contract" not in research_question_payload(
        question,
        include_estimator_execution_contract=False,
    )


def test_absent_frozen_contract_does_not_change_legacy_question_payload() -> None:
    question = OpenResearchQuestion(
        id="legacy",
        title="Legacy",
        description="A task without a frozen executable ABI.",
    )

    assert "estimator_execution_contract" not in _question_to_payload(question)
    prompt = build_algorithm_engineer_prompt(
        question=question,
        theory_packet={},
        simulation_manifest={},
        implementation_gaps=[],
    )
    assert "estimator_execution_contract" not in prompt
