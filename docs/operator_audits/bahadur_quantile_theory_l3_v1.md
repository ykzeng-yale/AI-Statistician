# Task108 Operator Audit: Bahadur Quantile Linearization

## Disposition

**FAILED, consumed, immutable.** The sole exact-Haiku product draw ended
`BLOCKED` in CriticEvaluator. Runtime research evaluation and the sole isolated
hidden assessment are both `0/1`. The hidden mechanical harness passed `7/7`, but
semantic adjudication satisfied only five of eight claims. Trustworthy aggregate
capability remains `7/108`.

## Frozen Boundary

- Public authority: R. R. Bahadur, *A Note on Quantiles in Large Samples*,
  Annals of Mathematical Statistics 37(3), 1966, DOI
  `10.1214/aoms/1177699450`.
- Visible question commit: `79e0d14d0bb5f17302d5f1595300a4f7045ea653`.
- Preactivation ledger commit and product source head:
  `07d748050de685790149d1817cf6473dd904cc22`.
- Product model: `claude-haiku-4-5-20251001` only; Sonnet, Opus, and automatic
  escalation were disabled.
- Run: `runs/main_worker_research_l3_bahadur_quantile_theory_20260829_v1_codex_workspace_exact_haiku`.
- Formalization, scientific code, simulation, source replication, and novelty
  were not applicable and did not run.

An initial CLI startup preflight failed before a run directory, model request, or
artifact existed because the wrapper resolved the venv interpreter symlink to the
system Python and could not import NumPy. The sole product invocation then used the
literal venv interpreter. This was zero product calls, not a discarded draw or a
rerun.

Hidden reference mathematics, rubric, calibration cases, near miss, labels,
responses, and judgments remained evaluator-only. The one post-runtime assessment
made two exact-Haiku candidate calls, generated no runtime feedback, and cannot
revise the consumed artifact.

## Harness Evidence

The retained workspace architecture operated without a second scheduler or repair
worker:

- TheoryDeveloper authored one 460-line, 19,960-byte Markdown/LaTeX document and
  committed one hash-bound checkpoint.
- One independent 240-line referee report was persisted and accepted. Its first
  workspace segment made durable progress; one same-owner continuation resumed the
  exact checkpoint without Architect replanning.
- Four runtime steps consumed three outer iterations plus one same-owner referee
  continuation.
- All 70 product calls were exact-Haiku client-tool turns: 22 TheoryDeveloper, 27
  independent referee, and 21 CriticEvaluator turns. The runtime executed 78 tools
  and returned ten raw tool errors to their current owners.
- No direct model call, retry, fallback, runtime-authored mathematical edit,
  Formalizer, AlgorithmEngineer, SimulationEngineer, Sonnet, or Opus ran.

This is valid evidence for durable mathematical authoring, isolated review,
same-owner checkpoint continuation, tool feedback, optional formalization, and
fail-closed final authority. It is not evidence that the author or referee reasoned
correctly.

## Mathematical Failure

The document states the familiar final Bahadur representation and limiting variance,
but its active derivation is not coherent.

1. The quantile inequalities subtract `F(q_p+t)` with the wrong right-hand sign.
   The required comparison is against `p-F(q_p+t)`, not `F(q_p+t)-p`.
2. The centered empirical-process increment is repeatedly assigned an extra
   deterministic `t f(q_p)` term. This conflates the deterministic CDF increment
   with the centered stochastic increment and destroys the load-bearing
   cancellation.
3. The local argument invokes an empirical density or weak derivative for the
   step-function empirical CDF, then acknowledges that the object is not defined.
   Later corrections do not deactivate those earlier equations.
4. The overshoot discussion says equality at a jump has probability zero. The
   empirical quantile is itself an order statistic and the empirical CDF generally
   overshoots `p` by a grid amount; the stated reason is false.
5. Most decisively, the influence function is written with the opposite sign from
   the document's own Bahadur expansion. The expansion requires the summand
   `(p - 1{x <= q_p}) / f(q_p)`, while the influence-function section uses
   `(1{x <= q_p} - p) / f(q_p)`. Matching variances cannot establish equivalence.
6. Multiple passages labeled `Wait`, `Revised`, or `Correct approach` leave false
   abandoned derivations active in the authoritative document rather than removing
   or delimiting them as scratch.

The hidden semantic judge independently rejected the local empirical-process
remainder, sign/influence consistency, and whole-document active-claim consistency.
Those judgments agree with the operator audit; the task would remain failed even if
the final Critic transport had succeeded.

## Referee Failure

The independent report noticed that the local empirical-process step was heuristic
and that abandoned revisions remained in the document, but called both nonblocking.
It then accepted the load-bearing theorem, called the influence function correct,
and used the matching variance as support. It missed the sign contradiction, the
false active equations, and the fact that an acknowledged missing load-bearing
transition leaves the derivation incomplete.

## Critic Harness Failure

CriticEvaluator's first terminal payload was truncated at its 5,000-token output
limit. Four later complete submissions copied the visible contract's literal
`gap_disclosure.status` value:

`COMPLETE: all known gaps are disclosed, including for an INCONCLUSIVE or REJECT result; this does not mean the research succeeded`

The validator accepted only the exact string `COMPLETE`. The model therefore obeyed
one runtime-owned ABI representation and was rejected by another until the generic
no-progress boundary stopped the session. This is a shared schema defect, not a
mathematical repair opportunity. The rejected Critic also proposed `ACCEPT`, so a
transport fix cannot retroactively make its judgment correct.

## Future-Task Correction

Commit `8e3a58c7` changes only shared future behavior. The visible Critic contract and
terminal tool schema now use the same exact `COMPLETE` enum. Existing author,
referee, and Critic prompts now require claimed aggregate, summand,
influence/action, normalized, and asymptotic representations to be expanded from
common definitions and checked term by term for sign and scale; a correct endpoint
variance or rate cannot close an unresolved load-bearing transition.

This follows official Codex's schema-first tools, stable model/tool loop, raw
observations returned to the same owner, bounded context, and explicit checkpoint
principles. Codex Core, App Server, thread manager, scheduler, provider transport,
and GPT-specific tool grammar were not imported. No Bahadur formula, quantile rule,
mathematical parser, RepairAgent, extra model call, retry, fallback, Sonnet, or Opus
was added.

## Evidence Hashes

- Theory document: `b27352e66f90915ca071a4d0a3b45070d279ff598a2475f1646818b14f37f248`.
- Referee report: `a077a98e5090c83a51f8749711c72668e91c73f9f282de3dc2eeb42f1f259b5b`.
- Runtime manifest: `3a6b9d6d11499fdd8436c73fa991537355aa379171b74dee845b2c5b71d332e2`.
- Runtime result: `faff2f4a0529171898abf589ee0f1d0a707f1503821f9a9a08b7782cc630f519`.
- Hidden assessment: `c1614529f662a4fd6045573c23da94f7b17f077a8d56cd46db88a6706ce9ebcb`.
- Runtime topology: `4d2e420bc59f58f07868e987c5c4ed38e17ec94d8eb9edd321149971d83515ee`.

The draw, artifacts, report, and assessment are consumed. Never rerun, resume,
repair, reevaluate, rescore, resample, manually patch, expose hidden authority, or
model-escalate Task108.
