import { loadPyodide } from "pyodide";

const packages = [
  "numpy",
  "scipy",
  "pandas",
  "scikit-learn",
  "statsmodels",
];

const pyodide = await loadPyodide();
for (const packageName of packages) {
  await pyodide.loadPackage(packageName);
}
console.log(JSON.stringify({
  artifact_kind: "ScientificSandboxPreparationManifest",
  backend: "pyodide",
  packages,
  status: "READY",
  boundary: "Trusted preparation resolves pinned runtime packages; it does not execute generated code.",
}));
