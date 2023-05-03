
"""
Using signals auto generate the country and user-id for new user
"""
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.utils import country
from allauth.socialaccount.models import SocialAccount
from core.models import UserData, UserCount, GemsCoins


@receiver(post_save, sender=SocialAccount)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        user_obj = UserData.objects.get(id=instance.user.id)
        social_user_obj = SocialAccount.objects.get(user=user_obj)
        if not user_obj.user_id:
            if social_user_obj.provider == 'google':
                f_name = social_user_obj.extra_data['given_name']
                google_number = UserCount.objects.get(id=1)
                count = google_number.google
                # user_obj.login_role = 'google'
                user_obj.login_role = social_user_obj.provider
                user_obj.country = country()
                user_obj.user_id = f'{f_name[:10]}_{count:05d}'
                user_obj.profile_url = social_user_obj.extra_data['picture']
                user_obj.save()
                gemcoin = GemsCoins(user=user_obj, coins=5000, gems=20)
                gemcoin.save()
                google_number.google = count + 1
                google_number.save()
            else:
                f_name = social_user_obj.extra_data['first_name']
                fb_number = UserCount.objects.get(id=1)
                count = fb_number.facebook
                # user.login_role = 'facebook'
                user_obj.login_role = social_user_obj.provider
                user_obj.country = country()
                user_obj.user_id = f'{f_name[:10]}_{count:05d}'
                user_obj.profile_url = social_user_obj.extra_data['picture']['data']['url']
                user_obj.save()
                gemcoin = GemsCoins(user=user_obj, coins=5000, gems=120)
                gemcoin.save()
                fb_number.facebook = count + 1
                fb_number.save()