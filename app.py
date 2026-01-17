import json, requests, os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Render will pull this from your Environment Variables
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def ask_groq(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-70b-versatile",
        "messages": messages, 
        "response_format": {"type": "json_object"}
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=25)
        res.raise_for_status()
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"DIAGNOSTIC: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process():
    data = request.json
    if not GROQ_API_KEY:
        return jsonify({"mood":"angry", "reply":"API KEY MISSING IN RENDER DASHBOARD.", "insight":None})
    
    profile = data.get('profile', {})
    history = data.get('history', [])
    
    # SYSTEM PROMPT: Mirror Protocol
    sys_msg = (
        f"You are Celi, the sovereign advisor for {profile.get('name')}. "
        "Identity: Brutally honest, smart-casual, witty mirror. "
        "Instructions: Challenge assumptions and identify loops. "
        "Return JSON: {'mood':'sharp', 'reply':'text', 'insight':'text'}"
    )
    
    ai_raw = ask_groq([{"role": "system", "content": sys_msg}, {"role": "user", "content": data['message']}])
    
    if ai_raw is None:
        return jsonify({"mood":"anxious", "reply":"Handshake failed at the API level.", "insight":None})
    
    return ai_raw

if __name__ == '__main__':
    app.run(debug=True)
  
