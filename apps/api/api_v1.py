import json
import logging
from datetime import datetime
from typing import Any, Dict

from django.conf import settings
from django.http import HttpRequest
from ninja import NinjaAPI

from apps.api.decorators import check_notify_permission, ratelimit
from apps.api.exception_handlers import add_exception_handlers
from apps.api.schemas import RoomsList, Source, WebhookPayload
from apps.api.security import APIKeyPath
from apps.handlers import AvailableSources, get_handler
from apps.home.models import MatrixRoomModel, UserAccountModel, WebhookMetrics
from apps.matrix import bot

logger = logging.getLogger(settings.LOGGER_NAME)

from apps.helpers import get_pending_invitation_key, get_redis_client
from apps.matrix.utils import get_matrix_config

api = NinjaAPI(title="Matrix Webhooks API", version="1", auth=APIKeyPath())


def update_api_usage(user: settings.AUTH_USER_MODEL, room_id: str) -> None:
    current_time = datetime.now().replace(second=0, microsecond=0)
    try:
        room = MatrixRoomModel.objects.get(room_id=room_id)
    except MatrixRoomModel.DoesNotExist:
        # should I log an error or a success ?
        return

    try:
        api_metrics = WebhookMetrics.objects.get(ts=current_time, user=user, room=room)
        api_metrics.count += 1
        api_metrics.save()
    except WebhookMetrics.DoesNotExist:
        WebhookMetrics.objects.create(room=room, user=user, count=1, ts=current_time)


def _handle_webhook(
    room_id: str,
    webhook_payload: Dict[Any, Any],
    request: HttpRequest,
    source: AvailableSources = AvailableSources.DISCORD,
):

    try:
        # update api usage metrics
        update_api_usage(request.user, room_id)
    except Exception as e:
        logging.warning(f"Couldn't update api usage: {e}", exc_info=True)

    handler = get_handler(source.name)()
    headers = request.headers
    try:
        payload = handler.parse(webhook_payload, headers=headers)
    except Exception as e:
        logger.warning(f"unable to parse")
        logger.warning(f"payload: {webhook_payload}")
        logger.warning(f"source: {source.name}")
        logger.warning(f"headers: {headers}")
        raise e

    config = get_matrix_config()
    bot.send(config, room_id, payload)

    return {"status": "success", "msg": "webhook sent"}


@api.post("/notify/{user_token}/{room_id}/{source}", url_name="notify")
@ratelimit
@check_notify_permission
def notify(
    request, user_token: str, room_id: str, source: Source, data: WebhookPayload
):
    payload = json.loads(request.body)

    return _handle_webhook(room_id, payload, request, source.source)


@api.post("/notify/{user_token}/{room_id}/", url_name="notify")
@ratelimit
@check_notify_permission
def notify_default(request, user_token: str, room_id: str, data: WebhookPayload):
    payload = json.loads(request.body)
    return _handle_webhook(room_id, payload, request)


@api.get("/status/{user_token}/{room_id}/")
@ratelimit
def status(request, user_token: str, room_id: str):
    # check if we have a pending invitation.
    pending_invitation = get_pending_invitation_key(room_id)
    redis_client = get_redis_client()
    if redis_client.get(pending_invitation):
        status = "pending"
    else:
        config = get_matrix_config()
        status = "joined" if bot.check_in_room(config, room_id) else "not joined"

    return {"status": status}


@api.get("/rooms/{user_token}/", response=RoomsList)
@ratelimit
def rooms(request, user_token: str) -> RoomsList:
    logger.info(f"user: {request.auth}")
    return UserAccountModel.objects.get(user=request.auth)


add_exception_handlers(api)
