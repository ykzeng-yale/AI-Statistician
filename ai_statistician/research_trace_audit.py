from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .proof_bank import get_obligation
from .research_knowledge import FORMAL_INFRASTRUCTURE_KNOWLEDGE, PRIMARY_KNOWLEDGE_BY_PROBLEM_CLASS


REQUIRED_RESEARCH_TRACE_KEYS = {
    "trace_version",
    "trace_kind",
    "created_at",
    "provenance",
    "question",
    "problem",
    "procedures",
    "knowledge",
    "paper_sources",
    "formal_subclaims",
    "simulations",
    "theorem_goals",
    "theory_plan",
    "status",
    "limitations",
}

READY_STATUS = "RESEARCH_TRACE_READY_WITH_FORMAL_GAPS"
SIM_FLAG_STATUS = "SIMULATION_FLAGGED_WITH_FORMAL_GAPS"
FORMAL_BLOCKED_STATUS = "FORMAL_BLOCKED"

LOCAL_FORMAL_SOURCE_KNOWLEDGE = {
    "local_mathlib_probability",
    "local_statinference_repo",
    "empirical_process_lean",
    "lean_stat_learning_theory",
    "legacy_ai_statistician_statinference",
}

FORMAL_SEARCH_KNOWLEDGE = {
    "lean_finder",
    "leandojo_reprover",
    "loogle",
    "openprover_pipeline",
}

SIMULATION_DIAGNOSIS_STATUSES = {
    "OK",
    "THEORY_OR_PROCEDURE_ISSUE",
    "IMPLEMENTATION_OR_NUMERICAL_ISSUE",
    "ENVIRONMENT_OR_DGP_ISSUE",
    "INSUFFICIENT_MC_PRECISION",
}

SIMULATION_ESCALATION_TARGETS = {
    "none",
    "theory_developer",
    "algorithm_engineer",
    "simulator_environment",
    "rerun_more_mc",
}


DIAGNOSTIC_METRIC_ALIASES: dict[str, tuple[str, ...]] = {
    "se_calibration": ("se_ratio", "mean_estimated_se", "empirical_se"),
    "conservativeness_ratio": ("mean_conservativeness_ratio",),
    "censoring_fraction": ("mean_censoring_fraction",),
    "contamination_fraction": ("mean_contamination_fraction", "target_contamination_fraction"),
    "privacy_noise_sd": ("mean_privacy_noise_sd",),
    "clipping_fraction": ("mean_clipping_fraction",),
    "sieve_dimension": ("polynomial_degree",),
    "alignment": ("mean_alignment", "alignment_sd"),
    "angle_error": ("mean_angle_error_rad",),
    "subspace_error": ("mean_subspace_error",),
    "explained_variance": ("mean_explained_variance_ratio",),
    "false_discovery_proportion": ("fdp_sd", "empirical_fdr"),
    "mean_stop_time": ("null_mean_stop_time", "alt_mean_stop_time"),
    "optional_stopping_rejection_rate": ("type1_error",),
}


@dataclass(frozen=True)
class ResearchTraceAuditRow:
    question_id: str
    trace_path: str
    ok: bool
    errors: tuple[str, ...] = ()


