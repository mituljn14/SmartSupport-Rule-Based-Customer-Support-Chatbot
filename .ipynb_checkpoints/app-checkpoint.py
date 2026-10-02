"""
app.py
------
Flask web server for SmartSupport.

Responsibilities:
  - Serve the chatbot web UI (GET /)
  - Handle chat messages via the API (POST /chat)
  - Clear conversation history (POST /clear)
  - Store per-visitor conversation history in a Flask session

All chatbot "intelligence" lives in chatbot.py — this file only deals with
the web server, routing and session/state management.
"""

from datetime import datetime

from flask import Flask, render_template, request, jsonify, session

from chatbot import get_bot_reply

app = Flask(__name__)

# NOTE: in a real deployment, set this via an environment variable instead.
app.secret_key = "smartsupport-dev-secret-key-change-me"


def _now() -> str:
    """Simple HH:MM timestamp string for chat messages."""
    return datetime.now().strftime("%H:%M")


@app.route("/")
def index():
    """Render the chatbot web UI."""
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """
    Receive a user message, run it through the rule-based chatbot, store the
    exchange in the session's conversation history, and return the response.

    Request JSON:  {"message": "Where is my order?"}
    Response JSON: {"response": "...", "intent": "order_status"}
    """
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"response": "Please type a message so I can help you!",
                         "intent": "unknown"})

    # Keep conversation history in the session (list of dicts)
    history = session.get("history", [])
    last_intent = session.get("last_intent")

    response_text, intent = get_bot_reply(user_message, last_intent=last_intent)

    history.append({
        "user": user_message,
        "bot": response_text,
        "intent": intent,          # kept internally; NOT shown to the end user in the UI
        "time": _now(),
    })

    # Keep the history from growing unbounded in a long session
    session["history"] = history[-50:]
    session["last_intent"] = intent
    session.modified = True

    # We do return the intent in the API response (useful for debugging /
    # the quick-action buttons), but the frontend does not display it to users.
    return jsonify({"response": response_text, "intent": intent})


@app.route("/clear", methods=["POST"])
def clear():
    """Clear the current conversation history and context."""
    session.pop("history", None)
    session.pop("last_intent", None)
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    app.run(debug=True)
