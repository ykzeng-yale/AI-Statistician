"""Prepare four existing draw configurations; do not activate or run a study."""

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from ai_statistician.algorithm_engineer_llm import AlgorithmEngineerConfig
from ai_statistician.architect_coordinator_llm import ArchitectCoordinatorConfig
from ai_statistician.architect_metric_semantic_reviewer_llm import ArchitectMetricSemanticReviewerConfig
from ai_statistician.critic_evaluator_llm import CriticEvaluatorConfig
from ai_statistician.cross_family_eval_protocol import (
    CONFIRMATORY_EVALUATION_COHORT_CONTEXT_KEY, CONFIRMATORY_EVALUATION_SEED_MODULUS,
    resolve_confirmatory_evaluation_cohort,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.generated_code_semantic_reviewer_llm import GeneratedCodeSemanticReviewerConfig
from ai_statistician.local_model_backend import LocalChatGeneratorBackend
from ai_statistician.research_agent_runtime import ResearchAgentRuntimeConfig
from ai_statistician.research_architect import ResearchArchitectConfig
from ai_statistician.research_schema import load_open_research_questions
from ai_statistician.research_source_library import load_research_source_execution_spec, load_research_source_snapshot
from ai_statistician.simulation_engineer_llm import SimulationEngineerConfig


HERE = Path(__file__).resolve().parent
MODES = ("free_planning", "same_workflow", "no_cross_role_revision", "full_collaboration")
WORKFLOW = (
    "Develop a reviewable theory checkpoint; inspect the current theory before promoting code; "
    "bind and execute exact estimator source; develop diagnostic simulation; inspect the exact "
    "current sources and protocol before separate confirmation; report selected evidence and gaps. "
    "Your review shares the author context and is self-review, not isolated scientific authority. "
    "You own all edits and local feedback iteration."
)


def file_ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "byte_size": len(raw)}


