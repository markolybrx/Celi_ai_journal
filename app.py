import os, requests, json, time
from flask import Flask, render_template, request, jsonify, session
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.secret_key = "celi_voyager_fchq_2026_v3.7_final"
app.permanent_session_lifetime = timedelta(days=30)

VAULT_PATH = 'vault.json'

RANK_DATA = {
    "Observer": {"state": "Static", "color": "#3B82F6", "desc": "You are currently static, noticing patterns without interference."},
    "Moonwalker": {"state": "Detached", "color": "#94A3B8", "desc": "You are gaining distance, observing your life from a cold, stable orbit."},
    "Stellar": {"state": "Ignited", "color": "#F59E0B", "desc": "The fusion has begun. You are now self-sustaining and radiating intent."},
    "Celestial": {"state": "Navigational", "color": "#06B6D4", "desc": "Mechanics are understood. You are steering through your own gravity."},
    "Interstellar": {"state": "Voyaging", "color": "#8B5CF6", "desc": "You have left the familiar. Discipline is your only oxygen now."},
    "Galactic": {"state": "Systemic", "color": "#D946EF", "desc": "Your thoughts have become a unified structure. You are a system now."},
    "Ethereal": {"state": "Transcendent", "color": "#FFFFFF", "desc": "The boundary between observer and observed has vanished. Complete clarity."}
}

def get_vault():
    if not os.path.exists(VAULT_PATH):
        with open(VAULT_PATH, 'w') as f: json.dump({"users": {}}, f)
    with open(VAULT_PATH, 'r') as f: return json.load(f)

def save_vault(data):
    with open(VAULT_PATH, 'w') as f: json.dump(data, f, indent=4)

def calculate_prestige(points, last_seen_str):
    today = date.today()
    try: last_seen = datetime.strptime(last_seen_str, '%Y-%m-%d').date()
    except: last_seen = today
    penalty = max(0, (today - last_seen).days - 1)
    adj_pts = max(0, points - penalty)
    config = [("Observer", 3, 2), ("Moonwalker", 3, 2), ("Stellar", 4, 3), 
              ("Celestial", 4, 3), ("Interstellar", 5, 4), ("Galactic", 5, 4), ("Ethereal", 5, 8)]
    temp_pts = adj_pts
    for i, (name, level_count, req) in enumerate(config):
        rank_total = level_count * req
        if temp_pts >= rank_total:
            if name == "Ethereal": return name, "I", adj_pts, 0, "Max"
            temp_pts -= rank_total
        else:
            sn = req - (temp_pts % req)
            sub = level_count - (temp_pts // req)
            rom = {5:"V", 4:"IV", 3:"III", 2:"II", 1:"I"}
            nr = config[i+1][0] if (sub == 1 and i < len(config)-1) else name
            return name, rom.get(sub, "V"), adj_pts, sn, nr
    return "Observer", "V", adj_pts, 2, "Observer"

@app.route('/')
def index(): return render_template('index.html' if 'user' in session else 'auth.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    uid = data.get('user_id', '').strip().lower()
    vault = get_vault()
    if uid in vault['users'] and vault['users'][uid]['password'] == data.get('password'):
        session['user'] = uid
        return jsonify({"success": True})
    return jsonify({"success": False}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    uid = data.get('user_id', '').strip().lower()
    vault = get_vault()
    if uid in vault['users']: return jsonify({"success": False}), 400
    vault['users'][uid] = {
        "name": data.get('name'), "password": data.get('password'),
        "birthday": data.get('birthday'), "fav_color": data.get('fav_color'),
        "points": 0, "stars": [], "history": {}, "last_seen": str(date.today())
    }
    save_vault(vault)
    session['user'] = uid
    return jsonify({"success": True})

@app.route('/api/data')
def get_data():
    if 'user' not in session: return jsonify({})
    vault = get_vault()
    u = vault['users'][session['user']]
    rn, rs, pts, sn, nr = calculate_prestige(u['points'], u['last_seen'])
    
    # Emotional detection
    mood = "neutral"
    if u['history']:
        last = list(u['history'].values())[-1]
        if last.get('sig', 5) >= 8: mood = "happy"
        elif last.get('sig', 5) <= 3: mood = "blue"

    return jsonify({
        "name": u.get('name'), "rank": rn, "level": rs, "points": pts,
        "history": u['history'], "stars": u['stars'], "mood": mood,
        "rank_info": RANK_DATA[rn], "next_rank": nr, "stars_needed": sn,
        "all_ranks": RANK_DATA
    })

@app.route('/api/process', methods=['POST'])
def process():
    if 'user' not in session: return jsonify({"error": "Auth"}), 401
    vault = get_vault()
    u = vault['users'][session['user']]
    msg = request.json.get('message', '')
    sys = f"Celi. User: {u.get('name')}. Smart-casual, witty, empathetic advisor. Mirror the truth. JSON: {{'reply':'...', 'color':'#hex', 'sig':1-10}}"
    res = requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
        json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": sys}, {"role": "user", "content": msg}], "response_format": {"type": "json_object"}})
    ai = json.loads(res.json()['choices'][0]['message']['content'])
    u['points'] += 1
    u['last_seen'] = str(date.today())
    u['history'][str(time.time())] = {"user_msg": msg, "reply": ai['reply'], "color": ai['color'], "ts": time.time(), "sig": ai.get('sig', 5)}
    save_vault(vault)
    return jsonify(ai)

@app.route('/api/logout')
def logout(): session.clear(); return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
