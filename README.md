# 🧘 Calm AI — Emotionally Tuned Meditation Generator
Calm AI is a modular, AI-powered meditation backend built with Django. It generates personalized meditation sessions by combining natural language generation, expressive voice synthesis, and ambient sound mixing. Designed for mobile integration, Calm AI delivers immersive, emotionally resonant audio experiences tailored to the user's mood and intention.

At its core, Calm AI takes a user’s emotional state (like stress, sadness, or calm), a preferred voice (male or female), a background ambiance (like forest or rain), and a few words about how they’re feeling. It then generates a guided meditation script using OpenAI’s language model, converts that script into a soothing voice using ElevenLabs, and overlays it with ambient audio using Pydub. The result is a high-quality .mp3 file that can be streamed or downloaded by a mobile app.

The system is built with modularity in mind. The meditation app contains three key components:

script_generator.py: Uses OpenAI to generate a meditation script based on the user's mood and input.

tts_engine.py: Converts the script into voice using ElevenLabs, handling pauses and emotional tone.

mixer.py: Mixes the voice with a looping background sound (e.g., forest, rain) to create a calming atmosphere.

The Django backend exposes a single API endpoint: POST /api/generate/. This endpoint accepts a JSON payload with the user's mood, voice preference, background sound, and a short description of their current feelings. It returns a JSON response containing the path to the generated audio file and the structured script used to create it.

All generated sessions are saved in meditation/output/, and background audio files are stored in static/backgrounds/. The project uses .env for secure API key management, and the architecture is designed to be easily extendable — you can plug in new voices, moods, or background types with minimal changes.

Calm AI is ideal for wellness apps, mental health tools, or any product that aims to deliver personalized, emotionally intelligent audio experiences. It’s built for clarity, control, and comfort — both for developers and end users.

For Testing: 
    python manage.py runserver

In Postman:
Post:  http://127.0.0.1:8000/api/generate/
In Body :
{
  "mood": "sadness",
  "voice": "male",
  "background": "ocean",
  "answers": {
    "What’s making you feel sad?": "Loneliness",
    "What helps you feel comforted?": "Connection",
    "What does your heart need right now?": "Compassion",
    "What helps you express your emotions?": "Crying",
    "What’s one kind thing you can say to yourself?": "I’m allowed to feel"
  }
}
