import os, requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def ask_groq(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile", 
        "messages": messages, 
        "temperature": 0.7,
        "response_format": {"type": "json_object"}
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=25)
        res.raise_for_status()
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Check Error: {e}")
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
    is_venting = data.get('venting_mode', False)
    
    # Scaling Logic: Start at 3, increase by 2 per constellation
    threshold = 3 + (badges_count * 2)
    should_close = star_count >= threshold

    if is_venting:
        sys_msg = "Event Horizon mode. Validate briefly. No emojis. JSON: {'reply': '...', 'color': '#000000', 'is_void': true}"
    elif data.get('whisper_entry'):
        sys_msg = "Memory Retrieval. Summarize entry. No emojis. JSON: {'reply': '...'}"
    else:
        sys_msg = (
            f"You are Celi, a brutally honest Stellar Guide. Strictly NO emojis. "
            f"Current constellation progress: {star_count}/{threshold}. "
            f"If {should_close} is True, include 'close_sector': true and 'shape': 'Sigil-Heart' or 'Sigil-Shield'. "
            "Return JSON: {'reply': '...', 'color': '#hex', 'vibe': '...', 'close_sector': bool, 'shape': '...'}"
        )
    
    ai_raw = ask_groq([{"role": "system", "content": sys_msg}, {"role": "user", "content": data.get('message', 'Hello')}])
    return ai_raw if ai_raw else jsonify({"reply": "The signal is lost in the void.", "color": "#ffffff"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
    
