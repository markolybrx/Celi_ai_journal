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

# --- SETUP LOGGING ---
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)

# --- 1. CONFIG: SECRET & REDIS ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'celi_super_secret_key_999')
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_REDIS'] = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'))

# Initialize Session Engine
server_session = Session(app)

# --- 2. CONFIG: CELERY (Background Tasks) ---
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=os.environ.get('REDIS_URL', 'redis://localhost:6379'),
        broker=os.environ.get('REDIS_URL', 'redis://localhost:6379')
    )
    celery.conf.update(app.config)
    return celery

celery_app = make_celery(app)

# --- 3. CONFIG: MONGODB (Eternal Memory) ---
mongo_uri = os.environ.get("MONGO_URI")
db = None
users_col = None
history_col = None

if mongo_uri:
    try:
        client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
        db = client['celi_journal_db']
        users_col = db['users']
        history_col = db['history']
        print("✅ Memory Core (MongoDB) Connected")
    except Exception as e:
        print(f"❌ Memory Core Error: {e}")
else:
    print("❌ CRITICAL: MONGO_URI missing from Render Environment")

# --- 4. CONFIG: AI CORE ---
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    try:
        genai.configure(api_key=api_key.strip().replace("'", "").replace('"', ""))
        print("✅ AI Core Online")
    except:
        print("❌ AI Key Error")

# --- PERSONAS ---
VOID_INSTRUCTION = "You are 'The Void'. You are a sentient, infinite, and safe emptiness. Listen to pain and help release it. Be deep, calm, and abstract."
CELI_INSTRUCTION = "You are 'Celi', a warm AI Journaling Companion. If the user rants, ask: 'I sense heavy energy. Would you like to open The Void?'"

# --- HELPER: AUTH CHECK ---
def login_required():
    if 'user_id' not in session:
        return False
    return True

# ==================================================
#                 ROUTING LOGIC
# ==================================================

@app.route('/')
def index():
    # Gatekeeper: If not logged in, go to Login Page
    if not login_required():
        return redirect(url_for('login_page'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    # If GET, show the Auth HTML
    if request.method == 'GET':
        if login_required(): return redirect(url_for('index'))
        return render_template('auth.html')
    
    # If POST, handle the Login Logic
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not users_col: return jsonify({"status": "error", "error": "Database Offline"})

        user = users_col.find_one({"username": username})
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "error": "Invalid Credentials"}), 401
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# ==================================================
#                 AUTH API ENDPOINTS
# ==================================================

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        if users_col.find_one({"username": data['reg_username']}):
            return jsonify({"status": "error", "error": "Username taken"})

        new_user = {
            "user_id": str(uuid.uuid4()),
            "username": data['reg_username'],
            "password_hash": generate_password_hash(data['reg_password']),
            "first_name": data['fname'],
            "last_name": data['lname'],
            "dob": data['dob'],
            "aura_color": data.get('fav_color', '#00f2fe'),
            "secret_question": data['secret_question'],
            "secret_answer_hash": generate_password_hash(data['secret_answer'].lower().strip()),
            "rank": "Observer I",
            "rank_progress": 0,
            "profile_pic": data.get('profile_pic', ''), # Base64 string
            "joined_at": datetime.now()
        }
        
        users_col.insert_one(new_user)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

@app.route('/api/find_user', methods=['POST'])
def find_user():
    data = request.json
    user = users_col.find_one({
        "first_name": data['fname'],
        "last_name": data['lname'],
        "dob": data['dob']
    })
    if user:
        q_map = {"pet": "First Pet?", "city": "Birth City?"}
        return jsonify({"status": "found", "question_code": q_map.get(user.get('secret_question'), "Security Question")})
    return jsonify({"status": "not_found"})

@app.route('/api/recover', methods=['POST'])
def recover():
    data = request.json
    user = users_col.find_one({"first_name": data['fname'], "last_name": data['lname']})
    if user and check_password_hash(user['secret_answer_hash'], data['secret_answer'].lower().strip()):
        return jsonify({"status": "success", "username": user['username']})
    return jsonify({"status": "error"})

@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    data = request.json
    users_col.update_one(
        {"username": data['username']},
        {"$set": {"password_hash": generate_password_hash(data['new_password'])}}
    )
    return jsonify({"status": "success"})

# ==================================================
#                 APP LOGIC (CHAT)
# ==================================================

@app.route('/api/data')
def get_data():
    if 'user_id' not in session: return jsonify({"status": "guest"}), 401
    
    user = users_col.find_one({"user_id": session['user_id']})
    if not user: return jsonify({"status": "error"}), 404

    history_cursor = history_col.find({"user_id": session['user_id']}, {'_id': 0}).sort("timestamp", 1)
    loaded_history = {entry['timestamp']: entry for entry in history_cursor}

    return jsonify({
        "status": "user",
        "username": user.get("username"),
        "first_name": user.get("first_name"),
        "rank": user.get("rank"),
        "rank_progress": user.get("rank_progress"),
        "history": loaded_history
    })

def generate_with_fallback(msg, is_void):
    candidates = ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.5-flash"]
    system = VOID_INSTRUCTION if is_void else CELI_INSTRUCTION
    for model_name in candidates:
        try:
            model = genai.GenerativeModel(model_name=model_name, system_instruction=system)
            response = model.generate_content(msg)
            return response.text.strip(), model_name
        except: continue
    return "⚠️ Signal Lost. AI Models Unreachable.", "None"

@app.route('/api/process', methods=['POST'])
def process():
    if 'user_id' not in session: return jsonify({"reply": "Session Expired"}), 401
    
    try:
        data = request.json
        msg, mode = data.get('message', ''), data.get('mode', 'journal')
        timestamp = str(datetime.now().timestamp())
        
        # Redis Session Context for "Switch to Void" logic
        awaiting_void = session.get('awaiting_void_confirm', False)
        reply, command = "...", None

        if mode == 'rant':
            reply, _ = generate_with_fallback(msg, is_void=True)
        else:
            if awaiting_void:
                if any(x in msg.lower() for x in ["yes", "sure", "ok"]):
                    reply = "Understood. Opening the Void..."
                    command = "switch_to_void"
                    session['awaiting_void_confirm'] = False
                else:
                    session['awaiting_void_confirm'] = False
                    reply, _ = generate_with_fallback(f"User declined void. Respond to: {msg}", is_void=False)
            else:
                reply, _ = generate_with_fallback(msg, is_void=False)
                if "open The Void" in reply: session['awaiting_void_confirm'] = True

        # Save to MongoDB
        history_col.insert_one({
            "user_id": session['user_id'], "timestamp": timestamp, "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": msg[:50] + "...", "full_message": msg, "reply": reply, "mode": mode
        })
        
        # XP Logic
        users_col.find_one_and_update({"user_id": session['user_id']}, {"$inc": {"rank_progress": 1}})

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

# --- SYSTEM FILES ---
@app.route('/sw.js')
def service_worker(): return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/manifest.json')
def manifest(): return send_from_directory('static', 'manifest.json', mimetype='application/json')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
