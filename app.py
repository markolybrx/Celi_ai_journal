import os
from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# --- MEMORY & CONTEXT TRACKING ---
HISTORY = {} 
# Simple global state to track if Celi just offered the void.
CONTEXT_STATE = {"awaiting_void_confirm": False}

# --- SYSTEM ROUTES ---
@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

# --- APP ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

# --- AUTH ROUTES (FIXED 404 ERROR) ---
@app.route('/logout')
def logout():
    # In a real app, you would clear the session here: session.clear()
    # For this prototype, we just redirect back to the app or a login placeholder
    return redirect(url_for('login'))

@app.route('/login')
def login():
    # Simple placeholder for a login page to prevent crashing
    return """
    <body style="background:#000; color:#fff; font-family:sans-serif; display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh;">
        <h1>Celi Terminal</h1>
        <p>Session Ended.</p>
        <a href="/" style="color:#00f2fe; text-decoration:none; border:1px solid #00f2fe; padding:10px 20px; border-radius:20px; margin-top:20px;">Reconnect</a>
    </body>
    """

@app.route('/api/data')
def get_data():
    return jsonify({
        "status": "user",
        "username": "User",
        "first_name": "Traveler",
        "rank": "Observer I",
        "rank_progress": 25,
        "user_id": "8492-X",
        "history": HISTORY
    })

@app.route('/api/process', methods=['POST'])
def process():
    try:
        data = request.json
        msg = data.get('message', '')
        mode = data.get('mode', 'journal') # 'journal' (Celi) or 'rant' (Void)
        
        timestamp = str(datetime.now().timestamp())
        summary = msg[:30] + "..." if len(msg) > 30 else msg
        reply = "..."
        command = None 

        # --- LOGIC BRAIN ---
        
        # 1. VOID PERSONA
        if mode == 'rant':
            lower_msg = msg.lower()
            if "sad" in lower_msg or "hurt" in lower_msg:
                reply = "I sense your pain. It is safe to let it go here. The void consumes it, so you don't have to carry it."
            elif "advice" in lower_msg or "help" in lower_msg:
                reply = "From the silence, clarity emerges: Breathe. Detach. You are the sky, not the clouds."
            else:
                reply = "I am listening. Your words are safe in the silence. Release them."

        # 2. CELI AI PERSONA
        else:
            lower_msg = msg.lower()
            
            # CHECK: Switching Context
            if CONTEXT_STATE["awaiting_void_confirm"]:
                if "yes" in lower_msg or "sure" in lower_msg or "please" in lower_msg:
                    reply = "Understood. Opening the Void for you now..."
                    command = "switch_to_void"
                    CONTEXT_STATE["awaiting_void_confirm"] = False
                else:
                    reply = "Okay, we can stay here in the light. What else is on your mind?"
                    CONTEXT_STATE["awaiting_void_confirm"] = False
            
            # CHECK: Rant Detection
            elif any(word in lower_msg for word in ["hate", "angry", "annoyed", "furious", "sucks", "tired of", "stupid"]):
                reply = "I sense a lot of heavy energy in your words. Would you like to step into The Void to let this out safely?"
                CONTEXT_STATE["awaiting_void_confirm"] = True
            
            # NORMAL CHAT
            else:
                if "hello" in lower_msg or "hi" in lower_msg:
                    reply = "Hi there! Systems are bright and optimal. How is your day going?"
                elif "thank" in lower_msg:
                    reply = "You are very welcome, Traveler!"
                else:
                    reply = f"I hear you. '{summary}'... tell me more about that."

        # Save Entry
        HISTORY[timestamp] = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": summary,
            "reply": reply,
            "mode": mode
        }

        return jsonify({"reply": reply, "command": command})

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"reply": "System Error: Neural Link Severed."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
