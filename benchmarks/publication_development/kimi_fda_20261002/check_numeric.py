"""Read-only evaluator: the submitted vectors and metrics are not model feedback."""

import argparse
import json
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--actual", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    expected = next(row for row in json.loads((args.reference / "reference.json").read_text())["results"]
                    if row["split_seed"] == args.seed)
    result = {"passed": False, "error": None}
    try:
        predictions = np.load(args.actual / "predictions.npy", allow_pickle=False)
        metrics = json.loads((args.actual / "metrics.json").read_text())
        gold = np.load(args.reference / f"predictions_{args.seed}.npy", allow_pickle=False)
        result.update({"shape_matches": predictions.shape == gold.shape,
                       "predictions_match": bool(np.array_equal(predictions, gold)),
                       "accuracy_matches": bool(np.isfinite(float(metrics["accuracy"])) and
                           abs(float(metrics["accuracy"]) - expected["accuracy"]) <= 1e-12),
                       "parameters_match": metrics["best_params"] == expected["best_params"],
                       "seed_matches": metrics["split_seed"] == args.seed})
        result["passed"] = all(result[key] for key in ("shape_matches", "predictions_match",
                               "accuracy_matches", "parameters_match", "seed_matches"))
    except Exception as error:
        result["error"] = str(error)
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()
