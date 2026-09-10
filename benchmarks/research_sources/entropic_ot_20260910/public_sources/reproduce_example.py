"""Execute the unchanged POT example and export its numerical artifacts."""
import json
from pathlib import Path
import runpy

import matplotlib

matplotlib.use("Agg")
state = runpy.run_path("plot_OT_1D.py")
a, b, cost = state["a"], state["b"], state["M"]
result = {"n_bins": int(state["n"]), "a": a.tolist(), "b": b.tolist(),
          "cost": cost.tolist(), "regularization": 0.001, "plans": {}}
for name in ("G0", "Gs"):
    plan = state[name]
    result["plans"][name] = {
        "coupling": plan.tolist(),
        "transport_cost": float((plan * cost).sum()),
        "row_max_error": float(abs(plan.sum(axis=1) - a).max()),
        "column_max_error": float(abs(plan.sum(axis=0) - b).max()),
    }
Path("ot_example_result.json").write_text(json.dumps(result, sort_keys=True) + "\n")
print(json.dumps({name: {k: v for k, v in values.items() if k != "coupling"}
                  for name, values in result["plans"].items()}, sort_keys=True))
