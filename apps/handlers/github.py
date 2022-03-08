from .generic import GenericHandler


class GithubWebhookHandler(GenericHandler):
    def parse(self, payload):
        raise Exception('Not Implemented')
