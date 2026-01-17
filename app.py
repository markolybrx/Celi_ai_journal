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
        "temperature": 0.8,
        "max_tokens": 150  # Hard limit on response length
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
    
    # SYSTEM PROMPT: Strictly Short & Empathetic
    if is_venting:
        sys_msg = f"You are Celi. {user_name} is venting. Be a silent, warm listener. Max 10 words. Validate only."
    else:
        sys_msg = (
            f"You are Celi, the witty, compassionate best friend of {user_name}. "
            "STRICT RULES: Keep responses under 3 short sentences. No fluff. No 'How can I help you today?' "
            "If user is HAPPY: Be high-energy, lively, and celebrate with them! "
            "If user is SAD: Be soft, compassionate, and brief. "
            "Always be direct. If they need a 'Bestie Prescription' (walk, sleep, water), say it straight."
        )
    
    ai_raw = ask_groq([{"role": "system", "content": sys_msg}, {"role": "user", "content": data['message']}])
    
    if ai_raw:
        return jsonify({"reply": ai_raw})
    
    return jsonify({"reply": "I'm right here. Try again?"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
