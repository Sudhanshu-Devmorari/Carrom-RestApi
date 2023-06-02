from rest_framework import serializers
from core.models import UserData, GemsCoins, Friends, GiftSent, Leaderboard, RequestGift, UserStriker, Striker, AdPurchase

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserData
        fields = ['login_role','username','user_id','email','first_name','last_name','country','star_level','total_wining','profile_pic','profile_url','total_match','total_win_match']


    def validate_username(self, value):
        if "_" in value or " " in value:
            raise serializers.ValidationError("You cannot use a space or an underscore in your username.")
        return value

class GemsCoinsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GemsCoins
        fields = ['user', 'coins', 'gems']

    """def validate(self, data):
        if data['coins'] == 0 or data['gems'] == 0:
            raise serializers.ValidationError('There are no specific coins or gems in your inventory.')
        return data"""
    def validate_coins(self, value):
        if value==0:
            raise serializers.ValidationError('There are no specific coins in your inventory.')
        return value
    def validate_gems(self, value):
        if value==0:
            raise serializers.ValidationError('There are no specific gems in your inventory.')
        return value

class FriendsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friends
        fields = ['sender', 'receiver', 'friend_status']

class GiftSentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiftSent
        fields = '__all__'


class LeaderboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leaderboard
        fields = '__all__'

class RequestGiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestGift
        fields = '__all__'

class StrikerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Striker
        fields = ('index',)

class UserStrikerSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    striker = StrikerSerializer()

    class Meta:
        model = UserStriker
        fields = ('user', 'striker')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Update striker table index key as striker_key
        representation['striker']['striker_index'] = representation['striker'].pop('index')
        merged_data = {**representation['user'], **representation['striker']}
        return merged_data
    
class AdPurchaseSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    
    class Meta:
        model = AdPurchase
        fields = ('user','is_purchase')