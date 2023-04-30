import asyncio
from typing import (
    Any, AsyncIterable, List, MutableSequence, Sequence, Set, TypeVar, overload,
)

from aiochannel import Channel


T = TypeVar("T")


class PluginCollection(MutableSequence[T]):
    STREAM_BUFFER = 128

    def __init__(self):
        self.__items: List[T] = []

    def insert(self, index: int, value: T) -> None:
        self.__items.insert(index, value)

    def __setitem__(self, index: int, value: T) -> None:
        self.__items[index] = value

    def __delitem__(self, index: int) -> None:
        del self.__items[index]

    def __len__(self) -> int:
        return len(self.__items)

    @overload
    def __getitem__(self, index: slice) -> Sequence[T]:
        return self.__items[index]

    @overload
    def __getitem__(self, index: int) -> T:
        return self.__items[index]

    def __getitem__(self, index: int) -> T: ...

    async def gather(self, method: str, *args, **kwargs) -> None:
        await asyncio.gather(
            *[
                getattr(item, method)(*args, **kwargs) for item in self.__items
            ]
        )

    def stream(
        self, method: str, *args: Any, **kwargs: Any
    ) -> AsyncIterable[T]:
        results: Channel[T] = Channel(self.STREAM_BUFFER)
        iterators: Set[asyncio.Task] = set()

        async def iterator(iterable: AsyncIterable[T]) -> None:
            nonlocal results
            async for element in iterable:
                await results.put(element)

        for item in self:
            iterators.add(
                asyncio.create_task(
                    iterator(
                        getattr(item, method)(*args, **kwargs),
                    ),
                ),
            )

        async def waiter():
            try:
                await asyncio.gather(*iterators)
            finally:
                results.close()

        async def streamer() -> AsyncIterable[T]:
            waiter_task = asyncio.create_task(waiter())
            try:
                async for element in results:
                    yield element
            except asyncio.CancelledError:
                waiter_task.cancel()
                raise
            else:
                await waiter_task

        return streamer()
