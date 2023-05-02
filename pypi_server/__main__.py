import argparse
import asyncio
import contextvars
import os
from pathlib import Path
from types import ModuleType
from typing import Dict

import aiomisc
import aiomisc_log
from aiomisc.entrypoint import CURRENT_ENTRYPOINT

from pypi_server.storage import STORAGES

from .arguments import CURRENT_PARSER, Parser, make_parser
from .plugins import setup_plugins


def run(*, parser: Parser, plugins: Dict[str, ModuleType]):
    CURRENT_PARSER.set(parser)
    # Config for logging plugins run logs

    async def prepare():
        entrypoint: aiomisc.Entrypoint = CURRENT_ENTRYPOINT.get()
        await asyncio.gather(
            *[
                plugin.run(entrypoint) for plugin in plugins.values()
            ]
        )

    with aiomisc.entrypoint(
        log_level=parser.log.level,
        log_format=parser.log.format,
        pool_size=parser.pool_size,
    ) as loop:
        loop.run_until_complete(prepare())

        if not STORAGES:
            raise RuntimeError("No any storage has been enabled.")

        loop.run_forever()


def main():
    # Early config for logging plugins setup logs
    aiomisc_log.basic_config()

    plugins = dict(setup_plugins())
    parser = make_parser(
        description=open(Path(__file__).parent / "description.txt").read(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        config_files=tuple(
            filter(
                None,
                [
                    "pypi-server.ini",
                    "~/.config/pypi-server.ini",
                    "/etc/pypi-server.ini",
                    os.getenv("PYPI_SERVER_CONFIG", ""),
                ],
            ),
        ),
        auto_env_var_prefix="PYPI_SERVER_",
    )
    parser.parse_args()
    parser.sanitize_env()

    ctx = contextvars.copy_context()
    ctx.run(run, parser=parser, plugins=plugins)
