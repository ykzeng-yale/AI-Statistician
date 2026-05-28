# Full AI-for-Math Collection

Generated: 2026-05-12

Scope: this is the broader AI-for-math / mathematical discovery collection. It is intentionally separate from the narrower `autoformalization-ai-for-math` Google Doc. This file tracks ideas, systems, benchmarks, and research routes; the companion `paper_links.html/json/txt` files track verified URLs.

Primary link list:

- `paper_links.html`
- `paper_links.txt`
- `paper_links.json`

Current state:

- 120 links in `ai-math-discovery-systems`.
- 98 manually verified links from the Gemini conversation plus foundational additions.
- 22 additional AI-for-math links were found in the current `ykzeng2019@gmail.com` Chrome session files and folded into the same collection.
- Latest Chrome scan: 2026-05-12, 6 session files, 73 paper/resource links seen this run, no new cumulative links.
- Unverified/hallucination-prone names are kept in `needs_verification.md`.

## Reading Route / 阅读路线

### 1. Generation + Verification Loop

Core idea: modern AI-for-math systems are not just LLMs. They are closed-loop systems: generate candidates, verify with a hard checker, recycle successes into training or a skill library.

Useful sources:

- FunSearch: program search + evaluator loop.
- AlphaProof / AlphaGeometry: neural generation plus formal/symbolic verification.
- DeepSeek-Prover series: proof assistant feedback, RL, MCTS, subgoal decomposition.
- STP: self-play theorem proving with iterative conjecturing and proving.
- Axiom Putnam 2025 repo/report: public artifact for a generation-verification style system in Lean.

Status: verified as a real research direction. The exact private Axiom training stack is not public.

### 2. Construction Side: Example, Counterexample, Pattern Boost, Formal Conjecture

Core idea: discovery is not only proof search. A system needs a construction loop:

1. Generate objects or examples with Python/Rust/search.
2. Search for patterns or invariants.
3. Generate counterexamples to kill weak conjectures.
4. Translate surviving patterns into formal statements.
5. Prove or refute them in Lean/Isabelle/Coq.

Useful sources:

- PatternBoost / Axplorer for transformer-guided construction search over mathematical objects.
- Int2Int for transformer-based math object prediction over integer-encoded structures.
- Global Lyapunov functions with symbolic transformers as a concrete construction + symbolic verification case.
- FunSearch for program-guided mathematical object discovery.
- AlphaGeometry for auxiliary construction in geometry.
- Construction-Verification benchmark for construction-first applied math in Lean.
- Learning to Disprove for counterexample generation.
- LeanConjecturer and STP for formal conjecture generation.
- Fel's Conjecture / Chen-Gendron / Anderson-style Axiom-related papers for research-level conjecture resolution.

Status: verified. PatternBoost and Axplorer now have public paper/code links in `paper_links.*`. The exact private Axiom training stack is still not public.

### 3. Lean + Rust/Python Spec Stack

Core idea: split high-throughput search from final verification.

Architecture sketch:

```text
Rust/Python object generator
  -> candidate objects / counterexamples / empirical patterns
  -> LLM formalizer
  -> Lean definitions + theorem statements
  -> Lean prover / search / tactic generator
  -> checked proof or rejected conjecture
```

Rust/Python is for large search spaces. Lean is for `Prop`, definitions, theorem statements, and proof checking.

Useful sources:

- FunSearch.
- Construction-Verification benchmark.
- DeepSeek-Prover / AlphaProof for verifier feedback.
- RustBelt as a useful reference for Rust + formal logic foundations.

Status: verified as an architecture pattern. Exact production code differs by system.

### 4. Curry-Howard / Proofs as Programs

Core idea: propositions as types; proofs as programs; proof checking as type checking.

Why it matters for AI-for-math:

- A theorem statement is a type.
- A proof is a term inhabiting that type.
- Searching for a proof becomes searching for a well-typed program.
- Lean/Coq-style verification becomes compiler-like checking.

Useful sources:

- Proofs and Types.
- Lean theorem prover system paper.
- Lean4Lean for the external Lean 4 typechecker written in Lean.
- Lean Language Reference: elaboration, compilation, and trusted kernel overview.
- CompCert as a mature proofs-as-programs / verified compiler application.

