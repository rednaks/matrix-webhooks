import logging
from datetime import datetime

from asgiref.sync import async_to_sync, sync_to_async
from mautrix.types import EventType, Membership
from mautrix.client import Client
import markdownify

from apps.helpers import get_redis_client
from apps.home.models import UserAccountModel, MatrixRoomModel
from apps.matrix.render import jinja_env, TEMPLATE
from apps.handlers.discord import DiscordWebhookHandler
from apps.types import MatrixConfig
from apps.helpers import get_pending_invitation_key, get_invitation_incident_key


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


async def joinserver(config: MatrixConfig) -> None:
    client = await get_client(config)
    redis_client = get_redis_client()
    # TODO: add to custom settings, change to list to include moderators maybe.
    _ADMIN_PL = 100

    @client.on(EventType.ROOM_POWER_LEVELS)
    async def handle_power_level_invites(event):

        pending_invitation = get_pending_invitation_key(event.room_id)
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
            redis_client.set(get_invitation_incident_key(inviter, room_id), "banned")
            redis_client.expire(get_invitation_incident_key(inviter, room_id), 60 * 60)
        else:
            logging.info("Invitation accepted")
        redis_client.delete(pending_invitation)

    @client.on(EventType.ROOM_MEMBER)
    async def handle_join_invite(event):
        logging.debug(f"handling invites {event.json()}")
        if not (event.content.membership == Membership.INVITE and event.unsigned.invite_room_state):
            return
        joined = []
        for state in event.unsigned.invite_room_state:
            if state.room_id in joined:
                continue
            try:
                logging.debug(f"{event.content}")
                if redis_client.ttl(get_invitation_incident_key(event.sender, state.room_id)) > -1:
                    await client.leave_room(state.room_id,
                                            reason=f"Can't accept invitation, {event.sender} is blocked")
                    continue

                if not event.content.is_direct:
                    # set invitation for review
                    review_key = get_pending_invitation_key(state.room_id)
                    logging.info(f"setting invitation for review: {review_key}")
                    redis_client.set(review_key, event.sender)
                else:
                    logging.info(f"Bot was invited in a direct chat, joining without review : {state.room_id}")

                if event.content.reason:
                    # find user with token
                    provided_token = event.content.reason
                    room_id = state.room_id
                    logging.info(f"Invitation provided a reason (token) '{provided_token}', looking for user match")
                    await assign_room_to_user(provided_token, room_id)

                await client.join_room(state.room_id)
                joined.append(state.room_id)
            except Exception:
                logging.error(f"Error when handling invitation", exc_info=True)

    @client.on(EventType.ROOM_MEMBER)
    async def handle_leave(event):
        processed_event_key = f"processed_matrix_event:{event.event_id}"
        processed = redis_client.get(processed_event_key)

        if event.content.membership == Membership.LEAVE and not processed:
            logging.info(f"Bot was removed from room: {event.room_id} by @{event.sender}")
            try:
                await unassign_room_from_user(event.room_id)
            except Exception:
                logging.warning(f"something happened when handling leave for room {event.room_id}", exc_info=True)
            redis_client.set(processed_event_key, datetime.now().timestamp())
            redis_client.expire(processed_event_key, 60 * 60 * 24 * 10)
        elif processed:
            logging.info(f"Event {event.event_id} is already processed, nothing to do")

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


@sync_to_async
def assign_room_to_user(provided_token, room_id):
    try:
        user = UserAccountModel.objects.get(token=provided_token)
        room, _ = MatrixRoomModel.objects.get_or_create(room_id=room_id)
        user.rooms.add(room)
        user.save()
    except UserAccountModel.DoesNotExist:
        logging.warning(f"No user found with provided token {provided_token}")


@sync_to_async
def unassign_room_from_user(room_id):
    try:
        room = MatrixRoomModel.objects.get(room_id=room_id)
        user = UserAccountModel.objects.get(rooms=room)
        user.rooms.remove(room)
        user.save()
    except MatrixRoomModel.DoesNotExist:
        ...
    except UserAccountModel.DoesNotExist:
        ...


class BotAPIException(Exception):
    ...
