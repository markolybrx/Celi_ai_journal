import os, json, time, random, uuid, ssl, logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import date, timedelta
import google.generativeai as genai
from pymongo import MongoClient
import certifi
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from celery import Celery

# --- CONFIGURATION (v3.1.00) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
app = Flask(__name__)
app.secret_key = "celi_ai_v3.1.00_starlight"
app.permanent_session_lifetime = timedelta(days=30)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# --- REDIS & CELERY ---
raw_redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
if raw_redis_url.startswith('Redis://'): raw_redis_url = raw_redis_url.replace('Redis://', 'rediss://', 1)
elif 'upstash' in raw_redis_url and raw_redis_url.startswith('redis://'): raw_redis_url = raw_redis_url.replace('redis://', 'rediss://', 1)

app.config['CELERY_BROKER_URL'] = raw_redis_url
app.config['CELERY_RESULT_BACKEND'] = raw_redis_url

def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'], backend=app.config['CELERY_RESULT_BACKEND'])
    celery.conf.update(app.config)
    celery.conf.broker_use_ssl = {"ssl_cert_reqs": ssl.CERT_NONE}
    celery.conf.redis_backend_use_ssl = {"ssl_cert_reqs": ssl.CERT_NONE}
    return celery

celery_app = make_celery(app)

# --- DATABASE ---
MONGO_URI = os.environ.get("MONGO_URI")
db = None; users_col = None
if MONGO_URI:
    try:
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
        db = client.get_database("celi_db")
        users_col = db.users
        logger.info("✅ MONGODB CONNECTED")
    except Exception as e: logger.error(f"❌ MONGO FAIL: {e}")

# --- AI ENGINE ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
model = None
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})

# --- RANKING SYSTEM (Constellation Logic) ---
RANK_CONFIG = [
    {"name": "Observer", "levels": 3, "stars_per_lvl": 2, "threshold": 6, "phase": "The Awakening"},
    {"name": "Moonwalker", "levels": 3, "stars_per_lvl": 2, "threshold": 12, "phase": "The Awakening"},
    {"name": "Celestial", "levels": 4, "stars_per_lvl": 3, "threshold": 24, "phase": "The Ignition"},
    {"name": "Stellar", "levels": 4, "stars_per_lvl": 3, "threshold": 36, "phase": "The Ignition"},
    {"name": "Interstellar", "levels": 5, "stars_per_lvl": 4, "threshold": 56, "phase": "The Expansion"},
    {"name": "Galactic", "levels": 5, "stars_per_lvl": 4, "threshold": 76, "phase": "The Expansion"},
    {"name": "Ethereal", "levels": 5, "stars_per_lvl": 8, "threshold": 116, "phase": "The Singularity"}
]

# --- WORKER ---
@celery_app.task(name='app.background_analyze_soul')
def background_analyze_soul(username, recent_logs):
    if not GEMINI_KEY: return
    try:
        worker_model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
        prompt = f"Analyze user based on these journals: {recent_logs}. Output JSON: {{ 'analysis': 'A deep, mystical psychological observation (max 30 words).' }}"
        response = worker_model.generate_content(prompt, request_options={'timeout': 20})
        analysis = json.loads(response.text)['analysis']
        w_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        w_client.get_database("celi_db").users.update_one({"username": username}, {"$set": {"celi_analysis": analysis}})
    except Exception as e: logger.error(f"Worker Error: {e}")

# --- ROUTES ---
def normalize_date(d):
    if not d: return ""
    if '/' in d: parts = d.split('/'); return f"{parts[2]}-{parts[1]}-{parts[0]}" if len(parts)==3 else d
    return d

def get_user(u): return users_col.find_one({"username": u}) if users_col is not None else None

@app.route('/health')
def health(): return "System Operational", 200

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username'); p = request.form.get('password')
        if not users_col: return jsonify({"error": "Database Offline"}), 500
        user = users_col.find_one({"username": u})
        if user and check_password_hash(user.get('password'), p):
            session['user'] = u; session.permanent = True
            return jsonify({"status": "success"})
        return jsonify({"error": "Signal mismatch."}), 401
    return render_template('auth.html')

@app.route('/api/register', methods=['POST'])
def register():
    d = request.json
    if not users_col: return jsonify({"error": "DB Offline"}), 500
    if users_col.find_one({"username": d.get('reg_username')}): return jsonify({"error": "Frequency taken."}), 400
    new_user = {
        "username": d.get('reg_username'), "password": generate_password_hash(d.get('reg_password')),
        "first_name": d.get('fname'), "last_name": d.get('lname'),
        "birthday": normalize_date(d.get('dob')), "secret_question": d.get('secret_question'),
        "secret_answer": d.get('secret_answer').lower().strip(),
        "fav_color": d.get('fav_color', '#00f2fe'), "user_id": str(uuid.uuid4())[:8].upper(),
        "points": 0, "void_count": 0, "history": {}, "profile_pic": d.get('profile_pic', ""),
        "celi_analysis": "Initializing neural link..."
    }
    users_col.insert_one(new_user)
    return jsonify({"status": "success"})

