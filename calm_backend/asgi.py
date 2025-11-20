"""
ASGI config for calm_backend project.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env before Django settings
load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "calm_backend.settings")

from django.core.asgi import get_asgi_application

application = get_asgi_application()
