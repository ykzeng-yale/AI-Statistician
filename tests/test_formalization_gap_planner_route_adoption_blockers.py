from __future__ import annotations

import json
from pathlib import Path

from ai_statistician import formalization_gap_planner_llm_route_planner
from ai_statistician.cli import main
from ai_statistician.formalization_gap_planner_route_adoption_blockers import (
    ROUTE_ADOPTION_BLOCKER_VALUES,
    ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID,
    export_route_adoption_blocker_taxonomy,
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


def test_export_route_adoption_blocker_taxonomy_writes_reusable_artifacts(
    tmp_path: Path,
) -> None:
    manifest = export_route_adoption_blocker_taxonomy(tmp_path)

    schema_path = (
        tmp_path
        / "formalization_gap_planner_route_adoption_blocker_taxonomy.schema.json"
    )
    taxonomy_path = (
        tmp_path / "formalization_gap_planner_route_adoption_blocker_taxonomy.json"
    )
    manifest_path = (
        tmp_path
        / "formalization_gap_planner_route_adoption_blocker_taxonomy_manifest.json"
    )
    schema = json.loads(schema_path.read_text())
    payload = json.loads(taxonomy_path.read_text())
    manifest_payload = json.loads(manifest_path.read_text())

    assert manifest["all_ok"] is True
    assert manifest_payload["all_ok"] is True
    assert schema["$id"] == ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID
    assert payload["schema_id"] == ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID
    assert tuple(payload["blocker_values"]) == ROUTE_ADOPTION_BLOCKER_VALUES
    assert manifest_payload["taxonomy_path"] == str(taxonomy_path)


def test_route_adoption_blocker_taxonomy_cli_exports_artifacts(
    tmp_path: Path,
) -> None:
    out_dir = tmp_path / "taxonomy_cli"

    rc = main(
        [
            "formalization-gap-planner-route-adoption-blocker-taxonomy",
            "--out",
            str(out_dir),
        ]
    )

    assert rc == 0
    manifest = json.loads(
        (
            out_dir
            / "formalization_gap_planner_route_adoption_blocker_taxonomy_manifest.json"
        ).read_text()
    )
    payload = json.loads(
        (
            out_dir / "formalization_gap_planner_route_adoption_blocker_taxonomy.json"
        ).read_text()
    )
    assert manifest["all_ok"] is True
    assert payload["schema_id"] == ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID
