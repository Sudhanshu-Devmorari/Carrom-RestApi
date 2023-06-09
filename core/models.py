from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator
# Create your models here.

class UserData(AbstractUser):
    login_role = models.CharField(max_length=50, null=True, blank=True)
    username = models.CharField(unique=True, max_length=50, null=True, blank=True, validators=[MinLengthValidator(2)])
    password = models.CharField(null=True, blank=True)
    # email = models.EmailField(unique=True, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    first_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=30, null=True, blank=True)
    user_id = models.CharField(unique=True, max_length=16, null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)
    star_level = models.IntegerField(default=1, null=True, blank=True)
    total_wining = models.IntegerField(null=True, blank=True)
    profile_pic = models.CharField(default=0)
    profile_url = models.CharField(max_length=500, null=True, blank=True)
    total_match = models.IntegerField(default=0, null=True, blank=True)
    total_win_match = models.IntegerField(default=0,null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s"%(self.username)


class GemsCoins(models.Model):
    user = models.ForeignKey(UserData, on_delete=models.CASCADE)
    coins = models.IntegerField(null=True, blank=True)
    gems = models.IntegerField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # def __str__(self):
    #     return "%s"%(self.user.username)

class Leaderboard(models.Model):
    user = models.ForeignKey(UserData, on_delete=models.CASCADE)
    weekly_coins = models.IntegerField(null=True, blank=True)
    lastweek_coins = models.IntegerField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


FRIEND_CHOISE = (
    ('accept','Approve'),
    ('reject','Reject'),
    ('pending','Pending'),
)
class Friends(models.Model):
    sender = models.ForeignKey(UserData, on_delete=models.CASCADE, related_name='sender')
    receiver = models.ForeignKey(UserData, on_delete=models.CASCADE, related_name='receiver')
    friend_status = models.CharField(max_length=20, choices = FRIEND_CHOISE)



class GiftSent(models.Model):
    coin_sender = models.ForeignKey(UserData, on_delete=models.CASCADE, related_name='coin_sender')
    coin_receiver = models.ForeignKey(UserData, on_delete=models.CASCADE, related_name='coin_receiver')
    coin = models.IntegerField()
    flag = models.BooleanField(default=False)


class RequestGift(models.Model):
    request_sender = models.ForeignKey(UserData, on_delete=models.CASCADE, related_name='request_sender')
    request_receiver = models.ForeignKey(UserData, on_delete=models.CASCADE, related_name='request_receiver')
    flag = models.BooleanField(default=False)


class UserCount(models.Model):
    guest = models.IntegerField(null=True, blank=True, default=0)
    facebook = models.IntegerField(null=True, blank=True, default=0)
    google = models.IntegerField(null=True, blank=True, default=0)


class Match(models.Model):
    TYPE_CHOICES = (
        (0, 'Online Match'),
        (1, 'Play With Friends'),
    )

    code = models.CharField(max_length=50)
    match_type = models.IntegerField(default=None, blank=True, null=True, choices=TYPE_CHOICES) 
    status = models.IntegerField(default=1) # 1: active,0: deactivate
    created_by = models.ForeignKey(UserData, on_delete=models.CASCADE, related_name='match_created_by')
    start_time = models.DateTimeField(default=None, blank=True, null=True)
    end_time = models.DateTimeField(default=None, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)


class MatchCity(models.Model):
    city = models.CharField(max_length=100)
    entry_fee = models.IntegerField(default=0)
    prize = models.IntegerField(default=0)
    index = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)  


class MatchUser(models.Model):
    STATUS_CHOICES = (
        (0, 'Pending'),
        (1, 'Running'),
        (2, 'Closed'),
    )

    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    user = models.ForeignKey(UserData, on_delete=models.CASCADE, related_name='match_user')
    status = models.IntegerField(default=0, choices=STATUS_CHOICES) 
    city = models.ForeignKey(MatchCity, on_delete=models.CASCADE, default=None, blank=True, null=True)
    user_turn = models.BooleanField(default=False)
    skip_turn = models.BooleanField(default=False)
    score = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)  


class Striker(models.Model):
    index = models.IntegerField(default=0)
    status = models.IntegerField(default=1) # 1: active,0: deactivate
    prize = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class UserStriker(models.Model): 
    user = models.ForeignKey(UserData, on_delete=models.CASCADE, related_name='user_striker')
    striker = models.ForeignKey(Striker, on_delete=models.CASCADE)
    status = models.IntegerField(default=0) # 1: active,0: deactivate
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class AdPurchase(models.Model):
    user = models.ForeignKey(UserData, on_delete=models.CASCADE, related_name='ad_purchase_user')
    is_purchase = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