def audit_research_traces(run_dir: Path, out_dir: Path | None = None) -> dict[str, object]:
    """Validate research-lab traces against `research_benchmark_manifest.json`."""

    manifest_path = run_dir / "research_benchmark_manifest.json"
    manifest_errors: list[str] = []
    rows: list[ResearchTraceAuditRow] = []
    if not manifest_path.exists():
        manifest_errors.append(f"missing research benchmark manifest: {manifest_path}")
        manifest: dict[str, Any] = {}
        summaries: list[dict[str, Any]] = []
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            manifest_errors.append(f"failed to parse manifest JSON: {type(exc).__name__}: {exc}")
            manifest = {}
        summaries = list(manifest.get("questions", [])) if isinstance(manifest.get("questions"), list) else []

    manifest_provenance = manifest.get("provenance")
    n_ready = 0
    n_simulation_flagged = 0
    n_formal_blocked = 0
    for summary in summaries:
        question_id = str(summary.get("question", "<missing>"))
        trace_path = run_dir / f"{question_id}.json"
        errors: list[str] = []
        data: dict[str, Any] = {}
        if not trace_path.exists():
            errors.append(f"missing research trace file: {trace_path}")
        else:
            try:
                data = json.loads(trace_path.read_text(encoding="utf-8"))
            except Exception as exc:
                errors.append(f"failed to parse trace JSON: {type(exc).__name__}: {exc}")
        if data:
            errors.extend(_validate_research_trace(data, question_id, summary, manifest_provenance, run_dir))
            status = data.get("status")
            if status == READY_STATUS:
                n_ready += 1
            elif status == SIM_FLAG_STATUS:
                n_simulation_flagged += 1
            elif status == FORMAL_BLOCKED_STATUS:
                n_formal_blocked += 1
        rows.append(
            ResearchTraceAuditRow(
                question_id=question_id,
                trace_path=str(trace_path),
                ok=not errors,
                errors=tuple(errors),
            )
        )

    if manifest:
        if manifest.get("trace_kind") != "research_theory_lab":
            manifest_errors.append("manifest trace_kind is not research_theory_lab")
        if int(manifest.get("n_questions", -1)) != len(rows):
            manifest_errors.append("manifest n_questions does not match trace rows")
        if int(manifest.get("n_ready_with_gaps", -1)) != n_ready:
            manifest_errors.append("manifest n_ready_with_gaps does not match trace statuses")
        if int(manifest.get("n_simulation_flagged", -1)) != n_simulation_flagged:
            manifest_errors.append("manifest n_simulation_flagged does not match trace statuses")
        if int(manifest.get("n_formal_blocked", -1)) != n_formal_blocked:
            manifest_errors.append("manifest n_formal_blocked does not match trace statuses")

    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "manifest": str(manifest_path),
        "n_traces": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not manifest_errors and all(row.ok for row in rows),
        "manifest_errors": manifest_errors,
        "rows": [asdict(row) for row in rows],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "research_trace_audit_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
    return payload


