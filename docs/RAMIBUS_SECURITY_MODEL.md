# RAMIBUS security and capability boundary

## Product naming

The user-facing configuration namespace is **RAMIBUS Tradecraft**. It replaces the old OSIRIS-specific settings label and is the home for intelligence sources and future capabilities such as aviation, CCTV, phone intelligence, sanctions, weather, satellites, scanners, and other registered tools.

Capabilities must be registered with a stable name, category, provider, required permissions, data-source policy, risk level, and health check. Installing a new tool must update the registry and produce an audit event; a model must not silently add arbitrary tools to the active tool list.

## Privilege policy

RAMIBUS must not give an agent unrestricted host `sudo` or root access. That would make prompt injection, a compromised provider, or a malicious tool equivalent to full host compromise. Instead:

1. Normal planning and read-only public-feed work runs unprivileged.
2. Tool installation and privileged actions run through a dedicated execution gateway or isolated `rami-kali` container.
3. The gateway validates the requested package, source, target, capability, and risk level.
4. The operator sees the exact command, requested permissions, target, network access, and rollback information.
5. High/critical actions require explicit approval and expire if not approved.
6. Installation and execution are logged with request ID, tool version, source, actor, approval, result, and hashes where available.
7. The agent cannot approve its own request, widen scope, change the policy, or hide the audit record.

If a workflow genuinely needs root—for example packet capture, Wireshark dependencies, or network tooling—give only the isolated container or a narrowly scoped helper the required capability. Do not expose the host filesystem, host credentials, or unrestricted host network by default.

## Network and search routing

“Never hit Google” is implemented as an egress policy, not as a model promise:

- Default `egress_mode` is `configured_only`.
- Search requests route through the configured private SearXNG endpoint.
- Tor is optional and must be explicitly configured and approved for the relevant capability.
- Direct search-provider domains are denied unless the operator adds them to an allowlist.
- Public APIs and data feeds remain separate, visible providers; they are not silently represented as private search.
- The UI must show the route used, source, timestamp, and whether the response was direct, SearXNG, or Tor-routed.
- Network denial is fail-closed for active tradecraft tools and fail-visible for optional intelligence feeds.

No system can truthfully guarantee that an external provider never receives data if that provider is enabled. RAMIBUS should therefore expose an explicit provider/egress inventory and require approval before enabling a new external destination.

## Environment-specific public URLs

- Replit: do not install or start ngrok; use the platform URL and report its limitations.
- Colab: ngrok is optional, secret-backed, and opt-in. Never print the auth token. Public exposure requires a warning and approval.
- Local/VPS/cloud: ngrok is optional; prefer an authenticated reverse proxy and TLS for persistent deployments.

Every public URL must be visible in the UI, associated with an audit event, and revocable from the control plane.

## Capability registration contract

A future self-installing tool flow should be:

```text
request -> classify capability -> check source/license -> propose package and permissions
        -> operator approval -> isolated install -> health check
        -> registry update -> audit event -> tool availability
```

The registry should reject missing metadata, untrusted install sources, duplicate names, and capabilities without a risk/permission declaration. A failed install must not become an active tool.
