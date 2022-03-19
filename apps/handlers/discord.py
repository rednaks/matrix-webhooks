from .generic import GenericHandler
from typing import List, Optional
from pydantic import BaseModel, Field  # , validator


class EmbedAuthor(BaseModel):
    name: str = Field()
    url: Optional[str] = Field()


class EmbedField(BaseModel):
    name: str = Field()
    value: str = Field()


class Embed(BaseModel):
    title: str = Field(title="Embed Title")
    author: Optional[EmbedAuthor] = Field(title="Embed Author")
    color:  Optional[str] = Field()  # TODO
    url: Optional[str] = Field()
    description: Optional[str] = Field()
    timestamp: Optional[str] = Field()
    fields: Optional[List[EmbedField]] = Field()


class DiscordHandlerModel(BaseModel):
    content: Optional[str] = Field(title='Message content, required if embeds not present')
    embeds: Optional[List[Embed]] = Field(title='List of embeds, required if content is not present')

    # @validator('embeds')
    # def check_content_or_embed(cls, v, values):
    #     if 'content' not in values and not embeds:
    #         raise ValueError("either 'content' or 'embeds' must be present ")
    #     return embeds


class DiscordWebhookHandler(GenericHandler):
    def parse(self, payload, **_):
        return DiscordHandlerModel(**payload)
