from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now
from django.conf import settings
import datetime


def default_expiry():
    """
    Return a timestamp 60 seconds from now.
    Used only for OTP codes (registration & password reset).
    """
    return now() + datetime.timedelta(seconds=60)


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ("superadmin", "Super Admin"),
        ("admin", "Admin"),
        ("user", "User"),
    )

    SUBSCRIPTION_CHOICES = (
        ("free", "Free"),
        ("monthly", "Premium (Monthly)"),
        ("annual", "Premium (Annual)"),
    )

    email = models.EmailField(unique=True)  # enforce unique email
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")
    is_verified = models.BooleanField(default=False)  # email verification flag
    avatar_initial = models.CharField(max_length=1, blank=True)
    subscription = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_CHOICES,
        default="free"
    )
    contact_number = models.CharField(max_length=20, blank=True, null=True)

    def save(self, *args, **kwargs):
        # auto-generate avatar initial from username or email
        if not self.avatar_initial:
            source = self.username or self.email or ""
            self.avatar_initial = source[:1].upper() if source else ""
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"

    # convenience role checks
    def is_superadmin(self):
        return self.role == "superadmin"

    def is_admin(self):
        return self.role in ["admin", "superadmin"]

    def is_user(self):
        return self.role == "user"


class OTPCode(models.Model):
    """
    OTP for registration verification.
    Expires in 60 seconds.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="otps"
    )
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expiry)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"OTP for {self.user.email} - {self.code}"

    def is_valid(self):
        return not self.is_used and self.expires_at > now()

    class Meta:
        indexes = [
            models.Index(fields=["user", "code", "is_used"]),
        ]
        verbose_name = "Registration OTP"
        verbose_name_plural = "Registration OTPs"


class PasswordResetOTP(models.Model):
    """
    OTP for password reset (user + admin).
    Expires in 60 seconds.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reset_otps"
    )
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expiry)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Reset OTP for {self.user.email} - {self.code}"

    def is_valid(self):
        return not self.is_used and self.expires_at > now()

    class Meta:
        indexes = [
            models.Index(fields=["user", "code", "is_used"]),
        ]
        verbose_name = "Password Reset OTP"
        verbose_name_plural = "Password Reset OTPs"
