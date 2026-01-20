import os, json, time, random, uuid, ssl, logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import date, timedelta
import google.generativeai as genai
from pymongo import MongoClient
import certifi
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from celery import Celery

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- CONFIGURATION ---
app.secret_key = os.environ.get("SECRET_KEY", "fallback_debug_key_999")
app.permanent_session_lifetime = timedelta(days=30)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# --- REDIS ---
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

# --- MONGODB CONNECTION ---
MONGO_URI = os.environ.get("MONGO_URI")
db = None
users_col = None
MONGO_STATUS = "Not Initialized"

if MONGO_URI:
    try:
        # Connect with 5 second timeout
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
        db = client.get_database("celi_db")
        users_col = db.users
        # Test connection immediately
        client.admin.command('ping')
        MONGO_STATUS = "Connected ✅"
        logger.info("✅ MONGODB CONNECTED")
    except Exception as e:
        MONGO_STATUS = f"Failed ❌: {str(e)}"
        logger.error(f"❌ MONGO CONNECTION FAILED: {e}")
        users_col = None
else:
    MONGO_STATUS = "Missing MONGO_URI Env Var ❌"

# --- GEMINI ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
model = None
if GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
    except: pass

# --- DEBUG ROUTE (VISIT THIS IN BROWSER) ---
@app.route('/debug')
def debug_page():
    return jsonify({
        "status": "online",
        "mongo_status": MONGO_STATUS,
        "mongo_uri_present": bool(MONGO_URI),
        "redis_url_present": bool(raw_redis_url),
        "gemini_key_present": bool(GEMINI_KEY),
        "secret_key_configured": app.secret_key != "fallback_debug_key_999"
    })

# --- NORMAL ROUTES ---
@app.route('/health')
def health(): return "Alive", 200

def normalize_date(d):
    if not d: return ""
    if '/' in d: parts = d.split('/'); return f"{parts[2]}-{parts[1]}-{parts[0]}" if len(parts)==3 else d
    return d

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        
        if users_col is None: 
            return jsonify({"error": f"DB Error: {MONGO_STATUS}"}), 500
            
        user = users_col.find_one({"username": u})
        if user and check_password_hash(user.get('password', ''), p):
            session['user'] = u
            session.permanent = True
            return jsonify({"status": "success"})
        return jsonify({"error": "Invalid credentials"}), 401
    return render_template('auth.html')

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        if users_col is None: return jsonify({"error": f"DB Error: {MONGO_STATUS}"}), 500
        
        u = data.get('reg_username')
        if users_col.find_one({"username": u}): 
            return jsonify({"error": "Username taken"}), 400
        
        hashed_pw = generate_password_hash(data.get('reg_password'))
        new_user = {
            "username": u, "password": hashed_pw,
            "first_name": data.get('fname'), "last_name": data.get('lname'),
            "birthday": normalize_date(data.get('dob')), "secret_question": data.get('secret_question'),
            "secret_answer": data.get('secret_answer').lower().strip(),
            "fav_color": data.get('fav_color', '#00f2fe'), "user_id": str(uuid.uuid4())[:8].upper(),
            "points": 0, "void_count": 0, "history": {}, "profile_pic": data.get('profile_pic', ""),
            "celi_analysis": "New Signal Detected."
        }
        users_col.insert_one(new_user)
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Register Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

# ... (Include other API routes like find_user, recover, data, process here as usual) ...
# For brevity, ensuring the core login/register works is priority.

# Minimal required APIs for the frontend to not crash 404
@app.route('/api/data')
def get_data():
    if 'user' not in session: return jsonify({"status": "guest"})
    if users_col is None: return jsonify({"status": "error"})
    u = users_col.find_one({"username": session['user']})
    if not u: session.clear(); return jsonify({"status": "guest"})
    return jsonify({"status": "ok", "username": u['username'], "points": u.get('points',0), "rank": "Observer I", "history": u.get('history', {})})

if __name__ == '__main__':
    app.run(debug=True)
