from __future__ import annotations

import hashlib
import json
from collections import Counter
from fractions import Fraction as Q
from pathlib import Path

import pytest

from ai_statistician.architect_theory_execution_preflight import (
    build_architect_theory_execution_preflight_material,
    build_architect_theory_execution_preflight_prompt,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.theory_workspace import theory_workspace_document_manifest


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "benchmarks/reviewer_thinking_controls_20260909"
PROTOCOL = json.loads((STUDY / "protocol.json").read_text())
CASES = PROTOCOL["evaluator_only_cases"]


def test_frozen_control_inputs_and_counterbalanced_configuration() -> None:
    assert PROTOCOL["model"] == "claude-haiku-4-5-20251001"
    assert PROTOCOL["arms"]["A"]["thinking_budget_tokens"] == 0
    assert PROTOCOL["arms"]["B"]["thinking_budget_tokens"] == 2048
    assert PROTOCOL["max_tokens"] == 8000
    assert Counter(row["expected_verdict"] for row in CASES.values()) == {
        "ACCEPT": 3, "REVISE": 3,
    }
    order = PROTOCOL["invocation_order"]
    assert len(order) == len({tuple(row) for row in order}) == 12
    assert {tuple(row) for row in order} == {
        (case_id, arm) for case_id in CASES for arm in ("A", "B")
    }
    first_arms = {}
    for case_id, arm in order:
        first_arms.setdefault(case_id, arm)
    assert Counter(first_arms.values()) == {"A": 3, "B": 3}
    for row in CASES.values():
        assert hashlib.sha256((STUDY / row["path"]).read_bytes()).hexdigest() == row["sha256"]


@pytest.mark.parametrize("case_id", CASES)
def test_control_projection_contains_candidate_but_no_evaluator_labels(
    case_id: str, tmp_path: Path,
) -> None:
    source = (STUDY / CASES[case_id]["path"]).read_text()
    (tmp_path / "theory.md").write_text(source)
    semantic = {"theory_workspace_manifest": theory_workspace_document_manifest(
        {"theory.md": source}, workspace_dir=tmp_path,
    )}
    material = build_architect_theory_execution_preflight_material(
        question=OpenResearchQuestion(
            id="independent_derivation_review",
            title="Independent derivation review",
            description=PROTOCOL["question"],
            task_intent=PROTOCOL["task_intent"],
        ),
        theory_protocol_material={
            "source_theory_packet_id": "theory_document:" + stable_hash(source),
            "source_theory_packet_hash": stable_hash(semantic),
            "theory_semantic_material": semantic,
        },
        upstream_research_contract={"dimension_requirements": PROTOCOL["task_intent"]},
    )
    assert not material["execution_handoff_required"]
    documents = [row for row in material["anchor_catalog"]
                 if row["artifact_role"] == "authoritative_theory_document"]
    assert len(documents) == 1
    assert documents[0]["content"] == source
    prompt = build_architect_theory_execution_preflight_prompt(material)
    assert PROTOCOL["question"] in prompt
    assert "evaluator_only_cases" not in prompt
    for row in CASES.values():
        assert row["rubric"] not in prompt
    assert "protocol.json" not in prompt


def test_matrix_control_labels_against_exact_product_derivative() -> None:
    # BA^-1 + AX must vanish; invertible A makes the derivative X unique.
    correct = ((Q(0), Q(-1, 6)), (Q(-1, 6), Q(0)))
    incorrect = ((Q(0), Q(-1, 4)), (Q(-1, 9), Q(0)))
    b_a_inverse = ((Q(0), Q(1, 3)), (Q(1, 2), Q(0)))
    for candidate, valid in ((correct, True), (incorrect, False)):
        residual = [b_a_inverse[i][j] + (2, 3)[i] * candidate[i][j]
                    for i in range(2) for j in range(2)]
        assert all(value == 0 for value in residual) is valid


def test_moving_domain_control_exact_change_of_variables_and_boundary() -> None:
    for t in (Q(1, 3), Q(1), Q(7, 2)):
        for u in (Q(0), Q(1, 5), Q(1)):
            assert (t * u) / (t**2 + (t * u)**2) * t == u / (1 + u**2)
        boundary = t / (t**2 + t**2)
        partial_integral = t / (2 * t**2) - t / t**2
        assert boundary + partial_integral == 0
        assert partial_integral == -1 / (2 * t) != 0


def test_uniform_convergence_control_exact_moving_point_witnesses() -> None:
    # Finite exact witnesses supplement the limit proof in the frozen rubric;
    # this test does not mistake finitely many probes for an asymptotic proof.
    for n in range(1, 257):
        x = Q(1, n + 1)
        value = n * x * (1 - x)**n
        assert value == Q(n, n + 1)**(n + 1)
        assert value >= Q(1, 4)
        assert 1 - (n + 1) * x == 0
