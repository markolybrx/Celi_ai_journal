import os, json, time, random, uuid
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import date
import google.generativeai as genai
from pymongo import MongoClient
import certifi

app = Flask(__name__)
app.secret_key = "celi_ai_v1.6.6_json_auth"

# --- MONGODB ---
MONGO_URI = os.environ.get("MONGO_URI")
db = None; users_col = None
if MONGO_URI:
    try:
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        db = client.get_database("celi_db"); users_col = db.users
        print("MONGODB CONNECTED")
    except Exception as e: print(f"MONGO FAIL: {e}")

# --- AI ---
model = None
try:
    GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
    if GEMINI_KEY:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
except Exception as e: print(f"AI FAIL: {e}")

RANK_CONFIG = [
    {"name": "Observer", "levels": 3, "stars_per_lvl": 2, "threshold": 6, "phase": "The Awakening Phase"},
    {"name": "Moonwalker", "levels": 3, "stars_per_lvl": 2, "threshold": 12, "phase": "The Awakening Phase"},
    {"name": "Celestial", "levels": 4, "stars_per_lvl": 3, "threshold": 24, "phase": "The Ignition Phase"},
    {"name": "Stellar", "levels": 4, "stars_per_lvl": 3, "threshold": 36, "phase": "The Ignition Phase"},
    {"name": "Interstellar", "levels": 5, "stars_per_lvl": 4, "threshold": 56, "phase": "The Expansion Phase"},
    {"name": "Galactic", "levels": 5, "stars_per_lvl": 4, "threshold": 76, "phase": "The Expansion Phase"},
    {"name": "Ethereal", "levels": 5, "stars_per_lvl": 8, "threshold": 116, "phase": "The Singularity"}
]

# --- HELPERS ---
def get_user_data(username): return users_col.find_one({"username": username}) if users_col else None
def update_user_data(username, data): users_col.update_one({"username": username}, {"$set": data}) if users_col else None
def analyze_user_soul(user_data):
    if not model: return "Simulated Mode."
    hist = user_data.get('history', {})
    if len(hist) < 3: return "Data insufficient."
    logs = [l.get('summary','') for l in list(hist.values())[-5:]]
    try:
        res = model.generate_content(f"Analyze journals: {logs}. Output JSON: {{ 'analysis': 'Short witty summary.' }}")
        return json.loads(res.text)['analysis']
    except: return "Connection unstable."

# --- API ---
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json; username = data.get('reg_username')
        if users_col and users_col.find_one({"username": username}): return jsonify({"error": "Username taken"}), 400
        new_user = {
            "username": username, "password": data.get('reg_password'),
            "first_name": data.get('fname'), "last_name": data.get('lname'),
            "birthday": data.get('dob'), "secret_question": data.get('secret_question'),
            "secret_answer": data.get('secret_answer').lower().strip(),
            "fav_color": data.get('fav_color', '#00f2fe'), "user_id": str(uuid.uuid4())[:8].upper(),
            "points": 0, "void_count": 0, "history": {}, "unlocked_trivias": [], "profile_pic": "", "celi_analysis": "New Signal."
        }
        if users_col: users_col.insert_one(new_user); return jsonify({"status": "success"})
        return jsonify({"error": "DB Error"}), 500
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/recover', methods=['POST'])
def recover():
    try:
        d = request.json
        q = { "first_name": d.get('fname'), "last_name": d.get('lname'), "birthday": d.get('dob'), "secret_question": d.get('secret_question'), "secret_answer": d.get('secret_answer').lower().strip() }
        if users_col:
            u = users_col.find_one(q)
            if u: return jsonify({"status": "success", "username": u['username']})
            return jsonify({"error": "Identity verification failed"}), 404
        return jsonify({"error": "DB Error"}), 500
    except: return jsonify({"error": "Fail"}), 500

