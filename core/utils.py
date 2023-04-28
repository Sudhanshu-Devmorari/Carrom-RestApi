import requests
import geoip2.database
from core.models import UserData
from channels.db import database_sync_to_async


def get_public_ip_address():
    response = requests.get("https://myexternalip.com/raw")
    return response.text.strip()

def country():
    reader = geoip2.database.Reader("/home/hp/Documents/Carrom-BE/GeoLite2-Country.mmdb")

    ip_address = get_public_ip_address()
    # ip_address = "59.43.33.122"->china  # ip_address = "157.32.225.3"->India
    try:
        response = reader.country(ip_address)
        country_name = response.country.name
        print("--------> ", country_name)
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
    user_obj = UserData.objects.get(username=user)
    user_obj.total_match += 1
    user_obj.save() 
    return True