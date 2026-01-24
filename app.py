import random
from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# --- MEMORY ---
HISTORY = {} 
CONTEXT_STATE = {"awaiting_void_confirm": False}

# --- RESPONSES DATA ---
VOID_RESPONSES = {
    "pain": [
        "Your pain is valid here. Let it drift away into the endless dark.",
        "Sorrow is heavy, but here you can set it down. I am listening.",
        "You are not alone in the dark. The stars are watching over you."
    ],
    "anger": [
        "Let the fire burn out in the vacuum. Scream if you must.",
        "Anger is energy. Release it here where it cannot harm you.",
        "The void can handle your rage. Let it all out."
    ],
    "advice": [
        "Sometimes the best path is found by standing still.",
        "Look within. The universe outside is a reflection of the universe inside.",
        "Breathe. This moment is fleeting. You will find your way."
    ],
    "default": [
        "I am listening. Your words are safe in the silence.",
        "Go on. Unburden yourself.",
        "The void absorbs all. Speak freely.",
        "Your thoughts echo in the vastness. Continue."
    ]
}

CELI_RESPONSES = {
    "greeting": [
        "Hello there, Traveler! 🌟 Ready to log some memories?",
        "Hi! Systems are bright and optimal. How is your day going?",
        "Greetings! It's a beautiful cycle to be alive. What's up?"
    ],
    "good": [
        "That makes my circuits glow! What made it so good?",
        "I love hearing that! Keep that positive energy flowing!",
        "Fantastic! Tell me the highlight of your day."
    ],
    "food": [
        "Ooh, tasty! 🍗 Fueling the biological engine is important. Was it good?",
        "Sounds delicious! I can't eat, but I imagine it tasted wonderful.",
        "Food always helps the mood. Who did you eat with?"
    ],
    "sleep": [
        "Rest is critical for your neural networks. Sleep well, Traveler.",
        "Recharging is just as important as working. Sweet dreams.",
        "The galaxy will still be here when you wake up. Rest now."
    ],
    "closing": [
        "Understood. Short and sweet. 🚀",
        "Alright then. I'll log that entry. Anything else?",
        "Got it. Systems standing by for your next thought."
    ],
    "default": [
        "I see. That's interesting. Tell me more?",
        "Noted. How did that make you feel?",
        "I'm listening. Go on.",
        "And then what happened?"
    ]
}

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

@app.route('/logout')
def logout():
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return redirect(url_for('index'))

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
        mode = data.get('mode', 'journal')
        
        timestamp = str(datetime.now().timestamp())
        summary = msg[:30] + "..." if len(msg) > 30 else msg
        reply = "..."
        command = None 
        msg_lower = msg.lower()

        # --- LOGIC BRAIN ---
        
        # 1. VOID PERSONA
        if mode == 'rant':
            if any(x in msg_lower for x in ['sad', 'hurt', 'pain', 'lonely', 'cry']):
                reply = random.choice(VOID_RESPONSES["pain"])
            elif any(x in msg_lower for x in ['angry', 'hate', 'mad', 'furious', 'annoyed']):
                reply = random.choice(VOID_RESPONSES["anger"])
            elif any(x in msg_lower for x in ['advice', 'help', 'lost', 'what should i do']):
                reply = random.choice(VOID_RESPONSES["advice"])
            else:
                reply = random.choice(VOID_RESPONSES["default"])

        # 2. CELI AI PERSONA
        else:
            # Check Switch Context
            if CONTEXT_STATE["awaiting_void_confirm"]:
                if any(x in msg_lower for x in ["yes", "sure", "please", "okay", "yeah"]):
                    reply = "Understood. Opening the Void for you now..."
                    command = "switch_to_void"
                    CONTEXT_STATE["awaiting_void_confirm"] = False
                else:
                    reply = "Okay, we can stay here in the light. What else is on your mind?"
                    CONTEXT_STATE["awaiting_void_confirm"] = False
            
            # Check Rant
            elif any(x in msg_lower for x in ["hate", "angry", "furious", "sucks", "tired of", "stupid", "worst"]):
                reply = "I sense a lot of heavy energy in your words. Would you like to step into The Void to let this out safely?"
                CONTEXT_STATE["awaiting_void_confirm"] = True
            
            # Contextual Chat
            elif any(x in msg_lower for x in ['hello', 'hi', 'hey']):
                reply = random.choice(CELI_RESPONSES["greeting"])
            elif any(x in msg_lower for x in ['good', 'great', 'happy', 'awesome']):
                reply = random.choice(CELI_RESPONSES["good"])
            elif any(x in msg_lower for x in ['eat', 'ate', 'food', 'jollibee', 'dinner', 'lunch']):
                reply = random.choice(CELI_RESPONSES["food"])
            elif any(x in msg_lower for x in ['sleep', 'tired', 'bed', 'night']):
                reply = random.choice(CELI_RESPONSES["sleep"])
            elif any(x in msg_lower for x in ["that's it", "nothing else", "nope", "bye"]):
                reply = random.choice(CELI_RESPONSES["closing"])
            else:
                reply = random.choice(CELI_RESPONSES["default"])

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
