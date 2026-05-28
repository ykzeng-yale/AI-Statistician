from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .algorithms import audit_algorithm_registry
from .evaluation import EvalConfig, run_seed_eval
from .intake_audit import audit_question_intake
from .proof_audit import audit_proof_bank
from .questions import QUESTIONS, load_question_file
from .retrieval import audit_proof_bank_retrieval
from .schema import StatisticalQuestion
from .system import AIStatisticianSystem, build_provenance, compact_summary, write_run_manifest, write_trace
from .trace_audit import audit_run_traces
from .verifier import AxleProofVerifier, MockProofVerifier, ProofVerifier


@dataclass(frozen=True)
class SystemAuditConfig:
    n_runs: int = 300
    seeds: tuple[int, ...] = (20260528, 20260529)
    use_axle: bool = False
    include_eval: bool = True


async def run_system_audit(
    out_dir: Path,
    *,
    questions: list[StatisticalQuestion] | None = None,
    config: SystemAuditConfig = SystemAuditConfig(),
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    verifier: ProofVerifier = AxleProofVerifier() if config.use_axle else MockProofVerifier()
    selected_questions = questions or list(QUESTIONS.values())

    intake_manifest = audit_question_intake(out_dir / "intake_audit")
    algorithm_manifest = audit_algorithm_registry(out_dir / "algorithm_audit")
    retrieval_manifest = audit_proof_bank_retrieval(out_dir / "retrieval_audit", k=5)
    proof_manifest = await audit_proof_bank(
        verifier,
        out_dir / "proof_audit",
        export_lean=True,
    )

    system = (
        AIStatisticianSystem.with_axle(n_runs=config.n_runs, seed=config.seeds[0])
        if config.use_axle
        else AIStatisticianSystem(n_runs=config.n_runs, seed=config.seeds[0])
    )
    question_reports = []
    question_dir = out_dir / "question_runs"
    for question in selected_questions:
        report = await system.run(question)
        question_reports.append(report)
        write_trace(report, question_dir)
    write_run_manifest(question_reports, question_dir)
    trace_manifest = audit_run_traces(question_dir, out_dir / "trace_audit")

    eval_manifest: dict[str, object] | None = None
    if config.include_eval:
        eval_manifest = await run_seed_eval(
            selected_questions,
            EvalConfig(seeds=config.seeds, n_runs=config.n_runs, use_axle=config.use_axle),
            out_dir / "evaluation",
        )

    question_gate_ok = all(report.status == "ACCEPTED" for report in question_reports)
    eval_gate_ok = None
    if eval_manifest is not None:
        eval_gate_ok = all(
            row["acceptance_rate"] == 1.0
            for row in eval_manifest["summary"].values()
        )

    gates = {
        "intake_audit": bool(intake_manifest["all_ok"]),
        "algorithm_audit": bool(algorithm_manifest["all_ok"]),
        "retrieval_audit": bool(retrieval_manifest["all_top_k"]),
        "proof_audit": bool(proof_manifest["all_verified"]),
        "question_runs": question_gate_ok,
        "trace_audit": bool(trace_manifest["all_ok"]),
    }
    if eval_gate_ok is not None:
        gates["evaluation"] = eval_gate_ok
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": {
            "n_runs": config.n_runs,
            "seeds": list(config.seeds),
            "use_axle": config.use_axle,
            "include_eval": config.include_eval,
        },
        "provenance": build_provenance(),
        "all_gates_passed": all(gates.values()),
        "gates": gates,
        "counts": {
            "questions": len(selected_questions),
            "question_runs_accepted": sum(1 for report in question_reports if report.status == "ACCEPTED"),
            "intake_supported_accepted": intake_manifest["n_supported_accepted"],
            "intake_supported_total": intake_manifest["n_supported"],
            "intake_unsupported_rejected": intake_manifest["n_unsupported_rejected"],
            "intake_unsupported_total": intake_manifest["n_unsupported"],
            "algorithms_ok": algorithm_manifest["n_ok"],
            "algorithms_total": algorithm_manifest["n_algorithms"],
            "retrieval_top_k": retrieval_manifest["top_k"],
            "retrieval_total": retrieval_manifest["n_obligations"],
            "proofs_verified": proof_manifest["n_verified"],
            "proofs_total": proof_manifest["n_obligations"],
            "traces_ok": trace_manifest["n_ok"],
            "traces_total": trace_manifest["n_traces"],
        },
        "questions": [compact_summary(report) for report in question_reports],
        "artifacts": {
            "intake_audit": str(out_dir / "intake_audit" / "intake_audit_manifest.json"),
            "algorithm_audit": str(out_dir / "algorithm_audit" / "algorithm_audit_manifest.json"),
            "retrieval_audit": str(out_dir / "retrieval_audit" / "retrieval_audit_manifest.json"),
            "proof_audit": str(out_dir / "proof_audit" / "proof_audit_manifest.json"),
            "question_runs": str(question_dir / "manifest.json"),
            "trace_audit": str(out_dir / "trace_audit" / "trace_audit_manifest.json"),
            "evaluation": str(out_dir / "evaluation" / "evaluation_manifest.json") if eval_manifest else None,
        },
    }
    (out_dir / "system_audit_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    return payload


def load_audit_questions(question_file: str | None, include_partial_examples: bool) -> list[StatisticalQuestion]:
    questions = list(QUESTIONS.values())
    if question_file:
        questions.extend(load_question_file(Path(question_file)))
    if include_partial_examples:
        path = Path("examples/partial_questions.json")
        if path.exists():
            questions.extend(load_question_file(path))
    seen: set[str] = set()
    unique: list[StatisticalQuestion] = []
    for question in questions:
        if question.id in seen:
            continue
        seen.add(question.id)
        unique.append(question)
    return unique
