"""Backend registry + routing, including the cloud Gemini backend.

These tests never make network calls: without credentials every real backend
reports itself unavailable and (in `auto` mode) the registry falls back to the
deterministic mock backend.
"""

import pytest

from arbiter.config import Settings
from arbiter.providers import describe_backend, get_backend
from arbiter.providers.registry import _construct


def _settings(**env):
    import os

    for k, v in env.items():
        os.environ[k] = v
    try:
        return Settings()
    finally:
        for k in env:
            os.environ.pop(k, None)


@pytest.mark.parametrize("name", ["openai", "anthropic", "gemini", "ollama", "mock"])
def test_all_backends_constructible(name):
    backend = _construct(name, Settings())
    assert backend.name == name


def test_unknown_backend_rejected():
    with pytest.raises(ValueError):
        _construct("does-not-exist", Settings())


def test_gemini_default_model():
    s = Settings()
    assert s.gemini_model == "gemini-2.0-flash"
    backend = _construct("gemini", s)
    assert backend.model == "gemini-2.0-flash"


def test_gemini_unavailable_without_key_falls_back_to_mock():
    s = _settings(ARBITER_BACKEND_MODE="auto")
    # No GOOGLE_API_KEY -> gemini is unavailable -> auto falls back to mock.
    assert get_backend("gemini", s).name == "mock"
    info = describe_backend("gemini", s)
    assert info["requested"] == "gemini"
    assert info["effective"] == "mock"
    assert info["available"] is False


def test_strict_mode_errors_on_unavailable_backend():
    s = _settings(ARBITER_BACKEND_MODE="strict")
    with pytest.raises(RuntimeError):
        get_backend("gemini", s)


def test_google_api_key_accepts_either_env_name(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "abc123")
    assert Settings().google_api_key == "abc123"
