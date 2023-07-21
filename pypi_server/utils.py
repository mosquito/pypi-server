import asyncio
from contextvars import ContextVar
from typing import (
    Any, AsyncIterable, Coroutine, Generic, Optional, Set, TypeVar, Union,
)

from aiochannel import Channel


T = TypeVar("T")


async def strict_gather(
    *coroutines: Union[asyncio.Future[T], Coroutine[Any, Any, T]]
) -> T:
    futures = [asyncio.ensure_future(coro) for coro in coroutines]

    try:
        return await asyncio.gather(*futures)
    except Exception as e:
        errors = []
        pending = []

        for task in futures:
            if task.done():
                if task.exception():
                    errors.append(task)
                continue
            task.cancel()
            pending.append(task)

        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

        if errors:
            raise errors[0].exception() from e
        raise


def join_iterators(
    *iterators: AsyncIterable[T], stream_buffer: int = 128
) -> AsyncIterable[T]:
    results: Channel[T] = Channel(stream_buffer)
    tasks: Set[asyncio.Task] = set()

    async def iterator(iterable: AsyncIterable[T]) -> None:
        nonlocal results
        async for element in iterable:
            await results.put(element)

    for item in iterators:
        tasks.add(asyncio.create_task(iterator(item)))

    async def waiter():
        try:
            await strict_gather(*tasks)
        finally:
            results.close()

    async def streamer() -> AsyncIterable[T]:
        waiter_task = asyncio.create_task(waiter())
        try:
            async for element in results:
                yield element
        except asyncio.CancelledError:
            if not waiter_task.done():
                waiter_task.cancel()
                await asyncio.gather(waiter_task, return_exceptions=True)
            raise
        else:
            await waiter_task

    return streamer()


async def fanout_iterators(src: AsyncIterable[T], *dest: Channel[T]) -> None:
    targets: Set[Channel[T]] = set(dest)

    try:
        closed: Set[Channel[T]]
        async for item in src:
            closed = set()
            if not targets:
                return

            for target in targets:
                if target.closed():
                    closed.add(target)
                    continue
                await target.put(item)

            if closed:
                targets -= closed
    finally:
        for target in targets:
            target.close()


class StrictContextVar(Generic[T]):
    def __init__(self, name: str, exc: Exception):
        self.exc: Exception = exc
        self.context_var: ContextVar = ContextVar(name)

    def get(self) -> T:
        value: Optional[T] = self.context_var.get(None)
        if value is None:
            raise self.exc
        return value

    def set(self, value: T) -> None:
        self.context_var.set(value)

    @property
    def current(self) -> T:
        return self.get()
