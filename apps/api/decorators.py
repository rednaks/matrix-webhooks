from functools import wraps

from apps.helpers import get_redis_client
from constance import config


class RateLimitException(Exception):
    ...


def ratelimit(func):
    @wraps(func)
    def wrapper(request, *a, **kw):
        print(f"token : {kw['user_token']}")
        token = kw['user_token']
        redis_client = get_redis_client()
        key = f"ratelimit:{token}"

        if int(redis_client.incr(key)) > config.API_RATE_LIMIT:
            raise RateLimitException("Too Many Requests")

        if redis_client.ttl(key) == -1:
            redis_client.expire(key, 1)

        return func(request, *a, **kw)

    return wrapper
