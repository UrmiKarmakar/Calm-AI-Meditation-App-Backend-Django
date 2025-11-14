from django.urls import path
from . import views

urlpatterns = [
    path("register", views.register),
    path("verify-otp", views.verify_otp),
    path("login", views.login_view),
    path("submit", views.submit_onboarding),
]
