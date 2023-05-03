from pathlib import Path
from typing import Dict

import pytest

from pypi_server import Parser
from pypi_server.arguments import Group, ParserBuilder


@pytest.fixture
def sample_file(tmp_path) -> Path:
    path = tmp_path / "test.txt"
    with path.open("w") as fp:
        for i in range(1_000):
            fp.write(f"Hello {i} times\n")
    return path


@pytest.fixture()
def parser_builder() -> ParserBuilder:
    return ParserBuilder()


@pytest.fixture()
def parser_groups() -> Dict[str, Group]:
    return {}


@pytest.fixture()
def parser(
    parser_builder: ParserBuilder, parser_groups: Dict[str, Group]
) -> Parser:
    for name, group in parser_groups.items():
        parser_builder[name] = group

    parser_builder.build()
    return parser_builder.parser
