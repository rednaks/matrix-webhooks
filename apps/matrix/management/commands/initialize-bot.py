from django.core.management.base import BaseCommand
from constance import config
from apps.matrix import bot
from apps.matrix.utils import get_matrix_config


class Command(BaseCommand):
    def handle(self, *args, **options):
        matrix_config = get_matrix_config()
        matrix_config.password = options.get('password')
        response = bot.login(matrix_config)
        self.stdout.write(f"New token: {response.access_token}")
        setattr(config, "MATRIX_BOT_TOKEN", response.access_token)

    def add_arguments(self, parser):
        parser.add_argument('--password', dest='password', type=str)
