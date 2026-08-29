# Poisson log-linear IRLS L0 v1 operator audit

## Frozen result

Task `poisson_loglinear_irls_known_implementation` received its sole product draw
from product head `c99947868a16870ca40262e76bde1f751b7ca019`. Runtime returned
`BLOCKED`; research evaluation completed `0/1`, and the post-runtime hidden
authority returned `0/1` without executing either candidate harness because no
independently accepted Algorithm handoff existed. The trustworthy aggregate is
therefore `5/89`.

The visible question, exact estimator ABI, statsmodels v0.14.6 source snapshot,
reference estimator, three behavioral negatives, two 1000-replicate confirmatory
designs, and hidden evaluator were frozen and activation-tested before the first
product call. Theory and formalization were explicitly not applicable.

## Exact topology

One `AgentRuntime` used four outer steps and three sparse handoffs:

1. Architect routed directly to AlgorithmEngineer without a Theory task.
2. AlgorithmEngineer returned no accepted source.
3. SimulationEvaluator correctly refused to proceed without an immutable accepted
   Algorithm handoff.
4. CriticEvaluator terminated the task as `RESEARCH_CANDIDATE_INCONCLUSIVE`.

All 29 product model turns used exact `claude-haiku-4-5-20251001`: one Architect
turn, 26 retained Algorithm client-tool turns, and two Critic turns. Simulation
made no model call. Formalizer and its semantic reviewer were disabled. There was
no Sonnet or Opus call, provider fallback, model escalation, repair worker, or
second scheduler.

## Source-owner failure

The Algorithm session used 10 `search_research_sources` calls and 14
`read_research_source` calls. It authored no source, requested no sandbox run, and
made no exact edit. After all 24 ordinary turns were consumed, the generic loop
exposed only the terminal tool. Both resulting `commit_scientific_source` calls
received the same raw rejection: no executed scientific source was available to
commit. The persisted checkpoint contained zero source updates, zero checks, and
no draft, so it correctly was not promotable or resumable.

This is a shared harness-capacity finding, not a Poisson implementation finding.
No product candidate reached Python, independent source review, Simulation, or the
hidden evaluator. The run provides no evidence about whether that model could have
implemented the estimator after finishing its source inspection.

## Future-task correction

Commit `c3a754e2cde4a264b4f9b54f14b39a78fb1bf499` gives the existing retained
Theory, Algorithm, Simulation, and Lean owners longer single-session capacity and
makes the Scientific/Lean allowance explicit in their initial context. It adds no
task formula, source patch, hidden feedback, retry, fallback, agent, scheduler, or
verifier. A source owner can still terminate as soon as it commits.

This follows the useful OpenAI Codex harness boundary: the same model session owns
tool selection and receives raw outputs; artifact state remains external and
content-addressed; cross-workspace handoffs occur only for substantive ownership
changes. Codex Core, App Server, Responses transport, provider state, Guardian,
thread/worktree management, and its multi-agent scheduler remain outside the
canonical runtime.

## Immutable evidence

- Runtime manifest SHA-256: `27198457cf05dffa3c341295df9d11eefd7e82262e4e9cb62e8c53bba39216bf`
- Runtime result SHA-256: `9fde2c8d8549dcb53f52cd0854df9723aced2011e469e1fdfc001bfcea19dbb3`
- Hidden gold evaluation SHA-256: `0983402ca3d75e04dee4cee13f64a54787210fd5cd482c97de48ca9a544f7491`
- LLM topology SHA-256: `b8cc246e1462b547f7e8fdc4df93265d4dc972d965ac1a0174d942e605bfa3dc`
- Completion summary SHA-256: `ef2cf1406e116c6d1125dec8e6ea51423b6f6e2451839e8d47d1b5d8ddca7e4d`
- Failure summary SHA-256: `03427e45a9f439c34d453115231ddf861031e4cafde9b22e5c591aa35a6e6afd`
- Algorithm session SHA-256: `b055004bc2b2919d92f9efaeabfb6bc960252284301940cf28a5ce4e327e2237`

The sole product invocation and automatic post-runtime gold assessment are
consumed. Never rerun, resume, repair, reevaluate, rescore, resample, manually
complete its source, or expose hidden/operator findings to this task's source
owners.
