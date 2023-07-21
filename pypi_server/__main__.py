import asyncio
import contextvars
import io
import logging
import os
import sys
from pathlib import Path
from typing import List

import aiomisc
import aiomisc_log
import rich.console
import rich.markdown
import rich.text
import rich.theme
import rich_argparse
from aiomisc.entrypoint import CURRENT_ENTRYPOINT

from pypi_server.storage import STORAGES, StorageCollection

from .arguments import ParserBuilder
from .plugins import ConfigurationError, Plugin, load_plugins


class MarkdownDescriptionRichHelpFormatter(rich_argparse.RichHelpFormatter):

    styles = dict(
        **{"argparse.env": "bright_magenta"},
        **rich_argparse.RichHelpFormatter.styles
    )

    highlights = (
        # highlight --words-with-dashes as args
        r"(?:^|\s)(?P<args>-{1,2}[\w]+[\w-]*)",
        r"'(?P<syntax>[^`]*)'",
        r"\[(?P<syntax>ENV:).*\]",
        r"ENV: (?P<env>[A-Z_]+)",
        r"\((?P<args>default: \S+)\)",
    )

    def _rich_format_text(self, text: str) -> rich.text.Text:
        with io.StringIO() as fp:
            console = rich.console.Console(
                file=fp,
                force_terminal=os.isatty(sys.stdout.fileno()),
                stderr=True,
                width=self._width,
            )
            console.print(rich.markdown.Markdown(text, hyperlinks=True))
            return rich.text.Text(fp.getvalue())


def create_collections():
    STORAGES.set(StorageCollection())


def check_config(parser_builder: ParserBuilder):
    if not STORAGES.current:
        raise ConfigurationError(
            msg="No any storage has been enabled",
            hint="See --help and enable and configure a storage",
        )


def run():
    parser_builder = ParserBuilder()
    plugins: List[Plugin] = []

    create_collections()

    for name, plugin in load_plugins():
        try:
            logging.debug(
                "Making plugin instance %r instance from plugin %r",
                plugin, name,
            )
            plugin_instance = plugin(parser_builder)
            plugin_instance.setup()
            plugins.append(plugin_instance)
        except Exception:
            logging.exception("Failed to load plugin %r", name)
            continue

    description_path = (Path(__file__).parent / "README.md")
    description = description_path.open("r").read()
    description += (
        "\n"
        "A complete list of all program options\n"
        "======================================"
    )
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
