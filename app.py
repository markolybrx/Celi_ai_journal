import os, requests, json, time, random
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import date, datetime

app = Flask(__name__)
# In production, use a secure, complex random key
app.secret_key = "celi_sovereign_v10.22_master_key"
VAULT_PATH = 'vault.json'
TRIVIA_PATH = 'trivia.json'

RANK_CONFIG = [
    {"name": "Observer", "threshold": 6, "theme": "Light, Eyes, Perception, Horizon", "synthesis": "Like the first light striking a lens, you are beginning to perceive your thoughts as distinct celestial objects rather than an indistinguishable void."},
    {"name": "Moonwalker", "threshold": 12, "theme": "The Moon, Craters, Tides, Silence", "synthesis": "The ego functions as a satellite. You are learning to navigate the quiet, cratered landscape of your internal world, finding beauty in the reflection of your own light."},
    {"name": "Stellar", "threshold": 24, "theme": "Stars, The Sun, Nuclear Fusion, Heat", "synthesis": "Nuclear fusion has commenced. Your internal values are generating enough gravity to form a permanent core, burning away the cold of external validation."},
    {"name": "Celestial", "threshold": 36, "theme": "Planetary Orbits, Mechanics, Gravity", "synthesis": "You have entered a stable orbit. The flux of the self is now governed by higher purpose, moving in harmony with the greater cosmic clockwork."},
    {"name": "Interstellar", "threshold": 56, "theme": "Nebulas, Void, Voyager, Distance", "synthesis": "You are pushing beyond the boundaries of your past identity, traveling through the vast vacuum between who you were and who you are becoming."},
    {"name": "Galactic", "threshold": 76, "theme": "Milky Way, Black Holes, Spiral Arms", "synthesis": "You are no longer a single star, but a system of billions. You manage the complex gravity of relationships, career, and spirit with the equilibrium of a rotating galaxy."},
    {"name": "Ethereal", "threshold": 116, "theme": "Universe, Big Bang, Quantum, Entropy", "synthesis": "Singularity achieved. The distinction between the observer and the universe has collapsed; you are the cosmos experiencing itself through a human lens."}
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
    # Live Explorer: Ask AI for a new fact if we run out
    sys_prompt = f"You are Celi. Generate ONE short, fascinating scientific trivia fact about: {rank_theme}. Max 20 words. JSON only: {{'text': 'Fact'}}."
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": sys_prompt}], "response_format": {"type": "json_object"}})
        
        data = json.loads(res.json()['choices'][0]['message']['content'])
        new_fact = {"text": data['text'], "rank": rank_name}
        
        # Save to DB so we don't have to ask again next time
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
    
    # 1. Check Local DB
    full_db = get_trivia_db()
    unlocked = u.setdefault('unlocked_trivias', [])
    available = [t for t in full_db if t['rank'] == rank_name and t['text'] not in unlocked]
    
    # 2. Get Fact (Local or AI Generated)
    if available: fact = random.choice(available)['text']
    else: fact = generate_live_trivia(rank_name, rank_theme)

    # 3. Save to User History
    if fact not in unlocked:
        u['unlocked_trivias'].append(fact)
        save_vault(v)
    return jsonify({"trivia": fact})

@app.route('/api/data')
def get_data():
    if 'user' not in session: return jsonify({})
    v = get_vault(); u = v['users'][session['user']]
    pts = u.get('points', 0)
    
    # Calculate Display Data
    current_rank = "Observer"
    current_prog = 0
    current_syn = ""
    for i, rank in enumerate(RANK_CONFIG):
        if pts < rank['threshold']:
            prev = RANK_CONFIG[i-1]['threshold'] if i > 0 else 0
            current_rank = rank['name']
            current_prog = ((pts - prev) / (rank['threshold'] - prev)) * 100
            current_syn = rank['synthesis']
            break
    else:
        current_rank = "Ethereal"
        current_prog = 100
        current_syn = RANK_CONFIG[-1]['synthesis']

    return jsonify({
        "username": session['user'],
        "points": pts, 
        "rank": current_rank,
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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
    
