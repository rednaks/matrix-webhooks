from typing import List

from ninja import Schema
from ninja.orm import create_schema

from apps.handlers import AvailableSources
from apps.home.models import MatrixRoomModel


class Source(Schema):
    source: AvailableSources


class WebhookPayload(Schema):
    ...


RoomSchema = create_schema(MatrixRoomModel)


class RoomsList(Schema):
    rooms: List[RoomSchema]
