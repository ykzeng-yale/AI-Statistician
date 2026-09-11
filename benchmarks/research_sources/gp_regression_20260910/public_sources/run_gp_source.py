"""Operator calibration launcher for an unchanged public GP implementation."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import scipy
import sklearn
from scipy.stats import chi2, norm
from sklearn.gaussian_process.kernels import ConstantKernel, RBF


source = Path("_gpr.py")
spec = importlib.util.spec_from_file_location("sklearn.gaussian_process._frozen_gpr", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def run_design(seed, length_scale, noise_variance):
    x = np.linspace(-1.5, 1.5, 8).reshape(-1, 1)
    t = np.array([-1.1, -0.35, 0.45, 1.25]).reshape(-1, 1)
    signal_variance, repetitions = 1.7, 1000
    kernel = ConstantKernel(signal_variance) * RBF(length_scale)
    locations = np.concatenate([x, t])
    prior_root = np.linalg.cholesky(kernel(locations))
    rng = np.random.default_rng(seed)
    counts = np.zeros((2, len(t)), dtype=int)
    joint_counts = np.zeros(2, dtype=int)
    residual_cross_products = np.zeros((2, len(t), len(t)))
    model = module.GaussianProcessRegressor(kernel=kernel, alpha=noise_variance, optimizer=None, normalize_y=False)
    for _ in range(repetitions):
        f = prior_root @ rng.standard_normal(len(locations))
        y = f[:len(x)] + np.sqrt(noise_variance) * rng.standard_normal(len(x))
        noisy_test = f[len(x):] + np.sqrt(noise_variance) * rng.standard_normal(len(t))
        model.fit(x, y)
        mean, covariance = model.predict(t, return_cov=True)
        covariances = [covariance, covariance + noise_variance * np.eye(len(t))]
        for index, target in enumerate([f[len(x):], noisy_test]):
            residual = target - mean
            counts[index] += np.abs(residual) <= norm.ppf(.975) * np.sqrt(np.diag(covariances[index]))
            joint_counts[index] += residual @ np.linalg.solve(covariances[index], residual) <= chi2.ppf(.95, len(t))
            residual_cross_products[index] += np.outer(residual, residual)
    coverage, joint = counts / repetitions, joint_counts / repetitions
    return {
        "seed": seed, "replicates": repetitions, "length_scale": length_scale,
        "signal_variance": signal_variance, "noise_variance": noise_variance,
        "marginal_counts_latent_observed": counts.tolist(), "joint_counts_latent_observed": joint_counts.tolist(),
        "marginal_coverage": coverage.tolist(), "marginal_mcse": np.sqrt(coverage * (1 - coverage) / repetitions).tolist(),
        "joint_coverage": joint.tolist(), "joint_mcse": np.sqrt(joint * (1 - joint) / repetitions).tolist(),
        "posterior_covariances": [value.tolist() for value in covariances],
        "residual_second_moments": (residual_cross_products / repetitions).tolist(),
    }


result = {
    "scope": "Operator calibration using unchanged scikit-learn source, not historical book figure reproduction",
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "packages": {"numpy": np.__version__, "scipy": scipy.__version__, "scikit-learn": sklearn.__version__},
    "designs": [run_design(9108801, .35, .09), run_design(9108802, .75, .36)],
}
Path("gp_source_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps({"result": "gp_source_result.json", "designs": len(result["designs"]), "fits": 2000}, sort_keys=True))
