# Current Execution Goal and Resource Adoption

Updated: 2026-09-04

## Objective

Establish the next trustworthy AI-Statistician capability milestone with the
existing single `AgentRuntime` and retained exact-Haiku workspaces. The milestone
is complete only when fresh immutable evaluations establish all three results:

1. One disjoint known-result task has accepted theory, model-authored scientific
   code, and frozen confirmatory evidence.
2. One pinned published-paper task has exact reproducible source evidence.
3. One disjoint formal task has exact identity-bound, axiom-clean kernel closure
   in the active Statlib/StatInference project.

All product and evaluator model calls use exactly
`claude-haiku-4-5-20251001`. Formalization remains optional unless frozen task
intent requires it. Passing unit tests, finding a declaration, or compiling a
support lemma does not satisfy any of these gates.

This replaces the previous role-only goal. Being the main worker is an ownership
fact, not a measurable research objective.

## Evaluation Order

1. Preserve Task114 as the next numbered evaluation. Qualify its independent
   semantic authority, freeze the activation record, and only then permit its one
   product draw. Task114 measures a known-result Theory, Python, and confirmatory
   Simulation path; Lean and source replication are not applicable to its frozen
   intent.
2. Keep the beta-regression gasoline-precision reproduction as a separate,
   unnumbered candidate. After Task114, freeze its remaining authority and measure
   the pinned R paper/code/data reproduction path without turning it into Task115.
3. Freeze a new, unrelated formal task only after the earlier boundary permits it.
   Success requires the exact requested theorem in the active project, not a nearby
   theorem, retrieved declaration, pseudo-formal review, or compiled helper.

This ordering protects sealed evaluation authority. It is not a universal product
waterfall. Within a research task, Theory, exploratory Python/R, Simulation, source
search, and a light Lean scout may overlap whenever their inputs are stable.

## Scientific Operating Model

The model owns the scientific path:

```text
question and source horizon
  -> search literature, code, data, and reusable formal declarations
  -> reproduce a pinned baseline first when one exists
  -> develop a durable Markdown/LaTeX claim and derivation workspace
       <-> run model-authored Python/R diagnostics and exploratory simulation
       <-> use optional light Lean scouting to expose statement ambiguity
  -> independent mathematical and source review
  -> freeze a stable claim, algorithm, and confirmatory protocol
  -> run confirmatory evidence to evaluator-owned precision
  -> perform deep Lean formalization only when requested or useful
  -> report a multidimensional evidence vector and unresolved gaps
```

No mathematical quality criterion is a fixed number of derivation steps, files,
agents, candidates, or simulation repetitions. Runtime ceilings protect execution
and authority; a workspace may checkpoint and continue while its hash-bound files
show real progress. Confirmatory sample size is selected from the frozen precision
target, not a hardcoded repetition count.

The harness mechanically owns only task identity, source horizon, permissions,
artifact lineage, blinding, execution isolation, budgets, independent review, and
verifier authority. It does not own statistical content, derivation order,
experiments, Lean tactics, or repair recipes. Raw errors and reviewer findings
return to the same source-owning model.

## Change Admission Rule

A fresh failure may justify a shared change only when the evidence identifies a
defect in model context, prompt instructions, a generic file/tool loop, source or
retrieval identity, reviewer feedback, or evidence promotion. A model-only
mathematical mistake does not justify a task-family branch or hardcoded correction.

Prefer deleting or consolidating a control surface. Do not add a repair agent,
second scheduler, framework wrapper, fixed reasoning recipe, task answer, theorem
family rule, Lean grammar patch, universal formal gate, model escalation, or
compatibility fallback. A new external corpus is not a capability until a current
workspace uses it under an exact identity and the relevant executor verifies it.

## Current Resource Decisions

The following table is the operational adoption record. The older broad resource
audit remains historical collection evidence.

### Active Runtime and Scientific Sources

