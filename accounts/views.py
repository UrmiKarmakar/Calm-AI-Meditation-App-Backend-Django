import json
import datetime
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from .models import CustomUser, OTPCode, PasswordResetOTP
from common.security_utils import issue_jwt

RESEND_SECONDS = 120   # minimum wait before resending OTP
OTP_EXPIRY_SECONDS = 120  # OTP validity duration


# Helpers
def _json(request):
    try:
        body = request.body.decode("utf-8") if request.body else ""
        return json.loads(body) if body else {}
    except json.JSONDecodeError:
        return {}


def _latest_otp(model, user):
    return model.objects.filter(user=user, is_used=False).order_by("-created_at").first()


def _can_resend(latest):
    if not latest:
        return True
    delta = (now() - latest.created_at).total_seconds()
    return delta >= RESEND_SECONDS


def _send_otp_email(email: str, subject: str, code: str):
    # Plain text fallback
    text_content = (
        f"Dear User,\n\n"
        f"Your One-Time Password (OTP) is: {code}\n"
        f"This code will expire in {OTP_EXPIRY_SECONDS // 60} minutes.\n\n"
        f"If you did not request this, please ignore this email.\n\n"
        f"Best regards,\n"
        f"CalmAI Support Team"
    )

    # HTML version for professional look
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <p>Dear User,</p>
            <p>Your <strong>One-Time Password (OTP)</strong> is:</p>
            <h2 style="color:#2c3e50;">{code}</h2>
            <p>This code will expire in <strong>{OTP_EXPIRY_SECONDS // 60} minutes</strong>.</p>
            <p>If you did not request this, please ignore this email.</p>
            <br>
            <p>Best regards,<br>
            <em>CalmAI Support Team</em></p>
        </body>
    </html>
    """

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,  # use configured sender
        to=[email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)


# Registration & Verification
@csrf_exempt
def register(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    data = _json(request)
    username = data.get("name") or data.get("username")
    email = data.get("email")
    password = data.get("password")
    confirm = data.get("confirm password")

    if not all([username, email, password, confirm]):
        return JsonResponse({"error": "Missing fields"}, status=400)
    if password != confirm:
        return JsonResponse({"error": "Passwords do not match"}, status=400)

    # If user exists but not verified → allow resend OTP
    existing = CustomUser.objects.filter(Q(username=username) | Q(email=email)).first()
    if existing:
        if existing.is_verified:
            return JsonResponse({"error": "Username or email already exists"}, status=409)
        else:
            latest = _latest_otp(OTPCode, existing)
            if not _can_resend(latest):
                remain = RESEND_SECONDS - int((now() - latest.created_at).total_seconds())
                return JsonResponse({"error": "Resend too soon", "retry in": remain}, status=429)

            code = get_random_string(6, allowed_chars="0123456789")
            OTPCode.objects.create(user=existing, code=code, expires_at=now() + datetime.timedelta(seconds=OTP_EXPIRY_SECONDS))
            _send_otp_email(email=existing.email, subject="Your CalmAI OTP", code=code)
            return JsonResponse({"message": "OTP resent. Verify to activate account."}, status=200)

    # enforce password validation rules
    try:
        validate_password(password)
    except ValidationError as e:
        return JsonResponse({"error": e.messages}, status=400)

    # Create inactive user
    user = CustomUser.objects.create(
        username=username,
        email=email,
        password=make_password(password),
        role="user",
        is_active=False,   # inactive until verified
        is_staff=False,
        is_superuser=False,
        is_verified=False,
    )

    # Generate OTP
    code = get_random_string(6, allowed_chars="0123456789")
    OTPCode.objects.create(user=user, code=code, expires_at=now() + datetime.timedelta(seconds=OTP_EXPIRY_SECONDS))
    _send_otp_email(email=user.email, subject="Your CalmAI OTP", code=code)

    return JsonResponse({"message": "Registered. Verify OTP.", "resend after": RESEND_SECONDS}, status=201)


@csrf_exempt
def verify_otp(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    data = _json(request)
    email = data.get("email")
    code = data.get("otp") or data.get("code")

    if not email or not code:
        return JsonResponse({"error": "Missing email or code"}, status=400)

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    otp = OTPCode.objects.filter(user=user, code=code, is_used=False).order_by("-created_at").first()
    if not otp:
        return JsonResponse({"error": "Invalid code"}, status=400)
    if otp.expires_at < now():
        return JsonResponse({"error": "Code expired"}, status=400)

    otp.is_used = True
    otp.save()
    user.is_verified = True
    user.is_active = True   # activate after verification
    user.save()

    return JsonResponse({"message": "Email verified. Account activated."}, status=200)


# Login
@csrf_exempt
def login_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    data = _json(request)
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not password or (not username and not email):
        return JsonResponse({"error": "Missing credentials"}, status=400)

    try:
        if username:
            user = CustomUser.objects.get(username=username)
        else:
            user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    if not user.check_password(password):
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    if not user.is_verified or not user.is_active:
        return JsonResponse({"error": "Email not verified"}, status=403)

    token = issue_jwt(user)

    return JsonResponse({
        "token": token,
        "id": user.id,
        "role": user.role,
        "username": user.username,
        "email": user.email,
        "avatar initial": (user.username or user.email)[0].upper()
    }, status=200)


# Password Reset
@csrf_exempt
def forgot_password(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    data = _json(request)
    email = data.get("email")
    if not email:
        return JsonResponse({"error": "Email required"}, status=400)

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        # Soft success to avoid user enumeration
        return JsonResponse({"message": "If the email exists, an OTP was sent"}, status=200)

    latest = _latest_otp(PasswordResetOTP, user)
    if not _can_resend(latest):
        remain = RESEND_SECONDS - int((now() - latest.created_at).total_seconds())
        return JsonResponse({"error": "Resend too soon", "retry_in": remain}, status=429)

    code = get_random_string(6, allowed_chars="0123456789")
    PasswordResetOTP.objects.create(user=user, code=code, expires_at=now() + datetime.timedelta(seconds=OTP_EXPIRY_SECONDS))
    _send_otp_email(email=user.email, subject="Your CalmAI Reset OTP", code=code)

    return JsonResponse({"message": "Reset OTP sent", "resend_after": RESEND_SECONDS}, status=200)


@csrf_exempt
def verify_reset_otp(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    data = _json(request)
    email = data.get("email")
    code = data.get("otp") or data.get("code")

    if not email or not code:
        return JsonResponse({"error": "Missing email or code"}, status=400)

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    otp = PasswordResetOTP.objects.filter(user=user, code=code, is_used=False).order_by("-created_at").first()
    if not otp:
        return JsonResponse({"error": "Invalid code"}, status=400)
    if otp.expires_at < now():
        return JsonResponse({"error": "Code expired"}, status=400)

    otp.is_used = True
    otp.save()
    return JsonResponse({"message": "OTP verified. You can reset password now."}, status=200)

@csrf_exempt
def reset_password(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    data = _json(request)
    email = data.get("email")
    new_password = data.get("password")
    confirm = data.get("confirm password")

    if not all([email, new_password, confirm]):
        return JsonResponse({"error": "Missing fields"}, status=400)
    if new_password != confirm:
        return JsonResponse({"error": "Passwords do not match"}, status=400)

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    # Enforce password validation rules (pass user for similarity validator)
    try:
        validate_password(new_password, user=user)
    except ValidationError as e:
        return JsonResponse({"error": e.messages}, status=400)

    user.password = make_password(new_password)
    user.save()
    return JsonResponse({"message": "Password updated"}, status=200)