Status: foundational and verified. Lean also supports classical axioms in mathlib, so the simple constructive Curry-Howard story needs nuance.

### 5. Forward / Backward Search and Deduction

Core idea: proof search can move from assumptions forward or from the goal backward. Real systems mix both.

System patterns:

- Backward proof search: decompose a Lean goal into subgoals.
- Forward exploration: generate useful lemmas, examples, auxiliary constructions.
- Value / progress model: rank which branch to expand.
- Verifier feedback: stop failed tactic branches early.

Useful sources:

- HyperTree Proof Search.
- LeanDojo / ReProver.
- DeepSeek-Prover-V1.5 and V2.
- Process-Verified RL.
- AlphaProof Nature paper.
- AgentV-RL for verifier-style forward/backward checking in reward modeling.

Status: verified as a search pattern. Some Gemini wording, such as an exact “AlphaProof Master Plan” public paper, was not verified.

### 6. Lemma Hierarchy, Skill Base, Long-Term Memory

Core idea: strong provers need a growing library of reusable verified chunks.

Mechanisms:

- Propose subgoal lemmas.
- Prove them independently.
- Store successful lemmas as reusable skills.
- Generalize overly specific lemmas.
- Retrieve them later by goal state or semantic purpose.

Useful sources:

- LEGO-Prover for growing libraries / evolving skill base.
- LeanAgent for lifelong learning in formal theorem proving.
- STP for self-play conjecture/prove loops.
- LeanConjecturer for conjecture generation in Lean.
- AI Co-Mathematician for agentic theory-building workflow.

Status: verified. “Evolver” details vary by paper/system; do not assume Axiom uses exactly LEGO-Prover internals.

### 7. Mathlib RAG, Semantic Search, Relative Utility

Core idea: lemma search should not only be name retrieval. It should rank by proof-state utility and mathematical purpose.

Retrieval layers:

- Syntactic search: theorem name, constants, subexpressions.
- Semantic search: natural-language intent to Lean theorem.
- Premise selection: historical utility for closing similar goals.
- Dependency graph: theorem-def-lemma graph and hidden infrastructure.
- Reranking: combine semantic similarity, type compatibility, current proof state, dependency distance, and past utility.

Useful sources:

- LeanDojo / ReProver.
- Loogle.
- Moogle.
- LeanSearch / Semantic Search Engine for Mathlib4.
- Lean Finder.
- The Network Structure of Mathlib.
- MathlibGraph / ProofGraph.
- Semantic Search over 9 Million Mathematical Theorems.
- LemmaNet for purpose-driven lemma adaptation in program verification.

Status: verified. “Relative utility” is our synthesis of premise-selection / proof-state utility ideas, not always a named term in the papers.

### 8. Isomorphism-Aware Retrieval, Transfer, Typeclass Abstraction

Core idea: if theory A and theory B are equivalent or share an abstract interface, theorem search should retrieve lemmas across that bridge.

Engineering route:

1. Extract type signatures and declarations from mathlib.
2. Extract known equivalences/isomorphisms, e.g. `Equiv`, equivalences of categories, additive/multiplicative wrappers.
3. Build a graph of theory objects and structure-preserving maps.
4. In retrieval, rerank theorem `Q` higher if it can be transported to target `P` along a known bridge.
5. Try `transfer`, rewriting, equivalence transport, or abstracting a lemma to a typeclass.

Useful sources:

- Lean `transfer` tactic documentation.
- HoTT / univalence sources for the theory intuition.
- LeanDojo and Mathlib dependency graphs for extraction.
- Lean Finder / LeanSearch for intent-layer retrieval.

Status: partly ready. Manual `transfer` and typeclass abstraction are real. Fully automatic cross-theory lemma transport and reranking is still a research build, not a polished public system.

### 9. Knowledge Graph / Citation Graph for Formal Math

Core idea: in Lean, “citation” is not just bibliography. It is theorem dependency: proof A uses lemma B, definition C, typeclass D.

Graph nodes:

- definitions
- theorems / lemmas
- tactics / proof states
- imports / modules
- typeclass instances
- equivalence bridges

