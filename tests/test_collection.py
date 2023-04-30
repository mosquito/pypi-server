import asyncio
from typing import AsyncIterable

import pytest
from pytest_subtests import SubTests

from pypi_server import Collection


class SamplePlugin:
    def __init__(self):
        self.failing = False
        self.future: asyncio.Future = asyncio.Future()

    async def get_id(self) -> int:
        await asyncio.sleep(0)
        return id(self)

    async def wait_state(self) -> None:
        await asyncio.sleep(0)
        if self.failing:
            raise ValueError

    async def wait_forever(self):
        if self.failing:
            await asyncio.sleep(0.01)
            raise ValueError()

        loop = asyncio.get_running_loop()
        self.future = loop.create_future()
        try:
            await self.future
        except asyncio.CancelledError:
            raise

    async def get_stream(self):
        if self.failing:
            await asyncio.sleep(0)
            raise ValueError

        for i in range(10):
            await asyncio.sleep(0)
            yield i

    async def get_sum(self, iterable: AsyncIterable[int], expected: int):
        result = 0

        async for item in iterable:
            result += item

        assert result == expected


class SampleCollection(Collection[SamplePlugin]):
    pass


async def test_suites(subtests: SubTests):
    collection = SampleCollection()
    plugins = [SamplePlugin() for _ in range(10)]

    with subtests.test():
        for plugin in plugins:
            collection.append(plugin)

        collection[0] = plugins[0]
        assert collection[1] == plugins[1]
        assert collection[0:2] == plugins[0:2]

    with subtests.test():
        ids = await collection.gather("get_id")
        assert set(ids) == set(id(plugin) for plugin in plugins)

    with subtests.test():
        assert await collection.gather("wait_state")
        collection[0].failing = True

        with pytest.raises(ValueError):
            assert await collection.gather("wait_state")

        collection[0].failing = False
        assert await collection.gather("wait_state")

    with subtests.test():
        collection[0].failing = True

        with pytest.raises(ValueError):
            assert await collection.gather("wait_forever")

        for item in collection[1:]:
            assert item.future.done()

            with pytest.raises(asyncio.CancelledError):
                assert item.future.result()

    with subtests.test():
        collection[0].failing = False

        results = []
        async for item in collection.stream("get_stream"):
            results.append(item)
        results.sort()

        assert results == sorted(list(range(10)) * len(collection))

    with subtests.test():
        collection[0].failing = True

        with pytest.raises(ValueError):
            async for _ in collection.stream("get_stream"):
                pass

    with subtests.test():
        iterations = 100

        async def iterator():
            for i in range(iterations):
                await asyncio.sleep(0)
                yield i

        await collection.fanout("get_sum", iterator(), sum(range(100)))

