from django.contrib import admin
from core.models import UserData, UserCount, GemsCoins, Friends, GiftSent, Leaderboard, RequestGift, Match, MatchUser

# Register your models here.

@admin.register(UserData)
class UserDataAdmin(admin.ModelAdmin):
    list_display = ('login_role','username','first_name','last_name','email','user_id','star_level','total_wining','total_match','total_win_match','country','profile_url','created','updated')

@admin.register(UserCount)
class UserCountAdmin(admin.ModelAdmin):
    list_display = ('guest','facebook','google')

@admin.register(GemsCoins)
class GemsCoinsAdmin(admin.ModelAdmin):
    list_display = ('user','coins','gems')

@admin.register(Friends)
class FriendsAdmin(admin.ModelAdmin):
    list_display = ('sender','receiver','friend_status')

@admin.register(GiftSent)
class GiftSentAdmin(admin.ModelAdmin):
    list_display = ('coin_sender','coin_receiver','coin','flag')

@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('user','weekly_coins','lastweek_coins')

@admin.register(RequestGift)
class RequestGiftdAdmin(admin.ModelAdmin):
    list_display = ('request_sender','request_receiver','flag')

@admin.register(Match)
class MatchdAdmin(admin.ModelAdmin):
    list_display = ('code','status','created_by')

@admin.register(MatchUser)
class MatchUserdAdmin(admin.ModelAdmin):
    list_display = ('match','user','status')