import pytest

from pypi_server import (
    Group, Parser, get_parsed_group, register_parser_group,
    unregister_parser_group,
)
from pypi_server.arguments import CURRENT_PARSER, _make_parser


class TestCase:
    class ArgumentsGroup(Group):
        pass

    NAME = "test"

    @pytest.fixture()
    def parser(self, request: pytest.FixtureRequest) -> Parser:
        group = self.ArgumentsGroup()
        register_parser_group(group, name=self.NAME)
        request.addfinalizer(lambda: unregister_parser_group(group))
        parser = _make_parser()
        CURRENT_PARSER.set(parser)
        yield parser


class TestSimple(TestCase):
    def test_enabled_flag(self, parser: Parser):
        parser.parse_args([])
        group = get_parsed_group(self.ArgumentsGroup)
        assert not group.enabled

        parser.parse_args(["--test-enabled"])
        group = get_parsed_group(self.ArgumentsGroup)
        assert group.enabled


class TestBadName(TestCase):
    def test_name(self, request: pytest.FixtureRequest):
        group = self.ArgumentsGroup()
        request.addfinalizer(lambda: unregister_parser_group(group))
        with pytest.raises(ValueError):
            register_parser_group(group, name=" ")


class TestRegisterTwice(TestCase):
    def test_name(self, request: pytest.FixtureRequest):
        group = self.ArgumentsGroup()

        register_parser_group(group)
        request.addfinalizer(lambda: unregister_parser_group(group))

        with pytest.raises(ValueError):
            register_parser_group(group)


def test_unknown_group():
    class UnknownGroup(Group):
        pass

    with pytest.raises(LookupError):
        get_parsed_group(UnknownGroup)
