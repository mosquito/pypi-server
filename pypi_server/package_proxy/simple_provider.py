from __future__ import annotations

from html.parser import HTMLParser
from typing import List, Dict, Tuple

from aiohttp import ClientSession, hdrs
from yarl import URL


SIMPLE_HEADERS = (
    (hdrs.ACCEPT, "text/html"),
)


class SimpleParser(HTMLParser):
    def __init__(self, results: List[Tuple[str, Dict[str, str]]]):
        super().__init__()
        self.results = results
        self.tag = None
        self.attrs = None
        self.data = None

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]],
    ) -> None:
        self.tag = tag
        self.attrs = dict(attrs)

    def handle_data(self, data: str) -> None:
        self.data = data

    def handle_endtag(self, tag: str) -> None:
        if tag != "a":
            return
        self.results.append((self.data, self.attrs))


async def parse_simple_packages(
    pypi_url: URL, client: ClientSession,
) -> List[str]:

    result = []
    parser = SimpleParser(result)

    async with client.get(
        pypi_url / f"simple/", allow_redirects=True, headers=SIMPLE_HEADERS
    ) as response:
        response.raise_for_status()

        try:
            encoding = response.get_encoding()
        except (RuntimeError, LookupError):
            encoding = "utf-8"

        while not response.content.is_eof():
            line = await response.content.readline()
            parser.feed(line.decode(encoding))

        return [name for name, attrs in result]


async def parse_simple_package_files(
    pypi_url: URL, package_name: str, client: ClientSession,
) -> List[str, str]:

    result = []
    parser = SimpleParser(result)

    async with client.get(
        pypi_url / f"simple/{package_name}/", allow_redirects=True,
        headers=SIMPLE_HEADERS
    ) as response:
        response.raise_for_status()

        try:
            encoding = response.get_encoding()
        except (RuntimeError, LookupError):
            encoding = "utf-8"

        while not response.content.is_eof():
            line = await response.content.readline()
            parser.feed(line.decode(encoding))

        return result
