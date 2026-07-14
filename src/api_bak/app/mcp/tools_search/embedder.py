"""
Embedding 抽象层

支持通过 HTTP 调用兼容 OpenAI 格式的 Embedding 服务（如 Ollama、FastEmbed 等）。
"""
from typing import Protocol, runtime_checkable

import httpx


@runtime_checkable
class Embedder(Protocol):
    """Embedding 服务协议，任何实现 embed() 方法的类均可作为 Embedder 使用"""

    async def embed(self, text: str) -> list[float]: ...


class HttpEmbedder:
    """
    调用兼容 OpenAI `/embeddings` 格式的 HTTP Embedding 服务。
    默认适配 Ollama：POST /api/embeddings
    """

    def __init__(self, url: str, model: str = "bge-small-zh-v1.5"):
        self._url = url
        self._model = model

    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                self._url,
                json={"model": self._model, "input": text},
            )
            resp.raise_for_status()
            data = resp.json()
            # 兼容 OpenAI 格式: {"data": [{"embedding": [...]}]}
            # 兼容 Ollama 格式:   {"embedding": [...]}
            if "data" in data:
                return data["data"][0]["embedding"]
            return data["embedding"]
