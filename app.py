import os, requests, json, time, random, uuid
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = "celi_sovereign_v1.01.01_hotfix"
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

def sanitize_user_data(u):
    changed = False
    # Ensure ID exists
    if 'user_id' not in u: 
        u['user_id'] = str(uuid.uuid4())[:8].upper()
        changed = True
    # Ensure Analysis exists
    if 'celi_analysis' not in u: 
        u['celi_analysis'] = "Awaiting neural synchronization..."
        changed = True
    # Ensure basics
    defaults = {"points": 0, "void_count": 0, "history": {}, "unlocked_trivias": [], "birthday": "Unset", "fav_color": "#00f2fe"}
    for k, v in defaults.items():
        if k not in u:
            u[k] = v
            changed = True
    return changed

def get_rank_info(pts):
    for rank in RANK_CONFIG:
        if pts < rank['threshold']: return rank['name'], rank['theme']
    return "Ethereal", RANK_CONFIG[-1]['theme']

def analyze_user_soul(user_data):
    history = user_data.get('history', {})
    if not history: return "The void is silent. Begin your journey to form a signal."
    recent_logs = list(history.values())[-5:]
    summaries = [log.get('summary', 'Log') for log in recent_logs]
    
    sys_prompt = f"Analyze user based on journals: {summaries}. Max 30 words. Deep, witty, cosmic."
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": sys_prompt}], "max_tokens": 60})
        return res.json()['choices'][0]['message']['content']
    except: return "Atmospheric interference detected."

def generate_live_trivia(rank_name, rank_theme):
    sys = f"Generate ONE short scientific trivia fact about: {rank_theme}. Max 20 words. JSON only: {{'text': 'Fact'}}."
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": sys}], "response_format": {"type": "json_object"}})
        data = json.loads(res.json()['choices'][0]['message']['content'])
        new_fact = {"text": data['text'], "rank": rank_name}
        db = get_trivia_db()
        if not any(t['text'] == new_fact['text'] for t in db):
            db.append(new_fact)
            save_trivia_db(db)
        return new_fact['text']
    except: return "The cosmos is quiet."

@app.route('/api/trivia')
def get_trivia():
    if 'user' not in session: return jsonify({"trivia": "Connecting..."})
    v = get_vault(); u = v['users'][session['user']]
    if sanitize_user_data(u): save_vault(v)
    rank_name, rank_theme = get_rank_info(u.get('points', 0))
    full_db = get_trivia_db()
    unlocked = u.setdefault('unlocked_trivias', [])
    available = [t for t in full_db if t['rank'] == rank_name and t['text'] not in unlocked]
    fact = random.choice(available)['text'] if available else generate_live_trivia(rank_name, rank_theme)
    if fact not in unlocked:
        u['unlocked_trivias'].append(fact)
        save_vault(v)
    return jsonify({"trivia": fact})

@app.route('/api/data')
def get_data():
    if 'user' not in session: return jsonify({})
    v = get_vault(); u = v['users'][session['user']]
    if sanitize_user_data(u): save_vault(v)
    
    pts = u.get('points', 0)
    current_rank_name, current_roman, current_prog, current_phase = "Observer", "III", 0, "The Awakening Phase"
    cumulative = 0
    
    for rank in RANK_CONFIG:
        start_pts = cumulative
        end_pts = rank['threshold']
        if pts < end_pts:
            current_rank_name = rank['name']
            current_phase = rank['phase']
            pts_in_rank = pts - start_pts
            stars_per = rank['stars_per_lvl']
            
            level_idx = pts_in_rank // stars_per
            max_lvl = rank['levels']
            current_lvl_num = max(1, max_lvl - int(level_idx))
            roman_map = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}
            current_roman = roman_map.get(current_lvl_num, "I")
            
            pts_in_level = pts_in_rank % stars_per
            current_prog = (pts_in_level / stars_per) * 100
            break
        cumulative = end_pts
    else:
        current_rank_name = "Ethereal"
        current_roman = "I"
        current_prog = 100
        current_phase = RANK_CONFIG[-1]['phase']

    synthesis_map = {
        "Observer": "Like the first light striking a lens, you are beginning to perceive your thoughts.",
        "Moonwalker": "The ego functions as a satellite. You are learning to navigate the quiet landscape.",
        "Celestial": "You have entered a stable orbit. The flux of the self is governed by purpose.",
        "Stellar": "Nuclear fusion has commenced. Your internal values are generating gravity.",
        "Interstellar": "You are pushing beyond the boundaries, traveling through the vast vacuum.",
        "Galactic": "You are no longer a single star, but a system of billions.",
        "Ethereal": "Singularity achieved. You are the cosmos experiencing itself."
    }

    return jsonify({
        "username": session['user'],
        "user_id": u.get('user_id'),
        "birthday": u.get('birthday'),
        "fav_color": u.get('fav_color'),
        "points": pts, 
        "rank": f"{current_rank_name} {current_roman}",
        "rank_pure": current_rank_name,
        "rank_roman": current_roman,
        "phase": current_phase,
        "rank_progress": current_prog,
        "rank_synthesis": synthesis_map.get(current_rank_name, ""),
        "history": u.get('history', {}), 
        "unlocked_trivias": u.get('unlocked_trivias', []),
        "celi_analysis": u.get('celi_analysis'),
        "rank_config": RANK_CONFIG
    })

@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    if 'user' not in session: return jsonify({"status": "error"})
    v = get_vault(); u = v['users'][session['user']]
    data = request.json
    u['birthday'] = data.get('birthday')
    u['fav_color'] = data.get('fav_color')
    u['celi_analysis'] = analyze_user_soul(u)
    save_vault(v)
    return jsonify({"status": "success"})

@app.route('/api/delete_user', methods=['POST'])
def delete_user():
    if 'user' not in session: return jsonify({"status": "error"})
    v = get_vault()
    if session['user'] in v['users']: del v['users'][session['user']]; save_vault(v)
    session.clear()
    return jsonify({"status": "success"})

@app.route('/api/process', methods=['POST'])
def process():
    v = get_vault(); u = v['users'][session['user']]
    sanitize_user_data(u)
    data = request.json
    is_rant = data.get('mode') == 'rant'
    sys = "You are Celi. Heart-spoken, witty. JSON ONLY."
    res = requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
        json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": sys}, {"role": "user", "content": data.get('message')}], "response_format": {"type": "json_object"}})
    ai_data = json.loads(res.json()['choices'][0]['message']['content'])
    if not is_rant: u['points'] = u.get('points', 0) + 1
    else: u['void_count'] = u.get('void_count', 0) + 1
    u['history'][str(time.time())] = {"summary": ai_data['summary'], "reply": ai_data['reply'], "date": str(date.today()), "type": "rant" if is_rant else "journal"}
    save_vault(v)
    return jsonify(ai_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user'] = request.form['username']
        v = get_vault()
        if session['user'] not in v['users']: v['users'][session['user']] = {}; save_vault(v)
        return redirect(url_for('home'))
    return render_template('auth.html')

@app.route('/')
def home():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

if __name__ == '__main__': app.run(debug=True)
    
