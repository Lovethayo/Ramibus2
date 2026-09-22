"""Osiris capability gateway for RamiBot.

The Osiris project contains two different things:

* reusable data adapters (CCTV, weather, aircraft, OSINT, markets, and more)
* a standalone browser UI

RamiBot owns the UI and approval boundary. This module exposes the adapter
surface as a single, auditable capability gateway. Keyless feeds are executed
locally; other Osiris routes may be delegated to an operator-managed internal
Osiris API service through OSIRIS_API_URL. No public-facing Osiris UI is
required, and an unavailable delegated source is returned explicitly rather
than being replaced with fabricated data.
"""

from __future__ import annotations

import asyncio
import csv
import io
import os
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from cctv_feeds import CCTVFeedService


OSIRIS_API_URL = os.environ.get("OSIRIS_API_URL", "").rstrip("/")
REQUEST_TIMEOUT = httpx.Timeout(20, connect=5)


# This is intentionally a registry, not a second UI route list. It mirrors
# the data/API surface in osiris/src/app/api and is used by the RamiBot tool
# selector, the capability status endpoint, and the operator-facing panel.
OSIRIS_CAPABILITIES: list[dict[str, Any]] = [
    {"id": "cctv", "category": "geospatial", "mode": "direct+bridge", "authorization": "public_or_authorized_only"},
    {"id": "aircraft", "category": "tracking", "mode": "bridge"},
    {"id": "flights", "category": "tracking", "mode": "bridge"},
    {"id": "flight-route", "category": "tracking", "mode": "bridge"},
    {"id": "satellites", "category": "geospatial", "mode": "direct+bridge"},
    {"id": "satellites/orbit", "category": "geospatial", "mode": "bridge"},
    {"id": "weather", "category": "environment", "mode": "direct+bridge"},
    {"id": "air-quality", "category": "environment", "mode": "bridge"},
    {"id": "earthquakes", "category": "environment", "mode": "direct+bridge"},
    {"id": "fires", "category": "environment", "mode": "direct+bridge"},
    {"id": "space-weather", "category": "environment", "mode": "direct+bridge"},
    {"id": "news", "category": "news", "mode": "direct+bridge"},
    {"id": "live-news", "category": "news", "mode": "bridge"},
    {"id": "gdelt", "category": "news", "mode": "bridge"},
    {"id": "gdelt-events", "category": "news", "mode": "bridge"},
    {"id": "crypto", "category": "markets", "mode": "direct+bridge"},
    {"id": "markets", "category": "markets", "mode": "bridge"},
    {"id": "markets/history", "category": "markets", "mode": "bridge"},
    {"id": "maritime", "category": "tracking", "mode": "bridge"},
    {"id": "radar", "category": "network", "mode": "bridge"},
    {"id": "cloudflare-radar", "category": "network", "mode": "bridge"},
    {"id": "cyber-attacks", "category": "cyber", "mode": "bridge"},
    {"id": "cyber-threats", "category": "cyber", "mode": "direct+bridge"},
    {"id": "malware", "category": "cyber", "mode": "bridge"},
    {"id": "osint/dns", "category": "osint", "mode": "bridge"},
    {"id": "osint/certs", "category": "osint", "mode": "bridge"},
    {"id": "osint/whois", "category": "osint", "mode": "bridge"},
    {"id": "osint/ip", "category": "osint", "mode": "bridge"},
    {"id": "osint/bgp", "category": "osint", "mode": "bridge"},
    {"id": "osint/mac", "category": "osint", "mode": "bridge"},
    {"id": "osint/phone", "category": "osint", "mode": "bridge"},
    {"id": "osint/username", "category": "osint", "mode": "bridge"},
    {"id": "osint/github", "category": "osint", "mode": "bridge"},
    {"id": "osint/cve", "category": "osint", "mode": "bridge"},
    {"id": "osint/threats", "category": "osint", "mode": "bridge"},
    {"id": "osint/shodan", "category": "osint", "mode": "bridge"},
    {"id": "osint/leaks", "category": "osint", "mode": "bridge"},
    {"id": "osint/crypto", "category": "osint", "mode": "bridge"},
    {"id": "osint/sanctions", "category": "osint", "mode": "bridge"},
    {"id": "osint/hudsonrock", "category": "osint", "mode": "bridge"},
    {"id": "osint/sweep", "category": "osint", "mode": "bridge"},
    {"id": "scanner", "category": "security", "mode": "bridge", "authorization": "operator_approved_only"},
    {"id": "directions", "category": "geospatial", "mode": "bridge"},
    {"id": "geosearch", "category": "geospatial", "mode": "direct+bridge"},
    {"id": "geo", "category": "geospatial", "mode": "bridge"},
    {"id": "geo/reverse", "category": "geospatial", "mode": "bridge"},
    {"id": "region-dossier", "category": "analysis", "mode": "bridge"},
    {"id": "country-risk", "category": "analysis", "mode": "bridge"},
    {"id": "conflicts", "category": "analysis", "mode": "bridge"},
    {"id": "frontlines", "category": "analysis", "mode": "bridge"},
    {"id": "infrastructure", "category": "analysis", "mode": "bridge"},
    {"id": "sentinel", "category": "geospatial", "mode": "bridge"},
    {"id": "chain/daily", "category": "markets", "mode": "bridge"},
    {"id": "scm-suppliers", "category": "analysis", "mode": "bridge"},
    {"id": "astra", "category": "analysis", "mode": "bridge"},
    # Complete API inventory. These routes are kept in the gateway even when
    # their implementation is delegated to the internal Osiris runtime.
    {"id": "ai/analyze", "category": "analysis", "mode": "bridge"},
    {"id": "ai/briefing", "category": "analysis", "mode": "bridge"},
    {"id": "ai/overview", "category": "analysis", "mode": "bridge"},
    {"id": "arcgis", "category": "geospatial", "mode": "bridge"},
    {"id": "cctv/proxy", "category": "geospatial", "mode": "bridge", "authorization": "public_or_authorized_only"},
    {"id": "cctv/resolve", "category": "geospatial", "mode": "bridge", "authorization": "public_or_authorized_only"},
    {"id": "cctv/stream-status", "category": "geospatial", "mode": "bridge", "authorization": "public_or_authorized_only"},
    {"id": "cctv/texas/snapshot", "category": "geospatial", "mode": "bridge", "authorization": "public_or_authorized_only"},
    {"id": "entity/expand", "category": "osint", "mode": "bridge"},
    {"id": "github-webhook", "category": "integration", "mode": "bridge", "authorization": "operator_approved_only"},
    {"id": "health", "category": "system", "mode": "bridge"},
    {"id": "malware/stream", "category": "cyber", "mode": "bridge", "authorization": "operator_approved_only"},
    {"id": "proxy-tiles", "category": "geospatial", "mode": "bridge", "authorization": "public_or_authorized_only"},
    {"id": "sdk/ingest", "category": "integration", "mode": "bridge", "authorization": "operator_approved_only"},
    {"id": "sdk/stream", "category": "integration", "mode": "bridge", "authorization": "operator_approved_only"},
    {"id": "stats", "category": "system", "mode": "bridge"},
]


