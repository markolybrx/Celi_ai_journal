import os, json, time, random, uuid, ssl, logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import date, timedelta
import google.generativeai as genai
from pymongo import MongoClient
import certifi
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from celery import Celery

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- CONFIGURATION ---
app.secret_key = "celi_ai_v1.14.00.00_recovery_flow"
app.permanent_session_lifetime = timedelta(days=30)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# --- REDIS URL CLEANER ---
raw_redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
if raw_redis_url.startswith('Redis://'):
    raw_redis_url = raw_redis_url.replace('Redis://', 'rediss://', 1)
elif raw_redis_url.startswith('redis://') and 'upstash' in raw_redis_url:
    raw_redis_url = raw_redis_url.replace('redis://', 'rediss://', 1)

app.config['CELERY_BROKER_URL'] = raw_redis_url
app.config['CELERY_RESULT_BACKEND'] = raw_redis_url

# --- CELERY ---
def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'], backend=app.config['CELERY_RESULT_BACKEND'])
    celery.conf.update(app.config)
    celery.conf.broker_use_ssl = {"ssl_cert_reqs": ssl.CERT_NONE}
    celery.conf.redis_backend_use_ssl = {"ssl_cert_reqs": ssl.CERT_NONE}
    return celery

celery_app = make_celery(app)

# --- MONGODB ---
MONGO_URI = os.environ.get("MONGO_URI")
db = None; users_col = None

if MONGO_URI:
    try:
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
        db = client.get_database("celi_db")
        users_col = db.users
        client.admin.command('ping')
        logger.info("✅ MONGODB CONNECTED")
    except Exception as e:
        logger.error(f"❌ MONGO CONNECTION FAILED: {e}")
        users_col = None

# --- GEMINI ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
model = None
if GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
    except: pass

RANK_CONFIG = [
    {"name": "Observer", "levels": 3, "stars_per_lvl": 2, "threshold": 6, "phase": "The Awakening Phase"},
    {"name": "Moonwalker", "levels": 3, "stars_per_lvl": 2, "threshold": 12, "phase": "The Awakening Phase"},
    {"name": "Celestial", "levels": 4, "stars_per_lvl": 3, "threshold": 24, "phase": "The Ignition Phase"},
    {"name": "Stellar", "levels": 4, "stars_per_lvl": 3, "threshold": 36, "phase": "The Ignition Phase"},
    {"name": "Interstellar", "levels": 5, "stars_per_lvl": 4, "threshold": 56, "phase": "The Expansion Phase"},
    {"name": "Galactic", "levels": 5, "stars_per_lvl": 4, "threshold": 76, "phase": "The Expansion Phase"},
    {"name": "Ethereal", "levels": 5, "stars_per_lvl": 8, "threshold": 116, "phase": "The Singularity"}
]

@celery_app.task(name='app.background_analyze_soul')
def background_analyze_soul(username, recent_logs):
    logger.info(f"🔄 Worker: Analyzing {username}...")
    try:
        if not GEMINI_KEY: return
        genai.configure(api_key=GEMINI_KEY)
        worker_model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
        prompt = f"Analyze user based on journals: {recent_logs}. Output JSON: {{ 'analysis': 'Deep, witty psychological summary (max 30 words).' }}"
        response = worker_model.generate_content(prompt, request_options={'timeout': 20})
        analysis_text = json.loads(response.text)['analysis']
        
        worker_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        worker_db = worker_client.get_database("celi_db")
        worker_db.users.update_one({"username": username}, {"$set": {"celi_analysis": analysis_text}})
        logger.info(f"✅ Worker: Analysis saved for {username}")
    except Exception as e:
        logger.error(f"❌ Worker Error: {e}")

def get_user_data(username):
    if users_col is None: return None
    return users_col.find_one({"username": username})

def update_user_data(username, update_dict):
    if users_col is None: return
    users_col.update_one({"username": username}, {"$set": update_dict})

# --- API ROUTES ---

@app.route('/health')
def health(): return "Alive", 200

# NEW ROUTE: Step 1 of Recovery - Find User & Get Question
@app.route('/api/find_user', methods=['POST'])
def find_user():
    try:
        d = request.json
        # Look for user by Name + DOB only
        q = { 
            "first_name": d.get('fname'), 
            "last_name": d.get('lname'), 
            "birthday": d.get('dob') 
        }
        if users_col is not None:
            user = users_col.find_one(q)
            if user:
                # Return the question so the UI can display it
                return jsonify({
                    "status": "found", 
                    "question_code": user.get('secret_question', 'pet')
                })
            return jsonify({"error": "No account found."}), 404
        return jsonify({"error": "DB Unavailable"}), 500
    except Exception as e: return jsonify({"error": str(e)}), 500

