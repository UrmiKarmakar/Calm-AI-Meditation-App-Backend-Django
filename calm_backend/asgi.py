"""
ASGI config for calm_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from dotenv import load_dotenv  

# Load environment variables from .env
load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'calm_backend.settings')

from django.core.asgi import get_asgi_application
application = get_asgi_application()
