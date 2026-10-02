"""One fresh production graph; evaluation and other study arms remain external."""

from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path

from ai_statistician.agent_runtime import load_persisted_runtime_result
from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_agent_runtime import run_research_agent_runtime, _normalized_runtime_evaluation_model_config
from ai_statistician.research_evaluation import load_runtime_research_submission
from ai_statistician.research_schema import research_question_payload
from benchmarks.publication.feedback_ablation import NO_CROSS_ROLE_REVISION, no_cross_role_revision_policy


def run_collaborative_research_draw(*, question, backend, agents, config, out_dir: Path,
                                    architect_context=None, study_provenance=None, mode="full_collaboration"):
    if mode not in {"full_collaboration", "no_cross_role_revision"}:
        raise ValueError("unsupported production study arm")
    if (getattr(backend, "provider_name", None) != "local"
        or any(agent.provider is not backend for agent in agents.values())):
        raise ValueError("publication production draw requires one shared local backend")
    if config.evaluation_mode != "research_eval":
        raise ValueError("publication production draw requires research_eval")
    if question.task_intent.get("formal") == "required":
        raise ValueError("this study entry has no required-formal executor")
    if config.local_model_call_limit is not None and (
        type(config.local_model_call_limit) is not int or config.local_model_call_limit < 1
    ):
        raise ValueError("local model call limit must be a positive integer or None")
    config = _normalized_runtime_evaluation_model_config(config)
    question, context = deepcopy(question), deepcopy(dict(architect_context or {}))
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=False)
    public = research_question_payload(question, include_task_intent=True)
    frozen = {"question": public, "question_hash": stable_hash(public), "mode": mode,
              "intervention": NO_CROSS_ROLE_REVISION if mode == "no_cross_role_revision" else None,
              "runtime_config": asdict(config), "architect_context": context,
              "role_configs": {role: asdict(agent.config) for role, agent in agents.items()},
              "provider": backend.provider_name, "backend_class": type(backend).__qualname__,
              "base_url": getattr(backend, "base_url", None),
              "study_provenance": deepcopy(dict(study_provenance or {})),
              "authority": "one_production_draw_not_external_scientific_acceptance"}
    with (out_dir / "frozen_draw.json").open("x", encoding="utf-8") as stream:
        json.dump({**frozen, "frozen_draw_hash": stable_hash(frozen)}, stream, indent=2)
    manifest = run_research_agent_runtime(
        [question], out_dir / "author", theory_developer=agents["theory"],
        architect_coordinator=agents["architect"], algorithm_engineer=agents["algorithm"],
        simulation_engineer=agents["simulation"], critic_evaluator=agents["critic"],
        generated_code_semantic_reviewer=agents["code_reviewer"], config=config, architect_context=context,
        handoff_policy=no_cross_role_revision_policy(config) if mode == "no_cross_role_revision" else None,
    )
    paths = manifest["artifacts"]["per_question_results"]
    if len(paths) != 1:
        raise ValueError("production draw must return exactly one question result")
    result = load_persisted_runtime_result(Path(paths[0]))
    submission = load_runtime_research_submission(result, question=question)
    return result, submission or None
