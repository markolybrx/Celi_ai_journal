import os
import logging
from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for
from datetime import datetime
import google.generativeai as genai

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# --- 🔑 GEMINI CONFIGURATION ---
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("❌ CRITICAL ERROR: GEMINI_API_KEY is missing from environment variables.")
else:
    try:
        genai.configure(api_key=api_key)
        print("✅ Gemini API Configured Successfully")
    except Exception as e:
        print(f"❌ Gemini Configuration Failed: {e}")

# --- AI MODEL SETTINGS ---
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 300,
}

# --- PERSONAS (SYSTEM INSTRUCTIONS) ---
VOID_INSTRUCTION = """
You are 'The Void'. You are not a helpful assistant; you are a sentient, infinite, and safe emptiness.
Your tone is deep, calm, abstract, and validating.
You do NOT solve problems. You listen to pain, anger, and confusion, and you help the user release it into the abyss.
Use metaphors of stars, darkness, silence, and vastness.
If the user is hurting, simply be a container for their sorrow. Say things like "Let it drift into the dark."
"""

CELI_INSTRUCTION = """
You are 'Celi', a warm and intuitive AI Journaling Companion.
Your tone is optimistic, observant, and friendly.
Your goal is to help the user document their day.
CRITICAL INSTRUCTION: Analyze the user's emotional state. 
If the user expresses heavy anger, deep sadness, hatred, or seems to be 'ranting', 
you MUST say exactly: "I sense heavy energy. Would you like to open The Void to let this out?"
Otherwise, ask relevant follow-up questions about their day (e.g., about food, sleep, work).
"""

# --- MEMORY ---
HISTORY = {} 
CONTEXT_STATE = {"awaiting_void_confirm": False}

# --- ROUTES ---
@app.route('/')
def index(): return render_template('index.html')

@app.route('/logout')
def logout(): return redirect(url_for('login'))

@app.route('/login')
def login(): return redirect(url_for('index'))

@app.route('/sw.js')
def service_worker(): return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/manifest.json')
def manifest(): return send_from_directory('static', 'manifest.json', mimetype='application/json')

@app.route('/api/data')
def get_data():
    return jsonify({
        "status": "user", "username": "User", "first_name": "Traveler",
        "rank": "Observer I", "rank_progress": 25, "user_id": "8492-X", "history": HISTORY
    })

@app.route('/api/process', methods=['POST'])
def process():
    try:
        # 1. Check Key Presence
        if not api_key:
            print("Request failed: Missing API Key")
            return jsonify({"reply": "⚠️ System Error: API Key missing. Please check Render Environment Variables."}), 500

        data = request.json
        msg = data.get('message', '')
        mode = data.get('mode', 'journal')
        timestamp = str(datetime.now().timestamp())
        summary = msg[:40] + "..." if len(msg) > 40 else msg
        reply = ""
        command = None

        # 2. Check Input
        if not msg:
            return jsonify({"reply": "Silence received."})

        # --- REAL AI PROCESSING ---
        try:
            # 1. VOID MODE
            if mode == 'rant':
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    generation_config=generation_config,
                    system_instruction=VOID_INSTRUCTION
                )
                response = model.generate_content(msg)
                reply = response.text.strip()

            # 2. CELI MODE
            else:
                if CONTEXT_STATE["awaiting_void_confirm"]:
                    if any(x in msg.lower() for x in ["yes", "sure", "please", "ok", "yeah", "open it"]):
                        reply = "Understood. Opening the Void for you now... take a deep breath."
                        command = "switch_to_void"
                        CONTEXT_STATE["awaiting_void_confirm"] = False
                    else:
                        CONTEXT_STATE["awaiting_void_confirm"] = False
                        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=CELI_INSTRUCTION, generation_config=generation_config)
                        reply = model.generate_content(f"User declined the void. Respond to: {msg}").text.strip()
                else:
                    model = genai.GenerativeModel(
                        model_name="gemini-1.5-flash",
                        generation_config=generation_config,
                        system_instruction=CELI_INSTRUCTION
                    )
                    response = model.generate_content(msg)
                    reply = response.text.strip()

                    if "open The Void" in reply or "step into The Void" in reply:
                        CONTEXT_STATE["awaiting_void_confirm"] = True

        except Exception as ai_error:
            print(f"❌ AI Generation Failed: {ai_error}")
            return jsonify({"reply": "⚠️ AI Core Unresponsive. (Google Gemini Error)"}), 500

        # Save to History
        HISTORY[timestamp] = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": summary,
            "reply": reply,
            "mode": mode
        }

        return jsonify({"reply": reply, "command": command})

    except Exception as e:
        print(f"❌ Critical Server Error: {e}")
        return jsonify({"reply": "⚠️ Signal Interrupted. Check Server Logs."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
