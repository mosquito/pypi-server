import logging
import ssl
from typing import Iterable, Type

from patio import (
    AbstractBroker, AbstractExecutor, TCPClientBroker, TCPServerBroker,
)

from pypi_server import Plugin
from pypi_server.dependency import strict_dependency

from ...plugins import ConfigurationError
from .arguments import TCPClientParser, TCPServerParser


log = logging.getLogger(__name__)


class TCPServerWorkersPlugin(Plugin):
    parser_name = "tcp_server"
    parser_group = TCPServerParser()

    def declare_dependencies(self, group: TCPServerParser) -> None:
        @strict_dependency
        async def patio_broker(
            patio_executor: AbstractExecutor,
        ) -> AbstractBroker:
            ssl_context = None
            if (
                group.ssl_key and group.ssl_cert
            ) and (
                group.ssl_key.exists() and group.ssl_cert.exists()
            ):
                ssl_context = ssl.create_default_context()
                ssl_context.load_cert_chain(group.ssl_cert, group.ssl_key)

            if not group.listen:
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
                key=group.key,
            )

            await broker.setup()

            for address_port in group.listen:
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

    def declare_dependencies(self, group: TCPServerParser) -> None:
        @strict_dependency
        async def patio_broker(
            patio_executor: AbstractExecutor,
        ) -> AbstractBroker:
            ssl_context = None
            if group.use_ssl:
                ssl_context = ssl.create_default_context()
                if (
                    group.ssl_key and group.ssl_cert
                ) and (
                    group.ssl_key.exists() and group.ssl_cert.exists()
                ):
                    ssl_context.load_cert_chain(
                        group.ssl_cert, group.ssl_key,
                    )

            if not group.connect_to:
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
                key=group.key,
            )

            await broker.setup()

            for address_port in group.connect_to:
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
