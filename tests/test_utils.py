import asyncio
from typing import List

import pytest
from aiochannel import Channel

from pypi_server.utils import join_iterators, fanout_iterators, strict_gather


async def test_strict_gather_cancel():
    async def fail():
        await asyncio.sleep(0.01)
        raise ValueError

    futures = [asyncio.Future() for _ in range(10)]

    for future in futures:
        assert not future.done()

    with pytest.raises(ValueError):
        await strict_gather(fail(), *futures)

    for future in futures:
        assert future.done()


async def test_strict_gather():
    get_num = iter(range(1000))

    async def ok():
        await asyncio.sleep(0.01)
        return next(get_num)

    result = await strict_gather(*[ok() for _ in range(100)])
    assert sorted(result) == list(range(100))


async def test_join_iterators():
    get_num = iter(range(1000000))

    async def iterator():
        for _ in range(100):
            await asyncio.sleep(0)
            yield next(get_num)

    results = []
    async for item in join_iterators(*[iterator() for _ in range(10)]):
        results.append(item)

    results.sort()

    assert results == list(range(1000))


async def test_join_iterators_exc():
    get_num = iter(range(100))

    async def iterator():
        for _ in range(100):
            await asyncio.sleep(0)
            try:
                yield next(get_num)
            except StopIteration:
                raise RuntimeError

    with pytest.raises(RuntimeError):
        async for _ in join_iterators(*[iterator() for _ in range(10)]):
            pass


async def test_fanout_iterators(event_loop: asyncio.AbstractEventLoop):
    channels: List[Channel[int]] = [Channel() for _ in range(10)]

    async def iterator():
        for i in range(100):
            await asyncio.sleep(0)
            yield i

    task = event_loop.create_task(fanout_iterators(iterator(), *channels))

    for channel in channels:
        result = []
        async for item in channel:
            result.append(item)
        assert result == list(range(100))

    await task


async def test_fanout_iterators_close(event_loop: asyncio.AbstractEventLoop):
    channels: List[Channel[int]] = [Channel(1) for _ in range(10)]

    async def iterator():
        for i in range(100):
            await asyncio.sleep(0)
            yield i

    task = event_loop.create_task(fanout_iterators(iterator(), *channels))

    result = []
    for channel in channels:
        async for item in channel:
            result.append(item)
            break
        channel.close()

    await task
    assert result == [0] * len(channels)


