# AI for Math + Formal Verification Structured Outline

Updated: 2026-05-16 13:03

Core point: AI-for-math is a stack, not a flat bibliography. 这版按奠基关系组织。

## Dependency Spine

0. **Orientation / AI Mathematician Systems** — 先看全局系统图
   - Thesis: What is the end-to-end system trying to do? 不是单篇 prover，而是 generate -> verify -> learn -> retrieve -> discover 的闭环。
   - Depends on: None. This frames the target architecture.
   - Enables: Helps decide which technical route to study: Lean prover, construction search, RAG, multimodal, or verification.
1. **Logic / Kernel / Verification Substrate** — 最底层：为什么每一步可验证
   - Thesis: The trusted base: type theory, Lean kernel, mathlib design, proof certificates, SAT certificates, and hardware/software formal verification. 这里决定什么叫 checked proof。
   - Depends on: Minimal logic foundations: type theory, SAT/SMT, temporal logic, or proof certificates.
   - Enables: All later AI systems can use a hard verifier instead of trusting model text.
2. **Formal Data / Autoformalization / Benchmarks** — 把自然语言题目变成可验证任务
   - Thesis: Build formal statements, datasets, and benchmark tasks. This is the bridge from arXiv/text/competition problems into Lean/Isabelle/Coq objects.
   - Depends on: Layer 1 verifier and formal library conventions.
   - Enables: Training and evaluating provers; producing large formal task corpora despite Lean data scarcity.
3. **Mathlib Retrieval / Knowledge Graph / Long-Term Memory** — 让 agent 找到对的 lemma，而不是只靠名字搜索
   - Thesis: Index declarations by type, dependency, semantic intent, proof-state utility, and graph position. This is where RAG becomes proof-aware.
   - Depends on: Layer 1 libraries and Layer 2 formal data extraction.
   - Enables: Layer 4 provers can retrieve useful lemmas; Layer 5 discovery systems can reuse and transport skills.
4. **Formal Prover Engines / RL / Proof Search** — 证明器主体：搜索、RL、self-play、早停、skill base
   - Thesis: Models generate tactics/subgoals/proof sketches; Lean or Isabelle checks them; RL/search updates policy, value, and skill memory.
   - Depends on: Layer 1 verifier plus Layer 3 retrieval/memory. Strong systems also use Layer 2 datasets.
   - Enables: Layer 5 conjecture/discovery systems can validate generated claims and recycle proof skills.
5. **Discovery / Construction / Conjecturing** — 数学发现本体：构造例子、反例、pattern、formal conjecture
   - Thesis: This layer generates new mathematical objects or statements, then uses lower layers to verify/refute them. It is construction-first, not proof-only.
   - Depends on: Layer 4 proving to validate claims; Layer 3 retrieval to reuse lemmas; often external Python/Rust/program search.
   - Enables: New conjectures, counterexamples, constructions, and synthetic verified training data.
6. **Multimodal / Spatial / Diagrammatic Math Reasoning** — 视觉和空间结构：不止符号序列
   - Thesis: Geometry diagrams, visual math retrieval, physical/math diagrams, and graph/string-diagram proof systems. The frontier is grounding visual structure into verifiable logic.
   - Depends on: Layer 1 verification and Layer 2 formalization; often Layer 5 construction heuristics.
   - Enables: Visual/spatial heuristic construction, multimodal autoformalization, diagrammatic proof search.
7. **Code / Project Pages / Datasets** — 可直接上手的实现入口
   - Thesis: Repositories, project pages, and datasets that are useful when you move from reading to building.
   - Depends on: Specific target depends on which layer you are implementing.
   - Enables: Local experiments: LeanDojo/ReProver, PatternBoost/Axplorer, Int2Int, mathlib graph, AlphaGeometry, miniF2F/ProofNet.

## System Composition

