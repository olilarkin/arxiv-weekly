import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import pytest
from openai import APIError

from model_utils import (
    RequestBudget,
    RequestLimitExceeded,
    build_chat_kwargs,
    build_token_kwargs,
    get_ai_config,
    get_api_key,
    get_request_budget,
    has_api_key,
    supports_custom_temperature,
)

SETTINGS = {
    "ai": {"provider": "gemini"},
    "gemini": {
        "api_key_env": "GEMINI_API_KEY",
        "endpoint": "https://example.invalid/openai/",
        "model": "gemini-3.5-flash",
    },
    "github_models": {
        "api_key_env": "GITHUB_TOKEN",
        "endpoint": "https://models.github.ai/inference",
        "model": "openai/gpt-4o",
    },
}


class TestSupportsCustomTemperature:
    def test_gpt4o_supports_temperature(self):
        assert supports_custom_temperature("gpt-4o") is True

    def test_gpt4o_mini_supports_temperature(self):
        assert supports_custom_temperature("gpt-4o-mini") is True

    def test_gpt5_does_not_support_temperature(self):
        assert supports_custom_temperature("gpt-5") is False

    def test_gpt5_turbo_does_not_support_temperature(self):
        assert supports_custom_temperature("gpt-5-turbo") is False

    def test_o1_supports_temperature(self):
        # o1 does not start with gpt-5, so supports temperature
        assert supports_custom_temperature("o1") is True


class TestBuildTokenKwargs:
    def test_gpt4o_uses_max_tokens(self):
        result = build_token_kwargs("gpt-4o", 1000)
        assert result == {"max_tokens": 1000}

    def test_gpt5_uses_max_completion_tokens(self):
        result = build_token_kwargs("gpt-5", 500)
        assert result == {"max_completion_tokens": 500}

    def test_o1_uses_max_completion_tokens(self):
        result = build_token_kwargs("o1", 200)
        assert result == {"max_completion_tokens": 200}

    def test_o3_uses_max_completion_tokens(self):
        result = build_token_kwargs("o3", 100)
        assert result == {"max_completion_tokens": 100}

    def test_o4_uses_max_completion_tokens(self):
        result = build_token_kwargs("o4", 300)
        assert result == {"max_completion_tokens": 300}


class TestBuildChatKwargs:
    def test_gpt4o_with_temperature(self):
        result = build_chat_kwargs("gpt-4o", 1000, temperature=0.3)
        assert result == {"max_tokens": 1000, "temperature": 0.3}

    def test_gpt4o_without_temperature(self):
        result = build_chat_kwargs("gpt-4o", 1000)
        assert result == {"max_tokens": 1000}
        assert "temperature" not in result

    def test_gpt5_ignores_temperature(self):
        result = build_chat_kwargs("gpt-5", 500, temperature=0.5)
        assert result == {
            "max_completion_tokens": 500,
            "reasoning_effort": "minimal",
        }
        assert "temperature" not in result

    def test_temperature_none_is_excluded(self):
        result = build_chat_kwargs("gpt-4o", 800, temperature=None)
        assert "temperature" not in result


class TestNamespacedModelNames:
    """GitHub Models and Gemini both use publisher/model style identifiers."""

    def test_namespaced_gpt4o_uses_max_tokens(self):
        assert build_token_kwargs("openai/gpt-4o", 1000) == {"max_tokens": 1000}

    def test_namespaced_gpt5_uses_max_completion_tokens(self):
        assert build_token_kwargs("openai/gpt-5", 500) == {
            "max_completion_tokens": 500
        }

    def test_namespaced_gpt5_ignores_temperature(self):
        assert supports_custom_temperature("openai/gpt-5") is False


class TestGeminiModels:
    def test_gemini3_does_not_support_temperature(self):
        assert supports_custom_temperature("gemini-3.5-flash") is False

    def test_gemini3_uses_max_tokens(self):
        assert build_token_kwargs("gemini-3.5-flash", 16000) == {"max_tokens": 16000}

    def test_gemini3_defaults_to_medium_reasoning_effort(self):
        result = build_chat_kwargs("gemini-3.5-flash", 16000, temperature=0.3)
        assert result == {"max_tokens": 16000, "reasoning_effort": "medium"}

    def test_gemini3_reasoning_effort_override(self):
        result = build_chat_kwargs("gemini-3.5-flash", 100, reasoning_effort="low")
        assert result["reasoning_effort"] == "low"


class TestRequestBudget:
    def test_allows_requests_up_to_the_limit(self):
        budget = RequestBudget("p", 3)
        for _ in range(3):
            budget.consume()
        assert budget.used == 3

    def test_raises_once_the_limit_is_spent(self):
        budget = RequestBudget("p", 1)
        budget.consume()
        with pytest.raises(RequestLimitExceeded):
            budget.consume()

    def test_is_not_an_api_error(self):
        # analyze_batch retries APIError; budget exhaustion must not be
        # retried, since retrying can never replenish the budget.
        assert not isinstance(RequestLimitExceeded("x"), APIError)

    def test_limit_is_at_least_one(self):
        assert RequestBudget("p", 0).limit == 1

    def test_same_provider_and_limit_share_one_budget(self):
        first = get_request_budget("shared", 5)
        first.consume()
        assert get_request_budget("shared", 5) is first
        assert get_request_budget("shared", 5).used == 1


class TestGetAiConfig:
    def test_returns_provider_selected_in_settings(self):
        provider, cfg = get_ai_config(SETTINGS)
        assert provider == "gemini"
        assert cfg["model"] == "gemini-3.5-flash"

    def test_explicit_provider_overrides_settings(self):
        provider, cfg = get_ai_config(SETTINGS, provider="github_models")
        assert provider == "github_models"
        assert cfg["model"] == "openai/gpt-4o"

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError):
            get_ai_config(SETTINGS, provider="nope")

    def test_missing_ai_block_raises(self):
        with pytest.raises(ValueError):
            get_ai_config({"gemini": SETTINGS["gemini"]})


class TestApiKeyResolution:
    def test_reads_key_from_configured_env_var(self):
        key = get_api_key("gemini", SETTINGS["gemini"], {"GEMINI_API_KEY": "abc"})
        assert key == "abc"

    def test_missing_key_raises(self):
        with pytest.raises(EnvironmentError):
            get_api_key("gemini", SETTINGS["gemini"], {})

    def test_wrong_env_var_does_not_satisfy_provider(self):
        # A leftover GITHUB_TOKEN must not be mistaken for a Gemini key.
        assert has_api_key(SETTINGS, {"GITHUB_TOKEN": "ghp_x"}) is False

    def test_has_api_key_true_when_present(self):
        assert has_api_key(SETTINGS, {"GEMINI_API_KEY": "abc"}) is True
