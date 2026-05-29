# Meta Atlas Lean and Autoform-Bot Integration

Latest integration audit: 2026-05-29.

The system now uses local mirrors of the user-owned forks as preferred sources,
with upstream Meta repositories as fallback acquisition/provenance references:

- Atlas Lean: `/Users/yukang/.codex/external/ykzeng-atlas-lean`
  - Remote: `https://github.com/ykzeng-yale/atlas-lean.git`
  - Commit: `c5a10f1a95de31e5476484c8bb3856ee7f164ea0`
- Autoform-Bot: `/Users/yukang/.codex/external/ykzeng-autoform-bot`
  - Remote: `https://github.com/ykzeng-yale/autoform-bot.git`
  - Commit: `f137da6cc9a60621d3b6aa0964e69443ba35903d`

## Atlas Lean Retrieval

Atlas is integrated as a retrieval/formal-source corpus, not as an imported Lean
dependency of the current proof bank. The formal-source index includes focused
subtrees that are directly useful for statistical theory development:

- `atlas_lean_high_dimensional_statistics`
- `atlas_lean_theory_of_probability`
- `atlas_lean_probabilistic_methods`
- `atlas_lean_analysis_foundations`

The latest formal-source audit indexed these Atlas declarations:

```text
atlas_lean_high_dimensional_statistics: 1503 declarations
atlas_lean_probabilistic_methods: 1133 declarations
atlas_lean_theory_of_probability: 493 declarations
atlas_lean_analysis_foundations: 127 declarations
```

Retrieval smoke evidence:

```text
query=Atlas HighDimensionalStatistics IsSubGaussian mgf bound Bernstein concentration
top_hit=IsSubGaussian.mgf_bound
source=atlas_lean_high_dimensional_statistics

query=Atlas TheoryOfProbability CLT Lindeberg Feller Borel Cantelli weak convergence
top_hit=ProbabilityTheory.weakConvergence_iff_tendsto
source=atlas_lean_theory_of_probability
```

This gives the AI Statistician a larger local Lean search surface for
sub-Gaussian concentration, high-dimensional statistics, probability limit
theory, and analysis primitives while keeping AXLE/Lean as the final verifier.

## Autoform-Bot Harness

Autoform-Bot is integrated as a harness adapter. The system records reusable
entrypoints for:

- statement extraction
- Lean compilation/evaluation checks
- Lean REPL/LSP tooling
- multi-agent orchestration
- trace/visualization utilities

Current detected command templates:

```bash
python -m autoform.statement_extraction run --book-dir <book_dir> --output <book_dir>/targets.yaml
python -m autoform.bot.main run --config <config.yaml> --name <run_name>
python -m autoform.eval run --repo_dir <lean_repo> --code_dir <lean_source_dir> --task_file <targets.yaml> --book_dir <book_dir>
python -m autoform.visualizer.app --runs-dir <workspace> --port 8003
```

The real research-system audit gate `autoform_harness` now requires the local
harness to expose the statement extraction, Lean eval, Lean REPL, and multi-agent
bot components.

The AI Statistician now also writes concrete Autoform inputs from its own formal
gap queue:

```bash
python -m ai_statistician.cli autoform-target-export \
  --run-dir runs/research_benchmark \
  --out runs/autoform_targets
```

That command emits:

- `autoform_targets.yaml`: Autoform-Bot `FormalizationTarget` records.
- `autoform_book/formal_gap_statements.md`: book-style descriptions of each
  statistical theorem-development target.
- `autoform_targets_manifest.json`: audit/provenance, command templates, and
  target fingerprint.

This is still a formalization handoff, not a proof claim: the exported targets
preserve `FORMAL_GAP` and placeholder-assumption boundaries.

## Usage Boundary

The checked-out fork license text still carries upstream no-training language.
Therefore Atlas and Autoform-Bot are marked:

- `atlas_lean_*`: `retrieval_only_no_training_export`
- `autoform_bot_harness`: `integration_reference_no_training_export`

Training exports filter these sources out unless a separate authorization
artifact is added. This keeps proof/retrieval use explicit while avoiding silent
training-data leakage.

## Latest Validation

Real Lean/AXLE system audit:

```bash
PYTHONPATH=/Users/yukang/AI\ Statistician \
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli research-system-audit --real-lean \
  --runs 20 --out runs/research_system_real_lean_43_bh_compl_bridge
```

Result:

```text
all_gates_passed=True
autoform_harness=True
autoform_targets=20/20
sources=19/19
proofs=43/43
frontier_supported=60/60
formalized_gaps=20/20
missing_primitives=97
```

The same audit now reports `proof_bank_expansion_bridge_ready=6`; the new
bridge-ready target is `independent_null_pvalues`, backed by the verified
`independent_null_event_family_inter_probability` and
`independent_null_event_family_compl_inter_probability` obligations plus local
StatInference source hits for the BH/FDR formalization queue.
