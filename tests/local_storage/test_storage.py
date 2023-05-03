import hashlib
from pathlib import Path

import pytest
from aiomisc import Entrypoint

from pypi_server import ParserBuilder
from pypi_server.storage import BytesPayload
from pypi_server_local_storage import LocalStorage, LocalStoragePlugin

from .. import file_hash


@pytest.fixture()
async def plugin(
    parser_builder: ParserBuilder, entrypoint: Entrypoint, tmp_path,
) -> LocalStoragePlugin:
    plugin = LocalStoragePlugin(parser_builder)
    plugin.setup()

    parser = parser_builder.build()
    parser.parse_args([
        "--local-storage-enabled",
        f"--local-storage-storage-path={tmp_path}",
    ])
    await plugin.run(entrypoint)
    return plugin


async def test_write(plugin: LocalStorage, sample_file: Path):
    oid = "1"
    expected_hash = file_hash(sample_file)

    for _ in range(2):
        payload = BytesPayload.from_path(sample_file)

        await plugin.put(oid, payload)

        hasher = hashlib.blake2s()
        async for chunk in plugin.get(oid):
            hasher.update(chunk)

        assert hasher.hexdigest() == expected_hash
