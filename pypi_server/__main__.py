import argparse
import asyncio
import logging
import os
from pathlib import Path
from typing import List, Iterable

import aiomisc
import aiomisc_log
from aiomisc.entrypoint import CURRENT_ENTRYPOINT

from pypi_server.storage import STORAGES

from .arguments import ParserBuilder, Parser
from .plugins import load_plugins, Plugin


def run(*, parser: Parser, plugins: Iterable[Plugin]):

    async def prepare():
        entrypoint: aiomisc.Entrypoint = CURRENT_ENTRYPOINT.get()
        await asyncio.gather(
            *[plugin.run(entrypoint) for plugin in plugins]
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

    parser_builder = ParserBuilder()
    plugins: List[Plugin] = []
    for name, plugin in load_plugins():
        try:
            logging.debug(
                "Making plugin instance %r instance from plugin %r",
                plugin, name
            )
            plugin_instance = plugin(parser_builder)
            plugin_instance.setup()
            plugins.append(plugin_instance)
        except Exception:
            logging.exception("Failed to load plugin %r", name)
            continue

    parser_builder.build(
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

    parser_builder.parser.parse_args()
    parser_builder.parser.sanitize_env()

    run(parser=parser_builder.parser, plugins=plugins)
