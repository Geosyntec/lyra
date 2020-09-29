import functools
import hashlib
import logging

import orjson
import redis

from lyra.models.response_models import CachedJSONResponse

logger = logging.getLogger(__name__)


redis_cache = redis.Redis(host="redis", port=6379, db=9)

CAN_CACHE = False


def flush():  # pragma: no cover
    try:
        if redis_cache.ping():
            redis_cache.flushdb()
            logger.debug("flushed redis function cache")
    except redis.ConnectionError:
        pass


def use_cache(state: bool = True):  # pragma: no cover
    try:
        if redis_cache.ping():
            redis_cache.set("CACHE_ENDABLED", orjson.dumps(state))
            logger.debug("flushed redis function cache")
    except redis.ConnectionError:
        pass


def _get_result(obj, ex, as_response, cache_enabled, *args, **kwargs):
    errors = None
    result = b"null"
    process_type = "cached" if cache_enabled else "cache_disabled"

    try:
        result = obj(*args, **kwargs)

    except Exception as e:
        if as_response:
            errors = [repr(e), str(getattr(e, "data", ""))]
            response = CachedJSONResponse(
                status="FAILURE",
                process_type="cache_failed",
                expires_after=0,
                errors=errors,
            ).dict()
            return orjson.dumps(response)
        else:
            raise e

    if as_response:
        data = orjson.loads(result)
        response = CachedJSONResponse(
            process_type=process_type, data=data, expires_after=ex, errors=errors
        ).dict()
        result = orjson.dumps(response)

    return result


def rcache(**rkwargs):
    _24hrs = 3600 * 24
    ex = rkwargs.pop("ex", _24hrs)  # default expire within 24 hours
    as_response = rkwargs.pop("as_response", False)

    def _rcache(obj):
        cache = redis_cache

        @functools.wraps(obj)
        def memoizer(*args, **kwargs):
            cache_enabled = orjson.loads(cache.get("CACHE_ENDABLED") or b"true")

            if not cache_enabled:
                return _get_result(obj, ex, as_response, cache_enabled, *args, **kwargs)

            sorted_kwargs = {k: kwargs[k] for k in sorted(kwargs.keys())}

            logger.info("cached call: " + obj.__name__ + str(args) + str(sorted_kwargs))

            # hashing the key may not be necessary, but it keeps the server-side filepaths hidden
            key = hashlib.sha256(
                (obj.__name__ + str(args) + str(sorted_kwargs)).encode("utf-8")
            ).hexdigest()

            if cache.get(key) is None:
                logger.debug(f"redis cache miss {key}")

                result = _get_result(
                    obj, ex, as_response, cache_enabled, *args, **kwargs
                )

                cache.set(key, result, ex=ex)

            else:
                logger.debug(f"redis hit cache {key}")

            return cache.get(key)

        return memoizer

    return _rcache


def no_cache(**rkwargs):  # pragma: no cover
    def _rcache(obj):
        @functools.wraps(obj)
        def memoizer(*args, **kwargs):
            return obj(*args, **kwargs)

        return memoizer

    return _rcache


def get_cache_decorator():
    """fetch a cache decorator for functions. If redis is up,
    use that, else use no_cache.

    The point of the no_cache fallback is to make development easier.
    In production and even in CI this should use the redis cache.
    """
    global CAN_CACHE
    try:
        if redis_cache.ping():
            CAN_CACHE = True
            return rcache
        else:  # pragma: no cover
            return no_cache
    except redis.ConnectionError:  # pragma: no cover
        return no_cache


cache_decorator = get_cache_decorator()
