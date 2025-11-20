# onboarding/models.py
from django.db import models
from accounts.models import CustomUser

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    mindfulness_goal = models.CharField(max_length=100, blank=True, null=True)   # Q1
    experience_level = models.CharField(max_length=100, blank=True, null=True)   # Q2
    meditation_time = models.CharField(max_length=100, blank=True, null=True)    # Q3
    voice_preference = models.CharField(max_length=100, blank=True, null=True)   # Q4
    stress_level = models.CharField(max_length=50, blank=True, null=True)        # Q5

    onboarding_complete = models.BooleanField(default=False)
    subscription_active = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile of {self.user.username}"
