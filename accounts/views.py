import json
import datetime
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password, check_password
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

from .models import CustomUser, OTPCode, PasswordResetOTP
from common.jwt_utils import issue_jwt

RESEND_SECONDS = 60


def _json(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return None


def _latest_otp(model, user):
    return model.objects.filter(user=user, is_used=False).order_by("-created_at").first()


def _can_resend(latest):
    if not latest:
        return True
    delta = (now() - latest.created_at).total_seconds()
    return delta >= RESEND_SECONDS


# Auth
@csrf_exempt
def register(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    data = _json(request) or {}
    username = data.get("name") or data.get("username")
    email = data.get("email")
    password = data.get("password")
    confirm = data.get("confirm_password")

    if not all([username, email, password, confirm]):
        return JsonResponse({"error": "Missing fields"}, status=400)
    if password != confirm:
        return JsonResponse({"error": "Passwords do not match"}, status=400)
    if CustomUser.objects.filter(Q(username=username) | Q(email=email)).exists():
        return JsonResponse({"error": "Username or email already exists"}, status=409)

    user = CustomUser.objects.create(
        username=username,
        email=email,
        password=make_password(password),
        role="user",
        is_active=True,
        is_staff=False,
        is_superuser=False,
        is_verified=False,
    )

    latest = _latest_otp(OTPCode, user)
    if not _can_resend(latest):
        remain = RESEND_SECONDS - int((now() - latest.created_at).total_seconds())
        return JsonResponse({"error": "Resend too soon", "retry_in": remain}, status=429)

    code = get_random_string(6, allowed_chars="0123456789")
    OTPCode.objects.create(user=user, code=code, expires_at=now() + datetime.timedelta(minutes=10))
    return JsonResponse({"message": "Registered. Verify OTP.", "otp_preview": code, "resend_after": RESEND_SECONDS}, status=201)


@csrf_exempt
def verify_otp(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    data = _json(request) or {}
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
    user.save()
    return JsonResponse({"message": "Email verified"}, status=200)


@csrf_exempt
def login_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not all([username, email, password]):
        return JsonResponse({"error": "Missing email, username, or password"}, status=400)

    try:
        user = CustomUser.objects.get(username=username, email=email,)
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    if not user.check_password(password):
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    if not user.is_verified:
        return JsonResponse({"error": "Email not verified"}, status=403)

    token = issue_jwt(user)

    return JsonResponse({
        "token": token,
        "id": user.id,
        "role": user.role,
        "username": user.username,
        "email": user.email,
        "avatar_initial": user.username[0].upper()
    }, status=200)

# Password Reset
@csrf_exempt
def forgot_password(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    data = _json(request) or {}
    email = data.get("email")
    if not email:
        return JsonResponse({"error": "Email required"}, status=400)
    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return JsonResponse({"message": "If the email exists, an OTP was sent"}, status=200)

    latest = _latest_otp(PasswordResetOTP, user)
    if not _can_resend(latest):
        remain = RESEND_SECONDS - int((now() - latest.created_at).total_seconds())
        return JsonResponse({"error": "Resend too soon", "retry_in": remain}, status=429)

    code = get_random_string(6, allowed_chars="0123456789")
    PasswordResetOTP.objects.create(user=user, code=code, expires_at=now() + datetime.timedelta(minutes=10))
    return JsonResponse({"message": "Reset OTP sent", "otp_preview": code, "resend_after": RESEND_SECONDS}, status=200)


@csrf_exempt
def verify_reset_otp(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    data = _json(request) or {}
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
    data = _json(request) or {}
    email = data.get("email")
    new_password = data.get("password")
    confirm = data.get("confirm_password")
    if not all([email, new_password, confirm]):
        return JsonResponse({"error": "Missing fields"}, status=400)
    if new_password != confirm:
        return JsonResponse({"error": "Passwords do not match"}, status=400)
    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    user.password = make_password(new_password)
    user.save()
    return JsonResponse({"message": "Password updated"}, status=200)
