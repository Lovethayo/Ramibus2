from __future__ import annotations

SUPPORTED_PROVIDERS = {
    'local_gguf': {'label': 'llama.cpp / GGUF', 'kind': 'local'},
    'lmstudio': {'label': 'LM Studio', 'kind': 'local'},
    'openai': {'label': 'OpenAI API', 'kind': 'api'},
    'anthropic': {'label': 'Anthropic API', 'kind': 'api'},
    'openrouter': {'label': 'OpenRouter API', 'kind': 'api'},
}
DEFAULT_PROVIDER = 'local_gguf'
REMOTE_PROVIDERS = {'openai', 'anthropic', 'openrouter'}


def normalize_provider(provider: str | None) -> str:
    value = (provider or '').strip().lower()
    if value not in SUPPORTED_PROVIDERS:
        raise ValueError(f'Unsupported AI provider: {provider}')
    return value


def select_provider(provider: str | None, *, allow_remote_apis: bool = True) -> str:
    value = normalize_provider(provider or DEFAULT_PROVIDER)
    if value in REMOTE_PROVIDERS and not allow_remote_apis:
        raise ValueError(f'Remote AI providers are disabled: {value}')
    return value


def provider_payload(settings: dict) -> dict:
    active = select_provider(settings.get('ai', {}).get('active_provider', DEFAULT_PROVIDER), allow_remote_apis=bool(settings.get('ai', {}).get('allow_remote_apis', True)))
    return {'active_provider': active, 'supported': list(SUPPORTED_PROVIDERS), 'remote_enabled': active in REMOTE_PROVIDERS}
