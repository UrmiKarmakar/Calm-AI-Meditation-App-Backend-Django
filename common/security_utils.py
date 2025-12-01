import jwt
import datetime
from django.conf import settings
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from django.core.mail import send_mail


# JWT Utilities (for login sessions)

def issue_jwt(user):
    """
    Issue a JWT token for a user.
    Token stays valid until exp time (default: settings.JWT_EXP_MINUTES).
    """
    exp = timezone.now() + datetime.timedelta(minutes=settings.JWT_EXP_MINUTES)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "exp": exp,
        "iat": timezone.now(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGO)


def decode_jwt(token: str):
    """
    Decode a JWT token.
    Raises jwt.ExpiredSignatureError if expired.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGO])


# OTP Utilities (for registration & password reset)

def generate_6_digit_otp():
    """Generate a random 6-digit numeric OTP."""
    return get_random_string(6, allowed_chars="0123456789")


def send_otp_email(user, code, subject="Your CalmAI OTP Code"):
    """
    Send OTP email to the user.
    """
    message = (
        f"Hello {user.username or user.email},\n\n"
        f"Your OTP code is {code}. It expires in 60 seconds.\n\n"
        f"If you did not request this, please ignore."
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def create_and_email_otp(user, model_cls, subject):
    """
    Create OTP entry in DB and send it via email.
    """
    code = generate_6_digit_otp()
    otp = model_cls.objects.create(
        user=user,
        code=code,
        expires_at=now() + datetime.timedelta(seconds=60)  # 60s expiry
    )
    send_otp_email(user, code, subject=subject)
    return otp
