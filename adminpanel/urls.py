from django.urls import path
from .views import (
    admin_login, admin_forgot_password, admin_verify_reset_otp,
    admin_reset_password, dashboard, list_users, list_admins,
    add_admin, delete_admin, backgrounds, moods, mood_questions,
    list_sessions,
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
    path("backgrounds", backgrounds, name="backgrounds"),
    path("moods", moods, name="moods"),
    path("mood-questions", mood_questions, name="mood_questions_admin"),
]