Graph edges:

- proof dependency
- import dependency
- typeclass dependency
- semantic embedding neighbor
- equivalence/transport edge

Useful sources:

- LeanDojo dependency extraction.
- The Network Structure of Mathlib.
- MathlibGraph.
- ProofGraph.
- Axiom Putnam dependency graph page.

Status: verified. `QED-Bridge` as named by Gemini was not verified.

### 10. Dynamic Pruning, Reflection, Early Stop

Core idea: proof search explodes unless a critic decides when a branch is not worth expanding.

Signals:

- Lean error / tactic failure.
- no proof progress.
- proof-state novelty too low.
- branch value score too low.
- similar branch already failed.
- generated lemma too weak or too specific.

Useful sources:

- Process-Verified RL.
- LeanProgress.
- DeepSeek-Prover-V1.5 MCTS.
- HyperTree Proof Search.
- Reflexion is useful as a general agent idea, but not included as a primary theorem-proving paper.

Status: verifier-guided pruning is verified. Some Gemini-named papers like `Novelty-based Tree-of-Thought Search` and `From Roots to Rewards` were not verified under those exact names.

### 11. Synthetic Data and Lean Data Scarcity

Core idea: formal proof data is scarce, so systems manufacture training tasks.

Routes:

- autoformalize informal math into formal statements.
- mine subgoals from existing proofs.
- self-play: conjecture, prove, add successful examples.
- generate counterexamples for bad conjectures.
- mutate/formalize problems by symmetry or difficulty.
- use verifier feedback as deterministic reward.

Useful sources:

- PACT.
- LeanDojo.
- DeepSeek-Prover.
- STP.
- LeanConjecturer.
- EvolProver.
- Seed-Prover.
- AI Co-Mathematician.

Status: verified. A standalone Axiom synthetic-data tech report was not found.

### 12. Benchmarks

Covered benchmark families:

- Putnam 2025 / Axiom public Lean repo.
- IMO / AlphaProof / AlphaGeometry.
- miniF2F.
- FIMO.
- ProofNet.
- FormalMATH.
- Construction-Verification.
- CombiBench.
- MathNet.
- MathVerse.
- MathVista.
- PolyMATH.

Status: verified. `Mini-CTX v2` as a math benchmark was not verified under that exact name.

### 13. HoTT, Logic-as-Geometry, Diagrammatic Reasoning

Core idea: symbolic text is one projection of mathematical structure; graphs, spaces, paths, and diagrams can be more natural for some reasoning.

Relevant theory:

- HoTT: types as spaces, equality as paths, univalence as equivalence-to-equality.
- Category theory: objects and morphisms, functors, natural transformations.
- String diagrams: graphical syntax for monoidal/categorical reasoning.
- Graph rewriting: proof as structure-preserving graph transformation.

Useful sources:

- HoTT Book.
- Homotopy Type Theory in Lean.
- Higher Groups in HoTT.
- Formalization of higher inductive types / synthetic homotopy theory.
- HoTTLean / certifying proof assistant for synthetic mathematics in Lean.
- Quantomatic.
- String diagram rewrite theory.

Status: theory and tools are real. Directly replacing Lean's symbolic kernel with visual reasoning is not current practice; the practical route is graph/diagram reasoning plus a verified symbolic or proof-producing backend.

### 14. Multimodal / Visual / Spatial Mathematical Reasoning

Core idea: many math problems require diagram, spatial, or structural intuition; a future system should ground visual structure into formal constraints.

Routes:

- Geometry construction: auxiliary point/line/circle prediction.
- Diagram grounding: parse visual entities into constraints.
- Multimodal autoformalization: image/diagram/physics setup to formal spec.
- Math-aware retrieval: detect when two problems are structurally the same even if text/diagram differs.

Useful sources:

- AlphaGeometry.
- MMFormalizer.
- MathNet.
- MathVerse.
- MathVista.
- PolyMATH.
- Autoformalizing Euclidean Geometry.

Status: verified and active. The broader “real-world RL with Lean compile reward from visual structure” is a plausible architecture, not a solved system.

