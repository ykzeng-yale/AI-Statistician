# AXLE Integration Assessment

This note records the current role of the Axiom AXLE Lean Engine in the
StatLean workflow.

## Status

AXLE is usable as an auxiliary remote Lean-processing backend. Live smoke tests
on May 1, 2026 confirmed that `check`, `extract_decls`, and `verify_proof`
accept small Lean snippets through the StatLean CLI.  The official AXLE API and
console list the following tools as available integration targets:

- `check`
- `verify_proof`
- `extract_decls`
- `theorem2sorry`
- `theorem2lemma`
- `have2sorry`
- `have2lemma`
- `sorry2lemma`
- `normalize`
- `simplify_theorems`
- `repair_proofs`
- `disprove`

The service currently exposes Lean environments through `lean-4.29.0` in the
environment list observed during the audit. This repository is pinned to
`leanprover/lean4:v4.30.0-rc2`, so AXLE should not replace local `lake build`.
Use it for compatible self-contained snippets, theorem-hole generation, proof
repair attempts, and declaration extraction.

## Recommended Role

The local Lake verifier remains the source of truth for repository acceptance.
AXLE should be treated as a parallel accelerator:

1. Run `check` on extracted theorem candidates before adding them to the repo.
2. Run `verify_proof` to make sure a candidate proof preserves an expected
   theorem signature.
3. Run `extract_decls` to build theorem cards and dependency records.
4. Run `theorem2sorry` to generate benchmark holes from complete Lean files.
5. Run `have2lemma` and `sorry2lemma` to mine missing sublemmas.
6. Run `repair_proofs` and `simplify_theorems` opportunistically, followed by
   local verification.
7. Run `disprove` as a sanity check for suspicious autoformalized statements.
8. Run `normalize`, `rename`, and `theorem2lemma` for hygiene only.

## Security

Do not commit API keys. The CLI reads `AXLE_API_KEY` from the environment when
available:

```bash
export AXLE_API_KEY="<redacted>"
```

The key is optional for limited unauthenticated calls, but authenticated usage
should still be kept outside the repository.

## CLI

Generic tool call:

```bash
PYTHONPATH=src python -m statlean_agent.cli axle-tool check path/to/File.lean --env lean-4.29.0
PYTHONPATH=src python -m statlean_agent.cli axle-tool extract_decls path/to/File.lean --output artifacts/axle/decls.json
PYTHONPATH=src python -m statlean_agent.cli axle-tool theorem2sorry path/to/File.lean --content-output artifacts/axle/File.sorry.lean
```

For repository files that import local `StatInference.*` modules, add
`--ignore-imports` and treat the result as dependency extraction or repair
guidance, not final acceptance:

```bash
PYTHONPATH=src python -m statlean_agent.cli axle-tool extract_decls \
  StatInference/Asymptotics/Basic.lean \
  --env lean-4.29.0 \
  --ignore-imports
```

Signature-preserving proof validation:

```bash
PYTHONPATH=src python -m statlean_agent.cli axle-verify-proof \
  --statement artifacts/axle/Expected.lean \
  --content artifacts/axle/Candidate.lean \
  --env lean-4.29.0
```

## Limits

AXLE does not solve the semantic formalization problem. It can validate,
split, normalize, and repair Lean code, but it cannot decide whether a
statistical statement is the right formal meaning of a theorem in van der Vaart
and Wellner. The curation gates still need to check:

- no `sorry` or new unsafe axiom in accepted library code;
- non-vacuity examples for new assumption interfaces;
- explicit measurability and integrability assumptions;
- downstream reuse and proof-cost improvement;
- consistency with the textbook theorem statement.
