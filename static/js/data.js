async function loadData() { 
    try { 
        const res = await fetch('/api/data'); if(!res.ok) return; 
        const data = await res.json(); 
        if(data.status === 'guest') { window.location.href='/login'; return; } 
        
        // --- DASHBOARD ---
        globalRankTree = data.progression_tree; 
        document.getElementById('greeting-text').innerText = `Welcome, ${data.first_name}!`; 
        document.getElementById('rank-display').innerText = data.rank; 
        document.getElementById('rank-psyche').innerText = data.rank_psyche; 
        document.getElementById('rank-progress-bar').style.width = `${data.rank_progress}%`; 
        document.getElementById('stardust-cnt').innerText = `${data.stardust_current}/${data.stardust_max} SD`; 
        document.getElementById('pfp-img').src = data.profile_pic || 'https://ui-avatars.com/api/?name=User'; 
        document.documentElement.style.setProperty('--mood', data.current_color); 
        document.getElementById('main-rank-icon').innerHTML = data.current_svg; 
        document.getElementById('profile-pfp-large').src = data.profile_pic || '';
        document.getElementById('profile-fullname').innerText = `${data.first_name} ${data.last_name}`;
        document.getElementById('profile-id').innerText = `@${data.username}`;

        // --- CALENDAR ---
        fullChatHistory = data.history;
        userHistoryDates = Object.values(data.history).map(h => h.date);
        renderCalendar();
        
        // --- ECHO CARD ---
        const historyKeys = Object.keys(data.history).sort();
        if(historyKeys.length > 0) {
            const lastKey = historyKeys[historyKeys.length-1];
            const lastEntry = data.history[lastKey];
            document.getElementById('echo-date').innerText = lastEntry.date;
            document.getElementById('echo-text').innerText = lastEntry.summary || lastEntry.full_message;
        }
    } catch(e) { console.error(e); } 
}

function renderCalendar() { 
    const g = document.getElementById('cal-grid'); g.innerHTML=''; 
    const m = currentCalendarDate.getMonth(); const y = currentCalendarDate.getFullYear(); 
    document.getElementById('cal-month-year').innerText = new Date(y,m).toLocaleString('default',{month:'long',year:'numeric'}); 
    ["S","M","T","W","T","F","S"].forEach(d => g.innerHTML+=`<div class="text-[10px] opacity-50 font-bold">${d}</div>`); 
    const days = new Date(y, m+1, 0).getDate(); const f = new Date(y, m, 1).getDay(); 
    for(let i=0; i<f; i++) g.innerHTML+=`<div></div>`; 
    for(let i=1; i<=days; i++){ 
        const d = document.createElement('div'); d.className='cal-day'; d.innerText=i; 
        const dateStr = `${y}-${String(m+1).padStart(2,'0')}-${String(i).padStart(2,'0')}`;
        if(userHistoryDates.includes(dateStr)) {
            d.classList.add('has-entry');
            d.onclick = () => {
                // Find entry for this date
                const entryKey = Object.keys(fullChatHistory).find(k => fullChatHistory[k].date === dateStr);
                if(entryKey) openArchive(entryKey);
            }
        }
        if(i === new Date().getDate() && m === new Date().getMonth()) d.classList.add('today');
        g.appendChild(d); 
    } 
}
function changeMonth(d) { currentCalendarDate.setMonth(currentCalendarDate.getMonth()+d); renderCalendar(); }
// Auto Load
window.addEventListener('load', loadData);
