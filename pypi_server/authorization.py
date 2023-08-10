from abc import ABC, abstractmethod
from enum import Enum
from typing import List, AsyncIterator

from pypi_server.dependency import strict_dependency


class AuthorizationContext(Enum):
    API = "api"


class AuthorizationProvider(ABC):
    @abstractmethod
    async def match(
        self, username: str, password: str, context: AuthorizationContext
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def authorize(
        self, username: str, password: str, context: AuthorizationContext
    ):
        raise NotImplementedError


class AuthorizationProviders(List[AuthorizationProvider]):
    async def match(
        self, username: str, password: str, context: AuthorizationContext
    ) -> AsyncIterator[AuthorizationProvider]:
        for candidate in self:
            if not await candidate.match(username, password, context):
                continue
            yield candidate


@strict_dependency
def authorization_providers() -> AuthorizationProviders:
    return AuthorizationProviders()
