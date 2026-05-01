import json

from statlean_agent.axle import AxleClient, AxleError


class _FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_axle_transform_code_uses_official_payload_shape(monkeypatch) -> None:
    captured: dict = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse({"okay": True, "lean_messages": {"errors": [], "warnings": [], "infos": []}})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = AxleClient(base_url="https://example.test", api_key="secret", timeout_seconds=9)

    payload = client.transform_code(
        "check",
        "theorem probe : True := by trivial",
        env="lean-4.29.0",
        ignore_imports=True,
        timeout_seconds=3,
    )

    assert payload["okay"] is True
    assert captured["url"] == "https://example.test/api/v1/check"
    assert captured["headers"]["Authorization"] == "Bearer secret"
    assert captured["headers"]["X-request-source"] == "statlean-agent"
    assert captured["timeout"] == 9
    assert captured["payload"] == {
        "content": "theorem probe : True := by trivial",
        "environment": "lean-4.29.0",
        "ignore_imports": True,
        "timeout_seconds": 3,
    }


def test_axle_rejects_user_error_payload(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        return _FakeResponse({"user_error": "bad Lean source"})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = AxleClient(base_url="https://example.test")

    try:
        client.transform_code("check", "broken")
    except AxleError as error:
        assert "bad Lean source" in str(error)
    else:
        raise AssertionError("expected AxleError")
