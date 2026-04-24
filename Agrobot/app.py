from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai
import requests
import os
from flask_sqlalchemy import SQLAlchemy
from PIL import Image
import time

app = Flask(__name__)
app.secret_key = "agroboat_secret"

# ======================
# MULTI API KEY SYSTEM
# ======================
API_KEYS = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
]

current_key_index = 0

def get_model():
    global current_key_index
    genai.configure(api_key=API_KEYS[current_key_index])
    return genai.GenerativeModel("gemini-1.5-flash")

WEATHER_KEY = os.getenv("WEATHER_KEY")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///farmers.db"
db = SQLAlchemy(app)

# ======================
# DATABASE MODEL
# ======================
class Farmer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    crop = db.Column(db.String(50))
    soil = db.Column(db.String(50))

# ======================
# SAFE AI FUNCTION (ROTATING KEYS)
# ======================
def safe_generate(prompt):
    global current_key_index

    for _ in range(len(API_KEYS)):
        try:
            model = get_model()
            response = model.generate_content(prompt)
            return response.text

        except Exception as e:
            print("AI ERROR:", e)

            # 🔁 Switch API key
            current_key_index = (current_key_index + 1) % len(API_KEYS)
            time.sleep(1)

    return "⚠ AI service temporarily unavailable. Please try again later."

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
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_KEY}&units=metric"
        res = requests.get(url, timeout=5).json()

        if "main" not in res:
            return "Weather unavailable"

        temp = res["main"]["temp"]
        desc = res["weather"][0]["description"]

        return f"Weather in {city}: {temp}°C, {desc}\n{advisory_engine(desc)}"
    except Exception as e:
        print("WEATHER ERROR:", e)
        return "⚠ Weather service unavailable"

def get_weather_by_coords(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_KEY}&units=metric"
        res = requests.get(url, timeout=5).json()

        if "main" not in res:
            return "Weather unavailable"

        temp = res["main"]["temp"]
        desc = res["weather"][0]["description"]

        return f"Temp: {temp}°C | {desc}\n{advisory_engine(desc)}"
    except:
        return "⚠ Weather service unavailable"

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

def extract_crop(msg):
    crops = ["rice", "wheat", "maize"]
    for c in crops:
        if c in msg:
            return c
    return None

# ======================
# GOVERNMENT SCHEMES
# ======================
def government_schemes():
    return """📜 Government Schemes:
• PM-KISAN: ₹6000/year support
• Soil Health Card Scheme
• PMFBY (Crop Insurance)
• Kisan Credit Card

Visit nearest agriculture office for full details."""

def search_disease(symptoms):
    try:
        query = f"plant leaf disease {symptoms}"

        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {
            "Ocp-Apim-Subscription-Key": os.getenv("BING_KEY")
        }
        params = {"q": query}

        res = requests.get(url, headers=headers, params=params, timeout=5).json()
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
    try:
        data = request.get_json()
        msg = data.get("message", "").lower()

        crop = extract_crop(msg)

        if "weather" in msg:
            return jsonify({"reply": get_weather()})

        if "fertilizer" in msg:
            if not crop:
                return jsonify({"reply": "🌾 Please specify crop (rice, wheat, maize)."})
            return jsonify({"reply": fertilizer_advice(crop)})

        if "calendar" in msg or "crop" in msg:
            if not crop:
                return jsonify({"reply": "🌾 Please specify crop."})
            return jsonify({"reply": crop_calendar(crop)})

        if "scheme" in msg or "government" in msg:
            return jsonify({"reply": government_schemes()})

        reply = safe_generate(msg)
        return jsonify({"reply": reply})

    except Exception as e:
        print("CHAT ERROR:", e)
        return jsonify({"reply": "⚠ Server issue. Try again."})

@app.route("/weather_coords", methods=["POST"])
def weather_coords():
    data = request.get_json()
    return jsonify({"reply": get_weather_by_coords(data["lat"], data["lon"])})

@app.route("/detect_disease", methods=["POST"])
def detect_disease():
    try:
        file = request.files.get("image")
        if not file:
            return jsonify({"reply": "No image uploaded."})

        img = Image.open(file).convert("RGB")

        symptom_prompt = "List 3–5 visible plant leaf symptoms."

        symptoms = safe_generate([symptom_prompt, img])
        disease = search_disease(symptoms)

        final_prompt = f"""
        Symptoms: {symptoms}
        Disease: {disease}
        Give cause, treatment, prevention simply.
        """

        reply = safe_generate(final_prompt)

        return jsonify({
            "symptoms": symptoms,
            "disease": disease,
            "reply": reply
        })

    except Exception as e:
        print("IMAGE ERROR:", e)
        return jsonify({"reply": "⚠ Image processing failed."})

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

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
