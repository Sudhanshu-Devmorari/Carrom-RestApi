from core.models import UserData
from django.contrib.auth.backends import BaseBackend
import requests
import geoip2.database



def get_public_ip_address():
    response = requests.get("https://myexternalip.com/raw")
    return response.text.strip()

def country():
    reader = geoip2.database.Reader("/home/hp/Documents/Carrom-BE/GeoLite2-Country.mmdb")

    ip_address = get_public_ip_address()
    # ip_address = "59.43.33.122"
    try:
        response = reader.country(ip_address)
        country_name = response.country.name
        return country_name
    except geoip2.errors.AddressNotFoundError:
        print(f"ERROR : The IP address {ip_address} is not found in the database")
    finally:
        reader.close()

class GoogleBackend(BaseBackend):
    def authenticate(self, request, **kwargs):
        if 'email' in kwargs:
            try:
                user = UserData.objects.get(email=kwargs['email'])
                user.login_type = 'Google'
                user.country = country() # if necessary, than only use this country otherwise use utils.country
                user.save()
                return user
            except UserData.DoesNotExist:
                return None

    def get_user(self, user_id):
        try:
            return UserData.objects.get(pk=user_id)
        except UserData.DoesNotExist:
            return None
