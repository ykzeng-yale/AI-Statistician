"""One frozen source-review qualification, not a research-system draw."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
import urllib.request

from ai_statistician.agentic_api_workspace import FileGrant, run_file_session
from ai_statistician.agentic_scientific_review import ScientificReviewWorkspace
from benchmarks.publication_deployment_qualification_20261003.observe import digest, write_json
from benchmarks.publication_deployment_qualification_20261003.observe_retained_session import RecordingBackend
from scripts.run_agentic_api import load_config


def run_cases(*, plan, backend, config, identity, prompt, output):
    if not plan["cases"]:
        raise ValueError("A qualification requires the frozen nonempty control panel")
    output.mkdir(parents=True, exist_ok=False)
    bank_root = Path(plan["bank_root"]).resolve()
    bank = json.loads((bank_root / "bank.json").read_text())
    requirements = output / "requirements.json"
    write_json(requirements, bank["rubric"])
    ids = tuple(row["claim_id"] for row in bank["rubric"]["claims"])
    rows = [{"id": case["id"], "state": "NOT_RUN"} for case in plan["cases"]]
    result = {"status": "INCOMPLETE", "scientific_qualification": "NOT_ESTABLISHED",
              "scope": plan["scope"], "cases": rows}
    started = time.monotonic()
    for case, row in zip(plan["cases"], rows):
        root = output / case["id"]
        root.mkdir()
        try:
            workspace = ScientificReviewWorkspace((
                FileGrant("task.md", bank_root / bank["question_file"]),
                FileGrant("requirements.json", requirements),
                *(FileGrant(f"sources/reference-{i}.md", bank_root / name)
                  for i, name in enumerate(bank["reference_files"])),
                *(FileGrant(f"candidate/document-{i}.md", bank_root / name)
                  for i, name in enumerate(case["files"])),
                FileGrant("review.md", root / "review.md", writable=True),
            ), ids)
            review = run_file_session(backend=backend, workspace=workspace, prompt=prompt,
                model=config["model"], max_tokens=config["max_tokens"], temperature=config["temperature"],
                max_turns=config["max_turns"], session_dir=root / "session", session_id=case["id"],
                deployment_identity=identity)
            actual = {item["id"]: item["status"] for item in review.terminal_payload["verdicts"]}
            status = "FAIL" if "FAIL" in actual.values() else "UNCERTAIN" if "UNCERTAIN" in actual.values() else "PASS"
            row.update(state="COMPLETED", actual=actual, status=status, expected=case["expected_status"],
                       labels_match=status == case["expected_status"], report_sha256=digest(root / "review.md"),
                       session_sha256=digest(root / "session/result.json"), usage=dict(review.provider_usage))
        except Exception as exc:
            row.update(state="ERROR", error={"type": type(exc).__name__, "message": str(exc)})
            break
        finally:
            write_json(root / "case_result.json", row)
    else:
        result["status"] = ("LABELS_MATCHED_ARGUMENT_EXAMINATION_REQUIRED"
                            if all(row["labels_match"] for row in rows) else "LABEL_MISMATCH")
    result["elapsed_seconds"] = time.monotonic() - started
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    for ref in plan["inputs"]:
        if digest(Path(ref["path"])) != ref["sha256"]:
            raise ValueError("Frozen qualification input changed: " + ref["path"])
    config, identity = load_config(Path(plan["api_config"]), model=plan["model"])
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(config["base_url"].rstrip("/") + "/models", timeout=10) as reply:
        served = json.load(reply)
    if [(row["id"], row["max_model_len"]) for row in served["data"]] != [(plan["model"], plan["context"])]:
        raise ValueError("Served model/context differs from the frozen condition")
    output = Path(plan["output"]).resolve()
    wire = output.parent / (output.name + "-wire")
    wire.mkdir(parents=True, exist_ok=False)
    backend = RecordingBackend(wire, base_url=config["base_url"], timeout_s=config["timeout_seconds"])
    result = run_cases(plan=plan, backend=backend, config=config,
        identity={**identity, "plan_sha256": digest(args.plan), "served": served},
        prompt=Path(plan["prompt"]).read_text(), output=output)
    result.update(model_attempts=backend.attempts,
        inputs_unchanged=all(Path(ref["path"]).is_file() and digest(Path(ref["path"])) == ref["sha256"]
                             for ref in plan["inputs"]))
    if not result["inputs_unchanged"]:
        result["status"] = "INPUTS_CHANGED"
    write_json(output / "result.json", result)
    print(json.dumps({"status": result["status"], "model_attempts": backend.attempts,
                      "scientific_qualification": result["scientific_qualification"]}), flush=True)
    return 0 if result["status"] == "LABELS_MATCHED_ARGUMENT_EXAMINATION_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
