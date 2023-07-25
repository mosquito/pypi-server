from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import argclass

from pypi_server import Group


@dataclass
class AddressPort:
    address: str
    port: int

    @classmethod
    def parse(cls, address_line: str) -> "AddressPort":
        address, port = address_line.rsplit(":", 1)
        return cls(address=address, port=int(port))


class TCPServerParser(Group):
    __doc__ = (Path(__file__).parent / "README.md").open().read()

    __plugin_name__ = "TCP Server mode"

    key: bytes = b""
    listen: List[AddressPort] = argclass.Argument(
        nargs=argclass.Nargs.ONE_OR_MORE, type=AddressPort.parse, default=[],
    )

    ssl_key: Optional[Path]
    ssl_cert: Optional[Path]


class TCPClientParser(Group):
    __doc__ = (Path(__file__).parent / "README.md").open().read()

    __plugin_name__ = "TCP Client mode"

    key: bytes = b""

    connect_to: List[AddressPort] = argclass.Argument(
        nargs=argclass.Nargs.ONE_OR_MORE, type=AddressPort.parse, default=[],
    )

    use_ssl: bool = False
    ssl_key: Optional[Path]
    ssl_cert: Optional[Path]