- Lean RAG agent: Layer 1 -> Layer 3 -> Layer 4.
- Conjecturer: Layer 5 -> Layer 2 -> Layer 4 -> back into Layer 3 memory.
- Long-term skill base: Layer 4 proves reusable blocks -> Layer 3 indexes utility -> Layer 5 reuses them.
- Multimodal verifier: Layer 6 extracts structure -> Layer 2 formal specs -> Layer 1 kernel verification.

## Layer 0 — Orientation / AI Mathematician Systems

**先看全局系统图**

Thesis: What is the end-to-end system trying to do? 不是单篇 prover，而是 generate -> verify -> learn -> retrieve -> discover 的闭环。

Depends on: None. This frames the target architecture.

Enables: Helps decide which technical route to study: Lean prover, construction search, RAG, multimodal, or verification.

### Core papers / 必读主线
- **AlphaEvolve: A coding agent for scientific and algorithmic discovery** [paper] — Coding-agent route for large-scale scientific/algorithmic discovery.  
  https://arxiv.org/abs/2506.13131
- **Mathematical discoveries from program search with large language models** [paper] — Generation + evaluator loop; key model for construction discovery.  
  https://www.nature.com/articles/s41586-023-06924-6
- **Axiom: From Seeing Why to Checking Everything** [blog/report] — Supporting reference for this layer.  
  https://axiommath.ai/territory/from-seeing-why-to-checking-everything
- **AxiomProver at Putnam 2025** [code] — Supporting reference for this layer.  
  https://github.com/AxiomMath/putnam2025

### Supporting sources / 补充材料
- **A Survey on Deep Learning for Theorem Proving** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2404.09939
- **AI Co-Mathematician: Accelerating Mathematicians with Agentic AI** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2605.06651
- **AI Mathematician as a Partner in Advancing Mathematical Discovery - A Case Study in Homogenization Theory** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2510.26380
- **AI Mathematician: Towards Fully Automated Frontier Mathematical Research** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2505.22451
- **Mathematical exploration and discovery at scale** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2511.02864
- **AI achieves silver-medal standard solving International Mathematical Olympiad problems** [blog/report] — Supporting reference for this layer.  
  https://deepmind.google/blog/ai-solves-imo-problems-at-silver-medal-level/
- **AlphaProof Paper** [blog/report] — Formal Lean/RL route for olympiad-level proof.  
  https://www.julian.ac/blog/2025/11/13/alphaproof-paper/
- **AxiomMath · GitHub** [code] — Supporting reference for this layer.  
  https://github.com/AxiomMath
- **Axplorer GitHub repository** [code] — Supporting reference for this layer.  
  https://github.com/AxiomMath/axplorer
- **AxiomProver Putnam 2025 dependency graphs** [resource] — Supporting reference for this layer.  
  https://axiommath.github.io/Putnam2025/

## Layer 1 — Logic / Kernel / Verification Substrate

**最底层：为什么每一步可验证**

Thesis: The trusted base: type theory, Lean kernel, mathlib design, proof certificates, SAT certificates, and hardware/software formal verification. 这里决定什么叫 checked proof。

Depends on: Minimal logic foundations: type theory, SAT/SMT, temporal logic, or proof certificates.

Enables: All later AI systems can use a hard verifier instead of trusting model text.

### Core papers / 必读主线
- **A Verified SAT Solver Framework with Learn, Forget, Restart, and Incrementality** [paper] — Proof-certificate style verification for SAT; useful analogy for proof checking.  
  https://link.springer.com/article/10.1007/s10817-018-9455-7
- **Lean4Lean: Towards a Verified Typechecker for Lean, in Lean** [paper] — Verified typechecker direction: check Lean with Lean.  
  https://arxiv.org/abs/2403.14064
- **RustBelt: Securing the Foundations of the Rust Programming Language** [paper] — Formal verification for programming-language memory safety.  
  https://doi.org/10.1145/3158154
- **The Lean mathematical library** [paper] — Canonical large formal math library; substrate for RAG and AI training.  
  https://arxiv.org/abs/1910.09336
