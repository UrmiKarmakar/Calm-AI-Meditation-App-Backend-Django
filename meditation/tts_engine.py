import os
import logging
import tempfile
import requests
from typing import List, Dict
from pydub import AudioSegment
from dotenv import load_dotenv
from pathlib import Path

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

# Session counter file path
SESSION_COUNTER_PATH = os.path.join("meditation", "output", "session_counter.txt")

def get_next_session_number() -> int:
    if not os.path.exists(SESSION_COUNTER_PATH):
        with open(SESSION_COUNTER_PATH, "w") as f:
            f.write("1")
        return 1
    with open(SESSION_COUNTER_PATH, "r+") as f:
        current = int(f.read().strip())
        next_num = current + 1
        f.seek(0)
        f.write(str(next_num))
        f.truncate()
        return next_num

def parse_duration(duration_str: str) -> int:
    try:
        value = float(duration_str.split()[0])
        unit = duration_str.lower()
        if "minute" in unit:
            return int(value * 60000)
        elif "second" in unit:
            return int(value * 1000)
        else:
            return int(value)
    except Exception as e:
        logging.warning("Invalid pause format: %s", duration_str)
        return 1000

def call_elevenlabs(text: str, voice_label: str = "female") -> str:
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

def synthesize_voice(tokens: List[Dict], voice_label: str = "female") -> str:
    segments = []

    for token in tokens:
        if token["type"] == "pause":
            ms = parse_duration(token["duration"])
            segments.append(AudioSegment.silent(duration=ms))
        elif token["type"] == "text":
            mp3_path = call_elevenlabs(token["content"], voice_label)
            if not mp3_path:
                raise RuntimeError(f"Voice synthesis failed for: {token['content'][:40]}")
            segments.append(AudioSegment.from_file(mp3_path))

    if not segments:
        raise RuntimeError("No audio segments generated.")

    final_audio = segments[0]
    for seg in segments[1:]:
        final_audio += seg



    BASE_DIR = Path(__file__).resolve().parent  # points to meditation/
    output_dir = BASE_DIR / "output"
    output_dir.mkdir(exist_ok=True)

    os.makedirs(output_dir, exist_ok=True)

    session_num = get_next_session_number()
    out_path = output_dir / f"session{session_num}.mp3"
    final_audio.export(str(out_path), format="mp3", bitrate="192k")
    logging.info("Final voice saved to: %s", out_path)

    return out_path