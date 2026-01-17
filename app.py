import os, requests, json, time
from flask import Flask, render_template, request, jsonify, session
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.secret_key = "celi_voyager_prestige_2026"
app.permanent_session_lifetime = timedelta(days=30)

VAULT_PATH = 'vault.json'

RANK_DEFS = {
    "Observer": "Psychological State: Static/Observer. User is a spectator of their life, noticing patterns.",
    "Moonwalker": "Psychological State: Detached. User has taken the first step toward objectivity.",
    "Stellar": "Psychological State: Ignited. Self-reflection is now a self-sustaining energy source.",
    "Celestial": "Psychological State: Navigational. User understands their emotional mechanics.",
    "Interstellar": "Psychological State: Voyaging. User is navigating the deep void with discipline.",
    "Galactic": "Psychological State: Systemic. User sees their history as a unified structure.",
    "Ethereal": "Psychological State: Transcendent. The boundary between user and universe is dissolved."
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
        vault['users'][uid] = {
            "points": 0, "stars": [], "history": {}, 
            "last_seen": str(date.today()), "rank": "Observer"
        }
        save_vault(vault)
    
    session['user'] = uid
    session.permanent = True
    return jsonify({"success": True})

@app.route('/api/process', methods=['POST'])
def process():
    if 'user' not in session: return jsonify({"error": "Unauthorized"}), 401
    vault = get_vault()
    user_data = vault['users'][session['user']]
    
    rank_name, rank_sub, pts, penalty = calculate_prestige(user_data['points'], user_data['last_seen'])
    p_state = RANK_DEFS.get(rank_name, "")

    msg = request.json.get('message', '')
    sys_msg = f"Act as Celi. User is Rank: {rank_name} {rank_sub}. {p_state} Be witty/empathetic. Return JSON {{'reply':'...', 'color':'#hex'}}"
    
    try:
        # Note: Replace with your actual API key env variable
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
    return jsonify({"rank": rn, "level": rs, "points": pts, "penalty": pen, "history": user_data['history'], "stars": user_data['stars']})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
                                                                   
