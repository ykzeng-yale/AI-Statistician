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

Do reuse the legacy repo as a historical source pool. Its useful assets are
vendored under `legacy_sources/ai_statistician/` and registered in the source
inventory, but its Lean snapshot is not a live Formalizer source:

- `legacy_ai_statistician_statinference`: historical Lean provenance and
  owner-authorized training material from the old `StatInference/` tree.
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
- A historical audit extracted 5,088 Lean declarations from the legacy
  `StatInference` tree. This is snapshot evidence, not the current live index.

## High-Value Legacy Hits

The legacy tree identified useful proof surfaces during reconciliation:

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

The knowledge audit still inventories the legacy repo:

```bash
python3 -m ai_statistician.cli research-knowledge-audit \
  --out runs/research_knowledge_audit_legacy_sources
```

The 2026-08-02 reconciliation compared both vendored snapshots with the current
StatLib-founded `EmpericalProcessLEAN/main` tree:

- All 830 historical Lean file paths have current owners.
- All 1,412 declarations whose qualified names changed from the vendored
  EmpericalProcessLEAN snapshot retain the same declaration short name in the
  current canonical graph.
- Of 142 changed legacy AI-Statistician declaration names, 137 retain current
  short-name owners. Four discarded declarations were `0 = 0` demo markers;
  the fifth was a reverse outer-to-ordinary almost-sure bridge invalidated by a
  later semantic definition change.
- The current graph is the only live StatInference provider: 1,185 files,
  51,982 declarations, zero duplicate names, zero `sorry`, and `BOUND_MATCH`.

## Reuse Boundary

Reusable now:

- Historical theorem/interface names for provenance and training comparison.
- Theorem-hole benchmark and curation artifacts as future training/evaluation
  data.
- Schema ideas for future proof-attempt and verification-report artifacts.
- Tokenization/tagging ideas from `src/statlean_agent/retrieval.py`; the current
  formal-source index now uses fast Lean-name token splitting for underscores,
  dots, apostrophes, and camel case.

Not reused as active runtime:

- The two superseded Lean snapshots as live Formalizer retrieval providers.
- The old Python orchestration stack.
- The old worktree manager.
- The old Lake verifier wrapper.
- The old benchmark/evaluation CLI.

Those are superseded by the current production scaffold and AXLE-backed
proof-bank audit.
