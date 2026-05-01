# StatLeanAgent Meta-Instruction

## Target

Build a verifier-first AI system for statistical theorem proving in Lean. The
system must progressively grow a curated `StatInference` Lean library,
benchmark its own proof capability, and train domain-adapted proof models from
verified traces.

The long-run target is broad statistical inference coverage:

- asymptotic linearity and asymptotic normality;
- `op`/`Op`, Slutsky, delta-method, and continuous-mapping calculus;
- ERM consistency and uniform convergence;
- empirical-process and Glivenko-Cantelli/Donsker interfaces;
- M-estimation and Z-estimation;
- influence functions and semiparametric orthogonality;
- causal estimators including IPW/AIPW/TMLE-style bridges.

## Operating Principles

- Lean verification is mandatory for accepted formal results.
- No accepted `sorry`, `admit`, unreviewed `axiom`, or `unsafe` shortcut.
- Do not weaken theorem statements just to make proofs compile.
- Definitions and assumptions require statistical semantic review; Lean
  typechecking alone is not enough.
- Prefer small verified lemmas over large opaque proofs.
- Use abstract bridge structures only when the theorem is explicitly an
  interface theorem, not as a substitute for proving a concrete result.
- Keep benchmark tasks reproducible from typed registries, not hand-edited
  JSONL.

## Iterative Loop

1. Add or improve a Lean theorem/definition in `StatInference`.
2. Add benchmark tasks that force use of the new local lemma.
3. Render and verify benchmark tasks.
4. Score attempts with dense reward and failure diagnostics.
5. Repair failures or mine reusable sublemmas.
6. Curate only useful, non-vacuous, verified lemmas.
7. Regenerate SFT/DPO/GRPO manifests from benchmark and verifier artifacts.
8. Run Python tests, Lean build, and GitHub CI before promotion.

## Swarm Policy

Agents work in disjoint ownership zones. A code-writing agent must list changed
files, validation commands, and any unresolved blockers. Integration happens
only after local tests and Lean/CI checks.

When active-agent capacity is limited, prioritize:

1. Lean foundation workers;
2. benchmark and verifier workers;
3. retrieval/training/CI workers;
4. documentation and planning workers.

