"""Training manifest generation for SFT, DPO, and GRPO experiments."""

from __future__ import annotations

from dataclasses import dataclass, field
from dataclasses import replace

from statlean_agent.contracts import BenchmarkTask, ProofAttempt, VerificationReport, VerificationStatus
from statlean_agent.rewards import score_attempt
from statlean_agent.verifier import render_task


@dataclass(frozen=True)
class SFTExample:
    """One supervised proof example."""

    example_id: str
    task_id: str
    prompt: str
    response: str


@dataclass(frozen=True)
class DPOPair:
    """One chosen/rejected proof preference pair."""

    pair_id: str
    task_id: str
    chosen: str
    rejected: str


@dataclass(frozen=True)
class GRPOTask:
    """One verifier-reward RL prompt."""

    task_id: str
    prompt: str
    reward_source: str = "lean_process_reward"


@dataclass(frozen=True)
class TrainingManifest:
    """Small deterministic manifest for downstream trainers."""

    run_id: str
    base_model: str
    sft_examples: tuple[SFTExample, ...] = ()
    dpo_pairs: tuple[DPOPair, ...] = ()
    grpo_tasks: tuple[GRPOTask, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)


def build_sft_examples(tasks: tuple[BenchmarkTask, ...]) -> tuple[SFTExample, ...]:
    """Use benchmark gold statements as initial supervised examples."""

    examples: list[SFTExample] = []
    for task in tasks:
        examples.append(
            SFTExample(
                example_id=f"sft::{task.task_id}",
                task_id=task.task_id,
                prompt=_task_prompt(task),
                response=task.lean_task.statement,
            )
        )
    return tuple(examples)


def build_verified_sft_examples(
    tasks: tuple[BenchmarkTask, ...],
    attempts: tuple[ProofAttempt, ...],
    reports: tuple[VerificationReport, ...],
) -> tuple[SFTExample, ...]:
    """Use accepted, no-placeholder proof attempts as supervised examples."""

    task_by_id = {task.task_id: task for task in tasks}
    examples: list[SFTExample] = []
    for attempt, report in zip(attempts, reports, strict=True):
        task = task_by_id.get(attempt.task_id)
        if task is None:
            continue
        if task.lean_task.allowed_sorry:
            continue
        if report.status is not VerificationStatus.ACCEPTED:
            continue
        examples.append(
            SFTExample(
                example_id=f"sft::{attempt.task_id}::verified",
                task_id=attempt.task_id,
                prompt=_task_prompt(task),
                response=attempt.lean_code,
            )
        )
    return tuple(examples)


def build_dpo_pairs(
    attempts: tuple[ProofAttempt, ...],
    reports: tuple[VerificationReport, ...],
) -> tuple[DPOPair, ...]:
    """Create accepted-vs-failed preference pairs grouped by task."""

    by_task: dict[str, list[tuple[ProofAttempt, VerificationReport]]] = {}
    for attempt, report in zip(attempts, reports, strict=True):
        by_task.setdefault(attempt.task_id, []).append((attempt, report))

    pairs: list[DPOPair] = []
    for task_id, items in sorted(by_task.items()):
        accepted = [item for item in items if item[1].status is VerificationStatus.ACCEPTED]
        failed = [item for item in items if item[1].status is not VerificationStatus.ACCEPTED]
        if not accepted or not failed:
            continue
        chosen = max(accepted, key=lambda item: score_attempt(item[0], item[1]).total)[0]
        rejected = min(failed, key=lambda item: score_attempt(item[0], item[1]).total)[0]
        pairs.append(
            DPOPair(
                pair_id=f"dpo::{task_id}::{len(pairs)}",
                task_id=task_id,
                chosen=chosen.lean_code,
                rejected=rejected.lean_code,
            )
        )
    return tuple(pairs)


def build_rejected_dpo_attempts(
    tasks: tuple[BenchmarkTask, ...],
    *,
    agent_key: str = "dpo-negative-generator",
) -> tuple[ProofAttempt, ...]:
    """Create deterministic same-statement rejected attempts for DPO.

    The generated attempts preserve each benchmark theorem statement but replace
    its proof body with a missing-premise reference. This yields Lean-labeled
    unknown-declaration failures without using `sorry`, `admit`, or other
    forbidden placeholders.
    """

    attempts: list[ProofAttempt] = []
    for task in tasks:
        if task.lean_task.allowed_sorry:
            continue
        negative_task = replace(
            task.lean_task,
            statement=_replace_proof_body_with_missing_premise(task.lean_task.statement),
            allowed_sorry=False,
        )
        attempts.append(
            ProofAttempt(
                task_id=task.task_id,
                agent_key=agent_key,
                lean_code=render_task(negative_task),
                premises_used=(),
            )
        )
    return tuple(attempts)


def build_grpo_tasks(tasks: tuple[BenchmarkTask, ...]) -> tuple[GRPOTask, ...]:
    """Create verifier-reward RL prompts from benchmark tasks."""

    return tuple(GRPOTask(task_id=task.task_id, prompt=_task_prompt(task)) for task in tasks)


def build_training_manifest(
    tasks: tuple[BenchmarkTask, ...],
    attempts: tuple[ProofAttempt, ...] = (),
    reports: tuple[VerificationReport, ...] = (),
    run_id: str = "local-seed",
    base_model: str = "unspecified-lean-prover",
) -> TrainingManifest:
    """Build a deterministic training manifest from current artifacts."""

    return TrainingManifest(
        run_id=run_id,
        base_model=base_model,
        sft_examples=(
            build_verified_sft_examples(tasks, attempts, reports)
            if attempts and reports
            else build_sft_examples(tasks)
        ),
        dpo_pairs=build_dpo_pairs(attempts, reports) if attempts and reports else (),
        grpo_tasks=build_grpo_tasks(tasks),
        metadata={
            "task_count": str(len(tasks)),
            "attempt_count": str(len(attempts)),
            "dpo_pair_count": str(len(build_dpo_pairs(attempts, reports)) if attempts and reports else 0),
            "sft_source": "verified_attempts" if attempts and reports else "benchmark_gold",
        },
    )


def _task_prompt(task: BenchmarkTask) -> str:
    natural = task.natural_language or "Prove the Lean theorem."
    return f"{natural}\n\n```lean\n{render_task(task.lean_task)}\n```"


def _replace_proof_body_with_missing_premise(statement: str) -> str:
    marker = ":= by"
    prefix, separator, _ = statement.partition(marker)
    if separator:
        return f"{prefix}{separator}\n  exact StatInference.__statlean_dpo_missing_premise__"
    return f"{statement}\n  exact StatInference.__statlean_dpo_missing_premise__"
