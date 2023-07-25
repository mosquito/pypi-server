from __future__ import annotations

import asyncio
from html.parser import HTMLParser
from typing import AsyncIterator, Tuple

from aiochannel import Channel
from aiohttp import ClientSession
from yarl import URL

from pypi_server.workers import worker


ResultsType = Channel[Tuple[str, str]]


class SimpleParser(HTMLParser):
    def __init__(self, results: ResultsType):
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

        href = self.attrs.get("href")
        name = self.data
        self.results.put_nowait((name, href))


@worker("parse_simple_packages")
async def parse_simple_packages(
    url: URL, client: ClientSession,
) -> AsyncIterator[Tuple[str, str]]:

    results: ResultsType = Channel()
    parser = SimpleParser(results)

    async with client.get(url, allow_redirects=True) as response:
        try:
            encoding = response.get_encoding()
        except (RuntimeError, LookupError):
            encoding = "utf-8"

        async def feeder():
            while not response.content.is_eof():
                line = await response.content.readline()
                parser.feed(line.decode(encoding))
            results.close()

        task = asyncio.create_task(feeder())

        try:
            async for name, href in results:
                yield name, href
        finally:
            if task.done():
                return

            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
