import os, requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def ask_groq(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.8
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        res.raise_for_status()
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"SYSTEM ERROR: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/process', methods=['POST', 'OPTIONS'])
def process():
    if request.method == 'OPTIONS':
        return '', 200

    data = request.json
    profile = data.get('profile', {})
    is_venting = data.get('venting_mode', False)
    user_name = profile.get('name', 'friend')
    
    # DYNAMIC SYSTEM PROMPT
    if is_venting:
        sys_msg = (
            f"You are Celi, {user_name}'s compassionate listener. "
            "MODE: VENTING. Do NOT give advice. Do NOT try to fix things. "
            "Your only job is to listen, validate, and let them vent. "
            "Use phrases like 'I'm listening', 'That sounds so hard', or 'Let it all out.' "
            "Be a silent, supportive presence. No wit, just pure empathy."
        )
    else:
        sys_msg = (
            f"You are Celi, the compassionate, witty best friend of {user_name}. "
            "MODE: COMPANION. Be warm, insightful, and funny. "
            "If they are stressed, give a 'Bestie Prescription' (rest, walk, hydration). "
            "Use gentle humor to lift their spirits."
        )
    
    ai_raw = ask_groq([{"role": "system", "content": sys_msg}, {"role": "user", "content": data['message']}])
    
    if ai_raw:
        return jsonify({"reply": ai_raw})
    
    return jsonify({"reply": "I'm right here. My connection blinked, but I'm still listening."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
                                                                     
