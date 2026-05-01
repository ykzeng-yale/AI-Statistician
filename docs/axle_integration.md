# AXLE Integration

AXLE is an optional external Lean Engine backend for StatLeanAgent.  It is used
to improve proof exploration and repair success, not to replace local Lean
verification or the semantic curation gate.

## Secret Handling

Never commit an AXLE key to this repository.  Configure it only in the process
environment:

```bash
export AXLE_API_KEY="<redacted>"
```

The client also honors the standard AXLE server URL through the command-line
`--base-url` option.  The default is:

```text
https://axle.axiommath.ai
```

## Current Compatibility

The project uses the public AXLE HTTP API shape:

- endpoint: `/api/v1/{tool}`;
- source field: `content`;
- Lean environment field: `environment`;
- optional import-relaxation field: `ignore_imports`;
- authentication header: `Authorization: Bearer $AXLE_API_KEY`.

AXLE currently offers Mathlib-backed Lean environments up to `lean-4.29.0`.
The local repository may track a newer Lean toolchain, so AXLE is best used for
Mathlib-compatible snippets, standalone theorem repair, declaration
extraction, normalization, and proof transformation.  Project-local
`StatInference` imports must still be checked by local `lake build`.

## CLI Usage

Run a remote syntax/elaboration check:

```bash
statlean axle-tool check path/to/File.lean --ignore-imports
```

Extract all declaration kinds from a Lean file:

```bash
statlean axle-tool extract_decls path/to/File.lean --output artifacts/axle/decls.json
```

Use `extract_decls`, not `extract_theorems`; AXLE has deprecated
`extract_theorems`.

Attempt proof repair on a standalone file:

```bash
statlean axle-tool repair_proofs path/to/File.lean \
  --output artifacts/axle/repair.json \
  --content-output artifacts/axle/File.repaired.lean \
  --ignore-imports
```

Validate a candidate proof against a statement:

```bash
statlean axle-verify-proof \
  --statement artifacts/axle/Statement.lean \
  --content artifacts/axle/Candidate.lean \
  --ignore-imports
```

## Operating Loop Placement

Use AXLE in this order:

1. Local static scan rejects forbidden placeholders first.
2. Local `lake env lean` remains the final verifier for repository code.
3. AXLE can run before or after local Lean to extract declarations, normalize a
   file, repair a failing proof, or split holes into standalone lemma targets.
4. A repaired proof must be copied back into the repo only after local Lean,
   benchmark verification, forbidden-token scanning, and semantic review pass.

## Statistical Safety Boundary

AXLE can improve Lean proof mechanics.  It must not decide theorem meaning.
For empirical-process and statistical-inference results, the VdV&W semantic
guardrails still apply:

- no theorem weakening to make repair easier;
- no dropped measurability, envelope, separability, tightness, or outer
  probability conditions;
- no promotion of a certificate interface as if it were a primitive theorem;
- no accepted proof containing `sorry`, `admit`, unreviewed `axiom`, or unsafe
  shortcuts.
