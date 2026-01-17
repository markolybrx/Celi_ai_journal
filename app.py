import os, requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# SECURITY: Pulled from Render Environment Variables
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def ask_groq(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": messages,
        "temperature": 0.8
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        if res.status_code != 200:
            print(f"GROQ ERROR: {res.status_code} - {res.text}")
        res.raise_for_status()
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"SYSTEM CRASH: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process():
    data = request.json
    if not GROQ_API_KEY:
        return jsonify({"mood":"angry", "reply":"KEY MISSING IN RENDER DASHBOARD", "insight":None})
    
    profile = data.get('profile', {})
    
    sys_msg = (
        f"You are Celi, the sovereign advisor for {profile.get('name')}. "
        "Identity: Brutally honest, witty mirror. "
        "Challenge user's excuses. Always reply in this EXACT format: "
        "MOOD: [mood] | REPLY: [text] | INSIGHT: [one sentence]"
    )
    
    ai_raw = ask_groq([{"role": "system", "content": sys_msg}, {"role": "user", "content": data['message']}])
    
    if ai_raw:
        try:
            # Safer parsing for mobile stability
            mood = ai_raw.split("MOOD:")[1].split("|")[0].strip()
            reply = ai_raw.split("REPLY:")[1].split("|")[0].strip()
            insight = ai_raw.split("INSIGHT:")[1].strip()
            return jsonify({"mood": mood, "reply": reply, "insight": insight})
        except:
            return jsonify({"mood": "sharp", "reply": ai_raw, "insight": "Direct analysis enabled."})
    
    return jsonify({"mood": "anxious", "reply": "Handshake failed.", "insight": None})

if __name__ == '__main__':
    # Render provides a PORT environment variable. We MUST use it.
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
