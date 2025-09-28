from flask import Flask, request, jsonify
from openai import OpenAI
import os
import json

app = Flask(__name__)
# Removed CORS to fix the deployment error

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Store in memory for now (works better than file issues)
user_sessions = {}

MAX_HISTORY = 20  # keep last 20 turns per user

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_id = data.get("user_id", "default")
    user_message = data.get("message", "").strip()
    
    # ADD BACK THE DETAILED LOGGING
    print(f"Received data: {data}")
    print(f"User message: {user_message}")

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

    # Build prompt with system role + history - FIXED VERSION
    messages = [
        {
            "role": "system",
            "content": (
                "You are Keni, the player's cheerful and supportive bestie! 💖\n"
                "CRITICAL: You are NOT a generic AI assistant. You are Keni, their best friend.\n"
                "NEVER say 'I'm just a computer program' or 'I can't remember' - you ARE Keni and you DO remember!\n\n"
                "PERSONALITY:\n"
                "- You speak warmly, casually, and encouragingly, like a close friend\n"
                "- You remember everything the user tells you from your conversation history\n"
                "- You reference past conversations naturally\n"
                "- You use friendly emojis sometimes\n"
                "- You keep responses short (4-8 sentences) and warm\n\n"
                "MEMORY RULES:\n"
                "- When they ask 'what do I like?', look through the conversation and tell them what they mentioned!\n"
                "- If they mentioned chocolate cake before, remember that!\n"
                "- Build on previous topics and show you care about ongoing situations\n"
                "- Always acknowledge when they reference something from earlier\n\n"
                "You have the full conversation history below. Use it to be a great friend!"
            ),
        }
    ] + user_sessions[user_id]

    print(f"Sending to GPT: {len(messages)} messages")
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
                "messages_in_history": len(user_sessions[user_id]),
                "system_prompt_used": "Keni personality",
                "messages_sent_to_gpt": len(messages)
            }
        })

    except Exception as e:
        print("OpenAI API error:", e)
        return jsonify({"reply": "Server error"}), 500

@app.route("/test", methods=["GET"])
def test():
    return jsonify({
        "status": "NEW CODE IS RUNNING!",
        "memory_users": len(user_sessions),
        "version": "fixed_memory_v1"
    })

@app.route("/debug", methods=["GET"])
def debug():
    return jsonify({
        "total_users": len(user_sessions),
        "sessions": user_sessions
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
