from __future__ import annotations

from typing import Any


LLM_PROOF_BODY_GENERATION_CONTRACT: dict[str, Any] = {
    "mode": "llm_zero_shot_with_lean_compile_feedback",
    "candidate_generators": [
        "formalizer_proofengineer_llm",
        "openprover_hlm_controller",
    ],
    "context_providers": [
        "lean_lsp_mcp",
        "emperical_process_lean_rag",
        "openprover_verified_feedback_assets",
    ],
    "task_normalization": "model_selected_current_goal_task",
    "candidate_response_contract": "json_schema",
    "compiler_feedback_retry": True,
    "openprover_initial_static_search": False,
    "static_tactic_fallback": False,
    "verification_authority": "exact_local_lean_or_axle_kernel_rerun",
}


def llm_proof_body_generation_contract() -> dict[str, Any]:
    """Return an isolated JSON-ready proof-agent contract."""

    return {
        key: list(value) if isinstance(value, list) else value
        for key, value in LLM_PROOF_BODY_GENERATION_CONTRACT.items()
    }
