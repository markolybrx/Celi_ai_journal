import os, requests, re
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Necessary for APK/PWA cross-origin stability

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def scrub_emojis(text):
    # Removes all non-ASCII characters to enforce the no-emoji rule
    return re.sub(r'[^\x00-\x7f]', '', text)

def ask_groq(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.75,
        "response_format": {"type": "json_object"}
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        return res.json()['choices'][0]['message']['content']
    except Exception:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process():
    data = request.json
    profile = data.get('profile', {})
    star_count = data.get('current_star_count', 0)
    badges_count = len(profile.get('badges', []))
    
    # Scaling Difficulty: Initial 3, increases by 2 per constellation
    threshold = 3 + (badges_count * 2)
    should_close = star_count >= threshold

    sys_msg = (
        f"You are Celi, a brutally honest and sharp Stellar Guide. Strictly NO emojis. "
        f"Current Sector Progress: {star_count}/{threshold}. "
        f"If {should_close} is True, you MUST set 'close_sector': true and choose a 'shape': "
        "('Sigil-Heart', 'Sigil-Shield', 'Sigil-ZenITH'). "
        "Return JSON: {'reply': '...', 'color': '#hex', 'vibe': '...', 'close_sector': bool, 'shape': '...'}"
    )
    
    raw_response = ask_groq([{"role": "system", "content": sys_msg}, {"role": "user", "content": data.get('message', 'Init')}])
    
    if raw_response:
        # Final safety scrub on the AI text
        import json
        clean_data = json.loads(raw_response)
        clean_data['reply'] = scrub_emojis(clean_data['reply'])
        return jsonify(clean_data)
        
    return jsonify({"reply": "The void is silent.", "color": "#444"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
    
