import requests
import geoip2.database

# models
from core.models import UserData, Match, MatchUser
from channels.db import database_sync_to_async
from django.db.models import F

# rest_framework
from rest_framework.response import Response
from rest_framework import status


def get_public_ip_address():
    response = requests.get("https://myexternalip.com/raw")
    return response.text.strip()


def country():
    reader = geoip2.database.Reader("GeoLite2-Country.mmdb")

    ip_address = get_public_ip_address()
    try:
        response = reader.country(ip_address)
        country_name = response.country.name
        return country_name
    except geoip2.errors.AddressNotFoundError:
        print(f"ERROR : The IP address {ip_address} is not found in the database")
    finally:
        reader.close()


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
    

@database_sync_to_async
def total_match(user):
    UserData.objects.filter(username=user).update(total_match=F('total_match') + 1)
    return True


@database_sync_to_async
def get_match_data(code):
    return Match.objects.filter(code=code, status=1).first()
    

@database_sync_to_async
def is_match_exists_with_code(code):
    return Match.objects.filter(code=code, status=1).exists()


@database_sync_to_async
def create_match(code, user_id):
    return Match.objects.create(code=code, created_by_id=user_id)


@database_sync_to_async
def create_match_user(match, user_id):
    obj, created =MatchUser.objects.get_or_create(match=match, user_id=user_id, status=1)
    return created


@database_sync_to_async
def update_match_user_status(match, user_id):
    MatchUser.objects.filter(match=match, user_id=user_id).update(status=0) 
    if not MatchUser.objects.filter(match=match, status=1).exists():
        Match.objects.filter(id=match.id).update(status=0)
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