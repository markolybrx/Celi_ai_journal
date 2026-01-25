# ==================================================
#           CELI RANKING SYSTEM & LORE
# ==================================================

RANK_SYSTEM = [
    # --- PHASE 1: THE DEPARTURE (Observation & Grounding) ---
    {"title": "Observer III", "req": 20, "psyche": "The Separation", "desc": "You begin to separate the thinker from the thought. You are stepping back from the noise to simply watch."},
    {"title": "Observer II", "req": 20, "psyche": "The Pattern Recognition", "desc": "Through your entries, constellations of behavior appear. You notice the cycles you used to repeat blindly."},
    {"title": "Observer I", "req": 20, "psyche": "The Orbital View", "desc": "You have achieved distance. Your problems look smaller from here; you are watching your life rather than just reacting to it."},
    
    {"title": "Moonwalker III", "req": 50, "psyche": "The First Step", "desc": "You leave the gravity of your comfort zone. The terrain of your inner world is grey and unfamiliar, but you are walking it."},
    {"title": "Moonwalker II", "req": 50, "psyche": "The Crater Study", "desc": "You explore the impact sites of your past. You realize that scars are just geography, not definitions."},
    {"title": "Moonwalker I", "req": 50, "psyche": "The Earthrise", "desc": "Looking back at your old self from a distance, you feel a profound shift in perspective. You are not who you were."},

    # --- PHASE 2: THE IGNITION (Formation & Endurance) ---
    {"title": "Celestial IV", "req": 80, "psyche": "The Accretion", "desc": "You are gathering your fragmented parts. Memories and hopes coalesce into a solid, spherical identity."},
    {"title": "Celestial III", "req": 80, "psyche": "The Atmosphere", "desc": "You develop a protective layer. Your journal burns up the meteors of daily stress before they can strike the surface."},
    {"title": "Celestial II", "req": 80, "psyche": "The Axis", "desc": "You find your tilt. You accept your seasons—the cold winters and warm summers—as necessary cycles."},
    {"title": "Celestial I", "req": 80, "psyche": "The Gravity", "desc": "You now possess weight. You do not chase orbit; you attract what belongs to you through the power of your core."},

    {"title": "Stellar IV", "req": 100, "psyche": "The Protostar", "desc": "Pressure builds. You realize that the crushing weight of life is actually the fuel for your ignition."},
    {"title": "Stellar III", "req": 100, "psyche": "The Fusion", "desc": "Alchemy. You take the hydrogen of your pain and fuse it into the helium of wisdom. You are generating heat."},
    {"title": "Stellar II", "req": 100, "psyche": "The Photosphere", "desc": "You stop reflecting the light of others and begin to radiate your own. Your authenticity is becoming visible."},
    {"title": "Stellar I", "req": 100, "psyche": "The Main Sequence", "desc": "Stability. You burn steadily and brightly. You have found the fuel source that will sustain you for a lifetime."},

    {"title": "Interstellar IV", "req": 120, "psyche": "The Departure", "desc": "You leave the safety of known systems. You journal about the unknown, facing the deep silence between chapters of your life."},
    {"title": "Interstellar III", "req": 120, "psyche": "The Dark Nebula", "desc": "You navigate through the clouds that obscure vision. You learn to trust your internal compass when you cannot see the stars."},
    {"title": "Interstellar II", "req": 120, "psyche": "Time Dilation", "desc": "You realize healing is relative. A moment of realization can undo years of stagnation. You travel at your own speed."},
    {"title": "Interstellar I", "req": 120, "psyche": "The Event Horizon", "desc": "You approach a point of no return. The insights you have gained are about to pull you into a new reality."},

    # --- PHASE 3: THE TRANSCENDENCE (Systemic Connection) ---
    {"title": "Galactic V", "req": 150, "psyche": "The Spiral Arm", "desc": "You see the structure. Childhood trauma, present joy, and future hope are all connected in one great spiral."},
    {"title": "Galactic IV", "req": 150, "psyche": "The Rotation", "desc": "You stop fighting the current. You spin with the galaxy, accepting the flow of uncontrollable events."},
    {"title": "Galactic III", "req": 150, "psyche": "Dark Matter", "desc": "You acknowledge the invisible forces—the subconscious drives—that hold your visible life together."},
    {"title": "Galactic II", "req": 150, "psyche": "The Supermassive", "desc": "You face the void at your center. You realize it is not emptiness, but infinite density and potential."},
    {"title": "Galactic I", "req": 150, "psyche": "The System", "desc": "You are not a solitary star. You contain billions of moments, a complex ecosystem of self."},

    {"title": "Intergalactic V", "req": 180, "psyche": "The Filament", "desc": "You sense the web. Through writing, you connect your story to the universal human experience."},
    {"title": "Intergalactic IV", "req": 180, "psyche": "The Drift", "desc": "There is no up or down in the cosmos. You release the need for rigid definitions of success or failure."},
    {"title": "Intergalactic III", "req": 180, "psyche": "Redshift", "desc": "You are expanding. You are moving away from your origin point so fast that the light of the past changes color."},
    {"title": "Intergalactic II", "req": 180, "psyche": "The Great Attractor", "desc": "You are pulled toward a destiny you cannot see but can feel. You trust the pull."},
    {"title": "Intergalactic I", "req": 180, "psyche": "The Cosmic Scale", "desc": "Ego death. Your daily anxieties are merely dust against the background radiation of your spirit."},

    {"title": "Ethereal VI", "req": 200, "psyche": "The Nebula", "desc": "Form becomes fluid. You realize you can reshape your narrative at will. You are the cloud before the star."},
    {"title": "Ethereal V", "req": 200, "psyche": "Quantum Superposition", "desc": "You accept contradiction. You can be both sad and grateful, lost and found, simultaneously."},
    {"title": "Ethereal IV", "req": 200, "psyche": "Entanglement", "desc": "You understand that nothing is separate. Your past self and future self are communicating across time."},
    {"title": "Ethereal III", "req": 200, "psyche": "The Singularity", "desc": "Focus becomes infinite. The barrier between the writer and the written word dissolves."},
    {"title": "Ethereal II", "req": 200, "psyche": "The Big Bang", "desc": "Creation. You speak, and a new universe is born. You are the author of your reality."},
    {"title": "Ethereal I", "req": 200, "psyche": "The Source", "desc": "You return to the beginning, but with full knowledge. You are the Universe experiencing itself."}
]