| Resource | Audited identity | Decision |
|---|---|---|
| [OpenAI Codex](https://github.com/openai/codex/tree/8e6a44b4) | `8e6a44b4` | Adopt retained source ownership, stable capability-accurate tools, file-backed state, raw observations, checkpoint lineage, and isolated review. Do not embed Codex Core, App Server, provider transport, worktree management, or another scheduler. |
| [Statlib](https://github.com/stat-lib/statlib/tree/6575d611b5d32ef6013e9560d30b1a82a1972fb6) | active pin `6575d611` | Active importable statistical foundation and premise authority. |
| [EmpericalProcessLEAN](https://github.com/ykzeng-yale/EmpericalProcessLEAN/tree/4cec7860c926feebd4cbcdaccedb63b2156972dd) | `4cec7860` | Active Lean project and current StatInference declaration authority. Its `main` RAG package supersedes the older divergent RAG branches; do not merge those branches wholesale. |
| [lean-stat-learning-theory](https://github.com/YuanheZ/lean-stat-learning-theory/tree/d0f506f0a695) | `d0f506f0` | Active external companion corpus for source-identified retrieval. Reuse its layered module organization, small-lemma decomposition, exact references, and source review conventions; do not copy its model tier or human-supervision assumptions. |
| [OpenProver](https://github.com/ykzeng-yale/OpenProver/tree/3960746da069) | `3960746d` | Existing optional LSP/MCP and hindsight-lemma proof-search provider. The Formalizer must choose model-authored proof-state queries; provider output remains candidate context until active-project checking. |

### Discovery or Design Sources

| Resource | Status | Admission boundary |
|---|---|---|
| [Statlib upstream](https://github.com/stat-lib/statlib/tree/01d2a03770455f5c775bb25c57e7fbb8e1eaf8d8) | Discovery only | Its own build passed, but the combined StatInference migration produced 207 Lean errors. Do not expose declarations as importable premises until a dedicated whole-project port succeeds. |
| [Stat-Lean](https://github.com/StatLean/Stat-Lean/tree/855b6afb69fead1bef066111732ed44df181040e) | Discovery corpus | Apache-2.0, Lean 4.29.1, Mathlib `5e932f97`, 1,142 Lean files, about 549k lines, and 8,636 indexed declarations at tree `b1107070`. The existing generic index needs no adapter. A clean exact-snapshot trial retrieved BH, Kaplan-Meier, AIPW, and bootstrap obligations in both global and source-scoped context (4/4); the aggregate external benchmark remains red because two older LML/SciLean scoped cases miss. A static source scan found no standalone `sorry` or `axiom` declarations, but that is not a kernel audit. The corpus remains non-importable until selected declarations are ported and elaborated in the active Lean 4.30.0/Mathlib `81343555` project. |
| [LeanDojo/ReProver](https://arxiv.org/abs/2306.15626) | Design and provider reference | Reuse accessible-premise extraction, proof-state retrieval, hard negatives, and challenging splits. Do not import another task controller. |
| [Numina Lean Agent](https://arxiv.org/abs/2601.14027) and [AxProverBase](https://arxiv.org/abs/2602.24273) | Harness references | Reinforce the direct model -> search/compile -> raw feedback -> same-model revision loop. They do not justify task-specific repair infrastructure. |
| [LeanMarathon](https://arxiv.org/abs/2606.05400) | Long-form formalization reference | Use an evolving theorem/lemma blueprint only for genuinely long formal projects. Do not force its DAG ceremony onto ordinary research tasks. |
| [pseudo-formalization](https://github.com/Slim205/pseudo-formalization/tree/0aa51d25726c) | Advisory review reference | PF/BV can expose structural mathematical gaps. It is natural-language evidence and can never substitute for Lean proof. |
| [ERA](https://github.com/google-research/era/tree/440711e3bef5) | Conditional algorithm-search reference | Use candidate tree search only where an independent executable score is trustworthy. Do not use it for open theory whose score is model opinion. |
| [AI Co-Scientist](https://arxiv.org/abs/2502.18864) | Open-hypothesis reference | Generate, debate, and evolve hypotheses when no direct verifier exists; retain explicit uncertainty and external review. |

### Evaluation and Reproduction Sources

| Resource | Reuse decision |
|---|---|
| [PaperBench](https://openai.com/index/paperbench/) | Keep rollout and grading environments separate and use author-derived fine-grained rubrics. |
| [Read Paper. Write Code.](https://arxiv.org/abs/2604.21965) | Use strict information isolation, deterministic result comparison, and error attribution for paper-to-code tasks. |
| [SocSci Repro Bench](https://arxiv.org/abs/2606.11447) | Include both reproducible and demonstrably non-reproducible sources so the evaluator can distinguish agent failure from source failure. |
| [ReproAgent](https://arxiv.org/abs/2608.24291) | Reuse the idea of a persistent, explicit source contract and file work packages. Do not import a separate prepare/plan/generate/repair orchestration pipeline. |

`CodexProver` branches remain evaluated historical mechanism sources, not a merge
target. Their evidence controls informed immutable splits and source identity, but
their packet/controller surface would restore the complexity removed from the
canonical runtime. `EmpericalProcessLEAN` branch tips likewise remain source history;
the newer `main` implementation wins unless an isolated commit fixes a measured gap.

## After This Goal

Only after the three current gates close should evaluation advance to hidden
known-theory rederivation, historical frontier rediscovery, near-frontier extension,
and finally genuinely open problems. Open research without a gold answer must be
reported as a reproducible, falsifiable candidate, not as established correctness
because several models agreed.
