"""One external numerical inspection of each frozen final pilot selection."""

import argparse
import json
from pathlib import Path

from ai_statistician.client_tool_loop import read_hash_bound_utf8_file
from ai_statistician.research_schema import load_open_research_questions
from ai_statistician.scientific_sandbox import ScientificEstimatorBinding
from benchmarks.publication.evaluate_final_artifacts import evaluate_final_research_artifacts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--draw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    protocol = json.loads(args.protocol.read_text())
    assert args.mode in protocol["configs"]
    files = {}
    for name in ("question_ref", "task_ref"):
        text, errors = read_hash_bound_utf8_file(protocol[name])
        if errors:
            raise ValueError(errors)
        files[name] = text
    frozen = json.loads((args.draw / "frozen_draw.json").read_text())
    assert frozen["study_provenance"]["config_ref"] == protocol["configs"][args.mode]
    public = load_open_research_questions(Path(protocol["question_ref"]["path"]))[0]
    final_path = args.draw / "final_material.json"
    args.out.mkdir(parents=True, exist_ok=False)
    if not final_path.exists():
        result = {"mode": args.mode, "task_passed": False, "final_selection": "missing",
                  "dimension_status": {name: {"status": "missing"} for name in ("theory", "scientific_code", "empirical")},
                  "unselected_candidates_salvaged": False}
    else:
        final = json.loads(final_path.read_text())
        material = final["material"]
        result = evaluate_final_research_artifacts(
            question=public, task=json.loads(files["task_ref"]), submission_identity=final["submission_identity"],
            project_root=Path(__file__).resolve().parents[3], out_dir=args.out / "common_outcome",
            theory_documents=material["theory_documents"],
            estimator_bindings=tuple(ScientificEstimatorBinding(**row) for row in material["estimator_bindings"]),
            empirical_artifact=material["empirical_artifact"],
        )
        result["mode"] = args.mode
    with (args.out / "pilot_outcome.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
