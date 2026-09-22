# RAMIBUS Consolidation Roadmap

> **Target:** make `ramibot/` the single product surface for RAMIBUS by absorbing the useful capabilities from `osiris/` and `OMNIBUS/`, while removing dead or duplicate code only after migration and smoke-test gates pass.
>
> **Guiding principle:** capability expansion must not weaken operator control. RAMIBUS may reason, discover, plan, and prepare actions autonomously, but actions that cross a configured security boundary require explicit human approval and produce an immutable audit record.

## Product direction

RAMIBUS will be a general-purpose, local-first AI workspace with specialist operating lanes:

- **General assistant:** normal conversation, writing, teaching, research, planning, and day-to-day professional work.
- **OSINT/world intelligence:** maps, aviation, maritime, CCTV, earthquakes, fires, weather, satellites, news, conflict, Telegram, sanctions, and crypto intelligence from OSIRIS.
- **Cybersecurity operations:** recon, analysis, defense, reporting, MCP tools, Docker terminal, findings, and evidence-locked reports from the existing RamiBot platform.
- **Agent runtime:** capability discovery, provider adapters, registry-driven tools, policy evaluation, execution profiles, persistence, and orchestration from OMNIBUS.
- **Multi-agent routing:** planner, tradecraft, evidence, world, defense, tooling, and review lanes using the existing deterministic routing contract in `ramibot/backend/agent_roster.py`.

The product should present these as one RAMIBUS application, not three loosely connected projects.

## Non-negotiable safety model

### Authorized means

The operator explicitly configures:

- allowed target CIDRs, domains, URLs, workspaces, and data sources;
- enabled providers, MCP servers, Spaces, and external integrations;
- permitted capabilities and execution backends;
- the maximum risk level that may run without approval;
- whether network, filesystem, Docker, shell, browser, or public-sharing actions are allowed.

The default posture is deny-by-default for external execution and public exposure. Read-only public feeds may be enabled separately from active scanning or command execution.

### Human gate

An agent may classify a request and propose an action, but it cannot raise its own permissions or bypass the operator policy. A request becomes approval-required when it:

- executes a shell, Docker, MCP, browser, scanner, exploit, or network action;
- targets a host, domain, account, file tree, or service outside the configured scope;
- changes firewall, routing, Tor, credentials, system state, or deployment state;
- uploads data, publishes a Space, opens an ngrok/public URL, or sends an external message;
- accesses a secret, private dataset, or provider with a missing/unclear authorization;
- is classified as high or critical risk by the capability policy.

Every decision must record request ID, timestamp, user/session, capability, target, arguments, policy version, approval state, approver, result, and failure reason. Evidence and audit records must be kept separate from model-generated interpretation.

## Milestones

### M0 — Baseline and inventory

- [ ] Freeze a known-good baseline of `ramibot/`, `osiris/`, and `OMNIBUS/`.
- [ ] Run existing RamiBot frontend/backend tests and OSIRIS tests.
- [ ] Run OMNIBUS compilation, tests, registry checks, policy checks, and orchestrator smoke tests.
- [ ] Produce a capability inventory mapping every OSIRIS route/component and every OMNIBUS module to a RAMIBUS destination.
- [ ] Identify duplicate implementations, dead files, external assumptions, and license/attribution obligations.
- [ ] Do not delete any source during this milestone.

**Exit gate:** baseline commands and known failures are documented in `docs/baseline.md`.

### M1 — Unified configuration and setup contract

- [ ] Add a typed configuration model owned by RamiBot, replacing scattered `.env` assumptions.
- [ ] Add a Settings UI for provider keys, optional data-source keys, Hugging Face, ngrok, scanner, Docker, MCP, and deployment settings.
- [ ] Store secrets securely where the environment supports it; never render full secrets back to the UI or logs.
- [ ] Add connection-test buttons with clear states: not configured, configured, reachable, rate-limited, unauthorized, and failed.
- [ ] Keep keyless OSIRIS feeds working when optional keys are absent.
- [ ] Document which feature each key unlocks and its fallback behavior.

**Initial settings inventory:**

| Setting | Use | Required? |
|---|---|---|
| `OPENAI_API_KEY` / OAuth | hosted model provider | optional |
| `ANTHROPIC_API_KEY` | hosted model provider | optional |
| `OPENROUTER_API_KEY` | model routing | optional |
| `HF_TOKEN` | Hugging Face models, Spaces, gated assets, MCP-adjacent integrations | optional |
| `NGROK_AUTHTOKEN` | public URL/tunnel setup | optional, opt-in |
| `SCANNER_URL`, `SCANNER_KEY` | OSIRIS recon scanner backend | optional |
| `CLOUDFLARE_API_TOKEN` | Radar layers | optional |
| `ETHERSCAN_API_KEY`, `HELIUS_API_KEY` | deeper chain intelligence | optional |
| `FIRMS_API_KEY`, OpenSky credentials, `N2YO_API_KEY`, `AIS_API_KEY` | higher-rate data providers | optional |

