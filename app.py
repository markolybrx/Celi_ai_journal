import os, requests, json, time
from flask import Flask, render_template, request, jsonify, session
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.secret_key = "celi_voyager_prestige_2026"
app.permanent_session_lifetime = timedelta(days=30)

VAULT_PATH = 'vault.json'

def get_vault():
    if not os.path.exists(VAULT_PATH):
        with open(VAULT_PATH, 'w') as f: json.dump({"users": {}}, f)
    with open(VAULT_PATH, 'r') as f: return json.load(f)

def save_vault(data):
    with open(VAULT_PATH, 'w') as f: json.dump(data, f, indent=4)

def calculate_rank_and_level(points, last_seen_str):
    today = date.today()
    last_seen = datetime.strptime(last_seen_str, '%Y-%m-%d').date()
    days_missed = (today - last_seen).days
    
    penalty = 0
    if days_missed > 1:
        penalty = days_missed - 1
        points = max(0, points - penalty)

    config = [
        ("Observer", 3, 2),     
        ("Moonwalker", 3, 2),   
        ("Stellar", 4, 3),      
        ("Celestial", 4, 3),    
        ("Interstellar", 5, 4), 
        ("Galactic", 5, 4),     
        ("Ethereal", 5, 8)      
    ]

    current_points = points
    for name, level_count, req in config:
        rank_total = level_count * req
        if current_points >= rank_total:
            if name == "Ethereal" and current_points >= rank_total:
                return name, "I", points, penalty
            current_points -= rank_total
        else:
            levels_cleared = current_points // req
            sub_num = level_count - levels_cleared
            roman = {5: "V", 4: "IV", 3: "III", 2: "II", 1: "I"}
            return name, roman.get(sub_num, "V"), points, penalty
            
    return "Ethereal", "I", points, penalty

@app.route('/')
def index():
    return render_template('index.html' if 'user' in session else 'auth.html')

@app.route('/api/process', methods=['POST'])
def process():
    if 'user' not in session: return jsonify({"error": "Unauthorized"}), 401
    user_id = session['user']
    msg = request.json.get('message', '')
    vault = get_vault()
    user_data = vault['users'][user_id]
    
    # Save History & Add Point
    date_key = time.strftime("%Y-%m-%d")
    user_data['points'] = user_data.get('points', 0) + 1
    user_data['last_seen'] = str(date.today())
    
    # Simple Mock AI Response for speed
    reply = f"Point recorded. Your trajectory is sharpening."
    user_data['history'][date_key] = {"user_msg": msg, "reply": reply, "color": "#A855F7", "ts": time.time()}
    user_data['stars'].append({"color": "#A855F7", "x": 10 + (time.time() % 80), "y": 20 + (time.time() % 60)})
    
    save_vault(vault)
    return jsonify({"reply": reply, "color": "#A855F7"})

@app.route('/api/data')
def get_data():
    if 'user' not in session: return jsonify({})
    vault = get_vault()
    user_data = vault['users'][session['user']]
    
    rank_name, rank_sub, updated_pts, penalty = calculate_rank_and_level(
        user_data.get('points', 0), 
        user_data.get('last_seen', str(date.today()))
    )
    
    user_data['points'] = updated_pts
    user_data['last_seen'] = str(date.today())
    save_vault(vault)

    return jsonify({
        "user_id": session['user'],
        "history": user_data['history'],
        "stars": user_data['stars'],
        "rank": rank_name,
        "level": rank_sub,
        "points": updated_pts,
        "penalty": penalty
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
