# Dream-RSI Adoption Analysis

Reviewed 2026-09-26 against AI-Statistician `a7ad0441`. Decision: adopt a small
Codex operating skill now, not another product controller. No runtime integration,
replay experiment, live model call, or scientific capability improvement is claimed.

## Inspected Sources

- [Requested PDF](https://www.dream-rsi.com/assets/dream-rsi.pdf): 36 pages including
  appendices; inspected method, experiment tables/figures, and prompts. SHA-256:
  `b2403013a14c588d772fc6b66a2ae556e5e8e2bcc58402dd4b582d9ba95a793f`.
- [Versioned paper](https://arxiv.org/html/2609.14858v1): September 14, 2026.
- [User fork](https://github.com/ykzeng-yale/Dream-RSI/tree/4149ea9181ab1db80f85717ffda2c9f0f130e85b)
  and [upstream](https://github.com/zhengkid/Dream-RSI/tree/4149ea9181ab1db80f85717ffda2c9f0f130e85b):
  both expose only `main` at that commit, no tags. Upstream has no releases.
  Recursive tree inspection finds README, citation, images, and PDF, not runnable
  harness modules. README says implementation and reproduction scripts are pending.
- [Pinned repository PDF](https://github.com/ykzeng-yale/Dream-RSI/blob/4149ea9181ab1db80f85717ffda2c9f0f130e85b/papers/Dream-RSI.pdf):
  SHA-256 `5701649cd9793b29cd5fb32d727d101ad21fb23639c0d9f33c9adef826194342`.
  It differs from the website PDF, including method prose; do not treat their
  bytes or formulations as identical. Section/page references below use the
  requested website PDF. The versioned HTML clarifies recorded-child selection.

No repository LICENSE is present; GitHub reports `license: null`. The PDF bears
an all-rights-reserved notice. This skill is original operating guidance, not
copied prompt/code. Check release contents and licensing before any later vendoring.
Appendix C's solver listing is not the missing search harness.

## Paper Findings

Section 3 (pp. 4-6) separates a fixed coding agent/evaluator from model-edited
exploration-policy code. Recorded outcomes support alternative traversals, not
new generations. Selection improves the fitted replay objective, not necessarily
future discovery. Experiments concern Lasso implementations, numerical mathematical
constructions, and GPU kernels, not statistical-theory derivation or Lean.

The controlled Lasso Pro comparison is 317 versus 550 discovery calls and
2931.0 versus 3587.1 ms mean downstream runtime (Fig. 3). These are not total
policy-development costs or a Haiku result. Autocorrelation is worse than fixed
exploration (Table 1). The guidance ablation is on ConvDiv (Fig. 5), not evidence
that useful scientific instructions generally hurt.

Appendix B (pp. 18-23) prescribes exhaustive history reading, failure categories,
recovery allocation, and beta-adjustment rules. Its AUC/parallel-penalty objective
is not the same formula as Section 3's best-score/call-cost/batching objective.
That discrepancy needs executable-release clarification; neither should silently
become our scientific acceptance criterion.

## Engineering Interpretation

The following are our design conclusions, not claimed paper results.

**Best initial fit: executable exploration.** Algorithm implementation and
numerical counterexample search can offer trustworthy, comparatively cheap
observations. Preserve correctness constraints ahead of performance. A policy can
help choose candidate effort; it cannot choose which scientific conditions count
as correctness. For noisy simulation scores, retaining seeds, uncertainty and the
selection history matters more than simply maximizing the observed maximum.
Keep adaptive exploration separate from untouched confirmatory data.

**Theory should not acquire a fabricated reward.** A missing premise, explicit
counterexample, or independently reviewed lemma is useful feedback. A referee's
confidence, equation count, or polished derivation is not a numerical ground-truth
score. Continue long-horizon file-backed reasoning and review rather than force
every theory task into a scored candidate tree.

**Lean remains its own authority.** Selecting which exact proof workspace to
continue could eventually benefit. Reduced goal count or a compiling helper must
not substitute for the requested theorem's identity, statement review and clean
kernel check. Library/environment changes require new checks. Do not import a
search policy's definition of success into proof promotion.

**Recorded support is limited.** Unvisited alternatives have unknown outcomes.
A stopped historical branch does not establish that further work is futile.
Reordering branches also changes outcomes when their models consumed shared
history or state. Parent identity alone is insufficient in that situation: the
full observation dependencies must match. Treat historical policy comparison as
a restricted diagnostic, not causal off-policy evaluation of an arbitrary agent.

**Optimize neither bookkeeping nor the judge.** Use whole-history/task splits,
not random adjacent nodes, for policy development and transfer checks. A policy
can overfit repeated feedback without literally reading hidden scores. Measure
actual tokens, execution cost and elapsed time; batching bonuses do not model
stragglers, cache changes, shared resources or API limits. Do not transfer claims
from another generator to pinned Haiku without fresh evidence.

## Fit to the Existing Product

| Existing component | Reuse boundary |
|---|---|
| [`client_tool_loop.py`](../../../ai_statistician/client_tool_loop.py), `workspace_history_tool` and `_persist_workspace_observation` | Exact archived tool observations already exist. Retrieve them on demand; do not build a second memory store. |
| Same file, `persist_client_tool_session` and `client_tool_session_contract_fingerprint` | Parent references, durable-state identity, prompt/tool/model contracts can identify contexts. They are not automatically independent candidate branches. |
| Same file, `run_bounded_client_tool_loop` | Keep edits and raw execution feedback with the same source owner. No policy-development worker belongs inside every ordinary tool turn. |
| [`agent_runtime.py`](../../../ai_statistician/agent_runtime.py), `AgentRuntime.run` | Executes one active task at a time. A paper's batching policy does not supply missing isolated forks and joins. Do not wrap it in another scheduler. |
| [`production_design.md`](../../../docs/production_design.md) | Independent review, source horizon, confirmation blinding and intent-selected Lean remain authoritative. Policy preference is not evidence authority. |

Current transcripts record tool activity and checkpoint lineage, not a ready-made
Dream-RSI discovery tree with fixed per-candidate scores and replayable branching.
No adapter or simulator was added. This Codex skill is also not automatically
visible to AI-Statistician's Anthropic sessions; product context adoption would
need an explicit, version-bound reference through its existing source tools.

## Smallest Justified Next Experiment

Only pursue executable integration when a real exploratory task demonstrates
that candidate allocation is the bottleneck, and licensed implementation or a
separately justified small component is available. Start within one existing
scientific workspace, not across the whole research graph.

Use newly designated exploratory training histories with exact candidate/context,
evaluator, environment and measured cost references. Exclude all consumed
evaluation and confirmation records. Validate prefix visibility, immutable
outcomes, independent replay state, unsupported actions, and missing dependencies
before using a replay score. These are prospective tests, not tests performed here.

Compare an unchanged existing policy with the proposed policy on fresh disjoint
tasks under matched generator/evaluator settings and declared resource accounting.
All product tests/evaluations stay on `claude-haiku-4-5-20251001`. Choose experiment
scale from the question and available evidence, not the paper's branch counts.
Freeze the comparison before outcomes; do not retry consumed draws until one wins.
Adopt only a measured benefit in accepted quality versus total cost. Otherwise
retain the simpler model/tool loop.

## Skill Delivery

The parent `SKILL.md` is the sole operating entrypoint. Its repository location
keeps it versioned; a local symlink in `~/.codex/skills` makes it available to this
installation without copying instructions. No plugin, service, model provider,
permission change, or automatic task is required. Local discovery can vary by
Codex version; newer documented locations also include `.agents/skills`.
See [official skill documentation](https://learn.chatgpt.com/docs/build-skills).
Validation checks format and links, not scientific efficacy or automatic selection.
