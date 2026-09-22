---
name: RAMIBUS integration boundaries
description: Durable constraints for extending the imported RamiBot frontend and World Intelligence layer.
---

When extending RAMIBUS, preserve the imported RamiBot UI and existing MCP/approval concepts. World Intelligence should report unavailable gateways and missing source material explicitly rather than inventing live data, camera URLs, or source health.

**Why:** The workspace can contain handoff notes without the referenced source repositories or a mounted backend, and Docker is not guaranteed to be available in Replit.

**How to apply:** Keep source adapters behind the existing network/action gateway, use the Replit shell as the non-Docker execution path, and treat OSIRIS/World Monitor as capability references until their repositories are actually present for audit.

Managed artifact services start from the artifact directory, so workspace-level backend commands need paths relative to that directory (for example, `../../ramibot/backend`).

**Why:** The API workflow initially failed when it assumed the workspace root was its working directory; the managed service starts cleanly only after using artifact-relative paths.

**How to apply:** When changing a service command in an existing artifact, validate the path from the artifact directory and keep the command compatible with both development and production service runners.