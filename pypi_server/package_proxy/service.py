import logging
import ssl
from typing import Any

import aiohttp
from aiomisc.service.periodic import PeriodicService
from patio import AbstractBroker

from .arguments import PackageProxyArguments
from .simple_provider import parse_simple_packages


log = logging.getLogger(__name__)


class PackageProxySyncer(PeriodicService):
    __required__ = ("arguments",)
    arguments: PackageProxyArguments

    client: aiohttp.ClientSession
    broker: AbstractBroker

    async def start(self) -> None:
        self.client = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                limit=self.arguments.connection_limit,
                ssl_context=ssl.create_default_context(),
            ),
            connector_owner=True,
        )

        log.debug("Waiting active broker")
        self.broker = await self.context["BROKER"]
        log.debug("done")
        return await super().start()

    async def callback(self) -> Any:
        url = self.arguments.url.with_path(self.arguments.simple_list_path)
        async for name, href in parse_simple_packages(url, self.client):
            print(name, href)
        print("done")
