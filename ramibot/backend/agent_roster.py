"""Deterministic RAMIBUS agent roster and non-competitive role routing.

The roster is intentionally generated from stable role families instead of
pretending that 1,200 independent model processes are running. Each slot has
one owner model and one operational lane, so planner and tradecraft work do
not compete for the same task.
"""

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class AgentSlot:
    id: str
    name: str
    lane: str
    model_role: str
    team: str


ROLE_FAMILIES = (
    ("R1 Planner", "planning", "planner", "red"),
    ("Tradecraft Lead", "tradecraft", "tradecraft", "red"),
    ("Recon Analyst", "recon", "tradecraft", "red"),
    ("Evidence Custodian", "evidence", "planner", "blue"),
    ("World Monitor", "world", "planner", "blue"),
    ("Defense Analyst", "defense", "planner", "blue"),
    ("MCP Operator", "tooling", "tradecraft", "red"),
    ("Review Officer", "review", "planner", "blue"),
)


def build_roster(limit: int = 1200) -> list[dict]:
    limit = max(0, min(int(limit), 1200))
    roster: list[dict] = []
    for index in range(limit):
        family, lane, model_role, team = ROLE_FAMILIES[index % len(ROLE_FAMILIES)]
        slot_number = index + 1
        slot = AgentSlot(
            id=f"agent-{slot_number:04d}",
            name=f"{family} {slot_number:04d}",
            lane=lane,
            model_role=model_role,
            team=team,
        )
        roster.append(asdict(slot))
    return roster


def route_request(message: str, team_mode: str = "red") -> dict:
    """Choose exactly one owner lane for a request.

    This is a deterministic router, not a debate between models. Planner owns
    planning, review, evidence, world, and defense requests; tradecraft owns
    execution-oriented requests. The selected model can still be hot-swapped
    by the caller without changing the lane contract.
    """
    text = (message or "").lower()
    planner_terms = (
        "plan", "prioritize", "review", "summarize", "report", "evidence",
        "world", "weather", "earthquake", "news", "map", "defend", "harden",
        "remediate", "coordinate", "route", "assign",
    )
    lane = "planner" if any(term in text for term in planner_terms) else "tradecraft"
    if team_mode == "blue" and lane == "tradecraft":
        lane = "planner"
    return {
        "lane": lane,
        "agent_id": "agent-0001" if lane == "planner" else "agent-0002",
        "agent_name": "R1 Planner 0001" if lane == "planner" else "Tradecraft Lead 0002",
        "model_role": lane,
    }