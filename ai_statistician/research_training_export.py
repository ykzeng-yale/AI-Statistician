from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


RESEARCH_TRAINING_EXPORT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ResearchSftExample:
    schema_version: int
    example_id: str
    split: str
    task: str
    prompt: str
    completion: str
    question_id: str
    trace_path: str
    problem_class: str
    procedure_ids: tuple[str, ...]
    theorem_goal_ids: tuple[str, ...]
    formal_subclaim_ids: tuple[str, ...]
    simulation_ids: tuple[str, ...]
    tags: tuple[str, ...]


@dataclass(frozen=True)
class ResearchGrpoTask:
    schema_version: int
    task_id: str
    task: str
    prompt: str
    reference_completion: str
    reward: float
    reward_source: str
    question_id: str
    trace_path: str
    problem_class: str
    tags: tuple[str, ...]


def export_research_training_dataset(
    run_dir: Path,
    out_dir: Path,
    *,
    validation_fraction: float = 0.2,
    base_model: str = "untrained-trace-export",
) -> dict[str, object]:
    """Export audited research traces as agent-training examples.

    This is a dataset exporter, not a trainer. It turns the production trace
    format into supervised examples for the theory-lab stack:
    problem formalization, theory-plan generation, simulation critique, and
    formal-gap routing. The export deliberately keeps GRPO tasks as
    verifier/simulator-scored records and does not claim any model weights were
    updated.
    """

    if not 0.0 <= validation_fraction < 1.0:
        raise ValueError("validation_fraction must be in [0.0, 1.0)")
    traces = _load_research_traces(run_dir)
    examples: list[ResearchSftExample] = []
    grpo_tasks: list[ResearchGrpoTask] = []
    for trace_path, trace in traces:
        examples.extend(_sft_examples_for_trace(trace_path, trace, validation_fraction))
        grpo_tasks.extend(_grpo_tasks_for_trace(trace_path, trace))

    out_dir.mkdir(parents=True, exist_ok=True)
    train_path = out_dir / "research_sft_train.jsonl"
    validation_path = out_dir / "research_sft_validation.jsonl"
    all_path = out_dir / "research_sft_all.jsonl"
    grpo_path = out_dir / "research_grpo_tasks.jsonl"
    _write_jsonl(train_path, [row for row in examples if row.split == "train"])
    _write_jsonl(validation_path, [row for row in examples if row.split == "validation"])
    _write_jsonl(all_path, examples)
    _write_jsonl(grpo_path, grpo_tasks)

    by_task = _count_by_task(examples)
    grpo_by_task = _count_by_task(grpo_tasks)
    manifest = {
        "schema_version": RESEARCH_TRAINING_EXPORT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "base_model": base_model,
        "validation_fraction": validation_fraction,
        "n_traces": len(traces),
        "n_sft_examples": len(examples),
        "n_train": sum(1 for row in examples if row.split == "train"),
        "n_validation": sum(1 for row in examples if row.split == "validation"),
        "n_grpo_tasks": len(grpo_tasks),
        "by_task": by_task,
        "grpo_by_task": grpo_by_task,
        "train_jsonl": str(train_path),
        "validation_jsonl": str(validation_path),
        "all_jsonl": str(all_path),
        "grpo_jsonl": str(grpo_path),
        "legacy_training_manifest": str(out_dir / "legacy_training_manifest.json"),
        "dataset_fingerprint": stable_hash([asdict(row) for row in examples]),
        "grpo_fingerprint": stable_hash([asdict(row) for row in grpo_tasks]),
        "all_ok": _all_ok(traces, examples),
        "limitations": [
            "exports trace-supervised examples only; no model weights are trained",
            "deterministic v1 labels mirror the current registry-gated system and can encode its limitations",
            "simulation GRPO rewards are coarse pass/fail signals, not dense process rewards",
            "formal-gap routing examples preserve honest gaps and do not provide missing Lean proofs",
        ],
    }
    legacy = {
        "run_id": f"research_training:{stable_hash([str(run_dir), manifest['dataset_fingerprint']])[:12]}",
        "base_model": base_model,
        "sft_examples": [asdict(row) for row in examples],
        "dpo_pairs": [],
        "grpo_tasks": [asdict(row) for row in grpo_tasks],
        "metadata": {
            "schema_version": str(RESEARCH_TRAINING_EXPORT_SCHEMA_VERSION),
            "source_run_dir": str(run_dir),
            "n_traces": str(len(traces)),
            "n_sft_examples": str(len(examples)),
            "n_grpo_tasks": str(len(grpo_tasks)),
            "dataset_fingerprint": str(manifest["dataset_fingerprint"]),
        },
    }
    (out_dir / "legacy_training_manifest.json").write_text(
        json.dumps(legacy, indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / "research_training_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / "research_training.md").write_text(_markdown_report(manifest), encoding="utf-8")
    return manifest


def _load_research_traces(run_dir: Path) -> list[tuple[Path, dict[str, Any]]]:
    traces: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(run_dir.glob("*.json")):
        if path.name.endswith("_manifest.json"):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if payload.get("trace_kind") == "research_theory_lab":
            traces.append((path, payload))
    return traces


def _sft_examples_for_trace(
    trace_path: Path,
    trace: dict[str, Any],
    validation_fraction: float,
) -> list[ResearchSftExample]:
    question = trace.get("question", {}) if isinstance(trace.get("question"), dict) else {}
    problem = trace.get("problem", {}) if isinstance(trace.get("problem"), dict) else {}
    procedures = [row for row in trace.get("procedures", []) if isinstance(row, dict)]
    theorem_goals = [row for row in trace.get("theorem_goals", []) if isinstance(row, dict)]
    formal_subclaims = [row for row in trace.get("formal_subclaims", []) if isinstance(row, dict)]
    simulations = [row for row in trace.get("simulations", []) if isinstance(row, dict)]
    knowledge = [row for row in trace.get("knowledge", []) if isinstance(row, dict)]
    question_id = str(question.get("id", trace_path.stem))
    problem_class = str(problem.get("problem_class", ""))
    context = _base_context(question)
    examples = [
        _example(
            trace_path,
            trace,
            task="problem_formalization",
            prompt="\n".join(
                [
                    "You are the ProblemFormalizer in an AI Statistical Theory Lab.",
                    "Given a paper-style statistical research question, extract the DGP, estimand, assumptions, asymptotic regime, diagnostics, and stress tests.",
                    "Return JSON only.",
                    "",
                    context,
                ]
            ),
            completion=_json(problem),
            validation_fraction=validation_fraction,
        ),
        _example(
            trace_path,
            trace,
            task="theory_plan_generation",
            prompt="\n".join(
                [
                    "You are the TheoryDeveloper in an AI Statistical Theory Lab.",
                    "Given the normalized problem and retrieved knowledge, propose procedures, theorem goals, and formal subclaims.",
                    "Return JSON only.",
                    "",
                    context,
                    "",
                    "Problem spec:",
                    _json(problem),
                    "",
                    "Retrieved knowledge:",
                    _json([_compact_knowledge(row) for row in knowledge[:8]]),
                ]
            ),
            completion=_json(
                {
                    "procedures": [_compact_procedure(row) for row in procedures],
                    "theorem_goals": [_compact_theorem_goal(row) for row in theorem_goals],
                    "formal_subclaims": [_compact_formal_subclaim(row) for row in formal_subclaims],
                }
            ),
            validation_fraction=validation_fraction,
        ),
        _example(
            trace_path,
            trace,
            task="formal_gap_routing",
            prompt="\n".join(
                [
                    "You are the FormalVerifier coordinator.",
                    "Given theorem goals and formal subclaims, route proved Mathlib-backed subclaims and honest FORMAL_GAP items into the next Lean-library work queue.",
                    "Return JSON only.",
                    "",
                    context,
                    "",
                    "Theorem goals:",
                    _json([_compact_theorem_goal(row) for row in theorem_goals]),
                    "",
                    "Formal subclaims:",
                    _json([_compact_formal_subclaim(row) for row in formal_subclaims]),
                ]
            ),
            completion=_json(_formal_gap_completion(theorem_goals, formal_subclaims)),
            validation_fraction=validation_fraction,
        ),
    ]
    for sim in simulations:
        procedure = next((row for row in procedures if row.get("id") == sim.get("procedure_id")), {})
        examples.append(
            _example(
                trace_path,
                trace,
                task="simulation_critique",
                prompt="\n".join(
                    [
                        "You are the Simulator/Critic agent.",
                        "Given a procedure, simulation design, and Monte Carlo metrics, diagnose whether the theory/algorithm passed and what feedback should be routed upstream.",
                        "Return JSON only.",
                        "",
                        context,
                        "",
                        "Problem spec:",
                        _json(problem),
                        "",
                        "Procedure:",
                        _json(_compact_procedure(procedure)),
                        "",
                        "Simulation design and metrics:",
                        _json({"design": sim.get("design"), "metrics": sim.get("metrics")}),
                    ]
                ),
                completion=_json(
                    {
                        "procedure_id": sim.get("procedure_id"),
                        "passed": sim.get("passed"),
                        "feedback": sim.get("feedback"),
                        "recommended_route": "accept" if sim.get("passed") else "theory_or_algorithm_revision",
                    }
                ),
                validation_fraction=validation_fraction,
            )
        )
    return examples


def _grpo_tasks_for_trace(trace_path: Path, trace: dict[str, Any]) -> list[ResearchGrpoTask]:
    question = trace.get("question", {}) if isinstance(trace.get("question"), dict) else {}
    problem = trace.get("problem", {}) if isinstance(trace.get("problem"), dict) else {}
    procedures = [row for row in trace.get("procedures", []) if isinstance(row, dict)]
    simulations = [row for row in trace.get("simulations", []) if isinstance(row, dict)]
    rows: list[ResearchGrpoTask] = []
    for sim in simulations:
        procedure = next((row for row in procedures if row.get("id") == sim.get("procedure_id")), {})
        prompt = "\n".join(
            [
                "Choose whether to accept this statistical procedure or request revision based on the diagnostics.",
                "Return JSON with decision and reason.",
                "",
                _base_context(question),
                "",
                "Problem spec:",
                _json(problem),
                "",
                "Procedure:",
                _json(_compact_procedure(procedure)),
                "",
                "Simulation metrics:",
                _json(sim.get("metrics", {})),
            ]
        )
        reference = {
            "decision": "accept" if sim.get("passed") else "revise",
            "feedback": sim.get("feedback"),
        }
        rows.append(
            ResearchGrpoTask(
                schema_version=RESEARCH_TRAINING_EXPORT_SCHEMA_VERSION,
                task_id=f"research_grpo:{trace_path.stem}:{sim.get('procedure_id', 'procedure')}",
                task="simulation_acceptance_reward",
                prompt=prompt,
                reference_completion=_json(reference),
                reward=1.0 if sim.get("passed") else 0.0,
                reward_source="simulation_passed",
                question_id=str(question.get("id", trace_path.stem)),
                trace_path=str(trace_path),
                problem_class=str(problem.get("problem_class", "")),
                tags=("research_trace", "simulation", "grpo_seed"),
            )
        )
    return rows


def _example(
    trace_path: Path,
    trace: dict[str, Any],
    *,
    task: str,
    prompt: str,
    completion: str,
    validation_fraction: float,
) -> ResearchSftExample:
    question = trace.get("question", {}) if isinstance(trace.get("question"), dict) else {}
    problem = trace.get("problem", {}) if isinstance(trace.get("problem"), dict) else {}
    procedures = [row for row in trace.get("procedures", []) if isinstance(row, dict)]
    theorem_goals = [row for row in trace.get("theorem_goals", []) if isinstance(row, dict)]
    formal_subclaims = [row for row in trace.get("formal_subclaims", []) if isinstance(row, dict)]
    simulations = [row for row in trace.get("simulations", []) if isinstance(row, dict)]
    question_id = str(question.get("id", trace_path.stem))
    example_id = f"{task}:{question_id}:{stable_hash([prompt, completion])[:16]}"
    return ResearchSftExample(
        schema_version=RESEARCH_TRAINING_EXPORT_SCHEMA_VERSION,
        example_id=example_id,
        split=_split_for_example(example_id, validation_fraction),
        task=task,
        prompt=prompt,
        completion=completion,
        question_id=question_id,
        trace_path=str(trace_path),
        problem_class=str(problem.get("problem_class", "")),
        procedure_ids=tuple(str(row.get("id", "")) for row in procedures if row.get("id")),
        theorem_goal_ids=tuple(str(row.get("id", "")) for row in theorem_goals if row.get("id")),
        formal_subclaim_ids=tuple(str(row.get("id", "")) for row in formal_subclaims if row.get("id")),
        simulation_ids=tuple(str(row.get("procedure_id", "")) for row in simulations if row.get("procedure_id")),
        tags=("research_trace", task, str(problem.get("problem_class", ""))),
    )


def _base_context(question: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Question id: {question.get('id', '')}",
            f"Title: {question.get('title', '')}",
            f"Description: {question.get('description', '')}",
            f"Tags: {', '.join(str(item) for item in question.get('tags', []) or [])}",
        ]
    )


def _compact_knowledge(row: dict[str, Any]) -> dict[str, object]:
    return {
        "id": row.get("id"),
        "title": row.get("title"),
        "source_type": row.get("source_type"),
        "summary": row.get("summary"),
        "tags": row.get("tags", []),
    }


def _compact_procedure(row: dict[str, Any]) -> dict[str, object]:
    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "role": row.get("role"),
        "formula": row.get("formula"),
        "informal_derivation": row.get("informal_derivation"),
        "algorithm": row.get("algorithm"),
        "theorem_goals": row.get("theorem_goals", []),
        "simulation_design": row.get("simulation_design"),
        "limitations": row.get("limitations", []),
    }


