"""One declared full StepMix development draw, without external scoring."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import time
import urllib.error
import urllib.request

from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_source_library import load_research_source_execution_spec, load_research_source_snapshot
from ai_statistician.scientific_sandbox import discover_scientific_sandbox_runtime
from ai_statistician.theory_workspace import theory_scratchpad_client_tool
from benchmarks.publication.execute_draw import _file_ref, _stop_owned_group, run_declared_draw


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "runs/stepmix_integrated_development_20261015"
BASE = ROOT / "runs/publication_host_conditions_20261004/standalone/stepmix/full_collaboration.json"
ASSETS = ROOT / "benchmarks/publication_deployment_qualification_20261003/plan.json"


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
    return _file_ref(path)


def checked(path, digest):
    ref = _file_ref(path)
    if ref["sha256"] != digest:
        raise ValueError("declared input changed: " + str(path))
    return ref


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    observation = {"started_at": datetime.now(timezone.utc).isoformat(), "status": "PREPARING",
                   "scientific_acceptance": "UNASSESSED", "official_study_activated": False,
                   "draw_started": False}
    server = None
    try:
        observation["base_ref"] = checked(BASE, "a62ed2d40702369be4febf784b11f1b822b45c0947bae84554fbcefed65f41f6")
        observation["asset_plan_ref"] = checked(ASSETS, "603b40c084c3f0375a7fbbebbdd1fefbb759648a7a6e59017b668bd04c73e149")
        config, assets = json.loads(BASE.read_text()), json.loads(ASSETS.read_text())
        observation["product_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        observation["runner_ref"] = _file_ref(Path(__file__))
        observation["machine"] = subprocess.check_output(["sysctl", "hw.memsize", "hw.ncpu", "machdep.cpu.brand_string"], text=True)
        for field in ("question_ref", "source_snapshot_ref", "source_execution_ref"):
            ref = config[field]
            checked(Path(ref["path"]), ref["sha256"])
        native = config["native_execution_refs"]["python"]
        checked(Path(native["path"]), native["sha256"])
        if any(os.environ.get(name) for name in ("AI_STATISTICIAN_NATIVE_R_CONFIG", "AI_STATISTICIAN_NATIVE_PROJECT_CONFIG")):
            raise ValueError("undeclared native environment is set")
        configured = os.environ.get("AI_STATISTICIAN_NATIVE_PYTHON_CONFIG")
        if configured and Path(configured).resolve() != Path(native["path"]):
            raise ValueError("conflicting native Python configuration")
        os.environ["AI_STATISTICIAN_NATIVE_PYTHON_CONFIG"] = native["path"]
        runtime = discover_scientific_sandbox_runtime()
        profiles = theory_scratchpad_client_tool().input_schema["properties"]["execution_profile"]["enum"]
        if not runtime.native_available("python") or "scientific_native_python" not in profiles:
            raise ValueError("declared native Python is absent from the source-owner tool")
        sources = load_research_source_snapshot(Path(config["source_snapshot_ref"]["path"]))
        load_research_source_execution_spec(Path(config["source_execution_ref"]["path"]), research_sources=sources)
        read = sources.read("paper/article.txt", line_start=1, line_end=12)
        observation["source_access_check"] = {key: read[key] for key in ("document_id", "sha256", "content_sha256")}
        weights = (ROOT / assets["download"]["verified_path"]).resolve()
        observation["assets"] = [checked(weights, assets["weights_sha256"]), checked(Path(assets["server_binary"]), assets["server_sha256"]),
            *(checked(Path(assets["library_directory"]) / name, digest) for name, digest in assets["library_sha256"].items())]
        with socket.socket() as check:
            check.bind(("127.0.0.1", 8081))
        command = [assets["server_binary"], *assets["server_arguments"]]
        command = [str(weights) if arg == "{verified_weights}" else arg for arg in command]
        command[command.index("--seed") + 1] = "2026101502"
        observation["server_command"] = command
        config["runtime"]["seed"] = 730215
        config["architect_context"] = {"cross_family_evaluation_protocol": {
            "protocol_fingerprint": stable_hash({"development": OUT.name, "question_ref": config["question_ref"], "seed": 730215}),
            "candidate_gate_independence_required": True, "post_outcome_fresh_cohort_required": True,
            "confirmatory_candidate_seed_blinding_required": True},
            "source_access_note": "The supplied snapshot contains the primary paper/article.txt and paper/article.pdf plus package and replication sources. Public discovery can read preprint original source as well as metadata. Compare editions explicitly; previous experiment results are not inputs."}
        config["source_discovery"] = {"source_horizon": "2026-10-15", "state_dir": "discovery", "timeout_seconds": 30.0}
        with (OUT / "server.stdout").open("xb") as stdout, (OUT / "server.stderr").open("xb") as stderr:
            server = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "DYLD_LIBRARY_PATH": assets["library_directory"]}, start_new_session=True)
        observation["server_pid"] = server.pid
        write(OUT / "started_process.json", {"pid": server.pid, "command": command})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        deadline = time.monotonic() + 180
        while True:
            if server.poll() is not None:
                raise RuntimeError("owned model server exited during startup")
            try:
                with opener.open("http://127.0.0.1:8081/props", timeout=5) as reply:
                    props = json.load(reply)
                break
            except (OSError, urllib.error.URLError):
                if time.monotonic() >= deadline:
                    raise TimeoutError("owned server startup deadline")
                time.sleep(1)
        with opener.open("http://127.0.0.1:8081/v1/models", timeout=5) as reply:
            models = json.load(reply)
        observation["props_ref"] = write(OUT / "props.json", props)
        observation["models_ref"] = write(OUT / "models.json", models)
        settings = props["default_generation_settings"]
        expected = {"seed": 2026101502, "temperature": 0.7, "top_k": 20, "top_p": 0.8, "min_p": 0.0}
        if (settings["n_ctx"] != 131072 or props["total_slots"] != 1
            or props["model_alias"] != assets["model"] or props["model_path"] != str(weights)
            or [row["id"] for row in models["data"]] != [assets["model"]]
            or hashlib.sha256(props["chat_template"].encode()).hexdigest() != assets["expected_chat_template_sha256"]
            or any(abs(settings["params"][key] - value) > 1e-6 for key, value in expected.items())):
            raise ValueError("active model differs from the prospective condition")
        config["deployment_ref"] = write(OUT / "deployment.json", {
            "model": assets["model"], "weights_sha256": assets["weights_sha256"], "quantization": "Q4_K_M",
            "actual_props_ref": observation["props_ref"], "actual_models_ref": observation["models_ref"],
            "server_command": command, "sampling": expected, "context_tokens": 131072,
            "scientific_capacity_qualified": False, "official_study_activated": False})
        observation["config_ref"] = write(OUT / "config.json", config)
        write(OUT / "prepared.json", observation)
        observation["draw_started"] = True
        print("Starting one fresh complete StepMix methods-research development draw.", flush=True)
        observation["draw_terminal"] = run_declared_draw(config_path=OUT / "config.json", record_dir=OUT / "execution")
        observation["status"] = "TERMINATED"
    except BaseException as exc:
        observation.update(status="FAILED", exception_type=type(exc).__name__, exception=str(exc))
        raise
    finally:
        if server is not None:
            observation["server_termination_signals"] = _stop_owned_group(server, 10)
            observation["server_returncode"] = server.returncode
        observation["finished_at"] = datetime.now(timezone.utc).isoformat()
        write(OUT / "observation.json", observation)
    print(json.dumps(observation, indent=2))


if __name__ == "__main__":
    main()
