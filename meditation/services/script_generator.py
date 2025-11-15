import os
import json
import logging
from random import shuffle
from typing import List, Dict
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv(find_dotenv(), override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Constants
WORDS_PER_MINUTE = 120
MS_PER_WORD = 60000 / WORDS_PER_MINUTE
TARGET_MINUTES = 15

def format_system_prompt() -> str:
    return (
        "You are an expert guided meditation writer. Your voice should be soft, slow, and melodious — ideal for deep relaxation and emotional comfort.\n"
        "Output exactly one JSON array of tokens.\n\n"
        "Each token must be one of:\n"
        "- {\"type\": \"text\", \"content\": \"...\"}\n"
        "- {\"type\": \"pause\", \"duration\": \"<N> seconds\" or \"<N> minutes\"}\n\n"
        "Rules:\n"
        "1. Every pause must be preceded by a guiding instruction that clearly tells the listener what to do and for how long.\n"
        "2. Mention durations naturally in the text (e.g. '...for 30 seconds.','...for a while','...take some moment').\n"
        "3. Use pauses for breathing, reflection, or emotional settling — never silently.\n"
        "4. Use varied pause durations: short (5–10s), medium (15–30s), long (1–2min).\n"
        "5. Maintain a gentle, soft, slow, calm emotionally attuned tone throughout.\n"
        "6. End with: 'Now take a deep breath... and gently return to the present moment.' followed by 'Your session has now gently come to an end.'\n"
        "7. After the final line, do not add any more tokens.\n"
        "8. Output only valid JSON — no markdown, no commentary, no extra text."
    )

def estimate_duration(tokens: List[Dict]) -> float:
    """Estimate total duration in minutes based on tokens."""
    total_ms = 0
    for token in tokens:
        if token.get("type") == "pause":
            try:
                value, unit = token["duration"].split()
                value = float(value)
                if "minute" in unit.lower():
                    total_ms += value * 60000
                elif "second" in unit.lower():
                    total_ms += value * 1000
            except Exception:
                continue
        elif token.get("type") == "text":
            word_count = len(token.get("content", "").split())
            total_ms += word_count * MS_PER_WORD
    return round(total_ms / 60000, 2)

def pad_tokens_to_duration(tokens: List[Dict], target_minutes: int) -> List[Dict]:
    """Pad tokens with extra pauses until target duration is reached."""
    if any("your session has now gently come to an end" in t.get("content", "").lower() for t in tokens):
        return tokens

    padding_blocks = [
        ("Let your breath guide you... Stay here for 30 seconds.", "30 seconds"),
        ("Feel your body soften... Remain still for 1 minute.", "1 minute"),
        ("Let go of tension... and breathe gently for 15 seconds.", "15 seconds"),
        ("Stay present... and quiet for 10 seconds.", "10 seconds"),
        ("Allow your thoughts to settle... for 20 seconds.", "20 seconds"),
        ("Let your body rest... for 1 minute.", "1 minute"),
        ("Breathe slowly... and stay here for 15 seconds.", "15 seconds"),
        ("Let your breath anchor you... for 30 seconds.", "30 seconds")
    ]

    shuffle(padding_blocks)

    # Keep adding pauses until duration >= target_minutes
    while estimate_duration(tokens) < target_minutes:
        text, duration = padding_blocks[0]
        tokens.append({"type": "text", "content": text})
        tokens.append({"type": "pause", "duration": duration})
        shuffle(padding_blocks)  # reshuffle for variety

    return tokens

def trim_to_target(tokens: List[Dict], target_minutes: int, tolerance: float = 0.17) -> List[Dict]:
    """
    Trim tokens so final duration is within target ± tolerance (default ~10 seconds).
    """
    while estimate_duration(tokens) > target_minutes + tolerance and tokens:
        # Remove last pause or text if overshooting
        tokens.pop()
    return tokens

def fallback_tokens(mood: str, duration: int = 15) -> List[Dict]:
    logging.warning("Using fallback script for mood '%s'", mood)

    mood_opening = {
        "tired": "Welcome... to your meditation session... I’m your guide today... You’ve carried so much — let’s gently lay it down together...",
        "sadness": "Welcome... to your meditation session... I’m here with you... In this quiet space, we’ll hold your feelings with care...",
        "anxiety": "Welcome... to your meditation session... I’m your guide today... Let’s slow everything down. You’re safe here...",
        "stress": "Welcome... to your meditation session... I’m here to help you release the tension you’ve been carrying...",
        "calm": "Welcome... to your meditation session... I’m your guide today... Let’s deepen the stillness already within you..."
    }

    mood = mood if mood in mood_opening else "calm"

    base = [
        {"type": "text", "content": mood_opening[mood]},
        {"type": "pause", "duration": "5 seconds"},
        {"type": "text", "content": "Take a slow breath in... and exhale gently... Stay here for 30 seconds."},
        {"type": "pause", "duration": "30 seconds"},
        {"type": "text", "content": "Let your body settle... and your breath guide you... Stay here for 1 minute."},
        {"type": "pause", "duration": "1 minute"},
        {"type": "text", "content": "Feel the tension gently melting away... Stay here for 30 seconds."},
        {"type": "pause", "duration": "30 seconds"},
        {"type": "text", "content": "Now, stay in peaceful silence... simply breathing... for 2 minutes."},
        {"type": "pause", "duration": "2 minutes"}
    ]

    padded = pad_tokens_to_duration(base, duration)
    padded.extend([
        {"type": "text", "content": "Now take a deep breath... and gently return to the present moment."},
        {"type": "pause", "duration": "10 seconds"},
        {"type": "text", "content": "Thank yourself... for this time of calm and care."},
        {"type": "pause", "duration": "10 seconds"},
        {"type": "text", "content": "Your session has now gently come to an end."},
        {"type": "pause", "duration": "10 seconds"}
    ])
    return padded

def mood_prompt(mood: str, formatted_answers: str) -> str:
    mood_descriptions = {
        "tired": "physical fatigue, mental rest, and gentle renewal",
        "sadness": "emotional tenderness, quiet support, and inner healing",
        "anxiety": "slowing down, grounding, and breath-based safety",
        "stress": "release, softening, and tension relief",
        "calm": "deepening stillness, spaciousness, and breath awareness"
    }

    return (
        f"You are a professional meditation coach creating a 15 minutes guided session for someone feeling '{mood}'. "
        f"Session must be 15 minutes and should focus on {mood_descriptions.get(mood, 'general relaxation and mindfulness')}.\n"
        "Your voice should be soft, slow, and melodious — ideal for deep relaxation and emotional comfort. "
        "Your tone must be warm, grounded, and emotionally attuned. "
        "Include breath cues, natural pauses, and gentle transitions. "
        "End with: 'Now take a deep breath... and gently return to the present moment...' "
        "Then close with: 'Your session has now gently come to an end.' "
        f"Here are their answers:\n{formatted_answers}\n"
        "Format the output strictly as a JSON array of tokens — no markdown, no commentary, no extra text."
    )

def trim_after_session_end(tokens: List[Dict]) -> List[Dict]:
    for i, token in enumerate(tokens):
        if (
            token.get("type") == "text"
            and "your session has now gently come to an end" in token.get("content", "").lower()
        ):
            return tokens[: i + 1]
    return tokens

def generate_script(mood: str, answers: Dict[str, str]) -> List[Dict]:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is missing or not loaded")

    duration = TARGET_MINUTES
    formatted_answers = "\n".join([f"{q}: {a}" for q, a in answers.items()])
    prompt = mood_prompt(mood, formatted_answers)

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": format_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        content = response.choices[0].message.content.strip()

        try:
            tokens = json.loads(content)
            if not isinstance(tokens, list):
                raise ValueError("Invalid token structure")
        except Exception as e:
            logging.error("Invalid JSON from OpenAI: %s", e)
            return fallback_tokens(mood, duration)

        initial_duration = estimate_duration(tokens)
        logging.info("Initial script duration: %.2f minutes", initial_duration)

        # Pad once
        tokens = pad_tokens_to_duration(tokens, duration)

        # Trim overshoot to ~15:00 ± 10s
        tokens = trim_to_target(tokens, duration)

        # Trim after final "session end"
        tokens = trim_after_session_end(tokens)

        final_duration = estimate_duration(tokens)
        logging.info("Final script duration: %.2f minutes", final_duration)

        return tokens

    except Exception as e:
        logging.error("GPT error or invalid response: %s", e)
        return fallback_tokens(mood, duration)