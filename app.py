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
        "messages": messages
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        if res.status_code != 200:
            print(f"GROQ ERROR: {res.status_code} - {res.text}")
            return f"ERROR: {res.status_code}"
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"SYSTEM CRASH: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/process', methods=['POST', 'OPTIONS'])
def process():
    # Handle the "handshake" pre-flight from browsers
    if request.method == 'OPTIONS':
        return '', 200

    data = request.json
    if not GROQ_API_KEY:
        return jsonify({"reply": "API KEY MISSING IN RENDER"}), 500
    
    profile = data.get('profile', {})
    
    sys_msg = f"You are Celi, the sovereign advisor for {profile.get('name')}. Be brutally honest."
    
    ai_raw = ask_groq([{"role": "system", "content": sys_msg}, {"role": "user", "content": data['message']}])
    
    if ai_raw:
        return jsonify({"reply": ai_raw})
    
    return jsonify({"reply": "Handshake failed at the AI level."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
