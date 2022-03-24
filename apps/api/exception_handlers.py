from django.http import JsonResponse
from ninja import NinjaAPI

from apps.api.decorators import RateLimitException, NoPermissionToNotifyRoomException
from apps.handlers.generic import HandlerParseException
from apps.matrix.bot import BotAPIException


def bot_error_handler(*_):
    return JsonResponse(
        {
            'status': 'error',
            'msg': 'internal api error'
        },
        status_code=503
    )


def ratelimit_exception_handler(*_):
    return JsonResponse(
        {
            'status': 'error',
            'msg': 'too many requests'
        },
        status=429
    )


def notify_permission_exception_handler(*_):
    return JsonResponse(
        {
            'status': 'error',
            'msg': "You Don't have permission to send notifications to this room"
        },
        status=401,
    )


def parse_error_exception_handler(*_):
    return JsonResponse(
        {
            'status': 'error',
            'msg': 'Unsupported payload'

        },
        status=422
    )


def add_exception_handlers(api: NinjaAPI) -> None:
    api.add_exception_handler(BotAPIException, bot_error_handler)
    api.add_exception_handler(RateLimitException, ratelimit_exception_handler)
    api.add_exception_handler(NoPermissionToNotifyRoomException, notify_permission_exception_handler)
    api.add_exception_handler(HandlerParseException, parse_error_exception_handler)
