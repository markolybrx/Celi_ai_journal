import os, requests, json, time, random
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = "celi_sovereign_v10.25_phase_logic"
VAULT_PATH = 'vault.json'
TRIVIA_PATH = 'trivia.json'

# REVISED RANK LOGIC: Descending Levels
# levels: The max roman numeral (e.g., 3 means start at III, end at I)
# threshold: Cumulative points to complete the ENTIRE rank
RANK_CONFIG = [
    # THE AWAKENING PHASE
    {"name": "Observer", "levels": 3, "stars_per_lvl": 2, "threshold": 6, "phase": "The Awakening Phase", "theme": "Light, Eyes, Perception", "synthesis": "Like the first light striking a lens, you are beginning to perceive your thoughts."},
    {"name": "Moonwalker", "levels": 3, "stars_per_lvl": 2, "threshold": 12, "phase": "The Awakening Phase", "theme": "The Moon, Craters, Tides", "synthesis": "The ego functions as a satellite. You are learning to navigate the quiet landscape."},
    
    # THE IGNITION PHASE
    {"name": "Celestial", "levels": 4, "stars_per_lvl": 3, "threshold": 24, "phase": "The Ignition Phase", "theme": "Planetary Orbits, Mechanics", "synthesis": "You have entered a stable orbit. The flux of the self is now governed by higher purpose."},
    {"name": "Stellar", "levels": 4, "stars_per_lvl": 3, "threshold": 36, "phase": "The Ignition Phase", "theme": "Stars, The Sun, Fusion", "synthesis": "Nuclear fusion has commenced. Your internal values are generating enough gravity."},
    
    # THE EXPANSION PHASE
    {"name": "Interstellar", "levels": 5, "stars_per_lvl": 4, "threshold": 56, "phase": "The Expansion Phase", "theme": "Nebulas, Void, Voyager", "synthesis": "You are pushing beyond the boundaries of your past identity."},
    {"name": "Galactic", "levels": 5, "stars_per_lvl": 4, "threshold": 76, "phase": "The Expansion Phase", "theme": "Milky Way, Black Holes", "synthesis": "You are no longer a single star, but a system of billions."},
    
    # THE SINGULARITY
    {"name": "Ethereal", "levels": 5, "stars_per_lvl": 8, "threshold": 116, "phase": "The Singularity", "theme": "Universe, Quantum, Entropy", "synthesis": "Singularity achieved. You are the cosmos experiencing itself."}
]

def get_vault():
    if not os.path.exists(VAULT_PATH):
        with open(VAULT_PATH, 'w') as f: json.dump({"users": {}}, f)
    with open(VAULT_PATH, 'r') as f: return json.load(f)

def get_trivia_db():
    if not os.path.exists(TRIVIA_PATH):
        with open(TRIVIA_PATH, 'w') as f: json.dump([], f)
        return []
    with open(TRIVIA_PATH, 'r') as f: return json.load(f)

def save_trivia_db(data):
    with open(TRIVIA_PATH, 'w') as f: json.dump(data, f, indent=4)

def save_vault(data):
    with open(VAULT_PATH, 'w') as f: json.dump(data, f, indent=4)

def get_rank_info(pts):
    for rank in RANK_CONFIG:
        if pts < rank['threshold']:
            return rank['name'], rank['theme']
    return "Ethereal", RANK_CONFIG[-1]['theme']

def generate_live_trivia(rank_name, rank_theme):
    sys_prompt = f"You are Celi. Generate ONE short, fascinating scientific trivia fact about: {rank_theme}. Max 20 words. JSON only: {{'text': 'Fact'}}."
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": sys_prompt}], "response_format": {"type": "json_object"}})
        data = json.loads(res.json()['choices'][0]['message']['content'])
        new_fact = {"text": data['text'], "rank": rank_name}
        db = get_trivia_db()
        if not any(t['text'] == new_fact['text'] for t in db):
            db.append(new_fact)
            save_trivia_db(db)
        return new_fact['text']
    except:
        return "The cosmos is quiet today."

@app.route('/api/trivia')
def get_trivia():
    if 'user' not in session: return jsonify({"trivia": "Connecting..."})
    v = get_vault(); u = v['users'][session['user']]
    rank_name, rank_theme = get_rank_info(u.get('points', 0))
    full_db = get_trivia_db()
    unlocked = u.setdefault('unlocked_trivias', [])
    available = [t for t in full_db if t['rank'] == rank_name and t['text'] not in unlocked]
    
    if available: fact = random.choice(available)['text']
    else: fact = generate_live_trivia(rank_name, rank_theme)

    if fact not in unlocked:
        u['unlocked_trivias'].append(fact)
        save_vault(v)
    return jsonify({"trivia": fact})

@app.route('/api/data')
def get_data():
    if 'user' not in session: return jsonify({})
    v = get_vault(); u = v['users'][session['user']]
    pts = u.get('points', 0)
    
    # ADVANCED RANK CALCULATION
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
            # We are inside this rank
            current_rank_name = rank['name']
            current_syn = rank['synthesis']
            current_phase = rank['phase']
            
            # Calculate Level (Descending Logic)
            # Total points earned within this rank
            pts_in_rank = pts - start_pts
            total_levels = rank['levels']
            stars_per = rank['stars_per_lvl']
            
            # Which level index are we at? (0 = highest roman, e.g. III)
            level_idx = pts_in_rank // stars_per
            
            # Roman Numerals: III, II, I (or V, IV...)
            romans = ["I", "II", "III", "IV", "V"] # Index 0=I, 1=II...
            # If total_levels is 3, romans we want are: III(2), II(1), I(0)
            # Current Roman Index = (total_levels - 1) - level_idx
            roman_idx = max(0, (total_levels - 1) - int(level_idx))
            current_roman = romans[roman_idx]
            
            # Progress within the specific level
            pts_in_level = pts_in_rank % stars_per
            current_prog = (pts_in_level / stars_per) * 100
            break
            
        cumulative = end_pts
    else:
        # Cap at Ethereal
        current_rank_name = "Ethereal"
        current_roman = "I"
        current_prog = 100
        current_syn = RANK_CONFIG[-1]['synthesis']
        current_phase = RANK_CONFIG[-1]['phase']

    return jsonify({
        "username": session['user'],
        "points": pts, 
        "rank": f"{current_rank_name} {current_roman}",
        "rank_pure": current_rank_name,
        "rank_roman": current_roman,
        "phase": current_phase,
        "rank_progress": current_prog,
        "rank_synthesis": current_syn,
        "history": u.get('history', {}), 
        "unlocked_trivias": u.get('unlocked_trivias', []),
        "rank_config": RANK_CONFIG
    })

@app.route('/api/process', methods=['POST'])
def process():
    v = get_vault(); u = v['users'][session['user']]
    data = request.json
    is_rant = data.get('mode') == 'rant'
    sys = "You are Celi. Heart-spoken, witty, and empathetic. Mode-dependent persona. JSON ONLY."
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
        if session['user'] not in v['users']:
            v['users'][session['user']] = {"points": 0, "void_count": 0, "history": {}, "unlocked_trivias": []}
            save_vault(v)
        return redirect(url_for('home'))
    return render_template('auth.html')

@app.route('/')
def home():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
    
