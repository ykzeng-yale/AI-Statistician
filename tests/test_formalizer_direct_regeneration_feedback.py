from __future__ import annotations

import json

from ai_statistician.formalizer_llm import (
    _build_lean_candidate_workspace_tool_prompt,
    _compact_value,
)
from ai_statistician.research_agent_runtime import (
    _formalizer_lean_candidate_revision_feedback,
)
from ai_statistician.research_schema import OpenResearchQuestion


QUESTION = OpenResearchQuestion(
    id="generic_formal_feedback",
    title="Generic formal feedback",
    description="Regenerate an exact Lean source from environment observations.",
    tags=("formalization",),
)


def test_formalizer_receives_complete_source_and_raw_tool_observations() -> None:
    source = "theorem exact_target : True := by\n" + "  skip\n" * 900
    stdout = "compiler stdout\n" + "x" * 6000 + "STDOUT_TAIL"
    stderr = "compiler stderr\n" + "y" * 6000 + "STDERR_TAIL"
    manifest = {
        "artifact_kind": "RuntimeFormalizerLeanCandidateMaterialization",
        "manifest_id": "materialization:complete-feedback",
        "future_manifest_observation": {"opaque": [1, 2, 3]},
        "n_candidate_sources": 1,
        "n_candidate_artifacts_written": 1,
        "n_precheck_rejected": 0,
        "n_local_lean_checked": 1,
        "n_local_lean_compiled": 0,
        "candidate_rows": [
            {
                "candidate_id": "exact-target",
                "candidate_kind": "formal_target_lean_statement_sketch",
                "source_field": "formal_targets",
                "lean_source": source,
                "local_lean_attempted": True,
                "local_lean_compiled": False,
                "local_lean_exit_status": "1",
                "local_lean_stdout": stdout,
                "local_lean_stderr": stderr,
                "future_compiler_observation": {
                    "provider_specific": "PRESERVE_ME"
                },
                "future_repair_diagnostics": {
                    "raw_provider_message": "PRESERVE_DESPITE_LEGACY_SUFFIX"
                },
                "candidate_live_proof_state_request": {
                    "mcp_tool_calls": [
                        {"tool": "lean_multi_attempt", "arguments": {}}
                    ]
                },
                "tool_call_trace": [
                    {
                        "tool": "lean_lsp_mcp.lean_diagnostic_messages",
                        "status": "mcp_tool_call_succeeded",
                    }
                ],
                "preferred_tool_order": ["runtime-authored-legacy-recipe"],
            }
        ],
    }
    reviewer_feedback = {
        "feedback_type": "formal_target_semantic_review_feedback",
        "findings": [
            {
                "finding_id": "reviewer:finding",
                "required_change": "MODEL_REVIEWER_OBSERVATION_MUST_SURVIVE",
            }
        ],
    }

    feedback = _formalizer_lean_candidate_revision_feedback(
        manifest,
        prior_environment_feedback=reviewer_feedback,
    )

    assert feedback is not None
    assert "future_manifest_observation" not in feedback
    row = feedback["candidate_diagnostics"][0]
    assert row["lean_source"] == source
    assert row["local_lean_stdout"] == stdout
    assert row["local_lean_stderr"] == stderr
    assert row["future_compiler_observation"]["provider_specific"] == (
        "PRESERVE_ME"
    )
    assert "future_repair_diagnostics" in row

    prompt = _build_lean_candidate_workspace_tool_prompt(
        question=QUESTION,
        theory_packet={"packet_id": "theory:complete-feedback"},
        parent_packet={
            "artifact_kind": "FormalizerWorkspaceTarget",
            "target_ref_id": "formalizer_workspace_target:exact-target",
            "formal_target": {
                "id": "exact-target",
                "formal_target_role": "SOURCE_THEOREM_CANDIDATE",
                "informal_source": "The exact target holds.",
                "candidate_lean_declaration": "exact_target",
                "semantic_alignment_constraints": ["Preserve the target."],
                "source_theorem_target_provenance": {
                    "source_theorem_goal_id": "exact-target",
                    "source_theorem_target_known": True,
                },
                "expected_status": "NEEDS_KERNEL_CHECK",
            },
        },
        candidate_id="exact-target",
        candidate_source_field="formal_targets",
        candidate_lean_declaration="exact_target",
        initial_source=source,
        environment_feedback=feedback,
    )
    payload = json.loads(prompt)
    carried = payload["runtime_observations"]
    carried_row = carried["candidate_diagnostics"][0]
    assert "lean_source" not in carried_row
    assert carried_row["local_lean_stdout"].endswith("STDOUT_TAIL")
    assert carried_row["local_lean_stderr"].endswith("STDERR_TAIL")
    assert carried_row["future_compiler_observation"]["provider_specific"] == (
        "PRESERVE_ME"
    )
    assert carried_row["future_repair_diagnostics"] == {
        "raw_provider_message": "PRESERVE_DESPITE_LEGACY_SUFFIX"
    }
    assert "preferred_tool_order" not in carried_row
    assert "candidate_live_proof_state_request" not in carried_row
    assert "lean_multi_attempt" not in json.dumps(carried_row, sort_keys=True)
    assert carried_row["tool_call_trace"][0]["tool"] == (
        "lean_lsp_mcp.lean_diagnostic_messages"
    )
    assert "required_change" not in (
        carried["semantic_review"]["findings"][0]
    )
    assert payload["boundaries"]["model_owns_lean_source_and_search_queries"]
    assert payload["boundaries"]["runtime_selected_lean_code"] is False


def test_formalizer_compaction_preserves_model_method_and_tool_fields() -> None:
    observations = {
        "proof_strategy": "Model-authored argument.",
        "experiment_recipe": {"source": "model-authored source"},
        "provider_repair_rule": "Raw provider observation, not harness authority.",
    }

    assert _compact_value(observations) == observations
