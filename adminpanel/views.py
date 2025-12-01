import json
import datetime
from django.http import JsonResponse
from django.utils.timezone import now
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.paginator import Paginator
from meditation.mood_questions import get_questions
from accounts.models import CustomUser, PasswordResetOTP
from meditation.models import Session, Mood, Background, MoodQuestion
from common.security_utils import issue_jwt
from common.decorators import auth_required, role_required

RESEND_SECONDS = 120   # minimum wait before resending OTP
OTP_EXPIRY_SECONDS = 120  # OTP validity duration in seconds


# Helpers
def _json(request):
    """Safely parse JSON body from request."""
    try:
        body = request.body.decode("utf-8") if request.body else ""
        return json.loads(body) if body else {}
    except json.JSONDecodeError:
        return {}


def _latest_otp(model, user):
    """Get the latest unused OTP for a user."""
    return model.objects.filter(user=user, is_used=False).order_by("-created_at").first()


def _can_resend(latest):
    """Check if enough time has passed to resend OTP."""
    if not latest:
        return True
    delta = (now() - latest.created_at).total_seconds()
    return delta >= RESEND_SECONDS


def _send_otp_email(email: str, subject: str, code: str):
    """Send OTP email to admin/superadmin."""
    send_mail(
        subject=subject,
        message=f"Your OTP is {code}. It will expire in {OTP_EXPIRY_SECONDS // 60} minutes.",
        from_email="urmikarmakar16@gmail.com",
        recipient_list=[email],
        fail_silently=False,
    )


# Admin Authentication
@csrf_exempt
def admin_login(request):
    """Admin/superadmin login with email or username."""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    data = _json(request)
    identifier = data.get("email") or data.get("username")
    password = data.get("password")

    if not identifier or not password:
        return JsonResponse({"error": "Missing credentials"}, status=400)

    try:
        if "@" in identifier:
            user = CustomUser.objects.get(email=identifier)
        else:
            user = CustomUser.objects.get(username=identifier)
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    if user.role not in ["admin", "superadmin"]:
        return JsonResponse({"error": "Forbidden"}, status=403)

    if not check_password(password, user.password):
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    token = issue_jwt(user)
    return JsonResponse({
        "token": token,
        "role": user.role,
        "username": user.username,
        "email": user.email
    }, status=200)


# Admin Password Reset
@csrf_exempt
def admin_forgot_password(request):
    """Send OTP for admin/superadmin password reset."""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    data = _json(request)
    email = data.get("email")
    if not email:
        return JsonResponse({"error": "Email required"}, status=400)

    try:
        user = CustomUser.objects.get(email=email, role__in=["admin", "superadmin"])
    except CustomUser.DoesNotExist:
        # Soft success to avoid user enumeration
        return JsonResponse({"message": "If the email exists, an OTP was sent"}, status=200)

    latest = _latest_otp(PasswordResetOTP, user)
    if not _can_resend(latest):
        remain = RESEND_SECONDS - int((now() - latest.created_at).total_seconds())
        return JsonResponse({"error": "Resend too soon", "retry_in": remain}, status=429)

    code = get_random_string(6, allowed_chars="0123456789")
    PasswordResetOTP.objects.create(
        user=user,
        code=code,
        expires_at=now() + datetime.timedelta(seconds=OTP_EXPIRY_SECONDS)
    )
    _send_otp_email(email=user.email, subject="Admin Reset OTP", code=code)

    return JsonResponse({"message": "Reset OTP sent", "resend_after": RESEND_SECONDS}, status=200)


@csrf_exempt
def admin_verify_reset_otp(request):
    """Verify OTP for admin/superadmin password reset."""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    data = _json(request)
    email = data.get("email")
    code = data.get("otp")

    if not email or not code:
        return JsonResponse({"error": "Missing email or code"}, status=400)

    try:
        user = CustomUser.objects.get(email=email, role__in=["admin", "superadmin"])
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
def admin_reset_password(request):
    """Reset password for admin/superadmin after OTP verification."""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    data = _json(request)
    email = data.get("email")
    pw = data.get("new_password")
    cpw = data.get("confirm_password")

    if not all([email, pw, cpw]):
        return JsonResponse({"error": "Missing fields"}, status=400)
    if pw != cpw:
        return JsonResponse({"error": "Passwords do not match"}, status=400)

    try:
        user = CustomUser.objects.get(email=email, role__in=["admin", "superadmin"])
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    try:
        validate_password(pw, user=user)
    except ValidationError as e:
        return JsonResponse({"error": e.messages}, status=400)

    user.password = make_password(pw)
    user.save()
    return JsonResponse({"message": "Password updated"}, status=200)

