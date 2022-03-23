import logging
from typing import Optional, Any

from django.http import HttpRequest
from django.urls import resolve

from ninja.security.apikey import APIKeyBase
from apps.home.models import UserAccountModel


class APIKeyPath(APIKeyBase):
    openapi_type: str = 'apikey'
    openapi_in: str = 'user_token'

    def _get_key(self, request: HttpRequest) -> Optional[str]:
        key = resolve(request.path).kwargs.get('user_token')
        return key

    def authenticate(self, request: HttpRequest, key) -> Optional[Any]:
        try:
            user = UserAccountModel.objects.get(token=key).user
            return user
        except UserAccountModel.DoesNotExist:
            logging.info("User not found")
