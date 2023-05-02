import hashlib
from pathlib import Path
from typing import IO, AsyncIterable


def io_hash(fp: IO[bytes]) -> str:
    hasher = hashlib.blake2s()
    for line in fp:
        hasher.update(line)
    return hasher.hexdigest()


def file_hash(path: Path) -> str:
    with path.open("rb") as fp:
        return io_hash(fp)


async def async_hash(iterator: AsyncIterable[bytes]) -> str:
    hasher = hashlib.blake2s()
    async for chunk in iterator:
        hasher.update(chunk)
    return hasher.hexdigest()
