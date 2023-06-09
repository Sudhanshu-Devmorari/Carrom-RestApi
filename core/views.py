from django.contrib.auth import login, logout
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q

# From app
from core.utils import country, create_response, handle_exceptions, validate_facebook_token, generate_password, generate_auth_token
from core.serializers import (UserSerializer, GemsCoinsSerializer, FriendsSerializer, GiftSentSerializer, RequestGiftSerializer,
                              UserStrikerSerializer, AdPurchaseSerializer, UserAccountDataSerializer, UserAccountDataWithTokenSerializer)

# From rest_framework 
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

# From all auth
from allauth.socialaccount.models import SocialAccount

# Models
from core.models import (UserData, UserCount, GemsCoins, Friends, GiftSent, Leaderboard, RequestGift,
                         FRIEND_CHOISE, Striker, UserStriker, AdPurchase)


DEFAULT_STRIKER = 0

class GuestLoginView(APIView):

    @handle_exceptions
    def get(self, request, format=None, *args, **kwargs):
        guest_number = UserCount.objects.get(id=1)
        count = guest_number.guest
        country_name = country()

        # Validation to check unique username and userid
        while True:
            already_exist = UserData.objects.filter(Q(username=f'Guest_{count:09d}') | Q(user_id=f'Guest_{count:09d}')).exists()
            if already_exist:
                count += 1
            else:
                break

        # Manully generate password
        password = f'Guest_{count:09d}@{count:04d}'
        encrypted_password = generate_password(password)

        # Create user object
        user = UserData(
            login_role = 'guest',
            username = f'Guest_{count:09d}',
            user_id = f'Guest_{count:09d}',
            country = country_name,
            password = encrypted_password
        )
        user.save()
        
        # Generate token for user authentication
        generate_auth_token(user)

        # Assign coins and gems to user
        gemcoin = GemsCoins(user=user, coins=5000, gems=120)
        gemcoin.save()

        # Validate if striker entry exists if not than make new one
        striker_obj = Striker.objects.filter(index=DEFAULT_STRIKER, status=1).first()
        if not striker_obj:
            striker_obj, created = Striker.objects.update_or_create(index=DEFAULT_STRIKER, defaults={'status':1})
        
        # Assign default striker to user
        UserStriker.objects.create(user=user ,striker=striker_obj, status=1)

        # Increment user count
        guest_number.guest = guest_number.guest + 1
        guest_number.save()
        
        serializer = UserAccountDataWithTokenSerializer(user)
        user_dict = serializer.data

        login(request, user)
        return Response(user_dict, status=status.HTTP_200_OK)


