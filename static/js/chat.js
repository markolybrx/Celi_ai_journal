function openChat(mode) { 
    currentMode = mode; 
    const modal = document.getElementById('chat-overlay');
    const windowEl = document.getElementById('chat-modal-window');
    const title = document.getElementById('chat-header-title');
    const subtitle = document.getElementById('chat-header-subtitle');
    const iconContainer = document.getElementById('chat-header-icon');

    // 1. Set Theme Class
    if (mode === 'rant') {
        windowEl.classList.remove('origin-ai');
        windowEl.classList.add('origin-void');
        title.innerText = "THE VOID";
        title.style.color = "#ef4444";
        subtitle.innerText = "SCREAM INTO THE ABYSS";
        iconContainer.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="8" y1="12" x2="16" y2="12"></line></svg>`;
    } else {
        windowEl.classList.remove('origin-void');
        windowEl.classList.add('origin-ai');
        title.innerText = "CELI AI";
        title.style.color = "var(--text)";
        subtitle.innerText = "JOURNAL COMPANION";
        iconContainer.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 0 1 10 10 10 10 0 0 1-10 10 10 10 0 0 1-10-10 10 10 0 0 1 10-10z"></path></svg>`;
    }

    // 2. Render History
    renderChatHistory();

    // 3. Show
    modal.classList.add('active');
    setTimeout(() => { document.getElementById('chat-input').focus(); }, 100);
}

function closeChat() { document.getElementById('chat-overlay').classList.remove('active'); }

function renderChatHistory() { 
    const c = document.getElementById('chat-history'); c.innerHTML = '';
    // Sort logic here if needed, or pull from memory
    const sortedKeys = Object.keys(fullChatHistory).sort().slice(-50);
    sortedKeys.forEach(k => {
        const entry = fullChatHistory[k];
        if(entry.full_message) appendMsg(entry.full_message, 'user');
        if(entry.reply) appendMsg(entry.reply, 'ai');
    });
    c.scrollTop = c.scrollHeight;
}

async function sendMessage() { 
    if(isProcessing) return; 
    const input = document.getElementById('chat-input'); 
    const msg = input.value.trim(); 
    if(!msg && !activeMediaFile && !activeAudioFile) return; 
    
    appendMsg(msg || "[Media Transmitting...]", 'user'); 
    input.value=''; isProcessing=true; 
    document.getElementById('typing-indicator').classList.remove('hidden');

    const formData = new FormData(); 
    formData.append('message', msg); formData.append('mode', currentMode); 
    if(activeMediaFile) formData.append('media', activeMediaFile); 
    if(activeAudioFile) formData.append('audio', activeAudioFile); 
    
    try { 
        const res = await fetch('/api/process', { method:'POST', body: formData }); 
        const data = await res.json(); 
        document.getElementById('typing-indicator').classList.add('hidden');
        appendMsg(data.reply, 'ai'); 
        
        if(data.command === 'switch_to_void') setTimeout(()=>openChat('rant'), 1500);
        if(data.command === 'level_up' || data.command === 'daily_reward') loadData(); // Refresh stats
        
        activeMediaFile = null; activeAudioFile = null; 
    } catch(e) { 
        document.getElementById('typing-indicator').classList.add('hidden');
        appendMsg("Connection Lost.", 'ai'); 
    } 
    isProcessing=false; 
}

function appendMsg(txt, sender) { 
    const div = document.createElement('div'); 
    div.className = `msg msg-${sender}`; 
    div.innerText = txt; // Simple text for now, markdown if needed
    document.getElementById('chat-history').insertBefore(div, document.getElementById('typing-indicator'));
    document.getElementById('chat-history').scrollTop = 99999;
}

// Media handlers
function handleFileSelect() { activeMediaFile = document.getElementById('img-upload').files[0]; }
function toggleMic() { document.getElementById('audio-upload').click(); }
function handleAudioSelect() { activeAudioFile = document.getElementById('audio-upload').files[0]; sendMessage(); }
