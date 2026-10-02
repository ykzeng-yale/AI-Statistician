"""Freeze one declared four-arm development pilot before research calls."""

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
from ai_statistician.research_agent_runtime import ResearchAgentRuntimeConfig
from ai_statistician.research_gold_evaluation import _visible_question_hash_payload
from ai_statistician.research_schema import load_open_research_questions, research_question_payload
from ai_statistician.scientific_sandbox import discover_scientific_sandbox_runtime
from ai_statistician.simulation_engineer_llm import SimulationEngineerConfig
from ai_statistician.research_architect import ResearchArchitectConfig


MODEL = "Qwen3-4B-Instruct-2507"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WEIGHTS = Path.home() / ".cache/huggingface/hub/models--unsloth--Qwen3-4B-Instruct-2507-GGUF/snapshots/a06e946bb6b655725eafa393f4a9745d460374c9/Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
SERVER = Path.home() / "DTR-MultiRoundLLM/work/bin/llama-server"
PINS = {"weights_sha256": "3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597",
        "server_sha256": "f124807ba31de5a65ea22fd624f33fd4dfe3c837d1c014dcf4a516b66812ffd7",
        "chat_template_sha256": "c979e0e71a3e21b8f208e6ab120d5cb29327885f29d2a8b18fda67a723798e18"}
SERVER_ARGUMENTS = ["--model", str(WEIGHTS), "--alias", MODEL, "--host", "127.0.0.1", "--port", "8081",
                    "--ctx-size", "32768", "--parallel", "1", "--jinja", "--threads", "4", "--n-gpu-layers", "99",
                    "--flash-attn", "on", "--cache-type-k", "q8_0", "--cache-type-v", "q8_0",
                    "--no-warmup", "--no-context-shift", "--seed", "20261002"]


