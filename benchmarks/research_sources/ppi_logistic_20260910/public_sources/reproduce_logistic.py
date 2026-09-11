"""Seeded numeric replay of the unchanged upstream logistic CI helper."""
import json
import runpy
from pathlib import Path

import numpy as np


def main():
    helper = runpy.run_path("test_logistic.py")["ppi_logistic_ci_subtest"]
    alphas = np.array([0.05, 0.1, 0.2])
    counts = np.zeros(3, dtype=int)
    for index in range(1000):
        np.random.seed(761000 + index)
        counts += helper(index, alphas).astype(int)
    result = {
        "upstream_helper": "tests/test_logistic.py:ppi_logistic_ci_subtest",
        "source_commit": "3d1f0c668444907b39bd045cb9dd38e479ce7dd6",
        "replicates": 1000,
        "seed_rule": "numpy.random.seed(761000 + replicate_index)",
        "labeled_size": 1000,
        "unlabeled_size": 10000,
        "dimension": 1,
        "alphas": alphas.tolist(),
        "included_counts": counts.tolist(),
        "coverage": (counts / 1000).tolist(),
    }
    text = json.dumps(result, sort_keys=True)
    Path("ppi_logistic_result.json").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
