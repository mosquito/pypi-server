from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncIterable, AsyncIterator

from aiomisc.io import async_open


class BytesPayload:
    def __init__(self, size: int, payload: AsyncIterable[bytes]):
        self.size: int = size
        self.payload: AsyncIterable[bytes] = payload

    async def __aiter__(self) -> AsyncIterator[bytes]:
        async for chunk in self.payload:
            yield chunk

    @classmethod
    def from_iterator(
        cls, size: int, iterator: AsyncIterable[bytes],
    ) -> BytesPayload:
        return cls(size, iterator)

    @classmethod
    def from_path(
        cls, path: Path, chunk_size: int = 65535,
    ) -> BytesPayload:
        async def iterator() -> AsyncIterable[bytes]:
            async with async_open(path, "rb") as afp:
                chunk = await afp.read(chunk_size)
                while chunk:
                    yield chunk
                    chunk = await afp.read(chunk_size)
        return cls.from_iterator(path.stat().st_size, iterator())


class Storage(ABC):
    @abstractmethod
    async def setup(self) -> None: ...

    @abstractmethod
    async def put(self, object_id: str, body: BytesPayload) -> None: ...

    @abstractmethod
    def get(self, object_id: str) -> BytesPayload: ...
