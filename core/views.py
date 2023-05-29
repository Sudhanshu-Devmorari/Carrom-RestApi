from django.contrib.auth import login, logout
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q

# From app
from core.utils import country, create_response, handle_exceptions
from core.custom_authentication import CsrfExemptSessionAuthentication,CustomFacebookOAuth2Adapter
from core.serializers import UserSerializer, GemsCoinsSerializer, FriendsSerializer, GiftSentSerializer, RequestGiftSerializer

# From rest_framework 
from rest_framework.authentication import BasicAuthentication 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

# From all auth
from allauth.socialaccount.models import SocialAccount

# Models
from core.models import UserData, UserCount, GemsCoins, Friends, GiftSent, Leaderboard, RequestGift, FRIEND_CHOISE


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
        
        # Create user object
        user = UserData(
            login_role = 'guest',
            username = f'Guest_{count:09d}',
            user_id = f'Guest_{count:09d}',
            country = country_name
        )
        user.save()

        # Assign coins and gems to user
        gemcoin = GemsCoins(user=user, coins=5000, gems=20)
        gemcoin.save()

        # Increment user count
        guest_number.guest = guest_number.guest + 1
        guest_number.save()
        
        user_dict = {
            'login_role': user.login_role,
            'username': user.username,
            'user_id': user.user_id,
            'country': user.country
        }

        login(request, user)
        return Response(user_dict, status=status.HTTP_200_OK)


# @method_decorator(csrf_exempt, name='dispatch')
class ProfileView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
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
        
        serializer = UserSerializer(user)
        data = serializer.data
        return Response(data=data, status=status.HTTP_200_OK)

    """
    update the authenticated user's username data.
    """
    @handle_exceptions
    def post(self, request, format=None, *args, **kwargs):
        data = {}
        if request.data.get('username'):
            # Validate uniqueness of username
            AlredayExist = UserData.objects.filter(~Q(id=request.user.id), username=request.data.get('username')).exists()
            if AlredayExist:
                return Response(create_response(status.HTTP_409_CONFLICT,"A user with this name already exists. Please try another name.", data=data), status=status.HTTP_409_CONFLICT)

            # Update username
            user = UserData.objects.get(username=request.user.username)
            user.username = request.data.get('username')
            user.save()

            serializer = UserSerializer(user)
            data = serializer.data
            return Response(create_response(status.HTTP_200_OK,"Username sucessfully updated.", data=data),status=status.HTTP_200_OK)
        else:
            return Response(create_response(status.HTTP_404_NOT_FOUND,"Username not found."),status=status.HTTP_404_NOT_FOUND)


class GemsCoinsView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
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
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = [IsAuthenticated]

    """
    Search the guest user with user-id if user exist
    """
    @handle_exceptions
    def get(self, request, format=None, *args, **kwargs):
        data = {}

        # Validate user_id
        user = UserData.objects.filter(user_id=request.query_params.get('user_id')).first()
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
        receiver = UserData.objects.filter(username=request.data.get('receiver')).first()
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
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
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
                choice_list = [i for i,j in FRIEND_CHOISE]
                if request.data.get('status') not in choice_list:
                    return Response(create_response(status.HTTP_404_NOT_FOUND,"Invalid Status."), status=status.HTTP_404_NOT_FOUND)

                user = Friends.objects.filter(sender__username=request.data.get('user'), receiver=request.user).first()
                if user:
                    user.friend_status = request.data.get('status')
                    user.save()
                    serializer = FriendsSerializer(user)
                    data = serializer.data
                    return Response(data=data, status=status.HTTP_200_OK)
                else:
                    return Response(create_response(status.HTTP_404_NOT_FOUND,f"Friend request with {request.data.get('user')} not found."), status=status.HTTP_404_NOT_FOUND)
            else:
                return Response(create_response(status.HTTP_404_NOT_FOUND,"There is no user available. Please provide one."), status=status.HTTP_404_NOT_FOUND)
        
        # Sent gift list for user
        elif request.data.get('coin'):
            if request.data.get('coin-sender'):
                gift = GiftSent.objects.get(coin_sender__username=request.data.get('coin-sender'), coin_receiver=request.user)
                gift.flag = True
                gift.save()
                user = GemsCoins.objects.get(user=request.user)
                user.coins = user.coins + int(request.data.get('coin'))
                user.save()
                serializer = GemsCoinsSerializer(user)
                data = serializer.data
                return Response(data=data, status=status.HTTP_200_OK)
            else:
                return Response(create_response(status.HTTP_404_NOT_FOUND,"Coin-Sender not found."), status=status.HTTP_404_NOT_FOUND)
        
        # Send request for gift
        elif request.data.get('request-sender'):
            req_gift = RequestGift.objects.filter(request_sender__username=request.data.get('request-sender'), request_receiver=request.user).first()
            
            if not req_gift:
                return Response(create_response(status.HTTP_404_NOT_FOUND,f"Request gift data from {request.data.get('request-sender')} not found."), status=status.HTTP_404_NOT_FOUND)

            req_gift.flag = True
            req_gift.save()
            sender_obj = UserData.objects.get(username=request.data.get('request-sender'))
            giftsent_obj = GiftSent.objects.create(coin_sender=request.user, coin_receiver=sender_obj, coin=150)
            serializer = GiftSentSerializer(giftsent_obj)
            data = serializer.data
            return Response(data=data, status=status.HTTP_200_OK)
        else:
            return Response(create_response(status.HTTP_404_NOT_FOUND,"There is no status available. Please provide one."), status=status.HTTP_404_NOT_FOUND)


