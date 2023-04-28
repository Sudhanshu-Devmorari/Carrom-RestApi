from core.models import Leaderboard

def transfercoin():
    leader_obj = Leaderboard.objects.all()
    for user in leader_obj:
        user.lastweek_coins = user.weekly_coins
        user.weekly_coins = 0
        user.save()
    return True