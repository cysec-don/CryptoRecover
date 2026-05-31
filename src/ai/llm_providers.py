"""
AI Provider Abstraction Layer for CryptoRecover.

Supports all major AI/LLM providers:
- Cloud: OpenAI, Anthropic, Google Gemini, Mistral, DeepSeek, Groq, OpenRouter, etc.
- Local: Ollama, LM Studio, llama.cpp, text-generation-webui, LocalAI, GPT4All

All providers implement a unified interface, making it easy to swap between them.
Most local providers use OpenAI-compatible APIs, so they share the same base implementation.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
import json
import asyncio


class ProviderType(Enum):
    """Type of AI provider."""
    CLOUD = "cloud"
    LOCAL = "local"
    AGGREGATOR = "aggregator"


@dataclass
class LLMMessage:
    """A message in an LLM conversation."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """Response from an LLM."""
    content: str
    model: str = ""
    provider: str = ""
    tokens_used: int = 0
    latency_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None


@dataclass
class ProviderConfig:
    """Configuration for an AI provider."""
    name: str
    provider_type: ProviderType
    base_url: str
    api_key: Optional[str] = None
    model: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 60
    supports_streaming: bool = True
    supports_function_calling: bool = False
    openai_compatible: bool = False
    extra_headers: Dict[str, str] = field(default_factory=dict)


# ============================================================
# Provider Registry - All supported providers
# ============================================================

PROVIDER_REGISTRY: Dict[str, ProviderConfig] = {
    # === Cloud Providers ===
    "openai": ProviderConfig(
        name="OpenAI",
        provider_type=ProviderType.CLOUD,
        base_url="https://api.openai.com/v1",
        api_key=None,  # User must provide
        model="gpt-4o",
        max_tokens=4096,
        temperature=0.7,
        openai_compatible=True,
        supports_function_calling=True,
    ),
    "openai-gpt4": ProviderConfig(
        name="OpenAI GPT-4",
        provider_type=ProviderType.CLOUD,
        base_url="https://api.openai.com/v1",
        api_key=None,
        model="gpt-4",
        max_tokens=4096,
        temperature=0.7,
        openai_compatible=True,
        supports_function_calling=True,
    ),
    "openai-o1": ProviderConfig(
        name="OpenAI o1",
        provider_type=ProviderType.CLOUD,
        base_url="https://api.openai.com/v1",
        api_key=None,
        model="o1",
        max_tokens=8192,
        temperature=1.0,  # o1 requires temp >= 1
        openai_compatible=True,
    ),
    "openai-o3-mini": ProviderConfig(
        name="OpenAI o3-mini",
        provider_type=ProviderType.CLOUD,
        base_url="https://api.openai.com/v1",
        api_key=None,
        model="o3-mini",
        max_tokens=8192,
        temperature=1.0,
        openai_compatible=True,
    ),
    "anthropic": ProviderConfig(
        name="Anthropic Claude",
        provider_type=ProviderType.CLOUD,
        base_url="https://api.anthropic.com/v1",
        api_key=None,
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        temperature=0.7,
        openai_compatible=False,
        extra_headers={"anthropic-version": "2023-06-01"},
    ),
    "anthropic-opus": ProviderConfig(
        name="Anthropic Claude Opus",
        provider_type=ProviderType.CLOUD,
        base_url="https://api.anthropic.com/v1",
        api_key=None,
        model="claude-opus-4-20250514",
        max_tokens=4096,
        temperature=0.7,
        openai_compatible=False,
        extra_headers={"anthropic-version": "2023-06-01"},
    ),
    "google-gemini": ProviderConfig(
        name="Google Gemini",
        provider_type=ProviderType.CLOUD,
        base_url="https://generativelanguage.googleapis.com/v1beta",
        api_key=None,
        model="gemini-2.0-flash",
        max_tokens=4096,
        temperature=0.7,
        openai_compatible=False,
    ),
    "mistral": ProviderConfig(
        name="Mistral AI",
        provider_type=ProviderType.CLOUD,
        base_url="https://api.mistral.ai/v1",
        api_key=None,
        model="mistral-large-latest",
        max_tokens=4096,
        temperature=0.7,
        openai_compatible=True,
    ),
    "deepseek": ProviderConfig(
        name="DeepSeek",
        provider_type=ProviderType.CLOUD,
        base_url="https://api.deepseek.com/v1",
        api_key=None,
        model="deepseek-chat",
        max_tokens=4096,
        temperature=0.7,
        openai_compatible=True,
    ),
    "deepseek-reasoner": ProviderConfig(
        name="DeepSeek Reasoner",
        provider_type=ProviderType.CLOUD,
        base_url="https://api.deepseek.com/v1",
        api_key=None,
        model="deepseek-reasoner",
        max_tokens=8192,
        temperature=0.7,
        openai_compatible=True,
    ),
    "groq": ProviderConfig(
        name="Groq",
        provider_type=ProviderType.CLOUD,
        base_url="https://api.groq.com/openai/v1",
        api_key=None,
        model="llama-3.3-70b-versatile",
        max_tokens=4096,
        temperature=0.7,
        openai_compatible=True,
    ),
    "openrouter": ProviderConfig(
        name="OpenRouter",
        provider_type=ProviderType.AGGREGATOR,
        base_url="https://openrouter.ai/api/v1",
        api_key=None,
        model="openai/gpt-4o",  # Default, can route to any model
        max_tokens=4096,
        temperature=0.7,
        openai_compatible=True,
        extra_headers={"HTTP-Referer": "https://cryptorecover.app"},
    ),
    "together": ProviderConfig(
        name="Together AI",
        provider_type=ProviderType.CLOUD,
        base_url="https://api.together.xyz/v1",
        api_key=None,
        model="meta-llama/Llama-3-70b-chat-hf",
        max_tokens=4096,
        temperature=0.7,
        openai_compatible=True,
    ),
    "fireworks": ProviderConfig(
        name="Fireworks AI",
        provider_type=ProviderType.CLOUD,
        base_url="https://api.fireworks.ai/inference/v1",
        api_key=None,
        model="accounts/fireworks/models/llama-v3-70b-chat",
        max_tokens=4096,
        temperature=0.7,
        openai_compatible=True,
    ),
    "perplexity": ProviderConfig(
        name="Perplexity",
        provider_type=ProviderType.CLOUD,
        base_url="https://api.perplexity.ai",
        api_key=None,
        model="sonar-pro",
        max_tokens=4096,
        temperature=0.7,
        openai_compatible=True,
    ),
    "cohere": ProviderConfig(
        name="Cohere",
        provider_type=ProviderType.CLOUD,
        base_url="https://api.cohere.ai/v1",
        api_key=None,
        model="command-r-plus",
        max_tokens=4096,
        temperature=0.7,
        openai_compatible=False,
    ),

    # === Local Providers ===
    "ollama": ProviderConfig(
        name="Ollama",
        provider_type=ProviderType.LOCAL,
        base_url="http://localhost:11434/v1",
        api_key="ollama",  # Ollama doesn't require a key
        model="llama3.1:8b",
        max_tokens=4096,
        temperature=0.7,
        openai_compatible=True,
        timeout=120,  # Local models can be slower
    ),
    "lm-studio": ProviderConfig(
        name="LM Studio",
        provider_type=ProviderType.LOCAL,
        base_url="http://localhost:1234/v1",
        api_key="lm-studio",
        model="loaded-model",  # LM Studio uses whatever model is loaded
        max_tokens=4096,
        temperature=0.7,
        openai_compatible=True,
        timeout=120,
    ),
    "llama-cpp": ProviderConfig(
        name="llama.cpp Server",
        provider_type=ProviderType.LOCAL,
        base_url="http://localhost:8080/v1",
        api_key="llama-cpp",
        model="loaded-model",
        max_tokens=4096,
        temperature=0.7,
        openai_compatible=True,
        timeout=120,
    ),
    "localai": ProviderConfig(
        name="LocalAI",
        provider_type=ProviderType.LOCAL,
        base_url="http://localhost:8080/v1",
        api_key="localai",
        model="llama3",
        max_tokens=4096,
        temperature=0.7,
        openai_compatible=True,
        timeout=120,
    ),
    "text-gen-webui": ProviderConfig(
        name="text-generation-webui",
        provider_type=ProviderType.LOCAL,
        base_url="http://localhost:5000/v1",
        api_key="text-gen",
        model="loaded-model",
        max_tokens=4096,
        temperature=0.7,
        openai_compatible=True,
        timeout=120,
    ),
    "koboldcpp": ProviderConfig(
        name="KoboldCpp",
        provider_type=ProviderType.LOCAL,
        base_url="http://localhost:5001/v1",
        api_key="kobold",
        model="loaded-model",
        max_tokens=4096,
        temperature=0.7,
        openai_compatible=True,
        timeout=120,
    ),
    "gpt4all": ProviderConfig(
        name="GPT4All",
        provider_type=ProviderType.LOCAL,
        base_url="http://localhost:4891/v1",
        api_key="gpt4all",
        model="loaded-model",
        max_tokens=4096,
        temperature=0.7,
        openai_compatible=True,
        timeout=120,
    ),
}


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self._client = None

    @abstractmethod
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Send a chat request and get a response."""
        pass

    @abstractmethod
    async def list_models(self) -> List[str]:
        """List available models from this provider."""
        pass

    async def health_check(self) -> bool:
        """Check if the provider is accessible."""
        try:
            models = await self.list_models()
            return len(models) > 0  # Must have at least one model available
        except Exception:
            return False

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        headers.update(self.config.extra_headers)
        return headers


