import logging

from asgiref.sync import async_to_sync
from mautrix.types import EventType, Membership
from mautrix.client import Client
import markdownify

from apps.helpers import get_redis_client
from apps.matrix.render import jinja_env, TEMPLATE
from apps.handlers.discord import DiscordWebhookHandler
from apps.types import MatrixConfig


def build_msg(msg, fallback_msg):
    return {
        'body': fallback_msg,
        'formatted_body': msg,
        'msgtype': 'm.text',
        "format": "org.matrix.custom.html"
    }


def build_formatted_msg(payload: DiscordWebhookHandler) -> str:
    tmpl = jinja_env.from_string(TEMPLATE)
    return tmpl.render(context=payload.dict())


def build_fallback_msg(formatted_msg):
    return markdownify.markdownify(formatted_msg)


async def get_client(config: MatrixConfig) -> Client:
    return Client(config.user_id, base_url=config.homeserver, token=config.access_token)


PENDING_INVITATIONS_PREFIX = "pending_invitations"
INCIDENTS_CACHE_KEY_PREFIX = "invitation_incident"


def _get_pending_invitation_key(key: str) -> str:
    return f"{PENDING_INVITATIONS_PREFIX}:{key}"


def _get_invitation_incident_key(user_id: str, room_id: str) -> str:
    return f"{INCIDENTS_CACHE_KEY_PREFIX}:{user_id}:{room_id}"


async def joinserver(config: MatrixConfig) -> None:
    client = await get_client(config)
    redis_client = get_redis_client()
    # TODO: add to custom settings, change to list to include moderators maybe.
    _ADMIN_PL = 100

    @client.on(EventType.ROOM_POWER_LEVELS)
    async def handle_power_level_invites(event):

        pending_invitation = _get_pending_invitation_key(event.room_id)
        logging.debug(f"{event.json()}")
        inviter = redis_client.get(pending_invitation)
        if not inviter:
            return
        inviter = inviter.decode("utf-8")
        room_id = event.room_id
        logging.info(f"Reviewing invitation for room {room_id} from {inviter}")
        if event.content.users.get(inviter) != _ADMIN_PL:
            logging.info(f"Conditions not met ! leaving {room_id}, because of {inviter}")
            # Leave with reason !
            await client.leave_room(room_id, reason=f"{inviter} is not admin, not allowed to invite me in this room.")

            # Ban the user from inviting the bot for 1h.
            redis_client.set(_get_invitation_incident_key(inviter, room_id), "banned")
            redis_client.expire(_get_invitation_incident_key(inviter, room_id), 60 * 60)
        else:
            logging.info("Invitation accepted")
        redis_client.delete(pending_invitation)

    @client.on(EventType.ROOM_MEMBER)
    async def handle_join_invite(event):
        logging.debug(f"handling invites {event.json()}")
        if event.content.membership == Membership.INVITE and event.unsigned.invite_room_state:
            joined = []
            for state in event.unsigned.invite_room_state:
                if state.room_id in joined:
                    continue
                try:
                    logging.debug(f"{event.content}")
                    logging.debug(f"{event.json()}")
                    if redis_client.ttl(_get_invitation_incident_key(event.sender, state.room_id)) > -1:
                        await client.leave_room(state.room_id,
                                                reason="Can't accept invitation, {event.sender} is blocked")
                    else:
                        await client.join_room(state.room_id)
                    if not event.content.is_direct:
                        redis_client.set(_get_pending_invitation_key(state.room_id), event.sender)
                    else:
                        logging.info(f"joined : {state.room_id}")
                    joined.append(state.room_id)
                except Exception:
                    logging.error(f"Error when handleing invitation", exc_info=True)

    logging.info("start join server")
    await client.start(filter_data=None)


@async_to_sync
async def check_in_room(config: MatrixConfig, room_id: str) -> bool:
    client = await get_client(config)
    try:
        joined_rooms = await client.get_joined_rooms()
        return room_id in joined_rooms
    except Exception as e:
        logging.error("couldn't get list of joined rooms.", exc_info=True)
        raise BotAPIException(e.message)
    finally:
        await client.api.session.close()


@async_to_sync
async def send(config: MatrixConfig, room_id: str, payload: DiscordWebhookHandler) -> None:
    client = await get_client(config)

    rendered = build_formatted_msg(payload)

    fallback_msg = build_fallback_msg(rendered)
    msg = build_msg(rendered, fallback_msg)
    try:
        await client.send_message_event(
            room_id=room_id,
            content=msg,
            event_type=EventType.ROOM_MESSAGE
        )
    except Exception as e:
        logging.error(f"couldn't send msg to {room_id}.", exc_info=True)
        raise BotAPIException(e.message)
    finally:
        await client.api.session.close()


@async_to_sync
async def login(config: MatrixConfig) -> None:
    client = await get_client(config)
    response = await client.login(password=config.password)
    await client.set_displayname("@webhooks:matrix-webhooks.com")
    await client.api.session.close()
    return response


class BotAPIException(Exception):
    ...
