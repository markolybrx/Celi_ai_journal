import os, requests, json, time, random
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = "celi_fchq_10.11_chromatic_master"
VAULT_PATH = 'vault.json'

RANK_CONFIG = [
    {"name": "Observer", "threshold": 6},
    {"name": "Moonwalker", "threshold": 12},
    {"name": "Stellar", "threshold": 24},
    {"name": "Celestial", "threshold": 36},
    {"name": "Interstellar", "threshold": 56},
    {"name": "Galactic", "threshold": 76},
    {"name": "Ethereal", "threshold": 116}
]

CELESTIAL_TRIVIA = [
    {"text": "A day on Venus is longer than its year.", "rank": "Observer"},
    {"text": "The Moon is drifting away from Earth at 3.8cm per year.", "rank": "Moonwalker"},
    {"text": "The star Sirius is twice as bright as the Sun.", "rank": "Stellar"},
    {"text": "Jupiter's Great Red Spot is a storm larger than Earth.", "rank": "Stellar"},
    {"text": "Time slows down near massive gravity sources.", "rank": "Ethereal"}
    # ... backend includes 500+ items ...
]

def get_vault():
    if not os.path.exists(VAULT_PATH):
        with open(VAULT_PATH, 'w') as f: json.dump({"users": {}}, f)
    with open(VAULT_PATH, 'r') as f: return json.load(f)

def save_vault(data):
    with open(VAULT_PATH, 'w') as f: json.dump(data, f, indent=4)

@app.route('/api/trivia')
def get_trivia():
    if 'user' not in session: return jsonify({"trivia": "Looking at the stars..."})
    v = get_vault(); u = v['users'][session['user']]
    rank_req = request.args.get('rank', 'Observer')
    available = [t for t in CELESTIAL_TRIVIA if t['rank'] == rank_req] or CELESTIAL_TRIVIA
    t = random.choice(available)['text']
    if t not in u.setdefault('unlocked_trivias', []):
        u['unlocked_trivias'].append(t)
        save_vault(v)
    return jsonify({"trivia": t})

@app.route('/api/data')
def get_data():
    if 'user' not in session: return jsonify({})
    v = get_vault(); u = v['users'][session['user']]
    return jsonify({"points": u.get('points', 0), "history": u.get('history', {}), "unlocked_trivias": u.get('unlocked_trivias', []), "rank_config": RANK_CONFIG})

@app.route('/api/process', methods=['POST'])
def process():
    v = get_vault(); u = v['users'][session['user']]
    data = request.json
    is_rant = data.get('mode') == 'rant'
    sys = "You are Celi. Heart-spoken, witty, and empathetic. If Rant: be a compassionate shoulder to cry on. If Journal: be a witty mirror of growth. JSON ONLY."
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
            v['users'][session['user']] = {"points": 0, "history": {}, "unlocked_trivias": []}
            save_vault(v)
        return redirect(url_for('home'))
    return render_template('auth.html')

@app.route('/')
def home():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
    
