import logging
from typing import Iterator, List, Tuple, Type, TypeVar

import aiomisc
from aiomisc.compat import entry_pont_iterator

from pypi_server.arguments import Group, ParserBuilder


log = logging.getLogger(__name__)

T = TypeVar("T", bound=Group)


class Plugin:
    PARSER_BUILDER_CLASS = ParserBuilder

    parser_group: T
    parser_name: str
    parser_builder: PARSER_BUILDER_CLASS

    def __init__(self, parser_builder: ParserBuilder):
        self.parser_builder: ParserBuilder = parser_builder

    def add_parser_group(self, name: str, group: Group):
        self.parser_builder[name] = group

    def get_parsed_group(self, group: Type[T]) -> T:
        return self.parser_builder.get_parsed_group(group)

    def setup_parser(self) -> None:
        self.add_parser_group(self.parser_name, self.parser_group)

    async def run(self, entrypoint: aiomisc.Entrypoint) -> None:
        group = self.get_parsed_group(type(self.parser_group))
        if not group.enabled:
            log.debug("Plugin %r not enabled. Skipping.", self)
            return

        await self.on_enabled(group=group, entrypoint=entrypoint)

    def setup(self) -> None:
        group: T = self.get_parsed_group(type(self.parser_group))
        if not group.enabled:
            return
        log.debug(
            "Configuring dependencies for %r", self.__class__.__name__,
        )
        self.declare_dependencies(group)

    def declare_dependencies(self, group: T) -> None:
        return

    async def on_enabled(
        self, group: T, entrypoint: aiomisc.Entrypoint,
    ) -> None:
        pass

    @classmethod
    def collect(
        cls, entrypoint: str,
    ) -> Iterator[Tuple[str, Type["Plugin"]]]:
        module_plugin_attribute = f"__{entrypoint}_plugins__"

        for entry_point in entry_pont_iterator(entrypoint):
            try:
                module = entry_point.load()
                log.debug(
                    "Trying to load %r %r", entry_point.name, module,
                )
                for plugin in getattr(module, module_plugin_attribute, ()):
                    yield entry_point.name, plugin
            except:  # noqa
                log.warning(
                    "Error on %s plugin setup. Ignoring", entry_point.name,
                    exc_info=True,
                )
                continue

    @classmethod
    def collect_and_setup(
        cls, entrypoint: str,
    ) -> Tuple[ParserBuilder, List["Plugin"]]:
        parser_builder = cls.PARSER_BUILDER_CLASS()
        plugins: List[Plugin] = []

        plugin: Type[Plugin]
        for name, plugin in cls.collect(entrypoint):
            if not issubclass(plugin, Plugin):
                continue

            try:
                logging.debug(
                    "Making plugin instance %r instance from plugin %r",
                    plugin, name,
                )
                plugin_instance = plugin(parser_builder)
                plugin_instance.setup_parser()
                plugins.append(plugin_instance)
            except Exception:
                logging.exception("Failed to load plugin %r", name)
                continue

        return parser_builder, plugins


class ConfigurationError(RuntimeError):
    def __init__(self, msg: str, hint: str = ""):
        self.msg = msg
        self.hint = hint