- **The Lean Theorem Prover (system description)** [paper] — Core system paper for Lean architecture and kernel idea.  
  https://lean-lang.org/papers/lean.pdf
- **GRAT: Efficient Formally Verified SAT Solver Certification Toolchain** [resource] — Proof-certificate style verification for SAT; useful analogy for proof checking.  
  https://www21.in.tum.de/~lammich/grat/
- **Kami: A Platform for High-Level Parametric Hardware Specification and its Modular Verification** [resource] — Hardware specification and modular verification case study.  
  https://adam.chlipala.net/papers/KamiICFP17/

### Supporting sources / 补充材料
- **A Certifying Proof Assistant for Synthetic Mathematics in Lean** [paper] — Supporting reference for this layer.  
  https://research.chalmers.se/publication/551200/file/551200_Fulltext.pdf
- **Constructing the Propositional Truncation using Non-recursive HITs** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/1512.02274
- **Higher Groups in Homotopy Type Theory** [paper] — Theory for equality-as-path and equivalence-aware transfer.  
  https://arxiv.org/abs/1802.04315
- **Homotopy Type Theory in Lean** [paper] — Theory for equality-as-path and equivalence-aware transfer.  
  https://arxiv.org/abs/1704.06781
- **Homotopy Type Theory: Univalent Foundations of Mathematics** [paper] — Theory for equality-as-path and equivalence-aware transfer.  
  https://arxiv.org/abs/1308.0729
- **HoTTLean: Formalizing the Meta-Theory of HoTT in Lean** [paper] — Theory for equality-as-path and equivalence-aware transfer.  
  https://msp.cis.strath.ac.uk/types2025/abstracts/TYPES2025_paper25.pdf
- **On the Formalization of Higher Inductive Types and Synthetic Homotopy Theory** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/1808.10690
- **Pictures of Processes: Automated Graph Rewriting for Monoidal Categories and Applications to Quantum Computing** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/1203.0202
- **String Diagram Rewrite Theory I: Rewriting with Frobenius Structure** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2012.01847
- **String Diagram Rewrite Theory II: Rewriting with Symmetric Monoidal Structure** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2104.14686
- **The DRAT format and DRAT-trim checker** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/1610.06229
- **Lean transfer tactic documentation** [tool/docs] — Lean tactic route for moving lemmas across related structures.  
  https://leanprover-community.github.io/mathlib_docs/tactic/transfer.html
- **RISC-V Formal documentation: references and related work** [tool/docs] — Supporting reference for this layer.  
  https://yosyshq.readthedocs.io/projects/riscv-formal/en/latest/references.html
- **Formal Verification of a Realistic Compiler** [resource] — Supporting reference for this layer.  
  https://cacm.acm.org/research/formal-verification-of-a-realistic-compiler/
- **Proofs and Types** [resource] — Supporting reference for this layer.  
  https://www.seas.upenn.edu/~sweirich/types/archive/1989/msg00053.html
- **The Lean Language Reference: Elaboration and Compilation** [resource] — Supporting reference for this layer.  
  https://lean-lang.org/doc/reference/latest/Elaboration-and-Compilation/

## Layer 2 — Formal Data / Autoformalization / Benchmarks

**把自然语言题目变成可验证任务**

Thesis: Build formal statements, datasets, and benchmark tasks. This is the bridge from arXiv/text/competition problems into Lean/Isabelle/Coq objects.

Depends on: Layer 1 verifier and formal library conventions.

Enables: Training and evaluating provers; producing large formal task corpora despite Lean data scarcity.

### Core papers / 必读主线
- None assigned.

### Supporting sources / 补充材料
- **Autoformalization with Large Language Models** [paper] — Translate informal math into formal statements/proofs.  
  https://arxiv.org/abs/2205.12615
- **Autoformalizing Euclidean Geometry** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2405.17216
- **Draft, Sketch, and Prove: Guiding Formal Theorem Provers with Informal Proofs** [paper] — Translate informal proof sketches into formal proof search guidance.  
  https://arxiv.org/abs/2210.12283
