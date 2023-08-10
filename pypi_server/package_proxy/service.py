import logging
import ssl
from typing import Any, List

import aiohttp
from aiomisc.service import Service
from aiomisc.service.periodic import PeriodicService
from patio import AbstractBroker

from pypi_server.workers import rpc

from .arguments import PackageProxyArguments
from .simple_provider import parse_simple_packages


log = logging.getLogger(__name__)


class PackageProxySyncer(PeriodicService):
    __required__ = ("arguments",)
    __dependencies__ = ("patio_broker",)

    arguments: PackageProxyArguments
    patio_broker: AbstractBroker

    async def callback(self) -> Any:
        for name in await self.patio_broker.call(
            "package_proxy.all_packages"
        ):
            print(name)
        print("done")


class PackageProxySyncerWorker(Service):
    __required__ = ("arguments",)
    __dependencies__ = ("patio_broker",)

    arguments: PackageProxyArguments
    client: aiohttp.ClientSession
    patio_broker: AbstractBroker

    async def start(self) -> None:
        self.client = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                limit=self.arguments.connection_limit,
                ssl_context=ssl.create_default_context(),
            ),
            connector_owner=True,
        )

        rpc["package_proxy.all_packages"] = self.parse_all_packages

    async def parse_all_packages(self) -> List[str]:
        url = self.arguments.url.with_path(self.arguments.simple_list_path)
        return await parse_simple_packages(pypi_url=url, client=self.client)
