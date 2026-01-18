import os, requests, json, time, random, uuid
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = "celi_sovereign_v10.26_profile_master"
VAULT_PATH = 'vault.json'
TRIVIA_PATH = 'trivia.json'

# --- RANK CONFIG (UNCHANGED from v10.25) ---
RANK_CONFIG = [
    {"name": "Observer", "levels": 3, "stars_per_lvl": 2, "threshold": 6, "phase": "The Awakening Phase", "theme": "Light, Eyes, Perception", "synthesis": "Like the first light striking a lens, you are beginning to perceive your thoughts."},
    {"name": "Moonwalker", "levels": 3, "stars_per_lvl": 2, "threshold": 12, "phase": "The Awakening Phase", "theme": "The Moon, Craters, Tides", "synthesis": "The ego functions as a satellite. You are learning to navigate the quiet landscape."},
    {"name": "Celestial", "levels": 4, "stars_per_lvl": 3, "threshold": 24, "phase": "The Ignition Phase", "theme": "Planetary Orbits, Mechanics", "synthesis": "You have entered a stable orbit. The flux of the self is now governed by higher purpose."},
    {"name": "Stellar", "levels": 4, "stars_per_lvl": 3, "threshold": 36, "phase": "The Ignition Phase", "theme": "Stars, The Sun, Fusion", "synthesis": "Nuclear fusion has commenced. Your internal values are generating enough gravity."},
    {"name": "Interstellar", "levels": 5, "stars_per_lvl": 4, "threshold": 56, "phase": "The Expansion Phase", "theme": "Nebulas, Void, Voyager", "synthesis": "You are pushing beyond the boundaries of your past identity."},
    {"name": "Galactic", "levels": 5, "stars_per_lvl": 4, "threshold": 76, "phase": "The Expansion Phase", "theme": "Milky Way, Black Holes", "synthesis": "You are no longer a single star, but a system of billions."},
    {"name": "Ethereal", "levels": 5, "stars_per_lvl": 8, "threshold": 116, "phase": "The Singularity", "theme": "Universe, Quantum, Entropy", "synthesis": "Singularity achieved. You are the cosmos experiencing itself."}
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

# --- ROUTES ---

@app.route('/api/data')
def get_data():
    if 'user' not in session: return jsonify({})
    v = get_vault(); u = v['users'][session['user']]
    pts = u.get('points', 0)
    
    # RANK CALCULATION
    current_rank_name = "Observer"
    current_roman = "III"
    current_prog = 0
    current_syn = ""
    current_phase = ""
    cumulative = 0
    
    for rank in RANK_CONFIG:
        start_pts = cumulative
        end_pts = rank['threshold']
        if pts < end_pts:
            current_rank_name = rank['name']
            current_syn = rank['synthesis']
            current_phase = rank['phase']
            pts_in_rank = pts - start_pts
            stars_per = rank['stars_per_lvl']
            level_idx = pts_in_rank // stars_per
            romans = ["I", "II", "III", "IV", "V"] 
            # Logic: If levels=3, index 0=III, 1=II, 2=I. 
            # We map level_idx (0,1,2) to reversed roman list
            # Need strict mapping based on total levels
            max_lvl = rank['levels'] # e.g., 3
            # Current level number (descending): max_lvl - level_idx
            # e.g., 3 - 0 = 3 (III). 3 - 1 = 2 (II).
            current_lvl_num = max(1, max_lvl - int(level_idx))
            
            # Map int to Roman
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
        current_syn = RANK_CONFIG[-1]['synthesis']
        current_phase = RANK_CONFIG[-1]['phase']

    # PSYCHO-ANALYSIS MOCKUP (In real app, AI generates this from journal history)
    # Simple logic based on entry count
    entry_count = len(u.get('history', {}))
    if entry_count < 5:
        analysis = "Signal faint. Your identity is still forming in the nebula. More data required for full diagnostic."
    elif entry_count < 20:
        analysis = "Patterns emerging. You show a tendency towards introspection, though solar flares of emotion occasionally disrupt your orbit."
    else:
        analysis = "Stable trajectory confirm. You are navigating chaos with increasing gravity. Your core values are becoming a reliable navigation system."

    return jsonify({
        "username": session['user'],
        "user_id": u.get('user_id', 'Unknown'),
        "birthday": u.get('birthday', 'Unset'),
        "fav_color": u.get('fav_color', ' #00f2fe'), # Default Cyan
        "points": pts, 
        "rank": f"{current_rank_name} {current_roman}",
        "rank_pure": current_rank_name,
        "rank_roman": current_roman,
        "phase": current_phase,
        "rank_progress": current_prog,
        "rank_synthesis": current_syn,
        "history": u.get('history', {}), 
        "unlocked_trivias": u.get('unlocked_trivias', []),
        "celi_analysis": analysis,
        "rank_config": RANK_CONFIG
    })

@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    if 'user' not in session: return jsonify({"status": "error"})
    v = get_vault(); u = v['users'][session['user']]
    data = request.json
    u['birthday'] = data.get('birthday')
    u['fav_color'] = data.get('fav_color')
    save_vault(v)
    return jsonify({"status": "success"})

@app.route('/api/delete_user', methods=['POST'])
def delete_user():
    if 'user' not in session: return jsonify({"status": "error"})
    v = get_vault()
    del v['users'][session['user']]
    save_vault(v)
    session.clear()
    return jsonify({"status": "success"})

# --- STANDARD ROUTES (Trivia, Process, Login) UNCHANGED ---
# (Keeping them brief for the report, assume identical to v10.25)
@app.route('/api/trivia')
def get_trivia():
    # ... (Same logic) ...
    return jsonify({"trivia": "The stars align."}) # Placeholder for brevity

@app.route('/api/process', methods=['POST'])
def process():
    # ... (Same logic) ...
    v = get_vault(); u = v['users'][session['user']]
    data = request.json
    u['points'] = u.get('points', 0) + 1
    save_vault(v)
    return jsonify({"reply": "Orbit stabilized.", "summary": "Log accepted."}) 

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user'] = request.form['username']
        v = get_vault()
        if session['user'] not in v['users']:
            # Initialize User
            v['users'][session['user']] = {
                "points": 0, 
                "void_count": 0, 
                "history": {}, 
                "unlocked_trivias": [],
                "user_id": str(uuid.uuid4())[:8].upper(), # Generate Short ID
                "birthday": "Unset",
                "fav_color": "#00f2fe"
            }
            save_vault(v)
        return redirect(url_for('home'))
    return render_template('auth.html')

@app.route('/')
def home():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
    
