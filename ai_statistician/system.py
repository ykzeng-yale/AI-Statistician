from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .agents import AlgorithmEngineerAgent, FormalVerifierAgent, TheoryDeveloperAgent
from .algorithms import algorithm_registry_fingerprint
from .proof_bank import proof_bank_fingerprint
from .questions import estimator_registry_fingerprint, get_question, question_registry_fingerprint
from .retrieval import ProofBankRetriever
from .schema import StatisticalQuestion, SystemReport
from .simulation import SimulatorAgent
from .verifier import AxleProofVerifier, MockProofVerifier, ProofVerifier


class AIStatisticianSystem:
    """Coordinator for the production-oriented AI statistician core."""

    def __init__(
        self,
        *,
        proof_verifier: ProofVerifier | None = None,
        n_runs: int = 1000,
        seed: int = 20260528,
    ) -> None:
        self.theory = TheoryDeveloperAgent()
        self.algorithm = AlgorithmEngineerAgent()
        self.formal = FormalVerifierAgent(
            verifier=proof_verifier or MockProofVerifier(),
            retriever=ProofBankRetriever(),
        )
        self.simulator = SimulatorAgent(n_runs=n_runs, seed=seed)

    @classmethod
    def with_axle(cls, *, n_runs: int = 1000, seed: int = 20260528) -> "AIStatisticianSystem":
        return cls(proof_verifier=AxleProofVerifier(), n_runs=n_runs, seed=seed)

    async def run_question(self, question_id: str) -> SystemReport:
        question = get_question(question_id)
        return await self.run(question)

    async def run(self, question: StatisticalQuestion) -> SystemReport:
        estimator = self.theory.develop(question)
        proofs = await self.formal.verify_estimator(estimator)
        algorithm = self.algorithm.implement(estimator)
        simulation = self.simulator.run(question, algorithm)

        formal_ok = all(check.ok for check in proofs)
        sim_ok = simulation.pass_bias and simulation.pass_coverage and simulation.pass_se_calibration
        if formal_ok and sim_ok:
            status = "ACCEPTED"
        elif not formal_ok:
            status = "FORMAL_BLOCKED"
        else:
            status = "SIMULATION_BLOCKED"
        return SystemReport(
            question=question,
            estimator=estimator,
            proofs=proofs,
            algorithm=algorithm,
            simulation=simulation,
            status=status,
        )

    async def run_all(self) -> list[SystemReport]:
        return [
            await self.run_question(question_id)
            for question_id in get_registered_question_ids()
        ]


def get_registered_question_ids() -> tuple[str, ...]:
    from .questions import QUESTIONS

    return tuple(QUESTIONS)


def write_trace(report: SystemReport, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{report.question.id}.json"
    payload = {
        "trace_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provenance": build_provenance(),
        **report.to_json(),
    }
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def write_run_manifest(reports: list[SystemReport], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    summaries = [compact_summary(report) for report in reports]
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provenance": build_provenance(),
        "n_questions": len(reports),
        "n_accepted": sum(1 for report in reports if report.status == "ACCEPTED"),
        "n_formal_blocked": sum(1 for report in reports if report.status == "FORMAL_BLOCKED"),
        "n_simulation_blocked": sum(1 for report in reports if report.status == "SIMULATION_BLOCKED"),
        "questions": summaries,
    }
    path = out_dir / "manifest.json"
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def build_provenance() -> dict[str, str]:
    return {
        "question_registry_fingerprint": question_registry_fingerprint(),
        "estimator_registry_fingerprint": estimator_registry_fingerprint(),
        "algorithm_registry_fingerprint": algorithm_registry_fingerprint(),
        "proof_bank_fingerprint": proof_bank_fingerprint(),
    }


def compact_summary(report: SystemReport) -> dict[str, object]:
    metrics = report.simulation.metrics
    return {
        "question": report.question.id,
        "status": report.status,
        "formal": f"{sum(1 for p in report.proofs if p.ok)}/{len(report.proofs)}",
        "bias": round(metrics.bias, 5),
        "relative_bias": round(metrics.relative_bias, 5),
        "rmse": round(metrics.rmse, 5),
        "coverage_95": round(metrics.coverage_95, 3),
        "verifier": report.proofs[0].verifier if report.proofs else "none",
    }
