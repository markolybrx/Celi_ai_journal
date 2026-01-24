import os
import logging
import traceback
from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for
from datetime import datetime
import google.generativeai as genai

# --- SETUP LOGGING ---
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)

# --- CONFIG ---
HISTORY = {} 
CONTEXT_STATE = {"awaiting_void_confirm": False}

# --- 1. SETUP API KEY ---
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    # Strip whitespace/quotes to prevent auth errors
    api_key = api_key.strip().replace("'", "").replace('"', "")
    try:
        genai.configure(api_key=api_key)
        print(f"✅ Key Configured.")
    except Exception as e:
        print(f"❌ Key Config Error: {e}")
else:
    print("❌ API KEY MISSING")

# --- PERSONAS ---
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

def generate_with_fallback(msg, is_void):
    """
    Targets the specific models available on your key.
    """
    # UPDATED CANDIDATES BASED ON YOUR DIAGNOSTIC REPORT
    candidates = [
        "gemini-2.0-flash",       # Primary: Fast & Intelligent
        "gemini-2.0-flash-lite",  # Backup: Ultra-fast
        "gemini-2.5-flash",       # Fallback: Cutting edge
    ]
    
    last_error = ""
    system_instruction = VOID_INSTRUCTION if is_void else CELI_INSTRUCTION

    for model_name in candidates:
        try:
            print(f"🔄 Trying model: {model_name}...")
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction
            )
            response = model.generate_content(msg)
            return response.text.strip(), model_name # Success!
            
        except Exception as e:
            print(f"⚠️ Failed with {model_name}: {e}")
            last_error = str(e)
            continue # Try next model

    # If all fail, return error
    return f"⚠️ CONNECTION FAILED. All Gemini 2.0 models failed. Error: {last_error}", "None"


@app.route('/api/process', methods=['POST'])
def process():
    try:
        data = request.json
        msg = data.get('message', '')
        mode = data.get('mode', 'journal')
        timestamp = str(datetime.now().timestamp())
        summary = msg[:40] + "..." if len(msg) > 40 else msg
        reply = "..."
        command = None

        # --- LOGIC BRAIN ---
        if mode == 'rant':
            reply, used_model = generate_with_fallback(msg, is_void=True)
        else:
            # Handle Switch Logic
            if CONTEXT_STATE["awaiting_void_confirm"]:
                if any(x in msg.lower() for x in ["yes", "sure", "please", "ok"]):
                    reply = "Understood. Opening the Void..."
                    command = "switch_to_void"
                    CONTEXT_STATE["awaiting_void_confirm"] = False
                else:
                    CONTEXT_STATE["awaiting_void_confirm"] = False
                    reply, used_model = generate_with_fallback(f"User declined void. User said: {msg}", is_void=False)
            else:
                reply, used_model = generate_with_fallback(msg, is_void=False)
                if "open The Void" in reply: CONTEXT_STATE["awaiting_void_confirm"] = True

        # Save Entry
        HISTORY[timestamp] = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": summary,
            "reply": reply,
            "mode": mode
        }

        return jsonify({"reply": reply, "command": command})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"reply": f"SYSTEM CRASH: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
