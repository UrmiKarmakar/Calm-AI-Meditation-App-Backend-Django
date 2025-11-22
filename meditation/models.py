from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Session(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sessions"
    )
    mood = models.CharField(max_length=50, blank=True)
    selected_answers = models.JSONField(default=dict, blank=True)
    background = models.CharField(max_length=100, blank=True)
    voice = models.CharField(
        max_length=10,
        choices=[("male", "Male"), ("female", "Female")],
        help_text="Voice used for meditation narration"
    )
    duration_minutes = models.PositiveIntegerField(default=15)
    script = models.TextField(blank=True)
    audio_url = models.CharField(max_length=255, blank=True)
    is_completed = models.BooleanField(default=False)
    rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Session {self.id} • {self.mood} • {self.user} • {self.created_at.date()}"


class Mood(models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Background(models.Model):
    name = models.CharField(max_length=100, unique=True)
    audio_file = models.FileField(upload_to="backgrounds/", blank=True, null=True)  # ✅ allow empty
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name



class MoodQuestion(models.Model):
    mood = models.ForeignKey(Mood, on_delete=models.CASCADE, related_name="questions")
    question = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["mood", "created_at"]

    def __str__(self):
        return f"{self.mood.name}: {self.question[:30]}"
