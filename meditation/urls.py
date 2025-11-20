from django.urls import path
from .views import (
    list_moods, mood_questions, generate_session,
    history, rate_session, get_stats
)

app_name = "meditation"

urlpatterns = [
    path("moods/", list_moods, name="list_moods"),
    path("questions/", mood_questions, name="mood_questions"),
    path("generate/", generate_session, name="generate_session"),
    path("history/", history, name="history"),
    path("rate/", rate_session, name="rate_session"),
    path("stats/", get_stats, name="get_stats"),
]
