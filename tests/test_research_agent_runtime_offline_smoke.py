from __future__ import annotations

from pathlib import Path

import ai_statistician.research_agent_runtime_offline_smoke as offline_smoke
from ai_statistician.critic_evaluator_llm import CRITIC_EVALUATOR_OUTPUT_CONTRACT


def test_offline_smoke_fixture_exercises_formal_gap_feedback() -> None:
    architect_response = offline_smoke._architect_response()
    evidence_contract = architect_response["evidence_contract"]

    assert evidence_contract["formal_verification_policy"] == "required"
    assert evidence_contract["formal_required_for_final"] is True
    assert "formal gap" in architect_response["iteration_policy"][
        "reroute_triggers"
    ]
    critic_response = offline_smoke._critic_response()
    for field in CRITIC_EVALUATOR_OUTPUT_CONTRACT:
        assert critic_response[field]


def test_offline_smoke_runtime_config_requires_formal_feedback(
    monkeypatch,
    tmp_path: Path,
) -> None:
    captured = {}

    def fake_runtime(*args, **kwargs):
        Path(args[1]).mkdir(parents=True, exist_ok=True)
        captured["config"] = kwargs["config"]
        return {}

    monkeypatch.setattr(offline_smoke, "run_research_agent_runtime", fake_runtime)

    offline_smoke.run_research_agent_runtime_offline_smoke(
        tmp_path / "offline-smoke",
        n_runs=1,
        max_iterations=1,
    )

    assert captured["config"].formal_verification_policy == "required"
