"""StatLeanAgent orchestration package."""

from statlean_agent.agents import AGENT_REGISTRY, AgentRole, get_agent
from statlean_agent.contracts import LeanTask, ProofAttempt, StatClaim

__all__ = [
    "AGENT_REGISTRY",
    "AgentRole",
    "LeanTask",
    "ProofAttempt",
    "StatClaim",
    "get_agent",
]

