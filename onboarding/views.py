# onboarding/views.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from common.decorators import auth_required
from .models import UserProfile

def _json(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return None

# Fixed options for validation
OPTIONS = {
    "mindfulness_goal": ["Reduce stress", "Better sleep", "Reduce anxiety", "Improve focus", "Build self-confidence"],
    "experience_level": ["Completely new", "Beginner (tried occasionally)", "Regular meditator (several times per week)", "Advanced (daily practice)"],
    "meditation_time": ["Morning", "Afternoon", "Evening", "Just before bed", "I don't have a routine yet"],
    "voice_preference": ["Calm female voice", "Calm male voice", "No preference"],
    "stress_level": ["Low", "Average", "High"],
}

@csrf_exempt
@auth_required
def submit_onboarding(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    data = _json(request) or {}
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    # Validate each answer: must be in OPTIONS or empty string
    for field, valid_options in OPTIONS.items():
        answer = data.get(field, "")
        if answer == "":
            setattr(profile, field, "")  # skip
        elif answer in valid_options:
            setattr(profile, field, answer)
        else:
            return JsonResponse({"error": f"Invalid option for {field}"}, status=400)

    profile.onboarding_complete = True
    profile.save()

    return JsonResponse({"message": "Onboarding complete. Show subscription page."}, status=200)

@csrf_exempt
@auth_required
def activate_subscription(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.subscription_active = True
    profile.save()
    return JsonResponse({"message": "Subscription activated. Redirect to Home."}, status=200)

@csrf_exempt
@auth_required
def get_profile(request):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user = request.user
    return JsonResponse({
        "username": user.username,
        "email": user.email,
        "avatar_initial": user.username[0].upper()
    }, status=200)

