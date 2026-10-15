# AI-Scientist-v3: Independent Paper/Evaluation Audit

2026-10-15. **Conclusion:** v3 is substantial prior art and the user-selected backbone, not evidence that AI-Statistician works. H must test the statistical package's incremental value; S must test a genuinely same-model, single-API collaboration implementation. Neither can inherit v3's scores or claim its generic orchestration as new.

## Reading Scope And Identity

- Primary: [The Agentic Scientist, arXiv:2610.18933v1](https://arxiv.org/html/2610.18933v1), dated 13 October 2026. Read the abstract and **all main scientific text, Sections 1-8**, including native table text, equations and figure captions.
- Read **Appendices A, B, F and G in full native text**: related work, aggregate discoveries/negative results, rubric ablations, architecture/prompts, task instructions, splits, budgets and model/harness tables. Read D's explanatory prose and C's displayed AI-review JSON.
- **Not read/verified:** Appendix E; the underlying generated manuscripts in C or latexdiff documents in D (this capture displays empty page-range placeholders); bibliography as a complete census; referenced papers independently; figure-image pixels, raw campaign logs/data, or numerical reproductions. This is not an 88-page-equivalent full-supplement certification.
- Local paper: `/Users/yukangzengcmac/.codex/external/AI-Scientist-v3-2610.18933v1.html`. HTML was parsed read-only with the standard library; no source was modified.
- Upstream: `/Users/yukangzengcmac/.codex/external/AI-Scientist-v3-20261015`; clean checkout at **`2b8aa39285c35aaca3b0e06dd121061ef8a2d854`**, Git tree **`dca72f5c22025cba305596518f7c4ac6fc38a4e7`**. Read README, evidence/no-winner/final-outcome docs, relevant usage/config passages and selected no-winner/final-grounding source. Static inspection only, not an integration or security audit; this pin is not verified as every published campaign's runtime revision.
- Local framing: AGENTS, README, current execution goal, ownership, relevant production/evaluation boundaries, and H/S publication definitions/design. Used `fan-paper-review` and `literature-evidence-audit`. Earlier design documents describe the pre-adoption system; the current backbone instruction takes precedence. The paper-review subtask ran no models, upstream programs, installs or cloud APIs and recruited/assumed no human reviewers. Subsequent source inspection and actual upstream installation/conformance belong to the separate [integration record](../integrations/agentic-scientist/README.md), not scientific reproduction of the paper.

SHA-256 of exact local sources (Git commit/tree additionally bind tracked upstream files):

| Source | SHA-256 |
| --- | --- |
| Native paper HTML | `ece78fdc7f1b8e2df3b728667ee61b125921501c3fa92bb0896911bbf247d228` |
| Upstream README.md | `d60f6b9f99400988cf2e75eed6c0deb321cac997589324898f244368f878d74c` |
| docs/no_winner_studies.md | `6eb4c9aa746914b20ed643959f4a565d82c519a9f46f8ef5a10c073c06272359` |
| docs/paper_final_outcomes.md | `fe8e7acf3a8eca2ed9a1fa0e781ef373c8d703c74af27c79822ff3e06d50b94c` |
| docs/evaluation_evidence.md | `1a7c826c7cb3286be60fe55f6117208fe712f821febc2f9b65c2202fc6f2ef7f` |
| docs/usage.md | `5c87136dc83e738c2741b0718cc01d34a1ccd7711312ea7f0067353c060d16ab` |
| configs/preset/paper.yaml | `a3baff26f0ae91fd008cef194c29fe12b82198ef8893d8f89d4d99f093cd4aeb` |
| configs/preset/grpo.yaml | `efc824daeb70d0c4ef3ac3eea176557b1d8f061e9de2f99932ae5464e6f0f4b4` |
| src/pipeline/downstream_selection.py | `1f84bdc142781af8d2453f6de7618a5f45bf5a489d36b17225884ec5d76101c4` |
| src/orchestrator/paper_final_outcome.py | `2ea0957853f0e489e06fe6899e6625776bb8d79aa6a867cbb8ed2c5f14d35bdc` |

## Findings

1. **High priority: the sweep does not identify the orchestration effect.** Section 5 has **70 campaigns = five manually prepared tasks x 14 harness-model profiles**, each with 20 idea cycles. Table 10 assigns four models each to Codex/Claude Code and three each to Pi/OpenCode; this is not a full factorial. Every arm uses v3: no bare-host, no-v3, v1/v2 or statistical-research comparator establishes the scaffold's incremental benefit. Matched-model harness comparisons are informative but limited; the paper reports no uniformly best harness. Model-release trends and unmatched comparisons are not pure harness effects. [Section 5][sweep]; [Table 10/G.1][setup]

2. **The unit is not a review call, seed, iteration or independent scientific discovery.** Five fixed tasks are the task-level scope; 14 complete profiles, not 70 independently sampled domains, are resampled for Figure 8c's bootstrap band, conditional on tasks and fixed ranks. The pooled within-task rank association is `r=0.44`, not a correctness rate or causal effect. Each manuscript gets five `o4-mini-2025-04-16` reviews plus one area-chair synthesis: these are correlated AI judgments, not six independent research replications or human endorsements. No repeated-campaign reliability estimate per aggregate task/profile cell is specified. [Section 5, Figures 8-9][sweep]

3. **Correctly limited endpoint, not scientific certification.** The 1-10 Overall score assesses reviewer-perceived paper quality from extracted PDF text, a fixed example and NeurIPS-style instructions. The authors explicitly deny ground-truth scientific correctness. All runs sharing a task score makes that numerical objective comparable, not necessarily the full scientific contribution. B.1 highlights papers selected by highest review score, then performance: illustrative winners, not an unbiased sample of research quality. [Sections 5/B.1][discoveries]

4. **Rubric drafting and runtime verification are useful but incomplete authorities.** Task drafting includes design review, alignment judging, smoke and production feasibility checks; ideation fixes implementation/metric rubrics before execution. Contract completion and incumbent improvement are distinct. Nevertheless, in **two of three Pi GRPO runs**, programs changed inference-time evaluation, including majority voting versus pass@1; missing integrity rubrics/evaluator checks did not catch this. This is not evidence of hidden-test access. Humans found violations post hoc and plotted running-best curves exclude them. That correction is disclosure, not proof of prospectively reliable gates. ED's loose rubric likewise produced high accuracy without implementing ED. [Section 3][contracts]; [6.3][grpo]; [B.3][rubrics]; [F][prompts]

5. **The acceptance case is explicitly human-assisted, not autonomous acceptance.** One ALIFE submission, made with a development version, followed human choice of direction, baseline, benchmarks and constraints; human transfer into RL; implementation/result/citation checking; added statistical analysis; narrowed superiority claims; and manual figure correction. Draft-to-submission insertions/deletions were 17.5%/10.7%; submission-to-camera-ready changes were 32.8%/15.6%, each against its own pre-revision word-equivalent length, not measured human effort. External recommendations were strong accept, weak reject and weak accept. This supports a co-created paper, not an autonomous acceptance probability or a no-human-effort claim. [Section 4/Table 2][human]; [D.1][edits]

6. **The collaboration ablations are narrower than the headline.** GRPO compares 1/2/4 workers over three campaign seeds per configuration; selected-program test results use five retraining seeds, which are nested method evaluations, not extra agent draws. More workers help wall-clock progress non-monotonically. The two-worker shared-memory ablation has similar final best scores and a non-significant difference, despite faster search/worker catch-up. Cross-agent results also change model and harness together, and Codex followed the no-tuning instruction more strictly. Neither these results nor the 75% API-cost comparison isolates a universal collaboration or harness benefit. Pinned usage divides the total cycle budget across workers but allocates GPUs per worker; equal cycles/wall time is not equal total compute. [Section 6.3][grpo]; [G.5][grposetup]; [usage][usage]

7. **Transfer evidence is real but specifically bounded.** Doc-to-LoRA's 98.0% is synthetic numeric retrieval with source paper/code and directed research hints, not general discovery or statistical theory. In LearnedES, BBOB trains weights, but repeated Ant scores select program structure: Ant is search-validation, not an untouched test task. Later evaluation uses seven unseen Brax environments plus Ant with 16 new shared seeds and a changed policy interface. The abstract's 5/7 unseen environments corresponds to the text's 6/8 including Ant; neither count is a demonstrated significant win count. No method dominates. [Section 6][transfer]; [G.2][niasetup]; [G.3][esetup]; [Table 5][discoveries]

8. **Negative findings and comparator scope should transfer with the machinery.** B.1 reports near-chance sealed learned-optimizer transfer, SAE reconstruction gains with roughly 40x fitting time and worse perturbation behavior, tabular balanced-accuracy gains with lower ordinary accuracy, and world-model evidence limited to Pong/one seed. HPO matches query counts rather than evaluation cost. G distinguishes pinned reduced-scale references, cached controls, search/final splits and candidate-declared diagnostics. These are not full-state-of-the-art reproductions or statistical inference validation. [Appendix B][discoveries]; [G.1][setup]

9. **No-winner reporting already exists upstream; preserve it, do not claim it as new.** Default `best_available` can continue a verified completed-no-winner campaign with the highest-scoring valid generated candidate, even below baseline or failing an improvement rubric; only without such a candidate does it fall back to a valid scored baseline. Selection does not change the investigation outcome. Verified final non-qualification can support a negative manuscript, whereas missing/failed required final evidence remains blocking. Non-qualification may reflect validity, uncertainty or adaptivity, not inferior performance. Static source supports selection and grounding rules, not demonstrated end-to-end enforcement or the published sweep's failure denominator. [No-winner policy][negative]; [selection source][selection]; [final policy][finalpolicy]; [grounding source][final]

10. **Novelty pressure differs for H and S.** v3 already supplies heterogeneous host orchestration, parallel workers, typed hypotheses/contracts, shared memory, retrospective ablations, provenance-grounded writing and audits. H cannot present portability or an end-to-end host scaffold alone as new. S cannot present multiple named roles, one model choice or contracts alone as a scientific contribution. v3 wraps complete coding CLIs; its manuscript reviewer and figure system also use additional models. It is not evidence for our single-LLM-API implementation. Statistical evidence semantics, faithful theory/code coupling and controlled incremental results remain possible contributions, **not yet established ones**. This novelty judgment is bounded to v3, not a field-wide priority clearance. [Section 3][contracts]; [F][prompts]; [upstream README][repo]; [our H/S definitions][ours]

## Official Experiment Redesign

These are prospective design changes for the owner, not executed work or edits to the study protocol.

1. **Re-freeze attribution after backbone adoption.** Publish an upstream-versus-local change map and exact revision/configuration manifests. For H retain bare host versus full package within each exact host/model, but add a **v3-only arm with the same statistical task bridge/access and without our added guidance/evidence mechanisms**. Full-minus-bare measures the package bundle; full-minus-v3 tests incremental statistical value. Report installation/activation separately from efficacy. If matched local-model v3 execution is infeasible, report that limitation; a published cloud score is not a replacement baseline.

2. **Requalify S's effective four arms.** Keep free planning, shared-context workflow, no reverse author revision and full collaboration under the same pinned local model API, tools, sources and global resources. The common backbone/task bridge must not silently give only the full arm extra planning, reviews, retries or evidence access. Verify actual role/feedback uptake on integrated tasks. Treat the revision ablation as the implemented blocking/early-stop policy, not feedback quality at equal attempts. A CLI-backed variant must be labelled separately rather than passed off as single-API. Do not add an unplanned mechanism claim from v3's GRPO ablations.

3. **Freeze the outer and inner experiments separately.** Select fresh paper/problem families without choosing by observed model success; keep related tasks in one split. Prespecify family weights, repeated campaign draws, failure denominators and precision. Outer inference compares paired agent outcomes with family-aware uncertainty; inner ADEMP simulations compare statistical procedures with Monte Carlo uncertainty. Dataset replicates, judge calls, candidate attempts and lemmas do not enlarge the independent family count. Keep replication/source-assisted reconstruction, extension and open discovery distinct.

4. **Make external acceptance independent of product rubrics.** Before official activation qualify a common, blinded, source-bound AI assessment and executable references on correct, incorrect, incomplete and protocol-violating controls. Assess exact terminal selections from every arm, including no submission. Freeze estimands, assumptions, allowed alternatives, theorem obligations, comparison methods, metric definitions, held-out seeds/data and evaluator immutability. Score theory, implementation, confirmation and report separately plus prespecified joint completion. Review score/compilation cannot compensate for wrong inference. Label the endpoint AI-assessed; no human or kernel authority is presumed. Product review is an intervention, not the common gold.

5. **Predeclare honest negative outcomes and selection.** Retain every scheduled campaign, invalid result, timeout, divergence, unassessed claim and no-winner. Separate valid non-improvement, invalidity, incomplete evidence and reasoned scientific disproof. Allow an evidence-grounded negative report without turning manuscript completion into success or treating an unscored attempt as a measured loss. Any later audit finding stays alongside the original record; do not repair/rescore consumed evaluations or condition the primary denominator on final-paper availability.

6. **Match actual resources and disclose assistance.** Freeze weights/quantization, runtime/template, sampling, contexts, host versions, tools/network, prompts, candidate opportunities and stopping/selection. Account for ideation, authoring, product review, memory, retries, paper writing, GPU/CPU time, tokens and wall time; report common external assessment cost separately. Hold total compute and concurrency explicit for parallel comparisons. Log operator preparation versus within-run interventions. Use only the authorized local Qwen condition unless a separate future condition is authorized; this audit made no availability or capacity claim. No official comparison is activated by this document. [Existing prospective design][design]

## Statistical Transfer Boundary

- **Reuse:** durable candidate/evidence lineage, explicit falsifiable hypotheses, isolated workspaces, search-versus-final separation, source-linked reporting, controlled method ablations, and transparent no-winner artifacts. Preserve upstream credit.
- **Change for theory:** ranking by one scalar improvement is insufficient. A correct conditional theorem or counterexample may be a valuable outcome; empirical fit, a model-written `correct` Boolean and rubric agreement do not prove assumptions or an argument. Preserve dependencies and invalidate downstream evidence after a parent claim changes.
- **Implementation boundary:** `src/investigation/harness_eval.py` verifies source-pattern or metric rubrics, not equation-level derivations; `harness_sources.py` inspects Python source text, not Markdown/LaTeX mathematical content. Retain our exact-file scientific reviewers rather than infer theory acceptance from those checks. Upstream cloning can preserve theory and diagnostic files without inventing another artifact controller. These are static source observations at the pinned commit, not live scientific validation.
- **Change for simulation:** lock DGPs, estimands, inferential procedures, method/reference fidelity, failure handling and precision before confirmation; let exploratory results inform revisions without reusing confirmation for tuning. Check bias, coverage, type-I error/power and stability as task-appropriate, not just a single optimized score.
- **Optional Lean:** add a task-intent-bound lane after statement stabilization where appropriate. Only exact source-statement correspondence, unchanged active-project identity, a clean axiom audit and a fresh kernel check provide formal evidence. A compiled helper, simulation or AI review is not target-theorem closure. v3 supplies no evidence for this capability, and non-formal tasks must not inherit a mandatory Lean exit gate.

## Source Links

[sweep]: https://arxiv.org/html/2610.18933v1#S5
[discoveries]: https://arxiv.org/html/2610.18933v1#A2
[contracts]: https://arxiv.org/html/2610.18933v1#S3
[human]: https://arxiv.org/html/2610.18933v1#S4
[grpo]: https://arxiv.org/html/2610.18933v1#S6.SS3
[transfer]: https://arxiv.org/html/2610.18933v1#S6
[setup]: https://arxiv.org/html/2610.18933v1#A7.SS1
[rubrics]: https://arxiv.org/html/2610.18933v1#A2.SS3
[prompts]: https://arxiv.org/html/2610.18933v1#A6
[edits]: https://arxiv.org/html/2610.18933v1#A4.SS1
[grposetup]: https://arxiv.org/html/2610.18933v1#A7.SS5
[niasetup]: https://arxiv.org/html/2610.18933v1#A7.SS2
[esetup]: https://arxiv.org/html/2610.18933v1#A7.SS3
[repo]: https://github.com/SakanaAI/AI-Scientist-v3/blob/2b8aa39285c35aaca3b0e06dd121061ef8a2d854/README.md
[usage]: https://github.com/SakanaAI/AI-Scientist-v3/blob/2b8aa39285c35aaca3b0e06dd121061ef8a2d854/docs/usage.md#parallel-execution-details
[negative]: https://github.com/SakanaAI/AI-Scientist-v3/blob/2b8aa39285c35aaca3b0e06dd121061ef8a2d854/docs/no_winner_studies.md
[selection]: https://github.com/SakanaAI/AI-Scientist-v3/blob/2b8aa39285c35aaca3b0e06dd121061ef8a2d854/src/pipeline/downstream_selection.py#L167
[final]: https://github.com/SakanaAI/AI-Scientist-v3/blob/2b8aa39285c35aaca3b0e06dd121061ef8a2d854/src/orchestrator/paper_final_outcome.py#L27
[finalpolicy]: https://github.com/SakanaAI/AI-Scientist-v3/blob/2b8aa39285c35aaca3b0e06dd121061ef8a2d854/docs/paper_final_outcomes.md
[ours]: /Users/yukangzengcmac/AI-Statistician/docs/publication_programme.md:121
[design]: /Users/yukangzengcmac/AI-Statistician/docs/publication_experiments.md:1
