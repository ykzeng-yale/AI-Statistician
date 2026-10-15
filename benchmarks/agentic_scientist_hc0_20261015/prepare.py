"""Stage the exposed HC0 task for an unmodified upstream native investigation."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    source = root / "benchmarks/research_l0_questions_20260814.json"
    question = json.loads(source.read_text())["questions"][0]
    run = args.destination.resolve()
    run.mkdir(exist_ok=False)
    task = run / "task"
    task.mkdir(exist_ok=False)
    (task / "program_0/src").mkdir(parents=True)
    (task / "task.md").write_text(
        "# Goal\n\n" + question["description"] + "\n\n"
        "Keep your derivation in src/theory.md and simulation code and findings "
        "with the candidate. The public evaluator checks only the run_estimator "
        "implementation against statsmodels, not theory or scientific completion. "
        "The seed is deliberately unimplemented; do not evaluate it.\n"
    )
    (task / "program_0/src/program.py").write_text(
        '"""Implement the public task; no baseline solution is supplied."""\n'
        'def run_estimator(request):\n    raise NotImplementedError("Implement the public HC0 task")\n'
    )
    upstream = root / "third_party/ai-scientist-v3/examples/circpack"
    shutil.copy2(upstream / "program_0/program_spec.toml", task / "program_0/program_spec.toml")
    shutil.copy2(upstream / "capture.py", task / "capture.py")
    shutil.copy2(Path(__file__).with_name("evaluate.py"), task / "evaluate.py")
    (task / "requirements.txt").write_text("numpy==2.4.2\nscipy==1.17.1\nstatsmodels==0.14.6\n")
    home = run / "home"
    config_dir = home / ".config/opencode"
    config_dir.mkdir(parents=True, exist_ok=False)
    config = json.loads((root / "integrations/agentic-scientist/opencode.local.json").read_text())
    config["autoupdate"] = False
    config["provider"]["local-qwen"]["models"]["Qwen3-4B-Instruct-2507"]["options"] = {
        "temperature": 0.7, "topP": 0.8, "maxOutputTokens": 16384,
    }
    (config_dir / "opencode.json").write_text(json.dumps(config, indent=2) + "\n")
    manifest = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in [source, *sorted(task.rglob("*"))] if path.is_file()}
    (run / "prepared_inputs.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(task)


if __name__ == "__main__":
    main()