- **Multilingual Mathematical Autoformalization** [paper] — Translate informal math into formal statements/proofs.  
  https://arxiv.org/abs/2311.03755
- **NeurIPS Poster Autoformalize Mathematical Statements by Symbolic Equivalence and Semantic Consistency** [paper] — Supporting reference for this layer.  
  https://neurips.cc/virtual/2024/poster/96359
- **Peano: Learning Formal Mathematical Reasoning** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2211.15864
- **[2505.04528] Beyond Theorem Proving: Formulation, Framework and Benchmark for Formal Problem-Solving** [benchmark/data] — Supporting reference for this layer.  
  https://arxiv.org/abs/2505.04528
- **Construction-Verification: A Benchmark for Applied Mathematics in Lean 4** [benchmark/data] — Supporting reference for this layer.  
  https://arxiv.org/abs/2602.01291
- **FormalMATH: Benchmarking Formal Mathematical Reasoning of Large Language Models** [benchmark/data] — Benchmark/dataset for evaluating formal math systems.  
  https://arxiv.org/abs/2505.02735
- **MiniF2F: a cross-system benchmark for formal Olympiad-level mathematics** [benchmark/data] — Benchmark/dataset for evaluating formal math systems.  
  https://arxiv.org/abs/2109.00110
- **ProofNet: Autoformalizing and Formally Proving Undergraduate-Level Mathematics** [benchmark/data] — Benchmark/dataset for evaluating formal math systems.  
  https://arxiv.org/abs/2302.12433
- **FIMO: Formal IMO-level mathematics dataset** [code] — Benchmark/dataset for evaluating formal math systems.  
  https://github.com/liuchengwucn/FIMO
- **miniF2F GitHub repository** [code] — Benchmark/dataset for evaluating formal math systems.  
  https://github.com/openai/miniF2F
- **zhangir-azerbayev/ProofNet: Benchmark for undergraduate-level formal mathematics · GitHub** [code] — Benchmark/dataset for evaluating formal math systems.  
  https://github.com/zhangir-azerbayev/ProofNet

## Layer 3 — Mathlib Retrieval / Knowledge Graph / Long-Term Memory

**让 agent 找到对的 lemma，而不是只靠名字搜索**

Thesis: Index declarations by type, dependency, semantic intent, proof-state utility, and graph position. This is where RAG becomes proof-aware.

Depends on: Layer 1 libraries and Layer 2 formal data extraction.

Enables: Layer 4 provers can retrieve useful lemmas; Layer 5 discovery systems can reuse and transport skills.

### Core papers / 必读主线
- **A Semantic Search Engine for Mathlib4** [paper] — Practical semantic/type/signature search over mathlib.  
  https://arxiv.org/abs/2403.13310
- **Lean Finder: Semantic Search for Mathlib That Understands User Intents** [paper] — Natural-language intent to mathlib lemma search.  
  https://arxiv.org/abs/2510.15940
- **LeanDojo: Theorem Proving with Retrieval-Augmented Language Models** [paper] — Lean proof-state extraction and retrieval/prover infrastructure.  
  https://arxiv.org/abs/2306.15626
- **The Network Structure of Mathlib** [paper] — Knowledge graph / dependency graph view of formal libraries.  
  https://arxiv.org/abs/2604.24797
- **ReProver: Retrieval-Augmented Theorem Provers for Lean** [code] — Premise retrieval as part of theorem proving; utility-style lemma retrieval.  
  https://github.com/lean-dojo/ReProver
- **Loogle: Lean and Mathlib search by constants, names, and subexpressions** [tool/docs] — Practical type/signature/subexpression search over mathlib.  
  https://loogle.lean-lang.org/
- **Moogle: Semantic search over mathlib4** [tool/docs] — Practical semantic search over mathlib.  
  https://www.moogle.ai/
- **MathlibGraph: The Multinetwork of Mathlib** [resource] — Knowledge graph / dependency graph view of formal libraries.  
  https://huggingface.co/datasets/MathNetwork/MathlibGraph

