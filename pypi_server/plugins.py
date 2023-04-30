import logging
from typing import Callable, Iterator, Tuple


logger = logging.getLogger(__name__)


def setup_plugins() -> Iterator[Tuple[str, Callable]]:
    import pkg_resources

    for entry_point in pkg_resources.iter_entry_points("pypi_server"):
        plugin = entry_point.load()

        try:
            logger.debug("Trying to load %r %r", entry_point.name, plugin)
            plugin.setup()

            yield entry_point.name, plugin
        except:  # noqa
            logger.warning(
                "Error on %s plugin setup. Ignoring", entry_point.name,
                exc_info=True,
            )
            continue
