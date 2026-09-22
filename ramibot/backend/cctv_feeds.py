"""Public/authorized CCTV catalog adapters derived from the OSIRIS sources.

These are camera indexes and refreshing public images, not covert access. The
adapter never accepts an arbitrary URL and never probes a private network.
"""

import asyncio
import time
from typing import Any

import httpx


SOURCE_ENDPOINTS = {
    "tfl": "https://api.tfl.gov.uk/Place/Type/JamCam",
    "wsdot": "https://data.wsdot.wa.gov/log/public/cameras.json",
    "caltrans": "https://caltrans-gis.dot.ca.gov/arcgis/rest/services/CHhighway/CCTV/FeatureServer/0/query?where=1%3D1&outFields=*&f=json",
    "singapore": "https://api.data.gov.sg/v1/transport/traffic-images",
}


class CCTVFeedService:
    def __init__(self):
        self.cameras: list[dict] = []
        self.fetched_at = 0.0
        self.expires_at = 0.0
        self.status = "UNKNOWN"
        self.last_error = ""
        self.source_counts: dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def _get_json(self, url: str) -> Any:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(15, connect=5),
            headers={"User-Agent": "RamiBot-CCTV-Gateway/1.0"},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def _fetch_tfl(self) -> list[dict]:
        payload = await self._get_json(SOURCE_ENDPOINTS["tfl"])
        cameras = []
        for item in payload or []:
            image = next(
                (prop.get("value") for prop in item.get("additionalProperties", [])
                 if prop.get("key") == "imageUrl"),
                "",
            )
            camera_id = str(item.get("id", "")).replace("JamCams_", "")
            if item.get("lat") is None or item.get("lon") is None or not image:
                continue
            cameras.append(self._camera(
                f"tfl-{item.get('id')}", item.get("commonName") or "London JamCam",
                item["lat"], item["lon"], image, "TfL",
                "https://tfl.gov.uk/modes/driving/cameras",
                city="London", country="UK", metadata={"camera_key": camera_id},
            ))
        return cameras

    async def _fetch_wsdot(self) -> list[dict]:
        payload = await self._get_json(SOURCE_ENDPOINTS["wsdot"])
        cameras = []
        for item in payload or []:
            location = item.get("CameraLocation") or {}
            latitude, longitude, image = location.get("Latitude"), location.get("Longitude"), item.get("ImageURL")
            if latitude is None or longitude is None or not image:
                continue
            cameras.append(self._camera(
                f"wsdot-{item.get('CameraID')}", item.get("Title") or "WSDOT Camera",
                latitude, longitude, image, "WSDOT",
                "https://wsdot.wa.gov/travel/real-time/traffic-cameras",
                city="Washington", country="US",
            ))
        return cameras

    async def _fetch_caltrans(self) -> list[dict]:
        payload = await self._get_json(SOURCE_ENDPOINTS["caltrans"])
        cameras = []
        for feature in payload.get("features", []):
            attrs = feature.get("attributes") or {}
            latitude, longitude, image = attrs.get("latitude"), attrs.get("longitude"), attrs.get("currentImageURL")
            if latitude is None or longitude is None or not image:
                continue
            cameras.append(self._camera(
                f"caltrans-{attrs.get('OBJECTID')}", attrs.get("locationName") or "Caltrans Camera",
                latitude, longitude, image, "Caltrans",
                "https://quickmap.dot.ca.gov/",
                city=attrs.get("nearbyPlace") or attrs.get("county") or "California",
                country="US",
            ))
        return cameras

    async def _fetch_singapore(self) -> list[dict]:
        payload = await self._get_json(SOURCE_ENDPOINTS["singapore"])
        items = (payload.get("items") or [{}])[0].get("cameras") or []
        cameras = []
        for item in items:
            location = item.get("location") or {}
            latitude, longitude, image = location.get("latitude"), location.get("longitude"), item.get("image")
            if latitude is None or longitude is None or not image:
                continue
            camera_id = item.get("camera_id")
            cameras.append(self._camera(
                f"singapore-{camera_id}", f"Singapore Traffic Camera {camera_id}",
                latitude, longitude, image, "LTA Singapore",
                "https://datamall.lta.gov.sg/content/datamall/en.html",
                city="Singapore", country="Singapore",
            ))
        return cameras

    async def refresh(self, force: bool = False) -> list[dict]:
        if self.cameras and not force and time.time() < self.expires_at:
            return self.cameras
        async with self._lock:
            if self.cameras and not force and time.time() < self.expires_at:
                return self.cameras
            results = await asyncio.gather(
                self._safe_source("tfl", self._fetch_tfl),
                self._safe_source("wsdot", self._fetch_wsdot),
                self._safe_source("caltrans", self._fetch_caltrans),
                self._safe_source("singapore", self._fetch_singapore),
            )
            cameras = [camera for result in results for camera in result]
            if cameras or not self.cameras:
                self.cameras = cameras
            self.fetched_at = time.time()
            self.expires_at = self.fetched_at + 300
            self.status = "ONLINE" if cameras else ("STALE" if self.cameras else "OFFLINE")
            return self.cameras

    async def _safe_source(self, source_id: str, fetcher) -> list[dict]:
        try:
            cameras = await fetcher()
            self.source_counts[source_id] = len(cameras)
            return cameras
        except Exception as error:
            self.source_counts[source_id] = 0
            self.last_error = f"{source_id}: {error}"
            return []

    async def search(self, query: str = "", limit: int = 100) -> list[dict]:
        cameras = await self.refresh()
        needle = (query or "").strip().lower()
        if needle:
            cameras = [
                camera for camera in cameras
                if needle in " ".join(
                    str(camera.get(field, "")) for field in ("name", "city", "country", "source")
                ).lower()
            ]
        return cameras[: max(1, min(limit, 1000))]

    async def nearby(self, latitude: float, longitude: float, radius_km: float = 25, limit: int = 100) -> list[dict]:
        cameras = await self.refresh()
        result = []
        for camera in cameras:
            distance = self._distance_km(latitude, longitude, camera["latitude"], camera["longitude"])
            if distance <= radius_km:
                item = dict(camera)
                item["metadata"] = {**item.get("metadata", {}), "distance_km": round(distance, 2)}
                result.append(item)
        result.sort(key=lambda camera: camera["metadata"]["distance_km"])
        return result[: max(1, min(limit, 1000))]

    async def get(self, camera_id: str) -> dict | None:
        for camera in await self.refresh():
            if camera["id"] == camera_id:
                return camera
        return None

    def health(self) -> dict:
        now = time.time()
        status = self.status
        if self.cameras and self.expires_at and now >= self.expires_at and status == "ONLINE":
            status = "STALE"
        return {
            "id": "cctv",
            "source_id": "cctv",
            "status": status,
            "count": len(self.cameras),
            "fetched_at": self.fetched_at or None,
            "age_seconds": round(now - self.fetched_at, 1) if self.fetched_at else None,
            "last_error": self.last_error or None,
            "key_required": False,
            "subsources": self.source_counts,
        }

    async def call_tool(self, name: str, arguments: dict) -> Any:
        if name in {"cctv_search", "cctv_latest"}:
            return await self.search(arguments.get("query", ""), int(arguments.get("limit", 100)))
        if name == "cctv_nearby":
            return await self.nearby(
                float(arguments["latitude"]),
                float(arguments["longitude"]),
                float(arguments.get("radius_km", 25)),
                int(arguments.get("limit", 100)),
            )
        if name == "cctv_get":
            camera = await self.get(str(arguments["camera_id"]))
            if not camera:
                raise ValueError("CCTV camera not found")
            return camera
        if name == "cctv_status":
            await self.refresh()
            return self.health()
        raise ValueError(f"Unknown CCTV tool: {name}")

    @staticmethod
    def _camera(camera_id, name, latitude, longitude, feed_url, source, source_url, **extra):
        return {
            "id": camera_id,
            "type": "camera",
            "name": name,
            "latitude": float(latitude),
            "longitude": float(longitude),
            "altitude": None,
            "city": extra.pop("city", ""),
            "country": extra.pop("country", ""),
            "source": source,
            "source_url": source_url,
            "status": "active",
            "timestamp": int(time.time() * 1000),
            "feed_url": feed_url,
            "stream_url": None,
            "stream_type": "jpg",
            "external_url": source_url,
            "metadata": extra.pop("metadata", {}),
        }

    @staticmethod
    def _distance_km(lat1, lng1, lat2, lng2):
        radius = 6371
        phi1, phi2 = __import__("math").radians(lat1), __import__("math").radians(lat2)
        d_phi = __import__("math").radians(lat2 - lat1)
        d_lambda = __import__("math").radians(lng2 - lng1)
        value = __import__("math").sin(d_phi / 2) ** 2 + __import__("math").cos(phi1) * __import__("math").cos(phi2) * __import__("math").sin(d_lambda / 2) ** 2
        return 2 * radius * __import__("math").asin(min(1, __import__("math").sqrt(value)))


CCTV_TOOLS = [
    {
        "name": "cctv_search",
        "description": "Search the indexed public CCTV catalog by city, country, or source.",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}},
    },
    {
        "name": "cctv_nearby",
        "description": "Find public CCTV camera snapshots near a coordinate.",
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
        "name": "cctv_get",
        "description": "Get one public CCTV camera's metadata and current feed URL.",
        "inputSchema": {"type": "object", "required": ["camera_id"], "properties": {"camera_id": {"type": "string"}}},
    },
    {
        "name": "cctv_status",
        "description": "Report public CCTV catalog freshness and provider health.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]