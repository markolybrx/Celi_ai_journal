import os, requests, json, time
from flask import Flask, render_template, request, jsonify, session
from datetime import date, datetime, timedelta

app = Flask(__name__)
app.secret_key = "celi_fchq_8.5_geometric_ascension"
VAULT_PATH = 'vault.json'

RANK_CONFIG = [
    {"name": "Observer", "levels": 3, "stars_per_lvl": 2},
    {"name": "Moonwalker", "levels": 3, "stars_per_lvl": 2},
    {"name": "Stellar", "levels": 4, "stars_per_lvl": 3},
    {"name": "Celestial", "levels": 4, "stars_per_lvl": 3},
    {"name": "Interstellar", "levels": 5, "stars_per_lvl": 4},
    {"name": "Galactic", "levels": 5, "stars_per_lvl": 4},
    {"name": "Ethereal", "levels": 5, "stars_per_lvl": 8}
]

def get_rank_and_level(pts):
    cumulative = 0
    roman = ["V", "IV", "III", "II", "I"]
    for rank in RANK_CONFIG:
        rank_total = rank['levels'] * rank['stars_per_lvl']
        if pts < cumulative + rank_total:
            pts_in_rank = pts - cumulative
            level_idx = pts_in_rank // rank['stars_per_lvl']
            roman_subset = roman[5-rank['levels']:] 
            current_sub_lvl = roman_subset[level_idx] if level_idx < rank['levels'] else roman_subset[-1]
            lvl_floor = cumulative + (level_idx * rank['stars_per_lvl'])
            progress = ((pts - lvl_floor) / rank['stars_per_lvl']) * 100
            return f"{rank['name']} {current_sub_lvl}", progress
        cumulative += rank_total
    return "Ethereal I", 100

def handle_decay(user):
    last_str = user.get('last_journal_date')
    if last_str:
        last_date = datetime.strptime(last_str, '%Y-%m-%d').date()
        days_missed = (date.today() - last_date).days
        if days_missed > 1:
            penalty = days_missed - 1
            user['points'] = max(0, user.get('points', 0) - penalty)
            return True
    return False

@app.route('/api/data')
def get_data():
    if 'user' not in session: return jsonify({})
    v = json.load(open(VAULT_PATH)); u = v['users'][session['user']]
    decayed = handle_decay(u)
    with open(VAULT_PATH, 'w') as f: json.dump(v, f, indent=4)
    rank_str, rank_pct = get_rank_and_level(u.get('points', 0))
    return jsonify({
        "rank": rank_str, 
        "rank_progress": rank_pct, 
        "decayed": decayed, 
        "void_count": u['void_count'], 
        "history": u['history'], 
        "date": date.today().strftime("%b %d")
    })

@app.route('/api/process', methods=['POST'])
def process():
    v = json.load(open(VAULT_PATH)); u = v['users'][session['user']]
    data = request.json
    msg = data.get('message', '')
    is_rant = data.get('mode') == 'rant'
    
    sys = "You are Celi. Heart-spoken, witty. If rant: be a listener. If journal: be a mirror. JSON response only."
    res = requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
        json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": sys}, {"role": "user", "content": msg}], "response_format": {"type": "json_object"}})
    ai = json.loads(res.json()['choices'][0]['message']['content'])
    
    if not is_rant:
        u['points'] = u.get('points', 0) + 1
    else:
        u['void_count'] = u.get('void_count', 0) + 1
        
    u['last_journal_date'] = str(date.today())
    u['history'][str(time.time())] = {"user_msg": msg, "reply": ai['reply'], "date": str(date.today()), "summary": ai['summary'], "type": data.get('mode')}
    with open(VAULT_PATH, 'w') as f: json.dump(v, f, indent=4)
    return jsonify(ai)
    
