from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .architect_coordinator_llm import (
    ArchitectCoordinatorConfig,
    LLMArchitectCoordinatorAgent,
)
from .model_backend import (
    GeneratorBackend,
    GeneratorRequest,
    GeneratorResponse,
    LIVE_EVALUATION_CLAUDE_MODEL_TIER,
    OpenAIResponsesGeneratorBackend,
    generator_backend_provider_name,
    is_live_generator_backend,
    resolve_live_evaluation_model,
)
from .research_architect import AnthropicArchitectLLMProvider, StaticArchitectLLMProvider
from .research_schema import OpenResearchQuestion


ARCHITECT_PATH_POLICY_EVAL_NOT_PROOF_EVIDENCE = (
    "ARCHITECT_RESEARCH_PATH_POLICY_EVAL_NOT_PROOF_EVIDENCE"
)


@dataclass(frozen=True)
class ArchitectPathPolicyCase:
    case_id: str
    question: OpenResearchQuestion
    runtime_config: Mapping[str, Any]
    architect_context: Mapping[str, Any]
    acceptable_policies: tuple[str, ...]
    acceptable_paths: tuple[str, ...]
    expected_formal_required_for_final: bool | None


def run_architect_research_path_policy_eval(
    *,
    out_dir: Path,
    provider_name: str = "anthropic",
    model: str = "",
    static_response_file: Path | None = None,
    llm_timeout_seconds: float | None = None,
    max_tokens: int = 4000,
    temperature: float = 0.1,
) -> dict[str, Any]:
    """Run a narrow Architect path-policy capability eval.

    The eval checks whether the generator-backed ArchitectCoordinator returns a
    valid research path/evidence contract for proof-gated, simulation-first, and
    optional/free-choice scenarios. It does not execute downstream tools and is
    not proof or simulation evidence.
    """

    out_dir.mkdir(parents=True, exist_ok=True)
    provider_name = provider_name.strip().lower()
    provider = _architect_path_policy_eval_provider(
        provider_name=provider_name,
        static_response_file=static_response_file,
        llm_timeout_seconds=llm_timeout_seconds,
    )
    backend_provider_name = generator_backend_provider_name(provider, provider_name)
    resolved_model = resolve_live_evaluation_model(
        provider_name,
        model,
    )
    architect = LLMArchitectCoordinatorAgent(
        provider=provider,
        config=ArchitectCoordinatorConfig(
            provider_name=provider_name,
            model=resolved_model,
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            max_tokens=max_tokens,
            temperature=temperature,
            max_validation_retries=1,
        ),
    )
    rows: list[dict[str, Any]] = []
    packets: dict[str, Any] = {}
    for case in _architect_path_policy_cases():
        packet = architect.propose(
            question=case.question,
            architect_context=case.architect_context,
            runtime_config=case.runtime_config,
        )
        packets[case.case_id] = packet
        contract = (
            packet.get("evidence_contract", {})
            if isinstance(packet.get("evidence_contract", {}), Mapping)
            else {}
        )
        policy = str(contract.get("formal_verification_policy", "") or "").lower()
        path = str(contract.get("recommended_research_path", "") or "").lower()
        formal_required = contract.get("formal_required_for_final")
        case_ok = (
            policy in case.acceptable_policies
            and path in case.acceptable_paths
            and (
                case.expected_formal_required_for_final is None
                or formal_required is case.expected_formal_required_for_final
            )
        )
        rows.append(
            {
                "case_id": case.case_id,
                "question_id": case.question.id,
                "question_title": case.question.title,
                "requested_formal_verification_policy": str(
                    case.runtime_config.get("formal_verification_policy", "")
                ),
                "requested_recommended_research_path": str(
                    case.runtime_config.get("recommended_research_path", "")
                ),
                "architect_formal_verification_policy": policy,
                "architect_recommended_research_path": path,
                "architect_formal_required_for_final": formal_required,
                "acceptable_policies": list(case.acceptable_policies),
                "acceptable_paths": list(case.acceptable_paths),
                "expected_formal_required_for_final": (
                    case.expected_formal_required_for_final
                ),
                "case_ok": case_ok,
                "packet_id": str(packet.get("packet_id", "") or ""),
                "has_problem_analysis": bool(packet.get("problem_analysis")),
                "has_stat_knowledge_bank_plan": bool(
                    packet.get("stat_knowledge_bank_plan")
                ),
                "has_literature_fair_comparison_plan": bool(
                    packet.get("literature_fair_comparison_plan")
                ),
                "proof_evidence_status": str(
                    packet.get("proof_evidence_status", "") or ""
                ),
            }
        )
    live_generator = is_live_generator_backend(provider_name, backend_provider_name)
    n_cases = len(rows)
    n_cases_ok = sum(1 for row in rows if row["case_ok"])
    n_with_problem_analysis = sum(1 for row in rows if row["has_problem_analysis"])
    n_with_knowledge_plan = sum(
        1 for row in rows if row["has_stat_knowledge_bank_plan"]
    )
    n_with_fair_comparison = sum(
        1 for row in rows if row["has_literature_fair_comparison_plan"]
    )
    all_cases_ok = bool(
        n_cases > 0
        and n_cases_ok == n_cases
        and n_with_problem_analysis == n_cases
        and n_with_knowledge_plan == n_cases
        and n_with_fair_comparison == n_cases
    )
    manifest = {
        "schema_version": 1,
        "artifact_kind": "ArchitectResearchPathPolicyEvalManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provider_name": provider_name,
        "backend_provider_name": backend_provider_name,
        "model": resolved_model,
        "live_generator": live_generator,
        "component_eval": "ArchitectCoordinator research path policy",
        "n_cases": n_cases,
        "n_cases_ok": n_cases_ok,
        "n_with_problem_analysis": n_with_problem_analysis,
        "n_with_stat_knowledge_bank_plan": n_with_knowledge_plan,
        "n_with_literature_fair_comparison_plan": n_with_fair_comparison,
        "rows": rows,
        "all_cases_ok": all_cases_ok,
        "capability_evidence_ok": bool(live_generator and all_cases_ok),
        "static_or_fixture_only": not live_generator,
        "runtime_executed": False,
        "kernel_verified": False,
        "proof_evidence_status": ARCHITECT_PATH_POLICY_EVAL_NOT_PROOF_EVIDENCE,
        "boundary": (
            "This component eval checks whether the live ArchitectCoordinator "
            "can emit valid evidence-policy and research-path plans across "
            "representative scenarios. It does not execute tools, run "
            "simulations, or prove theorems; static replay is fixture plumbing "
            "only and cannot satisfy capability_evidence_ok."
        ),
    }
    manifest_path = out_dir / "architect_research_path_policy_eval_manifest.json"
    result_path = out_dir / "architect_research_path_policy_eval_result.json"
    manifest["artifacts"] = {
        "manifest_json": str(manifest_path),
        "result_json": str(result_path),
    }
    result_path.write_text(
        json.dumps(
            {
                "rows": rows,
                "packets": packets,
            },
            indent=2,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return manifest


def write_architect_research_path_policy_eval_failure_manifest(
    *,
    out_dir: Path,
    provider_name: str,
    model: str,
    exc: Exception,
    backend_provider_name: str = "",
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    provider_name = provider_name.strip().lower()
    backend_provider_name = (
        backend_provider_name.strip().lower() if backend_provider_name else provider_name
    )
    resolved_model = resolve_live_evaluation_model(
        provider_name,
        model,
    )
    live_generator = is_live_generator_backend(provider_name, backend_provider_name)
    manifest_path = out_dir / "architect_research_path_policy_eval_manifest.json"
    manifest = {
        "schema_version": 1,
        "artifact_kind": "ArchitectResearchPathPolicyEvalManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provider_name": provider_name,
        "backend_provider_name": backend_provider_name,
        "model": resolved_model,
        "live_generator": live_generator,
        "component_eval": "ArchitectCoordinator research path policy",
        "result_status": "PROVIDER_OR_RUNTIME_FAILURE",
        "failure_classification": "provider_or_runtime_exception",
        "failure_exception_type": type(exc).__name__,
        "failure_message": str(exc)[:1000],
        "n_cases": 0,
        "n_cases_ok": 0,
        "all_cases_ok": False,
        "capability_evidence_ok": False,
        "static_or_fixture_only": not live_generator,
        "runtime_executed": False,
        "kernel_verified": False,
        "proof_evidence_status": ARCHITECT_PATH_POLICY_EVAL_NOT_PROOF_EVIDENCE,
        "boundary": (
            "The Architect policy eval did not complete. This failure manifest "
            "is inspectable status only, not capability evidence."
        ),
        "artifacts": {
            "manifest_json": str(manifest_path),
        },
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return manifest


class _SequenceStaticGeneratorBackend:
    provider_name = "static"

    def __init__(self, responses: list[Any]) -> None:
        if not responses:
            raise ValueError("static response sequence must be nonempty")
        self._responses = [
            json.dumps(row, indent=2, default=str)
            if isinstance(row, Mapping)
            else str(row)
            for row in responses
        ]
        self._index = 0

    def generate(self, request: GeneratorRequest) -> GeneratorResponse:
        response = self._responses[min(self._index, len(self._responses) - 1)]
        self._index += 1
        return GeneratorResponse(
            text=response,
            provider=self.provider_name,
            model=request.model,
            metadata={"generator_only": True, "tools_available": False},
        )


def _architect_path_policy_eval_provider(
    *,
    provider_name: str,
    static_response_file: Path | None,
    llm_timeout_seconds: float | None,
) -> GeneratorBackend:
    if provider_name == "anthropic":
        return AnthropicArchitectLLMProvider(timeout_s=llm_timeout_seconds)
    if provider_name == "openai":
        return OpenAIResponsesGeneratorBackend(timeout_s=llm_timeout_seconds)
    if provider_name == "static":
        if static_response_file is None:
            raise ValueError("static provider requires static_response_file")
        payload = json.loads(static_response_file.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return _SequenceStaticGeneratorBackend(payload)
        return StaticArchitectLLMProvider(payload)
    raise ValueError(
        "unsupported Architect policy eval provider: "
        f"{provider_name!r}; expected anthropic, openai, or static"
    )


def _architect_path_policy_cases() -> tuple[ArchitectPathPolicyCase, ...]:
    return (
        ArchitectPathPolicyCase(
            case_id="required_finite_sample_coverage",
            question=OpenResearchQuestion(
                id="architect_policy_required_coverage",
                title="Machine-checked finite-sample coverage theorem",
                description=(
                    "Develop a split-conformal-style finite-sample coverage "
                    "guarantee where final acceptance requires a machine-checked "
                    "formal proof, not just simulation."
                ),
                tags=("coverage", "formal_verification_required"),
            ),
            runtime_config={
                "formal_verification_policy": "required",
                "recommended_research_path": "",
                "max_iterations": 8,
            },
            architect_context={
                "runtime_learning_memory_summary": {
                    "source_theorem_kernel_verified": False,
                    "formal_gaps": 2,
                }
            },
            acceptable_policies=("required",),
            acceptable_paths=("proof_first", "dual_track"),
            expected_formal_required_for_final=True,
        ),
        ArchitectPathPolicyCase(
            case_id="advisory_algorithm_simulation",
            question=OpenResearchQuestion(
                id="architect_policy_advisory_algorithm",
                title="Simulation-first robust estimator exploration",
                description=(
                    "Explore a new robust estimator and compare RMSE, coverage, "
                    "and failure modes across DGP stress tests. Formal proof is "
                    "diagnostic only for this early-stage algorithmic research."
                ),
                tags=("algorithm", "simulation", "advisory_formalization"),
            ),
            runtime_config={
                "formal_verification_policy": "advisory",
                "recommended_research_path": "simulation_first",
                "max_iterations": 6,
            },
            architect_context={},
            acceptable_policies=("advisory",),
            acceptable_paths=("simulation_first",),
            expected_formal_required_for_final=False,
        ),
        ArchitectPathPolicyCase(
            case_id="optional_path_choice",
            question=OpenResearchQuestion(
                id="architect_policy_optional_choice",
                title="Adaptive inference method with mixed evidence costs",
                description=(
                    "Design an adaptive inference method where simulation can "
                    "quickly find counterexamples, but finite-sample calibration "
                    "subclaims may be good formalization targets if cheap."
                ),
                tags=("adaptive_inference", "optional_formalization"),
            ),
            runtime_config={
                "formal_verification_policy": "optional",
                "recommended_research_path": "",
                "max_iterations": 8,
            },
            architect_context={},
            acceptable_policies=("optional", "advisory", "required"),
            acceptable_paths=("simulation_first", "proof_first", "dual_track"),
            expected_formal_required_for_final=None,
        ),
    )