def update_rank_progress(users_col, user_id):
    """
    Calculates Stardust gain and checks for Rank Level Up.
    Returns: 'level_up', 'xp_gain', or None
    """
    user = users_col.find_one({"user_id": user_id})
    if not user: return None
    
    current_idx = user.get("rank_index", 0)
    current_stardust = user.get("stardust", 0)
    
    # AWARD XP (5 SD per entry)
    stardust_gain = 5 
    new_stardust = current_stardust + stardust_gain
    
    # Get stats for current rank
    rank_data = RANK_SYSTEM[current_idx] if current_idx < len(RANK_SYSTEM) else RANK_SYSTEM[-1]
    req = rank_data['req']
    leveled_up = False
    new_rank_title = rank_data['title']
    
    # CHECK LEVEL UP
    # If we have enough dust AND we are not at the final rank
    if new_stardust >= req and current_idx < len(RANK_SYSTEM) - 1:
        new_stardust = new_stardust - req  # Carry over overflow dust
        current_idx += 1                   # Increment Rank Index
        new_rank_title = RANK_SYSTEM[current_idx]['title']
        leveled_up = True
        
    # SAVE TO DB
    users_col.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "rank_index": current_idx,
                "rank": new_rank_title,
                "stardust": new_stardust
            }
        }
    )
    
    return "level_up" if leveled_up else "xp_gain"

def get_rank_meta(idx):
    """Returns the metadata (req, psyche, desc) for a given rank index."""
    if idx < 0: idx = 0
    if idx >= len(RANK_SYSTEM): idx = len(RANK_SYSTEM) - 1
    return RANK_SYSTEM[idx]
