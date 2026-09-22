"""Keyless-first OSIRIS-derived world feed gateway for RamiBot.

This module owns source isolation, normalization, short-lived caching, and
health reporting. It deliberately returns untrusted evidence; it does not
execute feed content or create a second MCP client.
"""

import asyncio
import math
import time
from dataclasses import dataclass
from typing import Any

import httpx
from cctv_feeds import CCTVFeedService, CCTV_TOOLS
from osiris_tools import OMNIBUS_CAPABILITIES, OSIRIS_TOOLS, OsirisCapabilityService


USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
EONET_URL = "https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=50"


@dataclass
class FeedState:
    data: list[dict]
    fetched_at: float = 0
    expires_at: float = 0
    last_error: str = ""
    status: str = "UNKNOWN"


class WorldFeedService:
    def __init__(self):
        self._states = {
            "usgs": FeedState([]),
            "eonet": FeedState([]),
            "weather": FeedState([]),
            "satellites": FeedState([]),
            "news": FeedState([]),
            "cctv": FeedState([]),
        }
        self._locks = {source_id: asyncio.Lock() for source_id in self._states}
        self.cctv = CCTVFeedService()
        self.osiris = OsirisCapabilityService(self.cctv)

    async def _get_json(self, url: str) -> Any:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(15, connect=5),
            headers={"User-Agent": "RamiBot-WorldGateway/1.0"},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def _refresh(self, source_id: str, fetcher, ttl_seconds: int = 60) -> list[dict]:
        state = self._states[source_id]
        now = time.time()
        if state.data and now < state.expires_at:
            return state.data

        async with self._locks[source_id]:
            now = time.time()
            if state.data and now < state.expires_at:
                return state.data
            try:
                data = await fetcher()
                if not isinstance(data, list):
                    raise ValueError("provider returned a non-list payload")
                # Empty refreshes do not erase the last known good data.
                if data or not state.data:
                    state.data = data
                state.fetched_at = now
                state.expires_at = now + ttl_seconds
                state.last_error = ""
                state.status = "ONLINE" if data else "DEGRADED"
            except Exception as error:
                state.last_error = str(error)
                state.status = "STALE" if state.data else "OFFLINE"
                state.expires_at = now + 30
            return state.data

    async def _fetch_usgs(self) -> list[dict]:
        payload = await self._get_json(USGS_URL)
        events = []
        for feature in payload.get("features", []):
            coords = (feature.get("geometry") or {}).get("coordinates") or [None, None, None]
            props = feature.get("properties") or {}
            if coords[0] is None or coords[1] is None:
                continue
            events.append({
                "id": feature.get("id"),
                "type": "earthquake",
                "name": props.get("place") or "Earthquake",
                "latitude": coords[1],
                "longitude": coords[0],
                "altitude": -(coords[2] or 0),
                "source": "usgs",
                "source_url": props.get("url") or USGS_URL,
                "status": "active",
                "timestamp": props.get("time"),
                "metadata": {
                    "magnitude": props.get("mag"),
                    "depth_km": coords[2],
                    "tsunami": props.get("tsunami", 0),
                    "alert": props.get("alert"),
                    "felt": props.get("felt"),
                },
            })
        return events

    async def _fetch_eonet(self) -> list[dict]:
        payload = await self._get_json(EONET_URL)
        events = []
        for event in payload.get("events", []):
            geometries = event.get("geometry") or []
            geometry = geometries[-1] if geometries else {}
            coords = geometry.get("coordinates")
            if geometry.get("type") == "Point" and isinstance(coords, list) and len(coords) >= 2:
                events.append({
                    "id": event.get("id"),
                    "type": "event",
                    "name": event.get("title") or "NASA natural event",
                    "latitude": coords[1],
                    "longitude": coords[0],
                    "altitude": None,
                    "source": "eonet",
                    "source_url": event.get("link") or EONET_URL,
                    "status": "active",
                    "timestamp": geometry.get("date"),
                    "metadata": {
                        "categories": [category.get("title") for category in event.get("categories", [])],
                    },
                })
        return events

    async def recent(self, limit: int = 50) -> list[dict]:
        results = await asyncio.gather(
            self._refresh("usgs", self._fetch_usgs),
            self._refresh("eonet", self._fetch_eonet),
            return_exceptions=True,
        )
        events = []
        for result in results:
            if isinstance(result, list):
                events.extend(result)
        events.sort(key=lambda event: str(event.get("timestamp") or ""), reverse=True)
        return events[: max(1, min(limit, 500))]

    async def search(self, query: str, limit: int = 50) -> list[dict]:
        needle = (query or "").strip().lower()
        events = await self.recent(500)
        if not needle:
            return events[:limit]
        return [
            event for event in events
            if needle in str(event.get("name", "")).lower()
            or needle in str(event.get("type", "")).lower()
            or needle in str(event.get("source", "")).lower()
        ][:limit]

    async def nearby(self, latitude: float, longitude: float, radius_km: float = 250, limit: int = 50) -> list[dict]:
        matches = []
        for event in await self.recent(500):
            event_lat = event.get("latitude")
            event_lng = event.get("longitude")
            if event_lat is None or event_lng is None:
                continue
            distance = self._distance_km(latitude, longitude, event_lat, event_lng)
            if distance <= radius_km:
                item = dict(event)
                item["metadata"] = {**(item.get("metadata") or {}), "distance_km": round(distance, 2)}
                matches.append(item)
        matches.sort(key=lambda item: item["metadata"]["distance_km"])
        return matches[:limit]

    def source_health(self) -> list[dict]:
        now = time.time()
        health = []
        for source_id, state in self._states.items():
            if state.data and now >= state.expires_at and state.status == "ONLINE":
                status = "STALE"
            else:
                status = state.status
            health.append({
                "id": source_id,
                "source_id": source_id,
                "status": status,
                "count": len(state.data),
                "fetched_at": state.fetched_at or None,
                "age_seconds": round(now - state.fetched_at, 1) if state.fetched_at else None,
                "last_error": state.last_error or None,
                "key_required": False,
            })
        health = [item for item in health if item.get("id") != "cctv"]
        health.append(self.cctv.health())
        health.append(self.osiris.health())
        return health

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        if tool_name == "osiris_capabilities":
            return self.osiris.capabilities()
        if tool_name == "osiris_source_health":
            return self.osiris.health()
        if tool_name == "osiris_query":
            return await self.osiris.query(arguments.get("capability", ""), arguments.get("params", {}))
        if tool_name == "osiris_batch_query":
            return await self.osiris.batch_query(arguments.get("queries", []))
        if tool_name == "omnibus_capabilities":
            return OMNIBUS_CAPABILITIES
        if tool_name in {"world_recent", "feeds_latest", "earthquakes_latest"}:
            return await self.recent(int(arguments.get("limit", 50)))
        if tool_name in {"world_search", "feeds_search"}:
            return await self.search(arguments.get("query", ""), int(arguments.get("limit", 50)))
        if tool_name in {"world_near", "feeds_nearby", "earthquakes_nearby"}:
            return await self.nearby(
                float(arguments["latitude"]),
                float(arguments["longitude"]),
                float(arguments.get("radius_km", 250)),
                int(arguments.get("limit", 50)),
            )
        if tool_name in {"world_source_health", "feeds_status"}:
            return self.source_health()
        if tool_name.startswith("cctv_"):
            return await self.cctv.call_tool(tool_name, arguments)
        raise ValueError(f"Unknown built-in world tool: {tool_name}")

    @staticmethod
    def _distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        radius = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        d_phi = math.radians(lat2 - lat1)
        d_lambda = math.radians(lng2 - lng1)
        value = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
        return 2 * radius * math.asin(min(1, math.sqrt(value)))


WORLD_TOOLS = [
    {
        "name": "world_recent",
        "description": "Read recent normalized public world events from the RamiBot gateway.",
        "inputSchema": {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 500}}},
    },
    {
        "name": "world_search",
        "description": "Search recent normalized public world events by text or source.",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}},
    },
    {
        "name": "world_near",
        "description": "Find recent normalized public world events near latitude and longitude.",
        "inputSchema": {
            "type": "object",
            "required": ["latitude", "longitude"],
            "properties": {
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
                "radius_km": {"type": "number"},
                "limit": {"type": "integer"},
            },
        },
    },
    {
        "name": "world_source_health",
        "description": "Report health, freshness, and errors for world data sources.",
        "inputSchema": {"type": "object", "properties": {}},
    },
] + CCTV_TOOLS + OSIRIS_TOOLS