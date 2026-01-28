from datetime import datetime, timedelta

# ==================================================
#           ASSET LIBRARY (COLORS & SVGS)
# ==================================================

PHASE_COLORS = {
    "Observer": "#00f2fe", "Moonwalker": "#00f2fe",      
    "Celestial": "#facc15", "Stellar": "#facc15",        
    "Interstellar": "#facc15",
    "Galactic": "#a855f7", "Intergalactic": "#a855f7",   
    "Ethereal": "#ffffff"                                
}

# Geometric Vector Icons (Solid Cutout Style)
RANK_ICONS = {
    'Observer': """<svg viewBox="0 0 24 24" fill="currentColor"><path fill-rule="evenodd" clip-rule="evenodd" d="M12 1C5.9 1 1 5.9 1 12C1 18.1 5.9 23 12 23C18.1 23 23 18.1 23 12C23 5.9 18.1 1 12 1ZM12 18C15.5 18 18.5 15.5 19 12C18.5 8.5 15.5 6 12 6C8.5 6 5.5 8.5 5 12C5.5 15.5 8.5 18 12 18ZM12 14C10.9 14 10 13.1 10 12C10 10.9 10.9 10 12 10C13.1 10 14 10.9 14 12C14 13.1 13.1 14 12 14Z"/></svg>""",
    'Moonwalker': """<svg viewBox="0 0 24 24" fill="currentColor"><path fill-rule="evenodd" clip-rule="evenodd" d="M12 1C5.9 1 1 5.9 1 12C1 18.1 5.9 23 12 23C18.1 23 23 18.1 23 12C23 5.9 18.1 1 12 1ZM12 4C7.58 4 4 7.58 4 12C4 16.42 7.58 20 12 20C16.42 20 20 16.42 20 12C20 7.58 16.42 4 12 4ZM15.5 12C15.5 13.93 13.93 15.5 12 15.5C10.07 15.5 8.5 13.93 8.5 12C8.5 10.07 10.07 8.5 12 8.5C13.93 8.5 15.5 10.07 15.5 12Z"/></svg>""",
    'Celestial': """<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"/></svg>""",
    'Stellar': """<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L14.4 9.6H22L16 14.4L18.4 22L12 17.6L5.6 22L8 14.4L2 9.6H9.6L12 2Z"/></svg>""",
    'Galactic': """<svg viewBox="0 0 24 24" fill="currentColor"><path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 20C7.59 20 4 16.41 4 12C4 7.59 7.59 4 12 4C16.41 4 20 7.59 20 12C20 16.41 16.41 20 12 20ZM12 6C8.69 6 6 8.69 6 12C6 15.31 8.69 18 12 18C15.31 18 18 15.31 18 12C18 8.69 15.31 6 12 6ZM12 16C9.79 16 8 14.21 8 12C8 9.79 9.79 8 12 8C14.21 8 16 9.79 16 12C16 14.21 14.21 16 12 16Z"/></svg>""",
    'Ethereal': """<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM11 19.93C7.05 19.44 4 16.08 4 12C4 7.92 7.05 4.56 11 4.07V19.93ZM13 19.93V4.07C16.95 4.56 20 7.92 20 12C20 16.08 16.95 19.44 13 19.93Z"/></svg>"""
}

# ==================================================
#           RANK HIERARCHY (The 18 Steps)
# ==================================================

RANK_SYSTEM = [
    {"title": "Observer I", "req": 20, "desc": "You are awakening.", "psyche": "The Spark"},
    {"title": "Observer II", "req": 50, "desc": "The fog clears.", "psyche": "The Glimpse"},
    {"title": "Observer III", "req": 100, "desc": "Eyes open wide.", "psyche": "The Sight"},
    
    {"title": "Moonwalker I", "req": 200, "desc": "Gravity loosens.", "psyche": "The Drift"},
    {"title": "Moonwalker II", "req": 350, "desc": "Silence speaks.", "psyche": "The Echo"},
    {"title": "Moonwalker III", "req": 500, "desc": "Walking on light.", "psyche": "The Path"},
    
    {"title": "Celestial I", "req": 800, "desc": "You shine from within.", "psyche": "The Glow"},
    {"title": "Celestial II", "req": 1200, "desc": "Stars align for you.", "psyche": "The Align"},
    {"title": "Celestial III", "req": 1700, "desc": "Burning bright.", "psyche": "The Flame"},
    
    {"title": "Stellar I", "req": 2300, "desc": "A sun is born.", "psyche": "The Core"},
    {"title": "Stellar II", "req": 3000, "desc": "Orbiting the truth.", "psyche": "The Gravity"},
    {"title": "Stellar III", "req": 3800, "desc": "Light reaches far.", "psyche": "The Radius"},
    
    {"title": "Interstellar I", "req": 4800, "desc": "Crossing the void.", "psyche": "The Voyage"},
    {"title": "Interstellar II", "req": 6000, "desc": "Time is fluid.", "psyche": "The Flux"},
    {"title": "Interstellar III", "req": 7500, "desc": "Beyond the veil.", "psyche": "The Beyond"},
    
    {"title": "Galactic I", "req": 10000, "desc": "One with the stars.", "psyche": "The Nexus"},
    {"title": "Intergalactic", "req": 15000, "desc": "Universal mind.", "psyche": "The Cosmos"},
    {"title": "Ethereal", "req": 25000, "desc": "Pure energy.", "psyche": "The Source"}
]

def process_daily_rewards(users_col, user_id, message):
    user = users_col.find_one({"user_id": user_id})
    if not user: return {"awarded": False, "message": "User not found"}
    
    # Simple Stardust Logic
    # 5 Stardust per entry, max once per day (handled by frontend check or simplified here)
    # For Anchor v1.0.0, we just give points for every entry to ensure engagement
    
    points = 5
    if len(message) > 100: points += 5 # Bonus for depth
    
    new_dust = user.get('stardust', 0) + points
    
    users_col.update_one({"user_id": user_id}, {"$set": {"stardust": new_dust}})
    
    return {"awarded": True, "message": f"+{points} Stardust"}

def update_rank_check(users_col, user_id):
    user = users_col.find_one({"user_id": user_id})
    current_dust = user.get('stardust', 0)
    current_idx = user.get('rank_index', 0)
    
    # Cap at max rank
    if current_idx >= len(RANK_SYSTEM) - 1: return None
    
    rank_data = RANK_SYSTEM[current_idx]
    req = rank_data['req']
    
    if current_dust >= req:
        # Level Up!
        new_idx = current_idx + 1
        new_rank_data = RANK_SYSTEM[new_idx]
        
        users_col.update_one({"user_id": user_id}, {
            "$set": {
                "rank_index": new_idx,
                "rank": new_rank_data['title'],
                "stardust": current_dust - req # Reset bucket or keep? Usually reset bucket in this logic
            }
        })
        return "level_up"
    
    return None

def get_rank_meta(idx):
    if idx < 0: idx = 0
    if idx >= len(RANK_SYSTEM): idx = len(RANK_SYSTEM) - 1
    
    data = RANK_SYSTEM[idx].copy()
    base_name = data['title'].split(' ')[0]
    data['svg'] = RANK_ICONS.get(base_name, RANK_ICONS.get('Observer'))
    data['color'] = PHASE_COLORS.get(base_name, "#00f2fe")
    return data

def get_all_ranks_data():
    return RANK_SYSTEM