# @method_decorator(csrf_exempt, name='dispatch')
class ProfileView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    """
    get the authenticated user profile data.
    """
    @handle_exceptions
    def get(self, request, format=None, *args, **kwargs):
        data = {}
        
        username = request.query_params.get('username') if request.query_params.get('username') else request.user.username
        user = UserData.objects.filter(username=username).first() 
        if not user:
            return Response(create_response(status.HTTP_404_NOT_FOUND,"User not found."), status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserAccountDataSerializer(user)
        data = serializer.data
        return Response(data=data, status=status.HTTP_200_OK)

    """
    update the authenticated user's username data.
    """
    @handle_exceptions
    def post(self, request, format=None, *args, **kwargs):
        data = {}
        if not request.data.get('username') and request.data.get('profile_pic_index') in ['', None]:
            return Response(create_response(status.HTTP_404_NOT_FOUND, "Data not found to update."), status=status.HTTP_404_NOT_FOUND)

        user = UserData.objects.get(id=request.user.id)
        
        # Update username
        if request.data.get('username'):
            # Validate uniqueness of username
            AlredayExist = UserData.objects.filter(~Q(id=request.user.id), username=request.data.get('username')).exists()
            if AlredayExist:
                return Response(create_response(status.HTTP_409_CONFLICT,"A user with this name already exists. Please try another name.", data=data), status=status.HTTP_409_CONFLICT)

            # Update username
            user.username = request.data.get('username')
            user.save(update_fields=['username'])

            # Generate token for user authentication
            generate_auth_token(user, created=False)

        # Update profile pic
        if request.data.get('profile_pic_index') not in ['', None]:
            user.profile_pic = request.data.get('profile_pic_index')
            user.save(update_fields=['profile_pic'])

        serializer = UserAccountDataWithTokenSerializer(user)
        data = serializer.data
        return Response(create_response(status.HTTP_200_OK,"Profile sucessfully updated.", data=data),status=status.HTTP_200_OK)


class GemsCoinsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @handle_exceptions
    def get(self, request, format=None, *args, **kwargs):
        data = {}
        user = GemsCoins.objects.get(user=request.user)
        serializer = GemsCoinsSerializer(user)
        data = serializer.data
        return Response(data=data, status=status.HTTP_200_OK)

    @handle_exceptions
    def post(self, request, format=None, *args, **kwargs):
        user = GemsCoins.objects.get(user=request.user)
        if (request.data.get('operation')).lower() == 'add':
            if request.data.get('coin'):
                user.coins = user.coins + int(request.data.get('coin'))
                user.save()
            if request.data.get('gem'):
                user.gems = user.gems + int(request.data.get('gem'))
                user.save()
            
            serializer = GemsCoinsSerializer(user)
            data = serializer.data
            return Response(data=data, status=status.HTTP_200_OK)

        if (request.data.get('operation')).lower() == 'sub':
            if request.data.get('coin'):
                user.coins = user.coins - int(request.data.get('coin'))
                if user.coins >= 0:
                    user.save()
                    serializer = GemsCoinsSerializer(user)
                    data = serializer.data
                    return Response(data=data, status=status.HTTP_200_OK)
                else:
                    return Response(create_response(status.HTTP_404_NOT_FOUND,"Not enough Coins?"),status=status.HTTP_404_NOT_FOUND)
            if request.data.get('gem'):
                user.gems = user.gems - int(request.data.get('gem'))
                if user.gems >= 0:
                    user.save()
                    serializer = GemsCoinsSerializer(user)
                    data = serializer.data
                    return Response(data=data, status=status.HTTP_200_OK)
                else:
                    return Response(create_response(status.HTTP_404_NOT_FOUND,"Not enough Gems?"),status=status.HTTP_404_NOT_FOUND)


class GuestFriendSearchView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    """
    Search the guest user with user-name if user exist
    """
    @handle_exceptions
    def get(self, request, format=None, *args, **kwargs):
        data = {}

        # Validate username
        username = request.query_params.get('username').strip() if request.query_params.get('username') else None
        user = UserData.objects.filter(username=username).first()
        if not user:
            return Response(create_response(status.HTTP_404_NOT_FOUND,"User not found."), status=status.HTTP_404_NOT_FOUND)
        
        # Return user data
        serializer = UserSerializer(user)
        data = serializer.data
        return Response(data=data, status=status.HTTP_200_OK)

    """
    Send the request to user who found previously.
    """
    @handle_exceptions
    def post(self, request, format=None, *args, **kwargs):
        print("------sender-",request.data.get('sender'),'--------receiver-', request.data.get('receiver'))
        '''serializer = FriendsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)'''
        data = {}

        # Validate receiver
        receiver_username = request.data.get('receiver').strip() if request.data.get('receiver') else None
        receiver = UserData.objects.filter(username=receiver_username).first()
        if not receiver:
            return Response(create_response(status.HTTP_404_NOT_FOUND,"receiver not found."), status=status.HTTP_404_NOT_FOUND)

        # Validate if already requested to this receiver
        AlreadyRequested = Friends.objects.filter(sender=request.user, receiver=receiver, friend_status='pending').exists()
        if AlreadyRequested:
            return Response(create_response(status.HTTP_409_CONFLICT,f"You already have pending request with {receiver.username}"), status=status.HTTP_409_CONFLICT)

        # Make friend request
        req = Friends(sender=request.user, receiver=receiver, friend_status='pending') 
        req.save()

        # Return friend request data
        serializer = FriendsSerializer(req)
        data = serializer.data
        return Response(data=data, status=status.HTTP_200_OK)


class GuestFriendView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    """
    Friend Request Retrive: Retrieve the friend list of a user with a pending friend status. And also retrive gift list for user.
    And also retrive the user list who request for gift.
    """
    @handle_exceptions
    def get(self, request, format=None, *args, **kwargs):
        data = {}
        friend_requests = []
        if Friends.objects.filter(receiver=request.user, friend_status='pending').exists():
            users = Friends.objects.filter(receiver=request.user, friend_status='pending')
            for user in users:
                friend_requests.append(user.sender.username)
            data['friend_request'] = friend_requests

        store = []
        if GiftSent.objects.filter(coin_receiver=request.user, flag=False).exists():
            user = GiftSent.objects.filter(coin_receiver=request.user, flag=False)
            for ur in user:
                detail = {
                    'username':ur.coin_sender.username,
                    'coin':ur.coin
                }
                store.append(detail)
            data['coin_gift'] = store

        gift_requests = []
        if RequestGift.objects.filter(request_receiver=request.user, flag=False).exists():
            user_obj = RequestGift.objects.filter(request_receiver=request.user, flag=False)
            for user in user_obj:
                gift_requests.append(user.request_sender.username)
            data['gift_requests'] = gift_requests

        return Response(data=data, status=status.HTTP_200_OK)
    
    """
    Accepting or Rejecting friend requests or gifts for authenticated users.
    """
    @handle_exceptions
    def post(self, request, format=None, *args, **kwargs):
        # accept/reject request
        if request.data.get('status'):
            if request.data.get('user'):
                request_status = request.data.get('status').strip() if request.data.get('status') else None
                request_sender = request.data.get('user').strip() if request.data.get('user') else None

                choice_list = [i for i,j in FRIEND_CHOISE]
                if request_status not in choice_list:
                    return Response(create_response(status.HTTP_404_NOT_FOUND,"Invalid Status."), status=status.HTTP_404_NOT_FOUND)

                user = Friends.objects.filter(sender__username=request_sender, receiver=request.user).first()
                if user:
                    user.friend_status = request_status
                    user.save()
                    serializer = FriendsSerializer(user)
                    data = serializer.data
                    return Response(data=data, status=status.HTTP_200_OK)
                else:
                    return Response(create_response(status.HTTP_404_NOT_FOUND,f"Friend request with {request_sender} not found."), status=status.HTTP_404_NOT_FOUND)
            else:
                return Response(create_response(status.HTTP_404_NOT_FOUND,"There is no user available. Please provide one."), status=status.HTTP_404_NOT_FOUND)
        
        # Sent gift list for user
        elif request.data.get('coin'):
            coin_sender = request.data.get('coin-sender').strip() if request.data.get('coin-sender') else None
            sender_coin = int(request.data.get('coin'))
            
            if coin_sender:
                gift = GiftSent.objects.filter(coin_sender__username=coin_sender, coin_receiver=request.user).first()
                if not gift:
                    return Response(create_response(status.HTTP_404_NOT_FOUND,f"{coin_sender} cannot send any coin."), status=status.HTTP_404_NOT_FOUND)

                # Is login user has enough coin to send
                user_has_coin = GemsCoins.objects.filter(user_id=gift.coin_sender.id, coins__gte=sender_coin).exists()
                if not user_has_coin:
                    return Response(create_response(status.HTTP_404_NOT_FOUND,f"{gift.coin_sender.username} cannot have enough coin to gift"), status=status.HTTP_404_NOT_FOUND)
                
                gift.flag = True
                gift.save()

                # Update receiver coins
                user = GemsCoins.objects.get(user=request.user)
                user.coins = user.coins + sender_coin
                user.save()

                # Deduct coin from sender user
                coin_sender_obj = GemsCoins.objects.get(user_id=gift.coin_sender.id)
                coin_sender_obj.coins = coin_sender_obj.coins - sender_coin
                coin_sender_obj.save()

                serializer = GemsCoinsSerializer(user)
                data = serializer.data
                return Response(data=data, status=status.HTTP_200_OK)
            else:
                return Response(create_response(status.HTTP_404_NOT_FOUND,"Coin-Sender not found."), status=status.HTTP_404_NOT_FOUND)
        
        # Send request for gift
        elif request.data.get('request-sender'):
            gift_request_sender = request.data.get('request-sender').strip() if request.data.get('request-sender') else None
            gift_coin = 150
            
            # Update status that receiver accepted request_gift request
            req_gift = RequestGift.objects.filter(request_sender__username=gift_request_sender, request_receiver=request.user).first()
            if not req_gift:
                return Response(create_response(status.HTTP_404_NOT_FOUND,f"Request gift data from {gift_request_sender} not found."), status=status.HTTP_404_NOT_FOUND)

            req_gift.flag = True
            req_gift.save()

            # Send gift to receiver by login user
            sender_obj = UserData.objects.get(username=gift_request_sender)
            giftsent_obj = GiftSent.objects.create(coin_sender=request.user, coin_receiver=sender_obj, coin=gift_coin)
            
            serializer = GiftSentSerializer(giftsent_obj)
            data = serializer.data
            return Response(data=data, status=status.HTTP_200_OK)
        else:
            return Response(create_response(status.HTTP_404_NOT_FOUND,"There is no status available. Please provide one."), status=status.HTTP_404_NOT_FOUND)


class GiftSentView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    """
    Retrieve the friend list of a user whose friend status is Accept.
    """
    @handle_exceptions
    def get(self, request, format=None, *args, **kwargs):
        all_users = []
        if Friends.objects.filter(sender=request.user, friend_status='accept').exists():
            users = Friends.objects.filter(sender=request.user, friend_status='accept')
            for user in users:
                all_users.append(user.receiver.username)
        if Friends.objects.filter(receiver=request.user, friend_status='accept').exists():
            users = Friends.objects.filter(receiver=request.user, friend_status='accept')
            for user in users:
                all_users.append(user.sender.username)
        """
        if user login role is facebook.
        """
        if request.user.login_role == 'facebook' and SocialAccount.objects.filter(user=request.user).exists():
            user = SocialAccount.objects.get(user=request.user)
            if 'friends' in user.extra_data:
                for i in range(len(user.extra_data['friends']['data'])):
                    friend_id = user.extra_data['friends']['data'][i]['id']
                    ur = SocialAccount.objects.filter(uid=friend_id).first()
                    if ur: all_users.append(ur.user.username) 
        data = {}
        data['user'] = all_users
        return Response(data=data, status=status.HTTP_200_OK) 
    
    """
    Send the coins to your friends as gifts.
    """
    @handle_exceptions
    def post(self, request, format=None, *args, **kwargs):
        # print('----', request.user)
        if request.data.get('coin'):
            if request.data.get('coin_receiver'):
                user = UserData.objects.filter(username=request.data.get('coin_receiver')).first()
                if user:
                    gift = GiftSent(coin=request.data.get('coin'), coin_sender=request.user, coin_receiver=user)
                    gift.save()
                    serializer = GiftSentSerializer(gift)
                    data = serializer.data
                    return Response(data=data, status=status.HTTP_200_OK)
                else:
                    return Response(create_response(status.HTTP_404_NOT_FOUND,"Provide valid coin_receiver."), status=status.HTTP_404_NOT_FOUND)
            else:
                return Response(create_response(status.HTTP_404_NOT_FOUND,"There is no coin-receiver available. Please provide one."), status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(create_response(status.HTTP_404_NOT_FOUND,"There is no coins available. Please provide one."), status=status.HTTP_404_NOT_FOUND)


class RequestGiftView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @handle_exceptions
    def post(self, request, formate=None, *args, **kwargs):
        print("------------", request.user)
        if request.data.get('request-receiver'):
            if UserData.objects.filter(username=request.data.get('request-receiver')).exists():
                req_user = UserData.objects.get(username=request.data.get('request-receiver'))
                req_gift = RequestGift.objects.create(request_sender=request.user, request_receiver=req_user)
                serializer = RequestGiftSerializer(req_gift)
                data = serializer.data
                return Response(data=data, status=status.HTTP_200_OK)
            else:
                return Response(create_response(status.HTTP_404_NOT_FOUND,"Provide valid request_receiver."), status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(create_response(status.HTTP_404_NOT_FOUND,"There is no request_receiver available. Please provide one."), status=status.HTTP_404_NOT_FOUND)


class LeaguesLeaderboardView(APIView):
    """
    For the Leagues Leaderboard, created the API that retrieves the users as per star level.
    """
    @handle_exceptions
    def get(self, request, format=None, *args, **kwargs):
        # print("***", request.user,"-------",request.user.star_level)
            star_level = request.user.star_level
            a = {
                "1,9":[x for x in range(1,10)],
                "10,14":[x for x in range(10,15)],
                "15,19":[x for x in range(15,20)],
                "20,24":[x for x in range(20,25)],
                "25,34":[x for x in range(25,35)],
                "35,44":[x for x in range(35,45)],
                "45,54":[x for x in range(45,55)],
                "55,74":[x for x in range(55,15)],
                "75,99":[x for x in range(75,100)],
                "100,150":[x for x in range(100,151)],
            }
            for key in a:
                if a[key].count(star_level) > 0:
                    # print(int(key.split(',')[0]),int(key.split(',')[-1]),star_level)
                    if not request.query_params.get('key'):
                        users = Leaderboard.objects.filter(user__star_level__range=(int(key.split(',')[0]), int(key.split(',')[-1]))).order_by('-weekly_coins')
                        data = []
                        for user in users:
                                detail = {
                                    'username':user.user.username,
                                    'coins':user.weekly_coins
                                }
                                data.append(detail)
                        return Response(data=dict(enumerate(data)), status=status.HTTP_200_OK)
                    else:
                        users = Leaderboard.objects.filter(user__star_level__range=(int(key.split(',')[0]), int(key.split(',')[-1]))).order_by('-lastweek_coins')
                        data = []
                        for user in users:
                                detail = {
                                    'username':user.user.username,
                                    'coins':user.lastweek_coins
                                }
                                data.append(detail)
                        return Response(data=dict(enumerate(data)), status=status.HTTP_200_OK)


class FriendsLeaderboardView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    """
    API use for retrieve the user's friends list for the Friends Leaderboard.
    """
    @handle_exceptions
    def get(self, request, format=None, *args, **kwargs):
        all_users = []
        if Friends.objects.filter(sender=request.user, friend_status='accept').exists():
            users = Friends.objects.filter(sender=request.user, friend_status='accept')
            for user in users:
                all_users.append(user.receiver.username)
        if Friends.objects.filter(receiver=request.user, friend_status='accept').exists():
            users = Friends.objects.filter(receiver=request.user, friend_status='accept')
            for user in users:
                all_users.append(user.sender.username)

        if request.user.login_role == 'facebook' and SocialAccount.objects.filter(user=request.user).exists():
            user = SocialAccount.objects.get(user=request.user)
            if 'friends' in user.extra_data:
                for i in range(len(user.extra_data['friends']['data'])):
                    friend_user = UserData.objects.filter(first_name=user.extra_data['friends']['data'][i]['name']).first()
                    if friend_user: all_users.append(friend_user.username)

        data = []
        if not request.query_params.get('key'):
            """
            Depending on current week coins.
            """
            for users in all_users:
                coin_obj = Leaderboard.objects.filter(user__username=users).first()
                
                if coin_obj:
                    detail = {
                            'username':coin_obj.user.username,
                            'coins':coin_obj.weekly_coins
                        }
                    data.append(detail)

            # sort the data by coins in descending order
            data = sorted(data, key=lambda k: k['coins'], reverse=True)

            return Response(data=dict(enumerate(data)), status=status.HTTP_200_OK)
        else:
            """
            Depending on last week coins
            """
            for users in all_users:
                coin_obj = Leaderboard.objects.filter(user__username=users).first()
                
                if coin_obj:
                    detail = {
                            'username':coin_obj.user.username,
                            'coins':coin_obj.lastweek_coins
                        }
                    data.append(detail)

            # sort the data by coins in descending order
            data = sorted(data, key=lambda k: k['coins'], reverse=True)

            return Response(data=dict(enumerate(data)), status=status.HTTP_200_OK)


class CountryLeaderboardView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    """
    API use for retrieve the user's list country wise for the Country Leaderboard.
    """
    @handle_exceptions
    def get(self, request, format=None, *args, **kwargs):
        # print("***", request.user,"***", request.user.country)
        data = []
        if not request.query_params.get('key'):
            coin_obj = Leaderboard.objects.filter(user__country=request.user.country).order_by('-weekly_coins')
            for user in coin_obj:
                detail = {
                    'username':user.user.username,
                    'coins':user.weekly_coins
                }
                data.append(detail)
            return Response(data=dict(enumerate(data)), status=status.HTTP_200_OK)
        else:
            coin_obj = Leaderboard.objects.filter(user__country=request.user.country).order_by('-lastweek_coins')
            for user in coin_obj:
                detail = {
                    'username':user.user.username,
                    'coins':user.lastweek_coins
                }
                data.append(detail)
            return Response(data=dict(enumerate(data)), status=status.HTTP_200_OK)


class WorldLeaderboardView(APIView):
    """
    API use for retrieve users lists for the World Leaderboard.
    """
    @handle_exceptions
    def get(self, request, format=None, *args, **kwargs):
        # print("***", request.user,"***")
        data = []
        if not request.query_params.get('key'):
            coin_obj = Leaderboard.objects.all().order_by('-weekly_coins')
            for user in coin_obj:
                detail = {
                    'username':user.user.username,
                    'coins':user.weekly_coins
                }
                data.append(detail)
            return Response(data=dict(enumerate(data)), status=status.HTTP_200_OK)
        else:
            coin_obj = Leaderboard.objects.all().order_by('-lastweek_coins')
            for user in coin_obj:
                detail = {
                    'username':user.user.username,
                    'coins':user.lastweek_coins
                }
                data.append(detail)
            return Response(data=dict(enumerate(data)), status=status.HTTP_200_OK)


class FaceBookFriendListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @handle_exceptions
    def get(self, request, format=None, *args, **kwargs):
        # print("***", request.user,"***")
        friends = []
        if request.user.login_role == 'facebook' and SocialAccount.objects.filter(user=request.user).exists():
            user = SocialAccount.objects.get(user=request.user)
            # print("---------GET user---------",user.extra_data['friends']['data'][0]['id'])
            # ur = SocialAccount.objects.get(uid=user.extra_data['friends']['data'][0]['id'])
            if 'friends' in user.extra_data:
                for i in range(len(user.extra_data['friends']['data'])):
                    friends.append(user.extra_data['friends']['data'][i]['name'])
      
        return Response(data=dict(enumerate(friends)), status=status.HTTP_200_OK)

class RemoveFriends(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    """
    Retrive the Friends List.
    """
    @handle_exceptions
    def get(self, request, format=None, *args, **kwargs):
        # print("***", request.user,"-------")
        all_users = []
        if Friends.objects.filter(sender=request.user, friend_status='accept').exists():
            users = Friends.objects.filter(sender=request.user, friend_status='accept')
            for user in users:
                all_users.append(user.receiver.username)
        if Friends.objects.filter(receiver=request.user, friend_status='accept').exists():
            users = Friends.objects.filter(receiver=request.user, friend_status='accept')
            for user in users:
                all_users.append(user.sender.username)

        if request.user.login_role == 'facebook' and SocialAccount.objects.filter(user=request.user).exists():
            social_user = SocialAccount.objects.get(user=request.user)
            if 'friends' in social_user.extra_data:
                for i in range(len(social_user.extra_data['friends']['data'])):
                    user = UserData.objects.filter(first_name=social_user.extra_data['friends']['data'][i]['name']).first()
                    if user: all_users.append(user.username)

        return Response(data=dict(enumerate(all_users)), status=status.HTTP_200_OK)

    """
    Remove friend from Friends List.
    """
    @handle_exceptions
    def post(self, request, format=None, *args, **kwargs):
        # print("***", request.user,"***")
        user_obj = UserData.objects.filter(username=request.data.get("username")).first()
        if user_obj:
            if Friends.objects.filter(sender=user_obj, receiver=request.user, friend_status='accept').exists():
                instance = Friends.objects.filter(sender=user_obj, receiver=request.user, friend_status='accept')
                instance.delete()
            if Friends.objects.filter(sender=request.user, receiver=user_obj, friend_status='accept').exists():
                instances = Friends.objects.filter(sender=request.user, receiver=user_obj, friend_status='accept')
                instances.delete()
            return Response(create_response(status.HTTP_200_OK, f"{request.data.get('username')} sucessfully removed from your friends list."), status=status.HTTP_200_OK)
        else:
            return Response(create_response(status.HTTP_404_NOT_FOUND,f"{request.data.get('username')} user not found."), status=status.HTTP_404_NOT_FOUND)


class LeaderboardWiningView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    """
    Create or Get the user and add the winning coins in weekly coins field.
    """
    @handle_exceptions
    def post(self, request, format=None, *args, **kwargs):
        if request.data.get('winner'):
            if int(request.data.get('coins')):
                if UserData.objects.filter(username=request.data.get('winner')).exists():
                    
                    user_obj = UserData.objects.get(username=request.data.get('winner'))
                    user_obj.total_win_match += 1
                    user_obj.save()
                    
                    if Leaderboard.objects.filter(user=user_obj).exists():
                        win_obj = Leaderboard.objects.get(user=user_obj)
                        win_obj.weekly_coins += int(request.data.get('coins'))
                        win_obj.save()
                        return Response(create_response(status.HTTP_200_OK, "The coin has been successfully added to the user's weekly_coins."), status=status.HTTP_200_OK)
                    else:
                        win_obj = Leaderboard.objects.create(user=user_obj, weekly_coins=request.data.get('coins'))
                        return Response(create_response(status.HTTP_200_OK, "The user has successfully been added to the Leaderboard with weekly coins."), status=status.HTTP_200_OK)
                else:
                    return Response(create_response(status.HTTP_404_NOT_FOUND,"There is no User available with this username."), status=status.HTTP_404_NOT_FOUND)
            else:
                return Response(create_response(status.HTTP_404_NOT_FOUND,"There is no coin available. Please provide one."), status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(create_response(status.HTTP_404_NOT_FOUND,"There is no winner username available. Please provide one."), status=status.HTTP_404_NOT_FOUND)        


class GuestLogout(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @handle_exceptions
    def get(self, request, format=None, *args, **kwargs):
        # print("***", request.user,"***")
        request.user.auth_token.delete()
        logout(request)
        return Response(create_response(status.HTTP_200_OK, "User successfully logged Out..."), status=status.HTTP_200_OK)


# For update the user star level:
class UpdateStarLevelView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @handle_exceptions
    def get(self, request, format=None, *args, **kwargs):
        # print("***", request.user,"***")
        user_obj = UserData.objects.get(username=request.user.username)
        user_obj.star_level += 1
        user_obj.save()
        return Response(create_response(status.HTTP_200_OK, ""), status=status.HTTP_200_OK)


class CheckView(APIView):
    def get(self, request):
        # print("-------",request.user)
        return Response(request.user.username,status=status.HTTP_200_OK)


class StrikerView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    """
    Retrieve striker data of user.
    """
    @handle_exceptions
    def get(self, request, format=None, *args, **kwargs):
        data = {}
        username = request.query_params.get('username').strip() if request.query_params.get('username') else request.user.username

        # validate user
        user = UserData.objects.filter(username=username).first() 
        if not user:
            return Response(create_response(status.HTTP_404_NOT_FOUND,"User not found."), status=status.HTTP_404_NOT_FOUND)
        
        # striker data
        striker_obj = UserStriker.objects.filter(user=user, status=1).first()
        serializer = UserStrikerSerializer(striker_obj)
        data = serializer.data
        return Response(data=data, status=status.HTTP_200_OK)

    """
    Make entry for striker selected by user.
    """
    @handle_exceptions
    def post(self, request, format=None, *args, **kwargs):
        # get data
        username = request.data.get('username').strip() if request.data.get('username') else request.user.username
        striker_index = request.data.get('striker_index').split(',') if request.data.get('striker_index') else []

        # validate data
        user = UserData.objects.filter(username=username).first() 
        striker_index = Striker.objects.filter(index__in=striker_index, status=1).values_list('index', flat=True)
        if not all([user, striker_index]):
            return Response(create_response(status.HTTP_404_NOT_FOUND,"Data not found."), status=status.HTTP_404_NOT_FOUND)
        
        # Make striker entry for user
        striker_ids = Striker.objects.filter(index__in=striker_index, status=1).values_list('id', flat=True)
        for striker_id in striker_ids:
            user_striker_obj, created = UserStriker.objects.get_or_create(user=user, striker_id=striker_id)

        # Return response
        return Response(create_response(status.HTTP_200_OK,"Striker added successfully."),status=status.HTTP_200_OK)

        
class AdPurchaseView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    """
    Get ad purchase data of user.
    """
    @handle_exceptions
    def get(self, request, format=None, *args, **kwargs):
        data = {}
        username = request.query_params.get('username').strip() if request.query_params.get('username') else request.user.username

        # Validate user
        user = UserData.objects.filter(username=username).first() 
        if not user:
            return Response(create_response(status.HTTP_404_NOT_FOUND,"User not found."), status=status.HTTP_404_NOT_FOUND)
        
        # Does user puchase any ad
        ad_purchase_obj = AdPurchase.objects.filter(user=user).first()
        if not ad_purchase_obj:
            serializer = UserSerializer(user)
            data = {**serializer.data}
            data.update({'is_purchase': False})
            return Response(data=data, status=status.HTTP_200_OK)

        # Return user's ad purchase data
        serializer = AdPurchaseSerializer(ad_purchase_obj)
        data = serializer.data
        return Response(data=data, status=status.HTTP_200_OK)
        
    
    @handle_exceptions
    def post(self, request, format=None, *args, **kwargs):
        username = request.data.get('username').strip() if request.data.get('username') else request.user.username

        # validate user
        user = UserData.objects.filter(username=username).first() 
        if not user:
            return Response(create_response(status.HTTP_404_NOT_FOUND,"User not found."), status=status.HTTP_404_NOT_FOUND)
        
        # Make entry in ad purchase for user
        AdPurchase.objects.get_or_create(user=user, is_purchase=True)

        # Return response
        return Response(create_response(status.HTTP_200_OK,"Ad purchase successfully."),status=status.HTTP_200_OK)
    

class FacebookLoginView(APIView):

    def get(self, request, format=None, *args, **kwargs):
        access_token = request.GET.get('access_token', None)

        if not access_token:
            return Response(create_response(status.HTTP_404_NOT_FOUND, "Access token not found."), status=status.HTTP_404_NOT_FOUND)

        try:
            response = validate_facebook_token(access_token)
            if response['is_token_verified']:
                serializer = UserAccountDataWithTokenSerializer(response['user_obj'])
                data = serializer.data
                
                login(request, response['user_obj'])
                return Response(data=data, status=status.HTTP_200_OK)
            else:
                return Response(create_response(status.HTTP_404_NOT_FOUND, "Access token not verified."), status=status.HTTP_404_NOT_FOUND)
        except:
            return Response(create_response(status.HTTP_400_BAD_REQUEST, "Token verification failed"), status=status.HTTP_400_BAD_REQUEST)