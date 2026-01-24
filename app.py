import os
from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for
from datetime import datetime
import google.generativeai as genai

app = Flask(__name__)

# --- 🔑 GEMINI CONFIGURATION ---
# This grabs the key you saved in Render's Environment Variables
api_key = os.environ.get("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
else:
    print("⚠️ WARNING: GEMINI_API_KEY not found in environment variables.")

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

# --- MEMORY & STATE ---
HISTORY = {} 
CONTEXT_STATE = {"awaiting_void_confirm": False}

# --- ROUTES ---
@app.route('/')
def index(): return render_template('index.html')

@app.route('/logout')
def logout(): return redirect(url_for('login'))

@app.route('/login')
def login(): return redirect(url_for('index')) # Redirect to app for now

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
        data = request.json
        msg = data.get('message', '')
        mode = data.get('mode', 'journal')
        timestamp = str(datetime.now().timestamp())
        summary = msg[:40] + "..." if len(msg) > 40 else msg
        reply = ""
        command = None

        if not api_key:
            return jsonify({"reply": "System Error: API Key missing. Check Render settings."}), 500

        # --- REAL AI PROCESSING ---
        
        # 1. VOID MODE
        if mode == 'rant':
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=generation_config,
                system_instruction=VOID_INSTRUCTION
            )
            # Create a one-off chat response (stateless for the void effect)
            response = model.generate_content(msg)
            reply = response.text.strip()

        # 2. CELI MODE
        else:
            # Check for Context Switch Confirmation FIRST
            if CONTEXT_STATE["awaiting_void_confirm"]:
                if any(x in msg.lower() for x in ["yes", "sure", "please", "ok", "yeah", "open it"]):
                    reply = "Understood. Opening the Void for you now... Breathe."
                    command = "switch_to_void"
                    CONTEXT_STATE["awaiting_void_confirm"] = False
                else:
                    # User declined Void
                    CONTEXT_STATE["awaiting_void_confirm"] = False
                    model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=CELI_INSTRUCTION, generation_config=generation_config)
                    reply = model.generate_content(f"User declined the void. Respond to: {msg}").text.strip()
            else:
                # Normal Celi Chat
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    generation_config=generation_config,
                    system_instruction=CELI_INSTRUCTION
                )
                response = model.generate_content(msg)
                reply = response.text.strip()

                # LOGIC: Check if Celi detected a rant (Self-Correction)
                # If Gemini generated the specific phrase we told it to use in the system instruction
                if "open The Void" in reply or "step into The Void" in reply:
                    CONTEXT_STATE["awaiting_void_confirm"] = True

        # Save to History
        HISTORY[timestamp] = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": summary,
            "reply": reply,
            "mode": mode
        }

        return jsonify({"reply": reply, "command": command})

    except Exception as e:
        print(f"AI Error: {e}")
        return jsonify({"reply": "⚠️ Signal Interrupted. Neural Link Unstable."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