# OMNIBUS contributes the capability vocabulary and policy boundary. The
# execution surface remains RamiBot, so there is no Open WebUI dependency.
OMNIBUS_CAPABILITIES: list[dict[str, Any]] = [
    {"id": "reasoning", "category": "model", "status": "ramibot_provider_routing"},
    {"id": "coding", "category": "model", "status": "ramibot_provider_routing"},
    {"id": "web_research", "category": "research", "status": "ramibot_mcp_and_osiris"},
    {"id": "browser", "category": "computer_use", "status": "not_configured", "note": "No hidden browser is claimed."},
    {"id": "video_generation", "category": "media", "status": "provider_dependent"},
    {"id": "image_generation", "category": "media", "status": "provider_dependent"},
    {"id": "globe", "category": "geospatial", "status": "ramibus_world_globe"},
    {"id": "public_cctv", "category": "geospatial", "status": "osiris_public_authorized_gateway", "authorization": "public_or_authorized_only"},
    {"id": "satellite", "category": "geospatial", "status": "osiris_gateway"},
    {"id": "document_rag", "category": "knowledge", "status": "ramibot_conversation_context"},
]


def _capability(capability_id: str) -> dict[str, Any] | None:
    return next((item for item in OSIRIS_CAPABILITIES if item["id"] == capability_id), None)