def _validate_research_trace(
    data: dict[str, Any],
    question_id: str,
    summary: dict[str, Any],
    manifest_provenance: object,
    run_dir: Path,
) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_RESEARCH_TRACE_KEYS - set(data))
    if missing:
        errors.append(f"missing trace keys: {', '.join(missing)}")
    if data.get("trace_version") != 1:
        errors.append(f"unexpected trace_version: {data.get('trace_version')!r}")
    if data.get("trace_kind") != "research_theory_lab":
        errors.append(f"unexpected trace_kind: {data.get('trace_kind')!r}")
    if manifest_provenance is not None and data.get("provenance") != manifest_provenance:
        errors.append("trace provenance does not match research manifest provenance")

    question = data.get("question")
    if not isinstance(question, dict) or question.get("id") != question_id:
        errors.append("trace question.id does not match filename/manifest")
    problem = data.get("problem")
    if not isinstance(problem, dict):
        errors.append("problem section missing or not an object")
        diagnostics: tuple[str, ...] = ()
        stress_tests: tuple[str, ...] = ()
        problem_class = ""
    else:
        for key in (
            "problem_class",
            "dgp",
            "estimand",
            "assumptions",
            "asymptotic_regime",
            "diagnostics",
            "stress_tests",
            "extraction_evidence",
        ):
            if not problem.get(key):
                errors.append(f"problem missing {key}")
        if problem.get("problem_class") != summary.get("problem_class"):
            errors.append("problem_class does not match manifest summary")
        problem_class = str(problem.get("problem_class", ""))
        evidence = problem.get("extraction_evidence")
        if isinstance(evidence, dict) and problem.get("problem_class") != "unsupported_frontier_question":
            for key in ("problem_class", "dgp", "estimand", "assumptions", "asymptotic_regime"):
                if not evidence.get(key):
                    errors.append(f"problem extraction_evidence missing {key}")
        diagnostics = tuple(str(item) for item in problem.get("diagnostics", ()) if str(item))
        stress_tests = tuple(str(item) for item in problem.get("stress_tests", ()) if str(item))

    if data.get("status") != summary.get("status"):
        errors.append("trace status does not match manifest summary")

    procedures = data.get("procedures")
    procedure_ids: set[str] = set()
    procedure_theorem_goal_ids: set[str] = set()
    algorithm_hashes: dict[str, str] = {}
    if not isinstance(procedures, list) or not procedures:
        errors.append("procedures section missing or empty")
    else:
        for idx, procedure in enumerate(procedures):
            if not isinstance(procedure, dict):
                errors.append(f"procedure {idx} is not an object")
                continue
            for key in ("id", "name", "role", "formula", "informal_derivation", "algorithm", "theorem_goals"):
                if not procedure.get(key):
                    errors.append(f"procedure {idx} missing {key}")
            if procedure.get("id"):
                procedure_ids.add(str(procedure["id"]))
            raw_goals = procedure.get("theorem_goals")
            if not isinstance(raw_goals, list) or not raw_goals:
                errors.append(f"procedure {idx} theorem_goals is not a nonempty list")
            else:
                procedure_theorem_goal_ids.update(str(goal_id) for goal_id in raw_goals if str(goal_id))
            algorithm_spec = procedure.get("algorithm_spec")
            if not isinstance(algorithm_spec, dict):
                errors.append(f"procedure {idx} missing algorithm_spec")
            else:
                if algorithm_spec.get("id") != procedure.get("algorithm"):
                    errors.append(f"procedure {idx} algorithm_spec.id does not match algorithm")
                if algorithm_spec.get("registry_status") != "vetted":
                    errors.append(f"procedure {idx} algorithm registry_status is not vetted")
                implementation_hash = str(algorithm_spec.get("implementation_hash", ""))
                if len(implementation_hash) != 64:
                    errors.append(f"procedure {idx} implementation_hash is not a SHA-256 hex digest")
                if procedure.get("id"):
                    algorithm_hashes[str(procedure["id"])] = implementation_hash
        if procedure_ids != set(summary.get("procedures", [])):
            errors.append("procedure ids do not match manifest summary")
        expected_algorithms = {
            str(row.get("procedure_id")): str(row.get("implementation_hash", ""))
            for row in summary.get("algorithms", [])
            if isinstance(row, dict)
        }
        if expected_algorithms and expected_algorithms != algorithm_hashes:
            errors.append("algorithm implementation hashes do not match manifest summary")

    theorem_goals = data.get("theorem_goals")
    theorem_goal_ids: set[str] = set()
    theorem_goals_by_id: dict[str, dict[str, Any]] = {}
    theorem_goal_proof_obligations: dict[str, list[str]] = {}
    if not isinstance(theorem_goals, list) or not theorem_goals:
        errors.append("theorem_goals section missing or empty")
    else:
        for idx, goal in enumerate(theorem_goals):
            if not isinstance(goal, dict):
                errors.append(f"theorem goal {idx} is not an object")
                continue
            for key in ("id", "title", "informal_statement", "proof_strategy", "status", "required_primitives"):
                if not goal.get(key):
                    errors.append(f"theorem goal {idx} missing {key}")
            if goal.get("status") == "FORMAL_GAP" and not goal.get("required_primitives"):
                errors.append(f"theorem goal {idx} formal gap missing required_primitives")
            if goal.get("id"):
                goal_id = str(goal["id"])
                theorem_goal_ids.add(goal_id)
                theorem_goals_by_id[goal_id] = goal
                raw_support = goal.get("proof_obligations", [])
                if raw_support is None:
                    raw_support = []
                if not isinstance(raw_support, list):
                    errors.append(f"theorem goal {idx} proof_obligations is not a list")
                    raw_support = []
                support_ids = [str(item) for item in raw_support if str(item)]
                theorem_goal_proof_obligations[goal_id] = support_ids
                for obligation_id in support_ids:
                    try:
                        get_obligation(obligation_id)
                    except KeyError:
                        errors.append(f"theorem goal {idx} references unknown proof obligation {obligation_id}")
        dangling_procedure_goals = sorted(procedure_theorem_goal_ids - theorem_goal_ids)
        if dangling_procedure_goals:
            errors.append(
                "procedure theorem_goals missing theorem_goal definitions: "
                + ", ".join(dangling_procedure_goals)
            )
        unattached_theorem_goals = sorted(theorem_goal_ids - procedure_theorem_goal_ids)
        if unattached_theorem_goals:
            errors.append(
                "theorem_goals not attached to any procedure: "
                + ", ".join(unattached_theorem_goals)
            )

    knowledge = data.get("knowledge")
    if not isinstance(knowledge, list) or not knowledge:
        errors.append("knowledge retrieval section missing or empty")
    else:
        expected_primary = PRIMARY_KNOWLEDGE_BY_PROBLEM_CLASS.get(problem_class)
        knowledge_ids: set[str] = set()
        method_card_ids: set[str] = set()
        local_formal_ids: set[str] = set()
        search_ids: set[str] = set()
        for idx, card in enumerate(knowledge):
            if not isinstance(card, dict):
                errors.append(f"knowledge card {idx} is not an object")
                continue
            for key in ("id", "title", "source_type", "location", "summary", "tags"):
                if not card.get(key):
                    errors.append(f"knowledge card {idx} missing {key}")
            card_id = str(card.get("id", ""))
            knowledge_ids.add(card_id)
            if card.get("source_type") == "statistical_method":
                method_card_ids.add(card_id)
                if (
                    expected_primary
                    and card_id == expected_primary
                    and problem_class
                    and problem_class not in set(str(tag) for tag in card.get("tags", []))
                ):
                    errors.append(f"statistical method card {card_id} missing problem_class tag {problem_class}")
            if card_id in LOCAL_FORMAL_SOURCE_KNOWLEDGE:
                local_formal_ids.add(card_id)
            if card_id in FORMAL_SEARCH_KNOWLEDGE:
                search_ids.add(card_id)
        if expected_primary and expected_primary not in knowledge_ids:
            errors.append(f"knowledge retrieval missing primary method card: {expected_primary}")
        if not method_card_ids:
            errors.append("knowledge retrieval has no statistical_method card")
        if not (knowledge_ids & set(FORMAL_INFRASTRUCTURE_KNOWLEDGE)):
            errors.append("knowledge retrieval has no Lean/search/local formalization infrastructure card")
        if not local_formal_ids:
            errors.append("knowledge retrieval has no local Lean/stat formal source card")
        if not search_ids:
            errors.append("knowledge retrieval has no formal retrieval/search system card")

    paper_sources = data.get("paper_sources")
    summary_paper_sources = summary.get("paper_sources", [])
    if not isinstance(paper_sources, list) or not paper_sources:
        errors.append("paper_sources retrieval section missing or empty")
    else:
        frontier_or_ai_hits = 0
        for idx, source in enumerate(paper_sources):
            if not isinstance(source, dict):
                errors.append(f"paper source {idx} is not an object")
                continue
            for key in ("id", "title", "source_type", "source_path", "score", "matched_terms"):
                if source.get(key) in (None, "", []):
                    errors.append(f"paper source {idx} missing {key}")
            if source.get("source_type") in {"frontier_stat_paper", "ai_math_paper"}:
                frontier_or_ai_hits += 1
            if source.get("source_type") == "frontier_stat_paper":
                withheld = set(str(item) for item in source.get("withheld_fields", []))
                if not {"expected_theoretical_results", "evaluation_prompt"} <= withheld:
                    errors.append(f"frontier paper source {idx} does not record withheld benchmark fields")
        if not frontier_or_ai_hits:
            errors.append("paper source retrieval has no frontier-stat or AI-for-math paper hit")
        if isinstance(summary_paper_sources, list) and not summary_paper_sources:
            errors.append("manifest summary missing compact paper source hits")

    formal_subclaims = data.get("formal_subclaims")
    if not isinstance(formal_subclaims, list) or not formal_subclaims:
        errors.append("formal_subclaims section missing or empty")
    else:
        errors.extend(_validate_formal_subclaims(formal_subclaims, theorem_goals_by_id, summary, run_dir))
        errors.extend(_validate_theorem_goal_proof_obligations(formal_subclaims, theorem_goal_proof_obligations))
        errors.extend(
            _validate_procedure_theorem_goal_coverage(
                formal_subclaims,
                procedure_theorem_goal_ids,
            )
        )

    theory_plan = data.get("theory_plan")
    if not isinstance(theory_plan, dict) or not theory_plan:
        errors.append("theory_plan section missing or empty")
    else:
        errors.extend(
            _validate_theory_plan(
                theory_plan,
                problem,
                procedure_ids,
                theorem_goal_ids,
                data.get("status"),
            )
        )

    simulations = data.get("simulations")
    if not isinstance(simulations, list) or not simulations:
        errors.append("simulations section missing or empty")
    else:
        for idx, simulation in enumerate(simulations):
            if not isinstance(simulation, dict):
                errors.append(f"simulation {idx} is not an object")
                continue
            procedure_id = simulation.get("procedure_id")
            if procedure_id not in procedure_ids:
                errors.append(f"simulation {idx} procedure_id is not a planned procedure")
            if not isinstance(simulation.get("metrics"), dict) or not simulation["metrics"]:
                errors.append(f"simulation {idx} metrics missing")
            else:
                missing_diagnostics = [
                    diagnostic
                    for diagnostic in diagnostics
                    if not _diagnostic_covered(diagnostic, simulation["metrics"])
                ]
                if missing_diagnostics:
                    errors.append(
                        f"simulation {idx} does not cover diagnostics: {', '.join(missing_diagnostics)}"
                    )
            if stress_tests:
                simulation_stress_tests = simulation.get("stress_tests")
                if not isinstance(simulation_stress_tests, list) or not simulation_stress_tests:
                    errors.append(f"simulation {idx} stress_tests ledger missing")
                    simulation_stress_tests = []
                missing_stress_tests = sorted(set(stress_tests) - set(str(item) for item in simulation_stress_tests))
                if missing_stress_tests:
                    errors.append(
                        f"simulation {idx} does not cover stress_tests: {', '.join(missing_stress_tests)}"
                    )
                stress_metrics = simulation.get("stress_test_metrics")
                if not isinstance(stress_metrics, dict) or not stress_metrics:
                    errors.append(f"simulation {idx} stress_test_metrics missing")
                else:
                    for stress_test in stress_tests:
                        row = stress_metrics.get(stress_test)
                        if not isinstance(row, dict):
                            errors.append(f"simulation {idx} stress metric missing for {stress_test}")
                            continue
                        for key in ("covered", "stress_flag", "primary_value", "threshold"):
                            if key not in row or not isinstance(row[key], (int, float)):
                                errors.append(f"simulation {idx} stress metric {stress_test} missing numeric {key}")
            if not isinstance(simulation.get("passed"), bool):
                errors.append(f"simulation {idx} passed flag missing")
            if not simulation.get("feedback"):
                errors.append(f"simulation {idx} feedback missing")
            diagnosis = simulation.get("diagnosis")
            if not isinstance(diagnosis, dict) or not diagnosis:
                errors.append(f"simulation {idx} diagnosis missing")
            else:
                diagnosis_status = diagnosis.get("status")
                escalate_to = diagnosis.get("escalate_to")
                if diagnosis_status not in SIMULATION_DIAGNOSIS_STATUSES:
                    errors.append(f"simulation {idx} diagnosis.status invalid")
                if escalate_to not in SIMULATION_ESCALATION_TARGETS:
                    errors.append(f"simulation {idx} diagnosis.escalate_to invalid")
                if bool(simulation.get("passed")):
                    if diagnosis_status != "OK":
                        errors.append(f"simulation {idx} passed but diagnosis is not OK")
                    if escalate_to != "none":
                        errors.append(f"simulation {idx} passed but escalation target is not none")
                elif diagnosis_status == "OK":
                    errors.append(f"simulation {idx} failed but diagnosis is OK")
                if diagnosis_status != "OK" and not diagnosis.get("failed_diagnostics"):
                    errors.append(f"simulation {idx} non-OK diagnosis lacks failed_diagnostics")
                if not diagnosis.get("rationale"):
                    errors.append(f"simulation {idx} diagnosis rationale missing")
                if not isinstance(diagnosis.get("metric_evidence"), dict):
                    errors.append(f"simulation {idx} diagnosis metric_evidence missing")

    limitations = data.get("limitations")
    gap_count = int(summary.get("formal", {}).get("gaps", 0)) if isinstance(summary.get("formal"), dict) else 0
    if gap_count and not limitations:
        errors.append("formal gaps exist but limitations section is empty")
    return errors


