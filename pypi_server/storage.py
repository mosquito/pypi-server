import asyncio
from abc import ABC, abstractmethod
from typing import AsyncIterable, Iterable, List

from aiochannel import Channel

from pypi_server.plugin_collection import PluginCollection


class BytesPayload:
    def __init__(self, size: int, payload: AsyncIterable[bytes]):
        self.size: int = size
        self.payload: AsyncIterable[bytes] = payload

    async def __aiter__(self) -> bytes:
        async for chunk in self.payload:
            yield chunk


class Storage(ABC):
    @abstractmethod
    async def setup(self) -> None:
        pass

    @abstractmethod
    async def put(self, object_id: str, body: BytesPayload) -> None:
        pass

    @abstractmethod
    def get(self, object_id: str) -> BytesPayload:
        pass


class Storages(PluginCollection[Storage]):
    STORE_CHUNKS_BUFFER = 64

    async def setup(self) -> None:
        await self.gather("setup")

    @staticmethod
    async def __multiplicator(
        channels: Iterable[Channel[bytes]], body: AsyncIterable[bytes],
    ) -> None:
        try:
            async for chunk in body:
                for ch in channels:
                    await ch.put(chunk)
        finally:
            for ch in channels:
                ch.close()

    async def put(self, object_id: str, body: BytesPayload):
        channels: List[Channel[bytes]] = [
            Channel(self.STORE_CHUNKS_BUFFER) for _ in range(len(self))
        ]

        tasks = [asyncio.create_task(self.__multiplicator(channels, body))]

        for storage, channel in zip(self, channels):
            tasks.append(
                asyncio.create_task(
                    storage.put(object_id, BytesPayload(body.size, channel)),
                ),
            )

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            for channel in channels:
                channel.close()
            raise

    def get(self, object_id: str) -> BytesPayload:
        if not self:
            raise RuntimeError("No storages")
        return self[0].get(object_id)


STORAGES = Storages()

