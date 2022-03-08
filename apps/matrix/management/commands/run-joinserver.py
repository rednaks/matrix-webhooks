import asyncio

from django.core.management.base import BaseCommand
from apps.matrix import bot
from apps.matrix.utils import get_matrix_config


class Command(BaseCommand):
    def handle(self, *args, **options):
        config = get_matrix_config()
        config.homeserver = options.get('homeserver') or config.homeserver
        asyncio.get_event_loop().run_until_complete(bot.joinserver(config))

    def add_arguments(self, parser):
        parser.add_argument('--homeserver', dest='homeserver', type=str, required=False)