def _validate_theorem_goal_proof_obligations(
    formal_subclaims: list[Any],
    theorem_goal_proof_obligations: dict[str, list[str]],
) -> list[str]:
    errors: list[str] = []
    proved_ids = {
        str(subclaim.get("proof_obligation_id"))
        for subclaim in formal_subclaims
        if isinstance(subclaim, dict) and subclaim.get("status") == "PROVED" and subclaim.get("proof_obligation_id")
    }
    for goal_id, support_ids in theorem_goal_proof_obligations.items():
        if not support_ids:
            continue
        missing = sorted(set(support_ids) - proved_ids)
        if missing:
            errors.append(
                f"theorem goal {goal_id} proof_obligations are not verified subclaims: "
                + ", ".join(missing)
            )
    return errors


def _validate_procedure_theorem_goal_coverage(
    formal_subclaims: list[Any],
    procedure_theorem_goal_ids: set[str],
) -> list[str]:
    errors: list[str] = []
    if not procedure_theorem_goal_ids:
        return errors
    proved_ids: set[str] = set()
    gap_goal_ids: set[str] = set()
    for subclaim in formal_subclaims:
        if not isinstance(subclaim, dict):
            continue
        if subclaim.get("status") == "PROVED" and subclaim.get("proof_obligation_id"):
            proved_ids.add(str(subclaim["proof_obligation_id"]))
            if subclaim.get("id"):
                proved_ids.add(str(subclaim["id"]).split(":")[-1])
        elif subclaim.get("status") == "FORMAL_GAP" and subclaim.get("id"):
            gap_goal_ids.add(str(subclaim["id"]).split(":")[-1])
    covered = proved_ids | gap_goal_ids
    missing = sorted(procedure_theorem_goal_ids - covered)
    if missing:
        errors.append(
            "procedure theorem_goals not covered by proved subclaims or formal gaps: "
            + ", ".join(missing)
        )
    return errors


