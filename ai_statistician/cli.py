from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Mapping

from .agent_runtime import (
    AgentTask,
    agent_task_from_payload,
    restore_agent_task_continuation,
)
from .algorithms import audit_algorithm_registry
from .assumption_interface_export import export_assumption_interfaces
from .autoform_harness import audit_autoform_harness
from .capability_audit import build_capability_audit, write_capability_audit
from .doctor import build_doctor_report, write_doctor_manifest
from .evaluation import EvalConfig, run_seed_eval
from .autoform_target_export import export_autoform_targets
from .frontier_backlog_audit import audit_frontier_backlog
from .frontier_coverage_audit import audit_frontier_coverage
from .frontier_discover_and_prove_prompt_packets import (
    export_frontier_discover_and_prove_prompt_packets,
)
from .frontier_evaluation_triage import audit_frontier_evaluation_triage
from .frontier_precision_audit import audit_frontier_precision
from .frontier_simulation_rerun_audit import audit_frontier_simulation_reruns
from .frontier_smoke_benchmark import FrontierSmokeConfig, run_frontier_smoke_benchmark
from .fingerprint import stable_hash
from .frontier_theory_revision_formalization_audit import audit_frontier_theory_revision_formalization
from .frontier_theory_revision_queue import export_frontier_theory_revision_queue
from .frontier_theory_target_audit import audit_frontier_theory_targets
from .formal_gap_task_export import export_formal_gap_lean_tasks
from .formalization_delta_plan import build_formalization_delta_plan
from .formalization_target_audit import audit_formalization_targets
from .formal_source_graph import audit_formal_source_graph
from .formal_source_index import (
    FormalSourceRoot,
    FormalSourceSqliteIndex,
    audit_formal_source_index,
    build_formal_source_search_backend,
)
from .lean_agent_providers import (
    EmpericalProcessLeanRetrievalProvider,
    OpenProverHLMConfig,
    OpenProverHLMProofSearchProvider,
)
from .proof_bank_formal_source import build_default_formal_source_retriever
from .formal_source_hybrid import FormalSourceHybridRetriever
from .formal_source_retrieval_ablation import run_formal_source_retrieval_ablation_benchmark
from .formal_source_retrieval_benchmark import (
    ALL_FORMAL_SOURCE_RETRIEVAL_BENCHMARKS,
    DEFAULT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK,
    EXTERNAL_USER_INTENT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK,
    run_formal_source_retrieval_benchmark,
)
from .huggingface_lean_source_audit import audit_huggingface_lean_sources
from .hf_lean_source_revalidation_tasks import (
    export_huggingface_lean_source_revalidation_tasks,
)
from .hf_lean_source_revalidation_prompt_packets import (
    export_huggingface_lean_source_revalidation_prompt_packets,
)
from .hf_lean_source_revalidation_artifact_validation import (
    export_huggingface_lean_source_revalidation_artifact_validation,
)
from .hf_lean_source_revalidation_promotion_queue import (
    export_huggingface_lean_source_revalidation_promotion_queue,
)
from .intake_audit import audit_question_intake
from .lean_rag_package_audit import (
    apply_lean_rag_source_registry_expansion,
    audit_lean_rag_package,
    preflight_lean_rag_source_registry_expansion,
    stage_lean_rag_source_registry_expansion,
)
from .lean_blueprint_knowledge import export_lean_blueprint_knowledge
from .lean_rag_dependency_health import audit_lean_rag_dependency_health
from .paper_theory_roundtrip import export_paper_theory_roundtrip
from .proof_audit import audit_proof_bank
from .proof_bank_action_export import export_proof_bank_actions
from .proof_bank import all_obligations, obligations_by_tags
from .proof_bank_expansion_export import export_proof_bank_expansion_candidates
from .proof_policy_baseline import evaluate_retrieval_proof_policy_baseline
from .proof_policy_model import train_proof_policy_model
from .proof_search_audit import audit_proof_search_controller
from .proof_search_kernel_rerun_queue import export_proof_search_kernel_rerun_queue
from .proof_search_retrieval_ablation import run_proof_search_retrieval_ablation
from .proof_search_training_export import export_proof_search_process_dataset
from .proof_search_value_model import train_proof_search_value_model
from .proof_training_export import export_proof_training_dataset
from .prover_component_audit import build_prover_component_audit, write_prover_component_audit
from .release import ReleaseBundleConfig, build_release_bundle
from .research_evaluation import ResearchEvalConfig, run_research_seed_eval
from .research_gap_audit import audit_research_gap_backlog
from .research_intake_audit import audit_research_question_intake
from .research_knowledge_audit import audit_research_knowledge
from .research_lab import audit_research_algorithm_registry, load_open_research_questions, run_research_benchmark
from .research_next_iteration_audit import audit_next_iteration_queue
from .research_capability_audit import build_research_capability_audit, write_research_capability_audit
from .research_policy_baseline import evaluate_research_policy_baseline
from .research_report import build_research_markdown_report
from .research_source_library import (
    load_research_source_execution_spec,
    load_research_source_snapshot,
)
from .research_architect import (
    AnthropicArchitectLLMProvider,
    LLMTheoryDeveloperAgent,
    ResearchArchitectAgent,
    ResearchArchitectConfig,
    StaticArchitectLLMProvider,
)
from .architect_coordinator_llm import ArchitectCoordinatorConfig, LLMArchitectCoordinatorAgent
from .architect_research_path_policy_eval import (
    run_architect_research_path_policy_eval,
    write_architect_research_path_policy_eval_failure_manifest,
)
from .algorithm_engineer_llm import AlgorithmEngineerConfig, LLMAlgorithmEngineerAgent
from .model_backend import (
    LIVE_EVALUATION_CLAUDE_MODEL,
    LIVE_EVALUATION_CLAUDE_MODEL_TIER,
    DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
    LIVE_CLAUDE_MODEL_TIERS,
    SUPPORTED_GENERATOR_PROVIDERS,
    SUPPORTED_LIVE_GENERATOR_PROVIDERS,
    OpenAIResponsesGeneratorBackend,
    claude_model_tier_for_model,
    default_generator_model,
    default_generator_provider,
)
from .proof_state_feedback import (
    DEFAULT_LEAN_TOOL_TIMEOUT_SECONDS,
    LeanLspMcpProofStateFeedbackProvider,
    LocalLeanProofStateFeedbackProvider,
)
from .simulation_engineer_llm import LLMSimulationEngineerAgent, SimulationEngineerConfig
from .research_agent_runtime import (
    ResearchAgentRuntimeConfig,
    RUNTIME_SCHEMA_VERSION,
    run_research_agent_runtime,
)
from .research_agent_runtime_audit import audit_research_agent_runtime
from .research_trace_audit import audit_research_traces
from .research_training_export import export_research_training_dataset
from .critic_evaluator_llm import CriticEvaluatorConfig, LLMCriticEvaluatorAgent
from .generated_code_semantic_reviewer_llm import (
    GeneratedCodeSemanticReviewerConfig,
    LLMGeneratedCodeSemanticReviewerAgent,
)
from .formal_target_semantic_reviewer_llm import (
    FormalTargetSemanticReviewerConfig,
    LLMFormalTargetSemanticReviewerAgent,
)
from .cross_family_eval_protocol import (
    load_cross_family_eval_protocol,
    resolve_cross_family_eval_panel,
)
from .formalizer_llm import FormalizerConfig, LLMFormalizerProofEngineerAgent
from .questions import QUESTIONS, load_question_file
from .retrieval import audit_proof_bank_retrieval
from .system import AIStatisticianSystem, compact_summary, write_run_manifest, write_trace
from .system_audit import SystemAuditConfig, load_audit_questions, run_system_audit
from .task_family import (
    is_explicit_task_family,
    primary_task_family_from_question,
    task_family_value,
)
from .theorem_composition_export import export_theorem_composition_packets
from .theory_proposal import GeneratorTheoryProposer
from .trace_audit import audit_run_traces
from .verifier import AxleProofVerifier, LocalLeanProofVerifier, MockProofVerifier


_DEFAULT_DOTENV = Path(".env")
_OPERATOR_DOTENV_ENV_VAR = "AI_STATISTICIAN_ENV_FILE"
_OPERATOR_DOTENV_FILENAMES = (
    "api_key_AI_statistician.md",
    "api_keys_AI_statistician.md",
)
# Global safety ceiling; source-workspace and lineage budgets remain the loop guards.
FULL_LIVE_MIN_AGENT_RUNTIME_ITERATIONS = 40
RESEARCH_EVAL_MIN_AGENT_RUNTIME_ITERATIONS = 24
LIVE_EVALUATION_MIN_ARCHITECT_MAX_TOKENS = 3000
LIVE_EVALUATION_MIN_METRIC_REVIEWER_MAX_TOKENS = 16000
LIVE_EVALUATION_MIN_SERIOUS_THEORY_MAX_TOKENS = 16000
SERIOUS_THEORY_MIN_LLM_TIMEOUT_SECONDS = (
    DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS * 3.0
)
RESEARCH_AGENT_RUNTIME_FORMAL_SOURCE_INDEX_CACHE = Path(
    "runs/formal_source_index_cache/formal_source_index.sqlite"
)


def _resolve_dotenv_path(path: Path | str | None) -> Path:
    requested = Path(path or _DEFAULT_DOTENV).expanduser()
    if requested.exists():
        return requested
    if requested != _DEFAULT_DOTENV:
        return requested

    operator_env_file = os.environ.get(_OPERATOR_DOTENV_ENV_VAR, "").strip()
    if operator_env_file:
        return Path(os.path.expandvars(operator_env_file)).expanduser()

    for filename in _OPERATOR_DOTENV_FILENAMES:
        candidate = Path.home() / "Downloads" / filename
        if candidate.exists():
            return candidate
    return requested


def _load_dotenv(path: Path) -> None:
    path = _resolve_dotenv_path(path)
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("```"):
            continue
        if stripped.lower().startswith("export "):
            stripped = stripped[len("export ") :].strip()
        if "=" in stripped:
            key, value = stripped.split("=", 1)
        elif ":" in stripped:
            key, value = stripped.split(":", 1)
            key = _dotenv_key_from_markdown_label(key)
        else:
            key = _dotenv_key_from_secret_value(stripped)
            value = stripped
        key = key.strip()
        value = value.strip().strip("'\"`")
        if key and value:
            os.environ.setdefault(key, value)


def _dotenv_key_from_markdown_label(label: str) -> str:
    normalized = "".join(
        ch for ch in str(label or "").strip().lower() if ch.isalnum()
    )
    if normalized in {
        "anthropicapikey",
        "anthropicapi",
        "claudeapikey",
        "claudeapi",
    }:
        return "ANTHROPIC_API_KEY"
    if normalized in {"openaiapikey", "openaiapi"}:
        return "OPENAI_API_KEY"
    if normalized in {"aristotleapikey", "aristotleapi"}:
        return "ARISTOTLE_API_KEY"
    if normalized in {
        "axleapikey",
        "axleapi",
        "axiommathaxleapikey",
        "axiommathaxleapi",
    }:
        return "AXLE_API_KEY"
    return str(label or "").strip()


def _dotenv_key_from_secret_value(value: str) -> str:
    stripped = str(value or "").strip()
    if stripped.startswith("sk-ant-"):
        return "ANTHROPIC_API_KEY"
    if stripped.startswith("sk-"):
        return "OPENAI_API_KEY"
    return ""






def _load_runtime_resume_task_from_manifest(
    path: Path,
) -> tuple[str, AgentTask, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    artifact_kind = str(payload.get("artifact_kind", "") or "")
    if artifact_kind != "RuntimePendingNextTask":
        artifacts = payload.get("artifacts", {})
        pending_path_value = (
            artifacts.get("runtime_pending_next_tasks_jsonl", "")
            if isinstance(artifacts, Mapping)
            else ""
        )
        pending_path = _resolve_runtime_resume_path(
            str(pending_path_value or ""),
            base_dir=path.parent,
        )
        pending_rows: list[Mapping[str, Any]] = []
        if pending_path is not None:
            for line in pending_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                if isinstance(row, Mapping):
                    pending_rows.append(row)
        selected_rows = list(pending_rows)
        if len(selected_rows) != 1:
            failure_summary = payload.get("runtime_failure_summary", {})
            terminal_question_id = str(
                failure_summary.get("terminal_question_id", "") or ""
            ) if isinstance(failure_summary, Mapping) else ""
            selected_rows = [
                row
                for row in pending_rows
                if terminal_question_id
                and str(row.get("question_id", "") or "")
                == terminal_question_id
            ]
        if len(selected_rows) != 1:
            raise ValueError(
                f"{path} does not resolve to exactly one pending runtime task"
            )
        payload = dict(selected_rows[0])
        artifact_kind = "RuntimePendingNextTask"

    question_id = str(payload.get("question_id", "") or "")
    if not question_id:
        raise ValueError(
            f"{path} pending task does not expose a question id; cannot resume safely"
        )
    artifacts = _runtime_resume_blackboard_artifacts(
        resume_path=path,
        resume_payload=payload,
        question_id=question_id,
    )
    continuation_ref = payload.get("pending_task_continuation_ref", {})
    if isinstance(continuation_ref, Mapping) and continuation_ref:
        continuation_id = str(
            continuation_ref.get("continuation_id", "") or ""
        )
        continuation = artifacts.get(continuation_id, {})
        if not isinstance(continuation, Mapping) or (
            continuation.get("artifact_kind")
            != "RuntimeAgentTaskContinuation"
        ):
            raise ValueError(
                f"{path} pending task continuation is unavailable"
            )
        if (
            stable_hash(dict(continuation))
            != str(continuation_ref.get("continuation_hash", "") or "")
            or continuation.get("task_ref")
            != continuation_ref.get("task_ref")
        ):
            raise ValueError(
                f"{path} pending task continuation hash mismatch"
            )
        task = restore_agent_task_continuation(continuation, artifacts)
    else:
        task_payload = payload.get("pending_next_task", {})
        if not isinstance(task_payload, Mapping) or not task_payload or (
            task_payload.get("artifact_kind") == "AgentTaskRef"
        ):
            raise ValueError(
                f"{path} pending task has no resumable continuation"
            )
        task = agent_task_from_payload(task_payload)

    task_question_id = _runtime_resume_task_question_id(
        {"inputs": task.inputs}
    )
    if task_question_id and task_question_id != question_id:
        raise ValueError(
            f"{path} pending task question id does not match its checkpoint"
        )
    return question_id, task, artifacts


def _runtime_resume_blackboard_artifacts(
    *,
    resume_path: Path,
    resume_payload: Mapping[str, Any],
    question_id: str,
) -> dict[str, Any]:
    source_manifest = _resolve_runtime_resume_source_manifest(
        resume_path=resume_path,
        resume_payload=resume_payload,
    )
    if source_manifest is None:
        return {}
    artifacts = source_manifest.get("artifacts", {})
    if not isinstance(artifacts, Mapping):
        return {}
    result_paths = artifacts.get("per_question_results", [])
    if not isinstance(result_paths, list):
        return {}
    for raw_result_path in result_paths:
        result_path = _resolve_runtime_resume_path(
            str(raw_result_path),
            base_dir=Path(source_manifest.get("_manifest_path", "") or ".").parent,
        )
        if result_path is None:
            continue
        try:
            result_payload = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if _runtime_result_question_id(result_payload) != question_id:
            continue
        blackboard = result_payload.get("blackboard", {})
        if not isinstance(blackboard, Mapping):
            return {}
        blackboard_artifacts = blackboard.get("artifacts", {})
        if not isinstance(blackboard_artifacts, Mapping):
            return {}
        rehydrated_artifacts = _load_runtime_blackboard_artifact_payloads(
            result_payload=result_payload,
            result_path=result_path,
        )
        rehydrated_artifacts.update(
            _runtime_resume_prior_ledger_artifacts(
                result_payload,
                question_id=question_id,
                source_manifest_path=str(
                    source_manifest.get("_manifest_path", "") or resume_path
                ),
                source_result_path=str(result_path),
            )
        )
        return rehydrated_artifacts
    return {}


def _load_runtime_blackboard_artifact_payloads(
    *,
    result_payload: Mapping[str, Any],
    result_path: Path,
) -> dict[str, Any]:
    blackboard = result_payload.get("blackboard", {})
    artifacts = (
        blackboard.get("artifacts", {})
        if isinstance(blackboard, Mapping)
        else {}
    )
    if not isinstance(artifacts, Mapping):
        raise ValueError(f"{result_path} has no runtime artifact map")
    if (
        result_payload.get("blackboard_artifact_payload_policy")
        != "content_addressed_refs"
    ):
        return {
            str(artifact_id): deepcopy(artifact)
            for artifact_id, artifact in artifacts.items()
        }

    loaded: dict[str, Any] = {}
    for raw_artifact_id, raw_reference in artifacts.items():
        artifact_id = str(raw_artifact_id)
        if not isinstance(raw_reference, Mapping) or (
            raw_reference.get("artifact_kind") != "RuntimeArtifactRef"
        ):
            raise ValueError(
                f"{result_path} artifact {artifact_id} is not a stored reference"
            )
        if str(raw_reference.get("artifact_id", "") or "") != artifact_id:
            raise ValueError(
                f"{result_path} artifact reference identity mismatch: {artifact_id}"
            )
        artifact_path = _resolve_runtime_resume_path(
            str(raw_reference.get("path", "") or ""),
            base_dir=result_path.parent,
        )
        if artifact_path is None:
            raise ValueError(
                f"{result_path} artifact payload is unavailable: {artifact_id}"
            )
        try:
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"{result_path} artifact payload is unreadable: {artifact_id}"
            ) from exc
        if stable_hash(artifact) != str(
            raw_reference.get("content_hash", "") or ""
        ):
            raise ValueError(
                f"{result_path} artifact payload hash mismatch: {artifact_id}"
            )
        expected_kind = str(raw_reference.get("payload_kind", "") or "")
        if expected_kind and (
            not isinstance(artifact, Mapping)
            or str(artifact.get("artifact_kind", "") or "")
            != expected_kind
        ):
            raise ValueError(
                f"{result_path} artifact payload kind mismatch: {artifact_id}"
            )
        loaded[artifact_id] = artifact
    return loaded


def _runtime_resume_prior_ledger_artifacts(
    result_payload: Mapping[str, Any],
    *,
    question_id: str,
    source_manifest_path: str,
    source_result_path: str,
) -> dict[str, Any]:
    blackboard = (
        result_payload.get("blackboard", {})
        if isinstance(result_payload.get("blackboard", {}), Mapping)
        else {}
    )
    prior_evidence = [
        dict(row)
        for row in blackboard.get("evidence_ledger", []) or []
        if isinstance(row, Mapping)
    ]
    prior_handoffs = [
        dict(row)
        for row in blackboard.get("handoff_ledger", []) or []
        if isinstance(row, Mapping)
    ]
    artifacts: dict[str, Any] = {}
    common = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "question_id": str(question_id or ""),
        "source_manifest_path": str(source_manifest_path or ""),
        "source_result_path": str(source_result_path or ""),
        "proof_evidence_status": "PRIOR_RUNTIME_LEDGER_NOT_CURRENT_EVIDENCE",
        "boundary": (
            "Prior runtime ledger rows are resume continuity memory only. "
            "They are rehydrated as blackboard artifacts, not as current "
            "evidence_ledger or handoff_ledger entries, and do not prove any "
            "new statistical, simulation, generated-code, or theorem claim."
        ),
    }
    if prior_evidence:
        artifacts[f"runtime_resume_prior_evidence_ledger:{question_id}"] = {
            **common,
            "artifact_kind": "RuntimeResumePriorEvidenceLedger",
            "n_prior_evidence_rows": len(prior_evidence),
            "rows": prior_evidence,
        }
    if prior_handoffs:
        artifacts[f"runtime_resume_prior_handoff_ledger:{question_id}"] = {
            **common,
            "artifact_kind": "RuntimeResumePriorHandoffLedger",
            "n_prior_handoff_rows": len(prior_handoffs),
            "rows": prior_handoffs,
        }
    return artifacts


