import asyncio

import pytest
from pytest_subtests import SubTests

from pypi_server import PluginCollection


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


class SamplePluginCollection(PluginCollection[SamplePlugin]):
    pass


async def test_suites(subtests: SubTests):
    collection = SamplePluginCollection()
    plugins = [SamplePlugin() for _ in range(10)]

    for plugin in plugins:
        collection.append(plugin)

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
