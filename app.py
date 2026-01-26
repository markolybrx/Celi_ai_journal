import os
import logging
import traceback
import certifi
import uuid
import redis
import ssl
import json
import gridfs
from bson.objectid import ObjectId
from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for, session, Response
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import google.generativeai as genai
from pymongo import MongoClient
from celery import Celery

# --- IMPORT RANK LOGIC ---
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
if 'upstash' in redis_url or 'rediss' in redis_url:
    if redis_url.startswith('redis://'): redis_url = redis_url.replace('redis://', 'rediss://', 1)
    app.config['SESSION_REDIS'] = redis.from_url(redis_url, ssl_cert_reqs=None)
else:
    app.config['SESSION_REDIS'] = redis.from_url(redis_url)

server_session = Session(app)

# --- CONFIG: MONGODB & GRIDFS ---
mongo_uri = os.environ.get("MONGO_URI")
db, users_col, history_col, fs = None, None, None, None

if mongo_uri:
    try:
        client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
        db = client['celi_journal_db']
        users_col = db['users']
        history_col = db['history']
        fs = gridfs.GridFS(db) # File Storage System initialized
        print("✅ Memory Core (MongoDB + GridFS) Connected")
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

def generate_constellation_name(entries_text):
    """Names a group of 7 entries."""
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = f"Here are 7 days of journal entries. Give them a mystical 'Constellation Name' that summarizes the theme (e.g., 'The Week of Rain', 'Orion of Hope'). Just the name. Entries: {entries_text}"
        response = model.generate_content(prompt)
        return response.text.strip().replace('"', '').replace("'", "")
    except:
        return "Unknown Constellation"

def generate_with_media(msg, media_bytes=None, media_mime=None, is_void=False):
    candidates = ["gemini-2.0-flash", "gemini-2.0-flash-lite"]
    system = "You are 'The Void'. Infinite, safe emptiness. Absorb pain." if is_void else "You are Celi. Analyze the user's day based on their text and/or image. Be warm and observant."
    
    content = [msg]
    if media_bytes and media_mime and 'image' in media_mime:
        # Convert bytes to Gemini compatible input
        content.append({'mime_type': media_mime, 'data': media_bytes})

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

# --- MEDIA SERVING ROUTE (New!) ---
@app.route('/api/media/<file_id>')
def get_media(file_id):
    try:
        if fs is None: return "Database Error", 500
        grid_out = fs.get(ObjectId(file_id))
        return Response(grid_out.read(), mimetype=grid_out.content_type)
    except Exception as e:
        return "File not found", 404

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
    
    rank_info = get_rank_meta(user.get('rank_index', 0))
    progression_tree = get_all_ranks_data()
    max_dust = rank_info['req']
    current_dust = user.get('stardust', 0)
    
    # Load recent history (without full text to save bandwidth)
    history_cursor = history_col.find({"user_id": session['user_id']}, {'_id': 0, 'media_file_id': 0, 'audio_file_id': 0}).sort("timestamp", 1).limit(50)
    loaded_history = {entry['timestamp']: entry for entry in history_cursor}

    return jsonify({
        "status": "user", "username": user.get("username"), "first_name": user.get("first_name"),
        "rank": user.get("rank", "Observer III"), "rank_index": user.get("rank_index", 0),
        "rank_progress": (current_dust/max_dust)*100 if max_dust>0 else 0,
        "rank_psyche": rank_info.get("psyche", "Unknown"), "rank_desc": rank_info.get("desc", ""),
        "current_svg": rank_info.get("svg"), "current_color": rank_info.get("color"),
        "stardust_current": current_dust, "stardust_max": max_dust,
        "history": loaded_history, "profile_pic": user.get("profile_pic", ""),
        "progression_tree": progression_tree
    })

