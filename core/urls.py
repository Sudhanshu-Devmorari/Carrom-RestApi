from django.urls import path
from . import views

urlpatterns = [
    path('guest-login/', views.GuestLoginView.as_view(), name='guest-login'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('gemcoin/', views.GemsCoinsView.as_view(), name='gems-coins'),
    path('guest-friend-search/', views.GuestFriendSearchView.as_view(), name='guest-friend'),
    path('request-show/', views.GuestFriendView.as_view(), name='request-show'),
    path('gift-coins/', views.GiftSentView.as_view(), name='gift-coins'),
    path('league/', views.LeaguesLeaderboardView.as_view(), name='league'),
    path('friend/', views.FriendsLeaderboardView.as_view(), name='friend'),
    path('country/', views.CountryLeaderboardView.as_view(), name='country'),
    path('world/', views.WorldLeaderboardView.as_view(), name='world'),
    path('friends/', views.FaceBookFriendListView.as_view(), name='fb-friend-list'),
    path('weekly-winning/', views.LeaderboardWiningView.as_view(), name='weekly-winning'),
    path('star-level/', views.UpdateStarLevelView.as_view(), name='star-level'),
    path('remove-friend/', views.RemoveFriends.as_view(), name='remove-friend'),
    path('logout/', views.GuestLogout.as_view(), name='logout'),
    path('', views.CheckView.as_view(), name='check'),
    path('request-gift/', views.RequestGiftView.as_view(), name='request-gift'),
    path('striker/', views.StrikerView.as_view(), name='striker-view'),
    path('ad-purchase/', views.AdPurchaseView.as_view(), name='ad-purchase'),
]

"""
FB-LogIn: https://127.0.0.1:8000/accounts/facebook/login/
Google-LogIn: https://127.0.0.1:8000/accounts/google/login/

LogOut: https://127.0.0.1:8000/accounts/logout/

# WebSocket URL:
new WebSocket("wss://127.0.0.1:8000/?secure_code=QWER1234");
"""