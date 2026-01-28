// --- DUAL CHAT LOGIC ---

// Global Refs
let activeChatMode = null; // 'journal' or 'rant'

function openChat(mode) { 
    activeChatMode = mode; 
    const modalId = mode === 'journal' ? 'celi-modal' : 'void-modal';
    
    // Open specific modal
    document.getElementById(modalId).classList.add('active');
    
    // Play Sound
    if(typeof SonicAtmosphere !== 'undefined') SonicAtmosphere.playMode(mode); 
    
    // Render History specific to mode
    renderChatHistory(mode);
    
    // Focus Input
    const inputId = mode === 'journal' ? 'celi-input' : 'void-input';
    setTimeout(() => document.getElementById(inputId).focus(), 100);
}

function closeChat(mode) { 
    const modalId = mode === 'journal' ? 'celi-modal' : 'void-modal';
    document.getElementById(modalId).classList.remove('active');
    if(typeof SonicAtmosphere !== 'undefined') SonicAtmosphere.playMode('journal'); 
    activeChatMode = null;
}

function renderChatHistory(mode) {
    const containerId = mode === 'journal' ? 'celi-history' : 'void-history';
    const container = document.getElementById(containerId);
    container.innerHTML = ''; // Clear
    
    // Filter history by mode
    const sortedKeys = Object.keys(fullChatHistory).sort();
    
    sortedKeys.slice(-50).forEach(k => {
        const entry = fullChatHistory[k];
        // Only show matching mode entries
        const entryMode = entry.mode || 'journal'; // default to journal if undefined
        if (entryMode === mode) {
            appendMsgToContainer(entry.user_msg || "...", 'user', container);
            appendMsgToContainer(entry.reply || "...", 'ai', container);
        }
    });
    
    container.scrollTop = container.scrollHeight;
}

function appendMsgToContainer(txt, sender, container) {
    const div = document.createElement('div');
    div.className = `msg msg-${sender}`;
    div.innerHTML = parseMarkdown(txt);
    container.appendChild(div);
}

async function sendMessage(mode) {
    if(isProcessing) return;
    
    // Get Elements based on Mode
    const prefix = mode === 'journal' ? 'celi' : 'void';
    const input = document.getElementById(`${prefix}-input`);
    const history = document.getElementById(`${prefix}-history`);
    const typing = document.getElementById(`${prefix}-typing`);
    
    const msg = input.value.trim();
    if(!msg && !activeMediaFile && !activeAudioFile) return;
    
    // Optimistic UI
    appendMsgToContainer(msg || "[Media Transmitting...]", 'user', history);
    input.value = '';
    history.scrollTop = history.scrollHeight;
    
    isProcessing = true;
    typing.classList.remove('hidden');
    history.scrollTop = history.scrollHeight;

    const formData = new FormData();
    formData.append('message', msg);
    formData.append('mode', mode);
    if(activeMediaFile) formData.append('media', activeMediaFile);
    if(activeAudioFile) formData.append('audio', activeAudioFile);

    try {
        const res = await fetch('/api/process', { method: 'POST', body: formData });
        const data = await res.json();
        
        typing.classList.add('hidden');
        appendMsgToContainer(data.reply, 'ai', history);
        history.scrollTop = history.scrollHeight;
        
        if(data.command === 'daily_reward' || data.command === 'level_up') spawnStardust();
        
        // Clear Media
        activeMediaFile = null; 
        activeAudioFile = null;
        
        // Reload Data (Stardust/Calendar)
        await loadData();
        
    } catch(e) {
        typing.classList.add('hidden');
        appendMsgToContainer("Connection failed.", 'ai', history);
    }
    isProcessing = false;
}

// Media Handlers
function handleFileSelect(mode) {
    const prefix = mode === 'journal' ? 'celi' : 'void';
    const input = document.getElementById(`${prefix}-img-upload`);
    const textField = document.getElementById(`${prefix}-input`);
    
    if(input.files && input.files[0]) {
        activeMediaFile = input.files[0];
        textField.placeholder = "Image attached. Add context...";
        textField.focus();
    }
}

