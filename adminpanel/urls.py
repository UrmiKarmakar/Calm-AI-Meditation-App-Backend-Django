from django.urls import path
from .views import (
    admin_login, admin_forgot_password, admin_verify_reset_otp,
    admin_reset_password, dashboard, list_users, list_admins,
    add_admin, delete_admin, list_backgrounds, add_background, delete_background, list_moods, add_mood,
    delete_mood, list_mood_questions, add_mood_question, delete_mood_question, list_sessions,
)
urlpatterns = [
    path("login", admin_login, name="admin_login"),
    path("forgot-password", admin_forgot_password, name="admin_forgot_password"),
    path("verify-reset-otp", admin_verify_reset_otp, name="admin_verify_reset_otp"),
    path("reset-password", admin_reset_password, name="admin_reset_password"),

    path("dashboard", dashboard, name="dashboard"),
    path("users", list_users, name="list_users"),

    path("admins", list_admins, name="list_admins"),
    path("admins/add", add_admin, name="add_admin"),
    path("admins/<int:admin_id>/delete", delete_admin, name="delete_admin"),

    path("sessions/", list_sessions, name="list_sessions"),

    path("backgrounds", list_backgrounds, name="list_backgrounds"),
    path("backgrounds/add", add_background, name="add_background"),
    path("backgrounds/<int:background_id>/delete", delete_background, name="delete_background"),
    
    path("moods", list_moods, name="list_moods"),
    path("moods/add", add_mood, name="add_mood"),
    path("moods/<int:mood_id>/delete", delete_mood, name="delete_mood"),
    
    path("mood-questions", list_mood_questions, name="list_mood_questions"),
    path("mood-questions/add", add_mood_question, name="add_mood_question"),
    path("mood-questions/<int:question_id>/delete", delete_mood_question, name="delete_mood_question"),
]
