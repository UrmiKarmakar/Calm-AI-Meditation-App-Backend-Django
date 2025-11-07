import os
import json
import openai
import logging
from dotenv import load_dotenv
from random import choice
from typing import List, Dict
from random import shuffle

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

logging.basicConfig(level=logging.INFO)

def format_system_prompt() -> str:
    return (
        "You are an expert guided meditation writer. Output exactly one JSON array of tokens.\n"
        "Each token must be either:\n"
        "- {\"type\":\"text\",\"content\":\"...\"}\n"
        "- {\"type\":\"pause\",\"duration\":\"<N> seconds\"} or {\"type\":\"pause\",\"duration\":\"<N> minutes\"}\n"
        "Use varied pause durations based on emotional pacing — longer pauses for reflection, shorter for transitions.\n"
        "Only output the JSON array. No explanation, no formatting, no markdown."
    )

def estimate_duration(tokens: List[Dict]) -> float:
    total_ms = 0
    for t in tokens:
        if t["type"] == "pause":
            try:
                value = float(t["duration"].split()[0])
                total_ms += value * (60000 if "minute" in t["duration"] else 1000)
            except:
                continue
        elif t["type"] == "text":
            total_ms += len(t["content"].split()) * 500
    return total_ms / 60000

def pad_tokens_to_duration(tokens: List[Dict], target_minutes: int) -> List[Dict]:
    calm_prompts = [
    # Instructional cues
        "Now take a moment to feel your breath moving through your body.",
        "Let your shoulders drop. Let your jaw soften.",
        "Picture yourself in a peaceful forest. Hear the leaves rustling.",
        "Feel the ground beneath you. Let it hold you.",
        "Notice any tension in your body. Gently release it.",
        "Let your thoughts pass like clouds in the sky.",
        "Now imagine a warm light filling your chest.",
        "Let that light expand with each breath.",
        "You are doing a 2-minute meditation right now. Just be here.",
        "Let yourself be still. Let yourself be quiet.",
        "Feel your body becoming lighter with each breath.",
        "Let your breath guide you deeper into calm.",
        "You don’t need to do anything. Just be.",

        # Affirmations
        "You are safe and supported.",
        "Let your breath guide you to stillness.",
        "You are present. You are calm. You are whole.",
        "Thank yourself for this moment of peace.",
        "Let your thoughts drift like clouds.",
        "Feel your body becoming lighter.",
        "You are grounded and calm.",
        "Picture a warm light surrounding you.",
        "Let this light fill your body with ease.",
        "You are enough."
]
    used = set()
    shuffle(calm_prompts)

    while estimate_duration(tokens) < target_minutes:
        for line in calm_prompts:
            if line not in used:
                tokens.append({"type": "pause", "duration": "15 seconds"})
                tokens.append({"type": "text", "content": line})
                used.add(line)
                break
        else:
            used.clear()
            shuffle(calm_prompts)

    return tokens