function handleAudioSelect(mode) {
    const prefix = mode === 'journal' ? 'celi' : 'void';
    const input = document.getElementById(`${prefix}-audio-upload`);
    const textField = document.getElementById(`${prefix}-input`);
    
    if(input.files && input.files[0]) {
        activeAudioFile = input.files[0];
        textField.placeholder = "Audio attached. Sending...";
        sendMessage(mode); // Auto send audio
    }
}

function toggleMic(mode) {
    const prefix = mode === 'journal' ? 'celi' : 'void';
    document.getElementById(`${prefix}-audio-upload`).click();
}

// --- SHARED UTILS (Preserved) ---
function getStarsHTML(rankTitle) { 
    let count = 0; 
    if (rankTitle.includes("VI")) count = 6; 
    else if (rankTitle.includes("IV")) count = 4; 
    else if (rankTitle.includes("V")) count = 5; 
    else if (rankTitle.includes("III")) count = 3; 
    else if (rankTitle.includes("II")) count = 2; 
    else if (rankTitle.includes("I")) count = 1; 
    if(rankTitle.includes("Ethereal") && count > 5) count = 5; 
    return Array(count).fill(STAR_SVG).join(''); 
}

function parseMarkdown(text) {
    if (!text) return "";
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
               .replace(/\*(.*?)\*/g, '<em>$1</em>')
               .replace(/\n/g, '<br>');
}

function speakText(text) {
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1; utterance.pitch = 1;
        window.speechSynthesis.speak(utterance);
    } else { alert("Voice synthesis not supported."); }
}

// Archive functions are still here, connected to data.js logic
function openArchive(id) { 
    const modal = document.getElementById('archive-modal'); 
    modal.classList.add('active'); 
    modal.style.display = 'flex'; 

    document.getElementById('archive-date').innerText = "Loading...";
    document.getElementById('archive-analysis').innerText = "Loading synthesis...";
    document.getElementById('archive-image-container').classList.add('hidden');
    document.getElementById('archive-audio-container').classList.add('hidden');

    fetch('/api/star_detail', { 
        method:'POST', 
        headers:{'Content-Type':'application/json'}, 
        body:JSON.stringify({id})
    })
    .then(r => r.json())
    .then(d => { 
        document.getElementById('archive-date').innerText = d.date; 
        document.getElementById('archive-analysis').innerText = d.analysis || d.summary || "No synthesis available."; 
        
        if(d.image_url) { 
            document.getElementById('archive-image-container').classList.remove('hidden'); 
            document.getElementById('archive-image').src = d.image_url; 
        } 
        if(d.audio_url) { 
            document.getElementById('archive-audio-container').classList.remove('hidden'); 
            document.getElementById('archive-audio').src = d.audio_url; 
        } 
    })
    .catch(e => {
        document.getElementById('archive-analysis').innerText = "Error retrieving archive data.";
    });
}

function closeArchive() { 
    const modal = document.getElementById('archive-modal');
    modal.classList.remove('active'); 
    modal.style.display = 'none'; 
    const audio = document.getElementById('archive-audio');
    if(audio) audio.pause(); 
}

function spawnStardust() { 
    const s = document.getElementById('nav-pfp').getBoundingClientRect(); 
    const t = document.getElementById('rank-progress-bar').getBoundingClientRect(); 
    const pfp = document.getElementById('nav-pfp'); 
    pfp.classList.remove('pulse-anim'); void pfp.offsetWidth; pfp.classList.add('pulse-anim'); 
    for(let i=0; i<8; i++){ 
        setTimeout(()=>{ 
            const p = document.createElement('div'); p.className='stardust-particle'; 
            p.style.left = (s.left+s.width/2)+'px'; p.style.top = (s.top+s.height/2)+'px'; 
            document.body.appendChild(p); 
            const tx = t.left+Math.random()*t.width; const ty = t.top+t.height/2; 
            p.animate([{transform:'translate(0,0) scale(1)', opacity:1}, {transform:`translate(${tx-parseFloat(p.style.left)}px, ${ty-parseFloat(p.style.top)}px) scale(0.5)`, opacity:0}], {duration: 800+Math.random()*400, easing:'cubic-bezier(0.25,1,0.5,1)'}).onfinish = () => p.remove(); 
        }, i*100); 
    } 
}