def prepare(*, out, deployment, sources, source_execution, call_limit, output_tokens, temperature,
            seed, confirmation_base, replicates, execution_timeout, model_timeout,
            no_progress_turns):
    """Assembly only; the caller still owns source, authority and arm qualification."""
    out = Path(out).resolve()
    if out.exists():
        raise FileExistsError("configuration preparation output already exists")
    if any(type(value) is not int or value < 1 for value in (
        call_limit, output_tokens, replicates, execution_timeout, no_progress_turns,
    )) or not 0 <= temperature <= 2 or not 0 < model_timeout < float("inf"):
        raise ValueError("invalid declared resource or decoding settings")
    if (type(seed) is not int or type(confirmation_base) is not int
        or not 0 <= seed < CONFIRMATORY_EVALUATION_SEED_MODULUS
        or not 0 <= confirmation_base < CONFIRMATORY_EVALUATION_SEED_MODULUS):
        raise ValueError("data seeds must fit the existing cohort range")
    confirmations = [(confirmation_base + index * 1_000_003) % CONFIRMATORY_EVALUATION_SEED_MODULUS
                     for index in range(call_limit)]
    if seed in confirmations or len(set(confirmations)) != len(confirmations):
        raise ValueError("confirmation schedule overlaps exploration or itself")
    deployment_ref = file_ref(deployment)
    declared = json.loads(Path(deployment_ref["path"]).read_bytes())
    model = declared["model"]
    if not isinstance(model, str) or not model.strip():
        raise ValueError("deployment must declare its local model identity")
    source_ref = file_ref(sources)
    snapshot = load_research_source_snapshot(Path(source_ref["path"]))
    if snapshot.identity_errors() or snapshot.manifest_sha256 != source_ref["sha256"]:
        raise ValueError("source snapshot identity mismatch")
    execution_ref = file_ref(source_execution)
    execution = load_research_source_execution_spec(Path(execution_ref["path"]), research_sources=snapshot)
    if execution.manifest_sha256 != execution_ref["sha256"]:
        raise ValueError("source execution identity mismatch")
    question_ref = file_ref(HERE / "questions.json")
    questions = load_open_research_questions(Path(question_ref["path"]))
    if len(questions) != 1:
        raise ValueError("the case requires one declared question")
    question = questions[0]
    backend = {"base_url": "http://127.0.0.1:8081/v1", "timeout_s": model_timeout}
    LocalChatGeneratorBackend(**backend)  # Validate the existing transport; no HTTP call.
    common = dict(provider_name="local", model=model, model_tier="local",
                  max_tokens=output_tokens, temperature=temperature)
    roles = {
        "theory": asdict(ResearchArchitectConfig(**common, serious_model=model,
            serious_model_tier="local", serious_max_tokens=output_tokens,
            theory_workspace_max_turns=call_limit, theory_workspace_max_tool_calls=2 * call_limit,
            theory_workspace_max_no_progress_turns=no_progress_turns)),
        "algorithm": asdict(AlgorithmEngineerConfig(**common, client_tool_code_max_turns=call_limit,
            client_tool_code_max_no_progress_turns=no_progress_turns)),
        "simulation": asdict(SimulationEngineerConfig(**common, client_tool_code_max_turns=call_limit,
            client_tool_code_max_no_progress_turns=no_progress_turns)),
        "theory_reviewer": asdict(ArchitectMetricSemanticReviewerConfig(**common,
            client_tool_max_turns=call_limit, client_tool_max_tool_calls=2 * call_limit,
            client_tool_max_no_progress_turns=no_progress_turns)),
        "code_reviewer": asdict(GeneratedCodeSemanticReviewerConfig(**common,
            client_tool_max_turns=call_limit, client_tool_max_tool_calls=2 * call_limit,
            client_tool_max_no_progress_turns=no_progress_turns)),
        "architect": asdict(ArchitectCoordinatorConfig(**common, metric_semantic_reviewer_model=model,
            metric_semantic_reviewer_model_tier="local", metric_semantic_reviewer_max_tokens=output_tokens)),
        "critic": asdict(CriticEvaluatorConfig(**common, client_tool_max_turns=call_limit,
            client_tool_max_tool_calls=2 * call_limit, client_tool_max_no_progress_turns=no_progress_turns)),
    }
    control_request = {"system_prompt": "Research the supplied question with the actual workspace tools. "
        "Own source revisions, preserve selected evidence and report unresolved gaps honestly.",
        "model": model, "max_tokens": output_tokens, "temperature": temperature, "tool_choice": "any"}
    fingerprint = stable_hash({"question_ref": question_ref, "deployment_ref": deployment_ref,
        "source_snapshot_ref": source_ref, "source_execution_ref": execution_ref,
        "backend": backend, "roles": roles, "control_request": control_request, "workflow": WORKFLOW, "modes": MODES,
        "call_limit": call_limit, "seed": seed, "replicates": replicates,
        "execution_timeout": execution_timeout, "no_progress_turns": no_progress_turns,
        "confirmation_schedule": confirmations})
    context = {"cross_family_evaluation_protocol": {
        "protocol_fingerprint": fingerprint, "candidate_gate_independence_required": True,
        "post_outcome_fresh_cohort_required": True, "confirmatory_candidate_seed_blinding_required": True}}
    cohort, errors = resolve_confirmatory_evaluation_cohort(context, question_id=question.id,
                                                         execution_seed=confirmation_base)
    if errors:
        raise ValueError("; ".join(errors))
    context[CONFIRMATORY_EVALUATION_COHORT_CONTEXT_KEY] = cohort
    configurations = {}
    for mode in MODES:
        collaborative = mode in {"no_cross_role_revision", "full_collaboration"}
        config = {"question_ref": question_ref, "question_id": question.id,
            "deployment_ref": deployment_ref, "source_snapshot_ref": source_ref,
            "source_execution_ref": execution_ref,
            "mode": mode, "backend": backend,
            "roles": roles if collaborative else {key: value for key, value in roles.items()
                                                   if key not in {"architect", "critic"}}}
        if collaborative:
            config.update(runtime=asdict(ResearchAgentRuntimeConfig(n_runs=replicates, seed=seed,
                generated_simulation_timeout_seconds=execution_timeout,
                theory_scratch_timeout_seconds=execution_timeout,
                max_iterations=call_limit, local_model_call_limit=call_limit,
                evaluation_mode="research_eval", formal_verification_policy="optional",
                evaluation_provider="local", evaluation_model_tier="local", evaluation_model=model)),
                architect_context=context)
        else:
            config.update(request=control_request,
                workflow_instructions=WORKFLOW if mode == "same_workflow" else "",
                estimator_ids=[question.estimator_execution_contract["estimator_id"]],
                execution={"n_runs": replicates, "seed": seed, "timeout_s": execution_timeout,
                           "confirmatory_seeds": confirmations},
                limits={"max_turns": call_limit, "max_tool_calls": 2 * call_limit,
                        "max_no_progress_turns": no_progress_turns, "local_model_call_limit": call_limit})
        configurations[mode] = config
    out.mkdir(parents=True, exist_ok=False)
    refs = {}
    for mode, config in configurations.items():
        path = out / (mode + ".json")
        with path.open("x", encoding="utf-8") as stream:
            json.dump(config, stream, indent=2, allow_nan=False)
        refs[mode] = file_ref(path)
    with (out / "preparation.json").open("x", encoding="utf-8") as stream:
        json.dump({"scope": "configuration_preparation_only", "study_activated": False,
            "model_calls": 0, "scientific_evaluation_performed": False, "configs": refs,
            "question_ref": question_ref, "deployment_ref": deployment_ref, "source_snapshot_ref": source_ref,
            "source_execution_ref": execution_ref,
            "authority": "Declared settings and file identity, not live deployment or complete arm qualification",
            "remaining": ["complete source/data/environment capsule and missing helper",
                          "scientific execution availability and reference/gold qualification",
                          "observed requests, confirmation exposure and opportunity matching",
                          "roster/split, independent assessment, draw schedule and analysis"]}, stream, indent=2)
    return refs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("out", "deployment", "sources", "source-execution"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("call-limit", "output-tokens", "seed", "confirmation-base", "replicates",
                 "execution-timeout", "no-progress-turns"):
        parser.add_argument("--" + name, type=int, required=True)
    for name in ("temperature", "model-timeout"):
        parser.add_argument("--" + name, type=float, required=True)
    print(json.dumps(prepare(**vars(parser.parse_args()))))


if __name__ == "__main__":
    main()