def _compact_theorem_goal(row: dict[str, Any]) -> dict[str, object]:
    return {
        "id": row.get("id"),
        "title": row.get("title"),
        "informal_statement": row.get("informal_statement"),
        "proof_strategy": row.get("proof_strategy"),
        "status": row.get("status"),
        "required_primitives": row.get("required_primitives", []),
        "proof_obligations": row.get("proof_obligations", []),
    }


def _compact_formal_subclaim(row: dict[str, Any]) -> dict[str, object]:
    return {
        "id": row.get("id"),
        "title": row.get("title"),
        "status": row.get("status"),
        "claim_type": row.get("claim_type"),
        "proof_obligation_id": row.get("proof_obligation_id"),
        "formalization_status": row.get("formalization_status"),
        "gap_reason": row.get("gap_reason"),
        "proof_dependencies": row.get("proof_dependencies", []),
        "formal_source_hits": row.get("formal_source_hits", [])[:5],
    }


def _formal_gap_completion(
    theorem_goals: list[dict[str, Any]],
    formal_subclaims: list[dict[str, Any]],
) -> dict[str, object]:
    proved = [
        row
        for row in formal_subclaims
        if row.get("status") in {"VERIFIED", "PROVED"} or row.get("formalization_status") == "VERIFIED"
    ]
    gaps = [
        row
        for row in formal_subclaims
        if str(row.get("status", "")).upper() == "FORMAL_GAP"
        or str(row.get("formalization_status", "")).upper() == "FORMAL_GAP"
    ]
    primitives_by_goal = {
        str(goal.get("id", "")): goal.get("required_primitives", [])
        for goal in theorem_goals
        if goal.get("id")
    }
    return {
        "proved_subclaims": [_compact_formal_subclaim(row) for row in proved],
        "formal_gaps": [_compact_formal_subclaim(row) for row in gaps],
        "required_primitives_by_goal": primitives_by_goal,
        "next_action": "export_formal_gap_lean_tasks_and_proof_bank_expansion_candidates",
    }


