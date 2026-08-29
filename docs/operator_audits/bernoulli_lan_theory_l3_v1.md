# Bernoulli LAN theory L3 operator audit

## Disposition

**FAILED, consumed, immutable: 0/1.** Aggregate trustworthy full-task capability
remains **7/104**.

Task `bernoulli_local_alternatives_lan_known_theory_rederivation` had one frozen
product draw at product head `c3245943a789a75b824a7aa435162809e4e7edbd` and one
post-runtime gold-assessment invocation. It must never be rerun, resumed, repaired,
reevaluated, rescored, resampled, manually patched, or model-escalated.

## Frozen scope

- Level: L3 known-theory rederivation.
- Required dimensions: theory and unresolved-gap disclosure.
- Not applicable: source replication, scientific code, empirical simulation,
  formalization, and novelty.
- Product/evaluation model: `claude-haiku-4-5-20251001` only.
- Hidden authority was frozen before the product draw under manifest SHA-256
  `e322a00588c90da6bdaf99ebc2ebbba4172e343ff99cfc040a9f531e68d999c4`.
- Runtime product head and both remote refs before the draw:
  `c3245943a789a75b824a7aa435162809e4e7edbd`.

## Runtime evidence

The canonical AgentRuntime terminated `BLOCKED` with classification
`theory_developer_reported_gap`. It used three outer-graph iterations and two
same-owner workspace continuations across five traces. The retained client-tool
progress records 96 product-model turns and 95 tool executions:

- 80 TheoryDeveloper turns.
- 16 isolated `ArchitectMetricSemanticReviewer` referee turns.
- 29 theory-document reads, 12 document writes/edits, 24 structured handoff writes,
  8 scratch executions, 8 checkpoint attempts, 2 progress checkpoints, and one
  explicit theory-gap terminal action.
- 15 tool executions returned raw errors; no runtime-authored content repair,
  retry agent, fallback, second scheduler, Sonnet call, or Opus call occurred.

The first TheoryDeveloper checkpoint produced a persistent mathematical document.
The independent referee rejected it after tracing a real LAN scaling error: the
linear coefficient was written as `h Z_n/(p_0 q_0)` instead of
`h Z_n/sqrt(p_0 q_0)`. The exact finding returned directly to the same source owner.
That owner revised the persistent workspace and propagated the central correction
through the likelihood expansion, Fisher-information form, joint limit, and power
calculation.

The final authoritative document is 319 lines and 14,309 bytes, SHA-256
`df3f1aee0ba26108621188705dc7e4d9979a7cea7a8d84e336e688c26db002c2`.
The referee report is 266 lines and 10,807 bytes, SHA-256
`d3e7530356e9c35b55d5617b890c52c0c394927a92e79b053dbd10b6b9768669`.

No independent review accepted the revised checkpoint. The source owner repeatedly
received only `claim_index[0] has invalid status` and
`sanity_check_index[0] has invalid status`, tried plausible undocumented values, and
then honestly reported a blocker. The actual runtime ABI allowed only
`OPEN|SUPPORTED|REJECTED|INCONCLUSIVE` for claims and
`PASS|FAIL|INCONCLUSIVE` for checks. This is a shared tool-contract discoverability
failure, not evidence that the revised mathematics was accepted.

Operator inspection also found an unreviewed active error in the terminal document:
line 218 says the upper-tail power approaches alpha as `h -> -infinity`; the displayed
formula approaches zero. This observation did not enter runtime feedback or hidden
scoring and is not used to patch or rescore the consumed task.

## Assessment boundary

The sole post-runtime gold-assessment invocation received the serialized
content-addressed result directly instead of a hydrated blackboard. It therefore
reported `runtime result is missing`, evaluated zero tasks, ran neither the hidden
mechanical nor semantic candidate evaluator, and made zero evaluator-model calls.
That invocation is consumed. It is not rerun after the loader correction.

The task remains 0/1 independently of that operator invocation defect: runtime had no
independently accepted revised theory packet, no completed research loop, and no
terminal Critic acceptance or gap-disclosure packet.

## Immutable hashes

- Runtime result: `9136f9b613770e162f362fa9a548bf61e520f0d3335b85e2e6c54f461d90afd8`.
- Runtime manifest: `f4e5ba1e8af09e28b160cfa558a0f62acf32f0677a5a8f263e3a8ccfcf416fe2`.
- Gold-assessment record: `52e8fb5eda961a894ba4cc33e63790437f31155711dc48efea09c541bd19f5c0`.
- Completion summary: `72349049e69db8ce8dd56cdfc5c121f4ac5184c943e69a9fc26dcc88eb180f36`.
- Failure summary: `bb755aba66b460f19e2b1da39f580f9677252740adccaa01a388db21666dfd2b`.
- LLM topology: `b00a05fec1ae65fe2d9fc3341758fbe5afae35c1f6621b8c5aa0a99372c298e8`.
- Progress ledger: `d27fa9759824cc8d67f78449a444b5096ab93ef1bc2244aceeb3f0e899a91dfc`.

## Future-task mechanism correction

Commit `36a3dbbe` makes every theory-index rejection name its exact allowed values and
adds one public hash-verified persisted-runtime loader used by resume and post-runtime
evaluation. Follow-up `9bf3a789` resolves relative persisted paths from result
lineage rather than process cwd. Neither commit adds a statistical formula, LAN rule,
source patch, retry, fallback, agent, scheduler, or model escalation. The shared
regression panel passed 157/157; the final complete repository passed 1074/1074 in
80.83 seconds. This is deterministic future-task harness evidence only and does not
alter Task104.
