import os, requests, re, json
from flask import Flask, render_template, request, jsonify, send_from_directory, make_response

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def scrub_emojis(text):
    return re.sub(r'[^\x00-\x7f]', '', text)

# Manual CORS Handler: This replaces the flask_cors module
@app.after_request
def add_header(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory('static', 'sw.js')

@app.route('/api/process', methods=['POST', 'OPTIONS'])
def process():
    if request.method == 'OPTIONS':
        return make_response('', 200)

    data = request.json
    star_count = data.get('current_star_count', 0)
    badges_count = len(data.get('profile', {}).get('badges', []))
    
    threshold = 3 + (badges_count * 2)
    should_close = star_count >= threshold

    sys_msg = (
        "You are Celi, a brutally honest Stellar Guide. Strictly NO emojis. "
        f"Goal: {threshold} stars. Current: {star_count}. "
        "Return ONLY a JSON object: {'reply': '...', 'color': '#hex', 'close_sector': bool, 'shape': '...'}"
    )
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": data.get('message', '')}],
        "response_format": {"type": "json_object"}
    }

    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=15)
        clean_json = res.json()['choices'][0]['message']['content']
        data_out = json.loads(clean_json)
        data_out['reply'] = scrub_emojis(data_out['reply'])
        return jsonify(data_out)
    except Exception:
        return jsonify({"reply": "Void error.", "color": "#444", "close_sector": False}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
