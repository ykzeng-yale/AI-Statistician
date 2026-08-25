# Fixed-effect inverse-variance meta-analysis R L0 v1 operator audit

## Frozen authority

- Task: `inverse_variance_fixed_effect_meta_analysis_r_known_result`
- Family: `fixed_effect_meta_analysis_r`
- Public reference: W. G. Cochran, *The Combination of Estimates from
  Different Experiments*, Biometrics 10(1), 1954, DOI `10.2307/3001666`
- Visible question SHA-256:
  `e0e5bae056b35066ba89db63b335d82d9aac77712c260e38fbe5bd685207bfd1`
- Visible question hash:
  `a28f053f6488f02d4ecfef60f42c2500d70f8eb313a3bafab0b26c91fc356b09`
- Evaluator descriptor:
  `136f974374dc57862c0d5e91c7caaff23f7c95bef3df4ce553ad68d8f7af581a`
- Activation commit: `74ceafe62d5e22618dd96356252cce949a55e58c`
- Runtime code head: `a0186de603283986360724ee7ddfce853a67b911`
- Model for every enabled live role: `claude-haiku-4-5-20251001`
- Formal evidence: `not_applicable`

The visible task and evaluator-only gold were calibrated, frozen, committed,
and pushed before the first product-model call. The task received exactly one
fresh model draw and one post-termination hidden evaluation. Its immutable
full-task score is `0/1`; it must not be rerun, resumed, repaired, rescored, or
resampled.

## Runtime result

The canonical runtime terminated `BLOCKED` after seven outer traces, three
Architect traces, and six handoffs. It executed one generated Algorithm
sandbox and no generated Simulation sandbox. Research evaluation was `0/1`
but mode-conformant. Formalizer correctly remained inactive. The terminal
classification was `architect_metric_requirement_packet_validation_failed`.

TheoryDeveloper produced three authoritative Markdown/LaTeX documents in its
persistent workspace. Independent preflight accepted the exact document set.
The accepted packet hash is
`ab142945e9aec1b61f961ae3c8d2ac0f9632ea5d3972829563895ea1af947de7`;
the document-set hash is
`e804277cbe20007ba31c124a9d95c6ea02b40b574c53d568d38a5ded9cb0e961`.

AlgorithmEngineer authored, executed, and committed one exact R
`run_estimator` implementation. The independent reviewer ran one
reviewer-authored R probe against those immutable source bytes and accepted
the source. The accepted source hash is
`e1a9a43aef71e17d5a54179737ef9072ee082cf912abaf25f31bad84b673e9c5`;
its accepted handoff hash is
`1f63b09e3f3501f29225da4571f6cfbde7569684e8a720b7d0ef93eae9184500`.

The metric source owner then used the external `metric_protocol.json`
workspace. Across ten model/tool calls it read once, wrote an initial
candidate, received raw validation errors on commit, and revised the same
hash-bound file. Three invalid operators remained after the second commit.
Because `edit_metric_protocol` accepted only one exact replacement per call,
the model repaired two rows in separate turns. Its attempted third edit was
rejected when the standard-turn budget ended, and the required terminal commit
correctly failed with the final row still invalid. Simulation and Critic were
never reached.

## Hidden evaluation

The immutable hidden result is `0/1`:

- theory mechanics: `7/7`;
- calibrated theory semantics: `7/7 SATISFIED` after `9/9` calibration;
- exact R estimator contract: `12/15` over 23 invocations;
- exact empirical assessment: `7/7` over 12,000 estimator invocations;
- empirical dimension: hidden gold passed, but runtime never accepted it;
- unresolved-gap disclosure and overall runtime loop: failed;
- formalization: `not_applicable`.

The three failed source checks were aggregate acceptance, rejection of a
request with missing or extra keys, and rejection of an invalid named
`theta0`. Both boundary behaviors were explicit in the public estimator
contract. The generated source did not validate them, and the source reviewer
did not falsify them with its optional probe. Formula, equivariance, equal
variance, and empirical checks passed, but those component facts cannot erase
the public-interface failures.

The hidden theory, semantic, algorithm, and empirical result hashes are,
respectively:

- `2448162397b7703a7f48b7085f566f96c6179c7bac3eeaf4f72af86fd45a11b6`;
- `10e452086c2b7700435b62637bb7812eb6f2ad1550387c7a62290682962a1e28`;
- `67313b4e117d8c52e0ced5e90c626338d1ba728397de3136f96841b260d7d13a`;
- `095f8a720285a0bbf98bc2906a462ae4478e410bd83293a4db9df4a8634c19cb`.

The runtime manifest, runtime result, and hidden report SHA-256 values are:

- `6954407883a94f8cacea913b18b41ce133e579f3a3484998c0cb83cea6cffd79`;
- `36bac7742e95ad917575eb9d1fa7d0edcd639b3dc9ec168b2ce92f9512f6aa59`;
- `b34a7e94e0e5eb22f3b9048e3761ee995ea4233c0e19da636a9d2f1e9389cedf`.

## Shared diagnosis

This draw validates the Codex-inspired persistent artifact loop but exposes
two generic tool-use issues.

First, exact single-literal editing is too weak when one validator observation
reports several independent defects. The existing edit tool should support an
atomic list of exact replacements under one parent SHA-256. Runtime should
verify uniqueness and atomicity; the model should continue choosing all
content. This is a capability-preserving tool improvement, not a retry,
repair agent, packet translator, or larger turn budget.

Second, an executable reviewer with an exact-artifact probe should be prompted
to try to falsify explicit public rejection and boundary behavior, preferably
in one broad model-authored probe. The harness must not encode a fixed test
checklist or hidden cases.

Both corrections apply only to future unrelated tasks. Neither may change this
task's immutable `0/1`.
