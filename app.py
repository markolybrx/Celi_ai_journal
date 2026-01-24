from flask import Flask, render_template, jsonify, request, send_from_directory
from datetime import datetime

app = Flask(__name__)

# --- MEMORY (Resets on restart) ---
HISTORY = {} 

# --- SYSTEM ROUTES ---
@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

@app.route('/')
def index():
    return render_template('index.html')

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
        mode = data.get('mode', 'journal') # 'journal' or 'rant'
        
        timestamp = str(datetime.now().timestamp())
        summary = msg[:30] + "..." if len(msg) > 30 else msg
        reply = "..."

        # --- LOGIC BRAIN ---
        if mode == 'rant':
            reply = "Signal weak. Entry logged."
        else:
            # AI SIMULATION (Replace with real AI logic later)
            msg_lower = msg.lower()
            if "hello" in msg_lower:
                reply = "Systems online. I am listening."
            elif "who are you" in msg_lower:
                reply = "I am Celi. Your navigational archive."
            elif "sad" in msg_lower or "tired" in msg_lower:
                reply = "Rest is part of the journey. The stars will wait."
            else:
                reply = f"Logged: {summary}. Systems stable."

        # Save Entry
        HISTORY[timestamp] = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": summary,
            "reply": reply,
            "mode": mode
        }

        return jsonify({"reply": reply})

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"reply": "System Error: Neural Link Severed."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
