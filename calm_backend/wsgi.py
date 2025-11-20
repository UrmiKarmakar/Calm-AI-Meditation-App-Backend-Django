"""
WSGI config for calm_backend project.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env before Django settings
load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "calm_backend.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
