import redis
from django.conf import settings


def get_redis_client() -> redis.Redis:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT
    )
    assert redis_client.ping()  # check if connection is successful
    return redis_client


def make_invitation_code_key(invitation_code):
    return f"INVITATION_CODE:{invitation_code.lower()}"


PENDING_INVITATIONS_PREFIX = "pending_invitations"
INCIDENTS_CACHE_KEY_PREFIX = "invitation_incident"


def get_pending_invitation_key(key: str) -> str:
    return f"{PENDING_INVITATIONS_PREFIX}:{key}"


def get_invitation_incident_key(user_id: str, room_id: str) -> str:
    return f"{INCIDENTS_CACHE_KEY_PREFIX}:{user_id}:{room_id}"


