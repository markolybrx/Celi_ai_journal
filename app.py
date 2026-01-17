import os, requests, json, time, math
from flask import Flask, render_template, request, jsonify, session
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.secret_key = "celi_voyager_fchq_2026"
app.permanent_session_lifetime = timedelta(days=30)

VAULT_PATH = 'vault.json'

def get_vault():
    if not os.path.exists(VAULT_PATH):
        with open(VAULT_PATH, 'w') as f: json.dump({"users": {}}, f)
    with open(VAULT_PATH, 'r') as f: return json.load(f)

def save_vault(data):
    with open(VAULT_PATH, 'w') as f: json.dump(data, f, indent=4)

@app.route('/')
def index(): return render_template('index.html' if 'user' in session else 'auth.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    uid = data.get('user_id', '').strip().lower()
    vault = get_vault()
    
    if uid in vault['users']:
        # If user exists, check password (Simple logic for this version)
        if vault['users'][uid].get('password') == data.get('password'):
            session['user'] = uid
            return jsonify({"success": True, "mode": "login"})
        return jsonify({"success": False, "error": "Incorrect password"}), 401

    # New Registration
    vault['users'][uid] = {
        "name": data.get('name'),
        "password": data.get('password'),
        "birthday": data.get('birthday'),
        "fav_color": data.get('fav_color'),
        "points": 0,
        "stars": [],
        "history": {},
        "last_seen": str(date.today())
    }
    save_vault(vault)
    session['user'] = uid
    return jsonify({"success": True, "mode": "register"})

@app.route('/api/birthday_trivia', methods=['POST'])
def birthday_trivia():
    bday = request.json.get('birthday')
    sys_msg = "You are Celi. Give a witty, short 1-sentence astronomical trivia related to this birth date (season, star signs, or space history). No emojis."
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": bday}]})
        return jsonify({"trivia": res.json()['choices'][0]['message']['content']})
    except: return jsonify({"trivia": "You were born under the infinite watch of the cosmos."})

# ... (Previous /api/data and /api/process routes remain same as v2.3) ...
