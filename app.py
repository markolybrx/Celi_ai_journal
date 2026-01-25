import os
import logging
import traceback
import certifi
import uuid
import redis
import ssl
import json
from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for, session
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import google.generativeai as genai
from pymongo import MongoClient
from celery import Celery

# --- IMPORT NEW LOGIC ---
from rank_system import process_daily_rewards, update_rank_check, get_rank_meta, get_all_ranks_data

# --- SETUP LOGGING ---
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)

# --- CONFIG: SECRET & REDIS ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'celi_super_secret_key_999')
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
# Fix Upstash/SSL
if 'upstash' in redis_url or 'rediss' in redis_url:
    if redis_url.startswith('redis://'): redis_url = redis_url.replace('redis://', 'rediss://', 1)
    app.config['SESSION_REDIS'] = redis.from_url(redis_url, ssl_cert_reqs=None)
else:
    app.config['SESSION_REDIS'] = redis.from_url(redis_url)

server_session = Session(app)

# --- CONFIG: CELERY ---
def make_celery(app):
    celery = Celery(app.import_name, backend=redis_url, broker=redis_url)
    if 'rediss' in redis_url:
        celery.conf.update(broker_use_ssl={"ssl_cert_reqs": ssl.CERT_NONE}, redis_backend_use_ssl={"ssl_cert_reqs": ssl.CERT_NONE})
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
#                 HELPER FUNCTIONS
# ==================================================

def generate_analysis(entry_text):
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = f"Analyze this journal entry psychologically. Be warm, insightful, and brief (max 2 sentences). Entry: {entry_text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "Analysis unavailable due to signal interference."

def generate_with_media(msg, media_data=None, is_void=False):
    candidates = ["gemini-2.0-flash", "gemini-2.0-flash-lite"]
    system = "You are 'The Void'. Infinite, safe emptiness. Absorb pain." if is_void else "You are Celi. Analyze the user's day based on their text and/or image. Be warm and observant."
    
    content = [msg]
    if media_data:
        content.append(media_data)

    for m in candidates:
        try:
            model = genai.GenerativeModel(m, system_instruction=system)
            response = model.generate_content(content)
            return response.text.strip()
        except Exception as e:
            print(f"Model Error ({m}): {e}")
            continue
    return "⚠️ Signal Lost. Visual/Text processing failed."

# ==================================================
#                 ROUTES
# ==================================================

@app.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'GET': return redirect(url_for('index')) if 'user_id' in session else render_template('auth.html')
    try:
        username, password = request.form.get('username'), request.form.get('password')
        if users_col is None: return jsonify({"status": "error", "error": "Database Offline"})
        user = users_col.find_one({"username": username})
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            return jsonify({"status": "success"})
        else: return jsonify({"status": "error", "error": "Invalid Credentials"}), 401
    except Exception as e: return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login_page'))

# --- AUTH API ---
@app.route('/api/register', methods=['POST'])
def register():
    try:
        if users_col is None: return jsonify({"status": "error", "error": "Database Offline"})
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

# --- DATA API ---
@app.route('/api/data')
def get_data():
    if 'user_id' not in session: return jsonify({"status": "guest"}), 401
    if users_col is None: return jsonify({"status": "error"}), 500
    user = users_col.find_one({"user_id": session['user_id']})
    if not user: return jsonify({"status": "error"}), 404
    
    # Get Metadata for CURRENT rank
    rank_info = get_rank_meta(user.get('rank_index', 0))
    
    # Get Full List for Modal
    progression_tree = get_all_ranks_data()
    
    max_dust = rank_info['req']
    current_dust = user.get('stardust', 0)
    
    history_cursor = history_col.find({"user_id": session['user_id']}, {'_id': 0}).sort("timestamp", 1).limit(50)
    loaded_history = {entry['timestamp']: entry for entry in history_cursor}

    return jsonify({
        "status": "user", 
        "username": user.get("username"), 
        "first_name": user.get("first_name"),
        "rank": user.get("rank", "Observer III"),
        "rank_index": user.get("rank_index", 0), 
        "rank_progress": (current_dust/max_dust)*100 if max_dust>0 else 0,
        "rank_psyche": rank_info.get("psyche", "Unknown"), 
        "rank_desc": rank_info.get("desc", ""),
        "current_svg": rank_info.get("svg"), 
        "current_color": rank_info.get("color"),
        "stardust_current": current_dust, 
        "stardust_max": max_dust,
        "history": loaded_history, 
        "profile_pic": user.get("profile_pic", ""),
        "progression_tree": progression_tree
    })

