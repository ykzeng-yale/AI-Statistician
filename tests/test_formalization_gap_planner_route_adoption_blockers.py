from __future__ import annotations

from ai_statistician import formalization_gap_planner_llm_route_planner
from ai_statistician.formalization_gap_planner_route_adoption_blockers import (
    ROUTE_ADOPTION_BLOCKER_VALUES,
    route_adoption_blocker_array_json_schema,
    route_adoption_blocker_taxonomy_json_schema,
    route_adoption_blocker_taxonomy_payload,
    validate_route_adoption_blocker_taxonomy_payload,
)


def test_route_adoption_blocker_taxonomy_payload_validates() -> None:
    payload = route_adoption_blocker_taxonomy_payload()
    schema = route_adoption_blocker_taxonomy_json_schema()

    assert schema["$id"] == payload["schema_id"]
    assert validate_route_adoption_blocker_taxonomy_payload(payload) == ()
    assert tuple(payload["blocker_values"]) == ROUTE_ADOPTION_BLOCKER_VALUES
    assert "not theorem proof evidence" in str(
        payload["proof_evidence_boundary"]
    ).lower()


def test_route_adoption_blocker_array_schema_uses_canonical_values() -> None:
    schema = route_adoption_blocker_array_json_schema()

    assert schema["items"]["enum"] == list(ROUTE_ADOPTION_BLOCKER_VALUES)


def test_llm_route_planner_reexports_route_adoption_blocker_contract() -> None:
    assert (
        formalization_gap_planner_llm_route_planner.ROUTE_ADOPTION_BLOCKER_VALUES
        == ROUTE_ADOPTION_BLOCKER_VALUES
    )
    assert (
        formalization_gap_planner_llm_route_planner.route_adoption_blocker_taxonomy_payload()
        == route_adoption_blocker_taxonomy_payload()
    )
    assert (
        formalization_gap_planner_llm_route_planner.route_adoption_blocker_taxonomy_json_schema()
        == route_adoption_blocker_taxonomy_json_schema()
    )
    assert (
        formalization_gap_planner_llm_route_planner.validate_route_adoption_blocker_taxonomy_payload(
            route_adoption_blocker_taxonomy_payload()
        )
        == ()
    )
