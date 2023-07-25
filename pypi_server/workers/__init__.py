import logging
from typing import Any

from aiomisc_dependency import dependency
from patio import AbstractExecutor, AsyncExecutor
from patio.registry import Registry


log = logging.getLogger(__name__)
worker = Registry(project="pypi-server", auto_naming=False)


@worker("ping")
async def ping(**kwargs) -> Any:
    return kwargs


@dependency
async def patio_executor() -> AbstractExecutor:
    executor = AsyncExecutor(worker)
    await executor.setup()

    try:
        yield executor
    finally:
        log.debug("Closing broker %r", executor)
        await executor.shutdown()
