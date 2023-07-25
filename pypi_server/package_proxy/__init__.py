from typing import Iterable, Type

from aiomisc import Entrypoint

from pypi_server import Plugin

from .arguments import PackageProxyArguments
from .service import PackageProxySyncer


PARSER_GROUP = PackageProxyArguments()


class PackageProxyPlugin(Plugin):
    parser_name = "package_proxy"
    parser_group = PARSER_GROUP

    async def on_enabled(
        self, group: PackageProxyArguments, entrypoint: Entrypoint,
    ) -> None:
        await entrypoint.start_services(
            PackageProxySyncer(
                interval=group.refresh_interval,
                delay=group.refresh_delay,
                arguments=group,
            ),
        )


class PackageProxyWorkerPlugin(Plugin):
    parser_name = "package_proxy"
    parser_group = PARSER_GROUP

    async def on_enabled(
        self, group: PackageProxyArguments, entrypoint: Entrypoint,
    ) -> None:
        await entrypoint.start_services(
            PackageProxySyncer(
                interval=group.refresh_interval,
                delay=group.refresh_delay,
                arguments=group,
            ),
        )


__pypi_server_plugins__: Iterable[Type[Plugin]] = (
    PackageProxyPlugin,
)
__pypi_server_worker_plugins__: Iterable[Type[Plugin]] = (
    PackageProxyWorkerPlugin,
)
