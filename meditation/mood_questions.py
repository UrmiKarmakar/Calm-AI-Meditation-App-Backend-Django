from typing import List, Dict

def get_questions(mood: str) -> List[Dict[str, List[str]]]:
    mood = mood.lower()

    if mood == "calm":
        return [
            {
                "question": "What helps you feel calm and centered?",
                "options": ["Breathing", "Nature", "Music", "Silence"]
            },
            {
                "question": "Are there places or people that bring you peace?",
                "options": ["Home", "Friends", "Forest", "Beach"]
            },
            {
                "question": "How does calmness feel in your body?",
                "options": ["Light", "Warm", "Still", "Soft"]
            },
            {
                "question": "What thoughts help you stay grounded?",
                "options": ["Gratitude", "Presence", "Hope", "Faith"]
            },
            {
                "question": "What would deepen your sense of calm today?",
                "options": ["Rest", "Meditation", "Connection", "Solitude"]
            }
        ]

    elif mood == "anxiety":
        return [
            {
                "question": "What usually triggers your anxiety?",
                "options": ["Uncertainty", "Crowds", "Deadlines", "Conflict"]
            },
            {
                "question": "What helps you feel safe?",
                "options": ["Routine", "Support", "Quiet", "Breathing"]
            },
            {
                "question": "Where do you feel anxiety in your body?",
                "options": ["Chest", "Stomach", "Head", "Hands"]
            },
            {
                "question": "What helps you release tension?",
                "options": ["Movement", "Music", "Talking", "Stillness"]
            },
            {
                "question": "What thought brings you comfort?",
                "options": ["I am safe", "This will pass", "I am strong", "I am loved"]
            }
        ]

    elif mood == "tired":
        return [
            {
                "question": "What’s making you feel tired today?",
                "options": ["Work", "Emotions", "Lack of sleep", "Overthinking"]
            },
            {
                "question": "What helps you recharge?",
                "options": ["Sleep", "Nature", "Silence", "Laughter"]
            },
            {
                "question": "What does your body need right now?",
                "options": ["Rest", "Stretching", "Hydration", "Stillness"]
            },
            {
                "question": "What kind of rest feels most nourishing?",
                "options": ["Physical", "Mental", "Emotional", "Spiritual"]
            },
            {
                "question": "What’s one gentle thing you can do for yourself?",
                "options": ["Lie down", "Take a walk", "Listen to music", "Say no"]
            }
        ]

    elif mood == "stress":
        return [
            {
                "question": "What’s causing stress today?",
                "options": ["Deadlines", "Relationships", "Health", "Uncertainty"]
            },
            {
                "question": "What helps you release stress?",
                "options": ["Breathing", "Movement", "Talking", "Silence"]
            },
            {
                "question": "Where do you feel stress in your body?",
                "options": ["Neck", "Back", "Chest", "Jaw"]
            },
            {
                "question": "What helps you feel in control?",
                "options": ["Planning", "Support", "Rest", "Letting go"]
            },
            {
                "question": "What’s one thing you can let go of?",
                "options": ["Perfection", "Pressure", "Overthinking", "Control"]
            }
        ]

    elif mood == "sadness":
        return [
            {
                "question": "What’s making you feel sad?",
                "options": ["Loss", "Loneliness", "Disappointment", "Uncertainty"]
            },
            {
                "question": "What helps you feel comforted?",
                "options": ["Music", "Connection", "Nature", "Rest"]
            },
            {
                "question": "What does your heart need right now?",
                "options": ["Compassion", "Stillness", "Expression", "Support"]
            },
            {
                "question": "What helps you express your emotions?",
                "options": ["Writing", "Talking", "Crying", "Art"]
            },
            {
                "question": "What’s one kind thing you can say to yourself?",
                "options": ["I’m doing my best", "I’m allowed to feel", "I’m healing", "I’m not alone"]
            }
        ]

    else:
        return []