import os, json, time, random, uuid
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import date
import google.generativeai as genai
from pymongo import MongoClient
import certifi

app = Flask(__name__)
app.secret_key = "celi_ai_v1.6.1_ui_polish"

# --- MONGODB CONNECTION ---
MONGO_URI = os.environ.get("MONGO_URI")
db = None
users_col = None

if MONGO_URI:
    try:
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        db = client.get_database("celi_db")
        users_col = db.users
        print("MONGODB CONNECTED")
    except Exception as e:
        print(f"MONGO CONNECTION FAILED: {e}")
else:
    print("WARNING: MONGO_URI not found.")

# --- GEMINI CONFIGURATION ---
model = None
try:
    GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
    if GEMINI_KEY:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash', 
            generation_config={"response_mime_type": "application/json"})
    else:
        print("GEMINI_API_KEY missing. AI Disabled.")
except Exception as e:
    print(f"AI INIT ERROR: {e}")

RANK_CONFIG = [
    {"name": "Observer", "levels": 3, "stars_per_lvl": 2, "threshold": 6, "phase": "The Awakening Phase"},
    {"name": "Moonwalker", "levels": 3, "stars_per_lvl": 2, "threshold": 12, "phase": "The Awakening Phase"},
    {"name": "Celestial", "levels": 4, "stars_per_lvl": 3, "threshold": 24, "phase": "The Ignition Phase"},
    {"name": "Stellar", "levels": 4, "stars_per_lvl": 3, "threshold": 36, "phase": "The Ignition Phase"},
    {"name": "Interstellar", "levels": 5, "stars_per_lvl": 4, "threshold": 56, "phase": "The Expansion Phase"},
    {"name": "Galactic", "levels": 5, "stars_per_lvl": 4, "threshold": 76, "phase": "The Expansion Phase"},
    {"name": "Ethereal", "levels": 5, "stars_per_lvl": 8, "threshold": 116, "phase": "The Singularity"}
]

# --- DATABASE HELPERS ---
def get_user_data(username):
    if users_col is None: return None
    user = users_col.find_one({"username": username})
    return user

def update_user_data(username, update_dict):
    if users_col is None: return
    users_col.update_one({"username": username}, {"$set": update_dict})

def analyze_user_soul(user_data):
    if not model: return "Simulation Mode: Trajectory stable."
    history = user_data.get('history', {})
    if len(history) < 3: return "Data insufficient. Continue journaling."
    
    recent_logs = list(history.values())[-5:]
    summaries = [log.get('summary', '') for log in recent_logs]
    
    prompt = f"""
    Analyze user based on journals: {summaries}.
    Output JSON: {{ "analysis": "Deep, witty psychological summary (max 30 words)." }}
    """
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)['analysis']
    except: return "Neural uplink unstable."

