from typing import TypeVar

from aiomisc_dependency import STORE, dependency


T = TypeVar("T")


def strict_dependency(func: T) -> T:
    if STORE.has_provider(func.__name__):
        raise LookupError(f"Dependency cannot be declared twice: {func!r}")
    return dependency(func)
