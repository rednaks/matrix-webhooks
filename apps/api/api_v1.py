from django.http import HttpRequest
from ninja import NinjaAPI, Schema

from apps.api.decorators import ratelimit, RateLimitException
from apps.api.security import APIKeyPath
from apps.handlers import get_handler, AvailableSources
from apps.matrix import bot
from typing import Any, Dict
import json

from apps.matrix.utils import get_matrix_config

api = NinjaAPI(version='1', auth=APIKeyPath())


class Source(Schema):
    source: AvailableSources


class WebhookPayload(Schema):
    ...


def _handle_webhook(room_id: str, webhook_payload: Dict[Any, Any], request: HttpRequest = None,
                    source: AvailableSources = AvailableSources.DISCORD):
    handler = get_handler(source.name)()
    payload = handler.parse(webhook_payload, headers=request.headers)

    config = get_matrix_config()
    bot.send(config, room_id, payload)
    return {
        'status': 'success',
        'msg': 'webhook sent'
    }


@api.exception_handler(bot.BotAPIException)
def bot_error_handler(request, _):
    return api.create_response(
        request,
        {
            'status': 'error',
            'msg': 'internal api error'
        },
        status=503
    )


@api.exception_handler(RateLimitException)
def ratelimit_exception_handler(request, _):
    return api.create_response(
        request,
        {
            'status': 'error',
            'msg': 'too many requests'
        },
        status=420
    )


@api.post('/notify/{user_token}/{room_id}/{source}', url_name='notify')
@ratelimit
def notify(request, user_token: str, room_id: str, source: Source,
           data: WebhookPayload):
    payload = json.loads(request.body)

    return _handle_webhook(room_id, payload, request, source.source)


@api.post('/notify/{user_token}/{room_id}/', url_name='notify')
@ratelimit
def notify_default(request, user_token: str, room_id: str, data: WebhookPayload):
    payload = json.loads(request.body)
    return _handle_webhook(room_id, payload)


@api.get('/status/{user_token}/{room_id}/')
@ratelimit
def status(request, user_token: str, room_id: str):
    config = get_matrix_config()
    return {
        'status': 'joined' if bot.check_in_room(config, room_id) else 'not joined'
    }