def _validate_theory_plan(
    theory_plan: dict[str, Any],
    problem: object,
    procedure_ids: set[str],
    theorem_goal_ids: set[str],
    status: object,
) -> list[str]:
    errors: list[str] = []
    if theory_plan.get("plan_version") != 1:
        errors.append("theory_plan plan_version is not 1")
    if theory_plan.get("status") != status:
        errors.append("theory_plan status does not match trace status")

    problem_formalization = theory_plan.get("problem_formalization")
    if not isinstance(problem_formalization, dict):
        errors.append("theory_plan problem_formalization missing")
    elif isinstance(problem, dict):
        for key in ("question_id", "problem_class", "dgp", "estimand", "asymptotic_regime"):
            if problem_formalization.get(key) != problem.get(key):
                errors.append(f"theory_plan problem_formalization.{key} does not match problem")
        if set(problem_formalization.get("assumptions", []) or []) != set(problem.get("assumptions", []) or []):
            errors.append("theory_plan assumptions do not match problem")

    candidate_procedures = theory_plan.get("candidate_procedures")
    if not isinstance(candidate_procedures, list) or not candidate_procedures:
        errors.append("theory_plan candidate_procedures missing")
    else:
        plan_procedure_ids = {str(row.get("id", "")) for row in candidate_procedures if isinstance(row, dict)}
        if plan_procedure_ids != procedure_ids:
            errors.append("theory_plan candidate_procedures do not match trace procedures")
        for idx, row in enumerate(candidate_procedures):
            if not isinstance(row, dict):
                errors.append(f"theory_plan candidate_procedure {idx} is not an object")
                continue
            for key in ("id", "role", "algorithm", "theorem_goals", "simulation_design"):
                if not row.get(key):
                    errors.append(f"theory_plan candidate_procedure {idx} missing {key}")

    roadmap = theory_plan.get("theorem_roadmap")
    if not isinstance(roadmap, list) or not roadmap:
        errors.append("theory_plan theorem_roadmap missing")
    else:
        roadmap_ids = {str(row.get("id", "")) for row in roadmap if isinstance(row, dict)}
        if roadmap_ids != theorem_goal_ids:
            errors.append("theory_plan theorem_roadmap does not match theorem_goals")
        for idx, row in enumerate(roadmap):
            if not isinstance(row, dict):
                errors.append(f"theory_plan theorem_roadmap {idx} is not an object")
                continue
            for key in ("id", "title", "status", "informal_statement", "proof_strategy", "required_primitives"):
                if not row.get(key):
                    errors.append(f"theory_plan theorem_roadmap {idx} missing {key}")

    verification = theory_plan.get("formal_verification_plan")
    if not isinstance(verification, dict):
        errors.append("theory_plan formal_verification_plan missing")
    else:
        if not isinstance(verification.get("proved_obligations"), list):
            errors.append("theory_plan formal_verification_plan proved_obligations missing")
        if not isinstance(verification.get("formal_gaps"), list):
            errors.append("theory_plan formal_verification_plan formal_gaps missing")

    simulation_plan = theory_plan.get("simulation_plan")
    if not isinstance(simulation_plan, dict):
        errors.append("theory_plan simulation_plan missing")
    elif not simulation_plan.get("procedure_runs"):
        errors.append("theory_plan simulation_plan procedure_runs missing")

    agenda = theory_plan.get("next_iteration_agenda")
    if not isinstance(agenda, dict):
        errors.append("theory_plan next_iteration_agenda missing")
    else:
        if agenda.get("agenda_version") != 1:
            errors.append("theory_plan next_iteration_agenda agenda_version is not 1")
        items = agenda.get("items")
        if not isinstance(items, list) or not items:
            errors.append("theory_plan next_iteration_agenda items missing")
        else:
            for idx, item in enumerate(items):
                if not isinstance(item, dict):
                    errors.append(f"theory_plan next_iteration_agenda item {idx} is not an object")
                    continue
                for key in ("id", "owner_agent", "trigger", "priority", "action", "evidence"):
                    if not item.get(key):
                        errors.append(f"theory_plan next_iteration_agenda item {idx} missing {key}")
        owner_counts = agenda.get("owner_counts")
        if not isinstance(owner_counts, dict) or not owner_counts:
            errors.append("theory_plan next_iteration_agenda owner_counts missing")
        if not agenda.get("stop_condition"):
            errors.append("theory_plan next_iteration_agenda stop_condition missing")

    retrieval_context = theory_plan.get("retrieval_context")
    if not isinstance(retrieval_context, dict):
        errors.append("theory_plan retrieval_context missing")
    else:
        if not retrieval_context.get("knowledge_cards"):
            errors.append("theory_plan retrieval_context knowledge_cards missing")
        if not retrieval_context.get("paper_sources"):
            errors.append("theory_plan retrieval_context paper_sources missing")

    honesty = theory_plan.get("honesty_boundary")
    if not isinstance(honesty, dict):
        errors.append("theory_plan honesty_boundary missing")
    elif honesty.get("full_frontier_theorem_proved") is not False:
        errors.append("theory_plan honesty_boundary must not claim full frontier theorem proof")
    return errors