class GiftSentView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    """
    Retrieve the friend list of a user whose friend status is Accept.
    """
    def get(self, request, format=None, *args, **kwargs):
        # print('-----', request.user)
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
    def post(self, request, format=None, *args, **kwargs):
        # print('----', request.user)
        if request.data.get('coin'):
            if request.data.get('coin_receiver'):
                if UserData.objects.filter(username=request.data.get('coin_receiver')).exists():
                    user = UserData.objects.get(username=request.data.get('coin_receiver'))
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
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
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
    """
    API use for retrieve the user's friends list for the Friends Leaderboard.
    """
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
    """
    API use for retrieve the user's list country wise for the Country Leaderboard.
    """
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
    def get(self, request, format=None, *args, **kwargs):
        # print("***", request.user,"***")
        friends = []
        if request.user.login_role == 'facebook' and SocialAccount.objects.filter(user=request.user).exists():
            user = SocialAccount.objects.get(user=request.user)
            # print("---------GET user---------",user.extra_data['friends']['data'][0]['id'])
            # ur = SocialAccount.objects.get(uid=user.extra_data['friends']['data'][0]['id'])

            for i in range(len(user.extra_data['friends']['data'])):
                friends.append(user.extra_data['friends']['data'][i]['name'])
      
        return Response(data=dict(enumerate(friends)), status=status.HTTP_200_OK)

class RemoveFriends(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    """
    Retrive the Friends List.
    """
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
            user = SocialAccount.objects.get(user=request.user)
            for i in range(len(user.extra_data['friends']['data'])):
                user = UserData.objects.get(first_name=user.extra_data['friends']['data'][i]['name'])
                all_users.append(user.username)

        return Response(data=dict(enumerate(all_users)), status=status.HTTP_200_OK)

    """
    Remove friend from Friends List.
    """
    def post(self, request, format=None, *args, **kwargs):
        # print("***", request.user,"***")
        if request.data.get("username"):
            user_obj = UserData.objects.get(username=request.data.get("username"))
            if Friends.objects.filter(sender=user_obj, receiver=request.user, friend_status='accept').exists():
                instance = Friends.objects.filter(sender=user_obj, receiver=request.user, friend_status='accept')
                instance.delete()
            if Friends.objects.filter(sender=request.user, receiver=user_obj, friend_status='accept').exists():
                instances = Friends.objects.filter(sender=request.user, receiver=user_obj, friend_status='accept')
                instances.delete()
            return Response(create_response(status.HTTP_200_OK, f"{request.data.get('username')} sucessfully removed from your friends list."), status=status.HTTP_200_OK)
        else:
            return Response(create_response(status.HTTP_404_NOT_FOUND,"There is no username available. Please provide one."), status=status.HTTP_404_NOT_FOUND)


class LeaderboardWiningView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    """
    Create or Get the user and add the winning coins in weekly coins field.
    """
    def post(self, request, format=None, *args, **kwargs):
        if request.data.get('winner'):
            if request.data.get('coins'):
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
    def get(self, request, format=None, *args, **kwargs):
        # print("***", request.user,"***")
        logout(request)
        return Response(create_response(status.HTTP_200_OK, "User successfully logged Out..."), status=status.HTTP_200_OK)


# For update the user star level:
class UpdateStarLevelView(APIView):
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
