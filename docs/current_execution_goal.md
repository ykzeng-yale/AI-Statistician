# Current Execution Goal

Updated: 2026-09-11, use one explicit native-thinking configuration for retained workspaces.

## Operative Objective

Develop a general, model-led AI Statistical Theory Lab: given a statistical
question or paper, it can investigate prior work, reproduce relevant baselines,
progressively develop reviewable theory, implement and challenge methods in Python
and R, independently validate stable results, optionally formalize them in Lean,
and reuse verified research and proof artifacts across unrelated problems.

This restores the complete [original product goal](goal-ai-statistician.md).
One accepted task is a milestone, not the goal. Repeatedly substituting another
easy benchmark, extending a scorecard, or collecting more repositories cannot
stand in for scientific capability or completion of this roadmap.

Use the existing single outer `AgentRuntime` and shared retained model/tool loop.
Improve or consolidate their actual tools, context, collaboration and authority
mechanisms; do not rebuild working workspaces or add a second scheduler. The
[local-literature and implementation audit](original_goal_harness_redesign_20260909.md)
records what was inspected, what is already implemented, and what remains design
rather than capability. [Production design](production_design.md) is the canonical
implementation contract; the older Architect goal is now only a role map.

### Native Goal Record

The app's native goal is active again. The operator designated a local credential
on 2026-09-10; it now resides only in gitignored `.env` with mode 0600. The existing
CLI loader reads it, and Anthropic accepted a pinned-Haiku model metadata request.
This removes the credential-configuration blocker, not the missing scientific
evidence. The preregistered configuration pilot has now completed with 94 exact-Haiku
generation calls; it adds no research-E2E credit. The native objective still has
the older one-result/Task114 wording.
The goal API cannot replace an unfinished objective, and its completion/blocking
operations must not be misused to rename it. This user-revised document is the
operative scope; the stale native text is recorded honestly in status. Neither
the native milestone nor the broader objective has been achieved. Do not report
that the native text was successfully replaced.

## Scientific Operating Model

```text
question / paper + explicit source horizon and evidence requirements
  -> inspect literature, code, data and reusable declarations as needed
  -> reproduce a pinned baseline when relevant and permitted
  -> durable Markdown/LaTeX theory <-> exploratory Python/R and simulation
       <-> optional light Lean investigation of definitions and stable lemmas
  -> independent review of stable claims and their exact implementation
  -> freeze confirmatory protocol, metrics and precision/stopping rule
  -> confirmatory computation and intent-selected deep Lean work
  -> evidence report, remaining gaps and reusable verified artifacts
```

This is a dependency policy, not a mandatory waterfall. An executable estimand,
DGP and procedure interface can justify an early prototype before all theory is
finished. Exploratory observations can revise theory. Confirmation cannot revise
its own criteria after seeing results. There is no universal 100-repetition rule:
precision and valid stopping belong to the frozen experimental question.

Heavy Lean work normally follows stable statements; foundational lemmas may be
investigated earlier. Formalization is required only by explicit task intent or
its frozen benchmark. A formal gap stays visible without erasing valid evidence
in unrelated dimensions. Current workspace transitions are serial/interleaved;
true independent parallel execution is not yet implemented.

The model owns derivations, research order, useful tests, search queries and all
source revisions. The harness owns identity, source horizon, permissions,
isolation, checkpoints, budgets, blinding and verifier authority. No fixed step
count, file count, candidate count or tool-use ritual defines research quality.
Feedback handling must not infer scientific meaning or instruction ownership from
field-name patterns. Preserve model methods and unknown tool observations; retire
legacy routing metadata at its producers rather than expand a repair blacklist.
Shared changes require a demonstrated context, tool, state or authority defect.
Deterministic tests should vary opaque diagnostics and candidate data to verify
unchanged source, complete feedback and same-owner iteration, not teach a particular
research answer. A model reasoning error is not by itself a harness defect. Moving
benchmark-specific remedies into prompts or renaming verdicts is not a demonstrated
solution either. Scientific improvement requires separate fresh capability evidence;
mechanism tests cannot establish it or authorize rejudging consumed evaluations.

## Measurable Deliveries

These are separate product evidence obligations, not gates imposed on every task.
Current support and missing implementation are detailed in the audit.

