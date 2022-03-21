import redis
from django.conf import settings


def get_redis_client() -> redis.Redis:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT
    )
    assert redis_client.ping()  # check if connection is successful
    return redis_client
