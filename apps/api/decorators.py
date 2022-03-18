from functools import wraps


class RateLimitException(Exception):
    ...


def ratelimit(func):
    @wraps(func)
    def wrapper(request, *a, **kw):
        print(a)
        print(kw)
        if False:
            raise RateLimitException("Too Many Requests")

        return func(request, *a, **kw)

    return wrapper
