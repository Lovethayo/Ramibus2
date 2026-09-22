"""Lazy dual-model llama.cpp adapter for the two workspace GGUF files."""

import asyncio
import json
import os
import signal
from pathlib import Path
from typing import AsyncGenerator

import httpx

from .base import BaseAdapter


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
LLAMA_SERVER = Path(
    os.environ.get("RAMIBUS_LLAMA_SERVER", str(WORKSPACE_ROOT / "llama.cpp" / "build" / "bin" / "llama-server"))
)


class LocalGGUFAdapter(BaseAdapter):
    provider_name = "local_gguf"

    def __init__(self, **settings):
        self.host = settings.get("host", "127.0.0.1")
        self.base_port = int(settings.get("base_port", os.environ.get("RAMIBUS_GGUF_BASE_PORT", "8100")))
        models_dir = Path(settings.get("models_dir", str(WORKSPACE_ROOT / "models")))
        self.profiles = {
            "rami-planner": {
                "id": "rami-planner",
                "name": "R1 Planner · DeepSeek-R1 Distill Qwen 1.5B",
                "role": "planner",
                "path": str(models_dir / "DeepSeek-R1-Distill-Qwen-1.5B-Q8_0.gguf"),
                "port": self.base_port,
            },
            "rami-tradecraft": {
                "id": "rami-tradecraft",
                "name": "Tradecraft · Llama 3.2 3B Instruct",
                "role": "tradecraft",
                "path": str(models_dir / "Llama-3.2-3B-Instruct-abliterated.Q6_K.gguf"),
                "port": self.base_port + 1,
            },
        }
        self.processes: dict[str, asyncio.subprocess.Process] = {}
        self._lock = asyncio.Lock()

    async def capabilities(self) -> dict:
        return {
            "streaming": True,
            "tool_calling": True,
            "reasoning": True,
            "models": list(self.profiles),
            "hot_swap": True,
            "parallel_slots": 2,
            "routing": "deterministic role ownership",
        }

    async def list_models(self) -> list[dict]:
        return [
            {
                "id": profile["id"],
                "name": profile["name"],
                "role": profile["role"],
                "available": Path(profile["path"]).exists(),
                "runtime": "llama.cpp",
            }
            for profile in self.profiles.values()
        ]

    async def _ensure_server(self, model: str) -> dict:
        profile = self.profiles.get(model) or self.profiles["rami-planner"]
        if not Path(profile["path"]).exists():
            raise RuntimeError(f"Local model file is missing: {profile['path']}")
        if not LLAMA_SERVER.exists():
            raise RuntimeError(f"llama-server is missing: {LLAMA_SERVER}")

        process = self.processes.get(profile["id"])
        if process and process.returncode is None:
            return profile

        async with self._lock:
            process = self.processes.get(profile["id"])
            if process and process.returncode is None:
                return profile
            process = await asyncio.create_subprocess_exec(
                str(LLAMA_SERVER),
                "--model", profile["path"],
                "--alias", profile["id"],
                "--host", self.host,
                "--port", str(profile["port"]),
                "--ctx-size", os.environ.get("RAMIBUS_GGUF_CTX", "4096"),
                "--no-webui",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=True,
            )
            self.processes[profile["id"]] = process

        url = f"http://{self.host}:{profile['port']}/health"
        last_error = "server did not become ready"
        async with httpx.AsyncClient(timeout=3) as client:
            for _ in range(60):
                if process.returncode is not None:
                    stderr = await process.stderr.read() if process.stderr else b""
                    detail = stderr.decode("utf-8", errors="replace").strip()
                    raise RuntimeError(detail or last_error)
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        return profile
                    last_error = f"llama-server health returned {response.status_code}"
                except Exception as error:
                    last_error = str(error)
                await asyncio.sleep(1)
        raise RuntimeError(last_error)

    async def shutdown(self):
        for process in self.processes.values():
            if process.returncode is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        for process in self.processes.values():
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except Exception:
                if process.returncode is None:
                    process.kill()
        self.processes.clear()

    async def generate(self, messages: list[dict], model: str, **kwargs) -> dict:
        profile = await self._ensure_server(model)
        payload = {"model": profile["id"], "messages": messages}
        if kwargs.get("tools"):
            payload["tools"] = kwargs["tools"]
        async with httpx.AsyncClient(timeout=httpx.Timeout(300, connect=10)) as client:
            response = await client.post(
                f"http://{self.host}:{profile['port']}/v1/chat/completions",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        tool_calls = [
            {
                "id": item.get("id", f"call_{index}"),
                "name": item.get("function", {}).get("name", ""),
                "arguments": item.get("function", {}).get("arguments", "{}"),
            }
            for index, item in enumerate(message.get("tool_calls") or [])
        ] or None
        return {
            "content": message.get("content", "") or "",
            "role": "assistant",
            "token_usage": data.get("usage", {}),
            "tool_calls": tool_calls,
        }

    async def stream(self, messages: list[dict], model: str, **kwargs) -> AsyncGenerator[dict, None]:
        profile = await self._ensure_server(model)
        payload = {"model": profile["id"], "messages": messages, "stream": True}
        if kwargs.get("tools"):
            payload["tools"] = kwargs["tools"]
        tool_calls: dict[int, dict] = {}
        async with httpx.AsyncClient(timeout=httpx.Timeout(300, connect=10)) as client:
            async with client.stream(
                "POST",
                f"http://{self.host}:{profile['port']}/v1/chat/completions",
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    raw = line[6:]
                    if raw == "[DONE]":
                        for call in tool_calls.values():
                            yield {"type": "tool_call", "data": call}
                        yield {"type": "done", "data": None}
                        return
                    try:
                        chunk = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    choice = (chunk.get("choices") or [{}])[0]
                    delta = choice.get("delta", {})
                    for item in delta.get("tool_calls") or []:
                        index = item.get("index", 0)
                        call = tool_calls.setdefault(index, {"id": f"call_{index}", "name": "", "arguments": ""})
                        if item.get("id"):
                            call["id"] = item["id"]
                        call["name"] += item.get("function", {}).get("name", "")
                        call["arguments"] += item.get("function", {}).get("arguments", "")
                    if delta.get("content"):
                        yield {"type": "token", "data": delta["content"]}
                    if chunk.get("usage"):
                        yield {"type": "usage", "data": chunk["usage"]}