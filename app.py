import os, requests, json, time, random
from flask import Flask, render_template, request, jsonify, session
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.secret_key = "celi_fchq_production_2026_v6"
app.permanent_session_lifetime = timedelta(days=30)

VAULT_PATH = 'vault.json'

CONSTELLATIONS = [
    {"name": "Lyra", "stars": 5, "trivia": "Lyra represents the lyre of Orpheus.", "star_names": ["Vega", "Zeta", "Sheliak", "Sulafat", "Delta"]},
    {"name": "Cygnus", "stars": 9, "trivia": "The Northern Cross swan.", "star_names": ["Deneb", "Albireo", "Sadr", "Gienah", "Azelfafage", "Rukh", "Fawaris", "Al Fawaris", "Theta"]},
    {"name": "Orion", "stars": 12, "trivia": "The Hunter's belt.", "star_names": ["Betelgeuse", "Rigel", "Bellatrix", "Mintaka", "Alnilam", "Alnitak", "Saiph", "Meissa", "Hatysa", "Nair al Saif", "Thabit", "Tabit"]}
]

MOOD_COLORS = {
    "Joyful": "#FFD700", "Anxious": "#A855F7", "Melancholy": "#4facfe",
    "Grateful": "#00f2fe", "Angry": "#ff4b2b", "Peaceful": "#89f7fe", "Determined": "#667eea"
}

RANK_DATA = {
    "Observer": {"color": "#3B82F6"}, "Moonwalker": {"color": "#94A3B8"},
    "Stellar": {"color": "#F59E0B"}, "Celestial": {"color": "#06B6D4"},
    "Interstellar": {"color": "#8B5CF6"}, "Galactic": {"color": "#D946EF"},
    "Ethereal": {"color": "#FFFFFF"}
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
    
    config = [("Observer", 3, 2), ("Moonwalker", 3, 2), ("Stellar", 4, 3), 
              ("Celestial", 4, 3), ("Interstellar", 5, 4), ("Galactic", 5, 4), ("Ethereal", 5, 8)]
    
    temp_pts = adj_pts
    for i, (name, level_count, req) in enumerate(config):
        rank_total = level_count * req
        if temp_pts >= rank_total:
            if name == "Ethereal": return name, "I", adj_pts, 100
            temp_pts -= rank_total
        else:
            prog = (temp_pts / rank_total) * 100
            sub = level_count - (temp_pts // req)
            rom = {5:"V", 4:"IV", 3:"III", 2:"II", 1:"I"}
            return name, rom.get(sub, "V"), adj_pts, prog
    return "Observer", "V", 0, 0

@app.route('/')
def index(): return render_template('index.html' if 'user' in session else 'auth.html')

@app.route('/api/data')
def get_data():
    if 'user' not in session: return jsonify({})
    v = get_vault(); u = v['users'][session['user']]
    rn, rs, pts, prog = calculate_prestige(u['points'], u['last_seen'])
    return jsonify({
        "name": u.get('name'), "void_count": u.get('void_count', 0),
        "history": u['history'], "const_stars": u.get('const_stars', 0),
        "const_idx": u.get('const_idx', 0),
        "constellation": CONSTELLATIONS[min(u.get('const_idx', 0), len(CONSTELLATIONS)-1)],
        "completed": CONSTELLATIONS[:u.get('const_idx', 0)],
        "rank": rn, "level": rs, "progress": prog, "rank_color": RANK_DATA[rn]['color'],
        "needs_pulse": (date.today() - datetime.strptime(u['last_seen'], '%Y-%m-%d').date()).days >= 1
    })

@app.route('/api/process', methods=['POST'])
def process():
    if 'user' not in session: return jsonify({"error": "Auth"}), 401
    v = get_vault(); u = v['users'][session['user']]
    msg = request.json.get('message', '')
    c_idx = u.get('const_idx', 0)
    c_data = CONSTELLATIONS[min(c_idx, len(CONSTELLATIONS)-1)]
    star_name = c_data['star_names'][u['const_stars'] % len(c_data['star_names'])]

    sys = f"Celi. User: {u.get('name')}. Witty, heart-spoken advisor. JSON: {{'reply':'...', 'color':'#hex', 'mood':'OneWord', 'summary':'Short Essence'}}"
    res = requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
        json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": sys}, {"role": "user", "content": msg}], "response_format": {"type": "json_object"}})
    ai = json.loads(res.json()['choices'][0]['message']['content'])
    
    mood_color = MOOD_COLORS.get(ai['mood'], ai['color'])
    u['points'] += 1
    u['const_stars'] += 1
    u['last_seen'] = str(date.today())
    
    bonus = False
    if u['const_stars'] >= c_data['stars']:
        u['points'] += 2; u['const_idx'] += 1; u['const_stars'] = 0; bonus = True

    u['history'][str(time.time())] = {
        "user_msg": msg, "reply": ai['reply'], "color": mood_color, "ts": time.time(),
        "star": star_name, "mood": ai['mood'], "summary": ai['summary'], "date": str(date.today())
    }
    save_vault(v)
    return jsonify({**ai, "star_name": star_name, "star_color": mood_color, "bonus": bonus, "trivia": c_data['trivia'] if bonus else ""})

@app.route('/api/process_vent', methods=['POST'])
def process_vent():
    if 'user' not in session: return jsonify({"error": "Auth"}), 401
    v = get_vault(); u = v['users'][session['user']]
    u['void_count'] = u.get('void_count', 0) + 1
    save_vault(v)
    msg = request.json.get('message', '')
    sys = "Celi. Friend/Advisor. User is venting. Provide witty, heart-spoken comfort. JSON: {'reply':'...'}"
    res = requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
        json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": sys}, {"role": "user", "content": msg}], "response_format": {"type": "json_object"}})
    return res.json()['choices'][0]['message']['content']

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
