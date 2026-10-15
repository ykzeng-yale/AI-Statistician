"""Run one frozen assessor qualification using the existing semantic-review loop."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

from ai_statistician.theory_semantic_gold_judge import run_theory_semantic_gold_judge
from benchmarks.publication_deployment_qualification_20261003.observe import digest, write_json
from benchmarks.publication_deployment_qualification_20261003.observe_retained_session import RecordingBackend


def settings_match(actual, expected):
    if actual.keys() != expected.keys():
        return False
    for key, value in expected.items():
        observed = actual[key]
        if key in {"temperature", "top_p", "min_p"}:
            if any(type(item) not in (int, float) or not math.isfinite(item)
                   for item in (observed, value)):
                return False
            if not math.isclose(observed, value, rel_tol=0, abs_tol=1e-7):
                return False
        elif type(observed) is not type(value) or observed != value:
            return False
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    output = Path(plan["output"]).resolve()
    output.mkdir(parents=True, exist_ok=False)
    wire = output / "wire"
    wire.mkdir()
    result = {"scope": plan["scope"], "plan_sha256": digest(args.plan),
              "runner_sha256": digest(Path(__file__)), "status": "pre_call_checks",
              "scientific_qualification": "not_established", "model_attempts": 0,
              "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()}
    started, backend = time.monotonic(), None
    try:
        for ref in plan["inputs"]:
            if digest(Path(ref["path"])) != ref["sha256"]:
                raise ValueError("frozen qualification input changed: " + ref["path"])
        assets = json.loads(Path(plan["asset_plan"]).read_text())
        deployment_files = [(Path(assets["download"]["verified_path"]).resolve(), assets["weights_sha256"]),
                            (Path(assets["server_binary"]), assets["server_sha256"]),
                            *[(Path(assets["library_directory"]) / name, sha)
                              for name, sha in assets["library_sha256"].items()]]
        result["deployment_files"] = [{"path": str(path), "sha256": digest(path)}
                                      for path, _ in deployment_files]
        if any(ref["sha256"] != expected for ref, (_, expected) in zip(result["deployment_files"], deployment_files)):
            raise ValueError("deployment asset changed")
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        observed = {}
        for route, name in (("/props", "props"), ("/v1/models", "models")):
            with opener.open(plan["server_url"] + route, timeout=10) as reply:
                observed[name] = json.load(reply)
            write_json(output / (name + ".json"), observed[name])
        props = observed["props"]
        settings = props["default_generation_settings"]
        actual = {"model": props["model_alias"], "model_path": props["model_path"],
                  "model_ids": [row["id"] for row in observed["models"]["data"]],
                  "context": settings["n_ctx"], "slots": props["total_slots"],
                  "template_sha256": hashlib.sha256(props["chat_template"].encode()).hexdigest(),
                  **{key: settings["params"][key] for key in ("seed", "temperature", "top_k", "top_p", "min_p")}}
        if not settings_match(actual, plan["active_settings"]):
            raise ValueError("active model/template/decoding differs from prospective condition")
        result["active_settings"] = actual
        result["hardware"] = subprocess.check_output(
            ["sysctl", "hw.memsize", "hw.ncpu", "machdep.cpu.brand_string"], text=True)
        result["os_version"] = subprocess.check_output(["sw_vers"], text=True)
        result["python"] = {"version": sys.version, "executable": str(Path(sys.executable).resolve()),
                            "sha256": digest(Path(sys.executable).resolve())}
        root = Path(plan["bank"]).parent
        bank = json.loads(Path(plan["bank"]).read_text())

        def document(name):
            path = root / name
            return {"path": "submission.md", "content": path.read_text(), "sha256": digest(path)}

        def cases(rows):
            return [{"case_id": row["case_id"], "expected_status": row["expected_status"],
                     "documents": [{**document(name), "path": f"document-{i}.md"}
                                   for i, name in enumerate(row["files"])]} for row in rows]

        write_json(output / "before_inference.json", result)
        backend = RecordingBackend(wire, base_url=plan["server_url"] + "/v1", timeout_s=plan["request_timeout_seconds"])
        judgment = run_theory_semantic_gold_judge(
            provider=backend, workspace_root=output / "review_sessions", task_id=bank["task_id"],
            visible_question={"id": bank["task_id"], "question": (root / bank["question_file"]).read_text()},
            candidate_documents=[document(name) for name in bank["candidate_files"]],
            reference_documents=[document(name) for name in bank["reference_files"]],
            rubric=bank["rubric"], calibration_cases=cases(bank["calibration"]),
            candidate_mode_negative_cases=cases(bank["candidate_mode_negative"]),
            model=plan["active_settings"]["model"], model_tier="local",
            max_tokens=plan["max_tokens"], candidate_adjudication_strategy="integrated_single")
        write_json(output / "judgment.json", judgment)
        result.update(status="review_protocol_completed", semantic_judge_calibrated=judgment["semantic_judge_calibrated"],
                      candidate_status=judgment["candidate_status"], judgment_sha256=digest(output / "judgment.json"))
    except Exception as exc:
        result.update(status="stopped", error={"type": type(exc).__name__, "message": str(exc)})
    finally:
        result["model_attempts"] = backend.attempts if backend else 0
        result["elapsed_seconds"] = time.monotonic() - started
        result["limitations"] = plan["limitations"]
        result["inputs_unchanged"] = all(Path(ref["path"]).is_file() and
                                         digest(Path(ref["path"])) == ref["sha256"] for ref in plan["inputs"])
        write_json(output / "result.json", result)
    print(json.dumps(result), flush=True)
    return 0 if result["status"] == "review_protocol_completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