def _path_to_capability(path: str) -> str:
    normalized = path.strip().strip("/")
    if normalized.startswith("api/"):
        normalized = normalized[4:]
    return normalized


class OsirisCapabilityService:
    """Execute direct feeds and delegate the rest to an internal API bridge."""

    def __init__(self, cctv: CCTVFeedService):
        self.cctv = cctv
        self._cache: dict[str, tuple[float, Any]] = {}
        self._lock = asyncio.Lock()
        self._last_errors: dict[str, str] = {}

    def capabilities(self) -> list[dict[str, Any]]:
        bridge_online = bool(OSIRIS_API_URL)
        return [
            {
                **item,
                "status": (
                    "DIRECT"
                    if item["mode"].startswith("direct")
                    else "BRIDGE_CONFIGURED" if bridge_online else "BRIDGE_UNAVAILABLE"
                ),
                "last_error": self._last_errors.get(item["id"]),
            }
            for item in OSIRIS_CAPABILITIES
        ]

    def health(self) -> dict[str, Any]:
        direct = [item for item in self.capabilities() if item["mode"].startswith("direct")]
        bridge = [item for item in self.capabilities() if item["mode"] == "bridge"]
        return {
            "id": "osiris",
            "status": "ONLINE" if direct else "DEGRADED",
            "bridge_configured": bool(OSIRIS_API_URL),
            "capability_count": len(OSIRIS_CAPABILITIES),
            "direct_count": len(direct),
            "bridge_count": len(bridge),
            "last_errors": self._last_errors,
            "policy": "public_or_authorized_sources_only",
        }

    async def query(self, path: str, params: dict[str, Any] | None = None) -> Any:
        capability_id = _path_to_capability(path)
        capability = _capability(capability_id)
        if not capability:
            raise ValueError(f"Unknown Osiris capability: {capability_id}")

        params = {key: value for key, value in (params or {}).items() if value is not None and value != ""}
        try:
            direct = await self._direct(capability_id, params)
            if direct is not None:
                return direct
            return await self._bridge(capability_id, params)
        except Exception as error:
            self._last_errors[capability_id] = str(error)
            raise

    async def batch_query(self, queries: list[dict[str, Any]]) -> dict[str, Any]:
        """Run independent public-feed queries concurrently.

        This is the AI equivalent of opening several live feeds together. It
        returns per-query errors so one unavailable source never contaminates
        the evidence from the sources that did respond.
        """
        bounded = queries[:32]

        async def run(item: dict[str, Any]) -> dict[str, Any]:
            capability = str(item.get("capability", "")).strip()
            params = item.get("params") if isinstance(item.get("params"), dict) else {}
            try:
                return {"capability": capability, "ok": True, "result": await self.query(capability, params)}
            except Exception as error:
                return {"capability": capability, "ok": False, "error": str(error)}

        results = await asyncio.gather(*(run(item) for item in bounded))
        return {
            "requested": len(queries),
            "executed": len(bounded),
            "concurrent": True,
            "results": results,
            "evidence_policy": "untrusted_feed_content",
        }

    async def _direct(self, capability_id: str, params: dict[str, Any]) -> Any | None:
        cached = self._cache.get(capability_id)
        if cached and time.time() < cached[0] and not params.get("refresh"):
            return cached[1]

        # When the internal bridge is configured it owns the complete Osiris
        # worldwide camera catalog. The embedded RamiBot catalog is the safe
        # fallback for installations that do not run that bridge.
        if capability_id == "cctv" and OSIRIS_API_URL:
            return None
        if capability_id == "cctv":
            result = await self.cctv.search(str(params.get("query", "")), int(params.get("limit", 100)))
            return result
        if capability_id == "geosearch":
            query = str(params.get("q", params.get("query", ""))).strip()
            if not query:
                return []
            encoded = urlencode({"q": query, "format": "jsonv2", "limit": 5, "addressdetails": 1})
            async with httpx.AsyncClient(
                timeout=REQUEST_TIMEOUT,
                headers={"User-Agent": "RamiBot-Osiris-Gateway/1.0 (public geosearch)"},
            ) as client:
                response = await client.get(f"https://nominatim.openstreetmap.org/search?{encoded}")
                response.raise_for_status()
                return response.json()
        if capability_id == "earthquakes":
            payload = await self._json("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson")
            result = self._geojson_events(payload, "earthquake", "usgs")
            return self._remember(capability_id, result, 60)
        if capability_id == "fires":
            payload = await self._json("https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=100")
            result = self._eonet_events(payload)
            return self._remember(capability_id, result, 60)
        if capability_id == "weather":
            lat = float(params.get("latitude", 0))
            lon = float(params.get("longitude", 0))
            query = urlencode({
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                "hourly": "precipitation_probability,temperature_2m",
                "timezone": "UTC",
            })
            return await self._json(f"https://api.open-meteo.com/v1/forecast?{query}")
        if capability_id == "crypto":
            return await self._json(
                "https://api.coingecko.com/api/v3/simple/price?"
                "ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true"
            )
        if capability_id == "cyber-threats":
            return await self._json(
                "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
            )
        if capability_id == "space-weather":
            kp, alerts, xray = await asyncio.gather(
                self._json("https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"),
                self._json("https://services.swpc.noaa.gov/json/alerts.json"),
                self._json("https://services.swpc.noaa.gov/json/goes/primary/xray-flares-latest.json"),
                return_exceptions=True,
            )
            return {"kp": kp if not isinstance(kp, Exception) else [], "alerts": alerts if not isinstance(alerts, Exception) else [], "xray": xray if not isinstance(xray, Exception) else []}
        if capability_id == "satellites":
            return await self._satellites()
        if capability_id == "news":
            return await self._news()
        return None

    async def _bridge(self, capability_id: str, params: dict[str, Any]) -> Any:
        if not OSIRIS_API_URL:
            raise RuntimeError(
                f"Osiris capability '{capability_id}' is not available in this runtime. "
                "Configure the internal OSIRIS_API_URL bridge to enable this adapter."
            )
        path = f"{OSIRIS_API_URL}/api/{capability_id}"
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=False) as client:
            response = await client.get(path, params=params)
            response.raise_for_status()
            payload = response.json()
            if capability_id == "cctv":
                cameras = payload.get("cameras", payload) if isinstance(payload, dict) else payload
                return [self._normalize_camera(camera) for camera in cameras or []]
            return payload

    @staticmethod
    def _normalize_camera(camera: dict[str, Any]) -> dict[str, Any]:
        """Keep Osiris' lat/lng shape compatible with RamiBot's camera cards."""
        return {
            **camera,
            "latitude": camera.get("latitude", camera.get("lat")),
            "longitude": camera.get("longitude", camera.get("lng")),
            "feed_url": camera.get("feed_url"),
            "external_url": camera.get("external_url", camera.get("source_url")),
            "source_url": camera.get("source_url", camera.get("external_url")),
            "status": camera.get("status", "active"),
            "type": "camera",
        }

    async def _json(self, url: str) -> Any:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, headers={"User-Agent": "RamiBot-Osiris-Gateway/1.0"}) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    def _remember(self, key: str, result: Any, ttl: int) -> Any:
        self._cache[key] = (time.time() + ttl, result)
        return result

    async def _satellites(self) -> dict[str, Any]:
        # Keep the gateway keyless and bounded. The complete orbital catalogue
        # remains available through the internal Osiris bridge when configured.
        text = await self._text("https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        satellites = []
        for index in range(0, len(lines) - 2, 3):
            if not lines[index + 1].startswith("1") or not lines[index + 2].startswith("2"):
                continue
            satellites.append({
                "name": lines[index],
                "line1": lines[index + 1],
                "line2": lines[index + 2],
                "noradId": lines[index + 1][2:7].strip(),
                "type": "satellite",
            })
        return {"satellites": satellites, "total": len(satellites), "source": "celestrak-stations"}

    async def _news(self) -> list[dict[str, Any]]:
        feeds = [
            ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
            ("The Guardian World", "https://www.theguardian.com/world/rss"),
            ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
        ]
        results: list[dict[str, Any]] = []
        for source, url in feeds:
            try:
                raw = await self._text(url)
                results.extend(self._parse_rss(raw, source))
            except Exception as error:
                self._last_errors[f"news:{source}"] = str(error)
        results.sort(key=lambda item: item.get("published", ""), reverse=True)
        return results[:100]

    @staticmethod
    def _parse_rss(raw: str, source: str) -> list[dict[str, Any]]:
        import xml.etree.ElementTree as element_tree

        root = element_tree.fromstring(raw)
        result = []
        for item in root.findall(".//item"):
            result.append({
                "title": item.findtext("title", ""),
                "url": item.findtext("link", ""),
                "published": item.findtext("pubDate", ""),
                "description": item.findtext("description", ""),
                "source": source,
                "type": "news",
            })
        return result

    async def _text(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, headers={"User-Agent": "RamiBot-Osiris-Gateway/1.0"}) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    @staticmethod
    def _geojson_events(payload: dict[str, Any], event_type: str, source: str) -> list[dict[str, Any]]:
        result = []
        for feature in payload.get("features", []):
            coords = (feature.get("geometry") or {}).get("coordinates") or []
            props = feature.get("properties") or {}
            if len(coords) < 2:
                continue
            result.append({
                "id": feature.get("id"),
                "type": event_type,
                "name": props.get("place") or event_type.title(),
                "latitude": coords[1],
                "longitude": coords[0],
                "source": source,
                "source_url": props.get("url"),
                "timestamp": props.get("time"),
                "metadata": props,
            })
        return result

    @staticmethod
    def _eonet_events(payload: dict[str, Any]) -> list[dict[str, Any]]:
        result = []
        for event in payload.get("events", []):
            geometries = event.get("geometry") or []
            geometry = geometries[-1] if geometries else {}
            coords = geometry.get("coordinates")
            if geometry.get("type") != "Point" or not isinstance(coords, list) or len(coords) < 2:
                continue
            result.append({
                "id": event.get("id"),
                "type": "event",
                "name": event.get("title") or "NASA natural event",
                "latitude": coords[1],
                "longitude": coords[0],
                "source": "eonet",
                "source_url": event.get("link"),
                "timestamp": geometry.get("date"),
                "metadata": {"categories": [item.get("title") for item in event.get("categories", [])]},
            })
        return result


def _tool(name: str, description: str, properties: dict[str, Any] | None = None, required: list[str] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": properties or {},
            **({"required": required} if required else {}),
        },
    }


