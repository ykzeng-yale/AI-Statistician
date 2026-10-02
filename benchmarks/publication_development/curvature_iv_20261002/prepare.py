"""Freeze one source-assisted four-mode development panel before model calls."""

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import random
import subprocess
import urllib.request

from ai_statistician.algorithm_engineer_llm import AlgorithmEngineerConfig
from ai_statistician.architect_coordinator_llm import ArchitectCoordinatorConfig
from ai_statistician.architect_metric_semantic_reviewer_llm import ArchitectMetricSemanticReviewerConfig
from ai_statistician.critic_evaluator_llm import CriticEvaluatorConfig
from ai_statistician.fingerprint import stable_hash
from ai_statistician.generated_code_semantic_reviewer_llm import GeneratedCodeSemanticReviewerConfig
from ai_statistician.research_architect import ResearchArchitectConfig
from ai_statistician.research_agent_runtime import ResearchAgentRuntimeConfig
from ai_statistician.research_gold_evaluation import _visible_question_hash_payload
from ai_statistician.research_schema import load_open_research_questions, research_question_payload
from ai_statistician.research_source_library import load_research_source_snapshot
from ai_statistician.scientific_sandbox import discover_scientific_sandbox_runtime
from ai_statistician.simulation_engineer_llm import SimulationEngineerConfig


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MODEL = "Qwen3-4B-Instruct-2507"
WEIGHTS = Path.home() / ".cache/huggingface/hub/models--unsloth--Qwen3-4B-Instruct-2507-GGUF/snapshots/a06e946bb6b655725eafa393f4a9745d460374c9/Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
SERVER = Path.home() / "DTR-MultiRoundLLM/work/bin/llama-server"
SERVER_ARGUMENTS = ["--model", str(WEIGHTS), "--alias", MODEL, "--host", "127.0.0.1", "--port", "8081",
                    "--ctx-size", "131072", "--parallel", "1", "--jinja", "--threads", "4", "--n-gpu-layers", "99",
                    "--flash-attn", "on", "--cache-type-k", "q8_0", "--cache-type-v", "q8_0", "--cache-ram", "0",
                    "--no-warmup", "--no-context-shift", "--seed", "20261012", "--temp", "0.7",
                    "--top-p", "0.8", "--top-k", "20", "--min-p", "0"]
