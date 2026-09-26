# Current Execution Goal

Updated: 2026-09-11, prioritize model-owned scientific iteration and usable feedback.

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

The [deeper comparative reuse review](research_harness_reuse_strategy.md) informs
selective adoption, not a new infrastructure roadmap. Codex improves the product harness; the
product researcher must do literature selection, environment preparation,
derivation, implementation, and interpretation. Operator-prepared paper answers,
install commands, or error-specific repairs cannot count as product autonomy.
Do not prioritize VM, proxy, package-registry, or container engineering without
evidence that a required scientific workflow is blocked by the existing tools.
The proposed network extension was withdrawn before commit. Existing optional
offline native execution remains available, not a prerequisite for research.

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

1. Inspect the existing Theory -> exploratory code/simulation -> independent
   review -> same-owner revision path. Demonstrate a missing tool, unreadable
   observation, lost context, or incorrect lineage before changing the harness.
   Repair the shared mechanism so the product model can investigate and revise
   its own research. Do not infer a harness defect from a wrong mathematical
   answer or spend a new scientific draw just to justify unrelated infrastructure.
2. Improve long-horizon Theory through recoverable observations and native
   Markdown/LaTeX work. Theory, Scientific and Lean owners now share a read-only
   history tool backed by the existing immutable session store. Full observations
   survive model-context omission; parent references permit on-demand reads across
   checkpoint windows without copying the entire history or rerunning tools.
   This is mechanism support, not demonstrated long-horizon scientific reliability.
   Let the model decide derivation length, useful scratch work, and when to revise
   or report an unresolved gap; do not add a second memory service or summary agent.
3. Use the existing source-discovery, exact snapshot, file-import, Python/R and
   optional native tools for permitted baselines. Make selected source-grounded
   operating knowledge accessible through those tools. Evaluate portable
   AREX-Skill-style references and PaperQA's
   lower-level parsing/provenance components, not their agent controllers.
   Preserve original-source access, version identity, and benchmark blinding;
   do not turn skills into mandatory recipes or an answer bank.
   General environment reconstruction remains incomplete, but further native or
   network engineering is deferred until a required workflow demonstrates the need.
4. Support genuinely independent work and exact-input joins in the sole
   AgentRuntime. Reuse Codex/Pi lifecycle principles; do not embed their loops.
   Normal environment feedback stays with the source owner. Changed premises
   invalidate dependent evidence, not all work in unrelated dimensions.
5. Prefer native Lean dependency extraction and active-project premise access
   over source-text guesses. Reuse Prove2Me's statement/proof separation,
   LeanMarathon's scoped DAG context, ReProver's accessibility contract, and
   Statlib/SLT's mathematical module conventions. Keep incompatible upstream
   libraries discovery-only until an explicit full-project migration succeeds.
6. Use ERA-style candidate search only inside an existing exploratory workspace
   with a trustworthy executable score. No automatic search tree, model ensemble,
   extra reviewer, repair taxonomy, or fixed iteration ritual is required.
   The [Dream-RSI adoption review](../skills/dream-rsi-scientific-search/references/adoption.md)
   extends this principle to history-informed candidate allocation. Its Codex skill
   is available as operating guidance, not a product replay controller. Do not turn
   consumed evaluations into policy-training histories or prioritize replay
   infrastructure before a scientific workflow demonstrates the need.
7. Verify each shared change with content-neutral mechanism tests, then fresh,
   prospectively defined cross-task evidence. Measure research outcomes and
   preparation/downstream costs separately. Preserve all consumed evaluations;
   do not replace failed tasks repeatedly to manufacture a success milestone.

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
  Hidden-gold protocols 24/25 retain complete read-only candidate/reference files,
  scratch tools and private Markdown referee reports. They now honor the same
  explicit thinking setting, bound by the existing qualification/session hash;
  past evaluations remain frozen with their original configuration.
  Provider/model provenance comes from the existing hash-bound retained turn
  history, not a second operator-copied call log. Protocols 22/23 and consumed
  qualifications cannot be migrated or retroactively accepted under this change.
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
The bootstrap-particle theory and source qualifications completed once with
181 and 76 exact-Haiku calls; mechanical qualification also passed once. These
results used raw question JSON, while the product CLI uses the existing typed
question projection. The preparation script included extra source metadata, so
the exact-context identity check rejected activation before any product call.
The original judgments and nominal raw-context activation remain unchanged, but
are not valid product activation. Do not launch, requalify, change their hashes,
or add a product exception. Future qualification preparation must reuse the
CLI's existing question producer and compare contexts before model calls, not
introduce another reviewer validator or expose bookkeeping metadata to agents.
The [theory receipt](evaluation_activations/bootstrap_particle_theory_qualification.json)
and [execution preparation](evaluation_activations/bootstrap_particle_frozen_execution.json)
retain their original time-specific facts. No research-E2E credit was added.
Current facts live in
[main_worker_status.json](main_worker_status.json); historical manifests and
qualification ledgers remain the original evidence.

The later [UCB1 qualification](operator_audits/ucb1_prequalification_20260911.md)
also failed: 22 exact-Haiku calls, unchanged complete inputs and the correct CLI
context, but disagreement over an extra experimental condition introduced by one
reviewer. No product draw occurred. This is an independent-authority limitation,
not observed product TheoryDeveloper failure. Preserve the attempt; do not
immediately substitute another task, strengthen the question after the fact,
add an issue-specific prompt rule or append another judge to seek acceptance.
