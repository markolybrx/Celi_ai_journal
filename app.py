import os, requests, json, time, random
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = "celi_sovereign_v10.33_stable_core"
VAULT_PATH = 'vault.json'
TRIVIA_PATH = 'trivia.json'

RANK_CONFIG = [
    {"name": "Observer", "levels": 3, "stars_per_lvl": 2, "threshold": 6, "phase": "The Awakening Phase", "theme": "Light, Eyes, Perception"},
    {"name": "Moonwalker", "levels": 3, "stars_per_lvl": 2, "threshold": 12, "phase": "The Awakening Phase", "theme": "The Moon, Craters, Tides"},
    {"name": "Celestial", "levels": 4, "stars_per_lvl": 3, "threshold": 24, "phase": "The Ignition Phase", "theme": "Planetary Orbits, Mechanics"},
    {"name": "Stellar", "levels": 4, "stars_per_lvl": 3, "threshold": 36, "phase": "The Ignition Phase", "theme": "Stars, The Sun, Fusion"},
    {"name": "Interstellar", "levels": 5, "stars_per_lvl": 4, "threshold": 56, "phase": "The Expansion Phase", "theme": "Nebulas, Void, Voyager"},
    {"name": "Galactic", "levels": 5, "stars_per_lvl": 4, "threshold": 76, "phase": "The Expansion Phase", "theme": "Milky Way, Black Holes"},
    {"name": "Ethereal", "levels": 5, "stars_per_lvl": 8, "threshold": 116, "phase": "The Singularity", "theme": "Universe, Quantum, Entropy"}
]

def get_vault():
    if not os.path.exists(VAULT_PATH):
        with open(VAULT_PATH, 'w') as f: json.dump({"users": {}}, f)
    with open(VAULT_PATH, 'r') as f: return json.load(f)

def save_vault(data):
    with open(VAULT_PATH, 'w') as f: json.dump(data, f, indent=4)

def get_trivia_db():
    if not os.path.exists(TRIVIA_PATH):
        with open(TRIVIA_PATH, 'w') as f: json.dump([], f)
        return []
    with open(TRIVIA_PATH, 'r') as f: return json.load(f)

def save_trivia_db(data):
    with open(TRIVIA_PATH, 'w') as f: json.dump(data, f, indent=4)

# --- ROBUST DATA SANITIZATION ---
def sanitize_user(u):
    updated = False
    if "points" not in u: u["points"] = 0; updated = True
    if "history" not in u: u["history"] = {}; updated = True
    if "unlocked_trivias" not in u: u["unlocked_trivias"] = []; updated = True
    if "user_id" not in u: u["user_id"] = f"USR-{random.randint(1000,9999)}"; updated = True
    if "birthday" not in u: u["birthday"] = "Unset"; updated = True
    if "fav_color" not in u: u["fav_color"] = "#00f2fe"; updated = True
    return updated

def generate_trivia(theme):
    sys = f"Generate 1 short scientific fact about {theme}. Max 15 words. JSON: {{'text':'fact'}}."
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role":"system","content":sys}], "response_format":{"type":"json_object"}})
        return json.loads(r.json()['choices'][0]['message']['content'])['text']
    except: return "The stars are silent."

@app.route('/api/data')
def get_data():
    if 'user' not in session: return jsonify({})
    v = get_vault(); u = v['users'][session['user']]
    if sanitize_user(u): save_vault(v)
    
    pts = u['points']
    c_rank, c_roman, c_phase, c_prog, c_syn = "Ethereal", "I", "The Singularity", 100, ""
    
    cum = 0
    for r in RANK_CONFIG:
        if pts < r['threshold']:
            c_rank, c_phase, c_syn = r['name'], r['phase'], r.get('synthesis', '')
            pts_in = pts - cum
            # Roman Logic
            idx = pts_in // r['stars_per_lvl']
            roman_map = ["I", "II", "III", "IV", "V"]
            # Safe index access
            ridx = max(0, r['levels'] - 1 - int(idx))
            if ridx < len(roman_map): c_roman = roman_map[ridx]
            
            c_prog = ((pts_in % r['stars_per_lvl']) / r['stars_per_lvl']) * 100
            break
        cum = r['threshold']

    return jsonify({
        "username": session['user'],
        "user_id": u['user_id'],
        "birthday": u['birthday'],
        "fav_color": u['fav_color'],
        "points": pts,
        "rank": f"{c_rank} {c_roman}",
        "rank_pure": c_rank,
        "rank_roman": c_roman,
        "phase": c_phase,
        "rank_progress": c_prog,
        "rank_synthesis": c_syn,
        "history": u['history'],
        "unlocked_trivias": u['unlocked_trivias'],
        "rank_config": RANK_CONFIG
    })

@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    if 'user' not in session: return jsonify({})
    v = get_vault(); u = v['users'][session['user']]
    u['birthday'] = request.json.get('birthday')
    u['fav_color'] = request.json.get('fav_color')
    save_vault(v)
    return jsonify({"status":"ok"})

@app.route('/api/delete_user', methods=['POST'])
def delete_user():
    if 'user' not in session: return jsonify({})
    v = get_vault(); del v['users'][session['user']]; save_vault(v)
    session.clear()
    return jsonify({"status":"ok"})

@app.route('/api/trivia')
def get_trivia():
    if 'user' not in session: return jsonify({"trivia":"Loading..."})
    v = get_vault(); u = v['users'][session['user']]
    db = get_trivia_db()
    # Simple random selection or gen
    if not db: 
        t = generate_trivia("Stars")
        db.append({"text":t, "rank":"General"})
        save_trivia_db(db)
    
    fact = random.choice(db)['text']
    if fact not in u['unlocked_trivias']:
        u['unlocked_trivias'].append(fact)
        save_vault(v)
    return jsonify({"trivia": fact})

@app.route('/api/process', methods=['POST'])
def process():
    v = get_vault(); u = v['users'][session['user']]
    if request.json.get('mode') != 'rant': u['points'] += 1
    
    # Simple echo for speed/stability, replace with AI if needed
    u['history'][str(time.time())] = {"summary": "Log Entry", "reply": "Orbit updated.", "date": str(date.today()), "type": request.json.get('mode')}
    save_vault(v)
    return jsonify({"reply": "Noted in the stars.", "summary": "Log Entry"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user'] = request.form['username']
        v = get_vault()
        if session['user'] not in v['users']: v['users'][session['user']] = {} # Sanitized on read
        save_vault(v)
        return redirect(url_for('home'))
    return render_template('auth.html')

@app.route('/')
def home():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

if __name__ == '__main__': app.run(debug=True)
    
