def ask_groq(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",  # Switched to the most stable high-speed model
        "messages": messages,
        "temperature": 0.7 # Added to ensure creative but stable responses
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=25)
        # This will now print the EXACT error message from Groq in your Render logs
        if res.status_code != 200:
            print(f"GROQ ERROR: {res.status_code} - {res.text}")
        res.raise_for_status()
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"DIAGNOSTIC: {str(e)}")
        return None

@app.route('/api/process', methods=['POST'])
def process():
    data = request.json
    if not GROQ_API_KEY:
        return jsonify({"mood":"angry", "reply":"API KEY MISSING", "insight":None})
    
    profile = data.get('profile', {})
    history = data.get('history', [])
    
    # Updated prompt: Removed JSON constraint to prevent 400 errors
    sys_msg = (
        f"You are Celi, sovereign advisor for {profile.get('name')}. "
        "Tone: Brutally honest, smart-casual, witty. "
        "Identify blind spots. Always reply in valid JSON format: "
        '{"mood":"sharp", "reply":"your_text", "insight":"one_sentence_insight"}'
    )
    
    ai_raw = ask_groq([{"role": "system", "content": sys_msg}, {"role": "user", "content": data['message']}])
    
    if ai_raw is None:
        return jsonify({"mood":"anxious", "reply":"The API handshake failed. Check Render logs for the GROQ ERROR line.", "insight":None})
    
    # We return the raw string because the AI is instructed to format it as JSON
    return ai_raw
    
