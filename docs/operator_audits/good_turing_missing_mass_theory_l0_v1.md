# Good-Turing Missing-Mass Theory L0 Operator Audit

## Disposition

Task 87 is consumed once at `0/1`. AgentRuntime returned `ACCEPTED`, but the
frozen post-runtime gold evaluator rejected the required theory dimension. The
aggregate ladder remains `5/87`.

This result must not be rerun, resumed, repaired, reevaluated, rescored,
resampled, or returned to any source-owning model as feedback.

## Frozen Scope

- Public task: `good_turing_missing_mass_bias_theory_known_result`
- Primary authority: I. J. Good, *Biometrika* 40(3-4), 1953,
  DOI `10.1093/biomet/40.3-4.237`
- Modern context: Amichai Painsky, JMLR 23(279), 2022
- Product and evaluator model: `claude-haiku-4-5-20251001`
- Formalization, code, simulation, source replication, and novelty: not applicable
- Activation commit: `9bd948ab74ea4da67e048c6a7384c2fe8d6b7c3c`
- Product head: `04783ac48eadbf4516787960a1a7b001cae07fe4`

Gold authority remained outside the repository, runtime RAG, and model
workspaces. Its qualification used eight preactivation Haiku calls; activation
reused that record with zero new calls.

## Runtime Evidence

The canonical path used three outer nodes and two sparse handoffs:

1. TheoryDeveloper: 10 model turns and 10 workspace tools.
2. Independent theory preflight: 6 model turns and 6 tools, including three
   referee-authored scratch checks.
3. CriticEvaluator: 23 model turns and 23 tools.

The model wrote one 228-line authoritative Markdown/LaTeX document and one
277-line independent referee report. No Algorithm, Simulation, Formalizer,
Lean, or Architect-planning lane ran.

Runtime research completion and mode conformance were both `1/1`. The hidden
mechanical authority passed `7/7`; calibrated integrated semantics passed only
`5/7`, so the required theory dimension failed.

## Mathematical Findings

The active document contains multiple material defects:

- Line 54 states `E[K_(n+1),1] = n E[M_n]`; lines 67-79 later derive the correct
  factor `n+1`, but the earlier theorem statement remains active.
- Line 121 says the bias is strictly positive iff at least one `p_x > 0`.
  Every pmf satisfies that condition, including the point mass that lines
  123-130 correctly identify as zero bias.
- Lines 138-149 give a full-sample singleton indicator rather than explicitly
  defining the deleted-sample event. Lines 170-176 then reuse `N_x^(n-1)`,
  originally defined on the first `n-1` observations, for the different sample
  `X_2,...,X_n`.
- Line 199 suggests consistency from vanishing unconditional bias, despite the
  task's explicit instruction not to claim consistency and without controlling
  estimation error for the random missing mass.

The independent referee declared every theorem correct. The terminal Critic
also accepted and cited preflight approval plus positive numerical examples,
although its existing generic prompt says neither is correctness evidence.

## Harness Judgment

No shared product change is warranted from this draw. The existing preflight
protocol already requires treating all active assertions as a conjunction,
reconstructing decisive transitions, searching for contradictions, and refusing
to let later corrections or positive examples erase an earlier false statement.
The Critic prompt independently repeats those requirements.

Adding Good-Turing formulas, a consistency keyword rule, synonymous prompt
guardrails, another reviewer vote, retries, a repair worker, a fallback, a new
scheduler, or model escalation would overfit a consumed Haiku failure. The
minimal Codex-derived harness principles worked: model-owned tool loops,
persistent externalized files, raw observations, sparse handoffs, hash-bound
state, and a fail-closed external evaluator.

## Evidence Hashes

- Runtime manifest: `889b55aa74e5bc1018275c738d521970606a5115af3539d362b4f604634338ab`
- Runtime result: `445f90c0a47eb842fa1b07cf23570d967a096eaea8dc9c90add7f79e9069542f`
- Gold evaluation: `a787c2d0c6c799414baa613862e28348e6cf57bdd0ecc23d77a80607e020a150`
- Theory document: `a8049ff5a966da3c78711fefc46746f3f848932f400ef8f10206c9d1f4f34cc0`
- Independent report: `0482fa53f7cbb5a06963dcdad6fb5d64e6f40d21ccfee9173f13744c0f9842ca`
