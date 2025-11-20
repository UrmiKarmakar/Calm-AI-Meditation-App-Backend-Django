from django.contrib import admin
from .models import CustomUser, OTPCode, PasswordResetOTP

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "role", "is_verified", "is_staff", "is_superuser")
    search_fields = ("username", "email", "role")
    list_filter = ("role", "is_verified", "is_staff", "is_superuser")

@admin.register(OTPCode)
class OTPAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "code", "created_at", "expires_at", "is_used")
    search_fields = ("user__username", "code")
    list_filter = ("is_used",)

@admin.register(PasswordResetOTP)
class ResetOTPAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "code", "created_at", "expires_at", "is_used")
    search_fields = ("user__username", "code")
    list_filter = ("is_used",)