**Exit gate:** a clean install can configure all available features from the UI without manually editing multiple project-specific files.

### M2 — Absorb OMNIBUS runtime logic into RamiBot

Port the concepts, not the obsolete project boundary:

- [ ] `CapabilitySpec`, `AdapterSpec`, and registry loading from `OMNIBUS/src/sovereign/registry.py`.
- [ ] YAML/JSON capability manifests and dynamic capability discovery from `discovery.py`.
- [ ] Provider and adapter selection from `adapters/`.
- [ ] Risk levels, approval states, request IDs, and operator-controlled thresholds from `policy.py`.
- [ ] Execution profiles and safe command execution from `execution.py`.
- [ ] Planning/execution separation and multi-hop orchestration from `orchestrator.py`.
- [ ] Persistence of provider state, approval records, and audit events.
- [ ] CLI diagnostics and capability listing from `cli.py`.
- [ ] Add a RamiBot-native `CapabilityRegistry`, `ApprovalPolicy`, `AuditLog`, and `ExecutionGateway` rather than leaving imports pointed at `OMNIBUS/`.

**Exit gate:** RamiBot can list capabilities, evaluate a request, pause for approval, execute through a selected backend, and return an auditable result without importing OMNIBUS at runtime.

### M3 — Absorb OSIRIS intelligence capabilities

- [ ] Port OSIRIS data adapters behind the unified RamiBot capability interface.
- [ ] Preserve the strongest OSIRIS capabilities: MapLibre/WebGL map, progressive and viewport-aware loading, global layers, recon toolkit, sanctions cross-checks, chain intelligence, Telegram public-channel ingestion, and source-health reporting.
- [ ] Move OSIRIS API routes into RamiBot namespaced routes such as `/api/intel/*` or `/api/osiris/*` while maintaining a compatibility layer during migration.
- [ ] Reuse existing RamiBot endpoints where they already provide the same function, especially `/api/world/*` and `/api/osiris/*`.
- [ ] Make every active scanner or external query pass through scope, provider configuration, rate limits, and audit logging.
- [ ] Keep public-feed ingestion read-only by default.
- [ ] Add visible source attribution, freshness, confidence, and key/rate-limit status to the UI.

**Exit gate:** OSIRIS functionality is reachable from the RAMIBUS UI and backend, with no feature requiring the old OSIRIS process to be running.

### M4 — Unified RAMIBUS frontend

- [ ] Make `ramibot/frontend` the only supported frontend.
- [ ] Add a workspace shell with Chat, World/OSINT, Cyber, Agents, Providers, MCP, Terminal, Findings, Approvals, Audit, and Setup views.
- [ ] Add a capability-aware command palette so users can discover features without memorizing routes.
- [ ] Add a clear mode distinction: conversational planning versus executable operations.
- [ ] Preserve RamiBot SSE streaming, tool traces, approval banners, findings, PDF export, and terminal panels.
- [ ] Bring the OSIRIS visual language into the new interface without obscuring approvals or evidence.
- [ ] Support normal chat nuance alongside specialist routing; two-model operation must remain explicit and inspectable rather than pretending that many agents are independently running.

**Exit gate:** a user can complete a normal chat, OSINT lookup, cyber workflow, and approval-gated tool action from one frontend.

### M5 — Environment-adaptive one-paste installer

Implement one documented entry point with platform-specific fallback scripts:

```text
install.sh       Linux, macOS, WSL2, Replit, cloud VPS, Colab-compatible shells
install.ps1      Windows PowerShell
install.bat      Windows convenience wrapper
```

The installer must:

- [ ] Detect OS, shell, architecture, Python, Node, package manager, Git, Docker, CUDA, NVIDIA driver, GPU model, available VRAM, and writable storage.
- [ ] Detect Replit, Google Colab, Google CLI/Cloud Shell, WSL2, local Linux, Windows, and generic VPS without relying on one environment variable.
- [ ] Check versions before installing and explain every change.
- [ ] Prefer existing system tools; create an isolated Python environment and reproducible frontend dependencies.
- [ ] Detect GPU/T4/CUDA/NVIDIA availability and choose CPU, CUDA, or hosted/local model paths accordingly.
- [ ] Treat Docker as optional where unavailable and disable only the features that require it.
- [ ] Offer ngrok setup for public URLs only after explicit operator opt-in; display the resulting URL and warn that exposed endpoints require authentication.
- [ ] Offer Hugging Face login/token configuration for gated models, Spaces, and related integrations.
- [ ] Configure persistence paths correctly for ephemeral Colab/Replit environments and durable VPS/laptop environments.
- [ ] Run post-install health checks and print exact remediation commands.
- [ ] Be idempotent: rerunning setup must preserve configuration and avoid destructive changes.

