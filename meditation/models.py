from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Background(models.Model):
    """
    Static background options like forest, ocean, rain, etc.
    Stored for admin management and frontend selection.
    """
    name = models.CharField(max_length=50, unique=True)
    asset_url = models.URLField(blank=True)  # e.g. /static/backgrounds/forest.mp3

    def __str__(self):
        return self.name


class Session(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sessions"
    )
    mood = models.CharField(max_length=50, blank=True)
    selected_answers = models.JSONField(default=dict, blank=True)
    background = models.CharField(max_length=50, blank=True)
    voice = models.CharField(max_length=50, blank=True, help_text="Voice used for meditation narration")
    duration_minutes = models.IntegerField(default=15)
    script = models.TextField(blank=True)
    audio_url = models.CharField(max_length=255, blank=True)  # ✅ safer than URLField
    is_completed = models.BooleanField(default=False)
    rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.id} • {self.mood} • {self.user} • {self.created_at.date()}"