from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .formal_source_index import build_formal_source_index, formal_source_index_fingerprint
from .frontier_coverage_audit import audit_frontier_coverage
from .autoform_harness import build_autoform_harness_profile
from .proof_attempt_log import PROOF_ATTEMPT_SCHEMA_VERSION
from .proof_bank import all_obligations, proof_bank_fingerprint
from .proof_policy_baseline import PROOF_POLICY_BASELINE_SCHEMA_VERSION
from .proof_repair_export import PROOF_REPAIR_EXPORT_SCHEMA_VERSION
from .proof_search import PROOF_SEARCH_SCHEMA_VERSION
from .proof_training_export import PROOF_TRAINING_EXPORT_SCHEMA_VERSION
from .research_policy_baseline import RESEARCH_POLICY_BASELINE_SCHEMA_VERSION
from .research_training_export import RESEARCH_TRAINING_EXPORT_SCHEMA_VERSION
from .research_lab import (
    PROVABLE_SUBCLAIMS,
    all_research_algorithm_specs,
    load_open_research_questions,
    research_algorithm_registry_fingerprint,
)
from .research_knowledge import FORMAL_INFRASTRUCTURE_KNOWLEDGE, KNOWLEDGE_CARDS
from .research_source_inventory import build_research_source_inventory, research_source_inventory_fingerprint


@dataclass(frozen=True)
class ProverComponentRow:
    component: str
    paper_stack_layer: str
    status: str
    trained_or_built: str
    why_it_matters: str
    current_evidence: tuple[str, ...]
    missing_or_next: tuple[str, ...]


