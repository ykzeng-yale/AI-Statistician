"""Prepare fresh, arm-isolated inputs; never alter consumed HC0 observations."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil


def prepare(destination: Path, arm: str) -> None:
    here = Path(__file__).resolve().parent
    root = here.parents[1]
    destination.mkdir(parents=True, exist_ok=False)
    task = destination / "task"
    source = task / "program_0" / "src"
    source.mkdir(parents=True)
    for name in ("task.md", "evaluate.py"):
        shutil.copy2(here / name, task / name)
    (source / "program.py").write_text(
        '"""Unimplemented candidate seed, not a baseline solution."""\n'
        'def run_estimator(request):\n'
        '    raise NotImplementedError("Author the requested method")\n'
    )
    upstream = root / "third_party" / "ai-scientist-v3" / "examples" / "circpack"
    shutil.copy2(upstream / "program_0" / "program_spec.toml", source.parent)
    shutil.copy2(upstream / "capture.py", task / "capture.py")
    (task / "requirements.txt").write_text(
        "numpy==2.4.2\nscipy==1.17.1\nstatsmodels==0.14.6\n"
    )
    (task / "rubrics.json").write_text(json.dumps([{
        "id": "computational_compliance", "type": "metric",
        "description": "All specified numerical comparisons completed; not theory acceptance",
        "metric": "combined_score", "operator": ">=", "threshold": 1.0,
    }], indent=2) + "\n")
    if arm == "statistical":
        public = task / "resources" / "search"
        public.mkdir(parents=True)
        shutil.copytree(root / "skills" / "statistical-research", public / "statistical-research")
        shutil.copy2(root / "integrations" / "agentic-scientist" / "prompts" / "investigate.md",
                     destination / "investigate.md")
    hashes = {str(path.relative_to(destination)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in sorted(destination.rglob("*")) if path.is_file()}
    (destination / "prepared_inputs.json").write_text(json.dumps({"arm": arm, "files": hashes}, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--arm", choices=("stock", "statistical"), required=True)
    args = parser.parse_args()
    prepare(args.destination, args.arm)
