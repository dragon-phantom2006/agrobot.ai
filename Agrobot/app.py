from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai
import requests
import os
from flask_sqlalchemy import SQLAlchemy
from PIL import Image

app = Flask(__name__)
app.secret_key = "agroboat_secret"

# ======================
# CONFIG
# ======================
import os
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
WEATHER_KEY = os.getenv("WEATHER_KEY")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///farmers.db"
db = SQLAlchemy(app)

model = genai.GenerativeModel("gemini-2.5-flash")
chat_session = model.start_chat(history=[])

# ======================
# DATABASE MODEL
# ======================
class Farmer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    crop = db.Column(db.String(50))
    soil = db.Column(db.String(50))

# ======================
# WEATHER FUNCTIONS
# ======================
def advisory_engine(desc):
    if "rain" in desc:
        return "⚠ Rain expected — delay fertilizer application."
    if "clear" in desc:
        return "Good time for irrigation."
    return ""

def get_weather(city="Kolkata,IN"):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_KEY}&units=metric"
    res = requests.get(url).json()

    if "main" not in res:
        return "Weather unavailable"

    temp = res["main"]["temp"]
    desc = res["weather"][0]["description"]

    return f"Weather in {city}: {temp}°C, {desc}\n{advisory_engine(desc)}"

def get_weather_by_coords(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_KEY}&units=metric"
    res = requests.get(url).json()

    if "main" not in res:
        return "Weather unavailable"

    temp = res["main"]["temp"]
    desc = res["weather"][0]["description"]

    return f"Temp: {temp}°C | {desc}\n{advisory_engine(desc)}"


# ======================
# AGRICULTURE FEATURES
# ======================
def crop_calendar(crop):
    calendars = {
        "rice": "Rice: Sowing Jun–Jul | Harvest Oct–Nov",
        "wheat": "Wheat: Sowing Oct–Nov | Harvest Mar–Apr",
        "maize": "Maize: Sowing Jun–Jul | Harvest Sep–Oct"
    }
    return calendars.get(crop.lower(), "Calendar unavailable.")

def fertilizer_advice(crop):
    rules = {
        "rice": "Use NPK 10:26:26 — 50kg/acre",
        "wheat": "Use Urea + DAP combination",
        "maize": "Apply nitrogen-rich fertilizer"
    }
    return rules.get(crop.lower(), "No fertilizer data.")
def search_disease(symptoms):
    query = f"plant leaf disease {symptoms}"

    url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {
        "Ocp-Apim-Subscription-Key": "2b10iDH1eRqn3cZW7I6LXRwYcu"
    }
    params = {"q": query}

    try:
        res = requests.get(url, headers=headers, params=params).json()

        results = res.get("webPages", {}).get("value", [])

        for r in results:
            title = r["name"].lower()

            if "blight" in title:
                return "Blight Disease"
            if "leaf spot" in title:
                return "Leaf Spot Disease"
            if "rust" in title:
                return "Rust Disease"

        return "Leaf Disease"

    except:
        return "Unknown Disease"

# ======================
# ROUTES
# ======================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    msg = data["message"].lower()

    if "rice" in msg:
        session["crop"] = "rice"
    if "wheat" in msg:
        session["crop"] = "wheat"

    if "weather" in msg:
        return jsonify({"reply": get_weather()})

    if "calendar" in msg and "crop" in session:
        return jsonify({"reply": crop_calendar(session["crop"])})

    if "fertilizer" in msg and "crop" in session:
        return jsonify({"reply": fertilizer_advice(session["crop"])})

    response = chat_session.send_message(msg)
    return jsonify({"reply": response.text})

@app.route("/weather_coords", methods=["POST"])
def weather_coords():
    data = request.get_json()
    return jsonify({"reply": get_weather_by_coords(data["lat"], data["lon"])})

@app.route("/detect_disease", methods=["POST"])
def detect_disease():
    try:
        file = request.files["image"]
        img = Image.open(file).convert("RGB")

        # STEP 1: Extract symptoms using Gemini
        symptom_prompt = """
        Look at this plant leaf image and list only visible symptoms.
        Example:
        - brown spots
        - yellow edges
        - holes
        - white powder

        Give only 3-5 short symptom phrases.
        """

        symptom_response = model.generate_content([symptom_prompt, img])
        symptoms = symptom_response.text.strip()

        # STEP 2: Search disease using symptoms
        disease = search_disease(symptoms)

        # STEP 3: Get treatment from chatbot
        final_prompt = f"""
        A plant has the following symptoms:
        {symptoms}

        The most likely disease is: {disease}

        Explain:
        - Disease name
        - Cause
        - Treatment
        - Prevention

        Keep it simple for farmers.
        """

        final_response = model.generate_content(final_prompt)

        return jsonify({
            "symptoms": symptoms,
            "disease": disease,
            "reply": final_response.text
        })

    except Exception as e:
        print("IMAGE ERROR:", e)
        return jsonify({"reply": f"Error: {str(e)}"})
@app.route("/save_profile", methods=["POST"])
def save_profile():
    data = request.get_json()

    farmer = Farmer(
        name=data["name"],
        crop=data["crop"],
        soil=data["soil"]
    )

    db.session.add(farmer)
    db.session.commit()

    return jsonify({"reply": "Profile saved!"})

# ======================
# RUN
# ======================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
