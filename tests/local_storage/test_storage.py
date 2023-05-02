import hashlib
from pathlib import Path

import aiomisc
import pytest

from pypi_server.storage import BytesPayload
from pypi_server_local_storage import LocalStorage, run, setup

from .. import file_hash


@pytest.fixture()
async def local_storage(tmp_path) -> LocalStorage:
    storage = LocalStorage(tmp_path)
    await storage.setup()
    return storage


async def test_write(local_storage: LocalStorage, sample_file: Path):
    oid = "1"
    expected_hash = file_hash(sample_file)

    for _ in range(2):
        payload = BytesPayload.from_path(sample_file)

        await local_storage.put(oid, payload)

        hasher = hashlib.blake2s()
        async for chunk in local_storage.get(oid):
            hasher.update(chunk)

        assert hasher.hexdigest() == expected_hash


async def test_run(parser, entrypoint: aiomisc.Entrypoint):
    setup()
    await run(entrypoint)
