import logging
import uuid
from pathlib import Path

import argclass
from aiomisc import Entrypoint, threaded
from aiomisc.io import async_open

from pypi_server import (
    STORAGES, BytesPayload, Group, Storage, get_parsed_group,
    register_parser_group,
)

from .compat import FAdvice, fadvise, fallocate


log = logging.getLogger(__name__)


def bytes_payload_from_path(path: Path) -> BytesPayload:
    size = path.stat().st_size

    async def iterator():
        async with async_open(path, "rb") as afp:
            await fadvise(afp.fileno(), FAdvice.SEQUENTIAL, length=size)

            chunk = await afp.read(65535)
            while chunk:
                yield chunk
                chunk = await afp.read(65535)

    return BytesPayload(size, iterator())


class LocalStorageArguments(Group):
    """
    This plugin store package files to the local filesystem.
    """

    __plugin_name__ = "Local Storage plugin"

    enabled: bool
    storage_path: Path = argclass.Argument(
        help="Path to store package binaries",
    )
    chunk_size: int = 65535


class LocalStorage(Storage):
    CHUNK_SIZE = 65535

    def __init__(self, storage_path: Path):
        self.path = storage_path.resolve()

    @threaded
    def setup(self) -> None:
        log.info(
            "Setting up %s with path: %s", self.__class__.__name__, self.path,
        )
        self.path.mkdir(mode=0o700, parents=True, exist_ok=True)

    def make_path_from_oid(self, object_id: str) -> Path:
        oid = uuid.uuid5(uuid.NAMESPACE_OID, object_id).hex
        return self.path / oid[0] / oid[1] / oid[2] / oid[3:]

    async def put(self, object_id: str, body: BytesPayload) -> None:
        async with async_open(self.make_path_from_oid(object_id), "wb") as afp:
            await fallocate(afp.fileno(), size=body.size)
            await fadvise(afp.fileno(), FAdvice.SEQUENTIAL, length=body.size)

            async for chunk in body:
                await afp.write(chunk)

    def get(self, object_id: str) -> BytesPayload:
        return bytes_payload_from_path(self.make_path_from_oid(object_id))


def setup() -> None:
    register_parser_group(
        LocalStorageArguments(), name="local_storage",
    )


async def run(_: Entrypoint) -> None:
    group = get_parsed_group(LocalStorageArguments)

    if not group.enabled:
        return

    if not group.storage_path:
        raise RuntimeError(
            "LocalStorage has been enabled but storage path must be provided.",
        )

    LocalStorage.CHUNK_SIZE = group.chunk_size
    storage = LocalStorage(group.storage_path)
    STORAGES.append(storage)
    await storage.setup()
