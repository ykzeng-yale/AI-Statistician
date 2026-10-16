"""Prepare a new full-study native API condition from the retained HC0 evaluator."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import shutil


HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "agentic_scientist_hc0_bouchet_20261015"


def prepare(destination: Path, arm: str) -> None:
    runpy.run_path(str(PREVIOUS / "prepare.py"))["prepare"](destination, arm)
    task = destination / "task"
    shutil.copy2(HERE / "task.md", task / "task.md")
    rubrics = json.loads((task / "rubrics.json").read_text())
    (task / "rubrics.json").unlink()
    rubrics.extend([
        {"id": "theory", "type": "review", "description": "Assess the complete stated argument, its assumptions and every substantive limit or residual-substitution step; report unresolved gaps without inferring proof from numerical agreement."},
        {"id": "method_study", "type": "review", "description": "Assess exact theory-to-code correspondence and whether the study explanation faithfully addresses the prespecified scientific question, methods, uncertainty and limitations."},
    ])
    (task / "target_rubrics.json").write_text(json.dumps(rubrics, indent=2) + "\n")
    (task / "public_outputs.json").write_text(json.dumps([
        {"path": "summaries.json", "kind": "table", "media_type": "application/json"},
        {"path": "study.json", "kind": "derived", "media_type": "application/json"},
    ], indent=2) + "\n")
    plan = task / "posthoc"
    plan.mkdir()
    candidate = {
        "id": "study_interpretation", "title": "Interpret the completed prespecified study",
        "family": "statistical_study_report",
        "hypothesis": "Determine what the observed comparisons and stated argument support, including negative or unresolved findings.",
        "relevance_reason": "Join the exact scientific source with actual full-study evidence.",
        "feasibility_reason": "Read existing summaries without repeating evaluation or adding computation.",
        "required_artifacts": ["evidence/summaries.json", "evidence/study.json", "program_0/src"],
        "requires_retrain": False,
        "implementation_plan": ["Read the source and complete summaries.", "Write the main interpretation and complete supporting appendix with failures, uncertainty and limits."],
        "expected_claim": "Only conclusions supported by the selected source and observed outputs.",
        "expected_outputs": ["analysis_summary.md", "appendix.md"],
    }
    (plan / "posthoc_bundle.json").write_text(json.dumps({"decision": "propose_analyses", "analyses": [candidate]}, indent=2) + "\n")
    (plan / "posthoc_selection.json").write_text(json.dumps({"accepted": [{"id": candidate["id"]}], "rejected": []}, indent=2) + "\n")
    hashes = {str(path.relative_to(destination)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in sorted(destination.rglob("*")) if path.is_file() and path.name != "prepared_inputs.json"}
    (destination / "prepared_inputs.json").write_text(json.dumps({"arm": arm, "files": hashes,
        "scope": "New exposed development preparation; original evaluator and consumed outcomes are unchanged."}, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--arm", choices=("stock", "statistical"), required=True)
    args = parser.parse_args()
    prepare(args.destination, args.arm)
