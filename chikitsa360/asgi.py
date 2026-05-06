"""
ASGI config for chikitsa360.

Order of operations matters here. Channels' AuthMiddlewareStack and any
consumer that touches Django models requires the app registry to be ready.
That means we MUST:
  1. Set DJANGO_SETTINGS_MODULE
  2. Call get_asgi_application() (initializes Django's app registry)
  3. Only THEN import routing / consumer code
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chikitsa360.settings')

from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()

# Imports below must come AFTER get_asgi_application(), since chat consumers
# pull in models (User, Appointment, etc.) which need apps to be loaded.
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat_app.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat_app.routing.websocket_urlpatterns
        )
    ),
})
