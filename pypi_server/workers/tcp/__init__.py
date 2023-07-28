import logging
import ssl
from typing import Iterable, Type

from patio import (
    AbstractBroker, AbstractExecutor, AsyncExecutor, TCPClientBroker,
    TCPServerBroker,
)

from pypi_server import Plugin
from pypi_server.dependency import strict_dependency
from pypi_server.workers import rpc

from ...plugins import ConfigurationError
from .arguments import TCPClientParser, TCPServerParser


log = logging.getLogger(__name__)


class TCPServerWorkersPlugin(Plugin):
    parser_name = "tcp_server"
    parser_group = TCPServerParser()

    def declare_dependencies(self) -> None:
        @strict_dependency
        async def patio_executor() -> AbstractExecutor:
            executor = AsyncExecutor(rpc, max_workers=self.group.max_workers)
            await executor.setup()

            try:
                yield executor
            finally:
                await executor.shutdown()

        @strict_dependency
        async def patio_broker(
            patio_executor: AbstractExecutor,
        ) -> AbstractBroker:
            ssl_context = None
            if (
                self.group.ssl_key and self.group.ssl_cert
            ) and (
                self.group.ssl_key.exists() and self.group.ssl_cert.exists()
            ):
                ssl_context = ssl.create_default_context()
                ssl_context.load_cert_chain(
                    self.group.ssl_cert, self.group.ssl_key
                )

            if not self.group.listen:
                raise ConfigurationError(
                    "You must specify at least one listen address",
                    hint=(
                        'Specify "--tcp-server-listen A.DD.RE.SS:PORT" '
                        "argument"
                    ),
                )

            broker = TCPServerBroker(
                executor=patio_executor,
                ssl_context=ssl_context,
                key=self.group.key,
            )

            await broker.setup()

            for address_port in self.group.listen:
                log.debug(
                    "Listening %s://%s:%s",
                    "tcp" if not ssl_context else "tls",
                    address_port.address,
                    address_port.port,
                )
                await broker.listen(
                    address=address_port.address,
                    port=address_port.port,
                )

            try:
                log.debug(
                    "Started broker %r with executor %r",
                    broker, patio_executor,
                )
                yield broker
            finally:
                log.debug("Closing broker %r", broker)
                await broker.close()


class TCPClientWorkersPlugin(Plugin):
    parser_name = "tcp_client"
    parser_group = TCPClientParser()

    def declare_dependencies(self) -> None:
        @strict_dependency
        async def patio_executor() -> AbstractExecutor:
            executor = AsyncExecutor(rpc, max_workers=self.group.max_workers)
            await executor.setup()

            try:
                yield executor
            finally:
                await executor.shutdown()

        @strict_dependency
        async def patio_broker(
            patio_executor: AbstractExecutor,
        ) -> AbstractBroker:
            ssl_context = None
            if self.group.use_ssl:
                ssl_context = ssl.create_default_context()
                if (
                    self.group.ssl_key and self.group.ssl_cert
                ) and (
                    self.group.ssl_key.exists() and
                    self.group.ssl_cert.exists()
                ):
                    ssl_context.load_cert_chain(
                        self.group.ssl_cert, self.group.ssl_key,
                    )

            if not self.group.connect_to:
                raise ConfigurationError(
                    "You must specify at least one server address",
                    hint=(
                        'Specify "--tcp-client-connect-to A.DD.RE.SS:PORT" '
                        "argument"
                    ),
                )

            broker = TCPClientBroker(
                executor=patio_executor,
                ssl_context=ssl_context,
                key=self.group.key,
            )

            await broker.setup()

            for address_port in self.group.connect_to:
                log.info(
                    "Adding peer %s://%s:%s",
                    "tcp" if not ssl_context else "tls",
                    address_port.address,
                    address_port.port,
                )
                await broker.connect(
                    address=address_port.address,
                    port=address_port.port,
                )

            try:
                log.debug(
                    "Started broker %r with executor %r",
                    broker, patio_executor,
                )
                yield broker
            finally:
                log.debug("Closing broker %r", broker)
                await broker.close()


class TCPClientPlugin(TCPClientWorkersPlugin):
    parser_name = "workers_tcp_client"


class TCPServerPlugin(TCPServerWorkersPlugin):
    parser_name = "workers_tcp_server"


__pypi_server_plugins__: Iterable[Type[Plugin]] = (
    TCPServerPlugin, TCPClientPlugin,
)

__pypi_server_worker_plugins__: Iterable[Type[Plugin]] = (
    TCPServerWorkersPlugin, TCPClientWorkersPlugin,
)
