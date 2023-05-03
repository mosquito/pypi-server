from typing import Iterable, Type

from aiomisc import Entrypoint
from yarl import URL

from pypi_server import Group, PluginWithArguments, Plugin


class PackageProxyArguments(Group):
    """
    This plugin provides packages information from remote pypi server.
    """

    __plugin_name__ = "Packages Proxy plugin"

    url: URL = "https://pypi.org"
    package_list_path: str = "/simple"
    connection_limit: int = 100


class PackageProxyPlugin(PluginWithArguments):
    parser_name = "package_proxy"
    parser_group = PackageProxyArguments()

    async def on_enabled(
        self, group: PackageProxyArguments, entrypoint: Entrypoint
    ) -> None:
        pass


__pypi_server_plugins__: Iterable[Type[Plugin]] = (PackageProxyPlugin,)