# --- GALAXY MAP API (LOD SUPPORT) ---
@app.route('/api/galaxy_map')
def galaxy_map():
    if 'user_id' not in session: return jsonify([])
    cursor = history_col.find({"user_id": session['user_id']}, 
                              {'_id': 0, 'full_message': 0, 'reply': 0, 'media_file_id': 0, 'audio_file_id': 0}).sort("timestamp", 1)
    
    stars = []
    # Fetch all, but frontend will handle physics LOD
    # Backend adds semantic constellation names if they exist
    for index, doc in enumerate(cursor):
        star_type = "void" if doc.get('mode') == 'rant' else "journal"
        constellation_group = index // 7
        
        stars.append({
            "id": doc['timestamp'],
            "date": doc['date'],
            "summary": doc.get('summary', '...'),
            "type": star_type,
            "has_media": doc.get('has_media', False),
            "has_audio": doc.get('has_audio', False),
            "group": constellation_group,
            "constellation_name": doc.get('constellation_name', None), # For Semantic UI
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
    
    # Generate analysis if missing
    analysis = entry.get('ai_analysis')
    if not analysis:
        analysis = generate_analysis(entry.get('full_message', ''))
        history_col.update_one({"user_id": session['user_id'], "timestamp": timestamp}, {"$set": {"ai_analysis": analysis}})
    
    # Construct Media URLs
    image_url = None
    if entry.get('media_file_id'):
        image_url = f"/api/media/{entry['media_file_id']}"
        
    audio_url = None
    if entry.get('audio_file_id'):
        audio_url = f"/api/media/{entry['audio_file_id']}"

    return jsonify({
        "date": entry['date'],
        "analysis": analysis,
        "image_url": image_url,
        "audio_url": audio_url,
        "mode": entry.get('mode', 'journal')
    })

# --- PROCESS ENTRY API (FILES & NAMING) ---
@app.route('/api/process', methods=['POST'])
def process():
    if 'user_id' not in session: return jsonify({"reply": "Session Expired"}), 401
    try:
        # Handle FormData (files + text)
        msg = request.form.get('message', '')
        mode = request.form.get('mode', 'journal')
        image_file = request.files.get('media')
        audio_file = request.files.get('audio')
        
        timestamp = str(datetime.now().timestamp())
        
        # 1. PROCESS FILES (GridFS)
        media_id = None
        audio_id = None
        
        # Save Image
        image_bytes = None
        image_mime = None
        if image_file:
            image_bytes = image_file.read()
            image_mime = image_file.mimetype
            media_id = fs.put(image_bytes, filename=f"img_{timestamp}", content_type=image_mime)
            image_file.seek(0) # Reset pointer if needed elsewhere? Not really.

        # Save Audio
        if audio_file:
            audio_id = fs.put(audio_file, filename=f"aud_{timestamp}", content_type=audio_file.mimetype)

        # 2. PROCESS DAILY REWARD
        reward_result = process_daily_rewards(users_col, session['user_id'], msg)
        
        # 3. SEMANTIC CONSTELLATION NAMING
        constellation_name = None
        if reward_result.get('event') == 'constellation_complete':
            # Fetch last 6 entries + current one to name them
            last_entries = history_col.find({"user_id": session['user_id']}, {'full_message': 1}).sort("timestamp", -1).limit(6)
            text_block = msg + " " + " ".join([e.get('full_message','') for e in last_entries])
            constellation_name = generate_constellation_name(text_block)
            
            # Note: Ideally we update previous stars with this name, but for simplicity, 
            # we tag the "Keystone" (7th star) with the name.

        # 4. GENERATE AI REPLY
        reply = "..."
        if mode == 'rant':
            reply = generate_with_media(msg, image_bytes, image_mime, is_void=True)
        else:
            if session.get('awaiting_void_confirm', False):
                if any(x in msg.lower() for x in ["yes", "sure", "ok"]): 
                    reply, command, session['awaiting_void_confirm'] = "Understood. Opening Void...", "switch_to_void", False
                else: 
                    session['awaiting_void_confirm'] = False
                    reply = generate_with_media(f"User declined void. Respond: {msg}", image_bytes, image_mime, False)
            else:
                reply = generate_with_media(msg, image_bytes, image_mime, False)
                if "open The Void" in reply: session['awaiting_void_confirm'] = True

        # 5. SAVE TO DB (Lightweight)
        history_col.insert_one({
            "user_id": session['user_id'],
            "timestamp": timestamp,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": msg[:50] + "..." if msg else "Visual Entry",
            "full_message": msg,
            "reply": reply,
            "ai_analysis": None,
            "mode": mode,
            "has_media": bool(media_id),
            "media_file_id": media_id, # ObjectId
            "has_audio": bool(audio_id),
            "audio_file_id": audio_id, # ObjectId
            "constellation_name": constellation_name, # Saved if this is the 7th star
            "is_valid_star": reward_result['awarded']
        })
        
        # 6. CHECK LEVEL UP
        command = None
        level_check = update_rank_check(users_col, session['user_id'])
        
        if level_check == "level_up": 
            command = "level_up"
            reply += f"\n\n[System]: Level Up! {reward_result.get('message', '')}"
        elif reward_result['awarded']:
            command = "daily_reward"
            reply += f"\n\n[System]: {reward_result['message']}"
            if constellation_name:
                reply += f"\n[Cosmos]: A new constellation has formed: '{constellation_name}'"

        return jsonify({"reply": reply, "command": command})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"reply": f"SYSTEM ERROR: {str(e)}"}), 500

@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    if 'user_id' in session and history_col is not None:
        # Note: Should delete GridFS files too, but keeping simple for now
        history_col.delete_many({"user_id": session['user_id']})
        return jsonify({"status": "success"})
    return jsonify({"status": "error"})

@app.route('/sw.js')
def service_worker(): return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/manifest.json')
def manifest(): return send_from_directory('static', 'manifest.json', mimetype='application/json')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
