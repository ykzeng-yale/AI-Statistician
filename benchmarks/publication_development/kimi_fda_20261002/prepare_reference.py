"""Evaluator-only source-derived FDA reference variants, never an agent tool."""

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import skfda


AUTHOR_SHA = "a256cf7a4dee6195ce976fd22f34bab4a52b5b11010f507c1315c5f66467288b"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author", type=Path, required=True)
    parser.add_argument("--data-cache", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    assert hashlib.sha256(args.author.read_bytes()).hexdigest() == AUTHOR_SHA
    args.out.mkdir(parents=True, exist_ok=False)
    os.environ["SCIKIT_LEARN_DATA"] = str(args.data_cache.resolve())
    X, y = skfda.datasets.fetch_phoneme(return_X_y=True)
    np.savez(args.out / "phoneme.npz", curves=X.data_matrix[..., 0],
             grid_points=X.grid_points[0], labels=y)
    tree = ast.parse(args.author.read_text())
    start = next(i for i, node in enumerate(tree.body)
                 if isinstance(node, ast.ImportFrom) and node.module == "sklearn.model_selection")
    stop = next(i for i in range(start, len(tree.body))
                if isinstance(tree.body[i], ast.Expr) and isinstance(tree.body[i].value, ast.Call)
                and isinstance(tree.body[i].value.func, ast.Name) and tree.body[i].value.func.id == "print")
    body = tree.body[start:stop + 1]
    seed_calls = [node for statement in body for node in ast.walk(statement)
                  if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                  and node.func.id == "train_test_split"]
    assert len(seed_calls) == 1
    seed_arg = next(arg for arg in seed_calls[0].keywords if arg.arg == "random_state")
    assert isinstance(seed_arg.value, ast.Constant) and seed_arg.value.value == 0
    seed_arg.value = ast.Name(id="split_seed", ctx=ast.Load())
    compiled = compile(ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])),
                       str(args.author), "exec")
    results = []
    for seed in (0, 17):
        namespace = {"skfda": skfda, "split_seed": seed}
        exec(compiled, namespace)
        predictions = namespace["grid"].predict(namespace["X_test"])
        np.save(args.out / f"predictions_{seed}.npy", predictions)
        results.append({"split_seed": seed, "accuracy": float(namespace["score"]),
                        "best_params": namespace["grid"].best_params_,
                        "train_count": len(namespace["y_train"]), "test_count": len(namespace["y_test"])})
    assert f'{results[0]["accuracy"]:.3}' == "0.879"
    (args.out / "reference.json").write_text(json.dumps({
        "source_sha256": AUTHOR_SHA,
        "adaptation": "Original Section 3.5 AST only; replace split random_state 0 with declared seed. No algorithm or original source file edit. Dataset reloaded from the pinned original cache.",
        "results": results}, indent=2) + "\n")
    print(json.dumps({"prepared": True, "variants": len(results), "data_shape": list(X.data_matrix.shape)}))


if __name__ == "__main__":
    main()
