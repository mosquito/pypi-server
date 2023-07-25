from typing import Iterable, Type

from patio import AbstractBroker, AbstractExecutor, MemoryBroker

from pypi_server import Group, Plugin
from pypi_server.dependency import strict_dependency


class EmbeddedWorkersArguments(Group):
    """
    Activates workers in the same process as the server is running,
    useful if you don't want to deploy a distributed installation
    and just want to run it as easy as possible
    """


class EmbeddedWorkersPlugin(Plugin):
    parser_name = "embedded_workers"
    parser_group = EmbeddedWorkersArguments()

    def declare_dependencies(self, group: EmbeddedWorkersArguments) -> None:
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


__pypi_server_plugins__: Iterable[Type[Plugin]] = (EmbeddedWorkersPlugin,)