**Exit gate:** one paste gets a supported environment to a usable RAMIBUS process or reports a precise blocked prerequisite with a safe fallback.

### M6 — Deployment profiles

Provide tested profiles rather than claiming every environment is identical:

- [ ] Local Linux laptop: native Python/Node, optional Docker, GPU autodetection.
- [ ] Windows: PowerShell/WSL2 path, Docker Desktop detection, Windows-safe subprocess behavior.
- [ ] Replit: shell mode, no assumed Docker, persistent secrets/config, truthful runtime capability report.
- [ ] Google Colab: notebook bootstrap, Drive persistence, T4/CUDA detection, HF secret lookup, optional ngrok.
- [ ] Google Cloud Shell/CLI: shell installer, authenticated CLI checks, port/public URL guidance.
- [ ] Cloud VPS: systemd or Docker deployment, firewall guidance, TLS/reverse proxy, persistent volumes.
- [ ] CPU-only fallback: hosted provider or lightweight local model with disabled unsupported features.

**Exit gate:** each profile has a tested command, expected ports, persistence behavior, supported features, and known limitations.

### M7 — Verification, security review, and cleanup

- [ ] Add unit tests for capability registry, policy evaluation, approval expiry, audit immutability, secret redaction, and environment detection.
- [ ] Add integration tests for provider connection checks, OSINT adapters, MCP calls, scanner scope enforcement, SSE streaming, and frontend setup flows.
- [ ] Add smoke tests for chat-only, keyless OSINT, configured OSINT, MCP approval, denied action, Docker-unavailable mode, GPU mode, and public URL opt-in.
- [ ] Test that unauthorized targets are denied before tool execution.
- [ ] Test that ngrok never starts silently and that public endpoints are not exposed without a warning and configured protection.
- [ ] Test that no API key, HF token, ngrok token, or private prompt is written to logs, findings, screenshots, or reports.
- [ ] Update the professional README with architecture, screenshots, colored badges, setup paths, configuration, security model, feature matrix, and troubleshooting.
- [ ] Remove old OSIRIS and OMNIBUS entry points only after migration gates pass.
- [ ] Archive or delete dead duplicate code in a separate reviewed change, preserving attribution and migration notes.

**Final exit gate:** fresh-environment smoke tests pass for the supported profiles, and the repository presents RAMIBUS as the single maintained product.

## Proposed destination layout

```text
ramibot/
├── backend/
│   ├── main.py                 FastAPI gateway and compatibility routes
│   ├── capabilities/           registry, manifests, discovery, adapters
│   ├── policy/                 authorization, risk, approvals, audit
│   ├── orchestration/          planner, routing, execution gateway
│   ├── providers/              hosted/local/Hugging Face model providers
│   ├── intelligence/           OSIRIS feeds, adapters, normalization
│   ├── mcp/                    MCP client, servers, tool schemas
│   ├── skills/                 red/blue/general workflows
│   ├── environment/            platform, GPU, CUDA, Docker detection
│   ├── setup/                  configuration and connection checks
│   ├── db/                     conversations, findings, audit persistence
│   └── tests/
├── frontend/
│   └── src/
│       ├── views/              chat, world, cyber, agents, setup, audit
│       ├── components/         maps, approvals, terminal, findings
│       └── stores/              workspace and capability state
├── rami-kali/                  scoped security tool container
├── scripts/                    installers, smoke tests, environment probes
├── docs/                       architecture, deployment, security, migration
├── install.sh
├── install.ps1
└── README.md
```

## Immediate next work package

1. Create `docs/baseline.md` and capture the current test/build status.
2. Create the capability inventory and mark each OSIRIS/OMNIBUS item as **port**, **reuse**, **replace**, or **delete**.
3. Implement the unified settings schema and redacted connection-test API.
4. Port OMNIBUS policy/registry/orchestration behind RamiBot interfaces first; this establishes the safety boundary before expanding capabilities.
5. Add the first OSIRIS adapter slice: world source health, map layer inventory, and one keyless feed plus one optional-key feed.
6. Add installer environment detection before attempting broad cleanup.

## Definition of done for RAMIBUS

RAMIBUS is done when a fresh user can paste one setup command, configure only the providers or keys they have, receive truthful environment and capability status, use ordinary conversation, access OSINT and cybersecurity tools through one UI, and see every security-boundary action pause for approval and enter an auditable record. No migration is complete merely because code was copied; it is complete only when the old process is no longer required and the relevant smoke tests pass.
