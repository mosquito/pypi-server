from __future__ import annotations

from html.parser import HTMLParser
from typing import List

from aiohttp import ClientSession
from yarl import URL


class SimpleParser(HTMLParser):
    def __init__(self, results: List[str]):
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
        # href = self.attrs.get("href")
        name = self.data
        self.results.append(name)


async def parse_simple_packages(
    url: URL, client: ClientSession,
) -> List[str]:

    result = []
    parser = SimpleParser(result)

    async with client.get(url, allow_redirects=True) as response:
        try:
            encoding = response.get_encoding()
        except (RuntimeError, LookupError):
            encoding = "utf-8"

        while not response.content.is_eof():
            line = await response.content.readline()
            parser.feed(line.decode(encoding))

        return result
