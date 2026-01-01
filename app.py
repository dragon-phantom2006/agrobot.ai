from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# ==============================
# Gemini API Setup
# ==============================
genai.configure(api_key=("AIzaSyCYNm6B6YjxoUi3rmDVNmRGMCFo4FlOEyU"))

model = genai.GenerativeModel("gemini-2.5-flash")
chat_session = model.start_chat(
    history=[
        {
            "role": "user",
            "parts": [
                "You are AGROBOAT, an agriculture assistant.\n"
                "Follow user instructions STRICTLY.\n"
                "If user asks for points, respond ONLY in numbered points.\n"
                "If user asks for a paragraph, respond ONLY in paragraph form.\n"
                "If user specifies an exact number of points, give EXACTLY that number.\n"
                "Do not mix formats."
            ]
        }
    ]
)

# ==============================
# Routes
# ==============================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")

    try:
        response = chat_session.send_message(user_message)
        return jsonify({"reply": response.text})
    except Exception as e:
        return jsonify({"reply": "❌ Error: " + str(e)}), 500

# ==============================
# Run Server
# ==============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)