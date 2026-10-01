from __future__ import annotations

import os

from ai_statistician.model_backend import (
    LIVE_EVALUATION_MODEL,
    LIVE_EVALUATION_MODEL_TIER,
    resolve_live_evaluation_model,
)


EXPECTED_TEST_HAIKU_MODEL = "claude-haiku-4-5-20251001"


def test_offline_suite_is_credential_free_and_future_tests_use_local_qwen() -> None:
    assert LIVE_EVALUATION_MODEL_TIER == "local"
    assert LIVE_EVALUATION_MODEL == "Qwen3-4B-Instruct-2507"
    assert os.environ["AI_STATISTICIAN_LLM_PROVIDER"] == "local"
    assert os.environ["AI_STATISTICIAN_CLAUDE_HAIKU_MODEL"] == (
        EXPECTED_TEST_HAIKU_MODEL
    )
    assert os.environ["AI_STATISTICIAN_ANTHROPIC_HAIKU_MODEL"] == (
        EXPECTED_TEST_HAIKU_MODEL
    )
    assert resolve_live_evaluation_model("local") == LIVE_EVALUATION_MODEL
    for name in (
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "AXLE_API_KEY",
        "ARISTOTLE_API_KEY",
    ):
        assert name not in os.environ
    assert os.environ["AI_STATISTICIAN_ENV_FILE"] == os.devnull
