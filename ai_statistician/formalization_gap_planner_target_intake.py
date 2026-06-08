from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_standalone import (
    FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT,
    FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_VERSION,
)


FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_SCHEMA_VERSION = 1
FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_SCHEMA_ID = (
    "urn:ai-statistician:schemas:formalization-gap-planner-target-intake:1"
)
FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:formalization-gap-planner-target-intake-row:1"
)
FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_COMPONENT = (
    "formalization_gap_planner_target_intake"
)
PROOF_EVIDENCE_STATUS = "FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner target-intake rows normalize theorem requests "
    "into route seeds, primitive candidates, and refinement queries. They are "
    "not theorem proof evidence."
)
DEFAULT_TARGET_PROVER_FAMILY = "lean4"
GENERIC_TERMS = {
    "theorem",
    "proof",
    "show",
    "prove",
    "result",
    "claim",
    "target",
    "given",
    "under",
    "where",
    "with",
    "using",
    "current",
    "desired",
}
KEYWORD_PRIMITIVES = (
    ("exchangeab", "exchangeability"),
    ("iid", "iid"),
    ("independent", "independence"),
    ("measur", "measurability"),
    ("integrab", "integrability"),
    ("conditional expectation", "conditional_expectation"),
    ("conditional mean", "conditional_mean_identity"),
    ("finite sample", "finite_sample_bound"),
    ("coverage", "coverage_inequality"),
    ("asymptotic normal", "asymptotic_normality"),
    ("central limit", "central_limit_theorem"),
    ("consisten", "consistency"),
    ("convergen", "convergence"),
    ("uniform", "uniform_bound"),
    ("martingale", "martingale"),
    ("filtration", "filtration"),
    ("empirical process", "empirical_process"),
    ("vc", "vc_dimension"),
    ("rademacher", "rademacher_complexity"),
    ("positivity", "positivity"),
    ("unconfounded", "unconfoundedness"),
    ("potential outcome", "potential_outcomes"),
    ("rank", "rank_uniformity"),
    ("quantile", "quantile_definition"),
)