class OpenAICompatibleProvider(BaseLLMProvider):
    """
    Provider implementation for OpenAI-compatible APIs.
    This covers: OpenAI, Mistral, DeepSeek, Groq, OpenRouter, Together AI,
    Fireworks AI, Perplexity, Ollama, LM Studio, llama.cpp, LocalAI,
    text-generation-webui, KoboldCpp, GPT4All.
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Send a chat request using OpenAI-compatible API."""
        import httpx
        import time

        url = f"{self.config.base_url}/chat/completions"
        headers = self._get_headers()

        payload = {
            "model": kwargs.get("model", self.config.model),
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
        }

        if "stream" in kwargs:
            payload["stream"] = kwargs["stream"]

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)

            latency = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                tokens_used = data.get("usage", {}).get("total_tokens", 0)
                model = data.get("model", self.config.model)

                return LLMResponse(
                    content=content,
                    model=model,
                    provider=self.config.name,
                    tokens_used=tokens_used,
                    latency_ms=latency,
                    success=True,
                )
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:500]}"
                return LLMResponse(
                    content="",
                    provider=self.config.name,
                    success=False,
                    error=error_msg,
                    latency_ms=latency,
                )
        except Exception as e:
            return LLMResponse(
                content="",
                provider=self.config.name,
                success=False,
                error=str(e),
            )

    async def list_models(self) -> List[str]:
        """List models from the provider."""
        import httpx

        url = f"{self.config.base_url}/models"
        headers = self._get_headers()

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    return [m.get("id", m.get("name", "")) for m in data["data"]]
            return []
        except Exception:
            return []


