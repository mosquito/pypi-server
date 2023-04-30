import asyncio
from typing import (
    Any, AsyncIterable, List, MutableSequence, Sequence, Set, TypeVar, overload,
)

from aiochannel import Channel

from .utils import strict_gather, join_iterators

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

    def __getitem__(self, index: int) -> T:
        return self.__items[index]

    async def gather(self, method: str, *args, **kwargs) -> Any:
        futures = [
            getattr(item, method)(*args, **kwargs) for item in self.__items
        ]
        return await strict_gather(*futures)

    async def stream(
        self, method: str, *args: Any, **kwargs: Any
    ) -> AsyncIterable[T]:
        iterators = [getattr(item, method)(*args, **kwargs) for item in self]
        async for item in join_iterators(
            *iterators, stream_buffer=self.STREAM_BUFFER
        ):
            yield item