# --- GALAXY MAP API ---
@app.route('/api/galaxy_map')
def galaxy_map():
    if 'user_id' not in session: return jsonify([])
    if history_col is None: return jsonify([])
    
    cursor = history_col.find({"user_id": session['user_id']}, {'_id': 0, 'full_message': 0}).sort("timestamp", 1)
    
    stars = []
    for index, doc in enumerate(cursor):
        star_type = "void" if doc.get('mode') == 'rant' else "journal"
        constellation_group = index // 7 
        
        stars.append({
            "id": doc['timestamp'],
            "date": doc['date'],
            "summary": doc.get('summary', '...'),
            "type": star_type,
            "has_media": doc.get('has_media', False),
            "group": constellation_group,   
            "index": index                  
        })
    return jsonify(stars)

# --- STAR DETAIL API ---
@app.route('/api/star_detail', methods=['POST'])
def star_detail():
    if 'user_id' not in session: return jsonify({"error": "Auth"})
    data = request.json
    timestamp = data.get('id')
    
    entry = history_col.find_one({"user_id": session['user_id'], "timestamp": timestamp}, {'_id': 0})
    if not entry: return jsonify({"error": "Not found"})
    
    analysis = entry.get('ai_analysis')
    if not analysis:
        analysis = generate_analysis(entry.get('full_message', ''))
        history_col.update_one({"user_id": session['user_id'], "timestamp": timestamp}, {"$set": {"ai_analysis": analysis}})
    
    return jsonify({
        "date": entry['date'],
        "analysis": analysis,
        "media": entry.get('media_base64', None),
        "mode": entry.get('mode', 'journal')
    })

# --- PROCESS ENTRY API ---
@app.route('/api/process', methods=['POST'])
def process():
    if 'user_id' not in session: return jsonify({"reply": "Session Expired"}), 401
    try:
        data = request.json
        msg = data.get('message', '')
        media_b64 = data.get('media', None)
        mode = data.get('mode', 'journal')
        timestamp = str(datetime.now().timestamp())
        
        # 1. PROCESS DAILY REWARD
        reward_result = process_daily_rewards(users_col, session['user_id'], msg)
        
        # 2. GENERATE AI REPLY
        gemini_media = {'mime_type': 'image/jpeg', 'data': media_b64.split(',')[1]} if media_b64 else None
        
        reply = "..."
        if mode == 'rant':
            reply = generate_with_media(msg, gemini_media, is_void=True)
        else:
            if session.get('awaiting_void_confirm', False):
                if any(x in msg.lower() for x in ["yes", "sure", "ok"]): 
                    reply, command, session['awaiting_void_confirm'] = "Understood. Opening Void...", "switch_to_void", False
                else: 
                    session['awaiting_void_confirm'] = False
                    reply = generate_with_media(f"User declined void. Respond: {msg}", gemini_media, False)
            else:
                reply = generate_with_media(msg, gemini_media, False)
                if "open The Void" in reply: session['awaiting_void_confirm'] = True

        # 3. SAVE TO DB
        history_col.insert_one({
            "user_id": session['user_id'],
            "timestamp": timestamp,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": msg[:50] + "...",
            "full_message": msg,
            "reply": reply,
            "ai_analysis": None,
            "mode": mode,
            "has_media": bool(media_b64),
            "media_base64": media_b64,
            "is_valid_star": reward_result['awarded']
        })
        
        # 4. CHECK LEVEL UP
        command = None
        level_check = update_rank_check(users_col, session['user_id'])
        
        if level_check == "level_up": 
            command = "level_up"
            reply += f"\n\n[System]: Level Up! {reward_result.get('message', '')}"
        elif reward_result['awarded']:
            command = "daily_reward"
            reply += f"\n\n[System]: {reward_result['message']}"

        return jsonify({"reply": reply, "command": command})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"reply": f"SYSTEM ERROR: {str(e)}"}), 500

@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    if 'user_id' in session and history_col is not None:
        history_col.delete_many({"user_id": session['user_id']})
        return jsonify({"status": "success"})
    return jsonify({"status": "error"})

@app.route('/sw.js')
def service_worker(): return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/manifest.json')
def manifest(): return send_from_directory('static', 'manifest.json', mimetype='application/json')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
