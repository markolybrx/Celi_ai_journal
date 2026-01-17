import os, requests, json, time
from flask import Flask, render_template, request, jsonify, session
from datetime import date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "celi_fchq_stable_2026"
app.permanent_session_lifetime = timedelta(days=30)

VAULT_PATH = 'vault.json'

CONSTELLATIONS = [
    {"name": "Lyra", "stars": 5, "trivia": "Lyra represents the lyre of Orpheus. Its brightest star, Vega, was the first star ever photographed!", "star_names": ["Vega", "Zeta", "Sheliak", "Sulafat", "Delta"]},
    {"name": "Cygnus", "stars": 9, "trivia": "Cygnus, the Swan, contains one of the strongest radio sources in the sky: Cygnus A.", "star_names": ["Deneb", "Albireo", "Sadr", "Gienah", "Azelfafage", "Rukh", "Fawaris", "Al Fawaris", "Theta"]}
]

MOOD_COLORS = {
    "Joyful": "#FFD700", "Anxious": "#A855F7", "Melancholy": "#4facfe",
    "Grateful": "#00f2fe", "Angry": "#ff4b2b", "Peaceful": "#89f7fe", "Determined": "#667eea"
}

def get_vault():
    if not os.path.exists(VAULT_PATH):
        with open(VAULT_PATH, 'w') as f: json.dump({"users": {}}, f)
    with open(VAULT_PATH, 'r') as f: return json.load(f)

def save_vault(data):
    with open(VAULT_PATH, 'w') as f: json.dump(data, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html') if 'user' in session else render_template('auth.html')

@app.route('/api/auth', methods=['POST'])
def api_auth():
    data = request.json
    u_name = data.get('username', '').strip()
    u_pass = data.get('password', '')
    a_type = data.get('type')
    vault = get_vault()
    
    if a_type == 'register':
        if u_name in vault['users']: return jsonify({"error": "Identity already taken"}), 400
        vault['users'][u_name] = {
            "password": generate_password_hash(u_pass), "name": u_name,
            "points": 0, "void_count": 0, "const_stars": 0, "const_idx": 0,
            "last_seen": str(date.today()), "history": {}
        }
        save_vault(vault)
        return jsonify({"message": "Identity registered successfully. You may now log in."})
    else:
        user = vault['users'].get(u_name)
        if user and check_password_hash(user['password'], u_pass):
            session['user'] = u_name
            session.permanent = True
            return jsonify({"message": "Welcome back, Observer."})
        return jsonify({"error": "Invalid Identity or Passkey"}), 401

@app.route('/api/data')
def get_data():
    if 'user' not in session: return jsonify({})
    v = get_vault(); u = v['users'][session['user']]
    return jsonify({
        "name": u.get('name'), "void_count": u.get('void_count', 0),
        "history": u['history'], "const_stars": u.get('const_stars', 0),
        "const_idx": u.get('const_idx', 0),
        "constellation": CONSTELLATIONS[min(u.get('const_idx', 0), len(CONSTELLATIONS)-1)]
    })

@app.route('/api/process', methods=['POST'])
def process():
    if 'user' not in session: return jsonify({"error": "Auth"}), 401
    v = get_vault(); u = v['users'][session['user']]
    msg = request.json.get('message', '')
    
    c_idx = u.get('const_idx', 0)
    c_data = CONSTELLATIONS[min(c_idx, len(CONSTELLATIONS)-1)]
    star_name = c_data['star_names'][u['const_stars'] % len(c_data['star_names'])]

    sys = "You are Celi. Friendly, heart-spoken, and witty. Provide emotional support and insight. JSON: {'reply':'...', 'color':'#hex', 'mood':'OneWord', 'summary':'Short'}"
    res = requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
        json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": sys}, {"role": "user", "content": msg}], "response_format": {"type": "json_object"}})
    ai = json.loads(res.json()['choices'][0]['message']['content'])
    
    color = MOOD_COLORS.get(ai['mood'], ai['color'])
    u['const_stars'] += 1
    u['points'] += 1
    
    bonus = u['const_stars'] >= c_data['stars']
    trivia = c_data['trivia'] if bonus else ""
    if bonus: u['const_idx'] += 1; u['const_stars'] = 0

    u['history'][str(time.time())] = {
        "user_msg": msg, "reply": ai['reply'], "color": color, "ts": time.time(),
        "star": star_name, "mood": ai['mood'], "summary": ai['summary'], "date": str(date.today())
    }
    save_vault(v)
    return jsonify({**ai, "star_name": star_name, "star_color": color, "bonus": bonus, "trivia": trivia})

@app.route('/api/process_vent', methods=['POST'])
def process_vent():
    v = get_vault(); u = v['users'][session['user']]
    u['void_count'] += 1
    save_vault(v)
    return jsonify({"reply": "The Void has taken it."})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
    