def sha256(path):
    with path.open("rb") as stream:
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
        raise FileExistsError("pilot preparation already exists")
    assert sha256(WEIGHTS) == PINS["weights_sha256"] and sha256(SERVER) == PINS["server_sha256"]
    with urllib.request.urlopen("http://127.0.0.1:8081/props", timeout=10) as response:
        props = json.load(response)
    assert hashlib.sha256(props["chat_template"].encode()).hexdigest() == PINS["chat_template_sha256"]
    with urllib.request.urlopen("http://127.0.0.1:8081/v1/models", timeout=10) as response:
        assert MODEL in {row["id"] for row in json.load(response)["data"]}
    questions = load_open_research_questions(HERE / "questions.json")
    assert len(questions) == 1
    question = questions[0]
    public = research_question_payload(question, include_task_intent=True)
    reference = json.loads(args.reference.read_text())
    assert reference["oracle_sha256"] == sha256(HERE / "numerical_evaluator.py")
    assert reference["validator_sha256"] == sha256(HERE / "validate_reference.py")
    assert reference["matched_feasible"] + reference["matched_infeasible"] == 648
    assert reference["matched_finite_experiment_cases"] == 64
    out.mkdir(parents=True, exist_ok=False)
    reference_ref = write(out / "numerical_reference_validation.json", reference)
    question_ref = write(out / "questions.json", [public])
    deployment_ref = write(out / "deployment.json", {
        "model": MODEL, "quantization": "Q4_K_M", **PINS,
        "weights_path": str(WEIGHTS), "server_path": str(SERVER), "runtime_commit": "4fea119",
        "server_arguments": SERVER_ARGUMENTS, "dynamic_library_path": str(SERVER.parent),
        "hardware": {"platform": platform.platform(), "machine": platform.machine(),
                     "memory_bytes": int(subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True)),
                     "cpu": subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()},
        "active_props": props, "scientific_runtime": asdict(discover_scientific_sandbox_runtime()),
        "request_sampling": {"temperature": 0, "max_tokens": 4096, "parallel_tool_calls": False,
                             "thinking_budget_tokens": None}, "research_calls_before_freeze": 0,
    })
    order = ["free_planning", "same_workflow", "no_cross_role_revision", "full_collaboration"]
    random.Random(20261002).shuffle(order)
    common = dict(provider_name="local", model=MODEL, model_tier="local", max_tokens=4096, temperature=0)
    roles = {
        "theory": asdict(ResearchArchitectConfig(**common, serious_model=MODEL, serious_model_tier="local", serious_max_tokens=4096)),
        "algorithm": asdict(AlgorithmEngineerConfig(**common)), "simulation": asdict(SimulationEngineerConfig(**common)),
        "theory_reviewer": asdict(ArchitectMetricSemanticReviewerConfig(**common)),
        "code_reviewer": asdict(GeneratedCodeSemanticReviewerConfig(**common)),
        "architect": asdict(ArchitectCoordinatorConfig(**common, metric_semantic_reviewer_model=MODEL,
                                                     metric_semantic_reviewer_model_tier="local", metric_semantic_reviewer_max_tokens=4096)),
        "critic": asdict(CriticEvaluatorConfig(**common)),
    }
    workflow = ("Use the same conceptual workflow as the collaborative system: build a reviewable theory checkpoint, "
                "review theory before promoted code; bind and execute exact method source; author a diagnostic experiment; "
                "review the exact frozen sources and protocol; execute separate confirmation; report selected evidence and gaps. "
                "All review here shares your author context and is self-review, not isolated authority. You own all edits and local feedback iteration.")
    configs = {}
    for mode in order:
        collaborative = mode in {"full_collaboration", "no_cross_role_revision"}
        config = {"question_ref": question_ref, "question_id": question.id, "deployment_ref": deployment_ref,
                  "mode": mode, "backend": {"base_url": "http://127.0.0.1:8081/v1", "timeout_s": 300},
                  "roles": roles if collaborative else {key: value for key, value in roles.items() if key not in {"architect", "critic"}}}
        if collaborative:
            config["runtime"] = asdict(ResearchAgentRuntimeConfig(
                n_runs=2000, seed=730103, generated_simulation_timeout_seconds=60,
                theory_scratch_timeout_seconds=20, max_iterations=128, local_model_call_limit=128,
                formal_verification_policy="optional", evaluation_mode="research_eval",
                evaluation_provider="local", evaluation_model_tier="local", evaluation_model=MODEL))
            config["architect_context"] = {"cross_family_evaluation_protocol": {
                "protocol_fingerprint": stable_hash({"study": HERE.name, "public_question": public, "seed": 730103}),
                "candidate_gate_independence_required": True, "post_outcome_fresh_cohort_required": True,
                "confirmatory_candidate_seed_blinding_required": True}}
        else:
            config.update(request={"system_prompt": "Conduct the supplied statistical research using the actual workspace tools. "
                                   "Own all mathematical and source revisions, preserve selected evidence and report unresolved gaps honestly.",
                                   "model": MODEL, "max_tokens": 4096, "temperature": 0, "tool_choice": "auto"},
                          workflow_instructions=workflow if mode == "same_workflow" else "", estimator_ids=["fixed_k_l2"],
                          execution={"n_runs": 2000, "seed": 730103, "timeout_s": 60,
                                     "confirmatory_seeds": [1730106 + index * 1000003 for index in range(128)]},
                          limits={"max_turns": 128, "max_tool_calls": 256, "max_no_progress_turns": 2, "local_model_call_limit": 128})
        configs[mode] = write(out / (mode + ".json"), config)
    evaluator = HERE / "numerical_evaluator.py"
    numerical = {"language": "python", "harness_path": str(evaluator), "harness_sha256": sha256(evaluator),
                 "dependencies": [], "seed": 730109, "replicates": 1, "timeout_seconds": 60}
    task = {"task_id": question.id, "task_intent": question.task_intent,
            "visible_question_hash": stable_hash(_visible_question_hash_payload(public)),
            "hidden_algorithm_evaluator": {**numerical, "required_estimator_id": "fixed_k_l2", "acceptance_checks": [
                {"check_id": "exact_finite_optima", "path": ["all_cases_passed"], "operator": "eq", "expected": True}]},
            "hidden_empirical_evaluator": {**numerical, "acceptance_checks": [
                {"check_id": "finite_mean_compatibility", "path": ["compatible_numerical_experiment"], "operator": "eq", "expected": True}]}}
    task_ref = write(out / "evaluator_task.json", task)
    write(out / "protocol.json", {
        "study_id": HERE.name, "scope": "one_family_four_arm_development_not_official_efficacy_or_full_task_qualification",
        "product_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_files": {path.name: sha256(path) for path in (HERE / "questions.json", evaluator, Path(__file__))},
        "question_ref": question_ref, "deployment_ref": deployment_ref, "task_ref": task_ref, "configs": configs,
        "numerical_reference_validation_ref": reference_ref,
        "draw_order": order, "replicates_per_arm": 1, "independent_families": 1,
        "full_task_mathematical_authority_qualified": False, "official_study_activated": False,
        "external_results_return_to_author": False, "automatic_retry_or_escalation": False,
        "main_test_pool_exclusion": "Entire Truong/Oudre/Vayatis fixed-K segmentation family",
        "resource_boundary": "Same global request ceiling is not equal tokens, tools, realized attempts or scientific computation; report all actual costs.",
        "confirmation_boundary": "Controls start at 1730106; product starts at runtime base 730103. Both use outcome-independent increments 1000003. "
                                 "Private-cohort/authoring visibility and runtime source access are not declared identical.",
        "termination_boundary": "Collect only trusted terminal selected artifacts; failed or pending runs cannot be resumed, salvaged or rescored.",
    })


if __name__ == "__main__":
    main()
