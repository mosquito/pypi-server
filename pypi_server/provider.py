from abc import ABC
from typing import AsyncIterable, TypeVar


T = TypeVar("T")


class Provider(AsyncIterable[T], ABC):
    pass