@dataclass(frozen=True)
class FormalizationGapPlannerTargetIntakeRow:
    schema_version: int
    target_intake_id: str
    target_id: str
    display_name: str
    domain: str
    target_prover_family: str
    library_snapshot_ref: str
    theorem_statement: str
    theorem_skeleton: str
    normalized_objects: tuple[str, ...]
    normalized_assumptions: tuple[str, ...]
    normalized_procedure: str
    normalized_claim: str
    desired_theorem_shape: str
    proof_source_refs: tuple[str, ...]
    primitive_seed_rows: tuple[dict[str, object], ...]
    extracted_primitive_candidates: tuple[str, ...]
    background_primitives: tuple[str, ...]
    standalone_route_id: str
    literature_queries: tuple[str, ...]
    formal_library_grounding_queries: tuple[str, ...]
    lean_grounding_queries: tuple[str, ...]
    proof_state_probe_required: bool
    missing_required_fields: tuple[str, ...]
    review_flags: tuple[str, ...]
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def normalize_formalization_gap_planner_target_intake(
    input_path: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Normalize raw theorem requests into portable planner route seeds."""

    errors: list[str] = []
    input_payload = _read_input_payload(input_path, errors)
    targets = _target_records(input_payload)
    if not targets:
        errors.append("target intake input contains no target records")
    rows = [_target_intake_row(target) for target in targets]
    standalone_seed = _standalone_seed(input_payload, rows)
    row_dicts = [asdict(row) for row in rows]
    row_schema = target_intake_row_json_schema()
    row_schema_errors = [
        validate_target_intake_row(row_dict, row_schema) for row_dict in row_dicts
    ]
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_SCHEMA_VERSION,
        "schema_id": FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_SCHEMA_ID,
        "target_intake_row_schema_id": FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_ROW_SCHEMA_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_COMPONENT,
        "input_path": str(input_path),
        "n_targets": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_target_intake_row_schema_valid": sum(
            1 for errors_for_row in row_schema_errors if not errors_for_row
        ),
        "n_target_intake_row_schema_invalid": sum(
            1 for errors_for_row in row_schema_errors if errors_for_row
        ),
        "n_missing_proof_sources": sum(
            1 for row in rows if "proof_source_refs_missing" in row.review_flags
        ),
        "n_missing_theorem_skeleton": sum(
            1 for row in rows if "theorem_skeleton_missing" in row.review_flags
        ),
        "n_primitive_seed_rows": sum(len(row.primitive_seed_rows) for row in rows),
        "n_literature_queries": sum(len(row.literature_queries) for row in rows),
        "n_formal_library_grounding_queries": sum(
            len(row.formal_library_grounding_queries) for row in rows
        ),
        "n_lean_grounding_queries": sum(len(row.lean_grounding_queries) for row in rows),
        "all_ok": (
            not errors
            and bool(rows)
            and all(row.ok for row in rows)
            and all(not errors_for_row for errors_for_row in row_schema_errors)
        ),
        "errors": errors,
        "row_schema_errors": row_schema_errors,
        "rows": row_dicts,
        "standalone_seed": standalone_seed,
        "standalone_seed_component": FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT,
        "target_intake_fingerprint": stable_hash(row_dicts),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "target intake produces search and route seeds, not a complete proof route",
            "primitive seeds default to needs_search until literature and library adapters respond",
            "source faithfulness still requires source-backed route evidence and downstream prover replay",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formalization_gap_planner_target_intake_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (out_dir / "formalization_gap_planner_target_intake.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (
            out_dir / "formalization_gap_planner_target_intake_standalone_seed.json"
        ).write_text(json.dumps(standalone_seed, indent=2, default=str), encoding="utf-8")
        (out_dir / "formalization_gap_planner_target_intake.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_target_intake.schema.json").write_text(
            json.dumps(target_intake_json_schema(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        (
            out_dir / "formalization_gap_planner_target_intake_row.schema.json"
        ).write_text(
            json.dumps(row_schema, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    return payload


def target_intake_json_schema() -> dict[str, object]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_SCHEMA_ID,
        "title": "Formalization Gap Planner Target Intake",
        "description": (
            "Raw theorem-request input contract for seeding a portable "
            "library-aware formalization gap plan."
        ),
        "type": "object",
        "additionalProperties": True,
        "properties": {
            "schema_version": {
                "const": FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_SCHEMA_VERSION
            },
            "component_name": {
                "const": FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_COMPONENT
            },
            "target_prover_family": {"type": "string"},
            "library_snapshot_ref": {"type": "string", "minLength": 1},
            "target_id": {"type": "string"},
            "title": {"type": "string"},
            "domain": {"type": "string"},
            "theorem_statement": {"type": "string"},
            "informal_statement": {"type": "string"},
            "target_theorem": {"type": "string"},
            "objects": {"type": "array", "items": {"type": "string"}},
            "assumptions": {"type": "array", "items": {"type": "string"}},
            "statistical_procedure": {"type": "string"},
            "desired_conclusion": {"type": "string"},
            "desired_theorem_shape": {"type": "string"},
            "known_proof_sources": {"type": "array", "items": {"type": "string"}},
            "candidate_primitives": {
                "type": "array",
                "items": {
                    "oneOf": [
                        {"type": "string"},
                        {
                            "type": "object",
                            "additionalProperties": True,
                            "required": ["primitive"],
                        },
                    ]
                },
            },
            "targets": {"type": "array", "items": {"type": "object"}},
        },
    }


def target_intake_row_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    object_array = {"type": "array", "items": {"type": "object"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_ROW_SCHEMA_ID,
        "title": "Formalization Gap Planner Target Intake Row",
        "description": (
            "Portable normalized theorem-request row emitted by target intake. "
            "Rows seed informal route synthesis, library grounding, and proof-state "
            "queries; they are not theorem proof evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "target_intake_id",
            "target_id",
            "display_name",
            "domain",
            "target_prover_family",
            "library_snapshot_ref",
            "theorem_statement",
            "theorem_skeleton",
            "normalized_objects",
            "normalized_assumptions",
            "normalized_procedure",
            "normalized_claim",
            "desired_theorem_shape",
            "proof_source_refs",
            "primitive_seed_rows",
            "extracted_primitive_candidates",
            "background_primitives",
            "standalone_route_id",
            "literature_queries",
            "lean_grounding_queries",
            "proof_state_probe_required",
            "missing_required_fields",
            "review_flags",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "ok",
            "errors",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_SCHEMA_VERSION,
            },
            "target_intake_id": {"type": "string", "minLength": 1},
            "target_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "domain": {"type": "string"},
            "target_prover_family": {"type": "string", "minLength": 1},
            "library_snapshot_ref": {"type": "string", "minLength": 1},
            "theorem_statement": {"type": "string", "minLength": 1},
            "theorem_skeleton": {"type": "string"},
            "normalized_objects": string_array,
            "normalized_assumptions": string_array,
            "normalized_procedure": {"type": "string"},
            "normalized_claim": {"type": "string"},
            "desired_theorem_shape": {"type": "string"},
            "proof_source_refs": string_array,
            "primitive_seed_rows": object_array,
            "extracted_primitive_candidates": string_array,
            "background_primitives": string_array,
            "standalone_route_id": {"type": "string", "minLength": 1},
            "literature_queries": string_array,
            "formal_library_grounding_queries": string_array,
            "lean_grounding_queries": string_array,
            "proof_state_probe_required": {"type": "boolean"},
            "missing_required_fields": string_array,
            "review_flags": string_array,
            "proof_evidence_status": {"const": PROOF_EVIDENCE_STATUS},
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
            "ok": {"type": "boolean"},
            "errors": string_array,
        },
    }


def validate_target_intake_row(
    row: dict[str, Any],
    schema: dict[str, object] | None = None,
) -> list[str]:
    row_schema = schema or target_intake_row_json_schema()
    if not isinstance(row, dict):
        return ["target intake row must be an object"]
    errors: list[str] = []
    required = row_schema.get("required", [])
    if isinstance(required, list):
        for field_name in required:
            if isinstance(field_name, str) and field_name not in row:
                errors.append(f"{field_name} required")
    properties = row_schema.get("properties", {})
    if isinstance(properties, dict):
        for field_name, field_schema in properties.items():
            if not isinstance(field_name, str) or field_name not in row:
                continue
            if isinstance(field_schema, dict):
                errors.extend(
                    _schema_property_errors(field_name, row[field_name], field_schema)
                )
    return errors


def _target_intake_row(target: dict[str, Any]) -> FormalizationGapPlannerTargetIntakeRow:
    target_id = _first_text(target, "target_id", "id", "name") or "target:" + stable_hash(target)[:12]
    title = _first_text(target, "title", "display_name", "name")
    statement = _first_text(
        target,
        "theorem_statement",
        "informal_statement",
        "target_theorem",
        "open_question",
        "claim",
    )
    claim = _first_text(target, "desired_conclusion", "conclusion", "claim") or statement
    procedure = _first_text(target, "statistical_procedure", "procedure", "estimator", "method")
    desired_shape = _first_text(target, "desired_theorem_shape", "theorem_shape")
    theorem_skeleton = _first_text(target, "theorem_skeleton", "formal_skeleton")
    target_family = (
        _first_text(target, "target_prover_family", "prover_family")
        or DEFAULT_TARGET_PROVER_FAMILY
    )
    library_snapshot_ref = _first_text(target, "library_snapshot_ref", "library_snapshot")
    domain = _first_text(target, "domain", "field", "problem_class")
    objects = _str_tuple(target.get("objects", target.get("mathematical_objects", [])))
    assumptions = _str_tuple(target.get("assumptions", []))
    proof_sources = _str_tuple(
        [
            *_str_tuple(target.get("known_proof_sources", [])),
            *_str_tuple(target.get("source_refs", [])),
            *_str_tuple(target.get("references", [])),
        ]
    )
    background = _str_tuple(target.get("background_primitives", []))
    primitive_rows = _primitive_seed_rows(
        target,
        statement=statement,
        claim=claim,
        procedure=procedure,
        objects=objects,
        assumptions=assumptions,
        proof_sources=proof_sources,
    )
    primitive_names = _str_tuple(row.get("primitive", "") for row in primitive_rows)
    display_name = _safe_name(title or target_id or statement[:80] or "target_theorem")
    literature_queries = _literature_queries(
        display_name,
        statement=statement,
        assumptions=assumptions,
        claim=claim,
        primitives=primitive_names,
    )
    formal_library_queries = _formal_library_grounding_queries(
        theorem_shape=desired_shape,
        primitives=primitive_names,
        objects=objects,
    )
    missing_required = []
    if not statement:
        missing_required.append("theorem_statement")
    if not library_snapshot_ref:
        missing_required.append("library_snapshot_ref")
    if not primitive_rows:
        missing_required.append("primitive_seed_rows")
    review_flags = []
    if not proof_sources:
        review_flags.append("proof_source_refs_missing")
    if not theorem_skeleton:
        review_flags.append("theorem_skeleton_missing")
    if not desired_shape:
        review_flags.append("desired_theorem_shape_missing")
    if any(row.get("coverage_status") == "needs_search" for row in primitive_rows):
        review_flags.append("library_coverage_search_required")
    errors = tuple(f"{field} missing" for field in missing_required)
    route_id = "target_intake_route:" + stable_hash([target_id, statement, primitive_names])[:16]
    return FormalizationGapPlannerTargetIntakeRow(
        schema_version=FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_SCHEMA_VERSION,
        target_intake_id="formalization_gap_planner_target_intake:"
        + stable_hash([target_id, statement, library_snapshot_ref])[:16],
        target_id=target_id,
        display_name=display_name,
        domain=domain,
        target_prover_family=target_family,
        library_snapshot_ref=library_snapshot_ref,
        theorem_statement=statement,
        theorem_skeleton=theorem_skeleton,
        normalized_objects=objects,
        normalized_assumptions=assumptions,
        normalized_procedure=procedure,
        normalized_claim=claim,
        desired_theorem_shape=desired_shape,
        proof_source_refs=proof_sources,
        primitive_seed_rows=primitive_rows,
        extracted_primitive_candidates=primitive_names,
        background_primitives=background,
        standalone_route_id=route_id,
        literature_queries=literature_queries,
        formal_library_grounding_queries=formal_library_queries,
        lean_grounding_queries=formal_library_queries,
        proof_state_probe_required=bool(theorem_skeleton),
        missing_required_fields=tuple(missing_required),
        review_flags=tuple(review_flags),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=errors,
    )


def _standalone_seed(
    input_payload: dict[str, Any],
    rows: list[FormalizationGapPlannerTargetIntakeRow],
) -> dict[str, object]:
    route_target_families = tuple(
        row.target_prover_family.strip()
        for row in rows
        if row.target_prover_family.strip()
    )
    route_target_keys = {
        _target_prover_key(target) for target in route_target_families if target
    }
    if "" in route_target_keys:
        route_target_keys.remove("")
    top_level_target_family = str(input_payload.get("target_prover_family", "")).strip()
    if not top_level_target_family and len(route_target_keys) == 1:
        top_level_target_family = route_target_families[0]
    elif len(route_target_keys) > 1:
        top_level_target_family = ""
    snapshot = (
        str(input_payload.get("library_snapshot_ref", "")).strip()
        or (rows[0].library_snapshot_ref if rows else "")
    )
    background = _str_tuple(
        primitive
        for row in rows
        for primitive in row.background_primitives
    )
    seed: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_VERSION,
        "component_name": FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT,
        "library_snapshot_ref": snapshot,
        "background_primitives": background,
        "routes": [
            {
                "route_id": row.standalone_route_id,
                "display_name": row.display_name,
                "target_prover_family": row.target_prover_family,
                "theorem_statement": row.theorem_statement,
                "theorem_skeleton": row.theorem_skeleton,
                "source_refs": row.proof_source_refs,
                "informal_proof_steps": tuple(
                    item
                    for item in (
                        row.desired_theorem_shape,
                        row.normalized_claim,
                        row.normalized_procedure,
                    )
                    if item
                ),
                "primitives": row.primitive_seed_rows,
            }
            for row in rows
        ],
    }
    if top_level_target_family:
        seed["target_prover_family"] = top_level_target_family
    return seed


def _primitive_seed_rows(
    target: dict[str, Any],
    *,
    statement: str,
    claim: str,
    procedure: str,
    objects: tuple[str, ...],
    assumptions: tuple[str, ...],
    proof_sources: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    rows: dict[str, dict[str, object]] = {}
    for raw in _raw_items(target.get("candidate_primitives", target.get("primitives", []))):
        row = _primitive_row_from_raw(raw, proof_sources)
        if row:
            rows[str(row["primitive"])] = row
    for source_kind, values in (
        ("assumption", assumptions),
        ("object", objects),
        ("procedure", (procedure,)),
        ("claim", (claim,)),
        ("statement_keyword", _keyword_primitives(" ".join([statement, claim, procedure, *assumptions]))),
    ):
        for value in values:
            primitive = _primitive_name(value)
            if not primitive or primitive in rows:
                continue
            rows[primitive] = {
                "primitive": primitive,
                "coverage_status": "needs_search",
                "source_refs": proof_sources,
                "source_field": source_kind,
            }
    return tuple(rows[name] for name in sorted(rows))


def _primitive_row_from_raw(raw: Any, proof_sources: tuple[str, ...]) -> dict[str, object]:
    if isinstance(raw, str):
        primitive = _primitive_name(raw)
        if not primitive:
            return {}
        return {
            "primitive": primitive,
            "coverage_status": "needs_search",
            "source_refs": proof_sources,
            "source_field": "candidate_primitives",
        }
    if not isinstance(raw, dict):
        return {}
    primitive = _primitive_name(str(raw.get("primitive", "")))
    if not primitive:
        return {}
    row = dict(raw)
    row["primitive"] = primitive
    row.setdefault("coverage_status", "needs_search")
    row.setdefault("source_refs", proof_sources)
    row.setdefault("source_field", "candidate_primitives")
    return row


def _keyword_primitives(text: str) -> tuple[str, ...]:
    lower = text.lower()
    return tuple(
        primitive for needle, primitive in KEYWORD_PRIMITIVES if needle in lower
    )


def _literature_queries(
    display_name: str,
    *,
    statement: str,
    assumptions: tuple[str, ...],
    claim: str,
    primitives: tuple[str, ...],
) -> tuple[str, ...]:
    return _str_tuple(
        [
            f"{display_name} theorem assumptions proof route",
            statement,
            " ".join(assumptions),
            claim,
            " ".join(primitives[:8]),
            f"{display_name} measurability integrability side conditions",
        ]
    )


def _formal_library_grounding_queries(
    *,
    theorem_shape: str,
    primitives: tuple[str, ...],
    objects: tuple[str, ...],
) -> tuple[str, ...]:
    return _str_tuple([theorem_shape, *primitives, *objects])


def _read_input_payload(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"missing target intake input: {path}")
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {
            "informal_statement": text.strip(),
            "target_id": "raw_text_target:" + stable_hash(text)[:12],
            "library_snapshot_ref": "",
        }
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list):
        return {"targets": payload}
    errors.append("target intake input must be a JSON object, JSON list, or plain text")
    return {}


def _target_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    inherited = {
        key: value
        for key, value in payload.items()
        if key
        in {
            "target_prover_family",
            "library_snapshot_ref",
            "domain",
            "background_primitives",
        }
    }
    if isinstance(payload.get("targets"), list):
        return [
            {**inherited, **dict(target)}
            for target in payload["targets"]
            if isinstance(target, dict)
        ]
    return [payload] if payload else []


def _target_prover_key(value: object) -> str:
    target = str(value or "").strip().lower()
    aliases = {
        "lean": "lean4",
        "lean_4": "lean4",
        "coq": "rocq",
        "coq8": "rocq",
        "isabelle_hol": "isabelle",
    }
    return aliases.get(target, target)


def _first_text(row: dict[str, Any], *field_names: str) -> str:
    for field_name in field_names:
        value = row.get(field_name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        values = _split_text_items(values)
    if not isinstance(values, (list, tuple, set)):
        try:
            values = tuple(values)
        except TypeError:
            return tuple()
    return tuple(dict.fromkeys(str(item).strip() for item in values if str(item).strip()))


def _raw_items(values: Any) -> tuple[Any, ...]:
    if values is None:
        return tuple()
    if isinstance(values, (list, tuple, set)):
        return tuple(values)
    return (values,)


def _split_text_items(value: str) -> tuple[str, ...]:
    parts = re.split(r";|\n|,(?=\s*[a-zA-Z])|\band\b", value)
    return tuple(part.strip() for part in parts if part.strip())


def _primitive_name(value: str) -> str:
    normalized = value.strip().lower()
    if not normalized:
        return ""
    normalized = normalized.replace("'", "")
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    normalized = re.sub(r"_+", "_", normalized)
    tokens = [token for token in normalized.split("_") if token and token not in GENERIC_TERMS]
    if not tokens:
        return ""
    if len(tokens) > 8:
        tokens = tokens[:8]
    return "_".join(tokens)


def _safe_name(value: str) -> str:
    name = _primitive_name(value)
    return name or "target_theorem"


def _schema_property_errors(
    field_name: str,
    value: Any,
    field_schema: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    expected_type = field_schema.get("type")
    if expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{field_name} must be integer")
    elif expected_type == "string":
        if not isinstance(value, str):
            errors.append(f"{field_name} must be string")
        elif field_schema.get("minLength") and len(value) < int(
            field_schema["minLength"]
        ):
            errors.append(f"{field_name} must be non-empty")
    elif expected_type == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{field_name} must be boolean")
    elif expected_type == "array":
        if not isinstance(value, (list, tuple)):
            errors.append(f"{field_name} must be array")
        else:
            item_schema = field_schema.get("items", {})
            if isinstance(item_schema, dict) and item_schema.get("type") == "string":
                bad_indexes = [
                    idx for idx, item in enumerate(value) if not isinstance(item, str)
                ]
                if bad_indexes:
                    errors.append(
                        f"{field_name} items must be string at indexes "
                        + ",".join(str(idx) for idx in bad_indexes)
                    )
            if isinstance(item_schema, dict) and item_schema.get("type") == "object":
                bad_indexes = [
                    idx for idx, item in enumerate(value) if not isinstance(item, dict)
                ]
                if bad_indexes:
                    errors.append(
                        f"{field_name} items must be object at indexes "
                        + ",".join(str(idx) for idx in bad_indexes)
                    )
    elif expected_type == "object":
        if not isinstance(value, dict):
            errors.append(f"{field_name} must be object")
    if "const" in field_schema and value != field_schema["const"]:
        errors.append(f"{field_name} must equal {field_schema['const']!r}")
    pattern = field_schema.get("pattern")
    if isinstance(pattern, str) and isinstance(value, str):
        if re.search(pattern, value) is None:
            errors.append(f"{field_name} must match /{pattern}/")
    return errors


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Target Intake",
        "",
        f"- Targets: {payload.get('n_ok')}/{payload.get('n_targets')}",
        f"- Primitive seeds: {payload.get('n_primitive_seed_rows')}",
        f"- Literature queries: {payload.get('n_literature_queries')}",
        f"- Formal-library queries: {payload.get('n_formal_library_grounding_queries')}",
        f"- Missing proof sources: {payload.get('n_missing_proof_sources')}",
        f"- Missing theorem skeletons: {payload.get('n_missing_theorem_skeleton')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Targets",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('display_name')}` primitives={len(row.get('primitive_seed_rows', []))} "
            f"flags={','.join(str(item) for item in row.get('review_flags', []))}"
        )
    return "\n".join(lines) + "\n"
