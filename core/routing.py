from django.urls import path

from core import consumers

websocket_urlpatterns = [
    path('', consumers.PlaywithFriendsConsumer.as_asgi()),
    path('online-match/', consumers.OnlineMatchConsumer.as_asgi()),
]