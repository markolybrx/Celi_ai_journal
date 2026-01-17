import os, requests, json, time
from flask import Flask, render_template, request, jsonify, session
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.secret_key = "celi_voyager_prestige_2026"
app.permanent_session_lifetime = timedelta(days=30)

VAULT_PATH = 'vault.json'

RANK_DATA = {
    "Observer": {"desc": "You are a spectator of your life, beginning to notice the patterns of the inner sky.", "state": "Static", "color": "#1E3A8A"},
    "Moonwalker": {"desc": "You have detached from old habits and are looking back at your world from a distance.", "state": "Detached", "color": "#94A3B8"},
    "Stellar": {"desc": "Internal fusion achieved. Your self-reflection is now a self-sustaining source of energy.", "state": "Ignited", "color": "#F59E0B"},
    "Celestial": {"desc": "You understand the complex mechanics of your emotions and how they govern your trajectory.", "state": "Navigational", "color": "#06B6D4"},
    "Interstellar": {"desc": "You are navigating the deep gaps of the void with discipline and momentum.", "state": "Voyaging", "color": "#8B5CF6"},
    "Galactic": {"desc": "You possess immense psychological gravity, managing your history as a unified structure.", "state": "Systemic", "color": "#D946EF"},
    "Ethereal": {"desc": "The boundary between traveler and universe has dissolved. You are the work.", "state": "Transcendent", "color": "#FFFFFF"}
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
    points = max(0, points - penalty)

    config = [
        ("Observer", 3, 2), ("Moonwalker", 3, 2), ("Stellar", 4, 3), 
        ("Celestial", 4, 3), ("Interstellar", 5, 4), ("Galactic", 5, 4), ("Ethereal", 5, 8)
    ]

    current_points = points
    for name, level_count, req in config:
        rank_total = level_count * req
        if current_points >= rank_total:
            if name == "Ethereal": return name, "I", points, penalty
            current_points -= rank_total
        else:
            sub_num = level_count - (current_points // req)
            roman = {5:"V", 4:"IV", 3:"III", 2:"II", 1:"I"}
            return name, roman.get(sub_num, "V"), points, penalty
    return "Observer", "V", points, penalty

@app.route('/')
def index():
    return render_template('index.html' if 'user' in session else 'auth.html')

@app.route('/api/auth', methods=['POST'])
def auth():
    data = request.json
    uid = data.get('user_id', '').strip().lower()
    if not uid: return jsonify({"error": "Identity required"}), 400
    vault = get_vault()
    if uid not in vault['users']:
        vault['users'][uid] = {"points": 0, "stars": [], "history": {}, "last_seen": str(date.today()), "rank": "Observer"}
        save_vault(vault)
    session['user'] = uid
    session.permanent = True
    return jsonify({"success": True})

@app.route('/api/process', methods=['POST'])
def process():
    if 'user' not in session: return jsonify({"error": "Unauthorized"}), 401
    vault = get_vault()
    user_data = vault['users'][session['user']]
    rn, rs, pts, pen = calculate_prestige(user_data['points'], user_data['last_seen'])
    
    msg = request.json.get('message', '')
    p_state = RANK_DATA[rn]['state']
    sys_msg = f"Act as Celi. Rank: {rn} {rs} ({p_state}). Be witty/empathetic. Return JSON {{'reply':'...', 'color':'#hex'}}"
    
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

@app.route('/api/data')
def get_data():
    if 'user' not in session: return jsonify({})
    vault = get_vault()
    user_data = vault['users'][session['user']]
    rn, rs, pts, pen = calculate_prestige(user_data['points'], user_data['last_seen'])
    user_data['points'] = pts
    user_data['last_seen'] = str(date.today())
    save_vault(vault)
    return jsonify({"rank": rn, "level": rs, "points": pts, "penalty": pen, "history": user_data['history'], "stars": user_data['stars'], "theme": RANK_DATA[rn]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
                                                                   
