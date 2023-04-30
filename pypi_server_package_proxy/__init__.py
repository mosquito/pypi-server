from aiomisc import Entrypoint
from yarl import URL

from pypi_server import Group, get_parsed_group, register_parser_group


class PackageProxyArguments(Group):
    """
    This plugin provides packages information from remote pypi server.
    """

    __plugin_name__ = "Packages Proxy plugin"

    url: URL = "https://pypi.org"
    package_list_path: str = "/simple"
    connection_limit: int = 100


def setup() -> None:
    register_parser_group(PackageProxyArguments(), name="package_proxy")


async def run(entrypoint: Entrypoint) -> None:
    group = get_parsed_group(PackageProxyArguments)
    if not group.enabled:
        return