def build_prover_component_audit(
    *,
    root: Path | None = None,
    question_file: Path = Path("examples/research_questions.json"),
    frontier_benchmark_file: Path = Path("docs/frontier_stat_theory_benchmark.md"),
) -> dict[str, object]:
    """Audit the AI Statistician system against the modern prover stack.

    The source outline in ``AI for Math Resources/master_ai_for_math_formal_verification.md``
    treats AI-for-math as a stack: verifier, formal data, retrieval/memory,
    prover/search/RL, and discovery/construction. This audit maps that stack to
    the current codebase and explicitly separates built components from
    untrained or missing components.
    """

    project_root = (root or Path.cwd()).resolve()
    question_path = _resolve(project_root, question_file)
    frontier_path = _resolve(project_root, frontier_benchmark_file)
    paper_outline = project_root / "AI for Math Resources" / "master_ai_for_math_formal_verification.md"

    questions = load_open_research_questions(question_path)
    frontier = audit_frontier_coverage(benchmark_file=frontier_path)
    source_inventory = build_research_source_inventory()
    autoform_profile = build_autoform_harness_profile()
    algorithms = all_research_algorithm_specs()
    obligations = all_obligations()
    declarations = build_formal_source_index()

    rows = [
        ProverComponentRow(
            component="hard verifier / Lean kernel interface",
            paper_stack_layer="Layer 1: Logic / Kernel / Verification Substrate",
            status="READY",
            trained_or_built="Built, not trained. Lean/AXLE is the trusted verifier; models and search are untrusted generators.",
            why_it_matters="This is the soundness boundary: every accepted proof-bank claim must pass AXLE/Lean, not LLM confidence.",
            current_evidence=(
                f"proof_bank_obligations={len(obligations)}",
                "AxleProofVerifier calls AXLE verify_proof for --real-lean audits",
                f"proof_bank_fingerprint={proof_bank_fingerprint()[:16]}",
            ),
            missing_or_next=(
                "No tactic-level Lean environment wrapper yet; current verifier is proof-file/obligation level.",
            ),
        ),
        ProverComponentRow(
            component="formal data and frontier benchmarks",
            paper_stack_layer="Layer 2: Formal Data / Autoformalization / Benchmarks",
            status="READY_FOR_CURRENT_RELEASE",
            trained_or_built="Built deterministic benchmark/intake data; not a learned autoformalization dataset.",
            why_it_matters="The system needs stable tasks and held-out frontier-style questions before model training or RL makes sense.",
            current_evidence=(
                f"open_research_questions={len(questions)}",
                f"frontier_supported={frontier['n_supported']}/{frontier['n_questions']}",
                f"frontier_unsupported_backlog={frontier['n_unsupported']}",
                str(question_path),
                str(frontier_path),
            ),
            missing_or_next=(
                "No large traced Lean proof-state dataset.",
                "No natural-language paper-to-Lean theorem SFT corpus yet.",
            ),
        ),
        ProverComponentRow(
            component="statistical problem formalizer / autoformalizer",
            paper_stack_layer="Layer 2: Formal Data / Autoformalization / Benchmarks",
            status="PARTIAL",
            trained_or_built="Built registry-gated statistical formalizer for DGP/estimand/assumptions/asymptotic regime; not trained.",
            why_it_matters="It turns paper-style questions into structured theory-lab problems while refusing unsupported topics.",
            current_evidence=(
                "ProblemFormalizer extracts registered statistical problem classes",
                "research-intake-audit checks supported acceptance and unsupported rejection",
                "Markdown paper-style examples are supported",
                f"autoform_bot_harness_ready={autoform_profile.exists and autoform_profile.has_statement_extraction and autoform_profile.has_lean_eval}",
                f"autoform_bot_commit={autoform_profile.git_commit[:12]}",
            ),
            missing_or_next=(
                "No general LLM autoformalizer that writes arbitrary Lean theorem statements from new papers.",
                "No verifier-filtered training loop for informal-to-formal statistical statements.",
            ),
        ),
        ProverComponentRow(
            component="premise retrieval / Lean RAG / formal-source search",
            paper_stack_layer="Layer 3: Mathlib Retrieval / Knowledge Graph / Long-Term Memory",
            status="PARTIAL_STRONG_LOCAL",
            trained_or_built="Built local declaration-level retrieval with SQLite FTS, theorem compression, declaration-symbol graph expansion, OpenProver-token fallback, and optional Loogle evidence; not learned semantic retrieval.",
            why_it_matters="Most current proof failures are premise-selection failures. Efficient local retrieval is the path from Mathlib/StatInference source to proof-bank expansion.",
            current_evidence=(
                f"formal_source_declarations={len(declarations)}",
                f"formal_source_fingerprint={formal_source_index_fingerprint(declarations)[:16]}",
                f"knowledge_cards={len(KNOWLEDGE_CARDS)}",
                f"formal_infrastructure_cards={len(FORMAL_INFRASTRUCTURE_KNOWLEDGE)}",
                f"source_inventory_ok={source_inventory['n_ok']}/{source_inventory['n_sources']}",
            ),
            missing_or_next=(
                "No Lean Finder/ReProver runtime provider fusion yet.",
                "No embedding index, proof-dependency graph from traced proofs, or tactic-state-aware retrieval yet.",
            ),
        ),
        ProverComponentRow(
            component="tactic / whole-proof policy model",
            paper_stack_layer="Layer 4: Formal Prover Engines / RL / Proof Search",
            status="BASELINE_ONLY",
            trained_or_built="Not trained. A deterministic nearest-neighbor whole-proof policy baseline exists for exported SFT data.",
            why_it_matters="A real prover needs a policy that proposes tactics/proof blocks from proof states and retrieved premises.",
            current_evidence=(
                "Proof-bank obligations contain known proof bodies",
                "FormalSubclaimProver retrieves and verifies registered obligations",
                f"proof_policy_baseline_schema_version={PROOF_POLICY_BASELINE_SCHEMA_VERSION}",
                "proof-policy-baseline evaluates proof-memory predictions on validation examples",
            ),
            missing_or_next=(
                "Train or integrate a tactic/whole-proof generator over traced Lean states.",
                "Add error-message repair and pass@k proof sampling.",
            ),
        ),
        ProverComponentRow(
            component="search controller / MCTS / best-first proof search",
            paper_stack_layer="Layer 4: Formal Prover Engines / RL / Proof Search",
            status="PARTIAL_WHOLE_PROOF_SEARCH",
            trained_or_built="Built a bounded best-first whole-proof search controller over proof-body candidates; not tactic-state search or MCTS.",
            why_it_matters="Search decides which proof branch to expand when one-shot proof generation fails.",
            current_evidence=(
                f"proof_search_schema_version={PROOF_SEARCH_SCHEMA_VERSION}",
                "BestFirstWholeProofSearchController expands a bounded candidate frontier and verifies each node",
                "proof-search-audit writes proof_search_results.jsonl with node-level verifier feedback",
            ),
            missing_or_next=(
                "Build a Lean step environment wrapper.",
                "Upgrade from whole-proof candidate search to tactic-state best-first search before RL.",
                "Add MCTS/value guidance after tactic-state traces exist.",
            ),
        ),
        ProverComponentRow(
            component="value/progress model and verifier-grounded RL",
            paper_stack_layer="Layer 4: Formal Prover Engines / RL / Proof Search",
            status="MISSING",
            trained_or_built="Not trained. Current audits use verifier outcomes as release gates, not as gradient/RL data.",
            why_it_matters="Process reward and progress prediction reduce branch explosion and convert Lean feedback into learning.",
            current_evidence=(
                "Proof audits persist verification results and elapsed times",
                "No training buffer, value head, PPO/GRPO/DPO, or expert-iteration loop",
            ),
            missing_or_next=(
                "Log failed proof attempts and earliest Lean errors.",
                "Train progress/value models only after tactic-state traces exist.",
            ),
        ),
        ProverComponentRow(
            component="subgoal decomposition / theorem planning",
            paper_stack_layer="Layer 4: Formal Prover Engines / RL / Proof Search",
            status="PARTIAL_TEMPLATE",
            trained_or_built="Built statistical theorem-goal templates and formal-gap decomposition; not a learned decomposer.",
            why_it_matters="Frontier statistical theory proofs naturally decompose into identification, consistency, linearization, CLT, variance, and remainder lemmas.",
            current_evidence=(
                "TheoryPlanner emits theorem goals, proof obligations, and missing formal primitives",
                f"problem_classes_with_provable_subclaims={len(PROVABLE_SUBCLAIMS)}",
            ),
            missing_or_next=(
                "No recursive subgoal prover.",
                "No learned usefulness/reuse reward for generated sublemmas.",
            ),
        ),
        ProverComponentRow(
            component="skill library / reusable proof memory",
            paper_stack_layer="Layer 3 + Layer 4: Long-Term Memory / Growing Libraries",
            status="PARTIAL",
            trained_or_built="Built a curated proof bank with dependencies; not an autonomously growing skill library.",
            why_it_matters="Reusable verified lemmas are the bridge from one-off proof success to cumulative statistical formalization.",
            current_evidence=(
                f"proof_bank_obligations={len(obligations)}",
                f"dependency_linked_problem_classes={len(PROVABLE_SUBCLAIMS)}",
                "proof-audit exports per-obligation Lean files",
            ),
            missing_or_next=(
                "No automatic mining of have-lemmas from successful proofs.",
                "No skill usefulness metric or pruning/generalization loop.",
            ),
        ),
        ProverComponentRow(
            component="construction/procedure generator",
            paper_stack_layer="Layer 5: Discovery / Construction / Conjecturing",
            status="PARTIAL_REGISTRY",
            trained_or_built="Built registry-backed candidate procedure generation and vetted algorithms; not free-form estimator/procedure invention.",
            why_it_matters="For AI Statistician, construction means proposing estimators, scores, confidence sets, tests, and algorithms before proving/evaluating them.",
            current_evidence=(
                f"vetted_research_algorithms={sum(1 for row in algorithms if row.registry_status == 'vetted')}/{len(algorithms)}",
                f"algorithm_registry_fingerprint={research_algorithm_registry_fingerprint()[:16]}",
            ),
            missing_or_next=(
                "No learned estimator/procedure construction model.",
                "No verifier/simulator-guided construction search over estimator families.",
            ),
        ),
        ProverComponentRow(
            component="counterexample / disproof / falsification loop",
            paper_stack_layer="Layer 5: Discovery / Construction / Conjecturing",
            status="PARTIAL_EMPIRICAL",
            trained_or_built="Built simulation-based falsification of procedure behavior; not formal counterexample generation.",
            why_it_matters="False statistical conjectures should be killed early by small counterexamples or simulation stress tests.",
            current_evidence=(
                "ResearchSimulator flags bias, coverage, FDR, power, optional-stopping error, PCA alignment, and tail coverage",
                "Unsupported topics are rejected rather than hallucinated",
            ),
            missing_or_next=(
                "No Lean counterexample generator for false theorem statements.",
                "No SMT/finite-model search or formal disproof proof bank.",
            ),
        ),
        ProverComponentRow(
            component="simulation/evaluator loop for statistical claims",
            paper_stack_layer="Domain-specific evaluator beside Layers 4-5",
            status="READY_FOR_CURRENT_RELEASE",
            trained_or_built="Built Monte Carlo environments and diagnostics for registered frontier-style problem classes.",
            why_it_matters="Simulation is not proof, but it is the empirical critic that catches estimator/procedure failures before formalization effort is spent.",
            current_evidence=(
                f"vetted_research_algorithms={len(algorithms)}",
                "research-system-audit requires zero simulation-flagged supported benchmark traces",
            ),
            missing_or_next=(
                "No automatic adversarial DGP generator.",
                "No simulator-to-theory gradient/training loop yet.",
            ),
        ),
        ProverComponentRow(
            component="trace/audit/provenance layer",
            paper_stack_layer="System composition / release engineering",
            status="READY",
            trained_or_built="Built manifests, fingerprints, trace audits, gap audits, proof audits, and source inventory audits.",
            why_it_matters="A research assistant that cannot explain what was proved, simulated, retrieved, or left as a gap is not production-safe.",
            current_evidence=(
                f"source_inventory_fingerprint={research_source_inventory_fingerprint()[:16]}",
                "research-system-audit gates intake, knowledge, retrieval, algorithms, proofs, traces, simulations, and gaps",
            ),
            missing_or_next=(
                "No experiment tracking database beyond JSON/Markdown artifacts.",
            ),
        ),
        ProverComponentRow(
            component="proof-attempt logging / training data substrate",
            paper_stack_layer="Layer 2 -> Layer 4 learning loop",
            status="PARTIAL_DATA_EXPORT",
            trained_or_built="Built proof-level attempt JSONL logging plus whole-proof SFT dataset export; not tactic-state tracing or model training.",
            why_it_matters="Verifier-filtered attempt rows and SFT prompt/completion exports are the first substrate for whole-proof SFT, rejection sampling, repair data, and future value-model labels.",
            current_evidence=(
                f"proof_attempt_schema_version={PROOF_ATTEMPT_SCHEMA_VERSION}",
                f"proof_training_export_schema_version={PROOF_TRAINING_EXPORT_SCHEMA_VERSION}",
                f"proof_repair_export_schema_version={PROOF_REPAIR_EXPORT_SCHEMA_VERSION}",
                "proof-audit writes proof_attempts.jsonl and proof_attempt_log_manifest.json",
                "proof-training-export writes proof_sft_train.jsonl, proof_sft_validation.jsonl, and proof_training_manifest.json",
                "proof-repair-export writes failed-attempt repair examples when negative controls/search failures are present",
                "positive rows include supervision_target; negative rows preserve verifier errors and reward=0",
            ),
            missing_or_next=(
                "No tactic-state transitions or earliest failing tactic extraction yet.",
                "Use existing LeanDojo/ReProver/Lean Finder infrastructure where possible.",
            ),
        ),
        ProverComponentRow(
            component="research-agent trace training data substrate",
            paper_stack_layer="Layer 2 -> Layer 4 learning loop",
            status="PARTIAL_DATA_EXPORT",
            trained_or_built="Built trace-level SFT/GRPO seed exports and a no-training nearest-neighbor baseline for theory-lab agents; no model weights trained.",
            why_it_matters="Problem formalization, theory planning, formal-gap routing, and simulation critique need their own supervised and reward-labeled data, not only proof-bank data.",
            current_evidence=(
                f"research_training_export_schema_version={RESEARCH_TRAINING_EXPORT_SCHEMA_VERSION}",
                f"research_policy_baseline_schema_version={RESEARCH_POLICY_BASELINE_SCHEMA_VERSION}",
                "research-training-export writes research_sft_train.jsonl, research_sft_validation.jsonl, research_grpo_tasks.jsonl, and a legacy training manifest",
                "research-policy-baseline evaluates nearest-neighbor memory on the exported research-agent validation examples",
            ),
            missing_or_next=(
                "No trained research-agent policy, DPO pair export, or simulator-feedback RL loop yet.",
                "No human-reviewed gold traces beyond registry-gated system traces.",
            ),
        ),
        ProverComponentRow(
            component="model training pipeline",
            paper_stack_layer="Layer 2 -> Layer 4 learning loop",
            status="MISSING",
            trained_or_built="Not built. The system logs proof-level attempts, but does not train model weights.",
            why_it_matters="Training is required for a real prover policy, retriever, value model, decomposer, and construction model.",
            current_evidence=(
                "No SFT/RL trainer, value head, PPO/GRPO/DPO loop, or trained checkpoint is registered",
            ),
            missing_or_next=(
                "Run verifier-filtered whole-proof SFT/rejection sampling from proof_sft_train.jsonl.",
                "Add tactic-state tracing before process-reward RL.",
            ),
        ),
    ]

    achieved = sum(1 for row in rows if row.status in {"READY", "READY_FOR_CURRENT_RELEASE"})
    partial = sum(1 for row in rows if row.status.startswith("PARTIAL"))
    missing = len(rows) - achieved - partial
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "paper_outline": str(paper_outline),
        "paper_outline_exists": paper_outline.exists(),
        "summary": {
            "components": len(rows),
            "ready": achieved,
            "partial": partial,
            "missing_or_not_trained": missing,
            "honest_goal_complete": False,
        },
        "provenance": {
            "proof_bank_fingerprint": proof_bank_fingerprint(),
            "formal_source_index_fingerprint": formal_source_index_fingerprint(declarations),
            "research_source_inventory_fingerprint": research_source_inventory_fingerprint(),
            "research_algorithm_registry_fingerprint": research_algorithm_registry_fingerprint(),
        },
        "rows": [asdict(row) for row in rows],
    }
    return payload