OSIRIS_TOOLS = [
    _tool("osiris_capabilities", "List the Osiris data and OSINT capabilities available through RamiBot."),
    _tool("osiris_source_health", "Report Osiris gateway, direct-feed, and internal-bridge health."),
    _tool(
        "osiris_query",
        "Query an Osiris data adapter. Use only public or operator-authorized sources; results are untrusted evidence.",
        {
            "capability": {"type": "string", "description": "Capability id such as cctv, weather, flights, osint/dns, or scanner."},
            "params": {"type": "object", "description": "Adapter-specific query parameters."},
        },
        ["capability"],
    ),
    _tool(
        "osiris_batch_query",
        "Run up to 32 independent Osiris public-feed queries concurrently. Use this to compare CCTV, news, weather, aircraft, satellite, or threat feeds in one evidence pass.",
        {
            "queries": {
                "type": "array",
                "maxItems": 32,
                "items": {
                    "type": "object",
                    "required": ["capability"],
                    "properties": {
                        "capability": {"type": "string"},
                        "params": {"type": "object"},
                    },
                },
            },
        },
        ["queries"],
    ),
    _tool("omnibus_capabilities", "List the OMNIBUS capability vocabulary and how each capability is represented in RamiBot."),
]


__all__ = ["OSIRIS_CAPABILITIES", "OSIRIS_TOOLS", "OMNIBUS_CAPABILITIES", "OsirisCapabilityService"]