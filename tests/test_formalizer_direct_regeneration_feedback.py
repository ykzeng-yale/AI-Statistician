from __future__ import annotations

import json

from ai_statistician.formalizer_llm import build_formalizer_prompt
from ai_statistician.research_agent_runtime import (_formalizer_lean_candidate_revision_feedback,)
from ai_statistician.research_schema import (OpenResearchQuestion,)


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

    prompt = build_formalizer_prompt(
        question=QUESTION,
        theory_packet={"packet_id": "theory:complete-feedback"},
        simulation_manifest={},
        algorithm_manifest={},
        registered_problem={},
        theorem_goals=[],
        environment_feedback=feedback,
    )
    payload = json.loads(prompt[prompt.index('{"question":') :])
    carried = payload["runtime_environment_feedback"]
    carried_row = carried["candidate_diagnostics"][0]
    assert carried_row["lean_source"] == source
    assert carried_row["local_lean_stdout"].endswith("STDOUT_TAIL")
    assert carried_row["local_lean_stderr"].endswith("STDERR_TAIL")
    assert carried_row["future_compiler_observation"]["provider_specific"] == (
        "PRESERVE_ME"
    )
    assert "future_repair_diagnostics" not in carried_row
    assert "preferred_tool_order" not in carried_row
    assert "candidate_live_proof_state_request" not in carried_row
    assert "lean_multi_attempt" not in json.dumps(carried_row, sort_keys=True)
    assert carried_row["tool_call_trace"][0]["tool"] == (
        "lean_lsp_mcp.lean_diagnostic_messages"
    )
    assert "required_change" not in (
        carried["prior_environment_feedback"]["findings"][0]
    )
    assert "complete standalone model-authored Lean source" in prompt
    assert "AgentRuntime does not inject" in prompt
