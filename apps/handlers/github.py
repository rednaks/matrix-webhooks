from typing import Dict

from .discord import DiscordHandlerModel, Embed, EmbedAuthor
from .generic import GenericHandler, HandlerParseException


class GithubWebhookHandler(GenericHandler):

    def __init__(self):
        self.__EVENT_TO_BUILDER__ = {
            'push': GithubWebhookHandler._build_push,
            'issues': GithubWebhookHandler._build_issue,
            'issue_comment': GithubWebhookHandler._build_comment,
            'pull_request': GithubWebhookHandler._build_pull_request,
        }

    def parse(self, payload: Dict, **kwargs) -> DiscordHandlerModel:
        event = kwargs.get('headers', {}).get('X-Github-Event')
        return DiscordHandlerModel(
            embeds=[
                self._build_embed_for_event(payload, event)
            ]
        )

    def _build_embed_for_event(self, data, event) -> Embed:
        try:
            return self.__EVENT_TO_BUILDER__[event](data)
        except KeyError:
            raise HandlerParseException("unsupported event name")

    @staticmethod
    def _build_push(data: Dict) -> Embed:
        repo = data['repository']['name']
        branch = data['ref'].replace('refs/heads/', '')

        commits = data['commits']
        number_of_commits = len(commits)
        # TODO: link to commit
        description = "<br/>".join([f"`{commit['id'][:7]}` {commit['message']}" for commit in commits[:10]])

        return Embed(
            author=EmbedAuthor(name=data['pusher']['name']),
            title=f"[{repo}:{branch}] {number_of_commits} commit(s)",  # TODO: title url
            # TODO: url= refs diff
            description=description,
            color='7506394'
        )

    @staticmethod
    def _build_issue(data: Dict) -> Embed:
        repo = data['repository']['name']

        issue_attributes = data['issue']
        description = issue_attributes['body']
        action = data['action']
        user = issue_attributes['user']

        _ACTION_COLOR = {
            'closed': '0',
            'opened': '15426592',
            'reopened': '15426592',
        }

        return Embed(
            author=EmbedAuthor(name=user['login'], url=user['html_url']),
            title=f"[{repo}] Issue {action}: #{issue_attributes['number']} {issue_attributes['title']}",
            description=description,
            url=issue_attributes['html_url'],
            color=_ACTION_COLOR.get(action, '0')
        )

    @staticmethod
    def _build_comment(data: Dict) -> Embed:
        repo = data['repository']['name']

        comment = data['comment']
        description = comment['body']
        issue = data['issue']
        user = comment['user']

        return Embed(
            author=EmbedAuthor(name=user['login'], url=user['html_url']),
            title=f"[{repo}] New comment on issue #{issue['number']} {issue['title']}",
            description=description,
            url=comment['html_url'],
            color='15109472'
        )

    @staticmethod
    def _build_pull_request(data: Dict) -> Embed:
        _ACTION_COLOR = {
            'closed': '0',
            'opened': '10026904',
            'reopened': '15426592',
        }

        repo = data['repository']['name']

        pr = data['pull_request']
        description = pr['body']
        action = data['action']
        user = pr['user']

        return Embed(
            author=EmbedAuthor(name=user['login'], url=user['html_url']),
            title=f"[{repo}] Pull request {action}: #{pr['number']} {pr['title']}",
            description=description,
            url=pr['html_url'],
            color=_ACTION_COLOR.get(action, '0')
        )
