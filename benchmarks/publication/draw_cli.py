"""One fresh declared control or production draw; no study activation or scoring."""

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from ai_statistician.algorithm_engineer_llm import AlgorithmEngineerConfig, LLMAlgorithmEngineerAgent
from ai_statistician.architect_metric_semantic_reviewer_llm import ArchitectMetricSemanticReviewerConfig, LLMArchitectMetricSemanticReviewerAgent
from ai_statistician.architect_coordinator_llm import ArchitectCoordinatorConfig, LLMArchitectCoordinatorAgent
from ai_statistician.client_tool_loop import read_hash_bound_utf8_file
from ai_statistician.generated_code_semantic_reviewer_llm import GeneratedCodeSemanticReviewerConfig, LLMGeneratedCodeSemanticReviewerAgent
from ai_statistician.critic_evaluator_llm import CriticEvaluatorConfig, LLMCriticEvaluatorAgent
from ai_statistician.local_model_backend import LocalChatGeneratorBackend
from ai_statistician.model_backend import ClientToolTurnRequest
from ai_statistician.research_architect import LLMTheoryDeveloperAgent, ResearchArchitectConfig
from ai_statistician.research_agent_runtime import ResearchAgentRuntimeConfig
from ai_statistician.research_schema import load_open_research_questions
from ai_statistician.research_source_discovery import PublicResearchSourceDiscovery, PublicResearchSourceDiscoveryConfig
from ai_statistician.research_source_library import load_research_source_snapshot
from ai_statistician.simulation_engineer_llm import LLMSimulationEngineerAgent, SimulationEngineerConfig
from benchmarks.publication.evaluate_final_artifacts import publication_material_from_submission
from benchmarks.publication.run_control_draw import run_single_context_research_draw
from benchmarks.publication.run_collaborative_draw import run_collaborative_research_draw


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    config_path = args.config.resolve()
    raw = config_path.read_bytes()
    config = json.loads(raw)
    if not isinstance(config, dict) or config.get("mode") not in {"free_planning", "same_workflow", "full_collaboration", "no_cross_role_revision"}:
        raise ValueError("unsupported study draw mode")
    collaborative = config["mode"] in {"full_collaboration", "no_cross_role_revision"}
    allowed = {"question_ref", "question_id", "mode", "backend", "roles", "deployment_ref", "source_snapshot_ref", "source_discovery"}
    allowed |= {"runtime", "architect_context"} if collaborative else {"request", "workflow_instructions", "estimator_ids", "execution", "limits"}
    if not isinstance(config, dict) or set(config) - allowed:
        raise ValueError("unsupported study draw configuration fields")
    out_dir = args.out.resolve()
    if out_dir.exists():
        raise FileExistsError("study draw output directory already exists")

    def reference(field):
        ref = dict(config[field])
        ref["path"] = str((config_path.parent / ref["path"]).resolve())
        text, errors = read_hash_bound_utf8_file(ref)
        if errors:
            raise ValueError(field + " identity mismatch: " + ",".join(errors))
        return ref, text

    question_ref, _ = reference("question_ref")
    questions = load_open_research_questions(Path(question_ref["path"]))
    reference("question_ref")  # Reject changes during the existing question loader.
    matches = [row for row in questions if row.id == config["question_id"]]
    if len(matches) != 1:
        raise ValueError("study draw requires exactly one declared question")
    deployment_ref, deployment_text = reference("deployment_ref")
    deployment = json.loads(deployment_text)
    request = None if collaborative else ClientToolTurnRequest(messages=(), tools=(), **config["request"])
    if not isinstance(deployment, dict) or not deployment.get("model") or (request and deployment["model"] != request.model):
        raise ValueError("declared deployment differs from the requested model")
    mode, workflow = config["mode"], config.get("workflow_instructions", "")
    if (not isinstance(workflow, str)
        or (mode == "same_workflow") != bool(workflow.strip())):
        raise ValueError("control mode and declared workflow disagree")

    sources = None
    if "source_snapshot_ref" in config:
        source_ref, _ = reference("source_snapshot_ref")
        sources = load_research_source_snapshot(Path(source_ref["path"]))
        if sources.manifest_sha256 != source_ref["sha256"]:
            raise ValueError("source snapshot changed during loading")
    backend = LocalChatGeneratorBackend(**config["backend"])
    role_types = {"theory": (LLMTheoryDeveloperAgent, ResearchArchitectConfig),
                  "algorithm": (LLMAlgorithmEngineerAgent, AlgorithmEngineerConfig),
                  "simulation": (LLMSimulationEngineerAgent, SimulationEngineerConfig),
                  "theory_reviewer": (LLMArchitectMetricSemanticReviewerAgent, ArchitectMetricSemanticReviewerConfig),
                  "code_reviewer": (LLMGeneratedCodeSemanticReviewerAgent, GeneratedCodeSemanticReviewerConfig)}
    if collaborative:
        role_types.update(architect=(LLMArchitectCoordinatorAgent, ArchitectCoordinatorConfig), critic=(LLMCriticEvaluatorAgent, CriticEvaluatorConfig))
    required_roles = set(role_types) if collaborative else {"theory", "algorithm", "simulation"}
    if set(config["roles"]) - set(role_types) or not required_roles <= set(config["roles"]):
        raise ValueError("study roles must declare the production owners and only supported reviewers")
    settings_by_role = {}
    for role, values in config["roles"].items():
        config_cls = role_types[role][1]
        settings = config_cls(**values)
        if (settings.provider_name != "local" or settings.model_tier != "local"
            or settings.model != deployment["model"] or (request and settings.temperature != request.temperature)
            or (role == "theory" and (settings.serious_model != deployment["model"] or settings.serious_model_tier != "local"))
            or (role == "architect" and (settings.metric_semantic_reviewer_model != deployment["model"] or settings.metric_semantic_reviewer_model_tier != "local"))):
            raise ValueError("study role differs from the frozen local model configuration")
        settings_by_role[role] = settings
    runtime_config = ResearchAgentRuntimeConfig(**config["runtime"]) if collaborative else None
    if runtime_config and (runtime_config.evaluation_provider != "local" or runtime_config.evaluation_model_tier != "local"
                           or runtime_config.evaluation_model != deployment["model"]):
        raise ValueError("production runtime differs from the declared local deployment")
    discovery = None
    if "source_discovery" in config:
        declared = dict(config["source_discovery"])
        state_dir = (config_path.parent / declared.pop("state_dir")).resolve()
        if state_dir.exists() or state_dir.is_relative_to(out_dir):
            raise ValueError("discovery storage must be fresh and outside the exclusive draw directory")
        discovery = PublicResearchSourceDiscovery(config=PublicResearchSourceDiscoveryConfig(**declared), state_dir=state_dir)
    agents = {}
    for role, settings in settings_by_role.items():
        if role == "architect":
            continue
        cls = role_types[role][0]
        agents[role] = cls(provider=backend, config=settings, **(
            {"research_sources": sources, "research_source_discovery": discovery}
            if role in {"theory", "theory_reviewer"} else {}))
    if collaborative:
        agents["architect"] = LLMArchitectCoordinatorAgent(provider=backend, config=settings_by_role["architect"],
                                                           metric_semantic_reviewer=agents["theory_reviewer"])
    provenance = {"config_ref": {"path": str(config_path), "sha256": hashlib.sha256(raw).hexdigest(), "byte_size": len(raw)},
                  "question_ref": question_ref, "deployment_ref": deployment_ref, "declared_deployment": deployment,
                  "deployment_authority": "caller_declaration_not_live_attestation_or_scientific_qualification",
                  "source_snapshot": sources.descriptor() if sources else None,
                  "source_discovery": {**discovery.descriptor(), "state_dir": str(state_dir)} if discovery else None}
    if collaborative:
        result, submission = run_collaborative_research_draw(question=matches[0], backend=backend, agents=agents,
            config=runtime_config, out_dir=out_dir, architect_context=config.get("architect_context"), study_provenance=provenance, mode=mode)
    else:
        result, submission = run_single_context_research_draw(
            question=matches[0], request=request, backend=backend, out_dir=out_dir,
            theory_agent=agents["theory"], algorithm_agent=agents["algorithm"], simulation_agent=agents["simulation"],
            theory_reviewer=agents.get("theory_reviewer"), code_reviewer=agents.get("code_reviewer"),
            estimator_ids=config["estimator_ids"], workflow_instructions=workflow, study_provenance=provenance,
            **config["execution"], **config["limits"],
        )
        result = result.to_json()
    material_ref = None
    if submission is not None:
        scopes = None if collaborative else {"algorithm" if index == 0 else f"algorithm_{index + 1}": value
                                             for index, value in enumerate(config["estimator_ids"])}
        source_kind = "runtime" if collaborative else "control"
        material = publication_material_from_submission(submission, source_kind=source_kind, control_estimator_scopes=scopes)
        fields = ("question_id", "question_hash", "task_intent") + (
            ("internal_status", "selected_artifact_refs") if collaborative else ("selected_checkpoints", "report_ref"))
        body = {"source_kind": source_kind, "submission_identity": {key: submission[key] for key in fields},
            **({"assessment": submission["selected_artifacts"]["assessment"]} if collaborative
               else {"report_markdown": submission["report_markdown"]}),
            "material": {**material, "estimator_bindings": [asdict(row) for row in material["estimator_bindings"]]},
            "authority": "selected_final_material_not_scientific_acceptance"}
        encoded = (json.dumps(body, indent=2, allow_nan=False) + "\n").encode("utf-8")
        path = out_dir / "final_material.json"
        with path.open("xb") as stream:
            stream.write(encoded)
        material_ref = {"path": str(path), "sha256": hashlib.sha256(encoded).hexdigest(), "byte_size": len(encoded)}
    print(json.dumps({"status": result["status"], "question_id": matches[0].id, "final_material_ref": material_ref,
                      "local_model_usage": result.get("local_model_usage"), "scientific_evaluation_performed": False}))
    return 0 if submission is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