| Delivery | Required demonstration | Current boundary |
|---|---|---|
| Progressive theory and scientific research | Two unrelated, fresh known-result research tasks with reviewable definitions and derivations, useful exploratory computation, accepted exact code, frozen confirmation and independent full-task acceptance | The latest trimmed-mean run completed the internal graph but failed independent gold; no new credit |
| Reproduction and Python/R breadth | A pinned published-paper/code/data reproduction with exact environment and independently compared results, including real R execution; separately assess paper-to-code with author code hidden | R and controlled source execution exist; arbitrary dependency/data/environment reconstruction remains incomplete |
| Optional formalization and library reuse | A nontrivial exact statistical target closed in the active Statlib/Mathlib project with independent statement review; reuse a verified supporting artifact in an unrelated formal task | Some scoped formal credits exist; strict development source-theorem closure remains 0/2 |
| Long-horizon collaboration | Theory receives real code/simulation/prover findings, revises the relevant files and dependencies, and downstream evidence is revalidated only for changed inputs | Same-owner continuation and interleaving exist; independent concurrent work and join semantics remain unimplemented |
| Durable improvement | A source/version/assumption-bound artifact demonstrably helps a disjoint later task, without hidden-answer leakage or stale proof authority | Retrieval and trace export exist; export alone is not learning or autonomous library growth |

These deliveries establish a first integrated capability baseline, not autonomous
frontier discovery. Then advance through hidden known-theory rederivation,
historical rediscovery, near-frontier extensions and genuinely open questions.
Historical literature cutoffs restrict accessible sources but cannot remove
pretraining contamination; report that limitation. Open results need external
mathematical/scientific scrutiny, not model consensus or an invented success rate.
Existing sealed held-out and strict-formal protocols are not weakened or unlocked.

## Implementation Order

1. Keep the model in control of source and scientific decisions. The retained
   file/tool loop already returns complete observations to the same owner.
   Regression tests should vary source and unfamiliar errors, check exact transport
   and model-authored edits, and preserve identity/authority. A failed mathematical
   judgment does not justify a new runtime rule or a case-specific prompt.
2. Remove identified content-authoring machinery instead of wrapping it. Architect
   no longer rejects prose by matching phrases such as "simulation passed": even
   negated statements and future acceptance conditions hit that old blacklist.
   Existing typed execution/proof flags still cannot grant model authority.
   The offline keyword-based theory revision generator and its downstream
   formal-obligation audit, CLI commands and smoke stages are now removed.
   This is deletion of a known architectural violation, not improved E2E capability.
   Other legacy baselines remain explicitly non-authoritative.
3. Address scientific reliability without turning evaluation into the product.
   The latest [linear IV/GMM qualification](operator_audits/linear_iv_gmm_prequalification_20260911.md)
   failed under protocols 22/23: one incomplete control was judged correctly,
   but the complete reference was marked incomplete for lacking executed
   confirmation, which its theory rubric did not request. Preserve that failure.
   Do not launch another topic, add a reviewer, rename verdicts, or move the
   benchmark remedy into a prompt. Establish a shared interface/context defect
   independently before changing the harness; better judgment needs fresh evidence.
   A separate identity gap is now fixed: qualification binds the exact original
   question shown to the reviewer, not just its task ID. Changed or missing context
   identity cannot reuse an old qualification or trigger automatic requalification.
   This does not change the review prompt, solve scope overreach, or activate GMM.
   Hidden reviewers now honor the existing explicit Haiku thinking setting instead
   of overriding it with zero. Default-off behavior and acceptance rules stay
   unchanged; changed configuration requires fresh independent qualification.
   The next full research experiment can use native model reasoning without a
   second reviewer framework. Its efficacy remains unproven, and no consumed
   task or control may be reused to tune or qualify it.
4. Improve the existing source-project and Python/R environment only where real
   reproduction exposes a general limitation. Pinned source execution exists;
   arbitrary paper/data/environment reconstruction remains incomplete.
   Keep published-source replication separate from hidden rederivation.
5. Align formal execution and retrieval to the same active checkout, reuse selected
   verified declarations, and keep deep Lean optional unless task intent requires
   it. Implement useful isolated concurrency and dependency-aware joins only
   within the existing graph, without concurrent writes to one artifact.
6. Demonstrate the scoped deliveries above on fresh, independently qualified
   tasks, then assess cross-task reuse and advance the published-result ladder.
   Record actual scientific outcomes and calls/time. Mechanism tests, source
   resource checks and rejected qualifications add no research-E2E credit.

The [implementation audit](original_goal_harness_redesign_20260909.md), dated
operator audits and Git history retain earlier changes and evidence. This goal
document is a forward work contract, not a growing chronology of fixes.

## Resource and Change Policy

