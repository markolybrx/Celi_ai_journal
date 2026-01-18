// celi_ai v1.5.3 External Script
console.log("Script File Loaded v1.5.3");
document.getElementById('debug-status').innerText = "Core Active";

const PHASE_COLORS = { "The Awakening Phase": "#00f2fe", "The Ignition Phase": "#fbbf24", "The Expansion Phase": "#8b5cf6", "The Singularity": "#ffffff" };

const app = {
    data: { username: "Traveler", rank: "Observer", profile_pic: null, rank_config: [], history: {} },
    calDate: new Date(),
    bubbleTimer: null,

    log: function(msg) {
        const el = document.getElementById('debug-status');
        if(el) el.innerText = msg;
        console.log(msg);
    },

    changeMonth: function(delta) {
        this.calDate.setMonth(this.calDate.getMonth() + delta);
        this.renderCalendar();
    },

    renderCalendar: function() {
        const year = this.calDate.getFullYear();
        const month = this.calDate.getMonth();
        const firstDay = new Date(year, month, 1).getDay();
        const lastDate = new Date(year, month + 1, 0).getDate();
        const today = new Date();
        const isCurrentMonth = today.getFullYear() === year && today.getMonth() === month;
        
        const monthNames = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
        document.getElementById('cal-month-year').innerText = `${monthNames[month]} ${year}`;
        
        const grid = document.getElementById('cal-days');
        grid.innerHTML = "";

        for (let i = 0; i < firstDay; i++) { grid.innerHTML += `<div></div>`; }

        for (let i = 1; i <= lastDate; i++) {
            let classes = "cal-day";
            if (isCurrentMonth && i === today.getDate()) classes += " cal-day-today";
            const checkDate = `${year}-${String(month+1).padStart(2,'0')}-${String(i).padStart(2,'0')}`;
            let hasEntry = false;
            if (this.data.history) {
                hasEntry = Object.values(this.data.history).some(log => log.date === checkDate);
            }
            const dotHtml = hasEntry ? `<div class="has-entry-dot"></div>` : '';
            grid.innerHTML += `<div class="${classes}">${i}${dotHtml}</div>`;
        }
    },

    render: function() {
        const d = this.data;
        const phaseColor = PHASE_COLORS[d.phase] || "#00f2fe";
        
        document.documentElement.style.setProperty('--mood', phaseColor);
        document.getElementById('greeting').innerText = `Hello, ${d.username || 'Traveler'}!`;
        document.getElementById('rank-display').innerText = d.rank || 'Observer';
        document.getElementById('rank-display').style.color = phaseColor;
        document.getElementById('rank-bar').style.backgroundColor = phaseColor;
        document.getElementById('rank-bar').style.width = (d.rank_progress || 0) + '%';
        
        const mini = document.getElementById('mini-rank-logo');
        mini.style.borderColor = phaseColor;
        mini.style.boxShadow = `0 0 10px ${phaseColor}66`;
        if (d.rank && d.rank.includes("Observer")) {
            mini.innerHTML = `<div class="w-3 h-3 bg-white rounded-full pulse-glow" style="color:${phaseColor}"></div>`;
        } else {
            mini.innerHTML = `<div class="w-3 h-3 border-2 border-current rotate-45 shadow-[0_0_5px_currentColor]" style="color:${phaseColor}"></div>`;
        }

        const largeIcon = document.getElementById('portal-rank-icon');
        largeIcon.style.borderColor = phaseColor;
        largeIcon.style.boxShadow = `0 0 30px ${phaseColor}44`;
        if (d.rank && d.rank.includes("Observer")) {
            largeIcon.innerHTML = `<div class="w-16 h-16 bg-white rounded-full pulse-glow" style="color:${phaseColor}"></div>`;
        } else {
            largeIcon.innerHTML = `<div class="w-16 h-16 border-4 border-current rotate-45 shadow-[0_0_20px_currentColor]" style="color:${phaseColor}"></div>`;
        }

        const roman = (d.rank_roman || "I");
        const count = {"I":1, "II":2, "III":3, "IV":4, "V":5}[roman] || 1;
        document.getElementById('portal-level-stars').innerHTML = Array(count).fill(`<div class="star-four-point" style="color:${phaseColor}"></div>`).join('');
        
        document.getElementById('portal-rank-name').innerText = d.rank;
        document.getElementById('portal-rank-name').style.color = phaseColor;
        document.getElementById('portal-progress-bar').style.backgroundColor = phaseColor;
        document.getElementById('portal-progress-bar').style.width = (d.rank_progress || 0) + '%';
        document.getElementById('portal-points').innerText = `${d.points || 0} Stars`;
        document.getElementById('portal-synthesis-text').innerText = d.rank_synthesis || "Connecting...";

        const listContainer = document.getElementById('portal-future-list');
        if (d.rank_config && d.rank_config.length > 0) {
            let currentPhaseName = "";
            let html = "";
            d.rank_config.forEach(r => {
                const pColor = PHASE_COLORS[r.phase];
                if (r.phase !== currentPhaseName) {
                    currentPhaseName = r.phase;
                    html += `<div class="mt-6 mb-2 pl-2 border-l-2 text-[9px] font-black uppercase tracking-widest" style="color:${pColor}; border-color:${pColor}44; text-shadow: 0 0 10px ${pColor}44;">${currentPhaseName}</div>`;
                }
                const isUnlocked = (d.points || 0) >= r.threshold;
                const itemColor = isUnlocked ? pColor : "rgba(255,255,255,0.3)";
                const clickAction = isUnlocked ? "" : `onclick="app.flashWarning(${r.threshold - (d.points || 0)})"`;
                const cursor = isUnlocked ? "default" : "pointer";
                html += `<div class="flex justify-between items-center py-2 px-2 border-b border-white/5" ${clickAction} style="cursor:${cursor}"><span class="text-[10px] font-bold uppercase" style="color:${itemColor}">${r.name}</span><span class="text-[8px] uppercase opacity-40">${isUnlocked ? 'ALIGNED' : 'LOCKED'}</span></div>`;
            });
            listContainer.innerHTML = html;
        }

        const defaultIcon = document.getElementById('icon-user').outerHTML;
        let imgHTML = defaultIcon;
        if (d.profile_pic && d.profile_pic.length > 50) {
            imgHTML = `<img src="${d.profile_pic}" class="profile-img" style="border-radius:12px;">`;
            let roundImg = `<img src="${d.profile_pic}" class="profile-img" style="border-radius:50%;">`;
            document.getElementById('portal-profile-container').innerHTML = roundImg;
        } else {
            document.getElementById('portal-profile-container').innerHTML = defaultIcon;
        }
        document.getElementById('header-profile-container').innerHTML = imgHTML;

        document.getElementById('profile-name').innerText = d.username;
        document.getElementById('profile-bday').innerText = d.birthday || '--';
        if(d.fav_color) document.getElementById('profile-color-dot').style.backgroundColor = d.fav_color;
        document.getElementById('celi-analysis-text').innerText = d.celi_analysis || "Connecting...";
        
        document.getElementById('edit-bday').value = (d.birthday && d.birthday !== 'Unset') ? d.birthday : '';
        document.getElementById('edit-color').value = d.fav_color || '#00f2fe';

        this.renderCalendar();
    },

    sync: async function() {
        this.log("Syncing...");
        try {
            const res = await fetch('/api/data');
            if (res.redirected) { window.location.href = '/login'; return; }
            const json = await res.json();
            if (json.status === 'guest') { window.location.href = '/login'; return; }
            this.data = json;
            this.render();
            this.log("System Active");
        } catch (e) {
            this.log("Offline Mode");
            this.render();
        }
    },

    openTab: function(id) { document.querySelectorAll('.overlay, #chat-modal').forEach(el => el.style.display = 'none'); document.getElementById(id + '-overlay').style.display = 'flex'; this.sync(); },
    closeUI: function() { document.querySelectorAll('.overlay, #chat-modal').forEach(el => el.style.display = 'none'); document.getElementById('celi-bubble').style.display = 'none'; },
    closeChat: function() { document.getElementById('chat-modal').style.display = 'none'; },
    showIntent: function() { this.toggleAiMenu(); },
    toggleAiMenu: function() { const b = document.getElementById('celi-bubble'); if (b.style.display === 'block' && b.classList.contains('bubble-menu')) { b.style.display = 'none'; } else { this.speak("How shall we proceed?", 'menu'); } },
    openEditProfile: function() { document.getElementById('edit-modal').style.display = 'flex'; },
    
    startChat: function(mode) { this.currentMode = mode; document.getElementById('celi-bubble').style.display = 'none'; document.getElementById('chat-modal').style.display = 'flex'; setTimeout(() => document.getElementById('msg-input').focus(), 100); },
    
    speak: function(msg, type) {
        const b = document.getElementById('celi-bubble'); const t = document.getElementById('bubble-text'); const a = document.getElementById('bubble-actions');
        b.className = ''; b.classList.add(type === 'menu' ? 'bubble-menu' : (type === 'warn' ? 'bubble-warn' : 'bubble-trivia'));
        t.innerText = msg; a.classList.toggle('hidden', type !== 'menu'); b.style.display = 'block';
        if (this.bubbleTimer) clearTimeout(this.bubbleTimer);
        if (type !== 'menu') this.bubbleTimer = setTimeout(() => { b.style.display = 'none'; }, 6000);
    },
    
    flashWarning: function(needed) { this.speak(`Access Denied. You need ${needed} more stars to align with this frequency.`, 'warn'); },
    triggerTrivia: async function() { try { const res = await fetch('/api/trivia'); const d = await res.json(); if(d.trivia) this.speak(d.trivia, 'trivia'); } catch(e) {} },

    saveProfile: async function() { const bday = document.getElementById('edit-bday').value; const color = document.getElementById('edit-color').value; const file = document.getElementById('edit-pic').files[0]; let payload = { birthday: bday, fav_color: color }; const send = async (p) => { this.log("Saving..."); await fetch('/api/update_profile', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(p) }); document.getElementById('edit-modal').style.display = 'none'; this.sync(); }; if (file) { const reader = new FileReader(); reader.onload = (e) => { payload.profile_pic = e.target.result; send(payload); }; reader.readAsDataURL(file); } else { send(payload); } },
    confirmDelete: async function() { if (confirm("Delete data?")) { await fetch('/api/delete_user', { method: 'POST' }); window.location.reload(); } },
    
    getTime: function() { const now = new Date(); return now.getHours().toString().padStart(2,'0') + ":" + now.getMinutes().toString().padStart(2,'0'); },
    
    sendAction: async function() {
        const input = document.getElementById('msg-input'); const text = input.value; if (!text) return;
        const con = document.getElementById('chat-scroller'); const time = this.getTime();
        con.innerHTML += `<div class="msg msg-user">${text}<span class="timestamp">${time}</span></div>`;
        input.value = ''; con.scrollTop = con.scrollHeight;
        const typing = document.getElementById('typing-indicator'); typing.style.display = 'flex'; con.scrollTop = con.scrollHeight;
        try {
            const res = await fetch('/api/process', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: text, mode: this.currentMode || 'journal' }) });
            const d = await res.json();
            setTimeout(() => { typing.style.display = 'none'; con.innerHTML += `<div class="msg msg-celi">${d.reply}<span class="timestamp">${time}</span></div>`; con.scrollTop = con.scrollHeight; this.sync(); }, 1500);
        } catch (e) { this.log("Msg Error"); typing.style.display = 'none'; }
    }
};

document.addEventListener('DOMContentLoaded', () => { app.sync(); setInterval(() => app.sync(), 30000); setTimeout(() => app.triggerTrivia(), 5000); setInterval(() => app.triggerTrivia(), 60000); });
