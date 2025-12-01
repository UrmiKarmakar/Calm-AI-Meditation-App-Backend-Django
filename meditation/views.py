# meditation/views.py
import json
from pathlib import Path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Count
from django.conf import settings
from common.decorators import auth_required
from .models import Session
from .mood_questions import get_questions
# Services
from .services.script_generator import generate_script
from .services.tts_engine import synthesize_voice
from .services.mixer import mix_background

def _json(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return None


@csrf_exempt
@auth_required
def list_moods(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET allowed"}, status=405)
    moods = ["sadness", "tired", "stress", "anxiety", "calm"]
    return JsonResponse({"moods": moods}, status=200)


@csrf_exempt
@auth_required
def mood_questions(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET allowed"}, status=405)
    mood = (request.GET.get("mood") or "").lower()
    questions = get_questions(mood)
    if not questions:
        return JsonResponse({"error": "Unknown mood"}, status=400)
    return JsonResponse({"mood": mood, "questions": questions}, status=200)


@csrf_exempt
@auth_required
def generate_session(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    data = _json(request) or {}
    mood = data.get("mood", "")
    answers = data.get("answers") or []
    background = data.get("background") or ""
    voice = data.get("voice") or "male"

    if not mood or not answers:
        return JsonResponse({"error": "Missing required fields: mood and answers"}, status=400)

    # Validate answers: must be a list of 5 strings
    if not isinstance(answers, list) or len(answers) != 5:
        return JsonResponse({"error": "Answers must be a list of 5 items"}, status=400)

    # check answers against expected options for the mood
    expected_questions = get_questions(mood)
    expected_options = [q["options"] for q in expected_questions]
    for idx, ans in enumerate(answers):
        if ans not in expected_options[idx]:
            return JsonResponse({"error": f"Invalid answer: {ans}"}, status=400)

    try:
        # Generate meditation script from mood + answers
        tokens = generate_script(mood, answers)

        # Create DB session
        session = Session.objects.create(
            user=request.user,
            mood=mood,
            selected_answers=answers,
            background=background,
            voice=voice,
            duration_minutes=15,
        )

        # Ensure media/audio directory exists
        media_root = Path(getattr(settings, "MEDIA_ROOT", "media"))
        audio_dir = media_root / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Synthesize voice
        voice_only_path = synthesize_voice(tokens=tokens, voice_label=voice, session_num=session.id)

        # Mix background if provided
        final_path = mix_background(voice_path=voice_only_path, bg_name=background, session_num=session.id) if background else voice_only_path

        # Save audio_url
        audio_url = f"/media/audio/{Path(final_path).name}"
        session.audio_url = audio_url
        session.save(update_fields=["audio_url"])

        return JsonResponse({
            "session_id": session.id,
            "duration": session.duration_minutes,
            "audio_url": session.audio_url
        }, status=201)

    except Exception as e:
        import logging
        logging.exception("Error generating session")
        return JsonResponse({"error": f"Failed to generate session: {str(e)}"}, status=500)

@csrf_exempt
@auth_required
def history(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET allowed"}, status=405)
    sessions = Session.objects.filter(user=request.user).order_by("-created_at")
    items = [{
        "id": s.id,
        "mood": s.mood,
        "background": s.background,
        "voice": s.voice,
        "answers": s.selected_answers,
        "rating": s.rating,
        "is_completed": s.is_completed,
        "audio_url": s.audio_url,
        "created_at": s.created_at.isoformat(),
        "duration": s.duration_minutes,
    } for s in sessions]
    return JsonResponse({"sessions": items}, status=200)


@csrf_exempt
@auth_required
def rate_session(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    data = _json(request) or {}
    session_id = data.get("session_id")
    rating = data.get("rating")
    if not session_id or rating is None:
        return JsonResponse({"error": "Missing fields: session_id, rating"}, status=400)
    try:
        session = Session.objects.get(id=session_id, user=request.user)
    except Session.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)
    session.rating = int(rating)
    session.is_completed = True
    session.save(update_fields=["rating", "is_completed"])
    return JsonResponse({"message": "Rating saved"}, status=200)


@csrf_exempt
@auth_required
def get_stats(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET allowed"}, status=405)
    qs = Session.objects.filter(user=request.user, is_completed=True)
    total = qs.count()
    avg_rating = qs.aggregate(avg=Avg("rating"))["avg"] or 0
    dist = {i: 0 for i in range(1, 6)}
    for row in qs.values("rating").annotate(c=Count("id")):
        if row["rating"]:
            dist[row["rating"]] = row["c"]
    labels = {5: "Excellent", 4: "Good", 3: "Average", 2: "Bad", 1: "Worst"}
    return JsonResponse({
        "total_completed": total,
        "average_rating": round(avg_rating, 2),
        "rating_distribution": {labels[k]: dist[k] for k in dist}
    }, status=200)
