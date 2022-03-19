import os
import redis
from django.conf import settings


def get_redis_client():
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db='db0',  # os.getenv('REDIS_DB'),
    )
    assert redis_client.ping()  # check if connection is successful
    return redis_client
