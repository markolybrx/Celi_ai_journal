// --- DATA & CALENDAR LOGIC ---

let pickerDate = new Date();
let selectedMonthIdx = 0;

async function loadData() { 
    try { 
        const res = await fetch('/api/data'); if(!res.ok) return; 
        const data = await res.json(); 
        if(data.status === 'guest') { window.location.href='/login'; return; } 
        
        globalRankTree = data.progression_tree; currentLockIcon = data.progression_tree.lock_icon; 
        const hour = new Date().getHours(); let timeGreet = hour >= 18 ? "Good Evening" : (hour >= 12 ? "Good Afternoon" : "Good Morning");
        document.getElementById('greeting-text').innerText = `${timeGreet}, ${data.first_name}!`; 
        document.getElementById('rank-display').innerText = data.rank; 
        document.getElementById('rank-psyche').innerText = data.rank_psyche; 
        document.getElementById('rank-progress-bar').style.width = `${data.rank_progress}%`; 
        document.getElementById('stardust-cnt').innerText = `${data.stardust_current}/${data.stardust_max} Stardust`; 
        
        document.getElementById('pfp-img').src = data.profile_pic || ''; 
        document.documentElement.style.setProperty('--mood', data.current_color); 
        document.getElementById('main-rank-icon').innerHTML = data.current_svg; 
        document.getElementById('profile-pfp-large').src = data.profile_pic || ''; 
        document.getElementById('profile-fullname').innerText = `${data.first_name} ${data.last_name}`; 
        document.getElementById('profile-id').innerText = data.username; 
        document.getElementById('profile-color-text').innerText = data.aura_color; 
        
        const dot = document.getElementById('profile-color-dot'); dot.style.backgroundColor = data.aura_color;
        if (!data.aura_color || dot.style.backgroundColor === '') dot.style.backgroundColor = data.current_color;

        document.getElementById('profile-secret-q').innerText = SQ_MAP[data.secret_question] || data.secret_question;
        document.getElementById('edit-fname').value = data.first_name; 
        document.getElementById('edit-lname').value = data.last_name; 
        document.getElementById('edit-color').value = data.aura_color; 
        document.getElementById('edit-uid-display').innerText = data.username;
        document.getElementById('theme-btn').innerText = document.documentElement.getAttribute('data-theme') === 'light' ? 'Light' : 'Dark';
        
        if(data.history) fullChatHistory = data.history; 
        userHistoryDates = Object.values(data.history).map(e=>e.date);
        
        // --- HUMANIZED ECHO LOGIC ---
        const historyKeys = Object.keys(fullChatHistory).sort();
        if (historyKeys.length > 0) {
            const lastKey = historyKeys[historyKeys.length - 1];
            const lastEntry = fullChatHistory[lastKey];
            
            // Prefer summary, fallback to user message
            let conversationText = "";
            
            if (lastEntry.summary) {
                // If backend provides a summary: "You mentioned [summary]..."
                conversationText = `You mentioned ${lastEntry.summary.toLowerCase()}... How is that going?`;
            } else {
                // Fallback to raw text: "We talked about..."
                const raw = lastEntry.user_msg || "something on your mind";
                const snippet = raw.length > 50 ? raw.substring(0, 50) + "..." : raw;
                conversationText = `We talked about "${snippet}". Want to continue?`;
            }
            
            // Clean markdown if any
            conversationText = conversationText.replace(/\*\*/g, '').replace(/\*/g, '');
            
            document.getElementById('echo-text').innerText = conversationText;
            document.getElementById('echo-date').innerText = lastEntry.date;
        }

        renderCalendar(); 
    } catch(e) { console.error(e); } 
}

