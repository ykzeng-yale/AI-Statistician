"""Planning utilities for the StatLeanAgent workflow."""

from __future__ import annotations

from dataclasses import dataclass

from statlean_agent.agents import AGENT_REGISTRY, AgentRole


@dataclass(frozen=True)
class WorkflowStage:
    name: str
    agents: tuple[str, ...]
    output: str


DEFAULT_WORKFLOW: tuple[WorkflowStage, ...] = (
    WorkflowStage("ingest", ("problem_ingest",), "StatClaim"),
    WorkflowStage("formalize", ("formalization", "library_cartographer"), "LeanTask"),
    WorkflowStage("plan", ("proof_planner", "lemma_miner"), "Proof plan and sublemmas"),
    WorkflowStage("prove", ("tactic_synthesizer", "whole_proof_generator", "verifier"), "ProofAttempt"),
    WorkflowStage("repair", ("error_repair", "verifier"), "Verified proof or failure taxonomy"),
    WorkflowStage("curate", ("library_curator", "worktree_steward"), "Accepted lemma patch"),
    WorkflowStage("benchmark", ("benchmark_generator", "reward_eval"), "StatInferBench task"),
    WorkflowStage("train", ("trainer", "reward_eval"), "SFT/DPO/GRPO training manifest"),
)


def workflow_agents() -> tuple[AgentRole, ...]:
    """Return all agents used by the default workflow in registry order."""

    used = {key for stage in DEFAULT_WORKFLOW for key in stage.agents}
    return tuple(agent for agent in AGENT_REGISTRY if agent.key in used)

