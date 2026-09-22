"""Supported RAMIBUS AI provider contract.

RAMIBUS supports local llama.cpp/ GGUF, LM Studio, and configured remote AI APIs.
Provider selection never installs or contacts a provider implicitly.
"""

SUPPORTED_PROVIDER_GROUPS = {
    "local_llama_cpp": {"local_gguf"},
    "lm_studio": {"lmstudio"},
    "remote_api": {"openai", "anthropic", "openrouter"},
}


def provider_group(provider: str) -> str | None:
    for group, names in SUPPORTED_PROVIDER_GROUPS.items():
        if provider in names:
            return group
    return None


def is_supported_provider(provider: str) -> bool:
    return provider_group(provider) is not None


def public_provider_inventory() -> list[dict]:
    return [
        {
            "id": "local_gguf",
            "group": "local_llama_cpp",
            "label": "llama.cpp / GGUF",
            "requires_api_key": False,
            "requires_local_runtime": True,
        },
        {
            "id": "lmstudio",
            "group": "lm_studio",
            "label": "LM Studio",
            "requires_api_key": False,
            "requires_local_runtime": True,
        },
        {
            "id": "openai",
            "group": "remote_api",
            "label": "OpenAI API",
            "requires_api_key": True,
            "requires_local_runtime": False,
        },
        {
            "id": "anthropic",
            "group": "remote_api",
            "label": "Anthropic API",
            "requires_api_key": True,
            "requires_local_runtime": False,
        },
        {
            "id": "openrouter",
            "group": "remote_api",
            "label": "OpenRouter API",
            "requires_api_key": True,
            "requires_local_runtime": False,
        },
    ]
