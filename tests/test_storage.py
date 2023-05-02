import asyncio
import hashlib
from io import BytesIO
from pathlib import Path
from typing import Dict

import aiomisc
import pytest
from aiomisc import threaded_iterable

from pypi_server.storage import BytesPayload, Storage, StorageCollection
from . import file_hash, async_hash


async def test_bytes_payload(sample_file: Path):
    expected_hash = file_hash(sample_file)
    payload = BytesPayload.from_path(sample_file)

    payload_hash = hashlib.blake2s()
    async for line in payload:
        payload_hash.update(line)

    assert expected_hash == payload_hash.hexdigest()


class DummyStorage(Storage):
    def __init__(self):
        self.setup_event = asyncio.Event()
        self.objects: Dict[str, BytesIO] = {}

    async def setup(self) -> None:
        await asyncio.sleep(0)
        self.setup_event.set()

    async def put(self, object_id: str, body: BytesPayload) -> None:
        fp = BytesIO()
        async for chunk in body:
            fp.write(chunk)

        assert fp.tell() == body.size
        fp.seek(0)
        self.objects[object_id] = fp

    def get(self, object_id: str) -> BytesPayload:
        fp = self.objects[object_id]
        size = len(fp.getvalue())

        @threaded_iterable(max_size=128)
        def iterator():
            fp.seek(0)
            yield from fp

        return BytesPayload(size, iterator())


async def test_empty_storage(sample_file: Path):
    storages = StorageCollection()

    oid = "1"

    with pytest.raises(RuntimeError):
        await storages.put(oid, BytesPayload.from_path(sample_file))

    counter = 0
    with pytest.raises(RuntimeError):
        async for _ in storages.get(oid):
            counter += 1

    assert counter == 0


@aiomisc.timeout(2)
async def test_storage(sample_file: Path):
    storages = StorageCollection()

    for _ in range(3):
        storages.append(DummyStorage())

    await storages.setup()

    storage: DummyStorage
    for storage in storages:
        assert storage.setup_event.is_set()

    oid = "1"

    iter_hash = await async_hash(BytesPayload.from_path(sample_file))

    assert iter_hash == file_hash(sample_file)

    await storages.put(oid, BytesPayload.from_path(sample_file))
    assert iter_hash == await async_hash(storages.get(oid))

    for storage in storages:
        assert iter_hash == await async_hash(storage.get(oid))
