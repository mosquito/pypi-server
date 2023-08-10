import logging
from pathlib import Path
from typing import Iterable, Type

import aiohttp.log
import aiomisc
import argclass
from aiomisc import Entrypoint

from pypi_server import Group, Plugin

from .service import HTTPService


log = logging.getLogger(__name__)


class HTTPArguments(Group):
    __plugin_name__ = "HTTP server plugin"
    __doc__ = (Path(__file__).parent / "README.md").open().read()

    enabled: bool = False
    address: str = argclass.Argument(
        "-l", "--http-address", help="HTTP Listen address", default="::",
    )
    port: int = argclass.Argument(
        "-p", "--http-port", default=8998, help="HTTP Listen port",
    )
    access_log_level = argclass.LogLevel
    server_log_level = argclass.LogLevel
    web_log_level = argclass.LogLevel
    ws_log_level = argclass.LogLevel


class HTTPPlugin(Plugin):
    parser_name = "http"
    parser_group = HTTPArguments()
    readme = (Path(__file__).parent / "README.md").open().read()

    async def start_services(self) -> Iterable[aiomisc.Service]:
        aiohttp.log.access_logger.setLevel(self.group.access_log_level)
        aiohttp.log.server_logger.setLevel(self.group.server_log_level)
        aiohttp.log.web_logger.setLevel(self.group.web_log_level)
        aiohttp.log.ws_logger.setLevel(self.group.ws_log_level)

        return [
            HTTPService(address=self.group.address, port=self.group.port)
        ]


__pypi_server_plugins__: Iterable[Type[Plugin]] = (HTTPPlugin,)
