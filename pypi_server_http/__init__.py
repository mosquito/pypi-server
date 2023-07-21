import logging
from typing import Iterable, Type

import aiohttp.log
import argclass
from aiomisc import Entrypoint

from pypi_server import Group, Plugin, PluginWithArguments

from .service import HTTPService


log = logging.getLogger(__name__)


class HTTPArguments(Group):
    """
    This plugin is the HTTP server
    """

    __plugin_name__ = "HTTP server plugin"

    enabled: bool
    address: str = argclass.Argument(
        "-l", "--http-address", help="HTTP Listen address", default="::"
    )
    port: int = argclass.Argument(
        "-p", "--http-port", default=8998, help="HTTP Listen port",
    )
    access_log_level = argclass.LogLevel
    server_log_level = argclass.LogLevel
    web_log_level = argclass.LogLevel
    ws_log_level = argclass.LogLevel


class HTTPPlugin(PluginWithArguments):
    parser_name = "http"
    parser_group = HTTPArguments()

    async def on_enabled(
        self, group: HTTPArguments, entrypoint: Entrypoint,
    ) -> None:
        aiohttp.log.access_logger.setLevel(group.access_log_level)
        aiohttp.log.server_logger.setLevel(group.server_log_level)
        aiohttp.log.web_logger.setLevel(group.web_log_level)
        aiohttp.log.ws_logger.setLevel(group.ws_log_level)

        await entrypoint.start_services(
            HTTPService(
                address=group.address,
                port=group.port,

            ),
        )


__pypi_server_plugins__: Iterable[Type[Plugin]] = (HTTPPlugin,)
