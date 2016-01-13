# encoding: utf-8
import logging
import os
import signal
from time import time
from functools import wraps
from inspect import isgeneratorfunction
from collections import defaultdict
from multiprocessing import RLock
from tornado.gen import Return, sleep
from tornado.ioloop import IOLoop
from tornado.locks import Lock


try:
    import cPickle as pickle
except ImportError:
    import pickle


FunctionType = type(lambda: None)
log = logging.getLogger("cache")


class Result(object):
    def __init__(self, result):
        self.__result = result
        self.__ts = time()

    @property
    def result(self):
        return self.__result

    @property
    def ts(self):
        return self.__ts


class Cache(object):
    __slots__ = ('timeout', 'ignore_self', 'oid', 'files_cache')

    CACHE_DIR = None
    CACHE = {}
    FUTURE_LOCKS = defaultdict(Lock)
    RLOCKS = defaultdict(RLock)

    def __init__(self, timeout, ignore_self=False, oid=None, files_cache=False):
        self.timeout = timeout
        self.ignore_self = ignore_self
        self.oid = oid
        self.files_cache = files_cache

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

    def get_cache(self, key):
        if self.files_cache:
            fname = self.get_cache_file(key)

            if not os.path.exists(fname):
                return None

            with open(fname, 'rb') as f:
                result = pickle.load(f)

            if result.ts < (time() - self.timeout):
                IOLoop.current().add_callback(os.remove, fname)
                return None

            return result

        return self.CACHE.get(key)

    def set_cache(self, key, value):
        if self.files_cache:
            fname = self.get_cache_file(key)

            with open(fname, 'wb+') as f:
                pickle.dump(value, f)

        else:
            self.CACHE[key] = value

    @classmethod
    def invalidate_all(cls, *args, **kwargs):
        log.warning("Invalidating all memory cache.")
        cls.CACHE.clear()
        cls.FUTURE_LOCKS.clear()
        cls.RLOCKS.clear()

        log.warning("Invalidating all disk cache.")
        files = filter(
            lambda x: os.path.isfile(x),
            (os.path.join(cls.CACHE_DIR, f) for f in os.listdir(cls.CACHE_DIR))
        )

        for file in files:
            try:
                os.remove(file)
            except Exception as e:
                log.exception(e)

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
                ret = self.get_cache(args_key)

                if isinstance(ret, Result):
                    log.debug("HIT Cache [%s] %r", key, args_key)
                    return ret.result

                ret = Result(func(*args, **kwargs))
                self.set_cache(args_key, ret)

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
                ret = self.get_cache(args_key)

                if isinstance(ret, Result):
                    yield sleep(0)
                    log.debug("HIT Cache [%s] %r", key, args_key)
                    raise Return(ret.result)

                gen = func(*args, **kwargs)

                try:
                    f = next(gen)
                    while True:
                        try:
                            res = yield f
                            f = gen.send(res)
                        except (Return, StopIteration):
                            raise
                        except Exception as e:
                            f = gen.throw(e)

                except Return as e:
                    ret = Result(e.value)
                except StopIteration as e:
                    ret = Result(getattr(e, 'value', None))

                if ret.result:
                    self.set_cache(args_key, ret)

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

    def get_cache_file(self, args_key):
        return os.path.join(self.CACHE_DIR, str(hash(args_key)))

    def _expire(self, key, args_key):
        if self.files_cache:
            fname = self.get_cache_file(args_key)
            if os.path.exists(fname):
                os.remove(fname)

        self.CACHE.pop(args_key)
        log.debug("EXPIRED Cache [%s] %r", key, args_key)


signal.signal(signal.SIGUSR1, Cache.invalidate_all)
signal.signal(signal.SIGUSR2, Cache.invalidate_all)


MINUTE = 60
HOUR = MINUTE * 60
DAY = 24 * HOUR
WEEK = 7 * DAY
MONTH = 4 * WEEK
