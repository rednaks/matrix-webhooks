from django.http import HttpRequest
from ninja import NinjaAPI

from apps.api.decorators import ratelimit, check_notify_permission
from apps.api.exception_handlers import add_exception_handlers
from apps.api.schemas import Source, WebhookPayload, RoomsList
from apps.api.security import APIKeyPath
from apps.handlers import get_handler, AvailableSources
from apps.home.models import UserAccountModel
from apps.matrix import bot
from typing import Any, Dict
import json
import logging

from apps.helpers import get_redis_client, get_pending_invitation_key

from apps.matrix.utils import get_matrix_config

api = NinjaAPI(title="Matrix Webhooks API", version='1', auth=APIKeyPath())


def _handle_webhook(room_id: str, webhook_payload: Dict[Any, Any], request: HttpRequest = None,
                    source: AvailableSources = AvailableSources.DISCORD):
    handler = get_handler(source.name)()
    try:
        headers = request.headers
        payload = handler.parse(webhook_payload, headers=headers)
    except Exception as e:
        logging.warning(f'unable to parse')
        logging.warning(f'payload: {webhook_payload}')
        logging.warning(f'source: {source.name}')
        logging.warning(f'headers: {headers}')
        raise e

    config = get_matrix_config()
    bot.send(config, room_id, payload)
    return {
        'status': 'success',
        'msg': 'webhook sent'
    }


@api.post('/notify/{user_token}/{room_id}/{source}', url_name='notify')
@ratelimit
@check_notify_permission
def notify(request, user_token: str, room_id: str, source: Source,
           data: WebhookPayload):
    payload = json.loads(request.body)

    return _handle_webhook(room_id, payload, request, source.source)


@api.post('/notify/{user_token}/{room_id}/', url_name='notify')
@ratelimit
@check_notify_permission
def notify_default(request, user_token: str, room_id: str, data: WebhookPayload):
    payload = json.loads(request.body)
    return _handle_webhook(room_id, payload, request)


@api.get('/status/{user_token}/{room_id}/')
@ratelimit
def status(request, user_token: str, room_id: str):
    # check if we have a pending invitation.
    pending_invitation = get_pending_invitation_key(room_id)
    redis_client = get_redis_client()
    if redis_client.get(pending_invitation):
        status = 'pending'
    else:
        config = get_matrix_config()
        status = 'joined' if bot.check_in_room(config, room_id) else 'not joined'

    return {
        'status': status
    }


@api.get('/rooms/{user_token}/', response=RoomsList)
@ratelimit
def rooms(request, user_token: str) -> RoomsList:
    logging.info(f"user: {request.auth}")
    return UserAccountModel.objects.get(user=request.auth)


add_exception_handlers(api)
