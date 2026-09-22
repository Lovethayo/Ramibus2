from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class CapabilityDecision:
    allowed: bool
    requires_approval: bool
    reason: str
    risk: str
    capability: str


class RuntimePolicy:
    def __init__(self, *, automatic_max_risk: str = "medium", allow_privileged_tools: bool = False):
        self.automatic_max_risk = automatic_max_risk.lower()
        self.allow_privileged_tools = allow_privileged_tools

    @staticmethod
    def rank(risk: str) -> int:
        order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        return order.get(str(risk).lower(), 1)

    def evaluate(self, *, capability: str, risk: str, permissions: tuple[str, ...] = (), allow_public_tunnel: bool = False, allow_package_install: bool = False) -> CapabilityDecision:
        risk_key = str(risk or "medium").lower()
        permission_set = set(str(p) for p in permissions)

        if capability == "public_tunnel" and not allow_public_tunnel:
            return CapabilityDecision(False, True, "public tunnel not allowed under current policy", risk_key, capability)

        if capability == "package_install" and not allow_package_install:
            return CapabilityDecision(False, True, "package install requires explicit operator approval", risk_key, capability)

        if "shell" in permission_set or "filesystem_write" in permission_set or "process_control" in permission_set:
            if not self.allow_privileged_tools:
                return CapabilityDecision(False, True, "privileged execution is disabled by default; enable only with operator approval", risk_key, capability)

        if self.rank(risk_key) > self.rank(self.automatic_max_risk):
            return CapabilityDecision(False, True, f"risk {risk_key} exceeds automatic max {self.automatic_max_risk}", risk_key, capability)

        return CapabilityDecision(True, False, "within configured safety policy", risk_key, capability)


def load_policy_from_settings(settings: dict) -> RuntimePolicy:
    security = settings.get("security", {}) if isinstance(settings, dict) else {}
    return RuntimePolicy(
        automatic_max_risk=str(security.get("automatic_max_risk") or "medium").lower(),
        allow_privileged_tools=bool(security.get("allow_privileged_tools", False)),
    )
