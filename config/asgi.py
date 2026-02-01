"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Инициализируем Django ASGI приложение ДО импорта routing
django_asgi_app = get_asgi_application()

from core.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    # HTTP запросы обрабатываются обычным Django
    "http": django_asgi_app,
    # WebSocket запросы идут через Channels
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})