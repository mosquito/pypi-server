import logging
import os
from enum import IntEnum

from aiomisc import threaded


log = logging.getLogger(__name__)


class FAdvice(IntEnum):
    NORMAL = getattr(os, "POSIX_FADV_NORMAL", -100000)
    SEQUENTIAL = getattr(os, "POSIX_FADV_SEQUENTIAL", -200000)
    RANDOM = getattr(os, "POSIX_FADV_RANDOM", -300000)
    NO_REUSE = getattr(os, "POSIX_FADV_NOREUSE", -400000)
    WILL_NEED = getattr(os, "POSIX_FADV_WILLNEED", -500000)
    DONT_NEED = getattr(os, "POSIX_FADV_DONTNEED", -600000)


try:
    from posix import POSIX_FADV_DONTNEED, posix_fadvise, posix_fallocate

    @threaded
    def fadvise(
        fd: int, mode: FAdvice, *, offset: int = 0, length: int = 0
    ) -> None:
        if mode < -100000:
            log.debug("POSIX_FADV constants is not presented in os module.")
            return

        return posix_fadvise(fd, offset, length, mode)

    @threaded
    def fallocate(fd: int, size: int, *, offset: int = 0) -> None:
        return posix_fallocate(fd, offset, size)

except ImportError:
    async def fadvise(
        fd: int, mode: FAdvice, *, offset: int = 0, length: int = 0
    ) -> None:
        log.debug(
            "posix_fadvise not supported, nothing to do for "
            "fd=%r mode=%r length=%r offset=%r", fd, mode, length, offset,
        )
        return None

    async def fallocate(fd: int, size: int, *, offset: int = 0) -> None:
        log.debug(
            "posix_fallocate not supported, nothing to do for "
            "fd=%r size=%r offset=%r",
            fd, size, offset,
        )
        return None
