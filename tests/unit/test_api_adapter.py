"""Unit tests for the ApiModelAdapter and credentials auto-detection."""
import pytest
from devo.model.api import detect_api_credentials


def test_detect_groq_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DEVO_API_KEY", raising=False)

    monkeypatch.setenv("GROQ_API_KEY_1", "gsk_test12345")
    key, endpoint, model = detect_api_credentials()
    assert key == "gsk_test12345"
    assert "groq.com" in endpoint
    assert "qwen" in model


def test_detect_gemini_key(monkeypatch):
    for k in ["GROQ_API_KEY", "GROQ_API_KEY_1", "GROQ_API_KEY_2", "GROQ_API_KEY_3", "GROQ_API_KEY_4"]:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DEVO_API_KEY", raising=False)

    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTest12345")
    key, endpoint, model = detect_api_credentials()
    assert key == "AIzaSyTest12345"
    assert "googleapis.com" in endpoint
    assert "gemini" in model


def test_detect_openai_key(monkeypatch):
    for k in ["GROQ_API_KEY", "GROQ_API_KEY_1", "GROQ_API_KEY_2", "GROQ_API_KEY_3", "GROQ_API_KEY_4", "GEMINI_API_KEY"]:
        monkeypatch.delenv(k, raising=False)

    monkeypatch.setenv("OPENAI_API_KEY", "sk-proj-test123")
    key, endpoint, model = detect_api_credentials()
    assert key == "sk-proj-test123"
    assert "openai.com" in endpoint
    assert model == "gpt-4o-mini"


def test_detect_no_keys_raises(monkeypatch):
    for k in ["GROQ_API_KEY", "GROQ_API_KEY_1", "GROQ_API_KEY_2", "GROQ_API_KEY_3", "GROQ_API_KEY_4", "GEMINI_API_KEY", "OPENAI_API_KEY", "DEVO_API_KEY"]:
        monkeypatch.delenv(k, raising=False)

    with pytest.raises(ValueError, match="No API key found"):
        detect_api_credentials()
