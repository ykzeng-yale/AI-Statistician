from pathlib import Path

import pytest

from ai_statistician.doctor import build_doctor_report
from ai_statistician.local_model_backend import DEFAULT_LOCAL_BASE_URL, LocalChatGeneratorBackend


def _forbid_network(*args, **kwargs):
    raise AssertionError("installation diagnosis must not contact a model")


def test_installed_local_diagnosis_does_not_require_checkout_or_cloud(tmp_path, monkeypatch):
    monkeypatch.setattr("urllib.request.build_opener", _forbid_network)
    report = build_doctor_report(
        root=tmp_path, environ={"AI_STATISTICIAN_LLM_PROVIDER": "local"},
        max_manifests=0,
    )
    checks = {row["name"]: row for row in report["checks"]}
    assert report["summary"]["required_ok"] is True
    assert report["summary"]["llm_theory_ready"] is True
    assert report["summary"]["llm_theory_blockers"] == []
    assert checks["package directory"]["status"] == "OK"
    assert Path(checks["package directory"]["detail"]).name == "ai_statistician"
    assert checks["example questions"]["status"] == "WARN"
    assert checks["example questions"]["required"] is False
    assert "Anthropic key" not in checks and "OpenAI key" not in checks
    assert "Configuration only" in checks["local model transport"]["detail"]
    assert "no endpoint request" in checks["local model transport"]["detail"]


@pytest.mark.parametrize("url", [
    DEFAULT_LOCAL_BASE_URL, "http://localhost:19001/v1", "http://[::1]:19002/v1",
    "https://example.invalid/v1", "http://example.invalid/v1",
    "http://probe@127.0.0.1/v1", "http://127.0.0.1/v1?token=probe", "",
])
def test_local_diagnosis_reuses_actual_backend_validation(tmp_path, monkeypatch, url):
    monkeypatch.setattr("urllib.request.build_opener", _forbid_network)
    try:
        LocalChatGeneratorBackend(base_url=url)
    except ValueError as exc:
        expected = [str(exc)]
    else:
        expected = []
    report = build_doctor_report(
        root=tmp_path, environ={
            "AI_STATISTICIAN_LLM_PROVIDER": "local",
            "AI_STATISTICIAN_LOCAL_BASE_URL": url,
        }, max_manifests=0,
    )
    assert report["summary"]["llm_theory_blockers"] == expected
    assert report["summary"]["llm_theory_ready"] is (not expected)


def test_local_diagnosis_preserves_environment_over_dotenv_without_value_leak(tmp_path, monkeypatch):
    monkeypatch.setattr("urllib.request.build_opener", _forbid_network)
    env_file = tmp_path / ".env"
    env_file.write_text("AI_STATISTICIAN_LOCAL_BASE_URL=http://unselected.invalid/v1\n")
    report = build_doctor_report(
        root=tmp_path, env_file=env_file, environ={
            "AI_STATISTICIAN_LLM_PROVIDER": "local",
            "AI_STATISTICIAN_LOCAL_BASE_URL": DEFAULT_LOCAL_BASE_URL,
        }, max_manifests=0,
    )
    assert report["summary"]["llm_theory_blockers"] == []
    assert "unselected.invalid" not in str(report)


def test_explicit_diagnosis_environment_does_not_inherit_unselected_process_url(tmp_path, monkeypatch):
    monkeypatch.setattr("urllib.request.build_opener", _forbid_network)
    monkeypatch.setenv("AI_STATISTICIAN_LOCAL_BASE_URL", "http://unselected.invalid/v1")
    report = build_doctor_report(
        root=tmp_path, environ={"AI_STATISTICIAN_LLM_PROVIDER": "local"},
        max_manifests=0,
    )
    assert report["summary"]["llm_theory_blockers"] == []
    with pytest.raises(ValueError, match="loopback"):
        LocalChatGeneratorBackend(base_url="")


@pytest.mark.parametrize("provider,key,label", [
    ("anthropic", "ANTHROPIC_API_KEY", "Anthropic key"),
    ("openai", "OPENAI_API_KEY", "OpenAI key"),
])
@pytest.mark.parametrize("present", [False, True])
def test_consolidated_optional_cloud_checks_preserve_prior_contract(
    provider, key, label, present, monkeypatch,
):
    from ai_statistician import doctor

    monkeypatch.setattr("urllib.request.build_opener", _forbid_network)
    monkeypatch.setattr(doctor, "_has_module", lambda name: present)
    env = {key: "test-only-placeholder"} if present else {}
    blockers = doctor._llm_runtime_blockers(provider=provider, env=env, dotenv_values={})
    checks = doctor._llm_provider_checks(provider, env=env, dotenv_values={})
    assert [c.name for c in checks] == [label, "optional package: " + provider]
    assert all(c.status == "OK" for c in checks) is present
    assert blockers == ([] if present else [
        key + " missing", "Python package '" + provider + "' missing; "
        "install with `python -m pip install -e '.[llm]'`",
    ])
