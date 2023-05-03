import re
from typing import (
    Any, Dict, Optional, Type, TypeVar, MutableMapping,
    Iterator
)

import aiomisc_log
import argclass


class LogGroup(argclass.Group):
    level: str = argclass.Argument(
        default=aiomisc_log.LogLevel.default(),
        choices=aiomisc_log.LogLevel.choices(),
    )
    format: str = argclass.Argument(
        default=aiomisc_log.LogFormat.default(),
        choices=aiomisc_log.LogFormat.choices(),
    )


class Group(argclass.Group):
    def __init__(
        self, title: Optional[str] = None, description: Optional[str] = None,
        prefix: Optional[str] = None,
        defaults: Optional[Dict[str, Any]] = None,
    ):
        if not title:
            default_title = getattr(
                self.__class__, "__plugin_name__",
                self.__class__.__name__,
            )
            title = f"{default_title} arguments"

        if not description:
            description = (
                self.__class__.__doc__.strip()
                if self.__class__.__doc__ else None
            )

        super().__init__(
            defaults=defaults,
            description=description,
            prefix=prefix,
            title=title,
        )

    enabled: bool = argclass.Argument(
        help="Enables this feature", action=argclass.Actions.STORE_TRUE,
    )


class Parser(argclass.Parser):
    log: LogGroup
    pool_size: int = argclass.Argument(
        help="Thread pool default size", default=4,
    )


GROUP = TypeVar("GROUP", bound=Group)


class ParserBuilder(MutableMapping[str, Group]):
    NAME_VALIDATOR = re.compile(r"^([a-z][a-z_]*[a-z])$")

    def __init__(self):
        self.__storage: Dict[str, Group] = {}
        self.__rev_storage: Dict[Type[Group], str] = {}
        self.parser_type: Optional[Type[Parser]] = None
        self.parser: Optional[Parser] = None

    @property
    def is_locked(self) -> bool:
        return self.parser_type is not None

    def _check_locked(self) -> None:
        if self.is_locked:
            raise RuntimeError(
                f"Can not modify locked {type(self.__class__)}"
            )

    def __setitem__(self, key: str, group: Group) -> None:
        self._check_locked()

        if self.NAME_VALIDATOR.match(key) is None:
            raise ValueError(
                "Group name must contain underscore-separated words."
            )

        group_type = type(group)

        if group_type in self.__rev_storage or key in self.__storage:
            raise ValueError(
                f"Group type {type(group)} already "
                f"registered with name {key!r}"
            )

        self.__storage[key] = group
        self.__rev_storage[group_type] = key

    def __delitem__(self, key: str) -> None:
        self._check_locked()
        group = self.__storage.pop(key)
        del self.__rev_storage[type(group)]

    def __getitem__(self, key: str) -> Group:
        return self.__storage[key]

    def __len__(self) -> int:
        return len(self.__storage)

    def __iter__(self) -> Iterator[str]:
        return iter(self.__storage)

    def build_type(self) -> None:
        self._check_locked()
        groups = dict(self.__storage)
        groups["log"] = LogGroup(title="Logging options")
        self.parser_type = type("Parser", (Parser,), groups)  # type: ignore

    def build(self, **kwargs) -> Parser:
        if self.parser is not None:
            return self.parser
        self.build_type()
        self.parser = self.parser_type(**kwargs)
        return self.parser

    def get_parsed_group(self, group: Type[GROUP]) -> GROUP:
        if self.parser_type is None:
            raise RuntimeError("Parser not built")
        group_name = self.__rev_storage[group]
        return getattr(self.parser, group_name)
