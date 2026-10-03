"""One case-preparation stage through the existing graph and Theory workspace."""

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import urllib.request

from ai_statistician.agent_runtime import AgentRuntime, AgentStepResult, AgentTask, BlackboardState
from ai_statistician.client_tool_loop import run_client_tool_workspace
from ai_statistician.local_model_backend import LocalChatGeneratorBackend
from ai_statistician.packet_validation import PacketValidationError
from ai_statistician.research_agent_runtime import _runtime_architect_context_with_requested_evidence_contract
from ai_statistician.research_architect import LLMTheoryDeveloperAgent, ResearchArchitectConfig
from ai_statistician.research_schema import load_open_research_questions
from ai_statistician.research_source_library import load_research_source_execution_spec, load_research_source_snapshot
from ai_statistician.theory_workspace import TheoryScratchpadConfig
from benchmarks.publication_deployment_qualification_20261003.observe import digest, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_bytes())
    out = Path(plan["output_path"]).resolve()
    out.mkdir(parents=True, exist_ok=False)
    assets = json.loads(Path(plan["deployment_asset_plan"]).read_bytes())
    for path, expected in (
        (Path(assets["download"]["verified_path"]), assets["weights_sha256"]),
        (Path(assets["server_binary"]), assets["server_sha256"]),
        (Path(plan["native_r_config_path"]), plan["native_r_config_sha256"]),
        *[(Path(assets["library_directory"]) / name, value)
          for name, value in assets["library_sha256"].items()],
    ):
        if digest(path) != expected:
            raise ValueError("prepared asset hash mismatch: " + str(path))
    if Path(os.environ.get("AI_STATISTICIAN_NATIVE_R_CONFIG", "")).resolve() != Path(plan["native_r_config_path"]).resolve():
        raise ValueError("native R configuration differs from the declared preparation")
    sources = load_research_source_snapshot(Path(plan["source_manifest_path"]))
    if (sources.identity_errors() or sources.manifest_sha256 != plan["source_manifest_sha256"]
            or sources.snapshot_hash != plan["source_snapshot_hash"]):
        raise ValueError("case source identity mismatch")
    execution = None
    if plan.get("source_execution_path"):
        execution_path = Path(plan["source_execution_path"])
        if digest(execution_path) != plan["source_execution_sha256"]:
            raise ValueError("source execution identity mismatch")
        execution = load_research_source_execution_spec(execution_path, research_sources=sources)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for endpoint, filename in (("/props", "props.json"), ("/v1/models", "models.json")):
        with opener.open("http://127.0.0.1:8081" + endpoint, timeout=10) as response:
            write_json(out / filename, json.load(response))
    props = json.loads((out / "props.json").read_bytes())
    models = json.loads((out / "models.json").read_bytes())
    settings, params = props["default_generation_settings"], props["default_generation_settings"]["params"]
    if (settings["n_ctx"] != plan["context_tokens"] or props["total_slots"] != 1
            or props["model_alias"] != plan["model"]
            or props["model_path"] != str(Path(assets["download"]["verified_path"]).resolve())
            or hashlib.sha256(props["chat_template"].encode()).hexdigest() != assets["expected_chat_template_sha256"]
            or [row["id"] for row in models["data"]] != [plan["model"]]
            or params["seed"] != plan["model_seed"] or params["top_k"] != plan["top_k"]
            or any(abs(params[k] - plan[k]) > 1e-6 for k in ("temperature", "top_p", "min_p"))):
        raise ValueError("active deployment differs from declared preparation")
    questions = load_open_research_questions(Path(plan["question_path"]))
    if len(questions) != 1:
        raise ValueError("case preparation requires the unchanged single case question")
    question = questions[0]
    context = _runtime_architect_context_with_requested_evidence_contract(
        {}, formal_verification_policy="optional", evaluation_mode="research_eval",
        task_intent=question.task_intent, estimator_execution_contract=question.estimator_execution_contract,
    )
    backend = LocalChatGeneratorBackend(base_url="http://127.0.0.1:8081/v1", timeout_s=plan["request_timeout_seconds"])
    config = ResearchArchitectConfig(
        provider_name="local", model=plan["model"], model_tier="local",
        serious_model=plan["model"], serious_model_tier="local",
        max_tokens=plan["max_tokens"], serious_max_tokens=plan["max_tokens"], temperature=plan["temperature"],
        theory_workspace_max_turns=plan["max_model_turns"], theory_workspace_max_tool_calls=plan["max_tool_calls"],
        theory_workspace_max_no_progress_turns=plan["max_no_progress_turns"],
    )
    agent = LLMTheoryDeveloperAgent(provider=backend, config=config, research_sources=sources,
        research_source_execution=execution)
    workspace = agent.prepare_workspace(
        question, architect_context=context, theory_workspace_root=out / "workspaces",
        theory_scratchpad=TheoryScratchpadConfig(sandbox_dir=out / "scratch", seed=plan["scratch_seed"],
            replicates=plan["scratch_default_replicates"], timeout_s=plan["scratch_timeout_seconds"]),
    )
    write_json(out / "frozen_stage.json", {
        "plan_sha256": digest(args.plan), "question_sha256": digest(Path(plan["question_path"])),
        "request": asdict(workspace.request), "config": asdict(config), "context": context,
        "source_snapshot": sources.descriptor(), "scope": plan["scope"], "scientific_acceptance": False,
    })

    class TheoryPreparation:
        name = "TheoryDeveloper"

        def run(self, task, blackboard):
            try:
                packet = run_client_tool_workspace(backend=backend, workspace=workspace)
            except PacketValidationError as exc:
                write_json(out / "failed_stage.json", {
                    "errors": exc.errors, "attempts": exc.attempts, "history": exc.history,
                    "last_invalid_packet": exc.last_invalid_packet, "recovery_checkpoint": exc.recovery_checkpoint,
                    "scientific_acceptance": False, "automatic_restart": False,
                })
                raise
            write_json(out / "selected_theory_packet.json", packet)
            return AgentStepResult(status="REROUTE", rationale="Selected preparatory draft awaits independent assessment.",
                produced_artifacts={"selected_packet_ref": {"path": str(out / "selected_theory_packet.json"),
                    "sha256": digest(out / "selected_theory_packet.json")}})

    def progress(row):
        with (out / "progress.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, sort_keys=True) + "\n")

    result = AgentRuntime(subsystems={"TheoryDeveloper": TheoryPreparation()},
        blackboard=BlackboardState(project_id=question.id)).run(
        AgentTask(task_id="theory-preparation:" + question.id, owner_subsystem="TheoryDeveloper",
            objective=question.description), max_iterations=1, local_model_call_limit=plan["max_model_turns"],
        progress_callback=progress,
    )
    write_json(out / "runtime_result.json", result.to_json())
    selected = (out / "selected_theory_packet.json").is_file()
    print(json.dumps({"status": result.status, "selected_draft": selected, "local_model_usage": result.local_model_usage,
        "scientific_acceptance": False, "official_study_activated": False}))
    return 0 if selected else 1


if __name__ == "__main__":
    raise SystemExit(main())
