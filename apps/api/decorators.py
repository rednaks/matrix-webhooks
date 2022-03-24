from functools import wraps
import logging

from apps.helpers import get_redis_client
from constance import config

from apps.home.models import MatrixRoomModel, UserAccountModel


class RateLimitException(Exception):
    ...


class NoPermissionToNotifyRoomException(Exception):
    ...


def ratelimit(func):
    @wraps(func)
    def wrapper(request, *a, **kw):
        logging.debug(f"token : {kw['user_token']}")
        token = kw['user_token']
        redis_client = get_redis_client()
        key = f"ratelimit:{token}"

        if int(redis_client.incr(key)) > config.API_RATE_LIMIT:
            raise RateLimitException("Too Many Requests")

        if redis_client.ttl(key) == -1:
            redis_client.expire(key, 1)

        return func(request, *a, **kw)

    return wrapper


def check_notify_permission(func):
    @wraps(func)
    def wrapper(request, *a, **kw):
        room_id = kw['room_id']
        token = kw['user_token']
        logging.info(f"Checking permission to notify : {room_id}")
        room, created = MatrixRoomModel.objects.get_or_create(room_id=room_id)
        user_account = UserAccountModel.objects.get(token=token)

        if created:
            logging.info(f"Room {room_id} not claimed will be assigned to user_account({user_account.id})")
            user_account.rooms.add(room)
        elif room not in user_account.rooms.all():
            raise NoPermissionToNotifyRoomException()

        return func(request, *a, **kw)

    return wrapper
