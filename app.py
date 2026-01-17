import os, requests, re, json
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def scrub_emojis(text):
    return re.sub(r'[^\x00-\x7f]', '', text)

@app.route('/')
def index():
    return render_template('index.html')

# Essential PWA routes to ensure the phone recognizes the app files
@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory('static', 'sw.js')

@app.route('/api/process', methods=['POST'])
def process():
    data = request.json
    star_count = data.get('current_star_count', 0)
    badges_count = len(data.get('profile', {}).get('badges', []))
    
    # Scaling: Each constellation requires more stars (3, 5, 7, 9...)
    threshold = 3 + (badges_count * 2)
    should_close = star_count >= threshold

    sys_msg = (
        "You are Celi, a brutally honest and sharp Stellar Guide. Strictly NO emojis. "
        f"Goal: {threshold} stars. Current stars in sector: {star_count}. "
        f"If {should_close} is True, you MUST set 'close_sector': true and pick a 'shape': "
        "('Sigil-Heart', 'Sigil-Shield', 'Sigil-ZenITH'). "
        "Return ONLY a JSON object: {'reply': '...', 'color': '#hex', 'close_sector': bool, 'shape': '...'}"
    )
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": data.get('message', '')}],
        "temperature": 0.7,
        "response_format": {"type": "json_object"}
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        ai_data = res.json()['choices'][0]['message']['content']
        clean_json = json.loads(ai_data)
        clean_json['reply'] = scrub_emojis(clean_json['reply'])
        return jsonify(clean_json)
    except Exception as e:
        return jsonify({"reply": "The signal is flickering.", "color": "#444", "close_sector": False}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
