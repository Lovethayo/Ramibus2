from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass(slots=True)
class CapabilitySpec:
    id: str
    category: str
    description: str = ""
    risk: str = "medium"
    permissions: tuple[str, ...] = ()
    data_sources: tuple[str, ...] = ()
    egress: tuple[str, ...] = ()
    installable: bool = False
    approval_required: bool = True
    default_enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "CapabilitySpec":
        return cls(
            id=str(data.get("id") or data.get("name") or "").strip(),
            category=str(data.get("category") or "general").strip(),
            description=str(data.get("description") or "").strip(),
            risk=str(data.get("risk") or "medium").lower(),
            permissions=tuple(str(x) for x in data.get("permissions") or ()),
            data_sources=tuple(str(x) for x in data.get("data_sources") or ()),
            egress=tuple(str(x) for x in data.get("egress") or ()),
            installable=bool(data.get("installable", False)),
            approval_required=bool(data.get("approval_required", True)),
            default_enabled=bool(data.get("default_enabled", True)),
            metadata={k: v for k, v in (data or {}).items() if k not in {
                "id", "name", "category", "description", "risk", "permissions",
                "data_sources", "egress", "installable", "approval_required",
                "default_enabled"
            }},
        )


class CapabilityRegistry:
    def __init__(self) -> None:
        self._items: dict[str, CapabilitySpec] = {}

    def register(self, spec: CapabilitySpec | dict[str, Any], *, replace: bool = False) -> CapabilitySpec:
        capability = spec if isinstance(spec, CapabilitySpec) else CapabilitySpec.from_mapping(spec)
        if not capability.id:
            raise ValueError("Capability id is required")
        if capability.id in self._items and not replace:
            return self._items[capability.id]
        self._items[capability.id] = capability
        return capability

    def register_many(self, capabilities: Iterable[CapabilitySpec | dict[str, Any]]) -> None:
        for item in capabilities:
            self.register(item, replace=True)

    def get(self, capability_id: str) -> CapabilitySpec | None:
        return self._items.get(capability_id)

    def list(self) -> list[dict[str, Any]]:
        items = []
        for spec in sorted(self._items.values(), key=lambda x: x.id.lower()):
            items.append({
                "id": spec.id,
                "category": spec.category,
                "description": spec.description,
                "risk": spec.risk,
                "permissions": list(spec.permissions),
                "data_sources": list(spec.data_sources),
                "egress": list(spec.egress),
                "installable": spec.installable,
                "approval_required": spec.approval_required,
                "default_enabled": spec.default_enabled,
                "metadata": spec.metadata,
            })
        return items


def default_capabilities() -> list[dict[str, Any]]:
    return [
        {
            "id": "world_intel",
            "category": "intel",
            "description": "OSINT and world feed intelligence",
            "risk": "low",
            "permissions": ("read_public_feeds",),
            "data_sources": ("public_routes", "osiris",),
            "egress": ("configured_public_feeds",),
            "installable": False,
            "approval_required": False,
            "default_enabled": True,
        },
        {
            "id": "network_scan",
            "category": "tradecraft",
            "description": "Recon or port scanning and targeted host enumeration",
            "risk": "medium",
            "permissions": ("network_scan", "targeted_probe"),
            "data_sources": ("scanner_backend",),
            "egress": ("network",),
            "installable": False,
            "approval_required": True,
            "default_enabled": True,
        },
        {
            "id": "package_install",
            "category": "maintenance",
            "description": "Install dependencies or packages on the host or isolated runtime",
            "risk": "high",
            "permissions": ("filesystem_write", "package_manager", "network_install"),
            "data_sources": ("apt", "pip", "npm", "git"),
            "egress": ("package_registry", "internet"),
            "installable": True,
            "approval_required": True,
            "default_enabled": False,
        },
        {
            "id": "public_tunnel",
            "category": "networking",
            "description": "Open a public URL or tunnel endpoint",
            "risk": "high",
            "permissions": ("expose_service", "external_network"),
            "data_sources": ("ngrok", "cloudflare"),
            "egress": ("public_tunnel",),
            "installable": False,
            "approval_required": True,
            "default_enabled": False,
        },
        {
            "id": "docker_operations",
            "category": "execution",
            "description": "Run containerized tools or helper workloads",
            "risk": "medium",
            "permissions": ("docker", "container_runtime"),
            "data_sources": ("docker",),
            "egress": ("container_network",),
            "installable": False,
            "approval_required": True,
            "default_enabled": True,
        },
        {
            "id": "shell_exec",
            "category": "execution",
            "description": "Execute arbitrary shell commands in the local environment",
            "risk": "critical",
            "permissions": ("shell", "filesystem", "process_control"),
            "data_sources": ("local_shell",),
            "egress": ("local_system",),
            "installable": False,
            "approval_required": True,
            "default_enabled": False,
        },
    ]


RAMIBUS_REGISTRY = CapabilityRegistry()
RAMIBUS_REGISTRY.register_many(default_capabilities())
