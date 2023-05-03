import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiomisc.entrypoint import CURRENT_ENTRYPOINT

from pypi_server.__main__ import main, run
from pypi_server.storage import STORAGES


def test_main_help(capsys: pytest.CaptureFixture):
    with patch(
        "sys.argv",
        new_callable=lambda: ["__main__", "--help"],
    ):
        with pytest.raises(SystemExit) as exc:
            main()

        assert exc.value.args == (0,)
        stdout, stderr = capsys.readouterr()
        assert stderr == ""
        assert stdout.startswith("usage:")


async def test_main():
    with patch(
        "sys.argv",
        new_callable=lambda: ["__main__"],
    ), patch("aiomisc.entrypoint", autospec=True) as entrypoint, patch(
        "pypi_server.plugins.load_plugins", return_value={}.items(),
    ):
        loop_mock = MagicMock(spec=asyncio.AbstractEventLoop)
        entrypoint.return_value.__enter__.return_value = loop_mock
        CURRENT_ENTRYPOINT.set(entrypoint)
        STORAGES.append(AsyncMock())

        main()

        assert loop_mock.run_until_complete.call_count
        assert loop_mock.run_forever.call_count

        coroutine = asyncio.ensure_future(
            loop_mock.run_until_complete.mock_calls[0].args[0],
        )
        await coroutine


async def test_run(event_loop, request: pytest.FixtureRequest):
    with patch("aiomisc.entrypoint", autospec=True) as entrypoint:
        loop_mock = MagicMock(spec=asyncio.AbstractEventLoop)
        entrypoint.return_value.__enter__.return_value = loop_mock
        CURRENT_ENTRYPOINT.set(entrypoint)
        STORAGES.append(AsyncMock())
        request.addfinalizer(STORAGES.clear)
        plugin = AsyncMock()
        run(parser=MagicMock(), plugins=[plugin])

        assert loop_mock.run_until_complete.call_count
        assert loop_mock.run_forever.call_count

        coroutine = asyncio.ensure_future(
            loop_mock.run_until_complete.mock_calls[0].args[0],
        )
        await coroutine
        assert plugin.run.called


async def test_run_no_storages(event_loop):
    with patch("aiomisc.entrypoint", autospec=True) as entrypoint:
        loop_mock = MagicMock(spec=asyncio.AbstractEventLoop)
        entrypoint.return_value.__enter__.return_value = loop_mock
        CURRENT_ENTRYPOINT.set(entrypoint)
        STORAGES.clear()
        plugin = AsyncMock()
        with pytest.raises(RuntimeError):
            run(parser=MagicMock(), plugins=[plugin])

        coroutine = asyncio.ensure_future(
            loop_mock.run_until_complete.mock_calls[0].args[0],
        )
        await coroutine
