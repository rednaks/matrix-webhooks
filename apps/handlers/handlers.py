from enum import Enum

from .discord import DiscordWebhookHandler
from .github import GithubWebhookHandler
from .gitlab import GitlabWebhookHandler


class AvailableSources(str, Enum):
    GITHUB = 'github'
    GITLAB = 'gitlab'
    DISCORD = ''


_HANDLERS = {
    AvailableSources.DISCORD.name: DiscordWebhookHandler,
    AvailableSources.GITHUB.name: GithubWebhookHandler,
    AvailableSources.GITLAB.name: GitlabWebhookHandler,
}


def get_handler(source):
    return _HANDLERS.get(source, _HANDLERS[AvailableSources.DISCORD.name])
