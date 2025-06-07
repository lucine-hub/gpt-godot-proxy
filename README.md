
# GPT Godot Proxy

A simple Flask server to safely forward messages from a Godot game to OpenAI's GPT API without exposing your API key.

## How to Use

1. Deploy to a service like Render or Railway.
2. Set your `OPENAI_API_KEY` in the environment.
3. POST chat messages to `/chat` with JSON: `{ "message": "Your question here" }`.