def _resolve_runtime_resume_source_manifest(
    *,
    resume_path: Path,
    resume_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    source_manifest_path = str(resume_payload.get("source_manifest_path", "") or "")
    if not source_manifest_path and str(resume_payload.get("artifact_kind", "") or "") != "RuntimePendingNextTask":
        source_manifest_path = str(resume_path)
    if not source_manifest_path:
        return None
    path = _resolve_runtime_resume_path(source_manifest_path, base_dir=resume_path.parent)
    if path is None:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(payload, dict):
        payload["_manifest_path"] = str(path)
        return payload
    return None


def _resolve_runtime_resume_path(raw_path: str, *, base_dir: Path) -> Path | None:
    if not raw_path:
        return None
    path = Path(raw_path)
    candidates = [path]
    if not path.is_absolute():
        candidates.append(base_dir / path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _runtime_result_question_id(payload: Mapping[str, Any]) -> str:
    traces = payload.get("traces", [])
    if isinstance(traces, list):
        for trace in traces:
            if not isinstance(trace, Mapping):
                continue
            task = trace.get("task", {})
            if not isinstance(task, Mapping):
                continue
            question_id = _runtime_resume_task_question_id(task)
            if question_id:
                return question_id
    blackboard = payload.get("blackboard", {})
    if isinstance(blackboard, Mapping):
        project_id = str(blackboard.get("project_id", "") or "")
        prefix = "ai_statistician:"
        if project_id.startswith(prefix):
            return project_id[len(prefix) :]
    return ""


def _runtime_resume_task_question_id(task_payload: Mapping[str, object]) -> str:
    inputs = task_payload.get("inputs", {})
    if not isinstance(inputs, Mapping):
        return ""
    question = inputs.get("question", {})
    if isinstance(question, Mapping) and str(question.get("id", "") or ""):
        return str(question.get("id", "") or "")
    environment_feedback = inputs.get("environment_feedback", {})
    if isinstance(environment_feedback, Mapping) and str(
        environment_feedback.get("question_id", "") or ""
    ):
        return str(environment_feedback.get("question_id", "") or "")
    return ""


def _select_questions_by_id(
    questions: list[object],
    question_ids: list[str] | tuple[str, ...],
) -> tuple[list[object], list[str]]:
    requested = [str(item).strip() for item in question_ids if str(item).strip()]
    if not requested:
        return questions, []
    by_id = {str(getattr(question, "id", "") or ""): question for question in questions}
    selected: list[object] = []
    missing: list[str] = []
    for question_id in requested:
        question = by_id.get(question_id)
        if question is None:
            missing.append(question_id)
            continue
        selected.append(question)
    return selected, missing


def _selected_question_task_families(questions: list[object]) -> list[str]:
    families: list[str] = []
    for question in questions:
        family = primary_task_family_from_question(question)
        if is_explicit_task_family(family):
            families.append(family)
    return sorted(dict.fromkeys(families))


def _select_questions_by_task_family(
    questions: list[object],
    task_families: list[str] | tuple[str, ...],
) -> tuple[list[object], list[str]]:
    requested = [
        task_family_value(item)
        for item in task_families
        if str(item).strip()
    ]
    if not requested:
        return questions, []
    invalid_requested = [
        item for item in requested if not is_explicit_task_family(item)
    ]
    explicit_requested = [
        item for item in requested if is_explicit_task_family(item)
    ]
    requested_keys = {item.lower() for item in explicit_requested}
    selected: list[object] = []
    available_keys: set[str] = set()
    for question in questions:
        family = primary_task_family_from_question(question)
        if not is_explicit_task_family(family):
            continue
        family_key = family.lower()
        available_keys.add(family_key)
        if family_key in requested_keys:
            selected.append(question)
    missing = [
        *invalid_requested,
        *(
            item
            for item in explicit_requested
            if item.lower() not in available_keys
        ),
    ]
    return selected, missing


def _minimum_task_family_selection_errors(
    questions: list[object],
    *,
    min_task_families: int,
) -> list[str]:
    if min_task_families <= 0:
        return []
    families = _selected_question_task_families(questions)
    if len(families) >= min_task_families:
        return []
    question_ids = [
        str(getattr(question, "id", "") or "")
        for question in questions
        if str(getattr(question, "id", "") or "")
    ]
    return [
        "--min-task-families="
        f"{min_task_families} requires at least {min_task_families} explicit "
        "statistics task families after question selection; selected "
        f"families={families} question_ids={question_ids}"
    ]


def _cross_family_eval_protocol_selection(
    args: argparse.Namespace,
    questions: list[object],
) -> tuple[list[str], dict[str, Any], list[str]]:
    protocol_path_value = str(
        getattr(args, "cross_family_eval_protocol", "") or ""
    ).strip()
    panel_id = str(getattr(args, "cross_family_eval_panel", "") or "").strip()
    if not protocol_path_value and not panel_id:
        return [], {}, []
    errors: list[str] = []
    if not protocol_path_value:
        errors.append(
            "--cross-family-eval-panel requires --cross-family-eval-protocol"
        )
    if not panel_id:
        errors.append(
            "--cross-family-eval-protocol requires --cross-family-eval-panel"
        )
    if errors:
        return [], {}, errors
    if not bool(getattr(args, "capability_eval", False)):
        errors.append("cross-family protocol runs require --capability-eval")
    if str(getattr(args, "capability_eval_preset", "") or "") != "full-live":
        errors.append(
            "cross-family protocol runs require --capability-eval-preset full-live"
        )
    forbidden_inputs = (
        ("resume_runtime_manifest", "--resume-runtime-manifest"),
        ("context_json", "--context-json"),
        ("question_task_family", "--question-task-family"),
    )
    for field, flag in forbidden_inputs:
        if getattr(args, field, None):
            errors.append(f"fresh cross-family protocol runs forbid {flag}")
    if int(getattr(args, "max_questions", 0) or 0) != 0:
        errors.append("fresh cross-family protocol runs forbid --max-questions")
    try:
        protocol = load_cross_family_eval_protocol(Path(protocol_path_value))
        expected_question_source = Path(str(protocol["question_source"])).resolve()
        actual_question_source = Path(str(args.question_file)).resolve()
        if expected_question_source != actual_question_source:
            errors.append(
                "cross-family protocol question source mismatch: expected "
                f"{expected_question_source}, got {actual_question_source}"
            )
        selection = resolve_cross_family_eval_panel(
            protocol,
            panel_id=panel_id,
            questions=questions,
        )
        selection["protocol_path"] = str(Path(protocol_path_value))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
        return [], {}, sorted(set(errors))
    requested_ids = [
        str(item).strip()
        for item in getattr(args, "question_id", []) or []
        if str(item).strip()
    ]
    panel_question_ids = list(selection["question_ids"])
    if requested_ids and (
        len(requested_ids) != len(panel_question_ids)
        or set(requested_ids) != set(panel_question_ids)
    ):
        errors.append(
            "--question-id values must exactly match the frozen protocol panel; "
            f"panel={panel_question_ids} requested={requested_ids}"
        )
    return panel_question_ids, selection, sorted(set(errors))































































LIVE_GENERATOR_PROVIDER_CHOICES = SUPPORTED_LIVE_GENERATOR_PROVIDERS
GENERATOR_PROVIDER_CHOICES = SUPPORTED_GENERATOR_PROVIDERS
SUBSYSTEM_GENERATOR_PROVIDER_CHOICES = (
    "same",
    *GENERATOR_PROVIDER_CHOICES,
    "none",
)

_RUNTIME_EVALUATION_MODEL_TIER_FIELDS = (
    "theory_model_tier",
    "serious_theory_model_tier",
)


def _runtime_evaluation_model_tier(args: argparse.Namespace) -> str:
    evaluation_mode = bool(getattr(args, "research_eval", False)) or bool(
        getattr(args, "capability_eval", False)
    )
    if evaluation_mode:
        return LIVE_EVALUATION_CLAUDE_MODEL_TIER
    return ""


def _runtime_effective_model_tier(
    args: argparse.Namespace,
    default_tier: str,
) -> str:
    return _runtime_evaluation_model_tier(args) or str(default_tier or "sonnet")


def _runtime_resolved_provider_choice(
    args: argparse.Namespace,
    provider_choice: str,
) -> str:
    choice = str(provider_choice or "same").strip().lower()
    if choice == "same":
        return str(
            getattr(args, "provider", _default_live_generator_provider()) or ""
        ).strip().lower()
    return choice


def _runtime_evaluation_model_name(
    args: argparse.Namespace,
    *,
    provider_choice: str,
    configured_model: str,
) -> str:
    if (
        _runtime_evaluation_model_tier(args)
        and _runtime_resolved_provider_choice(args, provider_choice) == "anthropic"
    ):
        return LIVE_EVALUATION_CLAUDE_MODEL
    return str(configured_model or "")


def _apply_research_agent_runtime_evaluation_model_policy(
    args: argparse.Namespace,
) -> None:
    """Pin live research evaluations to the current source-checked Haiku."""

    evaluation_tier = _runtime_evaluation_model_tier(args)
    if not evaluation_tier:
        return
    args.evaluation_claude_model_tier = evaluation_tier
    args.evaluation_claude_model = LIVE_EVALUATION_CLAUDE_MODEL
    for field_name in _RUNTIME_EVALUATION_MODEL_TIER_FIELDS:
        if hasattr(args, field_name):
            setattr(args, field_name, evaluation_tier)


def _research_agent_runtime_evaluation_model_policy_errors(
    args: argparse.Namespace,
) -> list[str]:
    evaluation_tier = _runtime_evaluation_model_tier(args)
    if not evaluation_tier:
        return []
    errors: list[str] = []
    if str(
        getattr(args, "evaluation_claude_model_tier", "") or ""
    ) != evaluation_tier:
        errors.append(
            "live research evaluation model policy was not applied before "
            "runtime construction"
        )
    if str(getattr(args, "evaluation_claude_model", "") or "") != (
        LIVE_EVALUATION_CLAUDE_MODEL
    ):
        errors.append(
            "live research evaluation model policy did not pin the current "
            f"Haiku model {LIVE_EVALUATION_CLAUDE_MODEL}"
        )
    for field_name in _RUNTIME_EVALUATION_MODEL_TIER_FIELDS:
        if not hasattr(args, field_name):
            continue
        configured_tier = str(getattr(args, field_name, "") or "").lower()
        if configured_tier != evaluation_tier:
            errors.append(
                f"live research evaluations require {field_name}="
                f"{evaluation_tier}; configured {configured_tier or 'missing'}"
            )
    return errors


def _default_live_generator_provider() -> str:
    provider = default_generator_provider()
    return provider if provider in LIVE_GENERATOR_PROVIDER_CHOICES else "anthropic"


def _default_model_for_provider(
    provider_name: str,
    requested_model: str = "",
    *,
    model_tier: str = "sonnet",
) -> str:
    return default_generator_model(provider_name, requested_model, model_tier=model_tier)


def _model_for_subsystem_provider(
    *,
    provider_choice: str,
    explicit_model: str,
    args: argparse.Namespace,
    default_model: str,
    model_tier: str,
) -> str:
    model_tier = _runtime_effective_model_tier(args, model_tier)
    explicit_model = _runtime_evaluation_model_name(
        args,
        provider_choice=provider_choice,
        configured_model=explicit_model,
    )
    if explicit_model:
        return explicit_model
    primary_provider = getattr(args, "provider", _default_live_generator_provider())
    if provider_choice == primary_provider:
        return _default_model_for_provider(primary_provider, model_tier=model_tier)
    if provider_choice == "same":
        return default_model
    return _default_model_for_provider(provider_choice, model_tier=model_tier)


def _build_theory_generator_backend(
    *,
    provider_name: str,
    static_response_file: str = "",
    llm_timeout_seconds: float | None = None,
):
    if provider_name == "static":
        if not static_response_file:
            raise ValueError("a static response file is required with provider=static")
        return (
            StaticArchitectLLMProvider(Path(static_response_file).read_text(encoding="utf-8")),
            "static",
        )
    if provider_name == "anthropic":
        return AnthropicArchitectLLMProvider(timeout_s=llm_timeout_seconds), "anthropic"
    if provider_name == "openai":
        return OpenAIResponsesGeneratorBackend(timeout_s=llm_timeout_seconds), "openai"
    raise ValueError(f"unknown theory provider: {provider_name}")


def _build_algorithm_engineer_agent_from_args(args: argparse.Namespace, *, default_model: str):
    provider_choice = getattr(args, "algorithm_engineer_provider", "none")
    if provider_choice == "none":
        return None
    if provider_choice == "same":
        provider_choice = getattr(args, "provider", _default_live_generator_provider())
    static_file = getattr(args, "algorithm_static_response_file", "")
    if provider_choice == "static" and not static_file:
        return None
    provider, provider_name = _build_theory_generator_backend(
        provider_name=provider_choice,
        static_response_file=static_file,
        llm_timeout_seconds=getattr(args, "llm_timeout_seconds", None),
    )
    model_tier = _runtime_effective_model_tier(args, "sonnet")
    model = _model_for_subsystem_provider(
        provider_choice=provider_choice,
        explicit_model=getattr(args, "algorithm_llm_model", ""),
        args=args,
        default_model=default_model,
        model_tier=model_tier,
    )
    return LLMAlgorithmEngineerAgent(
        provider=provider,
        config=AlgorithmEngineerConfig(
            model=model,
            model_tier=model_tier,
            max_tokens=getattr(args, "algorithm_max_tokens", 5000),
            temperature=getattr(args, "algorithm_temperature", 0.1),
            provider_name=provider_name,
            max_validation_retries=0,
        ),
    )


def _build_simulation_engineer_agent_from_args(args: argparse.Namespace, *, default_model: str):
    provider_choice = getattr(args, "simulation_engineer_provider", "none")
    if provider_choice == "none":
        return None
    if provider_choice == "same":
        provider_choice = getattr(args, "provider", _default_live_generator_provider())
    static_file = getattr(args, "simulation_static_response_file", "")
    if provider_choice == "static" and not static_file:
        return None
    provider, provider_name = _build_theory_generator_backend(
        provider_name=provider_choice,
        static_response_file=static_file,
        llm_timeout_seconds=getattr(args, "llm_timeout_seconds", None),
    )
    model_tier = _runtime_effective_model_tier(args, "sonnet")
    model = _model_for_subsystem_provider(
        provider_choice=provider_choice,
        explicit_model=getattr(args, "simulation_llm_model", ""),
        args=args,
        default_model=default_model,
        model_tier=model_tier,
    )
    return LLMSimulationEngineerAgent(
        provider=provider,
        config=SimulationEngineerConfig(
            model=model,
            model_tier=model_tier,
            max_tokens=getattr(args, "simulation_max_tokens", 8000),
            temperature=getattr(args, "simulation_temperature", 0.1),
            provider_name=provider_name,
            max_validation_retries=0,
        ),
    )


def _build_formalizer_agent_from_args(args: argparse.Namespace, *, default_model: str):
    provider_choice = getattr(args, "formalizer_provider", "none")
    if provider_choice == "none":
        return None
    if provider_choice == "same":
        provider_choice = getattr(args, "provider", _default_live_generator_provider())
    static_file = getattr(args, "formalizer_static_response_file", "")
    if provider_choice == "static" and not static_file:
        return None
    provider, provider_name = _build_theory_generator_backend(
        provider_name=provider_choice,
        static_response_file=static_file,
        llm_timeout_seconds=getattr(args, "llm_timeout_seconds", None),
    )
    model_tier = _runtime_effective_model_tier(args, "sonnet")
    model = _model_for_subsystem_provider(
        provider_choice=provider_choice,
        explicit_model=getattr(args, "formalizer_llm_model", ""),
        args=args,
        default_model=default_model,
        model_tier=model_tier,
    )
    return LLMFormalizerProofEngineerAgent(
        provider=provider,
        config=FormalizerConfig(
            model=model,
            model_tier=model_tier,
            max_tokens=getattr(args, "formalizer_max_tokens", 6000),
            temperature=getattr(args, "formalizer_temperature", 0.1),
            provider_name=provider_name,
        ),
    )


def _build_critic_evaluator_agent_from_args(args: argparse.Namespace, *, default_model: str):
    provider_choice = getattr(args, "critic_evaluator_provider", "none")
    if provider_choice == "none":
        return None
    if provider_choice == "same":
        provider_choice = getattr(args, "provider", _default_live_generator_provider())
    static_file = getattr(args, "critic_static_response_file", "")
    if provider_choice == "static" and not static_file:
        return None
    provider, provider_name = _build_theory_generator_backend(
        provider_name=provider_choice,
        static_response_file=static_file,
        llm_timeout_seconds=getattr(args, "llm_timeout_seconds", None),
    )
    model_tier = _runtime_effective_model_tier(args, "haiku")
    model = _model_for_subsystem_provider(
        provider_choice=provider_choice,
        explicit_model=getattr(args, "critic_llm_model", ""),
        args=args,
        default_model=default_model,
        model_tier=model_tier,
    )
    return LLMCriticEvaluatorAgent(
        provider=provider,
        config=CriticEvaluatorConfig(
            model=model,
            model_tier=model_tier,
            max_tokens=getattr(args, "critic_max_tokens", 5000),
            temperature=getattr(args, "critic_temperature", 0.1),
            provider_name=provider_name,
        ),
    )


def _build_generated_code_semantic_reviewer_agent_from_args(
    args: argparse.Namespace,
    *,
    default_model: str,
):
    provider_choice = getattr(
        args,
        "generated_code_semantic_reviewer_provider",
        "none",
    )
    if provider_choice == "none":
        return None
    if provider_choice == "same":
        provider_choice = getattr(args, "provider", _default_live_generator_provider())
    static_file = getattr(
        args,
        "generated_code_semantic_reviewer_static_response_file",
        "",
    )
    if provider_choice == "static" and not static_file:
        return None
    provider, provider_name = _build_theory_generator_backend(
        provider_name=provider_choice,
        static_response_file=static_file,
        llm_timeout_seconds=getattr(args, "llm_timeout_seconds", None),
    )
    model_tier = _runtime_effective_model_tier(args, "sonnet")
    model = _model_for_subsystem_provider(
        provider_choice=provider_choice,
        explicit_model=getattr(
            args,
            "generated_code_semantic_reviewer_llm_model",
            "",
        ),
        args=args,
        default_model=default_model,
        model_tier=model_tier,
    )
    return LLMGeneratedCodeSemanticReviewerAgent(
        provider=provider,
        config=GeneratedCodeSemanticReviewerConfig(
            model=model,
            model_tier=model_tier,
            max_tokens=getattr(
                args,
                "generated_code_semantic_reviewer_max_tokens",
                7000,
            ),
            temperature=getattr(
                args,
                "generated_code_semantic_reviewer_temperature",
                0.0,
            ),
            provider_name=provider_name,
            max_validation_retries=(
                2
                if _runtime_evaluation_model_tier(args)
                else GeneratedCodeSemanticReviewerConfig().max_validation_retries
            ),
        ),
    )


def _build_formal_target_semantic_reviewer_agent_from_args(
    args: argparse.Namespace,
    *,
    default_model: str,
):
    provider_choice = getattr(
        args,
        "formal_target_semantic_reviewer_provider",
        "none",
    )
    if provider_choice == "none":
        return None
    if provider_choice == "same":
        provider_choice = getattr(args, "provider", _default_live_generator_provider())
    static_file = getattr(
        args,
        "formal_target_semantic_reviewer_static_response_file",
        "",
    )
    if provider_choice == "static" and not static_file:
        return None
    provider, provider_name = _build_theory_generator_backend(
        provider_name=provider_choice,
        static_response_file=static_file,
        llm_timeout_seconds=getattr(args, "llm_timeout_seconds", None),
    )
    model_tier = _runtime_effective_model_tier(args, "sonnet")
    model = _model_for_subsystem_provider(
        provider_choice=provider_choice,
        explicit_model=getattr(
            args,
            "formal_target_semantic_reviewer_llm_model",
            "",
        ),
        args=args,
        default_model=default_model,
        model_tier=model_tier,
    )
    return LLMFormalTargetSemanticReviewerAgent(
        provider=provider,
        config=FormalTargetSemanticReviewerConfig(
            model=model,
            model_tier=model_tier,
            max_tokens=getattr(
                args,
                "formal_target_semantic_reviewer_max_tokens",
                8000,
            ),
            temperature=getattr(
                args,
                "formal_target_semantic_reviewer_temperature",
                0.0,
            ),
            provider_name=provider_name,
        ),
    )


def _build_architect_coordinator_agent_from_args(
    args: argparse.Namespace,
    *,
    default_model: str,
    formal_source_retriever: Any = None,
):
    provider_choice = getattr(args, "architect_coordinator_provider", "none")
    if provider_choice == "none":
        return None
    if provider_choice == "same":
        provider_choice = getattr(args, "provider", _default_live_generator_provider())
    static_file = getattr(args, "architect_static_response_file", "")
    if provider_choice == "static" and not static_file:
        return None
    provider, provider_name = _build_theory_generator_backend(
        provider_name=provider_choice,
        static_response_file=static_file,
        llm_timeout_seconds=getattr(args, "llm_timeout_seconds", None),
    )
    model_tier = _runtime_effective_model_tier(args, "sonnet")
    model = _model_for_subsystem_provider(
        provider_choice=provider_choice,
        explicit_model=getattr(args, "architect_llm_model", ""),
        args=args,
        default_model=default_model,
        model_tier=model_tier,
    )
    return LLMArchitectCoordinatorAgent(
        provider=provider,
        preflight_source_retriever=formal_source_retriever,
        config=ArchitectCoordinatorConfig(
            model=model,
            model_tier=model_tier,
            max_tokens=getattr(args, "architect_max_tokens", 3000),
            temperature=getattr(args, "architect_temperature", 0.1),
            provider_name=provider_name,
            metric_semantic_reviewer_model=_runtime_evaluation_model_name(
                args,
                provider_choice=provider_choice,
                configured_model=getattr(
                    args,
                    "architect_metric_semantic_reviewer_llm_model",
                    "",
                ),
            ),
            metric_semantic_reviewer_model_tier=model_tier,
            metric_semantic_reviewer_max_tokens=getattr(
                args,
                "architect_metric_semantic_reviewer_max_tokens",
                7000,
            ),
            metric_semantic_reviewer_max_revisions=getattr(
                args,
                "architect_metric_semantic_reviewer_max_revisions",
                1,
            ),
        ),
    )


async def _demo(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    system = (
        AIStatisticianSystem.with_axle(n_runs=args.runs, seed=args.seed)
        if args.real_lean
        else AIStatisticianSystem(n_runs=args.runs, seed=args.seed)
    )
    questions = _questions_from_args(args)
    reports = []
    for question in questions:
        report = await system.run(question)
        reports.append(report)
        if args.out:
            write_trace(report, Path(args.out))
    if args.out:
        write_run_manifest(reports, Path(args.out))

    print("\nAI Statistician System")
    print("=" * 72)
    for report in reports:
        s = compact_summary(report)
        print(
            f"{s['status']:18} {s['question']:24} "
            f"formal={s['formal']:>4} verifier={s['verifier']}"
        )
        print(
            f"  bias={s['bias']:+.5f} rel_bias={s['relative_bias']:+.5f} "
            f"rmse={s['rmse']:.5f} coverage95={s['coverage_95']:.3f}"
        )
        print(f"  sim feedback: {report.simulation.feedback}")
        for proof in report.proofs:
            badge = "OK" if proof.ok else "FAIL"
            print(f"  proof {badge}: {proof.obligation_id} ({proof.elapsed_ms} ms)")
            if proof.errors:
                print(f"    error: {proof.errors[0][:180]}")
        if args.verbose:
            print(f"  estimator: {report.estimator.formula}")
            print(f"  obligations: {', '.join(report.estimator.formal_obligation_ids)}")
    if args.out:
        print(f"\ntraces written to {Path(args.out).resolve()}")
        print(f"manifest written to {(Path(args.out) / 'manifest.json').resolve()}")
    return 0


def _questions_from_args(args: argparse.Namespace):
    proposer = _theory_proposer_from_args(args)
    questions = []
    if args.question_file:
        questions.extend(
            load_question_file(
                Path(args.question_file),
                theory_proposer=proposer,
                force_theory_proposer=bool(getattr(args, "force_llm_theory", False)),
            )
        )
    if getattr(args, "question", None):
        questions.extend(QUESTIONS[question_id] for question_id in args.question)
    if not questions:
        questions.extend(QUESTIONS.values())
    return questions


def _theory_proposer_from_args(args: argparse.Namespace):
    if not getattr(args, "llm_theory", False):
        return None
    provider_choice = getattr(args, "llm_provider", _default_live_generator_provider())
    provider, provider_name = _build_theory_generator_backend(
        provider_name=provider_choice,
        static_response_file=getattr(args, "llm_static_response_file", ""),
    )
    return GeneratorTheoryProposer(
        provider=provider,
        model=_default_model_for_provider(
            provider_choice,
            getattr(args, "llm_model", ""),
            model_tier="haiku",
        ),
        model_tier="haiku",
        provider_name=provider_name,
        max_tokens=getattr(args, "llm_max_tokens", 700),
    )


def _proof_verifier_from_args(args: argparse.Namespace):
    if getattr(args, "local_lean", False):
        lean_project = getattr(args, "lean_project", None) or getattr(
            args,
            "local_lean_project",
            None,
        )
        lean_timeout = getattr(
            args,
            "lean_timeout",
            getattr(args, "local_lean_timeout", 90),
        ) or getattr(args, "local_lean_timeout", 90)
        return LocalLeanProofVerifier(
            project_root=lean_project,
            timeout_s=lean_timeout,
        )
    return AxleProofVerifier() if getattr(args, "real_lean", False) else MockProofVerifier()


def _proof_state_provider_from_args(args: argparse.Namespace):
    local_lean_enabled = bool(getattr(args, "local_lean", False))
    formalizer_candidate_local_lean_enabled = bool(
        getattr(args, "formalizer_candidate_local_lean", False)
    )
    formalizer_candidate_lean_lsp_mcp_enabled = bool(
        getattr(args, "formalizer_candidate_lean_lsp_mcp", False)
    )
    formalizer_candidate_local_lean_enabled = (
        formalizer_candidate_local_lean_enabled
        or formalizer_candidate_lean_lsp_mcp_enabled
    )
    if not local_lean_enabled and not formalizer_candidate_local_lean_enabled:
        return None
    lean_project = (
        (
            getattr(args, "formalizer_candidate_lean_project", None)
            if formalizer_candidate_local_lean_enabled
            else None
        )
        or getattr(args, "lean_project", None)
        or getattr(args, "local_lean_project", None)
    )
    lean_timeout = (
        (
            getattr(args, "formalizer_candidate_lean_timeout", None)
            if formalizer_candidate_local_lean_enabled
            else None
        )
        or getattr(
            args,
            "lean_timeout",
            getattr(args, "local_lean_timeout", 90),
        )
        or getattr(args, "local_lean_timeout", 90)
    )
    provider_cls = (
        LeanLspMcpProofStateFeedbackProvider
        if formalizer_candidate_lean_lsp_mcp_enabled
        else LocalLeanProofStateFeedbackProvider
    )
    provider_kwargs: dict[str, Any] = {
        "project_root": lean_project,
        "timeout_s": lean_timeout,
    }
    if formalizer_candidate_lean_lsp_mcp_enabled:
        provider_kwargs["openprover_root"] = (
            str(getattr(args, "openprover_root", "") or "").strip()
            or _default_openprover_root()
            or None
        )
    return provider_cls(**provider_kwargs)


def _formal_source_retriever_from_runtime_args(
    args: argparse.Namespace,
):
    cache_value = str(
        getattr(
            args,
            "formal_source_index_cache",
            RESEARCH_AGENT_RUNTIME_FORMAL_SOURCE_INDEX_CACHE,
        )
        or ""
    ).strip()
    db_value = str(
        getattr(args, "formal_source_index_db", "") or ""
    ).strip()
    cache_path = Path(cache_value).expanduser() if cache_value else None
    db_path = (
        Path(db_value).expanduser()
        if db_value
        else cache_path
        if cache_path is not None
        else Path(str(getattr(args, "out", "runs/research_agent_runtime")))
        / "formal_source_index.sqlite"
    )
    local_retriever = build_formal_source_search_backend(
        db_path=db_path,
        cache_path=cache_path,
        refresh_cache=bool(
            getattr(args, "refresh_formal_source_index_cache", False)
        ),
    )
    root_value = str(
        getattr(args, "emperical_process_lean_rag_root", "") or ""
    ).strip()
    if not root_value:
        return build_default_formal_source_retriever(
            local_retriever=local_retriever,
        )
    root = Path(root_value).expanduser().resolve()
    script = root / "lean_rag" / "scripts" / "shared_proof_retrieval.py"
    if not script.is_file():
        raise ValueError(
            "--emperical-process-lean-rag-root must point to a checkout containing "
            f"lean_rag/scripts/shared_proof_retrieval.py; missing at {script}"
        )
    external = EmpericalProcessLeanRetrievalProvider(
        root=root,
        db_dir=(
            str(
                getattr(
                    args,
                    "emperical_process_lean_rag_db_dir",
                    "",
                )
                or ""
            ).strip()
            or None
        ),
        source=str(
            getattr(args, "emperical_process_lean_rag_source", "all") or "all"
        ),
        checkouts=tuple(
            getattr(args, "emperical_process_lean_rag_checkout", []) or []
        ),
        no_sorry=True,
        with_graph_context=True,
        reject_unknown_index_signature=not bool(
            getattr(
                args,
                "emperical_process_lean_rag_allow_unsigned_index",
                False,
            )
        ),
        reject_dirty_checkout=not bool(
            getattr(
                args,
                "emperical_process_lean_rag_allow_dirty_index",
                False,
            )
        ),
    )
    return build_default_formal_source_retriever(
        additional_providers=(external,),
        local_retriever=local_retriever,
    )


def _proof_search_provider_from_runtime_args(
    args: argparse.Namespace,
    *,
    generator_backend: Any,
    model: str,
    out_dir: Path,
):
    if not bool(getattr(args, "openprover_hlm", False)):
        return None
    root_value = str(getattr(args, "openprover_root", "") or "").strip()
    if not root_value:
        raise ValueError("--openprover-hlm requires --openprover-root")
    root = Path(root_value).expanduser().resolve()
    controller = root / "src" / "openprover" / "controller.py"
    if not controller.is_file():
        raise ValueError(
            "--openprover-root must contain src/openprover/controller.py; "
            f"missing at {controller}"
        )
    lean_project_value = str(
        getattr(args, "formalizer_candidate_lean_project", "")
        or getattr(args, "lean_project", "")
        or getattr(args, "local_lean_project", "")
        or ""
    ).strip()
    if not lean_project_value:
        raise ValueError(
            "--openprover-hlm requires --formalizer-candidate-lean-project or "
            "--lean-project so its candidates are checked in the intended Lake workspace"
        )
    lean_project = Path(lean_project_value).expanduser().resolve()
    if not lean_project.exists():
        raise ValueError(f"OpenProver Lake project does not exist: {lean_project}")
    return OpenProverHLMProofSearchProvider(
        generator_backend=generator_backend,
        config=OpenProverHLMConfig(
            root=root,
            out_dir=out_dir / "openprover_hlm",
            lean_project=lean_project,
            model=str(
                getattr(args, "openprover_hlm_model", "") or model
            ),
            max_tokens=int(
                getattr(args, "openprover_hlm_max_tokens", 1600) or 1600
            ),
            temperature=float(
                getattr(args, "openprover_hlm_temperature", 0.1) or 0.0
            ),
            max_rounds=int(
                getattr(args, "openprover_hlm_rounds", 2) or 2
            ),
            branches_per_round=int(
                getattr(args, "openprover_hlm_branches_per_round", 4) or 4
            ),
            feedback_top_k=int(
                getattr(args, "openprover_hlm_feedback_top_k", 4) or 4
            ),
            max_attempts=int(
                getattr(args, "openprover_hlm_max_attempts", 120) or 120
            ),
            route_strategy=str(
                getattr(args, "openprover_hlm_route_strategy", "hybrid")
                or "hybrid"
            ),
            verifier_timeout_s=int(
                getattr(args, "openprover_hlm_verifier_timeout", 120) or 120
            ),
            require_lake_project=True,
        ),
    )


async def _eval(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    questions = _questions_from_args(args)
    if args.seeds:
        seeds = tuple(int(seed) for seed in args.seeds)
    else:
        seeds = tuple(range(args.seed_start, args.seed_start + args.n_seeds))
    payload = await run_seed_eval(
        questions,
        EvalConfig(seeds=seeds, n_runs=args.runs, use_axle=args.real_lean),
        Path(args.out),
    )
    print("\nAI Statistician Evaluation")
    print("=" * 72)
    for question_id, row in payload["summary"].items():
        print(
            f"{question_id:32} accepted={row['accepted']}/{row['trials']} "
            f"rate={row['acceptance_rate']:.2f} "
            f"mean_coverage95={row['mean_coverage_95']:.3f} "
            f"mean_rmse={row['mean_rmse']:.5f}"
        )
    print(f"\nevaluation manifest written to {(Path(args.out) / 'evaluation_manifest.json').resolve()}")
    return 0


def _theory_intake(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    questions = _questions_from_args(args)
    print("\nAI Statistician Theory Intake")
    print("=" * 72)
    for question in questions:
        print(
            f"{question.id:32} dgp_family={question.dgp_family:10} "
            f"estimator_family={question.estimator_family:20} params={question.true_params}"
        )
        proposal_tags = [tag for tag in question.tags if tag.startswith("theory_proposal:")]
        if proposal_tags:
            print(f"  {proposal_tags[0]}")
    return 0


async def _proof_audit(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    verifier = _proof_verifier_from_args(args)
    payload = await audit_proof_bank(
        verifier,
        Path(args.out),
        ids=args.id,
        tags=args.tag,
        require_all_tags=args.require_all_tags,
        export_lean=not args.no_export_lean,
        export_attempt_log=not args.no_attempt_log,
        include_negative_controls=args.negative_controls,
    )
    print("\nAI Statistician Proof-Bank Audit")
    print("=" * 72)
    print(
        f"verified={payload['n_verified']}/{payload['n_obligations']} "
        f"kernel={payload['n_kernel_verified']}/{payload['n_obligations']} "
        f"verifier={payload['verifier']} strength={payload['verification_strength']}"
    )
    for check in payload["checks"]:
        badge = "OK" if check["ok"] else "FAIL"
        print(f"  proof {badge}: {check['obligation_id']} ({check['elapsed_ms']} ms)")
        if check["errors"]:
            print(f"    error: {check['errors'][0][:180]}")
    print(f"\nproof audit manifest written to {(Path(args.out) / 'proof_audit_manifest.json').resolve()}")
    if payload["lean_export_dir"]:
        print(f"Lean exports written to {Path(str(payload['lean_export_dir'])).resolve()}")
    if payload.get("proof_attempt_log"):
        attempt_log = payload["proof_attempt_log"]
        print(f"proof attempts written to {Path(str(attempt_log['attempt_log'])).resolve()}")
    return 0


def _algorithm_audit(args: argparse.Namespace) -> int:
    payload = audit_algorithm_registry(Path(args.out))
    print("\nAI Statistician Algorithm Audit")
    print("=" * 72)
    print(f"passed={payload['n_ok']}/{payload['n_algorithms']}")
    for row in payload["algorithms"]:
        badge = "OK" if row["ok"] else "FAIL"
        print(f"  algorithm {badge}: {row['algorithm_id']} hash={row['implementation_hash'][:12]}")
        if row["errors"]:
            print(f"    error: {row['errors'][0][:180]}")
    print(f"\nalgorithm audit manifest written to {(Path(args.out) / 'algorithm_audit_manifest.json').resolve()}")
    return 0


def _proof_training_export(args: argparse.Namespace) -> int:
    payload = export_proof_training_dataset(
        Path(args.attempt_log),
        Path(args.out),
        validation_fraction=args.validation_fraction,
    )
    print("\nAI Statistician Proof Training Export")
    print("=" * 72)
    print(
        f"examples={payload['n_sft_examples']} train={payload['n_train']} "
        f"validation={payload['n_validation']} source_attempts={payload['n_attempts']}"
    )
    print(f"train_jsonl={Path(str(payload['train_jsonl'])).resolve()}")
    print(f"validation_jsonl={Path(str(payload['validation_jsonl'])).resolve()}")
    print(f"manifest written to {(Path(args.out) / 'proof_training_manifest.json').resolve()}")
    return 0



def _proof_policy_baseline(args: argparse.Namespace) -> int:
    payload = evaluate_retrieval_proof_policy_baseline(
        Path(args.train_jsonl),
        Path(args.validation_jsonl),
        Path(args.out),
        k=args.k,
    )
    print("\nAI Statistician Proof Policy Baseline")
    print("=" * 72)
    print(
        f"validation={payload['n_validation']} train={payload['n_train']} "
        f"top1_exact={payload['top1_exact']}/{payload['n_validation']} "
        f"top{payload['k']}_exact={payload['top_k_exact']}/{payload['n_validation']}"
    )
    print(
        f"context_hits={payload['predicted_in_retrieved_context']}/{payload['n_validation']} "
        f"mean_score={payload['mean_top1_score']:.3f}"
    )
    print(f"predictions={Path(str(payload['predictions_jsonl'])).resolve()}")
    print(f"manifest written to {(Path(args.out) / 'proof_policy_baseline_manifest.json').resolve()}")
    return 0


def _proof_policy_train(args: argparse.Namespace) -> int:
    payload = train_proof_policy_model(
        Path(args.train_jsonl),
        Path(args.out),
        validation_jsonl=Path(args.validation_jsonl) if args.validation_jsonl else None,
        k=args.k,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        l2=args.l2,
        negatives_per_query=args.negatives_per_query,
    )
    print("\nAI Statistician Proof Policy Model")
    print("=" * 72)
    print(
        f"train={payload['n_train']} validation={payload['n_validation']} "
        f"train_top1={payload['train_top1_exact']}/{payload['n_train']} "
        f"validation_top{payload['k']}={payload['validation_top_k_exact']}/{payload['n_validation']}"
    )
    print(f"model={Path(str(payload['model_json'])).resolve()}")
    print(f"manifest written to {(Path(args.out) / 'proof_policy_model_manifest.json').resolve()}")
    return 0


async def _proof_search_audit(args: argparse.Namespace) -> int:
    verifier = _proof_verifier_from_args(args)
    payload = await audit_proof_search_controller(
        Path(args.out),
        verifier=verifier,
        max_obligations=args.max_obligations,
        max_nodes=args.max_nodes,
        include_invalid_probe=args.include_invalid_probe,
        include_registered_proof=not args.no_registered_proof,
        proof_policy_model_json=Path(args.policy_model_json) if args.policy_model_json else None,
        proof_value_model_json=Path(args.value_model_json) if args.value_model_json else None,
        legacy_static_template_baseline=args.legacy_static_template_baseline,
    )
    print("\nAI Statistician Proof Search Audit")
    print("=" * 72)
    print(
        f"solved={payload['n_solved']}/{payload['n_obligations']} "
        f"kernel_verified={payload['n_kernel_verified']} "
        f"mean_nodes={payload['mean_nodes_expanded']:.2f} "
        f"policy_model={'on' if payload['policy_model_enabled'] else 'off'} "
        f"value_model={'on' if payload['value_model_enabled'] else 'off'} "
        f"registered={payload['include_registered_proof']}"
    )
    print(f"results={Path(str(payload['results_jsonl'])).resolve()}")
    print(f"manifest written to {(Path(args.out) / 'proof_search_audit_manifest.json').resolve()}")
    return 0


def _proof_search_kernel_rerun_queue(args: argparse.Namespace) -> int:
    payload = export_proof_search_kernel_rerun_queue(
        Path(args.proof_search_audit_dir),
        Path(args.out),
        local_lean_project=args.local_lean_project,
        local_lean_timeout=args.local_lean_timeout,
        max_rows=args.max_rows,
    )
    print("\nAI Statistician Proof Search Kernel Rerun Queue")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_queue_rows']} "
        f"ready={payload['n_ready_for_local_lean_or_axle']} "
        f"blocked={payload['n_blocked_missing_selected_proof_body']} "
        f"source_kernel={payload['n_source_kernel_verified']} "
        f"all_ok={payload['all_ok']}"
    )
    print(f"rerun command: {payload['batch_local_lean_rerun_command']}")
    print(
        f"manifest written to "
        f"{(Path(args.out) / 'proof_search_kernel_rerun_queue_manifest.json').resolve()}"
    )
    print(f"jsonl written to {(Path(args.out) / 'proof_search_kernel_rerun_queue.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'proof_search_kernel_rerun_queue.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _proof_search_training_export(args: argparse.Namespace) -> int:
    payload = export_proof_search_process_dataset(
        Path(args.results_jsonl),
        Path(args.out),
        validation_fraction=args.validation_fraction,
    )
    print("\nAI Statistician Proof Search Process Export")
    print("=" * 72)
    print(
        f"examples={payload['n_process_examples']} "
        f"positive={payload['n_positive']} negative={payload['n_negative']} "
        f"train={payload['n_train']} validation={payload['n_validation']}"
    )
    print(f"train_jsonl={Path(str(payload['train_jsonl'])).resolve()}")
    print(f"validation_jsonl={Path(str(payload['validation_jsonl'])).resolve()}")
    print(f"manifest written to {(Path(args.out) / 'proof_search_training_manifest.json').resolve()}")
    return 0


def _proof_search_value_train(args: argparse.Namespace) -> int:
    payload = train_proof_search_value_model(
        Path(args.train_jsonl),
        Path(args.out),
        validation_jsonl=Path(args.validation_jsonl) if args.validation_jsonl else None,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        l2=args.l2,
    )
    print("\nAI Statistician Proof Search Value Model")
    print("=" * 72)
    print(
        f"train={payload['n_train']} validation={payload['n_validation']} "
        f"train_acc={payload['train_accuracy']:.3f} "
        f"val_acc={payload['validation_accuracy']:.3f}"
    )
    print(f"model={Path(str(payload['model_json'])).resolve()}")
    print(f"manifest written to {(Path(args.out) / 'proof_search_value_model_manifest.json').resolve()}")
    return 0


def _research_algorithm_audit(args: argparse.Namespace) -> int:
    payload = audit_research_algorithm_registry(Path(args.out))
    print("\nAI Statistical Theory Lab Algorithm Audit")
    print("=" * 72)
    print(f"passed={payload['n_ok']}/{payload['n_algorithms']}")
    for row in payload["algorithms"]:
        badge = "OK" if row["ok"] else "FAIL"
        print(f"  algorithm {badge}: {row['algorithm_id']} hash={row['implementation_hash'][:12]}")
        for error in row["errors"]:
            print(f"    error: {error[:180]}")
    print(
        f"\nresearch algorithm audit manifest written to "
        f"{(Path(args.out) / 'research_algorithm_audit_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _research_intake_audit(args: argparse.Namespace) -> int:
    supported_files = tuple(Path(path) for path in args.supported_file) if args.supported_file else None
    unsupported_files = tuple(Path(path) for path in args.unsupported_file) if args.unsupported_file else None
    payload = audit_research_question_intake(
        Path(args.out),
        supported_files=supported_files,
        unsupported_files=unsupported_files,
    )
    print("\nAI Statistical Theory Lab Intake Audit")
    print("=" * 72)
    print(
        f"supported={payload['n_supported_accepted']}/{payload['n_supported']} "
        f"unsupported_rejected={payload['n_unsupported_rejected']}/{payload['n_unsupported']} "
        f"all_ok={payload['all_ok']}"
    )
    for row in payload["rows"]:
        badge = "OK" if row["ok"] else "FAIL"
        print(
            f"  {badge:4} {row['question_id']} expected={row['expected']} "
            f"class={row['problem_class']}"
        )
        if row["error"]:
            print(f"       {row['error'][:180]}")
    print(
        f"\nresearch intake audit manifest written to "
        f"{(Path(args.out) / 'research_intake_audit_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _frontier_coverage_audit(args: argparse.Namespace) -> int:
    payload = audit_frontier_coverage(Path(args.out), benchmark_file=Path(args.benchmark_file))
    print("\nAI Statistical Theory Lab Frontier Coverage Audit")
    print("=" * 72)
    print(
        f"parsed={payload['n_questions']} supported={payload['n_supported']} "
        f"unsupported={payload['n_unsupported']} rate={payload['supported_rate']:.2f} "
        f"all_ok={payload['all_ok']}"
    )
    for problem_class, count in payload["by_problem_class"].items():
        print(f"  {problem_class}: {count}")
    print(
        f"\nfrontier coverage manifest written to "
        f"{(Path(args.out) / 'frontier_coverage_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'frontier_coverage.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _frontier_precision_audit(args: argparse.Namespace) -> int:
    payload = audit_frontier_precision(Path(args.out), benchmark_file=Path(args.benchmark_file))
    print("\nAI Statistical Theory Lab Frontier Precision Audit")
    print("=" * 72)
    print(
        f"supported={payload['n_supported']} body_evidence_ok={payload['n_ok']} "
        f"flagged={payload['n_flagged']} all_ok={payload['all_ok']}"
    )
    for row in payload["rows"]:
        evidence = ", ".join(row["evidence_terms"]) or row["reason"]
        print(f"  {row['ok']}: {row['question_id']} class={row['problem_class']} evidence={evidence}")
    print(f"\nfrontier precision manifest written to {(Path(args.out) / 'frontier_precision_manifest.json').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'frontier_precision.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _frontier_backlog_audit(args: argparse.Namespace) -> int:
    payload = audit_frontier_backlog(Path(args.out), benchmark_file=Path(args.benchmark_file))
    print("\nAI Statistical Theory Lab Frontier Backlog Audit")
    print("=" * 72)
    print(
        f"backlog={payload['n_ok']}/{payload['n_backlog']} "
        f"domains={len(payload['by_domain'])} all_ok={payload['all_ok']}"
    )
    for domain, count in payload["by_domain"].items():
        print(f"  {domain}: {count}")
    print(f"\nfrontier backlog manifest written to {(Path(args.out) / 'frontier_backlog_manifest.json').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'frontier_backlog.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _frontier_theory_target_audit(args: argparse.Namespace) -> int:
    payload = audit_frontier_theory_targets(
        Path(args.run_dir),
        Path(args.out),
        benchmark_file=Path(args.benchmark_file),
        coverage_threshold=args.coverage_threshold,
    )
    print("\nAI Statistical Theory Lab Frontier Theory Target Audit")
    print("=" * 72)
    print(
        f"scored={payload['n_scored']}/{payload['n_traces']} "
        f"covered={payload['n_covered_results']}/{payload['n_expected_results']} "
        f"rate={payload['expected_result_coverage_rate']:.2f} "
        f"all_scored={payload['all_scored']}"
    )
    for row in payload["rows"]:
        print(
            f"  {row['question_id']}: class={row['problem_class']} "
            f"covered={row['n_covered_results']}/{row['n_expected_results']} "
            f"mean={row['mean_expected_result_coverage']:.2f}"
        )
    print(
        f"\nfrontier theory target manifest written to "
        f"{(Path(args.out) / 'frontier_theory_target_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'frontier_theory_target.md').resolve()}")
    return 0 if payload["all_scored"] else 1


def _frontier_discover_and_prove_prompt_packets(args: argparse.Namespace) -> int:
    payload = export_frontier_discover_and_prove_prompt_packets(
        Path(args.out),
        benchmark_file=Path(args.benchmark_file),
        max_packets=args.max_packets,
    )
    print("\nAI Statistical Theory Lab Frontier Discover-and-Prove Prompt Packets")
    print("=" * 72)
    print(
        f"packets={payload['n_prompt_packets']} "
        f"contracts={payload['n_output_contracts']} "
        f"expected_leaks={payload['n_prompt_expected_result_leaks']} "
        f"source_leaks={payload['n_prompt_source_identity_leaks']} "
        f"status={payload['proof_evidence_status']}"
    )
    print(
        f"\nfrontier DAP prompt manifest written to "
        f"{(Path(args.out) / 'frontier_discover_and_prove_prompt_packets_manifest.json').resolve()}"
    )
    print(
        f"jsonl written to "
        f"{(Path(args.out) / 'frontier_discover_and_prove_prompt_packets.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'frontier_discover_and_prove_prompt_packets.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _paper_theory_roundtrip(args: argparse.Namespace) -> int:
    payload = export_paper_theory_roundtrip(
        Path(args.paper_root),
        Path(args.out),
        paper_id=args.paper_id or None,
        max_statements=args.max_statements,
    )
    print("\nAI Statistical Theory Lab Paper Theory Round-Trip")
    print("=" * 72)
    print(
        f"tex_files={payload['n_tex_files']} statements={payload['n_statements']} "
        f"lean_queue={payload['n_lean_candidate_queue_rows']} "
        f"roundtrip={payload['n_roundtrip_review_rows']} "
        f"status={payload['proof_evidence_status']}"
    )
    print(
        f"\npaper theory manifest written to "
        f"{(Path(args.out) / 'paper_theory_roundtrip_manifest.json').resolve()}"
    )
    print(
        f"statement catalog written to "
        f"{(Path(args.out) / 'paper_statement_catalog.jsonl').resolve()}"
    )
    print(
        f"Lean candidate queue written to "
        f"{(Path(args.out) / 'statement_to_lean_candidate_queue.jsonl').resolve()}"
    )
    print(
        f"round-trip review queue written to "
        f"{(Path(args.out) / 'lean_to_latex_roundtrip_review_queue.jsonl').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _frontier_evaluation_triage(args: argparse.Namespace) -> int:
    payload = audit_frontier_evaluation_triage(
        Path(args.run_dir),
        Path(args.theory_target_manifest),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Frontier Evaluation Triage")
    print("=" * 72)
    print(
        f"items={payload['n_ok']}/{payload['n_items']} "
        f"theory_misses={payload['n_theory_target_misses']} "
        f"simulation_flags={payload['n_simulation_flags']} "
        f"all_ok={payload['all_ok']}"
    )
    for owner, count in payload["by_owner"].items():
        print(f"  {owner}: {count}")
    print(
        f"\nfrontier evaluation triage manifest written to "
        f"{(Path(args.out) / 'frontier_evaluation_triage_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'frontier_evaluation_triage.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _frontier_simulation_rerun_audit(args: argparse.Namespace) -> int:
    payload = audit_frontier_simulation_reruns(
        Path(args.triage_manifest),
        Path(args.out),
        n_runs=args.runs,
        seed=args.seed,
    )
    print("\nAI Statistical Theory Lab Frontier Simulation Rerun Audit")
    print("=" * 72)
    print(
        f"items={payload['n_ok']}/{payload['n_items']} "
        f"resolved={payload['n_resolved']} "
        f"still_flagged={payload['n_still_flagged']} "
        f"all_ok={payload['all_ok']}"
    )
    for owner, count in payload["by_new_owner_agent"].items():
        print(f"  {owner}: {count}")
    print(
        f"\nfrontier simulation rerun manifest written to "
        f"{(Path(args.out) / 'frontier_simulation_rerun_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'frontier_simulation_rerun.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _frontier_theory_revision_queue(args: argparse.Namespace) -> int:
    payload = export_frontier_theory_revision_queue(
        Path(args.simulation_rerun_manifest),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Frontier Theory Revision Queue")
    print("=" * 72)
    print(
        f"tasks={payload['n_ok']}/{payload['n_tasks']} "
        f"all_ok={payload['all_ok']}"
    )
    for failure_class, count in payload["by_failure_class"].items():
        print(f"  {failure_class}: {count}")
    print(
        f"\nfrontier theory revision queue manifest written to "
        f"{(Path(args.out) / 'frontier_theory_revision_queue_manifest.json').resolve()}"
    )
    print(f"jsonl written to {(Path(args.out) / 'frontier_theory_revision_queue.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'frontier_theory_revision_queue.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _frontier_theory_revision_formalization_audit(args: argparse.Namespace) -> int:
    source_index = Path(args.formal_source_index) if args.formal_source_index else Path(args.out) / "formal_source_index.sqlite"
    payload = audit_frontier_theory_revision_formalization(
        Path(args.revision_queue_manifest),
        Path(args.out),
        formal_source_index_path=source_index,
        k=args.k,
    )
    print("\nAI Statistical Theory Lab Frontier Theory Revision Formalization Audit")
    print("=" * 72)
    print(
        f"obligations={payload['n_ok']}/{payload['n_obligations']} "
        f"unique={payload['n_unique_obligations']} "
        f"proof_bank_bridge={payload['n_unique_proof_bank_bridge']} "
        f"local_source_only={payload['n_unique_local_source_only']} "
        f"source_gap={payload['n_unique_source_gap']} "
        f"all_ok={payload['all_ok']}"
    )
    for classification, count in payload["by_unique_classification"].items():
        print(f"  {classification}: {count}")
    print(
        f"\nfrontier theory revision formalization manifest written to "
        f"{(Path(args.out) / 'frontier_theory_revision_formalization_manifest.json').resolve()}"
    )
    print(
        f"jsonl written to "
        f"{(Path(args.out) / 'frontier_theory_revision_formalization_tasks.jsonl').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'frontier_theory_revision_formalization.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _research_knowledge_audit(args: argparse.Namespace) -> int:
    payload = audit_research_knowledge(Path(args.out), question_file=Path(args.question_file))
    print("\nAI Statistical Theory Lab Knowledge Audit")
    print("=" * 72)
    print(
        f"sources={payload['n_source_ok']}/{payload['n_cards']} "
        f"inventory={payload['source_inventory']['n_ok']}/{payload['source_inventory']['n_sources']} "
        f"problem_retrieval={payload['n_problem_ok']}/{payload['n_problem_rows']} "
        f"all_ok={payload['all_ok']}"
    )
    for row in payload["problem_rows"]:
        print(
            f"  {row['question_id']}: class={row['problem_class']} "
            f"primary={row['expected_primary']} top={row['top_hit']} "
            f"formal_infra={row['has_formal_infra']}"
        )
    print(
        f"\nresearch knowledge manifest written to "
        f"{(Path(args.out) / 'research_knowledge_audit_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'research_knowledge_audit.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _lean_blueprint_knowledge(args: argparse.Namespace) -> int:
    payload = export_lean_blueprint_knowledge(
        Path(args.out),
        blueprint_root=Path(args.blueprint_root) if args.blueprint_root else None,
    )
    graph = payload["knowledge_graph"]
    source = payload["source"]
    print("\nAI Statistical Theory Lab LeanBlueprint Knowledge")
    print("=" * 72)
    print(
        f"available={source.get('exists')} all_ok={payload['all_ok']} "
        f"commit={str(source.get('git_commit', ''))[:12]} root={source.get('root')}"
    )
    print(
        f"macros={len(payload['macros'])} statuses={len(payload['statuses'])} "
        f"graph={graph.get('n_nodes')} nodes/{graph.get('n_edges')} edges"
    )
    print(
        f"\nLeanBlueprint manifest written to "
        f"{(Path(args.out) / 'lean_blueprint_knowledge_manifest.json').resolve()}"
    )
    print(f"graph written to {(Path(args.out) / 'lean_blueprint_knowledge_graph.json').resolve()}")
    print(
        f"adapter plan written to "
        f"{(Path(args.out) / 'lean_blueprint_visualization_adapter_plan.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


async def _frontier_smoke_benchmark(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    verifier = _proof_verifier_from_args(args)
    payload = await run_frontier_smoke_benchmark(
        Path(args.out),
        benchmark_file=Path(args.benchmark_file),
        config=FrontierSmokeConfig(
            n_runs=args.runs,
            seed=args.seed,
            max_per_class=args.max_per_class,
            use_axle=args.real_lean,
            cache_dir=args.frontier_smoke_cache or None,
            refresh_cache=args.refresh_frontier_smoke_cache,
            simulation_rerun_runs=args.simulation_rerun_runs,
        ),
        proof_verifier=verifier,
    )
    print("\nAI Statistical Theory Lab Frontier Smoke Benchmark")
    print("=" * 72)
    print(
        f"selected={payload['n_selected']} ready={payload['counts']['ready_with_gaps']}/{payload['counts']['questions']} "
        f"triage={payload['counts']['frontier_triage_items']} "
        f"rerun_resolved={payload['counts']['frontier_simulation_rerun_resolved']} "
        f"theory_revisions={payload['counts']['frontier_theory_revision_tasks']} "
        f"formalized_revision_obligations={payload['counts']['frontier_theory_revision_formal_obligations']} "
        f"all_gates_passed={payload['all_gates_passed']} "
        f"cache={payload['counts']['frontier_smoke_cache_status']}"
    )
    for row in payload["selections"]:
        print(f"  {row['question_id']}: class={row['problem_class']} topic={row['topic']}")
    print(f"\nfrontier smoke manifest written to {(Path(args.out) / 'frontier_smoke_manifest.json').resolve()}")
    return 0 if payload["all_gates_passed"] else 1


def _retrieval_audit(args: argparse.Namespace) -> int:
    payload = audit_proof_bank_retrieval(
        Path(args.out),
        k=args.k,
        include_loogle=args.loogle,
        loogle_k=args.loogle_k,
        loogle_timeout_s=args.loogle_timeout,
    )
    print("\nAI Statistician Retrieval Audit")
    print("=" * 72)
    print(
        f"top1={payload['top1']}/{payload['n_obligations']} "
        f"top{payload['k']}={payload['top_k']}/{payload['n_obligations']} "
        f"mrr={payload['mrr']:.3f}"
    )
    for row in payload["rows"]:
        top1 = row["top1"] or "none"
        print(f"  {row['obligation_id']}: rank={row['rank']} top1={top1}")
    if payload["loogle"]["enabled"]:
        loogle = payload["loogle"]
        print(
            f"\nloogle evidence: expected_lemma_hits="
            f"{loogle['n_expected_lemma_hits']}/{loogle['n_queries']} "
            f"errors={loogle['n_errors']}"
        )
        for row in loogle["rows"][:5]:
            status = "HIT" if row["expected_lemma_hit"] else "MISS"
            first = row["hits"][0] if row["hits"] else (row["error"] or "none")
            print(f"  loogle {status}: {row['obligation_id']} first={first}")
    print(f"\nretrieval audit manifest written to {(Path(args.out) / 'retrieval_audit_manifest.json').resolve()}")
    return 0


def _formal_source_audit(args: argparse.Namespace) -> int:
    payload = audit_formal_source_index(Path(args.out), k=args.k, backend=args.backend)
    print("\nAI Statistical Theory Lab Formal Source Index")
    print("=" * 72)
    print(
        f"sources={payload['n_sources']} declarations={payload['n_declarations']} "
        f"queries={payload['n_query_ok']}/{payload['n_queries']} backend={payload['search_backend']}"
    )
    for row in payload["query_rows"]:
        first = row["top_hits"][0] if row["top_hits"] else None
        first_name = first["name"] if first else "none"
        first_source = first["source_id"] if first else "none"
        print(f"  {row['query_id']}: ok={row['ok']} top={first_name} source={first_source}")
    print(
        f"\nformal source index manifest written to "
        f"{(Path(args.out) / 'formal_source_index_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'formal_source_index.md').resolve()}")
    if payload.get("sqlite_index_path"):
        print(f"sqlite index written to {Path(str(payload['sqlite_index_path'])).resolve()}")
    return 0 if payload["all_queries_ok"] else 1


def _formal_source_graph_audit(args: argparse.Namespace) -> int:
    payload = audit_formal_source_graph(
        Path(args.out),
        k=args.k,
        cache_path=Path(args.formal_source_graph_cache) if args.formal_source_graph_cache else None,
        refresh_cache=args.refresh_formal_source_graph_cache,
    )
    print("\nAI Statistical Theory Lab Formal Source Graph")
    print("=" * 72)
    print(
        f"declarations={payload['n_declarations']} "
        f"symbols={payload['n_symbol_nodes']} edges={payload['n_edges']} "
        f"queries={payload['n_query_ok']}/{payload['n_queries']} "
        f"cache={payload['cache']['status']}"
    )
    for row in payload["query_rows"]:
        first = row["top_hits"][0] if row["top_hits"] else None
        first_name = first["name"] if first else "none"
        first_source = first["source_id"] if first else "none"
        print(f"  {row['query_id']}: ok={row['ok']} top={first_name} source={first_source}")
    print(
        f"\nformal source graph manifest written to "
        f"{(Path(args.out) / 'formal_source_graph_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'formal_source_graph.md').resolve()}")
    return 0 if payload["all_queries_ok"] else 1


def _lean_rag_package_audit(args: argparse.Namespace) -> int:
    payload = audit_lean_rag_package(
        Path(args.out),
        package_root=Path(args.package_root) if args.package_root else None,
        db_dir=Path(args.db_dir) if args.db_dir else None,
    )
    registry = payload["source_registry"]
    seeds = payload["seed_queries"]
    coverage = payload["target_source_coverage"]
    graph = payload["shared_graph_manifest"]
    print("\nAI Statistical Theory Lab Lean RAG Package Audit")
    print("=" * 72)
    print(
        f"available={payload['available']} contract_ok={payload['contract_ok']} "
        f"package_root={payload['package_root']}"
    )
    print(
        f"sources=local:{registry.get('n_local_sources', 0)} "
        f"external:{registry.get('n_external_sources', 0)} "
        f"seed_queries={seeds.get('n_queries', 0)} lanes={','.join(seeds.get('lanes', [])) or 'none'}"
    )
    missing_targets = ",".join(coverage.get("missing_target_ids", [])) or "none"
    print(
        f"target_sources={coverage.get('n_present', 0)}/{coverage.get('n_targets', 0)} "
        f"coverage_ok={coverage.get('coverage_ok', False)} "
        f"registry_candidates={coverage.get('n_registry_expansion_candidates', 0)} "
        f"missing={missing_targets}"
    )
    print(
        f"shared_graph_manifest={graph.get('available')} "
        f"indexed_checkouts={graph.get('n_indexed_checkouts', 0)} "
        f"dirty_checkouts={graph.get('n_dirty_checkouts', 0)} "
        f"failed_checkouts={graph.get('n_failed_checkouts', 0)}"
    )
    print(
        f"\nlean RAG package audit manifest written to "
        f"{(Path(args.out) / 'lean_rag_package_audit_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'lean_rag_package_audit.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _lean_rag_source_registry_expansion(args: argparse.Namespace) -> int:
    payload = stage_lean_rag_source_registry_expansion(
        Path(args.out),
        package_root=Path(args.package_root) if args.package_root else None,
        db_dir=Path(args.db_dir) if args.db_dir else None,
    )
    before = payload["target_source_coverage_before"]
    after = payload["target_source_coverage_after"]
    print("\nAI Statistical Theory Lab Lean RAG Source Registry Expansion")
    print("=" * 72)
    print(
        f"package_contract_ok={payload['package_contract_ok']} "
        f"stage_ready={payload['stage_ready']} package_root={payload['package_root']}"
    )
    print(
        f"coverage={before.get('n_present', 0)}/{before.get('n_targets', 0)} -> "
        f"{after.get('n_present', 0)}/{after.get('n_targets', 0)} "
        f"candidates={payload['n_candidates']} staged={payload['n_staged']} "
        f"already_present={payload['n_already_present']} invalid={payload['n_invalid']}"
    )
    print(f"clone_commands={len(payload.get('clone_commands', []))}")
    print(
        f"\nsource registry expansion manifest written to "
        f"{(Path(args.out) / 'source_registry_expansion_manifest.json').resolve()}"
    )
    print(f"staged source registry written to {(Path(args.out) / 'staged_source_registry.json').resolve()}")
    return 0 if payload["all_ok"] else 1


def _lean_rag_source_registry_expansion_preflight(args: argparse.Namespace) -> int:
    payload = preflight_lean_rag_source_registry_expansion(
        Path(args.out),
        expansion_manifest=Path(args.expansion_manifest),
    )
    print("\nAI Statistical Theory Lab Lean RAG Source Registry Expansion Preflight")
    print("=" * 72)
    print(
        f"package_clean={payload['package_clean']} "
        f"apply_ready={payload['source_registry_apply_ready']} "
        f"no_staged={payload.get('no_staged', False)} "
        f"external_refresh_ready={payload['external_refresh_ready']}"
    )
    print(
        f"rows={payload['n_rows']} clone_required={payload['n_clone_required']} "
        f"present_clean_git={payload['n_present_clean_git']} "
        f"present_local_path={payload['n_present_local_path']} "
        f"indexer_unsupported={payload['n_indexer_unsupported']} "
        f"hard_blockers={payload['n_hard_blockers']}"
    )
    print(
        f"\nsource registry expansion preflight manifest written to "
        f"{(Path(args.out) / 'source_registry_expansion_preflight_manifest.json').resolve()}"
    )
    return 0 if payload["source_registry_apply_ready"] or payload.get("no_staged", False) else 1


def _lean_rag_source_registry_expansion_apply(args: argparse.Namespace) -> int:
    payload = apply_lean_rag_source_registry_expansion(
        Path(args.out),
        expansion_manifest=Path(args.expansion_manifest),
        preflight_manifest=Path(args.preflight_manifest)
        if args.preflight_manifest
        else None,
        dry_run=not args.apply,
    )
    before = dict(payload.get("target_source_coverage_before", {}) or {})
    after = dict(payload.get("target_source_coverage_after", {}) or {})
    print("\nAI Statistical Theory Lab Lean RAG Source Registry Expansion Apply")
    print("=" * 72)
    print(
        f"dry_run={payload['dry_run']} apply_ready={payload['apply_ready']} "
        f"applied={payload['applied']} no_staged={payload.get('no_staged', False)}"
    )
    print(
        f"coverage={before.get('n_present', 0)}/{before.get('n_targets', 0)} -> "
        f"{after.get('n_present', 0)}/{after.get('n_targets', 0)} "
        f"staged={payload['n_staged']}"
    )
    if payload["errors"]:
        print("errors=" + "; ".join(str(error) for error in payload["errors"]))
    if payload["warnings"]:
        print("warnings=" + "; ".join(str(warning) for warning in payload["warnings"]))
    print(
        f"\nsource registry expansion apply manifest written to "
        f"{(Path(args.out) / 'source_registry_expansion_apply_manifest.json').resolve()}"
    )
    return 0 if payload["apply_ready"] and (
        payload["dry_run"] or payload["applied"] or payload.get("no_staged", False)
    ) else 1


def _huggingface_lean_source_audit(args: argparse.Namespace) -> int:
    payload = audit_huggingface_lean_sources(
        Path(args.out),
        max_results_per_query=args.max_results_per_query,
        max_detail_fetches=args.max_detail_fetches,
        timeout_s=args.timeout,
        use_network=not args.no_network,
    )
    summary = payload["summary"]
    print("\nAI Statistical Theory Lab Hugging Face Lean Source Audit")
    print("=" * 72)
    print(
        f"candidates={summary.get('n_candidates', 0)} "
        f"critical={summary.get('n_critical', 0)} high={summary.get('n_high', 0)} "
        f"public_ungated={summary.get('n_public_ungated', 0)}"
    )
    print(
        f"oproofs_detected={summary.get('oproofs_detected', False)} "
        f"oproofs_rows={summary.get('oproofs_reported_rows', 0)} "
        f"oproofs_shards={summary.get('oproofs_parquet_shards', 0)} "
        f"proof_evidence_ready={summary.get('proof_evidence_ready', 0)}"
    )
    queue_summary = payload.get("revalidation_queue_summary", {})
    print(
        f"revalidation_queue={queue_summary.get('n_queue_rows', 0)} "
        f"ready={queue_summary.get('n_ready', 0)} "
        f"kernel_verified={queue_summary.get('n_kernel_verified', 0)} "
        f"status={queue_summary.get('proof_evidence_status', '')}"
    )
    for row in payload["rows"][:10]:
        print(
            f"  {row['priority']:8} {row['dataset_id']:48} "
            f"class={row['relevance_class']} rows={row['num_rows']}"
        )
    print(
        f"\nhuggingface Lean source audit manifest written to "
        f"{(Path(args.out) / 'huggingface_lean_source_audit_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'huggingface_lean_source_audit.md').resolve()}")
    return 0 if summary.get("oproofs_detected") else 1


def _huggingface_lean_source_revalidation_tasks(args: argparse.Namespace) -> int:
    payload = export_huggingface_lean_source_revalidation_tasks(
        Path(args.queue_jsonl),
        Path(args.out),
        max_tasks=args.max_tasks,
        sample_seed=args.sample_seed,
    )
    print("\nAI Statistical Theory Lab Hugging Face Lean Source Revalidation Tasks")
    print("=" * 72)
    print(
        f"tasks={payload['n_tasks']} ready={payload['n_ready']} "
        f"blocked={payload['n_blocked']} "
        f"license_review={payload['n_license_review_required']}"
    )
    print(
        f"kernel_verified={payload['n_kernel_verified']} "
        f"proof_evidence_ready={payload['n_proof_evidence_ready']} "
        f"status={payload['proof_evidence_status']}"
    )
    print(
        f"\nhf Lean source revalidation task manifest written to "
        f"{(Path(args.out) / 'hf_lean_source_revalidation_tasks_manifest.json').resolve()}"
    )
    print(
        f"task queue written to "
        f"{(Path(args.out) / 'hf_lean_source_revalidation_tasks.jsonl').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _huggingface_lean_source_revalidation_prompt_packets(args: argparse.Namespace) -> int:
    payload = export_huggingface_lean_source_revalidation_prompt_packets(
        Path(args.task_dir),
        Path(args.out),
        max_packets=args.max_packets,
    )
    print("\nAI Statistical Theory Lab Hugging Face Lean Source Revalidation Prompt Packets")
    print("=" * 72)
    print(
        f"tasks={payload['n_tasks']} ready={payload['n_ready_tasks']} "
        f"prompt_packets={payload['n_prompt_packets']} "
        f"license_review={payload['n_license_review_required']}"
    )
    print(
        f"output_contracts={payload['n_with_output_contract']} "
        f"status={payload['proof_evidence_status']}"
    )
    print(
        f"\nhf Lean source revalidation prompt packet manifest written to "
        f"{(Path(args.out) / 'hf_lean_source_revalidation_prompt_packets_manifest.json').resolve()}"
    )
    print(
        f"prompt packet queue written to "
        f"{(Path(args.out) / 'hf_lean_source_revalidation_prompt_packets.jsonl').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _huggingface_lean_source_revalidation_artifact_validation(args: argparse.Namespace) -> int:
    payload = export_huggingface_lean_source_revalidation_artifact_validation(
        Path(args.task_dir),
        Path(args.out),
        response_jsonl=Path(args.response_jsonl) if args.response_jsonl else None,
    )
    print("\nAI Statistical Theory Lab Hugging Face Lean Source Revalidation Artifact Validation")
    print("=" * 72)
    print(
        f"tasks={payload['n_tasks']} responses={payload['n_responses']} "
        f"awaiting={payload['n_awaiting_worker_output']} "
        f"contract_ok={payload['n_contract_ok']}"
    )
    print(
        f"kernel_verified_rows={payload['n_kernel_verified_rows']} "
        f"proof_evidence_ready={payload['n_proof_evidence_ready']} "
        f"status={payload['proof_evidence_status']}"
    )
    print(
        f"\nhf Lean source revalidation artifact validation manifest written to "
        f"{(Path(args.out) / 'hf_lean_source_revalidation_artifact_validation_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _huggingface_lean_source_revalidation_promotion_queue(args: argparse.Namespace) -> int:
    payload = export_huggingface_lean_source_revalidation_promotion_queue(
        Path(args.artifact_validation_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Hugging Face Lean Source Revalidation Promotion Queue")
    print("=" * 72)
    print(
        f"rows={payload['n_promotion_rows']} ready={payload['n_ready_for_promotion']} "
        f"awaiting={payload['n_awaiting_worker_output']} blocked={payload['n_blocked']}"
    )
    print(
        f"kernel_verified_rows={payload['n_kernel_verified_rows']} "
        f"proof_evidence_ready={payload['n_proof_evidence_ready']} "
        f"status={payload['proof_evidence_status']}"
    )
    print(
        f"\nhf Lean source promotion queue manifest written to "
        f"{(Path(args.out) / 'hf_lean_source_revalidation_promotion_queue_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _lean_rag_dependency_health(args: argparse.Namespace) -> int:
    payload = audit_lean_rag_dependency_health(
        Path(args.out),
        requested_db_path=Path(args.db) if args.db else None,
        active_db_path=Path(args.active_db) if args.active_db else Path(args.db) if args.db else None,
        auto_discovered=args.auto_discovered,
    )
    print("\nAI Statistical Theory Lab Lean RAG Dependency Health")
    print("=" * 72)
    print(
        f"status={payload['health_status']} active={payload['active_enabled']} "
        f"fallback={payload['fallback_used']} reason={payload['fallback_reason']}"
    )
    print(
        f"\nlean RAG dependency health manifest written to "
        f"{(Path(args.out) / 'lean_rag_dependency_health_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'lean_rag_dependency_health.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _formal_source_retrieval_benchmark(args: argparse.Namespace) -> int:
    suites = {
        "default": DEFAULT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK,
        "external": EXTERNAL_USER_INTENT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK,
        "all": ALL_FORMAL_SOURCE_RETRIEVAL_BENCHMARKS,
    }
    retriever = build_formal_source_search_backend(
        db_path=Path(args.formal_source_index),
        cache_path=Path(args.formal_source_index_cache) if args.formal_source_index_cache else None,
        refresh_cache=args.refresh_formal_source_index_cache,
        lean_rag_db_path=Path(args.lean_rag_db) if args.lean_rag_db else None,
    )
    payload = run_formal_source_retrieval_benchmark(
        Path(args.out),
        retriever=retriever,
        cases=suites[args.suite],
        k=args.k,
    )
    print("\nAI Statistical Theory Lab Formal Source Retrieval Benchmark")
    print("=" * 72)
    print(
        f"suite={args.suite} hits={payload['n_ok']}/{payload['n_cases']} "
        f"recall@{payload['k']}={payload['recall_at_k']:.3f} "
        f"mrr={payload['mean_reciprocal_rank']:.3f} "
        f"scoped_context={payload['n_source_scoped_context_ok']}/"
        f"{payload['n_cases']} "
        f"all_ok={payload['all_ok']} "
        f"lean_rag={payload['lean_rag_dependency_graph_enabled']} "
        f"cache={getattr(retriever, 'cache_status', 'unknown')}"
    )
    for row in payload["rows"]:
        print(
            f"  {row['query_id']}: ok={row['ok']} rank={row['hit_rank'] or 'miss'} "
            f"scoped_context_ok={row['source_scoped_context_ok']} "
            f"scoped_rank={row['source_scoped_context_hit_rank'] or 'miss'} "
            f"top={row['top1_name']} source={row['top1_source_id']}"
        )
    print(
        f"\nretrieval benchmark manifest written to "
        f"{(Path(args.out) / 'formal_source_retrieval_benchmark_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'formal_source_retrieval_benchmark.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _formal_source_retrieval_ablation(args: argparse.Namespace) -> int:
    suites = {
        "default": DEFAULT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK,
        "external": EXTERNAL_USER_INTENT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK,
        "all": ALL_FORMAL_SOURCE_RETRIEVAL_BENCHMARKS,
    }
    baseline_retriever, enhanced_retriever = _formal_source_ablation_retrievers(args)
    payload = run_formal_source_retrieval_ablation_benchmark(
        Path(args.out),
        baseline_retriever=baseline_retriever,
        enhanced_retriever=enhanced_retriever,
        cases=suites[args.suite],
        k=args.k,
    )
    print("\nAI Statistical Theory Lab Formal Source Retrieval Ablation")
    print("=" * 72)
    print(
        f"suite={args.suite} cases={payload['n_cases']} "
        f"new_hits={payload['n_new_hits']} lost_hits={payload['n_lost_hits']} "
        f"rank_improved={payload['n_rank_improved']} rank_regressed={payload['n_rank_regressed']} "
        f"dependency_sensitive={payload['n_dependency_sensitive_cases']} "
        f"lean_rag={payload['enhanced']['lean_rag_dependency_graph_enabled']}"
    )
    print(
        f"baseline_recall={payload['baseline']['recall_at_k']:.3f} "
        f"enhanced_recall={payload['enhanced']['recall_at_k']:.3f}"
    )
    print(
        f"\nretrieval ablation manifest written to "
        f"{(Path(args.out) / 'formal_source_retrieval_ablation_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'formal_source_retrieval_ablation.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _proof_search_retrieval_ablation(args: argparse.Namespace) -> int:
    baseline_retriever, enhanced_retriever = _formal_source_ablation_retrievers(args)
    payload = asyncio.run(
        run_proof_search_retrieval_ablation(
            Path(args.out),
            baseline_retriever=baseline_retriever,
            enhanced_retriever=enhanced_retriever,
            verifier=_proof_verifier_from_args(args),
            max_obligations=args.max_obligations,
            max_nodes=args.max_nodes,
            formal_source_k=args.formal_source_k,
            include_registered_proof=not args.no_registered_proof,
        )
    )
    print("\nAI Statistical Theory Lab Proof Search Retrieval Ablation")
    print("=" * 72)
    print(
        f"solved_delta={payload['solved_delta']} "
        f"candidate_delta={payload['formal_source_candidate_delta']} "
        f"node_delta={payload['nodes_expanded_delta']} "
        f"lean_rag={payload['lean_rag_dependency_graph_enabled']} "
        f"dependency_graph_search={payload['dependency_graph_search'] or 'disabled'} "
        f"registered={payload['include_registered_proof']} "
        f"saturated={payload['saturation_warning']}"
    )
    print(
        f"baseline_solved={payload['baseline']['n_solved']}/{payload['baseline']['n_obligations']} "
        f"enhanced_solved={payload['enhanced']['n_solved']}/{payload['enhanced']['n_obligations']}"
    )
    print(
        f"\nproof-search ablation manifest written to "
        f"{(Path(args.out) / 'proof_search_retrieval_ablation_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'proof_search_retrieval_ablation.md').resolve()}")
    return 0 if payload["no_solved_regression"] else 1


def _formal_source_ablation_retrievers(args: argparse.Namespace) -> tuple[object, object]:
    index_path = Path(args.formal_source_index)
    enhanced_retriever = build_formal_source_search_backend(
        db_path=index_path,
        cache_path=Path(args.formal_source_index_cache) if args.formal_source_index_cache else None,
        refresh_cache=args.refresh_formal_source_index_cache,
        lean_rag_db_path=Path(args.lean_rag_db) if args.lean_rag_db else None,
    )
    declarations = (
        enhanced_retriever.load_declarations()
        if hasattr(enhanced_retriever, "load_declarations")
        else []
    )
    baseline_retriever = FormalSourceHybridRetriever(
        declarations,
        FormalSourceSqliteIndex(index_path),
        dependency_retriever=None,
    )
    return baseline_retriever, enhanced_retriever


def _intake_audit(args: argparse.Namespace) -> int:
    supported_files = tuple(Path(path) for path in args.supported_file) if args.supported_file else None
    unsupported_files = tuple(Path(path) for path in args.unsupported_file) if args.unsupported_file else None
    payload = audit_question_intake(
        Path(args.out),
        supported_files=supported_files,
        unsupported_files=unsupported_files,
    )
    print("\nAI Statistician Intake Audit")
    print("=" * 72)
    print(
        f"supported={payload['n_supported_accepted']}/{payload['n_supported']} "
        f"unsupported_rejected={payload['n_unsupported_rejected']}/{payload['n_unsupported']} "
        f"all_ok={payload['all_ok']}"
    )
    for row in payload["rows"]:
        badge = "OK" if row["ok"] else "FAIL"
        print(f"  {badge:4} {row['question_id']} expected={row['expected']}")
        if row["error"]:
            print(f"       {row['error'][:180]}")
    print(f"\nintake audit manifest written to {(Path(args.out) / 'intake_audit_manifest.json').resolve()}")
    return 0 if payload["all_ok"] else 1


def _trace_audit(args: argparse.Namespace) -> int:
    payload = audit_run_traces(Path(args.run_dir), Path(args.out))
    print("\nAI Statistician Trace Audit")
    print("=" * 72)
    print(f"traces={payload['n_ok']}/{payload['n_traces']} all_ok={payload['all_ok']}")
    for error in payload["manifest_errors"]:
        print(f"  manifest error: {error}")
    for row in payload["rows"]:
        badge = "OK" if row["ok"] else "FAIL"
        print(f"  {badge:4} {row['question_id']} {row['trace_path']}")
        for error in row["errors"]:
            print(f"       {error[:180]}")
    print(f"\ntrace audit manifest written to {(Path(args.out) / 'trace_audit_manifest.json').resolve()}")
    return 0 if payload["all_ok"] else 1


def _research_trace_audit(args: argparse.Namespace) -> int:
    payload = audit_research_traces(Path(args.run_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Trace Audit")
    print("=" * 72)
    print(f"traces={payload['n_ok']}/{payload['n_traces']} all_ok={payload['all_ok']}")
    for error in payload["manifest_errors"]:
        print(f"  manifest error: {error}")
    for row in payload["rows"]:
        badge = "OK" if row["ok"] else "FAIL"
        print(f"  {badge:4} {row['question_id']} {row['trace_path']}")
        for error in row["errors"]:
            print(f"       {error[:180]}")
    print(f"\nresearch trace audit manifest written to {(Path(args.out) / 'research_trace_audit_manifest.json').resolve()}")
    return 0 if payload["all_ok"] else 1


def _research_gap_audit(args: argparse.Namespace) -> int:
    payload = audit_research_gap_backlog(Path(args.run_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Formal Gap Backlog")
    print("=" * 72)
    print(
        f"gaps={payload['n_ok']}/{payload['n_gaps']} "
        f"artifacts={payload['n_artifacts_present']}/{payload['n_gaps']} "
        f"all_ok={payload['all_ok']}"
    )
    for error in payload["manifest_errors"]:
        print(f"  manifest error: {error}")
    for row in payload["rows"]:
        badge = "OK" if row["ok"] else "FAIL"
        print(f"  {badge:4} {row['gap_id']} class={row['problem_class']}")
        for error in row["errors"]:
            print(f"       {error[:180]}")
    print(
        f"\nresearch gap backlog written to "
        f"{(Path(args.out) / 'research_gap_backlog_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'research_gap_backlog.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _formalization_target_audit(args: argparse.Namespace) -> int:
    payload = audit_formalization_targets(Path(args.run_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Formalization Target Queue")
    print("=" * 72)
    print(f"targets={payload['n_ok']}/{payload['n_targets']} all_ok={payload['all_ok']}")
    for row in payload["top_targets"][:10]:
        print(
            f"  {row['priority_band']:24} score={row['priority_score']:4} "
            f"{row['primitive']} gaps={row['n_gaps']}"
        )
        print(f"       bridge: {row['bridge_readiness']}")
        print(f"       next: {row['suggested_next_step'][:180]}")
    print(
        f"\nformalization target manifest written to "
        f"{(Path(args.out) / 'formalization_target_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'formalization_targets.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _formal_gap_task_export(args: argparse.Namespace) -> int:
    payload = export_formal_gap_lean_tasks(Path(args.run_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Formal Gap Lean Tasks")
    print("=" * 72)
    print(f"tasks={payload['n_ok']}/{payload['n_tasks']} all_ok={payload['all_ok']}")
    for row in payload["tasks"][:10]:
        print(
            f"  {row['priority_hint']:24} {row['task_id']} "
            f"primitives={len(row['required_primitives'])}"
        )
    print(
        f"\nformal gap task manifest written to "
        f"{(Path(args.out) / 'formal_gap_lean_task_manifest.json').resolve()}"
    )
    print(f"jsonl written to {(Path(args.out) / 'formal_gap_lean_tasks.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'formal_gap_lean_tasks.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _autoform_target_export(args: argparse.Namespace) -> int:
    payload = export_autoform_targets(Path(args.run_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Autoform Target Export")
    print("=" * 72)
    print(f"targets={payload['n_ok']}/{payload['n_targets']} all_ok={payload['all_ok']}")
    print(f"yaml written to {Path(str(payload['autoform_targets_yaml'])).resolve()}")
    print(f"book dir written to {Path(str(payload['autoform_book_dir'])).resolve()}")
    for command in payload["command_templates"]:
        print(f"  {command}")
    for error in payload["errors"]:
        print(f"  error: {error}")
    return 0 if payload["all_ok"] else 1


def _autoform_harness_audit(args: argparse.Namespace) -> int:
    payload = audit_autoform_harness(Path(args.out))
    profile = payload["profile"]
    print("\nAI Statistical Theory Lab Autoform Harness Audit")
    print("=" * 72)
    print(
        f"ready={payload['ready_for_integration']} "
        f"local_execution={payload.get('ready_for_local_execution')} "
        f"availability={profile.get('availability_status', '')} "
        f"root={profile['root']} commit={str(profile['git_commit'])[:12]}"
    )
    for key in (
        "has_statement_extraction",
        "has_lean_eval",
        "has_dependency_graph_eval",
        "has_lean_proof_checker",
        "has_lean_repl_tool",
        "has_native_lsp_tool",
        "has_lean_skill_docs",
        "has_multi_agent_bot",
        "has_visualizer",
    ):
        print(f"  {key}: {profile[key]}")
    print(f"\nautoform harness manifest written to {(Path(args.out) / 'autoform_harness_manifest.json').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'autoform_harness.md').resolve()}")
    return 0 if payload["ready_for_integration"] else 1


def _proof_bank_expansion_export(args: argparse.Namespace) -> int:
    payload = export_proof_bank_expansion_candidates(Path(args.run_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Proof-Bank Expansion Candidates")
    print("=" * 72)
    print(
        f"candidates={payload['n_ok']}/{payload['n_candidates']} "
        f"bridge_ready={payload['n_bridge_ready']} "
        f"exact_reuse={payload['n_reuse_exact_proof_bank_obligation']} "
        f"blocked_placeholder={payload['n_blocked_placeholder']} "
        f"all_ok={payload['all_ok']}"
    )
    for row in payload["candidates"][:10]:
        print(
            f"  {row['status']:22} score={row['priority_score']:4} "
            f"{row['primitive']} tasks={len(row['source_task_ids'])}"
        )
    print(
        f"\nproof-bank expansion manifest written to "
        f"{(Path(args.out) / 'proof_bank_expansion_manifest.json').resolve()}"
    )
    print(f"lemma proposals JSONL written to {(Path(args.out) / 'lemma_proposals.jsonl').resolve()}")
    print(
        f"theorem-hole queue written to "
        f"{(Path(args.out) / 'theorem_hole_promotion_queue_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _proof_bank_action_export(args: argparse.Namespace) -> int:
    payload = export_proof_bank_actions(Path(args.proof_bank_expansion_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Proof-Bank Actions")
    print("=" * 72)
    print(
        f"actions={payload['n_ok']}/{payload['n_actions']} "
        f"expansion_candidates={payload['expansion_candidates']} all_ok={payload['all_ok']}"
    )
    for action_class, count in payload["by_action_class"].items():
        print(f"  {action_class}: {count}")
    print(
        f"\nproof-bank action manifest written to "
        f"{(Path(args.out) / 'proof_bank_action_manifest.json').resolve()}"
    )
    print(f"jsonl written to {(Path(args.out) / 'proof_bank_actions.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'proof_bank_actions.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _assumption_interface_export(args: argparse.Namespace) -> int:
    payload = export_assumption_interfaces(
        Path(args.proof_bank_actions_dir),
        Path(args.out),
        lean_project=args.lean_project,
        lean_timeout=args.lean_timeout,
    )
    print("\nAI Statistical Theory Lab Assumption Interfaces")
    print("=" * 72)
    print(
        f"interfaces={payload['n_ok']}/{payload['n_interfaces']} "
        f"local_lean={payload['n_local_lean_compiled']}/{payload['n_local_lean_checked']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nassumption interface manifest written to "
        f"{(Path(args.out) / 'assumption_interface_manifest.json').resolve()}"
    )
    print(f"jsonl written to {(Path(args.out) / 'assumption_interfaces.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'assumption_interfaces.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _formalization_delta_plan(args: argparse.Namespace) -> int:
    payload = build_formalization_delta_plan(
        Path(args.proof_bank_actions_dir),
        Path(args.out),
        primitive_source_coverage_dir=(
            Path(args.primitive_source_coverage_dir)
            if args.primitive_source_coverage_dir
            else None
        ),
        formal_gap_tasks_dir=Path(args.formal_gap_tasks_dir) if args.formal_gap_tasks_dir else None,
    )
    print("\nAI Statistical Theory Lab Formalization Delta Plan")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_plan_rows']} "
        f"cost={payload['total_estimated_cost']} "
        f"graph={payload['dependency_graph_nodes']}n/{payload['dependency_graph_edges']}e "
        f"low={payload['n_low_cost_existing_reuse']} "
        f"medium={payload['n_medium_cost_bridge_or_wrapper']} "
        f"high={payload['n_high_cost_new_theory']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nformalization delta manifest written to "
        f"{(Path(args.out) / 'formalization_delta_plan_manifest.json').resolve()}"
    )
    print(f"jsonl written to {(Path(args.out) / 'formalization_delta_plan.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'formalization_delta_plan.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _formal_source_roots_from_specs(specs: list[str] | None) -> tuple[FormalSourceRoot, ...] | None:
    if not specs:
        return None
    roots: list[FormalSourceRoot] = []
    for idx, spec in enumerate(specs, start=1):
        if "=" in spec:
            root_id, location = spec.split("=", 1)
        else:
            location = spec
            root_id = f"formal_source_root_{idx}"
        roots.append(FormalSourceRoot(root_id.strip(), location.strip()))
    return tuple(roots)



def _research_training_export(args: argparse.Namespace) -> int:
    payload = export_research_training_dataset(
        Path(args.run_dir),
        Path(args.out),
        validation_fraction=args.validation_fraction,
        base_model=args.base_model,
    )
    print("\nAI Statistical Theory Lab Research Training Export")
    print("=" * 72)
    print(
        f"traces={payload['n_traces']} sft={payload['n_sft_examples']} "
        f"train={payload['n_train']} validation={payload['n_validation']} "
        f"grpo={payload['n_grpo_tasks']} all_ok={payload['all_ok']}"
    )
    for task, count in payload["by_task"].items():
        print(f"  {task}: {count}")
    print(
        f"\nresearch training manifest written to "
        f"{(Path(args.out) / 'research_training_manifest.json').resolve()}"
    )
    print(
        f"train JSONL written to "
        f"{(Path(args.out) / 'research_sft_train.jsonl').resolve()}"
    )
    print(
        f"validation JSONL written to "
        f"{(Path(args.out) / 'research_sft_validation.jsonl').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _research_policy_baseline(args: argparse.Namespace) -> int:
    payload = evaluate_research_policy_baseline(
        Path(args.train_jsonl),
        Path(args.validation_jsonl),
        Path(args.out),
        k=args.k,
    )
    print("\nAI Statistical Theory Lab Research Policy Baseline")
    print("=" * 72)
    print(
        f"train={payload['n_train']} validation={payload['n_validation']} "
        f"top1_exact={payload['top1_exact_rate']:.3f} "
        f"same_task={payload['same_task_rate']:.3f} "
        f"json_key_f1={payload['mean_json_key_f1']:.3f} "
        f"all_ok={payload['all_ok']}"
    )
    print(f"\nmanifest written to {(Path(args.out) / 'research_policy_baseline_manifest.json').resolve()}")
    print(f"predictions written to {(Path(args.out) / 'research_policy_baseline_predictions.jsonl').resolve()}")
    return 0 if payload["all_ok"] else 1


def _next_iteration_audit(args: argparse.Namespace) -> int:
    payload = audit_next_iteration_queue(Path(args.run_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Next-Iteration Queue")
    print("=" * 72)
    print(
        f"items={payload['n_ok']}/{payload['n_items']} "
        f"actionable={payload['n_actionable_items']} all_ok={payload['all_ok']}"
    )
    for owner, count in payload["by_owner"].items():
        print(f"  {owner}: {count}")
    print(
        f"\nnext-iteration queue manifest written to "
        f"{(Path(args.out) / 'next_iteration_queue_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'next_iteration_queue.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _research_report(args: argparse.Namespace) -> int:
    payload = build_research_markdown_report(Path(args.run_dir), Path(args.out))
    counts = payload["counts"]
    print("\nAI Statistical Theory Lab Research Report")
    print("=" * 72)
    print(
        f"questions={counts['questions']} ready_with_gaps={counts['ready_with_gaps']} "
        f"proved={counts['proved_subclaims']} gaps={counts['formal_gaps']} "
        f"simulations={counts['simulations_passed']}/{counts['simulations']}"
    )
    for error in payload["errors"]:
        print(f"  report error: {error[:180]}")
    print(f"\nmarkdown report written to {(Path(args.out) / 'research_report.md').resolve()}")
    print(f"report manifest written to {(Path(args.out) / 'research_report_manifest.json').resolve()}")
    return 0 if payload["all_ok"] else 1



def _theorem_composition_export(args: argparse.Namespace) -> int:
    payload = export_theorem_composition_packets(Path(args.claim_ledger_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Theorem Composition Packets")
    print("=" * 72)
    print(
        f"packets={payload['n_ok']}/{payload['n_packets']} "
        f"exact_links={payload['n_exact_proof_bank_links']} "
        f"unresolved_primitives={payload['n_unresolved_primitives']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\ntheorem-composition manifest written to "
        f"{(Path(args.out) / 'theorem_composition_manifest.json').resolve()}"
    )
    print(f"jsonl written to {(Path(args.out) / 'theorem_composition_packets.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'theorem_composition.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _doctor(args: argparse.Namespace) -> int:
    env_file = _resolve_dotenv_path(Path(args.env_file))
    _load_dotenv(env_file)
    report = build_doctor_report(
        root=Path(args.root),
        env_file=env_file,
        max_manifests=args.max_manifests,
    )
    if args.out:
        manifest = write_doctor_manifest(report, Path(args.out))
    else:
        manifest = None
    if args.json:
        import json

        print(json.dumps(report, indent=2, default=str))
    else:
        summary = report["summary"]
        print("\nAI Statistician Doctor")
        print("=" * 72)
        print(f"root={report['root']}")
        print(f"required_ok={summary['required_ok']}")
        print(f"real_lean_ready={summary['real_lean_ready']}")
        print(f"local_lean_available={summary['local_lean_available']}")
        print(f"llm_theory_ready={summary['llm_theory_ready']}")
        print(f"llm_provider={summary['llm_provider']}")
        print(f"llm_models={summary['llm_models']}")
        print(f"openprover_available={summary['openprover_available']}")
        print(f"registered: obligations={summary['n_obligations']} algorithms={summary['n_algorithms']}")
        for check in report["checks"]:
            required = "required" if check["required"] else "optional"
            print(f"  {check['status']:4} {check['name']} ({required})")
            print(f"       {check['detail']}")
        latest = report["latest_manifests"]
        if latest:
            print("\nlatest manifests")
            for row in latest[: args.max_manifests]:
                print(f"  {row['name']}: {row['path']}")
        if manifest:
            print(f"\ndoctor manifest written to {manifest.resolve()}")
    return 0 if report["summary"]["required_ok"] else 1


def _capability_audit(args: argparse.Namespace) -> int:
    report = build_capability_audit(root=Path(args.root), max_manifests=args.max_manifests)
    manifest = write_capability_audit(report, Path(args.out))
    if args.json:
        import json

        print(json.dumps(report, indent=2, default=str))
    else:
        print("\nAI Statistician Capability Audit")
        print("=" * 72)
        print(f"root={report['root']}")
        print(f"all_required_capabilities_present={report['all_required_capabilities_present']}")
        print(f"ready={report['n_ready']} partial={report['n_partial']} missing={report['n_missing']}")
        for row in report["findings"]:
            print(f"  {row['status']:7} {row['requirement']}")
            for evidence in row["evidence"][:3]:
                print(f"          evidence: {evidence}")
            for limitation in row["limitations"]:
                print(f"          limitation: {limitation}")
        print(f"\ncapability audit manifest written to {manifest.resolve()}")
    return 0 if report["all_required_capabilities_present"] else 1


def _research_capability_audit(args: argparse.Namespace) -> int:
    report = build_research_capability_audit(
        root=Path(args.root),
        question_file=Path(args.question_file),
        frontier_benchmark_file=Path(args.frontier_benchmark_file),
        max_manifests=args.max_manifests,
    )
    manifest = write_research_capability_audit(report, Path(args.out))
    if args.json:
        import json

        print(json.dumps(report, indent=2, default=str))
    else:
        print("\nAI Statistical Theory Lab Capability Audit")
        print("=" * 72)
        print(f"root={report['root']}")
        print(f"goal_complete={report['goal_complete']}")
        print(f"all_current_release_requirements_met={report['all_current_release_requirements_met']}")
        print(
            f"achieved={report['n_achieved']} partial={report['n_partial']} "
            f"not_achieved={report['n_not_achieved']}"
        )
        frontier = report["frontier_summary"]
        print(f"frontier_supported={frontier['n_supported']}/{frontier['n_questions']}")
        for row in report["findings"]:
            gate = "gate" if row["current_release_gate"] else "roadmap"
            print(f"  {row['status']:12} {gate:7} {row['requirement']}")
            for evidence in row["evidence"][:3]:
                print(f"          evidence: {evidence}")
            for limitation in row["limitations"][:2]:
                print(f"          limitation: {limitation}")
        print(f"\nresearch capability audit manifest written to {manifest.resolve()}")
        print(f"markdown report written to {(Path(args.out) / 'research_capability_audit.md').resolve()}")
    return 0 if report["all_current_release_requirements_met"] else 1



def _prover_component_audit(args: argparse.Namespace) -> int:
    payload = build_prover_component_audit(
        root=Path(args.root),
        question_file=Path(args.question_file),
        frontier_benchmark_file=Path(args.frontier_benchmark_file),
    )
    manifest, report = write_prover_component_audit(payload, Path(args.out))
    if args.json:
        import json

        print(json.dumps(payload, indent=2, default=str))
    else:
        summary = payload["summary"]
        print("\nAI Statistician Prover Component Audit")
        print("=" * 72)
        print(f"paper_outline_exists={payload['paper_outline_exists']}")
        print(
            f"components={summary['components']} ready={summary['ready']} "
            f"partial={summary['partial']} missing_or_not_trained={summary['missing_or_not_trained']}"
        )
        for row in payload["rows"]:
            print(f"  {row['status']:25} {row['component']}")
            for item in row["missing_or_next"][:2]:
                print(f"          next: {item}")
        print(f"\nprover component audit manifest written to {manifest.resolve()}")
        print(f"markdown report written to {report.resolve()}")
    return 0


async def _system_audit(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    questions = load_audit_questions(args.question_file, args.include_partial_examples)
    seeds = tuple(int(seed) for seed in args.seeds) if args.seeds else tuple(
        range(args.seed_start, args.seed_start + args.n_seeds)
    )
    payload = await run_system_audit(
        Path(args.out),
        questions=questions,
        config=SystemAuditConfig(
            n_runs=args.runs,
            seeds=seeds,
            use_axle=args.real_lean,
            include_eval=not args.no_eval,
        ),
    )
    print("\nAI Statistician System Audit")
    print("=" * 72)
    print(f"all_gates_passed={payload['all_gates_passed']}")
    for gate, ok in payload["gates"].items():
        print(f"  {gate}: {'OK' if ok else 'FAIL'}")
    counts = payload["counts"]
    print(
        f"  questions={counts['question_runs_accepted']}/{counts['questions']} "
        f"proofs={counts['proofs_verified']}/{counts['proofs_total']} "
        f"algorithms={counts['algorithms_ok']}/{counts['algorithms_total']}"
    )
    print(f"\nsystem audit manifest written to {(Path(args.out) / 'system_audit_manifest.json').resolve()}")
    return 0


async def _release_bundle(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    questions = load_audit_questions(args.question_file, args.include_partial_examples)
    seeds = tuple(int(seed) for seed in args.seeds) if args.seeds else tuple(
        range(args.seed_start, args.seed_start + args.n_seeds)
    )
    payload = await build_release_bundle(
        Path(args.out),
        root=Path(args.root),
        env_file=Path(args.env_file),
        questions=questions,
        config=ReleaseBundleConfig(
            n_runs=args.runs,
            seeds=seeds,
            use_axle=args.real_lean,
            include_eval=not args.no_eval,
            max_manifests=args.max_manifests,
        ),
    )
    print("\nAI Statistician Release Bundle")
    print("=" * 72)
    print(f"release_id={payload['release_id'][:16]}")
    print(f"all_release_gates_passed={payload['all_release_gates_passed']}")
    for gate, ok in payload["gates"].items():
        print(f"  {gate}: {'OK' if ok else 'FAIL'}")
    counts = payload["counts"]
    print(
        f"  questions={counts['question_runs_accepted']}/{counts['questions']} "
        f"proofs={counts['proofs_verified']}/{counts['proofs_total']} "
        f"algorithms={counts['algorithms_ok']}/{counts['algorithms_total']}"
    )
    print(f"\nrelease manifest written to {(Path(args.out) / 'release_manifest.json').resolve()}")
    return 0 if payload["all_release_gates_passed"] else 1


async def _research_benchmark(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    verifier = _proof_verifier_from_args(args)
    questions = load_open_research_questions(Path(args.question_file))
    payload = await run_research_benchmark(
        questions,
        Path(args.out),
        proof_verifier=verifier,
        formal_source_index_path=(
            Path(args.out) / "formal_source_index.sqlite"
            if args.formal_source_backend == "sqlite"
            else None
        ),
        lean_rag_db_path=Path(args.lean_rag_db) if args.lean_rag_db else None,
        n_runs=args.runs,
        seed=args.seed,
        adaptive_mc_rerun=args.adaptive_mc_rerun,
        adaptive_mc_multiplier=args.adaptive_mc_multiplier,
    )
    print("\nAI Statistical Theory Lab Benchmark")
    print("=" * 72)
    print(
        f"questions={payload['n_questions']} "
        f"ready_with_gaps={payload['n_ready_with_gaps']} "
        f"simulation_flagged={payload['n_simulation_flagged']} "
        f"formal_blocked={payload['n_formal_blocked']}"
    )
    if payload.get("simulation_policy"):
        policy = payload["simulation_policy"]
        print(
            "simulation_policy="
            f"adaptive_mc_rerun={policy.get('adaptive_mc_rerun')} "
            f"adaptive_mc_rows={policy.get('adaptive_mc_rows')} "
            f"adaptive_mc_resolved={policy.get('adaptive_mc_resolved')}"
        )
    if payload.get("formal_source_search"):
        search = payload["formal_source_search"]
        print(f"formal_source_search={search['backend']}")
        if search.get("sqlite_index_path"):
            print(f"sqlite index written to {Path(str(search['sqlite_index_path'])).resolve()}")
        if search.get("dependency_graph_backend"):
            print(f"dependency_graph_search={search['dependency_graph_backend']}")
    for row in payload["questions"]:
        formal = row["formal"]
        print(
            f"{row['status']:38} {row['question']:34} "
            f"class={row['problem_class']}"
        )
        print(
            f"  formal: proved={formal['proved']} gaps={formal['gaps']} "
            f"formalized_gaps={formal.get('formalized_gaps', 0)} failed={formal['failed']} "
            f"procedures={', '.join(row['procedures']) or 'none'}"
        )
        for sim in row["simulations"]:
            metrics = sim["metrics"]
            if "coverage_95" in metrics:
                print(
                    f"  sim {sim['procedure_id']}: passed={sim['passed']} "
                    f"coverage95={metrics['coverage_95']:.3f} rmse={metrics.get('rmse', metrics.get('rmse_center', 0.0)):.4f}"
                )
            else:
                print(f"  sim {sim['procedure_id']}: passed={sim['passed']}")
    print(f"\nresearch manifest written to {(Path(args.out) / 'research_benchmark_manifest.json').resolve()}")
    return 0



async def _research_eval(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    questions = load_open_research_questions(Path(args.question_file))
    seeds = tuple(int(seed) for seed in args.seeds) if args.seeds else tuple(
        range(args.seed_start, args.seed_start + args.n_seeds)
    )
    payload = await run_research_seed_eval(
        questions,
        ResearchEvalConfig(seeds=seeds, n_runs=args.runs, use_axle=args.real_lean),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Evaluation")
    print("=" * 72)
    print(
        f"questions={payload['n_questions']} seeds={payload['n_seeds']} "
        f"all_ready_with_gaps={payload['all_ready_with_gaps']} "
        f"trace_audits_ok={payload['all_trace_audits_ok']}"
    )
    for question_id, row in payload["summary"].items():
        print(
            f"{question_id:34} ready={row['ready_with_gaps']}/{row['trials']} "
            f"rate={row['ready_rate']:.2f} "
            f"sim_flagged={row['simulation_flagged']} formal_blocked={row['formal_blocked']}"
        )
        for procedure_id, metrics in row["procedures"].items():
            metric_bits = []
            for metric_key, summary in sorted(metrics.items()):
                if not isinstance(summary, Mapping):
                    continue
                value = summary.get("mean")
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    continue
                metric_bits.append(f"{metric_key}={float(value):.4f}")
            if metric_bits:
                print(f"  {procedure_id}: " + " ".join(metric_bits))
    print(f"\nresearch evaluation manifest written to {(Path(args.out) / 'research_evaluation_manifest.json').resolve()}")
    return 0 if payload["all_trace_audits_ok"] else 1



def _list(args: argparse.Namespace) -> int:
    print("Questions")
    for q in QUESTIONS.values():
        print(f"- {q.id}: {q.title}")
    print("\nFormal obligations")
    rows = obligations_by_tags(set(args.tag or [])) if args.tag else all_obligations()
    for obligation in rows:
        print(f"- {obligation.id}: {obligation.title} [{', '.join(obligation.tags)}]")
    return 0


def _research_architect_theory_develop(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    questions = load_open_research_questions(Path(args.question_file))
    questions, missing_question_ids = _select_questions_by_id(
        questions,
        getattr(args, "question_id", []) or [],
    )
    if missing_question_ids:
        print("\nAI Statistician Research Architect rejected question ids")
        print("=" * 72)
        for question_id in missing_question_ids:
            print(f"- unknown question_id: {question_id}")
        return 2
    if args.max_questions:
        questions = questions[: args.max_questions]
    provider, provider_name = _build_theory_generator_backend(
        provider_name=args.provider,
        static_response_file=args.static_response_file,
        llm_timeout_seconds=getattr(args, "llm_timeout_seconds", None),
    )
    research_source_manifest = str(
        getattr(args, "research_source_manifest", "") or ""
    ).strip()
    try:
        research_sources = (
            load_research_source_snapshot(Path(research_source_manifest))
            if research_source_manifest
            else None
        )
        research_source_execution_manifest = str(
            getattr(args, "research_source_execution_manifest", "") or ""
        ).strip()
        if research_source_execution_manifest and research_sources is None:
            raise ValueError(
                "--research-source-execution-manifest requires "
                "--research-source-manifest"
            )
        research_source_execution = (
            load_research_source_execution_spec(
                Path(research_source_execution_manifest),
                research_sources=research_sources,
            )
            if research_source_execution_manifest and research_sources is not None
            else None
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print("\nAI Statistician rejected research source snapshot")
        print("=" * 72)
        print(f"- {exc}")
        return 2
    if research_sources is not None and not callable(
        getattr(provider, "generate_client_tool_turn", None)
    ):
        print("\nAI Statistician rejected research source snapshot")
        print("=" * 72)
        print("- research sources require a provider with native client-tool turns")
        return 2
    context: dict[str, object] = {}
    if args.context_json:
        context = json.loads(Path(args.context_json).read_text(encoding="utf-8"))
    model = _default_model_for_provider(args.provider, args.llm_model, model_tier="sonnet")
    model_tier = (
        claude_model_tier_for_model(model)
        if provider_name == "anthropic"
        else ""
    ) or "sonnet"
    theory_developer = LLMTheoryDeveloperAgent(
        provider=provider,
        research_sources=research_sources,
        research_source_execution=research_source_execution,
        config=ResearchArchitectConfig(
            model=model,
            model_tier=model_tier,
            max_tokens=args.max_tokens,
            serious_model=model,
            serious_model_tier=model_tier,
            serious_max_tokens=args.max_tokens,
            temperature=args.temperature,
            provider_name=provider_name,
            max_validation_retries=args.max_validation_retries,
        ),
    )
    architect = ResearchArchitectAgent(
        theory_developer=theory_developer,
        out_dir=Path(args.out),
    )
    manifest = architect.run_theory_development(questions, architect_context=context)
    print("\nAI Statistician Research Architect")
    print("=" * 72)
    print(
        f"questions={manifest['n_questions']} "
        f"theory_packets={manifest['n_theory_derivation_packets']} "
        f"all_packets_ok={manifest['all_packets_ok']}"
    )
    print(f"proof_evidence_status={manifest['proof_evidence_status']}")
    print(
        "architect manifest written to "
        f"{(Path(args.out) / 'research_architect_manifest.json').resolve()}"
    )
    return 0 if manifest["all_packets_ok"] else 1


def _research_agent_runtime(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    try:
        _apply_research_agent_runtime_research_eval_profile(args)
        _apply_research_agent_runtime_capability_eval_preset(args)
        _apply_research_agent_runtime_evaluation_model_policy(args)
    except ValueError as exc:
        print("\nAI Statistician Agent Runtime evaluation profile rejected")
        print("=" * 72)
        print(f"- {exc}")
        return 2
    evaluation_model_policy_errors = (
        _research_agent_runtime_evaluation_model_policy_errors(args)
    )
    if evaluation_model_policy_errors:
        print("\nAI Statistician Agent Runtime evaluation model policy rejected")
        print("=" * 72)
        for error in evaluation_model_policy_errors:
            print(f"- {error}")
        return 2
    research_gold_manifest = str(
        getattr(args, "research_gold_manifest", "") or ""
    ).strip()
    if research_gold_manifest and not bool(getattr(args, "research_eval", False)):
        print("\nAI Statistician Agent Runtime rejected gold evaluation config")
        print("=" * 72)
        print("- --research-gold-manifest requires --research-eval")
        return 2
    _apply_research_agent_runtime_live_lean_defaults(args)
    if getattr(args, "capability_eval", False):
        config_errors = _research_agent_runtime_capability_config_errors(args)
        if not config_errors:
            config_errors.extend(
                _research_agent_runtime_local_lean_preflight_errors(args)
            )
        if config_errors:
            print("\nAI Statistician Agent Runtime capability eval rejected")
            print("=" * 72)
            for error in config_errors:
                print(f"- {error}")
            return 2
    static_config_errors = _research_agent_runtime_static_subsystem_config_errors(args)
    if static_config_errors:
        print("\nAI Statistician Agent Runtime static subsystem config rejected")
        print("=" * 72)
        for error in static_config_errors:
            print(f"- {error}")
        return 2
    proof_state_provider = _proof_state_provider_from_args(args)
    resume_initial_tasks: dict[str, AgentTask] = {}
    resume_blackboard_artifacts: dict[str, dict[str, Any]] = {}
    resume_question_id = ""
    if getattr(args, "resume_runtime_manifest", ""):
        resume_manifest_path = Path(args.resume_runtime_manifest)
        try:
            (
                resume_question_id,
                resume_task,
                resume_artifacts,
            ) = _load_runtime_resume_task_from_manifest(resume_manifest_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print("\nAI Statistician Agent Runtime rejected resume manifest")
            print("=" * 72)
            print(f"- {exc}")
            return 2
        resume_initial_tasks[resume_question_id] = resume_task
        resume_blackboard_artifacts[resume_question_id] = resume_artifacts
    questions = load_open_research_questions(Path(args.question_file))
    (
        protocol_question_ids,
        cross_family_protocol_selection,
        protocol_selection_errors,
    ) = _cross_family_eval_protocol_selection(args, questions)
    if protocol_selection_errors:
        print("\nAI Statistician Agent Runtime rejected evaluation protocol")
        print("=" * 72)
        for error in protocol_selection_errors:
            print(f"- {error}")
        return 2
    requested_question_ids = (
        protocol_question_ids
        if protocol_question_ids
        else list(getattr(args, "question_id", []) or [])
    )
    if resume_question_id and not requested_question_ids:
        requested_question_ids = [resume_question_id]
    questions, missing_question_ids = _select_questions_by_id(
        questions,
        requested_question_ids,
    )
    if missing_question_ids:
        print("\nAI Statistician Agent Runtime rejected question ids")
        print("=" * 72)
        for question_id in missing_question_ids:
            print(f"- unknown question_id: {question_id}")
        return 2
    questions, missing_task_families = _select_questions_by_task_family(
        questions,
        getattr(args, "question_task_family", []) or [],
    )
    if missing_task_families:
        print("\nAI Statistician Agent Runtime rejected task families")
        print("=" * 72)
        for task_family in missing_task_families:
            print(f"- unknown task_family: {task_family}")
        return 2
    if args.max_questions:
        questions = questions[: args.max_questions]
    if cross_family_protocol_selection:
        args.min_task_families = max(
            int(getattr(args, "min_task_families", 0) or 0),
            int(
                cross_family_protocol_selection[
                    "minimum_distinct_task_families"
                ]
            ),
        )
    task_family_selection_errors = _minimum_task_family_selection_errors(
        questions,
        min_task_families=int(getattr(args, "min_task_families", 0) or 0),
    )
    if task_family_selection_errors:
        print("\nAI Statistician Agent Runtime rejected task-family selection")
        print("=" * 72)
        for error in task_family_selection_errors:
            print(f"- {error}")
        return 2
    if resume_question_id and (
        len(questions) != 1 or str(getattr(questions[0], "id", "") or "") != resume_question_id
    ):
        print("\nAI Statistician Agent Runtime rejected resume selection")
        print("=" * 72)
        print(
            "- --resume-runtime-manifest must run exactly the pending question id: "
            f"{resume_question_id}"
        )
        return 2
    provider, provider_name = _build_theory_generator_backend(
        provider_name=args.provider,
        static_response_file=args.static_response_file,
        llm_timeout_seconds=getattr(args, "llm_timeout_seconds", None),
    )
    research_source_manifest = str(
        getattr(args, "research_source_manifest", "") or ""
    ).strip()
    try:
        research_sources = (
            load_research_source_snapshot(Path(research_source_manifest))
            if research_source_manifest
            else None
        )
        research_source_execution_manifest = str(
            getattr(args, "research_source_execution_manifest", "") or ""
        ).strip()
        if research_source_execution_manifest and research_sources is None:
            raise ValueError(
                "--research-source-execution-manifest requires "
                "--research-source-manifest"
            )
        research_source_execution = (
            load_research_source_execution_spec(
                Path(research_source_execution_manifest),
                research_sources=research_sources,
            )
            if research_source_execution_manifest and research_sources is not None
            else None
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print("\nAI Statistician Agent Runtime rejected research source snapshot")
        print("=" * 72)
        print(f"- {exc}")
        return 2
    if research_sources is not None and not callable(
        getattr(provider, "generate_client_tool_turn", None)
    ):
        print("\nAI Statistician Agent Runtime rejected research source snapshot")
        print("=" * 72)
        print("- research sources require a provider with native client-tool turns")
        return 2
    context: dict[str, object] = {}
    if args.context_json:
        context = json.loads(Path(args.context_json).read_text(encoding="utf-8"))
    if cross_family_protocol_selection:
        context["cross_family_evaluation_protocol"] = dict(
            cross_family_protocol_selection
        )
    theory_model_tier = _runtime_effective_model_tier(args, "sonnet")
    serious_theory_model_tier = _runtime_effective_model_tier(args, "sonnet")
    theory_model = _runtime_evaluation_model_name(
        args,
        provider_choice=args.provider,
        configured_model=getattr(args, "llm_model", ""),
    )
    serious_theory_model = _runtime_evaluation_model_name(
        args,
        provider_choice=args.provider,
        configured_model=getattr(args, "serious_theory_llm_model", ""),
    )
    model = _default_model_for_provider(
        args.provider,
        theory_model,
        model_tier=theory_model_tier,
    )
    theory_developer = LLMTheoryDeveloperAgent(
        provider=provider,
        research_sources=research_sources,
        research_source_execution=research_source_execution,
        config=ResearchArchitectConfig(
            model=theory_model,
            model_tier=theory_model_tier,
            max_tokens=args.max_tokens,
            serious_model=serious_theory_model,
            serious_model_tier=serious_theory_model_tier,
            serious_max_tokens=int(
                getattr(
                    args,
                    "serious_theory_max_tokens",
                    ResearchArchitectConfig().serious_max_tokens,
                )
                or 0
            ),
            temperature=args.temperature,
            provider_name=provider_name,
            max_validation_retries=args.theory_max_validation_retries,
        ),
    )
    try:
        formal_source_retriever = _formal_source_retriever_from_runtime_args(args)
    except ValueError as exc:
        print("\nAI Statistician Agent Runtime rejected Lean provider config")
        print("=" * 72)
        print(f"- {exc}")
        return 2
    architect_coordinator = _build_architect_coordinator_agent_from_args(
        args,
        default_model=model,
        formal_source_retriever=formal_source_retriever,
    )
    algorithm_engineer = _build_algorithm_engineer_agent_from_args(args, default_model=model)
    simulation_engineer = _build_simulation_engineer_agent_from_args(args, default_model=model)
    formalizer = _build_formalizer_agent_from_args(args, default_model=model)
    critic_evaluator = _build_critic_evaluator_agent_from_args(args, default_model=model)
    generated_code_semantic_reviewer = (
        _build_generated_code_semantic_reviewer_agent_from_args(
            args,
            default_model=model,
        )
    )
    formal_target_semantic_reviewer = (
        _build_formal_target_semantic_reviewer_agent_from_args(
            args,
            default_model=model,
        )
    )
    try:
        proof_search_provider = _proof_search_provider_from_runtime_args(
            args,
            generator_backend=(
                formalizer.provider if formalizer is not None else provider
            ),
            model=(
                str(formalizer.config.model or model)
                if formalizer is not None
                else model
            ),
            out_dir=Path(args.out),
        )
    except ValueError as exc:
        print("\nAI Statistician Agent Runtime rejected Lean provider config")
        print("=" * 72)
        print(f"- {exc}")
        return 2
    resume_through_architect = _effective_resume_through_architect(
        args,
        architect_coordinator_configured=architect_coordinator is not None,
    )
    manifest = run_research_agent_runtime(
        questions,
        Path(args.out),
        theory_developer=theory_developer,
        architect_coordinator=architect_coordinator,
        simulation_engineer=simulation_engineer,
        algorithm_engineer=algorithm_engineer,
        formalizer=formalizer,
        critic_evaluator=critic_evaluator,
        generated_code_semantic_reviewer=generated_code_semantic_reviewer,
        formal_target_semantic_reviewer=formal_target_semantic_reviewer,
        proof_state_provider=proof_state_provider,
        formal_source_retriever=formal_source_retriever,
        proof_search_provider=proof_search_provider,
        research_gold_manifest=(
            Path(research_gold_manifest) if research_gold_manifest else None
        ),
        architect_context=context,
        initial_task_overrides=resume_initial_tasks,
        initial_blackboard_artifacts=resume_blackboard_artifacts,
        config=ResearchAgentRuntimeConfig(
            n_runs=args.runs,
            seed=args.seed,
            generated_simulation_timeout_seconds=int(
                getattr(args, "generated_simulation_timeout_seconds", 60)
                or 60
            ),
            max_iterations=args.max_iterations,
            max_subsystem_retries=args.max_subsystem_retries,
            max_critic_revision_rounds=args.max_critic_revision_rounds,
            generated_code_semantic_review_max_revisions=int(
                getattr(
                    args,
                    "generated_code_semantic_review_max_revisions",
                    1,
                )
                or 0
            ),
            metric_protocol_max_upstream_theory_revisions=int(
                getattr(
                    args,
                    "architect_metric_protocol_max_upstream_theory_revisions",
                    2,
                )
                or 0
            ),
            formal_target_semantic_review_required=bool(
                getattr(args, "formal_target_semantic_review_required", False)
            ),
            formal_target_semantic_review_max_revisions=int(
                getattr(
                    args,
                    "formal_target_semantic_review_max_revisions",
                    2,
                )
                or 0
            ),
            resume_through_architect=resume_through_architect,
            formal_verification_policy=str(
                getattr(args, "formal_verification_policy", "optional") or "optional"
            ),
            recommended_research_path=str(
                getattr(args, "recommended_research_path", "") or ""
            ),
            evaluation_mode=(
                "capability_eval"
                if getattr(args, "capability_eval", False)
                else "research_eval"
                if getattr(args, "research_eval", False)
                else "debug"
            ),
            evaluation_claude_model_tier=str(
                getattr(args, "evaluation_claude_model_tier", "") or ""
            ),
            evaluation_claude_model=str(
                getattr(args, "evaluation_claude_model", "") or ""
            ),
            formalizer_candidate_local_lean=bool(
                getattr(args, "formalizer_candidate_local_lean", False)
                or getattr(args, "formalizer_candidate_lean_lsp_mcp", False)
                or getattr(args, "openprover_hlm", False)
            ),
            formalizer_candidate_lean_project=str(
                getattr(args, "formalizer_candidate_lean_project", "")
                or getattr(args, "lean_project", "")
                or ""
            ),
            formalizer_candidate_lean_timeout=int(
                getattr(
                    args,
                    "formalizer_candidate_lean_timeout",
                    DEFAULT_LEAN_TOOL_TIMEOUT_SECONDS,
                )
            ),
        ),
    )
    print("\nAI Statistician Agent Runtime")
    print("=" * 72)
    print(
        f"questions={manifest['n_questions']} "
        f"status_counts={manifest['status_counts']}"
    )
    print(
        f"kernel_verified_subclaims={manifest['n_kernel_verified_subclaims']} "
        "materialized_formal_gap_rows="
        f"{manifest['n_materialized_formal_gap_rows']} "
        "formal_unverified_questions="
        f"{manifest['formal_closure_summary']['n_questions_formal_unverified']} "
        "generated_code_sandbox_executed="
        f"{manifest['n_generated_code_sandbox_executed']} "
        "generated_simulation_sandbox_executed="
        f"{manifest['n_generated_simulation_sandbox_executed']}"
    )
    print(f"simulation_boundary={manifest['simulation_evidence_boundary']}")
    print(
        "runtime manifest written to "
        f"{(Path(args.out) / 'research_agent_runtime_manifest.json').resolve()}"
    )
    if getattr(args, "research_eval", False):
        summary = manifest.get("research_evaluation_summary", {})
        gold = manifest.get("research_gold_evaluation", {})
        print(
            "research_evaluation="
            f"{summary.get('n_questions_research_eval_complete', 0)}/"
            f"{summary.get('n_questions', 0)} "
            f"capability={summary.get('all_questions_research_loop_complete', False)} "
            f"conformant={summary.get('all_questions_mode_conformant', False)} "
            f"ready={summary.get('all_questions_research_eval_complete', False)}"
        )
        if gold.get("configured") is not False:
            print(
                "research_gold_evaluation="
                f"{gold.get('n_tasks_passed', 0)}/"
                f"{gold.get('n_active_tasks', 0)} "
                f"ready={gold.get('all_active_tasks_passed', False)}"
            )
        ready = _research_agent_runtime_research_eval_ready(
            summary=summary,
            gold=gold,
            research_gold_manifest=research_gold_manifest,
        )
        return 0 if ready else 1
    if getattr(args, "capability_eval", False):
        audit = audit_research_agent_runtime(
            Path(args.out),
            Path(args.out) / "runtime_capability_audit",
        )
        scorecard = audit.get("capability_scorecard", {})
        print(
            f"capability_scorecard={scorecard.get('n_passed')}/"
            f"{scorecard.get('n_requirements')} "
            f"ready={scorecard.get('ready')}"
        )
        failed = [
            str(row.get("requirement_id", "") or "")
            for row in scorecard.get("rows", []) or []
            if isinstance(row, dict) and row.get("passed") is not True
        ]
        if failed:
            print(f"missing_capabilities={','.join(row for row in failed if row)}")
        return 0 if audit.get("capability_ready_for_full_ai_statistician") else 1
    return 0


def _research_agent_runtime_research_eval_ready(
    *,
    summary: Mapping[str, Any],
    gold: Mapping[str, Any],
    research_gold_manifest: str,
) -> bool:
    """Use the frozen gold scope instead of imposing every research lane."""

    if research_gold_manifest:
        return gold.get("all_active_tasks_passed") is True
    return summary.get("all_questions_research_eval_complete") is True




















def _apply_research_agent_runtime_research_eval_profile(
    args: argparse.Namespace,
) -> None:
    """Configure the live research loop without enabling the strict formal lane."""

    if not bool(getattr(args, "research_eval", False)):
        return
    capability_preset = str(
        getattr(args, "capability_eval_preset", "none") or "none"
    ).strip()
    if bool(getattr(args, "capability_eval", False)) or capability_preset not in {
        "",
        "none",
    }:
        raise ValueError(
            "--research-eval cannot be combined with --capability-eval or "
            "--capability-eval-preset"
        )
    if str(getattr(args, "provider", "") or "") not in {"anthropic", "openai"}:
        args.provider = _default_live_generator_provider()
    for field_name in (
        "architect_coordinator_provider",
        "simulation_engineer_provider",
        "algorithm_engineer_provider",
        "critic_evaluator_provider",
        "generated_code_semantic_reviewer_provider",
    ):
        if str(getattr(args, field_name, "") or "") in {"", "none", "static"}:
            setattr(args, field_name, "same")
    args.formalizer_provider = "none"
    args.formal_target_semantic_reviewer_provider = "none"
    args.formal_target_semantic_review_required = False
    args.formal_verification_policy = "advisory"
    args.recommended_research_path = "simulation_first"
    args.architect_max_tokens = max(
        LIVE_EVALUATION_MIN_ARCHITECT_MAX_TOKENS,
        int(getattr(args, "architect_max_tokens", 0) or 0),
    )
    args.serious_theory_model_tier = LIVE_EVALUATION_CLAUDE_MODEL_TIER
    args.architect_metric_semantic_reviewer_max_tokens = max(
        LIVE_EVALUATION_MIN_METRIC_REVIEWER_MAX_TOKENS,
        int(
            getattr(
                args,
                "architect_metric_semantic_reviewer_max_tokens",
                0,
            )
            or 0
        ),
    )
    args.architect_metric_protocol_max_upstream_theory_revisions = max(
        2,
        int(
            getattr(
                args,
                "architect_metric_protocol_max_upstream_theory_revisions",
                0,
            )
            or 0
        ),
    )
    args.max_iterations = max(
        RESEARCH_EVAL_MIN_AGENT_RUNTIME_ITERATIONS,
        int(getattr(args, "max_iterations", 0) or 0),
    )
    args.serious_theory_max_tokens = max(
        LIVE_EVALUATION_MIN_SERIOUS_THEORY_MAX_TOKENS,
        int(getattr(args, "serious_theory_max_tokens", 0) or 0),
    )
    args.llm_timeout_seconds = max(
        SERIOUS_THEORY_MIN_LLM_TIMEOUT_SECONDS,
        float(
            getattr(
                args,
                "llm_timeout_seconds",
                DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
            )
            or DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS
        ),
    )


def _apply_research_agent_runtime_capability_eval_preset(
    args: argparse.Namespace,
) -> None:
    """Populate strict live capability-eval defaults without weakening gates."""

    preset = str(getattr(args, "capability_eval_preset", "") or "").strip()
    if preset in {"", "none"}:
        return
    if preset not in {"minimal-live", "full-live"}:
        raise ValueError(f"unsupported capability eval preset: {preset}")

    if str(getattr(args, "provider", "") or "") not in {"anthropic", "openai"}:
        args.provider = _default_live_generator_provider()
    for field_name in (
        "architect_coordinator_provider",
        "simulation_engineer_provider",
        "algorithm_engineer_provider",
        "formalizer_provider",
        "critic_evaluator_provider",
        "generated_code_semantic_reviewer_provider",
        "formal_target_semantic_reviewer_provider",
    ):
        if str(getattr(args, field_name, "") or "") in {"", "none", "static"}:
            setattr(args, field_name, "same")

    if not bool(getattr(args, "local_lean", False)) and not bool(
        getattr(args, "real_lean", False)
    ):
        args.local_lean = True
    lean_project = str(getattr(args, "lean_project", "") or "").strip()
    if not lean_project:
        for default_lean_project in (
            _capability_eval_default_lean_project_candidates()
        ):
            if _is_lake_project(default_lean_project):
                args.lean_project = str(default_lean_project)
                lean_project = str(default_lean_project)
                break

    args.formalizer_candidate_local_lean = True

    if not str(
        getattr(args, "emperical_process_lean_rag_root", "") or ""
    ).strip():
        from .research_source_inventory import (
            EXTERNAL_EMPIRICAL_PROCESS_LEAN_ROOT,
        )

        shared_retrieval = (
            EXTERNAL_EMPIRICAL_PROCESS_LEAN_ROOT
            / "lean_rag"
            / "scripts"
            / "shared_proof_retrieval.py"
        )
        if shared_retrieval.is_file():
            args.emperical_process_lean_rag_root = str(
                EXTERNAL_EMPIRICAL_PROCESS_LEAN_ROOT
            )

    lean_project_fields = ("formalizer_candidate_lean_project",)
    if lean_project:
        for field_name in lean_project_fields:
            if not str(getattr(args, field_name, "") or "").strip():
                setattr(args, field_name, lean_project)

    if preset == "full-live":
        args.architect_max_tokens = max(
            LIVE_EVALUATION_MIN_ARCHITECT_MAX_TOKENS,
            int(getattr(args, "architect_max_tokens", 0) or 0),
        )
        args.architect_metric_semantic_reviewer_max_tokens = max(
            LIVE_EVALUATION_MIN_METRIC_REVIEWER_MAX_TOKENS,
            int(
                getattr(
                    args,
                    "architect_metric_semantic_reviewer_max_tokens",
                    0,
                )
                or 0
            ),
        )
        args.llm_timeout_seconds = max(
            SERIOUS_THEORY_MIN_LLM_TIMEOUT_SECONDS,
            float(
                getattr(
                    args,
                    "llm_timeout_seconds",
                    DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
                )
                or DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS
            ),
        )
        if not str(
            getattr(args, "serious_theory_model_tier", "") or ""
        ).strip():
            args.serious_theory_model_tier = LIVE_EVALUATION_CLAUDE_MODEL_TIER
        if not hasattr(args, "serious_theory_llm_model"):
            args.serious_theory_llm_model = ""
        args.serious_theory_max_tokens = max(
            LIVE_EVALUATION_MIN_SERIOUS_THEORY_MAX_TOKENS,
            int(getattr(args, "serious_theory_max_tokens", 0) or 0),
        )
        args.formal_verification_policy = "required"
        args.formal_target_semantic_review_required = True
        args.max_iterations = max(
            FULL_LIVE_MIN_AGENT_RUNTIME_ITERATIONS,
            int(getattr(args, "max_iterations", 0) or 0),
        )
        args.architect_metric_protocol_max_upstream_theory_revisions = max(
            2,
            int(
                getattr(
                    args,
                    "architect_metric_protocol_max_upstream_theory_revisions",
                    0,
                )
                or 0
            ),
        )
        args.min_task_families = max(
            2,
            int(getattr(args, "min_task_families", 0) or 0),
        )
        args.formalizer_candidate_lean_lsp_mcp = True
        if not str(getattr(args, "openprover_root", "") or "").strip():
            discovered_openprover_root = _default_openprover_root()
            if discovered_openprover_root:
                args.openprover_root = discovered_openprover_root
        args.openprover_hlm = bool(
            str(getattr(args, "openprover_root", "") or "").strip()
        )
        args.generated_code_semantic_review_max_revisions = max(
            2,
            int(
                getattr(
                    args,
                    "generated_code_semantic_review_max_revisions",
                    0,
                )
                or 0
            ),
        )
        if (
            int(
                getattr(
                    args,
                    "formal_target_semantic_review_max_revisions",
                    0,
                )
                or 0
            )
            <= 0
        ):
            args.formal_target_semantic_review_max_revisions = 1


def _apply_research_agent_runtime_live_lean_defaults(
    args: argparse.Namespace,
) -> None:
    """Attach the canonical Lake project to live Formalizer/ProofEngineer checks.

    The default path supplies compiler/LSP feedback to the model-owned source
    loop. The canonical runtime has no bridge, planner, executor, or source-repair
    fallback outside that workspace.
    """

    if not _research_agent_runtime_formalizer_resolves_to_live_provider(args):
        return
    lean_project = str(getattr(args, "lean_project", "") or "").strip()
    if not lean_project:
        for default_lean_project in (
            _capability_eval_default_lean_project_candidates()
        ):
            if _is_lake_project(default_lean_project):
                lean_project = str(default_lean_project)
                args.lean_project = lean_project
                break
    if not lean_project:
        return
    if not str(getattr(args, "formalizer_candidate_lean_project", "") or "").strip():
        args.formalizer_candidate_lean_project = lean_project
    if not bool(getattr(args, "formalizer_candidate_lean_lsp_mcp", False)):
        args.formalizer_candidate_local_lean = True


def _research_agent_runtime_formalizer_resolves_to_live_provider(
    args: argparse.Namespace,
) -> bool:
    configured_provider = str(
        getattr(args, "formalizer_provider", "same") or "same"
    )
    main_provider = str(getattr(args, "provider", "") or "")
    resolved_provider = (
        main_provider if configured_provider == "same" else configured_provider
    )
    return resolved_provider in {"anthropic", "openai"}


def _effective_resume_through_architect(
    args: argparse.Namespace,
    *,
    architect_coordinator_configured: bool,
) -> bool:
    explicit = getattr(args, "resume_through_architect", None)
    if explicit is not None:
        return bool(explicit)
    return (
        bool(getattr(args, "capability_eval", False))
        and bool(str(getattr(args, "resume_runtime_manifest", "") or "").strip())
        and bool(architect_coordinator_configured)
    )


def _research_agent_runtime_static_subsystem_config_errors(
    args: argparse.Namespace,
) -> list[str]:
    errors: list[str] = []
    subsystem_static_files = (
        (
            "architect_coordinator_provider",
            "architect_static_response_file",
            "ArchitectCoordinator",
            "--architect-static-response-file",
        ),
        (
            "simulation_engineer_provider",
            "simulation_static_response_file",
            "SimulationEngineer",
            "--simulation-static-response-file",
        ),
        (
            "algorithm_engineer_provider",
            "algorithm_static_response_file",
            "AlgorithmEngineer",
            "--algorithm-static-response-file",
        ),
        (
            "formalizer_provider",
            "formalizer_static_response_file",
            "Formalizer/ProofEngineer",
            "--formalizer-static-response-file",
        ),
        (
            "critic_evaluator_provider",
            "critic_static_response_file",
            "CriticEvaluator",
            "--critic-static-response-file",
        ),
        (
            "generated_code_semantic_reviewer_provider",
            "generated_code_semantic_reviewer_static_response_file",
            "GeneratedCodeSemanticReviewer",
            "--generated-code-semantic-reviewer-static-response-file",
        ),
        (
            "formal_target_semantic_reviewer_provider",
            "formal_target_semantic_reviewer_static_response_file",
            "FormalTargetSemanticReviewer",
            "--formal-target-semantic-reviewer-static-response-file",
        ),
    )
    main_provider = str(getattr(args, "provider", "") or "")
    for provider_field, static_file_field, subsystem, flag in subsystem_static_files:
        configured_provider = str(getattr(args, provider_field, "none") or "none")
        if configured_provider == "none":
            continue
        resolved_provider = (
            main_provider if configured_provider == "same" else configured_provider
        )
        if resolved_provider != "static":
            continue
        if str(getattr(args, static_file_field, "") or "").strip():
            continue
        errors.append(
            f"{subsystem} resolves to static via --{provider_field.replace('_', '-')}="
            f"{configured_provider} but {flag} was not supplied; set "
            f"--{provider_field.replace('_', '-')} none to intentionally disable "
            "that subsystem in a partial debug replay"
        )
    return errors


def _capability_eval_default_lean_project_candidates() -> tuple[Path, ...]:
    from .research_source_inventory import (
        EXTERNAL_EMPIRICAL_PROCESS_LEAN_ROOT,
        VENDORED_EMPIRICAL_PROCESS_ROOT,
    )

    project_root = Path(__file__).resolve().parents[1]
    relative_vendored_project = Path("legacy_sources/emperical_process_lean")
    repo_vendored_project = project_root / relative_vendored_project
    candidates = (
        EXTERNAL_EMPIRICAL_PROCESS_LEAN_ROOT,
        relative_vendored_project,
        repo_vendored_project,
        VENDORED_EMPIRICAL_PROCESS_ROOT,
        Path.home() / "LeanProjects" / "LeanPractice",
    )
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return tuple(unique)




def _default_openprover_root() -> str:
    """Return a source-controlled OpenProver adapter checkout when available."""

    from .research_source_inventory import OPENPROVER_ROOT

    root = Path(OPENPROVER_ROOT).expanduser().resolve()
    required = (
        root / "src" / "openprover" / "lean_lsp_mcp.py",
        root / "src" / "openprover" / "controller.py",
    )
    return str(root) if all(path.is_file() for path in required) else ""


def _is_lake_project(path: Path) -> bool:
    return (
        path.exists()
        and path.is_dir()
        and (
            (path / "lakefile.lean").exists()
            or (path / "lakefile.toml").exists()
        )
    )


def _research_agent_runtime_local_lean_preflight_errors(
    args: argparse.Namespace,
) -> list[str]:
    """Fail before live provider calls when the strict Lean root is unbuilt."""

    if not bool(getattr(args, "capability_eval", False)):
        return []
    if not (
        bool(getattr(args, "local_lean", False))
        or bool(getattr(args, "formalizer_candidate_local_lean", False))
        or bool(getattr(args, "formalizer_candidate_lean_lsp_mcp", False))
    ):
        return []
    project_value = str(
        getattr(args, "formalizer_candidate_lean_project", "")
        or getattr(args, "lean_project", "")
        or ""
    ).strip()
    if not project_value:
        return []
    project = Path(project_value).expanduser().resolve()
    if not _is_lake_project(project):
        return [
            "capability eval local Lean preflight requires an existing Lake project; "
            f"invalid project: {project}"
        ]
    mathlib_roots = (
        project / ".lake" / "build" / "lib" / "lean" / "Mathlib.olean",
        project
        / ".lake"
        / "packages"
        / "mathlib"
        / ".lake"
        / "build"
        / "lib"
        / "lean"
        / "Mathlib.olean",
    )
    if not any(path.is_file() for path in mathlib_roots):
        return [
            "capability eval local Lean preflight found an unbuilt Mathlib root at "
            f"{project}; run `cd {project} && lake build Mathlib` before spending "
            "live LLM budget"
        ]
    formalizer_timeout = int(
        getattr(
            args,
            "formalizer_candidate_lean_timeout",
            DEFAULT_LEAN_TOOL_TIMEOUT_SECONDS,
        )
        or DEFAULT_LEAN_TOOL_TIMEOUT_SECONDS
    )
    return _lean_project_import_preflight_errors(
        project,
        timeout_seconds=max(30, formalizer_timeout),
    )


def _lean_project_import_preflight_errors(
    project: Path,
    *,
    timeout_seconds: int,
) -> list[str]:
    """Check the actual project import surface before any live model call."""

    from .formal_source_topology import (
        configured_formal_source_entry_modules,
    )

    configured_entries = configured_formal_source_entry_modules(
        "empirical_process_lean"
    )
    entry_sources = tuple(
        (
            module,
            project.joinpath(*module.split(".")).with_suffix(".lean"),
        )
        for module in configured_entries
        if project.joinpath(*module.split(".")).with_suffix(".lean").is_file()
    )

    def run_probe(module: str, probe: Path) -> list[str]:
        try:
            result = subprocess.run(
                ["lake", "env", "lean", str(probe)],
                cwd=project,
                check=False,
                capture_output=True,
                text=True,
                timeout=max(1, int(timeout_seconds)),
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return [
                "capability eval local Lean project-import preflight could not run "
                f"at {project}: {exc}"
            ]
        if result.returncode == 0:
            return []
        diagnostics = "\n".join(
            line
            for line in (result.stdout + "\n" + result.stderr).splitlines()[-12:]
            if line.strip()
        )
        return [
            "capability eval local Lean project-import preflight failed for "
            f"{module} at {project}; build the canonical project before spending "
            "live LLM budget. Lean diagnostics:\n"
            + (diagnostics or f"lake env lean exited with {result.returncode}")
        ]

    if entry_sources:
        errors: list[str] = []
        for module, source_path in entry_sources:
            errors.extend(run_probe(module, source_path))
        return errors

    with tempfile.TemporaryDirectory(
        prefix="ai-statistician-lean-preflight-"
    ) as temp_dir:
        probe = Path(temp_dir) / "Main.lean"
        probe.write_text("import Mathlib\n", encoding="utf-8")
        return run_probe("Mathlib", probe)


def _research_agent_runtime_capability_config_errors(
    args: argparse.Namespace,
) -> list[str]:
    errors: list[str] = []
    if getattr(args, "provider", "") not in {"anthropic", "openai"}:
        errors.append("capability eval requires --provider anthropic or --provider openai")
    subsystem_provider_fields = (
        ("architect_coordinator_provider", "ArchitectCoordinator"),
        ("simulation_engineer_provider", "SimulationEngineer"),
        ("algorithm_engineer_provider", "AlgorithmEngineer"),
        ("formalizer_provider", "Formalizer"),
        ("critic_evaluator_provider", "CriticEvaluator"),
        (
            "generated_code_semantic_reviewer_provider",
            "GeneratedCodeSemanticReviewer",
        ),
    )
    for field_name, subsystem in subsystem_provider_fields:
        provider_choice = str(getattr(args, field_name, "none") or "none")
        if provider_choice in {"none", "static"}:
            errors.append(
                f"capability eval requires live {subsystem}; "
                f"{field_name}={provider_choice}"
            )
    if bool(
        getattr(args, "formal_target_semantic_review_required", False)
    ) or str(getattr(args, "capability_eval_preset", "") or "") == "full-live":
        reviewer_provider = str(
            getattr(args, "formal_target_semantic_reviewer_provider", "none")
            or "none"
        )
        if reviewer_provider in {"none", "static"}:
            errors.append(
                "capability eval requires live FormalTargetSemanticReviewer; "
                "formal_target_semantic_reviewer_provider=" + reviewer_provider
            )
    if not (getattr(args, "local_lean", False) or getattr(args, "real_lean", False)):
        errors.append("capability eval requires --local-lean or --real-lean")
    if str(getattr(args, "recommended_research_path", "") or "").strip():
        errors.append(
            "capability eval must not use --recommended-research-path; "
            "manual path overrides are controlled-smoke/debug-only and cannot "
            "stand in for live Architect path selection"
        )
    proofengineer_required_flags = (
        (
            "formalizer_candidate_local_lean",
            "--formalizer-candidate-local-lean",
        ),
    )
    for field_name, flag in proofengineer_required_flags:
        if not bool(getattr(args, field_name, False)):
            errors.append(
                "capability eval requires the internal ProofEngineer proof path; "
                f"missing {flag}"
            )
    if (
        str(getattr(args, "capability_eval_preset", "") or "") == "full-live"
        and not bool(getattr(args, "formalizer_candidate_lean_lsp_mcp", False))
    ):
        errors.append(
            "capability eval preset full-live requires the live Lean LSP/MCP "
            "proof-state feedback path; missing "
            "--formalizer-candidate-lean-lsp-mcp"
        )
    if str(getattr(args, "capability_eval_preset", "") or "") == "full-live":
        serious_theory_model_tier = str(
            getattr(args, "serious_theory_model_tier", "") or ""
        ).strip().lower()
        required_serious_theory_model_tier = _runtime_effective_model_tier(
            args,
            "sonnet",
        )
        if serious_theory_model_tier != required_serious_theory_model_tier:
            errors.append(
                "capability eval preset full-live requires "
                f"{required_serious_theory_model_tier}-tier serious "
                "TheoryDeveloper workspaces under the active evaluation model "
                "policy; set --serious-theory-model-tier "
                f"{required_serious_theory_model_tier}"
            )
        serious_theory_max_tokens = int(
            getattr(args, "serious_theory_max_tokens", 0) or 0
        )
        if serious_theory_max_tokens < LIVE_EVALUATION_MIN_SERIOUS_THEORY_MAX_TOKENS:
            errors.append(
                "capability eval preset full-live requires a serious "
                "TheoryDeveloper output budget of at least "
                f"{LIVE_EVALUATION_MIN_SERIOUS_THEORY_MAX_TOKENS} tokens; set "
                "--serious-theory-max-tokens accordingly"
            )
        if not bool(getattr(args, "openprover_hlm", False)):
            errors.append(
                "capability eval preset full-live requires verifier-backed "
                "OpenProver whole-theorem search; missing --openprover-hlm "
                "or a discoverable --openprover-root"
            )
        if not str(getattr(args, "openprover_root", "") or "").strip():
            errors.append(
                "capability eval preset full-live requires --openprover-root "
                "so ProofEngineer can execute compiler-feedback proof search"
            )
        if (
            int(
                getattr(
                    args,
                    "generated_code_semantic_review_max_revisions",
                    0,
                )
                or 0
            )
            <= 0
        ):
            errors.append(
                "capability eval preset full-live requires bounded independent "
                "generated-code semantic-review revision; set "
                "--generated-code-semantic-review-max-revisions > 0"
            )
        if not bool(
            getattr(args, "formal_target_semantic_review_required", False)
        ):
            errors.append(
                "capability eval preset full-live requires independent whole-target "
                "semantic review before proof search; missing "
                "--formal-target-semantic-review-required"
            )
        if (
            int(
                getattr(
                    args,
                    "formal_target_semantic_review_max_revisions",
                    0,
                )
                or 0
            )
            <= 0
        ):
            errors.append(
                "capability eval preset full-live requires bounded formal-target "
                "semantic-review revision; set "
                "--formal-target-semantic-review-max-revisions > 0"
            )
    if (
        bool(getattr(args, "formalizer_candidate_local_lean", False))
        or bool(getattr(args, "formalizer_candidate_lean_lsp_mcp", False))
    ) and not (
        str(getattr(args, "formalizer_candidate_lean_project", "") or "").strip()
        or str(getattr(args, "lean_project", "") or "").strip()
    ):
        errors.append(
            "capability eval with --formalizer-candidate-local-lean requires "
            "--formalizer-candidate-lean-project or --lean-project so Mathlib/"
            "StatInference imports are available to the local Lean checker"
        )
    return errors


def _research_agent_runtime_audit(args: argparse.Namespace) -> int:
    payload = audit_research_agent_runtime(
        Path(args.runtime_dir),
        Path(args.out),
    )
    print("\nAI Statistician Agent Runtime Audit")
    print("=" * 72)
    scorecard = payload["capability_scorecard"]
    print(
        f"results={payload['n_ok']}/{payload['n_results']} "
        f"traces={payload['n_runtime_traces']} "
        f"observations={payload['n_runtime_observations']} "
        f"tool_calls={payload['n_runtime_tool_calls']}"
    )
    print(
        f"kernel_verified_subclaims={payload['n_kernel_verified_subclaims']} "
        "materialized_formal_gap_rows="
        f"{payload['n_materialized_formal_gap_rows']} "
        "formal_unverified_questions="
        f"{payload['formal_closure_summary'].get('n_questions_formal_unverified', 'unknown')} "
        f"full_frontier_theorem_proved={payload['n_full_frontier_theorem_proved']}"
    )
    print(
        f"capability_scorecard={scorecard['n_passed']}/"
        f"{scorecard['n_requirements']} "
        f"ready={payload['capability_ready_for_full_ai_statistician']}"
    )
    print(f"audit_integrity_ok={payload['all_ok']}")
    if payload["capability_gaps"]:
        print(f"missing_capabilities={','.join(payload['capability_gaps'])}")
    print(
        "runtime audit manifest written to "
        f"{(Path(args.out) / 'research_agent_runtime_audit_manifest.json').resolve()}"
    )
    return 0 if payload["capability_ready_for_full_ai_statistician"] else 1












def _architect_research_path_policy_eval(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    try:
        manifest = run_architect_research_path_policy_eval(
            out_dir=Path(args.out),
            provider_name=args.provider,
            model=args.llm_model,
            static_response_file=(
                Path(args.static_response_file)
                if args.static_response_file
                else None
            ),
            llm_timeout_seconds=args.llm_timeout_seconds,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
        )
    except Exception as exc:
        manifest = write_architect_research_path_policy_eval_failure_manifest(
            out_dir=Path(args.out),
            provider_name=args.provider,
            model=args.llm_model,
            exc=exc,
        )
        print("\nAI Statistician Architect Research-Path Policy Eval failed")
        print("=" * 72)
        print(f"- {exc}")
        print(f"manifest={manifest['artifacts']['manifest_json']}")
        return 1
    print("\nAI Statistician Architect Research-Path Policy Eval")
    print("=" * 72)
    print(f"provider={manifest['provider_name']} model={manifest['model']}")
    print(f"live_generator={manifest['live_generator']}")
    print(f"cases_ok={manifest['n_cases_ok']}/{manifest['n_cases']}")
    print(
        "long_horizon_fields="
        f"problem_analysis:{manifest['n_with_problem_analysis']} "
        f"knowledge_bank:{manifest['n_with_stat_knowledge_bank_plan']} "
        f"fair_comparison:{manifest['n_with_literature_fair_comparison_plan']}"
    )
    fixture_plumbing_ok = bool(
        manifest["static_or_fixture_only"] and manifest["all_cases_ok"]
    )
    print(f"fixture_plumbing_ok={fixture_plumbing_ok}")
    print(f"capability_evidence_ok={manifest['capability_evidence_ok']}")
    print(f"proof_evidence_status={manifest['proof_evidence_status']}")
    print(f"manifest={manifest['artifacts']['manifest_json']}")
    if manifest["capability_evidence_ok"]:
        return 0
    if args.allow_fixture_success and fixture_plumbing_ok:
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Statistician production core")
    sub = parser.add_subparsers(dest="cmd", required=True)

    demo = sub.add_parser("demo", help="run estimator + formal proof + simulation loop")
    demo.add_argument("--question", action="append", choices=sorted(QUESTIONS), help="run one built-in question; repeatable")
    demo.add_argument("--question-file", help="run one or more external questions from JSON")
    demo.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof instead of mock verifier")
    demo.add_argument("--llm-theory", action="store_true", help="allow a generator backend to classify supported estimator/DGP families during intake")
    demo.add_argument("--force-llm-theory", action="store_true", help="always ask the LLM for family classification")
    demo.add_argument("--llm-provider", choices=GENERATOR_PROVIDER_CHOICES, default=_default_live_generator_provider())
    demo.add_argument("--llm-static-response-file", default="", help="JSON response to replay when --llm-provider static is used")
    demo.add_argument("--llm-model", default="", help="model name for the intake generator; Anthropic defaults to Claude Haiku 4.5 for this light classifier")
    demo.add_argument("--llm-max-tokens", type=int, default=700)
    demo.add_argument("--runs", type=int, default=1000, help="Monte Carlo replicates")
    demo.add_argument("--seed", type=int, default=20260528)
    demo.add_argument("--out", default="runs/latest", help="trace output directory")
    demo.add_argument("--env-file", default=".env")
    demo.add_argument("--verbose", action="store_true")
    demo.set_defaults(func=lambda args: asyncio.run(_demo(args)))

    eval_cmd = sub.add_parser("eval", help="run multi-seed evaluation and write an aggregate manifest")
    eval_cmd.add_argument("--question", action="append", choices=sorted(QUESTIONS), help="run one built-in question; repeatable")
    eval_cmd.add_argument("--question-file", help="run one or more external questions from JSON")
    eval_cmd.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof instead of mock verifier")
    eval_cmd.add_argument("--llm-theory", action="store_true", help="allow a generator backend to classify supported estimator/DGP families during intake")
    eval_cmd.add_argument("--force-llm-theory", action="store_true", help="always ask the LLM for family classification")
    eval_cmd.add_argument("--llm-provider", choices=GENERATOR_PROVIDER_CHOICES, default=_default_live_generator_provider())
    eval_cmd.add_argument("--llm-static-response-file", default="", help="JSON response to replay when --llm-provider static is used")
    eval_cmd.add_argument("--llm-model", default="", help="model name for the intake generator; Anthropic defaults to Claude Haiku 4.5 for this light classifier")
    eval_cmd.add_argument("--llm-max-tokens", type=int, default=700)
    eval_cmd.add_argument("--runs", type=int, default=500, help="Monte Carlo replicates per trial")
    eval_cmd.add_argument("--n-seeds", type=int, default=3)
    eval_cmd.add_argument("--seed-start", type=int, default=20260528)
    eval_cmd.add_argument("--seeds", nargs="*", type=int, help="explicit seeds")
    eval_cmd.add_argument("--out", default="runs/eval", help="evaluation output directory")
    eval_cmd.add_argument("--env-file", default=".env")
    eval_cmd.set_defaults(func=lambda args: asyncio.run(_eval(args)))

    proof_audit = sub.add_parser("proof-audit", help="verify the reusable formal proof bank")
    proof_audit.add_argument("--id", action="append", help="specific obligation id; repeatable")
    proof_audit.add_argument("--tag", action="append", help="filter obligations by tag; repeatable")
    proof_audit.add_argument("--require-all-tags", action="store_true", help="require all provided tags instead of any")
    proof_audit.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof instead of mock verifier")
    proof_audit.add_argument("--local-lean", action="store_true", help="use local lake env lean kernel verification")
    proof_audit.add_argument("--lean-project", help="local Lake project used by --local-lean")
    proof_audit.add_argument("--lean-timeout", type=int, default=90, help="timeout seconds for each local Lean check")
    proof_audit.add_argument("--out", default="runs/proof_audit", help="proof audit output directory")
    proof_audit.add_argument("--env-file", default=".env")
    proof_audit.add_argument("--no-export-lean", action="store_true", help="do not export checked Lean candidates")
    proof_audit.add_argument("--no-attempt-log", action="store_true", help="do not write proof_attempts.jsonl training/audit data")
    proof_audit.add_argument(
        "--negative-controls",
        action="store_true",
        help="also verify one intentionally empty proof body per obligation for repair/value-model data",
    )
    proof_audit.set_defaults(func=lambda args: asyncio.run(_proof_audit(args)))


    proof_training_export = sub.add_parser(
        "proof-training-export",
        help="export verifier-positive proof attempts as whole-proof SFT JSONL data",
    )
    proof_training_export.add_argument(
        "--attempt-log",
        required=True,
        help="path to proof_attempts.jsonl from proof-audit",
    )
    proof_training_export.add_argument(
        "--validation-fraction",
        type=float,
        default=0.2,
        help="deterministic validation split fraction in [0, 1)",
    )
    proof_training_export.add_argument(
        "--out",
        default="runs/proof_training_export",
        help="output directory for proof_sft_*.jsonl and manifest",
    )
    proof_training_export.set_defaults(func=_proof_training_export)


    proof_policy_baseline = sub.add_parser(
        "proof-policy-baseline",
        help="evaluate a nearest-neighbor whole-proof policy over exported SFT data",
    )
    proof_policy_baseline.add_argument("--train-jsonl", required=True, help="proof_sft_train.jsonl")
    proof_policy_baseline.add_argument("--validation-jsonl", required=True, help="proof_sft_validation.jsonl")
    proof_policy_baseline.add_argument("--k", type=int, default=5, help="top-k proof-memory candidates")
    proof_policy_baseline.add_argument(
        "--out",
        default="runs/proof_policy_baseline",
        help="output directory for baseline predictions and manifest",
    )
    proof_policy_baseline.set_defaults(func=_proof_policy_baseline)

    proof_policy_train = sub.add_parser(
        "proof-policy-train",
        help="train a small whole-proof candidate ranking policy from proof SFT examples",
    )
    proof_policy_train.add_argument("--train-jsonl", required=True, help="proof_sft_train.jsonl")
    proof_policy_train.add_argument(
        "--validation-jsonl",
        default="",
        help="optional proof_sft_validation.jsonl; defaults to train set",
    )
    proof_policy_train.add_argument("--k", type=int, default=5)
    proof_policy_train.add_argument("--epochs", type=int, default=80)
    proof_policy_train.add_argument("--learning-rate", type=float, default=0.1)
    proof_policy_train.add_argument("--l2", type=float, default=0.001)
    proof_policy_train.add_argument("--negatives-per-query", type=int, default=8)
    proof_policy_train.add_argument(
        "--out",
        default="runs/proof_policy_model",
        help="output directory for proof_policy_model.json and predictions",
    )
    proof_policy_train.set_defaults(func=_proof_policy_train)

    proof_search_audit = sub.add_parser(
        "proof-search-audit",
        help="audit the bounded best-first whole-proof search controller",
    )
    proof_search_audit.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof")
    proof_search_audit.add_argument("--local-lean", action="store_true", help="use local Lean kernel verifier")
    proof_search_audit.add_argument("--local-lean-project", default=None)
    proof_search_audit.add_argument("--local-lean-timeout", type=int, default=90)
    proof_search_audit.add_argument(
        "--max-obligations",
        type=int,
        default=12,
        help="number of proof-bank obligations to search",
    )
    proof_search_audit.add_argument("--max-nodes", type=int, default=8, help="candidate nodes per obligation")
    proof_search_audit.add_argument(
        "--include-invalid-probe",
        action="store_true",
        help="put one invalid high-priority candidate before the registered proof to test branch/error logging",
    )
    proof_search_audit.add_argument(
        "--legacy-static-template-baseline",
        action="store_true",
        help=(
            "explicit calibration only: enable historical Python-generated tactic "
            "and formal-source proof templates; disabled by default and never "
            "attributed to the LLM coding-agent runtime"
        ),
    )
    proof_search_audit.add_argument(
        "--no-registered-proof",
        action="store_true",
        help="exclude gold registered proof bodies for a harder retrieval/search diagnostic",
    )
    proof_search_audit.add_argument(
        "--policy-model-json",
        default=None,
        help="optional proof_policy_model.json used to score and rerank candidate proof bodies",
    )
    proof_search_audit.add_argument(
        "--value-model-json",
        default=None,
        help="optional proof_search_value_model.json used to score and rerank candidate proof bodies",
    )
    proof_search_audit.add_argument(
        "--out",
        default="runs/proof_search_audit",
        help="output directory for proof_search_results.jsonl and manifest",
    )
    proof_search_audit.set_defaults(func=lambda args: asyncio.run(_proof_search_audit(args)))

    proof_search_kernel_rerun_queue = sub.add_parser(
        "proof-search-kernel-rerun-queue",
        help="queue mock/static proof-search solutions for AXLE/local Lean replay",
    )
    proof_search_kernel_rerun_queue.add_argument(
        "--proof-search-audit-dir",
        required=True,
        help="directory containing proof_search_audit_manifest.json and proof_search_results.jsonl",
    )
    proof_search_kernel_rerun_queue.add_argument(
        "--local-lean-project",
        default=None,
        help="optional local Lake project for the generated local Lean replay command",
    )
    proof_search_kernel_rerun_queue.add_argument("--local-lean-timeout", type=int, default=90)
    proof_search_kernel_rerun_queue.add_argument("--max-rows", type=int, default=50)
    proof_search_kernel_rerun_queue.add_argument(
        "--out",
        default="runs/proof_search_kernel_rerun_queue",
        help="proof-search kernel rerun queue output directory",
    )
    proof_search_kernel_rerun_queue.set_defaults(func=_proof_search_kernel_rerun_queue)

    proof_search_training_export = sub.add_parser(
        "proof-search-training-export",
        help="export proof-search expanded nodes as process-reward/value-model training examples",
    )
    proof_search_training_export.add_argument(
        "--results-jsonl",
        required=True,
        help="proof_search_results.jsonl from proof-search-audit",
    )
    proof_search_training_export.add_argument("--validation-fraction", type=float, default=0.2)
    proof_search_training_export.add_argument(
        "--out",
        default="runs/proof_search_training_export",
        help="output directory for proof_search_process_*.jsonl and manifest",
    )
    proof_search_training_export.set_defaults(func=_proof_search_training_export)

    proof_search_value_train = sub.add_parser(
        "proof-search-value-train",
        help="train a small logistic value baseline from proof-search process examples",
    )
    proof_search_value_train.add_argument(
        "--train-jsonl",
        required=True,
        help="proof_search_process_train.jsonl",
    )
    proof_search_value_train.add_argument(
        "--validation-jsonl",
        default="",
        help="optional proof_search_process_validation.jsonl; defaults to train set",
    )
    proof_search_value_train.add_argument("--epochs", type=int, default=200)
    proof_search_value_train.add_argument("--learning-rate", type=float, default=0.2)
    proof_search_value_train.add_argument("--l2", type=float, default=0.001)
    proof_search_value_train.add_argument(
        "--out",
        default="runs/proof_search_value_model",
        help="output directory for value model and prediction manifests",
    )
    proof_search_value_train.set_defaults(func=_proof_search_value_train)

    algorithm_audit = sub.add_parser("algorithm-audit", help="audit vetted algorithm implementations")
    algorithm_audit.add_argument("--out", default="runs/algorithm_audit", help="algorithm audit output directory")
    algorithm_audit.set_defaults(func=_algorithm_audit)

    research_algorithm_audit = sub.add_parser(
        "research-algorithm-audit",
        help="audit AI Statistical Theory Lab research procedure implementations",
    )
    research_algorithm_audit.add_argument(
        "--out",
        default="runs/research_algorithm_audit",
        help="research algorithm audit output directory",
    )
    research_algorithm_audit.set_defaults(func=_research_algorithm_audit)

    research_intake_audit = sub.add_parser(
        "research-intake-audit",
        help="audit paper-style research-question normalization and unsupported-topic rejection",
    )
    research_intake_audit.add_argument(
        "--supported-file",
        action="append",
        help="supported research question file; repeatable",
    )
    research_intake_audit.add_argument(
        "--unsupported-file",
        action="append",
        help="unsupported research question file; repeatable",
    )
    research_intake_audit.add_argument(
        "--out",
        default="runs/research_intake_audit",
        help="research intake audit output directory",
    )
    research_intake_audit.set_defaults(func=_research_intake_audit)

    research_knowledge_audit = sub.add_parser(
        "research-knowledge-audit",
        help="audit problem-aware research knowledge retrieval and source locations",
    )
    research_knowledge_audit.add_argument(
        "--question-file",
        default="examples/research_questions.json",
        help="supported research question file used for problem-aware retrieval checks",
    )
    research_knowledge_audit.add_argument(
        "--out",
        default="runs/research_knowledge_audit",
        help="research knowledge audit output directory",
    )
    research_knowledge_audit.set_defaults(func=_research_knowledge_audit)

    lean_blueprint_knowledge = sub.add_parser(
        "lean-blueprint-knowledge",
        help="export LeanBlueprint knowledge and visualization adapter artifacts",
    )
    lean_blueprint_knowledge.add_argument(
        "--blueprint-root",
        default="",
        help="optional local PatrickMassot/leanblueprint checkout; defaults to ~/.codex/external/leanblueprint",
    )
    lean_blueprint_knowledge.add_argument(
        "--out",
        default="runs/lean_blueprint_knowledge",
        help="LeanBlueprint knowledge output directory",
    )
    lean_blueprint_knowledge.set_defaults(func=_lean_blueprint_knowledge)

    frontier_coverage_audit = sub.add_parser(
        "frontier-coverage-audit",
        help="parse the frontier paper benchmark and report deterministic research-lab coverage",
    )
    frontier_coverage_audit.add_argument(
        "--benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    frontier_coverage_audit.add_argument(
        "--out",
        default="runs/frontier_coverage_audit",
        help="frontier coverage audit output directory",
    )
    frontier_coverage_audit.set_defaults(func=_frontier_coverage_audit)

    frontier_precision_audit = sub.add_parser(
        "frontier-precision-audit",
        help="validate that supported frontier classifications have direct body-text evidence",
    )
    frontier_precision_audit.add_argument(
        "--benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    frontier_precision_audit.add_argument(
        "--out",
        default="runs/frontier_precision_audit",
        help="frontier precision audit output directory",
    )
    frontier_precision_audit.set_defaults(func=_frontier_precision_audit)

    frontier_backlog_audit = sub.add_parser(
        "frontier-backlog-audit",
        help="cluster unsupported frontier benchmark rows into future theory-roadmap domains",
    )
    frontier_backlog_audit.add_argument(
        "--benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    frontier_backlog_audit.add_argument(
        "--out",
        default="runs/frontier_backlog_audit",
        help="frontier unsupported-theory backlog output directory",
    )
    frontier_backlog_audit.set_defaults(func=_frontier_backlog_audit)

    frontier_theory_target_audit = sub.add_parser(
        "frontier-theory-target-audit",
        help="score generated frontier traces against withheld expected theoretical results",
    )
    frontier_theory_target_audit.add_argument(
        "--run-dir",
        required=True,
        help="research_benchmark directory containing generated frontier trace JSON files",
    )
    frontier_theory_target_audit.add_argument(
        "--benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    frontier_theory_target_audit.add_argument(
        "--coverage-threshold",
        type=float,
        default=0.18,
        help="token-coverage threshold for marking one expected result as covered",
    )
    frontier_theory_target_audit.add_argument(
        "--out",
        default="runs/frontier_theory_target_audit",
        help="frontier theory target audit output directory",
    )
    frontier_theory_target_audit.set_defaults(func=_frontier_theory_target_audit)

    frontier_dap_prompt_packets = sub.add_parser(
        "frontier-discover-and-prove-prompt-packets",
        help="export DAP-style hard-mode frontier discovery and hard-to-easy rewrite prompt packets",
    )
    frontier_dap_prompt_packets.add_argument(
        "--benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    frontier_dap_prompt_packets.add_argument(
        "--max-packets",
        type=int,
        default=60,
        help="maximum hard-mode frontier rows to export",
    )
    frontier_dap_prompt_packets.add_argument(
        "--out",
        default="runs/frontier_discover_and_prove_prompt_packets",
        help="frontier DAP prompt packet output directory",
    )
    frontier_dap_prompt_packets.set_defaults(
        func=_frontier_discover_and_prove_prompt_packets
    )

    paper_theory_roundtrip = sub.add_parser(
        "paper-theory-roundtrip",
        help="extract TeX paper statements and queue Lean realization plus Lean-to-LaTeX review work",
    )
    paper_theory_roundtrip.add_argument(
        "--paper-root",
        default="examples/paper_theory_roundtrip_sample.tex",
        help="paper .tex file or directory containing arXiv LaTeX source",
    )
    paper_theory_roundtrip.add_argument(
        "--paper-id",
        default="",
        help="optional stable paper id for emitted statement ids",
    )
    paper_theory_roundtrip.add_argument("--max-statements", type=int, default=200)
    paper_theory_roundtrip.add_argument(
        "--out",
        default="runs/paper_theory_roundtrip",
        help="paper theory round-trip output directory",
    )
    paper_theory_roundtrip.set_defaults(func=_paper_theory_roundtrip)

    frontier_evaluation_triage = sub.add_parser(
        "frontier-evaluation-triage",
        help="turn frontier theory-target misses and simulation flags into owner-routed work items",
    )
    frontier_evaluation_triage.add_argument(
        "--run-dir",
        required=True,
        help="research_benchmark directory containing generated frontier trace JSON files",
    )
    frontier_evaluation_triage.add_argument(
        "--theory-target-manifest",
        required=True,
        help="frontier_theory_target_manifest.json produced by frontier-theory-target-audit",
    )
    frontier_evaluation_triage.add_argument(
        "--out",
        default="runs/frontier_evaluation_triage",
        help="frontier evaluation triage output directory",
    )
    frontier_evaluation_triage.set_defaults(func=_frontier_evaluation_triage)

    frontier_simulation_rerun_audit = sub.add_parser(
        "frontier-simulation-rerun-audit",
        help="rerun simulator-agent frontier triage items with a larger Monte Carlo budget",
    )
    frontier_simulation_rerun_audit.add_argument(
        "--triage-manifest",
        required=True,
        help="frontier_evaluation_triage_manifest.json containing simulator-agent items",
    )
    frontier_simulation_rerun_audit.add_argument("--runs", type=int, default=60)
    frontier_simulation_rerun_audit.add_argument("--seed", type=int, default=20260531)
    frontier_simulation_rerun_audit.add_argument(
        "--out",
        default="runs/frontier_simulation_rerun",
        help="frontier simulation rerun output directory",
    )
    frontier_simulation_rerun_audit.set_defaults(func=_frontier_simulation_rerun_audit)

    frontier_theory_revision_queue = sub.add_parser(
        "frontier-theory-revision-queue",
        help="export scoped TheoryDeveloper tasks for still-flagged frontier simulation reruns",
    )
    frontier_theory_revision_queue.add_argument(
        "--simulation-rerun-manifest",
        required=True,
        help="frontier_simulation_rerun_manifest.json produced by frontier-simulation-rerun-audit",
    )
    frontier_theory_revision_queue.add_argument(
        "--out",
        default="runs/frontier_theory_revision_queue",
        help="frontier theory revision queue output directory",
    )
    frontier_theory_revision_queue.set_defaults(func=_frontier_theory_revision_queue)

    frontier_theory_revision_formalization = sub.add_parser(
        "frontier-theory-revision-formalization-audit",
        help="ground frontier theory-revision obligations in proof-bank and Lean-source retrieval",
    )
    frontier_theory_revision_formalization.add_argument(
        "--revision-queue-manifest",
        required=True,
        help="frontier_theory_revision_queue_manifest.json produced by frontier-theory-revision-queue",
    )
    frontier_theory_revision_formalization.add_argument(
        "--formal-source-index",
        default="",
        help="optional existing formal_source_index.sqlite; defaults to an index under --out",
    )
    frontier_theory_revision_formalization.add_argument("--k", type=int, default=5)
    frontier_theory_revision_formalization.add_argument(
        "--out",
        default="runs/frontier_theory_revision_formalization",
        help="frontier theory-revision formalization audit output directory",
    )
    frontier_theory_revision_formalization.set_defaults(func=_frontier_theory_revision_formalization_audit)

    frontier_smoke_benchmark = sub.add_parser(
        "frontier-smoke-benchmark",
        help="run full research traces on selected supported entries from the frontier paper benchmark",
    )
    frontier_smoke_benchmark.add_argument(
        "--benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    frontier_smoke_benchmark.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof for Mathlib-backed subclaims")
    frontier_smoke_benchmark.add_argument("--local-lean", action="store_true", help="use local lake env lean kernel verification")
    frontier_smoke_benchmark.add_argument("--lean-project", help="local Lake project used by --local-lean")
    frontier_smoke_benchmark.add_argument("--lean-timeout", type=int, default=90, help="timeout seconds for each local Lean check")
    frontier_smoke_benchmark.add_argument("--runs", type=int, default=60, help="Monte Carlo replicates for each selected paper-style question")
    frontier_smoke_benchmark.add_argument(
        "--simulation-rerun-runs",
        type=int,
        default=60,
        help="Monte Carlo replicates for simulator-agent reruns of flagged frontier triage items",
    )
    frontier_smoke_benchmark.add_argument("--seed", type=int, default=20260528)
    frontier_smoke_benchmark.add_argument(
        "--max-per-class",
        type=int,
        default=1,
        help="maximum selected questions per formalized problem class; use 0 to score all supported frontier entries",
    )
    frontier_smoke_benchmark.add_argument(
        "--frontier-smoke-cache",
        default="",
        help="optional persistent cache directory for selected frontier smoke traces; empty disables",
    )
    frontier_smoke_benchmark.add_argument(
        "--refresh-frontier-smoke-cache",
        action="store_true",
        help="rebuild the selected frontier smoke trace cache entry",
    )
    frontier_smoke_benchmark.add_argument("--out", default="runs/frontier_smoke_benchmark", help="frontier smoke output directory")
    frontier_smoke_benchmark.add_argument("--env-file", default=".env")
    frontier_smoke_benchmark.set_defaults(func=lambda args: asyncio.run(_frontier_smoke_benchmark(args)))

    retrieval_audit = sub.add_parser("retrieval-audit", help="audit proof-bank premise retrieval")
    retrieval_audit.add_argument("--k", type=int, default=5, help="top-k threshold")
    retrieval_audit.add_argument("--loogle", action="store_true", help="also record optional Loogle search evidence")
    retrieval_audit.add_argument("--loogle-k", type=int, default=10, help="number of Loogle declarations to keep per query")
    retrieval_audit.add_argument("--loogle-timeout", type=float, default=8.0, help="seconds before a Loogle query is recorded as an error")
    retrieval_audit.add_argument("--out", default="runs/retrieval_audit", help="retrieval audit output directory")
    retrieval_audit.set_defaults(func=_retrieval_audit)

    formal_source_audit = sub.add_parser(
        "formal-source-audit",
        help="index local Lean formal sources and audit theorem-mining queries",
    )
    formal_source_audit.add_argument("--k", type=int, default=8, help="number of declarations to keep per query")
    formal_source_audit.add_argument(
        "--backend",
        choices=("sqlite", "memory"),
        default="sqlite",
        help="retrieval backend for theorem-mining queries",
    )
    formal_source_audit.add_argument(
        "--out",
        default="runs/formal_source_index",
        help="formal source index output directory",
    )
    formal_source_audit.set_defaults(func=_formal_source_audit)

    formal_source_graph_audit = sub.add_parser(
        "formal-source-graph-audit",
        help="audit graph expansion over local Lean/stat declaration symbols",
    )
    formal_source_graph_audit.add_argument("--k", type=int, default=8, help="number of graph-expanded declarations to keep per query")
    formal_source_graph_audit.add_argument(
        "--formal-source-graph-cache",
        default="",
        help="optional persistent cache directory for formal-source graph audits; empty disables",
    )
    formal_source_graph_audit.add_argument(
        "--refresh-formal-source-graph-cache",
        action="store_true",
        help="rebuild the matching formal-source graph cache entry",
    )
    formal_source_graph_audit.add_argument(
        "--out",
        default="runs/formal_source_graph",
        help="formal source graph output directory",
    )
    formal_source_graph_audit.set_defaults(func=_formal_source_graph_audit)

    lean_rag_package_audit = sub.add_parser(
        "lean-rag-package-audit",
        help="audit the shared EmpericalProcessLEAN/lean_rag package contract",
    )
    lean_rag_package_audit.add_argument(
        "--package-root",
        default="",
        help="optional path to the lean_rag package root; auto-discovered when omitted",
    )
    lean_rag_package_audit.add_argument(
        "--db-dir",
        default="",
        help="optional shared_proof_retrieval build/lean_graph directory to inspect",
    )
    lean_rag_package_audit.add_argument(
        "--out",
        default="runs/lean_rag_package_audit",
        help="lean RAG package audit output directory",
    )
    lean_rag_package_audit.set_defaults(func=_lean_rag_package_audit)

    lean_rag_source_registry_expansion = sub.add_parser(
        "lean-rag-source-registry-expansion",
        help="stage source_registry.json additions from Lean RAG target-source candidates",
    )
    lean_rag_source_registry_expansion.add_argument(
        "--package-root",
        default="",
        help="optional path to the lean_rag package root; auto-discovered when omitted",
    )
    lean_rag_source_registry_expansion.add_argument(
        "--db-dir",
        default="",
        help="optional shared_proof_retrieval build/lean_graph directory to inspect",
    )
    lean_rag_source_registry_expansion.add_argument(
        "--out",
        default="runs/lean_rag_source_registry_expansion",
        help="source registry expansion output directory",
    )
    lean_rag_source_registry_expansion.set_defaults(func=_lean_rag_source_registry_expansion)

    lean_rag_source_registry_expansion_preflight = sub.add_parser(
        "lean-rag-source-registry-expansion-preflight",
        help="check local readiness for a staged Lean RAG source registry expansion",
    )
    lean_rag_source_registry_expansion_preflight.add_argument(
        "--expansion-manifest",
        required=True,
        help="path to source_registry_expansion_manifest.json",
    )
    lean_rag_source_registry_expansion_preflight.add_argument(
        "--out",
        default="runs/lean_rag_source_registry_expansion_preflight",
        help="source registry expansion preflight output directory",
    )
    lean_rag_source_registry_expansion_preflight.set_defaults(
        func=_lean_rag_source_registry_expansion_preflight
    )

    lean_rag_source_registry_expansion_apply = sub.add_parser(
        "lean-rag-source-registry-expansion-apply",
        help="dry-run or apply a reviewed staged Lean RAG source registry expansion",
    )
    lean_rag_source_registry_expansion_apply.add_argument(
        "--expansion-manifest",
        required=True,
        help="path to source_registry_expansion_manifest.json",
    )
    lean_rag_source_registry_expansion_apply.add_argument(
        "--preflight-manifest",
        default="",
        help="optional source_registry_expansion_preflight_manifest.json to enforce",
    )
    lean_rag_source_registry_expansion_apply.add_argument(
        "--apply",
        action="store_true",
        help="mutate source_registry.json after all safety gates pass; omitted means dry-run",
    )
    lean_rag_source_registry_expansion_apply.add_argument(
        "--out",
        default="runs/lean_rag_source_registry_expansion_apply",
        help="source registry expansion apply output directory",
    )
    lean_rag_source_registry_expansion_apply.set_defaults(
        func=_lean_rag_source_registry_expansion_apply
    )

    huggingface_lean_source_audit = sub.add_parser(
        "huggingface-lean-source-audit",
        help="discover and rank Hugging Face Lean corpora for local RAG/training reuse",
    )
    huggingface_lean_source_audit.add_argument(
        "--max-results-per-query",
        type=int,
        default=100,
        help="maximum Hugging Face dataset search results per Lean-related query",
    )
    huggingface_lean_source_audit.add_argument(
        "--max-detail-fetches",
        type=int,
        default=140,
        help="maximum dataset detail API calls after search and pinned-source discovery",
    )
    huggingface_lean_source_audit.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="per-request Hugging Face API timeout in seconds",
    )
    huggingface_lean_source_audit.add_argument(
        "--no-network",
        action="store_true",
        help="only use built-in pinned metadata; mainly for smoke tests",
    )
    huggingface_lean_source_audit.add_argument(
        "--out",
        default="runs/huggingface_lean_source_audit",
        help="Hugging Face Lean source audit output directory",
    )
    huggingface_lean_source_audit.set_defaults(func=_huggingface_lean_source_audit)

    huggingface_lean_source_revalidation_tasks = sub.add_parser(
        "huggingface-lean-source-revalidation-tasks",
        help="export worker task packets from the Hugging Face Lean source revalidation queue",
    )
    huggingface_lean_source_revalidation_tasks.add_argument(
        "--queue-jsonl",
        default="runs/huggingface_lean_source_audit/huggingface_lean_source_revalidation_queue.jsonl",
        help="Hugging Face Lean source revalidation queue JSONL",
    )
    huggingface_lean_source_revalidation_tasks.add_argument(
        "--max-tasks",
        type=int,
        default=20,
        help="maximum source revalidation task packets to export",
    )
    huggingface_lean_source_revalidation_tasks.add_argument(
        "--sample-seed",
        type=int,
        default=20260605,
        help="deterministic sample seed recorded in task packets",
    )
    huggingface_lean_source_revalidation_tasks.add_argument(
        "--out",
        default="runs/huggingface_lean_source_revalidation_tasks",
        help="Hugging Face Lean source revalidation task output directory",
    )
    huggingface_lean_source_revalidation_tasks.set_defaults(
        func=_huggingface_lean_source_revalidation_tasks
    )

    huggingface_lean_source_revalidation_prompt_packets = sub.add_parser(
        "huggingface-lean-source-revalidation-prompt-packets",
        help="export worker prompt packets and response contracts for Hugging Face Lean source revalidation",
    )
    huggingface_lean_source_revalidation_prompt_packets.add_argument(
        "--task-dir",
        default="runs/huggingface_lean_source_revalidation_tasks",
        help="directory containing hf_lean_source_revalidation_tasks_manifest.json",
    )
    huggingface_lean_source_revalidation_prompt_packets.add_argument(
        "--max-packets",
        type=int,
        default=20,
        help="maximum source revalidation prompt packets to export",
    )
    huggingface_lean_source_revalidation_prompt_packets.add_argument(
        "--out",
        default="runs/huggingface_lean_source_revalidation_prompt_packets",
        help="Hugging Face Lean source revalidation prompt packet output directory",
    )
    huggingface_lean_source_revalidation_prompt_packets.set_defaults(
        func=_huggingface_lean_source_revalidation_prompt_packets
    )

    huggingface_lean_source_revalidation_artifact_validation = sub.add_parser(
        "huggingface-lean-source-revalidation-artifact-validation",
        help="validate worker outputs for Hugging Face Lean source revalidation task packets",
    )
    huggingface_lean_source_revalidation_artifact_validation.add_argument(
        "--task-dir",
        default="runs/huggingface_lean_source_revalidation_tasks",
        help="directory containing hf_lean_source_revalidation_tasks_manifest.json",
    )
    huggingface_lean_source_revalidation_artifact_validation.add_argument(
        "--response-jsonl",
        default="",
        help="optional worker output JSONL; default is task-dir/hf_lean_source_revalidation_worker_outputs.jsonl",
    )
    huggingface_lean_source_revalidation_artifact_validation.add_argument(
        "--out",
        default="runs/huggingface_lean_source_revalidation_artifact_validation",
        help="Hugging Face Lean source revalidation artifact validation output directory",
    )
    huggingface_lean_source_revalidation_artifact_validation.set_defaults(
        func=_huggingface_lean_source_revalidation_artifact_validation
    )

    huggingface_lean_source_revalidation_promotion_queue = sub.add_parser(
        "huggingface-lean-source-revalidation-promotion-queue",
        help="export promotion-review rows from validated Hugging Face Lean source artifacts",
    )
    huggingface_lean_source_revalidation_promotion_queue.add_argument(
        "--artifact-validation-dir",
        default="runs/huggingface_lean_source_revalidation_artifact_validation",
        help="directory containing hf_lean_source_revalidation_artifact_validation_manifest.json",
    )
    huggingface_lean_source_revalidation_promotion_queue.add_argument(
        "--out",
        default="runs/huggingface_lean_source_revalidation_promotion_queue",
        help="Hugging Face Lean source promotion queue output directory",
    )
    huggingface_lean_source_revalidation_promotion_queue.set_defaults(
        func=_huggingface_lean_source_revalidation_promotion_queue
    )

    lean_rag_dependency_health = sub.add_parser(
        "lean-rag-dependency-health",
        help="validate an optional EmpericalProcessLEAN lean_rag dependency graph SQLite DB",
    )
    lean_rag_dependency_health.add_argument(
        "--db",
        default="",
        help="requested lean_rag dependency graph SQLite DB path",
    )
    lean_rag_dependency_health.add_argument(
        "--active-db",
        default="",
        help="active DB path actually attached by the search backend, if any",
    )
    lean_rag_dependency_health.add_argument(
        "--auto-discovered",
        action="store_true",
        help="mark the active DB as auto-discovered rather than explicitly requested",
    )
    lean_rag_dependency_health.add_argument(
        "--out",
        default="runs/lean_rag_dependency_health",
        help="lean RAG dependency health output directory",
    )
    lean_rag_dependency_health.set_defaults(func=_lean_rag_dependency_health)

    formal_source_retrieval_benchmark = sub.add_parser(
        "formal-source-retrieval-benchmark",
        help="measure gold-family retrieval recall over default, external, or combined Lean source suites",
    )
    formal_source_retrieval_benchmark.add_argument(
        "--suite",
        choices=("default", "external", "all"),
        default="default",
        help="benchmark suite to run",
    )
    formal_source_retrieval_benchmark.add_argument("--k", type=int, default=8)
    formal_source_retrieval_benchmark.add_argument(
        "--formal-source-index",
        default="runs/formal_source_retrieval_benchmark/formal_source_index.sqlite",
        help="SQLite index path for this benchmark run",
    )
    formal_source_retrieval_benchmark.add_argument(
        "--formal-source-index-cache",
        default="runs/formal_source_index_cache/formal_source_index.sqlite",
        help="persistent SQLite cache; pass empty string to disable",
    )
    formal_source_retrieval_benchmark.add_argument(
        "--refresh-formal-source-index-cache",
        action="store_true",
        help="rebuild and overwrite the persistent formal-source index cache",
    )
    formal_source_retrieval_benchmark.add_argument(
        "--lean-rag-db",
        default=None,
        help="optional EmpericalProcessLEAN lean_rag dependency graph SQLite DB",
    )
    formal_source_retrieval_benchmark.add_argument(
        "--out",
        default="runs/formal_source_retrieval_benchmark",
        help="formal-source retrieval benchmark output directory",
    )
    formal_source_retrieval_benchmark.set_defaults(func=_formal_source_retrieval_benchmark)

    formal_source_retrieval_ablation = sub.add_parser(
        "formal-source-retrieval-ablation",
        help="compare formal-source retrieval with and without the Lean RAG dependency graph provider",
    )
    formal_source_retrieval_ablation.add_argument(
        "--suite",
        choices=("default", "external", "all"),
        default="default",
        help="benchmark suite to include before dependency-sensitive Lean RAG probes",
    )
    formal_source_retrieval_ablation.add_argument("--k", type=int, default=8)
    formal_source_retrieval_ablation.add_argument(
        "--formal-source-index",
        default="runs/formal_source_retrieval_ablation/formal_source_index.sqlite",
        help="SQLite index path for this ablation run",
    )
    formal_source_retrieval_ablation.add_argument(
        "--formal-source-index-cache",
        default="runs/formal_source_index_cache/formal_source_index.sqlite",
        help="persistent SQLite cache; pass empty string to disable",
    )
    formal_source_retrieval_ablation.add_argument(
        "--refresh-formal-source-index-cache",
        action="store_true",
        help="rebuild and overwrite the persistent formal-source index cache",
    )
    formal_source_retrieval_ablation.add_argument(
        "--lean-rag-db",
        default=None,
        help="optional EmpericalProcessLEAN lean_rag dependency graph SQLite DB",
    )
    formal_source_retrieval_ablation.add_argument(
        "--out",
        default="runs/formal_source_retrieval_ablation",
        help="formal-source retrieval ablation output directory",
    )
    formal_source_retrieval_ablation.set_defaults(func=_formal_source_retrieval_ablation)

    proof_search_retrieval_ablation = sub.add_parser(
        "proof-search-retrieval-ablation",
        help="compare bounded proof-search behavior with and without the Lean RAG dependency graph provider",
    )
    proof_search_retrieval_ablation.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof")
    proof_search_retrieval_ablation.add_argument("--local-lean", action="store_true", help="use local Lean kernel verifier")
    proof_search_retrieval_ablation.add_argument("--lean-project", default=None)
    proof_search_retrieval_ablation.add_argument("--lean-timeout", type=int, default=90)
    proof_search_retrieval_ablation.add_argument("--max-obligations", type=int, default=6)
    proof_search_retrieval_ablation.add_argument("--max-nodes", type=int, default=4)
    proof_search_retrieval_ablation.add_argument("--formal-source-k", type=int, default=4)
    proof_search_retrieval_ablation.add_argument(
        "--no-registered-proof",
        action="store_true",
        help="exclude gold registered proof bodies to measure RAG/search lift under a harder diagnostic",
    )
    proof_search_retrieval_ablation.add_argument(
        "--formal-source-index",
        default="runs/proof_search_retrieval_ablation/formal_source_index.sqlite",
        help="SQLite index path for this ablation run",
    )
    proof_search_retrieval_ablation.add_argument(
        "--formal-source-index-cache",
        default="runs/formal_source_index_cache/formal_source_index.sqlite",
        help="persistent SQLite cache; pass empty string to disable",
    )
    proof_search_retrieval_ablation.add_argument(
        "--refresh-formal-source-index-cache",
        action="store_true",
        help="rebuild and overwrite the persistent formal-source index cache",
    )
    proof_search_retrieval_ablation.add_argument(
        "--lean-rag-db",
        default=None,
        help="optional EmpericalProcessLEAN lean_rag dependency graph SQLite DB",
    )
    proof_search_retrieval_ablation.add_argument(
        "--out",
        default="runs/proof_search_retrieval_ablation",
        help="proof-search retrieval ablation output directory",
    )
    proof_search_retrieval_ablation.set_defaults(func=_proof_search_retrieval_ablation)

    intake_audit = sub.add_parser("intake-audit", help="audit supported question intake and unsupported question rejection")
    intake_audit.add_argument("--supported-file", action="append", help="supported question JSON file; repeatable")
    intake_audit.add_argument("--unsupported-file", action="append", help="unsupported question JSON file; repeatable")
    intake_audit.add_argument("--out", default="runs/intake_audit", help="intake audit output directory")
    intake_audit.set_defaults(func=_intake_audit)

    trace_audit = sub.add_parser("trace-audit", help="validate per-question traces against a run manifest")
    trace_audit.add_argument("--run-dir", required=True, help="directory containing manifest.json and question trace JSON files")
    trace_audit.add_argument("--out", default="runs/trace_audit", help="trace audit output directory")
    trace_audit.set_defaults(func=_trace_audit)

    research_trace_audit = sub.add_parser(
        "research-trace-audit",
        help="validate AI Statistical Theory Lab benchmark traces against their manifest",
    )
    research_trace_audit.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    research_trace_audit.add_argument(
        "--out",
        default="runs/research_trace_audit",
        help="research trace audit output directory",
    )
    research_trace_audit.set_defaults(func=_research_trace_audit)

    research_gap_audit = sub.add_parser(
        "research-gap-audit",
        help="aggregate and validate FORMAL_GAP records from a research benchmark run",
    )
    research_gap_audit.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    research_gap_audit.add_argument(
        "--out",
        default="runs/research_gap_backlog",
        help="formal gap backlog output directory",
    )
    research_gap_audit.set_defaults(func=_research_gap_audit)

    formalization_target_audit = sub.add_parser(
        "formalization-target-audit",
        help="rank missing FORMAL_GAP primitives into a Lean theorem-development queue",
    )
    formalization_target_audit.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    formalization_target_audit.add_argument(
        "--out",
        default="runs/formalization_target_audit",
        help="formalization target audit output directory",
    )
    formalization_target_audit.set_defaults(func=_formalization_target_audit)

    formal_gap_task_export = sub.add_parser(
        "formal-gap-task-export",
        help="export FORMAL_GAP skeletons as machine-readable Lean task JSONL",
    )
    formal_gap_task_export.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    formal_gap_task_export.add_argument(
        "--out",
        default="runs/formal_gap_lean_tasks",
        help="formal gap Lean task output directory",
    )
    formal_gap_task_export.set_defaults(func=_formal_gap_task_export)

    autoform_target_export = sub.add_parser(
        "autoform-target-export",
        help="export FORMAL_GAP tasks as Autoform-Bot-compatible target YAML",
    )
    autoform_target_export.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    autoform_target_export.add_argument(
        "--out",
        default="runs/autoform_targets",
        help="Autoform target YAML/book output directory",
    )
    autoform_target_export.set_defaults(func=_autoform_target_export)

    autoform_harness_audit = sub.add_parser(
        "autoform-harness-audit",
        help="audit the local Autoform-Bot harness checkout and reusable entrypoints",
    )
    autoform_harness_audit.add_argument(
        "--out",
        default="runs/autoform_harness",
        help="Autoform harness audit output directory",
    )
    autoform_harness_audit.set_defaults(func=_autoform_harness_audit)

    proof_bank_expansion_export = sub.add_parser(
        "proof-bank-expansion-export",
        help="export formal-gap tasks as proof-bank lemma proposals and theorem-hole queue rows",
    )
    proof_bank_expansion_export.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    proof_bank_expansion_export.add_argument(
        "--out",
        default="runs/proof_bank_expansion",
        help="proof-bank expansion candidate output directory",
    )
    proof_bank_expansion_export.set_defaults(func=_proof_bank_expansion_export)

    proof_bank_action_export = sub.add_parser(
        "proof-bank-action-export",
        help="export ranked FormalVerifier action rows from proof-bank expansion candidates",
    )
    proof_bank_action_export.add_argument(
        "--proof-bank-expansion-dir",
        required=True,
        help="directory containing proof_bank_expansion_manifest.json and lemma_proposals.jsonl",
    )
    proof_bank_action_export.add_argument(
        "--out",
        default="runs/proof_bank_actions",
        help="proof-bank action output directory",
    )
    proof_bank_action_export.set_defaults(func=_proof_bank_action_export)

    assumption_interface_export = sub.add_parser(
        "assumption-interface-export",
        help="export formalized Lean assumption-interface predicate targets from proof-bank actions",
    )
    assumption_interface_export.add_argument(
        "--proof-bank-actions-dir",
        required=True,
        help="directory containing proof_bank_action_manifest.json",
    )
    assumption_interface_export.add_argument(
        "--out",
        default="runs/assumption_interfaces",
        help="assumption-interface output directory",
    )
    assumption_interface_export.add_argument("--lean-project", help="optional local Lake project for `lake env lean` checks")
    assumption_interface_export.add_argument("--lean-timeout", type=int, default=90)
    assumption_interface_export.set_defaults(func=_assumption_interface_export)

    formalization_delta_plan = sub.add_parser(
        "formalization-delta-plan",
        help="rank the minimal useful Lean formalization delta from proof-bank action rows",
    )
    formalization_delta_plan.add_argument(
        "--proof-bank-actions-dir",
        required=True,
        help="directory containing proof_bank_action_manifest.json",
    )
    formalization_delta_plan.add_argument(
        "--primitive-source-coverage-dir",
        help="optional directory containing primitive_source_coverage_manifest.json",
    )
    formalization_delta_plan.add_argument(
        "--formal-gap-tasks-dir",
        help="optional directory containing formal_gap_lean_task_manifest.json",
    )
    formalization_delta_plan.add_argument(
        "--out",
        default="runs/formalization_delta_plan",
        help="formalization-delta output directory",
    )
    formalization_delta_plan.set_defaults(func=_formalization_delta_plan)


    research_training_export = sub.add_parser(
        "research-training-export",
        help="export research traces as SFT/GRPO seed data for theory-lab agents",
    )
    research_training_export.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    research_training_export.add_argument(
        "--validation-fraction",
        type=float,
        default=0.2,
        help="deterministic validation split fraction in [0, 1)",
    )
    research_training_export.add_argument(
        "--base-model",
        default="untrained-trace-export",
        help="base model label recorded in the legacy training manifest",
    )
    research_training_export.add_argument(
        "--out",
        default="runs/research_training_export",
        help="research trace training export output directory",
    )
    research_training_export.set_defaults(func=_research_training_export)

    research_policy_baseline = sub.add_parser(
        "research-policy-baseline",
        help="evaluate a nearest-neighbor baseline over exported research-agent SFT data",
    )
    research_policy_baseline.add_argument("--train-jsonl", required=True, help="research_sft_train.jsonl")
    research_policy_baseline.add_argument("--validation-jsonl", required=True, help="research_sft_validation.jsonl")
    research_policy_baseline.add_argument("--k", type=int, default=5, help="top-k research-memory candidates")
    research_policy_baseline.add_argument(
        "--out",
        default="runs/research_policy_baseline",
        help="output directory for research policy baseline predictions and manifest",
    )
    research_policy_baseline.set_defaults(func=_research_policy_baseline)

    next_iteration_audit = sub.add_parser(
        "next-iteration-audit",
        help="aggregate per-trace next_iteration_agenda items into a run-level agent queue",
    )
    next_iteration_audit.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    next_iteration_audit.add_argument(
        "--out",
        default="runs/next_iteration_queue",
        help="next-iteration queue output directory",
    )
    next_iteration_audit.set_defaults(func=_next_iteration_audit)

    research_report = sub.add_parser(
        "research-report",
        help="write a human-readable Markdown report from persisted AI Statistical Theory Lab traces",
    )
    research_report.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    research_report.add_argument(
        "--out",
        default="runs/research_report",
        help="research report output directory",
    )
    research_report.set_defaults(func=_research_report)


    theorem_composition = sub.add_parser(
        "theorem-composition-export",
        help="export theorem-composition packets from claim-ledger exact proof-bank reuse rows",
    )
    theorem_composition.add_argument(
        "--claim-ledger-dir",
        required=True,
        help="directory containing claim_ledger_manifest.json and claim_ledger.jsonl",
    )
    theorem_composition.add_argument(
        "--out",
        default="runs/theorem_composition",
        help="theorem-composition packet output directory",
    )
    theorem_composition.set_defaults(func=_theorem_composition_export)

    doctor = sub.add_parser("doctor", help="inspect local readiness for proof, LLM, retrieval, and audit runs")
    doctor.add_argument("--root", default=".", help="project root to inspect")
    doctor.add_argument("--env-file", default=".env", help="dotenv file to inspect for redacted key presence")
    doctor.add_argument("--out", default="runs/doctor", help="write doctor_manifest.json to this directory")
    doctor.add_argument("--max-manifests", type=int, default=12, help="number of latest run manifests to display")
    doctor.add_argument("--json", action="store_true", help="print machine-readable JSON")
    doctor.set_defaults(func=_doctor)

    capability_audit = sub.add_parser(
        "capability-audit",
        help="map the production objective to current source and manifest evidence",
    )
    capability_audit.add_argument("--root", default=".", help="project root to inspect")
    capability_audit.add_argument("--out", default="runs/capability_audit", help="write capability_audit_manifest.json here")
    capability_audit.add_argument("--max-manifests", type=int, default=12, help="number of recent manifests to include")
    capability_audit.add_argument("--json", action="store_true", help="print machine-readable JSON")
    capability_audit.set_defaults(func=_capability_audit)

    research_capability_audit = sub.add_parser(
        "research-capability-audit",
        help="map the broad AI Statistical Theory Lab goal to current evidence and honest gaps",
    )
    research_capability_audit.add_argument("--root", default=".", help="project root to inspect")
    research_capability_audit.add_argument("--question-file", default="examples/research_questions.json")
    research_capability_audit.add_argument(
        "--frontier-benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    research_capability_audit.add_argument(
        "--out",
        default="runs/research_capability_audit",
        help="write research_capability_audit_manifest.json here",
    )
    research_capability_audit.add_argument("--max-manifests", type=int, default=12, help="number of recent research manifests to include")
    research_capability_audit.add_argument("--json", action="store_true", help="print machine-readable JSON")
    research_capability_audit.set_defaults(func=_research_capability_audit)


    prover_component_audit = sub.add_parser(
        "prover-component-audit",
        help="audit the system against the modern prover-stack components from the AI-for-math paper outline",
    )
    prover_component_audit.add_argument("--root", default=".", help="project root to inspect")
    prover_component_audit.add_argument("--question-file", default="examples/research_questions.json")
    prover_component_audit.add_argument(
        "--frontier-benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    prover_component_audit.add_argument(
        "--out",
        default="runs/prover_component_audit",
        help="write prover_component_audit_manifest.json here",
    )
    prover_component_audit.add_argument("--json", action="store_true", help="print machine-readable JSON")
    prover_component_audit.set_defaults(func=_prover_component_audit)

    system_audit = sub.add_parser("system-audit", help="run release-style system gates and write one manifest")
    system_audit.add_argument("--question-file", help="additional question JSON file")
    system_audit.add_argument("--include-partial-examples", action="store_true", help="include examples/partial_questions.json")
    system_audit.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof instead of mock verifier")
    system_audit.add_argument("--runs", type=int, default=300, help="Monte Carlo replicates per question")
    system_audit.add_argument("--n-seeds", type=int, default=2)
    system_audit.add_argument("--seed-start", type=int, default=20260528)
    system_audit.add_argument("--seeds", nargs="*", type=int, help="explicit seeds")
    system_audit.add_argument("--no-eval", action="store_true", help="skip multi-seed evaluation gate")
    system_audit.add_argument("--out", default="runs/system_audit", help="system audit output directory")
    system_audit.add_argument("--env-file", default=".env")
    system_audit.set_defaults(func=lambda args: asyncio.run(_system_audit(args)))

    release_bundle = sub.add_parser("release-bundle", help="write a top-level release manifest from doctor, capability, and system audits")
    release_bundle.add_argument("--root", default=".", help="project root to inspect")
    release_bundle.add_argument("--question-file", help="additional question JSON file")
    release_bundle.add_argument("--include-partial-examples", action="store_true", help="include examples/partial_questions.json")
    release_bundle.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof in the bundled system audit")
    release_bundle.add_argument("--runs", type=int, default=300, help="Monte Carlo replicates per question")
    release_bundle.add_argument("--n-seeds", type=int, default=2)
    release_bundle.add_argument("--seed-start", type=int, default=20260528)
    release_bundle.add_argument("--seeds", nargs="*", type=int, help="explicit seeds")
    release_bundle.add_argument("--no-eval", action="store_true", help="skip multi-seed evaluation gate inside the bundle")
    release_bundle.add_argument("--max-manifests", type=int, default=12, help="number of recent manifests to include in doctor/capability subreports")
    release_bundle.add_argument("--out", default="runs/release_bundle", help="release bundle output directory")
    release_bundle.add_argument("--env-file", default=".env")
    release_bundle.set_defaults(func=lambda args: asyncio.run(_release_bundle(args)))

    theory_intake = sub.add_parser("theory-intake", help="normalize question JSON through deterministic or LLM-gated theory intake")
    theory_intake.add_argument("--question-file", required=True, help="question JSON file")
    theory_intake.add_argument("--llm-theory", action="store_true", help="allow a generator backend to classify supported estimator/DGP families during intake")
    theory_intake.add_argument("--force-llm-theory", action="store_true", help="always ask the LLM for family classification")
    theory_intake.add_argument("--llm-provider", choices=GENERATOR_PROVIDER_CHOICES, default=_default_live_generator_provider())
    theory_intake.add_argument("--llm-static-response-file", default="", help="JSON response to replay when --llm-provider static is used")
    theory_intake.add_argument("--llm-model", default="", help="model name for the intake generator; Anthropic defaults to Claude Haiku 4.5 for this light classifier")
    theory_intake.add_argument("--llm-max-tokens", type=int, default=700)
    theory_intake.add_argument("--env-file", default=".env")
    theory_intake.set_defaults(func=_theory_intake)

    research_benchmark = sub.add_parser(
        "research-benchmark",
        help="run the next-stage open-question statistical theory lab benchmark",
    )
    research_benchmark.add_argument("--question-file", default="examples/research_questions.json")
    research_benchmark.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof for Mathlib-backed subclaims")
    research_benchmark.add_argument("--local-lean", action="store_true", help="use local lake env lean kernel verification")
    research_benchmark.add_argument("--lean-project", help="local Lake project used by --local-lean")
    research_benchmark.add_argument("--lean-timeout", type=int, default=90, help="timeout seconds for each local Lean check")
    research_benchmark.add_argument("--runs", type=int, default=100, help="Monte Carlo research-simulation replicates")
    research_benchmark.add_argument("--seed", type=int, default=20260528)
    research_benchmark.add_argument(
        "--adaptive-mc-rerun",
        action="store_true",
        help="rerun only simulations diagnosed as INSUFFICIENT_MC_PRECISION with a larger MC budget",
    )
    research_benchmark.add_argument(
        "--adaptive-mc-multiplier",
        type=int,
        default=5,
        help="multiplier for adaptive MC reruns of precision-limited simulation rows",
    )
    research_benchmark.add_argument(
        "--formal-source-backend",
        choices=("sqlite", "memory"),
        default="sqlite",
        help="formal-gap retrieval backend for local Lean/stat source search",
    )
    research_benchmark.add_argument(
        "--lean-rag-db",
        default="",
        help=(
            "optional SQLite DB generated by EmpericalProcessLEAN/lean_rag "
            "shared_proof_retrieval.py; auto-discovered from the standard runs/ path when omitted"
        ),
    )
    research_benchmark.add_argument("--out", default="runs/research_benchmark", help="research trace output directory")
    research_benchmark.add_argument("--env-file", default=".env")
    research_benchmark.set_defaults(func=lambda args: asyncio.run(_research_benchmark(args)))


    research_eval = sub.add_parser(
        "research-eval",
        help="run multi-seed evaluation for the open-question statistical theory lab benchmark",
    )
    research_eval.add_argument("--question-file", default="examples/research_questions.json")
    research_eval.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof for Mathlib-backed subclaims")
    research_eval.add_argument("--runs", type=int, default=80, help="Monte Carlo research-simulation replicates per seed")
    research_eval.add_argument("--n-seeds", type=int, default=3)
    research_eval.add_argument("--seed-start", type=int, default=20260528)
    research_eval.add_argument("--seeds", nargs="*", type=int, help="explicit seeds")
    research_eval.add_argument("--out", default="runs/research_eval", help="research evaluation output directory")
    research_eval.add_argument("--env-file", default=".env")
    research_eval.set_defaults(func=lambda args: asyncio.run(_research_eval(args)))

    research_architect_theory = sub.add_parser(
        "research-architect-theory",
        help="run Architect -> LLM TheoryDeveloper and persist typed derivation/evidence artifacts",
    )
    research_architect_theory.add_argument("--question-file", default="examples/research_questions.json")
    research_architect_theory.add_argument(
        "--question-id",
        action="append",
        default=[],
        help=(
            "run only the matching question id from --question-file; repeatable "
            "for targeted live/runtime-learning smokes"
        ),
    )
    research_architect_theory.add_argument("--max-questions", type=int, default=0, help="optional cap for quick runs")
    research_architect_theory.add_argument(
        "--provider",
        choices=GENERATOR_PROVIDER_CHOICES,
        default=_default_live_generator_provider(),
        help="generator backend; defaults to Anthropic Claude API",
    )
    research_architect_theory.add_argument(
        "--static-response-file",
        default="",
        help="JSON response to replay when --provider static is used",
    )
    research_architect_theory.add_argument(
        "--context-json",
        default="",
        help="optional Architect context JSON with retrieval/proof/simulation feedback",
    )
    research_architect_theory.add_argument(
        "--research-source-manifest",
        default="",
        help=(
            "optional hash-bound manifest of model-visible UTF-8 papers, code, "
            "and documentation exposed as direct TheoryDeveloper search/read tools"
        ),
    )
    research_architect_theory.add_argument(
        "--research-source-execution-manifest",
        default="",
        help=(
            "optional operator-bound immutable Python entrypoint and environment; "
            "requires --research-source-manifest and exposes only a no-input run tool"
        ),
    )
    research_architect_theory.add_argument(
        "--llm-model",
        default="",
        help="model name for the TheoryDeveloper provider; Anthropic defaults to Claude Sonnet 4.6",
    )
    research_architect_theory.add_argument("--max-tokens", type=int, default=ResearchArchitectConfig().max_tokens)
    research_architect_theory.add_argument("--temperature", type=float, default=0.2)
    research_architect_theory.add_argument(
        "--max-validation-retries",
        type=int,
        default=ResearchArchitectConfig().max_validation_retries,
        help=(
            "maximum complete-packet retries after TheoryDeveloper validation "
            "packets; set 0 to disable extra provider calls"
        ),
    )
    research_architect_theory.add_argument("--out", default="runs/research_architect_theory")
    research_architect_theory.add_argument("--env-file", default=".env")
    research_architect_theory.set_defaults(func=_research_architect_theory_develop)

    research_agent_runtime = sub.add_parser(
        "research-agent-runtime",
        help=(
            "run the first AI Statistician AgentRuntime loop: "
            "TheoryDeveloper -> SimulationEvaluator with blackboard/evidence traces"
        ),
    )
    research_agent_runtime.add_argument("--question-file", default="examples/research_questions.json")
    research_agent_runtime.add_argument(
        "--question-id",
        action="append",
        default=[],
        help=(
            "run only the matching question id from --question-file; repeatable "
            "for targeted live/runtime-learning smokes"
        ),
    )
    research_agent_runtime.add_argument(
        "--question-task-family",
        action="append",
        default=[],
        help=(
            "run only questions whose primary statistics task family matches "
            "this value; repeatable for cross-family capability eval selection"
        ),
    )
    research_agent_runtime.add_argument(
        "--min-task-families",
        type=int,
        default=0,
        help=(
            "reject the selected question set unless it contains at least this "
            "many explicit statistics task families; useful before live L9 "
            "capability runs"
        ),
    )
    research_agent_runtime.add_argument(
        "--cross-family-eval-protocol",
        default="",
        help=(
            "frozen domain-neutral fresh-start evaluation protocol; requires "
            "--cross-family-eval-panel and full-live capability evaluation"
        ),
    )
    research_agent_runtime.add_argument(
        "--cross-family-eval-panel",
        choices=("development", "held_out"),
        default="",
        help=(
            "select exactly one frozen protocol panel; protocol selection "
            "forbids resume and task-learning-memory inputs"
        ),
    )
    research_agent_runtime.add_argument("--max-questions", type=int, default=0, help="optional cap for quick runs")
    research_agent_runtime.add_argument(
        "--provider",
        choices=GENERATOR_PROVIDER_CHOICES,
        default=_default_live_generator_provider(),
        help="generator backend; defaults to Anthropic Claude API",
    )
    research_agent_runtime.add_argument(
        "--static-response-file",
        default="",
        help="JSON response to replay when --provider static is used",
    )
    research_agent_runtime.add_argument(
        "--context-json",
        default="",
        help="optional Architect context JSON with retrieval/proof/simulation feedback",
    )
    research_agent_runtime.add_argument(
        "--research-source-manifest",
        default="",
        help=(
            "optional hash-bound manifest of model-visible UTF-8 papers, code, "
            "and documentation; evaluator-only gold must never be placed here"
        ),
    )
    research_agent_runtime.add_argument(
        "--research-source-execution-manifest",
        default="",
        help=(
            "optional operator-bound immutable Python entrypoint and environment; "
            "requires --research-source-manifest and never exposes a model-owned command"
        ),
    )
    research_agent_runtime.add_argument(
        "--resume-runtime-manifest",
        default="",
        help=(
            "resume from a prior research-agent-runtime manifest that ended with "
            "incomplete_pending_next_task; the run starts from that exact AgentTask "
            "payload instead of restarting at Architect/Retrieval"
        ),
    )
    resume_architect_group = research_agent_runtime.add_mutually_exclusive_group()
    resume_architect_group.add_argument(
        "--resume-through-architect",
        dest="resume_through_architect",
        action="store_true",
        default=None,
        help=(
            "when --resume-runtime-manifest and ArchitectCoordinator are configured, "
            "run an Architect resume-review turn before returning to the pending task"
        ),
    )
    resume_architect_group.add_argument(
        "--no-resume-through-architect",
        dest="resume_through_architect",
        action="store_false",
        help=(
            "when --resume-runtime-manifest is set, resume the pending AgentTask "
            "directly; intended for debug/replay runs because capability audits will "
            "not count this as live ArchitectCoordinator orchestration"
        ),
    )
    research_agent_runtime.add_argument(
        "--formal-source-index-db",
        default="",
        help=(
            "optional runtime SQLite FTS declaration index; defaults to the "
            "persistent --formal-source-index-cache"
        ),
    )
    research_agent_runtime.add_argument(
        "--formal-source-index-cache",
        default=str(RESEARCH_AGENT_RUNTIME_FORMAL_SOURCE_INDEX_CACHE),
        help=(
            "persistent SQLite FTS cache used by live formal-source retrieval; "
            "pass an empty string to build an index under --out"
        ),
    )
    research_agent_runtime.add_argument(
        "--refresh-formal-source-index-cache",
        action="store_true",
        help="rebuild the live formal-source SQLite FTS cache before the run",
    )
    research_agent_runtime.add_argument(
        "--llm-model",
        default="",
        help="model name for the TheoryDeveloper provider; Anthropic defaults to Claude Sonnet 4.6",
    )
    research_agent_runtime.add_argument(
        "--theory-model-tier",
        choices=("haiku", "sonnet"),
        default=ResearchArchitectConfig().model_tier,
        help="Claude tier for compact TheoryDeveloper handoff packets",
    )
    research_agent_runtime.add_argument("--max-tokens", type=int, default=ResearchArchitectConfig().max_tokens)
    research_agent_runtime.add_argument(
        "--serious-theory-llm-model",
        default="",
        help=(
            "optional explicit model for capability and upstream-revision "
            "TheoryDeveloper workspaces"
        ),
    )
    research_agent_runtime.add_argument(
        "--serious-theory-model-tier",
        choices=("haiku", "sonnet"),
        default=ResearchArchitectConfig().serious_model_tier,
        help="Claude tier for capability and upstream-revision theory workspaces",
    )
    research_agent_runtime.add_argument(
        "--serious-theory-max-tokens",
        type=int,
        default=ResearchArchitectConfig().serious_max_tokens,
        help="maximum output tokens for serious TheoryDeveloper workspaces",
    )
    research_agent_runtime.add_argument("--temperature", type=float, default=0.2)
    research_agent_runtime.add_argument(
        "--theory-max-validation-retries",
        type=int,
        default=ResearchArchitectConfig().max_validation_retries,
        help=(
            "maximum complete-packet retries after TheoryDeveloper validation "
            "packets; set 0 to disable extra provider calls"
        ),
    )
    research_agent_runtime.add_argument(
        "--llm-timeout-seconds",
        type=float,
        default=DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
        help=(
            "wall-clock timeout for each live LLM generator request; timeout "
            "retries remain bounded by --max-subsystem-retries for provider API "
            "timeouts, while local tool and generic timeout exceptions fail fast"
        ),
    )
    research_agent_runtime.add_argument(
        "--architect-coordinator-provider",
        choices=SUBSYSTEM_GENERATOR_PROVIDER_CHOICES,
        default="same",
        help=(
            "generator backend for top-level ArchitectCoordinator proposals; "
            "same reuses the main live provider, while static requires "
            "--architect-static-response-file"
        ),
    )
    research_agent_runtime.add_argument(
        "--architect-static-response-file",
        default="",
        help="JSON ArchitectCoordinator response to replay when --architect-coordinator-provider static",
    )
    research_agent_runtime.add_argument(
        "--architect-llm-model",
        default="",
        help="model name for ArchitectCoordinator proposals; Anthropic defaults to Claude Sonnet 4.6",
    )
    research_agent_runtime.add_argument("--architect-max-tokens", type=int, default=3000)
    research_agent_runtime.add_argument("--architect-temperature", type=float, default=0.1)
    research_agent_runtime.add_argument(
        "--architect-metric-semantic-reviewer-llm-model",
        default="",
        help=(
            "independent pre-execution metric-contract reviewer model; "
            "Anthropic is capped at the configured Claude Sonnet tier"
        ),
    )
    research_agent_runtime.add_argument(
        "--architect-metric-semantic-reviewer-max-tokens",
        type=int,
        default=7000,
    )
    research_agent_runtime.add_argument(
        "--architect-metric-semantic-reviewer-max-revisions",
        type=int,
        default=1,
        help=(
            "maximum full metric-contract rewrites after independent "
            "pre-execution semantic review rejects a candidate"
        ),
    )
    research_agent_runtime.add_argument(
        "--architect-metric-protocol-max-upstream-theory-revisions",
        type=int,
        default=1,
        help=(
            "maximum TheoryDeveloper revisions routed from independent "
            "pre-execution metric review before the task fails closed"
        ),
    )
    research_agent_runtime.add_argument(
        "--simulation-engineer-provider",
        choices=SUBSYSTEM_GENERATOR_PROVIDER_CHOICES,
        default="same",
        help=(
            "generator backend for SimulatorEngineer proposals; same reuses the "
            "main live provider, while static requires --simulation-static-response-file"
        ),
    )
    research_agent_runtime.add_argument(
        "--simulation-static-response-file",
        default="",
        help="JSON SimulatorEngineer response to replay when --simulation-engineer-provider static",
    )
    research_agent_runtime.add_argument(
        "--simulation-llm-model",
        default="",
        help="model name for SimulatorEngineer proposals; Anthropic defaults to Claude Sonnet 4.6",
    )
    research_agent_runtime.add_argument("--simulation-max-tokens", type=int, default=8000)
    research_agent_runtime.add_argument("--simulation-temperature", type=float, default=0.1)
    research_agent_runtime.add_argument(
        "--algorithm-engineer-provider",
        choices=SUBSYSTEM_GENERATOR_PROVIDER_CHOICES,
        default="same",
        help=(
            "generator backend for AlgorithmEngineer proposals; same reuses the "
            "main live provider, while static requires --algorithm-static-response-file"
        ),
    )
    research_agent_runtime.add_argument(
        "--algorithm-static-response-file",
        default="",
        help="JSON AlgorithmEngineer response to replay when --algorithm-engineer-provider static",
    )
    research_agent_runtime.add_argument(
        "--algorithm-llm-model",
        default="",
        help="model name for AlgorithmEngineer proposals; Anthropic defaults to Claude Sonnet 4.6",
    )
    research_agent_runtime.add_argument("--algorithm-max-tokens", type=int, default=5000)
    research_agent_runtime.add_argument("--algorithm-temperature", type=float, default=0.1)
    research_agent_runtime.add_argument(
        "--formalizer-provider",
        choices=SUBSYSTEM_GENERATOR_PROVIDER_CHOICES,
        default="same",
        help=(
            "generator backend for Formalizer/ProofEngineer proposals; same reuses "
            "the main live provider, while static requires --formalizer-static-response-file"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalizer-static-response-file",
        default="",
        help="JSON Formalizer/ProofEngineer response to replay when --formalizer-provider static",
    )
    research_agent_runtime.add_argument(
        "--formalizer-llm-model",
        default="",
        help="model name for Formalizer/ProofEngineer proposals; Anthropic defaults to Claude Sonnet 4.6",
    )
    research_agent_runtime.add_argument("--formalizer-max-tokens", type=int, default=6000)
    research_agent_runtime.add_argument("--formalizer-temperature", type=float, default=0.1)
    research_agent_runtime.add_argument(
        "--formalizer-candidate-local-lean",
        action="store_true",
        help=(
            "run local Lean on materialized LLM Formalizer candidate artifacts; "
            "this checks the generated Lean file itself, not just registered proof-bank subclaims"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalizer-candidate-lean-lsp-mcp",
        action="store_true",
        help=(
            "when --formalizer-candidate-local-lean is enabled, also call Lean LSP MCP "
            "diagnostic tools on materialized Formalizer candidate artifacts and feed the "
            "tool trace back to ProofEngineer; diagnostic only, not proof evidence"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalizer-candidate-lean-project",
        default="",
        help=(
            "local Lake project used by --formalizer-candidate-local-lean; "
            "defaults to --lean-project when omitted"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalizer-candidate-lean-timeout",
        type=int,
        default=DEFAULT_LEAN_TOOL_TIMEOUT_SECONDS,
        help="timeout seconds for each Formalizer local Lean or LSP/MCP tool call",
    )
    research_agent_runtime.add_argument(
        "--emperical-process-lean-rag-root",
        default=os.environ.get("EMPERICAL_PROCESS_LEAN_ROOT", ""),
        help=(
            "trusted local EmpericalProcessLEAN checkout whose mature "
            "lean_rag/scripts/shared_proof_retrieval.py provider is added to runtime "
            "formal-source retrieval"
        ),
    )
    research_agent_runtime.add_argument(
        "--emperical-process-lean-rag-db-dir",
        default="",
        help=(
            "EmpericalProcessLEAN shared declaration-graph database directory; "
            "when omitted, use the upstream provider's DEFAULT_DB_DIR; relative "
            "overrides are resolved under --emperical-process-lean-rag-root"
        ),
    )
    research_agent_runtime.add_argument(
        "--emperical-process-lean-rag-source",
        choices=("all", "main", "worktrees"),
        default="main",
        help=(
            "which indexed EmpericalProcessLEAN checkouts participate in retrieval; "
            "canonical runs default to the clean main checkout"
        ),
    )
    research_agent_runtime.add_argument(
        "--emperical-process-lean-rag-checkout",
        action="append",
        default=[],
        help="optional indexed checkout name filter; repeatable",
    )
    research_agent_runtime.add_argument(
        "--emperical-process-lean-rag-allow-unsigned-index",
        action="store_true",
        help=(
            "compatibility only: allow a declaration-graph shard whose source "
            "signature is unknown; strict runtime rejects unsigned shards"
        ),
    )
    research_agent_runtime.add_argument(
        "--emperical-process-lean-rag-allow-dirty-index",
        action="store_true",
        help=(
            "compatibility only: allow a shard built from or attached to a dirty "
            "checkout; strict runtime rejects dirty provenance"
        ),
    )
    research_agent_runtime.add_argument(
        "--openprover-hlm",
        action="store_true",
        help=(
            "run the configured OpenProver verifier-backed HLM controller on "
            "lineage-bound whole-theorem Formalizer search requests, then "
            "deterministically rerun direct candidates under the exact local "
            "AI-Statistician Lean gate before any LLM rewrite"
        ),
    )
    research_agent_runtime.add_argument(
        "--openprover-root",
        default=os.environ.get("OPENPROVER_ROOT", ""),
        help="trusted local ykzeng-yale/OpenProver checkout used by --openprover-hlm",
    )
    research_agent_runtime.add_argument(
        "--openprover-hlm-model",
        default="",
        help=(
            "model for OpenProver branch generation; defaults to the configured "
            "Formalizer/ProofEngineer model and reuses AI-Statistician's generator backend"
        ),
    )
    research_agent_runtime.add_argument(
        "--openprover-hlm-max-tokens",
        type=int,
        default=1600,
    )
    research_agent_runtime.add_argument(
        "--openprover-hlm-temperature",
        type=float,
        default=0.1,
    )
    research_agent_runtime.add_argument(
        "--openprover-hlm-rounds",
        type=int,
        default=2,
    )
    research_agent_runtime.add_argument(
        "--openprover-hlm-branches-per-round",
        type=int,
        default=4,
    )
    research_agent_runtime.add_argument(
        "--openprover-hlm-feedback-top-k",
        type=int,
        default=4,
    )
    research_agent_runtime.add_argument(
        "--openprover-hlm-max-attempts",
        type=int,
        default=120,
    )
    research_agent_runtime.add_argument(
        "--openprover-hlm-route-strategy",
        choices=(
            "hybrid",
            "whole_proof",
            "tactic_repair",
            "lemma_goal",
            "retrieval_feedback",
            "dependency_goal",
        ),
        default="hybrid",
    )
    research_agent_runtime.add_argument(
        "--openprover-hlm-verifier-timeout",
        type=int,
        default=120,
        help="timeout seconds for each OpenProver Lake-backed Lean check",
    )
    research_agent_runtime.add_argument(
        "--critic-evaluator-provider",
        choices=SUBSYSTEM_GENERATOR_PROVIDER_CHOICES,
        default="same",
        help=(
            "generator backend for CriticEvaluator boundary-audit proposals; same "
            "reuses the main live provider, while static requires --critic-static-response-file"
        ),
    )
    research_agent_runtime.add_argument(
        "--critic-static-response-file",
        default="",
        help="JSON CriticEvaluator response to replay when --critic-evaluator-provider static",
    )
    research_agent_runtime.add_argument(
        "--critic-llm-model",
        default="",
        help="model name for CriticEvaluator proposals; Anthropic defaults to Claude Haiku 4.5",
    )
    research_agent_runtime.add_argument("--critic-max-tokens", type=int, default=5000)
    research_agent_runtime.add_argument("--critic-temperature", type=float, default=0.1)
    research_agent_runtime.add_argument(
        "--generated-code-semantic-reviewer-provider",
        choices=SUBSYSTEM_GENERATOR_PROVIDER_CHOICES,
        default="none",
        help=(
            "independent generator backend for semantic review of exact executed "
            "generated code; live evaluations use the independent same-provider "
            "current Haiku model"
        ),
    )
    research_agent_runtime.add_argument(
        "--generated-code-semantic-reviewer-static-response-file",
        default="",
        help=(
            "JSON semantic-review response to replay when "
            "--generated-code-semantic-reviewer-provider static"
        ),
    )
    research_agent_runtime.add_argument(
        "--generated-code-semantic-reviewer-llm-model",
        default="",
        help=(
            "model for independent generated-code semantic review; Anthropic "
            "production use is capped at the configured Claude Sonnet tier, while "
            "live evaluations are pinned to the current Haiku model"
        ),
    )
    research_agent_runtime.add_argument(
        "--generated-code-semantic-reviewer-max-tokens",
        type=int,
        default=7000,
    )
    research_agent_runtime.add_argument(
        "--generated-code-semantic-reviewer-temperature",
        type=float,
        default=0.0,
    )
    research_agent_runtime.add_argument(
        "--generated-code-semantic-review-max-revisions",
        type=int,
        default=1,
        help=(
            "maximum fresh coding-agent regenerations after independent semantic "
            "review rejects otherwise runnable generated code"
        ),
    )
    research_agent_runtime.add_argument(
        "--formal-target-semantic-reviewer-provider",
        choices=SUBSYSTEM_GENERATOR_PROVIDER_CHOICES,
        default="none",
        help=(
            "independent generator backend for mathematical review of exact Lean "
            "theorem targets before proof search; live evaluations are pinned to "
            "the current Haiku model"
        ),
    )
    research_agent_runtime.add_argument(
        "--formal-target-semantic-reviewer-static-response-file",
        default="",
        help=(
            "JSON formal-target review response to replay when "
            "--formal-target-semantic-reviewer-provider static"
        ),
    )
    research_agent_runtime.add_argument(
        "--formal-target-semantic-reviewer-llm-model",
        default="",
        help=(
            "model for independent whole-target semantic review; Anthropic "
            "is capped at the configured Claude Sonnet tier"
        ),
    )
    research_agent_runtime.add_argument(
        "--formal-target-semantic-reviewer-max-tokens",
        type=int,
        default=8000,
    )
    research_agent_runtime.add_argument(
        "--formal-target-semantic-reviewer-temperature",
        type=float,
        default=0.0,
    )
    research_agent_runtime.add_argument(
        "--formal-target-semantic-review-required",
        action="store_true",
        help=(
            "require an independent semantic verdict for each hash-bound exact "
            "theorem target before typed prover search"
        ),
    )
    research_agent_runtime.add_argument(
        "--formal-target-semantic-review-max-revisions",
        type=int,
        default=1,
        help=(
            "maximum fresh Formalizer or TheoryDeveloper revisions after an "
            "independent whole-target semantic rejection"
        ),
    )
    research_agent_runtime.add_argument("--real-lean", action="store_true", help="use the configured Lean verifier for exact model-authored sources")
    research_agent_runtime.add_argument("--local-lean", action="store_true", help="use local lake env lean for exact model-authored sources")
    research_agent_runtime.add_argument("--lean-project", default="", help="local Lake project used by --local-lean")
    research_agent_runtime.add_argument("--lean-timeout", type=int, default=90, help="timeout seconds for each local Lean check")
    research_agent_runtime.add_argument("--runs", type=int, default=100)
    research_agent_runtime.add_argument("--seed", type=int, default=20260528)
    research_agent_runtime.add_argument(
        "--generated-simulation-timeout-seconds",
        type=int,
        default=60,
        help=(
            "wall-clock budget for one full generated simulation sandbox run; "
            "the exact budget is supplied to SimulationEngineer and recorded in "
            "its execution contract"
        ),
    )
    research_agent_runtime.add_argument("--max-iterations", type=int, default=12)
    research_agent_runtime.add_argument(
        "--formal-verification-policy",
        choices=("required", "optional", "advisory"),
        default="optional",
        help=(
            "research acceptance contract: required blocks final acceptance "
            "without Lean/AXLE source theorem evidence, optional lets Architect "
            "choose proof-first/simulation-first/dual-track, and advisory uses "
            "formal tools only as diagnostics with explicit gap disclosure"
        ),
    )
    research_agent_runtime.add_argument(
        "--recommended-research-path",
        choices=("simulation_first", "proof_first", "dual_track"),
        default="",
        help=(
            "optional runtime research-path request. Leave unset to let the "
            "Architect choose under --formal-verification-policy=optional; set "
            "to simulation_first, proof_first, or dual_track for controlled evals"
        ),
    )
    research_agent_runtime.add_argument(
        "--max-subsystem-retries",
        type=int,
        default=1,
        help=(
            "runtime-level retries for transient provider/subsystem exceptions "
            "such as API connection errors and provider API timeouts; local tool "
            "timeouts are not retried, and retry observations are recorded in traces"
        ),
    )
    research_agent_runtime.add_argument(
        "--max-critic-theory-revision-rounds",
        dest="max_critic_revision_rounds",
        type=int,
        default=1,
        help=(
            "bounded CriticEvaluator -> TheoryDeveloper model revision rounds "
            "before accepting remaining gaps"
        ),
    )
    runtime_evaluation_mode = research_agent_runtime.add_mutually_exclusive_group()
    runtime_evaluation_mode.add_argument(
        "--research-eval",
        action="store_true",
        help=(
            "run the live autonomous statistical research loop with serious theory, "
            "generated algorithm and simulation code, frozen metric protocol, "
            "independent semantic review, and final Critic evaluation. The strict "
            "Formalizer/Lean lane is reported separately and is not run by this mode"
        ),
    )
    runtime_evaluation_mode.add_argument(
        "--capability-eval",
        action="store_true",
        help=(
            "run as a strict main-capability evaluation: reject static/no-Architect/"
            "manual-proof-filter debug modes and return nonzero unless the runtime "
            "capability scorecard is ready"
        ),
    )
    research_agent_runtime.add_argument(
        "--research-gold-manifest",
        default="",
        help=(
            "evaluator-only hidden gold manifest for --research-eval. It runs "
            "after AgentRuntime termination and cannot enter model context or "
            "generate source-revision feedback"
        ),
    )
    research_agent_runtime.add_argument(
        "--capability-eval-preset",
        choices=("none", "minimal-live", "full-live"),
        default="none",
        help=(
            "populate strict live capability-eval defaults without weakening "
            "the scorecard gates. minimal-live enables live providers and the "
            "internal Lean/ProofEngineer paths; full-live requires at least two "
            "task families and enables model-owned Python/R/Lean tool workspaces, "
            "live Lean-LSP/MCP, and verifier-backed OpenProver search. Historical "
            "repair executors, proof bridges, and post-runtime formal fallbacks are "
            "absent from the canonical runtime. Formal capability "
            "evidence must come from the integrated runtime workspaces; static "
            "fixtures never become capability evidence."
        ),
    )
    research_agent_runtime.add_argument("--out", default="runs/research_agent_runtime")
    research_agent_runtime.add_argument("--env-file", default=".env")
    research_agent_runtime.set_defaults(func=_research_agent_runtime)

    research_agent_runtime_audit = sub.add_parser(
        "research-agent-runtime-audit",
        help="audit AgentRuntime outputs, agenda/learning rows, and proof-boundary accounting",
    )
    research_agent_runtime_audit.add_argument("--runtime-dir", default="runs/research_agent_runtime")
    research_agent_runtime_audit.add_argument("--out", default="runs/research_agent_runtime_audit")
    research_agent_runtime_audit.set_defaults(func=_research_agent_runtime_audit)

    architect_research_path_policy_eval = sub.add_parser(
        "architect-research-path-policy-eval",
        help=(
            "component eval for ArchitectCoordinator evidence-policy routing: "
            "check required/proof-first, advisory/simulation-first, and optional "
            "research-path plans from a generator backend"
        ),
    )
    architect_research_path_policy_eval.add_argument(
        "--provider",
        choices=("anthropic", "openai", "static"),
        default=_default_live_generator_provider(),
    )
    architect_research_path_policy_eval.add_argument(
        "--static-response-file",
        default="",
        help="JSON object or list of Architect responses to replay when --provider static",
    )
    architect_research_path_policy_eval.add_argument(
        "--llm-model",
        default="",
        help="model name for ArchitectCoordinator; Anthropic defaults to Claude Sonnet 4.6",
    )
    architect_research_path_policy_eval.add_argument(
        "--llm-timeout-seconds",
        type=float,
        default=DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
    )
    architect_research_path_policy_eval.add_argument(
        "--max-tokens",
        type=int,
        default=4000,
    )
    architect_research_path_policy_eval.add_argument(
        "--temperature",
        type=float,
        default=0.1,
    )
    architect_research_path_policy_eval.add_argument(
        "--out",
        default="runs/architect_research_path_policy_eval",
    )
    architect_research_path_policy_eval.add_argument(
        "--env-file",
        default=".env",
    )
    architect_research_path_policy_eval.add_argument(
        "--allow-fixture-success",
        action="store_true",
        help=(
            "return success for static fixture plumbing checks; default success "
            "requires live generator Architect policy evidence"
        ),
    )
    architect_research_path_policy_eval.set_defaults(
        func=_architect_research_path_policy_eval
    )

    list_cmd = sub.add_parser("list", help="list registered questions and formal obligations")
    list_cmd.add_argument("--tag", action="append", help="filter obligations by tag")
    list_cmd.set_defaults(func=_list)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
