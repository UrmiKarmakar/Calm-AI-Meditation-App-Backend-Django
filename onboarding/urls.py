# onboarding/urls.py
from django.urls import path
from .views import submit_onboarding, get_profile, activate_subscription

urlpatterns = [
    path("submit", submit_onboarding, name="submit_onboarding"),
    path("profile", get_profile, name="get_profile"),
    path("subscribe", activate_subscription, name="activate_subscription"),
]
