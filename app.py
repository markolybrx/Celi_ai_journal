import os, requests, json, time, math
from flask import Flask, render_template, request, jsonify, session
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.secret_key = "celi_voyager_fchq_2026"
app.permanent_session_lifetime = timedelta(days=30)

VAULT_PATH = 'vault.json'

RANK_DATA = {
    "Observer": {"desc": "Static. Noticing patterns of the inner sky.", "state": "Static", "color": "#3B82F6"},
    "Moonwalker": {"desc": "Detached. Gaining distance from old habits.", "state": "Detached", "color": "#94A3B8"},
    "Stellar": {"desc": "Ignited. Self-reflection is now a self-sustaining energy.", "state": "Ignited", "color": "#F59E0B"},
    "Celestial": {"desc": "Navigational. Understanding emotional mechanics.", "state": "Navigational", "color": "#06B6D4"},
    "Interstellar": {"desc": "Voyaging. Navigating the deep void with discipline.", "state": "Voyaging", "color": "#8B5CF6"},
    "Galactic": {"desc": "Systemic. Managing history as a unified structure.", "state": "Systemic", "color": "#D946EF"},
    "Ethereal": {"desc": "Transcendent. The boundary is gone.", "state": "Transcendent", "color": "#FFFFFF"}
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
    penalty = max(0, (today - last_seen).days - 1)
    adj_pts = max(0, points - penalty)
    
    config = [("Observer", 3, 2), ("Moonwalker", 3, 2), ("Stellar", 4, 3), ("Celestial", 4, 3), ("Interstellar", 5, 4), ("Galactic", 5, 4), ("Ethereal", 5, 8)]
    temp_pts = adj_pts
    for i, (name, level_count, req) in enumerate(config):
        rank_total = level_count * req
        if temp_pts >= rank_total:
            if name == "Ethereal": return name, "I", adj_pts, 0, "Max"
            temp_pts -= rank_total
        else:
            stars_needed = req - (temp_pts % req)
            sub_idx = level_count - (temp_pts // req)
            roman = {5:"V", 4:"IV", 3:"III", 2:"II", 1:"I"}
            next_rank = config[i+1][0] if (sub_idx == 1 and i < len(config)-1) else name
            return name, roman.get(sub_idx, "V"), adj_pts, stars_needed, next_rank
    return "Observer", "V", adj_pts, 2, "Observer"

@app.route('/')
def index(): return render_template('index.html' if 'user' in session else 'auth.html')

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
    rn, rs, pts, sn, nr = calculate_prestige(user_data['points'], user_data['last_seen'])
    msg = request.json.get('message', '')
    sys_msg = f"Celi here. User: {session['user']}. Rank: {rn} {rs}. Be brutally honest but empathetic. Return JSON: {{'reply':'...', 'color':'#hex', 'sig': 1-10}}"
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": msg}], "response_format": {"type": "json_object"}})
        ai = json.loads(res.json()['choices'][0]['message']['content'])
        user_data['points'] = pts + 1
        user_data['last_seen'] = str(date.today())
        user_data['stars'].append({"color": ai['color'], "x": 10+(time.time()*7%80), "y": 20+(time.time()*3%60)})
        user_data['history'][str(time.time())] = {"user_msg": msg, "reply": ai['reply'], "color": ai['color'], "ts": time.time(), "sig": ai.get('sig', 5)}
        save_vault(vault)
        return jsonify(ai)
    except: return jsonify({"reply": "The void is heavy.", "color": "#ff4444"})

@app.route('/api/data')
def get_data():
    if 'user' not in session: return jsonify({})
    vault = get_vault()
    u = vault['users'][session['user']]
    rn, rs, pts, sn, nr = calculate_prestige(u['points'], u['last_seen'])
    
    # Calculate Star DNA (History of colors)
    dna = {}
    for s in u['stars']:
        dna[s['color']] = dna.get(s['color'], 0) + 1
    
    return jsonify({
        "user_id": session['user'], "rank": rn, "level": rs, "history": u['history'], 
        "stars": u['stars'], "theme": RANK_DATA[rn], "next_rank": nr, 
        "stars_needed": sn, "dna": dna
    })

@app.route('/api/memory_summary')
def memory_summary():
    if 'user' not in session: return jsonify({"error": "Unauthorized"}), 401
    vault = get_vault()
    h = "\n".join([x['user_msg'] for x in vault['users'][session['user']]['history'].values()])
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": "Analyze user journey. No emojis."}, {"role": "user", "content": h}]})
        return jsonify({"summary": res.json()['choices'][0]['message']['content']})
    except: return jsonify({"summary": "Analyzing fragments..."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