def write_prover_component_audit(payload: dict[str, object], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = out_dir / "prover_component_audit_manifest.json"
    report = out_dir / "prover_component_audit.md"
    manifest.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report.write_text(_component_audit_markdown(payload), encoding="utf-8")
    return manifest, report


def _component_audit_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]  # type: ignore[index]
    rows = payload["rows"]  # type: ignore[index]
    lines = [
        "# AI Statistician Prover Component Audit",
        "",
        "This audit maps the current system to the prover-system stack in",
        f"`{payload['paper_outline']}`.",
        "",
        "## Summary",
        "",
        f"- Components audited: {summary['components']}",  # type: ignore[index]
        f"- Ready/current-release: {summary['ready']}",  # type: ignore[index]
        f"- Partial: {summary['partial']}",  # type: ignore[index]
        f"- Missing or not trained: {summary['missing_or_not_trained']}",  # type: ignore[index]
        f"- Full goal complete: {summary['honest_goal_complete']}",  # type: ignore[index]
        "",
        "## Component Table",
        "",
        "| Component | Layer | Status | Built/trained? | Missing / next |",
        "|---|---|---|---|---|",
    ]
    for row in rows:  # type: ignore[assignment]
        missing = "<br>".join(row["missing_or_next"]) if row["missing_or_next"] else ""
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(row["component"]),
                    _md_cell(row["paper_stack_layer"]),
                    _md_cell(row["status"]),
                    _md_cell(row["trained_or_built"]),
                    _md_cell(missing),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Evidence Details", ""])
    for row in rows:  # type: ignore[assignment]
        lines.extend(
            [
                f"### {row['component']}",
                "",
                f"- Status: `{row['status']}`",
                f"- Why it matters: {row['why_it_matters']}",
                "- Evidence:",
                *[f"  - {item}" for item in row["current_evidence"]],
                "- Missing / next:",
                *[f"  - {item}" for item in row["missing_or_next"]],
                "",
            ]
        )
    return "\n".join(lines)


def _md_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", "<br>")


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path
