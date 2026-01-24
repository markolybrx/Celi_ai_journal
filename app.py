import os
from flask import Flask, render_template, jsonify, request, send_from_directory
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURATION ---
# In a real app, you would use a database. For this demo, we use in-memory storage.
# This resets when the app restarts.
HISTORY = {} 

# --- PWA SYSTEM ROUTES (DO NOT TOUCH) ---
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

@app.route('/api/data')
def get_data():
    """Syncs user data and chat history to the frontend"""
    # In a real app, fetch this from a database based on session
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
    """Handles the Chat Logic"""
    try:
        data = request.json
        msg = data.get('message', '')
        mode = data.get('mode', 'journal') # 'journal' (AI) or 'rant' (Void)
        timestamp = str(datetime.now().timestamp())
        
        reply = ""
        summary = msg[:30] + "..." if len(msg) > 30 else msg

        # --- LOGIC BRAIN ---
        if mode == 'rant':
            # VOID MODE: Minimalist, thematic logging
            reply = "Signal weak. Entry logged."
        
        else:
            # AI MODE: Simulated Intelligence (Replace this with OpenAI/Gemini API call later)
            lower_msg = msg.lower()
            if "hello" in lower_msg or "hi" in lower_msg:
                reply = "Systems online. I am listening."
            elif "task" in lower_msg:
                reply = "I've noted that task. Focus is key."
            elif "sad" in lower_msg or "tired" in lower_msg:
                reply = "It is okay to rest. The stars will still be here when you wake."
            elif "galaxy" in lower_msg:
                reply = "The galaxy is vast, just like your potential."
            else:
                reply = "Data received. I am processing your thoughts."

        # Save to History
        HISTORY[timestamp] = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": summary,
            "reply": reply,
            "mode": mode
        }

        return jsonify({"reply": reply})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"reply": "System Error: Connection severed."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