# Dashboard
@auth_required
@role_required(["admin", "superadmin"])
def dashboard(request):
    today = timezone.now().date()

    total_users = CustomUser.objects.filter(role="user").count()
    new_users_today = CustomUser.objects.filter(role="user", date_joined__date=today).count()
    positive_reviews = Session.objects.filter(rating__gte=4).count()  # assuming rating field exists

    return JsonResponse({
        "total_users": total_users,
        "new_users_today": new_users_today,
        "positive_reviews": positive_reviews
    })


# User Management
@auth_required
@role_required(["admin", "superadmin"])
def list_users(request):
    page_number = int(request.GET.get("page", 1))
    users = CustomUser.objects.filter(role="user").order_by("id")

    paginator = Paginator(users, 10)
    page = paginator.get_page(page_number)

    def format_subscription(user):
        if user.subscription == "monthly":
            return "Premium (Monthly)"
        elif user.subscription == "annual":
            return "Premium (Annual)"
        return "Free"

    user_data = [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "subscription": format_subscription(user)
        }
        for user in page.object_list
    ]

    return JsonResponse({
        "users": user_data,
        "pagination": {
            "current_page": page.number,
            "total_pages": paginator.num_pages,
            "has_next": page.has_next(),
            "has_prev": page.has_previous()
        }
    })


# Administrators Management
@auth_required
@role_required(["admin", "superadmin"])
def list_admins(request):
    page_number = int(request.GET.get("page", 1))
    admins = CustomUser.objects.filter(role__in=["admin", "superadmin"]).order_by("id")
    paginator = Paginator(admins, 10)

    page = paginator.get_page(page_number)
    admin_data = [
        {
            "id": admin.id,
            "name": admin.username,
            "email": admin.email,
            "contact_number": admin.contact_number,
            "role": admin.role,
            "is_active": admin.is_active
        }
        for admin in page.object_list
    ]

    return JsonResponse({
        "admins": admin_data,
        "pagination": {
            "current_page": page.number,
            "total_pages": paginator.num_pages,
            "has_next": page.has_next(),
            "has_prev": page.has_previous()
        }
    })

@csrf_exempt
@auth_required
@role_required(["superadmin"])
def add_admin(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    data = _json(request) or {}
    email = data.get("email")
    password = data.get("password")
    username = data.get("name")
    contact = data.get("contact_number")
    role = data.get("role", "admin")

    if not all([email, password, username]):
        return JsonResponse({"error": "Missing required fields"}, status=400)

    if CustomUser.objects.filter(email=email).exists():
        return JsonResponse({"error": "Email already exists"}, status=400)

    admin = CustomUser.objects.create_user(
        username=username,
        email=email,
        password=password,
        role=role,
        contact_number=contact
    )
    return JsonResponse({"message": "Admin created", "id": admin.id}, status=201)


@csrf_exempt
@auth_required
@role_required(["superadmin"])
def delete_admin(request, admin_id: int):
    if request.method != "DELETE":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        u = CustomUser.objects.get(id=admin_id, role__in=["admin", "superadmin"])
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "Admin not found"}, status=404)

    if u.role == "superadmin":
        return JsonResponse({"error": "Cannot delete superadmin"}, status=403)

    u.delete()
    return JsonResponse({"message": "Admin deleted"}, status=200)


