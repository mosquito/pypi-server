from typing import Dict

import pytest

from pypi_server import Group, Parser, ParserBuilder


class TestCase:
    class CatGroup(Group):
        pass

    class DogGroup(Group):
        pass

    NAME = "test"

    @pytest.fixture()
    def parser_groups(self) -> Dict[str, Group]:
        return {self.NAME: self.CatGroup()}


class TestSimple(TestCase):
    def test_enabled_flag(
        self, parser: Parser, parser_builder: ParserBuilder
    ):
        parser.parse_args([])
        group = parser_builder.get_parsed_group(self.CatGroup)
        assert not group.enabled

        parser.parse_args(["--test-enabled"])
        group = parser_builder.get_parsed_group(self.CatGroup)
        assert group.enabled

    def test_locked(self, parser_builder: ParserBuilder):
        parser_builder.build()
        group = self.CatGroup()

        with pytest.raises(RuntimeError):
            parser_builder['test'] = group

    def test_bad_name(self, parser_builder: ParserBuilder):
        group = self.CatGroup()

        with pytest.raises(ValueError):
            parser_builder['_test'] = group

        with pytest.raises(ValueError):
            parser_builder['_test_'] = group

        with pytest.raises(ValueError):
            parser_builder['te-st'] = group

        with pytest.raises(ValueError):
            parser_builder[''] = group

    def test_name_conflict(self, parser_builder: ParserBuilder):
        group = self.CatGroup()

        parser_builder['test'] = group

        with pytest.raises(ValueError):
            parser_builder['test'] = group

    def test_name_del(self, parser_builder: ParserBuilder):
        group = self.CatGroup()

        parser_builder['test'] = group
        del parser_builder['test']
        parser_builder['test'] = group

    def test_get(self, parser_builder: ParserBuilder):
        group = self.CatGroup()

        parser_builder['test'] = group
        assert parser_builder['test'] == group

    def test_len(self, parser_builder: ParserBuilder):
        group1 = self.CatGroup()
        group2 = self.DogGroup()

        parser_builder['test_a'] = group1
        assert len(parser_builder) == 1

        parser_builder['test_b'] = group2
        assert len(parser_builder) == 2

        del parser_builder['test_a']
        assert len(parser_builder) == 1

        del parser_builder['test_b']
        assert len(parser_builder) == 0

    def test_iter(self, parser_builder: ParserBuilder):
        group1 = self.CatGroup()
        group2 = self.DogGroup()

        assert list(parser_builder) == []
        parser_builder["test_a"] = group1
        assert list(parser_builder) == ["test_a"]

        parser_builder["test_b"] = group2
        assert sorted(list(parser_builder)) == ["test_a", "test_b"]

    def test_lock(self, parser_builder: ParserBuilder):
        group1 = self.CatGroup()
        group2 = self.DogGroup()

        assert list(parser_builder) == []
        parser_builder["test_a"] = group1
        assert list(parser_builder) == ["test_a"]

        parser_builder["test_b"] = group2
        assert sorted(list(parser_builder)) == ["test_a", "test_b"]

    def test_build_twice(self, parser_builder: ParserBuilder):
        assert parser_builder.build() == parser_builder.build()

    def test_get_parser_group(self, parser_builder: ParserBuilder):
        parser_builder['test'] = self.CatGroup()

        with pytest.raises(RuntimeError):
            parser_builder.get_parsed_group(self.CatGroup)

        parser = parser_builder.build()

        parser.parse_args([])
        parser_builder.get_parsed_group(self.CatGroup)
