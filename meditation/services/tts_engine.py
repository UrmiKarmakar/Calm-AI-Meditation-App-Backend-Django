import os
import logging
import tempfile
import requests
import json
import re
from typing import List, Dict
from pydub import AudioSegment
from pathlib import Path
from django.conf import settings

ELEVENLABS_API_KEY = settings.ELEVENLABS_API_KEY
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
    """Convert flexible strings (e.g., '30 sec', '1.5 minutes') into ms."""
    s = (duration_str or "").strip().lower()
    try:
        # Extract first numeric value
        nums = re.findall(r'[\d\.]+', s)
        value = float(nums[0]) if nums else 1.0
        if "min" in s:
            return int(value * 60000)
        if "sec" in s or "second" in s:
            return int(value * 1000)
        # Fallback keywords
        if "half" in s and "minute" in s:
            return 30000
        if "quarter" in s and "minute" in s:
            return 15000
    except Exception:
        logging.warning("Invalid pause format: %s", duration_str)
    return 1000


def call_elevenlabs(text: str, voice_label: str = "female") -> str:
    """Send text to ElevenLabs API and return path to temporary MP3 file."""
    if not ELEVENLABS_API_KEY or len(ELEVENLABS_API_KEY) < 10:
        raise RuntimeError("ELEVENLABS_API_KEY missing or invalid. Check .env and settings.py.")

    voice_info = VOICE_MAP.get(voice_label.lower(), VOICE_MAP["female"])
    voice_id = voice_info["id"]

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "voice_settings": {"stability": 0.75, "similarity_boost": 0.85}
    }

    try:
        response = requests.post(url, headers=headers, json=payload, stream=True, timeout=30)
    except requests.RequestException as e:
        raise RuntimeError(f"ElevenLabs request failed: {e}")

    if response.status_code == 401:
        # Try to read error details from ElevenLabs
        detail = ""
        try:
            detail = response.text or ""
        except Exception:
            pass
        raise RuntimeError(f"ElevenLabs 401 Unauthorized. Check ELEVENLABS_API_KEY (user key required). Details: {detail}")

    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        raise RuntimeError(f"ElevenLabs HTTP error: {e}. Body: {response.text}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        for chunk in response.iter_content(8192):
            f.write(chunk)
        logging.info("Synthesized voice for: %s", text[:60])
        return f.name

def synthesize_voice(tokens: List[Dict], voice_label: str, session_num: int) -> str:
    """Convert tokens (text + pauses) into a single MP3 file for given session_num."""
    segments = []

    for token in tokens:
        if token.get("type") == "pause":
            ms = parse_duration(token.get("duration", "1 second"))
            segments.append(AudioSegment.silent(duration=ms))
        elif token.get("type") == "text":
            try:
                mp3_path = call_elevenlabs(token.get("content", ""), voice_label)
                audio = AudioSegment.from_file(mp3_path)
                os.remove(mp3_path)
                segments.append(audio)
            except Exception as e:
                logging.error("TTS failed for text '%s': %s", token.get("content", "")[:40], e)
                segments.append(AudioSegment.silent(duration=1000))

    if not segments:
        raise RuntimeError("No audio segments generated.")

    final_audio = AudioSegment.empty()
    for seg in segments:
        final_audio += seg

    out_path = OUTPUT_DIR / f"session{session_num}.mp3"
    final_audio.export(str(out_path), format="mp3", bitrate="192k")
    logging.info("Final voice saved to: %s (duration: %.2f sec)", out_path, len(final_audio) / 1000.0)


    return str(out_path)