import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.conf import settings
import jwt
from datetime import datetime, timedelta
from .models import User, OTPCode, UserProfile

def send_otp_email(user, code):
    send_mail("Your CalmAI verification code", f"Your 6-digit code is: {code}",
              settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)

@csrf_exempt
def register(request):
    data = json.loads(request.body.decode("utf-8"))
    email, password = data.get("email"), data.get("password")
    if User.objects.filter(email=email).exists():
        return JsonResponse({"error": "Email already registered"}, status=409)
    user = User.objects.create_user(username=email, email=email, password=password, is_verified=False)
    code = get_random_string(6, allowed_chars="0123456789")
    OTPCode.objects.create(user=user, code=code)
    send_otp_email(user, code)
    return JsonResponse({"message": "Registered. OTP sent to email."}, status=201)

@csrf_exempt
def verify_otp(request):
    data = json.loads(request.body.decode("utf-8"))
    email, code = data.get("email"), data.get("code")
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    otp = OTPCode.objects.filter(user=user, code=code, is_used=False).first()
    if not otp:
        return JsonResponse({"error": "Invalid or expired code"}, status=400)
    otp.is_used = True; otp.save()
    user.is_verified = True; user.save()
    return JsonResponse({"message": "Email verified. You can login now."})

@csrf_exempt
def login_view(request):
    """
    Login endpoint:
    - Authenticates user
    - Returns JWT token, role, and onboarding status
    - Handles missing UserProfile gracefully
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        email = data.get("email")
        password = data.get("password")

        # Authenticate user
        user = authenticate(request, username=email, password=password)
        if user is None:
            return JsonResponse({"error": "Invalid credentials"}, status=401)

        # Generate JWT token
        payload = {
            "user_id": user.id,
            "email": user.email,
            "exp": datetime.utcnow() + timedelta(hours=24),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        # Handle missing profile gracefully
        try:
            onboarding_completed = user.profile.onboarding_completed
        except UserProfile.DoesNotExist:
            onboarding_completed = False

        return JsonResponse({
            "token": token,
            "role": user.role,
            "onboarding_completed": onboarding_completed
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
@csrf_exempt
def submit_onboarding(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")

        # Get or create profile
        profile, _ = UserProfile.objects.get_or_create(user_id=user_id)

        profile.onboarding_completed = True
        profile.save()

        return JsonResponse({"message": "Onboarding completed"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
