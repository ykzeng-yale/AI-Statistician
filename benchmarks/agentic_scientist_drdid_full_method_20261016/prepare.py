"""Stage one fresh full-method task; no science source edits or model calls."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import subprocess


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREP = ROOT / "benchmarks/publication_reference_qualification_20261016/drdid"


def prepare(destination, sources):
    inventory = json.loads((PREP / "source_inventory.json").read_text())
    for row in inventory["extracted_files"]:
        path = sources / row["group"] / row["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError(f"Original source differs from its acquisition identity: {path}")
    if subprocess.check_output(["git", "-C", str(sources / "package"), "rev-parse", "HEAD"], text=True).strip() != inventory["package_commit"]:
        raise ValueError("Package source is not the declared pinned commit")
    runpy.run_path(str(ROOT / "scripts/prepare_agentic_task.py"))["prepare_task"](HERE / "brief.md", destination)
    public = destination / "resources/search/drdid"
    public.mkdir()
    shutil.copytree(sources / "replication-source-20261016", public / "replication")
    shutil.copytree(sources / "arxiv-source-20261016", public / "paper/native")
    for name in ("article.txt", "appendix.txt", "SantAnna_Zhao_DRDID.pdf", "DR-DID_Appendix.pdf"):
        shutil.copy2(sources / name, public / "paper" / name)
    shutil.copy2(PREP / "source_inventory.json", public)
    (public / "package").mkdir()
    package = subprocess.run(["git", "-C", str(sources / "package"), "archive", inventory["package_commit"]],
                             stdout=subprocess.PIPE, check=True)
    import io
    import tarfile
    with tarfile.open(fileobj=io.BytesIO(package.stdout)) as archive:
        archive.extractall(public / "package", filter="data")
    shutil.copy2(HERE / "evaluate.py", destination)
    upstream = ROOT / "third_party/ai-scientist-v3/examples/circpack"
    shutil.copy2(upstream / "capture.py", destination)
    seed = destination / "program_0"
    (seed / "src").mkdir(parents=True)
    shutil.copy2(upstream / "program_0/program_spec.toml", seed)
    (seed / "src/program.py").write_text('raise NotImplementedError("Author the full theory and study project")\n')
    (destination / "requirements.txt").write_text("")
    rubrics = [
        {"id": "full_execution", "type": "metric", "metric": "records_complete", "operator": ">=", "threshold": 1,
         "description": "Complete full-study and application record accounting, not statistical correctness"},
        {"id": "argument", "type": "review", "description": "Assess whether the candidate establishes its stated panel and repeated-cross-section identification, robustness and inference/efficiency claims under explicit applicable assumptions. FAIL means a demonstrated error or missing required argument; UNCERTAIN means unresolved correctness despite a supplied argument. Do not infer proof from execution or merely quote published theorem numbers. Report claim-located findings."},
        {"id": "method_correspondence", "type": "review", "description": "Assess whether the exact source implements the supplied ordinary Monte Carlo and NSW application scope, preserves original DGP/method/inference semantics and all failures, computes justified summaries/Monte Carlo uncertainty and faithfully connects theory to code. This is source review, not observed numerical-result assessment or whole-paper historical reproduction."},
    ]
    (destination / "target_rubrics.json").write_text(json.dumps(rubrics, indent=2) + "\n")
    (destination / "public_outputs.json").write_text(json.dumps([
        {"path": name, "kind": kind, "media_type": media} for name, kind, media in (
            ("study_summary.csv", "table", "text/csv"), ("application.csv", "table", "text/csv"),
            ("study_notes.md", "derived", "text/markdown"), ("execution_observation.json", "derived", "application/json"))], indent=2) + "\n")
    posthoc = destination / "posthoc"
    posthoc.mkdir()
    analysis = {"id": "method_report", "title": "Report the completed DR-DID investigation",
        "family": "statistical_method_report", "hypothesis": "Determine which theory and empirical conclusions are supported by the exact candidate and observed full study.",
        "relevance_reason": "Connect the inferential method to comparative results and the substantive NSW application.",
        "feasibility_reason": "Interpret existing public source, review and result tables without new execution.",
        "required_artifacts": ["evidence/study_summary.csv", "evidence/application.csv", "evidence/study_notes.md", "evidence/execution_observation.json", "program_0/src"],
        "requires_retrain": False, "implementation_plan": ["Read source arguments, review, actual tables and execution limits.", "Write a coherent main report and full empirical appendix, preserving gaps, failures and source/version differences."],
        "expected_claim": "Only conclusions actually supported; internal AI review is not independent scientific acceptance.",
        "expected_outputs": ["analysis_summary.md", "appendix.md"]}
    (posthoc / "posthoc_bundle.json").write_text(json.dumps({"decision": "propose_analyses", "analyses": [analysis]}, indent=2) + "\n")
    (posthoc / "posthoc_selection.json").write_text(json.dumps({"accepted": [{"id": analysis["id"]}], "rejected": []}, indent=2) + "\n")
    hashes = {str(path.relative_to(destination)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in sorted(destination.rglob("*")) if path.is_file()}
    (destination / "prepared_inputs.json").write_text(json.dumps({"files": hashes,
        "scope": "Original-byte sources and fresh full-method task; no model calls, executed research or qualification"}, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--sources", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.destination, args.sources)
