"""LLM provider utilities for API endpoints."""

from __future__ import annotations

from typing import Any

from loguru import logger


def make_llm_provider():
    """Create an LLM provider from the nanobot config.

    Returns:
        tuple: (provider, model_name)
    """
    from nanobot.config.loader import load_config, resolve_config_env_vars
    from nanobot.providers.base import GenerationSettings
    from nanobot.providers.registry import find_by_name

    config = resolve_config_env_vars(load_config())
    model = config.agents.defaults.model.strip()
    provider_name = config.get_provider_name(model)
    p = config.get_provider(model)
    spec = find_by_name(provider_name) if provider_name else None
    backend = spec.backend if spec else "openai_compat"

    if backend == "anthropic":
        from nanobot.providers.anthropic_provider import AnthropicProvider

        provider = AnthropicProvider(
            api_key=p.api_key if p else None,
            api_base=config.get_api_base(model),
            default_model=model,
            extra_headers=p.extra_headers if p else None,
        )
    else:
        from nanobot.providers.openai_compat_provider import OpenAICompatProvider

        provider = OpenAICompatProvider(
            api_key=p.api_key if p else None,
            api_base=config.get_api_base(model),
            default_model=model,
            extra_headers=p.extra_headers if p else None,
            spec=spec,
        )

    defaults = config.agents.defaults
    provider.generation = GenerationSettings(
        temperature=defaults.temperature,
        max_tokens=defaults.max_tokens,
        reasoning_effort=defaults.reasoning_effort,
    )
    return provider, model
