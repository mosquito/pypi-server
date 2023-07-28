import asyncio
import contextvars
import io
import logging
import os
from pathlib import Path

import aiomisc
import aiomisc_log
from aiomisc.entrypoint import CURRENT_ENTRYPOINT

from .argparse_formatter import MarkdownDescriptionRichHelpFormatter
from .arguments import ParserBuilder
from .plugins import ConfigurationError, Plugin, PLUGINS


def check_config(parser_builder: ParserBuilder):
    if not parser_builder.parser.http.enabled:
        logging.warn("HTTP plugin is not enabled")


def run():
    aiomisc_log.basic_config()
    parser_builder, plugins = Plugin.collect_and_setup(
        "pypi_server",
    )

    description_path = (Path(__file__).parent / "README.md")
    with io.StringIO() as description_fp:
        description_fp.write(description_path.open("r").read())

        description_fp.write(
            "\n# A complete list of all program options\n"
            "All configuration parameters are collected below, "
            "you can use them in combination with environment "
            "variables or use only environment variables.\n",
        )

        description = description_fp.getvalue()

    parser = parser_builder.build(
        description=description,
        formatter_class=MarkdownDescriptionRichHelpFormatter,
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

    aiomisc_log.basic_config(
        level=parser.log.level,
        log_format=parser.log.format,
    )

    for plugin in plugins:
        plugin.setup()

    PLUGINS.set(tuple(plugins))

    async def prepare():
        entrypoint: aiomisc.Entrypoint = CURRENT_ENTRYPOINT.get()
        await asyncio.gather(
            *[plugin.run_services(entrypoint) for plugin in plugins]
        )

    with aiomisc.entrypoint(
        log_level=parser.log.level,
        log_format=parser.log.format,
        pool_size=parser.pool_size,
    ) as loop:
        loop.run_until_complete(prepare())
        check_config(parser_builder)
        loop.run_forever()


def main():
    # Early config for logging plugins setup logs
    ctx = contextvars.copy_context()
    try:
        ctx.run(run)
    except ConfigurationError as e:
        logging.error("Invalid configuration: %s.", e.msg)
        if e.hint:
            logging.info("Hint: %s.", e.hint)
