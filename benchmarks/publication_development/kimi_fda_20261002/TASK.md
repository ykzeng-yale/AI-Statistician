# Published-method Reimplementation

Reconstruct the classification experiment in Section 3.5 of the supplied
scikit-fda paper using its described smoothing, dimension reduction,
classification and joint model selection. Author replication code and reference
outputs are not supplied. Reuse the installed scientific libraries rather than
inventing another estimator. This is paper-to-code reproduction, not novel theory
or recovery of the original author environment.

`data/phoneme.npz` contains the published dataset as `curves` (observations by
grid point), `grid_points` and integer `labels`, in original observation order.
Use that frozen data; do not obtain a different dataset or read other runs.
The prepared Python environment is selected by `PYTHON`. Its package versions are
listed in `environment.txt`. The paper PDF and extracted text are in `paper/`.
Do not modify any supplied input, install packages or inspect hidden references.
Ordinary workspace file editing and local execution are authorized.

Write a self-contained `experiment.py` accepting:

```text
python experiment.py --data data/phoneme.npz --split-seed 0 --out results
```

The seed changes only the paper's train/test split random state. For any supplied
integer seed, execute the complete published model-selection procedure and
evaluate on its held-out test portion. Save `results/predictions.npy` in held-out
observation order and `results/metrics.json` with `split_seed`, `accuracy` and
`best_params` (the chosen joint grid parameters with their original names).
The evaluator will run the final source once on each of two frozen split seeds;
one is the published split and one is an undisclosed split. It uses the same
data and prepared environment. Copied printed accuracy is not fresh computation.
Full prediction vectors and procedure fidelity, not just a rounded number, matter.

Execute your implementation on split 0, retaining the outputs. Write `research.md`
with mathematical definitions of the preprocessing, fitted procedure, model
selection and held-out accuracy; source provenance, execution, uncertainty,
limitations and remaining gaps. Distinguish model selection from test evaluation,
and numerical reproduction from independent mathematical validation. Do not claim
an independent referee, unseen results, a novel theorem or Lean proof. Lean is
not requested. No authorized independent reviewer is available in this host run.

The required final artifacts are `experiment.py`, `research.md`,
`results/predictions.npy` and `results/metrics.json`. Keep support code in the
single source file so a fresh evaluator can execute that exact final file. Work
only in this project; permitted research material is this task, the supplied
paper/data/environment, installed library documentation/source and the project's
statistical-research skill when present. Network research is not needed here.
Report unresolved failures honestly rather than manufacture outputs.
