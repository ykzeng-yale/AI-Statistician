"""Run unchanged numerical cells from the pinned official notebook."""
import json
from pathlib import Path

notebook = json.loads(Path("quickstart.ipynb").read_text())
namespace = {"__name__": "__main__"}
for index in (3, 5, 7, 10, 12, 14, 16, 18, 22, 24):
    cell = notebook["cells"][index]
    assert cell["cell_type"] == "code"
    exec(compile("".join(cell["source"]), f"quickstart.ipynb:cell-{index}", "exec"), namespace)

np, sampler = namespace["np"], namespace["sampler"]
chain = sampler.get_chain()
samples = sampler.get_chain(flat=True)
summary = {
    "chain_shape": list(chain.shape),
    "target_mean": namespace["means"].tolist(),
    "target_covariance": namespace["cov"].tolist(),
    "sample_mean": samples.mean(axis=0).tolist(),
    "sample_covariance": np.cov(samples, rowvar=False).tolist(),
    "mean_acceptance_fraction": float(sampler.acceptance_fraction.mean()),
    "autocorrelation_time": sampler.get_autocorr_time().tolist(),
    "executed_notebook_cells": [3, 5, 7, 10, 12, 14, 16, 18, 22, 24],
    "plots_reproduced": False,
}
Path("quickstart_result.json").write_text(json.dumps(summary, indent=2) + "\n")
