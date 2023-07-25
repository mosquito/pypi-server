from pathlib import Path

from yarl import URL

from pypi_server import Group


class PackageProxyArguments(Group):
    __doc__ = (Path(__file__).parent / "README.md").open().read()
    __plugin_name__ = "Packages Proxy plugin"

    url: URL = "https://pypi.org"
    connection_limit: int = 100

    refresh_interval: float = 300.
    refresh_delay: float = 0.

    simple_list_path: str = "/simple/"

    rss_prefix: str = "/rss/"
    rss_project_prefix: str = "/rss/project/"
    rss_project_suffix: str = "releases.xml"