class AnthropicProvider(BaseLLMProvider):
    """Provider implementation for Anthropic Claude API."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Send a chat request using Anthropic API."""
        import httpx
        import time

        url = f"{self.config.base_url}/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.config.api_key or "",
            "anthropic-version": "2023-06-01",
        }

        # Separate system message
        system_content = ""
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system_content = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        payload = {
            "model": kwargs.get("model", self.config.model),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "messages": chat_messages,
        }
        if system_content:
            payload["system"] = system_content

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)

            latency = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                content = data["content"][0]["text"]
                tokens_used = data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0)

                return LLMResponse(
                    content=content,
                    model=self.config.model,
                    provider=self.config.name,
                    tokens_used=tokens_used,
                    latency_ms=latency,
                    success=True,
                )
            else:
                return LLMResponse(
                    content="",
                    provider=self.config.name,
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text[:500]}",
                    latency_ms=latency,
                )
        except Exception as e:
            return LLMResponse(
                content="",
                provider=self.config.name,
                success=False,
                error=str(e),
            )

    async def list_models(self) -> List[str]:
        """Anthropic doesn't have a public model listing endpoint."""
        return [
            "claude-sonnet-4-20250514",
            "claude-opus-4-20250514",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
        ]


class GoogleGeminiProvider(BaseLLMProvider):
    """Provider implementation for Google Gemini API."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Send a chat request using Google Gemini API."""
        import httpx
        import time

        model = kwargs.get("model", self.config.model)
        url = f"{self.config.base_url}/models/{model}:generateContent"

        # Use header-based auth instead of URL parameter for security
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.config.api_key or "",
        }

        # Convert messages to Gemini format
        contents = []
        for m in messages:
            role = "user" if m.role in ("user", "system") else "model"
            contents.append({
                "role": role,
                "parts": [{"text": m.content}]
            })

        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
            }
        }

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)

            latency = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                return LLMResponse(
                    content=content,
                    model=model,
                    provider=self.config.name,
                    latency_ms=latency,
                    success=True,
                )
            else:
                return LLMResponse(
                    content="",
                    provider=self.config.name,
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text[:500]}",
                    latency_ms=latency,
                )
        except Exception as e:
            return LLMResponse(
                content="",
                provider=self.config.name,
                success=False,
                error=str(e),
            )

    async def list_models(self) -> List[str]:
        """List available Gemini models."""
        return [
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]


