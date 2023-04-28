"""
for override the csrf protection
"""
from rest_framework.authentication import SessionAuthentication, BasicAuthentication 

class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return
    

"""
for customize the behavior of the Facebook login process
"""
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.models import SocialAccount

class CustomFacebookOAuth2Adapter(FacebookOAuth2Adapter):
    def get_friends(self, access_token):
        client = self.get_client(None)
        url = 'https://graph.facebook.com/me/friends?access_token={}'.format(access_token)
        friends_data = client.get(url).json()
        friends = [friend['id'] for friend in friends_data['data']]
        return SocialAccount.objects.filter(uid__in=friends)
