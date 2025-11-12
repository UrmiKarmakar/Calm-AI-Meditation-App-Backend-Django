import os
import json
import logging
from random import choice, shuffle
from typing import List, Dict
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv(find_dotenv(), override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Constants
WORDS_PER_MINUTE = 120  # ~500ms per word
MS_PER_WORD = 60000 / WORDS_PER_MINUTE

def format_system_prompt() -> str:
    return (
        "You are an expert guided meditation writer. Your voice should be soft, slow, and melodious — ideal for deep relaxation and emotional comfort.\n"
        "Output exactly one JSON array of tokens.\n\n"
        "Each token must be one of:\n"
        "- {\"type\": \"text\", \"content\": \"...\"}\n"
        "- {\"type\": \"pause\", \"duration\": \"<N> seconds\" or \"<N> minutes\"}\n\n"
        "Rules:\n"
        "1. Before every pause, include a guiding instruction that clearly tells the listener what to do and for how long.\n"
        "2. Mention durations naturally in the text (e.g. '...for 2 minutes.').\n"
        "3. Use pauses for breathing, reflection, or emotional settling — never silently.\n"
        "4. Use varied pause durations: short (5–10s), medium (15–30s), long (1–2min).\n"
        "5. Maintain a gentle, emotionally attuned tone throughout.\n"
        "6. Output only valid JSON — no markdown, no commentary, no extra text."
    )

def estimate_duration(tokens: List[Dict]) -> float:
    total_ms = 0
    for token in tokens:
        if token["type"] == "pause":
            try:
                value, unit = token["duration"].split()
                value = float(value)
                unit = unit.lower()
                if "minute" in unit:
                    total_ms += value * 60000
                elif "second" in unit:
                    total_ms += value * 1000
            except (ValueError, IndexError):
                continue
        elif token["type"] == "text":
            word_count = len(token["content"].split())
            total_ms += word_count * MS_PER_WORD
    return round(total_ms / 60000, 2)

def pad_tokens_to_duration(tokens: List[Dict], target_minutes: int) -> List[Dict]:
    calm_prompts = [
        "Now, inhale deeply through your nose for 5 seconds... exhale through your mouth for 5 seconds.",
        "Stay here, simply breathing for some moment.. and feel it in your inside...",
        "Let your body rest in stillness for one minute...",
        "Take slow, gentle breaths for the next 30 seconds...",
        "Allow your mind to soften — stay quiet for some moment...",
        "Focus on your heart area... Breathe gently here for some times...",
        "Let each exhale release what you no longer need... Stay here for one minute.",
        "Notice your body becoming lighter... Continue breathing calmly for one minutes.",
        "Stay here in peaceful silence for a while, simply observing your breath.",
        "You are safe... and supported...",
        "Let your breath guide you... to stillness...",
        "You are present... You are calm... You are whole...",
        "Thank yourself... for this moment of peace...",
        "You are grounded... and calm...",
        "Picture a warm light surrounding you...",
        "Let this light fill your body with ease...",
        "You are enough... just as you are...",
        "Feel the gentle rhythm of your breath...",
    ]

    used = set()
    shuffle(calm_prompts)

    while estimate_duration(tokens) < target_minutes:
        for line in calm_prompts:
            if line not in used:
                tokens.append({"type": "text", "content": line})
                tokens.append({"type": "pause", "duration": "10 seconds"})
                used.add(line)
                break
        else:
            used.clear()
            shuffle(calm_prompts)
        if estimate_duration(tokens) >= target_minutes:
            break

    return tokens

def fallback_tokens(mood: str, duration: int = 15) -> List[Dict]:
    logging.warning("Using fallback script for mood '%s'", mood)
    mood_opening = {
        "tired": "Welcome... to your meditation session... I’m your guide today... You’ve carried so much — let’s gently lay it down together... This is your space to rest, to breathe, to soften...",
        "sadness": "Welcome... to your meditation session... I’m here with you... In this quiet space, we’ll hold your feelings with care. You don’t need to be strong right now — just present, just real...",
        "anxiety": "Welcome... to your meditation session... I’m your guide today... Let’s slow everything down. You’re safe here. Let your breath become your anchor... Feel the ground beneath you...",
        "stress": "Welcome... to your meditation session... I’m here to help you release the tension you’ve been carrying... Let’s begin by softening your shoulders, unclenching your jaw, and finding ease in your breath...",
        "calm": "Welcome... to your meditation session... I’m your guide today... Let’s deepen the stillness already within you... Feel the quiet expand with each breath..."
    }

    mood = mood if mood in mood_opening else "calm"

    base = [
        {"type": "text", "content": mood_opening[mood]},
        {"type": "pause", "duration": "5 seconds"},
        {"type": "text", "content": "Find a quiet space... Sit or lie down comfortably... Close your eyes... for 30 seconds..."},
        {"type": "pause", "duration": "30 seconds"},
        {"type": "text", "content": "Take a slow breath in through your nose... and exhale softly through your mouth... for one minutes..."},
        {"type": "pause", "duration": "60 seconds"},
        {"type": "text", "content": "Let your body settle... and your breath guide you... for 30 seconds..."},
        {"type": "pause", "duration": "30 seconds"},
        {"type": "text", "content": "Feel the tension gently melting away...    for 30 seconds..."},
        {"type": "pause", "duration": "30 seconds"},
        {"type": "text", "content": "Now, stay here in peaceful silence... simply breathing... for 2 minutes..."},
        {"type": "pause", "duration": "2 minutes"},
    ]

    padded = pad_tokens_to_duration(base, duration)
    padded.extend([
        {"type": "pause", "duration": "15 seconds"},
        {"type": "text", "content": "Now take a deep breath... and gently return to the present moment..."},
        {"type": "pause", "duration": "15 seconds"},
        {"type": "text", "content": "Thank yourself... for this time of calm and care..."},
        {"type": "pause", "duration": "10 seconds"},
        {"type": "text", "content": "Your session has now gently come to an end..."},
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
        f"You are a professional meditation coach creating a 15-minute guided session for someone feeling '{mood}'. "
        "Your voice should be soft, slow, and melodious — ideal for deep relaxation and emotional comfort. "
        "Your tone must be warm, grounded, and emotionally attuned. "
        "Include breath cues, natural pauses, and gentle transitions. "
        "End with: 'Now take a deep breath... and gently return to the present moment...' "
        "Then close with: 'Your session has now gently come to an end.' "
        f"Here are their answers:\n{formatted_answers}\n"
        "Format the output strictly as a JSON array of tokens — no markdown, no commentary, no extra text."
    )

def generate_script(mood: str, answers: Dict[str, str]) -> List[Dict]:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is missing or not loaded")

    duration = 15
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
        tokens = json.loads(content)
        if not tokens or not isinstance(tokens, list):
            raise ValueError("Invalid token structure")

        if estimate_duration(tokens) < duration * 0.9:
            tokens = pad_tokens_to_duration(tokens, duration)

        return tokens

    except Exception as e:
        logging.error("GPT error or invalid response: %s", e)
        return fallback_tokens(mood, duration)