class CohereProvider(BaseLLMProvider):
    """Provider implementation for Cohere API."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Send a chat request using Cohere API."""
        import httpx
        import time

        url = f"{self.config.base_url}/chat"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }

        # Cohere uses a different message format
        system_content = None
        chat_history = []
        last_message = ""
        for m in messages:
            if m.role == "system":
                system_content = m.content  # Pass as system_prompt param
            elif m.role == "user":
                last_message = m.content
            elif m.role == "assistant":
                chat_history.append({"role": "CHATBOT", "message": m.content})

        payload = {
            "model": kwargs.get("model", self.config.model),
            "message": last_message,
            "chat_history": chat_history,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
        }
        if system_content:
            payload["preamble"] = system_content

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)

            latency = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                content = data.get("text", "")
                return LLMResponse(
                    content=content,
                    model=self.config.model,
                    provider=self.config.name,
                    latency_ms=latency,
                    success=True,
                )
            else:
                return LLMResponse(
                    content="",
                    provider=self.config.name,
                    success=False,
                    error=f"HTTP {response.status_code}",
                    latency_ms=latency,
                )
        except Exception as e:
            return LLMResponse(
                content="",
                provider=self.config.name,
                success=False,
                error=str(e),
            )

    async def list_models(self) -> List[str]:
        return ["command-r-plus", "command-r", "command-light"]


class LLMProviderFactory:
    """Factory for creating LLM provider instances."""

    _providers: Dict[str, type] = {
        # OpenAI-compatible providers
        "openai": OpenAICompatibleProvider,
        "openai-gpt4": OpenAICompatibleProvider,
        "openai-o1": OpenAICompatibleProvider,
        "openai-o3-mini": OpenAICompatibleProvider,
        "mistral": OpenAICompatibleProvider,
        "deepseek": OpenAICompatibleProvider,
        "deepseek-reasoner": OpenAICompatibleProvider,
        "groq": OpenAICompatibleProvider,
        "openrouter": OpenAICompatibleProvider,
        "together": OpenAICompatibleProvider,
        "fireworks": OpenAICompatibleProvider,
        "perplexity": OpenAICompatibleProvider,
        # Local providers (all OpenAI-compatible)
        "ollama": OpenAICompatibleProvider,
        "lm-studio": OpenAICompatibleProvider,
        "llama-cpp": OpenAICompatibleProvider,
        "localai": OpenAICompatibleProvider,
        "text-gen-webui": OpenAICompatibleProvider,
        "koboldcpp": OpenAICompatibleProvider,
        "gpt4all": OpenAICompatibleProvider,
        # Custom API providers
        "anthropic": AnthropicProvider,
        "anthropic-opus": AnthropicProvider,
        "google-gemini": GoogleGeminiProvider,
        "cohere": CohereProvider,
    }

    @classmethod
    def create(cls, provider_id: str, **overrides) -> BaseLLMProvider:
        """Create a provider instance by ID."""
        if provider_id not in cls._providers:
            raise ValueError(
                f"Unknown provider: {provider_id}. "
                f"Available: {list(cls._providers.keys())}"
            )

        config = PROVIDER_REGISTRY[provider_id]

        # Deep-copy to avoid mutating the global registry (Bug C1 fix)
        import copy
        config = copy.deepcopy(config)

        # Apply overrides
        for key, value in overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)

        provider_class = cls._providers[provider_id]
        return provider_class(config)

    @classmethod
    def list_providers(cls) -> List[Dict[str, str]]:
        """List all available providers with their details."""
        result = []
        for pid, config in PROVIDER_REGISTRY.items():
            result.append({
                "id": pid,
                "name": config.name,
                "type": config.provider_type.value,
                "base_url": config.base_url,
                "default_model": config.model,
                "requires_api_key": config.api_key is None and config.provider_type == ProviderType.CLOUD,
                "openai_compatible": config.openai_compatible,
            })
        return result

    @classmethod
    def get_provider_configs_by_type(cls, provider_type: ProviderType) -> List[Dict]:
        """Get all providers of a specific type."""
        return [
            info
            for info in cls.list_providers()
            if info["type"] == provider_type.value
        ]

    @classmethod
    def detect_local_providers(cls) -> Dict[str, bool]:
        """
        Auto-detect which local providers are running.
        Checks common ports for local LLM servers.
        """
        import httpx
        import asyncio

        local_providers = {
            "ollama": "http://localhost:11434/v1/models",
            "lm-studio": "http://localhost:1234/v1/models",
            "llama-cpp": "http://localhost:8080/v1/models",
            "localai": "http://localhost:8080/v1/models",
            "text-gen-webui": "http://localhost:5000/v1/models",
            "koboldcpp": "http://localhost:5001/v1/models",
            "gpt4all": "http://localhost:4891/v1/models",
        }

        results = {}

        async def check(name: str, url: str):
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.get(url)
                    results[name] = resp.status_code == 200
            except Exception:
                results[name] = False

        async def check_all():
            tasks = [check(name, url) for name, url in local_providers.items()]
            await asyncio.gather(*tasks)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in an async context, create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    pool.submit(lambda: asyncio.run(check_all())).result()
            else:
                loop.run_until_complete(check_all())
        except RuntimeError:
            asyncio.run(check_all())

        return results
