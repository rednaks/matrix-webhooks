#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path, include

from apps.home import urls as home_urls
from apps.api import urls as api_urls

urlpatterns = [
    path('', include(home_urls)),
    path('api/', include(api_urls)),
]
