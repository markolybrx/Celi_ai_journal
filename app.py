import os, requests, re, json, time
from flask import Flask, render_template, request, jsonify, session
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "celi_complete_resurgence_2026"
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
    if not user: return jsonify({"success": False, "error": "Name required"}), 400
    
    vault = get_vault()
    if action == 'register':
        if user in vault['users']: return jsonify({"success": False, "error": "Exists"}), 400
        vault['users'][user] = {"history": {}, "stars": [], "level": 1, "rank": "Neophyte"}
        save_vault(vault)
        return jsonify({"success": True})
    
    if user in vault['users']:
        session.permanent = True
        session['user'] = user
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Unknown User"}), 404

@app.route('/api/process', methods=['POST'])
def process():
    if 'user' not in session: return jsonify({"error": "Unauthorized"}), 401
    user_id = session['user']
    msg = request.json.get('message', '')
    vault = get_vault()
    user_data = vault['users'][user_id]
    
    # Self-Learning Context (Last 5 history entries)
    history_list = sorted(user_data['history'].items(), key=lambda x: x[1]['ts'], reverse=True)[:5]
    memory = "\n".join([f"U: {v['user_msg']}\nC: {v['reply']}" for k, v in history_list])
    
    sys_msg = (
        f"You are Celi: AI Journal Companion. User: {user_id}. "
        "Character: Friendly, witty, compassionate, and smart-casual. "
        f"Memory Log:\n{memory}\n"
        "Strictly NO emojis. Return JSON: {'reply': 'string', 'color': '#hex'}"
    )
    
    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": msg}], "response_format": {"type": "json_object"}},
            timeout=15
        )
        ai_resp = json.loads(res.json()['choices'][0]['message']['content'])
        
        # Save to History (Date-keyed for Calendar)
        date_key = time.strftime("%Y-%m-%d")
        user_data['history'][date_key] = {"user_msg": msg, "reply": ai_resp['reply'], "color": ai_resp['color'], "ts": time.time()}
        
        # Star progression
        user_data['stars'].append({"color": ai_resp['color'], "x": 10 + (time.time() % 80), "y": 20 + (time.time() % 60)})
        
        # Rank logic
        ranks = ["Neophyte", "Observer", "Pathfinder", "Architect", "Sovereign"]
        user_data['level'] = (len(user_data['stars']) // 5) + 1
        user_data['rank'] = ranks[min(user_data['level']-1, 4)]
        
        save_vault(vault)
        return jsonify(ai_resp)
    except:
        return jsonify({"reply": "I'm still here, just lost in the nebula for a second.", "color": "#A855F7"})

@app.route('/api/data')
def get_data():
    if 'user' not in session: return jsonify({})
    return jsonify(get_vault()['users'][session['user']])

@app.route('/api/purge', methods=['POST'])
def purge():
    date_key = request.json.get('date')
    vault = get_vault()
    if date_key in vault['users'][session['user']]['history']:
        del vault['users'][session['user']]['history'][date_key]
        save_vault(vault)
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route('/api/logout')
def logout():
    session.clear()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
