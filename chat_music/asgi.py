import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_music.settings')
django.setup()  # <-- Always call this before importing anything Django-dependent

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import chat.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(chat.routing.websocket_urlpatterns)
    ),
})