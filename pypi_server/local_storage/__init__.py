import logging
import uuid
from pathlib import Path
from typing import Iterable, Type

import argclass
from aiomisc import threaded
from aiomisc.io import async_open

from pypi_server import BytesPayload, Group, Plugin, Storage
from pypi_server.plugins import ConfigurationError

from ..dependency import strict_dependency
from .compat import FAdvice, fadvise, fallocate


log = logging.getLogger(__name__)


class LocalStorageArguments(Group):
    __doc__ = (Path(__file__).parent / "README.md").open().read()
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
            "Setting up '%s' in: %s", self.__class__.__name__, self.path,
        )
        self.path.mkdir(mode=0o700, parents=True, exist_ok=True)

    def make_path_from_oid(self, object_id: str) -> Path:
        oid = uuid.uuid5(uuid.NAMESPACE_OID, object_id).hex
        return self.path / oid[0] / oid[1] / oid[2] / oid[3:]

    @threaded
    def _mkdir(self, path: Path) -> None:
        parent = path.parent
        if parent.is_dir():
            return
        parent.mkdir(mode=0o750, parents=True, exist_ok=True)

    # noinspection PyUnresolvedReferences
    async def put(self, object_id: str, body: BytesPayload) -> None:
        path = self.make_path_from_oid(object_id)
        await self._mkdir(path)

        async with async_open(path, "wb") as afp:
            await fallocate(afp.fileno(), size=body.size)
            await fadvise(afp.fileno(), FAdvice.SEQUENTIAL, length=body.size)

            async for chunk in body:
                await afp.write(chunk)

    def get(self, object_id: str) -> BytesPayload:
        return BytesPayload.from_path(self.make_path_from_oid(object_id))


class LocalStoragePlugin(Plugin):
    parser_name = "local_storage"
    parser_group = LocalStorageArguments()

    def declare_dependencies(self) -> None:

        @strict_dependency
        async def blob_storage() -> LocalStorage:
            if not self.group.storage_path:
                raise ConfigurationError(
                    msg=(
                        "LocalStorage has been enabled by "
                        "\"--local-storage-enabled\" but "
                        "storage path must be provided"
                    ),
                    hint="Specify '--local-storage-storage-path' option",
                )

            LocalStorage.CHUNK_SIZE = self.group.chunk_size
            storage = LocalStorage(self.group.storage_path)
            # noinspection PyUnresolvedReferences
            await storage.setup()
            return storage


__pypi_server_plugins__: Iterable[Type[Plugin]] = (LocalStoragePlugin,)