def _all_ok(
    traces: list[tuple[Path, dict[str, Any]]],
    examples: list[ResearchSftExample],
) -> bool:
    if not traces or not examples:
        return False
    by_question: dict[str, set[str]] = {}
    for row in examples:
        by_question.setdefault(row.question_id, set()).add(row.task)
    required = {"problem_formalization", "theory_plan_generation", "formal_gap_routing", "simulation_critique"}
    return all(required <= tasks for tasks in by_question.values())


def _split_for_example(example_id: str, validation_fraction: float) -> str:
    if validation_fraction <= 0.0:
        return "train"
    bucket = int(stable_hash(example_id)[:12], 16) / float(0xFFFFFFFFFFFF)
    return "validation" if bucket < validation_fraction else "train"


def _count_by_task(rows: list[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        task = str(getattr(row, "task", ""))
        counts[task] = counts.get(task, 0) + 1
    return dict(sorted(counts.items()))


def _json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, default=str)


def _write_jsonl(path: Path, rows: list[Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(asdict(row), default=str) + "\n")


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Research Trace Training Export",
        "",
        f"- Run directory: `{payload.get('run_dir')}`",
        f"- Traces: {payload.get('n_traces')}",
        f"- SFT examples: {payload.get('n_sft_examples')} ({payload.get('n_train')} train / {payload.get('n_validation')} validation)",
        f"- GRPO seed tasks: {payload.get('n_grpo_tasks')}",
        f"- All OK: `{payload.get('all_ok')}`",
        f"- Dataset fingerprint: `{payload.get('dataset_fingerprint')}`",
        "",
        "## SFT Tasks",
        "",
    ]
    by_task = payload.get("by_task", {})
    if isinstance(by_task, dict):
        for task, count in by_task.items():
            lines.append(f"- `{task}`: {count}")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Train JSONL: `{payload.get('train_jsonl')}`",
            f"- Validation JSONL: `{payload.get('validation_jsonl')}`",
            f"- All JSONL: `{payload.get('all_jsonl')}`",
            f"- GRPO JSONL: `{payload.get('grpo_jsonl')}`",
            f"- Legacy manifest: `{payload.get('legacy_training_manifest')}`",
            "",
            "This artifact is a training-data substrate only. It does not train or register a model checkpoint.",
        ]
    )
    return "\n".join(lines) + "\n"