def _diagnostic_covered(diagnostic: str, metrics: dict[str, Any]) -> bool:
    keys = set(metrics)
    aliases = DIAGNOSTIC_METRIC_ALIASES.get(diagnostic, ())
    return diagnostic in keys or any(alias in keys for alias in aliases)


def _validate_formal_subclaims(
    formal_subclaims: list[Any],
    theorem_goals_by_id: dict[str, dict[str, Any]],
    summary: dict[str, Any],
    run_dir: Path,
) -> list[str]:
    errors: list[str] = []
    theorem_goal_ids = set(theorem_goals_by_id)
    proved = gaps = failed = formalized_gaps = 0
    proved_ids = {
        str(subclaim.get("proof_obligation_id"))
        for subclaim in formal_subclaims
        if isinstance(subclaim, dict) and subclaim.get("status") == "PROVED" and subclaim.get("proof_obligation_id")
    }
    for idx, subclaim in enumerate(formal_subclaims):
        if not isinstance(subclaim, dict):
            errors.append(f"formal subclaim {idx} is not an object")
            continue
        status = subclaim.get("status")
        if status == "PROVED":
            proved += 1
            if subclaim.get("claim_type") != "lean_obligation":
                errors.append(f"proved subclaim {idx} is not a lean_obligation")
            if not subclaim.get("proof_obligation_id"):
                errors.append(f"proved subclaim {idx} missing proof_obligation_id")
            if not subclaim.get("lean_statement"):
                errors.append(f"proved subclaim {idx} missing lean_statement")
            if not subclaim.get("verifier"):
                errors.append(f"proved subclaim {idx} missing verifier")
            strength = subclaim.get("verification_strength")
            if not strength:
                errors.append(f"proved subclaim {idx} missing verification_strength")
            if not isinstance(subclaim.get("kernel_verified"), bool):
                errors.append(f"proved subclaim {idx} kernel_verified flag missing")
            if strength == "axle_lean_kernel":
                if subclaim.get("formalization_status") != "kernel_verified_proof":
                    errors.append(f"proved subclaim {idx} AXLE proof status is not kernel_verified_proof")
                if not subclaim.get("kernel_verified"):
                    errors.append(f"proved subclaim {idx} AXLE proof is not marked kernel_verified")
            elif strength == "mock_static_check":
                if subclaim.get("formalization_status") != "mock_verified_proof":
                    errors.append(f"proved subclaim {idx} mock proof status is not mock_verified_proof")
                if subclaim.get("kernel_verified"):
                    errors.append(f"proved subclaim {idx} mock proof must not be marked kernel_verified")
            else:
                errors.append(f"proved subclaim {idx} has unknown verification_strength: {strength!r}")
            if subclaim.get("errors"):
                errors.append(f"proved subclaim {idx} has verifier errors")
            errors.extend(_validate_proof_dependencies(idx, subclaim, proved_ids))
        elif status == "FORMAL_GAP":
            gaps += 1
            if subclaim.get("claim_type") != "theory_gap":
                errors.append(f"gap subclaim {idx} is not a theory_gap")
            if not subclaim.get("gap_reason"):
                errors.append(f"gap subclaim {idx} missing gap_reason")
            if subclaim.get("lean_statement"):
                formalized_gaps += 1
                if "FORMAL_GAP" not in str(subclaim["lean_statement"]):
                    errors.append(f"gap subclaim {idx} Lean skeleton does not identify FORMAL_GAP status")
                if "Retrieved local Lean/StatInference candidates" not in str(subclaim["lean_statement"]):
                    errors.append(f"gap subclaim {idx} Lean skeleton missing retrieved formal-source candidates")
                if "Primitive-level local candidates" not in str(subclaim["lean_statement"]):
                    errors.append(f"gap subclaim {idx} Lean skeleton missing primitive-level candidates")
                artifact_path = subclaim.get("artifact_path")
                if not artifact_path:
                    errors.append(f"gap subclaim {idx} missing artifact_path")
                elif not _artifact_exists(Path(str(artifact_path)), run_dir):
                    errors.append(f"gap subclaim {idx} artifact_path does not exist: {artifact_path}")
            hits = subclaim.get("formal_source_hits")
            if not isinstance(hits, list) or not hits:
                errors.append(f"gap subclaim {idx} missing formal_source_hits")
            else:
                for hit_idx, hit in enumerate(hits[:5]):
                    if not isinstance(hit, dict):
                        errors.append(f"gap subclaim {idx} formal_source_hit {hit_idx} is not an object")
                        continue
                    for key in ("source_id", "path", "line", "kind", "name", "score", "matched_terms"):
                        if hit.get(key) in (None, "", []):
                            errors.append(f"gap subclaim {idx} formal_source_hit {hit_idx} missing {key}")
            if subclaim.get("id"):
                goal_id = str(subclaim["id"]).split(":")[-1]
                if theorem_goal_ids and goal_id not in theorem_goal_ids:
                    errors.append(f"gap subclaim {idx} does not map to a theorem goal")
                primitive_hits = subclaim.get("primitive_formal_source_hits")
                goal = theorem_goals_by_id.get(goal_id)
                if goal is not None:
                    required_primitives = tuple(str(item) for item in goal.get("required_primitives", []) if str(item))
                else:
                    required_primitives = ()
                if required_primitives:
                    if not isinstance(primitive_hits, dict) or not primitive_hits:
                        errors.append(f"gap subclaim {idx} missing primitive_formal_source_hits")
                    else:
                        missing = sorted(set(required_primitives) - set(str(key) for key in primitive_hits))
                        if missing:
                            errors.append(
                                f"gap subclaim {idx} primitive_formal_source_hits missing primitives: "
                                + ", ".join(missing)
                            )
                        for primitive in required_primitives:
                            rows = primitive_hits.get(primitive)
                            if not isinstance(rows, list) or not rows:
                                errors.append(f"gap subclaim {idx} primitive {primitive} has no formal-source hits")
                                continue
                            if not any(isinstance(row, dict) and row.get("name") for row in rows):
                                errors.append(
                                    f"gap subclaim {idx} primitive {primitive} hit rows contain no declaration names"
                                )
        elif status == "FAILED":
            failed += 1
            if not subclaim.get("errors"):
                errors.append(f"failed subclaim {idx} has no errors")
        else:
            errors.append(f"formal subclaim {idx} has unknown status: {status!r}")
    expected = summary.get("formal", {})
    if isinstance(expected, dict):
        if int(expected.get("proved", -1)) != proved:
            errors.append("proved subclaim count does not match manifest summary")
        if int(expected.get("gaps", -1)) != gaps:
            errors.append("gap subclaim count does not match manifest summary")
        if int(expected.get("failed", -1)) != failed:
            errors.append("failed subclaim count does not match manifest summary")
        if int(expected.get("formalized_gaps", -1)) != formalized_gaps:
            errors.append("formalized gap count does not match manifest summary")
    return errors


