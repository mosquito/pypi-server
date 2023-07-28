import asyncio
import logging
from typing import Iterable, Type

from aiomisc import Entrypoint, Service
from patio import AbstractBroker, AbstractExecutor, AsyncExecutor, MemoryBroker

from pypi_server import Group, Plugin
from pypi_server.dependency import strict_dependency
from pypi_server.plugins import PLUGINS
from pypi_server.workers import rpc


log = logging.getLogger(__name__)


class EmbeddedWorkersArguments(Group):
    """
    Activates workers in the same process as the server is running,
    useful if you don't want to deploy a distributed installation
    and just want to run it as easy as possible
    """

    max_workers: int = 32


class EmbeddedWorkersPlugin(Plugin):
    parser_name = "embedded_workers"
    parser_group = EmbeddedWorkersArguments()

    def declare_dependencies(self) -> None:
        @strict_dependency
        async def patio_executor() -> AbstractExecutor:
            executor = AsyncExecutor(rpc, max_workers=self.group.max_workers)
            await executor.setup()

            try:
                yield executor
            finally:
                await executor.shutdown()

        @strict_dependency
        async def patio_broker(
            patio_executor: AbstractExecutor,
        ) -> AbstractBroker:
            broker = MemoryBroker(patio_executor)
            await broker.setup()

            try:
                yield broker
            finally:
                await broker.close()

    @staticmethod
    async def _run_workers(
        plugin: Plugin, entrypoint: Entrypoint
    ) -> None:
        log.debug("Running workers for plugin: %r", plugin)
        await plugin.run_workers(entrypoint)

    async def run_services(self, entrypoint: Entrypoint) -> None:
        if not self.is_enabled:
            return

        tasks = set()
        loop = asyncio.get_running_loop()

        for plugin in PLUGINS.get():
            if plugin is self:
                continue
            tasks.add(loop.create_task(self._run_workers(plugin, entrypoint)))
        await asyncio.gather(*tasks)


__pypi_server_plugins__: Iterable[Type[Plugin]] = (EmbeddedWorkersPlugin,)