### Supporting sources / 补充材料
- **Semantic Search over 9 Million Mathematical Theorems** [paper] — Practical semantic/type/signature search over mathlib.  
  https://arxiv.org/abs/2602.05216
- **leanprover-community/mathlib49** [code] — Supporting reference for this layer.  
  https://github.com/leanprover-community/mathlib49
- **leanprover-community/mathlib4: The math library of Lean 4 · GitHub** [code] — Supporting reference for this layer.  
  https://github.com/leanprover-community/mathlib4
- **ProofGraph: Network science and spectral graph theory applied to formalized mathematics** [resource] — Network-science view of formalized mathematics.  
  https://proofgraph.org/

## Layer 4 — Formal Prover Engines / RL / Proof Search

**证明器主体：搜索、RL、self-play、早停、skill base**

Thesis: Models generate tactics/subgoals/proof sketches; Lean or Isabelle checks them; RL/search updates policy, value, and skill memory.

Depends on: Layer 1 verifier plus Layer 3 retrieval/memory. Strong systems also use Layer 2 datasets.

Enables: Layer 5 conjecture/discovery systems can validate generated claims and recycle proof skills.

### Core papers / 必读主线
- **[2507.23726] Seed-Prover: Deep and Broad Reasoning for Automated Theorem Proving** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2507.23726
- **Aesop: White-Box Best-First Proof Search for Lean** [paper] — White-box best-first proof search in Lean.  
  https://zenodo.org/records/7430233
- **DeepSeek-Prover-V1.5: Harnessing Proof Assistant Feedback for Reinforcement Learning and Monte-Carlo Tree Search** [paper] — Verifier feedback + RL/MCTS/subgoal decomposition in Lean.  
  https://arxiv.org/abs/2408.08152
- **DeepSeek-Prover-V2: Advancing Formal Mathematical Reasoning via Reinforcement Learning for Subgoal Decomposition** [paper] — Verifier feedback + RL/MCTS/subgoal decomposition in Lean.  
  https://arxiv.org/abs/2504.21801
- **HyperTree Proof Search for Neural Theorem Proving** [paper] — Search-tree structure for proof search with verifier feedback.  
  https://arxiv.org/abs/2205.11491
- **LEGO-Prover: Neural Theorem Proving with Growing Libraries** [paper] — Growing skill library: modular lemma blocks and reuse.  
  https://arxiv.org/abs/2310.00656
- **NeurIPS Process-Verified Reinforcement Learning for Theorem Proving via Lean** [paper] — Process-level reward/verification rather than only final pass/fail.  
  https://neurips.cc/virtual/2025/131058
- **Olympiad-level formal mathematical reasoning with reinforcement learning** [paper] — Formal Lean/RL route for olympiad-level proof.  
  https://www.nature.com/articles/s41586-025-09833-y
- **Process-Verified Reinforcement Learning for Theorem Proving via Lean** [paper] — Process-level reward/verification rather than only final pass/fail.  
  https://iclr.cc/virtual/2026/poster/10009728
- **Process-Verified Reinforcement Learning for Theorem Proving via Lean** [paper] — Process-level reward/verification rather than only final pass/fail.  
  https://openreview.net/forum?id=sKvVHgmRP2
- **STP: Self-play LLM Theorem Provers with Iterative Conjecturing and Proving** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2502.00212
- **LEGO-Prover GitHub repository** [code] — Growing skill library: modular lemma blocks and reuse.  
  https://github.com/wiio12/LEGO-Prover

