from rest_framework import serializers
from core.models import UserData, GemsCoins, Friends, GiftSent, Leaderboard, RequestGift, UserStriker, Striker, AdPurchase
from rest_framework.authtoken.models import Token

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
        fields = ('index', 'prize')

class UserStrikerSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    striker = StrikerSerializer()

    class Meta:
        model = UserStriker
        fields = ('user', 'striker')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        user_purchsed_striker_ids = list(UserStriker.objects.filter(user_id=instance.user.id).values_list('striker__index', flat=True))
        user_purchsed_striker = {'purchased_striker': user_purchsed_striker_ids}

        # Update striker table index key as striker_key
        representation['striker']['striker_index'] = representation['striker'].pop('index')
        merged_data = {**representation['user'], **representation['striker'], **user_purchsed_striker}
        return merged_data
    
class AdPurchaseSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    
    class Meta:
        model = AdPurchase
        fields = ('user','is_purchase')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        boolean_dict = {'is_purchase': representation['is_purchase']}
        merged_data = {**representation['user'], **boolean_dict}
        return merged_data

class UserAccountDataSerializer(serializers.Serializer):
    user = UserSerializer()
    gmescoin = GemsCoinsSerializer()
    adpurchase = AdPurchaseSerializer()
    striker = UserStrikerSerializer()

    def to_representation(self, instance):
        user_obj = UserData.objects.get(id=instance.id)
        gems_obj = GemsCoins.objects.filter(user_id=instance.id).first()
        ad_purchase_obj = AdPurchase.objects.filter(user_id=instance.id).first()
        user_striker_obj = UserStriker.objects.filter(user_id=instance.id, status=1).first()
        
        user_model_data = UserSerializer(user_obj).data
        gems_model_data = GemsCoinsSerializer(gems_obj).data if gems_obj else {}
        ad_purchase_model_data = AdPurchaseSerializer(ad_purchase_obj).data if ad_purchase_obj else {'is_purchase': False}
        user_striker_model_data = UserStrikerSerializer(user_striker_obj).data if user_striker_obj else {}

        gems_model_data.pop('user', None)
        ad_purchase_model_data.pop('user', None)
        user_striker_model_data = {'striker_index': user_striker_model_data.get('striker_index', None),'purchased_striker':user_striker_model_data.get('purchased_striker', [])}

        merged_data = {**user_model_data, **gems_model_data, **ad_purchase_model_data, **user_striker_model_data}
        return merged_data
    

class UserAccountDataWithTokenSerializer(serializers.Serializer):

    def to_representation(self, instance):
        user_account_data = UserAccountDataSerializer(instance).data
        token_obj = Token.objects.filter(user=instance).first()
        if not token_obj:
            raise serializers.ValidationError('No token found.')

        merged_data = {**user_account_data, 'token': token_obj.key}
        return merged_data