@app.route('/api/process', methods=['POST'])
def process():
    try:
        u = get_user(session['user'])
        d = request.json
        msg = d.get('message'); mode = d.get('mode', 'orbit')
        
        system_tone = "Friendly, caring, empathetic, smart casual."
        if mode == 'void': system_tone = "Deeply empathetic, listening to a vent, validating, soothing."
        if mode == 'nebula': system_tone = "Creative, witty, inspiring, brainstorming partner."
        
        reply = "Connection unstable."
        summary = msg
        
        if model:
            try:
                # TRIVIA LOGIC INJECTED HERE
                if "trivia" in msg.lower():
                    prompt = f"Role: Celi. User asked for trivia. Output JSON: {{ 'reply': 'Give a short, fascinating trivia about Space, Psychology, or Stars.', 'summary': 'Trivia Request' }}"
                else:
                    prompt = f"Role: Celi ({system_tone}). User says: '{msg}'. Output JSON: {{ 'reply': 'Your response', 'summary': 'Short summary of user input' }}"
                
                res = model.generate_content(prompt, request_options={'timeout': 10})
                ai_data = json.loads(res.text)
                reply = ai_data['reply']; summary = ai_data['summary']
            except: reply = "Signal weak."

        new_hist = u.get('history', {})
        new_hist[str(time.time())] = {"summary": summary, "reply": reply, "date": str(date.today()), "type": mode}
        upd = {"history": new_hist}
        if mode != 'void': upd['points'] = u.get('points', 0) + 1
        users_col.update_one({"username": session['user']}, {"$set": upd})
        return jsonify({"reply": reply})
    except: return jsonify({"reply": "Static..."})

@app.route('/api/data')
def get_data():
    if 'user' not in session: return jsonify({"status": "guest"})
    u = get_user(session['user'])
    if not u: session.clear(); return jsonify({"status": "guest"})
    
    pts = u.get('points', 0); rank="Observer"; roman="I"; current_stars=0; total_stars=2
    
    # CONSTELLATION MATH
    cum = 0
    for r in RANK_CONFIG:
        if pts < r['threshold']:
            rank = r['name']
            diff = pts - cum
            lvl = diff // r['stars_per_lvl']
            current_stars = diff % r['stars_per_lvl']
            total_stars = r['stars_per_lvl']
            roman = {1:"I",2:"II",3:"III",4:"IV",5:"V"}.get(max(1, r['levels'] - int(lvl)), "I")
            break
        cum = r['threshold']
    else: rank="Ethereal"; roman="I"; current_stars=5; total_stars=5

    return jsonify({
        "status": "ok", "username": u['username'], "user_id": u['user_id'],
        "points": pts, "rank": f"{rank} {roman}", 
        "stars_current": current_stars, "stars_total": total_stars, # NEW
        "fav_color": u.get('fav_color'), "profile_pic": u.get('profile_pic'),
        "celi_analysis": u.get('celi_analysis'), "history": u.get('history', {})
    })

# --- RECOVERY ---
@app.route('/api/find_user', methods=['POST'])
def find_user():
    d = request.json; q = {"first_name":d.get('fname'),"last_name":d.get('lname'),"birthday":normalize_date(d.get('dob'))}
    u = users_col.find_one(q) if users_col else None
    return jsonify({"status":"found","question_code":u.get('secret_question')}) if u else (jsonify({"error":"Not found"}), 404)

@app.route('/api/recover', methods=['POST'])
def recover():
    d = request.json; q = {"first_name":d.get('fname'),"last_name":d.get('lname'),"birthday":normalize_date(d.get('dob')),"secret_answer":d.get('secret_answer').lower().strip()}
    u = users_col.find_one(q) if users_col else None
    return jsonify({"status":"success","username":u['username']}) if u else (jsonify({"error":"Incorrect"}), 401)

@app.route('/api/reset_password', methods=['POST'])
def reset_pw():
    d = request.json; q={"username":d.get('username'),"secret_answer":d.get('secret_answer').lower().strip()}
    if users_col and users_col.find_one(q):
        users_col.update_one({"username":d.get('username')},{"$set":{"password":generate_password_hash(d.get('new_password'))}})
        return jsonify({"status":"success"})
    return jsonify({"error":"Fail"}), 403

@app.route('/')
def home(): return redirect(url_for('login')) if 'user' not in session else render_template('index.html')
@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

if __name__ == '__main__': app.run(debug=True)
    
