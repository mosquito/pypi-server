from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncIterable, List

from aiochannel import Channel
from aiomisc import StrictContextVar
from aiomisc.io import async_open

from .collection import Collection
from .utils import fanout_iterators, strict_gather


class BytesPayload:
    def __init__(self, size: int, payload: AsyncIterable[bytes]):
        self.size: int = size
        self.payload: AsyncIterable[bytes] = payload

    async def __aiter__(self) -> bytes:
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


class StorageCollection(Collection[Storage]):
    STORE_CHUNKS_BUFFER = 64

    async def setup(self) -> None:
        await self.gather("setup")

    async def put(
        self, object_id: str, body: BytesPayload,
        buffer: int = STORE_CHUNKS_BUFFER,
    ) -> None:
        if not self:
            raise RuntimeError("No storages")

        channels: List[Channel[bytes]] = []
        tasks: List[asyncio.Task[None]] = []

        for storage in self:
            channel = Channel(buffer)
            payload = BytesPayload(body.size, channel)
            task = asyncio.create_task(storage.put(object_id, payload))
            tasks.append(task)
            channels.append(channel)

        fanout = asyncio.create_task(fanout_iterators(body, *channels))
        try:
            await strict_gather(fanout, *tasks)
        finally:
            for channel in channels:
                channel.close()

    def get(self, object_id: str) -> BytesPayload:
        if not self:
            raise RuntimeError("No storages")
        return self[0].get(object_id)


STORAGES: StrictContextVar[StorageCollection] = StrictContextVar(
    "STORAGES", RuntimeError("Storage collection has not been initialized"),
)
