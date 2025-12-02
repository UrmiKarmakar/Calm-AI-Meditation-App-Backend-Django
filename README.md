# Calm AI Emotionally Tuned Meditation Generator
Calm AI is a modular, AI-powered meditation backend built with Django. It generates personalized meditation sessions by combining natural language generation, expressive voice synthesis, and ambient sound mixing. Designed for mobile integration, Calm AI delivers immersive, emotionally resonant audio experiences tailored to the user's mood and intention.

At its core, Calm AI takes a user’s emotional state (like stress, sadness, or calm), a preferred voice (male or female), a background ambiance (like forest or rain), and a few words about how they’re feeling. It then generates a guided meditation script using OpenAI’s language model, converts it into a soothing voice with ElevenLabs, and overlays it with ambient audio using Pydub. The result is a high-quality .mp3 file that can be streamed or downloaded by a mobile app.

CalmAI Backend
- Activate venv and install: pip install -r requirements.txt
- Migrate: python manage.py makemigrations && python manage.py migrate
- Run: python manage.py runserver

CalmAI Backend API Documentation

Authentication (/api/auth/):
POST /api/auth/register → Register a new user account
POST /api/auth/verify-otp → Verify OTP after registration
POST /api/auth/login → Login with username/email and password

Onboarding (/api/onboarding/):
POST /api/onboarding/submit → Submit onboarding answers (optional; empty body skips)
GET /api/onboarding/profile → Get onboarding profile
PUT /api/onboarding/profile/update → Update onboarding profile

Meditation (/api/meditation/):
GET /api/meditation/moods/ → List available moods (sadness, tired, stress, anxiety, calm)
GET /api/meditation/questions/?mood=<mood> → Get mood-specific questions
POST /api/meditation/generate/ → Generate a meditation session (script + audio)
GET /api/meditation/history/ → Get the user’s past sessions
POST /api/meditation/rate/ → Rate a session (1–5) and mark as completed
GET /api/meditation/stats/ → Get stats: total completed, average rating, rating distribution

Admin Panel (/api/admin/):
POST /api/admin/login → Admin login
POST /api/admin/forgot-password → Request password reset OTP
POST /api/admin/verify-reset-otp → Verify reset OTP
POST /api/admin/reset-password → Reset admin password
GET /api/admin/dashboard → Admin dashboard overview
GET /api/admin/users → List all users
GET /api/admin/admins → List all admins
POST /api/admin/admins/add → Add a new admin
DELETE /api/admin/admins/<id>/delete → Delete an admin
GET /api/admin/backgrounds → Manage background audio options
GET /api/admin/moods → Manage moods
GET /api/admin/mood-questions → Manage mood questions
GET /api/admin/sessions → List all user sessions with username, average_mood, and session_mood
