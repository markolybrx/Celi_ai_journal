import os, requests, re, json, time
from flask import Flask, render_template, request, jsonify, session
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "celi_companion_prime_2026"
app.permanent_session_lifetime = timedelta(days=30)

VAULT_PATH = 'vault.json'

def get_vault():
    if not os.path.exists(VAULT_PATH):
        with open(VAULT_PATH, 'w') as f: json.dump({"users": {}}, f)
    with open(VAULT_PATH, 'r') as f: return json.load(f)

def save_vault(data):
    with open(VAULT_PATH, 'w') as f: json.dump(data, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html' if 'user' in session else 'auth.html')

@app.route('/api/auth', methods=['POST'])
def auth():
    data = request.json
    user = data.get('username', '').lower().strip()
    action = data.get('action')
    if not user: return jsonify({"error": "Name required"}), 400
    
    vault = get_vault()
    if action == 'register':
        if user in vault['users']: return jsonify({"error": "User exists"}), 400
        vault['users'][user] = {"history": [], "stars": [], "level": 0}
        save_vault(vault)
    
    if user in vault['users']:
        session.permanent = True
        session['user'] = user
        return jsonify({"success": True})
    return jsonify({"error": "Unknown User"}), 404

@app.route('/api/process', methods=['POST'])
def process():
    if 'user' not in session: return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session['user']
    msg = request.json.get('message', '')
    vault = get_vault()
    user_data = vault['users'][user_id]
    
    # Self-Learning Context Retrieval
    memory = "\n".join([f"User: {h['user_msg']}\nCeli: {h['reply']}" for h in user_data['history'][-5:]])
    
    sys_msg = (
        f"You are Celi: AI Journal Companion. User: {user_id}. "
        f"Character: Friendly, caring, empathetic, and witty. Smart-casual tone. "
        f"Use past context to show you are learning: \n{memory}\n"
        "Strictly NO emojis. Response must be JSON: {'reply': 'string', 'color': '#hex'}"
    )
    
    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": msg}],
                "response_format": {"type": "json_object"}
            }, timeout=15
        )
        ai_resp = json.loads(res.json()['choices'][0]['message']['content'])
        
        entry = {"user_msg": msg, "reply": ai_resp['reply'], "color": ai_resp['color'], "ts": time.time()}
        user_data['history'].append(entry)
        save_vault(vault)
        return jsonify(ai_resp)
    except:
        return jsonify({"reply": "I'm here and listening, even if the connection is a bit quiet.", "color": "#A855F7"})

@app.route('/api/history')
def get_history():
    if 'user' not in session: return jsonify([])
    return jsonify(get_vault()['users'][session['user']]['history'])

@app.route('/api/logout')
def logout():
    session.clear()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
