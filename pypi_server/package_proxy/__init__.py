from typing import Iterable, Type

from aiomisc import Entrypoint

from pypi_server import Plugin

from .arguments import PackageProxyArguments
from .service import PackageProxySyncer, PackageProxySyncerWorker

PARSER_GROUP = PackageProxyArguments()


class PackageProxyPlugin(Plugin):
    parser_name = "package_proxy"
    parser_group = PARSER_GROUP

    async def start_services(self, entrypoint: Entrypoint) -> None:
        await entrypoint.start_services(
            PackageProxySyncer(
                interval=self.group.refresh_interval,
                delay=self.group.refresh_delay,
                arguments=self.group,
            ),
        )

    async def start_workers(self, entrypoint: Entrypoint) -> None:
        await entrypoint.start_services(
            PackageProxySyncerWorker(arguments=self.group),
        )


__pypi_server_plugins__: Iterable[Type[Plugin]] = (PackageProxyPlugin,)
