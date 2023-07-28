import logging
from typing import Iterator, List, Tuple, Type, TypeVar, Sequence, Iterable

import aiomisc
from aiomisc import StrictContextVar
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

    @property
    def group(self) -> T:
        return self.get_parsed_group(type(self.parser_group))

    @property
    def is_enabled(self) -> bool:
        return self.group.enabled

    async def run_services(self, entrypoint: aiomisc.Entrypoint) -> None:
        if not self.is_enabled:
            log.debug("Plugin %r not enabled. Skipping.", self)
            return
        services = await self.start_services()
        if not services:
            log.debug("Plugin %r not provide services.", self)
            return
        await entrypoint.start_services(*services)

    async def run_workers(self, entrypoint: aiomisc.Entrypoint) -> None:
        if not self.is_enabled:
            log.debug("Workers for plugin %r not enabled. Skipping.", self)
            return
        workers = await self.start_workers()
        if not workers:
            log.debug("Plugin %r not provide workers.", self)
            return
        await entrypoint.start_services(*workers)

    def setup(self) -> None:
        if not self.is_enabled:
            return

        log.debug(
            "Configuring dependencies for %r", self.__class__.__name__,
        )
        self.declare_dependencies()

    def declare_dependencies(self) -> None:
        return

    async def start_services(self) -> Iterable[aiomisc.Service]:
        return ()

    async def start_workers(self) -> Iterable[aiomisc.Service]:
        return ()

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


PLUGINS: StrictContextVar[Sequence[Plugin]] = StrictContextVar(
    "PLUGINS", RuntimeError("Plugins has not been collected")
)


class ConfigurationError(RuntimeError):
    def __init__(self, msg: str, hint: str = ""):
        self.msg = msg
        self.hint = hint
