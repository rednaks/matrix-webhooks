from django.urls import path
from apps.api.api_v1 import api as api_v1


urlpatterns = [
    path('v1/', api_v1.urls),
]