### Supporting sources / 补充材料
- **[2310.04353] An In-Context Learning Agent for Formal Theorem-Proving** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2310.04353
- **[2601.15737] PhysProver: Advancing Automatic Theorem Proving for Physics** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2601.15737
- **[2604.01483] Type-Checked Compliance: Deterministic Guardrails for Agentic Financial Systems Using Lean 4 Theorem Proving** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2604.01483
- **AgentV-RL: Scaling Reward Modeling with Agentic Verifier** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2604.16004
- **Aristotle: IMO-level Automated Theorem Proving** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2510.01346
- **DeepSeekMath-V2: Towards Self-Verifiable Mathematical Reasoning** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2511.22570
- **DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2402.03300
- **Discover and Prove: An Open-source Agentic Framework for Hard Mode Automated Theorem Proving in Lean 4** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2604.15839
- **Generative Language Modeling for Automated Theorem Proving** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2009.03393
- **Goedel-Prover: A Frontier Model for Open-Source Automated Theorem Proving** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2502.07640
- **Leanabell-Prover-V2: Verifier-integrated Reasoning for Formal Theorem Proving via Reinforcement Learning** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2507.08649
- **LeanAgent: Lifelong Learning for Formal Theorem Proving** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2410.06209
- **LeanAgent: Lifelong Learning for Formal Theorem Proving** [paper] — Supporting reference for this layer.  
  https://openreview.net/forum?id=Uo4EHT4ZZ8
- **LeanProgress: Guiding Search for Neural Theorem Proving via Proof Progress Prediction** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2502.17925
- **Proof Artifact Co-training for Theorem Proving with Language Models** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2102.06203
- **Goedel-LM/Goedel-Prover-V2 · GitHub** [code] — Supporting reference for this layer.  
  https://github.com/Goedel-LM/Goedel-Prover-V2

## Layer 5 — Discovery / Construction / Conjecturing

**数学发现本体：构造例子、反例、pattern、formal conjecture**

Thesis: This layer generates new mathematical objects or statements, then uses lower layers to verify/refute them. It is construction-first, not proof-only.

Depends on: Layer 4 proving to validate claims; Layer 3 retrieval to reuse lemmas; often external Python/Rust/program search.

Enables: New conjectures, counterexamples, constructions, and synthetic verified training data.

### Core papers / 必读主线
- **Global Lyapunov functions: a long-standing open problem in mathematics, with symbolic transformers** [paper] — Neuro-symbolic construction with symbolic verification.  
  https://arxiv.org/abs/2410.08304
- **Int2Int: a framework for mathematics with transformers** [paper] — Transformer for integer-encoded math object prediction.  
  https://arxiv.org/abs/2502.17513
- **LeanConjecturer: Automatic Generation of Mathematical Conjectures for Theorem Proving** [paper] — Formal conjecture generation inside Lean-style environment.  
  https://arxiv.org/abs/2506.22005
- **Learning to Disprove: Formal Counterexample Generation with Large Language Models** [paper] — Counterexample generation as a discovery/proof pruning tool.  
  https://arxiv.org/abs/2603.19514
- **Lemma Discovery in Agentic Program Verification** [paper] — Purpose-driven lemma generation/adaptation for verification.  
  https://arxiv.org/abs/2603.22114
- **PatternBoost: Constructions in Mathematics with a Little Help from AI** [paper] — Transformer-guided search for mathematical constructions/counterexamples.  
  https://arxiv.org/abs/2411.00566
- **Global Lyapunov functions GitHub repository** [code] — Neuro-symbolic construction with symbolic verification.  
  https://github.com/facebookresearch/Lyapunov
- **Int2Int GitHub repository** [code] — Transformer for integer-encoded math object prediction.  
  https://github.com/FacebookResearch/Int2Int
- **Original PatternBoost experiments GitHub repository** [code] — Transformer-guided search for mathematical constructions/counterexamples.  
  https://github.com/zawagner22/transformers_math_experiments

### Supporting sources / 补充材料
- **[2510.00732] EvolProver: Advancing Automated Theorem Proving by Evolving Formalized Problems via Symmetry and Difficulty** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2510.00732
- **Automated Conjecture Resolution with Formal Verification** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2604.03789
- **Deep Learning for Symbolic Mathematics** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/1912.01412
- **Fel's Conjecture on Syzygies of Numerical Semigroups** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2602.03716
- **Linear Algebra with Transformers** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2112.01898
- **Mining Math Conjectures from LLMs: A Pruning Approach** [paper] — Supporting reference for this layer.  
  https://openreview.net/forum?id=aYlKvzY6ob
