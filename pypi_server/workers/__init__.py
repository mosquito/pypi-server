import logging
from typing import Any

from patio.registry import Registry


log = logging.getLogger(__name__)
rpc = Registry(project="pypi-server", auto_naming=False)


@rpc("ping")
async def ping(**kwargs) -> Any:
    return kwargs
