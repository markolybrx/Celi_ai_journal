from datetime import datetime, timedelta

# ==================================================
#           CELI RANKING SYSTEM & LORE (v5.0)
# ==================================================

# --- HELPER: ROMAN NUMERALS ---
def to_roman(n):
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syb = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    roman_num = ''
    i = 0
    while n > 0:
        for _ in range(n // val[i]):
            roman_num += syb[i]
            n -= val[i]
        i += 1
    return roman_num

# --- STATIC RANKS (PHASE 1 - 3) ---
STATIC_RANKS = [
    # --- PHASE 1: THE DEPARTURE (Ice Blue) ---
    {"title": "Observer III", "req": 20, "psyche": "The Telescope", "desc": "Like a lens focusing on the dark, you are learning to view your chaotic thoughts without engaging with them."},
    {"title": "Observer II", "req": 20, "psyche": "The Constellation", "desc": "You no longer see random stars of emotion; you see patterns and shapes in your behavior."},
    {"title": "Observer I", "req": 20, "psyche": "The Overview Effect", "desc": "You have achieved orbit. Looking down at your life from this distance, the storms look peaceful."},
    
    {"title": "Moonwalker III", "req": 50, "psyche": "The Launch", "desc": "You have escaped the gravity of your comfort zone. The silence of this new terrain is heavy, but you are here."},
    {"title": "Moonwalker II", "req": 50, "psyche": "The Dark Side", "desc": "You are walking into the craters of your shadow self, exploring the parts of you that never see the sun."},
    {"title": "Moonwalker I", "req": 50, "psyche": "The Earthrise", "desc": "Standing on your subconscious, you look back at your old identity. It is small, fragile, and beautiful."},

    # --- PHASE 2: THE IGNITION (Solar Gold) ---
    {"title": "Celestial IV", "req": 80, "psyche": "Accretion", "desc": "Like dust forming a world, you are gathering your fragmented memories into a solid, spherical identity."},
    {"title": "Celestial III", "req": 80, "psyche": "Atmosphere", "desc": "You have grown a shield. You burn up the meteors of daily anxiety before they can strike your surface."},
    {"title": "Celestial II", "req": 80, "psyche": "Axial Tilt", "desc": "You accept your internal seasons. You know that your cold winters are just a necessary part of your rotation."},
    {"title": "Celestial I", "req": 80, "psyche": "Gravity", "desc": "You have mass now. You do not chase things; you orbit in your lane and attract what belongs to you."},

    {"title": "Stellar IV", "req": 100, "psyche": "Protostar", "desc": "You realize that the crushing pressure you feel is not destruction; it is the gravity required for ignition."},
    {"title": "Stellar III", "req": 100, "psyche": "Nuclear Fusion", "desc": "Alchemy. You are taking the hydrogen of your pain and fusing it into the helium of wisdom. You generate heat."},
    {"title": "Stellar II", "req": 100, "psyche": "Photosphere", "desc": "You stop reflecting the light of others. You are now the source of light in your own system."},
    {"title": "Stellar I", "req": 100, "psyche": "Main Sequence", "desc": "Stability. You have found the equilibrium between gravity (discipline) and pressure (passion). You burn eternal."},

    {"title": "Interstellar IV", "req": 120, "psyche": "Heliopause", "desc": "You are leaving the magnetic protection of the known. You journal into the deep silence between chapters."},
    {"title": "Interstellar III", "req": 120, "psyche": "The Void", "desc": "There are no stars here to guide you. You must trust your internal navigation systems."},
    {"title": "Interstellar II", "req": 120, "psyche": "Time Dilation", "desc": "In the deep space of healing, time moves differently. A single realization changes years of history."},
    {"title": "Interstellar I", "req": 120, "psyche": "New Horizons", "desc": "You have crossed the great dark. A new system of thought is appearing on your sensors."},

    # --- PHASE 3: THE TRANSCENDENCE (Cosmic Purple) ---
    {"title": "Galactic V", "req": 150, "psyche": "The Spiral Arm", "desc": "You see the structure. Your past trauma and future hope are connected strands in one great design."},
    {"title": "Galactic IV", "req": 150, "psyche": "Rotation Curve", "desc": "You stop fighting the spin. You move with the flow of the universe, trusting the velocity of your life."},
    {"title": "Galactic III", "req": 150, "psyche": "Dark Matter", "desc": "You acknowledge the invisible forces—your subconscious drives—that hold your visible life together."},
    {"title": "Galactic II", "req": 150, "psyche": "Supermassive Core", "desc": "You face the hole at your center. You realize it is not emptiness, but infinite density and potential."},
    {"title": "Galactic I", "req": 150, "psyche": "The Ecosystem", "desc": "You are not a solitary star. You contain billions of moments, a complex galaxy of self."},

    {"title": "Intergalactic V", "req": 180, "psyche": "The Filament", "desc": "You sense the web. Through writing, you connect your story to the universal human experience."},
    {"title": "Intergalactic IV", "req": 180, "psyche": "The Great Void", "desc": "There is no up or down in space. You release the rigid definitions of success or failure."},
    {"title": "Intergalactic III", "req": 180, "psyche": "Redshift", "desc": "You are expanding. You are moving away from your origin point so fast that the light of the past changes color."},
    {"title": "Intergalactic II", "req": 180, "psyche": "The Great Attractor", "desc": "You are being pulled toward a destiny you cannot see but can feel. You trust the pull."},
    {"title": "Intergalactic I", "req": 180, "psyche": "Cosmic Scale", "desc": "Ego death. Your daily anxieties are merely dust against the background radiation of your spirit."},
]

# --- DYNAMIC RANKS (PHASE 4: ETHEREAL ASCENSION) ---
ETHEREAL_RANKS = []
base_req = 200  # Starting cost for Ethereal I

# Fixed Cycle of 10 for Ethereal
ethereal_states = [
    {"name": "The Nebula", "desc": "Form becomes fluid. You realize you can reshape your narrative at will. You are the cloud before the star."},
    {"name": "Quantum Superposition", "desc": "You accept contradiction. You can be both sad and grateful, lost and found, simultaneously."},
    {"name": "Entanglement", "desc": "You understand that nothing is separate. Your past self and future self are communicating across time."},
    {"name": "Relativity", "desc": "Your perspective defines your reality. By changing how you view the past, you physically change its weight."},
    {"name": "The Singularity", "desc": "Focus becomes infinite. The barrier between the writer and the written word dissolves."},
    {"name": "The Big Bang", "desc": "Creation. You speak, and a new universe is born. You are the author of your reality."},
    {"name": "Dark Energy", "desc": "Expansion. You are growing faster than the universe can contain you. You push boundaries effortlessly."},
    {"name": "Cosmic Background", "desc": "Memory. You carry the heat of your creation, but it no longer burns; it just sustains you."},
    {"name": "The Multiverse", "desc": "Possibility. You see every choice you didn't make not as a loss, but as a life lived elsewhere."},
    {"name": "The Source", "desc": "You return to the beginning, but with full knowledge. You are the Universe experiencing itself."}
]

# Generate Ethereal I to Ethereal X (10 levels)
for i in range(1, 11):
    roman = to_roman(i)
    cost = base_req + ((i - 1) * 100) # 200, 300, 400...
    state = ethereal_states[i-1]
    
    ETHEREAL_RANKS.append({
        "title": f"Ethereal {roman}",
        "req": cost,
        "psyche": state["name"],
        "desc": state["desc"]
    })

RANK_SYSTEM = STATIC_RANKS + ETHEREAL_RANKS

# ==================================================
#           DAILY REWARD & STREAK LOGIC
# ==================================================

def check_entry_quality(msg):
    """
    Quality control: Entry must be > 30 chars to earn Stardust.
    """
    if len(msg.strip()) < 30:
        return False
    return True

def process_daily_rewards(users_col, user_id, msg):
    """
    Calculates Daily Rewards, Streaks, and Constellation Bonuses.
    Returns: { 'awarded': bool, 'total_gain': int, 'message': str, 'event': str }
    """
    if users_col is None: return {'awarded': False}

    # 1. QUALITY CHECK
    if not check_entry_quality(msg):
        return {'awarded': False, 'message': "Entry too short for Stardust."}

    user = users_col.find_one({"user_id": user_id})
    if not user: return {'awarded': False}

    today_str = datetime.now().strftime("%Y-%m-%d")
    last_reward = user.get("last_reward_date") 
    current_streak = user.get("current_streak", 0)
    current_dust = user.get("stardust", 0)
    stars_count = user.get("star_count", 0) 

    # 2. CHECK IF ALREADY REWARDED TODAY
    if last_reward == today_str:
        return {'awarded': False, 'message': "Daily reward already claimed."}

    # 3. CALCULATE STREAK
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    if last_reward == yesterday_str:
        current_streak += 1
    else:
        current_streak = 1 # Reset if missed a day

    # 4. CALCULATE REWARDS
    base_sd = 5
    streak_sd = base_sd * current_streak
    
    # 5. CONSTELLATION BONUS (Every 7th Star/Entry)
    stars_count += 1
    constellation_bonus = 0
    is_constellation_complete = (stars_count % 7 == 0)
    
    if is_constellation_complete:
        constellation_bonus = 10
    
    total_gain = streak_sd + constellation_bonus
    new_dust = current_dust + total_gain
    
    # 6. UPDATE DB
    users_col.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "stardust": new_dust,
                "current_streak": current_streak,
                "last_reward_date": today_str,
                "star_count": stars_count
            }
        }
    )

    # 7. FORMAT FEEDBACK MESSAGE
    event_type = "daily_reward"
    msg_text = f"+{streak_sd} SD (Streak x{current_streak})"
    
    if constellation_bonus: 
        msg_text += f"\n+10 SD (Constellation Completed!)"
        event_type = "constellation_complete"

    return {
        'awarded': True, 
        'total_gain': total_gain, 
        'message': msg_text,
        'event': event_type
    }

def update_rank_check(users_col, user_id):
    """
    Checks if current stardust is enough to Level Up.
    Does NOT award XP, just processes Rank Changes.
    """
    if users_col is None: return None
    
    user = users_col.find_one({"user_id": user_id})
    current_idx = user.get("rank_index", 0)
    current_dust = user.get("stardust", 0)
    
    rank_data = RANK_SYSTEM[current_idx] if current_idx < len(RANK_SYSTEM) else RANK_SYSTEM[-1]
    req = rank_data['req']
    
    if current_dust >= req and current_idx < len(RANK_SYSTEM) - 1:
        new_dust = current_dust - req # Carry over overflow
        current_idx += 1
        new_rank = RANK_SYSTEM[current_idx]['title']
        
        users_col.update_one({"user_id": user_id}, {
            "$set": {"rank_index": current_idx, "rank": new_rank, "stardust": new_dust}
        })
        return "level_up"
    return None

def get_rank_meta(idx):
    if idx < 0: idx = 0
    if idx >= len(RANK_SYSTEM): idx = len(RANK_SYSTEM) - 1
    return RANK_SYSTEM[idx]
