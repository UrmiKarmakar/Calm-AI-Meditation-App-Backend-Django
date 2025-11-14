from django.db import models
from accounts.models import User

class Mood(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

class MoodQuestion(models.Model):
    mood = models.ForeignKey(Mood, on_delete=models.CASCADE, related_name="questions")
    question = models.CharField(max_length=255)
    options = models.JSONField(default=list)

class MeditationSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    mood = models.CharField(max_length=50)
    answers = models.JSONField(default=dict)
    tokens = models.JSONField(default=list)
    voice = models.CharField(max_length=50, blank=True)
    background = models.CharField(max_length=50, blank=True)
    duration = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
