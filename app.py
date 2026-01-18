import os, json, time, random, uuid
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import date
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = "celi_ai_v1.3.0_anchor_build"
VAULT_PATH = 'vault.json'
TRIVIA_PATH = 'trivia.json'

# --- GEMINI CONFIGURATION ---
model = None
try:
    GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
    if GEMINI_KEY:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash', 
            generation_config={"response_mime_type": "application/json"})
    else:
        print("WARNING: GEMINI_API_KEY missing. AI in Simulation Mode.")
except Exception as e:
    print(f"AI INIT ERROR: {e}")

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

# --- AI ENGINE ---
def analyze_user_soul(user_data):
    if not model: return "Simulation Mode: Trajectory stable."
    
    history = user_data.get('history', {})
    if len(history) < 3: return "Data insufficient. Continue journaling to form a behavioral model."
    
    recent_logs = list(history.values())[-10:]
    summaries = [log.get('summary', '') for log in recent_logs]
    
    prompt = f"""
    You are Celi, an AI Sovereign. Analyze this user.
    User Context: Birthday {user_data.get('birthday')}, Color {user_data.get('fav_color')}.
    Journal History: {summaries}
    
    Output a JSON object with a single key 'analysis'.
    The value should be a deep, witty, compassionate psychological summary (max 40 words).
    """
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)['analysis']
    except: return "Neural synchronization interrupted."

def generate_live_trivia(rank_name, rank_theme):
    if not model: return "The stars are silent (No API Key)."
    prompt = f"Generate ONE short scientific trivia fact about: {rank_theme}. Output JSON with key 'text'. Max 20 words."
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)['text']
    except: return "The cosmos is quiet."

def sanitize_user_data(u):
    changed = False
    defaults = {
        "points": 0, "void_count": 0, "history": {}, "unlocked_trivias": [],
        "user_id": str(uuid.uuid4())[:8].upper(), "birthday": "Unset", "fav_color": "#00f2fe",
        "profile_pic": "", "celi_analysis": "Awaiting data..."
    }
    for key, val in defaults.items():
        if key not in u or u[key] is None:
            u[key] = val
            changed = True
    return changed

def get_rank_info(pts):
    for rank in RANK_CONFIG:
        if pts < rank['threshold']: return rank['name'], rank['theme']
    return "Ethereal", RANK_CONFIG[-1]['theme']

# --- ROUTES ---
@app.route('/api/trivia')
def get_trivia():
    try:
        if 'user' not in session: return jsonify({"trivia": "Connecting..."})
        v = get_vault(); u = v['users'][session['user']]
        if sanitize_user_data(u): save_vault(v)
        
        rank_name, rank_theme = get_rank_info(u.get('points', 0))
        full_db = get_trivia_db()
        available = [t for t in full_db if t['rank'] == rank_name and t['text'] not in u['unlocked_trivias']]
        
        if available: fact = random.choice(available)['text']
        else: fact = generate_live_trivia(rank_name, rank_theme)

        if fact not in u['unlocked_trivias']:
            u['unlocked_trivias'].append(fact)
            save_vault(v)
        return jsonify({"trivia": fact})
    except: return jsonify({"trivia": "Stellar silence."})

@app.route('/api/data')
def get_data():
    try:
        if 'user' not in session: return jsonify({"status": "guest"})
        v = get_vault()
        if session['user'] not in v['users']: return jsonify({"status": "guest"})
        
        u = v['users'][session['user']]
        if sanitize_user_data(u): save_vault(v)
        
        pts = u.get('points', 0)
        current_rank_name, current_roman, current_prog, current_phase = "Observer", "III", 0, ""
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
            "status": "ok",
            "username": session['user'],
            "user_id": u.get('user_id'),
            "birthday": u.get('birthday'),
            "fav_color": u.get('fav_color'),
            "profile_pic": u.get('profile_pic'),
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
    except Exception as e:
        print(f"DATA ERROR: {e}")
        return jsonify({"status": "error"})

@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    try:
        v = get_vault(); u = v['users'][session['user']]
        data = request.json
        if 'birthday' in data: u['birthday'] = data['birthday']
        if 'fav_color' in data: u['fav_color'] = data['fav_color']
        if 'profile_pic' in data: u['profile_pic'] = data['profile_pic']
        u['celi_analysis'] = analyze_user_soul(u)
        save_vault(v)
        return jsonify({"status": "success"})
    except: return jsonify({"status": "error"})

@app.route('/api/delete_user', methods=['POST'])
def delete_user():
    try:
        v = get_vault(); del v['users'][session['user']]; save_vault(v)
        session.clear()
        return jsonify({"status": "success"})
    except: return jsonify({"status": "error"})

@app.route('/api/process', methods=['POST'])
def process():
    try:
        v = get_vault(); u = v['users'][session['user']]
        sanitize_user_data(u)
        data = request.json
        
        if not model:
            ai_data = {"summary": "Simulated Log", "reply": "I hear you. (Gemini Key Missing)"}
        else:
            prompt = f"""
            System: You are Celi. Heart-spoken, witty, empathetic. A shoulder to cry on.
            User Input: {data.get('message')}
            Task: Reply to the user and summarize their input.
            Output JSON: {{ "reply": "...", "summary": "..." }}
            """
            response = model.generate_content(prompt)
            ai_data = json.loads(response.text)

        if data.get('mode') != 'rant': u['points'] = u.get('points', 0) + 1
        else: u['void_count'] = u.get('void_count', 0) + 1
        
        u['history'][str(time.time())] = {"summary": ai_data['summary'], "reply": ai_data['reply'], "date": str(date.today()), "type": "rant" if data.get('mode') == 'rant' else "journal"}
        save_vault(v)
        return jsonify(ai_data)
    except Exception as e: 
        print(f"CHAT ERROR: {e}")
        return jsonify({"reply": "Static noise... (Error)", "summary": "Error"})

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
