import os
import logging
import tempfile
import requests
from typing import List, Dict
from pydub import AudioSegment
from dotenv import load_dotenv
from pathlib import Path
from django.conf import settings  # import Django settings for MEDIA_ROOT

# Load .env from current working directory or project root
load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
logging.basicConfig(level=logging.INFO)

if not ELEVENLABS_API_KEY:
    logging.error("ELEVENLABS_API_KEY is missing. Set it in your .env file.")

# Voice mapping
VOICE_MAP = {
    "female": {
        "name": "Rachel",
        "id": "21m00Tcm4TlvDq8ikWAM"
    },
    "male": {
        "name": "Josh",
        "id": "TxGEqnHWrfWFTfGW9XjX"
    }
}

# Base output directory -> media/audio
OUTPUT_DIR = Path(settings.MEDIA_ROOT) / "audio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Session counter file path
SESSION_COUNTER_PATH = OUTPUT_DIR / "session_counter.txt"

def get_next_session_number() -> int:
    """Increment and return the next session number."""
    if not SESSION_COUNTER_PATH.exists():
        SESSION_COUNTER_PATH.write_text("1")
        return 1
    current = int(SESSION_COUNTER_PATH.read_text().strip() or "0")
    next_num = current + 1
    SESSION_COUNTER_PATH.write_text(str(next_num))
    return next_num

def parse_duration(duration_str: str) -> int:
    """Convert '30 seconds' or '1 minute' into milliseconds."""
    try:
        value = float(duration_str.split()[0])
        unit = duration_str.lower()
        if "minute" in unit:
            return int(value * 60000)
        elif "second" in unit:
            return int(value * 1000)
        else:
            return int(value)
    except Exception:
        logging.warning("Invalid pause format: %s", duration_str)
        return 1000

def call_elevenlabs(text: str, voice_label: str = "female") -> str:
    """Send text to ElevenLabs API and return path to temporary MP3 file."""
    voice_info = VOICE_MAP.get(voice_label.lower(), VOICE_MAP["female"])
    voice_id = voice_info["id"]

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "voice_settings": {
            "stability": 0.75,
            "similarity_boost": 0.85
        }
    }

    response = requests.post(url, headers=headers, json=payload, stream=True)
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        for chunk in response.iter_content(8192):
            f.write(chunk)
        logging.info("Synthesized voice for: %s", text[:40])
        return f.name

def synthesize_voice(tokens: List[Dict], voice_label: str, session_num: int) -> str:
    """Convert tokens (text + pauses) into a single MP3 file for given session_num."""
    segments = []

    for token in tokens:
        if token.get("type") == "pause":
            ms = parse_duration(token.get("duration", "1 second"))
            segments.append(AudioSegment.silent(duration=ms))
        elif token.get("type") == "text":
            mp3_path = call_elevenlabs(token.get("content", ""), voice_label)
            if not mp3_path:
                raise RuntimeError(f"Voice synthesis failed for: {token.get('content', '')[:40]}")
            segments.append(AudioSegment.from_file(mp3_path))

    if not segments:
        raise RuntimeError("No audio segments generated.")

    final_audio = segments[0]
    for seg in segments[1:]:
        final_audio += seg

    out_path = OUTPUT_DIR / f"session{session_num}.mp3"
    final_audio.export(str(out_path), format="mp3", bitrate="192k")
    logging.info("Final voice saved to: %s", out_path)

    return str(out_path)
