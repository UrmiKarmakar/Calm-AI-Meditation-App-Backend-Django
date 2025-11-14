import json
import os
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .services.script_generator import generate_script
from .services.tts_engine import synthesize_voice
from .services.mixer import mix_background

logging.basicConfig(level=logging.INFO)

def get_next_session_filename():
    """
    Auto-increment session filenames: session1.mp3, session2.mp3, etc.
    """
    outdir = os.path.join(settings.MEDIA_ROOT, "audio")
    os.makedirs(outdir, exist_ok=True)

    existing = [f for f in os.listdir(outdir) if f.startswith("session") and f.endswith(".mp3")]
    nums = []
    for f in existing:
        try:
            nums.append(int(f.replace("session", "").replace(".mp3", "").replace("_final", "")))
        except ValueError:
            continue

    next_num = max(nums) + 1 if nums else 1
    fname = f"session{next_num}.mp3"
    return os.path.join(outdir, fname), f"{settings.MEDIA_URL}audio/{fname}"

@csrf_exempt
def generate_session(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        mood = data.get("mood", "")
        answers = data.get("answers", {})
        voice = data.get("voice", "female")
        background = data.get("background", "")

        # 1) Generate tokens (list of dicts)
        tokens = generate_script(mood, answers)

        # 2) Extract text segments correctly (use 'content' for text tokens)
        segments = [t["content"] for t in tokens if isinstance(t, dict) and t.get("type") == "text"]
        if not segments:
            logging.error("No text segments extracted from tokens.")
            return JsonResponse({"error": "No script text generated."}, status=500)

        script_text = " ".join(segments)
        logging.info("Generated script text: %s", script_text)

        # 3) Synthesize voice from tokens (NOT script_text)
        voice_path = synthesize_voice(tokens, voice)
        if not voice_path or not os.path.exists(voice_path):
            logging.error("TTS did not produce a file. voice_path=%s", voice_path)
            return JsonResponse({"error": "No audio segments generated."}, status=500)

        # 4) Mix background (returns a new path)
        mixed_path = mix_background(voice_path, background)
        if not mixed_path or not os.path.exists(mixed_path):
            logging.error("Mixer did not produce a file. mixed_path=%s", mixed_path)
            return JsonResponse({"error": "Audio mixing failed."}, status=500)

        # 5) Save final auto-increment file
        final_path, file_url = get_next_session_filename()
        if os.path.abspath(mixed_path) != os.path.abspath(final_path):
            with open(mixed_path, "rb") as src, open(final_path, "wb") as dst:
                dst.write(src.read())

        return JsonResponse({"file": file_url, "script": script_text})

    except Exception as e:
        logging.error("Error in generate_session: %s", e)
        return JsonResponse({"error": str(e)}, status=500)
