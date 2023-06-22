import requests
import geoip2.database
from django.contrib.auth.hashers import make_password

# models
from core.models import UserData, Match, MatchUser, MatchCity, GemsCoins
from channels.db import database_sync_to_async
from django.db.models import F, Sum
from django.db.models import Q

# rest_framework
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token

# From all auth
from allauth.socialaccount.models import SocialAccount
from social_core.exceptions import AuthTokenError

# Global variables
PlayWithFriendEntryFee = 5000
PlayWithFriendWinningPrize = 10000


def get_public_ip_address():
    response = requests.get("https://myexternalip.com/raw")
    return response.text.strip()


def country():
    country_name = "India"
    return country_name
    # reader = geoip2.database.Reader("GeoLite2-Country.mmdb")

    # ip_address = get_public_ip_address()
    # try:
    #     response = reader.country(ip_address)
    #     country_name = response.country.name
    #     return country_name
    # except geoip2.errors.AddressNotFoundError:
    #     print(f"ERROR : The IP address {ip_address} is not found in the database")
    # finally:
    #     reader.close()


def create_response(stts,msg,data=None):
    if stts != 200:
        response = {
            "status":"error",
            "data":{},
            "message":msg
        }
        return response
    if stts == 200:
        response = {
            "status":"success",
            "data":data if data else {},
            "message":msg
        }
        return response


def validate_facebook_token(access_token):
    try:
        token_verification = {'is_token_verified': False, 'user_obj': None}
        
        # Facebook graph API calls
        response = requests.get('https://graph.facebook.com/v13.0/me?fields=id,name,email,picture,first_name,friends', params={'access_token': access_token})
        
        # Get data
        if response.status_code != 200:
            return token_verification

        data = response.json()
        social_account_obj = SocialAccount.objects.filter(provider='facebook', uid=data.get('id')).first()
        if not social_account_obj:
            count = 0
            username = data.get('name', 'Facebook')

            # Validation to check unique username 
            while True:
                user_name = f'{username}_{count:09d}' if count else username
                already_exist = UserData.objects.filter(username=user_name).exists()
                if already_exist:
                    count += 1
                else:
                    break

            # Manully generate password
            password = f'{user_name}@{count:04d}'
            encrypted_password = generate_password(password)

            # Userdata entry
            user_obj = UserData.objects.create(
                profile_url = data['picture']['data']['url'] if data['picture']['data']['url'] else "",
                username = user_name,
                email = data.get('email', ""),
                first_name = data['name'],
                password = encrypted_password
            )

            # Generate token for user authentication
            generate_auth_token(user_obj)

            social_account_obj = SocialAccount.objects.create(user=user_obj, provider='facebook', uid=data.get('id'), extra_data=data)
        
        token_verification['is_token_verified'] = True
        token_verification['user_obj'] = social_account_obj.user
        return token_verification

    except AuthTokenError as e:
        raise e

    except Exception as e:
        raise AuthTokenError(e)


@database_sync_to_async
def create_match_user(dynamic_params):
    obj, created = MatchUser.objects.get_or_create(**dynamic_params)
    return created


@database_sync_to_async
def update_match_user_status(match, user_id):
    MatchUser.objects.filter(match=match, user_id=user_id).update(status=2)
    if not MatchUser.objects.filter(match=match, status=1).exists():
        Match.objects.filter(id=match.id).update(status=0)
    return True


@database_sync_to_async
def get_match_city(city_index):
    return MatchCity.objects.filter(index=city_index).first()


@database_sync_to_async
def user_has_enough_coin(user_id, entry_fee):
    return GemsCoins.objects.filter(user_id=user_id, coins__gte=entry_fee).exists()


@database_sync_to_async
def get_pending_city_match(city_id):
    return MatchUser.objects.filter(city_id=city_id, status=0).first()


@database_sync_to_async
def total_match(user):
    UserData.objects.filter(username=user).update(total_match=F('total_match') + 1)
    return True


@database_sync_to_async
def create_match(dynamic_params):
    return Match.objects.create(**dynamic_params)


@database_sync_to_async
def get_match_data(dynamic_params):
    return Match.objects.filter(**dynamic_params).first()


@database_sync_to_async
def is_match_exists_with_code(code, match_type):
    return Match.objects.filter(code=code, status=1, match_type=match_type).exists()


@database_sync_to_async
def get_match_id_list(match_id):
    return list(MatchUser.objects.filter(match_id=match_id).values_list('id', flat=True))