# --- API ROUTES ---

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('reg_username')
        
        if users_col is not None and users_col.find_one({"username": username}):
            return jsonify({"error": "Username already exists"}), 400
            
        new_user = {
            "username": username,
            "password": data.get('reg_password'),
            "first_name": data.get('fname'),
            "last_name": data.get('lname'),
            "birthday": data.get('dob'),
            "secret_question": data.get('secret_question'),
            "secret_answer": data.get('secret_answer').lower().strip(),
            "fav_color": data.get('fav_color', '#00f2fe'),
            "user_id": str(uuid.uuid4())[:8].upper(),
            "points": 0,
            "void_count": 0,
            "history": {},
            "unlocked_trivias": [],
            "profile_pic": "",
            "celi_analysis": "New Signal Detected."
        }
        
        if users_col is not None:
            users_col.insert_one(new_user)
            return jsonify({"status": "success"})
        else:
            return jsonify({"error": "Database unavailable"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recover', methods=['POST'])
def recover():
    try:
        data = request.json
        query = {
            "first_name": data.get('fname'),
            "last_name": data.get('lname'),
            "birthday": data.get('dob'),
            "secret_question": data.get('secret_question'),
            "secret_answer": data.get('secret_answer').lower().strip()
        }
        
        if users_col is not None:
            user = users_col.find_one(query)
            if user:
                return jsonify({"status": "success", "username": user['username']})
            else:
                return jsonify({"error": "Identity verification failed."}), 404
        return jsonify({"error": "Database unavailable"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    try:
        data = request.json
        username = data.get('username')
        new_pass = data.get('new_password')
        
        query = {
            "username": username,
            "first_name": data.get('fname'),
            "last_name": data.get('lname'),
            "secret_answer": data.get('secret_answer').lower().strip()
        }
        
        if users_col is not None:
            user = users_col.find_one(query)
            if user:
                users_col.update_one({"username": username}, {"$set": {"password": new_pass}})
                return jsonify({"status": "success"})
            else:
                return jsonify({"error": "Security check failed."}), 403
        return jsonify({"error": "Database unavailable"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/data')
def get_data():
    try:
        if 'user' not in session: return jsonify({"status": "guest"})
        u = get_user_data(session['user'])
        if not u: session.clear(); return jsonify({"status": "guest"})
        
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

        return jsonify({
            "status": "ok",
            "username": u['username'],
            "user_id": u.get('user_id'),
            "birthday": u.get('birthday'),
            "fav_color": u.get('fav_color'),
            "profile_pic": u.get('profile_pic'),
            "points": pts, 
            "rank": f"{current_rank_name} {current_roman}",
            "rank_roman": current_roman,
            "phase": current_phase,
            "rank_progress": current_prog,
            "rank_synthesis": "Orbiting...",
            "history": u.get('history', {}), 
            "unlocked_trivias": u.get('unlocked_trivias', []),
            "celi_analysis": u.get('celi_analysis'),
            "rank_config": RANK_CONFIG
        })
    except Exception as e:
        print(f"DATA ERROR: {e}")
        return jsonify({"status": "error"})

@app.route('/api/process', methods=['POST'])
def process():
    try:
        u = get_user_data(session['user'])
        data = request.json
        reply_text = "I'm listening..."
        summary_text = "User entry."
        if model:
            prompt = f"""You are Celi. Empathetic, friendly, witty. User: {data.get('message')} Output JSON: {{ "reply": "Your response", "summary": "Short summary" }}"""
            res = model.generate_content(prompt)
            ai_data = json.loads(res.text)
            reply_text = ai_data['reply']
            summary_text = ai_data['summary']

        updates = {}
        if data.get('mode') != 'rant': updates['points'] = u.get('points', 0) + 1
        else: updates['void_count'] = u.get('void_count', 0) + 1
        new_history = u.get('history', {})
        new_history[str(time.time())] = { "summary": summary_text, "reply": reply_text, "date": str(date.today()), "type": data.get('mode', 'journal') }
        updates['history'] = new_history
        update_user_data(session['user'], updates)
        return jsonify({"reply": reply_text})
    except Exception as e:
        print(f"CHAT ERROR: {e}")
        return jsonify({"reply": "Static noise..."})

@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    try:
        data = request.json
        u = get_user_data(session['user'])
        updates = {}
        if 'birthday' in data: updates['birthday'] = data['birthday']
        if 'fav_color' in data: updates['fav_color'] = data['fav_color']
        if 'profile_pic' in data: updates['profile_pic'] = data['profile_pic']
        updates['celi_analysis'] = analyze_user_soul(u)
        update_user_data(session['user'], updates)
        return jsonify({"status": "success"})
    except: return jsonify({"status": "error"})

@app.route('/api/delete_user', methods=['POST'])
def delete_user():
    if users_col is not None: users_col.delete_one({"username": session['user']})
    session.clear()
    return jsonify({"status": "success"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if users_col is not None:
            user = users_col.find_one({"username": username})
            if user and user.get('password') == password:
                session['user'] = username
                # Session is permanent if 'remember me' is managed by browser cookies mostly, 
                # but flask session defaults are okay for now.
                session.permanent = True 
                return redirect(url_for('home'))
            return jsonify({"error": "Invalid credentials"}), 401
        session['user'] = username
        return redirect(url_for('home'))
    return render_template('auth.html')

@app.route('/')
def home():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/api/trivia')
def api_trivia(): return jsonify({"trivia": "Stardust."})

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

if __name__ == '__main__': app.run(debug=True)
                                
