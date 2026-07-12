from __future__ import annotations

from typing import Any, Mapping


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
    "task_normalization": "llm_structured_json",
    "candidate_response_contract": "json_schema",
    "compiler_feedback_retry": True,
    "openprover_initial_static_search": False,
    "static_tactic_fallback": False,
    "verification_authority": "exact_local_lean_or_axle_kernel_rerun",
}


LEGACY_PYTHON_LEAN_STRATEGY_FIELDS = frozenset(
    {
        "ascii_identifier_rule",
        "core_lean_diagnostic_helper_shape",
        "core_lean_only_helper_example",
        "core_lean_only_helper_rule",
    }
)
LEGACY_PYTHON_LEAN_STRATEGY_DIAGNOSTIC_CLASSES = frozenset(
    {"lean_no_import_noncore_arithmetic"}
)


def llm_proof_body_generation_contract() -> dict[str, Any]:
    """Return an isolated JSON-ready proof-agent contract."""

    return {
        key: list(value) if isinstance(value, list) else value
        for key, value in LLM_PROOF_BODY_GENERATION_CONTRACT.items()
    }


def without_legacy_python_lean_strategy_fields(
    contract: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Drop retired runtime-authored proof strategies from carried memory."""

    cleaned = {
        str(key): value
        for key, value in dict(contract or {}).items()
        if str(key) not in LEGACY_PYTHON_LEAN_STRATEGY_FIELDS
    }
    if isinstance(cleaned.get("diagnostic_classes"), (list, tuple, set)):
        cleaned["diagnostic_classes"] = [
            str(value)
            for value in cleaned["diagnostic_classes"]
            if str(value) not in LEGACY_PYTHON_LEAN_STRATEGY_DIAGNOSTIC_CLASSES
        ]
    return cleaned
