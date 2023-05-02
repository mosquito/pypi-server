import contextvars
import re
from typing import Any, Dict, Optional, Type, TypeVar

from weakref import WeakKeyDictionary

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


def make_parser_type(**groups: argclass.Group) -> Type[Parser]:
    groups["log"] = LogGroup(title="Logging options")
    return type("Parser", (Parser,), groups)     # type: ignore


REGISTRY = {}
_REV_REGISTRY = WeakKeyDictionary()
_GROUP_NAME_EXP = re.compile(r"(?<!^)(?=[A-Z])")


def register_parser_group(group: Group, *, name: str = "") -> None:
    if not name:
        name = _GROUP_NAME_EXP.sub("_", group.__class__.__name__).lower()

    name = name.lower()

    if " " in name:
        raise ValueError(f"Bad parser name {name!r}")

    if name in REGISTRY:
        raise ValueError(f"Group already registered by {REGISTRY[name]!r}")

    REGISTRY[name] = group
    _REV_REGISTRY[type(group)] = name


def unregister_parser_group(group: Group) -> None:
    name = _REV_REGISTRY.pop(type(group), None)
    REGISTRY.pop(name, None)


def make_parser(**kwargs) -> Parser:
    parser_type = make_parser_type(**REGISTRY)
    return parser_type(**kwargs)


CURRENT_PARSER = contextvars.ContextVar("PARSER")
GROUP = TypeVar("GROUP", bound=Group)


def get_parsed_group(group: Type[GROUP]) -> GROUP:
    group_name = _REV_REGISTRY.get(group)
    if group_name is None:
        raise LookupError(f"Group {group!r} was not registered")
    parser = CURRENT_PARSER.get()
    return getattr(parser, group_name)
