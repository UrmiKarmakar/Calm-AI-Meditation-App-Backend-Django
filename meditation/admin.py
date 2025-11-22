from django.contrib import admin
from .models import Background, Session, Mood, MoodQuestion


@admin.register(Background)
class BackgroundAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "audio_file", "created_at")
    search_fields = ("name",)
    list_filter = ("created_at",)


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


@admin.register(Mood)
class MoodAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    list_filter = ("created_at",)


@admin.register(MoodQuestion)
class MoodQuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "mood", "question", "created_at")
    search_fields = ("question", "mood__name")
    list_filter = ("mood", "created_at")
