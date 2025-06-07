from flask import Flask, request, jsonify
import openai
import os
import traceback

app = Flask(__name__)

# 🔑 Replace this with your own OpenAI API key if not using environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/")
def home():
    return "✅ GPT Chat Server is running!"

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        print("Received data:", data)

        user_message = data.get("message", "")
        print("User message:", user_message)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )

        reply = response.choices[0].message.content.strip()
        print("GPT reply:", reply)

        return jsonify({"reply": reply})

    except Exception as e:
        print("❌ Error in /chat route:")
        traceback.print_exc()
        return jsonify({"reply": "Server error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
