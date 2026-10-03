"""Exercise installed local tools from a fresh workspace, without a model or gold."""

import json
from pathlib import Path
import sys

import ai_statistician
from ai_statistician.scientific_sandbox import execute_scientific_sandbox


def main():
    output = Path(sys.argv[1]).resolve()
    output.mkdir()
    python = """import numpy as np
import scipy
import pandas
import sklearn
import statsmodels
import sympy
from helper import marker

def run_sandbox(seed, replicates):
    return {"marker": int(np.sum([seed, replicates])), "project": marker()}
"""
    r = """source("helper.R")
run_sandbox <- function(seed, replicates) {
    list(marker = sum(c(seed, replicates)), project = marker())
}
"""
    results = []
    for language, source, dependencies, helper_path, helper_source in (
        ("python", python, ["numpy", "scipy", "pandas", "scikit-learn", "statsmodels", "sympy"],
         "helper.py", 'def marker(): return "local-project"\n'),
        ("r", r, ["base", "stats"], "helper.R", 'marker <- function() "local-project"\n'),
    ):
        result = execute_scientific_sandbox(
            sandbox_dir=output / language, artifact_id="installed-" + language,
            language=language, code=source, dependencies=dependencies,
            project_files=[{"path": helper_path, "content": helper_source}],
            seed=13, replicates=5, timeout_s=60,
        )
        assert result.status == "EXECUTED", result.errors
        assert result.metrics == {"marker": 18, "project": "local-project"}, result.metrics
        assert Path(result.code_path).read_text() == source
        failure_helper = ('def marker(): raise RuntimeError("installed raw observation")\n'
                          if language == "python" else
                          'marker <- function() stop("installed raw observation")\n')
        failed = execute_scientific_sandbox(
            sandbox_dir=output / (language + "-failure"), artifact_id="installed-failure-" + language,
            language=language, code=source, dependencies=dependencies,
            project_files=[{"path": helper_path, "content": failure_helper}],
            seed=13, replicates=5, timeout_s=60,
        )
        assert failed.status == "FAILED" and "installed raw observation" in failed.stderr_summary
        assert Path(failed.code_path).read_text() == source
        assert Path(failed.project_file_paths[helper_path]).read_text() == failure_helper
        results.extend([result.to_json(), failed.to_json()])
    print(json.dumps({
        "scope": "synthetic installed-tool conformance; not a statistical result",
        "installed_package": ai_statistician.__file__, "model_calls": 0,
        "execution_records": results,
    }, indent=2))


if __name__ == "__main__":
    main()