### 15. Verifiable Visual-Structure RL / Real-World Compile Reward

Core idea: use a formal checker as an RL reward for real-world or multimodal agents.

Possible stack:

```text
visual / spatial signal
  -> structural perception graph
  -> constraint extraction
  -> formal spec in Lean or another proof-producing logic
  -> action/proof candidate
  -> verifier feedback as reward
```

Research ingredients already exist:

- verifier-guided RL for Lean.
- visual math benchmarks.
- multimodal autoformalization.
- graph rewriting / diagrammatic proof.
- formal verification of software/hardware.

### 16. Lean Kernel / Every Proof Step Verifiable

Core idea: the LLM, tactic search, RAG, Rust/Python search, and PatternBoost are all untrusted generators. The trusted object is the final proof term checked by the Lean kernel.

Operational stack:

```text
informal statement / search idea
  -> Lean declaration + proof script
  -> elaborator expands tactics into proof terms
  -> kernel typechecks proof term
  -> accepted theorem or concrete error state
```

Important distinction:

- `def`, `structure`, and `inductive` do not need an informal original. They need to be well-typed, universe-safe, terminating when recursive, and strictly positive when inductive.
- If the goal is to formalize existing mathematics, humans still need to audit whether the Lean definition matches the intended informal concept.
- If the goal is to invent a new formal theory, Lean only checks internal logical coherence, not whether humans find the definition meaningful.

Useful sources:

- The Lean Theorem Prover system description.
- Lean4Lean.
- Lean Language Reference.
- The Lean mathematical library.

Status: verified. This is the right mental model for “all proof steps verifiable.”

### 17. SAT / Hardware Verification Bridge

Core idea: hardware formal verification is the mature industrial cousin of theorem proving. SAT/SMT/model checking handles bounded or finite-state properties; proof assistants handle parameterized, high-level, and compositional correctness.

Key concepts:

- SAT solver: searches Boolean assignments for CNF formulas.
- CDCL: modern SAT algorithm with conflict analysis, learned clauses, restarts, and watched literals.
- Certificate checking: do not fully trust the SAT solver; verify UNSAT/SAT proof certificates such as DRAT/GRAT with a smaller checker.
- RTL: register-transfer-level implementation of a circuit.
- ISA: instruction-set architecture, the contract between software and hardware.
- SVA/LTL: temporal assertions over clocked behavior, e.g. request must eventually receive acknowledgement.

Useful sources:

- A Verified SAT Solver Framework with Learn, Forget, Restart, and Incrementality.
- The DRAT format and DRAT-trim checker.
- GRAT verified SAT solver certification toolchain.
- Kami for Coq-based modular hardware verification.
- RISC-V Formal references.

Status: verified. This is adjacent to AI-for-math because it gives a mature blueprint for verifier-backed agents: untrusted search/generation, small trusted checker, proof/certificate artifacts.

Missing pieces:

- robust perception-to-formal-spec compiler.
- proof-producing visual graph transformations.
- scalable real-time verifier feedback.
- benchmarks that require real-world causal/spatial actions plus formal correctness.

Status: speculative system architecture, but grounded in verified components.

## Practical Build Plan for Our Agent Skill

Near-term extract layer:

1. Keep Chrome/session collection as source-of-truth registry.
2. Maintain manual verified bibliographies from Gemini/YouTube/interview conversations.
3. Store idea nodes separately from link nodes.
4. Map each idea to verified links and status.
5. Add `needs_verification` for hallucinated or private/internal claims.

Mathlib search skill route:

1. Extract mathlib declarations, types, imports, dependencies.
2. Index theorem names, statements, constants, type signatures, and docstrings.
3. Add semantic embeddings for informal query intent.
4. Add graph search over dependencies and typeclass infrastructure.
5. Add equivalence/transport labels from `Equiv`, isomorphisms, wrappers, and categories.
6. Rerank by proof-state utility and transport distance.
7. Try Lean `exact?`, `apply?`, `rw?`, `simp?`, `aesop?`, `loogle`, `transfer`, and generated abstraction lemmas.

This is the actionable version of the “isomorphism-aware RAG + automated lemma transport + abstract class refinement” idea.
