import os
import logging
import traceback
from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for
from datetime import datetime

# --- SETUP LOGGING ---
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)

# --- GLOBAL VARS ---
HISTORY = {} 
CONTEXT_STATE = {"awaiting_void_confirm": False}
GEMINI_STATUS = "Not Configured"

# --- 1. TRY LOADING GEMINI LIBRARY ---
try:
    import google.generativeai as genai
    GEMINI_STATUS = "Library Loaded"
except ImportError as e:
    GEMINI_STATUS = f"Library Error: {str(e)}"

# --- 2. TRY CONFIGURING API KEY ---
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    GEMINI_STATUS = "Missing API Key in Render Environment"
elif GEMINI_STATUS == "Library Loaded":
    try:
        genai.configure(api_key=api_key)
        GEMINI_STATUS = "Active"
    except Exception as e:
        GEMINI_STATUS = f"Config Error: {str(e)}"

# --- CONFIG ---
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 300,
}

VOID_INSTRUCTION = "You are 'The Void'. You are a sentient, infinite, and safe emptiness. Listen to pain and help release it. Be deep, calm, and abstract."
CELI_INSTRUCTION = "You are 'Celi', a warm AI Journaling Companion. If the user rants, ask: 'I sense heavy energy. Would you like to open The Void?'"

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
        # --- CRITICAL CHECK: IS AI WORKING? ---
        if GEMINI_STATUS != "Active":
            return jsonify({"reply": f"⚠️ SYSTEM FAILURE: {GEMINI_STATUS}. Check Render Logs."})

        data = request.json
        msg = data.get('message', '')
        mode = data.get('mode', 'journal')
        timestamp = str(datetime.now().timestamp())
        summary = msg[:40] + "..." if len(msg) > 40 else msg
        reply = "..."
        command = None

        # --- GENERATE CONTENT ---
        try:
            # SWITCHED TO 'gemini-pro' FOR MAX COMPATIBILITY
            model_name = "gemini-pro" 
            
            if mode == 'rant':
                model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)
                # Manually prepending instruction because gemini-pro handles system prompts differently than flash
                prompt = f"{VOID_INSTRUCTION}\n\nUser: {msg}"
                response = model.generate_content(prompt)
                reply = response.text.strip()
            else:
                if CONTEXT_STATE["awaiting_void_confirm"]:
                    if any(x in msg.lower() for x in ["yes", "sure", "please", "ok"]):
                        reply = "Understood. Opening the Void..."
                        command = "switch_to_void"
                        CONTEXT_STATE["awaiting_void_confirm"] = False
                    else:
                        CONTEXT_STATE["awaiting_void_confirm"] = False
                        model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)
                        prompt = f"{CELI_INSTRUCTION}\n\nUser declined void. User said: {msg}"
                        reply = model.generate_content(prompt).text.strip()
                else:
                    model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)
                    prompt = f"{CELI_INSTRUCTION}\n\nUser: {msg}"
                    response = model.generate_content(prompt)
                    reply = response.text.strip()
                    if "open The Void" in reply: CONTEXT_STATE["awaiting_void_confirm"] = True

        except Exception as e:
            return jsonify({"reply": f"⚠️ AI ERROR: {str(e)}"}), 200

        # Save & Return
        HISTORY[timestamp] = {"date": datetime.now().strftime("%Y-%m-%d"), "summary": summary, "reply": reply, "mode": mode}
        return jsonify({"reply": reply, "command": command})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"reply": f"⚠️ SERVER CRASH: {str(e)}"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
