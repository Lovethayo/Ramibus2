export const SUPPORTED_PROVIDERS = [
  { id: 'local_gguf', label: 'llama.cpp / GGUF', kind: 'local' },
  { id: 'lmstudio', label: 'LM Studio', kind: 'local' },
  { id: 'openai', label: 'OpenAI API', kind: 'api' },
  { id: 'anthropic', label: 'Anthropic API', kind: 'api' },
  { id: 'openrouter', label: 'OpenRouter API', kind: 'api' },
]

export const REMOTE_PROVIDER_IDS = new Set(['openai', 'anthropic', 'openrouter'])
export const DEFAULT_PROVIDER = 'local_gguf'

export function normalizeProviders(list = []) {
  const valid = new Set(SUPPORTED_PROVIDERS.map((provider) => provider.id))
  return list
    .map((provider) => (typeof provider === 'string' ? { id: provider } : provider))
    .filter((provider) => valid.has(provider.id || provider.name))
    .map((provider) => {
      const id = provider.id || provider.name
      const definition = SUPPORTED_PROVIDERS.find((item) => item.id === id)
      return { ...provider, id, label: definition.label, kind: definition.kind }
    })
}

export function resolveProvider(candidate, available = []) {
  const normalized = normalizeProviders(available)
  if (normalized.some((provider) => provider.id === candidate)) return candidate
  if (normalized.some((provider) => provider.id === DEFAULT_PROVIDER)) return DEFAULT_PROVIDER
  return normalized[0]?.id || DEFAULT_PROVIDER
}

export function providerSettingsPayload(settings = {}) {
  return {
    ai: {
      active_provider: settings.ai_provider || DEFAULT_PROVIDER,
      fallback_provider: settings.fallback_provider || 'lmstudio',
      allow_remote_apis: settings.allow_remote_apis !== false,
    },
    local_gguf: {
      host: settings.local_gguf_host || '127.0.0.1',
      port: Number(settings.local_gguf_port || 8080),
      planner_model: settings.local_gguf_planner_model || 'rami-planner',
      tradecraft_model: settings.local_gguf_tradecraft_model || 'rami-tradecraft',
    },
    lmstudio: { base_url: settings.lmstudio_base_url || 'http://localhost:1234/v1' },
    openai: {
      api_key: settings.openai_api_key || '',
      oauth_token: settings.openai_oauth_token || '',
      base_url: settings.openai_base_url || 'https://api.openai.com/v1',
    },
    anthropic: {
      api_key: settings.anthropic_api_key || '',
      oauth_token: settings.anthropic_oauth_token || '',
    },
    openrouter: {
      api_key: settings.openrouter_api_key || '',
      base_url: settings.openrouter_base_url || 'https://openrouter.ai/api/v1',
    },
    docker: { container: settings.docker_container || 'rami-kali' },
  }
}
