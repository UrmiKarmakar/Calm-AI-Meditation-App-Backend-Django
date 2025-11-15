import json
import os
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .services.script_generator import generate_script
from .services.tts_engine import synthesize_voice, get_next_session_number
from .services.mixer import mix_background

logging.basicConfig(level=logging.INFO)

@csrf_exempt
def generate_session(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        mood = data.get("mood", "")
        answers = data.get("answers", {})
        voice = data.get("voice", "female")
        background = data.get("background", "forest")

        # 1) Increment session counter ONCE
        session_num = get_next_session_number()

        # 2) Generate tokens
        tokens = generate_script(mood, answers)

        # 3) Extract text segments
        segments = [t["content"] for t in tokens if isinstance(t, dict) and t.get("type") == "text"]
        if not segments:
            logging.error("No text segments extracted from tokens.")
            return JsonResponse({"error": "No script text generated."}, status=500)

        script_text = " ".join(segments)
        logging.info("Generated script text: %s", script_text)

        # 4) Synthesize voice with session_num
        voice_path = synthesize_voice(tokens, voice, session_num)
        if not voice_path or not os.path.exists(voice_path):
            logging.error("TTS did not produce a file. voice_path=%s", voice_path)
            return JsonResponse({"error": "No audio segments generated."}, status=500)

        # 5) Mix background with same session_num
        mixed_path = mix_background(voice_path, background, session_num)
        if not mixed_path or not os.path.exists(mixed_path):
            logging.error("Mixer did not produce a file. mixed_path=%s", mixed_path)
            return JsonResponse({"error": "Audio mixing failed."}, status=500)

        # 6) Return final file URL
        file_url = f"/media/audio/session{session_num}_final.mp3"
        return JsonResponse({"file": file_url, "script": script_text})

    except Exception as e:
        logging.error("Error in generate_session: %s", e)
        return JsonResponse({"error": str(e)}, status=500)
