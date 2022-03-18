from functools import wraps


class RateLimitException(Exception):
    ...


def ratelimit(func):
    @wraps(func)
    def wrapper(request, *a, **kw):
        print(f"token : {kw['user_token']}")
        if False:
            raise RateLimitException("Too Many Requests")

        return func(request, *a, **kw)

    return wrapper
