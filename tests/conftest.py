from pathlib import Path
from typing import Callable, Dict

import pytest

from pypi_server import Parser
from pypi_server.arguments import make_parser, CURRENT_PARSER, Group, \
    register_parser_group, unregister_parser_group, REGISTRY


@pytest.fixture
def sample_file(tmp_path) -> Path:
    path = tmp_path / "test.txt"
    with path.open("w") as fp:
        for i in range(1_000):
            fp.write(f"Hello {i} times\n")
    return path


@pytest.fixture()
def parser_maker(request: pytest.FixtureRequest) -> Callable[..., Parser]:
    def finalizer(**parser_groups: Group):
        for name, group in parser_groups.items():
            unregister_parser_group(group)

    def maker(**parser_groups: Group):
        for name, group in parser_groups.items():
            register_parser_group(group, name=name)

        parser = make_parser()
        request.addfinalizer(lambda: finalizer(**parser_groups))
        return parser

    return maker


@pytest.fixture()
def parser_groups() -> Dict[str, Group]:
    pass


@pytest.fixture()
def parser(
    parser_maker: Callable[..., Parser],
    parser_groups: Dict[str, Group]
) -> Parser:
    REGISTRY.clear()
    parser = parser_maker(**parser_groups)
    token = CURRENT_PARSER.set(parser)

    try:
        yield parser
    finally:
        CURRENT_PARSER.reset(token)
        REGISTRY.clear()