def fallback_tokens(mood: str, duration: int = 15) -> List[Dict]:
    logging.warning("Using fallback script for mood '%s' and duration %d", mood, duration)

    mood_opening = {
        "tired": "Welcome to your meditation session... I’m your guide today. You’ve carried so much — let’s gently lay it down together. This is your space to rest, to breathe, to soften.",
        "sadness": "Welcome to your meditation session... I’m here with you. In this quiet space, we’ll hold your feelings with care. You don’t need to be strong right now — just present, just real.",
        "anxiety": "Welcome to your meditation session... I’m your guide today. Let’s slow everything down. You’re safe here. Let your breath become your anchor.",
        "stress": "Welcome to your meditation session... I’m here to help you release the tension you’ve been carrying. Let’s begin by softening your shoulders, unclenching your jaw, and finding ease in your breath.",
        "calm": "Welcome to your meditation session... I’m your guide today. Let’s deepen the stillness already within you. Feel the quiet expand with each breath."
    }

    base = [
        {"type": "text", "content": mood_opening.get(mood, "Welcome to your meditation session... I'm your guide today. Let's begin by settling into this moment together.")},
        {"type": "pause", "duration": "8 seconds"},
        {"type": "text", "content": "Find a quiet space. Sit or lie down comfortably. Close your eyes."},
        {"type": "pause", "duration": "15 seconds"},
    ]

    if mood == "sadness":
        base.extend([
            {"type": "text", "content": "Sadness is not weakness. It's a signal. A whisper from within."},
            {"type": "pause", "duration": "15 seconds"},
            {"type": "text", "content": "You don't have to fix anything right now."},
            {"type": "pause", "duration": "15 seconds"},
        ])
    elif mood == "tired":
        base.extend([
            {"type": "text", "content": "Take a slow breath in... and out."},
            {"type": "pause", "duration": "10 seconds"},
            {"type": "text", "content": "Let your body sink into stillness."},
            {"type": "pause", "duration": "15 seconds"},
            {"type": "text", "content": "You’ve carried a lot today. It’s okay to rest."},
            {"type": "pause", "duration": "15 seconds"},
        ])
    elif mood == "anxiety":
        base.extend([
            {"type": "text", "content": "Let your breath slow down. Inhale... and exhale."},
            {"type": "pause", "duration": "10 seconds"},
            {"type": "text", "content": "You are safe in this moment."},
            {"type": "pause", "duration": "15 seconds"},
        ])
    elif mood == "stress":
        base.extend([
            {"type": "text", "content": "Let go of the tension you've been holding."},
            {"type": "pause", "duration": "15 seconds"},
            {"type": "text", "content": "You don’t need to carry everything at once."},
            {"type": "pause", "duration": "15 seconds"},
        ])
    elif mood == "calm":
        base.extend([
            {"type": "text", "content": "Feel the calm within you expanding."},
            {"type": "pause", "duration": "15 seconds"},
            {"type": "text", "content": "Let your breath move like waves — steady and smooth."},
            {"type": "pause", "duration": "15 seconds"},
        ])

    padded = pad_tokens_to_duration(base, duration)
    padded.extend([
        {"type": "pause", "duration": "10 seconds"},
        {"type": "text", "content": "Now take a deep breath... and gently return to the present moment."},
        {"type": "pause", "duration": "10 seconds"},
        {"type": "text", "content": "Thank yourself for this time of calm and care."},
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
        f"You are a professional meditation coach creating a 15-minute guided session for someone feeling '{mood}'. "
        "Your tone should be warm, grounded, and emotionally attuned. "
        "Begin with a gentle welcome and introduce yourself as their meditation guide today. Let's begin with a slow breath in... and out. Voice flow will be slow and calm. "
        "Invite the listener to settle in: find a quiet space, sit or lie comfortably, and close their eyes. "
        f"Do not include language or affirmations related to other moods. Stay focused on the emotional tone of {mood} — {mood_descriptions.get(mood, 'gentle presence and breath awareness')}. "
        "Then transition into the meditation, using slow-paced, calming language. "
        "Incorporate breath cues and body awareness prompts to deepen relaxation. "
        "Use varied pause durations based on emotional pacing — longer pauses for reflection, shorter for transitions. "
        "Avoid repeating affirmations more than twice. Each should feel fresh and intentional. "
        "Use silence as a tool for healing. Let the listener reflect and breathe between phrases. "
        "Ensure the final audio reaches at least 15 minutes, balancing spoken content and pauses. "
        "End with: 'Now take a deep breath... and gently return to the present moment.' "
        "Then close with: 'Your session has now gently come to an end.' "
        f"Here are their answers:\n{formatted_answers}\nFormat the output as a JSON array of tokens only..."
    )

def generate_script(mood: str, answers: Dict[str, str]) -> List[Dict]:
    duration = 15
    logging.info("Requested mood: %s", mood)
    formatted_answers = "\n".join([f"{q}: {a}" for q, a in answers.items()])
    prompt = mood_prompt(mood, formatted_answers)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": format_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        content = response.choices[0].message.content.strip()
        logging.info("GPT Script:\n%s", content)

        tokens = json.loads(content)
        logging.info("Token count: %d", len(tokens))

        if not tokens or not isinstance(tokens, list):
            raise ValueError("GPT returned empty or invalid token list")

        actual_duration = estimate_duration(tokens)
        logging.info(f"Estimated duration before padding: {actual_duration:.2f} minutes")

        if actual_duration < duration * 0.9:
            tokens = pad_tokens_to_duration(tokens, duration)
            logging.info(f"Padded to duration: {estimate_duration(tokens):.2f} minutes")

        return tokens

    except Exception as e:
        logging.warning("GPT error or fallback triggered for mood '%s': %s", mood, e)
        return fallback_tokens(mood, duration)
