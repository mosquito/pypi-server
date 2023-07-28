import logging
from typing import TypeVar

from aiomisc_dependency import STORE, dependency


T = TypeVar("T")


def strict_dependency(func: T) -> T:
    logging.debug("Declaring depencency %r", func, exc_info=True)

    if STORE.has_provider(func.__name__):
        raise LookupError(
            f"Dependency cannot be declared twice: {func!r} and "
            f"{STORE.providers[func.__name__].func}"
        )
    return dependency(func)
