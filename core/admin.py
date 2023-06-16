from django.contrib import admin
from core.models import (UserData, UserCount, GemsCoins, Friends, GiftSent, Leaderboard, RequestGift, Match, MatchUser,
                         Striker, UserStriker, AdPurchase, MatchCity)

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
    list_display = ('id','code','match_type','status','created_by','start_time','end_time')

@admin.register(MatchUser)
class MatchUserdAdmin(admin.ModelAdmin):
    list_display = ('id','match','user','status','city','user_turn','skip_turn','score')

@admin.register(Striker)
class StrikerAdmin(admin.ModelAdmin):
    list_display = ('id','status','index','created')

@admin.register(UserStriker)
class UserStrikerAdmin(admin.ModelAdmin):
    list_display = ('user','striker','status','created')

@admin.register(AdPurchase)
class AdPurchaseAdmin(admin.ModelAdmin):
    list_display = ('user','is_purchase')

@admin.register(MatchCity)
class MatchCityAdmin(admin.ModelAdmin):
    list_display = ('city','entry_fee','prize','index')