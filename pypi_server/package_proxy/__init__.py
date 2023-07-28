from typing import Iterable, Type

from aiomisc import Entrypoint, Service

from pypi_server import Plugin

from .arguments import PackageProxyArguments
from .service import PackageProxySyncer, PackageProxySyncerWorker

PARSER_GROUP = PackageProxyArguments()


class PackageProxyPlugin(Plugin):
    parser_name = "package_proxy"
    parser_group = PARSER_GROUP

    async def start_services(self) -> Iterable[Service]:
        return [
            PackageProxySyncer(
                interval=self.group.refresh_interval,
                delay=self.group.refresh_delay,
                arguments=self.group,
            )
        ]

    async def start_workers(self) -> Iterable[Service]:
        return [PackageProxySyncerWorker(arguments=self.group)]


__pypi_server_plugins__: Iterable[Type[Plugin]] = (PackageProxyPlugin,)
