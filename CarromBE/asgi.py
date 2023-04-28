import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CarromBE.settings')

import django
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from channels.auth import AuthMiddlewareStack
import core.routing
from channels.security.websocket import AllowedHostsOriginValidator


django_asgi_app = get_asgi_application()


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(core.routing.websocket_urlpatterns))
    ),
})


'''import django
from django.conf import settings
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from core import routing


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CarromBE.settings')

django.setup()


application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})
'''