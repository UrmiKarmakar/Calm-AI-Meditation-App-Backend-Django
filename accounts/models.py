from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ("superadmin", "Super Admin"),
        ("admin", "Admin"),
        ("user", "User"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")
    is_verified = models.BooleanField(default=False)

class OTPCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=100, blank=True)
    avatar_initial = models.CharField(max_length=1, blank=True)
    onboarding_completed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        source = self.display_name or self.user.first_name or self.user.username or "U"
        self.avatar_initial = source.strip()[:1].upper()
        super().save(*args, **kwargs)
