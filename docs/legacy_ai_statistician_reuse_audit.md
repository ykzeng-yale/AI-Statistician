# Legacy AI-Statistician Reuse Audit

Source inspected:

`/Users/yukang/Desktop/AI for Math/Codex/AI-Statistician`

Reusable source vendored into this repository:

`legacy_sources/ai_statistician/`

## Decision

Do not replace the current `/Users/yukang/AI Statistician` codebase with the
legacy repo. The current repo remains the active production scaffold because it
has the frontier benchmark, research traces, simulation diagnostics, proof-bank
audit, formal-gap audit, release-style system audit, and registry-gated
algorithms.

Do reuse the legacy repo as a source pool. Its useful assets are now vendored
under `legacy_sources/ai_statistician/` and registered in the current source
inventory and formal-source index:

- `legacy_ai_statistician_statinference`: Lean declarations from the old
  `StatInference/` tree.
- `legacy_ai_statistician_benchmarks`: theorem-hole and formal benchmark seeds.
- `legacy_ai_statistician_schemas`: JSON contracts for Lean tasks, proof
  attempts, benchmark tasks, and verification reports.
- `legacy_ai_statistician_training_artifacts`: DPO/GRPO/proof-attempt training
  artifacts for future prover improvement work.

## What Was Found

- The old checkout is not clean: it has modified and untracked files, including
  many `StatInference/Matching` and empirical-process additions. It should be
  treated read-only until intentionally reconciled.
- The old `StatInference/` tree contains 401 Lean files and no detected
  `sorry`, `admit`, `unsafe`, or top-level `axiom` shortcuts in `.lean` files.
- The current formal-source index extracts 5,088 Lean declarations from the
  legacy `StatInference` tree.
- The combined local formal-source index now covers 40,592 declarations across
  7 sources:
  Mathlib Probability, Mathlib MeasureTheory, EmpiricalProcessLEAN,
  local StatInference, lean-stat-learning-theory, external EmpiricalProcessLEAN,
  and the legacy AI-Statistician StatInference tree.

## High-Value Legacy Hits

The legacy tree gives useful retrieval anchors for frontier statistical theory
planning:

- `StatInference.IndexedAsymptoticLinearCLTRoute.asymptoticNormal_via_bridge`
  for asymptotic-normality bridge planning.
- `StatInference.aipw_product_rate_route_constructor` for AIPW / double-robust
  product-rate routes.
- `StatInference.ipw_hajek_linearization_constructor` for IPW Hájek
  linearization.
- `StatInference.BracketingDeviationCertificate.toGlivenkoCantelliClass` and
  related bracketing constructors for empirical-process / Glivenko-Cantelli
  gaps.
- `StatInference.DonskerBridgeCertificate.weakConvergence` and
  `StatInference.ProbabilityMeasure.*weakConvergence*` for Donsker /
  weak-convergence gaps.

## Current Integration

The following commands now include the legacy repo:

```bash
python3 -m ai_statistician.cli research-knowledge-audit \
  --out runs/research_knowledge_audit_legacy_sources

python3 -m ai_statistician.cli formal-source-audit \
  --out runs/formal_source_index_legacy_sources
```

Observed audit status after integration:

- Research knowledge audit: `all_ok=True`, source inventory `11/11`.
- Formal source index: 40,592 declarations, 7 sources, theorem-mining query
  coverage `14/14`.

## Reuse Boundary

Reusable now:

- Lean declarations and theorem/interface names for retrieval.
- Theorem-hole benchmark and curation artifacts as future training/evaluation
  data.
- Schema ideas for future proof-attempt and verification-report artifacts.
- Tokenization/tagging ideas from `src/statlean_agent/retrieval.py`; the current
  formal-source index now uses fast Lean-name token splitting for underscores,
  dots, apostrophes, and camel case.

Not reused as active runtime:

- The old Python orchestration stack.
- The old worktree manager.
- The old Lake verifier wrapper.
- The old benchmark/evaluation CLI.

Those are superseded by the current production scaffold and AXLE-backed
proof-bank audit.
