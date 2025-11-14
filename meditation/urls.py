from django.urls import path
from .views import generate_session

urlpatterns = [
    path("generate/", generate_session, name="generate-session"),
]