# MODIFIED ROUTE: Step 2 of Recovery - Verify Answer
@app.route('/api/recover', methods=['POST'])
def recover():
    try:
        d = request.json
        q = { 
            "first_name": d.get('fname'), 
            "last_name": d.get('lname'), 
            "birthday": d.get('dob'), 
            # We verify the answer here
            "secret_answer": d.get('secret_answer').lower().strip() 
        }
        if users_col is not None:
            u = users_col.find_one(q)
            if u: 
                return jsonify({"status": "success", "username": u['username']})
            return jsonify({"error": "Incorrect Secret Answer."}), 401
        return jsonify({"error": "Database unavailable"}), 500
    except: return jsonify({"error": "Fail"}), 500

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        u = data.get('reg_username')
        if users_col is None: return jsonify({"error": "DB Offline"}), 500
        if users_col.find_one({"username": u}): return jsonify({"error": "Username taken"}), 400
        
        hashed_pw = generate_password_hash(data.get('reg_password'))
        new_user = {
            "username": u, "password": hashed_pw,
            "first_name": data.get('fname'), "last_name": data.get('lname'),
            "birthday": data.get('dob'), "secret_question": data.get('secret_question'),
            "secret_answer": data.get('secret_answer').lower().strip(),
            "fav_color": data.get('fav_color', '#00f2fe'), "user_id": str(uuid.uuid4())[:8].upper(),
            "points": 0, "void_count": 0, "history": {}, "unlocked_trivias": [],
            "profile_pic": data.get('profile_pic', ""), "celi_analysis": "New Signal Detected."
        }
        users_col.insert_one(new_user)
        return jsonify({"status": "success"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    try:
        d = request.json
        # Double check identity before reset
        q = { "username": d.get('username'), "first_name": d.get('fname'), "last_name": d.get('lname'), "secret_answer": d.get('secret_answer').lower().strip() }
        if users_col is not None and users_col.find_one(q):
            new_hashed = generate_password_hash(d.get('new_password'))
            users_col.update_one({"username": d.get('username')}, {"$set": {"password": new_hashed}})
            return jsonify({"status": "success"})
        return jsonify({"error": "Security check failed"}), 403
    except: return jsonify({"error": "Fail"}), 500

@app.route('/api/data')
def get_data():
    try:
        if 'user' not in session: return jsonify({"status": "guest"})
        u = get_user_data(session['user'])
        if not u: session.clear(); return jsonify({"status": "guest"})
        pts = u.get('points', 0); rank="Observer"; phase=""; prog=0; cum=0
        for r in RANK_CONFIG:
            if pts < r['threshold']:
                rank = r['name']; phase = r['phase']; diff = pts - cum; lvl = diff // r['stars_per_lvl']; rem = diff % r['stars_per_lvl']
                roman = {1:"I",2:"II",3:"III",4:"IV",5:"V"}.get(max(1, r['levels'] - int(lvl)), "I")
                prog = (rem / r['stars_per_lvl']) * 100; break
            cum = r['threshold']
        else: rank="Ethereal"; roman="I"; prog=100; phase="The Singularity"
        return jsonify({
            "status": "ok", "username": u['username'], "user_id": u.get('user_id'),
            "birthday": u.get('birthday'), "fav_color": u.get('fav_color'),
            "profile_pic": u.get('profile_pic'), "points": pts, 
            "rank": f"{rank} {roman}", "rank_roman": roman, "phase": phase, "rank_progress": prog, 
            "history": u.get('history', {}), "unlocked_trivias": u.get('unlocked_trivias', []),
            "celi_analysis": u.get('celi_analysis'), "rank_config": RANK_CONFIG
        })
    except: return jsonify({"status": "error"})

@app.route('/api/process', methods=['POST'])
def process():
    try:
        u = get_user_data(session['user'])
        data = request.json
        reply_text="Listening..."; summary_text="User entry."
        if model:
            try:
                res = model.generate_content(f"Celi (Friendly AI). User: {data.get('message')} Output JSON: {{ 'reply': '...', 'summary': '...' }}", request_options={'timeout': 10})
                ai = json.loads(res.text); reply_text=ai['reply']; summary_text=ai['summary']
            except Exception as e: logger.warning(f"Gemini Timeout: {e}"); reply_text = "Signal weak. Entry logged."
        updates = {}; updates['points'] = u.get('points', 0) + 1 if data.get('mode') != 'rant' else u.get('points', 0)
        if data.get('mode') == 'rant': updates['void_count'] = u.get('void_count', 0) + 1
        new_history = u.get('history', {}); new_history[str(time.time())] = { "summary": summary_text, "reply": reply_text, "date": str(date.today()), "type": data.get('mode', 'journal') }
        updates['history'] = new_history
        update_user_data(session['user'], updates)
        return jsonify({"reply": reply_text})
    except: return jsonify({"reply": "Static noise..."})

@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    try:
        data = request.json
        u_data = get_user_data(session['user'])
        updates = {}
        for k in ['birthday', 'fav_color', 'profile_pic']: 
            if k in data: updates[k] = data[k]
        if len(u_data.get('history', {})) >= 3:
            logs = [l.get('summary', '') for l in list(u_data['history'].values())[-5:]]
            background_analyze_soul.delay(session['user'], logs)
            updates['celi_analysis'] = "The stars are aligning... (Analysis in progress)"
        else: updates['celi_analysis'] = "More data needed for signal lock."
        update_user_data(session['user'], updates)
        return jsonify({"status": "success"})
    except: return jsonify({"status": "error"})

@app.route('/api/delete_user', methods=['POST'])
def delete_user():
    if users_col is not None: users_col.delete_one({"username": session['user']})
    session.clear(); return jsonify({"status": "success"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username'); p = request.form.get('password')
        if users_col is None: return jsonify({"error": "System Offline (DB)"}), 500
        user = users_col.find_one({"username": u})
        if user and check_password_hash(user.get('password', ''), p):
            session['user'] = u; session.permanent = True
            return jsonify({"status": "success"})
        return jsonify({"error": "Invalid credentials"}), 401
    return render_template('auth.html')

@app.route('/')
def home():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

@app.route('/api/trivia')
def api_trivia(): return jsonify({"trivia": "Stardust."})

if __name__ == '__main__':
    app.run(debug=True)
