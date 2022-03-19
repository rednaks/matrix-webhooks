from typing import Dict

from .discord import DiscordHandlerModel, Embed, EmbedAuthor
from .generic import GenericHandler


class GithubWebhookHandler(GenericHandler):

    def __init__(self):
        self.__EVENT_TO_BUILDER__ = {
            'push': GithubWebhookHandler._build_push,
            'issues': GithubWebhookHandler._build_issue,
            'note': GithubWebhookHandler._build_comment,
        }

    def parse(self, payload: Dict, **kwargs) -> DiscordHandlerModel:
        event = kwargs.get('headers', {}).get('X-Github-Event')
        return DiscordHandlerModel(
            embeds=[
                self._build_embed_for_event(payload, event)
            ]
        )

    def _build_embed_for_event(self, data, event) -> Embed:
        return self.__EVENT_TO_BUILDER__[event](data)

    @staticmethod
    def _build_push(data: Dict) -> Embed:
        repo = data['repository']['name']
        branch = data['ref'].replace('refs/heads/', '')

        commits = data['commits']
        number_of_commits = len(commits)
        # TODO: link to commit
        description = "\n".join([f"`{commit['id'][:7]}` {commit['message']}" for commit in commits[:10]])

        return Embed(
            author=EmbedAuthor(name=data.get('pusher', data['username'])),
            title=f"[{repo}:{branch}] {number_of_commits} commit(s)",  # TODO: title url
            # TODO: url= refs diff
            description=description,
            color='7506394'
        )

    @staticmethod
    def _build_issue(data: Dict) -> Embed:
        repo = data['project']['path_with_namespace']

        issue_attributes = data['object_attributes']
        description = issue_attributes['description']
        action = issue_attributes['action']
        user = data['user']

        _ACTION_COLOR = {
            'closed': '0',
            'open': '15426592',
            'reopen': '15426592',
        }

        return Embed(
            author=EmbedAuthor(name=user.get('name', user['username'])),
            title=f"[{repo}] Issue opened: #{issue_attributes['iid']} {issue_attributes['title']}",
            description=description,
            url=issue_attributes['url'],
            color=_ACTION_COLOR.get(action, '0')
        )

    @staticmethod
    def _build_comment(data: Dict) -> Embed:
        _NOTE_TYPE = {
            'Issue': data.get('issue'),
        }

        repo = data['project']['path_with_namespace']

        note = data['object_attributes']
        description = note['description']
        obj = _NOTE_TYPE.get(note['noteable_type'])
        user = data['user']

        return Embed(
            author=EmbedAuthor(name=user.get('name', user['username'])),
            title=f"[{repo}] New comment on issue #{obj['iid']} {obj['title']}",
            description=description,
            url=note['url'],
            color='15109472'
        )
