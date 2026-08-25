# Mann-Whitney U R L0 v1 operator audit

## Frozen authority

- Task: `mann_whitney_u_null_moments_r_known_result`
- Family: `two_sample_rank_inference_r`
- Public reference: H. B. Mann and D. R. Whitney, *On a Test of Whether
  one of Two Random Variables is Stochastically Larger than the Other*,
  The Annals of Mathematical Statistics 18(1), 1947, DOI
  `10.1214/aoms/1177730491`
- Visible question SHA-256:
  `94d5b2ed0a59b67878fbf8d62396e9ae13c0c565cabc12e9419abf3ba903d635`
- Visible question hash:
  `4292e222714f7b6daa389cfaec0f4622be319363d9ba6b387ed11eb85f6643d8`
- Evaluator descriptor:
  `677c9b8330d4ee88ca16b4d5f620773b4449af665f5c9dea61a4840fa87a7193`
- Activation commit: `8e8d2e7db9328298eb1215cb5b137c70e8f07c33`
- Runtime code head: `5b87529923eb3543267f6a5a8381e39b580cd5d1`
- Model for every enabled live role: `claude-haiku-4-5-20251001`
- Formal evidence: `not_applicable`

The visible task and evaluator-only gold were calibrated, frozen, committed,
and pushed before the first product-model call. The task received exactly one
fresh model draw and one post-termination hidden evaluation. Its immutable
full-task score is `0/1`; it must not be rerun, resumed, repaired, or rescored.

## Runtime result

The canonical runtime terminated `BLOCKED` after seven outer traces and six
handoffs. It executed one generated Algorithm sandbox and no generated
Simulation. Research evaluation was `0/1` but mode-conformant. Formalizer
correctly remained inactive. The terminal classification was
`architect_metric_requirement_packet_validation_failed`.

TheoryDeveloper used one persistent Markdown/LaTeX workspace for twelve model
turns. It wrote two authoritative documents, ran R and Python scratch programs,
corrected one write-validation error in the same session, and explicitly
committed. Independent preflight read the exact documents and accepted them.
The accepted packet hash is
`281f986f4dbd88becd5a03e7fe396df363ae4af2e23aebac349416c301fdaa02`;
the document-set hash is
`54e0d7c1a1bfd8d7d25659ff85a393dc08fdbc982cc72b6eb200a8fa4a584e07`.

AlgorithmEngineer authored, executed, and explicitly committed an R
`run_estimator` implementation in one persistent source-owning session. The
isolated generated-code reviewer voluntarily used the optional exact-estimator
probe twice. Both probes ran model-authored R against the exact immutable
source bytes. Its first verdict envelope was invalid; the same reviewer
received the validation observation and submitted an accepted disposition.
This is positive disjoint live evidence for the optional Codex-inspired probe
mechanism, but probe use itself is neither required nor proof.

The accepted estimator source hash is
`1ffe8120ff1ebe1e38aac078ac56f689522988c5bf142870680c7591be787454`.
Its accepted handoff hash is
`e225314114240ea1635165b2e31108c0f7271494c3f38e76b943c6cf28b28ee6`.

## Hidden evaluation

The immutable hidden result is `0/1`, with strong component evidence:

- theory mechanics: `7/7`;
- calibrated theory semantics: `7/7 SATISFIED` after `9/9` calibration;
- exact R estimator contract: `14/14` over 17 invocations;
- exact empirical assessment: `6/6` over all 41 assignments;
- empirical dimension: hidden gold passed, but runtime never accepted it;
- unresolved-gap disclosure and overall runtime loop: failed;
- formalization: `not_applicable`.

The hidden theory, semantic, algorithm, and empirical result hashes are,
respectively:

- `2448162397b7703a7f48b7085f566f96c6179c7bac3eeaf4f72af86fd45a11b6`;
- `51ff41a7c3374a8b11858595eccb1179d2c2dfac23b90341dd58272aad856ce5`;
- `6eb5fe65fb84ebcfedc7b1f5927cc42fc7ae95486c4e4578aa5fa64806929809`;
- `959ac63c279d111931b3a10a449c41043386bcf22fb84327c364f85cdb699989`.

The runtime manifest and hidden report hashes are
`412f15cf7599a48917c39c0ed76de588025eaebe315645c997d089d8e155feb5`
and
`ef13efa0811aaaaf1773d8c6b8a67d0fc3ed267bdd12d2bf9284e46d848f5cc9`.

## Shared diagnosis

The metric source owner read an empty `metric_protocol.json`, then attempted
the terminal `submit_metric_protocol_candidate` tool five times. Four complete
tool inputs were cut off at the provider token boundary and were correctly not
executed. The fifth stored an 8,041-byte model-authored document but failed two
shared mechanical checks: the portfolio replicate count was not preserved by
the materialized rows, and the submitted key did not produce a required
`SimulationEngineer` requirement row. No terminal recovery call remained.

This exposes a harness contradiction. The transport is described as an
editable persistent workspace, but its only authoring operation sends the
complete JSON document inside one terminal tool call. It is still full-packet
regeneration and makes artifact size compete with the final-disposition budget.
The right future-task correction is an external model-owned file with ordinary
read/write or patch actions and a compact hash-bound commit. Runtime may parse,
validate, and return raw errors, but must not author metrics, translate this
candidate, increase retries, or add another agent or scheduler.

Nothing in that shared correction can change this task's immutable `0/1`.
