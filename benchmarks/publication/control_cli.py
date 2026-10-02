"""One fresh control draw from declared inputs; no study activation or scoring."""

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from ai_statistician.algorithm_engineer_llm import AlgorithmEngineerConfig, LLMAlgorithmEngineerAgent
from ai_statistician.architect_metric_semantic_reviewer_llm import ArchitectMetricSemanticReviewerConfig, LLMArchitectMetricSemanticReviewerAgent
from ai_statistician.client_tool_loop import read_hash_bound_utf8_file
from ai_statistician.generated_code_semantic_reviewer_llm import GeneratedCodeSemanticReviewerConfig, LLMGeneratedCodeSemanticReviewerAgent
from ai_statistician.local_model_backend import LocalChatGeneratorBackend
from ai_statistician.model_backend import ClientToolTurnRequest
from ai_statistician.research_architect import LLMTheoryDeveloperAgent, ResearchArchitectConfig
from ai_statistician.research_schema import load_open_research_questions
from ai_statistician.research_source_discovery import PublicResearchSourceDiscovery, PublicResearchSourceDiscoveryConfig
from ai_statistician.research_source_library import load_research_source_snapshot
from ai_statistician.simulation_engineer_llm import LLMSimulationEngineerAgent, SimulationEngineerConfig
from benchmarks.publication.evaluate_final_artifacts import publication_material_from_submission
from benchmarks.publication.run_control_draw import run_single_context_research_draw


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    config_path = args.config.resolve()
    raw = config_path.read_bytes()
    config = json.loads(raw)
    allowed = {"question_ref", "question_id", "mode", "workflow_instructions", "backend", "request", "roles",
               "estimator_ids", "execution", "limits", "deployment_ref", "source_snapshot_ref", "source_discovery"}
    if not isinstance(config, dict) or set(config) - allowed:
        raise ValueError("unsupported control configuration fields")
    out_dir = args.out.resolve()
    if out_dir.exists():
        raise FileExistsError("control output directory already exists")

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
        raise ValueError("control requires exactly one declared question")
    deployment_ref, deployment_text = reference("deployment_ref")
    deployment = json.loads(deployment_text)
    request = ClientToolTurnRequest(messages=(), tools=(), **config["request"])
    if not isinstance(deployment, dict) or deployment.get("model") != request.model:
        raise ValueError("declared deployment differs from the requested model")
    mode, workflow = config["mode"], config.get("workflow_instructions", "")
    if (mode not in {"free_planning", "same_workflow"} or not isinstance(workflow, str)
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
    if set(config["roles"]) - set(role_types) or not {"theory", "algorithm", "simulation"} <= set(config["roles"]):
        raise ValueError("control roles must declare the production owners and only supported optional reviewers")
    settings_by_role = {}
    for role, values in config["roles"].items():
        config_cls = role_types[role][1]
        settings = config_cls(**values)
        if (settings.provider_name != "local" or settings.model_tier != "local"
            or settings.model != request.model or settings.temperature != request.temperature
            or (role == "theory" and (settings.serious_model != request.model or settings.serious_model_tier != "local"))):
            raise ValueError("control role differs from the frozen local model configuration")
        settings_by_role[role] = settings
    discovery = None
    if "source_discovery" in config:
        declared = dict(config["source_discovery"])
        state_dir = (config_path.parent / declared.pop("state_dir")).resolve()
        if state_dir.exists() or state_dir.is_relative_to(out_dir):
            raise ValueError("discovery storage must be fresh and outside the exclusive draw directory")
        discovery = PublicResearchSourceDiscovery(config=PublicResearchSourceDiscoveryConfig(**declared), state_dir=state_dir)
    agents = {}
    for role, settings in settings_by_role.items():
        cls = role_types[role][0]
        agents[role] = cls(provider=backend, config=settings, **(
            {"research_sources": sources, "research_source_discovery": discovery}
            if role in {"theory", "theory_reviewer"} else {}))
    provenance = {"config_ref": {"path": str(config_path), "sha256": hashlib.sha256(raw).hexdigest(), "byte_size": len(raw)},
                  "question_ref": question_ref, "deployment_ref": deployment_ref, "declared_deployment": deployment,
                  "deployment_authority": "caller_declaration_not_live_attestation_or_scientific_qualification",
                  "source_snapshot": sources.descriptor() if sources else None,
                  "source_discovery": {**discovery.descriptor(), "state_dir": str(state_dir)} if discovery else None}
    result, submission = run_single_context_research_draw(
        question=matches[0], request=request, backend=backend, out_dir=out_dir,
        theory_agent=agents["theory"], algorithm_agent=agents["algorithm"], simulation_agent=agents["simulation"],
        theory_reviewer=agents.get("theory_reviewer"), code_reviewer=agents.get("code_reviewer"),
        estimator_ids=config["estimator_ids"], workflow_instructions=workflow, study_provenance=provenance,
        **config["execution"], **config["limits"],
    )
    material_ref = None
    if submission is not None:
        scopes = {"algorithm" if index == 0 else f"algorithm_{index + 1}": value
                  for index, value in enumerate(config["estimator_ids"])}
        material = publication_material_from_submission(submission, source_kind="control", control_estimator_scopes=scopes)
        body = {"source_kind": "control", "submission_identity": {
            key: submission[key] for key in ("question_id", "question_hash", "task_intent", "selected_checkpoints", "report_ref")},
            "report_markdown": submission["report_markdown"],
            "material": {**material, "estimator_bindings": [asdict(row) for row in material["estimator_bindings"]]},
            "authority": "selected_final_material_not_scientific_acceptance"}
        encoded = (json.dumps(body, indent=2, allow_nan=False) + "\n").encode("utf-8")
        path = out_dir / "final_material.json"
        with path.open("xb") as stream:
            stream.write(encoded)
        material_ref = {"path": str(path), "sha256": hashlib.sha256(encoded).hexdigest(), "byte_size": len(encoded)}
    print(json.dumps({"status": result.status, "question_id": matches[0].id, "final_material_ref": material_ref,
                      "local_model_usage": result.local_model_usage, "scientific_evaluation_performed": False}))
    return 0 if submission is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
