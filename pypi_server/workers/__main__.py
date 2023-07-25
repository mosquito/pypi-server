import asyncio
import contextvars
import io
import logging
import os
from pathlib import Path

import aiomisc
import aiomisc_log
from aiomisc import CURRENT_ENTRYPOINT

from .. import ParserBuilder
from ..argparse_formatter import MarkdownDescriptionRichHelpFormatter
from ..plugins import ConfigurationError, Plugin


def check_config(parser_builder: ParserBuilder):
    pass


def run():
    parser_builder, plugins = Plugin.collect_and_setup(
        "pypi_server_worker",
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
                    "pypi-server-workers.ini",
                    "~/.config/pypi-server-workers.ini",
                    "/etc/pypi-server-workers.ini",
                    os.getenv("PYPI_SERVER_WORKERS_CONFIG", ""),
                ],
            ),
        ),
        auto_env_var_prefix="PYPI_SERVER_WORKERS_",
    )

    parser.parse_args()
    parser.sanitize_env()

    aiomisc_log.basic_config(
        level=parser.log.level,
        log_format=parser.log.format,
    )

    for plugin in plugins:
        plugin.setup()

    async def prepare():
        entrypoint: aiomisc.Entrypoint = CURRENT_ENTRYPOINT.get()
        await asyncio.gather(
            *[p.run(entrypoint) for p in plugins]
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
    aiomisc_log.basic_config()
    ctx = contextvars.copy_context()
    try:
        ctx.run(run)
    except ConfigurationError as e:
        logging.error("Invalid configuration: %s.", e.msg)
        if e.hint:
            logging.info("Hint: %s.", e.hint)
