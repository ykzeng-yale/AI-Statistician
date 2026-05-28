# Coverage Audit for Pasted Gemini Conversation

Generated: 2026-05-12

This audit checks whether the pasted Gemini conversation is covered by the local AI-for-math collection. Status meanings:

- **Covered:** verified source(s) are in `paper_links.*`.
- **Covered as idea:** no single paper title, but the concept is represented in `full_ai_for_math_collection.md` and mapped to verified sources.
- **Needs verification:** exact Gemini name was not reliably found or appears to be an internal/private/hallucinated title.

## Covered Topics

| Gemini topic / claim | Status | Local coverage |
|---|---:|---|
| AI mathematical discovery / conjecturing / generation + verification | Covered | FunSearch, AlphaProof, AlphaGeometry, AI Co-Mathematician, Axiom Putnam 2025, STP, LeanConjecturer |
| Axiom / AlphaProof / Lean verifier reward | Covered | Axiom Putnam repo/report, AlphaProof Nature paper, DeepMind IMO blog, DeepSeek-Prover papers |
| FunSearch evolutionary program search | Covered | Nature FunSearch paper |
| Construction: examples, counterexamples, pattern boost, formal conjecture | Covered as idea | FunSearch, AlphaGeometry, Construction-Verification, Learning to Disprove, LeanConjecturer |
| Lean + Rust/Python split for search and verification | Covered as idea | Construction-Verification, FunSearch, RustBelt, DeepSeek-Prover |
| Curry-Howard correspondence, dependent types, proofs-as-programs | Covered as idea | Proofs and Types, Lean theorem prover paper, CompCert |
| HoTT / univalence / equality as path | Covered | HoTT Book, Homotopy Type Theory in Lean, HoTTLean, higher inductive type sources |
| Lean HoTT applications | Covered | Homotopy Type Theory in Lean, Higher Groups in HoTT, higher inductive type dissertation, HoTTLean |
| Transfer / lemma transport / typeclass abstraction | Covered as idea | Lean transfer tactic docs, HoTT sources, Mathlib/Lean sources |
| Forward/backward theorem proving, proof search | Covered | HyperTree Proof Search, LeanDojo, DeepSeek-Prover, Process-Verified RL, AlphaProof |
| Lemma hierarchy / growing skill base | Covered | LEGO-Prover, LeanAgent, STP, AI Co-Mathematician |
| Lean library reconstruction / RAG / premise selection | Covered | LeanDojo/ReProver, LeanSearch, Lean Finder, Moogle, Loogle, MathlibGraph |
| Pattern matching for lemma search | Covered | Loogle, LeanSearch, Lean Finder |
| Relative utility / purpose-driven retrieval | Covered as idea | ReProver/LeanDojo, Lean Finder, LemmaNet |
| Mathlib dependency/citation knowledge graph | Covered | The Network Structure of Mathlib, MathlibGraph, ProofGraph, Axiom Putnam dependency graph |
| Agent self-reflection / early stop / proof tree pruning | Covered | Process-Verified RL, LeanProgress, DeepSeek-Prover-V1.5, HyperTree Proof Search |
| Data scarcity for Lean | Covered | PACT, LeanDojo, STP, DeepSeek-Prover, LeanConjecturer, Seed-Prover, EvolProver |
| Axiom benchmarks mentioned: Putnam, IMO, miniF2F, code verification, open research conjectures | Mostly covered | Putnam 2025, AlphaProof/IMO, miniF2F, Fel's Conjecture, Parity of k-differentials, Anderson open problem paper, CompCert/RustBelt for formal verification context |
| Combinatorics benchmark / CombiBench | Covered | CombiBench arXiv + GitHub |
| MathNet multimodal reasoning/retrieval | Covered | MathNet arXiv + project site |
| Visual/spatial/multimodal math reasoning | Covered | AlphaGeometry, MMFormalizer, MathNet, MathVerse, MathVista, PolyMATH |
| Graph + graph = graph / non-symbolic operators / diagrammatic proof | Covered as idea | Quantomatic, graph rewriting, string diagram rewrite theory, HoTT sources |
| Real-world RL with verified visual-structure compile reward | Covered as speculative architecture | Full collection idea map, grounded by Process-Verified RL + MMFormalizer + visual math benchmarks + graph rewriting |
| PatternBoost / Axplorer construction search | Covered | PatternBoost arXiv paper, AxiomMath/axplorer, original PatternBoost experiments repo |
| Int2Int / transformer math object prediction | Covered | Int2Int arXiv paper and FacebookResearch/Int2Int repo |
| François Charton / Alberto Alfarano neuro-symbolic object construction | Covered | Global Lyapunov functions paper + repo, Deep Learning for Symbolic Mathematics, Linear Algebra with Transformers |
| Lean kernel / how every proof step becomes verifiable | Covered | Lean system paper, Lean4Lean, Lean Language Reference |
| SAT solver construction and verified checking | Covered | Verified SAT Solver Framework, DRAT-trim, GRAT |
| Hardware verification basics: RTL, ISA, temporal logic | Covered as idea | Kami, RISC-V Formal references, SAT/DRAT/GRAT sources |

