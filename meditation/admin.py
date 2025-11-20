from django.contrib import admin
from .models import Background, Session


@admin.register(Background)
class BackgroundAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "asset_url")
    search_fields = ("name",)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "mood",
        "background",
        "voice",
        "duration_minutes",
        "rating",
        "is_completed",
        "created_at",
    )
    search_fields = ("user__username", "mood", "background", "voice")
    list_filter = ("mood", "is_completed", "rating", "created_at")
    readonly_fields = ("created_at", "duration_minutes", "script", "audio_url")