- **Parity of k-differentials in genus zero and one** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2602.03722
- **What is my math transformer doing? Three results on interpretability and generalization** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2211.00170
- **Google DeepMind formal-conjectures repository** [code] — Supporting reference for this layer.  
  https://github.com/google-deepmind/formal-conjectures

## Layer 6 — Multimodal / Spatial / Diagrammatic Math Reasoning

**视觉和空间结构：不止符号序列**

Thesis: Geometry diagrams, visual math retrieval, physical/math diagrams, and graph/string-diagram proof systems. The frontier is grounding visual structure into verifiable logic.

Depends on: Layer 1 verification and Layer 2 formalization; often Layer 5 construction heuristics.

Enables: Visual/spatial heuristic construction, multimodal autoformalization, diagrammatic proof search.

### Core papers / 必读主线
- **MMFormalizer: Multimodal Autoformalization in the Wild** [paper] — Translate informal math into formal statements/proofs.  
  https://arxiv.org/abs/2601.03017
- **MathNet project site** [benchmark/data] — Multimodal math reasoning/retrieval benchmark.  
  https://mathnet.mit.edu/
- **MathNet: a Global Multimodal Benchmark for Mathematical Reasoning and Retrieval** [benchmark/data] — Multimodal math reasoning/retrieval benchmark.  
  https://arxiv.org/abs/2604.18584
- **AlphaGeometry GitHub repository** [code] — Neuro-symbolic auxiliary construction; best example for visual/spatial heuristic proof.  
  https://github.com/google-deepmind/alphageometry

### Supporting sources / 补充材料
- **MathVista: Evaluating Mathematical Reasoning of Foundation Models in Visual Contexts** [paper] — Supporting reference for this layer.  
  https://arxiv.org/abs/2310.02255
- **Quantomatic: A Proof Assistant for Diagrammatic Reasoning** [paper] — Diagrammatic proof and graph rewriting route beyond text proofs.  
  https://arxiv.org/abs/1503.01034
- **Solving olympiad geometry without human demonstrations** [paper] — Supporting reference for this layer.  
  https://www.nature.com/articles/s41586-023-06747-5
- **Polymath: A Challenging Multi-modal Mathematical Reasoning Benchmark** [benchmark/data] — Supporting reference for this layer.  
  https://arxiv.org/abs/2410.14702
- **MathVerse: Does Your Multi-modal LLM Truly See the Diagrams in Visual Math Problems?** [resource] — Supporting reference for this layer.  
  https://web.cs.ucla.edu/~kwchang/bibliography/zhang2024mathverse/

## Layer 7 — Code / Project Pages / Datasets

**可直接上手的实现入口**

Thesis: Repositories, project pages, and datasets that are useful when you move from reading to building.

Depends on: Specific target depends on which layer you are implementing.

Enables: Local experiments: LeanDojo/ReProver, PatternBoost/Axplorer, Int2Int, mathlib graph, AlphaGeometry, miniF2F/ProofNet.

### Core papers / 必读主线
- None assigned.

### Supporting sources / 补充材料
- **CombiBench: Benchmarking LLM Capability for Combinatorial Mathematics** [benchmark/data] — Supporting reference for this layer.  
  https://arxiv.org/abs/2505.03171
- **CombiBench GitHub repository** [code] — Supporting reference for this layer.  
  https://github.com/MoonshotAI/CombiBench

## Watchlist / 需要继续核验
- Axiom private training stack / synthetic data loop is not fully public.
- Interview benchmark names like Mini-CTX v2, Combi Bench, PanDM still need public paper/page confirmation.
- Equivalence-aware RAG + automated lemma transport is feasible from components, but not yet a single mature open system.
- Some 2026 items should be rechecked before formal citation.
