from abc import ABC, abstractmethod
from typing import AsyncIterable, Optional, TypeVar

from .collection import Collection
from .package_metadata import Package, PackageShortInfo


T = TypeVar("T")


class PackageProvider(ABC):
    @abstractmethod
    def packages(self) -> AsyncIterable[PackageShortInfo]: ...

    @abstractmethod
    async def package_info(self, package_name: str) -> Package: ...


class PackageProviderCollection(Collection[PackageProvider]):
    def packages(self) -> AsyncIterable[str]:
        return self.stream("packages")

    async def package_info(self, package_name: str) -> Optional[Package]:
        package: Optional[Package]
        for provider in self:
            package = await provider.package_info(package_name)
            if package is not None:
                return package

        return None
