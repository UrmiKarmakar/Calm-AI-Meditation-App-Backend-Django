from django.urls import path
from .views import (
    register,
    verify_otp,
    login_view,
    forgot_password,
    verify_reset_otp,
    reset_password,
)

urlpatterns = [
    path("register", register, name="register"),
    path("verify-otp", verify_otp, name="verify_otp"),
    path("login", login_view, name="login"),
    path("forgot-password", forgot_password, name="forgot_password"),
    path("verify-reset-otp", verify_reset_otp, name="verify_reset_otp"),
    path("reset-password", reset_password, name="reset_password"),
]