# Sessions Management
@csrf_exempt
@auth_required
@role_required(["superadmin", "admin"])
def list_sessions(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET allowed"}, status=405)

    page_number = int(request.GET.get("page", 1))
    sessions = Session.objects.select_related("user").order_by("-created_at")
    paginator = Paginator(sessions, 10)
    page = paginator.get_page(page_number)

    mood_scores = {"Excellent": 5, "Good": 4, "Neutral": 3, "Bad": 2, "Terrible": 1}
    reverse_map = {v: k for k, v in mood_scores.items()}

    session_data = []
    for session in page.object_list:
        user_sessions = Session.objects.filter(user=session.user, is_completed=True)
        scores = [mood_scores.get(s.mood, 3) for s in user_sessions if s.mood]
        avg_score = sum(scores) / len(scores) if scores else 3
        average_mood = reverse_map.get(round(avg_score), "Neutral")

        session_data.append({
            "username": session.user.username,
            "average_mood": average_mood,
            "session_mood": session.mood
        })

    return JsonResponse({
        "sessions": session_data,
        "pagination": {
            "current_page": page.number,
            "total_pages": paginator.num_pages,
            "has_next": page.has_next(),
            "has_prev": page.has_previous()
        }
    }, status=200)


# Backgrounds Management
@csrf_exempt
@auth_required
@role_required(["superadmin", "admin"])
def list_backgrounds(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET allowed"}, status=405)

    backgrounds = Background.objects.all().values("id", "name", "audio_file", "created_at")
    return JsonResponse(list(backgrounds), safe=False, status=200)


@csrf_exempt
@auth_required
@role_required(["superadmin", "admin"])
def add_background(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    data = _json(request) or {}
    name = data.get("name")
    audio_file = data.get("audio_file")

    if not name:
        return JsonResponse({"error": "Missing background name"}, status=400)

    if Background.objects.filter(name=name).exists():
        return JsonResponse({"error": f"Background '{name}' already exists"}, status=400)

    background = Background.objects.create(name=name, audio_file=audio_file)
    return JsonResponse({
        "message": "Background added successfully",
        "id": background.id,
        "name": background.name,
        "audio_file": background.audio_file.url if background.audio_file else None
    }, status=201)


@csrf_exempt
@auth_required
@role_required(["superadmin", "admin"])
def delete_background(request, background_id):
    if request.method != "DELETE":
        return JsonResponse({"error": "Only DELETE allowed"}, status=405)

    try:
        Background.objects.get(id=background_id).delete()
        return JsonResponse({"message": "Background deleted"}, status=200)
    except Background.DoesNotExist:
        return JsonResponse({"error": "Background not found"}, status=404)


# Moods Management
@csrf_exempt
@auth_required
@role_required(["superadmin", "admin"])
def list_moods(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET allowed"}, status=405)

    moods = Mood.objects.all().values("id", "name", "created_at")
    return JsonResponse(list(moods), safe=False, status=200)


@csrf_exempt
@auth_required
@role_required(["superadmin", "admin"])
def add_mood(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    data = _json(request) or {}
    name = data.get("name")
    if not name:
        return JsonResponse({"error": "Missing mood name"}, status=400)

    mood = Mood.objects.create(name=name)
    return JsonResponse({
        "message": "Mood added successfully",
        "id": mood.id,
        "name": mood.name
    }, status=201)


@csrf_exempt
@auth_required
@role_required(["superadmin", "admin"])
def delete_mood(request, mood_id):
    if request.method != "DELETE":
        return JsonResponse({"error": "Only DELETE allowed"}, status=405)

    try:
        Mood.objects.get(id=mood_id).delete()
        return JsonResponse({"message": "Mood deleted"}, status=200)
    except Mood.DoesNotExist:
        return JsonResponse({"error": "Mood not found"}, status=404)


# Mood Questions Management
@csrf_exempt
@auth_required
@role_required(["superadmin", "admin"])
def list_mood_questions(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET allowed"}, status=405)

    # Get all moods from DB
    moods = Mood.objects.all().order_by("id")

    data = []
    for mood in moods:
        questions = get_questions(mood.name.lower())  # use your helper
        data.append({
            "mood_id": mood.id,
            "mood_name": mood.name,
            "questions": questions
        })

    return JsonResponse({"moods": data}, status=200)

@csrf_exempt
@auth_required
@role_required(["superadmin", "admin"])
def add_mood_question(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    data = _json(request) or {}
    mood_id = data.get("mood_id")
    question = data.get("question")

    if not mood_id or not question:
        return JsonResponse({"error": "Missing mood_id or question"}, status=400)

    mood = Mood.objects.filter(id=mood_id).first()
    if not mood:
        return JsonResponse({"error": "Mood not found"}, status=404)

    q = MoodQuestion.objects.create(mood=mood, question=question)

    return JsonResponse({
        "message": "Question added",
        "id": q.id,
        "mood_id": mood.id,
        "mood_name": mood.name,
        "question": q.question
    }, status=201)


@csrf_exempt
@auth_required
@role_required(["superadmin", "admin"])
def delete_mood_question(request, question_id):
    if request.method != "DELETE":
        return JsonResponse({"error": "Only DELETE allowed"}, status=405)

    try:
        q = MoodQuestion.objects.get(id=question_id)
        q.delete()
        return JsonResponse({
            "message": "Question deleted",
            "id": question_id,
            "question": q.question
        }, status=200)
    except MoodQuestion.DoesNotExist:
        return JsonResponse({"error": "Question not found"}, status=404)
    