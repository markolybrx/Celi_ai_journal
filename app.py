import os
import logging
import traceback
import certifi
import uuid
import redis
from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for, session
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import google.generativeai as genai
from pymongo import MongoClient
from celery import Celery

# --- IMPORT RANK LOGIC ---
from rank_system import update_rank_progress, get_rank_meta

# --- SETUP LOGGING ---
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)

# --- CONFIG: SECRET & REDIS ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'celi_super_secret_key_999')
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_REDIS'] = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'))
server_session = Session(app)

# --- CONFIG: CELERY ---
def make_celery(app):
    celery = Celery(app.import_name, backend=os.environ.get('REDIS_URL', 'redis://localhost:6379'), broker=os.environ.get('REDIS_URL', 'redis://localhost:6379'))
    celery.conf.update(app.config)
    return celery
celery_app = make_celery(app)

# --- CONFIG: MONGODB ---
mongo_uri = os.environ.get("MONGO_URI")
db, users_col, history_col = None, None, None
if mongo_uri:
    try:
        client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
        db = client['celi_journal_db']
        users_col = db['users']
        history_col = db['history']
        print("✅ Memory Core (MongoDB) Connected")
    except Exception as e: print(f"❌ Memory Core Error: {e}")

# --- CONFIG: AI CORE ---
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    try: genai.configure(api_key=api_key.strip().replace("'", "").replace('"', ""))
    except: pass

# ==================================================
#                 ROUTING LOGIC
# ==================================================
def login_required(): return 'user_id' in session

@app.route('/')
def index():
    if not login_required(): return redirect(url_for('login_page'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'GET':
        if login_required(): return redirect(url_for('index'))
        return render_template('auth.html')
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        if not users_col: return jsonify({"status": "error", "error": "Database Offline"})
        user = users_col.find_one({"username": username})
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            return jsonify({"status": "success"})
        else: return jsonify({"status": "error", "error": "Invalid Credentials"}), 401
    except Exception as e: return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# --- AUTH API ---
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        if users_col.find_one({"username": data['reg_username']}): return jsonify({"status": "error", "error": "Username taken"})
        new_user = {
            "user_id": str(uuid.uuid4()), "username": data['reg_username'], "password_hash": generate_password_hash(data['reg_password']),
            "first_name": data['fname'], "last_name": data['lname'], "dob": data['dob'], "aura_color": data.get('fav_color', '#00f2fe'),
            "secret_question": data['secret_question'], "secret_answer_hash": generate_password_hash(data['secret_answer'].lower().strip()),
            "rank": "Observer III", "rank_index": 0, "stardust": 0, "profile_pic": data.get('profile_pic', ''), "joined_at": datetime.now()
        }
        users_col.insert_one(new_user)
        return jsonify({"status": "success"})
    except Exception as e: return jsonify({"status": "error", "error": str(e)})

@app.route('/api/find_user', methods=['POST'])
def find_user():
    data = request.json
    user = users_col.find_one({"first_name": data['fname'], "last_name": data['lname'], "dob": data['dob']})
    if user: return jsonify({"status": "found", "question_code": user.get('secret_question', 'pet')})
    return jsonify({"status": "not_found"})

@app.route('/api/recover', methods=['POST'])
def recover():
    data = request.json
    user = users_col.find_one({"first_name": data['fname'], "last_name": data['lname']})
    if user and check_password_hash(user['secret_answer_hash'], data['secret_answer'].lower().strip()): return jsonify({"status": "success", "username": user['username']})
    return jsonify({"status": "error"})

@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    data = request.json
    users_col.update_one({"username": data['username']}, {"$set": {"password_hash": generate_password_hash(data['new_password'])}})
    return jsonify({"status": "success"})

# --- APP LOGIC ---
@app.route('/api/data')
def get_data():
    if 'user_id' not in session: return jsonify({"status": "guest"}), 401
    user = users_col.find_one({"user_id": session['user_id']})
    if not user: return jsonify({"status": "error"}), 404

    # Use Helper to get Rank Metadata
    idx = user.get('rank_index', 0)
    rank_info = get_rank_meta(idx)
    
    max_dust = rank_info['req']
    current_dust = user.get('stardust', 0)
    progress_percent = (current_dust / max_dust) * 100 if max_dust > 0 else 0

    history_cursor = history_col.find({"user_id": session['user_id']}, {'_id': 0}).sort("timestamp", 1)
    loaded_history = {entry['timestamp']: entry for entry in history_cursor}

    return jsonify({
        "status": "user", "username": user.get("username"), "first_name": user.get("first_name"),
        "rank": user.get("rank", "Observer III"), "rank_progress": progress_percent,
        "rank_psyche": rank_info.get("psyche", "Unknown"), "rank_desc": rank_info.get("desc", ""),
        "stardust_current": current_dust, "stardust_max": max_dust,
        "history": loaded_history,
        "profile_pic": user.get("profile_pic", "")
    })

def generate_with_fallback(msg, is_void):
    candidates = ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.5-flash"]
    system = "You are 'The Void'. Sentient, infinite, safe emptiness. Listen to pain. Be deep, abstract." if is_void else "You are 'Celi', a warm AI Journaling Companion. If user rants, ask: 'I sense heavy energy. Open The Void?'"
    for m in candidates:
        try: return genai.GenerativeModel(m, system_instruction=system).generate_content(msg).text.strip(), m
        except: continue
    return "⚠️ Signal Lost.", "None"

@app.route('/api/process', methods=['POST'])
def process():
    if 'user_id' not in session: return jsonify({"reply": "Session Expired"}), 401
    try:
        data = request.json
        msg, mode = data.get('message', ''), data.get('mode', 'journal')
        timestamp = str(datetime.now().timestamp())
        
        awaiting_void = session.get('awaiting_void_confirm', False)
        reply, command = "...", None

        if mode == 'rant': reply, _ = generate_with_fallback(msg, True)
        else:
            if awaiting_void:
                if any(x in msg.lower() for x in ["yes", "sure", "ok"]): reply, command, session['awaiting_void_confirm'] = "Understood. Opening the Void...", "switch_to_void", False
                else: session['awaiting_void_confirm'] = False; reply, _ = generate_with_fallback(f"User declined void. Respond to: {msg}", False)
            else:
                reply, _ = generate_with_fallback(msg, False)
                if "open The Void" in reply: session['awaiting_void_confirm'] = True

        history_col.insert_one({"user_id": session['user_id'], "timestamp": timestamp, "date": datetime.now().strftime("%Y-%m-%d"), "summary": msg[:50] + "...", "full_message": msg, "reply": reply, "mode": mode})
        
        # USE HELPER FROM RANK_SYSTEM.PY
        # Note: We pass 'users_col' because rank_system.py needs DB access
        rank_event = update_rank_progress(users_col, session['user_id'])
        if rank_event == "level_up": command = "level_up"
        elif rank_event == "xp_gain": command = "xp_gain"

        return jsonify({"reply": reply, "command": command})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"reply": f"SYSTEM ERROR: {str(e)}"}), 500

@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    if 'user_id' in session:
        history_col.delete_many({"user_id": session['user_id']})
        return jsonify({"status": "success"})
    return jsonify({"status": "error"})

@app.route('/sw.js')
def service_worker(): return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/manifest.json')
def manifest(): return send_from_directory('static', 'manifest.json', mimetype='application/json')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
