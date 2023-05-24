from django.urls import path, re_path
from core.views import (CheckView, GuestLoginView, ProfileView, GemsCoinsView, 
                        GuestFriendSearchView, GuestFriendView, GiftSentView, LeaguesLeaderboardView, FriendsLeaderboardView,
                        CountryLeaderboardView, WorldLeaderboardView, GuestLogout, FaceBookFriendListView, LeaderboardWiningView,
                        UpdateStarLevelView, RemoveFriends, RequestGiftView)
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('guest-login/', GuestLoginView.as_view(), name='guest-login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('gemcoin/', GemsCoinsView.as_view(), name='gems-coins'),
    path('guest-friend-search/', GuestFriendSearchView.as_view(), name='guest-friend'),
    path('request-show/', GuestFriendView.as_view(), name='request-show'),
    path('gift-coins/', GiftSentView.as_view(), name='gift-coins'),
    path('league/', LeaguesLeaderboardView.as_view(), name='league'),
    path('friend/', FriendsLeaderboardView.as_view(), name='friend'),
    path('country/', CountryLeaderboardView.as_view(), name='country'),
    path('world/', WorldLeaderboardView.as_view(), name='world'),
    path('friends/', FaceBookFriendListView.as_view(), name='fb-friend-list'),
    path('weekly-winning/', LeaderboardWiningView.as_view(), name='weekly-winning'),
    path('star-level/', UpdateStarLevelView.as_view(), name='star-level'),
    path('remove-friend/', RemoveFriends.as_view(), name='remove-friend'),
    path('logout/', GuestLogout.as_view(), name='logout'),
    path('', CheckView.as_view(), name='check'),
    path('request-gift/', RequestGiftView.as_view(), name='request-gift'),
]

"""
FB-LogIn: https://127.0.0.1:8000/accounts/facebook/login/
Google-LogIn: https://127.0.0.1:8000/accounts/google/login/

LogOut: https://127.0.0.1:8000/accounts/logout/

# WebSocket URL:
new WebSocket("wss://127.0.0.1:8000/?secure_code=QWER1234");
"""