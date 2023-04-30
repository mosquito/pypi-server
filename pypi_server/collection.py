import asyncio
from typing import Any, AsyncIterable, List, MutableSequence, TypeVar, Union

from aiochannel import Channel

from .utils import fanout_iterators, join_iterators, strict_gather


T = TypeVar("T")
R = TypeVar("R")


class Collection(MutableSequence[T]):
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

    def __getitem__(self, index: int) -> T:
        return self.__items[index]

    async def gather(self, method: str, *args, **kwargs) -> Any:
        futures = [
            getattr(item, method)(*args, **kwargs) for item in self.__items
        ]
        return await strict_gather(*futures)

    async def stream(
        self, method: str, *args: Any, **kwargs: Any
    ) -> AsyncIterable[R]:
        iterators = [getattr(item, method)(*args, **kwargs) for item in self]
        async for item in join_iterators(
            *iterators, stream_buffer=self.STREAM_BUFFER
        ):
            yield item

    async def fanout(
        self, method: str,
        iterator: Union[AsyncIterable[R]],
        *args: Any, **kwargs: Any,
    ) -> None:
        channels: List[Channel[T]] = []
        tasks: List[asyncio.Task] = []

        channel: Channel[T]
        for item in self:
            channel = Channel(self.STREAM_BUFFER)
            channels.append(channel)
            tasks.append(
                asyncio.create_task(
                    getattr(item, method)(channel, *args, **kwargs),
                ),
            )
        await strict_gather(
            fanout_iterators(iterator, *channels),
            *tasks
        )