@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    try:
        d = request.json
        q = { "username": d.get('username'), "first_name": d.get('fname'), "last_name": d.get('lname'), "secret_answer": d.get('secret_answer').lower().strip() }
        if users_col:
            if users_col.find_one(q):
                users_col.update_one({"username": d.get('username')}, {"$set": {"password": d.get('new_password')}})
                return jsonify({"status": "success"})
            return jsonify({"error": "Security check failed"}), 403
        return jsonify({"error": "DB Error"}), 500
    except: return jsonify({"error": "Fail"}), 500

@app.route('/api/data')
def get_data():
    if 'user' not in session: return jsonify({"status": "guest"})
    u = get_user_data(session['user'])
    if not u: session.clear(); return jsonify({"status": "guest"})
    pts = u.get('points', 0); rank_name, roman, prog, phase = "Observer", "I", 0, ""
    cumulative = 0
    for r in RANK_CONFIG:
        if pts < r['threshold']:
            rank_name = r['name']; phase = r['phase']; diff = pts - cumulative
            lvl = diff // r['stars_per_lvl']; rem = diff % r['stars_per_lvl']
            roman = {1:"I",2:"II",3:"III",4:"IV",5:"V"}.get(max(1, r['levels'] - lvl), "I")
            prog = (rem / r['stars_per_lvl']) * 100; break
        cumulative = r['threshold']
    else: rank_name = "Ethereal"; phase = "The Singularity"; prog = 100
    return jsonify({ "status": "ok", "username": u['username'], "points": pts, "rank": f"{rank_name} {roman}", "rank_progress": prog, "phase": phase, "history": u.get('history',{}), "rank_config": RANK_CONFIG, "profile_pic": u.get('profile_pic'), "fav_color": u.get('fav_color'), "birthday": u.get('birthday'), "celi_analysis": u.get('celi_analysis') })

@app.route('/api/process', methods=['POST'])
def process():
    u = get_user_data(session['user']); d = request.json
    reply = "Listening..."; summary = "Entry"
    if model:
        try:
            res = model.generate_content(f"Celi (Friendly AI). User: {d.get('message')}. Output JSON: {{'reply': '...', 'summary': '...'}}")
            ai = json.loads(res.text); reply = ai['reply']; summary = ai['summary']
        except: pass
    hist = u.get('history', {}); hist[str(time.time())] = {"summary": summary, "reply": reply, "date": str(date.today()), "type": d.get('mode')}
    update_user_data(session['user'], {"history": hist, "points": u.get('points', 0) + (1 if d.get('mode')!='rant' else 0), "void_count": u.get('void_count',0) + (1 if d.get('mode')=='rant' else 0)})
    return jsonify({"reply": reply})

@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    d = request.json; u = get_user_data(session['user']); up = {}
    if 'birthday' in d: up['birthday'] = d['birthday']
    if 'fav_color' in d: up['fav_color'] = d['fav_color']
    if 'profile_pic' in d: up['profile_pic'] = d['profile_pic']
    up['celi_analysis'] = analyze_user_soul(u); update_user_data(session['user'], up)
    return jsonify({"status": "success"})

@app.route('/api/delete_user', methods=['POST'])
def delete_user():
    if users_col: users_col.delete_one({"username": session['user']})
    session.clear(); return jsonify({"status": "success"})

# --- PAGE ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username'); p = request.form.get('password')
        if users_col:
            user = users_col.find_one({"username": u})
            if user and user.get('password') == p:
                session['user'] = u; session.permanent = True
                # CHANGED: Return JSON instead of redirecting
                return jsonify({"status": "success"}) 
            return jsonify({"error": "Invalid"}), 401
        # Fallback for dev mode
        session['user'] = u; return jsonify({"status": "success"})
    return render_template('auth.html')

@app.route('/'); def home(): return redirect(url_for('login')) if 'user' not in session else render_template('index.html')
@app.route('/logout'); def logout(): session.clear(); return redirect(url_for('login'))
@app.route('/api/trivia'); def api_trivia(): return jsonify({"trivia": "Stardust."})
if __name__ == '__main__': app.run(debug=True)
    