## Chrome Session Cross-check

The current `ykzeng2019@gmail.com` Chrome session files were scanned after the manual Gemini-derived bibliography.

Results:

- 73 paper/resource links seen in current Chrome session files across 6 session files.
- 156 cumulative links in the global registry.
- 120 links in the broader `ai-math-discovery-systems` collection.
- 22 AI-for-math links came from Chrome session files and were not in the manual verified list.
- 98 manual Gemini/follow-up links have been verified and stored in `manual-additions/ai_math_discovery_gemini_verified.json`.
- 2026-05-12 update: no new cumulative links were found compared with the previous run.

Important Chrome-discovered additions:

- DeepSeekMath-V2.
- Seed-Prover.
- Aristotle.
- Discover and Prove.
- EvolProver.
- PhysProver.
- Beyond Theorem Proving / Formal Problem-Solving.
- Autoformalize Mathematical Statements by Symbolic Equivalence and Semantic Consistency.
- Mining Math Conjectures from LLMs.
- AlphaProof Paper blog.
- LeanAgent OpenReview page.
- Process-Verified RL OpenReview/NeurIPS pages.
- Mathlib4 GitHub.
- ProofNet GitHub.

## Needs Verification / Corrected

These Gemini items were not added as verified primary sources:

- `Mini-CTX v2` / `Mini-Context v2`: no math-specific benchmark found under this exact name.
- `LeanDojo-v2` as a standalone paper: LeanDojo and tooling are verified; exact v2 paper not found.
- `QED-Bridge: Knowledge Graph Ingestion`: no reliable paper/project page found.
- `Axiom synthetic data tech report`: no standalone public report found.
- `AxiomMath/fel-polynomial`: repo not verified; Fel's Conjecture arXiv paper was added.
- `AlphaProof Master Plan & Blog 2025`: exact title not found; Nature paper and DeepMind blog added.
- `MMA: Multi-Modal Autoformalization`: corrected to `Multilingual Mathematical Autoformalization`; multimodal autoformalization is covered by `MMFormalizer`.
- `Machine-Checked Categorical Diagrammatic Reasoning (2024)`: exact title not verified; represented by Quantomatic and string diagram rewrite sources.
- `Novelty-based Tree-of-Thought Search for LLM Reasoning`: exact paper not verified.
- `From Roots to Rewards: Dynamic Tree Reasoning with RL`: exact paper not verified.
- `Artificial Intelligence and the Structure of Mathematics (2026)`: exact paper not verified.
- `The Einstein AI model` / Thomas Wolf blog: not reliably found from a primary source search; kept out of verified bibliography for now.

## Remaining Gaps to Search Later

- Public Axiom technical interviews/transcripts with exact benchmark names.
- Public Axiom synthetic-data methodology beyond Putnam/research-conjecture artifacts.
- More direct papers on automatic `Equiv` extraction and theorem transport in Lean 4.
- More direct systems for proof-producing visual graph transformations.
- Benchmarks that combine real-world action, perception, and formal verification reward.
