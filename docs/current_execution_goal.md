# Current Execution Goal

Updated: 2026-09-11, with complete review-contract binding; no new product draw.

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

1. Reconcile goals and capability claims with current code; remove contradictory
   tool instructions. Implemented in this revision; verification is recorded in status.
2. Prioritize complete source and observation access for the same owning model.
   Both suffix heuristics and the remaining explicit field-name blacklists have
   now been removed, including duplicate Formalizer filtering. Their historical
   recipe producers were largely offline utilities; live feedback could still lose
   model methods and raw tool diagnostics solely because of a dictionary key.
   Theory and scientific feedback now preserve permitted text and structured data
   through existing read-only documents, including line/character-range access to
   long diagnostics across continuation. No positional or field-name summary may
   silently replace the source. Prior diagnostics remain history, not current-source
   acceptance; visibility and release authority are unchanged.
   Scientific owners can use the existing run tool on their exact current project
   test files, with model-selected diagnostic inputs. This uses the same source and
   isolated Python/R runner, not a separate scratch agent. Confirmation artifacts
   and bound estimators remain outside that path; a successful test is not release.
   Independent semantic reviewers now receive complete candidate/reference files,
   not stripped mathematical paragraphs embedded in JSON. Citation indexes contain
   file locations; candidate excerpts remain verbatim. Private file identities are
   rechecked with the qualification record. Protocols 18/19 bind this changed input
   contract, with the same statuses, review strategies, model and reasoning budgets.
   Qualification now fingerprints the actual shared native request constructor,
   including the previously unbound prompt and submission tool. It reuses the
   retained-loop session fingerprint rather than another interface registry;
   loop/scratch settings are frozen as well. Changed authority is rejected before
   model calls, never automatically requalified. This closes an identity defect,
   not the unresolved mathematical reliability or report/status disagreement.
   Tests cover source fidelity, readable full context, opaque case labels and exact
   references. No new tool name, mathematical parser, reviewer, classifier or retry
   budget was added. These are workspace mechanisms, not proof of better mathematics
   or permission to rerun consumed tasks or failed qualifications.
   Establish subsequent changes from author/reviewer behavior on visible artifacts
   and unrelated synthetic controls. The latest internal/gold
   disagreement warrants diagnosis, not a benchmark-answer patch or more reviews
   by default. Do not start another draw merely to find an acceptance.
   Follow-up diagnosis found real conflicting scratch observations available to the
   same referee, not missing mathematics or truncated feedback. Native Haiku tool
   thinking is now opt-in transport support, without a scientific repair recipe.
   The [six-document configuration pilot](../benchmarks/reviewer_thinking_controls_20260909/README.md)
   completed once per case-arm pair. Both arms judged 6/6 candidates correctly,
   but some referee equation chains were wrong; the primary ceiling result is
   inconclusive. The [initial audit](operator_audits/referee_configuration_pilot_20260910.md)
   records 94 calls, report defects and shared tool-contract friction. Keep
   thinking off by default. Do not repeat or tune on this panel, add elementary
   controls merely to find a win, or mistake component judgments for research
   success. Code inspection established one shared interface defect: exploratory
   mathematics unnecessarily inherited the simulation callable/JSON-result ABI.
   Theory authors and isolated referees now run ordinary Python/R scripts in the
   existing sandbox and receive source-bound output/errors. No source patching,
   mathematical error classification, extra repair agent or statistical rule was
   added. Confirmation keeps its callable/metric authority. Full-suite verification
   passed 1326 tests; scientific improvement still requires fresh research evidence.
   Descriptions were delivered in the old pilot, so no transport omission is claimed.
3. Improve existing source-project/environment support where real reproduction
   needs it. Preserve model-selected actions and pinned dependencies; avoid a
   package-specific installer or another reproduction agent.
   Published Firth R, emcee and POT resources now execute through the existing
   source tools in pinned environments. These are operator resource checks, not
   autonomous research. Full source-aware task qualification failed for
   [Firth](operator_audits/firth_logistic_prequalification_20260910.md),
   [MCMC](operator_audits/emcee_stretch_prequalification_20260910.md) and
   [entropic transport](operator_audits/entropic_ot_prequalification_20260910.md).
   Each adds zero product draws. Preserve every record; do not rename a failed
   task, reduce its scope or keep selecting replacements just to obtain a pass.
   The latest protocol-13 theory calibration was 4/6; its reference also lacked
   a concrete confirmation design, so this is not a clean prompt-efficacy test.
   Do not turn that preparation flaw into another runtime prompt or error rule.
   Startup now verifies frozen mechanical and semantic authority without
   reexecuting calibration. Original reference/negative inputs stay hash-bound;
   missing or changed records cannot trigger automatic requalification.
   Hidden-gold review now reuses the retained loop, read-only document tools and
   isolated Python/R scratch, with a private Markdown report and exact transcript.
   The [PPI full-task qualification](operator_audits/ppi_logistic_prequalification_20260910.md)
   then completed once under protocol 15: 138 Haiku turns, 2083.906 seconds, 5/6
   short controls, and a rejected reference candidate. Its independent final
   referee introduced its own algebraic error and confused a pre-result design
   with completed experiments. The failed record is preserved, not corrected or
   relabeled; no source semantic qualification or product draw followed.
   A separate shared efficiency defect is corrected under protocols 16/17:
   stop after the first failed frozen control assessment, keep completed private
   reports, and mark an unreviewed candidate NOT_RUN. Do not change scientific
   labels, prompts, tools, within-case reasoning budgets or acceptance criteria.
   Do not run another task merely to find a pass or convert referee mistakes into
   statistical recipes. Diagnose general workspace/feedback limitations separately
   from mathematical reliability. New qualification remains unestablished; tests
   and operator source execution do not authorize a draw or establish research.
   A disjoint full-scope [GP qualification](operator_audits/gp_regression_prequalification_20260910.md)
   now supplies live evidence under the complete-file contract: mechanics passed,
   but theory qualification failed after 41 Haiku turns. Both reviewers described
   missing derivations without a counterexample yet emitted VIOLATED/FAIL. The
   original results remain unchanged; source semantic qualification and product
   execution did not run. Investigate completion-versus-contradiction semantics in
   the shared evaluator interface, not GP formulas, report-matching repairs, another
   reviewer or another topic selected merely to obtain acceptance. A possible
   interface correction is not yet a scientifically verified improvement.
4. Align formal execution and retrieval to the same active checkout. Use current
   file edits, Lean state and accessible-premise tools; transfer only selected
   verified declarations and their dependencies. Do not bulk-merge incompatible
   Lean libraries or equate RAG corpus membership with importability.
5. Add concurrency only where independent, measured work benefits, inside the
   existing graph with isolated workspaces, cancellation, hash-bound joins and
   stale-result handling. Do not add another runtime or concurrent writes to one
   authoritative document. Consolidate existing responsibility before expansion.
6. Measure scoped deliveries on fresh qualified tasks and cross-task reuse. Record
   actual calls, tokens, tool time, wall time and scientific outcomes. Compare
   mechanisms on preregistered disjoint controls, not repeated consumed candidates.

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
  Hidden-gold protocols 18/19 retain complete read-only candidate/reference files,
  scratch tools, thinking explicitly off, and private Markdown referee reports.
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
The MCMC, entropic-transport, PPI and GP theory qualifications are also consumed and failed.
Their source semantic roles were not run after the required gate failed; neither
the protocol-15 PPI report nor later execution changes add a product draw or credit.
Current facts live in
[main_worker_status.json](main_worker_status.json); historical manifests and
qualification ledgers remain the original evidence.
