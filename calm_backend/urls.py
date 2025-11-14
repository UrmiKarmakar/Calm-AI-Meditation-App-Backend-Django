from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django admin
    path("admin/", admin.site.urls),

    # Accounts app (authentication, onboarding, etc.)
    # These will resolve to:
    #   /api/auth/register
    #   /api/auth/verify-otp
    #   /api/auth/login
    path("api/auth/", include("accounts.urls")),

    # Onboarding endpoint
    #   /api/onboarding/submit
    path("api/onboarding/", include("accounts.urls")),

    # Meditation app
    #   /api/meditation/generate
    path("api/meditation/", include("meditation.urls")),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