PINS = {"weights_sha256": "3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597",
        "server_sha256": "f124807ba31de5a65ea22fd624f33fd4dfe3c837d1c014dcf4a516b66812ffd7",
        "chat_template_sha256": "c979e0e71a3e21b8f208e6ab120d5cb29327885f29d2a8b18fda67a723798e18"}


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write(path, body):
    raw = (json.dumps(body, indent=2, allow_nan=False) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(raw)
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "byte_size": len(raw)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args(argv)
    out = args.out.resolve()
    if out.exists():
        raise FileExistsError("panel preparation already exists")
    assert sha256(WEIGHTS) == PINS["weights_sha256"] and sha256(SERVER) == PINS["server_sha256"]
    with urllib.request.urlopen("http://127.0.0.1:8081/props", timeout=10) as response:
        props = json.load(response)
    assert hashlib.sha256(props["chat_template"].encode()).hexdigest() == PINS["chat_template_sha256"]
    with urllib.request.urlopen("http://127.0.0.1:8081/v1/models", timeout=10) as response:
        assert MODEL in {row["id"] for row in json.load(response)["data"]}
    question, = load_open_research_questions(HERE / "questions.json")
    public = research_question_payload(question, include_task_intent=True)
    reference = json.loads(args.reference.read_text())
    assert reference["oracle_sha256"] == sha256(HERE / "numerical_evaluator.py")
    assert reference["validator_sha256"] == sha256(HERE / "validate_reference.py")
    assert reference["numerical_cases"] == 35 and reference["zero_moment_cases"] > 0
    paper = ROOT / "runs/publication_reference_qualification_20261002/tsci/sources/paper.txt"
    paper_pdf = paper.with_suffix(".pdf")
    assert sha256(paper_pdf) == "ef38e39e3aeab082c65896ea591f32299132656e86fd51a9c8070468cd842b4e"
    out.mkdir(parents=True, exist_ok=False)
    source_dir = out / "public_sources"
    source_dir.mkdir()
    with (source_dir / "paper.txt").open("xb") as stream:
        stream.write(paper.read_bytes())
    source_ref = write(out / "source_manifest.json", {
        "schema_version": 1, "snapshot_id": "tsci-paper-curvature-dev-20261002", "source_horizon": "2026-10-02",
        "source_root": "public_sources", "documents": [{"document_id": "tsci-paper", "title": "TSCI JSS paper text",
            "source_kind": "published_paper", "relative_path": "paper.txt", "sha256": sha256(paper), "model_visible": True,
            "citation": "Carl, Emmenegger, Guo and Bühlmann (2025), JSS 114(7)",
            "url": "https://www.jstatsoft.org/article/view/v114i07", "license": "local_reading_copy_not_redistribution_qualification"}]})
    load_research_source_snapshot(out / "source_manifest.json")
    question_ref = write(out / "questions.json", [public])
    reference_ref = write(out / "numerical_reference_validation.json", reference)
    deployment_ref = write(out / "deployment.json", {
        "model": MODEL, "quantization": "Q4_K_M", **PINS, "weights_path": str(WEIGHTS), "server_path": str(SERVER),
        "runtime_commit": "4fea119", "server_arguments": SERVER_ARGUMENTS, "dynamic_library_path": str(SERVER.parent),
        "hardware": {"platform": platform.platform(), "machine": platform.machine(),
            "memory_bytes": int(subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True)),
            "cpu": subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()},
        "active_props": props, "scientific_runtime": asdict(discover_scientific_sandbox_runtime()),
        "request_sampling": {"temperature": 0.7, "max_tokens": 16384, "parallel_tool_calls": False},
        "server_sampling": {"top_p": 0.8, "top_k": 20, "min_p": 0, "seed": 20261012},
        "sampling_source": "https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507#best-practices",
        "research_calls_before_freeze": 0})
    common = dict(provider_name="local", model=MODEL, model_tier="local", max_tokens=16384, temperature=0.7)
    roles = {
        "theory": asdict(ResearchArchitectConfig(**common, serious_model=MODEL, serious_model_tier="local", serious_max_tokens=16384)),
        "algorithm": asdict(AlgorithmEngineerConfig(**common)), "simulation": asdict(SimulationEngineerConfig(**common)),
        "theory_reviewer": asdict(ArchitectMetricSemanticReviewerConfig(**common)),
        "code_reviewer": asdict(GeneratedCodeSemanticReviewerConfig(**common)),
        "architect": asdict(ArchitectCoordinatorConfig(**common, metric_semantic_reviewer_model=MODEL,
            metric_semantic_reviewer_model_tier="local", metric_semantic_reviewer_max_tokens=16384)),
        "critic": asdict(CriticEvaluatorConfig(**common))}
    order = ["free_planning", "same_workflow", "no_cross_role_revision", "full_collaboration"]
    random.Random(20261012).shuffle(order)
    configs = {}
    workflow = ("Build reviewable theory and self-review it before promoted implementation; bind and execute exact method source; "
                "author diagnostic simulation; self-review current sources and protocol; freeze and execute separate confirmation; "
                "report selected evidence and gaps. Review shares your author history and is not isolated authority. "
                "You own all edits and can iterate on actual tool feedback.")
    for mode in order:
        collaborative = mode in {"full_collaboration", "no_cross_role_revision"}
        config = {"question_ref": question_ref, "question_id": question.id, "deployment_ref": deployment_ref,
            "mode": mode, "backend": {"base_url": "http://127.0.0.1:8081/v1", "timeout_s": 600},
            "roles": roles if collaborative else {key: value for key, value in roles.items() if key not in {"architect", "critic"}},
            "source_snapshot_ref": source_ref}
        if collaborative:
            config["runtime"] = asdict(ResearchAgentRuntimeConfig(n_runs=2000, seed=730223,
                generated_simulation_timeout_seconds=120, theory_scratch_timeout_seconds=30,
                max_iterations=256, local_model_call_limit=96, formal_verification_policy="optional",
                evaluation_mode="research_eval", evaluation_provider="local", evaluation_model_tier="local", evaluation_model=MODEL))
            config["architect_context"] = {"cross_family_evaluation_protocol": {
                "protocol_fingerprint": stable_hash({"study": HERE.name, "public_question": public, "seed": 730223}),
                "candidate_gate_independence_required": True, "post_outcome_fresh_cohort_required": True,
                "confirmatory_candidate_seed_blinding_required": True}}
        else:
            config.update(request={"system_prompt": "Conduct the supplied statistical research with the actual workspace tools. "
                "Own all mathematical and source revisions and report selected evidence and unresolved gaps honestly.",
                "model": MODEL, "max_tokens": 16384, "temperature": 0.7, "tool_choice": "auto"},
                workflow_instructions=workflow if mode == "same_workflow" else "", estimator_ids=["curvature_iv"],
                execution={"n_runs": 2000, "seed": 730223, "timeout_s": 120,
                    "confirmatory_seeds": [1730226 + index * 1000003 for index in range(96)]},
                limits={"max_turns": 96, "max_tool_calls": 384, "max_no_progress_turns": 2, "local_model_call_limit": 96})
        configs[mode] = write(out / (mode + ".json"), config)
    numerical = {"language": "python", "harness_path": str(HERE / "numerical_evaluator.py"),
        "harness_sha256": sha256(HERE / "numerical_evaluator.py"), "dependencies": [], "seed": 730227,
        "replicates": 1, "timeout_seconds": 120}
    task_ref = write(out / "evaluator_task.json", {"task_id": question.id, "task_intent": question.task_intent,
        "visible_question_hash": stable_hash(_visible_question_hash_payload(public)),
        "hidden_algorithm_evaluator": {**numerical, "required_estimator_id": "curvature_iv", "acceptance_checks": [
            {"check_id": "exact_moment_procedure", "path": ["all_cases_passed"], "operator": "eq", "expected": True}]},
        "hidden_empirical_evaluator": {**numerical, "acceptance_checks": [
            {"check_id": "frozen_two_scenario_confirmation", "path": ["compatible_numerical_experiment"], "operator": "eq", "expected": True}]}})
    write(out / "protocol.json", {"study_id": HERE.name, "official_study_activated": False,
        "scope": "one_family_four_mode_integrated_development_not_scientific_efficacy",
        "product_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "question_ref": question_ref, "deployment_ref": deployment_ref, "source_snapshot_ref": source_ref,
        "task_ref": task_ref, "numerical_reference_validation_ref": reference_ref, "configs": configs,
        "draw_order": order, "replicates_per_mode": 1, "independent_families": 1, "wall_seconds_per_draw": 7200,
        "server_cold_start_per_draw": True, "automatic_retry_or_escalation": False,
        "full_task_mathematical_authority_qualified": False, "external_results_return_to_author": False,
        "main_test_pool_exclusion": "Entire TSCI/curvature-identification family",
        "source_files": {path.name: sha256(path) for path in (HERE / "questions.json", HERE / "numerical_evaluator.py", Path(__file__))},
        "resource_boundary": "Same request/output/context/wall caps, not equal realized tokens or compute. Role contexts, tools and confirmation schedules differ.",
        "confirmation_boundary": "Controls use private schedule starting 1730226; production starts 730223 and existing outcome-independent increments. Not an identical-cohort causal comparison.",
        "termination_boundary": "Only trusted terminal selection; no resume, intermediate salvage, candidate repair or consumed rescore."})
    print(json.dumps({"protocol": str(out / "protocol.json"), "draw_order": order}))


if __name__ == "__main__":
    main()
