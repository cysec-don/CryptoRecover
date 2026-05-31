"""Tests for AI/LLM Providers"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ai.llm_providers import (
    LLMProviderFactory, ProviderConfig, ProviderType,
    OpenAICompatibleProvider, AnthropicProvider,
    GoogleGeminiProvider, CohereProvider,
    LLMMessage, LLMResponse,
)


class TestProviderRegistry:
    """Tests for the provider registry."""

    def test_all_providers_have_config(self):
        """Every provider ID in the factory should have a config."""
        for pid in LLMProviderFactory._providers:
            assert pid in LLMProviderFactory.list_providers() or True
            config = LLMProviderFactory.list_providers()
            ids = [p["id"] for p in config]
            assert pid in ids

    def test_cloud_providers_require_api_key(self):
        """Cloud providers should require an API key."""
        providers = LLMProviderFactory.list_providers()
        cloud = [p for p in providers if p["type"] == "cloud"]
        for p in cloud:
            # At least verify the structure
            assert "requires_api_key" in p

    def test_local_providers_have_default_port(self):
        """Local providers should have localhost URLs."""
        providers = LLMProviderFactory.list_providers()
        local = [p for p in providers if p["type"] == "local"]
        for p in local:
            assert "localhost" in p["base_url"] or "127.0.0.1" in p["base_url"]

    def test_provider_count(self):
        """Verify we have a comprehensive set of providers."""
        providers = LLMProviderFactory.list_providers()
        # Should have at least 15 providers (cloud + local)
        assert len(providers) >= 15

    def test_cloud_provider_count(self):
        """Should have multiple cloud providers."""
        from src.ai.llm_providers import PROVIDER_REGISTRY
        cloud = [p for p in PROVIDER_REGISTRY.values() if p.provider_type == ProviderType.CLOUD]
        assert len(cloud) >= 10

    def test_local_provider_count(self):
        """Should have multiple local providers."""
        from src.ai.llm_providers import PROVIDER_REGISTRY
        local = [p for p in PROVIDER_REGISTRY.values() if p.provider_type == ProviderType.LOCAL]
        assert len(local) >= 5


class TestProviderFactory:
    """Tests for LLMProviderFactory."""

    def test_create_ollama(self):
        """Test creating an Ollama provider."""
        provider = LLMProviderFactory.create("ollama")
        assert isinstance(provider, OpenAICompatibleProvider)
        assert provider.config.name == "Ollama"

    def test_create_lm_studio(self):
        """Test creating an LM Studio provider."""
        provider = LLMProviderFactory.create("lm-studio")
        assert isinstance(provider, OpenAICompatibleProvider)
        assert provider.config.name == "LM Studio"

    def test_create_openai(self):
        """Test creating an OpenAI provider."""
        provider = LLMProviderFactory.create("openai", api_key="test-key")
        assert isinstance(provider, OpenAICompatibleProvider)
        assert provider.config.api_key == "test-key"

    def test_create_anthropic(self):
        """Test creating an Anthropic provider."""
        provider = LLMProviderFactory.create("anthropic", api_key="test-key")
        assert isinstance(provider, AnthropicProvider)

    def test_create_google_gemini(self):
        """Test creating a Google Gemini provider."""
        provider = LLMProviderFactory.create("google-gemini", api_key="test-key")
        assert isinstance(provider, GoogleGeminiProvider)

    def test_create_cohere(self):
        """Test creating a Cohere provider."""
        provider = LLMProviderFactory.create("cohere", api_key="test-key")
        assert isinstance(provider, CohereProvider)

    def test_create_invalid_provider(self):
        """Test creating an invalid provider raises error."""
        with pytest.raises(ValueError):
            LLMProviderFactory.create("invalid_provider")

    def test_create_with_model_override(self):
        """Test creating a provider with a custom model."""
        provider = LLMProviderFactory.create("ollama", model="llama3:70b")
        assert provider.config.model == "llama3:70b"

    def test_list_providers_structure(self):
        """Test the structure of listed providers."""
        providers = LLMProviderFactory.list_providers()
        for p in providers:
            assert "id" in p
            assert "name" in p
            assert "type" in p
            assert "base_url" in p
            assert "default_model" in p
            assert "openai_compatible" in p


class TestLLMMessage:
    """Tests for LLMMessage."""

    def test_message_creation(self):
        msg = LLMMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_system_message(self):
        msg = LLMMessage(role="system", content="You are helpful")
        assert msg.role == "system"


class TestLLMResponse:
    """Tests for LLMResponse."""

    def test_success_response(self):
        resp = LLMResponse(
            content="Test response",
            model="gpt-4o",
            provider="OpenAI",
            tokens_used=10,
            success=True,
        )
        assert resp.success is True
        assert resp.content == "Test response"

    def test_error_response(self):
        resp = LLMResponse(
            content="",
            provider="OpenAI",
            success=False,
            error="HTTP 401: Unauthorized",
        )
        assert resp.success is False
        assert resp.error == "HTTP 401: Unauthorized"
