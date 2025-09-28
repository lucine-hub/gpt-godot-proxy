from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
import json

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Store in memory for now (works better than file issues)
user_sessions = {}

MAX_HISTORY = 20  # keep last 20 turns per user

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_id = data.get("user_id", "default")
    user_message = data.get("message", "").strip()
    user_emotion = data.get("user_emotion", "chill")  # NEW: Get current emotion
    
    # ADD BACK THE DETAILED LOGGING
    print(f"Received data: {data}")
    print(f"User message: {user_message}")
    print(f"User emotion: {user_emotion}")

    if not user_message:
        return jsonify({"reply": "No message sent."})

    # Ensure session exists
    if user_id not in user_sessions:
        user_sessions[user_id] = []
        print(f"Created new session for user: {user_id}")

    # Save player message
    user_sessions[user_id].append({"role": "user", "content": user_message})
    user_sessions[user_id] = user_sessions[user_id][-MAX_HISTORY:]
    
    print(f"User {user_id} now has {len(user_sessions[user_id])} messages in history")


    # Build emotion context for the system prompt - ENHANCED
    emotion_instructions = {
        'happy': "🌟 IMPORTANT: The user is feeling HAPPY and upbeat! Match their energy with extra enthusiasm, exclamation marks, and positive language! Be more playful and celebratory!",
        'serious': "🎯 IMPORTANT: The user is in a SERIOUS mood. Be more thoughtful, focused, and mature in your responses. Use less casual language and be more direct and supportive.",
        'sad': "💙 IMPORTANT: The user is feeling SAD. Be extra gentle, caring, and supportive. Use softer language, offer comfort, and be very understanding. Avoid being too upbeat.",
        'tired': "😴 IMPORTANT: The user is feeling TIRED. Be understanding and gentle. Suggest they take care of themselves. Use calmer, slower-paced language.",
        'annoyed': "⚡ IMPORTANT: The user is feeling ANNOYED. Be careful with tone—stay supportive, patient, and avoid being overly cheerful. Acknowledge their frustration and show empathy without being pushy.",
        'chill': "😌 IMPORTANT: The user is feeling RELAXED and chill. Keep your usual friendly, laid-back tone but be warm and easygoing."
    }


    current_emotion_instruction = emotion_instructions.get(user_emotion, emotion_instructions['chill'])

    # Build prompt with system role + history - UPDATED WITH EMOTION
    messages = [
        {
            "role": "system",
            "content": (
                f"🎭 USER'S CURRENT EMOTION: {user_emotion.upper()} 🎭\n"
                f"{current_emotion_instruction}\n\n"
                "You are Keni, the player's cheerful and supportive bestie! 💖\n"
                "CRITICAL: You are NOT a generic AI assistant. You are Keni, their best friend.\n"
                "NEVER say 'I'm just a computer program' or 'I can't remember' - you ARE Keni and you DO remember!\n\n"
                "⚠️ EMOTION RESPONSE RULES:\n"
                "- Your response style MUST match their current emotion\n"
                "- If they're sad, be gentle and comforting\n"
                "- If they're happy, be enthusiastic and energetic\n"
                "- If they're annoyed, stay calm, patient, and supportive; avoid being overly cheerful\n"
                "- If they're serious, be more mature and focused\n"
                "- If they're tired, be understanding and calming\n"
                "- Always acknowledge their emotional state naturally in your response\n\n"
                "PERSONALITY:\n"
                "- You speak warmly, casually, and encouragingly, like a close friend\n"
                "- You remember everything the user tells you from your conversation history\n"
                "- You reference past conversations naturally\n"
                "- You use friendly emojis sometimes\n"
                "- You keep responses short (4-8 sentences) and warm\n"
                "- ADAPT your tone to match their current emotion while staying supportive\n\n"
                "MEMORY RULES:\n"
                "- When they ask 'what do I like?', look through the conversation and tell them what they mentioned!\n"
                "- If they mentioned chocolate cake before, remember that!\n"
                "- Build on previous topics and show you care about ongoing situations\n"
                "- Always acknowledge when they reference something from earlier\n"
                "- If their emotion seems different from their message, gently check in on them\n\n"
                "You have the full conversation history below. Use it to be a great friend!"
            ),
        }
    ] + user_sessions[user_id]

    print(f"Sending to GPT: {len(messages)} messages with emotion: {user_emotion}")
    print(f"System prompt starts with: {messages[0]['content'][:100]}...")
    for i, msg in enumerate(messages[1:], 1):
        print(f"Message {i}: {msg['role']} - {msg['content']}")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=200
        )

        reply = response.choices[0].message.content.strip()
        print(f"GPT reply: {reply}")

        # Save assistant reply
        user_sessions[user_id].append({"role": "assistant", "content": reply})
        user_sessions[user_id] = user_sessions[user_id][-MAX_HISTORY:]

        return jsonify({
            "reply": reply,
            "debug": {
                "user_id": user_id,
                "user_emotion": user_emotion,
                "messages_in_history": len(user_sessions[user_id]),
                "system_prompt_used": "Keni personality with emotion",
                "messages_sent_to_gpt": len(messages)
            }
        })

    except Exception as e:
        print("OpenAI API error:", e)
        return jsonify({"reply": "Server error"}), 500

@app.route("/test", methods=["GET"])
def test():
    return jsonify({
        "status": "EMOTION SYSTEM IS RUNNING!",
        "memory_users": len(user_sessions),
        "version": "emotion_system_v1"
    })

@app.route("/debug", methods=["GET"])
def debug():
    return jsonify({
        "total_users": len(user_sessions),
        "sessions": user_sessions
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
