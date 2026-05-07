"""Multi-provider LLM adapter layer."""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, Dict, Any
import os
import yaml
from core.path_config import CONFIG_DIR, FIXTURES_DIR


class LLMResponse:
    """Unified response from any LLM provider."""

    def __init__(self, content: str, model: str, provider: str, usage: Dict[str, int], raw_response: Any = None):
        self.content = content
        self.model = model
        self.provider = provider
        self.usage = usage
        self.raw_response = raw_response


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        ...

    @abstractmethod
    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        ...


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude API adapter."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514", **kwargs):
        from anthropic import AsyncAnthropic
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.default_kwargs = kwargs

    async def generate(self, system_prompt, user_prompt, temperature=0.3, max_tokens=4096):
        response = await self.client.messages.create(
            model=self.model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            **self.default_kwargs,
        )
        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            provider="claude",
            usage={"tokens_in": response.usage.input_tokens, "tokens_out": response.usage.output_tokens},
            raw_response=response,
        )

    async def stream(self, system_prompt, user_prompt, temperature=0.3, max_tokens=4096):
        async with self.client.messages.stream(
            model=self.model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        ) as stream:
            async for text in stream.text_stream:
                yield text


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API adapter (supports GPT-4o, o3, and compatible endpoints)."""

    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: Optional[str] = None, **kwargs):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.default_kwargs = kwargs

    async def generate(self, system_prompt, user_prompt, temperature=0.3, max_tokens=4096):
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            **self.default_kwargs,
        )
        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            provider="openai",
            usage={"tokens_in": response.usage.prompt_tokens, "tokens_out": response.usage.completion_tokens},
            raw_response=response,
        )

    async def stream(self, system_prompt, user_prompt, temperature=0.3, max_tokens=4096):
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class MockLLMProvider(BaseLLMProvider):
    """Mock provider for testing — returns pre-crafted responses."""

    def __init__(self, fixture_dir: str = str(FIXTURES_DIR)):
        self.fixture_dir = fixture_dir

    async def generate(self, system_prompt, user_prompt, temperature=0.3, max_tokens=4096):
        import json
        fixture_path = os.path.join(self.fixture_dir, "sample_ir_simple.json")
        with open(fixture_path, encoding="utf-8") as f:
            content = f.read()
        return LLMResponse(
            content=content, model="mock", provider="mock", usage={"tokens_in": 0, "tokens_out": 0},
        )

    async def stream(self, system_prompt, user_prompt, temperature=0.3, max_tokens=4096):
        import json
        fixture_path = os.path.join(self.fixture_dir, "sample_ir_simple.json")
        with open(fixture_path, encoding="utf-8") as f:
            content = f.read()
        yield content


class LLMProviderRegistry:
    """Registry for LLM providers, loaded from YAML config."""

    def __init__(self, config_path: str | None = None):
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._default_provider: str = "claude"
        self._load_config(config_path or str(CONFIG_DIR / "llm_providers.yaml"))

    def _load_config(self, config_path: str):
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        self._default_provider = config.get("default", "claude")

        for name, prov_config in config.get("providers", {}).items():
            provider = self._create_provider(name, prov_config)
            self._providers[name] = provider

    def _create_provider(self, name: str, config: dict) -> BaseLLMProvider:
        env_key = config.get("env_key")
        api_key = config.get("api_key", "")
        if not api_key and env_key:
            api_key = os.environ.get(env_key, "")
        model = config.get("model", "")
        base_url = config.get("base_url", None)
        kwargs = config.get("kwargs", {})

        if not api_key:
            if env_key:
                raise ValueError(
                    f"Provider '{name}' has no API key configured. Add api_key to config or set {env_key} environment variable."
                )
            raise ValueError(f"Provider '{name}' has no API key configured. Add api_key to config.")

        provider_type = config.get("type", name)
        if provider_type == "anthropic" or provider_type == "claude":
            return ClaudeProvider(api_key=api_key, model=model, **kwargs)
        elif provider_type == "openai":
            return OpenAIProvider(api_key=api_key, model=model, base_url=base_url, **kwargs)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")

    def get_provider(self, name: Optional[str] = None) -> BaseLLMProvider:
        key = name or self._default_provider
        if key not in self._providers:
            raise KeyError(f"Provider '{key}' not registered")
        return self._providers[key]

    def list_providers(self) -> list:
        return list(self._providers.keys())