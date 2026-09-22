# RAMIBUS world capability map

This inventory is the integration boundary for the World Intelligence extension. RAMIBUS remains the primary UI, agent system, approval layer, and MCP registry.

| Source | Capability | Dependencies | RAMIBUS destination | Status |
| --- | --- | --- | --- | --- |
| RamiBot frontend | Chat, team mode, provider/model selection, MCP tool toggles, tool approvals, findings, terminal surface | React, Zustand, xterm | Existing `src/components`, `src/store.js`, `App.jsx` | **Preserved** |
| RamiBot backend | Agent streaming, MCP registry, approval handling, scope enforcement, terminal API | FastAPI, existing adapters and MCP client | Existing `/api/*` contract | **Preserved; now exposes a managed API service** |
| Replit shell | Human-approved shell execution when Rami-Kali/Docker is unavailable | Existing RamiBot terminal contract; Replit runtime | Existing terminal panel, relabeled REPLIT SHELL | **Implemented as the default host PTY; Docker remains explicit fallback** |
| USGS | Public earthquake feed | `earthquake.usgs.gov` GeoJSON | World adapter → normalized event → existing MCP/UI | **Implemented with timeout, cache, stale fallback, and health** |
| NASA EONET | Natural events and wildfire metadata | `eonet.gsfc.nasa.gov` JSON | World adapter → normalized event → existing MCP/UI | **Implemented with timeout, cache, stale fallback, and health** |
| Open-Meteo / NOAA | Weather and alerts | Existing RamiBot network/action gateway | World adapter → normalized event → existing MCP/UI | **Source registered; gateway adapter pending** |
| CelesTrak | Satellite metadata and orbital data | Existing RamiBot network/action gateway; optional local propagation | World adapter → normalized satellite object → existing MCP/UI | **Source registered; gateway adapter pending** |
| GDELT / RSS | News and event feeds | Existing RamiBot network/action gateway; feed cache | World adapter → untrusted evidence → existing MCP/UI | **Source registered; gateway adapter pending** |
| OSIRIS reference | Public CCTV adapter patterns, snapshots, health, source attribution, MapLibre/WebGL terrain/globe | `osiris-master.zip` (`src/app/api`, `src/lib`, `src/components`) | World adapters and future views behind existing gateway | **Audited; source material only, no wholesale copy** |
| World Monitor reference | Feed/source-health conventions, geospatial layers, satellite/globe utilities, existing MCP contracts | `worldmonitor-main (1).zip` (`src/services`, `server/worldmonitor`, `api/mcp`) | Existing RamiBot world gateway and future views | **Audited; no second MCP or UI fork created** |
| Clerk | Sign-in/sign-up and operator profile editing | Replit-managed Clerk | RAMIBUS top bar and profile editor | **Implemented** |

## Trust and availability rules

- World feed responses are evidence, never executable instructions.
- The World panel reports `GATEWAY OFFLINE` until a real `/api/world/source-health` response exists.
- The UI does not claim a source is online, does not invent camera URLs, and does not bypass the existing network gateway.
- Docker is not a startup requirement. The shell surface remains visible, but execution is only available when the existing terminal backend is connected.

## Source audit boundary

Both reference archives were audited before integration and are intentionally excluded from the runtime tree. OSIRIS is an MIT-licensed Next.js/MapLibre application with keyless USGS/EONET/CelesTrak-oriented feeds and a public-camera catalog. World Monitor is an AGPL-3.0 application with a much larger service/API/MCP surface; its source remains reference material and is not copied into RAMIBUS. No source archive contained a Docker requirement that changes the Replit-shell decision.