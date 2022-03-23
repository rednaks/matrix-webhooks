from django.db import models
from django.conf import settings
import secrets
import random


class MatrixRoomModel(models.Model):
    room_id = models.CharField(max_length=512, unique=True)


class UserAccountModel(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    token = models.CharField(max_length=50)
    rooms = models.ManyToManyField(MatrixRoomModel)

    @staticmethod
    def generate_token():
        length = max(20, int(random.random() * 70))  # nosec
        return secrets.token_urlsafe(length)
