from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async


class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        try:
            query_string = scope["query_string"].decode("utf-8")
            token_key = None
            for param in query_string.split("&"):
                key, value = param.split("=")
                if key == "token":
                    token_key = value
                    break

            if token_key:
                token_user = await get_token_user(token_key)
                scope["user"] = token_user 
            return await self.inner(scope, receive, send)
        except Exception as e:
            print(f"Error in TokenAuthMiddleware: {e}")
            return None


@database_sync_to_async
def get_token_user(token_key):
    try:
        token = Token.objects.filter(key=token_key).last()
        if token and token.user:
            return token.user
        else:
            return AnonymousUser()
    except:
        return None


def TokenAuthMiddlewareStack(inner):
    return TokenAuthMiddleware(AuthMiddlewareStack(inner))
