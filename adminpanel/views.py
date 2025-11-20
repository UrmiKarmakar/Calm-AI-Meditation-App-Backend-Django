import json
import datetime
from django.http import JsonResponse
from django.db.models import Count
from django.utils.timezone import now
from django.conf import settings
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.paginator import Paginator

from accounts.models import CustomUser, PasswordResetOTP
from meditation.models import Session
from meditation.mood_questions import get_questions
from common.decorators import auth_required, role_required

def _json(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return None

# Admin Authentication
@csrf_exempt
def admin_login(request):
    from django.contrib.auth.hashers import check_password
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    data = _json(request) or {}
    identifier = data.get("email") or data.get("username")
    password = data.get("password")
    if not identifier or not password:
        return JsonResponse({"error": "Missing credentials"}, status=400)
    try:
        user = CustomUser.objects.get(email=identifier) if "@" in identifier else CustomUser.objects.get(username=identifier)
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    if user.role not in ["admin", "superadmin"]:
        return JsonResponse({"error": "Forbidden"}, status=403)
    if not check_password(password, user.password):
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    from common.jwt_utils import issue_jwt
    token = issue_jwt(user)
    return JsonResponse({"token": token, "role": user.role, "username": user.username}, status=200)

@csrf_exempt
def admin_forgot_password(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    data = _json(request) or {}
    email = data.get("email")
    if not email:
        return JsonResponse({"error": "Email required"}, status=400)
    try:
        user = CustomUser.objects.get(email=email, role__in=["admin", "superadmin"])
    except CustomUser.DoesNotExist:
        return JsonResponse({"message": "If the email exists, an OTP was sent"}, status=200)

    latest = PasswordResetOTP.objects.filter(user=user, is_used=False).order_by("-created_at").first()
    RESEND_SECONDS = 60
    if latest and (now() - latest.created_at).total_seconds() < RESEND_SECONDS:
        remain = RESEND_SECONDS - int((now() - latest.created_at).total_seconds())
        return JsonResponse({"error": "Resend too soon", "retry_in": remain}, status=429)

    code = get_random_string(6, allowed_chars="0123456789")
    PasswordResetOTP.objects.create(user=user, code=code, expires_at=now() + datetime.timedelta(minutes=10))
    return JsonResponse({"message": "Reset OTP sent", "otp_preview": code, "resend_after": RESEND_SECONDS}, status=200)

@csrf_exempt
def admin_verify_reset_otp(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    data = _json(request) or {}
    email = data.get("email")
    code = data.get("otp")
    try:
        user = CustomUser.objects.get(email=email, role__in=["admin", "superadmin"])
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    otp = PasswordResetOTP.objects.filter(user=user, code=code, is_used=False).order_by("-created_at").first()
    if not otp or otp.expires_at < now():
        return JsonResponse({"error": "Invalid or expired code"}, status=400)
    otp.is_used = True
    otp.save()
    return JsonResponse({"message": "OTP verified. You can reset password now."}, status=200)

@csrf_exempt
def admin_reset_password(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    data = _json(request) or {}
    email = data.get("email")
    pw = data.get("password")
    cpw = data.get("confirm_password")
    if not all([email, pw, cpw]) or pw != cpw:
        return JsonResponse({"error": "Invalid fields"}, status=400)
    try:
        user = CustomUser.objects.get(email=email, role__in=["admin", "superadmin"])
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    from django.contrib.auth.hashers import make_password
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

    paginator = Paginator(users, 10)  # 10 users per page
    page = paginator.get_page(page_number)

    user_data = [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "subscription": user.subscription

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
@role_required(["superadmin"])
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

    data = json.loads(request.body)
    email = data.get("email")
    password = data.get("password")
    username = data.get("name")
    contact = data.get("contact_number")
    role = data.get("role", "admin")

    if CustomUser.objects.filter(email=email).exists():
        return JsonResponse({"error": "Email already exists"}, status=400)

    admin = CustomUser.objects.create_user(
        username=username,
        email=email,
        password=password,
        role=role,
        contact_number=contact
    )
    return JsonResponse({"message": "Admin created", "id": admin.id})

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

# Backgrounds
@auth_required
@role_required(["admin", "superadmin"])
def backgrounds(request):
    if request.method == "GET":
        files = []
        # Ensure the backgrounds folder exists
        root = os.path.join(settings.STATICFILES_DIRS[0], "backgrounds")
        if not os.path.exists(root):
            return JsonResponse({"error": "Backgrounds folder not found"}, status=404)

        for f in os.listdir(root):
            if f.endswith(".mp3"):
                files.append(f)

        return JsonResponse({"backgrounds": files}, status=200)

    return JsonResponse({"error": "Method not allowed"}, status=405)


# Moods
@auth_required
@role_required(["admin", "superadmin"])
def moods(request):
    supported = ["calm", "anxiety", "tired", "stress", "sadness"]

    if request.method == "GET":
        # Explicit list of supported moods
        return JsonResponse({"moods": supported}, status=200)

    if request.method == "POST":
        data = _json(request) or {}
        mood = data.get("mood", "").lower()

        if not mood:
            return JsonResponse({"error": "Mood required"}, status=400)
        if mood in supported:
            return JsonResponse({"error": "Duplicate mood"}, status=400)

        # In a real system, you'd persist new moods in DB. For now, just acknowledge.
        return JsonResponse({"message": f"Mood '{mood}' added"}, status=201)

    return JsonResponse({"error": "Method not allowed"}, status=405)


# Mood Questions
@auth_required
@role_required(["admin", "superadmin"])
def mood_questions(request):
    if request.method == "GET":
        mood = request.GET.get("mood", "").lower()
        questions = get_questions(mood)
        if not questions:
            return JsonResponse({"error": "Unknown mood"}, status=404)
        return JsonResponse({"mood": mood, "questions": questions}, status=200)

    if request.method == "POST":
        data = _json(request) or {}
        mood = data.get("mood", "").lower()
        question = data.get("question")
        options = data.get("options", [])

        if not mood or not question or not isinstance(options, list) or not options:
            return JsonResponse({"error": "Invalid fields"}, status=400)

        # Normally you'd save to DB. Here we just echo back.
        return JsonResponse({
            "message": "Question added",
            "mood": mood,
            "question": question,
            "options": options
        }, status=201)

    if request.method == "DELETE":
        data = _json(request) or {}
        mood = data.get("mood", "").lower()
        question = data.get("question")

        if not mood or not question:
            return JsonResponse({"error": "Invalid fields"}, status=400)

        # Normally you'd remove from DB. Here we just echo back.
        return JsonResponse({
            "message": "Question removed",
            "mood": mood,
            "question": question
        }, status=200)

    return JsonResponse({"error": "Method not allowed"}, status=405)
