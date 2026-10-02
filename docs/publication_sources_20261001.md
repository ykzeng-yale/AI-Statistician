# Publication Sources And Reuse Decisions

Checked 2026-10-02. This is a focused continuation of the local collection and
[previous reuse audit](research_harness_reuse_strategy.md), not an exhaustive
survey of all publications. Read primary methods/limitations and inspect relevant
code before adopting a component. Website claims and published scores are not our
experimental results. Pins below are observed upstream HEADs, not dependencies.

## Closest Research Harness And Evaluation Work

| Primary source | What matters for our papers | Adoption boundary |
| --- | --- | --- |
| [PARNESS, May 2026](https://arxiv.org/abs/2605.05258) | Declarative research composition, paper/code links and durable knowledge are already prior art; its limitations distinguish operational E2E from measured quality | Read graph runner; do not add its second scheduler or copy unlicensed code |
| [NORA, May 2026](https://arxiv.org/abs/2605.02092) | Domain skills and generator/evaluator separation already appear in a domain-specific research harness with expert case evaluation | A statistical skill collection needs measured incremental value; do not inherit its fixed workflow/taxonomy |
| [ResearchClawBench, June 2026](https://arxiv.org/abs/2606.07591) | Hidden target papers, expert rubrics and a minimal native-API research loop | Reuse task isolation and evaluator methods; rubric score above a threshold is not mathematical novelty certification |
| [AutoSciRub, August 2026](https://arxiv.org/abs/2608.31076) | Explicitly studies evaluation quality before agent improvement | Evaluate referee calibration; do not allow author-generated/adaptive rubrics to redefine confirmation |
| [PaperBench](https://arxiv.org/abs/2504.01848) | Reference-aware replication rubric and separate execution/grading | Use cell/artifact-level independent replication checks and held implementation; statistical theory needs additional mathematical authority |
| [CORE-Bench](https://arxiv.org/abs/2409.11363) and [June 2026 follow-up](https://arxiv.org/abs/2606.26158) | Reproducibility, model/scaffold separation, shortcuts, reliability and human collaboration | Measure execution rather than copied output files, failures and effort; pin benchmark version |
| [AstaBench](https://arxiv.org/abs/2510.21652), [code](https://github.com/allenai/asta-bench) | Scientific task categories and reproducible evaluation environments | Candidate external component benchmark, not a statistical derivation gold set |
| [AI Agents That Matter](https://arxiv.org/abs/2407.01502) | Agent quality must be interpreted together with cost and evaluation validity | Matched resources, complete failure reporting and explicit model/scaffold attribution |
| [OneFlow / strong single-agent workflow baseline, v1](https://arxiv.org/html/2601.12307v1) | Shared-conversation role-playing is a distinct strong control for homogeneous workflows | Preserve a separate free-planning general-agent arm; do not import MCTS or assume cache/semantic equivalence |
| [Towards a Science of Scaling Agent Systems, v2](https://arxiv.org/html/2512.08296v2) | Controlled tools, prompt structures and resources expose task-dependent coordination benefits and costs | Test whether collaboration helps statistical tasks; neither agent count nor published cross-domain results establishes our benefit |
| [AI Scientist v2](https://arxiv.org/abs/2504.08066) | Executable candidate search and full research artifacts | Conditional baseline where compatible; do not port its controller or infer theoretical correctness from paper review scores |
| [Morris, White, Crowther](https://doi.org/10.1002/sim.8086) | ADEMP and uncertainty in simulation performance measures | Scientific experimental design and reporting; no hardcoded method choices |

## Formal Mathematics And Statistics

| Primary source | Useful design | Boundary |
| --- | --- | --- |
| [Statlib roadmap](https://stat-lib.github.io/roadmap.html), [repository](https://github.com/stat-lib/statlib) | Shared statistical objects and semantic modules covering inference, local asymptotics and other planned theory | Roadmap is not proved coverage; keep active-project pin until a tested migration |
| [Statistical Learning Theory in Lean 4](https://arxiv.org/abs/2602.02285), [repository](https://github.com/YuanheZ/lean-stat-learning-theory) | A coherent empirical-process development and reusable concentration infrastructure | Compatibility and statement audit before import; cite human/library contributions separately from agent performance |
| [Prove2Me](https://arxiv.org/abs/2608.28433), [workspace](https://github.com/prove2me/prove2me_workspace) | Stable statement/proof separation, explicit environment and solution dependencies | Borrow protocol concepts; no service submission or unlicensed copying; reductions can remain conditional |
| [Anthropic Fermat repository](https://github.com/anthropics/fermats-last-theorem) | `formalization.yaml`, `PROOF-PATH.md`, comparator and attribution provide a concrete proof-map release pattern | Adapt map/schema ideas to statistical sources, not its mathematical corpus; preserve source-fidelity and dependency checks |
| [Numina](https://arxiv.org/abs/2601.14027), [code](https://github.com/project-numina/numina-lean-agent) | General coding tools plus Lean environment feedback | Lean component baseline after compatible backend adaptation, not reported-score transfer to Qwen |
| [Minimal theorem agent](https://arxiv.org/abs/2602.24273), [code](https://github.com/Axiomatic-AI/ax-prover-base) | Iterative source generation and compilation as a compact prover baseline | Compare same targets/resources; no issue-specific Lean repair rules |
| [LeanDojo/ReProver](https://arxiv.org/abs/2306.15626), [code](https://github.com/lean-dojo/ReProver) | Accessible premises and verified state/action feedback | Environment compatibility and retrieval evaluation; cannot certify a natural-language statement by itself |
| [LeanMarathon](https://arxiv.org/abs/2606.05400) | Durable dependencies for long formal developments | Use only for sufficiently long proof work; not a mandatory graph for every small task |

## Code Pins And Licensing

New independent reference preparation uses
[RepliSims](https://arxiv.org/abs/2307.02052) and published JSS archives for
[scikit-fda](https://www.jstatsoft.org/article/view/v109i02) and
[bizicount](https://www.jstatsoft.org/article/view/v109i01). RepliSims assesses
replicability, not correctness of the original methods; neither those reports nor
package tests provide mathematical gold. The
[preparation record](../benchmarks/publication_reference_qualification_20261002/README.md)
pins six candidate sources, archive/source hashes, rights limits and actual
terminal outcomes. No full reference has yet qualified: Austin has two failing
branches and one runnable narrow probe; scikit-fda has three failed environment
attempts; bizicount has a package/session version mismatch; the other three
repositories have unresolved code rights. No author algorithm was patched, no
model was called, and no study or test split was activated. The already consumed
DoubleML paper family is excluded from the fresh test pool. This preparation is
evaluator work, not product research autonomy or a new runtime dependency.

GitHub API metadata/tree and selected source files were checked. No missing
license is interpreted as permission to copy. Existing earlier pin audits remain
historical; new HEADs do not automatically update our runtime.

| Repository | Observed SHA | License/inspection |
| --- | --- | --- |
| gtrhythm/PARNESS | `100b4f7d67d23fae3db58619dbc077dde451d2aa` | No top-level license observed; graph-runner contract inspected |
| InternScience/ResearchClawBench | `01bc2371f698f755892935ef2965a95a790ff0db` | MIT reported; task/evaluation tree and primary protocol inspected |
| princeton-pli/hal-harness | `16bb03ebc11577fb5ea6dc8bb6c968387085e6aa` | No top-level license reported; `hal/agent_runner.py` inspected; the previously found princeton-nlp URL returned 404 |
| stat-lib/statlib | `ba207125f4920a5725589da4dbe0d2dd63c2f209` | Apache-2.0; README/tutorial/roadmap and tree inspected; active dependency remains `6575d611` |
| YuanheZ/lean-stat-learning-theory | `d0f506f0a695018265dccb33bcb05e2f5ca1c876` | Apache-2.0; primary paper and library layout inspected |
| prove2me/prove2me_workspace | `4bb28221f86306b70b58f8119c4413025d09b302` | No top-level license observed; statement/proof and environment references inspected |
| anthropics/fermats-last-theorem | `6e837e75355538c7f80bab5b956861e86c4eacc2` | Apache-2.0; map/comparator paths, `formalization.yaml` and comparator launcher inspected |
| MoonshotAI/kimi-cli | `9ab1286b8fe4e6bcd116949a27ce5e0ac3389c82` | Apache-2.0; skill discovery documentation and tree inspected |

The earlier Kimi pin is historical: the Python repository is now archived and
points to [`MoonshotAI/kimi-code`](https://github.com/MoonshotAI/kimi-code).
The current repository was inspected at
`21406fb4c805cc8c715e6d1f16ad3fb5f25f4fe3` (MIT); native ACP skill lifecycle,
provider and scoped-tool interfaces were checked against the installed npm
`@moonshot-ai/kimi-code@2.1.1`. No upstream controller is added as a production
dependency. The CLI is a separate portable-host test subject.
The installed ACP adapter's `prompt` / `driveSkillActivation` uses the native
agent skill service. Discovery, headless prompt text and actual skill activation
are different surfaces. A deterministic captured-request check now verifies
the ACP path; no adapter or scheduler is copied into the product.

CORE-Bench was inspected at `e32a2980e72fe6eb04ee04eb749458f570625663`.
Its README marks the old runner as unmaintained and recommends HAL. Its public
`core_train` metadata is a development resource, not hidden publication test
gold. Capsule `7935517` includes generated paper outputs, precomputed data and
knitr caches inside `code/`; merely hiding `results/` is not enough to measure
fresh reproduction. The development pilot stages only licensed unchanged R
source/README/license and compares new seeded outputs with an independent
execution of the author function. It does not claim an original CORE-Bench score.
Both native Qwen draws failed to produce the requested CSV. The installed skill
was advertised but its body was not loaded in the headless arm, so this pilot
cannot estimate a causal harness effect. See the immutable
[first assessment](../benchmarks/publication_development/kimi_type_ms_20261001/observed_results.json).

Numina's current README now states MIT; the earlier audit found no root license
at its old pin. Recheck the exact code revision/license before redistribution.
HAL and PaperBench are external evaluation candidates, not production agent
framework dependencies. The Dream-RSI skill remains optional history-informed
exploration guidance; it is not a new scientific scheduler or proof authority.

## Host Integration

Native skill loading is the first portable integration boundary:
[Codex](https://learn.chatgpt.com/docs/build-skills),
[Claude Code](https://code.claude.com/docs/en/skills), and
[Kimi Code](https://moonshotai.github.io/kimi-code/en/customization/skills).
Use one source skill and each host's supported discovery path. Do not translate
an entire coding-agent CLI into a pure model generator or bypass its ownership.
Installation conformance, tool execution and scientific efficacy are separate.

The local model transport follows the upstream
[llama.cpp function-calling interface](https://github.com/ggml-org/llama.cpp/blob/master/docs/function-calling.md)
and the [Qwen model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507).
The server owns tokenization and native call parsing. The product retains source
ownership and executes only declared tools; no hand-written Qwen tool grammar,
benchmark answer repair or Anthropic fallback is added.