@database_sync_to_async
def get_current_player_data(match_id):
    match_data = MatchUser.objects.filter(match_id=match_id, user_turn=True).values('id','match_id','match__code','match__status',
                                                                       'user_id','user__user_id','user__username',
                                                                       'status','score').first()
    return match_data


@database_sync_to_async
def get_next_player_data(current_player_id, match_id):
    match_data = MatchUser.objects.filter(~Q(id=current_player_id), match_id=match_id).values('id','match_id','match__code','match__status',
                                                                       'user_id','user__user_id','user__username',
                                                                       'status','score').first()
    return match_data


@database_sync_to_async
def get_total_score(match_id):
    score_data = MatchUser.objects.filter(match_id=match_id).aggregate(total_score=Sum('score'))
    return score_data['total_score']


@database_sync_to_async
def update_player_score(match_user_id, score):
    MatchUser.objects.filter(id=match_user_id).update(score=F('score') + score)
    return True


@database_sync_to_async
def update_match_user(params_to_filter, params_to_update):
    MatchUser.objects.filter(**params_to_filter).update(**params_to_update)
    return True


@database_sync_to_async
def update_match(params_to_filter, params_to_update):
    Match.objects.filter(**params_to_filter).update(**params_to_update)
    return True


@database_sync_to_async
def assign_winning_prize(user_ids, prize_coin):
    GemsCoins.objects.filter(user_id__in=user_ids).update(coins=F('coins') + prize_coin)
    return True


@database_sync_to_async
def update_score_based_on_penlty(match_user_id, foul_penlty_w, foul_penlty_b, cookie_data_list):
    match_user_obj = MatchUser.objects.filter(id=match_user_id).only('score').first()

    if match_user_obj.score >= foul_penlty_w:
        match_user_obj.score -= foul_penlty_w
        cookie_data_list.append({'c':'W', 'x':0 , 'y':0, 'z':0})

    elif match_user_obj.score >= foul_penlty_b:
        match_user_obj.score -= foul_penlty_b
        cookie_data_list.append({'c':'B', 'x':0 , 'y':0, 'z':0})

    else:
        match_user_obj.skip_turn = True

    match_user_obj.save(update_fields=['score','skip_turn'])
    return cookie_data_list


@database_sync_to_async
def get_game_over_status(match_id):
    players_data = MatchUser.objects.filter(match_id=match_id).values('id','match__match_type','user_id', 'user__user_id','user__username' , 'city__prize', 'score')
    user_ids = list(map(lambda d: d['user_id'], players_data))

    if players_data[0]['score'] != players_data[1]['score']:
        status = 'winner'
        winner = max(players_data, key=lambda d: d['score'])
    else:
        status = 'tie'
        winner = False
    
    winning_prize = 0
    if players_data[0]['city__prize']:
        winning_prize = players_data[0]['city__prize']
    
    elif players_data[0]['match__match_type'] == 1:
        winning_prize = PlayWithFriendWinningPrize

    return {'status': status, 'winner': winner, 'user_ids':user_ids, 'winning_prize': winning_prize}


@database_sync_to_async
def is_skip_next_turn(id, match_id):
    obj = MatchUser.objects.filter(~Q(id=id), match_id=match_id).only('skip_turn').first()
    return obj.skip_turn


@database_sync_to_async
def update_skip_turn_of_player(id, match_id):
    MatchUser.objects.filter(~Q(id=id), match_id=match_id).update(skip_turn=False)
    return True


@database_sync_to_async
def charge_entry_fee(match_user_obj):
    entry_fee = 0
    playre_ids = MatchUser.objects.filter(match_id=match_user_obj.match_id).values_list('user_id', flat=True)
    if match_user_obj.match.match_type == 1:
        entry_fee = PlayWithFriendEntryFee
    
    elif match_user_obj.city:
        entry_fee = match_user_obj.city.entry_fee

    GemsCoins.objects.filter(user_id__in=playre_ids).update(coins=F('coins') - entry_fee)
    return True


def handle_exceptions(view_func):
    def wrapped_view(*args, **kwargs):
        try:
            return view_func(*args, **kwargs)
        except Exception as e:
            response = {
                "status": "error",
                "message": "Something went wrong..!"
            }
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return wrapped_view


def generate_password(password):
    encrypted_password = make_password(password)
    return encrypted_password


def generate_auth_token(user_obj, created=True):
    if created:
        Token.objects.create(user=user_obj)
    else:
        old_token = Token.objects.filter(user=user_obj).last()
        if old_token:
            old_token.delete()
        Token.objects.create(user=user_obj)