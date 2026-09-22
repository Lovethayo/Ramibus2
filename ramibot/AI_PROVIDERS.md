# RAMIBUS AI providers

RAMIBUS intentionally has three provider paths:

1. **llama.cpp / GGUF** (`local_gguf`) — local, keyless, private model execution.
2. **LM Studio** (`lmstudio`) — local OpenAI-compatible server, keyless by default.
3. **Configured AI APIs** — OpenAI, Anthropic, and OpenRouter; credentials are entered in the RAMIBUS Settings UI and never required for local operation.

The UI must show the active provider and whether it is local or remote. Remote APIs are opt-in. If no remote API key is configured, the user can still use llama.cpp or LM Studio.

The existing API-key panel already covers OpenAI, Anthropic, and OpenRouter. The provider setup should add:

- llama.cpp model path, binary, host, port, context size, and GPU layers;
- LM Studio base URL;
- an active-provider selector;
- a remote API opt-in indicator;
- connection tests that never print secrets.

No provider should be installed, started, or contacted silently. A local provider may be unavailable while RAMIBUS remains usable through a configured remote API, and vice versa.
