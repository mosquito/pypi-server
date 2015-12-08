# encoding: utf-8
import logging
import signal
from time import time
from functools import wraps
from inspect import isgeneratorfunction
from collections import namedtuple, defaultdict
from multiprocessing import RLock
from tornado.gen import Return, sleep
from tornado.ioloop import IOLoop
from tornado.locks import Lock


FunctionType = type(lambda: None)
log = logging.getLogger("cache")


class Result(namedtuple('ResultBase', "ts result")):
    def __new__(cls, result):
        return super(Result, cls).__new__(cls, ts=time(), result=result)


class Cache(object):
    __slots__ = ('timeout', 'ignore_self', 'oid')

    CACHE = {}
    FUTURE_LOCKS = defaultdict(Lock)
    RLOCKS = defaultdict(RLock)

    def __init__(self, timeout, ignore_self=False, oid=None):
        self.timeout = timeout
        self.ignore_self = ignore_self
        self.oid = oid

    @staticmethod
    def hash_func(key):
        if isinstance(key, FunctionType):
            return ".".join((key.__module__, key.__name__))
        else:
            return str(key)

    @classmethod
    def invalidate(cls, func):
        fkey = cls.hash_func(func)

        hash_fkey = hash(fkey)
        for key in filter(lambda x: hash(x[0]) == hash_fkey, cls.CACHE):
            log.debug('INVALIDATING Cache for %r', key)
            cls.CACHE.pop(key, -1)
            cls.FUTURE_LOCKS.pop(key, -1)
            cls.RLOCKS.pop(key, -1)

    @classmethod
    def invaliate_all(cls, *args, **kwargs):
        log.warning("Invalidating all memory cache.")
        cls.CACHE.clear()
        cls.FUTURE_LOCKS.clear()
        cls.RLOCKS.clear()

    def __call__(self, func):
        is_generator = isgeneratorfunction(func)
        key = self.oid or self.hash_func(func)

        def get_hash(func, args, kwargs):
            return tuple(
                map(
                    hash,
                    (
                        key,
                        tuple(map(hash, args[1:] if self.ignore_self else args)),
                        tuple(map(lambda x: tuple(map(hash, x)), kwargs.items())),
                        is_generator,
                    )
                )
            )

        @wraps(func)
        def wrap(*args, **kwargs):
            io_loop = IOLoop.current()

            args_key = get_hash(func, args, kwargs)
            start_time = io_loop.time()

            with self.RLOCKS[args_key]:
                ret = self.CACHE.get(args_key)

                if isinstance(ret, Result):
                    log.debug("HIT Cache [%s] %r", key, args_key)
                    return ret.result

                ret = Result(func(*args, **kwargs))
                self.CACHE[args_key] = ret

                io_loop.add_callback(
                    io_loop.call_later,
                    self.timeout,
                    self._expire,
                    key,
                    args_key
                )

                log.debug(
                    "MISS Cache [%s] %r. Execution time %.6f sec.",
                    key,
                    args_key,
                    io_loop.time() - start_time
                )
                return ret.result

        @wraps(func)
        def wrap_gen(*args, **kwargs):
            io_loop = IOLoop.current()

            args_key = get_hash(func, args, kwargs)
            start_time = io_loop.time()

            with (yield self.FUTURE_LOCKS[args_key].acquire()):
                ret = self.CACHE.get(args_key)

                if isinstance(ret, Result):
                    yield sleep(0)
                    log.debug("HIT Cache [%s] %r", key, args_key)
                    raise Return(ret.result)

                gen = func(*args, **kwargs)

                try:
                    f = next(gen)
                    while True:
                        res = yield f
                        f = gen.send(res)
                except Return as e:
                    ret = Result(e.value)
                except StopIteration as e:
                    ret = Result(getattr(e, 'value', None))

                if ret.result:
                    self.CACHE[args_key] = ret
                    io_loop.add_callback(
                        io_loop.call_later,
                        self.timeout,
                        self._expire,
                        key,
                        args_key
                    )

                    log.debug(
                        "MISS Cache [%s] %r. Execution time %.6f sec.",
                        key,
                        args_key,
                        io_loop.time() - start_time
                    )
                else:
                    log.warning(
                        "Generator '%s' no return any value. Cache ignoring.",
                        self.hash_func(func)
                    )

                    log.debug("INVALID Cache [%s] %r", key, args_key)

                raise Return(ret.result)

        return wrap_gen if is_generator else wrap

    def _expire(self, key, args_key):
        self.CACHE.pop(args_key)
        log.debug("EXPIRED Cache [%s] %r", key, args_key)


signal.signal(signal.SIGUSR1, Cache.invaliate_all)
signal.signal(signal.SIGUSR2, Cache.invaliate_all)


MINUTE = 60
HOUR = MINUTE * 60
DAY = 24 * HOUR
WEEK = 7 * DAY
MONTH = 4 * WEEK
