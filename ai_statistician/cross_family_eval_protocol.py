from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash
from .model_backend import (
    LIVE_EVALUATION_CLAUDE_MODEL,
    LIVE_EVALUATION_CLAUDE_MODEL_TIER,
)
from .task_family import (
    is_explicit_task_family,
    primary_task_family_from_question,
    task_family_value,
)


CROSS_FAMILY_EVAL_PROTOCOL_SCHEMA_VERSION = 1
CROSS_FAMILY_EVAL_PROTOCOL_KIND = "CrossFamilyEndToEndEvaluationProtocol"
CONFIRMATORY_EVALUATION_COHORT_KIND = "RuntimeConfirmatoryEvaluationCohort"
CONFIRMATORY_EVALUATION_COHORT_TRANSITION_KIND = "RuntimeConfirmatoryEvaluationCohortTransition"
CONFIRMATORY_EVALUATION_COHORT_CONTEXT_KEY = "runtime_confirmatory_evaluation_cohort"
CONFIRMATORY_EVALUATION_SEED_MODULUS = 2_147_483_647


def load_cross_family_eval_protocol(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_cross_family_eval_protocol(payload)
    if errors:
        raise ValueError("; ".join(errors))
    return dict(payload)


def validate_cross_family_eval_protocol(value: Any) -> list[str]:
    if not isinstance(value, Mapping):
        return ["cross-family evaluation protocol must be a JSON object"]
    errors: list[str] = []
    if value.get("schema_version") != CROSS_FAMILY_EVAL_PROTOCOL_SCHEMA_VERSION:
        errors.append(
            "cross-family evaluation protocol schema_version must equal "
            f"{CROSS_FAMILY_EVAL_PROTOCOL_SCHEMA_VERSION}"
        )
    if value.get("artifact_kind") != CROSS_FAMILY_EVAL_PROTOCOL_KIND:
        errors.append(
            f"cross-family evaluation protocol artifact_kind must equal "
            f"{CROSS_FAMILY_EVAL_PROTOCOL_KIND}"
        )
    for field in (
        "protocol_id",
        "split_frozen_at",
        "split_frozen_at_base_commit",
        "question_source",
    ):
        if not str(value.get(field, "") or "").strip():
            errors.append(f"cross-family evaluation protocol {field} is required")
    minimum_families = value.get("minimum_distinct_task_families_per_panel")
    if (
        isinstance(minimum_families, bool)
        or not isinstance(minimum_families, int)
        or minimum_families < 2
    ):
        errors.append(
            "minimum_distinct_task_families_per_panel must be an integer >= 2"
        )
        minimum_families = 2

    run_contract = value.get("run_contract", {})
    if not isinstance(run_contract, Mapping):
        errors.append("run_contract must be an object")
    else:
        required_true_fields = (
            "capability_eval_required",
            "fresh_start_required",
            "resume_forbidden",
            "task_learning_memory_forbidden",
            "component_eval_substitution_forbidden",
            "candidate_gate_independence_required",
            "confirmatory_source_outcome_blinding_required",
            "post_outcome_fresh_cohort_required",
            "confirmatory_candidate_seed_blinding_required",
            "generated_code_semantic_review_required",
            "semantic_review_source_and_execution_lineage_required",
            "all_live_anthropic_agents_exact_model_required",
            "sonnet_opus_live_calls_forbidden",
        )
        for field in required_true_fields:
            if run_contract.get(field) is not True:
                errors.append(f"run_contract.{field} must be true")
        if str(run_contract.get("capability_eval_preset", "") or "") != "full-live":
            errors.append("run_contract.capability_eval_preset must equal full-live")
        if str(
            run_contract.get("evaluation_claude_model_tier", "") or ""
        ) != LIVE_EVALUATION_CLAUDE_MODEL_TIER:
            errors.append(
                "run_contract.evaluation_claude_model_tier must equal "
                f"{LIVE_EVALUATION_CLAUDE_MODEL_TIER}"
            )
        if str(run_contract.get("evaluation_claude_model", "") or "") != (
            LIVE_EVALUATION_CLAUDE_MODEL
        ):
            errors.append(
                "run_contract.evaluation_claude_model must equal "
                f"{LIVE_EVALUATION_CLAUDE_MODEL}"
            )

    panels = value.get("panels", {})
    if not isinstance(panels, Mapping):
        errors.append("panels must be an object")
        return sorted(set(errors))
    required_panel_ids = {"development", "held_out"}
    missing_panels = required_panel_ids - set(panels)
    if missing_panels:
        errors.append(
            "panels must include development and held_out; missing: "
            + ", ".join(sorted(missing_panels))
        )

    panel_question_ids: dict[str, set[str]] = {}
    panel_task_families: dict[str, set[str]] = {}
    for panel_id, raw_panel in panels.items():
        prefix = f"panels.{panel_id}"
        if not isinstance(raw_panel, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        if str(raw_panel.get("role", "") or "") != str(panel_id):
            errors.append(f"{prefix}.role must equal {panel_id}")
        tasks = raw_panel.get("tasks")
        if not isinstance(tasks, list) or not tasks:
            errors.append(f"{prefix}.tasks must be a nonempty array")
            continue
        question_ids: list[str] = []
        task_families: list[str] = []
        for index, raw_task in enumerate(tasks):
            task_prefix = f"{prefix}.tasks[{index}]"
            if not isinstance(raw_task, Mapping):
                errors.append(f"{task_prefix} must be an object")
                continue
            question_id = str(raw_task.get("question_id", "") or "").strip()
            task_family = task_family_value(raw_task.get("task_family", ""))
            if not question_id:
                errors.append(f"{task_prefix}.question_id is required")
            else:
                question_ids.append(question_id)
            if not is_explicit_task_family(task_family):
                errors.append(f"{task_prefix}.task_family must be explicit")
            else:
                task_families.append(task_family)
        if len(set(question_ids)) != len(question_ids):
            errors.append(f"{prefix}.tasks contains duplicate question_id values")
        if len(set(task_families)) != len(task_families):
            errors.append(f"{prefix}.tasks must use distinct task families")
        if len(set(task_families)) < int(minimum_families):
            errors.append(
                f"{prefix}.tasks must contain at least {minimum_families} "
                "distinct task families"
            )
        panel_question_ids[str(panel_id)] = set(question_ids)
        panel_task_families[str(panel_id)] = set(task_families)

    development_ids = panel_question_ids.get("development", set())
    held_out_ids = panel_question_ids.get("held_out", set())
    if development_ids & held_out_ids:
        errors.append("development and held_out question IDs must be disjoint")
    development_families = panel_task_families.get("development", set())
    held_out_families = panel_task_families.get("held_out", set())
    if development_families & held_out_families:
        errors.append("development and held_out task families must be disjoint")

    required_evidence = value.get("required_per_task_evidence")
    if not isinstance(required_evidence, list) or not required_evidence or any(
        not isinstance(item, str) or not item.strip() for item in required_evidence
    ):
        errors.append("required_per_task_evidence must contain nonempty strings")
    return sorted(set(errors))


def resolve_cross_family_eval_panel(
    protocol: Mapping[str, Any],
    *,
    panel_id: str,
    questions: Sequence[object],
) -> dict[str, Any]:
    errors = validate_cross_family_eval_protocol(protocol)
    if errors:
        raise ValueError("; ".join(errors))
    panel_name = str(panel_id or "").strip()
    panels = protocol["panels"]
    if panel_name not in panels:
        raise ValueError(
            "unknown cross-family evaluation panel: "
            f"{panel_name or '<missing>'}; available={sorted(panels)}"
        )
    panel = panels[panel_name]
    tasks = panel["tasks"]
    by_id = {
        str(getattr(question, "id", "") or ""): question for question in questions
    }
    missing_question_ids: list[str] = []
    family_mismatches: list[str] = []
    question_ids: list[str] = []
    task_families: list[str] = []
    for task in tasks:
        question_id = str(task["question_id"])
        expected_family = task_family_value(task["task_family"])
        question = by_id.get(question_id)
        if question is None:
            missing_question_ids.append(question_id)
            continue
        actual_family = primary_task_family_from_question(question)
        if actual_family != expected_family:
            family_mismatches.append(
                f"{question_id}: expected {expected_family}, got {actual_family}"
            )
        question_ids.append(question_id)
        task_families.append(actual_family)
    if missing_question_ids or family_mismatches:
        details: list[str] = []
        if missing_question_ids:
            details.append("missing question IDs: " + ", ".join(missing_question_ids))
        if family_mismatches:
            details.append("task-family mismatches: " + "; ".join(family_mismatches))
        raise ValueError("; ".join(details))
    minimum_families = int(protocol["minimum_distinct_task_families_per_panel"])
    if len(set(task_families)) < minimum_families:
        raise ValueError(
            f"panel {panel_name} resolved to fewer than {minimum_families} "
            "distinct task families"
        )
    return {
        "schema_version": CROSS_FAMILY_EVAL_PROTOCOL_SCHEMA_VERSION,
        "artifact_kind": "CrossFamilyEndToEndEvaluationPanelSelection",
        "protocol_id": str(protocol["protocol_id"]),
        "protocol_fingerprint": stable_hash(dict(protocol)),
        "protocol_panel": panel_name,
        "split_frozen_at": str(protocol["split_frozen_at"]),
        "split_frozen_at_base_commit": str(
            protocol["split_frozen_at_base_commit"]
        ),
        "question_source": str(protocol["question_source"]),
        "question_ids": question_ids,
        "task_families": task_families,
        "minimum_distinct_task_families": minimum_families,
        "fresh_start_required": True,
        "resume_forbidden": True,
        "task_learning_memory_forbidden": True,
        "component_eval_substitution_forbidden": True,
        "candidate_gate_independence_required": True,
        "confirmatory_source_outcome_blinding_required": True,
        "post_outcome_fresh_cohort_required": True,
        "confirmatory_candidate_seed_blinding_required": True,
        "evaluation_claude_model_tier": str(
            protocol["run_contract"]["evaluation_claude_model_tier"]
        ),
        "evaluation_claude_model": str(
            protocol["run_contract"]["evaluation_claude_model"]
        ),
        "all_live_anthropic_agents_exact_model_required": True,
        "sonnet_opus_live_calls_forbidden": True,
        "required_per_task_evidence": list(protocol["required_per_task_evidence"]),
        "proof_evidence_status": "EVALUATION_PROTOCOL_SELECTION_NOT_PROOF_EVIDENCE",
    }


def _evaluation_selection(context: Mapping[str, Any]) -> Mapping[str, Any]:
    value = context.get("cross_family_evaluation_protocol", {})
    return value if isinstance(value, Mapping) else {}


def candidate_gate_independence_required(context: Mapping[str, Any]) -> bool:
    selection = _evaluation_selection(context)
    return bool(
        selection.get("candidate_gate_independence_required") is True
        and selection.get("post_outcome_fresh_cohort_required") is True
    )


def confirmatory_candidate_seed_blinding_required(
    context: Mapping[str, Any],
) -> bool:
    return bool(
        candidate_gate_independence_required(context)
        and _evaluation_selection(context).get(
            "confirmatory_candidate_seed_blinding_required"
        )
        is True
    )


def confirmatory_evaluation_seed(
    context: Mapping[str, Any],
    *,
    fallback_seed: int,
) -> int:
    cohort = context.get(CONFIRMATORY_EVALUATION_COHORT_CONTEXT_KEY, {})
    seed = cohort.get("seed") if isinstance(cohort, Mapping) else None
    return seed if isinstance(seed, int) and not isinstance(seed, bool) else fallback_seed


def _new_cohort(
    *,
    question_id: str,
    protocol_fingerprint: str,
    base_seed: int,
    cohort_index: int,
    previous_cohort_id: str = "",
    trigger_outcome_id: str = "",
) -> dict[str, Any]:
    seed = (
        base_seed
        if cohort_index == 0
        else (base_seed + cohort_index * 1_000_003)
        % CONFIRMATORY_EVALUATION_SEED_MODULUS
    )
    identity = {
        "artifact_kind": CONFIRMATORY_EVALUATION_COHORT_KIND,
        "question_id": question_id,
        "protocol_fingerprint": protocol_fingerprint,
        "base_seed": base_seed,
        "cohort_index": cohort_index,
        "seed": seed,
        "previous_cohort_id": previous_cohort_id,
        "trigger_outcome_id": trigger_outcome_id,
        "seed_derived_from_empirical_outcome": False,
        "candidate_model_seed_disclosure": "WITHHELD",
    }
    return {
        **identity,
        "cohort_id": "confirmatory_evaluation_cohort:" + stable_hash(identity)[:20],
        "proof_evidence_status": "EVALUATION_COHORT_NOT_PROOF_EVIDENCE",
        "boundary": (
            "Runtime owns only cohort identity and an outcome-independent execution "
            "seed; it does not choose or edit research content."
        ),
    }


def _cohort_errors(
    value: Any,
    *,
    question_id: str,
    protocol_fingerprint: str,
) -> list[str]:
    if not isinstance(value, Mapping):
        return ["confirmatory evaluation cohort must be an object"]
    errors: list[str] = []
    if value.get("artifact_kind") != CONFIRMATORY_EVALUATION_COHORT_KIND:
        errors.append("confirmatory cohort artifact_kind is invalid")
    if value.get("question_id") != question_id:
        errors.append("confirmatory cohort question_id mismatch")
    if value.get("protocol_fingerprint") != protocol_fingerprint:
        errors.append("confirmatory cohort protocol fingerprint mismatch")
    base_seed = value.get("base_seed")
    index = value.get("cohort_index")
    seed = value.get("seed")
    if any(
        isinstance(item, bool) or not isinstance(item, int)
        for item in (base_seed, index, seed)
    ):
        errors.append("confirmatory cohort seed fields must be integers")
        return errors
    if index < 0:
        errors.append("confirmatory cohort index must be nonnegative")
        return errors
    previous_id = str(value.get("previous_cohort_id", "") or "")
    outcome_id = str(value.get("trigger_outcome_id", "") or "")
    if (index == 0 and (previous_id or outcome_id)) or (
        index > 0 and (not previous_id or not outcome_id)
    ):
        errors.append("confirmatory cohort prior-outcome lineage is invalid")
    expected = _new_cohort(
        question_id=question_id,
        protocol_fingerprint=protocol_fingerprint,
        base_seed=base_seed,
        cohort_index=index,
        previous_cohort_id=previous_id,
        trigger_outcome_id=outcome_id,
    )
    if seed != expected["seed"] or value.get("cohort_id") != expected["cohort_id"]:
        errors.append("confirmatory cohort identity or seed derivation mismatch")
    if value.get("seed_derived_from_empirical_outcome") is not False:
        errors.append("confirmatory cohort seed depends on empirical outcomes")
    if value.get("candidate_model_seed_disclosure") != "WITHHELD":
        errors.append("confirmatory cohort seed was disclosed to the candidate model")
    return sorted(set(errors))


def resolve_confirmatory_evaluation_cohort(
    context: Mapping[str, Any],
    *,
    question_id: str,
    execution_seed: int,
) -> tuple[dict[str, Any], list[str]]:
    if not candidate_gate_independence_required(context):
        return {}, []
    fingerprint = str(_evaluation_selection(context).get("protocol_fingerprint", "") or "")
    existing = context.get(CONFIRMATORY_EVALUATION_COHORT_CONTEXT_KEY, {})
    cohort = (
        dict(existing)
        if isinstance(existing, Mapping) and existing
        else _new_cohort(
            question_id=question_id,
            protocol_fingerprint=fingerprint,
            base_seed=execution_seed,
            cohort_index=0,
        )
    )
    errors = _cohort_errors(
        cohort,
        question_id=question_id,
        protocol_fingerprint=fingerprint,
    )
    if cohort.get("seed") != execution_seed:
        errors.append("confirmatory task seed does not match its cohort")
    return cohort, sorted(set(errors))


def advance_confirmatory_evaluation_cohort(
    context: Mapping[str, Any],
    *,
    confirmatory_outcome: Mapping[str, Any],
    question_id: str,
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    if not candidate_gate_independence_required(context):
        return {}, {}, []
    fingerprint = str(_evaluation_selection(context).get("protocol_fingerprint", "") or "")
    current = context.get(CONFIRMATORY_EVALUATION_COHORT_CONTEXT_KEY, {})
    errors = _cohort_errors(
        current,
        question_id=question_id,
        protocol_fingerprint=fingerprint,
    )
    outcome_id = str(
        confirmatory_outcome.get("feedback_id", "")
        or confirmatory_outcome.get("observation_id", "")
        or ""
    )
    outcome_cohort = confirmatory_outcome.get("confirmatory_evaluation_cohort", {})
    if (
        not outcome_id
        or confirmatory_outcome.get("question_id") != question_id
        or not isinstance(outcome_cohort, Mapping)
        or outcome_cohort.get("cohort_id")
        != (current.get("cohort_id") if isinstance(current, Mapping) else None)
    ):
        errors.append("confirmatory outcome does not match the active cohort")
    if errors:
        return {}, {}, sorted(set(errors))
    next_cohort = _new_cohort(
        question_id=question_id,
        protocol_fingerprint=fingerprint,
        base_seed=int(current["base_seed"]),
        cohort_index=int(current["cohort_index"]) + 1,
        previous_cohort_id=str(current["cohort_id"]),
        trigger_outcome_id=outcome_id,
    )
    transition_body = {
        "artifact_kind": CONFIRMATORY_EVALUATION_COHORT_TRANSITION_KIND,
        "question_id": question_id,
        "trigger_outcome_id": outcome_id,
        "from_cohort_id": current["cohort_id"],
        "from_seed": current["seed"],
        "to_cohort_id": next_cohort["cohort_id"],
        "to_seed": next_cohort["seed"],
        "fresh_seed": current["seed"] != next_cohort["seed"],
        "seed_derived_from_empirical_outcome": False,
        "runtime_selected_research_content": False,
    }
    transition = {
        **transition_body,
        "transition_id": (
            "confirmatory_evaluation_cohort_transition:"
            + stable_hash(transition_body)[:20]
        ),
        "proof_evidence_status": "EVALUATION_TRANSITION_NOT_PROOF_EVIDENCE",
        "boundary": (
            "Runtime allocates a fresh cohort after outcome-informed continuation; "
            "the model still chooses the worker and all research content."
        ),
    }
    return next_cohort, transition, []


def withhold_confirmatory_evaluation_seed(
    value: Any,
    *,
    parent_key: str = "",
    evaluator_owned: bool = False,
) -> Any:
    """Project evaluator-owned seeds out of model-visible material."""

    if isinstance(value, Mapping):
        private_fields = set()
        if value.get("artifact_kind") == CONFIRMATORY_EVALUATION_COHORT_KIND:
            private_fields = {"seed", "base_seed"}
        elif value.get("artifact_kind") == CONFIRMATORY_EVALUATION_COHORT_TRANSITION_KIND:
            private_fields = {"from_seed", "to_seed"}
        return {
            str(key): (
                "EVALUATOR_WITHHELD"
                if str(key) in private_fields or (evaluator_owned and str(key) == "runtime_seed")
                or (
                    str(key) in {"seed", "base_seed", "runtime_seed"}
                    and parent_key
                    in {
                        "actual_runtime_arguments",
                        "confirmatory_evaluation_cohort",
                        CONFIRMATORY_EVALUATION_COHORT_CONTEXT_KEY,
                        "runtime_budget",
                        "runtime_config",
                        "runtime_execution_plan",
                    }
                )
                else withhold_confirmatory_evaluation_seed(
                    child,
                    parent_key=str(key),
                    evaluator_owned=evaluator_owned,
                )
            )
            for key, child in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [
            withhold_confirmatory_evaluation_seed(child, parent_key=parent_key, evaluator_owned=evaluator_owned)
            for child in value
        ]
    return deepcopy(value)


def summarize_candidate_gate_independence(
    evidence_rows: Sequence[Mapping[str, Any]],
    *,
    architect_context: Mapping[str, Any],
) -> dict[str, Any]:
    required = candidate_gate_independence_required(architect_context)
    cohorts: dict[str, Mapping[str, Any]] = {}
    transitions: list[Mapping[str, Any]] = []
    n_execution_rows = 0
    for row in evidence_rows:
        payload = row.get("payload", {})
        if not isinstance(payload, Mapping):
            continue
        if row.get("evidence_type") == "simulation":
            cohort = payload.get("confirmatory_evaluation_cohort", {})
            if isinstance(cohort, Mapping) and cohort:
                n_execution_rows += 1
                cohorts[str(cohort.get("cohort_id", "") or "")] = cohort
        elif row.get("evidence_type") == "confirmatory_evaluation_cohort_transition":
            transition = payload.get("transition", {})
            if isinstance(transition, Mapping) and transition:
                transitions.append(transition)
    seed_to_ids: dict[tuple[str, int], set[str]] = {}
    for cohort_id, cohort in cohorts.items():
        seed = cohort.get("seed")
        if isinstance(seed, int) and not isinstance(seed, bool):
            seed_scope = (str(cohort.get("question_id", "") or ""), seed)
            seed_to_ids.setdefault(seed_scope, set()).add(cohort_id)
    post_outcome_ids = {
        cohort_id
        for cohort_id, cohort in cohorts.items()
        if int(cohort.get("cohort_index", 0) or 0) > 0
    }
    transition_targets = {
        str(row.get("to_cohort_id", "") or "") for row in transitions
    }
    errors = []
    if any(len(ids) > 1 for ids in seed_to_ids.values()):
        errors.append("distinct confirmatory cohorts for one question reused one seed")
    if post_outcome_ids - transition_targets:
        errors.append("post-outcome cohort execution lacks a recorded transition")
    if any(
        row.get("fresh_seed") is not True
        or row.get("seed_derived_from_empirical_outcome") is not False
        or row.get("runtime_selected_research_content") is not False
        for row in transitions
    ):
        errors.append("confirmatory cohort transition violated evaluator ownership")
    status = (
        "NOT_REQUIRED"
        if not required
        else "VIOLATION"
        if errors
        else "POST_OUTCOME_FRESH_COHORT_VERIFIED"
        if post_outcome_ids
        else "POST_OUTCOME_FRESH_COHORT_ALLOCATED_NOT_EXECUTED"
        if transitions
        else "NO_POST_OUTCOME_CONTINUATION_OBSERVED"
        if cohorts
        else "NO_CONFIRMATORY_COHORT_EXECUTION_OBSERVED"
    )
    return {
        "required": required,
        "status": status,
        "n_confirmatory_cohort_execution_rows": n_execution_rows,
        "n_distinct_executed_cohorts": len(cohorts),
        "n_post_outcome_cohort_transitions": len(transitions),
        "n_post_outcome_fresh_cohort_executions": len(post_outcome_ids),
        "validation_errors": errors,
        "candidate_gate_independence_verified": (
            status == "POST_OUTCOME_FRESH_COHORT_VERIFIED"
        ),
        "proof_evidence_status": "EVALUATION_INDEPENDENCE_NOT_PROOF_EVIDENCE",
    }