def _validate_proof_dependencies(
    idx: int,
    subclaim: dict[str, Any],
    proved_ids: set[str],
) -> list[str]:
    errors: list[str] = []
    obligation_id = subclaim.get("proof_obligation_id")
    raw_dependencies = subclaim.get("proof_dependencies", [])
    if not isinstance(raw_dependencies, list):
        errors.append(f"proved subclaim {idx} proof_dependencies is not a list")
        return errors
    dependencies = [str(dep) for dep in raw_dependencies]
    if any(not dep for dep in dependencies):
        errors.append(f"proved subclaim {idx} has empty proof dependency id")
    if obligation_id and str(obligation_id) in dependencies:
        errors.append(f"proved subclaim {idx} depends on itself")
    try:
        obligation = get_obligation(str(obligation_id))
    except Exception as exc:
        errors.append(f"proved subclaim {idx} references unknown obligation: {exc}")
        return errors
    if tuple(dependencies) != obligation.depends_on:
        errors.append(
            f"proved subclaim {idx} dependency metadata mismatch: "
            f"trace={dependencies}, proof_bank={list(obligation.depends_on)}"
        )
    for dependency in dependencies:
        try:
            get_obligation(dependency)
        except Exception as exc:
            errors.append(f"proved subclaim {idx} has unknown dependency {dependency!r}: {exc}")
        if dependency in proved_ids:
            continue
        # The dependency may be verified by the global proof-bank audit but not
        # selected for this particular problem class; that is allowed. The trace
        # still records the edge so the release audit can check the full graph.
    return errors


def _artifact_exists(path: Path, run_dir: Path) -> bool:
    if path.exists():
        return True
    return (run_dir / path).exists()
