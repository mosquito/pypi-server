import inspect
import logging
from abc import abstractmethod, ABC
from types import ModuleType
from typing import Iterator, Tuple, Type, TypeVar

import aiomisc

from pypi_server.arguments import ParserBuilder, Group

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Group)


class Plugin(ABC):
    parser_builder: ParserBuilder

    def __init__(self, parser_builder: ParserBuilder):
        self.parser_builder: ParserBuilder = parser_builder

    def setup(self) -> None:
        pass

    @abstractmethod
    async def run(self, entrypoint: aiomisc.Entrypoint) -> None:
        pass


class PluginWithArguments(Plugin, ABC):
    parser_group: T
    parser_name: str

    def add_parser_group(self, name: str, group: Group):
        self.parser_builder[name] = group

    def get_parsed_group(self, group: Type[T]) -> T:
        return self.parser_builder.get_parsed_group(group)

    def setup(self) -> None:
        self.add_parser_group(self.parser_name, self.parser_group)

    async def run(self, entrypoint: aiomisc.Entrypoint) -> None:
        group = self.get_parsed_group(type(self.parser_group))
        if not group.enabled:
            logger.debug("Plugin %r not enabled. Skipping.", self)
            return

        await self.on_enabled(group=group, entrypoint=entrypoint)

    @abstractmethod
    async def on_enabled(
        self, group: T, entrypoint: aiomisc.Entrypoint
    ) -> None:
        pass


def load_plugins() -> Iterator[Tuple[str, Type[Plugin]]]:
    import pkg_resources

    for entry_point in pkg_resources.iter_entry_points("pypi_server"):
        try:
            module = entry_point.load()
            logger.debug("Trying to load %r %r", entry_point.name, module)
            for plugin in getattr(module, '__pypi_server_plugins__', ()):
                yield entry_point.name, plugin
        except:  # noqa
            logger.warning(
                "Error on %s plugin setup. Ignoring", entry_point.name,
                exc_info=True,
            )
            continue
