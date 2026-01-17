import os, requests, json, time
from flask import Flask, render_template, request, jsonify, session
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.secret_key = "celi_voyager_prestige_2026"
app.permanent_session_lifetime = timedelta(days=30)

VAULT_PATH = 'vault.json'

RANK_DATA = {
    "Observer": {"desc": "Static. Noticing patterns of the inner sky.", "state": "Static", "color": "#3B82F6"},
    "Moonwalker": {"desc": "Detached. Gaining distance from old habits.", "state": "Detached", "color": "#94A3B8"},
    "Stellar": {"desc": "Ignited. Self-reflection is now a self-sustaining energy.", "state": "Ignited", "color": "#F59E0B"},
    "Celestial": {"desc": "Navigational. Understanding emotional mechanics.", "state": "Navigational", "color": "#06B6D4"},
    "Interstellar": {"desc": "Voyaging. Navigating the deep void with discipline.", "state": "Voyaging", "color": "#8B5CF6"},
    "Galactic": {"desc": "Systemic. Managing history as a unified structure.", "state": "Systemic", "color": "#D946EF"},
    "Ethereal": {"desc": "Transcendent. The boundary between you and the universe is gone.", "state": "Transcendent", "color": "#FFFFFF"}
}

def get_vault():
    if not os.path.exists(VAULT_PATH):
        with open(VAULT_PATH, 'w') as f: json.dump({"users": {}}, f)
    with open(VAULT_PATH, 'r') as f: return json.load(f)

def save_vault(data):
    with open(VAULT_PATH, 'w') as f: json.dump(data, f, indent=4)

def calculate_prestige(points, last_seen_str):
    today = date.today()
    last_seen = datetime.strptime(last_seen_str, '%Y-%m-%d').date()
    days_missed = (today - last_seen).days
    penalty = max(0, days_missed - 1)
    adj_pts = max(0, points - penalty)

    config = [
        ("Observer", 3, 2), ("Moonwalker", 3, 2), ("Stellar", 4, 3), 
        ("Celestial", 4, 3), ("Interstellar", 5, 4), ("Galactic", 5, 4), ("Ethereal", 5, 8)
    ]

    temp_pts = adj_pts
    for name, level_count, req in config:
        rank_total = level_count * req
        if temp_pts >= rank_total:
            if name == "Ethereal": return name, "I", adj_pts, penalty
            temp_pts -= rank_total
        else:
            sub_idx = level_count - (temp_pts // req)
            roman = {5:"V", 4:"IV", 3:"III", 2:"II", 1:"I"}
            return name, roman.get(sub_idx, "V"), adj_pts, penalty
    return "Observer", "V", adj_pts, penalty

@app.route('/')
def index():
    return render_template('index.html' if 'user' in session else 'auth.html')

@app.route('/api/auth', methods=['POST'])
def auth():
    uid = request.json.get('user_id', '').strip().lower()
    if not uid: return jsonify({"error": "Identity required"}), 400
    vault = get_vault()
    if uid not in vault['users']:
        vault['users'][uid] = {"points": 0, "stars": [], "history": {}, "last_seen": str(date.today())}
        save_vault(vault)
    session['user'] = uid
    return jsonify({"success": True})

@app.route('/api/process', methods=['POST'])
def process():
    if 'user' not in session: return jsonify({"error": "Unauthorized"}), 401
    vault = get_vault()
    user_data = vault['users'][session['user']]
    rn, rs, pts, pen = calculate_prestige(user_data['points'], user_data['last_seen'])
    
    history_list = sorted(user_data['history'].values(), key=lambda x: x['ts'], reverse=True)[:10]
    memory_log = "\n".join([f"User: {h['user_msg']} -> Celi: {h['reply']}" for h in history_list])

    msg = request.json.get('message', '')
    sys_msg = (
        f"You are Celi. User: {session['user']}. Rank: {rn} {rs}. "
        f"Be empathetic, witty, and self-learning. Use Memory: {memory_log}. "
        f"No emojis. Return JSON: {{'reply':'...', 'color':'#hex'}}"
    )
    
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": msg}], "response_format": {"type": "json_object"}})
        ai_resp = json.loads(res.json()['choices'][0]['message']['content'])
        
        user_data['points'] = pts + 1
        user_data['last_seen'] = str(date.today())
        user_data['stars'].append({"color": ai_resp['color'], "x": 10+(time.time()%80), "y": 20+(time.time()%60)})
        user_data['history'][str(time.time())] = {"user_msg": msg, "reply": ai_resp['reply'], "color": ai_resp['color'], "ts": time.time()}
        save_vault(vault)
        return jsonify(ai_resp)
    except: return jsonify({"reply": "The void is silent.", "color": "#ff4444"})

@app.route('/api/memory_summary')
def memory_summary():
    if 'user' not in session: return jsonify({"error": "Unauthorized"}), 401
    vault = get_vault()
    user_data = vault['users'][session['user']]
    full_history = "\n".join([h['user_msg'] for h in user_data['history'].values()])
    
    sys_msg = "Summarize what you have learned about this user's psychological journey since day 1. Be compassionate and witty. No emojis."
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": full_history}]})
        return jsonify({"summary": res.json()['choices'][0]['message']['content']})
    except: return jsonify({"summary": "I am still gathering the fragments of your journey."})

@app.route('/api/data')
def get_data():
    if 'user' not in session: return jsonify({})
    vault = get_vault()
    user_data = vault['users'][session['user']]
    rn, rs, pts, pen = calculate_prestige(user_data['points'], user_data['last_seen'])
    return jsonify({"user_id": session['user'], "rank": rn, "level": rs, "history": user_data['history'], "stars": user_data['stars'], "theme": RANK_DATA[rn]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
