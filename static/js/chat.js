// --- CHAT & INTERACTION LOGIC ---

// Shared State
let currentMode = 'journal'; 

function openChat(mode) { 
    currentMode = mode; 
    const modal = document.getElementById('chat-overlay');
    const windowEl = document.getElementById('chat-modal-window');
    const title = document.getElementById('chat-header-title');
    const subtitle = document.getElementById('chat-header-subtitle');
    const iconContainer = document.getElementById('chat-header-icon');

    // 1. Set Theme
    if (mode === 'rant') {
        windowEl.className = "relative w-full max-w-md flex flex-col shadow-2xl overflow-hidden transition-all duration-500 origin-void";
        title.innerText = "THE VOID";
        subtitle.innerText = "SCREAM INTO THE ABYSS";
        iconContainer.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M8 12h8"></path></svg>`;
        if(typeof SonicAtmosphere !== 'undefined') SonicAtmosphere.playMode('rant');
    } else {
        windowEl.className = "relative w-full max-w-md bg-[var(--card-bg)] border border-[var(--border)] rounded-3xl flex flex-col shadow-2xl overflow-hidden transition-all duration-500 origin-ai";
        title.innerText = "CELI AI";
        subtitle.innerText = "JOURNAL COMPANION";
        iconContainer.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 0 1 10 10 10 10 0 0 1-10 10 10 10 0 0 1-10-10 10 10 0 0 1 10-10z"></path><path d="M8 12h8"></path><path d="M12 8v8"></path></svg>`;
        if(typeof SonicAtmosphere !== 'undefined') SonicAtmosphere.playMode('journal');
    }

    // 2. Render History
    renderChatHistory(fullChatHistory);

    // 3. Show Modal
    modal.classList.remove('hidden');
    setTimeout(() => {
        modal.classList.remove('opacity-0');
        document.getElementById('chat-input').focus();
    }, 10);
}

function closeChat() { 
    const modal = document.getElementById('chat-overlay');
    modal.classList.add('opacity-0');
    setTimeout(() => {
        modal.classList.add('hidden');
    }, 300);
    if(typeof SonicAtmosphere !== 'undefined') SonicAtmosphere.playMode('journal'); 
}

// --- MESSAGE RENDERING ---
function renderChatHistory(h) { 
    const c = document.getElementById('chat-history'); 
    c.innerHTML = ''; // Clear current
    
    // Sort and display last 50
    Object.keys(h).sort().slice(-50).forEach(k => { 
        const entry = h[k];
        // Only show relevant history? Or mixed?
        // Unified view usually shows mixed, but we can filter if desired.
        // For now, restoring behavior: Show all.
        if (entry.user_msg) appendMsg(entry.user_msg, 'user');
        if (entry.reply) appendMsg(entry.reply, 'ai');
    }); 
    c.scrollTop = c.scrollHeight;
}

async function sendMessage() { 
    if(isProcessing) return; 
    const input = document.getElementById('chat-input'); 
    const msg = input.value.trim(); 
    if(!msg && !activeMediaFile && !activeAudioFile) return; 
    
    appendMsg(msg || "[Media Transmitting...]", 'user'); 
    input.value=''; isProcessing=true; showTyping();

    const formData = new FormData(); 
    formData.append('message', msg); formData.append('mode', currentMode); 
    if(activeMediaFile) formData.append('media', activeMediaFile); 
    if(activeAudioFile) formData.append('audio', activeAudioFile); 
    
    try { 
        const res = await fetch('/api/process', { method:'POST', body: formData }); 
        const data = await res.json(); 
        hideTyping(); appendMsg(data.reply, 'ai'); 
        
        if(data.command === 'daily_reward' || data.command === 'level_up') spawnStardust(); 
        if(data.command === 'switch_to_void') setTimeout(()=>openChat('rant'), 1000); 
        
        activeMediaFile = null; activeAudioFile = null; 
        document.getElementById('media-preview').classList.add('hidden');
        document.getElementById('chat-input').placeholder = "Type a message..."; 
        
        await loadData(); 
    } catch(e) { hideTyping(); appendMsg("Signal Lost.", 'ai'); } 
    isProcessing=false; 
}

function appendMsg(txt, sender) { 
    const div = document.createElement('div'); 
    div.className = `msg msg-${sender}`; 
    div.innerHTML = parseMarkdown(txt); 
    
    if (sender === 'ai') {
        // Voice button logic
        const btn = document.createElement('span'); 
        btn.className = 'voice-play-btn'; 
        btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon></svg>`;
        btn.onclick = () => speakText(txt.replace(/\*/g, '')); 
        div.appendChild(btn);
    }
    
    const history = document.getElementById('chat-history'); 
    history.appendChild(div); 
    history.scrollTop = history.scrollHeight; 
}

function showTyping() { 
    const indicator = document.getElementById('typing-indicator');
    indicator.classList.remove('hidden'); 
    document.getElementById('chat-history').appendChild(indicator);
    document.getElementById('chat-history').scrollTop = 9999; 
}
function hideTyping() { document.getElementById('typing-indicator').classList.add('hidden'); }

// --- MEDIA UTILS ---
function handleFileSelect() { 
    const input = document.getElementById('img-upload'); 
    if(input.files && input.files[0]) { 
        activeMediaFile = input.files[0]; 
        document.getElementById('media-preview').classList.remove('hidden');
        document.querySelector('#media-preview span').innerText = "Image attached";
    } 
}
function handleAudioSelect() { 
    const input = document.getElementById('audio-upload'); 
    if(input.files && input.files[0]) { 
        activeAudioFile = input.files[0]; 
        sendMessage(); // Auto send
    } 
}
function toggleMic() { document.getElementById('audio-upload').click(); }
function clearMedia() {
    activeMediaFile = null;
    document.getElementById('img-upload').value = "";
    document.getElementById('media-preview').classList.add('hidden');
}

// --- ARCHIVE LOGIC (Restored) ---
function openArchive(id) { 
    const modal = document.getElementById('archive-modal'); 
    modal.classList.add('active'); 
    modal.style.display = 'flex'; // Flex for centering

    // Reset
    document.getElementById('archive-date').innerText = "Loading...";
    document.getElementById('archive-analysis').innerText = "Loading synthesis...";
    document.getElementById('archive-image-container').classList.add('hidden');
    document.getElementById('archive-audio-container').classList.add('hidden');

    fetch('/api/star_detail', { 
        method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id})
    }).then(r=>r.json()).then(d=>{
        document.getElementById('archive-date').innerText = d.date;
        document.getElementById('archive-analysis').innerText = d.analysis || d.summary || "No data.";
        if(d.image_url) {
            document.getElementById('archive-image-container').classList.remove('hidden');
            document.getElementById('archive-image').src = d.image_url;
        }
    });
}
function closeArchive() {
    const modal = document.getElementById('archive-modal');
    modal.classList.remove('active');
    setTimeout(()=>modal.style.display='none', 300);
}

// --- HELPERS ---
function parseMarkdown(text) { return text ? text.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>').replace(/\*(.*?)\*/g, '<i>$1</i>').replace(/\n/g, '<br>') : ''; }
function speakText(text) { if('speechSynthesis' in window) { window.speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(text); window.speechSynthesis.speak(u); } }
function spawnStardust() { /* ... existing animation code ... */ }