async function handlePfpUpload() { const input = document.getElementById('pfp-upload-input'); if(input.files && input.files[0]) { const formData = new FormData(); formData.append('pfp', input.files[0]); const res = await fetch('/api/update_pfp', { method: 'POST', body: formData }); const data = await res.json(); if(data.status === 'success') { document.getElementById('pfp-img').src = data.url; document.getElementById('profile-pfp-large').src = data.url; } } }
function askUpdateInfo() { openModal('info-confirm-modal'); }
async function confirmUpdateInfo() { const btn = document.getElementById('btn-confirm-info'); const originalText = "Confirm"; btn.innerHTML = '<span class="spinner"></span>'; btn.disabled = true; const body = { first_name: document.getElementById('edit-fname').value, last_name: document.getElementById('edit-lname').value, aura_color: document.getElementById('edit-color').value }; try { const res = await fetch('/api/update_profile', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) }); const data = await res.json(); if(data.status === 'success') { closeModal('info-confirm-modal'); closeModal('edit-info-modal'); showStatus(true, "Profile Updated"); loadData(); } else { showStatus(false, data.message); } } catch(e) { showStatus(false, "Connection Failed"); } btn.innerHTML = originalText; btn.disabled = false; }
async function updateSecurity(type) { let body = {}; const btn = type === 'pass' ? document.getElementById('btn-update-pass') : document.getElementById('btn-update-secret'); const originalText = "Update"; btn.innerHTML = '<span class="spinner"></span> Loading...'; btn.disabled = true; if(type === 'pass') { const p1 = document.getElementById('new-pass-input').value; const p2 = document.getElementById('confirm-pass-input').value; if(p1 !== p2) { document.getElementById('new-pass-input').classList.add('input-error'); document.getElementById('confirm-pass-input').classList.add('input-error'); setTimeout(()=>{ document.getElementById('new-pass-input').classList.remove('input-error'); document.getElementById('confirm-pass-input').classList.remove('input-error'); }, 500); btn.innerHTML=originalText; btn.disabled=false; return; } body = { new_password: p1 }; } else { const q = document.getElementById('new-secret-q').value; if(!q) { showStatus(false, "Select a Question"); btn.innerHTML=originalText; btn.disabled=false; return; } body = { new_secret_q: q, new_secret_a: document.getElementById('new-secret-a').value }; } try { const res = await fetch('/api/update_security', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) }); const data = await res.json(); if(data.status === 'success') { closeModal('change-pass-modal'); closeModal('change-secret-modal'); showStatus(true, "Security details updated."); loadData(); } else { showStatus(false, data.message); } } catch(e) { showStatus(false, "Connection Failed"); } btn.innerHTML = originalText; btn.disabled = false; }
async function performWipe() { const btn = document.querySelector('#delete-confirm-modal button.bg-red-500'); const originalText = btn.innerText; btn.innerText = "Deleting..."; btn.disabled = true; try { const res = await fetch('/api/clear_history', { method: 'POST' }); const data = await res.json(); if (data.status === 'success') { window.location.href = '/login'; } else { alert("Error: " + data.message); btn.innerText = originalText; btn.disabled = false; } } catch (e) { alert("Connection failed."); btn.innerText = originalText; btn.disabled = false; } }

function renderCalendar() { 
    const g = document.getElementById('cal-grid'); 
    g.innerHTML = ''; 
    const m = currentCalendarDate.getMonth(); 
    const y = currentCalendarDate.getFullYear(); 
    
    document.getElementById('cal-month-year').innerText = new Date(y,m).toLocaleString('default',{month:'long', year:'numeric'}); 
    
    const now = new Date();
    const isCurrent = (now.getMonth() === m && now.getFullYear() === y);
    const todayBtn = document.getElementById('cal-today-btn');
    if (todayBtn) {
        if (!isCurrent) todayBtn.classList.remove('hidden');
        else todayBtn.classList.add('hidden');
    }

    ["S","M","T","W","T","F","S"].forEach(d => g.innerHTML += `<div>${d}</div>`); 
    
    const days = new Date(y, m+1, 0).getDate(); 
    const f = new Date(y, m, 1).getDay(); 
    
    for(let i=0; i<f; i++) g.innerHTML += `<div></div>`; 
    
    for(let i=1; i<=days; i++) { 
        const d = document.createElement('div'); 
        d.className = 'cal-day'; 
        d.innerText = i; 
        
        if (isCurrent && i === now.getDate()) d.classList.add('today');
        
        if (userHistoryDates.includes(`${y}-${String(m+1).padStart(2,'0')}-${String(i).padStart(2,'0')}`)) {
            d.classList.add('has-entry');
        }
        g.appendChild(d); 
    } 
}

function changeMonth(d) { currentCalendarDate.setMonth(currentCalendarDate.getMonth() + d); renderCalendar(); }
function goToToday() { currentCalendarDate = new Date(); renderCalendar(); }

function toggleDatePicker() {
    const picker = document.getElementById('cal-picker');
    const isActive = picker.classList.contains('active');
    
    if (!isActive) {
        pickerDate = new Date(currentCalendarDate.getTime());
        selectedMonthIdx = pickerDate.getMonth();
        renderPickerUI();
        picker.classList.add('active');
    } else {
        picker.classList.remove('active');
    }
}

function renderPickerUI() {
    document.getElementById('picker-year-display').innerText = pickerDate.getFullYear();
    const container = document.getElementById('picker-months-container');
    container.innerHTML = '';
    
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    months.forEach((m, idx) => {
        const btn = document.createElement('div');
        btn.className = `picker-month-btn ${idx === selectedMonthIdx ? 'selected' : ''}`;
        btn.innerText = m;
        btn.onclick = () => selectPickerMonth(idx);
        container.appendChild(btn);
    });
}

function adjustPickerYear(delta) {
    pickerDate.setFullYear(pickerDate.getFullYear() + delta);
    document.getElementById('picker-year-display').innerText = pickerDate.getFullYear();
}

function selectPickerMonth(idx) {
    selectedMonthIdx = idx;
    pickerDate.setMonth(idx);
    renderPickerUI(); 
}

function confirmDateSelection() {
    currentCalendarDate.setFullYear(pickerDate.getFullYear());
    currentCalendarDate.setMonth(selectedMonthIdx);
    renderCalendar();
    toggleDatePicker(); 
}
