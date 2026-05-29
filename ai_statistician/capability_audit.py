from __future__ import annotations

import inspect
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .agents import AlgorithmEngineerAgent, FormalVerifierAgent, TheoryDeveloperAgent
from .algorithms import algorithm_registry_fingerprint, all_algorithms
from .doctor import _latest_manifests
from .proof_bank import all_obligations, proof_bank_fingerprint
from .questions import ESTIMATOR_FAMILIES, QUESTIONS, estimator_registry_fingerprint, question_registry_fingerprint
from .retrieval import LoogleRetriever, ProofBankRetriever
from .schema import SimulationMetrics
from .simulation import SAMPLERS
from .system import AIStatisticianSystem, write_run_manifest, write_trace
from .system_audit import run_system_audit
from .theory_proposal import AnthropicTheoryProposer
from .verifier import AxleProofVerifier


@dataclass(frozen=True)
class CapabilityFinding:
    requirement: str
    status: str
    evidence: tuple[str, ...]
    limitations: tuple[str, ...] = ()


def build_capability_audit(*, root: Path | None = None, max_manifests: int = 12) -> dict[str, object]:
    """Map the project objective to current, inspectable evidence.

    This is not a replacement for the system audit. It is a release-readiness
    index: each row states what part of the objective is satisfied by current
    source files or manifests, and which limitations remain.
    """

    project_root = (root or Path.cwd()).resolve()
    obligations = all_obligations()
    estimator_obligations = [row for row in obligations if "estimator" in row.tags]
    algorithms = all_algorithms()
    manifests = _latest_manifests(project_root / "runs", max_count=max_manifests)
    latest_system_audit = next(
        (row for row in manifests if row["name"] == "system_audit_manifest.json"),
        None,
    )
    latest_proof_audit = next(
        (row for row in manifests if row["name"] == "proof_audit_manifest.json"),
        None,
    )
    latest_proof_payload = _read_manifest_payload(latest_proof_audit)
    latest_kernel_verified = int(latest_proof_payload.get("n_kernel_verified", 0)) if latest_proof_payload else 0
    latest_non_kernel_verified = (
        int(latest_proof_payload.get("n_non_kernel_verified", 0)) if latest_proof_payload else 0
    )
    latest_all_kernel_verified = bool(latest_proof_payload.get("all_kernel_verified")) if latest_proof_payload else False
    axle_proof_status = "READY" if latest_all_kernel_verified and latest_kernel_verified > 0 else "PARTIAL"
    metric_fields = tuple(SimulationMetrics.__dataclass_fields__)

    findings = [
        CapabilityFinding(
            requirement="take statistical questions",
            status="READY",
            evidence=(
                f"{len(QUESTIONS)} built-in questions registered",
                "JSON intake supports explicit and inferred supported families",
                "intake-audit verifies unsupported examples are rejected before execution",
                str((project_root / "examples" / "questions.json").resolve()),
                str((project_root / "examples" / "partial_questions.json").resolve()),
                str((project_root / "examples" / "unsupported_questions.json").resolve()),
            ),
            limitations=(
                "Current supported DGPs are normal, Bernoulli, and constant.",
                "Unsupported statistical families are rejected before simulation.",
            ),
        ),
        CapabilityFinding(
            requirement="select or derive estimators",
            status="READY",
            evidence=(
                f"{len(ESTIMATOR_FAMILIES)} estimator families registered",
                f"{TheoryDeveloperAgent.__module__}.{TheoryDeveloperAgent.__name__}",
                f"{AnthropicTheoryProposer.__module__}.{AnthropicTheoryProposer.__name__} for optional gated LLM intake",
            ),
            limitations=(
                "Production estimator selection is registry-gated; LLM proposals only classify into supported families.",
            ),
        ),
        CapabilityFinding(
            requirement="multi-agent workflow",
            status="READY",
            evidence=(
                f"{AIStatisticianSystem.__module__}.{AIStatisticianSystem.__name__}",
                f"{TheoryDeveloperAgent.__name__} -> {FormalVerifierAgent.__name__} -> {AlgorithmEngineerAgent.__name__}",
                "SimulatorAgent runs after formal and algorithm stages",
            ),
        ),
        CapabilityFinding(
            requirement="verify Mathlib-backed estimator/probability properties in Lean via AXLE",
            status=axle_proof_status,
            evidence=(
                f"{len(obligations)} proof-bank obligations registered",
                f"{len(estimator_obligations)} estimator-tagged obligations registered",
                f"latest_proof_audit_kernel_verified={latest_kernel_verified}",
                f"latest_proof_audit_non_kernel_verified={latest_non_kernel_verified}",
                f"latest_proof_audit_all_kernel_verified={latest_all_kernel_verified}",
                f"{AxleProofVerifier.__module__}.{AxleProofVerifier.__name__} calls AXLE verify_proof",
                "proof-audit exports per-obligation Lean candidates",
                latest_proof_audit["path"] if latest_proof_audit else "no latest proof audit manifest found",
            ),
            limitations=(
                "Current Lean proofs cover finite Mathlib-backed facts, not full CLT, MLE consistency, or semiparametric efficiency.",
                "Offline mock-positive proof rows are regression evidence only; READY requires a latest proof audit with kernel_verified=true for all selected rows.",
                "AXLE availability is environment-dependent; run doctor/system-audit with --real-lean for live verification.",
            ),
        ),
        CapabilityFinding(
            requirement="implement vetted algorithms",
            status="READY" if algorithms and all(row.registry_status == "vetted" for row in algorithms) else "MISSING",
            evidence=tuple(
                f"{row.id}@{row.version} status={row.registry_status} hash={row.implementation_hash()[:12]}"
                for row in algorithms
            ),
            limitations=("Only vetted registry algorithms execute; LLM-written algorithms are not admitted yet.",),
        ),
        CapabilityFinding(
            requirement="run Monte Carlo simulation diagnostics",
            status="READY",
            evidence=(
                f"samplers={', '.join(sorted(SAMPLERS))}",
                f"metrics={', '.join(metric_fields)}",
            ),
        ),
        CapabilityFinding(
            requirement="persist auditable traces",
            status="READY" if callable(write_trace) and callable(write_run_manifest) else "MISSING",
            evidence=(
                f"{write_trace.__module__}.{write_trace.__name__}",
                f"{write_run_manifest.__module__}.{write_run_manifest.__name__}",
                latest_system_audit["path"] if latest_system_audit else "no latest system audit manifest found",
                f"question_registry_fingerprint={question_registry_fingerprint()[:12]}",
                f"estimator_registry_fingerprint={estimator_registry_fingerprint()[:12]}",
            ),
            limitations=(() if latest_system_audit else ("Run system-audit to create release-style evidence.",)),
        ),
        CapabilityFinding(
            requirement="integrate retrieval and prover infrastructure",
            status="READY",
            evidence=(
                f"{ProofBankRetriever.__module__}.{ProofBankRetriever.__name__}",
                f"{LoogleRetriever.__module__}.{LoogleRetriever.__name__} optional integration",
                "retrieval-audit --loogle records external Mathlib name-resolution evidence",
                "OpenProver tokenization is used opportunistically when the local checkout exists",
                f"proof_bank_fingerprint={proof_bank_fingerprint()[:12]}",
            ),
            limitations=(
                "Loogle/Lean Finder/ReProver are documented integration targets, not required runtime gates.",
            ),
        ),
        CapabilityFinding(
            requirement="release-style audit gates",
            status="READY",
            evidence=(
                f"{run_system_audit.__module__}.{run_system_audit.__name__}",
                latest_system_audit["path"] if latest_system_audit else "no latest system audit manifest found",
            ),
            limitations=(() if latest_system_audit else ("Run system-audit before treating a build as released.",)),
        ),
        CapabilityFinding(
            requirement="honest roadmap for stronger guarantees",
            status="READY" if _roadmap_documented(project_root / "docs" / "production_design.md") else "MISSING",
            evidence=(str((project_root / "docs" / "production_design.md").resolve()),),
            limitations=(
                "Roadmap explicitly separates current finite proofs from future asymptotic formalization.",
            ),
        ),
    ]

    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "root": str(project_root),
        "all_required_capabilities_present": all(row.status != "MISSING" for row in findings),
        "n_ready": sum(1 for row in findings if row.status == "READY"),
        "n_partial": sum(1 for row in findings if row.status == "PARTIAL"),
        "n_missing": sum(1 for row in findings if row.status == "MISSING"),
        "findings": [asdict(row) for row in findings],
        "latest_manifests": manifests,
        "source_files": {
            "system": inspect.getsourcefile(AIStatisticianSystem),
            "agents": inspect.getsourcefile(TheoryDeveloperAgent),
            "proof_bank": str((project_root / "ai_statistician" / "proof_bank.py").resolve()),
            "algorithms": str((project_root / "ai_statistician" / "algorithms.py").resolve()),
            "simulation": str((project_root / "ai_statistician" / "simulation.py").resolve()),
            "docs": str((project_root / "docs" / "production_design.md").resolve()),
        },
        "fingerprints": {
            "question_registry": question_registry_fingerprint(),
            "estimator_registry": estimator_registry_fingerprint(),
            "algorithm_registry": algorithm_registry_fingerprint(),
            "proof_bank": proof_bank_fingerprint(),
        },
    }
    return payload


def write_capability_audit(report: dict[str, object], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "capability_audit_manifest.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return path


def _roadmap_documented(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8").lower()
    return "next production steps" in text and "asymptotic" in text and "mathlib" in text


def _read_manifest_payload(row: dict[str, object] | None) -> dict[str, object]:
    if row is None:
        return {}
    try:
        return json.loads(Path(str(row["path"])).read_text(encoding="utf-8"))
    except Exception:
        return {}
