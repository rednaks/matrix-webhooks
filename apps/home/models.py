import random
import secrets

from django.conf import settings
from django.db import models


class MatrixRoomModel(models.Model):
    room_id = models.CharField(max_length=512, unique=True)


class WebhookMetrics(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room = models.ForeignKey(MatrixRoomModel, on_delete=models.CASCADE)
    ts = models.DateTimeField(auto_now_add=True)
    count = models.IntegerField(default=0)


# TODO: caching ?
class WaitingListUserAccountModel(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )


class UserAccountModel(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    token = models.CharField(max_length=50)
    rooms = models.ManyToManyField(MatrixRoomModel)

    @staticmethod
    def generate_token():
        length = max(20, int(random.random() * 49))  # nosec
        return secrets.token_urlsafe(length)
