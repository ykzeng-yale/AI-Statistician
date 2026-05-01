"""Agent registry for the AI-Statistician system."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class AgentRole:
    """Static description of a specialized agent."""

    key: str
    name: str
    mission: str
    owns: tuple[str, ...]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    may_write_code: bool = False
    requires_verification: bool = True


AGENT_REGISTRY: tuple[AgentRole, ...] = (
    AgentRole(
        key="problem_ingest",
        name="Problem Ingest Agent",
        mission="Normalize textbook, paper, or user claims into auditable statistical specifications.",
        owns=("schemas/stat_claim.schema.json", "benchmarks/raw_claims/"),
        inputs=("natural_language_claim", "source_metadata"),
        outputs=("StatClaim",),
    ),
    AgentRole(
        key="formalization",
        name="Formalization Agent",
        mission="Translate statistical specifications into Lean theorem skeletons without changing meaning.",
        owns=("StatInference/", "schemas/lean_task.schema.json"),
        inputs=("StatClaim", "formalization_guidelines"),
        outputs=("LeanTask", "statement_variants"),
        may_write_code=True,
    ),
    AgentRole(
        key="library_cartographer",
        name="Library Cartographer Agent",
        mission="Map mathlib, seed projects, and the local library into retrievable premise bundles.",
        owns=("artifacts/premise_index/", "src/statlean_agent/retrieval.py"),
        inputs=("LeanTask", "proof_state"),
        outputs=("premise_bundle",),
    ),
    AgentRole(
        key="proof_planner",
        name="Proof Planner Agent",
        mission="Decompose hard theorems into proof plans and candidate sublemmas.",
        owns=("artifacts/plans/",),
        inputs=("LeanTask", "premise_bundle"),
        outputs=("proof_plan", "sublemma_candidates"),
    ),
    AgentRole(
        key="tactic_synthesizer",
        name="Tactic Synthesizer Agent",
        mission="Generate state-local Lean tactics with retrieved premises and proof-state feedback.",
        owns=("artifacts/tactic_attempts/",),
        inputs=("proof_state", "premise_bundle", "proof_history"),
        outputs=("ProofAttempt",),
        may_write_code=True,
    ),
    AgentRole(
        key="whole_proof_generator",
        name="Whole-Proof Generator Agent",
        mission="Generate full Lean proof candidates for theorem statements when stepwise search is too slow.",
        owns=("artifacts/whole_proofs/",),
        inputs=("LeanTask", "proof_plan", "premise_bundle"),
        outputs=("ProofAttempt",),
        may_write_code=True,
    ),
    AgentRole(
        key="verifier",
        name="Verifier Agent",
        mission="Run Lean, Pantograph, or Kimina Lean Server and provide authoritative proof feedback.",
        owns=("artifacts/verification/",),
        inputs=("ProofAttempt", "LeanTask"),
        outputs=("VerificationReport",),
    ),
    AgentRole(
        key="error_repair",
        name="Error Repair Agent",
        mission="Classify Lean failures and propose minimal repairs for imports, tactics, and typeclass issues.",
        owns=("artifacts/repairs/",),
        inputs=("VerificationReport", "ProofAttempt"),
        outputs=("repair_patch", "failure_taxonomy"),
        may_write_code=True,
    ),
    AgentRole(
        key="lemma_miner",
        name="Lemma Miner Agent",
        mission="Extract reusable sublemmas from repeated failures and successful proof traces.",
        owns=("artifacts/lemma_candidates/",),
        inputs=("proof_traces", "failure_clusters"),
        outputs=("CuratedLemmaCandidate",),
    ),
    AgentRole(
        key="library_curator",
        name="Library Curator Agent",
        mission="Accept only verified, useful, non-vacuous statistics lemmas into the curated library.",
        owns=("src/statlean_agent/curation.py", "docs/curation_policy.md"),
        inputs=("CuratedLemmaCandidate", "downstream_usage"),
        outputs=("CurationDecision",),
    ),
    AgentRole(
        key="benchmark_generator",
        name="Benchmark Generator Agent",
        mission="Build StatInferBench tasks from theorem holes, proof states, and textbook theorem clusters.",
        owns=("benchmarks/", "schemas/benchmark_task.schema.json"),
        inputs=("LeanTask", "proof_trace", "domain_tag"),
        outputs=("BenchmarkTask",),
        may_write_code=True,
    ),
    AgentRole(
        key="reward_eval",
        name="Reward and Evaluation Agent",
        mission="Score proof attempts, curation decisions, and benchmark performance for SFT/DPO/GRPO.",
        owns=("src/statlean_agent/rewards.py", "artifacts/evals/"),
        inputs=("ProofAttempt", "VerificationReport", "BenchmarkTask"),
        outputs=("RewardBreakdown", "EvalReport"),
    ),
    AgentRole(
        key="trainer",
        name="Trainer Agent",
        mission="Prepare SFT, DPO, and process-reward GRPO datasets and launch training jobs.",
        owns=("training/", "config/training.toml"),
        inputs=("verified_traces", "preference_pairs", "reward_logs"),
        outputs=("training_run_manifest",),
    ),
    AgentRole(
        key="worktree_steward",
        name="Worktree Steward Agent",
        mission="Create isolated git worktrees and branch names for code-writing agents.",
        owns=("src/statlean_agent/worktrees.py", "docs/worktree_strategy.md"),
        inputs=("AgentRole", "base_branch"),
        outputs=("WorktreeAssignment",),
    ),
)


def get_agent(key: str) -> AgentRole:
    """Return an agent by key."""

    for agent in AGENT_REGISTRY:
        if agent.key == key:
            return agent
    raise KeyError(f"unknown agent key: {key}")


def writable_agents(agents: Iterable[AgentRole] = AGENT_REGISTRY) -> tuple[AgentRole, ...]:
    """Return agents that may write code or Lean files."""

    return tuple(agent for agent in agents if agent.may_write_code)