- Call Anthropic directly. All tests, qualification and live evaluations use
  exactly `claude-haiku-4-5-20251001`; no Opus or automatic tier escalation.
- Freeze any `AI_STATISTICIAN_HAIKU_TOOL_THINKING_BUDGET_TOKENS` setting before a
  fresh product draw. It enables native thinking only for retained tool workspaces,
  not tool-free Architect calls; existing total token bounds and
  explicit stopping remain. Native transport worked in the live component pilot,
  but scientific improvement and thinking-enabled research-E2E remain unproven.
  The default budget stays zero; the pilot compared a configuration bundle, not
  the isolated causal effect of thinking tokens.
  Hidden-gold protocols 22/23 retain complete read-only candidate/reference files,
  scratch tools and private Markdown referee reports. They now honor the same
  explicit thinking setting, bound by the existing qualification/session hash;
  past evaluations remain frozen with their original zero budget.
  Prospectively, the next full research experiment uses thinking 16384 and
  max_tokens 32768 for every retained author/reviewer workspace, with a 600-second
  request timeout. Tool-free Architect behavior and existing workspace/outer
  action budgets stay unchanged. Freeze the exact task and independent authority
  before calls; this configuration decision does not activate a task or establish
  efficacy, and is not permission to repeat any consumed evaluation.
  File-backed input is not a mathematical correction. Failed or older
  authority cannot silently qualify, resume or rerun. Tool access and reduced
  wasted calls are mechanism changes, not evidence of improved judgment.
- Credentials stay outside source, prompts, logs and `.env.example`. This revision
  uses the operator-designated `.env` through the existing CLI loader; absence of
  a process variable alone is not a blocker. The authentication check made one
  model-metadata request; the subsequent pilot made 94 generation calls, all
  exact Haiku. Use configured machine authentication for Git.
- Reuse Codex's retained file/tool feedback and independent authority principles,
  not Codex Core, App Server, provider transport or a second orchestrator.
- Reuse Numina and ReProver's environment/state access, LeanMarathon's evolving
  long-proof dependencies, and Prove2Me's stable target and blinded statement
  read-back. No source establishes that their reported results transfer to Haiku.
- Keep the active Statlib/Mathlib/StatInference foundation. External SLT, OpenProver,
  CodexProver and other branches are selected source/provider resources, not an
  instruction to merge every branch. The audit records pins and compatibility.
- Use ERA-style search only with a trustworthy exploratory executable score;
  never optimize against held-out confirmation or treat an LLM vote as proof.
- Prefer deletion and consolidation. No task-family formulas, Lean grammar/tactic
  patches, repair agents, packet hierarchies, model escalation or hidden fallback.
- Run focused synthetic checks while iterating and the full suite before pushing
  a shared mechanism change. Tests are mechanism evidence, not scientific success.

## Immutable Evaluation Record

The 114 numbered draws and four additional standalone draws remain consumed.
Their mixed-scope historical credits are preserved, not collapsed into E2E wins.
The latest [trimmed-mean closeout](operator_audits/trimmed_mean_l0_v1.md) records
102 completed product model turns over 947.444 seconds, internal acceptance, and
independent full-task rejection: algorithm 2/5, structural theory 7/7, semantic
theory 1 satisfied / 3 violated / 2 inconclusive, empirical 0/7. The 16 qualification
and two candidate semantic-evaluation calls are separate. Lean was not required.

Earlier [Task114](operator_audits/pareto_tail_index_l0_v1.md),
[beta-regression reproduction](operator_audits/betareg_gasoline_precision_l1_v1.md),
[Rademacher formal-only](operator_audits/rademacher_weighted_tail_formal_l0_v1.md)
and [entropy](operator_audits/multinomial_entropy_l0_v1.md) outcomes remain unchanged.
Never resume, repair, rerun, rejudge or rescore any consumed evaluation. No new
research benchmark is activated by this update. The separate configuration pilot
is also consumed: its 12 invocations are component diagnostics, not additional
research draws or full-task credits. The separately recorded Firth authority
qualification also adds zero research draws or credits; its failed source role
prevented activation, and this diagnostic-only change does not authorize a retry.
The later MCMC, entropic-transport, PPI, GP, GEE, conditional-quantile and linear
IV/GMM theory qualifications are also consumed and failed.
Their source semantic roles were not run after the required gate failed; neither
the protocol-15 PPI report nor later execution changes add a product draw or credit.
Current facts live in
[main_worker_status.json](main_worker_status.json); historical manifests and
qualification ledgers remain the original evidence.
