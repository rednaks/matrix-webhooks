from asgiref.sync import async_to_sync
from mautrix.types import EventType, Membership
from mautrix.client import Client
import markdownify
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


async def joinserver(config: MatrixConfig) -> None:
    client = await get_client(config)

    @client.on(EventType.ROOM_MEMBER)
    async def handle_join_invite(event):
        if event.content.membership == Membership.INVITE and event.unsigned.invite_room_state:
            joined = []
            for state in event.unsigned.invite_room_state:
                if state.room_id in joined:
                    continue
                try:
                    await client.join_room(state.room_id)
                    print(f"joined {state.room_id}")
                    joined.append(state.room_id)
                except Exception as e:
                    print(e)

    print("start join server")
    await client.start(filter_data=None)


@async_to_sync
async def check_in_room(config: MatrixConfig, room_id: str) -> bool:
    client = await get_client(config)
    try:
        joined_rooms = await client.get_joined_rooms()
        return room_id in joined_rooms
    except Exception as e:
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
        print(e.message)
        raise BotAPIException(e.message)
    finally:
        await client.api.session.close()


@async_to_sync
async def login(config: MatrixConfig) -> None:
    client = await get_client(config)
    response = await client.login(password=config.password)
    await client.api.session.close()
    return response


class BotAPIException(Exception):
    ...
