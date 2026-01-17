import os, requests, re, json
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__)

@app.after_request
def add_header(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/api/process', methods=['POST'])
def process():
    data = request.json
    msg = data.get('message', '')
    
    sys_msg = "You are Celi. A high-level, brutally honest advisor. No emojis. Dissect the user's input. Return JSON: {'reply': 'string', 'color': 'hex'}"
    
    headers = {"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": msg}],
        "response_format": {"type": "json_object"}
    }

    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=15)
        ai_resp = json.loads(res.json()['choices'][0]['message']['content'])
        return jsonify({
            "reply": re.sub(r'[^\x00-\x7f]', '', ai_resp.get('reply', '')),
            "color": ai_resp.get('color', '#B266FF')
        })
    except:
        return jsonify({"reply": "Void error.", "color": "#000"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
